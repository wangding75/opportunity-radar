from __future__ import annotations

import re
from copy import deepcopy
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.domain.schemas import CollectedRecord

SENSITIVE_KEY_FRAGMENTS = {
    "authorization", "auth_token", "access_token", "refresh_token", "token", "cookie", "password", "passwd",
    "phone", "mobile", "email", "address", "latitude", "longitude", "lat", "lng", "imei", "imsi", "device_id",
    "id_card", "identity", "session_key", "session_token", "secret", "api_key", "apikey", "credential", "csrf",
}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
CN_MOBILE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
LOG_SECRET_RE = re.compile(r"(?i)\b(authorization|auth_token|access_token|refresh_token|token|password|passwd|secret|api_key|apikey|credential|csrf)=([^\s&,]+)")
URL_CREDENTIAL_RE = re.compile(r"(?i)(://[^:/\s]+:)[^@/\s]+(@)")


def _is_sensitive_key(key: object) -> bool:
    raw = str(key).strip().replace("-", "_").replace(" ", "_")
    raw = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", raw)
    normalized = raw.lower()
    for fragment in SENSITIVE_KEY_FRAGMENTS:
        if fragment in {"lat", "lng"}:
            if normalized == fragment or normalized.endswith(f"_{fragment}") or normalized.startswith(f"{fragment}_"):
                return True
            continue
        if normalized == fragment or normalized.endswith(f"_{fragment}") or normalized.startswith(f"{fragment}_"):
            return True
    return False


def sanitize_payload(value):
    if isinstance(value, dict):
        return {
            str(key): sanitize_payload(child)
            for key, child in value.items()
            if not _is_sensitive_key(key)
        }
    if isinstance(value, list):
        return [sanitize_payload(child) for child in value]
    return value


def redact_text(value: str) -> str:
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    return CN_MOBILE_RE.sub("[REDACTED_PHONE]", value)


def sanitize_query(value: str | None) -> str:
    """Remove sensitive query fields before an API query is persisted to audit."""

    if not value:
        return ""
    safe_query = [
        (key, val)
        for key, val in parse_qsl(value, keep_blank_values=True)
        if not _is_sensitive_key(key)
    ]
    return urlencode(safe_query)


def redact_log_text(value: str) -> str:
    """Redact common secret forms from structured messages and tracebacks."""

    redacted = LOG_SECRET_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
    return URL_CREDENTIAL_RE.sub(r"\1[REDACTED]\2", redacted)


def sanitize_url(value: str | None) -> str | None:
    if not value:
        return value
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return None
    safe_query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_sensitive_key(key)
    ]
    # Never persist URL userinfo. It can contain basic-auth credentials even when
    # every query parameter is otherwise sanitized. Rebuild netloc exclusively
    # from the parsed hostname/port.
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    try:
        port = parts.port
    except ValueError:
        return None
    netloc = f"{host}:{port}" if port is not None else host
    return urlunsplit((parts.scheme, netloc, parts.path, urlencode(safe_query), ""))


def sanitize_instrumented(record: CollectedRecord) -> CollectedRecord:
    clean = record.model_copy(deep=True)
    clean.title = redact_text(clean.title)
    clean.text = redact_text(clean.text)
    clean.url = sanitize_url(clean.url)
    clean.payload = sanitize_payload(deepcopy(clean.payload))
    return clean
