"""Bounded, explicitly synthetic hiring-surge fixture and acceptance loader."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, Opportunity, OpportunityKeyword
from app.domain.schemas import ImportRecord
from app.services.analysis import process_new_raw, refresh_derived_analysis
from app.services.hiring_surge_alerts import materialize_hiring_surge_alerts
from app.services.ingestion import from_import, store_collected

DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "hiring_surge_mock.json"
MOCK_SOURCE_PREFIXES = ("synthetic-", "mock-")


def load_hiring_surge_mock_fixture(path: Path | None = None) -> dict:
    fixture_path = path or DEFAULT_FIXTURE
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("data_class") not in {"MOCK", "SYNTHETIC"}:
        raise ValueError("hiring surge fixture must be explicitly marked MOCK or SYNTHETIC")
    records = payload.get("records")
    if not isinstance(records, list) or not records or len(records) > 20:
        raise ValueError("hiring surge fixture must contain between 1 and 20 records")
    for record in records:
        if not isinstance(record, dict) or not str(record.get("source_id", "")).startswith(MOCK_SOURCE_PREFIXES):
            raise ValueError("hiring surge fixture source IDs must be synthetic-/mock- prefixed")
    return payload


def _ensure_mock_opportunity(db: Session, *, keyword: Keyword) -> Opportunity:
    opportunity = db.scalar(
        select(Opportunity)
        .join(OpportunityKeyword, OpportunityKeyword.opportunity_id == Opportunity.id)
        .where(OpportunityKeyword.keyword_id == keyword.id, Opportunity.stage != "DORMANT")
        .order_by(Opportunity.score.desc(), Opportunity.id.asc())
    )
    if opportunity is not None:
        return opportunity
    now = utc_now()
    opportunity = Opportunity(
        opportunity_key=f"mock-hiring:{keyword.canonical}",
        keyword_id=keyword.id,
        title=f"MOCK {keyword.display_name}",
        stage="VALIDATED",
        score=75.0,
        risk_score=25.0,
        evidence_count=1,
        summary="SYNTHETIC opportunity created only for hiring-surge acceptance.",
        analysis_provider="mock-fixture",
        analysis_status="READY",
        analysis_signature="m" * 64,
        first_seen_at=now,
        last_seen_at=now,
        updated_at=now,
    )
    db.add(opportunity)
    db.flush()
    db.add(OpportunityKeyword(opportunity_id=opportunity.id, keyword_id=keyword.id, role="PRIMARY", weight=1.0))
    db.flush()
    return opportunity


def seed_hiring_surge_mock(
    db: Session,
    *,
    fixture_path: Path | None = None,
    window_end: date | None = None,
) -> dict:
    """Load the bounded fixture through the real ingestion chain and materialize alerts.

    The function does not commit. Callers can roll back the whole acceptance run.
    Re-running it is safe because ingestion content hashes and alert detection
    signatures are both idempotent.
    """

    fixture = load_hiring_surge_mock_fixture(fixture_path)
    selected_window_end = window_end or date.fromisoformat(str(fixture["window_end"]))
    imported = 0
    duplicates = 0
    normalized_item_ids: set[int] = set()
    for raw_record in fixture["records"]:
        record = ImportRecord.model_validate(raw_record)
        raw, is_new = store_collected(
            db,
            source_id=record.source_id,
            query=record.query,
            record=from_import(record),
            acquisition_method=record.acquisition_method,
            evidence_quality=record.evidence_quality,
            acquisition_risk=record.acquisition_risk,
        )
        if not is_new:
            duplicates += 1
            continue
        imported += 1
        normalized_item_ids.add(process_new_raw(db, raw).id)
    if normalized_item_ids:
        refresh_derived_analysis(db, normalized_item_ids=normalized_item_ids)
    keyword = db.scalar(select(Keyword).where(Keyword.canonical == str(fixture["keyword_canonical"])))
    if keyword is None:
        raise RuntimeError("synthetic hiring fixture did not materialize its declared keyword")
    opportunity = _ensure_mock_opportunity(db, keyword=keyword)
    alerts = materialize_hiring_surge_alerts(db, keyword_ids={keyword.id}, window_end=selected_window_end)
    return {
        "fixture_name": fixture["fixture_name"],
        "data_class": fixture["data_class"],
        "window_end": selected_window_end.isoformat(),
        "records": len(fixture["records"]),
        "imported": imported,
        "duplicates": duplicates,
        "normalized": len(normalized_item_ids),
        "keyword_id": keyword.id,
        "opportunity_id": opportunity.id,
        "alerts": alerts,
    }
