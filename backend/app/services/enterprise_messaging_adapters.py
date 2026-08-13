"""Slack, Feishu and WeCom incoming-webhook adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.time import utc_now
from app.domain.enterprise_messaging import (
    EnterpriseMessageFailureKind,
    EnterpriseMessagePort,
    EnterpriseMessageRequest,
    EnterpriseMessageResult,
    EnterpriseMessageStatus,
    message_input_signature,
)


@dataclass(frozen=True)
class EnterpriseWebhookAdapterConfig:
    endpoint_url: str
    timeout_seconds: float = 10
    authorization_token: str | None = None

    def __post_init__(self) -> None:
        if not self.endpoint_url.startswith(("http://", "https://")) or "\r" in self.endpoint_url or "\n" in self.endpoint_url:
            raise ValueError("enterprise messaging endpoint must be an http(s) URL without CR/LF")
        if self.timeout_seconds < 1 or self.timeout_seconds > 120:
            raise ValueError("enterprise messaging timeout must be between 1 and 120 seconds")
        if self.authorization_token is not None and (not self.authorization_token.strip() or "\r" in self.authorization_token or "\n" in self.authorization_token):
            raise ValueError("enterprise messaging authorization token is invalid")


def _display_text(request: EnterpriseMessageRequest) -> str:
    return f"{request.title}\n{request.text}".strip() if request.title else request.text


class _EnterpriseWebhookAdapter(EnterpriseMessagePort):
    provider_name = "enterprise"

    def __init__(self, config: EnterpriseWebhookAdapterConfig, *, client: httpx.Client | None = None) -> None:
        self.config = config
        self._client = client or httpx.Client(timeout=config.timeout_seconds, follow_redirects=False)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def _payload(self, request: EnterpriseMessageRequest) -> dict[str, Any]:
        raise NotImplementedError

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": "opportunity-radar-enterprise-messaging/1"}
        if self.config.authorization_token:
            headers["Authorization"] = f"Bearer {self.config.authorization_token}"
        return headers

    def _provider_error(self, response: httpx.Response) -> tuple[EnterpriseMessageFailureKind, str, str] | None:
        return None

    def send(self, request: EnterpriseMessageRequest) -> EnterpriseMessageResult:
        signature = message_input_signature(request)
        now = utc_now()
        if request.provider != self.provider_name:
            return EnterpriseMessageResult(
                status=EnterpriseMessageStatus.INVALID,
                attempt=request.attempt,
                input_signature=signature,
                observed_at=now,
                failure_kind=EnterpriseMessageFailureKind.INVALID_DESTINATION,
                error_code="PROVIDER_MISMATCH",
                error_detail=f"request provider {request.provider!r} does not match {self.provider_name!r} adapter",
            )
        try:
            response = self._client.post(self.config.endpoint_url, json=self._payload(request), headers=self._headers())
        except httpx.RequestError as exc:
            return EnterpriseMessageResult(
                status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
                attempt=request.attempt,
                input_signature=signature,
                observed_at=now,
                failure_kind=EnterpriseMessageFailureKind.TRANSIENT_PROVIDER,
                error_code=f"{self.provider_name.upper()}_TRANSPORT_ERROR",
                error_detail=str(exc)[:2_000],
            )
        provider_error = self._provider_error(response)
        if provider_error is not None:
            kind, code, detail = provider_error
            return EnterpriseMessageResult(
                status=EnterpriseMessageStatus.PERMANENT_FAILURE,
                attempt=request.attempt,
                input_signature=signature,
                observed_at=now,
                failure_kind=kind,
                error_code=code,
                error_detail=detail,
            )
        if response.status_code in {408, 425, 429} or 500 <= response.status_code <= 599:
            return EnterpriseMessageResult(
                status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
                attempt=request.attempt,
                input_signature=signature,
                observed_at=now,
                failure_kind=EnterpriseMessageFailureKind.RATE_LIMITED if response.status_code == 429 else EnterpriseMessageFailureKind.TRANSIENT_PROVIDER,
                error_code=f"{self.provider_name.upper()}_HTTP_{response.status_code}",
                error_detail="enterprise messaging provider returned a retryable status",
            )
        if response.status_code < 200 or response.status_code >= 300:
            return EnterpriseMessageResult(
                status=EnterpriseMessageStatus.PERMANENT_FAILURE,
                attempt=request.attempt,
                input_signature=signature,
                observed_at=now,
                failure_kind=EnterpriseMessageFailureKind.AUTHENTICATION if response.status_code in {401, 403} else EnterpriseMessageFailureKind.INVALID_DESTINATION,
                error_code=f"{self.provider_name.upper()}_HTTP_{response.status_code}",
                error_detail="enterprise messaging provider rejected the message",
            )
        provider_message_id = response.headers.get("X-Request-ID") or response.headers.get("X-Message-ID") or f"{self.provider_name}-accepted-{signature[:20]}"
        return EnterpriseMessageResult(
            status=EnterpriseMessageStatus.SENT,
            attempt=request.attempt,
            input_signature=signature,
            observed_at=now,
            provider_message_id=provider_message_id,
        )


class SlackMessagingAdapter(_EnterpriseWebhookAdapter):
    provider_name = "slack"

    def _payload(self, request: EnterpriseMessageRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {"text": _display_text(request)}
        if request.blocks:
            payload["blocks"] = request.blocks
        return payload


class FeishuMessagingAdapter(_EnterpriseWebhookAdapter):
    provider_name = "feishu"

    def _payload(self, request: EnterpriseMessageRequest) -> dict[str, Any]:
        return {"msg_type": "text", "content": {"text": _display_text(request)}}

    def _provider_error(self, response: httpx.Response) -> tuple[EnterpriseMessageFailureKind, str, str] | None:
        try:
            body = response.json()
        except ValueError:
            return None
        code = body.get("code", body.get("StatusCode"))
        if response.status_code < 300 and code not in (None, 0, "0"):
            return EnterpriseMessageFailureKind.INVALID_DESTINATION, f"FEISHU_PROVIDER_{code}", str(body.get("msg", body.get("StatusMessage", "Feishu rejected the message")))[:2_000]
        return None


class WeComMessagingAdapter(_EnterpriseWebhookAdapter):
    provider_name = "wecom"

    def _payload(self, request: EnterpriseMessageRequest) -> dict[str, Any]:
        return {"msgtype": "text", "text": {"content": _display_text(request)}}

    def _provider_error(self, response: httpx.Response) -> tuple[EnterpriseMessageFailureKind, str, str] | None:
        try:
            body = response.json()
        except ValueError:
            return None
        code = body.get("errcode")
        if response.status_code < 300 and code not in (None, 0, "0"):
            kind = EnterpriseMessageFailureKind.AUTHENTICATION if code in {40001, 40014, 40016} else EnterpriseMessageFailureKind.INVALID_DESTINATION
            return kind, f"WECOM_PROVIDER_{code}", str(body.get("errmsg", "WeCom rejected the message"))[:2_000]
        return None


# Short aliases make provider selection tables readable without hiding the
# explicit MessagingAdapter names used by integrations.
SlackAdapter = SlackMessagingAdapter
FeishuAdapter = FeishuMessagingAdapter
WeComAdapter = WeComMessagingAdapter
