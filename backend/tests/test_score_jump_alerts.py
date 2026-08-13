from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import AlertEvent, Keyword, Opportunity, OpportunityScoreSnapshot, ScoreJumpRecord
from app.db.session import SessionLocal
from app.main import app
from app.services.score_jump_alerts import materialize_score_jump_alerts
from app.services.score_jumps import materialize_score_jumps
from app.services.score_jump_replay import replay_score_jump


client = TestClient(app)
PREVIOUS_AT = datetime(2026, 8, 1)
CURRENT_AT = datetime(2026, 8, 2)
AS_OF = datetime(2026, 8, 12, 12)


def _seed(*, with_evidence: bool) -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-score-jump-alert", display_name="SYNTHETIC Score Jump Alert", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key="synthetic-score-jump-alert",
            keyword_id=keyword.id,
            title="SYNTHETIC score jump alert opportunity",
            stage="VALIDATED",
            score=60.0,
            risk_score=20.0,
        )
        db.add(opportunity)
        db.flush()
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v1", input_signature="a" * 64, score=40.0, risk_score=25.0, stage="DISCOVERY", evidence_count=1, breakdown={"data_class": "SYNTHETIC", "total": 40}, calculated_at=PREVIOUS_AT))
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="score-v1", input_signature="b" * 64, score=60.0, risk_score=20.0, stage="VALIDATED", evidence_count=2, breakdown={"data_class": "SYNTHETIC", "total": 60}, calculated_at=CURRENT_AT))
        db.commit()
        return opportunity.id


def _add_evidence(opportunity_id: int) -> None:
    from app.db.models import NormalizedItem, OpportunityEvidence, RawObservation
    import hashlib

    with SessionLocal() as db:
        text = "SYNTHETIC score jump alert evidence"
        raw = RawObservation(source_id="synthetic-alert-source", external_id="synthetic-alert-1", query="synthetic score jump", item_type="NEWS", title="SYNTHETIC alert evidence", text=text, source_url="https://synthetic.invalid/alert", observed_at=datetime(2026, 8, 1, 12), acquisition_method="MOCK", evidence_quality="HIGH", acquisition_risk="LOW", content_hash=hashlib.sha256(text.encode()).hexdigest(), raw_payload={"data_class": "SYNTHETIC"})
        db.add(raw)
        db.flush()
        item = NormalizedItem(raw_observation_id=raw.id, canonical_key="synthetic-score-jump-alert-evidence", source_id=raw.source_id, query=raw.query, item_type=raw.item_type, title=raw.title, text=raw.text, source_url=raw.source_url, observed_at=raw.observed_at)
        db.add(item)
        db.flush()
        db.add(OpportunityEvidence(opportunity_id=opportunity_id, normalized_item_id=item.id, evidence_type="DEMAND", observed_at=raw.observed_at))
        db.commit()


def test_score_jump_alert_is_evidence_backed_idempotent_and_acceptance_ready():
    opportunity_id = _seed(with_evidence=True)
    _add_evidence(opportunity_id)
    with SessionLocal() as db:
        detected = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=AS_OF)
        alerts = materialize_score_jump_alerts(db, opportunity_ids={opportunity_id})
        db.commit()
        repeated = materialize_score_jump_alerts(db, opportunity_ids={opportunity_id})
        db.commit()
        record = db.scalar(select(ScoreJumpRecord).where(ScoreJumpRecord.opportunity_id == opportunity_id))
        event = db.scalar(select(AlertEvent).where(AlertEvent.opportunity_id == opportunity_id))

    assert detected["created"] == 1
    assert alerts["created"] == 1
    assert repeated["duplicates"] == 1
    assert record is not None and record.alert_event_id == event.id
    assert event is not None and event.status == "NEW"
    assert event.priority >= 1
    assert "evidence_ids=ev1_" in event.message
    accepted = client.patch(f"/api/v1/alerts/events/{event.id}", json={"status": "ACKNOWLEDGED"})
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACKNOWLEDGED"


def test_score_jump_alert_fails_closed_without_evidence_and_replay_is_read_only():
    opportunity_id = _seed(with_evidence=False)
    with SessionLocal() as db:
        before_records = db.scalar(select(func.count(ScoreJumpRecord.id)))
        before_events = db.scalar(select(func.count(AlertEvent.id)))
        result = materialize_score_jumps(db, opportunity_ids={opportunity_id}, evaluated_at=AS_OF)
        alerts = materialize_score_jump_alerts(db, opportunity_ids={opportunity_id})
        replay = replay_score_jump(db, opportunity_id, as_of=AS_OF)
        after_records = db.scalar(select(func.count(ScoreJumpRecord.id)))
        after_events = db.scalar(select(func.count(AlertEvent.id)))
        db.commit()

    assert result["created"] == 1
    assert alerts["created"] == 0
    assert alerts["evidence_missing"] == 1
    assert replay["jumped"] is True
    assert replay["replay_mode"] == "persisted_score_jump_evaluation"
    assert replay["read_only"] is True
    assert replay["evidence_ids"] == []
    assert after_records == before_records + 1
    assert before_events == after_events


def test_score_jump_replay_requires_admin_and_rejects_missing_history(monkeypatch):
    opportunity_id = _seed(with_evidence=False)
    missing_response = client.post("/api/v1/scoring/score-jumps/replay", params={"opportunity_id": opportunity_id, "as_of": "2026-07-01T00:00:00"})
    assert missing_response.status_code == 404

    import app.core.security as security
    from dataclasses import replace
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = client.post("/api/v1/scoring/score-jumps/replay", params={"opportunity_id": opportunity_id, "as_of": "2026-08-12T12:00:00"})
    assert response.status_code == 401
