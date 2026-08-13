from datetime import datetime, timedelta

from app.db.models import AlertEvent, Keyword, Opportunity
from app.db.session import SessionLocal
from app.domain.high_signal import HighSignalTriggerPolicy
from app.services.alerts import HIGH_SIGNAL_RULE_NAME, trigger_high_signal_alerts


def _opportunity(db, *, score=88, signature="a" * 64) -> Opportunity:
    keyword = Keyword(canonical="high-signal-alert", display_name="High signal alert", status="ACTIVE")
    db.add(keyword)
    db.flush()
    opportunity = Opportunity(
        opportunity_key="opp:high-signal-alert",
        keyword_id=keyword.id,
        title="High signal alert opportunity",
        stage="EARLY_GROWTH",
        score=score,
        risk_score=20,
        evidence_count=5,
        cross_source_score=10,
        analysis_status="READY",
        analysis_signature=signature,
        score_version="score-v1",
        updated_at=datetime(2026, 8, 12, 10),
    )
    db.add(opportunity)
    db.flush()
    return opportunity


def test_high_signal_alert_trigger_is_eventized_and_deduplicated():
    with SessionLocal() as db:
        opportunity = _opportunity(db)
        policy = HighSignalTriggerPolicy(cooldown_minutes=60)
        first = trigger_high_signal_alerts(db, opportunity_ids={opportunity.id}, now=datetime(2026, 8, 12, 12), policy=policy)
        db.commit()
        second = trigger_high_signal_alerts(db, opportunity_ids={opportunity.id}, now=datetime(2026, 8, 12, 12, 5), policy=policy)
        events = db.query(AlertEvent).all()
    assert first == {"rule": HIGH_SIGNAL_RULE_NAME, "opportunities": 1, "matched": 1, "created": 1, "suppressed": 0}
    assert second == {"rule": HIGH_SIGNAL_RULE_NAME, "opportunities": 1, "matched": 1, "created": 0, "suppressed": 1}
    assert len(events) == 1
    assert events[0].event_key and len(events[0].event_key) == 64
    assert "dedupe_key=" in events[0].message


def test_high_signal_cooldown_allows_a_meaningful_new_state_after_expiry():
    with SessionLocal() as db:
        opportunity = _opportunity(db)
        policy = HighSignalTriggerPolicy(cooldown_minutes=60)
        trigger_high_signal_alerts(db, opportunity_ids={opportunity.id}, now=datetime(2026, 8, 12, 12), policy=policy)
        db.commit()
        opportunity.score = 92
        opportunity.updated_at = datetime(2026, 8, 12, 13, 1)
        opportunity.analysis_signature = "b" * 64
        third = trigger_high_signal_alerts(db, opportunity_ids={opportunity.id}, now=datetime(2026, 8, 12, 13, 2), policy=policy)
        db.commit()
        event_count = db.query(AlertEvent).count()
    assert third["created"] == 1
    assert third["suppressed"] == 0
    assert event_count == 2


def test_high_signal_alerts_fail_closed_for_non_eligible_opportunity():
    with SessionLocal() as db:
        opportunity = _opportunity(db, score=70)
        result = trigger_high_signal_alerts(db, opportunity_ids={opportunity.id}, now=datetime(2026, 8, 12, 12))
        db.commit()
        event_count = db.query(AlertEvent).count()
    assert result["matched"] == 0
    assert result["created"] == 0
    assert event_count == 0
