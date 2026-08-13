from __future__ import annotations

import hashlib
import json
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive, utc_now
from app.db.models import RawObservation
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, EvidenceQuality
from app.domain.schemas import CollectedRecord, ImportRecord, InstrumentedAppObservation
from app.services.sanitizer import sanitize_instrumented


def _content_hash(source_id: str, query: str, record: CollectedRecord, app_meta: dict | None = None) -> str:
    observed_at = as_utc_naive(record.observed_at)
    app_meta = app_meta or {}
    stable = {
        "source_id": source_id,
        "query": query.strip().lower(),
        "external_id": record.external_id,
        "title": record.title.strip(),
        "text": record.text.strip(),
        "url": record.url,
        "item_type": record.item_type.value,
        "payload": record.payload,
        "observation_day": observed_at.date().isoformat(),
        "app_package": app_meta.get("app_package"),
        "app_version": app_meta.get("app_version"),
        "instrumentation_version": app_meta.get("instrumentation_version"),
    }
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def store_collected(
    db: Session,
    *,
    source_id: str,
    query: str,
    record: CollectedRecord,
    acquisition_method: AcquisitionMethod,
    evidence_quality: EvidenceQuality,
    acquisition_risk: AcquisitionRisk,
    app_meta: dict | None = None,
) -> tuple[RawObservation, bool]:
    app_meta = app_meta or {}
    digest = _content_hash(source_id, query, record, app_meta)
    existing = db.scalar(select(RawObservation).where(RawObservation.content_hash == digest))
    if existing:
        return existing, False
    row = RawObservation(
        source_id=source_id,
        external_id=record.external_id,
        query=query,
        item_type=record.item_type.value,
        title=record.title,
        text=record.text,
        source_url=record.url,
        observed_at=as_utc_naive(record.observed_at),
        acquisition_method=acquisition_method.value,
        evidence_quality=evidence_quality.value,
        acquisition_risk=acquisition_risk.value,
        content_hash=digest,
        raw_payload=record.payload,
        raw_payload_bytes=len(json.dumps(record.payload, ensure_ascii=False, sort_keys=True).encode("utf-8")),
        app_package=app_meta.get("app_package"),
        app_version=app_meta.get("app_version"),
        emulator_profile=app_meta.get("emulator_profile"),
        instrumentation_version=app_meta.get("instrumentation_version"),
        session_id=app_meta.get("session_id"),
    )
    try:
        # The pre-check handles the common idempotent path. The nested savepoint
        # closes the remaining race where two workers insert the same hash at once.
        with db.begin_nested():
            db.add(row)
            db.flush()
    except IntegrityError:
        existing = db.scalar(select(RawObservation).where(RawObservation.content_hash == digest))
        if existing is not None:
            return existing, False
        raise
    return row, True


def from_import(record: ImportRecord) -> CollectedRecord:
    return CollectedRecord(
        external_id=record.external_id,
        item_type=record.item_type,
        title=record.title,
        text=record.text,
        url=record.url,
        observed_at=record.observed_at or utc_now(),
        payload=record.payload,
    )


def from_instrumented(record: InstrumentedAppObservation) -> CollectedRecord:
    collected = CollectedRecord(
        external_id=record.external_id,
        item_type=record.item_type,
        title=record.title,
        text=record.text,
        url=record.url,
        observed_at=record.observed_at or utc_now(),
        payload=record.payload,
    )
    return sanitize_instrumented(collected)
