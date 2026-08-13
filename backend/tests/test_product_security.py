import pytest
from fastapi import HTTPException

from app.core.config import Settings, validate_runtime_settings
import app.core.security as security


def test_production_requires_rbac_postgres_and_disables_legacy_key():
    with pytest.raises(ValueError, match="AUTH_MODE"):
        validate_runtime_settings(Settings(app_env="production", auth_mode="disabled", database_url="sqlite:///x.db"))
    with pytest.raises(ValueError, match="AUTH_MODE"):
        validate_runtime_settings(Settings(app_env="production", auth_mode="all", database_url="postgresql+psycopg://u:p@db/x"))
    with pytest.raises(ValueError, match="ALLOW_LEGACY_API_KEY"):
        validate_runtime_settings(Settings(app_env="production", auth_mode="rbac", allow_legacy_api_key=True, database_url="postgresql+psycopg://u:p@db/x"))
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_runtime_settings(Settings(app_env="production", auth_mode="rbac", database_url="sqlite:///x.db"))
    validate_runtime_settings(Settings(app_env="production", auth_mode="rbac", database_url="postgresql+psycopg://u:p@db/x"))


def test_write_auth_uses_constant_time_key_validation(monkeypatch):
    monkeypatch.setattr(security, "settings", Settings(auth_mode="write", api_key="a" * 32))
    with pytest.raises(HTTPException) as exc:
        security.require_write_auth("wrong")
    assert exc.value.status_code == 401
    principal = security.require_write_auth("a" * 32)
    assert principal is not None and principal.role == "OWNER"


def test_sqlite_runtime_enforces_foreign_keys():
    from sqlalchemy import text
    from app.db.session import engine
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("PRAGMA busy_timeout")).scalar_one() >= 5000
