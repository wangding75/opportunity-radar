from datetime import datetime

import httpx

from app.domain.email_delivery import EmailDeliveryStatus, EmailTemplate, build_email_request
from app.services.mock_mail_http import MockMailHTTPConfig, MockMailHTTPService


def _request():
    return build_email_request(
        message_id="synthetic-http-mail",
        idempotency_key="synthetic-http-mail:v1",
        recipients=["recipient@example.com"],
        template=EmailTemplate(name="synthetic.http", version="v1", subject="SYNTHETIC", text_body="SYNTHETIC"),
        context={},
        requested_at=datetime(2026, 8, 12, 12),
        metadata={"data_class": "SYNTHETIC"},
    )


def test_mock_mail_http_accepts_labeled_mock_result(monkeypatch):
    request = _request()

    def post(url, **kwargs):
        assert url == "http://mock-mail:8082/v1/send"
        assert kwargs["json"]["metadata"]["data_class"] == "SYNTHETIC"
        return httpx.Response(
            200,
            json={
                "data_class": "MOCK",
                "result": {
                    "status": "SENT",
                    "message_id": request.message_id,
                    "idempotency_key": request.idempotency_key,
                    "input_signature": "0" * 64,
                    "provider_message_id": "mock-http-1",
                    "attempt": 1,
                    "observed_at": "2026-08-12T12:00:00",
                },
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", post)
    result = MockMailHTTPService(MockMailHTTPConfig("http://mock-mail:8082")).send(request)
    assert result.status == EmailDeliveryStatus.SENT
    assert result.provider_message_id == "mock-http-1"


def test_mock_mail_http_maps_network_and_bad_response_failures(monkeypatch):
    request = _request()
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ConnectError("SYNTHETIC unavailable")))
    retry = MockMailHTTPService(MockMailHTTPConfig("http://mock-mail:8082")).send(request)
    assert retry.status == EmailDeliveryStatus.RETRYABLE_FAILURE

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: httpx.Response(200, json={"data_class": "OBSERVED", "result": {}}))
    invalid = MockMailHTTPService(MockMailHTTPConfig("http://mock-mail:8082")).send(request)
    assert invalid.status == EmailDeliveryStatus.PERMANENT_FAILURE
    assert invalid.error_code == "MOCK_MAIL_INVALID_RESPONSE"
