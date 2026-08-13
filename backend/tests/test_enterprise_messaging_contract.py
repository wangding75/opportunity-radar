from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.domain.enterprise_messaging import (
    ENTERPRISE_MESSAGING_CONTRACT_VERSION,
    EnterpriseDataClass,
    EnterpriseMessageFailureKind,
    EnterpriseMessageRequest,
    EnterpriseMessageResult,
    EnterpriseMessageRetryPolicy,
    EnterpriseMessageStatus,
    canonical_message_bytes,
    message_input_signature,
    retry_at,
)


def _request(**overrides):
    values = {
        "message_id": "msg_synthetic_001",
        "idempotency_key": "idem_synthetic_001",
        "provider": "mock",
        "destination": "synthetic-channel",
        "title": "SYNTHETIC alert",
        "text": "SYNTHETIC enterprise message",
        "data_class": "SYNTHETIC",
        "metadata": {"source": "SYNTHETIC", "alert_event_id": 7},
        "requested_at": datetime(2026, 8, 12, 12, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return EnterpriseMessageRequest(**values)


def test_contract_normalizes_provider_and_time_and_has_stable_signature():
    request = _request(provider=" MOCK ")
    assert request.contract_version == ENTERPRISE_MESSAGING_CONTRACT_VERSION
    assert request.provider == "mock"
    assert request.requested_at == datetime(2026, 8, 12, 12)
    assert message_input_signature(request) == message_input_signature(request.model_copy(update={"attempt": 2}))
    assert b'"data_class":"SYNTHETIC"' in canonical_message_bytes(request)


def test_contract_rejects_empty_or_unsafe_fields_and_non_finite_payload():
    with pytest.raises(ValidationError):
        _request(text="")
    with pytest.raises(ValidationError):
        _request(destination="channel\nforged-header")
    with pytest.raises(ValidationError):
        _request(provider="bad provider")
    with pytest.raises(ValidationError):
        _request(metadata={"score": float("nan")})


def test_synthetic_builder_and_result_preserve_failure_semantics():
    request = EnterpriseMessageRequest.synthetic_alert(
        message_id="msg_synthetic_002",
        idempotency_key="idem_synthetic_002",
        provider="slack",
        destination="#synthetic",
        title="SYNTHETIC Slack alert",
        text="SYNTHETIC provider contract",
        alert_event_id=9,
        event_key="synthetic-event-9",
        data_class=EnterpriseDataClass.SYNTHETIC,
    )
    result = EnterpriseMessageResult(
        status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
        attempt=1,
        next_retry_at=retry_at(datetime(2026, 8, 12, 12), attempt=1),
        failure_kind=EnterpriseMessageFailureKind.RATE_LIMITED,
        error_code="RATE_LIMITED",
        error_detail="SYNTHETIC provider throttling",
    )
    assert request.metadata["alert_event_id"] == 9
    assert result.status == EnterpriseMessageStatus.RETRYABLE_FAILURE
    assert result.next_retry_at == datetime(2026, 8, 12, 12, 1)


def test_retry_policy_has_bounded_exponential_backoff():
    policy = EnterpriseMessageRetryPolicy(max_attempts=3, base_delay_seconds=2, max_delay_seconds=5)
    now = datetime(2026, 8, 12, 12)
    assert retry_at(now, attempt=1, policy=policy) == now + timedelta(seconds=2)
    assert retry_at(now, attempt=2, policy=policy) == now + timedelta(seconds=4)
    assert retry_at(now, attempt=3, policy=policy) == now + timedelta(seconds=5)
