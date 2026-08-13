from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, Request

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.auth import Principal, principal_from_api_token, principal_from_session, validate_csrf


def _legacy_authorized(provided: str | None) -> bool:
    expected = settings.api_key
    return bool(expected and provided and hmac.compare_digest(provided, expected))


def _authenticate(
    request: Request | None,
    *,
    authorization: str | None,
    legacy_key: str | None,
) -> Principal | None:
    if request is not None:
        session_token = request.cookies.get(settings.session_cookie_name)
        if session_token:
            with SessionLocal() as db:
                principal = principal_from_session(db, session_token)
            if principal is not None:
                request.state.principal = principal
                request.state.actor = principal.actor
                return principal
    if authorization and authorization.lower().startswith("bearer "):
        plain = authorization[7:].strip()
        if plain:
            with SessionLocal() as db:
                principal = principal_from_api_token(db, plain)
            if principal is not None:
                if request is not None:
                    request.state.principal = principal
                    request.state.actor = principal.actor
                return principal
    if settings.auth_mode != "rbac" and _legacy_authorized(legacy_key):
        principal = Principal(actor="legacy-api-key", role="OWNER", user_id=None, auth_type="legacy", scopes=frozenset({"read", "write", "admin"}))
        if request is not None:
            request.state.principal = principal
            request.state.actor = principal.actor
        return principal
    if settings.auth_mode == "rbac" and settings.allow_legacy_api_key and _legacy_authorized(legacy_key):
        principal = Principal(actor="legacy-api-key", role="OWNER", user_id=None, auth_type="legacy", scopes=frozenset({"read", "write", "admin"}))
        if request is not None:
            request.state.principal = principal
            request.state.actor = principal.actor
        return principal
    return None


def _require(
    scope: str,
    request: Request | None,
    authorization: str | None,
    legacy_key: str | None,
    csrf_token: str | None,
) -> Principal | None:
    if settings.auth_mode == "disabled":
        return None
    if settings.auth_mode == "write" and scope == "read":
        return None
    principal = _authenticate(request, authorization=authorization, legacy_key=legacy_key)
    if principal is None or not principal.has_scope(scope):
        raise HTTPException(status_code=401 if principal is None else 403, detail="authentication or permission required")
    if scope in {"write", "admin"} and principal.auth_type == "session":
        assert principal.session_id is not None
        with SessionLocal() as db:
            if not validate_csrf(db, principal.session_id, csrf_token):
                raise HTTPException(status_code=403, detail="valid CSRF token required")
    return principal


def require_read_auth(
    request: Request,
    authorization: str | None = Header(default=None),
    x_opportunity_radar_key: str | None = Header(default=None),
) -> Principal | None:
    return _require("read", request, authorization, x_opportunity_radar_key, None)


def require_write_auth(
    request: Request = None,
    authorization: str | None = Header(default=None),
    x_opportunity_radar_key: str | None = Header(default=None),
    x_csrf_token: str | None = Header(default=None),
) -> Principal | None:
    # Backward-compatible direct-call form used by legacy tests/tools:
    # require_write_auth("plain-api-key"). FastAPI always injects Request here.
    if isinstance(request, str):
        x_opportunity_radar_key = request
        request = None
    if not isinstance(authorization, str):
        authorization = None
    if not isinstance(x_opportunity_radar_key, str):
        x_opportunity_radar_key = None
    if not isinstance(x_csrf_token, str):
        x_csrf_token = None
    return _require("write", request, authorization, x_opportunity_radar_key, x_csrf_token)


def require_admin_auth(
    request: Request,
    authorization: str | None = Header(default=None),
    x_opportunity_radar_key: str | None = Header(default=None),
    x_csrf_token: str | None = Header(default=None),
) -> Principal | None:
    return _require("admin", request, authorization, x_opportunity_radar_key, x_csrf_token)
