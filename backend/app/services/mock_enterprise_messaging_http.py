"""HTTP adapter for the Docker-runnable Mock Enterprise Messaging service."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.time import utc_now
from app.domain.enterprise_messaging import (
    EnterpriseMessageFailureKind,
    EnterpriseMessagePort,
    EnterpriseMessageRequest,
    EnterpriseMessageResult,
    EnterpriseMessageStatus,
)


@dataclass(frozen=True)
class MockEnterpriseMessagingHTTPConfig:
    base_url: str
    timeout_seconds: float = 10

    def __post_init__(self) -> None:
        if not self.base_url.startswith(("http://", "https://")) or "\r" in self.base_url or "\n" in self.base_url:
            raise ValueError("mock enterprise messaging URL must be an http(s) URL without CR/LF")
        if self.timeout_seconds < 1 or self.timeout_seconds > 120:
            raise ValueError("mock enterprise messaging timeout must be between 1 and 120 seconds")


class MockEnterpriseMessagingHTTPService(EnterpriseMessagePort):
    """Transport adapter that requires an explicitly labeled MOCK response."""

    def __init__(self, config: MockEnterpriseMessagingHTTPConfig) -> None:
        self.config = config

    @staticmethod
    def _failure(request: EnterpriseMessageRequest, *, status: EnterpriseMessageStatus, kind: EnterpriseMessageFailureKind, code: str, detail: str) -> EnterpriseMessageResult:
        return EnterpriseMessageResult(
            status=status,
            attempt=request.attempt,
            input_signature=None,
            observed_at=utc_now(),
            failure_kind=kind,
            error_code=code,
            error_detail=detail,
        )

    def send(self, request: EnterpriseMessageRequest) -> EnterpriseMessageResult:
        try:
            response = httpx.post(
                f"{self.config.base_url.rstrip('/')}/v1/send",
                json=request.model_dump(mode="json"),
                timeout=self.config.timeout_seconds,
            )
        except httpx.RequestError as exc:
            return self._failure(
                request,
                status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
                kind=EnterpriseMessageFailureKind.TRANSIENT_PROVIDER,
                code="MOCK_ENTERPRISE_TRANSPORT_ERROR",
                detail=str(exc)[:2_000],
            )
        if response.status_code >= 500:
            return self._failure(
                request,
                status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
                kind=EnterpriseMessageFailureKind.TRANSIENT_PROVIDER,
                code=f"MOCK_ENTERPRISE_HTTP_{response.status_code}",
                detail="MOCK Enterprise Messaging service returned a server error",
            )
        if response.status_code >= 400:
            return self._failure(
                request,
                status=EnterpriseMessageStatus.PERMANENT_FAILURE,
                kind=EnterpriseMessageFailureKind.INVALID_DESTINATION,
                code=f"MOCK_ENTERPRISE_HTTP_{response.status_code}",
                detail="MOCK Enterprise Messaging service rejected the request",
            )
        try:
            body = response.json()
            if body.get("data_class") != "MOCK":
                raise ValueError("mock enterprise messaging response must be labeled MOCK")
            return EnterpriseMessageResult.model_validate(body["result"])
        except (KeyError, TypeError, ValueError) as exc:
            return self._failure(
                request,
                status=EnterpriseMessageStatus.PERMANENT_FAILURE,
                kind=EnterpriseMessageFailureKind.UNKNOWN,
                code="MOCK_ENTERPRISE_INVALID_RESPONSE",
                detail=str(exc)[:2_000],
            )
