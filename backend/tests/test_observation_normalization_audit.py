from __future__ import annotations

from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, EvidenceQuality
from app.domain.schemas import ImportRecord
from app.services.analysis import process_new_raw
from app.services.ingestion import from_import, store_collected
from app.services.normalization_audit import audit_observation_normalization


def _store(db, *, title: str = "  Synthetic   title ", observed_at: datetime | None = None):
    record = ImportRecord(
        source_id="synthetic-normalization",
        query="  Synthetic   query ",
        external_id="synthetic-1",
        title=title,
        text="  evidence   text ",
        observed_at=observed_at or datetime(2026, 8, 13, 2, 0, tzinfo=UTC),
        payload={"data_class": "SYNTHETIC"},
    )
    return store_collected(
        db,
        source_id=record.source_id,
        query=record.query,
        record=from_import(record),
        acquisition_method=AcquisitionMethod.MANUAL_IMPORT,
        evidence_quality=EvidenceQuality.C,
        acquisition_risk=AcquisitionRisk.R2,
    )


def test_empty_audit_is_pass_and_normalization_is_idempotent():
    with SessionLocal() as db:
        empty = audit_observation_normalization(db)
        assert empty["status"] == "PASS"
        raw, inserted = _store(db)
        assert inserted is True
        first = process_new_raw(db, raw)
        second = process_new_raw(db, raw)
        assert first.id == second.id
        report = audit_observation_normalization(db)
        assert report["status"] == "PASS"
        assert report["summary"]["normalized_coverage"] == 1.0


def test_duplicate_ingestion_is_a_noop_and_utc_normalization_is_auditable():
    with SessionLocal() as db:
        raw, inserted = _store(db)
        duplicate, duplicate_inserted = _store(db)
        assert inserted is True and duplicate_inserted is False
        assert raw.id == duplicate.id
        item = process_new_raw(db, raw)
        assert item.query == "Synthetic query"
        assert item.title == "Synthetic title"
        assert item.text == "evidence text"
        assert item.observed_at == datetime(2026, 8, 13, 2, 0)
        assert audit_observation_normalization(db)["status"] == "PASS"


def test_audit_detects_normalized_field_drift_before_it_can_be_treated_as_valid():
    with SessionLocal() as db:
        raw, _ = _store(db)
        item = process_new_raw(db, raw)
        item.title = "tampered normalized title"
        report = audit_observation_normalization(db)
        assert report["status"] == "FAIL"
        assert any(row["rule"] == "normalized_field_mirror" and row["field"] == "title" for row in report["violations"])
