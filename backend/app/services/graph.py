from __future__ import annotations

from datetime import timedelta
from itertools import combinations

from sqlalchemy import insert, or_, select, tuple_, update
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordMention, KeywordRelation, KeywordRelationItem, KeywordRelationSource, NormalizedItem
from app.services.keywords import canonicalize_keyword

MAX_KEYWORDS_PER_ITEM = 12


class GraphScopeLimitExceeded(RuntimeError):
    """Raised when a bounded graph-closure request would be silently truncated."""



def refresh_relations_for_item(db: Session, item: NormalizedItem) -> None:
    """Increment relation counts using set-based reads and executemany writes."""
    mention_rows = db.execute(
        select(KeywordMention.keyword_id, Keyword.canonical, Keyword.score)
        .join(Keyword, Keyword.id == KeywordMention.keyword_id)
        .where(KeywordMention.normalized_item_id == item.id)
    ).all()
    query_canonical = canonicalize_keyword(item.query)
    ranked = sorted(
        mention_rows,
        key=lambda row: (
            0 if row.canonical == query_canonical else 1,
            -float(row.score or 0.0),
            row.keyword_id,
        ),
    )
    # Keep graph fan-out bounded, but choose the same keywords deterministically
    # across SQLite/PostgreSQL and always prefer the probe/query keyword.
    unique_ids = sorted({row.keyword_id for row in ranked[:MAX_KEYWORDS_PER_ITEM]})
    pairs = list(combinations(unique_ids, 2))
    if not pairs:
        return

    existing_relations = db.scalars(
        select(KeywordRelation).where(
            tuple_(KeywordRelation.keyword_a_id, KeywordRelation.keyword_b_id).in_(pairs),
            KeywordRelation.relation_type == "CO_OCCURS",
        )
    ).all()
    relation_by_pair = {(r.keyword_a_id, r.keyword_b_id): r for r in existing_relations}
    existing_sources = set(
        db.execute(
            select(KeywordRelationSource.keyword_a_id, KeywordRelationSource.keyword_b_id).where(
                KeywordRelationSource.source_id == item.source_id,
                tuple_(KeywordRelationSource.keyword_a_id, KeywordRelationSource.keyword_b_id).in_(pairs),
            )
        ).all()
    )
    processed_items = set(
        db.execute(
            select(KeywordRelationItem.keyword_a_id, KeywordRelationItem.keyword_b_id).where(
                KeywordRelationItem.normalized_item_id == item.id,
                KeywordRelationItem.relation_type == "CO_OCCURS",
                tuple_(KeywordRelationItem.keyword_a_id, KeywordRelationItem.keyword_b_id).in_(pairs),
            )
        ).all()
    )

    new_relations: list[dict] = []
    relation_updates: list[dict] = []
    new_sources: list[dict] = []
    new_items: list[dict] = []
    for a, b in pairs:
        pair = (a, b)
        if pair in processed_items:
            continue
        relation = relation_by_pair.get(pair)
        is_new_source = pair not in existing_sources
        if relation is None:
            source_count = 1 if is_new_source else 0
            new_relations.append({
                "keyword_a_id": a,
                "keyword_b_id": b,
                "relation_type": "CO_OCCURS",
                "cooccurrence_count": 1,
                "source_count": source_count,
                "first_seen_at": item.observed_at,
                "last_seen_at": item.observed_at,
                "weight": round(min(100.0, 2.0 + source_count * 5.0), 2),
            })
        else:
            cooccurrence_count = relation.cooccurrence_count + 1
            source_count = relation.source_count + (1 if is_new_source else 0)
            relation_updates.append({
                "id": relation.id,
                "cooccurrence_count": cooccurrence_count,
                "source_count": source_count,
                "first_seen_at": min(relation.first_seen_at, item.observed_at),
                "last_seen_at": max(relation.last_seen_at, item.observed_at),
                "weight": round(min(100.0, cooccurrence_count * 2.0 + source_count * 5.0), 2),
            })
        if is_new_source:
            new_sources.append({
                "keyword_a_id": a,
                "keyword_b_id": b,
                "source_id": item.source_id,
                "first_seen_at": item.observed_at,
            })
            existing_sources.add(pair)
        new_items.append({
            "keyword_a_id": a,
            "keyword_b_id": b,
            "relation_type": "CO_OCCURS",
            "normalized_item_id": item.id,
            "source_id": item.source_id,
            "observed_at": item.observed_at,
        })

    if new_relations:
        db.execute(insert(KeywordRelation), new_relations)
    if relation_updates:
        db.execute(update(KeywordRelation), relation_updates)
    if new_sources:
        db.execute(insert(KeywordRelationSource), new_sources)
    if new_items:
        db.execute(insert(KeywordRelationItem), new_items)
    db.flush()


def connected_keyword_ids(
    db: Session,
    seed_ids: set[int],
    *,
    since_days: int = 90,
    min_weight: float = 12.0,
    max_nodes: int = 2_000,
) -> set[int]:
    """Return the strong-relation closure around a small set of changed keywords."""
    if not seed_ids:
        return set()
    cutoff = utc_now() - timedelta(days=since_days)
    found = set(seed_ids)
    frontier = set(seed_ids)
    while frontier:
        rows = db.execute(
            select(KeywordRelation.keyword_a_id, KeywordRelation.keyword_b_id).where(
                KeywordRelation.last_seen_at >= cutoff,
                KeywordRelation.weight >= min_weight,
                or_(
                    KeywordRelation.keyword_a_id.in_(frontier),
                    KeywordRelation.keyword_b_id.in_(frontier),
                ),
            )
        ).all()
        next_frontier: set[int] = set()
        for a, b in rows:
            if a not in found:
                next_frontier.add(a)
            if b not in found:
                next_frontier.add(b)
        if len(found | next_frontier) > max_nodes:
            raise GraphScopeLimitExceeded(
                f"strong-relation closure exceeds max_nodes={max_nodes}; "
                "refusing to return a partial component"
            )
        found.update(next_frontier)
        frontier = next_frontier
    return found


def keyword_graph(db: Session, *, keyword_id: int | None = None, limit: int = 100, since_days: int = 90) -> dict:
    if since_days < 1 or since_days > 3650:
        raise ValueError("since_days must be between 1 and 3650")
    stmt = (
        select(KeywordRelation)
        .where(KeywordRelation.last_seen_at >= utc_now() - timedelta(days=since_days))
        .order_by(KeywordRelation.weight.desc(), KeywordRelation.last_seen_at.desc())
    )
    if keyword_id is not None:
        stmt = stmt.where(
            (KeywordRelation.keyword_a_id == keyword_id) | (KeywordRelation.keyword_b_id == keyword_id)
        )
    relations = db.scalars(stmt.limit(limit)).all()
    ids = {r.keyword_a_id for r in relations} | {r.keyword_b_id for r in relations}
    names = {
        row.id: row.display_name
        for row in db.scalars(select(Keyword).where(Keyword.id.in_(ids))).all()
    } if ids else {}
    return {
        "nodes": [{"id": key, "keyword": names.get(key, str(key))} for key in sorted(ids)],
        "edges": [
            {
                "source": r.keyword_a_id,
                "target": r.keyword_b_id,
                "type": r.relation_type,
                "cooccurrences": r.cooccurrence_count,
                "sources": r.source_count,
                "weight": r.weight,
                "last_seen_at": r.last_seen_at,
            }
            for r in relations
        ],
    }
