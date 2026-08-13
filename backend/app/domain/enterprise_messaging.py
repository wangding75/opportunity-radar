"""Provider-neutral contract for enterprise alert messaging integrations."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive, utc_now

ENTERPRISE_MESSAGING_CONTRACT_VERSION = "enterprise-messaging-v1"
ENTERPRISE_MESSAGING_MAX_PAYLOAD_BYTES = 512 * 1024
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{8,200}$")
_PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{1,39}$")


class EnterpriseMessagingProvider(StrEnum):
    MOCK = "mock"
    SLACK = "slack"
    FEISHU = "feishu"
    WECOM = "wecom"


class EnterpriseDataClass(StrEnum):
    ALERT_EVENT = "ALERT_EVENT"
    OBSERVED = "OBSERVED"
    MOCK = "MOCK"
    SYNTHETIC = "SYNTHETIC"


class EnterpriseMessageStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    SENT = "SENT"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    SUPPRESSED = "SUPPRESSED"
    INVALID = "INVALID"


class EnterpriseMessageFailureKind(StrEnum):
    TRANSIENT_PROVIDER = "TRANSIENT_PROVIDER"
    RATE_LIMITED = "RATE_LIMITED"
    AUTHENTICATION = "AUTHENTICATION"
    INVALID_DESTINATION = "INVALID_DESTINATION"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNKNOWN = "UNKNOWN"


class EnterpriseMessageRetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="enterprise-message-retry-v1", min_length=1, max_length=50)
    max_attempts: int = Field(default=5, ge=1, le=20)
    base_delay_seconds: int = Field(default=60, ge=1, le=86_400)
    max_delay_seconds: int = Field(default=3_600, ge=1, le=7 * 86_400)

    @field_validator("max_delay_seconds")
    @classmethod
    def validate_delay_order(cls, value: int, info):
        if value < info.data.get("base_delay_seconds", 60):
            raise ValueError("max_delay_seconds must be at least base_delay_seconds")
        return value


class EnterpriseMessageRequest(BaseModel):
    """Canonical provider-neutral message input.

    `destination` is intentionally opaque: each adapter validates the
    provider-specific channel/webhook identifier and keeps credentials out of
    this contract. `metadata` is for audit-safe correlation only.
    """

    model_config = ConfigDict(extra="forbid")

    contract_version: str = ENTERPRISE_MESSAGING_CONTRACT_VERSION
    message_id: str = Field(min_length=8, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)
    provider: str = Field(min_length=2, max_length=40)
    destination: str = Field(min_length=1, max_length=500)
    title: str = Field(default="", max_length=300)
    text: str = Field(min_length=1, max_length=200_000)
    blocks: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    data_class: EnterpriseDataClass = EnterpriseDataClass.ALERT_EVENT
    metadata: dict[str, Any] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=utc_now)
    attempt: int = Field(default=1, ge=1, le=100)

    @field_validator("message_id", "idempotency_key")
    @classmethod
    def validate_tokens(cls, value: str) -> str:
        if not _TOKEN_RE.fullmatch(value):
            raise ValueError("message_id and idempotency_key contain unsupported characters")
        return value

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _PROVIDER_RE.fullmatch(normalized):
            raise ValueError("provider contains unsupported characters")
        return normalized

    @field_validator("destination", "title")
    @classmethod
    def reject_header_injection(cls, value: str) -> str:
        if "\r" in value or "\n" in value:
            raise ValueError("message destination and title must not contain CR/LF")
        return value

    @field_validator("text")
    @classmethod
    def reject_carriage_return(cls, value: str) -> str:
        if "\r" in value:
            raise ValueError("message text must not contain CR")
        return value

    @field_validator("requested_at", mode="before")
    @classmethod
    def normalize_requested_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("requested_at must be a datetime")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_canonical_payload(self):
        canonical_message_bytes(self)
        return self

    @classmethod
    def synthetic_alert(
        cls,
        *,
        message_id: str,
        idempotency_key: str,
        provider: str,
        destination: str,
        title: str,
        text: str,
        alert_event_id: int,
        event_key: str,
        data_class: EnterpriseDataClass = EnterpriseDataClass.ALERT_EVENT,
        requested_at: datetime | None = None,
    ) -> "EnterpriseMessageRequest":
        return cls(
            message_id=message_id,
            idempotency_key=idempotency_key,
            provider=provider,
            destination=destination,
            title=title,
            text=text,
            data_class=data_class,
            metadata={"alert_event_id": alert_event_id, "event_key": event_key},
            requested_at=requested_at or utc_now(),
        )


class EnterpriseMessageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: EnterpriseMessageStatus
    attempt: int = Field(ge=1, le=100)
    input_signature: str | None = Field(default=None, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime = Field(default_factory=utc_now)
    next_retry_at: datetime | None = None
    provider_message_id: str | None = Field(default=None, max_length=300)
    failure_kind: EnterpriseMessageFailureKind | None = None
    error_code: str | None = Field(default=None, max_length=100)
    error_detail: str | None = Field(default=None, max_length=2_000)


class EnterpriseMessagePort(Protocol):
    def send(self, request: EnterpriseMessageRequest) -> EnterpriseMessageResult:
        """Deliver one message; provider failures must be explicit results."""


# Readable aliases for adapters that use the shorter connector terminology.
EnterpriseMessagingPort = EnterpriseMessagePort
MessagingRequest = EnterpriseMessageRequest
MessagingResult = EnterpriseMessageResult


def canonical_message_bytes(request: EnterpriseMessageRequest | Mapping[str, Any]) -> bytes:
    normalized = request if isinstance(request, EnterpriseMessageRequest) else EnterpriseMessageRequest.model_validate(request)
    _assert_finite_json(normalized.blocks)
    _assert_finite_json(normalized.metadata)
    payload = normalized.model_dump(mode="json", exclude={"attempt"})
    try:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("enterprise message must be finite and JSON serializable") from exc
    if len(encoded) > ENTERPRISE_MESSAGING_MAX_PAYLOAD_BYTES:
        raise ValueError(f"enterprise message exceeds {ENTERPRISE_MESSAGING_MAX_PAYLOAD_BYTES} bytes")
    return encoded


def _assert_finite_json(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("enterprise message must not contain NaN or infinity")
    if isinstance(value, Mapping):
        for nested in value.values():
            _assert_finite_json(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_finite_json(nested)


def message_input_signature(request: EnterpriseMessageRequest | Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_message_bytes(request)).hexdigest()


def retry_at(now: datetime, *, attempt: int, policy: EnterpriseMessageRetryPolicy | None = None) -> datetime:
    policy = policy or EnterpriseMessageRetryPolicy()
    delay = min(policy.base_delay_seconds * (2 ** max(0, attempt - 1)), policy.max_delay_seconds)
    return as_utc_naive(now) + timedelta(seconds=delay)
