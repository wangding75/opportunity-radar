from pathlib import Path
import sys

import pytest
from fastapi import Response

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_security_review_auth import validate_security_review  # noqa: E402

from app.api import auth as auth_api
from app.core import security
from app.core.config import Settings
from app.db.session import SessionLocal
from app.domain.schemas import LoginRequest
from app.services.auth import create_user, hash_password, verify_password


def test_security_review_artifact_has_eight_passed_controls():
    result = validate_security_review(Path(__file__).parents[2] / "validation" / "security_review_auth.json")
    assert result["controls"] == 8
    assert result["status"] == "PASS"


def test_production_login_sets_secure_strict_http_only_session_cookie(monkeypatch):
    cfg = Settings(auth_mode="rbac", app_env="production", database_url=security.settings.database_url)
    monkeypatch.setattr(auth_api, "settings", cfg)
    username = "secure-cookie-review"
    password = "SecureCookiePassword-2026!"
    with SessionLocal() as db:
        create_user(db, username, password, role="OWNER")
        db.commit()
        response = Response()
        result = auth_api.login(LoginRequest(username=username, password=password), response, db)
        assert result["auth_mode"] == "rbac"
        cookies = [value for key, value in response.raw_headers if key.lower() == b"set-cookie"]
        session_cookie = next(value.decode("latin-1") for value in cookies if value.decode("latin-1").startswith(cfg.session_cookie_name + "="))
        csrf_cookie = next(value.decode("latin-1") for value in cookies if value.decode("latin-1").startswith(cfg.csrf_cookie_name + "="))
        assert "HttpOnly" in session_cookie
        assert "Secure" in session_cookie and "SameSite=strict" in session_cookie
        assert "Secure" in csrf_cookie and "HttpOnly" not in csrf_cookie and "SameSite=strict" in csrf_cookie


def test_password_hash_and_csrf_inputs_fail_closed():
    password = "CorrectHorseBattery-2026!"
    encoded = hash_password(password)
    assert verify_password(password, encoded)
    assert not verify_password("wrong", encoded)
    with SessionLocal() as db:
        user = create_user(db, "csrf-review", password, role="RESEARCHER")
        db.commit()
        from app.services.auth import create_session, validate_csrf

        _, csrf, session = create_session(db, user, ttl_hours=1)
        db.commit()
        assert validate_csrf(db, session.id, csrf)
        assert not validate_csrf(db, session.id, "wrong-csrf")
        assert not validate_csrf(db, session.id, None)
