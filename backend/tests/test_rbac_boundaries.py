from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core import security
from app.db.session import SessionLocal
from app.main import app
from app.services.auth import create_api_token, create_user


def _user_token(db, username: str, role: str, name: str, scopes: list[str]) -> tuple[int, str, int]:
    user = create_user(db, username, f"{username}-BoundaryPassword-2026!", role=role)
    plain, token = create_api_token(db, user, name=name, scopes=scopes)
    db.flush()
    return user.id, plain, token.id


def test_vertical_role_boundaries_and_horizontal_token_isolation(monkeypatch):
    cfg = replace(security.settings, auth_mode="rbac", allow_legacy_api_key=False)
    monkeypatch.setattr(security, "settings", cfg)
    monkeypatch.setattr(auth_api, "settings", cfg)
    with SessionLocal() as db:
        owner_id, owner_token, _ = _user_token(db, "boundary-owner", "OWNER", "owner-token", ["read", "write", "admin"])
        admin_id, admin_token, _ = _user_token(db, "boundary-admin", "ADMIN", "admin-token", ["read", "write", "admin"])
        researcher_a_id, researcher_a_token, researcher_a_token_id = _user_token(db, "boundary-researcher-a", "RESEARCHER", "researcher-a-token", ["read", "write"])
        researcher_b_id, researcher_b_token, researcher_b_token_id = _user_token(db, "boundary-researcher-b", "RESEARCHER", "researcher-b-token", ["read", "write"])
        viewer_id, viewer_token, _ = _user_token(db, "boundary-viewer", "VIEWER", "viewer-token", ["read"])
        db.commit()

    with TestClient(app) as client:
        assert client.get("/api/v1/dashboard").status_code == 401

        viewer = {"Authorization": f"Bearer {viewer_token}"}
        assert client.get("/api/v1/dashboard", headers=viewer).status_code == 200
        assert client.post("/api/v1/watch-keywords", headers=viewer, json={"keyword": "viewer blocked", "priority": 1}).status_code == 403
        assert client.post("/api/v1/alerts/evaluate", headers=viewer).status_code == 403

        researcher = {"Authorization": f"Bearer {researcher_a_token}"}
        assert client.post("/api/v1/watch-keywords", headers=researcher, json={"keyword": "researcher allowed", "priority": 1}).status_code == 200
        assert client.post("/api/v1/import", headers=researcher, json={"records": []}).status_code == 403
        assert client.get("/api/v1/workers", headers=researcher).status_code == 403
        assert client.patch(f"/api/v1/admin/users/{researcher_b_id}", headers=researcher, json={"enabled": False}).status_code == 403

        admin = {"Authorization": f"Bearer {admin_token}"}
        assert client.get("/api/v1/workers", headers=admin).status_code == 200
        assert client.post("/api/v1/admin/users", headers=admin, json={"username": "boundary-created", "password": "CreatedBoundaryPassword-2026!", "role": "VIEWER"}).status_code == 200
        assert client.post("/api/v1/admin/users", headers=admin, json={"username": "boundary-forbidden-owner", "password": "ForbiddenBoundaryPassword-2026!", "role": "OWNER"}).status_code == 403
        assert client.patch(f"/api/v1/admin/users/{owner_id}", headers=admin, json={"role": "ADMIN"}).status_code == 403

        owner = {"Authorization": f"Bearer {owner_token}"}
        assert client.get("/api/v1/admin/users", headers=owner).status_code == 200

        own_tokens = client.get("/api/v1/auth/tokens", headers=researcher).json()
        assert {row["name"] for row in own_tokens} == {"researcher-a-token"}
        assert client.delete(f"/api/v1/auth/tokens/{researcher_b_token_id}", headers=researcher).status_code == 404
        assert client.delete(f"/api/v1/auth/tokens/{researcher_a_token_id}", headers=researcher).status_code == 200

    assert admin_id and researcher_a_id and viewer_id and researcher_b_token
