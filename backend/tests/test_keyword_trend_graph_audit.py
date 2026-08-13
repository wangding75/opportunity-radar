from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.core.time import utc_now
from app.db.models import KeywordRelation, KeywordRelationItem
from app.db.session import SessionLocal
from app.services.analysis import process_new_raw, refresh_derived_analysis
from app.services.ingestion import from_import, store_collected
from app.services.keyword_trend_graph_audit import audit_keyword_trend_graph
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, EvidenceQuality
from app.domain.schemas import ImportRecord


def _ingest(db, source: str, external_id: str):
    record = ImportRecord(
        source_id=source,
        query="synthetic graph audit",
        external_id=external_id,
        item_type="CONTENT",
        title="synthetic graph audit",
        text="synthetic graph trend keyword evidence",
        observed_at=utc_now(),
        payload={"data_class": "SYNTHETIC"},
    )
    raw, inserted = store_collected(
        db,
        source_id=source,
        query=record.query,
        record=from_import(record),
        acquisition_method=AcquisitionMethod.MANUAL_IMPORT,
        evidence_quality=EvidenceQuality.C,
        acquisition_risk=AcquisitionRisk.R2,
    )
    item = process_new_raw(db, raw)
    return item, inserted


def test_empty_keyword_trend_graph_audit_is_pass():
    with SessionLocal() as db:
        result = audit_keyword_trend_graph(db)
        assert result["status"] == "PASS"
        assert result["summary"]["real_data_collected"] == 0


def test_keyword_trend_graph_counts_and_item_level_retry_are_idempotent():
    with SessionLocal() as db:
        item, inserted = _ingest(db, "synthetic-graph-a", "item-a")
        assert inserted is True
        process_new_raw(db, db.get(type(item.raw_observation), item.raw_observation_id))
        refresh_derived_analysis(db, normalized_item_ids={item.id})
        first = audit_keyword_trend_graph(db)
        assert first["status"] == "PASS", first
        relation_counts_before = {row.id: row.cooccurrence_count for row in db.scalars(select(KeywordRelation)).all()}
        relation_items_before = db.query(KeywordRelationItem).count()
        process_new_raw(db, db.get(type(item.raw_observation), item.raw_observation_id))
        assert {row.id: row.cooccurrence_count for row in db.scalars(select(KeywordRelation)).all()} == relation_counts_before
        assert db.query(KeywordRelationItem).count() == relation_items_before
        assert audit_keyword_trend_graph(db)["status"] == "PASS"


def test_keyword_trend_graph_audit_detects_relation_counter_drift():
    with SessionLocal() as db:
        item, _ = _ingest(db, "synthetic-graph-b", "item-b")
        refresh_derived_analysis(db, normalized_item_ids={item.id})
        relation = db.scalar(select(KeywordRelation))
        assert relation is not None
        relation.cooccurrence_count += 1
        result = audit_keyword_trend_graph(db)
        assert result["status"] == "FAIL"
        assert any(row["rule"] == "relation_counts_match_items" for row in result["violations"])
