import json

import httpx
import pytest

from app.domain.enterprise_messaging import EnterpriseMessageRequest, EnterpriseMessageStatus
from app.services.enterprise_messaging_adapters import (
    EnterpriseWebhookAdapterConfig,
    FeishuMessagingAdapter,
    SlackMessagingAdapter,
    WeComMessagingAdapter,
)


def _request(provider: str = "slack"):
    return EnterpriseMessageRequest(
        message_id="msg_synthetic_adapter_1",
        idempotency_key="idem_synthetic_adapter_1",
        provider=provider,
        destination="synthetic-destination",
        title="SYNTHETIC alert",
        text="SYNTHETIC adapter message",
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "SYNTHETIC"}}],
        data_class="SYNTHETIC",
    )


@pytest.mark.parametrize(
    ("adapter_type", "expected"),
    [
        (SlackMessagingAdapter, {"text": "SYNTHETIC alert\nSYNTHETIC adapter message"}),
        (FeishuMessagingAdapter, {"msg_type": "text", "content": {"text": "SYNTHETIC alert\nSYNTHETIC adapter message"}}),
        (WeComMessagingAdapter, {"msgtype": "text", "text": {"content": "SYNTHETIC alert\nSYNTHETIC adapter message"}}),
    ],
)
def test_provider_payloads_use_the_unified_contract(adapter_type, expected):
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        return httpx.Response(200, json={"errcode": 0, "code": 0}, request=request)

    provider = {SlackMessagingAdapter: "slack", FeishuMessagingAdapter: "feishu", WeComMessagingAdapter: "wecom"}[adapter_type]
    with adapter_type(EnterpriseWebhookAdapterConfig("https://provider.synthetic.invalid/hook"), client=httpx.Client(transport=httpx.MockTransport(handler))) as adapter:
        result = adapter.send(_request(provider))
    assert result.status == EnterpriseMessageStatus.SENT
    assert result.input_signature
    assert calls[0].headers["content-type"] == "application/json"
    body = json.loads(calls[0].content)
    for key, value in expected.items():
        assert body[key] == value


def test_http_status_and_provider_body_errors_are_not_fake_success():
    def throttled(request):
        return httpx.Response(429, json={}, request=request)

    with SlackMessagingAdapter(EnterpriseWebhookAdapterConfig("https://slack.synthetic.invalid/hook"), client=httpx.Client(transport=httpx.MockTransport(throttled))) as adapter:
        result = adapter.send(_request("slack"))
    assert result.status == EnterpriseMessageStatus.RETRYABLE_FAILURE
    assert result.failure_kind.value == "RATE_LIMITED"

    def feishu_error(request):
        return httpx.Response(200, json={"code": 999, "msg": "SYNTHETIC rejected"}, request=request)

    with FeishuMessagingAdapter(EnterpriseWebhookAdapterConfig("https://feishu.synthetic.invalid/hook"), client=httpx.Client(transport=httpx.MockTransport(feishu_error))) as adapter:
        result = adapter.send(_request("feishu"))
    assert result.status == EnterpriseMessageStatus.PERMANENT_FAILURE
    assert result.error_code == "FEISHU_PROVIDER_999"

    def wecom_error(request):
        return httpx.Response(200, json={"errcode": 40001, "errmsg": "SYNTHETIC auth"}, request=request)

    with WeComMessagingAdapter(EnterpriseWebhookAdapterConfig("https://wecom.synthetic.invalid/hook"), client=httpx.Client(transport=httpx.MockTransport(wecom_error))) as adapter:
        result = adapter.send(_request("wecom"))
    assert result.status == EnterpriseMessageStatus.PERMANENT_FAILURE
    assert result.failure_kind.value == "AUTHENTICATION"


def test_transport_failure_and_config_bounds_are_explicit():
    with pytest.raises(ValueError):
        EnterpriseWebhookAdapterConfig("ftp://invalid.synthetic")
    with pytest.raises(ValueError):
        EnterpriseWebhookAdapterConfig("https://invalid.synthetic", timeout_seconds=121)

    def unavailable(request):
        raise httpx.ConnectError("SYNTHETIC unavailable", request=request)

    with SlackMessagingAdapter(EnterpriseWebhookAdapterConfig("https://slack.synthetic.invalid/hook"), client=httpx.Client(transport=httpx.MockTransport(unavailable))) as adapter:
        result = adapter.send(_request("slack"))
    assert result.status == EnterpriseMessageStatus.RETRYABLE_FAILURE
