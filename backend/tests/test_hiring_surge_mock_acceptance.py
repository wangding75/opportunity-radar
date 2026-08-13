import json
from datetime import date

import pytest
from sqlalchemy import func, select

from app.db.models import AlertEvent, HiringSurgeRecord
from app.db.session import SessionLocal
from app.services.hiring_surge_mock import load_hiring_surge_mock_fixture, seed_hiring_surge_mock


def test_synthetic_fixture_runs_through_ingestion_opportunity_and_alert_chain():
    with SessionLocal() as db:
        first = seed_hiring_surge_mock(db, window_end=date(2026, 8, 12))
        db.commit()
        second = seed_hiring_surge_mock(db, window_end=date(2026, 8, 12))
        db.commit()

    assert first["data_class"] == "SYNTHETIC"
    assert first["records"] == 19
    assert first["imported"] == 19
    assert first["duplicates"] == 0
    assert first["normalized"] == 19
    assert first["alerts"]["surges"] == 1
    assert first["alerts"]["created"] == 1
    assert first["opportunity_id"] is not None
    assert second["imported"] == 0
    assert second["duplicates"] == 19
    assert second["alerts"]["duplicates"] == 1
    assert second["alerts"]["created"] == 0

    with SessionLocal() as db:
        record = db.scalar(select(HiringSurgeRecord).where(HiringSurgeRecord.keyword_id == first["keyword_id"]))
        assert record is not None
        assert record.status == "SURGE"
        assert record.opportunity_id == first["opportunity_id"]
        assert record.current_end == date(2026, 8, 12)
        assert record.evidence
        assert db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.keyword_id == first["keyword_id"])) == 1


def test_mock_loader_rejects_unmarked_or_real_source_fixture(tmp_path):
    fixture = load_hiring_surge_mock_fixture()
    fixture["data_class"] = "OBSERVED"
    bad_class = tmp_path / "bad-class.json"
    bad_class.write_text(json.dumps(fixture), encoding="utf-8")
    with pytest.raises(ValueError, match="MOCK or SYNTHETIC"):
        load_hiring_surge_mock_fixture(bad_class)

    fixture = load_hiring_surge_mock_fixture()
    fixture["records"][0]["source_id"] = "real-job-board"
    bad_source = tmp_path / "bad-source.json"
    bad_source.write_text(json.dumps(fixture), encoding="utf-8")
    with pytest.raises(ValueError, match="synthetic-/mock-"):
        load_hiring_surge_mock_fixture(bad_source)
