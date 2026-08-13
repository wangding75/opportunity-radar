"""HTTP adapter for the Docker-runnable MOCK Mail service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import httpx

from app.core.time import utc_now
from app.domain.email_delivery import (
    EmailDeliveryPort,
    EmailDeliveryRequest,
    EmailDeliveryResult,
    EmailDeliveryStatus,
    EmailFailureKind,
    build_delivery_result,
)


@dataclass(frozen=True)
class MockMailHTTPConfig:
    base_url: str
    timeout_seconds: float = 10

    def __post_init__(self) -> None:
        if not self.base_url.startswith(("http://", "https://")) or "\r" in self.base_url or "\n" in self.base_url:
            raise ValueError("mock mail URL must be an http(s) URL without CR/LF")
        if self.timeout_seconds < 1 or self.timeout_seconds > 120:
            raise ValueError("mock mail timeout must be between 1 and 120 seconds")


class MockMailHTTPService(EmailDeliveryPort):
    """Provider adapter that keeps Docker acceptance data explicitly MOCK."""

    def __init__(self, config: MockMailHTTPConfig) -> None:
        self.config = config

    @classmethod
    def from_settings(cls, settings) -> "MockMailHTTPService":
        return cls(MockMailHTTPConfig(settings.mock_mail_url, settings.mock_mail_timeout_seconds))

    @staticmethod
    def _failure(
        request: EmailDeliveryRequest,
        *,
        status: EmailDeliveryStatus,
        kind: EmailFailureKind,
        code: str,
        detail: str,
        now: datetime,
    ) -> EmailDeliveryResult:
        return build_delivery_result(
            request,
            status=status,
            attempt=1,
            failure_kind=kind,
            error_code=code,
            error_detail=detail,
            now=now,
        )

    def send(self, request: EmailDeliveryRequest) -> EmailDeliveryResult:
        now = utc_now()
        try:
            response = httpx.post(
                f"{self.config.base_url.rstrip('/')}/v1/send",
                json=request.model_dump(mode="json"),
                timeout=self.config.timeout_seconds,
            )
        except httpx.RequestError as exc:
            return self._failure(
                request,
                status=EmailDeliveryStatus.RETRYABLE_FAILURE,
                kind=EmailFailureKind.TRANSIENT_PROVIDER,
                code="MOCK_MAIL_TRANSPORT_ERROR",
                detail=str(exc)[:2_000],
                now=now,
            )
        if response.status_code >= 500:
            return self._failure(
                request,
                status=EmailDeliveryStatus.RETRYABLE_FAILURE,
                kind=EmailFailureKind.TRANSIENT_PROVIDER,
                code=f"MOCK_MAIL_HTTP_{response.status_code}",
                detail="MOCK Mail service returned a server error",
                now=now,
            )
        if response.status_code >= 400:
            kind = EmailFailureKind.INVALID_RECIPIENT if response.status_code == 422 else EmailFailureKind.POLICY_BLOCKED
            return self._failure(
                request,
                status=EmailDeliveryStatus.PERMANENT_FAILURE,
                kind=kind,
                code=f"MOCK_MAIL_HTTP_{response.status_code}",
                detail="MOCK Mail service rejected the request",
                now=now,
            )
        try:
            body = response.json()
            if body.get("data_class") != "MOCK":
                raise ValueError("mock mail response must be labeled MOCK")
            return EmailDeliveryResult.model_validate(body["result"])
        except (KeyError, TypeError, ValueError) as exc:
            return self._failure(
                request,
                status=EmailDeliveryStatus.PERMANENT_FAILURE,
                kind=EmailFailureKind.UNKNOWN,
                code="MOCK_MAIL_INVALID_RESPONSE",
                detail=str(exc)[:2_000],
                now=now,
            )
