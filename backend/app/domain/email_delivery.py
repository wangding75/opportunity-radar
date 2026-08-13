"""Versioned contract and provider port for email alert delivery."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from enum import StrEnum
from string import Template
from typing import Any, Mapping, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.time import as_utc_naive, utc_now

EMAIL_DELIVERY_CONTRACT_VERSION = "1"
EMAIL_DELIVERY_ALGORITHM_VERSION = "email-delivery-v1"
EMAIL_TEMPLATE_CONTRACT_VERSION = "email-template-v1"
_EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")
_TEMPLATE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,99}$")


class EmailDeliveryStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    SENT = "SENT"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    SUPPRESSED = "SUPPRESSED"
    INVALID = "INVALID"


class EmailFailureKind(StrEnum):
    TRANSIENT_PROVIDER = "TRANSIENT_PROVIDER"
    RATE_LIMITED = "RATE_LIMITED"
    AUTHENTICATION = "AUTHENTICATION"
    INVALID_RECIPIENT = "INVALID_RECIPIENT"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNKNOWN = "UNKNOWN"


class EmailTemplate(BaseModel):
    """A versioned template with a mandatory auditable plain-text rendering."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = EMAIL_TEMPLATE_CONTRACT_VERSION
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9._-]{0,99}$")
    version: str = Field(min_length=1, max_length=40)
    subject: str = Field(min_length=1, max_length=998)
    text_body: str = Field(min_length=1, max_length=200_000)
    html_body: str | None = Field(default=None, max_length=500_000)

    @field_validator("subject", "text_body", "html_body", mode="before")
    @classmethod
    def reject_control_injection(cls, value: Any) -> Any:
        if value is None:
            return value
        text = str(value)
        if "\r" in text or "\n" in text and cls.__name__ == "EmailTemplate":
            # Newlines are valid in bodies but not in a subject. The subject
            # validator below provides the precise message for that field.
            return text
        return text

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        if "\r" in value or "\n" in value:
            raise ValueError("email subject must not contain CR/LF")
        return value.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not _TEMPLATE_NAME_RE.fullmatch(value):
            raise ValueError("template name must use lowercase letters, digits, dot, underscore, or hyphen")
        return value


class EmailRetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="email-retry-policy-v1", min_length=1, max_length=50)
    max_attempts: int = Field(default=5, ge=1, le=20)
    base_delay_seconds: int = Field(default=60, ge=1, le=86_400)
    max_delay_seconds: int = Field(default=3_600, ge=1, le=7 * 86_400)

    @field_validator("max_delay_seconds")
    @classmethod
    def validate_delay_order(cls, value: int, info):
        base_delay = info.data.get("base_delay_seconds", 60)
        if value < base_delay:
            raise ValueError("max_delay_seconds must be at least base_delay_seconds")
        return value


class EmailDeliveryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(default="email-delivery-policy-v1", min_length=1, max_length=50)
    max_recipients: int = Field(default=50, ge=1, le=500)
    max_subject_length: int = Field(default=998, ge=1, le=998)
    max_text_body_length: int = Field(default=200_000, ge=1, le=1_000_000)
    max_html_body_length: int = Field(default=500_000, ge=1, le=2_000_000)
    retry: EmailRetryPolicy = Field(default_factory=EmailRetryPolicy)


class EmailDeliveryRequest(BaseModel):
    """Provider-neutral request; secrets and provider-specific fields are excluded."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = EMAIL_DELIVERY_CONTRACT_VERSION
    message_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)
    recipients: list[str] = Field(min_length=1, max_length=500)
    subject: str = Field(min_length=1, max_length=998)
    text_body: str = Field(min_length=1, max_length=1_000_000)
    html_body: str | None = Field(default=None, max_length=2_000_000)
    template_name: str = Field(min_length=1, max_length=100)
    template_version: str = Field(min_length=1, max_length=40)
    requested_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict, max_length=20)

    @field_validator("recipients", mode="before")
    @classmethod
    def normalize_recipients(cls, values: Sequence[str]) -> list[str]:
        if not isinstance(values, (list, tuple, set)):
            raise ValueError("recipients must be a list")
        normalized = sorted({str(value).strip().lower() for value in values if str(value).strip()})
        if not normalized:
            raise ValueError("recipients must not be empty")
        for recipient in normalized:
            if not _EMAIL_RE.fullmatch(recipient):
                raise ValueError(f"invalid email recipient: {recipient}")
        return normalized

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        value = value.strip()
        if "\r" in value or "\n" in value:
            raise ValueError("email subject must not contain CR/LF")
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if "\r" in str(key) or "\n" in str(key) or "\r" in item or "\n" in item:
                raise ValueError("email metadata must not contain CR/LF")
        return value

    @field_validator("requested_at", mode="before")
    @classmethod
    def normalize_requested_at(cls, value: datetime | str) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("requested_at must be a datetime")
        return as_utc_naive(value)


class EmailDeliveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = EMAIL_DELIVERY_CONTRACT_VERSION
    algorithm_version: str = EMAIL_DELIVERY_ALGORITHM_VERSION
    status: EmailDeliveryStatus
    message_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)
    input_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    provider_message_id: str | None = Field(default=None, max_length=300)
    attempt: int = Field(default=1, ge=1, le=100)
    failure_kind: EmailFailureKind | None = None
    error_code: str | None = Field(default=None, max_length=100)
    error_detail: str | None = Field(default=None, max_length=2_000)
    next_retry_at: datetime | None = None
    observed_at: datetime


class EmailDeliveryPort(Protocol):
    """Adapter interface implemented by the MOCK and SMTP providers."""

    def send(self, request: EmailDeliveryRequest) -> EmailDeliveryResult:
        ...


def render_email_template(template: EmailTemplate, context: Mapping[str, object]) -> tuple[str, str, str | None]:
    """Render subject/text/html and fail closed when a placeholder is missing."""

    try:
        subject = Template(template.subject).substitute(context)
        text_body = Template(template.text_body).substitute(context)
        html_body = Template(template.html_body).substitute(context) if template.html_body is not None else None
    except (KeyError, ValueError) as exc:
        raise ValueError(f"email template context is incomplete or invalid: {exc}") from exc
    if "\r" in subject or "\n" in subject:
        raise ValueError("rendered email subject must not contain CR/LF")
    return subject, text_body, html_body


def build_email_request(
    *,
    message_id: str,
    idempotency_key: str,
    recipients: Sequence[str],
    template: EmailTemplate,
    context: Mapping[str, object],
    requested_at: datetime | None = None,
    metadata: Mapping[str, str] | None = None,
    policy: EmailDeliveryPolicy | None = None,
) -> EmailDeliveryRequest:
    """Render a versioned template into a validated, provider-neutral request."""

    policy = policy or EmailDeliveryPolicy()
    if len(recipients) > policy.max_recipients:
        raise ValueError(f"recipient count exceeds {policy.max_recipients}")
    subject, text_body, html_body = render_email_template(template, context)
    if len(subject) > policy.max_subject_length:
        raise ValueError("rendered email subject exceeds policy limit")
    if len(text_body) > policy.max_text_body_length:
        raise ValueError("rendered text body exceeds policy limit")
    if html_body is not None and len(html_body) > policy.max_html_body_length:
        raise ValueError("rendered HTML body exceeds policy limit")
    return EmailDeliveryRequest(
        message_id=message_id,
        idempotency_key=idempotency_key,
        recipients=list(recipients),
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        template_name=template.name,
        template_version=template.version,
        requested_at=requested_at or utc_now(),
        metadata=dict(metadata or {}),
    )


def delivery_input_signature(request: EmailDeliveryRequest, *, policy: EmailDeliveryPolicy | None = None) -> str:
    """Stable signature for idempotency and audit; evaluation time is excluded."""

    policy = policy or EmailDeliveryPolicy()
    payload = {
        "contract_version": EMAIL_DELIVERY_CONTRACT_VERSION,
        "algorithm_version": EMAIL_DELIVERY_ALGORITHM_VERSION,
        "policy": policy.model_dump(mode="json"),
        "request": request.model_dump(mode="json", exclude={"requested_at"}),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def retry_at_for_failure(
    *,
    attempt: int,
    failure_kind: EmailFailureKind,
    now: datetime | None = None,
    policy: EmailRetryPolicy | None = None,
) -> datetime | None:
    """Return a bounded retry time only for transient provider failures."""

    policy = policy or EmailRetryPolicy()
    if attempt < 1 or attempt >= policy.max_attempts:
        return None
    if failure_kind not in {EmailFailureKind.TRANSIENT_PROVIDER, EmailFailureKind.RATE_LIMITED}:
        return None
    delay = min(policy.max_delay_seconds, policy.base_delay_seconds * (2 ** (attempt - 1)))
    return as_utc_naive(now or utc_now()) + timedelta(seconds=delay)


def build_delivery_result(
    request: EmailDeliveryRequest,
    *,
    status: EmailDeliveryStatus,
    attempt: int = 1,
    provider_message_id: str | None = None,
    failure_kind: EmailFailureKind | None = None,
    error_code: str | None = None,
    error_detail: str | None = None,
    now: datetime | None = None,
    policy: EmailRetryPolicy | None = None,
) -> EmailDeliveryResult:
    """Build a result with consistent retry semantics and a stable request signature."""

    observed_at = as_utc_naive(now or utc_now())
    next_retry_at = None
    if status == EmailDeliveryStatus.RETRYABLE_FAILURE:
        if failure_kind is None:
            raise ValueError("retryable failure requires failure_kind")
        next_retry_at = retry_at_for_failure(attempt=attempt, failure_kind=failure_kind, now=observed_at, policy=policy)
        if next_retry_at is None:
            raise ValueError("retryable failure is not eligible for another retry")
    elif failure_kind in {EmailFailureKind.TRANSIENT_PROVIDER, EmailFailureKind.RATE_LIMITED} and status != EmailDeliveryStatus.RETRYABLE_FAILURE:
        raise ValueError("transient failure kinds require RETRYABLE_FAILURE status")
    if status == EmailDeliveryStatus.SENT and not provider_message_id:
        raise ValueError("SENT result requires provider_message_id")
    return EmailDeliveryResult(
        status=status,
        message_id=request.message_id,
        idempotency_key=request.idempotency_key,
        input_signature=delivery_input_signature(request, policy=EmailDeliveryPolicy(retry=policy) if policy else None),
        provider_message_id=provider_message_id,
        attempt=attempt,
        failure_kind=failure_kind,
        error_code=error_code,
        error_detail=error_detail,
        next_retry_at=next_retry_at,
        observed_at=observed_at,
    )
