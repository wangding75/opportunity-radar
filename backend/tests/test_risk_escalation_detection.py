from datetime import datetime
from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.db.models import Keyword, Opportunity, OpportunityScoreSnapshot
from app.db.session import SessionLocal
from app.domain.risk_escalation import RiskEscalationStatus
from app.main import app
from app.services.risk_escalation import detect_risk_escalations


client = TestClient(app)


def _seed(*, dormant: bool = False, with_previous: bool = True) -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical=f"synthetic-risk-detection-{dormant}-{with_previous}", display_name="SYNTHETIC Risk Detection", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(opportunity_key=f"synthetic-risk-detection-{dormant}-{with_previous}", keyword_id=keyword.id, title="SYNTHETIC risk detection opportunity", stage="DORMANT" if dormant else "VALIDATED", risk_score=50.0)
        db.add(opportunity)
        db.flush()
        if with_previous:
            db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="risk-v1", input_signature="a" * 64, score=70.0, risk_score=20.0, stage="DISCOVERY", evidence_count=1, breakdown={"data_class": "SYNTHETIC", "risk": 20}, calculated_at=datetime(2026, 8, 1)))
        db.add(OpportunityScoreSnapshot(opportunity_id=opportunity.id, model_version="risk-v1", input_signature="b" * 64, score=70.0, risk_score=55.0, stage="VALIDATED", evidence_count=2, breakdown={"data_class": "SYNTHETIC", "risk": 55}, calculated_at=datetime(2026, 8, 2)))
        db.commit()
        return opportunity.id


def test_detection_matches_escalation_rule_and_is_read_only_and_stable():
    opportunity_id = _seed()
    with SessionLocal() as db:
        before = db.scalar(select(func.count(OpportunityScoreSnapshot.id)))
        first = detect_risk_escalations(db, opportunity_ids={opportunity_id}, evaluated_at=datetime(2026, 8, 12))
        second = detect_risk_escalations(db, opportunity_ids={opportunity_id}, evaluated_at=datetime(2026, 8, 13))
        after = db.scalar(select(func.count(OpportunityScoreSnapshot.id)))
    assert len(first) == len(second) == 1
    assert first[0].status == RiskEscalationStatus.ESCALATED
    assert first[0].escalated is True
    assert first[0].input_signature == second[0].input_signature
    assert before == after


def test_detection_handles_empty_filters_single_snapshot_and_dormant_opportunities():
    empty_id = _seed(with_previous=False)
    dormant_id = _seed(dormant=True)
    with SessionLocal() as db:
        assert detect_risk_escalations(db, opportunity_ids=set()) == []
        assert detect_risk_escalations(db, opportunity_ids={empty_id})[0].status == RiskEscalationStatus.NO_BASELINE
        assert detect_risk_escalations(db, opportunity_ids={dormant_id}) == []
        assert detect_risk_escalations(db, opportunity_ids={empty_id}, escalated_only=True) == []


def test_detection_limit_and_api_rbac_boundary(monkeypatch):
    opportunity_id = _seed()
    with SessionLocal() as db:
        try:
            detect_risk_escalations(db, limit=101)
        except ValueError as exc:
            assert "between 1 and 100" in str(exc)
        else:
            raise AssertionError("risk detection must enforce its upper bound")
    response = client.get("/api/v1/risk/escalations", params={"opportunity_id": opportunity_id, "escalated_only": "true"})
    assert response.status_code == 200
    assert response.json()[0]["status"] == "ESCALATED"
    import app.core.security as security
    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    assert client.get("/api/v1/risk/escalations").status_code == 401
