from __future__ import annotations

import hashlib
import importlib.util
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import auth as auth_api
from app.core import security
from app.core.config import Settings
from app.core.time import utc_now
from app.db.models import ApiToken, Opportunity, RawObservation, User
from app.db.session import SessionLocal
from app.main import app
from app.services import archive as archive_service
from app.services.auth import Principal, create_api_token, create_user, principal_from_api_token
from app.services.scoring import record_score_snapshot, replay_snapshot


def test_rbac_session_csrf_and_http_only_cookie(monkeypatch):
    cfg = Settings(auth_mode="rbac", app_env="test", database_url=security.settings.database_url)
    monkeypatch.setattr(security, "settings", cfg)
    monkeypatch.setattr(auth_api, "settings", cfg)
    with SessionLocal() as db:
        create_user(db, "owner", "OwnerPassword-2026!", role="OWNER")
        db.commit()

    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"username": "owner", "password": "OwnerPassword-2026!"})
        assert login.status_code == 200
        assert cfg.session_cookie_name in client.cookies
        assert cfg.csrf_cookie_name in client.cookies
        session_header = next(v for k, v in login.headers.multi_items() if k.lower() == "set-cookie" and v.startswith(cfg.session_cookie_name + "="))
        assert "HttpOnly" in session_header and "SameSite=strict" in session_header
        assert client.get("/api/v1/dashboard").status_code == 200
        blocked = client.post("/api/v1/watch-keywords", json={"keyword": "RBAC test", "priority": 3})
        assert blocked.status_code == 403
        csrf = client.cookies[cfg.csrf_cookie_name]
        created = client.post("/api/v1/watch-keywords", headers={"X-CSRF-Token": csrf}, json={"keyword": "RBAC test", "priority": 3})
        assert created.status_code == 200
        logout = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}, json={})
        assert logout.status_code == 200
        assert client.get("/api/v1/dashboard").status_code == 401


def test_personal_token_requires_interactive_session():
    principal = Principal(actor="token:u/t", role="OWNER", user_id=1, auth_type="api_token", scopes=frozenset({"read", "write", "admin"}))
    payload = auth_api.ApiTokenCreate(name="new", scopes=["read"])
    with SessionLocal() as db, pytest.raises(HTTPException) as exc:
        auth_api.issue_api_token(payload, principal=principal, db=db)
    assert exc.value.status_code == 403


def test_revoked_personal_token_name_can_be_reissued_and_old_secret_stays_invalid():
    with SessionLocal() as db:
        user = create_user(db, "token-user", "TokenUserPassword-2026!", role="RESEARCHER")
        old_plain, row = create_api_token(db, user, name="automation", scopes=["read", "write"])
        db.commit()
        row.revoked_at = utc_now()
        db.commit()
        new_plain, new_row = create_api_token(db, user, name="automation", scopes=["read"])
        db.commit()
        assert new_row.id == row.id
        assert new_plain != old_plain
        assert principal_from_api_token(db, old_plain) is None
        current = principal_from_api_token(db, new_plain)
        assert current is not None and current.scopes == frozenset({"read"})


def test_admin_cannot_mutate_owner_and_last_owner_cannot_be_removed():
    with SessionLocal() as db:
        owner = create_user(db, "owner", "OwnerPassword-2026!", role="OWNER")
        admin = create_user(db, "admin", "AdminPassword-2026!", role="ADMIN")
        db.commit()
        admin_principal = Principal(actor="user:admin", role="ADMIN", user_id=admin.id, auth_type="session", scopes=frozenset({"read", "write", "admin"}), session_id=99)
        with pytest.raises(HTTPException) as exc:
            auth_api.admin_patch_user(owner.id, auth_api.UserPatch(role="ADMIN"), principal=admin_principal, db=db)
        assert exc.value.status_code == 403
        owner_principal = Principal(actor="user:owner", role="OWNER", user_id=owner.id, auth_type="session", scopes=frozenset({"read", "write", "admin"}), session_id=1)
        with pytest.raises(HTTPException) as exc:
            auth_api.admin_patch_user(owner.id, auth_api.UserPatch(role="ADMIN"), principal=owner_principal, db=db)
        assert exc.value.status_code == 409


def test_score_replay_and_dormant_snapshot_are_persisted():
    now = utc_now()
    with SessionLocal() as db:
        # Use an existing keyword id only when needed by FK; SQLite FK is on.
        from app.db.models import Keyword
        kw = Keyword(canonical="score-test", display_name="score-test", status="ACTIVE", first_seen_at=now, last_seen_at=now)
        db.add(kw); db.flush()
        opp = Opportunity(opportunity_key="opp:score-test", keyword_id=kw.id, title="score", stage="EARLY", score=70, risk_score=10, evidence_count=3, first_seen_at=now, last_seen_at=now, updated_at=now, score_version="score-v1", score_breakdown={"total": 70})
        db.add(opp); db.flush()
        assert record_score_snapshot(db, opp, now=now)
        opp.stage = "DORMANT"; opp.score = 0; opp.score_breakdown = {"total": 0, "reason": "dormant"}
        assert record_score_snapshot(db, opp, now=now + timedelta(hours=1))
        db.commit()
        first = replay_snapshot(db, opp.id, as_of=now + timedelta(minutes=30))
        second = replay_snapshot(db, opp.id, as_of=now + timedelta(hours=2))
        assert first and first["score"] == 70 and first["stage"] == "EARLY"
        assert second and second["score"] == 0 and second["stage"] == "DORMANT"


def test_raw_payload_archive_round_trip_and_path_protection(monkeypatch, tmp_path):
    monkeypatch.setattr(archive_service, "settings", Settings(raw_payload_archive_dir=str(tmp_path)))
    old = utc_now() - timedelta(days=120)
    with SessionLocal() as db:
        payload = {"price": 99, "nested": {"value": "kept"}}
        raw = RawObservation(source_id="archive-test", external_id="1", query="q", item_type="CONTENT", title="old", text="", observed_at=old, acquisition_method="MANUAL_IMPORT", evidence_quality="D", acquisition_risk="R2", content_hash=hashlib.sha256(b"archive-test").hexdigest(), raw_payload=payload, raw_payload_bytes=0)
        db.add(raw); db.commit(); raw_id = raw.id
        preview = archive_service.archive_raw_payloads(db, older_than_days=90, dry_run=True)
        assert preview["eligible"] == 1 and preview["payload_bytes"] > 0
        archived = archive_service.archive_raw_payloads(db, older_than_days=90, dry_run=False)
        filename = Path(archived["archive_file"]).name
        db.expire_all(); row = db.get(RawObservation, raw_id)
        assert row.raw_payload.get("_archived") is True and row.raw_payload_archive_sha256
        restored = archive_service.restore_raw_payload_archive(db, filename)
        assert restored["restored"] == 1
        db.expire_all(); assert db.get(RawObservation, raw_id).raw_payload == payload
        with pytest.raises(FileNotFoundError):
            archive_service.restore_raw_payload_archive(db, "../outside.jsonl.gz")


def _load_restore_module():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("product_hardening_restore", root / "scripts" / "restore_database.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_postgres_staged_restore_validates_before_target_mutation(monkeypatch, tmp_path):
    restore = _load_restore_module()
    backup = tmp_path / "backup.pgdump"; backup.write_bytes(b"fake")
    monkeypatch.setattr(restore.shutil, "which", lambda name: f"/usr/bin/{name}")
    calls = []
    class Result:
        def __init__(self, stdout=""): self.stdout = stdout; self.returncode = 0
    def fake_run(args, **kwargs):
        args = list(args); calls.append(args)
        command = args[-1] if "--command" in args else ""
        if "version_num" in command: return Result("0031_login_rate_limits\n")
        if "information_schema.tables" in command: return Result("4\n")
        return Result("")
    monkeypatch.setattr(restore.subprocess, "run", fake_run)
    staging = restore.restore_postgres_staged(backup, "postgresql+psycopg://u:secret@db/radar", promote=False)
    assert staging.startswith("radar_restore_")
    restore_calls = [c for c in calls if c[0].endswith("pg_restore") and "--list" not in c]
    assert len(restore_calls) == 1 and staging in restore_calls[0]
    assert "--clean" not in restore_calls[0]
    assert all("secret" not in " ".join(c) for c in calls)
    assert not any("ALTER DATABASE" in " ".join(c) for c in calls)


def test_failed_login_lockout_persists_and_password_reset_clears_it():
    from app.services.auth import LOGIN_FAILURE_LIMIT, authenticate_credentials, update_user_password
    with SessionLocal() as db:
        user = create_user(db, "lock-user", "LockUserPassword-2026!", role="VIEWER")
        db.commit()
        for _ in range(LOGIN_FAILURE_LIMIT):
            assert authenticate_credentials(db, "lock-user", "wrong-password") is None
            db.commit()
        db.refresh(user)
        assert user.failed_login_count >= LOGIN_FAILURE_LIMIT and user.locked_until is not None
        assert authenticate_credentials(db, "lock-user", "LockUserPassword-2026!") is None
        update_user_password(db, user, "LockUserPassword-2027!")
        db.commit()
        assert authenticate_credentials(db, "lock-user", "LockUserPassword-2027!") is user


def test_personal_token_scopes_are_capped_by_current_user_role():
    with SessionLocal() as db:
        user = create_user(db, "demote-user", "DemoteUserPassword-2026!", role="ADMIN")
        plain, _ = create_api_token(db, user, name="admin-token", scopes=["read", "write", "admin"])
        db.commit()
        principal = principal_from_api_token(db, plain)
        assert principal and principal.has_scope("admin")
        user.role = "VIEWER"; db.commit()
        principal = principal_from_api_token(db, plain)
        assert principal and principal.role == "VIEWER"
        assert principal.has_scope("read") and not principal.has_scope("write") and not principal.has_scope("admin")


def test_backtest_isolated_to_active_scoring_model_version():
    from app.db.models import Keyword, OpportunityScoreSnapshot
    from app.services.scoring import backtest_summary
    now = utc_now()
    with SessionLocal() as db:
        kw = Keyword(canonical="backtest-model", display_name="backtest-model", status="ACTIVE", first_seen_at=now, last_seen_at=now)
        db.add(kw); db.flush()
        opp = Opportunity(opportunity_key="opp:backtest-model", keyword_id=kw.id, title="b", stage="EARLY", score=70, risk_score=0, evidence_count=2, first_seen_at=now, last_seen_at=now, updated_at=now)
        db.add(opp); db.flush()
        db.add(OpportunityScoreSnapshot(opportunity_id=opp.id, model_version="score-v0", input_signature="0"*64, score=99, risk_score=0, stage="EARLY", evidence_count=2, breakdown={}, calculated_at=now-timedelta(days=42)))
        db.add(OpportunityScoreSnapshot(opportunity_id=opp.id, model_version="score-v1", input_signature="1"*64, score=70, risk_score=0, stage="EARLY", evidence_count=2, breakdown={}, calculated_at=now-timedelta(days=40)))
        db.commit()
        result = backtest_summary(db, lookback_days=60, threshold=60)
        assert result["model_version"] == "score-v1"
        assert result["candidate_signals"] == 1


def test_admin_cannot_create_owner_and_password_reset_revokes_personal_tokens():
    from app.services.auth import update_user_password
    with SessionLocal() as db:
        admin = create_user(db, "create-admin", "CreateAdminPassword-2026!", role="ADMIN")
        target = create_user(db, "reset-target", "ResetTargetPassword-2026!", role="RESEARCHER")
        token, _ = create_api_token(db, target, name="automation", scopes=["read", "write"])
        db.commit()
        principal = Principal(actor="user:create-admin", role="ADMIN", user_id=admin.id, auth_type="session", scopes=frozenset({"read","write","admin"}), session_id=1)
        with pytest.raises(HTTPException) as exc:
            auth_api.admin_create_user(auth_api.UserCreate(username="forbidden-owner", password="ForbiddenOwnerPassword-2026!", role="OWNER"), principal=principal, db=db)
        assert exc.value.status_code == 403
        assert principal_from_api_token(db, token) is not None
        update_user_password(db, target, "ResetTargetPassword-2027!")
        db.commit()
        assert principal_from_api_token(db, token) is None


def test_postgres_server_args_do_not_drop_postgres_username():
    from app.core.postgres_cli import postgres_cli_server_args
    args, env = postgres_cli_server_args("postgresql+psycopg://postgres:secret@db.example:5433/radar")
    assert args == ["--host", "db.example", "--port", "5433", "--username", "postgres"]
    assert env["PGPASSWORD"] == "secret"


def test_auth_record_cleanup_dry_run_and_delete_old_revoked_records():
    from app.db.models import UserSession
    from app.services.auth import cleanup_auth_records, create_session
    now = utc_now()
    with SessionLocal() as db:
        user = create_user(db, "cleanup-user", "CleanupUserPassword-2026!", role="VIEWER")
        _, _, session = create_session(db, user, ttl_hours=1)
        _, token = create_api_token(db, user, name="cleanup-token", scopes=["read"])
        db.flush()
        session.expires_at = now - timedelta(days=120)
        session.revoked_at = now - timedelta(days=119)
        token.revoked_at = now - timedelta(days=118)
        db.commit()
        sid, tid = session.id, token.id

        preview = cleanup_auth_records(db, retention_days=90, dry_run=True)
        assert preview["expired_sessions"] == 1
        assert preview["expired_or_revoked_tokens"] == 1
        assert db.get(UserSession, sid) is not None
        assert db.get(ApiToken, tid) is not None

        result = cleanup_auth_records(db, retention_days=90, dry_run=False)
        assert result["expired_sessions"] == 1
        assert result["expired_or_revoked_tokens"] == 1
        assert db.get(UserSession, sid) is None
        assert db.get(ApiToken, tid) is None


def test_staged_restore_generated_database_names_stay_within_postgres_identifier_limit():
    restore = _load_restore_module()
    target = "r" * 63
    staging = restore._derived_database_name(target, "restore", "20260812174000")
    previous = restore._derived_database_name(target, "previous", "20260812174000")
    assert len(staging.encode("ascii")) <= 63
    assert len(previous.encode("ascii")) <= 63
    assert "_restore_20260812174000_" in staging
    assert "_previous_20260812174000_" in previous
