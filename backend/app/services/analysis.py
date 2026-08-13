from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import KeywordMention, NormalizedItem, RawObservation
from app.services.alerts import enqueue_alert_evaluations
from app.services.graph import GraphScopeLimitExceeded, refresh_relations_for_item
from app.services.keywords import discover_for_item, refresh_keyword_metrics
from app.services.locks import acquire_derived_analysis_lock
from app.services.normalizer import normalize_one
from app.services.opportunities import refresh_opportunities
from app.services.trends import refresh_trends
from app.services.tool_products import normalize_tool_product_entities
from app.services.tool_product_occurrences import materialize_tool_product_occurrences


def process_new_raw(db: Session, raw: RawObservation) -> NormalizedItem:
    # Keyword/graph/opportunity materialization shares mutable derived rows. A
    # PostgreSQL transaction-scoped advisory lock prevents two collection
    # workers from racing on keyword creation/relation updates and leaving the
    # derived state stale or violating unique constraints.
    acquire_derived_analysis_lock(db)
    item = normalize_one(db, raw)
    discover_for_item(db, item)
    refresh_relations_for_item(db, item)
    return item


def refresh_derived_analysis(db: Session, *, normalized_item_ids: set[int] | None = None, progress_callback=None) -> dict:
    """Refresh materialized analysis globally or incrementally.

    New ingestion passes normalized_item_ids so only affected keywords, dates and
    opportunity components are recalculated. Calling without IDs is the explicit
    maintenance/full-reconciliation path.
    """
    acquire_derived_analysis_lock(db)
    if normalized_item_ids is None:
        refresh_keyword_metrics(db)
        if progress_callback is not None:
            progress_callback()
        refresh_trends(db, days=90)
        if progress_callback is not None:
            progress_callback()
        opportunity_ids = refresh_opportunities(db, progress_callback=progress_callback)
        enqueue_alert_evaluations(db, opportunity_ids, reason="FULL_RECONCILIATION")
        tool_products = normalize_tool_product_entities(db, limit=500)
        tool_products["occurrences"] = materialize_tool_product_occurrences(db, limit=500)
        if progress_callback is not None:
            progress_callback()
        return {"mode": "full", "keywords": None, "opportunities": len(opportunity_ids), "tool_products": tool_products}

    if not normalized_item_ids:
        return {"mode": "incremental", "keywords": 0, "opportunities": 0, "tool_products": {"evaluated": 0}}
    tool_products = normalize_tool_product_entities(db, normalized_item_ids=normalized_item_ids, limit=500)
    tool_products["occurrences"] = materialize_tool_product_occurrences(db, limit=500)
    mentions = db.execute(
        select(KeywordMention.keyword_id, KeywordMention.observed_at).where(
            KeywordMention.normalized_item_id.in_(normalized_item_ids)
        )
    ).all()
    keyword_ids = {row.keyword_id for row in mentions}
    observed_days: set[date] = {row.observed_at.date() for row in mentions}
    if not keyword_ids:
        return {"mode": "incremental", "keywords": 0, "opportunities": 0, "tool_products": tool_products}
    refresh_keyword_metrics(db, keyword_ids=keyword_ids)
    refresh_trends(db, days=90, keyword_ids=keyword_ids, observed_days=observed_days)
    try:
        opportunity_ids = refresh_opportunities(db, affected_keyword_ids=keyword_ids, progress_callback=progress_callback)
        mode = "incremental"
    except GraphScopeLimitExceeded:
        # Never materialize a partial opportunity component. Extremely large
        # connected graphs are rare, but correctness is more important than the
        # incremental optimization: rebuild all derived state under the same
        # transaction-scoped advisory lock and let maintenance/monitoring expose
        # the expensive fallback rather than silently corrupting identity.
        refresh_keyword_metrics(db)
        if progress_callback is not None:
            progress_callback()
        refresh_trends(db, days=90)
        if progress_callback is not None:
            progress_callback()
        opportunity_ids = refresh_opportunities(db, progress_callback=progress_callback)
        mode = "fallback_full"
    enqueue_alert_evaluations(db, opportunity_ids)
    return {"mode": mode, "keywords": len(keyword_ids), "opportunities": len(opportunity_ids), "tool_products": tool_products}
