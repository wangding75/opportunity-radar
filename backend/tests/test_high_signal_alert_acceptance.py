from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.time import utc_now
from app.db.models import Keyword, Opportunity
from app.db.session import SessionLocal
from app.domain.citations import CITATION_CONTRACT_VERSION, evidence_id_for_row
from app.main import app
from app.mock_analysis_service import app as mock_analysis_app
from app.services.alerts import enqueue_alert_evaluations
from app.worker import run_once


client = TestClient(app)
mock_client = TestClient(mock_analysis_app)


def test_mock_failure_is_explicit_and_never_fabricates_analysis():
    response = mock_client.post(
        "/v1/analyze",
        headers={"X-Mock-Failure": "true"},
        json={"schema_version": "1", "citation_contract_version": CITATION_CONTRACT_VERSION, "opportunity": {"evidence": [{"evidence_id": "ev1_" + "a" * 64}]}} ,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "MOCK external provider failure"


def test_mock_driven_high_signal_alert_reaches_api_and_ack():
    evidence = {"source": "synthetic-mock", "type": "DEMAND", "title": "MOCK high signal evidence", "text": "SYNTHETIC acceptance fixture"}
    evidence_id = evidence_id_for_row(evidence)
    mock_response = mock_client.post(
        "/v1/analyze",
        json={
            "schema_version": "1",
            "citation_contract_version": CITATION_CONTRACT_VERSION,
            "opportunity": {
                "title": "MOCK high signal opportunity",
                "related_keywords": ["synthetic-alert"],
                "evidence": [{"evidence_id": evidence_id, **evidence}],
            },
        },
    )
    assert mock_response.status_code == 200
    mock_body = mock_response.json()
    assert mock_body["data_class"] == "MOCK"
    assert mock_body["citations"] == [{"evidence_id": evidence_id, "claim": "MOCK synthetic evidence reference: MOCK high signal evidence"}]

    now = utc_now()
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-alert", display_name="Synthetic Alert", status="ACTIVE")
        db.add(keyword)
        db.flush()
        opportunity = Opportunity(
            opportunity_key="opp:synthetic-mock-high-signal",
            keyword_id=keyword.id,
            title="MOCK high signal opportunity",
            stage="VALIDATING",
            score=92,
            risk_score=20,
            evidence_count=5,
            cross_source_score=7,
            analysis_status="READY",
            analysis_provider="mock",
            analysis_signature="m" * 64,
            summary=mock_body["summary"],
            analysis_citations=mock_body["citations"],
            updated_at=now,
            last_seen_at=now,
            first_seen_at=now - timedelta(hours=1),
        )
        db.add(opportunity)
        db.flush()
        enqueue_alert_evaluations(db, {opportunity.id}, reason="MOCK_HIGH_SIGNAL_ACCEPTANCE")
        db.commit()
        opportunity_id = opportunity.id

    worker_result = run_once(sync=False, limit=1, mode="alerts", worker_id="synthetic-mock-alert-worker")
    assert worker_result["alerts"]["processed"] == 1
    assert worker_result["alerts"]["created"] == 1
    assert worker_result["alerts"]["failed"] == 0

    events = client.get("/api/v1/alerts/events", params={"limit": 100}).json()
    matching = [row for row in events if row["opportunity_id"] == opportunity_id]
    assert len(matching) == 1
    event = matching[0]
    assert event["status"] == "NEW"
    assert event["priority"] == 5
    assert "MOCK high signal opportunity" in event["title"]
    assert "dedupe_key=" in event["message"]

    duplicate_worker_result = run_once(sync=False, limit=1, mode="alerts", worker_id="synthetic-mock-alert-worker")
    assert duplicate_worker_result["alerts"]["processed"] == 0
    assert client.get("/api/v1/alerts/events", params={"limit": 100}).json() == events

    acknowledged = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "ACKNOWLEDGED"
    assert acknowledged.json()["acknowledged_at"] is not None
