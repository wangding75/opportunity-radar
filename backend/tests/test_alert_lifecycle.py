import uuid

from fastapi.testclient import TestClient

from app.db.models import AlertEvent
from app.db.session import SessionLocal
from app.domain.alert_lifecycle import (
    AlertPriority,
    derive_alert_priority,
    validate_alert_status_transition,
)
from app.main import app


client = TestClient(app)


def _seed_event() -> dict:
    imported = client.post(
        "/api/v1/import",
        json={
            "records": [
                {"source_id": "synthetic-a", "query": "alert lifecycle", "item_type": "PRODUCT", "title": "Synthetic alert product", "text": "MOCK demand"},
                {"source_id": "synthetic-b", "query": "alert lifecycle", "item_type": "JOB", "title": "Synthetic alert job", "text": "MOCK demand"},
            ]
        },
    )
    assert imported.status_code == 200
    opportunity = client.get("/api/v1/opportunities", params={"min_score": 0}).json()[0]
    rule = client.post(
        "/api/v1/alerts/rules",
        json={"name": f"lifecycle-{uuid.uuid4().hex}", "min_score": 0, "max_risk_score": 100, "min_evidence_count": 1},
    )
    assert rule.status_code == 200
    assert client.post("/api/v1/alerts/evaluate").status_code == 200
    events = client.get("/api/v1/alerts/events", params={"limit": 100}).json()
    return next(row for row in events if row["opportunity_id"] == opportunity["id"] and row["status"] == "NEW")


def test_priority_and_transition_contract_boundaries():
    assert derive_alert_priority(score=80, risk_score=40, evidence_count=3) == AlertPriority.HIGH.value
    assert derive_alert_priority(score=90, risk_score=30, evidence_count=5) == AlertPriority.CRITICAL.value
    assert derive_alert_priority(score=59, risk_score=0, evidence_count=99) == AlertPriority.INFO.value
    assert validate_alert_status_transition("NEW", "ACKNOWLEDGED") == ("NEW", "ACKNOWLEDGED")
    assert validate_alert_status_transition("ACKNOWLEDGED", "RESOLVED") == ("ACKNOWLEDGED", "RESOLVED")

    try:
        validate_alert_status_transition("RESOLVED", "ACKNOWLEDGED")
    except ValueError as exc:
        assert "cannot transition" in str(exc)
    else:
        raise AssertionError("terminal alert state must not be reopenable")


def test_ack_lifecycle_is_idempotent_and_auditable():
    event = _seed_event()
    assert 1 <= event["priority"] <= 5

    acknowledged = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert acknowledged.status_code == 200
    first = acknowledged.json()
    assert first["status"] == "ACKNOWLEDGED"
    assert first["acknowledged_at"] is not None
    assert first["acknowledged_by"] == "local"

    repeated = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert repeated.status_code == 200
    assert repeated.json()["acknowledged_at"] == first["acknowledged_at"]
    assert repeated.json()["acknowledged_by"] == first["acknowledged_by"]

    resolved = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "RESOLVED"})
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None
    assert resolved.json()["resolved_by"] == "local"

    reopened = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "ACKNOWLEDGED"})
    assert reopened.status_code == 422


def test_dismissal_records_actor_and_is_terminal():
    event = _seed_event()
    dismissed = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "DISMISSED"})
    assert dismissed.status_code == 200
    assert dismissed.json()["dismissed_at"] is not None
    assert dismissed.json()["dismissed_by"] == "local"

    same = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "DISMISSED"})
    assert same.status_code == 200
    assert same.json()["dismissed_at"] == dismissed.json()["dismissed_at"]

    with SessionLocal() as db:
        row = db.get(AlertEvent, event["id"])
        assert row is not None
        assert row.status == "DISMISSED"
        assert row.dismissed_by == "local"

    invalid = client.patch(f"/api/v1/alerts/events/{event['id']}", json={"status": "RESOLVED"})
    assert invalid.status_code == 422
