from datetime import date, datetime

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.domain.digest import DigestStatus
from app.main import app
from app.services.digest import generate_daily_digest
from app.services.digest_persistence import get_daily_digest, save_daily_digest


def test_daily_digest_persistence_is_idempotent_and_round_trips_contract():
    with SessionLocal() as db:
        digest = generate_daily_digest(db, digest_date=date(2026, 8, 12), now=datetime(2026, 8, 12, 12))
        first = save_daily_digest(db, digest)
        second = save_daily_digest(db, digest)
        db.commit()
        loaded = get_daily_digest(db, digest_date=date(2026, 8, 12))
    assert first.id == second.id
    assert loaded.status == DigestStatus.EMPTY
    assert loaded.input_signature == digest.input_signature
    assert loaded.model_dump(mode="json") == digest.model_dump(mode="json")


def test_daily_digest_query_api_returns_404_then_persisted_empty_snapshot():
    client = TestClient(app)
    missing = client.get("/api/v1/digests/daily/2026-08-12")
    assert missing.status_code == 404
    generated = client.post("/api/v1/digests/daily/generate?digest_date=2026-08-12")
    assert generated.status_code == 200
    assert generated.json()["status"] == "EMPTY"
    fetched = client.get("/api/v1/digests/daily?digest_date=2026-08-12")
    assert fetched.status_code == 200
    assert fetched.json()["input_signature"] == generated.json()["input_signature"]
    latest = client.get("/api/v1/digests/daily")
    assert latest.status_code == 200
    assert latest.json()["digest_date"] == "2026-08-12"


def test_daily_digest_generation_requires_admin_in_rbac(monkeypatch):
    from dataclasses import replace

    import app.core.security as security
    from app.core.config import settings

    monkeypatch.setattr(security, "settings", replace(settings, auth_mode="rbac"))
    response = TestClient(app).post("/api/v1/digests/daily/generate?digest_date=2026-08-13")
    assert response.status_code == 401


def test_digest_worker_runs_the_same_generator_and_persists_snapshot():
    from app.connectors.registry import SourceRegistry
    from app.worker import run_once

    result = run_once(sync=False, limit=1, mode="digest", worker_id="digest-worker-test", registry=SourceRegistry())
    assert result["digest"]["status"] == "EMPTY"
    with SessionLocal() as db:
        loaded = get_daily_digest(db)
    assert loaded.status == DigestStatus.EMPTY
