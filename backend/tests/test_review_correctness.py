from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.postgres_cli import postgres_cli_connection
from app.core.time import utc_now
from app.db.models import (
    AlertEvaluationQueue,
    Keyword,
    KeywordMention,
    KeywordRelation,
    NormalizedItem,
    Opportunity,
    OpportunityKeyword,
    OpportunityLineage,
    OpportunityResearch,
    RawObservation,
)
from app.db.session import SessionLocal
from app.services import alerts as alerts_service
from app.services.graph import refresh_relations_for_item
from app.services.opportunities import _cluster_keywords, _match_components, refresh_opportunities
from app.services.watch_keywords import create_watch_keyword, patch_watch_keyword


def _keyword(db, name: str, *, score: float = 40.0) -> Keyword:
    now = utc_now()
    row = Keyword(
        canonical=name,
        display_name=name,
        status="ACTIVE",
        first_seen_at=now,
        last_seen_at=now,
        observation_count=3,
        source_count=2,
        score=score,
    )
    db.add(row)
    db.flush()
    return row


def _item_with_mentions(db, names: list[str], *, query: str, source_id: str = "review") -> tuple[NormalizedItem, list[Keyword]]:
    now = utc_now()
    raw = RawObservation(
        source_id=source_id,
        query=query,
        item_type="CONTENT",
        title=" ".join(names),
        text=" ".join(names),
        observed_at=now,
        acquisition_method="MANUAL_IMPORT",
        evidence_quality="D",
        acquisition_risk="R1",
        content_hash=f"review-{source_id}-{query}-{now.timestamp()}",
        raw_payload={},
    )
    db.add(raw)
    db.flush()
    item = NormalizedItem(
        raw_observation_id=raw.id,
        canonical_key=f"review-{raw.id}",
        source_id=source_id,
        query=query,
        item_type="CONTENT",
        title=raw.title,
        text=raw.text,
        observed_at=now,
    )
    db.add(item)
    db.flush()
    rows = []
    for index, name in enumerate(names):
        kw = _keyword(db, name, score=float(index + 1))
        rows.append(kw)
        db.add(KeywordMention(keyword_id=kw.id, normalized_item_id=item.id, source_id=source_id, observed_at=now))
    db.flush()
    return item, rows


def test_cluster_keeps_all_members_beyond_analysis_payload_limit():
    with SessionLocal() as db:
        rows = [_keyword(db, f"cluster-{idx}") for idx in range(10)]
        now = utc_now()
        for a, b in zip(rows, rows[1:]):
            db.add(KeywordRelation(
                keyword_a_id=min(a.id, b.id),
                keyword_b_id=max(a.id, b.id),
                relation_type="CO_OCCURS",
                cooccurrence_count=3,
                source_count=2,
                first_seen_at=now,
                last_seen_at=now,
                weight=20.0,
            ))
        db.flush()
        components = _cluster_keywords(db, rows, now - timedelta(days=90))
        assert len(components) == 1
        assert {kw.id for kw in components[0]} == {kw.id for kw in rows}


def test_bounded_reconciliation_does_not_dormant_unprocessed_opportunity():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    for idx, term in enumerate(["limit-alpha", "limit-beta"]):
        records = [
            {"source_id": f"l{idx}-a", "query": term, "external_id": "1", "item_type": "PRODUCT", "title": term, "text": f"{term} tool"},
            {"source_id": f"l{idx}-b", "query": term, "external_id": "2", "item_type": "JOB", "title": term, "text": f"{term} operator"},
            {"source_id": f"l{idx}-c", "query": term, "external_id": "3", "item_type": "TREND", "title": term, "text": f"{term} growth"},
        ]
        assert client.post("/api/v1/import", json={"records": records}).status_code == 200
    with SessionLocal() as db:
        beta = db.scalar(select(Opportunity).where(Opportunity.title == "limit-beta"))
        alpha = db.scalar(select(Opportunity).where(Opportunity.title == "limit-alpha"))
        assert alpha is not None and beta is not None
        # Force alpha to be the only bounded candidate; beta must not be treated as
        # absent from the universe and marked dormant merely because of the limit.
        alpha_kw = db.get(Keyword, alpha.keyword_id)
        beta_kw = db.get(Keyword, beta.keyword_id)
        alpha_kw.score = 100.0
        beta_kw.score = 1.0
        beta_before = beta.stage
        refresh_opportunities(db, limit=1)
        db.commit()
        db.refresh(beta)
        assert beta.stage == beta_before
        assert beta.stage != "DORMANT"


def test_split_merge_preserves_used_parent_identity():
    with SessionLocal() as db:
        k1, k2, k3, k4 = [_keyword(db, f"split-{idx}") for idx in range(4)]
        a = Opportunity(opportunity_key="opp:a", keyword_id=k1.id, title="A", stage="DISCOVERY")
        b = Opportunity(opportunity_key="opp:b", keyword_id=k3.id, title="B", stage="DISCOVERY")
        db.add_all([a, b]); db.flush()
        for opp, keys in [(a, [k1, k2]), (b, [k3, k4])]:
            for index, kw in enumerate(keys):
                db.add(OpportunityKeyword(opportunity_id=opp.id, keyword_id=kw.id, role="PRIMARY" if index == 0 else "RELATED", weight=kw.score))
        db.flush()
        assigned = _match_components(
            db,
            [[k1], [k2, k3, k4]],
            [a, b],
            {a.id: {k1.id, k2.id}, b.id: {k3.id, k4.id}},
            now=utc_now(),
        )
        assert assigned[0][1].id == a.id
        assert a.stage != "DORMANT"
        assert assigned[1][1].id == b.id
        db.flush()
        lineage = db.scalars(select(OpportunityLineage)).all()
        assert any(row.parent_opportunity_id == a.id and row.child_opportunity_id == b.id and row.relation_type == "SPLIT_MERGED_INTO" for row in lineage)


def test_watch_disable_and_priority_change_recalculate_keyword_immediately():
    with SessionLocal() as db:
        watch = create_watch_keyword(db, "watch-review", priority=5)
        db.flush()
        kw = db.scalar(select(Keyword).where(Keyword.canonical == "watch-review"))
        high_score = kw.score
        assert kw.status == "WATCHING"
        patch_watch_keyword(db, watch.id, priority=1)
        db.flush()
        db.refresh(kw)
        assert kw.score < high_score
        patch_watch_keyword(db, watch.id, enabled=False)
        db.flush()
        db.refresh(kw)
        assert kw.status != "WATCHING"
        assert kw.score == 0.0


def test_graph_selection_is_deterministic_and_prioritizes_query_keyword():
    with SessionLocal() as db:
        names = [f"graph-{idx}" for idx in range(13)]
        query = names[-1]
        item, rows = _item_with_mentions(db, names, query=query)
        query_id = rows[-1].id
        refresh_relations_for_item(db, item)
        db.flush()
        relations = db.scalars(select(KeywordRelation)).all()
        included = {value for rel in relations for value in (rel.keyword_a_id, rel.keyword_b_id)}
        assert query_id in included
        assert len(included) == 12


def test_alert_claim_is_exclusive_for_same_revision():
    with SessionLocal() as db:
        kw = _keyword(db, "claim-topic")
        opp = Opportunity(opportunity_key="opp:claim", keyword_id=kw.id, title="claim", stage="DISCOVERY")
        db.add(opp); db.flush()
        alerts_service.enqueue_alert_evaluations(db, {opp.id})
        db.commit()
        now = utc_now()
        assert alerts_service._claim_alert_evaluation(db, opp.id, 1, now=now) is True
        assert alerts_service._claim_alert_evaluation(db, opp.id, 1, now=now) is False


def test_alert_reenqueue_during_processing_is_not_lost(monkeypatch):
    with SessionLocal() as db:
        kw = _keyword(db, "reenqueue-topic")
        opp = Opportunity(opportunity_key="opp:reenqueue", keyword_id=kw.id, title="reenqueue", stage="DISCOVERY")
        db.add(opp); db.flush()
        alerts_service.enqueue_alert_evaluations(db, {opp.id})
        db.commit()

        def evaluate_and_requeue(session, *, opportunity_ids=None):
            alerts_service.enqueue_alert_evaluations(session, set(opportunity_ids or ()), reason="NEWER_SIGNAL")
            session.flush()
            return {"rules": 0, "opportunities": 1, "matched": 0, "created": 0}

        monkeypatch.setattr(alerts_service, "evaluate_alert_rules", evaluate_and_requeue)
        result = alerts_service.run_pending_alert_evaluations(db, limit=10)
        assert result["processed"] == 1
        row = db.get(AlertEvaluationQueue, opp.id)
        assert row is not None
        assert row.revision == 2
        assert row.claim_until is None
        assert row.reason == "NEWER_SIGNAL"


def test_alert_failure_backoff_does_not_block_other_queue_items(monkeypatch):
    with SessionLocal() as db:
        k1 = _keyword(db, "poison-topic")
        k2 = _keyword(db, "healthy-topic")
        first = Opportunity(opportunity_key="opp:poison", keyword_id=k1.id, title="poison", stage="DISCOVERY")
        second = Opportunity(opportunity_key="opp:healthy", keyword_id=k2.id, title="healthy", stage="DISCOVERY")
        db.add_all([first, second]); db.flush()
        alerts_service.enqueue_alert_evaluations(db, {first.id, second.id})
        db.commit()

        def evaluate_one(_session, *, opportunity_ids=None):
            opportunity_id = next(iter(opportunity_ids or ()))
            if opportunity_id == first.id:
                raise RuntimeError("poison")
            return {"rules": 0, "opportunities": 1, "matched": 0, "created": 0}

        monkeypatch.setattr(alerts_service, "evaluate_alert_rules", evaluate_one)
        result = alerts_service.run_pending_alert_evaluations(db, limit=10)
        assert result["failed"] == 1
        assert result["processed"] == 1
        failed = db.get(AlertEvaluationQueue, first.id)
        assert failed is not None and failed.attempt_count == 1 and failed.next_retry_at > utc_now()
        assert db.get(AlertEvaluationQueue, second.id) is None


def test_postgres_cli_parser_removes_driver_suffix_and_password_from_argv():
    args, env = postgres_cli_connection(
        "postgresql+psycopg://research:p%40ss@db.example:5433/radar?sslmode=require"
    )
    joined = " ".join(args)
    assert "postgresql+psycopg" not in joined
    assert "p@ss" not in joined
    assert args == ["--host", "db.example", "--port", "5433", "--username", "research", "--dbname", "radar"]
    assert env["PGPASSWORD"] == "p@ss"
    assert env["PGSSLMODE"] == "require"


def test_injected_http_clients_remain_caller_owned_after_connector_close():
    import httpx
    from app.connectors.github import GitHubSearchConnector
    from app.connectors.google_trends import GoogleTrendsRssConnector

    github_client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"items": []})))
    trends_client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"<rss><channel/></rss>")))
    GitHubSearchConnector(client=github_client).close()
    GoogleTrendsRssConnector(client=trends_client).close()
    assert github_client.is_closed is False
    assert trends_client.is_closed is False
    github_client.close()
    trends_client.close()


def test_bounded_refresh_keeps_complete_connected_cluster_membership():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    for source, external in [("cluster-a", "1"), ("cluster-b", "2")]:
        assert client.post("/api/v1/import", json={"records": [{
            "source_id": source,
            "query": "bound-alpha",
            "external_id": external,
            "item_type": "PRODUCT",
            "title": "bound-alpha bound-beta",
            "text": "bound-alpha bound-beta tool",
        }]}).status_code == 200
    # Add independent observations so both explicit terms satisfy opportunity candidate thresholds.
    for term in ["bound-alpha", "bound-beta"]:
        assert client.post("/api/v1/import", json={"records": [
            {"source_id": f"{term}-x", "query": term, "external_id": "x", "item_type": "TREND", "title": term, "text": term},
            {"source_id": f"{term}-y", "query": term, "external_id": "y", "item_type": "TREND", "title": term, "text": term},
        ]}).status_code == 200
    with SessionLocal() as db:
        alpha = db.scalar(select(Keyword).where(Keyword.canonical == "bound-alpha"))
        beta = db.scalar(select(Keyword).where(Keyword.canonical == "bound-beta"))
        assert alpha is not None and beta is not None
        alpha.score = 100.0
        beta.score = 1.0
        db.flush()
        refresh_opportunities(db, limit=1)
        db.commit()
        containing_both = db.scalars(
            select(Opportunity).join(OpportunityKeyword).where(OpportunityKeyword.keyword_id.in_([alpha.id, beta.id]))
        ).all()
        by_id = {}
        for opp in containing_both:
            by_id.setdefault(opp.id, opp)
        assert any(
            {row.keyword_id for row in db.scalars(select(OpportunityKeyword).where(OpportunityKeyword.opportunity_id == opp.id)).all()} >= {alpha.id, beta.id}
            for opp in by_id.values()
            if opp.stage != "DORMANT"
        )


def test_new_alert_rule_queues_existing_opportunities_for_evaluation():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    assert client.post("/api/v1/import", json={"records": [
        {"source_id": "rule-existing-a", "query": "rule-existing", "external_id": "1", "item_type": "PRODUCT", "title": "rule-existing", "text": "rule-existing tool"},
        {"source_id": "rule-existing-b", "query": "rule-existing", "external_id": "2", "item_type": "JOB", "title": "rule-existing", "text": "rule-existing operator"},
        {"source_id": "rule-existing-c", "query": "rule-existing", "external_id": "3", "item_type": "TREND", "title": "rule-existing", "text": "rule-existing growth"},
    ]}).status_code == 200
    with SessionLocal() as db:
        # Simulate a system that already drained opportunity-change alerts before
        # the user creates a new alert rule.
        for row in db.scalars(select(AlertEvaluationQueue)).all():
            db.delete(row)
        db.commit()
        active_ids = set(db.scalars(select(Opportunity.id).where(Opportunity.stage != "DORMANT")).all())
        assert active_ids
    created = client.post("/api/v1/alerts/rules", json={"name": "existing-opportunities", "min_score": 1, "min_evidence_count": 1})
    assert created.status_code == 200
    with SessionLocal() as db:
        queued_ids = {row.opportunity_id for row in db.scalars(select(AlertEvaluationQueue)).all()}
        assert active_ids <= queued_ids


def test_new_alert_revision_resets_old_failure_backoff_history():
    with SessionLocal() as db:
        kw = _keyword(db, "alert-revision-reset")
        opp = Opportunity(opportunity_key="opp:alert-revision-reset", keyword_id=kw.id, title="reset", stage="DISCOVERY")
        db.add(opp); db.flush()
        alerts_service.enqueue_alert_evaluations(db, {opp.id})
        row = db.get(AlertEvaluationQueue, opp.id)
        row.attempt_count = 7
        row.last_error = "old poison"
        row.next_retry_at = utc_now() + timedelta(hours=12)
        db.flush()
        alerts_service.enqueue_alert_evaluations(db, {opp.id}, reason="FRESH_SIGNAL")
        db.flush()
        row = db.get(AlertEvaluationQueue, opp.id)
        assert row.revision == 2
        assert row.attempt_count == 0
        assert row.last_error is None
        assert row.next_retry_at <= utc_now()


def _load_script_module(filename: str):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[2] / "scripts" / filename
    spec = importlib.util.spec_from_file_location(f"review_{filename.replace('.', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_postgres_restore_preflights_archive_before_destructive_restore(monkeypatch, tmp_path):
    restore = _load_script_module("restore_database.py")
    backup = tmp_path / "backup.pgdump"
    backup.write_bytes(b"fake-archive")
    calls = []
    monkeypatch.setattr(restore.shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(args, **kwargs):
        calls.append((list(args), kwargs))
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(restore.subprocess, "run", fake_run)
    restore.restore_postgres(backup, "postgresql+psycopg://u:secret@db/radar")
    assert calls[0][0][:2] == ["/usr/bin/pg_restore", "--list"]
    assert "--clean" in calls[1][0]
    assert "secret" not in " ".join(calls[1][0])
    assert calls[1][1]["env"]["PGPASSWORD"] == "secret"


def test_postgres_backup_is_atomic_and_cleans_failed_partial(monkeypatch, tmp_path):
    backup = _load_script_module("backup_database.py")
    output = tmp_path / "radar.pgdump"
    monkeypatch.setattr(backup.shutil, "which", lambda name: f"/usr/bin/{name}")

    calls = []
    def successful_run(args, **_kwargs):
        args = list(args); calls.append(args)
        if "--file" in args:
            target = args[args.index("--file") + 1]
            __import__("pathlib").Path(target).write_bytes(b"archive")
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(backup.subprocess, "run", successful_run)
    backup.backup_postgres("postgresql+psycopg://u:secret@db/radar", output)
    assert output.read_bytes() == b"archive"
    assert not output.with_suffix(output.suffix + ".tmp").exists()
    assert any(call[0].endswith("pg_restore") and "--list" in call for call in calls)


def test_connected_keyword_scope_limit_never_returns_partial_component():
    from app.services.graph import GraphScopeLimitExceeded, connected_keyword_ids
    from app.db.models import KeywordRelation

    with SessionLocal() as db:
        nodes = [_keyword(db, f"scope-limit-{idx}") for idx in range(4)]
        now = utc_now()
        db.add_all([
            KeywordRelation(keyword_a_id=nodes[0].id, keyword_b_id=nodes[1].id, relation_type="CO_OCCURS", cooccurrence_count=2, source_count=2, weight=20, first_seen_at=now, last_seen_at=now),
            KeywordRelation(keyword_a_id=nodes[1].id, keyword_b_id=nodes[2].id, relation_type="CO_OCCURS", cooccurrence_count=2, source_count=2, weight=20, first_seen_at=now, last_seen_at=now),
            KeywordRelation(keyword_a_id=nodes[2].id, keyword_b_id=nodes[3].id, relation_type="CO_OCCURS", cooccurrence_count=2, source_count=2, weight=20, first_seen_at=now, last_seen_at=now),
        ])
        db.flush()
        import pytest
        with pytest.raises(GraphScopeLimitExceeded):
            connected_keyword_ids(db, {nodes[0].id}, max_nodes=2)
