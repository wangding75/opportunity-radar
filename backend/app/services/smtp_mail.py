"""Production SMTP adapter for the provider-neutral email contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from email.message import EmailMessage
import hashlib
import re
import smtplib
import ssl
from datetime import datetime
from typing import Any

from app.core.time import utc_now
from app.domain.email_delivery import (
    EmailDeliveryPort,
    EmailDeliveryRequest,
    EmailDeliveryResult,
    EmailDeliveryStatus,
    EmailFailureKind,
    build_delivery_result,
)

_EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")
_RETRYABLE_SMTP_CODES = {421, 450, 451, 452}
_AUTH_SMTP_CODES = {530, 534, 535, 538}
_INVALID_RECIPIENT_CODES = {550, 551, 553}


@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int = 587
    username: str | None = None
    password: str | None = field(default=None, repr=False)
    from_address: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    require_auth: bool = True
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        host = self.host.strip()
        sender = self.from_address.strip()
        if not host or "\r" in host or "\n" in host:
            raise ValueError("SMTP host is required and must not contain CR/LF")
        if not 1 <= self.port <= 65_535:
            raise ValueError("SMTP port must be between 1 and 65535")
        if not 1 <= self.timeout_seconds <= 120:
            raise ValueError("SMTP timeout must be between 1 and 120 seconds")
        if self.use_tls and self.use_ssl:
            raise ValueError("SMTP TLS and SSL cannot both be enabled")
        if not _EMAIL_RE.fullmatch(sender):
            raise ValueError("SMTP from_address must be a valid email address")
        if "\r" in sender or "\n" in sender:
            raise ValueError("SMTP from_address must not contain CR/LF")
        if self.require_auth and (not self.username or not self.password):
            raise ValueError("SMTP username and password are required when authentication is enabled")


class SMTPMailService(EmailDeliveryPort):
    """Synchronous SMTP transport with contract-level failure mapping."""

    def __init__(self, config: SMTPConfig) -> None:
        self.config = config

    @classmethod
    def from_settings(cls, settings: Any) -> "SMTPMailService":
        return cls(
            SMTPConfig(
                host=settings.smtp_host or "",
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                from_address=settings.smtp_from_address or "",
                use_tls=settings.smtp_use_tls,
                use_ssl=settings.smtp_use_ssl,
                require_auth=settings.smtp_require_auth,
                timeout_seconds=settings.smtp_timeout_seconds,
            )
        )

    def _message(self, request: EmailDeliveryRequest) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = request.subject
        message["From"] = self.config.from_address
        message["To"] = ", ".join(request.recipients)
        message_id = hashlib.sha256(request.message_id.encode("utf-8")).hexdigest()[:32]
        message["Message-ID"] = f"<or-{message_id}@{self.config.from_address.split('@', 1)[1]}>"
        message["X-Opportunity-Radar-Message-ID"] = request.message_id
        message["X-Opportunity-Radar-Idempotency-Key"] = request.idempotency_key
        message.set_content(request.text_body)
        if request.html_body:
            message.add_alternative(request.html_body, subtype="html")
        return message

    @staticmethod
    def _smtp_error(exc: smtplib.SMTPResponseException) -> tuple[EmailDeliveryStatus, EmailFailureKind, str]:
        code = int(getattr(exc, "smtp_code", 0) or 0)
        if code in _RETRYABLE_SMTP_CODES:
            kind = EmailFailureKind.RATE_LIMITED if code in {421, 450, 452} else EmailFailureKind.TRANSIENT_PROVIDER
            return EmailDeliveryStatus.RETRYABLE_FAILURE, kind, f"SMTP_{code}"
        if code in _AUTH_SMTP_CODES:
            return EmailDeliveryStatus.PERMANENT_FAILURE, EmailFailureKind.AUTHENTICATION, f"SMTP_{code}"
        if code in _INVALID_RECIPIENT_CODES:
            return EmailDeliveryStatus.PERMANENT_FAILURE, EmailFailureKind.INVALID_RECIPIENT, f"SMTP_{code}"
        return EmailDeliveryStatus.PERMANENT_FAILURE, EmailFailureKind.POLICY_BLOCKED, f"SMTP_{code or 'UNKNOWN'}"

    def _failure(self, request: EmailDeliveryRequest, *, status: EmailDeliveryStatus, kind: EmailFailureKind, code: str, detail: str, now: datetime) -> EmailDeliveryResult:
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
        message = self._message(request)
        client = None
        try:
            if self.config.use_ssl:
                client = smtplib.SMTP_SSL(self.config.host, self.config.port, timeout=self.config.timeout_seconds, context=ssl.create_default_context())
            else:
                client = smtplib.SMTP(self.config.host, self.config.port, timeout=self.config.timeout_seconds)
            client.ehlo()
            if self.config.use_tls:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            if self.config.require_auth:
                client.login(self.config.username, self.config.password)
            client.send_message(message, from_addr=self.config.from_address, to_addrs=request.recipients)
            return build_delivery_result(
                request,
                status=EmailDeliveryStatus.SENT,
                provider_message_id=message["Message-ID"].strip("<>") if message["Message-ID"] else None,
                now=now,
            )
        except smtplib.SMTPAuthenticationError as exc:
            return self._failure(
                request,
                status=EmailDeliveryStatus.PERMANENT_FAILURE,
                kind=EmailFailureKind.AUTHENTICATION,
                code=f"SMTP_{getattr(exc, 'smtp_code', 0) or 'AUTH'}",
                detail="SMTP authentication failed",
                now=now,
            )
        except smtplib.SMTPConnectError as exc:
            return self._failure(
                request,
                status=EmailDeliveryStatus.RETRYABLE_FAILURE,
                kind=EmailFailureKind.TRANSIENT_PROVIDER,
                code="SMTP_CONNECT_ERROR",
                detail=str(exc)[:2_000],
                now=now,
            )
        except smtplib.SMTPResponseException as exc:
            status, kind, code = self._smtp_error(exc)
            detail = str(getattr(exc, "smtp_error", b"") or exc)[:2_000]
            return self._failure(request, status=status, kind=kind, code=code, detail=detail, now=now)
        except (ssl.SSLError,):
            return self._failure(
                request,
                status=EmailDeliveryStatus.PERMANENT_FAILURE,
                kind=EmailFailureKind.UNKNOWN,
                code="SMTP_TLS_ERROR",
                detail="SMTP TLS negotiation failed",
                now=now,
            )
        except (TimeoutError, OSError, smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError) as exc:
            return self._failure(
                request,
                status=EmailDeliveryStatus.RETRYABLE_FAILURE,
                kind=EmailFailureKind.TRANSIENT_PROVIDER,
                code="SMTP_TRANSPORT_ERROR",
                detail=str(exc)[:2_000],
                now=now,
            )
        except ValueError as exc:
            return self._failure(
                request,
                status=EmailDeliveryStatus.PERMANENT_FAILURE,
                kind=EmailFailureKind.UNKNOWN,
                code="SMTP_CONFIGURATION_ERROR",
                detail=str(exc)[:2_000],
                now=now,
            )
        finally:
            if client is not None:
                try:
                    client.quit()
                except (OSError, smtplib.SMTPException):
                    client.close()
