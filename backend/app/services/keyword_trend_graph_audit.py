"""Auditable correctness checks for keyword metrics, trend buckets and graph edges."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordMention, KeywordRelation, KeywordRelationItem, KeywordRelationSource, KeywordTrendDaily, NormalizedItem

KEYWORD_TREND_GRAPH_CONTRACT_VERSION = "keyword-trend-graph-v1"


def audit_keyword_trend_graph(db: Session, *, days: int = 90) -> dict:
    if days < 1 or days > 366:
        raise ValueError("days must be between 1 and 366")
    violations: list[dict] = []
    keywords = db.scalars(select(Keyword).order_by(Keyword.id)).all()
    mentions = db.scalars(select(KeywordMention).order_by(KeywordMention.id)).all()
    items = {item.id: item for item in db.scalars(select(NormalizedItem)).all()}
    keyword_ids = {keyword.id for keyword in keywords}

    mention_counts: Counter[int] = Counter()
    mention_sources: dict[int, set[str]] = defaultdict(set)
    expected_trends: Counter[tuple[int, object]] = Counter()
    expected_trend_sources: dict[tuple[int, object], set[str]] = defaultdict(set)
    cutoff = utc_now().date() - timedelta(days=days - 1)
    for mention in mentions:
        item = items.get(mention.normalized_item_id)
        if mention.keyword_id not in keyword_ids or item is None:
            violations.append({"rule": "keyword_mention_references_existing_rows", "mention_id": mention.id})
            continue
        if mention.source_id != item.source_id or mention.observed_at != item.observed_at:
            violations.append({"rule": "keyword_mention_mirrors_normalized_item", "mention_id": mention.id})
        mention_counts[mention.keyword_id] += 1
        mention_sources[mention.keyword_id].add(mention.source_id)
        if mention.observed_at.date() >= cutoff:
            key = (mention.keyword_id, mention.observed_at.date())
            expected_trends[key] += 1
            expected_trend_sources[key].add(mention.source_id)

    for keyword in keywords:
        if keyword.observation_count != mention_counts[keyword.id]:
            violations.append({"rule": "keyword_observation_count", "keyword_id": keyword.id})
        if keyword.source_count != len(mention_sources[keyword.id]):
            violations.append({"rule": "keyword_source_count", "keyword_id": keyword.id})

    trend_rows = db.scalars(select(KeywordTrendDaily).order_by(KeywordTrendDaily.keyword_id, KeywordTrendDaily.day)).all()
    trend_keys = [(row.keyword_id, row.day) for row in trend_rows]
    duplicate_trend_keys = [key for key, count in Counter(trend_keys).items() if count > 1]
    if duplicate_trend_keys:
        violations.append({"rule": "trend_day_unique", "keys": [list(key) for key in duplicate_trend_keys]})
    actual_trends = {(row.keyword_id, row.day): row for row in trend_rows}
    for key, count in expected_trends.items():
        row = actual_trends.get(key)
        if row is None or row.observation_count != count or row.source_count != len(expected_trend_sources[key]):
            violations.append({"rule": "trend_bucket_matches_mentions", "keyword_id": key[0], "day": key[1].isoformat()})
    for key, row in actual_trends.items():
        if key[1] >= cutoff and (key not in expected_trends or row.observation_count <= 0 or row.source_count <= 0):
            violations.append({"rule": "trend_bucket_has_evidence", "keyword_id": key[0], "day": key[1].isoformat()})

    relation_items = db.scalars(select(KeywordRelationItem)).all()
    relation_item_keys = [
        (row.keyword_a_id, row.keyword_b_id, row.relation_type, row.normalized_item_id)
        for row in relation_items
    ]
    duplicate_relation_items = [key for key, count in Counter(relation_item_keys).items() if count > 1]
    if duplicate_relation_items:
        violations.append({"rule": "relation_item_idempotency", "keys": [list(key) for key in duplicate_relation_items]})
    relation_item_counts: Counter[tuple[int, int, str]] = Counter()
    relation_item_sources: dict[tuple[int, int, str], set[str]] = defaultdict(set)
    relation_source_keys: set[tuple[int, int, str]] = set()
    for row in relation_items:
        if row.keyword_a_id >= row.keyword_b_id or row.keyword_a_id not in keyword_ids or row.keyword_b_id not in keyword_ids:
            violations.append({"rule": "relation_item_canonical_pair", "relation_item_id": row.id})
        if row.normalized_item_id not in items:
            violations.append({"rule": "relation_item_references_item", "relation_item_id": row.id})
        key = (row.keyword_a_id, row.keyword_b_id, row.relation_type)
        relation_item_counts[key] += 1
        relation_item_sources[key].add(row.source_id)
        relation_source_keys.add((row.keyword_a_id, row.keyword_b_id, row.source_id))

    relations = db.scalars(select(KeywordRelation)).all()
    relation_keys = {(row.keyword_a_id, row.keyword_b_id, row.relation_type) for row in relations}
    for relation in relations:
        key = (relation.keyword_a_id, relation.keyword_b_id, relation.relation_type)
        expected_count = relation_item_counts[key]
        expected_sources = len(relation_item_sources[key])
        expected_weight = round(min(100.0, expected_count * 2.0 + expected_sources * 5.0), 2)
        if relation.keyword_a_id >= relation.keyword_b_id:
            violations.append({"rule": "relation_canonical_pair", "relation_id": relation.id})
        if relation.cooccurrence_count != expected_count or relation.source_count != expected_sources:
            violations.append({"rule": "relation_counts_match_items", "relation_id": relation.id})
        if round(float(relation.weight), 2) != expected_weight:
            violations.append({"rule": "relation_weight_matches_counts", "relation_id": relation.id})
        if relation.first_seen_at > relation.last_seen_at:
            violations.append({"rule": "relation_time_order", "relation_id": relation.id})
        if expected_count == 0:
            violations.append({"rule": "relation_has_materialized_items", "relation_id": relation.id})
    for key in relation_item_counts:
        if key not in relation_keys:
            violations.append({"rule": "relation_item_has_relation", "key": list(key)})

    sources = db.scalars(select(KeywordRelationSource)).all()
    actual_source_keys = {(row.keyword_a_id, row.keyword_b_id, row.source_id) for row in sources}
    if actual_source_keys != relation_source_keys:
        violations.append({"rule": "relation_sources_match_items", "missing": [list(x) for x in sorted(relation_source_keys - actual_source_keys)], "orphaned": [list(x) for x in sorted(actual_source_keys - relation_source_keys)]})

    return {
        "audit_id": "opportunity-radar-keyword-trend-graph",
        "contract_version": KEYWORD_TREND_GRAPH_CONTRACT_VERSION,
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
        "summary": {
            "keywords": len(keywords),
            "keyword_mentions": len(mentions),
            "trend_buckets": len(trend_rows),
            "graph_relations": len(relations),
            "relation_items": len(relation_items),
            "relation_sources": len(sources),
            "window_days": days,
            "real_data_collected": 0,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }
