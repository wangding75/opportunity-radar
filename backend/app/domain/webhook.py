"""Versioned webhook event and HMAC signature contract."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Mapping, Protocol
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.time import as_utc_naive, utc_now
from app.services.webhook_security import validate_webhook_url_syntax

WEBHOOK_CONTRACT_VERSION = "webhook-event-v1"
WEBHOOK_SIGNATURE_VERSION = "v1"
WEBHOOK_SIGNATURE_ALGORITHM = "hmac-sha256"
WEBHOOK_MAX_PAYLOAD_BYTES = 512 * 1024
WEBHOOK_DEFAULT_TIMESTAMP_TOLERANCE_SECONDS = 300
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._~-]{8,128}$")
_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class WebhookEventType(StrEnum):
    ALERT_EVENT = "alert.event"


class WebhookDataClass(StrEnum):
    ALERT_EVENT = "ALERT_EVENT"
    OBSERVED = "OBSERVED"
    MOCK = "MOCK"
    SYNTHETIC = "SYNTHETIC"


class WebhookEvent(BaseModel):
    """The exact event body that is canonicalized and signed."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = WEBHOOK_CONTRACT_VERSION
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}", min_length=1, max_length=128)
    event_type: WebhookEventType = WebhookEventType.ALERT_EVENT
    event_version: str = Field(default="1", min_length=1, max_length=20)
    occurred_at: datetime = Field(default_factory=utc_now)
    data_class: WebhookDataClass = WebhookDataClass.ALERT_EVENT
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        if not _ID_RE.fullmatch(value):
            raise ValueError("event_id contains unsupported characters")
        return value

    @field_validator("occurred_at", mode="before")
    @classmethod
    def normalize_occurred_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("occurred_at must be a datetime")
        return as_utc_naive(value)

    @model_validator(mode="after")
    def validate_payload(self):
        canonical_event_bytes(self)
        return self


class WebhookSignature(BaseModel):
    """Parsed signature fields; the secret is deliberately not a model field."""

    model_config = ConfigDict(extra="forbid")

    timestamp: int = Field(ge=0)
    delivery_id: str = Field(min_length=1, max_length=128)
    nonce: str = Field(min_length=8, max_length=128)
    signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    version: str = WEBHOOK_SIGNATURE_VERSION

    @field_validator("delivery_id", "nonce")
    @classmethod
    def validate_token(cls, value: str) -> str:
        if not _TOKEN_RE.fullmatch(value):
            raise ValueError("webhook delivery_id and nonce must be safe tokens")
        return value


class WebhookDeliveryRequest(BaseModel):
    """Provider-neutral delivery input used by later endpoint/queue tasks."""

    model_config = ConfigDict(extra="forbid")

    event: WebhookEvent
    delivery_id: str = Field(default_factory=lambda: f"del_{uuid4().hex}", min_length=1, max_length=128)
    attempt: int = Field(default=1, ge=1, le=100)
    signature: WebhookSignature | None = None

    @field_validator("delivery_id")
    @classmethod
    def validate_delivery_id(cls, value: str) -> str:
        if not _TOKEN_RE.fullmatch(value):
            raise ValueError("delivery_id must be a safe token")
        return value


class WebhookDeliveryStatus(StrEnum):
    SENT = "SENT"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    INVALID = "INVALID"


class WebhookFailureKind(StrEnum):
    TRANSIENT_NETWORK = "TRANSIENT_NETWORK"
    RATE_LIMITED = "RATE_LIMITED"
    AUTHENTICATION = "AUTHENTICATION"
    INVALID_ENDPOINT = "INVALID_ENDPOINT"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNKNOWN = "UNKNOWN"


class WebhookRetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="webhook-retry-policy-v1", min_length=1, max_length=50)
    max_attempts: int = Field(default=5, ge=1, le=20)
    base_delay_seconds: int = Field(default=60, ge=1, le=86_400)
    max_delay_seconds: int = Field(default=3_600, ge=1, le=7 * 86_400)

    @field_validator("max_delay_seconds")
    @classmethod
    def validate_delay_order(cls, value: int, info):
        if value < info.data.get("base_delay_seconds", 60):
            raise ValueError("max_delay_seconds must be at least base_delay_seconds")
        return value


class WebhookDeliveryResult(BaseModel):
    """Provider result; it never contains the endpoint secret."""

    model_config = ConfigDict(extra="forbid")

    status: WebhookDeliveryStatus
    attempt: int = Field(ge=1, le=100)
    input_signature: str | None = Field(default=None, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    observed_at: datetime = Field(default_factory=utc_now)
    next_retry_at: datetime | None = None
    http_status: int | None = Field(default=None, ge=100, le=599)
    provider_message_id: str | None = Field(default=None, max_length=300)
    failure_kind: WebhookFailureKind | None = None
    error_code: str | None = Field(default=None, max_length=100)
    error_detail: str | None = Field(default=None, max_length=2_000)


class WebhookDeliveryPort(Protocol):
    def send(
        self,
        request: WebhookDeliveryRequest,
        *,
        endpoint_url: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> WebhookDeliveryResult:
        """Send one already-signed canonical request to an endpoint."""


class WebhookEndpointCreate(BaseModel):
    """Write model for endpoint management; secret is write-only at API level."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=2_000)
    secret: str = Field(min_length=16, max_length=4_096)
    event_types: list[WebhookEventType] = Field(default_factory=lambda: [WebhookEventType.ALERT_EVENT], min_length=1, max_length=10)
    enabled: bool = True
    description: str = Field(default="", max_length=2_000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,119}", value):
            raise ValueError("webhook endpoint name contains unsupported characters")
        return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_webhook_url_syntax(value)

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        validate_webhook_secret(value)
        return value

    @field_validator("event_types")
    @classmethod
    def normalize_event_types(cls, values: list[WebhookEventType]) -> list[WebhookEventType]:
        return list(dict.fromkeys(values))


class WebhookEndpointPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    url: str | None = Field(default=None, min_length=1, max_length=2_000)
    secret: str | None = Field(default=None, min_length=16, max_length=4_096)
    event_types: list[WebhookEventType] | None = Field(default=None, min_length=1, max_length=10)
    enabled: bool | None = None
    description: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def validate_patch_values(self):
        if self.name is not None:
            WebhookEndpointCreate.normalize_name(self.name)
        if self.url is not None:
            WebhookEndpointCreate.validate_url(self.url)
        if self.secret is not None:
            WebhookEndpointCreate.validate_secret(self.secret)
        if self.event_types is not None:
            WebhookEndpointCreate.normalize_event_types(self.event_types)
        return self


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("webhook payload must be finite and JSON serializable") from exc
    if len(encoded) > WEBHOOK_MAX_PAYLOAD_BYTES:
        raise ValueError(f"webhook payload exceeds {WEBHOOK_MAX_PAYLOAD_BYTES} bytes")
    return encoded


def canonical_event_bytes(event: WebhookEvent | Mapping[str, Any]) -> bytes:
    """Return the only JSON representation eligible for signing/transmission."""

    normalized = event if isinstance(event, WebhookEvent) else WebhookEvent.model_validate(event)
    return _canonical_json_bytes(normalized.model_dump(mode="json"))


def validate_webhook_secret(secret: str | bytes) -> bytes:
    if isinstance(secret, str):
        secret_bytes = secret.encode("utf-8")
    elif isinstance(secret, bytes):
        secret_bytes = secret
    else:
        raise ValueError("webhook secret must be text or bytes")
    if len(secret_bytes) < 16:
        raise ValueError("webhook secret must contain at least 16 bytes")
    if len(secret_bytes) > 4096:
        raise ValueError("webhook secret must not exceed 4096 bytes")
    if b"\r" in secret_bytes or b"\n" in secret_bytes:
        raise ValueError("webhook secret must not contain CR/LF")
    return secret_bytes


def _signature_input(*, payload: bytes, timestamp: int, delivery_id: str, nonce: str) -> bytes:
    if not isinstance(payload, bytes):
        raise ValueError("signature payload must be bytes")
    return b".".join((str(timestamp).encode("ascii"), delivery_id.encode("ascii"), nonce.encode("ascii"), payload))


def sign_webhook_event(
    event: WebhookEvent,
    secret: str | bytes,
    *,
    timestamp: int | None = None,
    delivery_id: str | None = None,
    nonce: str | None = None,
) -> WebhookSignature:
    """Sign canonical event bytes with HMAC-SHA256."""

    secret_bytes = validate_webhook_secret(secret)
    timestamp = int(time.time()) if timestamp is None else timestamp
    if timestamp < 0:
        raise ValueError("webhook timestamp must not be negative")
    delivery_id = delivery_id or f"del_{uuid4().hex}"
    nonce = nonce or secrets.token_urlsafe(18)
    parsed = WebhookSignature(
        timestamp=timestamp,
        delivery_id=delivery_id,
        nonce=nonce,
        signature="0" * 64,
    )
    digest = hmac.new(
        secret_bytes,
        _signature_input(payload=canonical_event_bytes(event), timestamp=parsed.timestamp, delivery_id=parsed.delivery_id, nonce=parsed.nonce),
        hashlib.sha256,
    ).hexdigest()
    return parsed.model_copy(update={"signature": digest})


def format_webhook_signature(signature: WebhookSignature) -> str:
    """Format a strict, single-value header suitable for HTTP transport."""

    return f"t={signature.timestamp},d={signature.delivery_id},n={signature.nonce},{signature.version}={signature.signature}"


def parse_webhook_signature(header: str) -> WebhookSignature:
    if not isinstance(header, str) or not header or "\r" in header or "\n" in header:
        raise ValueError("webhook signature header is invalid")
    fields: dict[str, str] = {}
    for item in header.split(","):
        if "=" not in item:
            raise ValueError("webhook signature header field is invalid")
        key, value = item.split("=", 1)
        key, value = key.strip(), value.strip()
        if key in fields or not value:
            raise ValueError("webhook signature header contains duplicate or empty fields")
        fields[key] = value
    if set(fields) != {"t", "d", "n", WEBHOOK_SIGNATURE_VERSION}:
        raise ValueError("webhook signature header fields are incomplete")
    try:
        timestamp = int(fields["t"])
    except ValueError as exc:
        raise ValueError("webhook signature timestamp is invalid") from exc
    return WebhookSignature(
        timestamp=timestamp,
        delivery_id=fields["d"],
        nonce=fields["n"],
        signature=fields[WEBHOOK_SIGNATURE_VERSION],
    )


def build_webhook_headers(event: WebhookEvent, secret: str | bytes, *, signature: WebhookSignature | None = None) -> dict[str, str]:
    signature = signature or sign_webhook_event(event, secret)
    return {
        "Content-Type": "application/json",
        "X-Webhook-Event": event.event_type.value,
        "X-Webhook-Contract-Version": event.contract_version,
        "X-Webhook-Delivery-ID": signature.delivery_id,
        "X-Webhook-Signature": format_webhook_signature(signature),
    }


def verify_webhook_signature(
    payload: bytes | str,
    secret: str | bytes,
    signature_header: str,
    *,
    now: datetime | None = None,
    tolerance_seconds: int = WEBHOOK_DEFAULT_TIMESTAMP_TOLERANCE_SECONDS,
    expected_delivery_id: str | None = None,
) -> bool:
    """Verify authenticity and freshness; return False for malformed input."""

    try:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if not isinstance(payload, bytes) or len(payload) > WEBHOOK_MAX_PAYLOAD_BYTES:
            return False
        if tolerance_seconds < 1 or tolerance_seconds > 86_400:
            return False
        parsed = parse_webhook_signature(signature_header)
        if expected_delivery_id is not None and parsed.delivery_id != expected_delivery_id:
            return False
        # ``utc_now`` is intentionally timezone-naive for database portability.
        # Attach UTC for the implicit current time; a caller-supplied naive
        # ``datetime.fromtimestamp`` retains Python's documented local-time
        # interpretation for compatibility, while aware values are normalized
        # to UTC. This also avoids Windows epoch conversion errors.
        if now is None:
            current = int(utc_now().replace(tzinfo=UTC).timestamp())
        elif now.tzinfo is None:
            try:
                current = int(now.timestamp())
            except (OSError, OverflowError, ValueError):
                current = int(now.replace(tzinfo=UTC).timestamp())
        else:
            current = int(as_utc_naive(now).replace(tzinfo=UTC).timestamp())
        if abs(current - parsed.timestamp) > tolerance_seconds:
            return False
        expected = hmac.new(
            validate_webhook_secret(secret),
            _signature_input(payload=payload, timestamp=parsed.timestamp, delivery_id=parsed.delivery_id, nonce=parsed.nonce),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, parsed.signature)
    except (TypeError, ValueError, UnicodeError):
        return False
