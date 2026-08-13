from dataclasses import replace
from datetime import datetime
import smtplib
import ssl

import pytest

from app.core.config import settings, validate_runtime_settings
from app.domain.email_delivery import EmailDeliveryStatus, EmailFailureKind, EmailTemplate, build_email_request
from app.services import email_delivery_queue as queue
from app.services.smtp_mail import SMTPConfig, SMTPMailService


def _request():
    return build_email_request(
        message_id="synthetic-smtp-message",
        idempotency_key="synthetic-smtp-message:v1",
        recipients=["recipient@example.com"],
        template=EmailTemplate(name="synthetic.smtp", version="v1", subject="SYNTHETIC alert", text_body="SYNTHETIC body"),
        context={},
        requested_at=datetime(2026, 8, 12, 12),
        metadata={"data_class": "SYNTHETIC"},
    )


class FakeSMTP:
    instances = []
    failure = None

    def __init__(self, host, port, timeout=None, context=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.context = context
        self.started_tls = False
        self.logged_in = None
        self.message = None
        self.from_addr = None
        self.to_addrs = None
        FakeSMTP.instances.append(self)

    def ehlo(self):
        return (250, b"ok")

    def starttls(self, context=None):
        self.started_tls = True
        self.tls_context = context

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message, from_addr=None, to_addrs=None):
        if FakeSMTP.failure is not None:
            raise FakeSMTP.failure
        self.message = message
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        return {}

    def quit(self):
        return (221, b"bye")

    def close(self):
        return None


def _config(**overrides):
    values = {
        "host": "smtp.synthetic.example",
        "port": 587,
        "username": "smtp-user",
        "password": "smtp-password",
        "from_address": "alerts@example.com",
        "use_tls": True,
        "use_ssl": False,
        "require_auth": True,
        "timeout_seconds": 5,
    }
    values.update(overrides)
    return SMTPConfig(**values)


def setup_function():
    FakeSMTP.instances = []
    FakeSMTP.failure = None


def test_smtp_adapter_sends_plain_text_over_starttls_without_exposing_password(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    result = SMTPMailService(_config()).send(_request())
    client = FakeSMTP.instances[0]
    assert result.status == EmailDeliveryStatus.SENT
    assert result.provider_message_id.startswith("or-")
    assert client.started_tls is True
    assert client.logged_in == ("smtp-user", "smtp-password")
    assert client.from_addr == "alerts@example.com"
    assert client.to_addrs == ["recipient@example.com"]
    assert client.message["X-Opportunity-Radar-Message-ID"] == "synthetic-smtp-message"
    assert "smtp-password" not in repr(_config())


def test_smtp_ssl_transport_and_retryable_451_are_mapped_to_contract(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    result = SMTPMailService(_config(use_tls=False, use_ssl=True, port=465)).send(_request())
    client = FakeSMTP.instances[0]
    assert result.status == EmailDeliveryStatus.SENT
    assert isinstance(client.context, ssl.SSLContext)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    FakeSMTP.failure = smtplib.SMTPResponseException(451, b"temporary provider failure")
    retry = SMTPMailService(_config()).send(_request())
    assert retry.status == EmailDeliveryStatus.RETRYABLE_FAILURE
    assert retry.failure_kind == EmailFailureKind.TRANSIENT_PROVIDER
    assert retry.error_code == "SMTP_451"
    assert retry.next_retry_at is not None


def test_smtp_authentication_and_transport_failures_never_report_success(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    FakeSMTP.failure = smtplib.SMTPAuthenticationError(535, b"bad credentials")
    auth = SMTPMailService(_config()).send(_request())
    assert auth.status == EmailDeliveryStatus.PERMANENT_FAILURE
    assert auth.failure_kind == EmailFailureKind.AUTHENTICATION

    FakeSMTP.failure = smtplib.SMTPServerDisconnected("connection dropped")
    transport = SMTPMailService(_config()).send(_request())
    assert transport.status == EmailDeliveryStatus.RETRYABLE_FAILURE
    assert transport.failure_kind == EmailFailureKind.TRANSIENT_PROVIDER


def test_smtp_configuration_boundaries_and_production_tls_fail_closed():
    with pytest.raises(ValueError, match="host"):
        SMTPConfig(host="", from_address="alerts@example.com", username="u", password="p")
    with pytest.raises(ValueError, match="both"):
        SMTPConfig(host="smtp.example.com", from_address="alerts@example.com", username="u", password="p", use_tls=True, use_ssl=True)
    with pytest.raises(ValueError, match="authentication"):
        SMTPConfig(host="smtp.example.com", from_address="alerts@example.com")

    missing_host = replace(
        settings,
        email_delivery_enabled=True,
        email_delivery_provider="smtp",
        email_delivery_recipients=("recipient@example.com",),
        smtp_host=None,
        smtp_from_address="alerts@example.com",
        smtp_username="u",
        smtp_password="p",
    )
    with pytest.raises(ValueError, match="SMTP_HOST"):
        validate_runtime_settings(missing_host)
    plaintext_production = replace(
        settings,
        app_env="production",
        auth_mode="rbac",
        database_url="postgresql+psycopg://user@db/radar",
        email_delivery_enabled=True,
        email_delivery_provider="smtp",
        email_delivery_recipients=("recipient@example.com",),
        smtp_host="smtp.example.com",
        smtp_from_address="alerts@example.com",
        smtp_username="u",
        smtp_password="p",
        smtp_use_tls=False,
        smtp_use_ssl=False,
    )
    with pytest.raises(ValueError, match="TLS or SSL"):
        validate_runtime_settings(plaintext_production)


def test_default_provider_selection_can_build_smtp_adapter_without_real_network(monkeypatch):
    smtp_settings = replace(
        settings,
        email_delivery_provider="smtp",
        smtp_host="smtp.synthetic.example",
        smtp_from_address="alerts@example.com",
        smtp_username="u",
        smtp_password="p",
    )
    monkeypatch.setattr(queue, "settings", smtp_settings)
    monkeypatch.setattr(queue, "_default_port", None)
    adapter = queue.get_default_email_delivery_port()
    assert isinstance(adapter, SMTPMailService)
