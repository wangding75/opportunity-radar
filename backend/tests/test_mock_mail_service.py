from datetime import datetime

from fastapi.testclient import TestClient

from app.domain.email_delivery import EmailTemplate, build_email_request
from app.mock_mail_service import app, mail
from app.services.mock_mail import MockMailService


client = TestClient(app)


def _request(*, metadata: dict[str, str] | None = None):
    return build_email_request(
        message_id="synthetic-alert-1",
        idempotency_key="synthetic-alert-1:v1",
        recipients=["recipient@example.com"],
        template=EmailTemplate(name="synthetic.alert", version="v1", subject="SYNTHETIC alert", text_body="SYNTHETIC message"),
        context={},
        requested_at=datetime(2026, 8, 12, 12),
        metadata={"data_class": "SYNTHETIC", **(metadata or {})},
    ).model_dump(mode="json")


def setup_function():
    mail.reset()


def test_mock_mail_sends_marks_mock_and_deduplicates_side_effects():
    first = client.post("/v1/send", json=_request())
    second = client.post("/v1/send", json=_request())
    assert first.status_code == second.status_code == 200
    assert first.json()["data_class"] == "MOCK"
    assert first.json()["result"]["status"] == "SENT"
    assert first.json()["result"]["provider_message_id"] == second.json()["result"]["provider_message_id"]
    messages = client.get("/v1/messages").json()
    assert len(messages) == 1
    assert messages[0]["data_class"] == "MOCK"
    assert messages[0]["text_body"] == "SYNTHETIC message"


def test_mock_mail_exposes_transient_permanent_and_suppressed_failure_modes():
    transient = client.post("/v1/send", json=_request(metadata={"_mock_failure": "transient"}))
    assert transient.json()["result"]["status"] == "RETRYABLE_FAILURE"
    assert transient.json()["result"]["next_retry_at"] is not None
    limited = client.post("/v1/send", headers={"X-Mock-Failure": "rate_limited"}, json=_request(metadata={"id": "rate"}))
    assert limited.json()["result"]["failure_kind"] == "RATE_LIMITED"
    permanent = client.post("/v1/send", headers={"X-Mock-Failure": "permanent"}, json=_request(metadata={"id": "permanent"}))
    assert permanent.json()["result"]["status"] == "PERMANENT_FAILURE"
    suppressed = client.post("/v1/send", headers={"X-Mock-Failure": "suppressed"}, json=_request(metadata={"id": "suppressed"}))
    assert suppressed.json()["result"]["status"] == "SUPPRESSED"
    assert client.get("/v1/messages").json() == []


def test_mock_mail_rejects_invalid_requests_and_reset_is_explicit():
    assert client.post("/v1/send", json={**_request(), "recipients": []}).status_code == 422
    assert client.post("/v1/send", json={**_request(), "subject": "bad\nsubject"}).status_code == 422
    assert client.get("/health").json() == {"status": "ok", "provider": "mock-mail", "data_class": "MOCK", "version": "mock-mail-v1"}
    client.post("/v1/send", json=_request())
    assert client.post("/v1/reset").json() == {"status": "reset", "data_class": "MOCK"}
    assert client.get("/v1/messages").json() == []


def test_mock_mail_service_respects_bounds_and_provider_port_shape():
    service = MockMailService(max_messages=1)
    request = build_email_request(message_id="one", idempotency_key="one", recipients=["a@example.com"], template=EmailTemplate(name="one", version="v1", subject="one", text_body="one"), context={})
    result = service.send(request)
    assert result.status == "SENT"
    assert service.messages(limit=1)[0]["provider_message_id"] == result.provider_message_id
    try:
        service.messages(limit=501)
    except ValueError as exc:
        assert "between 1 and 500" in str(exc)
    else:
        raise AssertionError("message query limit must be bounded")
