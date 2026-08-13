import time

from fastapi.testclient import TestClient

from app.domain.webhook import WebhookDataClass, WebhookEvent, build_webhook_headers, canonical_event_bytes, sign_webhook_event
from app import mock_webhook_service as receiver


SECRET = "synthetic-webhook-secret-0123456789"
client = TestClient(receiver.app)


def _request(*, delivery_id: str = "del_synthetic_mock_1", secret: str = SECRET):
    event = WebhookEvent(event_id="evt_synthetic_mock_1", data_class=WebhookDataClass.SYNTHETIC, payload={"value": "MOCK"})
    signature = sign_webhook_event(event, secret, timestamp=int(time.time()), delivery_id=delivery_id, nonce="nonce_synthetic_mock_1")
    headers = build_webhook_headers(event, secret, signature=signature)
    return event, headers, canonical_event_bytes(event)


def setup_function():
    receiver.store.reset()


def test_health_declares_mock_signature_and_idempotency_contract():
    body = client.get("/health").json()
    assert body["data_class"] == "MOCK"
    assert body["signature_verification"] == "enabled"
    assert body["idempotency"] == "delivery_id"


def test_receiver_verifies_signature_and_deduplicates_delivery_id():
    event, headers, payload = _request()
    first = client.post("/v1/hooks", content=payload, headers=headers)
    second = client.post("/v1/hooks", content=payload, headers=headers)
    assert first.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    messages = client.get("/v1/messages").json()
    assert len(messages) == 1
    assert messages[0]["data_class"] == "MOCK"
    assert messages[0]["event_data_class"] == "SYNTHETIC"
    assert messages[0]["event_id"] == event.event_id


def test_receiver_rejects_bad_signature_and_mismatched_delivery_id():
    _, headers, payload = _request()
    bad = dict(headers)
    signature = bad["X-Webhook-Signature"]
    bad["X-Webhook-Signature"] = f"{signature[:-1]}{'0' if signature[-1] != '0' else '1'}"
    assert client.post("/v1/hooks", content=payload, headers=bad).status_code == 400
    mismatch = dict(headers)
    mismatch["X-Webhook-Delivery-ID"] = "del_synthetic_mock_2"
    assert client.post("/v1/hooks", content=payload, headers=mismatch).status_code == 400


def test_receiver_exposes_controlled_mock_failures(monkeypatch):
    _, headers, payload = _request(delivery_id="del_synthetic_mock_failure")
    monkeypatch.setenv("MOCK_WEBHOOK_FAILURE_MODE", "retryable")
    assert client.post("/v1/hooks", content=payload, headers=headers).status_code == 503
    monkeypatch.setenv("MOCK_WEBHOOK_FAILURE_MODE", "permanent")
    assert client.post("/v1/hooks", content=payload, headers=headers).status_code == 422
    monkeypatch.delenv("MOCK_WEBHOOK_FAILURE_MODE", raising=False)
