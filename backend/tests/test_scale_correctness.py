from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.time import utc_now
from app.db.models import (
    AlertEvaluationQueue,
    Keyword,
    KeywordRelation,
    KeywordRelationSource,
    KeywordTrendDaily,
    Opportunity,
    OpportunityLineage,
    OpportunityResearch,
)
from app.db.session import SessionLocal
from app.main import app
from app.worker import run_once

client = TestClient(app)


def _records(term: str, prefix: str):
    return [
        {"source_id": f"{prefix}-market", "query": term, "external_id": f"{prefix}-1", "item_type": "PRODUCT", "title": term, "text": f"{term} tool"},
        {"source_id": f"{prefix}-jobs", "query": term, "external_id": f"{prefix}-2", "item_type": "JOB", "title": term, "text": f"{term} operator"},
        {"source_id": f"{prefix}-trend", "query": term, "external_id": f"{prefix}-3", "item_type": "TREND", "title": term, "text": f"{term} growth"},
    ]


def test_incremental_refresh_keeps_unrelated_trend_materialization():
    assert client.post("/api/v1/import", json={"records": _records("alpha-topic", "a")}).status_code == 200
    with SessionLocal() as db:
        alpha = db.scalar(select(Keyword).where(Keyword.canonical == "alpha-topic"))
        assert alpha is not None
        before = db.scalars(select(KeywordTrendDaily).where(KeywordTrendDaily.keyword_id == alpha.id)).all()
        assert before
        before_values = [(row.day, row.observation_count, row.source_count) for row in before]
    assert client.post("/api/v1/import", json={"records": _records("beta-topic", "b")}).status_code == 200
    with SessionLocal() as db:
        after = db.scalars(select(KeywordTrendDaily).where(KeywordTrendDaily.keyword_id == alpha.id)).all()
        assert [(row.day, row.observation_count, row.source_count) for row in after] == before_values


def test_opportunity_identity_survives_cluster_merge_and_records_lineage():
    assert client.post("/api/v1/import", json={"records": _records("alpha-topic", "a")}).status_code == 200
    assert client.post("/api/v1/import", json={"records": _records("beta-topic", "b")}).status_code == 200
    rows = client.get("/api/v1/opportunities", params={"min_score": 1}).json()
    alpha = next(row for row in rows if row["title"] == "alpha-topic")
    beta = next(row for row in rows if row["title"] == "beta-topic")
    alpha_detail = client.get(f"/api/v1/opportunities/{alpha['id']}").json()
    stable_key = alpha_detail["opportunity_key"]
    assert client.patch(
        f"/api/v1/opportunities/{alpha['id']}/research",
        json={"starred": True, "status": "TRACKING", "priority": 5, "notes": "preserve-me"},
    ).status_code == 200

    bridge = {"records": [
        {"source_id": "bridge-1", "query": "bridge", "external_id": "br1", "item_type": "PRODUCT", "title": "alpha-topic beta-topic", "text": "alpha-topic beta-topic"},
        {"source_id": "bridge-2", "query": "bridge", "external_id": "br2", "item_type": "TREND", "title": "alpha-topic beta-topic", "text": "alpha-topic beta-topic"},
    ]}
    assert client.post("/api/v1/import", json=bridge).status_code == 200

    with SessionLocal() as db:
        research = db.get(OpportunityResearch, alpha["id"])
        assert research is not None and research.starred is True and research.notes == "preserve-me"
        survivor = db.get(Opportunity, alpha["id"])
        assert survivor is not None and survivor.opportunity_key == stable_key
        lineage = db.scalars(select(OpportunityLineage)).all()
        assert any(row.parent_opportunity_id == beta["id"] and row.child_opportunity_id == alpha["id"] and row.relation_type == "MERGED_INTO" for row in lineage)
        assert survivor.cluster_generation >= 2


def test_relation_source_count_is_incremental_and_deduplicated():
    payload = {"records": [
        {"source_id": "same", "query": "pair", "external_id": "1", "item_type": "CONTENT", "title": "foo-topic bar-topic", "text": "foo-topic bar-topic"},
        {"source_id": "same", "query": "pair", "external_id": "2", "item_type": "CONTENT", "title": "foo-topic bar-topic", "text": "foo-topic bar-topic second"},
        {"source_id": "other", "query": "pair", "external_id": "3", "item_type": "CONTENT", "title": "foo-topic bar-topic", "text": "foo-topic bar-topic"},
    ]}
    assert client.post("/api/v1/import", json=payload).status_code == 200
    with SessionLocal() as db:
        foo = db.scalar(select(Keyword).where(Keyword.canonical == "foo-topic"))
        bar = db.scalar(select(Keyword).where(Keyword.canonical == "bar-topic"))
        a, b = sorted([foo.id, bar.id])
        relation = db.scalar(select(KeywordRelation).where(KeywordRelation.keyword_a_id == a, KeywordRelation.keyword_b_id == b))
        assert relation is not None
        assert relation.cooccurrence_count == 3
        assert relation.source_count == 2
        sources = db.scalars(select(KeywordRelationSource).where(KeywordRelationSource.keyword_a_id == a, KeywordRelationSource.keyword_b_id == b)).all()
        assert {row.source_id for row in sources} == {"same", "other"}


def test_alert_evaluation_queue_processes_changed_opportunity_only():
    assert client.post("/api/v1/import", json={"records": _records("queue-topic", "q")}).status_code == 200
    with SessionLocal() as db:
        queued = db.scalars(select(AlertEvaluationQueue)).all()
        assert queued
        queued_ids = {row.opportunity_id for row in queued}
    assert client.post("/api/v1/alerts/rules", json={"name": "queue-rule", "min_score": 1, "min_evidence_count": 1}).status_code == 200
    result = client.post("/api/v1/alerts/run-pending", params={"limit": 100})
    assert result.status_code == 200
    assert result.json()["processed"] == len(queued_ids)
    with SessionLocal() as db:
        assert db.scalars(select(AlertEvaluationQueue)).all() == []


def test_cursor_pagination_has_no_duplicate_items():
    for idx, term in enumerate(["page-alpha", "page-beta", "page-gamma"]):
        assert client.post("/api/v1/import", json={"records": _records(term, f"p{idx}")}).status_code == 200
    first = client.get("/api/v1/opportunities/page", params={"min_score": 1, "limit": 1})
    assert first.status_code == 200
    data1 = first.json()
    assert len(data1["items"]) == 1 and data1["next_cursor"]
    second = client.get("/api/v1/opportunities/page", params={"min_score": 1, "limit": 1, "cursor": data1["next_cursor"]})
    assert second.status_code == 200
    data2 = second.json()
    assert len(data2["items"]) == 1
    assert data1["items"][0]["id"] != data2["items"][0]["id"]

    observations1 = client.get("/api/v1/observations", params={"limit": 2}).json()
    assert observations1["next_cursor"]
    observations2 = client.get("/api/v1/observations", params={"limit": 2, "cursor": observations1["next_cursor"]}).json()
    assert {row["id"] for row in observations1["items"]}.isdisjoint({row["id"] for row in observations2["items"]})


def test_worker_heartbeat_and_retention_dry_run_are_operational():
    result = run_once(sync=False, limit=1, mode="maintenance", worker_id="test-maintenance")
    assert result["worker_id"] == "test-maintenance"
    workers = client.get("/api/v1/workers")
    assert workers.status_code == 200
    row = next(row for row in workers.json() if row["worker_id"] == "test-maintenance")
    assert row["status"] == "IDLE"
    retention = client.post("/api/v1/maintenance/retention", params={"dry_run": True})
    assert retention.status_code == 200
    assert retention.json()["dry_run"] is True
    assert retention.json()["policies"]["raw_observations"]["enabled"] is False


def test_incremental_opportunity_refresh_does_not_touch_unrelated_cluster():
    assert client.post("/api/v1/import", json={"records": _records("isolated-alpha", "ia")}).status_code == 200
    assert client.post("/api/v1/import", json={"records": _records("isolated-beta", "ib")}).status_code == 200
    with SessionLocal() as db:
        beta = db.scalar(select(Opportunity).where(Opportunity.title == "isolated-beta"))
        assert beta is not None
        beta_id = beta.id
        before_updated = beta.updated_at
        before_generation = beta.cluster_generation
    extra = {"records": [{"source_id": "ia-extra", "query": "isolated-alpha", "external_id": "ia-extra", "item_type": "TREND", "title": "isolated-alpha", "text": "isolated-alpha extra growth"}]}
    assert client.post("/api/v1/import", json=extra).status_code == 200
    with SessionLocal() as db:
        beta = db.get(Opportunity, beta_id)
        assert beta is not None
        assert beta.updated_at == before_updated
        assert beta.cluster_generation == before_generation


def test_keyword_relation_refresh_has_bounded_query_count():
    from sqlalchemy import event
    from app.db.models import KeywordMention, NormalizedItem, RawObservation
    from app.services.graph import refresh_relations_for_item

    with SessionLocal() as db:
        raw = RawObservation(
            source_id="query-count", query="q", item_type="CONTENT", title="", text="",
            observed_at=utc_now(), acquisition_method="MANUAL_IMPORT", evidence_quality="D", acquisition_risk="R1",
            content_hash="query-count-hash", raw_payload={},
        )
        db.add(raw); db.flush()
        item = NormalizedItem(raw_observation_id=raw.id, canonical_key="query-count", source_id="query-count", query="q", item_type="CONTENT", title="", text="", observed_at=raw.observed_at)
        db.add(item); db.flush()
        for idx in range(12):
            kw = Keyword(canonical=f"query-term-{idx}", display_name=f"query-term-{idx}", status="DISCOVERED", first_seen_at=raw.observed_at, last_seen_at=raw.observed_at)
            db.add(kw); db.flush()
            db.add(KeywordMention(keyword_id=kw.id, normalized_item_id=item.id, source_id="query-count", observed_at=raw.observed_at))
        db.flush()
        counter = {"count": 0}
        def before_cursor_execute(*_args, **_kwargs):
            counter["count"] += 1
        event.listen(db.get_bind(), "before_cursor_execute", before_cursor_execute)
        try:
            refresh_relations_for_item(db, item)
        finally:
            event.remove(db.get_bind(), "before_cursor_execute", before_cursor_execute)
        # 1 mention query + 1 relation batch query + 1 source batch query + bounded flush statements.
        # SQLAlchemy executemany may emit a few statements, but this must stay far below the old 100+ N+1 path.
        assert counter["count"] <= 12, counter
