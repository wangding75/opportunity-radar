from datetime import datetime

import httpx
from fastapi.testclient import TestClient

from app.domain.enterprise_messaging import EnterpriseMessageRequest, EnterpriseMessageStatus
from app.mock_enterprise_messaging_service import app, messaging
from app.services.mock_enterprise_messaging import MockEnterpriseMessagingService
from app.services.mock_enterprise_messaging_http import MockEnterpriseMessagingHTTPConfig, MockEnterpriseMessagingHTTPService


client = TestClient(app)


def _request(**metadata):
    return EnterpriseMessageRequest(
        message_id="msg_synthetic_mock_1",
        idempotency_key="idem_synthetic_mock_1",
        provider="mock",
        destination="synthetic-channel",
        title="SYNTHETIC enterprise alert",
        text="SYNTHETIC enterprise message",
        data_class="SYNTHETIC",
        metadata={"data_class": "SYNTHETIC", **metadata},
        requested_at=datetime(2026, 8, 12, 12),
    )


def setup_function():
    messaging.reset()


def test_mock_enterprise_service_sends_labeled_message_and_deduplicates():
    first = client.post("/v1/send", json=_request().model_dump(mode="json"))
    second = client.post("/v1/send", json=_request().model_dump(mode="json"))
    assert first.status_code == second.status_code == 200
    assert first.json()["data_class"] == "MOCK"
    assert first.json()["result"]["status"] == "SENT"
    assert first.json()["result"]["provider_message_id"] == second.json()["result"]["provider_message_id"]
    rows = client.get("/v1/messages").json()
    assert len(rows) == 1
    assert rows[0]["data_class"] == "MOCK"
    assert rows[0]["message_data_class"] == "SYNTHETIC"


def test_mock_enterprise_service_exposes_failure_modes_without_fake_success():
    transient = client.post("/v1/send", json=_request(_mock_failure="transient").model_dump(mode="json"))
    assert transient.json()["result"]["status"] == "RETRYABLE_FAILURE"
    assert transient.json()["result"]["next_retry_at"] is not None
    limited = client.post("/v1/send", headers={"X-Mock-Failure": "rate_limited"}, json=_request(id="rate").model_dump(mode="json"))
    assert limited.json()["result"]["failure_kind"] == "RATE_LIMITED"
    permanent = client.post("/v1/send", headers={"X-Mock-Failure": "permanent"}, json=_request(id="permanent").model_dump(mode="json"))
    assert permanent.json()["result"]["status"] == "PERMANENT_FAILURE"
    suppressed = client.post("/v1/send", headers={"X-Mock-Failure": "suppressed"}, json=_request(id="suppressed").model_dump(mode="json"))
    assert suppressed.json()["result"]["status"] == "SUPPRESSED"
    assert client.get("/v1/messages").json() == []


def test_mock_service_health_reset_and_bounds():
    assert client.get("/health").json()["data_class"] == "MOCK"
    client.post("/v1/send", json=_request().model_dump(mode="json"))
    assert client.post("/v1/reset").json() == {"status": "reset", "data_class": "MOCK"}
    assert client.get("/v1/messages").json() == []
    service = MockEnterpriseMessagingService(max_messages=1)
    assert service.send(_request()).status == EnterpriseMessageStatus.SENT
    try:
        service.messages(limit=501)
    except ValueError as exc:
        assert "between 1 and 500" in str(exc)
    else:
        raise AssertionError("message query limit must be bounded")


def test_http_adapter_requires_mock_label_and_maps_transport_failures(monkeypatch):
    request = _request()
    config = MockEnterpriseMessagingHTTPConfig("http://mock-enterprise:8084")

    def post(url, **kwargs):
        assert url == "http://mock-enterprise:8084/v1/send"
        assert kwargs["json"]["data_class"] == "SYNTHETIC"
        return httpx.Response(
            200,
            json={"data_class": "MOCK", "result": {"status": "SENT", "attempt": 1, "input_signature": "0" * 64, "provider_message_id": "mock-http-1", "observed_at": "2026-08-12T12:00:00"}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", post)
    adapter = MockEnterpriseMessagingHTTPService(config)
    assert adapter.send(request).status == EnterpriseMessageStatus.SENT

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ConnectError("SYNTHETIC unavailable")))
    assert adapter.send(request).status == EnterpriseMessageStatus.RETRYABLE_FAILURE
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: httpx.Response(200, json={"data_class": "OBSERVED", "result": {}}, request=httpx.Request("POST", "http://mock-enterprise:8084/v1/send")))
    invalid = adapter.send(request)
    assert invalid.status == EnterpriseMessageStatus.PERMANENT_FAILURE
    assert invalid.error_code == "MOCK_ENTERPRISE_INVALID_RESPONSE"
