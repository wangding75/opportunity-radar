from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "Opportunity Radar"
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parents[3] / 'opportunity_radar.db'}",
    )
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    google_trends_geos: tuple[str, ...] = tuple(
        geo.strip().upper() for geo in os.getenv("GOOGLE_TRENDS_GEOS", "US,TW").split(",") if geo.strip()
    )
    max_collect_items: int = int(os.getenv("MAX_COLLECT_ITEMS", "50"))
    max_request_body_bytes: int = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(25 * 1024 * 1024)))
    analysis_provider: str = os.getenv("ANALYSIS_PROVIDER", "heuristic").strip().lower()
    analysis_provider_priority: str = os.getenv("ANALYSIS_PROVIDER_PRIORITY", "").strip().lower()
    analysis_provider_selection_policy: str = os.getenv("ANALYSIS_PROVIDER_SELECTION_POLICY", "priority").strip().lower()
    analysis_provider_retry_attempts: int = int(os.getenv("ANALYSIS_PROVIDER_RETRY_ATTEMPTS", "2"))
    analysis_provider_retry_backoff_seconds: float = float(os.getenv("ANALYSIS_PROVIDER_RETRY_BACKOFF_SECONDS", "0.25"))
    analysis_provider_circuit_open_seconds: float = float(os.getenv("ANALYSIS_PROVIDER_CIRCUIT_OPEN_SECONDS", "60"))
    analysis_http_endpoint: str | None = os.getenv("ANALYSIS_HTTP_ENDPOINT")
    analysis_http_api_key: str | None = os.getenv("ANALYSIS_HTTP_API_KEY")
    analysis_http_timeout_seconds: float = float(os.getenv("ANALYSIS_HTTP_TIMEOUT_SECONDS", "20"))
    analysis_batch_limit: int = int(os.getenv("ANALYSIS_BATCH_LIMIT", "5"))
    analysis_retry_base_minutes: int = int(os.getenv("ANALYSIS_RETRY_BASE_MINUTES", "15"))
    analysis_evidence_limit: int = int(os.getenv("ANALYSIS_EVIDENCE_LIMIT", "30"))
    analysis_evidence_text_chars: int = int(os.getenv("ANALYSIS_EVIDENCE_TEXT_CHARS", "2000"))
    analysis_http_max_response_bytes: int = int(os.getenv("ANALYSIS_HTTP_MAX_RESPONSE_BYTES", "1000000"))
    discovery_feeds_json: str = os.getenv("DISCOVERY_FEEDS_JSON", "").strip()
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()
    auth_mode: str = os.getenv("AUTH_MODE", "disabled").strip().lower()
    api_key: str | None = os.getenv("API_KEY")
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "or_session").strip() or "or_session"
    csrf_cookie_name: str = os.getenv("CSRF_COOKIE_NAME", "or_csrf").strip() or "or_csrf"
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    auth_record_retention_days: int = int(os.getenv("AUTH_RECORD_RETENTION_DAYS", "90"))
    login_failure_limit: int = int(os.getenv("LOGIN_FAILURE_LIMIT", "5"))
    login_lock_minutes: int = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
    login_rate_limit_window_seconds: int = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60"))
    login_rate_limit_max_attempts: int = int(os.getenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "10"))
    login_rate_limit_block_seconds: int = int(os.getenv("LOGIN_RATE_LIMIT_BLOCK_SECONDS", "60"))
    allow_legacy_api_key: bool = os.getenv("ALLOW_LEGACY_API_KEY", "false").strip().lower() in {"1", "true", "yes", "on"}
    audit_actor_header: str = os.getenv("AUDIT_ACTOR_HEADER", "X-Actor").strip() or "X-Actor"
    audit_trusted_proxy_actor: bool = os.getenv("AUDIT_TRUSTED_PROXY_ACTOR", "false").strip().lower() in {"1", "true", "yes", "on"}
    trusted_proxy_cidrs: tuple[str, ...] = tuple(
        item.strip() for item in os.getenv("TRUSTED_PROXY_CIDRS", "").split(",") if item.strip()
    )
    collection_run_retention_days: int = int(os.getenv("COLLECTION_RUN_RETENTION_DAYS", "180"))
    audit_log_retention_days: int = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "365"))
    alert_event_retention_days: int = int(os.getenv("ALERT_EVENT_RETENTION_DAYS", "365"))
    email_delivery_enabled: bool = os.getenv("EMAIL_DELIVERY_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    webhook_delivery_enabled: bool = os.getenv("WEBHOOK_DELIVERY_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    webhook_delivery_timeout_seconds: float = float(os.getenv("WEBHOOK_DELIVERY_TIMEOUT_SECONDS", "10"))
    webhook_allowed_hosts: tuple[str, ...] = tuple(
        host.strip().lower().rstrip(".") for host in os.getenv("WEBHOOK_ALLOWED_HOSTS", "").split(",") if host.strip()
    )
    email_delivery_provider: str = os.getenv("EMAIL_DELIVERY_PROVIDER", "mock").strip().lower() or "mock"
    email_delivery_recipients: tuple[str, ...] = tuple(
        address.strip().lower() for address in os.getenv("EMAIL_DELIVERY_RECIPIENTS", "").split(",") if address.strip()
    )
    mock_mail_url: str = os.getenv("MOCK_MAIL_URL", "http://mock-mail:8082").strip() or "http://mock-mail:8082"
    mock_mail_timeout_seconds: float = float(os.getenv("MOCK_MAIL_TIMEOUT_SECONDS", "10"))
    smtp_host: str | None = os.getenv("SMTP_HOST") or None
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME") or None
    smtp_password: str | None = os.getenv("SMTP_PASSWORD") or None
    smtp_from_address: str | None = os.getenv("SMTP_FROM_ADDRESS", os.getenv("SMTP_FROM", "")) or None
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes", "on"}
    smtp_require_auth: bool = os.getenv("SMTP_REQUIRE_AUTH", "true").strip().lower() in {"1", "true", "yes", "on"}
    smtp_timeout_seconds: float = float(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    raw_observation_retention_days: int = int(os.getenv("RAW_OBSERVATION_RETENTION_DAYS", "0"))
    raw_payload_archive_dir: str = os.getenv("RAW_PAYLOAD_ARCHIVE_DIR", "archives/raw-payloads").strip() or "archives/raw-payloads"
    raw_payload_archive_after_days: int = int(os.getenv("RAW_PAYLOAD_ARCHIVE_AFTER_DAYS", "90"))
    raw_payload_archive_batch_size: int = int(os.getenv("RAW_PAYLOAD_ARCHIVE_BATCH_SIZE", "1000"))
    worker_stale_seconds: int = int(os.getenv("WORKER_STALE_SECONDS", "180"))
    maintenance_worker_stale_seconds: int = int(os.getenv("MAINTENANCE_WORKER_STALE_SECONDS", "1800"))


settings = Settings()


def validate_runtime_settings(value: Settings = settings) -> None:
    if value.max_collect_items < 1 or value.max_collect_items > 100:
        raise ValueError("MAX_COLLECT_ITEMS must be between 1 and 100")
    if value.max_request_body_bytes < 1_048_576 or value.max_request_body_bytes > 104_857_600:
        raise ValueError("MAX_REQUEST_BODY_BYTES must be between 1 MiB and 100 MiB")
    if value.app_env not in {"development", "production", "test"}:
        raise ValueError("APP_ENV must be development, production or test")
    if value.auth_mode not in {"disabled", "write", "all", "rbac"}:
        raise ValueError("AUTH_MODE must be disabled, write, all or rbac")
    if value.app_env == "production":
        if value.auth_mode != "rbac":
            raise ValueError("production requires AUTH_MODE=rbac")
        if value.allow_legacy_api_key:
            raise ValueError("ALLOW_LEGACY_API_KEY must be false in production")
        if value.database_url.startswith("sqlite"):
            raise ValueError("production requires PostgreSQL DATABASE_URL")
    if value.login_failure_limit < 1 or value.login_failure_limit > 100:
        raise ValueError("LOGIN_FAILURE_LIMIT must be between 1 and 100")
    if value.login_lock_minutes < 1 or value.login_lock_minutes > 1440:
        raise ValueError("LOGIN_LOCK_MINUTES must be between 1 and 1440")
    if value.login_rate_limit_window_seconds < 1 or value.login_rate_limit_window_seconds > 86_400:
        raise ValueError("LOGIN_RATE_LIMIT_WINDOW_SECONDS must be between 1 and 86400")
    if value.login_rate_limit_max_attempts < 1 or value.login_rate_limit_max_attempts > 10_000:
        raise ValueError("LOGIN_RATE_LIMIT_MAX_ATTEMPTS must be between 1 and 10000")
    if value.login_rate_limit_block_seconds < 1 or value.login_rate_limit_block_seconds > 86_400:
        raise ValueError("LOGIN_RATE_LIMIT_BLOCK_SECONDS must be between 1 and 86400")
    for network in value.trusted_proxy_cidrs:
        try:
            ipaddress.ip_network(network, strict=False)
        except ValueError as exc:
            raise ValueError(f"TRUSTED_PROXY_CIDRS contains an invalid network: {network}") from exc
    if value.app_env == "production" and value.audit_trusted_proxy_actor and not value.trusted_proxy_cidrs:
        raise ValueError("AUDIT_TRUSTED_PROXY_ACTOR requires TRUSTED_PROXY_CIDRS in production")
    if value.email_delivery_provider not in {"mock", "mock_http", "smtp"}:
        raise ValueError("EMAIL_DELIVERY_PROVIDER must be mock, mock_http or smtp")
    if value.email_delivery_enabled and not value.email_delivery_recipients:
        raise ValueError("EMAIL_DELIVERY_RECIPIENTS is required when EMAIL_DELIVERY_ENABLED=true")
    if value.email_delivery_enabled and value.app_env == "production" and value.email_delivery_provider != "smtp":
        raise ValueError("production email delivery requires EMAIL_DELIVERY_PROVIDER=smtp")
    if value.webhook_delivery_timeout_seconds < 1 or value.webhook_delivery_timeout_seconds > 120:
        raise ValueError("WEBHOOK_DELIVERY_TIMEOUT_SECONDS must be between 1 and 120")
    if any("\r" in host or "\n" in host or "/" in host or " " in host for host in value.webhook_allowed_hosts):
        raise ValueError("WEBHOOK_ALLOWED_HOSTS must contain comma-separated hostnames")
    if not 1 <= value.smtp_port <= 65_535:
        raise ValueError("SMTP_PORT must be between 1 and 65535")
    if value.smtp_timeout_seconds < 1 or value.smtp_timeout_seconds > 120:
        raise ValueError("SMTP_TIMEOUT_SECONDS must be between 1 and 120")
    if not value.mock_mail_url.startswith(("http://", "https://")) or "\r" in value.mock_mail_url or "\n" in value.mock_mail_url:
        raise ValueError("MOCK_MAIL_URL must be an http(s) URL without CR/LF")
    if value.mock_mail_timeout_seconds < 1 or value.mock_mail_timeout_seconds > 120:
        raise ValueError("MOCK_MAIL_TIMEOUT_SECONDS must be between 1 and 120")
    if value.smtp_use_tls and value.smtp_use_ssl:
        raise ValueError("SMTP_USE_TLS and SMTP_USE_SSL cannot both be true")
    if value.email_delivery_provider == "smtp" and value.email_delivery_enabled:
        if not value.smtp_host:
            raise ValueError("SMTP_HOST is required when EMAIL_DELIVERY_PROVIDER=smtp")
        if not value.smtp_from_address:
            raise ValueError("SMTP_FROM_ADDRESS is required when EMAIL_DELIVERY_PROVIDER=smtp")
        if value.smtp_require_auth and (not value.smtp_username or not value.smtp_password):
            raise ValueError("SMTP_USERNAME and SMTP_PASSWORD are required when SMTP_REQUIRE_AUTH=true")
        if value.app_env == "production" and not (value.smtp_use_tls or value.smtp_use_ssl):
            raise ValueError("production SMTP requires TLS or SSL")
    if not 1 <= value.session_ttl_hours <= 24 * 30:
        raise ValueError("SESSION_TTL_HOURS must be between 1 and 720")
    if not 1 <= value.auth_record_retention_days <= 3650:
        raise ValueError("AUTH_RECORD_RETENTION_DAYS must be between 1 and 3650")
    if value.analysis_provider not in {"heuristic", "http"}:
        raise ValueError("ANALYSIS_PROVIDER must be heuristic or http")
    priority = [item.strip() for item in value.analysis_provider_priority.split(",") if item.strip()]
    if len(priority) != len(set(priority)):
        raise ValueError("ANALYSIS_PROVIDER_PRIORITY must not contain duplicates")
    if value.analysis_provider_selection_policy not in {"priority", "majority"}:
        raise ValueError("ANALYSIS_PROVIDER_SELECTION_POLICY must be priority or majority")
    unsupported_priority = sorted(set(priority) - {"heuristic", "http"})
    if unsupported_priority:
        raise ValueError(f"ANALYSIS_PROVIDER_PRIORITY contains unsupported provider(s): {unsupported_priority}")
    if value.analysis_provider == "http":
        endpoint = (value.analysis_http_endpoint or "").strip()
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("ANALYSIS_HTTP_ENDPOINT must be an http(s) URL when ANALYSIS_PROVIDER=http")
        if value.app_env == "production" and not endpoint.startswith("https://"):
            raise ValueError("production requires HTTPS ANALYSIS_HTTP_ENDPOINT")
    if not 1 <= value.analysis_provider_retry_attempts <= 5:
        raise ValueError("ANALYSIS_PROVIDER_RETRY_ATTEMPTS must be between 1 and 5")
    if not 0 <= value.analysis_provider_retry_backoff_seconds <= 60:
        raise ValueError("ANALYSIS_PROVIDER_RETRY_BACKOFF_SECONDS must be between 0 and 60")
    if not 1 <= value.analysis_provider_circuit_open_seconds <= 86_400:
        raise ValueError("ANALYSIS_PROVIDER_CIRCUIT_OPEN_SECONDS must be between 1 and 86400")
    if value.analysis_http_timeout_seconds < 1 or value.analysis_http_timeout_seconds > 300:
        raise ValueError("ANALYSIS_HTTP_TIMEOUT_SECONDS must be between 1 and 300")
    if not 1 <= value.analysis_batch_limit <= 100:
        raise ValueError("ANALYSIS_BATCH_LIMIT must be between 1 and 100")
    if not 1 <= value.analysis_retry_base_minutes <= 1440:
        raise ValueError("ANALYSIS_RETRY_BASE_MINUTES must be between 1 and 1440")
    if not 1 <= value.analysis_evidence_limit <= 100:
        raise ValueError("ANALYSIS_EVIDENCE_LIMIT must be between 1 and 100")
    if not 0 <= value.analysis_evidence_text_chars <= 20_000:
        raise ValueError("ANALYSIS_EVIDENCE_TEXT_CHARS must be between 0 and 20000")
    if not 1_024 <= value.analysis_http_max_response_bytes <= 10_000_000:
        raise ValueError("ANALYSIS_HTTP_MAX_RESPONSE_BYTES must be between 1024 and 10000000")
    for name, days in {"COLLECTION_RUN_RETENTION_DAYS": value.collection_run_retention_days, "AUDIT_LOG_RETENTION_DAYS": value.audit_log_retention_days, "ALERT_EVENT_RETENTION_DAYS": value.alert_event_retention_days, "RAW_OBSERVATION_RETENTION_DAYS": value.raw_observation_retention_days}.items():
        if days < 0 or days > 36500:
            raise ValueError(f"{name} must be between 0 and 36500")
    if value.worker_stale_seconds < 30 or value.worker_stale_seconds > 86400:
        raise ValueError("WORKER_STALE_SECONDS must be between 30 and 86400")
    if value.maintenance_worker_stale_seconds < value.worker_stale_seconds or value.maintenance_worker_stale_seconds > 86400:
        raise ValueError("MAINTENANCE_WORKER_STALE_SECONDS must be >= WORKER_STALE_SECONDS and <= 86400")
    if value.analysis_provider == "http" and value.worker_stale_seconds <= value.analysis_http_timeout_seconds + 30:
        raise ValueError("WORKER_STALE_SECONDS must exceed ANALYSIS_HTTP_TIMEOUT_SECONDS by more than 30 seconds")
    if not 1 <= value.raw_payload_archive_after_days <= 36500:
        raise ValueError("RAW_PAYLOAD_ARCHIVE_AFTER_DAYS must be between 1 and 36500")
    if not 1 <= value.raw_payload_archive_batch_size <= 10000:
        raise ValueError("RAW_PAYLOAD_ARCHIVE_BATCH_SIZE must be between 1 and 10000")
