"""Deterministic Mock Mail adapter implementing the email delivery port."""

from __future__ import annotations

from threading import Lock

from app.core.time import utc_now
from app.domain.email_delivery import (
    EmailDeliveryPort,
    EmailDeliveryRequest,
    EmailDeliveryResult,
    EmailDeliveryStatus,
    EmailFailureKind,
    build_delivery_result,
    delivery_input_signature,
)

MOCK_MAIL_VERSION = "mock-mail-v1"


class MockMailService(EmailDeliveryPort):
    """In-memory mailbox with deterministic idempotency and explicit failures."""

    def __init__(self, *, max_messages: int = 1_000) -> None:
        if max_messages < 1 or max_messages > 10_000:
            raise ValueError("max_messages must be between 1 and 10000")
        self.max_messages = max_messages
        self._lock = Lock()
        self._accepted: dict[str, EmailDeliveryResult] = {}
        self._attempts: dict[str, int] = {}
        self._messages: list[dict] = []

    def send(self, request: EmailDeliveryRequest) -> EmailDeliveryResult:
        signature = delivery_input_signature(request)
        with self._lock:
            if signature in self._accepted:
                return self._accepted[signature]
            failure_mode = str(request.metadata.get("_mock_failure", "")).strip().lower()
            attempt = self._attempts.get(signature, 0) + 1
            self._attempts[signature] = attempt
            now = utc_now()
            if failure_mode in {"transient", "rate_limited", "rate-limit", "true", "1", "yes"}:
                failure_kind = EmailFailureKind.RATE_LIMITED if failure_mode in {"rate_limited", "rate-limit"} else EmailFailureKind.TRANSIENT_PROVIDER
                result = build_delivery_result(
                    request,
                    status=EmailDeliveryStatus.RETRYABLE_FAILURE,
                    attempt=attempt,
                    failure_kind=failure_kind,
                    error_code="MOCK_RATE_LIMITED" if failure_kind == EmailFailureKind.RATE_LIMITED else "MOCK_TRANSIENT_FAILURE",
                    error_detail="MOCK mail provider requested a retry",
                    now=now,
                )
                return result
            if failure_mode in {"permanent", "invalid", "blocked"}:
                result = build_delivery_result(
                    request,
                    status=EmailDeliveryStatus.PERMANENT_FAILURE,
                    attempt=attempt,
                    failure_kind=EmailFailureKind.POLICY_BLOCKED if failure_mode == "blocked" else EmailFailureKind.INVALID_RECIPIENT,
                    error_code="MOCK_PERMANENT_FAILURE",
                    error_detail="MOCK mail provider rejected this message permanently",
                    now=now,
                )
                self._accepted[signature] = result
                return result
            if failure_mode in {"suppressed", "suppress"}:
                result = build_delivery_result(
                    request,
                    status=EmailDeliveryStatus.SUPPRESSED,
                    attempt=attempt,
                    error_code="MOCK_SUPPRESSED",
                    error_detail="MOCK policy suppressed this message",
                    now=now,
                )
                self._accepted[signature] = result
                return result
            provider_message_id = f"mock-msg-{signature[:24]}"
            result = build_delivery_result(
                request,
                status=EmailDeliveryStatus.SENT,
                attempt=attempt,
                provider_message_id=provider_message_id,
                now=now,
            )
            self._accepted[signature] = result
            self._messages.append(
                {
                    "data_class": "MOCK",
                    "message_id": request.message_id,
                    "idempotency_key": request.idempotency_key,
                    "input_signature": signature,
                    "provider_message_id": provider_message_id,
                    "recipients": list(request.recipients),
                    "subject": request.subject,
                    "text_body": request.text_body,
                    "html_body": request.html_body,
                    "template_name": request.template_name,
                    "template_version": request.template_version,
                    "sent_at": now.isoformat(),
                }
            )
            if len(self._messages) > self.max_messages:
                self._messages = self._messages[-self.max_messages :]
            return result

    def messages(self, *, limit: int = 100) -> list[dict]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        with self._lock:
            return list(reversed(self._messages[-limit:]))

    def reset(self) -> None:
        with self._lock:
            self._accepted.clear()
            self._attempts.clear()
            self._messages.clear()
