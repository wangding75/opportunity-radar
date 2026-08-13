from datetime import datetime, timedelta

import pytest

from app.domain.webhook import (
    WEBHOOK_MAX_PAYLOAD_BYTES,
    WebhookDataClass,
    WebhookEvent,
    WebhookEventType,
    WebhookSignature,
    build_webhook_headers,
    canonical_event_bytes,
    format_webhook_signature,
    parse_webhook_signature,
    sign_webhook_event,
    verify_webhook_signature,
)


SECRET = "synthetic-webhook-secret-0123456789"


def _event(**overrides):
    values = {
        "event_id": "evt_synthetic_001",
        "occurred_at": datetime(2026, 8, 12, 12),
        "data_class": WebhookDataClass.SYNTHETIC,
        "payload": {"alert_event_id": 1, "title": "SYNTHETIC alert", "score": 88},
    }
    values.update(overrides)
    return WebhookEvent(**values)


def test_event_contract_canonicalizes_and_signs_deterministically():
    event = _event()
    reordered = _event(payload={"score": 88, "title": "SYNTHETIC alert", "alert_event_id": 1})
    assert event.event_type == WebhookEventType.ALERT_EVENT
    assert canonical_event_bytes(event) == canonical_event_bytes(reordered)
    signature = sign_webhook_event(event, SECRET, timestamp=1_800_000_000, delivery_id="del_synthetic_001", nonce="nonce_001")
    header = format_webhook_signature(signature)
    assert parse_webhook_signature(header) == signature
    assert verify_webhook_signature(canonical_event_bytes(event), SECRET, header, now=datetime.fromtimestamp(1_800_000_000))
    assert build_webhook_headers(event, SECRET, signature=signature)["X-Webhook-Event"] == "alert.event"


def test_signature_rejects_tampering_replay_and_wrong_delivery_id():
    event = _event()
    signature = sign_webhook_event(event, SECRET, timestamp=1_800_000_000, delivery_id="del_synthetic_002", nonce="nonce_002")
    header = format_webhook_signature(signature)
    assert not verify_webhook_signature(canonical_event_bytes(_event(payload={"changed": True})), SECRET, header, now=datetime.fromtimestamp(1_800_000_000))
    assert not verify_webhook_signature(canonical_event_bytes(event), "wrong-secret-0123456789", header, now=datetime.fromtimestamp(1_800_000_000))
    assert not verify_webhook_signature(canonical_event_bytes(event), SECRET, header, expected_delivery_id="del_other", now=datetime.fromtimestamp(1_800_000_000))
    assert not verify_webhook_signature(canonical_event_bytes(event), SECRET, header, now=datetime.fromtimestamp(1_800_000_000) + timedelta(seconds=301))
    assert verify_webhook_signature(canonical_event_bytes(event), SECRET, header, now=datetime.fromtimestamp(1_800_000_000) + timedelta(seconds=300))


def test_contract_rejects_unsafe_headers_secrets_ids_and_oversize_payloads():
    with pytest.raises(ValueError, match="at least 16"):
        sign_webhook_event(_event(), "short")
    with pytest.raises(ValueError, match="unsupported"):
        _event(event_id="bad event")
    with pytest.raises(ValueError, match="payload exceeds"):
        _event(payload={"text": "x" * WEBHOOK_MAX_PAYLOAD_BYTES})
    with pytest.raises(ValueError, match="CR/LF"):
        sign_webhook_event(_event(), SECRET + "\n", timestamp=1_800_000_000)
    with pytest.raises(ValueError):
        parse_webhook_signature("t=1,t=2,d=del_12345678,n=nonce123,v1=" + "0" * 64)
    assert not verify_webhook_signature(b"{}", SECRET, "t=1,d=del_12345678,n=nonce123,v1=" + "0" * 64, now=datetime.fromtimestamp(1))
