import json
from datetime import datetime
from pathlib import Path
from dataclasses import replace

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.db.models import AlertEvent, RiskEscalationRecord
from app.db.session import SessionLocal
from app.main import app
from app.services.risk_escalation_mock import load_risk_escalation_mock_fixture, seed_risk_escalation_mock
from app.services.risk_escalation_replay import replay_risk_escalation


client = TestClient(app)


def test_synthetic_fixture_seeds_real_chain_and_repeated_run_is_idempotent():
    with SessionLocal() as db:
        first = seed_risk_escalation_mock(db)
        db.commit()
        second = seed_risk_escalation_mock(db)
        db.commit()
        records = db.scalar(select(func.count(RiskEscalationRecord.id)))
        events = db.scalar(select(func.count(AlertEvent.id)))
    assert first["data_class"] == "SYNTHETIC"
    assert first["imported_snapshots"] == 2
    assert first["imported_evidence"] == 1
    assert first["alerts"]["alerts_created"] == 1
    assert second["imported_snapshots"] == 0
    assert second["duplicate_evidence"] == 1
    assert second["alerts"]["duplicates"] == 1
    assert records == 1
    assert events == 1


def test_replay_is_read_only_bounded_and_api_requires_admin():
    with SessionLocal() as db:
        seeded = seed_risk_escalation_mock(db)
        db.commit()
        before_records = db.scalar(select(func.count(RiskEscalationRecord.id)))
        before_events = db.scalar(select(func.count(AlertEvent.id)))
        first = replay_risk_escalation(db, seeded["opportunity_id"], as_of=datetime(2026, 8, 12, 12))
        second = replay_risk_escalation(db, seeded["opportunity_id"], as_of=datetime(2026, 8, 12, 23))
        after_records = db.scalar(select(func.count(RiskEscalationRecord.id)))
        after_events = db.scalar(select(func.count(AlertEvent.id)))
    assert first["escalated"] is True
    assert first["read_only"] is True
    assert first["replay_mode"] == "persisted_risk_escalation_evaluation"
    assert first["input_signature"] == second["input_signature"]
    assert first["evidence_ids"]
    assert before_records == after_records == 1
    assert before_events == after_events == 1
    missing = client.post("/api/v1/alerts/risk/replay", params={"opportunity_id": seeded["opportunity_id"], "as_of": "2026-07-01T00:00:00"})
    assert missing.status_code == 404
    import app.core.security as security
    monkeypatch = replace(settings, auth_mode="rbac")
    security.settings = monkeypatch
    try:
        unauthorized = client.post("/api/v1/alerts/risk/replay", params={"opportunity_id": seeded["opportunity_id"], "as_of": "2026-08-12T12:00:00"})
        assert unauthorized.status_code == 401
    finally:
        security.settings = settings


def test_fixture_validation_rejects_real_source_and_wrong_shape(tmp_path: Path):
    valid = load_risk_escalation_mock_fixture()
    invalid_source = dict(valid)
    invalid_source["evidence"] = [dict(valid["evidence"][0], source_id="real-source")]
    path = tmp_path / "invalid-source.json"
    path.write_text(json.dumps(invalid_source), encoding="utf-8")
    try:
        load_risk_escalation_mock_fixture(path)
    except ValueError as exc:
        assert "synthetic-/mock-" in str(exc)
    else:
        raise AssertionError("real source must be rejected by the synthetic fixture loader")

    invalid_shape = dict(valid)
    invalid_shape["snapshots"] = [valid["snapshots"][0]]
    path.write_text(json.dumps(invalid_shape), encoding="utf-8")
    try:
        load_risk_escalation_mock_fixture(path)
    except ValueError as exc:
        assert "exactly two" in str(exc)
    else:
        raise AssertionError("incomplete fixture must be rejected")
