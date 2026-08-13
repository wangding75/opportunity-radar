from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.core.time import utc_now
from app.db.models import (
    AlertEvaluationQueue,
    AlertEvent,
    AlertRule,
    EmailDeliveryRecord,
    Keyword,
    Opportunity,
    OpportunityScoreSnapshot,
    WebhookDeliveryRecord,
    WebhookEndpoint,
)
from app.db.session import SessionLocal
from app.services.alert_replay_backtest_audit import audit_alert_replay_backtest
from app.services.scoring import backtest_summary, replay_snapshot


def _seed_complete_chain(db):
    now = utc_now()
    keyword = Keyword(canonical="synthetic-alert-replay", display_name="Synthetic alert replay", status="ACTIVE", first_seen_at=now - timedelta(days=60), last_seen_at=now)
    db.add(keyword)
    db.flush()
    opportunity = Opportunity(opportunity_key="opp:synthetic-alert-replay", keyword_id=keyword.id, title="Synthetic alert replay", stage="DISCOVERY", score=70, risk_score=10)
    db.add(opportunity)
    db.flush()
    first_at = now - timedelta(days=45)
    second_at = now - timedelta(days=35)
    db.add_all([
        OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v1", input_signature="a" * 64, score=40, risk_score=10, stage="DISCOVERY", evidence_count=1, breakdown={}, calculated_at=first_at),
        OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v1", input_signature="b" * 64, score=70, risk_score=10, stage="DISCOVERY", evidence_count=2, breakdown={}, calculated_at=second_at),
    ])
    rule = AlertRule(name="SYNTHETIC_REPLAY_RULE", min_score=60, max_risk_score=100, min_evidence_count=1, cooldown_minutes=60, created_at=first_at, updated_at=first_at)
    db.add(rule)
    db.flush()
    event = AlertEvent(alert_rule_id=rule.id, opportunity_id=opportunity.id, keyword_id=keyword.id, event_key="c" * 64, status="ACKNOWLEDGED", priority=3, title="Synthetic alert", message="synthetic", score=70, risk_score=10, created_at=second_at, acknowledged_at=second_at + timedelta(minutes=1), acknowledged_by="synthetic")
    db.add(event)
    db.flush()
    db.add(AlertEvaluationQueue(opportunity_id=opportunity.id, reason="SYNTHETIC", queued_at=second_at, revision=1, attempt_count=0, next_retry_at=second_at))
    endpoint = WebhookEndpoint(name="synthetic-replay-endpoint", url="https://synthetic.invalid/hooks", secret="synthetic-secret-0123456789", secret_fingerprint="d" * 64, event_types=["alert.event"], created_at=second_at, updated_at=second_at)
    db.add(endpoint)
    db.flush()
    db.add(EmailDeliveryRecord(alert_event_id=event.id, message_id="synthetic-message", idempotency_key="synthetic-email-key", input_signature="e" * 64, recipients=["synthetic@example.invalid"], template_name="alert.event", template_version="v1", request_payload={"data_class": "SYNTHETIC"}, status="QUEUED", created_at=second_at, updated_at=second_at))
    db.add(WebhookDeliveryRecord(alert_event_id=event.id, endpoint_id=endpoint.id, event_id="synthetic-event", delivery_id="synthetic-delivery", input_signature="f" * 64, event_payload={"data_class": "SYNTHETIC"}, status="QUEUED", created_at=second_at, updated_at=second_at))
    db.flush()
    return opportunity.id, first_at, second_at


def test_empty_alert_replay_backtest_audit_is_pass():
    with SessionLocal() as db:
        result = audit_alert_replay_backtest(db)
        assert result["status"] == "PASS"
        assert result["summary"]["real_data_collected"] == 0


def test_alert_replay_backtest_audit_accepts_synthetic_chain_and_replay_is_cutoff_bounded():
    with SessionLocal() as db:
        opportunity_id, first_at, second_at = _seed_complete_chain(db)
        db.commit()
        assert replay_snapshot(db, opportunity_id, as_of=first_at + timedelta(minutes=1))["score"] == 40
        assert replay_snapshot(db, opportunity_id, as_of=second_at + timedelta(minutes=1))["score"] == 70
        result = audit_alert_replay_backtest(db)
        assert result["status"] == "PASS", result
        assert result["summary"]["replay_boundary_checks"] == 2


def test_audit_detects_future_snapshot_and_broken_alert_lifecycle():
    with SessionLocal() as db:
        opportunity_id, _first_at, second_at = _seed_complete_chain(db)
        event = db.scalar(select(AlertEvent))
        event.status = "RESOLVED"
        event.resolved_at = second_at - timedelta(minutes=1)
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity_id, model_version="score-v1", input_signature="1" * 64, score=99, risk_score=0, stage="DISCOVERY", evidence_count=1, breakdown={}, calculated_at=utc_now() + timedelta(days=1)))
        db.flush()
        result = audit_alert_replay_backtest(db)
        assert result["status"] == "FAIL"
        rules = {row["rule"] for row in result["violations"]}
        assert "score_snapshot_not_in_future" in rules
        assert "alert_lifecycle_time_after_creation" in rules


def test_backtest_excludes_future_score_snapshots():
    with SessionLocal() as db:
        now = utc_now()
        keyword = Keyword(canonical="synthetic-future-backtest", display_name="Synthetic future backtest", status="ACTIVE", first_seen_at=now, last_seen_at=now)
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(opportunity_key="opp:synthetic-future-backtest", keyword_id=keyword.id, title="Synthetic future", stage="DISCOVERY")
        db.add(opportunity)
        db.flush()
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v1", input_signature="2" * 64, score=99, risk_score=0, stage="DISCOVERY", evidence_count=1, breakdown={}, calculated_at=now + timedelta(days=1)))
        db.commit()
        result = backtest_summary(db, lookback_days=90, threshold=60)
        assert result["candidate_signals"] == 0
        assert result["immature_signals"] == 0
