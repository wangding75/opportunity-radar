from datetime import datetime, timezone

import pytest

from app.domain.email_delivery import (
    EmailDeliveryPolicy,
    EmailDeliveryStatus,
    EmailFailureKind,
    EmailRetryPolicy,
    EmailTemplate,
    build_delivery_result,
    build_email_request,
    delivery_input_signature,
    render_email_template,
    retry_at_for_failure,
)


def _template() -> EmailTemplate:
    return EmailTemplate(name="risk.alert", version="v1", subject="Risk alert for ${opportunity}", text_body="${message}\nEvidence: ${evidence_id}", html_body="<p>${message}</p>")


def test_template_render_and_request_normalize_recipients_and_signature():
    request = build_email_request(
        message_id="alert-1",
        idempotency_key="alert-1:v1",
        recipients=[" B@example.com ", "a@example.com", "a@example.com"],
        template=_template(),
        context={"opportunity": "SYNTHETIC opportunity", "message": "SYNTHETIC risk escalated", "evidence_id": "ev1_demo"},
        requested_at=datetime(2026, 8, 12, 12, tzinfo=timezone.utc),
        metadata={"data_class": "SYNTHETIC"},
    )
    assert request.recipients == ["a@example.com", "b@example.com"]
    assert request.subject == "Risk alert for SYNTHETIC opportunity"
    assert request.requested_at.tzinfo is None
    assert delivery_input_signature(request) == delivery_input_signature(request.model_copy(update={"requested_at": datetime(2030, 1, 1)}))


def test_template_missing_context_and_header_injection_fail_closed():
    with pytest.raises(ValueError, match="incomplete"):
        render_email_template(_template(), {"opportunity": "only"})
    with pytest.raises(ValueError, match="CR/LF"):
        build_email_request(message_id="1", idempotency_key="1", recipients=["a@example.com"], template=EmailTemplate(name="safe", version="v1", subject="Hello", text_body="body"), context={}, metadata={"x": "bad\nheader"})
    with pytest.raises(ValueError, match="invalid email"):
        build_email_request(message_id="1", idempotency_key="1", recipients=["not-an-email"], template=_template(), context={"opportunity": "x", "message": "y", "evidence_id": "z"})


def test_retry_policy_distinguishes_transient_permanent_and_attempt_boundary():
    policy = EmailRetryPolicy(max_attempts=3, base_delay_seconds=10, max_delay_seconds=20)
    now = datetime(2026, 8, 12, 12)
    assert retry_at_for_failure(attempt=1, failure_kind=EmailFailureKind.TRANSIENT_PROVIDER, now=now, policy=policy) == datetime(2026, 8, 12, 12, 0, 10)
    assert retry_at_for_failure(attempt=2, failure_kind=EmailFailureKind.RATE_LIMITED, now=now, policy=policy) == datetime(2026, 8, 12, 12, 0, 20)
    assert retry_at_for_failure(attempt=3, failure_kind=EmailFailureKind.TRANSIENT_PROVIDER, now=now, policy=policy) is None
    assert retry_at_for_failure(attempt=1, failure_kind=EmailFailureKind.INVALID_RECIPIENT, now=now, policy=policy) is None
    with pytest.raises(ValueError, match="at least"):
        EmailRetryPolicy(base_delay_seconds=20, max_delay_seconds=10)


def test_delivery_results_require_consistent_status_fields_and_are_versioned():
    request = build_email_request(message_id="alert-2", idempotency_key="alert-2:v1", recipients=["a@example.com"], template=_template(), context={"opportunity": "x", "message": "y", "evidence_id": "z"})
    sent = build_delivery_result(request, status=EmailDeliveryStatus.SENT, provider_message_id="mock-1", now=datetime(2026, 8, 12))
    assert sent.status == EmailDeliveryStatus.SENT
    assert sent.algorithm_version == "email-delivery-v1"
    assert sent.next_retry_at is None
    with pytest.raises(ValueError, match="provider_message_id"):
        build_delivery_result(request, status=EmailDeliveryStatus.SENT)
    with pytest.raises(ValueError, match="failure_kind"):
        build_delivery_result(request, status=EmailDeliveryStatus.RETRYABLE_FAILURE)
    with pytest.raises(ValueError, match="transient"):
        build_delivery_result(request, status=EmailDeliveryStatus.PERMANENT_FAILURE, failure_kind=EmailFailureKind.TRANSIENT_PROVIDER)


def test_delivery_limits_and_policy_are_enforced():
    template = EmailTemplate(name="limited", version="v1", subject="${x}", text_body="${x}")
    with pytest.raises(ValueError, match="recipient count"):
        build_email_request(message_id="1", idempotency_key="1", recipients=[f"{i}@example.com" for i in range(3)], template=template, context={"x": "x"}, policy=EmailDeliveryPolicy(max_recipients=2))
    with pytest.raises(ValueError, match="subject"):
        build_email_request(message_id="1", idempotency_key="1", recipients=["a@example.com"], template=EmailTemplate(name="long", version="v1", subject="${x}", text_body="ok"), context={"x": "x" * 5}, policy=EmailDeliveryPolicy(max_subject_length=3))
