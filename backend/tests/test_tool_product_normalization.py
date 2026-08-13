from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import (
    NormalizedItem,
    RawObservation,
    ToolProductEntity,
    ToolProductEntityEvidence,
    ToolProductNormalizationRun,
)
from app.db.session import SessionLocal
from app.main import app
from app.domain.tool_product import ToolProductIdentificationPolicy
from app.services.tool_products import normalize_tool_product_entities


client = TestClient(app)


def _seed_item(db, *, source: str, title: str, text: str, index: int, item_type: str = "CONTENT", content_hash: str | None = None) -> int:
    raw = RawObservation(
        source_id=source,
        external_id=f"synthetic-tool-{index}",
        query="SYNTHETIC tool discovery",
        item_type=item_type,
        title=title,
        text=text,
        source_url=f"https://synthetic.invalid/{index}",
        observed_at=datetime(2026, 8, 12, index % 23),
        acquisition_method="MANUAL_IMPORT",
        evidence_quality="E",
        acquisition_risk="R2",
        content_hash=content_hash or f"{index:064x}",
        raw_payload={"data_class": "SYNTHETIC"},
    )
    db.add(raw)
    db.flush()
    item = NormalizedItem(
        raw_observation_id=raw.id,
        canonical_key=f"synthetic-tool-item-{index}",
        source_id=source,
        query=raw.query,
        item_type=item_type,
        title=title,
        text=text,
        source_url=raw.source_url,
        observed_at=raw.observed_at,
    )
    db.add(item)
    db.flush()
    return item.id


def test_normalization_merges_two_sources_and_is_idempotent():
    with SessionLocal() as db:
        first_id = _seed_item(db, source="synthetic-a", title="Acme Copilot Tool", text="MOCK tool listing", index=1)
        second_id = _seed_item(db, source="synthetic-b", title=" acme   copilot tool ", text="SYNTHETIC tool review", index=2)
        result = normalize_tool_product_entities(db, normalized_item_ids={first_id, second_id}, evaluated_at=datetime(2026, 8, 12, 4))
        db.commit()

        repeat = normalize_tool_product_entities(db, normalized_item_ids={second_id}, evaluated_at=datetime(2026, 8, 12, 5))
        db.commit()

        entity = db.scalar(select(ToolProductEntity))
        links = db.scalars(select(ToolProductEntityEvidence).where(ToolProductEntityEvidence.entity_id == entity.id)).all()
        runs = db.scalars(select(ToolProductNormalizationRun)).all()

    assert result["identified"] == 1
    assert result["evidence_links"] == 2
    assert repeat["duplicates"] == 1
    assert entity is not None
    assert entity.kind == "TOOL"
    assert entity.source_count == 2
    assert len(links) == 2
    assert len(runs) == 1
    assert all(row.evidence_id.startswith("ev1_") for row in links)


def test_empty_and_ambiguous_inputs_fail_closed_without_entity_rows():
    with SessionLocal() as db:
        empty = normalize_tool_product_entities(db, normalized_item_ids=set())
        _seed_item(db, source="synthetic-empty", title="Acme", text="SYNTHETIC market mention", index=3)
        _seed_item(db, source="synthetic-empty-2", title=" acme ", text="SYNTHETIC market mention", index=5)
        ambiguous = normalize_tool_product_entities(db, limit=10)
        db.commit()
        entities = db.scalars(select(ToolProductEntity)).all()
        runs = db.scalars(select(ToolProductNormalizationRun)).all()

    assert empty["evaluated"] == 0
    assert ambiguous["unresolved"] == 1
    assert entities == []
    assert len(runs) == 1
    assert runs[0].status == "UNRESOLVED"


def test_invalid_evidence_fails_closed_and_retry_succeeds_after_rollback():
    with SessionLocal() as db:
        item_id = _seed_item(db, source="synthetic-retry", title="Retry Tool", text="MOCK tool", index=4, content_hash="invalid")
        db.commit()
        policy = ToolProductIdentificationPolicy(min_evidence_count=1)
        with pytest.raises(ValueError, match="content_hash"):
            normalize_tool_product_entities(db, normalized_item_ids={item_id}, policy=policy)
        db.rollback()
        raw = db.scalar(select(RawObservation).where(RawObservation.external_id == "synthetic-tool-4"))
        raw.content_hash = "4" * 64
        db.flush()
        result = normalize_tool_product_entities(db, normalized_item_ids={item_id}, policy=policy)
        db.commit()

    assert result["identified"] == 1
    assert result["duplicates"] == 0


def test_normalization_enforces_bounds_and_admin_rbac():
    with SessionLocal() as db:
        with pytest.raises(ValueError, match="between 1 and 500"):
            normalize_tool_product_entities(db, limit=501)

    from dataclasses import replace
    import app.core.security as security
    from app.core.config import settings

    original = security.settings
    security.settings = replace(settings, auth_mode="rbac")
    try:
        response = client.post("/api/v1/tool-products/normalize")
    finally:
        security.settings = original
    assert response.status_code == 401


def test_admin_normalization_api_materializes_and_reader_can_trace_entity():
    with SessionLocal() as db:
        _seed_item(db, source="synthetic-api-a", title="Radar Copilot Tool", text="MOCK tool", index=6)
        _seed_item(db, source="synthetic-api-b", title="radar copilot tool", text="SYNTHETIC tool", index=7)
        db.commit()

    response = client.post("/api/v1/tool-products/normalize", params={"limit": 20})
    assert response.status_code == 200
    assert response.json()["identified"] == 1
    entities = client.get("/api/v1/tool-products/entities", params={"kind": "TOOL"})
    assert entities.status_code == 200
    entity = entities.json()[0]
    detail = client.get(f"/api/v1/tool-products/entities/{entity['entity_key']}")
    assert detail.status_code == 200
    assert len(detail.json()["evidence"]) == 2
    occurrences = client.get("/api/v1/tool-products/occurrences", params={"classification": "FIRST_SEEN"})
    assert occurrences.status_code == 200
    assert len(occurrences.json()) == 1
