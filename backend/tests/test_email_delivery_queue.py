from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core import security
from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, EmailDeliveryRecord
from app.db.session import SessionLocal
from app.domain.email_delivery import EmailDeliveryStatus, EmailFailureKind, build_delivery_result
from app.main import app
from app.services.email_delivery_queue import (
    QUEUE_RETRY_POLICY,
    claim_email_deliveries,
    enqueue_alert_emails,
    process_email_delivery_queue,
)


client = TestClient(app)


def _seed_event(*, status: str = "NEW") -> int:
    now = utc_now()
    with SessionLocal() as db:
        rule = AlertRule(
            name=f"synthetic-email-rule-{now.timestamp()}",
            enabled=True,
            min_score=0,
            max_risk_score=100,
            min_evidence_count=1,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=1440,
            created_at=now,
            updated_at=now,
        )
        db.add(rule)
        db.flush()
        event = AlertEvent(
            alert_rule_id=rule.id,
            event_key=f"synthetic-email-event-{now.timestamp()}",
            status=status,
            priority=3,
            title="SYNTHETIC opportunity alert",
            message="SYNTHETIC queue test message",
            score=88,
            risk_score=22,
            created_at=now,
        )
        db.add(event)
        db.commit()
        return event.id


def _enqueue(event_id: int, *, now: datetime | None = None) -> int:
    with SessionLocal() as db:
        result = enqueue_alert_emails(
            db,
            alert_event_ids={event_id},
            recipients=["Recipient@example.com"],
            data_class="SYNTHETIC",
            now=now or utc_now(),
        )
        db.commit()
        assert result["created"] == 1
        return result["records"][0]["id"]


def test_enqueue_is_idempotent_and_empty_selection_is_a_noop():
    event_id = _seed_event()
    fixed_now = datetime(2026, 8, 12, 12)
    with SessionLocal() as db:
        first = enqueue_alert_emails(
            db,
            alert_event_ids={event_id},
            recipients=["recipient@example.com"],
            data_class="SYNTHETIC",
            now=fixed_now,
        )
        db.commit()
        second = enqueue_alert_emails(
            db,
            alert_event_ids={event_id},
            recipients=["RECIPIENT@example.com"],
            data_class="SYNTHETIC",
            now=fixed_now + timedelta(hours=1),
        )
        empty = enqueue_alert_emails(
            db,
            alert_event_ids=set(),
            recipients=["recipient@example.com"],
            data_class="SYNTHETIC",
        )
        assert first["created"] == 1
        assert second["duplicates"] == 1
        assert second["created"] == 0
        assert empty["selected"] == 0
        assert db.scalar(select(EmailDeliveryRecord.alert_event_id)) == event_id


def test_mock_port_processes_queue_once_and_keeps_audit_fields():
    event_id = _seed_event()
    record_id = _enqueue(event_id)
    with SessionLocal() as db:
        result = process_email_delivery_queue(db, limit=10)
        row = db.get(EmailDeliveryRecord, record_id)
        assert result["claimed"] == result["processed"] == 1
        assert result["sent"] == 1
        assert row is not None
        assert row.status == "SENT"
        assert row.attempt_count == 1
        assert row.provider_message_id.startswith("mock-msg-")
        assert row.sent_at is not None
        assert row.request_payload["metadata"]["data_class"] == "SYNTHETIC"
        assert process_email_delivery_queue(db)["processed"] == 0


class FailOncePort:
    def __init__(self):
        self.calls = 0

    def send(self, request):
        self.calls += 1
        if self.calls == 1:
            return build_delivery_result(
                request,
                status=EmailDeliveryStatus.RETRYABLE_FAILURE,
                attempt=1,
                failure_kind=EmailFailureKind.TRANSIENT_PROVIDER,
                error_code="SYNTHETIC_TRANSIENT",
                error_detail="SYNTHETIC first attempt",
                now=datetime(2026, 8, 12, 12),
                policy=QUEUE_RETRY_POLICY,
            )
        return build_delivery_result(
            request,
            status=EmailDeliveryStatus.SENT,
            attempt=2,
            provider_message_id="synthetic-provider-message-2",
            now=datetime(2026, 8, 12, 12, 1),
            policy=QUEUE_RETRY_POLICY,
        )


def test_transient_failure_retries_after_due_time_and_lease_expiry_is_reclaimable():
    event_id = _seed_event()
    record_id = _enqueue(event_id, now=datetime(2026, 8, 12, 12))
    port = FailOncePort()
    with SessionLocal() as db:
        first = process_email_delivery_queue(db, port=port, now=datetime(2026, 8, 12, 12))
        row = db.get(EmailDeliveryRecord, record_id)
        assert first["retry_wait"] == 1
        assert row.status == "RETRY_WAIT"
        assert row.next_retry_at is not None
        row.next_retry_at = datetime(2026, 8, 12, 11, 59)
        db.commit()
        second = process_email_delivery_queue(db, port=port, now=datetime(2026, 8, 12, 12, 2))
        assert second["sent"] == 1
        assert db.get(EmailDeliveryRecord, record_id).status == "SENT"

    event_id = _seed_event()
    record_id = _enqueue(event_id, now=datetime(2026, 8, 12, 12))
    with SessionLocal() as db:
        claimed = claim_email_deliveries(db, now=datetime(2026, 8, 12, 12))
        assert [row.id for row in claimed] == [record_id]
        row = db.get(EmailDeliveryRecord, record_id)
        row.claim_until = datetime(2026, 8, 12, 11, 59)
        db.commit()
        reclaimed = claim_email_deliveries(db, now=datetime(2026, 8, 12, 12, 1))
        assert [row.id for row in reclaimed] == [record_id]
        assert reclaimed[0].attempt_count == 2


class AlwaysRaisesPort:
    def send(self, request):
        raise RuntimeError("SYNTHETIC provider outage")


def test_provider_exception_is_retryable_then_permanent_at_attempt_boundary():
    event_id = _seed_event()
    record_id = _enqueue(event_id)
    with SessionLocal() as db:
        row = db.get(EmailDeliveryRecord, record_id)
        row.attempt_count = QUEUE_RETRY_POLICY.max_attempts - 1
        row.next_retry_at = utc_now()
        db.commit()
        result = process_email_delivery_queue(db, port=AlwaysRaisesPort())
        row = db.get(EmailDeliveryRecord, record_id)
        assert result["failed"] == 1
        assert row.status == "PERMANENT_FAILURE"
        assert row.error_code == "RETRY_EXHAUSTED"
        assert row.provider_message_id is None


def test_email_queue_api_and_admin_boundary(monkeypatch):
    event_id = _seed_event()
    response = client.post(
        "/api/v1/alerts/email/enqueue",
        json={"alert_event_ids": [event_id], "recipients": ["recipient@example.com"], "data_class": "SYNTHETIC"},
    )
    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert client.post("/api/v1/alerts/email/process", json={"limit": 10}).status_code == 200
    rows = client.get("/api/v1/alerts/email/records", params={"alert_event_id": event_id}).json()
    assert rows[0]["status"] == "SENT"
    assert client.post("/api/v1/alerts/email/enqueue", json={"alert_event_ids": [event_id], "recipients": []}).status_code == 422

    original = security.settings
    monkeypatch.setattr(security, "settings", replace(original, auth_mode="rbac", api_key=None, allow_legacy_api_key=False))
    try:
        forbidden = client.post(
            "/api/v1/alerts/email/enqueue",
            json={"alert_event_ids": [event_id], "recipients": ["recipient@example.com"]},
        )
        assert forbidden.status_code == 401
    finally:
        monkeypatch.setattr(security, "settings", original)
