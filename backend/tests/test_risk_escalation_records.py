import hashlib
from datetime import datetime
from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.db.models import AlertEvent, Keyword, NormalizedItem, Opportunity, OpportunityEvidence, OpportunityScoreSnapshot, RawObservation, RiskEscalationRecord
from app.db.session import SessionLocal
from app.main import app
from app.services.risk_escalation_alerts import materialize_risk_escalations


client = TestClient(app)
PREVIOUS_AT = datetime(2026, 8, 1)
CURRENT_AT = datetime(2026, 8, 2)
NOW = datetime(2026, 8, 12, 12)


def _seed(*, with_evidence: bool, with_previous: bool = True, stable: bool = False) -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical=f"synthetic-risk-record-{with_evidence}-{with_previous}-{stable}", display_name="SYNTHETIC Risk Record", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(opportunity_key=f"synthetic-risk-record-{with_evidence}-{with_previous}-{stable}", keyword_id=keyword.id, title="SYNTHETIC risk record opportunity", stage="VALIDATED", score=75.0, risk_score=55.0)
        db.add(opportunity)
        db.flush()
        if with_previous:
            db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="risk-v1", input_signature="a" * 64, score=70.0, risk_score=20.0, stage="DISCOVERY", evidence_count=1, breakdown={"data_class": "SYNTHETIC", "risk": 20}, calculated_at=PREVIOUS_AT))
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="risk-v1", input_signature="b" * 64, score=75.0, risk_score=25.0 if stable else 55.0, stage="VALIDATED", evidence_count=2, breakdown={"data_class": "SYNTHETIC", "risk": 25 if stable else 55}, calculated_at=CURRENT_AT))
        if with_evidence:
            text = "SYNTHETIC risk escalation evidence"
            raw = RawObservation(source_id="synthetic-risk-record-source", external_id="synthetic-risk-record-1", query="synthetic risk", item_type="NEWS", title="SYNTHETIC risk evidence", text=text, source_url="https://synthetic.invalid/risk", observed_at=datetime(2026, 8, 1, 12), acquisition_method="MOCK", evidence_quality="HIGH", acquisition_risk="LOW", content_hash=hashlib.sha256(text.encode()).hexdigest(), raw_payload={"data_class": "SYNTHETIC"})
            db.add(raw)
            db.flush()
            item = NormalizedItem(raw_observation_id=raw.id, canonical_key="synthetic-risk-record-item", source_id=raw.source_id, query=raw.query, item_type=raw.item_type, title=raw.title, text=raw.text, source_url=raw.source_url, observed_at=raw.observed_at)
            db.add(item)
            db.flush()
            db.add(OpportunityEvidence(opportunity_id=opportunity.id, normalized_item_id=item.id, evidence_type="RISK", observed_at=raw.observed_at))
        db.commit()
        return opportunity.id


def test_risk_record_persists_explanation_evidence_alert_and_is_idempotent():
    opportunity_id = _seed(with_evidence=True)
    with SessionLocal() as db:
        first = materialize_risk_escalations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        second = materialize_risk_escalations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
        record = db.scalar(select(RiskEscalationRecord).where(RiskEscalationRecord.opportunity_id == opportunity_id))
        event = db.scalar(select(AlertEvent).where(AlertEvent.opportunity_id == opportunity_id))
    assert first["created"] == 1
    assert first["alerts_created"] == 1
    assert second["duplicates"] == 1
    assert record is not None and record.delivery_status == "DELIVERED"
    assert record.status == "ESCALATED"
    assert record.current_level == "MEDIUM"
    assert record.change_breakdown["risk_score_delta"] == 35.0
    assert record.evidence_ids and record.evidence[0]["provenance"] == "SYNTHETIC"
    assert event is not None and record.alert_event_id == event.id
    assert "evidence_ids=ev1_" in event.message


def test_risk_record_fails_closed_without_evidence_and_persists_non_alert_states():
    missing_id = _seed(with_evidence=False)
    stable_id = _seed(with_evidence=False, stable=True)
    empty_id = _seed(with_evidence=False, with_previous=False)
    with SessionLocal() as db:
        result = materialize_risk_escalations(db, opportunity_ids={missing_id, stable_id, empty_id}, evaluated_at=NOW)
        db.commit()
        rows = db.scalars(select(RiskEscalationRecord).where(RiskEscalationRecord.opportunity_id.in_([missing_id, stable_id, empty_id]))).all()
        events = db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.opportunity_id.in_([missing_id, stable_id, empty_id])))
    by_opp = {row.opportunity_id: row for row in rows}
    assert result["evidence_missing"] == 1
    assert result["alerts_created"] == 0
    assert by_opp[missing_id].delivery_status == "REJECTED_NO_EVIDENCE"
    assert by_opp[stable_id].status == "STABLE" and by_opp[stable_id].delivery_status == "SUPPRESSED"
    assert by_opp[empty_id].status == "NO_BASELINE"
    assert events == 0


def test_risk_record_rollback_retries_and_api_requires_admin(monkeypatch):
    opportunity_id = _seed(with_evidence=True)
    with SessionLocal() as db:
        first = materialize_risk_escalations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        assert first["alerts_created"] == 1
        db.rollback()
        retry = materialize_risk_escalations(db, opportunity_ids={opportunity_id}, evaluated_at=NOW)
        db.commit()
    assert retry["created"] == 1
    assert retry["alerts_created"] == 1
    rows = client.get("/api/v1/alerts/risk/records", params={"opportunity_id": opportunity_id}).json()
    assert rows[0]["delivery_status"] == "DELIVERED"
    import app.core.security as security
    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    assert client.post("/api/v1/alerts/risk/evaluate", params={"opportunity_id": opportunity_id}).status_code == 401
