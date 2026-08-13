from dataclasses import replace
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core import security
from app.db.models import AlertEvent, AlertRule, WebhookDeliveryRecord, WebhookEndpoint
from app.db.session import SessionLocal
from app.domain.webhook import WebhookDeliveryResult, WebhookDeliveryStatus, WebhookFailureKind
from app.main import app
from app.services.webhook_delivery_queue import (
    claim_webhook_deliveries,
    enqueue_alert_webhooks,
    process_webhook_delivery_queue,
)


client = TestClient(app)
SECRET = "synthetic-webhook-secret-0123456789"


def _seed_event(*, status: str = "NEW") -> int:
    now = datetime(2026, 8, 12, 12)
    with SessionLocal() as db:
        suffix = len(db.scalars(select(AlertEvent.id)).all())
        rule = AlertRule(
            name=f"synthetic-webhook-rule-{now.timestamp()}-{status}-{suffix}", enabled=True, min_score=0, max_risk_score=100,
            min_evidence_count=1, stages=[], keyword_contains=[], cooldown_minutes=1440, created_at=now, updated_at=now,
        )
        db.add(rule)
        db.flush()
        event = AlertEvent(
            alert_rule_id=rule.id, event_key=f"synthetic-webhook-event-{now.timestamp()}-{status}-{suffix}", status=status,
            priority=2, title="SYNTHETIC webhook alert", message="SYNTHETIC webhook queue test", score=91,
            risk_score=11, created_at=now,
        )
        db.add(event)
        db.commit()
        return event.id


def _seed_endpoint(*, enabled: bool = True) -> int:
    with SessionLocal() as db:
        row = WebhookEndpoint(
            name=f"synthetic-webhook-endpoint-{len(db.scalars(select(WebhookEndpoint.id)).all())}",
            url="https://receiver.synthetic.invalid/hook",
            secret=SECRET,
            secret_fingerprint="a" * 64,
            event_types=["alert.event"],
            enabled=enabled,
            description="SYNTHETIC receiver",
            created_at=datetime(2026, 8, 12, 12),
            updated_at=datetime(2026, 8, 12, 12),
        )
        db.add(row)
        db.commit()
        return row.id


class RecordingPort:
    def __init__(self, *, fail_once: bool = False):
        self.calls = []
        self.fail_once = fail_once

    def send(self, request, *, endpoint_url, headers, body):
        self.calls.append((request, endpoint_url, headers, body))
        if self.fail_once and len(self.calls) == 1:
            return WebhookDeliveryResult(
                status=WebhookDeliveryStatus.RETRYABLE_FAILURE,
                attempt=request.attempt,
                http_status=503,
                failure_kind=WebhookFailureKind.TRANSIENT_NETWORK,
                error_code="SYNTHETIC_TRANSIENT",
                error_detail="SYNTHETIC first attempt",
                next_retry_at=datetime(2026, 8, 12, 12, 1),
            )
        return WebhookDeliveryResult(
            status=WebhookDeliveryStatus.SENT,
            attempt=request.attempt,
            http_status=202,
            provider_message_id="synthetic-receipt",
            observed_at=datetime(2026, 8, 12, 12, 2),
        )


def test_enqueue_is_per_endpoint_idempotent_and_never_serializes_secret():
    event_id = _seed_event()
    endpoint_id = _seed_endpoint()
    with SessionLocal() as db:
        first = enqueue_alert_webhooks(db, alert_event_ids={event_id}, endpoint_ids={endpoint_id}, data_class="SYNTHETIC", now=datetime(2026, 8, 12, 12))
        db.commit()
        second = enqueue_alert_webhooks(db, alert_event_ids={event_id}, endpoint_ids={endpoint_id}, data_class="SYNTHETIC", now=datetime(2026, 8, 12, 13))
        assert first["created"] == 1
        assert second["duplicates"] == 1
        assert SECRET not in str(first)
        row = db.scalar(select(WebhookDeliveryRecord).where(WebhookDeliveryRecord.alert_event_id == event_id))
        assert row is not None
        assert SECRET not in (row.event_payload or {})


def test_successful_delivery_is_signed_and_second_process_is_idempotent():
    event_id = _seed_event()
    endpoint_id = _seed_endpoint()
    with SessionLocal() as db:
        result = enqueue_alert_webhooks(db, alert_event_ids={event_id}, endpoint_ids={endpoint_id}, data_class="SYNTHETIC", now=datetime(2026, 8, 12, 12))
        db.commit()
        record_id = result["records"][0]["id"]
        port = RecordingPort()
        processed = process_webhook_delivery_queue(db, port=port, now=datetime(2026, 8, 12, 12))
        row = db.get(WebhookDeliveryRecord, record_id)
        assert processed["sent"] == 1
        assert row.status == "SENT"
        assert row.attempt_count == 1
        assert row.signature_header.startswith("t=") and ",d=del_alert_" in row.signature_header
        assert row.request_body and '"data_class":"SYNTHETIC"' in row.request_body
        assert len(port.calls) == 1
        assert port.calls[0][2]["X-Webhook-Signature"] == row.signature_header
        assert process_webhook_delivery_queue(db, port=port, now=datetime(2026, 8, 12, 12, 1))["processed"] == 0


def test_transient_failure_retries_after_due_time_and_expired_lease_is_reclaimable():
    event_id = _seed_event()
    endpoint_id = _seed_endpoint()
    port = RecordingPort(fail_once=True)
    with SessionLocal() as db:
        enqueue_alert_webhooks(db, alert_event_ids={event_id}, endpoint_ids={endpoint_id}, data_class="SYNTHETIC", now=datetime(2026, 8, 12, 12))
        db.commit()
        first = process_webhook_delivery_queue(db, port=port, now=datetime(2026, 8, 12, 12))
        row = db.scalar(select(WebhookDeliveryRecord).where(WebhookDeliveryRecord.alert_event_id == event_id))
        assert first["retry_wait"] == 1
        assert row.status == "RETRY_WAIT"
        second = process_webhook_delivery_queue(db, port=port, now=datetime(2026, 8, 12, 12, 1))
        assert second["sent"] == 1
        assert row.status == "SENT"

        event_id = _seed_event()
        enqueue_alert_webhooks(db, alert_event_ids={event_id}, endpoint_ids={endpoint_id}, now=datetime(2026, 8, 12, 12))
        db.commit()
        claimed = claim_webhook_deliveries(db, now=datetime(2026, 8, 12, 12))
        claimed[0].claim_until = datetime(2026, 8, 12, 11, 59)
        db.commit()
        reclaimed = claim_webhook_deliveries(db, now=datetime(2026, 8, 12, 12, 1))
        assert reclaimed[0].attempt_count == 2


def test_disabled_endpoint_is_suppressed_and_api_mutations_require_admin(monkeypatch):
    event_id = _seed_event()
    endpoint_id = _seed_endpoint(enabled=False)
    with SessionLocal() as db:
        result = enqueue_alert_webhooks(db, alert_event_ids={event_id}, endpoint_ids={endpoint_id}, data_class="SYNTHETIC")
        db.commit()
        assert result["created"] == 0

    original = security.settings
    monkeypatch.setattr(security, "settings", replace(original, auth_mode="rbac", api_key=None, allow_legacy_api_key=False))
    try:
        response = client.post("/api/v1/alerts/webhooks/enqueue", json={"alert_event_ids": [event_id], "endpoint_ids": [endpoint_id], "data_class": "SYNTHETIC"})
        assert response.status_code == 401
    finally:
        monkeypatch.setattr(security, "settings", original)
