from __future__ import annotations

from sqlalchemy.orm import Session

from app.connectors.base import SourceConnector
from app.domain.schemas import CollectorQuery
from app.services.analysis import process_new_raw, refresh_derived_analysis
from app.services.ingestion import store_collected


def collect_and_process(db: Session, connector: SourceConnector, query: CollectorQuery) -> dict:
    result = connector.collect(query)
    inserted = 0
    duplicates = 0
    normalized = 0
    item_ids: set[int] = set()
    for record in result.records:
        raw, is_new = store_collected(
            db,
            source_id=result.source_id,
            query=result.query,
            record=record,
            acquisition_method=connector.descriptor.acquisition_method,
            evidence_quality=connector.descriptor.evidence_quality,
            acquisition_risk=connector.descriptor.acquisition_risk,
        )
        if not is_new:
            duplicates += 1
            continue
        inserted += 1
        item = process_new_raw(db, raw)
        item_ids.add(item.id)
        normalized += 1
    derived = refresh_derived_analysis(db, normalized_item_ids=item_ids) if item_ids else None
    return {
        "source_id": result.source_id,
        "query": result.query,
        "fetched": len(result.records),
        "inserted": inserted,
        "duplicates": duplicates,
        "normalized": normalized,
        "derived": derived,
    }
