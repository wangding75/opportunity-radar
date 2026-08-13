from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from starlette.requests import Request

from app.api import auth as auth_api
from app.core import request_identity, security
from app.core.config import Settings, validate_runtime_settings
from app.db.models import AuditLog
from app.db.session import SessionLocal
from app.main import app
from app.services import auth as auth_service
from app.services.auth import create_user, login_rate_limit_retry_after, record_login_failure
from app.core.time import utc_now


def _request(peer: str, **headers: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
        "client": (peer, 4567),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


def _patch_runtime_settings(monkeypatch, settings: Settings) -> None:
    monkeypatch.setattr(auth_api, "settings", settings)
    monkeypatch.setattr(auth_service, "settings", settings)
    monkeypatch.setattr(request_identity, "settings", settings)
    monkeypatch.setattr(security, "settings", settings)


def test_login_rate_limit_is_shared_sql_state_and_expires(monkeypatch):
    cfg = replace(
        auth_service.settings,
        login_rate_limit_window_seconds=30,
        login_rate_limit_max_attempts=2,
        login_rate_limit_block_seconds=20,
    )
    monkeypatch.setattr(auth_service, "settings", cfg)
    first = utc_now()
    with SessionLocal() as db:
        record_login_failure(db, "203.0.113.10", "Owner@Example.com", now=first)
        db.commit()
    with SessionLocal() as db:
        record_login_failure(db, "203.0.113.10", "owner@example.com", now=first + timedelta(seconds=1))
        db.commit()
    with SessionLocal() as independent_worker_db:
        retry_after = login_rate_limit_retry_after(independent_worker_db, "203.0.113.10", "OWNER@example.com", now=first + timedelta(seconds=2))
        assert retry_after is not None and retry_after > 0
        assert login_rate_limit_retry_after(independent_worker_db, "203.0.113.11", "owner@example.com", now=first + timedelta(seconds=2)) is None
        assert login_rate_limit_retry_after(independent_worker_db, "203.0.113.10", "owner@example.com", now=first + timedelta(seconds=31)) is None


def test_audit_actor_ignores_client_header_and_uses_principal(monkeypatch):
    cfg = Settings(
        auth_mode="rbac",
        app_env="test",
        database_url=auth_service.settings.database_url,
        login_rate_limit_max_attempts=20,
        login_rate_limit_block_seconds=1,
    )
    _patch_runtime_settings(monkeypatch, cfg)
    with SessionLocal() as db:
        create_user(db, "audit-owner", "AuditOwnerPassword-2026!", role="OWNER")
        db.commit()

    client = TestClient(app)
    failed = client.post(
        "/api/v1/auth/login",
        json={"username": "audit-anonymous", "password": "wrong-password"},
        headers={"X-Actor": "attacker"},
    )
    assert failed.status_code == 401
    login_log = _latest_audit("/api/v1/auth/login")
    assert login_log.actor.startswith("login:")
    assert "attacker" not in login_log.actor
    assert "audit-anonymous" not in login_log.actor

    logged_in = client.post(
        "/api/v1/auth/login",
        json={"username": "audit-owner", "password": "AuditOwnerPassword-2026!"},
        headers={"X-Actor": "attacker"},
    )
    assert logged_in.status_code == 200
    logout = client.post(
        "/api/v1/auth/logout",
        headers={"X-Actor": "attacker", "X-CSRF-Token": client.cookies.get(cfg.csrf_cookie_name)},
    )
    assert logout.status_code == 200
    assert _latest_audit("/api/v1/auth/logout").actor == "user:audit-owner"


def test_proxy_actor_requires_explicit_trusted_peer(monkeypatch):
    cfg = replace(
        request_identity.settings,
        audit_trusted_proxy_actor=True,
        trusted_proxy_cidrs=("127.0.0.1/32",),
    )
    monkeypatch.setattr(request_identity, "settings", cfg)
    trusted = _request("127.0.0.1", **{"X-Actor": "edge-gateway"})
    untrusted = _request("198.51.100.20", **{"X-Actor": "attacker"})
    trusted_forwarded = _request("127.0.0.1", **{"X-Forwarded-For": "203.0.113.44"})
    untrusted_forwarded = _request("198.51.100.20", **{"X-Forwarded-For": "203.0.113.44"})
    assert request_identity.audit_actor_from_request(trusted) == "proxy:edge-gateway"
    assert request_identity.audit_actor_from_request(untrusted) == "anonymous"
    assert request_identity.client_ip_from_request(trusted_forwarded) == "203.0.113.44"
    assert request_identity.client_ip_from_request(untrusted_forwarded) == "198.51.100.20"


def test_production_proxy_actor_configuration_requires_network_boundary():
    with pytest.raises(ValueError, match="TRUSTED_PROXY_CIDRS"):
        validate_runtime_settings(
            Settings(
                app_env="production",
                auth_mode="rbac",
                database_url="postgresql+psycopg://user:password@db/radar",
                audit_trusted_proxy_actor=True,
            )
        )
    with pytest.raises(ValueError, match="invalid network"):
        validate_runtime_settings(
            Settings(
                app_env="test",
                auth_mode="rbac",
                trusted_proxy_cidrs=("not-a-network",),
            )
        )


def _latest_audit(resource: str) -> AuditLog:
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).where(AuditLog.resource == resource).order_by(AuditLog.id.desc())).first()
