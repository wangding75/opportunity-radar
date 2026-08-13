"""Deterministic Mock adapter implementing the enterprise messaging Port."""

from __future__ import annotations

from threading import Lock

from app.core.time import utc_now
from app.domain.enterprise_messaging import (
    EnterpriseMessageFailureKind,
    EnterpriseMessagePort,
    EnterpriseMessageRequest,
    EnterpriseMessageResult,
    EnterpriseMessageStatus,
    message_input_signature,
    retry_at,
)

MOCK_ENTERPRISE_MESSAGING_VERSION = "mock-enterprise-messaging-v1"


class MockEnterpriseMessagingService(EnterpriseMessagePort):
    """In-memory delivery service with explicit MOCK results and idempotency."""

    def __init__(self, *, max_messages: int = 1_000) -> None:
        if max_messages < 1 or max_messages > 10_000:
            raise ValueError("max_messages must be between 1 and 10000")
        self.max_messages = max_messages
        self._lock = Lock()
        self._accepted: dict[str, EnterpriseMessageResult] = {}
        self._attempts: dict[str, int] = {}
        self._messages: list[dict] = []

    def send(self, request: EnterpriseMessageRequest) -> EnterpriseMessageResult:
        signature = message_input_signature(request)
        with self._lock:
            if signature in self._accepted:
                return self._accepted[signature]
            attempt = max(request.attempt, self._attempts.get(signature, 0) + 1)
            self._attempts[signature] = attempt
            now = utc_now()
            failure_mode = str(request.metadata.get("_mock_failure", "")).strip().lower()
            if failure_mode in {"transient", "true", "1", "yes"}:
                return EnterpriseMessageResult(
                    status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
                    attempt=attempt,
                    input_signature=signature,
                    observed_at=now,
                    next_retry_at=retry_at(now, attempt=attempt),
                    failure_kind=EnterpriseMessageFailureKind.TRANSIENT_PROVIDER,
                    error_code="MOCK_TRANSIENT_FAILURE",
                    error_detail="MOCK enterprise messaging provider requested a retry",
                )
            if failure_mode in {"rate_limited", "rate-limit", "ratelimited"}:
                return EnterpriseMessageResult(
                    status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
                    attempt=attempt,
                    input_signature=signature,
                    observed_at=now,
                    next_retry_at=retry_at(now, attempt=attempt),
                    failure_kind=EnterpriseMessageFailureKind.RATE_LIMITED,
                    error_code="MOCK_RATE_LIMITED",
                    error_detail="MOCK enterprise messaging provider requested backoff",
                )
            if failure_mode in {"permanent", "invalid", "blocked"}:
                result = EnterpriseMessageResult(
                    status=EnterpriseMessageStatus.PERMANENT_FAILURE,
                    attempt=attempt,
                    input_signature=signature,
                    observed_at=now,
                    failure_kind=EnterpriseMessageFailureKind.POLICY_BLOCKED if failure_mode == "blocked" else EnterpriseMessageFailureKind.INVALID_DESTINATION,
                    error_code="MOCK_PERMANENT_FAILURE",
                    error_detail="MOCK enterprise messaging provider rejected this message permanently",
                )
                self._accepted[signature] = result
                return result
            if failure_mode in {"suppressed", "suppress"}:
                result = EnterpriseMessageResult(
                    status=EnterpriseMessageStatus.SUPPRESSED,
                    attempt=attempt,
                    input_signature=signature,
                    observed_at=now,
                    error_code="MOCK_SUPPRESSED",
                    error_detail="MOCK policy suppressed this message",
                )
                self._accepted[signature] = result
                return result
            provider_message_id = f"mock-enterprise-msg-{signature[:24]}"
            result = EnterpriseMessageResult(
                status=EnterpriseMessageStatus.SENT,
                attempt=attempt,
                input_signature=signature,
                observed_at=now,
                provider_message_id=provider_message_id,
            )
            self._accepted[signature] = result
            self._messages.append(
                {
                    "data_class": "MOCK",
                    "provider": request.provider,
                    "message_id": request.message_id,
                    "idempotency_key": request.idempotency_key,
                    "input_signature": signature,
                    "provider_message_id": provider_message_id,
                    "destination": request.destination,
                    "title": request.title,
                    "text": request.text,
                    "blocks": request.blocks,
                    "message_data_class": request.data_class.value,
                    "metadata": request.metadata,
                    "sent_at": now.isoformat(),
                }
            )
            if len(self._messages) > self.max_messages:
                self._messages = self._messages[-self.max_messages :]
            return result

    def messages(self, *, limit: int = 100) -> list[dict]:
        if limit < 1 or limit > 500:
            raise ValueError("message query limit must be between 1 and 500")
        with self._lock:
            return list(reversed(self._messages[-limit:]))

    def reset(self) -> None:
        with self._lock:
            self._accepted.clear()
            self._attempts.clear()
            self._messages.clear()
