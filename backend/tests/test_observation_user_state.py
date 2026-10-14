from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import auth as auth_api
from app.core import security
from app.db.session import SessionLocal
from app.main import app
from app.services.auth import create_api_token, create_user
from app.services.observation_state import (
    delete_user_observation_state,
    get_user_observation_state,
    upsert_user_observation_state,
    user_observation_state_map,
)

client = TestClient(app)


def _import_one_observation(title: str) -> str:
    """Seed a synthetic observation through the ingestion service layer.

    Tests switch the ambient auth mode via monkeypatch, so going through the
    HTTP import endpoint would require an admin principal here. Seeding via
    the service keeps the fixture independent of the mode under test.
    """
    from app.domain.enums import AcquisitionMethod, AcquisitionRisk, EvidenceQuality
    from app.domain.schemas import ImportRecord
    from app.services.ingestion import from_import, store_collected

    with SessionLocal() as db:
        raw, _is_new = store_collected(
            db,
            source_id="state-contract",
            query="bookmark",
            record=from_import(ImportRecord(source_id="state-contract", query="bookmark", title=title, text="state body")),
            acquisition_method=AcquisitionMethod.MANUAL_IMPORT,
            evidence_quality=EvidenceQuality.C,
            acquisition_risk=AcquisitionRisk.R2,
        )
        db.commit()
        return f"obs_{raw.content_hash}"


def _rbac_env(monkeypatch, *, auth_mode="rbac"):
    cfg = replace(security.settings, auth_mode=auth_mode, allow_legacy_api_key=False)
    monkeypatch.setattr(security, "settings", cfg)
    monkeypatch.setattr(auth_api, "settings", cfg)


def _user_with_token(db, username: str, role: str) -> tuple[int, str]:
    user = create_user(db, username, f"{username}-ObservationState-2026!", role=role)
    plain, _token = create_api_token(db, user, name=f"{username}-state-token", scopes=["read"] if role == "VIEWER" else ["read", "write"])
    db.commit()
    return user.id, plain


def test_anonymous_and_disabled_mode_return_explicit_null_user_state(monkeypatch):
    _rbac_env(monkeypatch, auth_mode="rbac")
    public_id = _import_one_observation("Anonymous null state")

    anon_client = TestClient(app)
    listing = anon_client.get("/api/v1/observations", params={"q": "Anonymous null state"})
    assert listing.status_code == 401

    # AUTH_MODE=disabled (development anonymous mode) allows reads but must
    # not fabricate a user identity: user_state stays an explicit null.
    _rbac_env(monkeypatch, auth_mode="disabled")
    listing = client.get("/api/v1/observations", params={"q": "Anonymous null state"})
    assert listing.status_code == 200
    body = listing.json()
    assert body["items"][0]["user_state"] is None
    detail = client.get(f"/api/v1/observations/{public_id}")
    assert detail.status_code == 200
    assert detail.json()["user_state"] is None
    state = client.get(f"/api/v1/observations/{public_id}/state")
    assert state.status_code == 401
    put = client.put(f"/api/v1/observations/{public_id}/state", json={"bookmarked": True})
    assert put.status_code in {401, 403}


def test_viewer_can_bookmark_dismiss_and_keep_own_state(monkeypatch):
    _rbac_env(monkeypatch)
    public_id = _import_one_observation("Viewer bookmark state")
    with SessionLocal() as db:
        viewer_id, viewer_token = _user_with_token(db, "state-viewer", "VIEWER")
        admin_id, admin_token = _user_with_token(db, "state-admin", "ADMIN")

    viewer = {"Authorization": f"Bearer {viewer_token}"}
    admin = {"Authorization": f"Bearer {admin_token}"}

    # Initial read: explicit null, not fabricated defaults.
    state = client.get(f"/api/v1/observations/{public_id}/state", headers=viewer)
    assert state.status_code == 200
    assert state.json()["user_state"] is None

    # VIEWER maintains their own bookmark even though the write scope normally
    # starts at RESEARCHER; observation personal state is a VIEWER capability.
    put = client.put(f"/api/v1/observations/{public_id}/state", headers=viewer, json={"bookmarked": True})
    assert put.status_code == 200
    body = put.json()
    assert body["user_state"]["bookmarked"] is True
    assert body["user_state"]["dismissed"] is False

    # Idempotent: repeating the same PUT converges on the same stored state
    # (one row, same values), even though updated_at reflects the last write.
    put_again = client.put(f"/api/v1/observations/{public_id}/state", headers=viewer, json={"bookmarked": True})
    assert put_again.status_code == 200
    assert put_again.json()["user_state"]["bookmarked"] is True
    assert put_again.json()["user_state"]["dismissed"] is False
    with SessionLocal() as db:
        from sqlalchemy import func as _func
        from app.db.models import UserObservationState, RawObservation
        observation_id = db.scalar(select(RawObservation.id).where(RawObservation.title == "Viewer bookmark state"))
        count = db.scalar(select(_func.count()).select_from(UserObservationState).where(
            UserObservationState.user_id == viewer_id,
            UserObservationState.observation_id == observation_id,
        ))
        assert count == 1

    # Dismiss + notes coexist with the bookmark.
    put_more = client.put(f"/api/v1/observations/{public_id}/state", headers=viewer, json={"dismissed": True, "notes": "看过，低价值"})
    assert put_more.status_code == 200
    assert put_more.json()["user_state"]["bookmarked"] is True
    assert put_more.json()["user_state"]["dismissed"] is True
    assert put_more.json()["user_state"]["notes"] == "看过，低价值"

    # List/detail carry the caller's own state back.
    listing = client.get("/api/v1/observations", params={"q": "Viewer bookmark state"}, headers=viewer)
    assert listing.json()["items"][0]["user_state"]["bookmarked"] is True
    detail = client.get(f"/api/v1/observations/{public_id}", headers=viewer)
    assert detail.json()["user_state"]["dismissed"] is True

    # Another user (ADMIN) sees their own null state, not the VIEWER's bookmark.
    admin_state = client.get(f"/api/v1/observations/{public_id}/state", headers=admin)
    assert admin_state.status_code == 200
    assert admin_state.json()["user_state"] is None
    admin_listing = client.get("/api/v1/observations", params={"q": "Viewer bookmark state"}, headers=admin)
    assert admin_listing.json()["items"][0]["user_state"] is None
    assert viewer_id != admin_id


def test_admin_state_is_isolated_from_viewer_and_delete_resets(monkeypatch):
    _rbac_env(monkeypatch)
    public_id = _import_one_observation("Admin isolated state")
    with SessionLocal() as db:
        viewer_id, viewer_token = _user_with_token(db, "iso-viewer", "VIEWER")
        admin_id, admin_token = _user_with_token(db, "iso-admin", "ADMIN")

    viewer = {"Authorization": f"Bearer {viewer_token}"}
    admin = {"Authorization": f"Bearer {admin_token}"}

    assert client.put(f"/api/v1/observations/{public_id}/state", headers=viewer, json={"bookmarked": True}).status_code == 200
    assert client.put(f"/api/v1/observations/{public_id}/state", headers=admin, json={"dismissed": True}).status_code == 200

    with SessionLocal() as db:
        from app.db.models import RawObservation
        observation_id = db.scalar(select(RawObservation.id).where(RawObservation.title == "Admin isolated state"))
        viewer_row = get_user_observation_state(db, viewer_id, observation_id)
        admin_row = get_user_observation_state(db, admin_id, observation_id)
        assert viewer_row is not None and viewer_row.bookmarked is True and viewer_row.dismissed_at is None
        assert admin_row is not None and admin_row.dismissed_at is not None and admin_row.bookmarked is False

    # DELETE removes only the caller's row; the other user's state survives.
    deleted = client.delete(f"/api/v1/observations/{public_id}/state", headers=admin)
    assert deleted.status_code == 200
    assert deleted.json()["user_state"] is None
    assert client.get(f"/api/v1/observations/{public_id}/state", headers=admin).json()["user_state"] is None
    viewer_after = client.get(f"/api/v1/observations/{public_id}/state", headers=viewer)
    assert viewer_after.json()["user_state"]["bookmarked"] is True

    # DELETE is idempotent: a missing row still returns a clean 200.
    again = client.delete(f"/api/v1/observations/{public_id}/state", headers=admin)
    assert again.status_code == 200
    assert again.json()["user_state"] is None


def test_state_routes_reject_unknown_observation_and_oversized_notes(monkeypatch):
    _rbac_env(monkeypatch)
    with SessionLocal() as db:
        _admin_id, admin_token = _user_with_token(db, "edge-admin", "ADMIN")
    admin = {"Authorization": f"Bearer {admin_token}"}

    missing = client.get("/api/v1/observations/obs_{'0' * 64}/state", headers=admin)
    assert missing.status_code == 404
    missing_put = client.put(f"/api/v1/observations/obs_{'0' * 64}/state", headers=admin, json={"bookmarked": True})
    assert missing_put.status_code == 404

    public_id = _import_one_observation("Edge oversized notes")
    oversized = client.put(f"/api/v1/observations/{public_id}/state", headers=admin, json={"notes": "x" * 50_001})
    assert oversized.status_code == 422
    payload = oversized.json()
    assert payload["code"] == "VALIDATION_FAILED"
    assert payload["request_id"]


def test_service_layer_upsert_and_map_roundtrip():
    public_id = _import_one_observation("Service layer state")
    with SessionLocal() as db:
        from app.db.models import RawObservation
        observation_id = db.scalar(select(RawObservation.id).where(RawObservation.title == "Service layer state"))
        user = create_user(db, "state-service-user", "ServiceLayerPassword-2026!", role="RESEARCHER")
        db.flush()

        assert get_user_observation_state(db, user.id, observation_id) is None
        state = upsert_user_observation_state(db, user.id, observation_id, bookmarked=True)
        assert state.bookmarked is True
        # Second upsert mutates the same row (unique constraint holds).
        state_again = upsert_user_observation_state(db, user.id, observation_id, notes="note")
        assert state_again.id == state.id
        assert state_again.bookmarked is True
        assert state_again.notes == "note"

        mapping = user_observation_state_map(db, user.id, [observation_id, 999999])
        assert set(mapping) == {observation_id}

        assert delete_user_observation_state(db, user.id, observation_id) is True
        assert delete_user_observation_state(db, user.id, observation_id) is False
        db.commit()


def test_unknown_observation_id_raises_key_error():
    with SessionLocal() as db:
        user = create_user(db, "state-keyerror-user", "KeyErrorPassword-2026!", role="RESEARCHER")
        db.flush()
        try:
            upsert_user_observation_state(db, user.id, 999_999_999, bookmarked=True)
            raise AssertionError("expected KeyError for unknown observation")
        except KeyError:
            pass
        db.rollback()
