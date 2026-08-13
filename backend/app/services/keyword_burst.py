"""Database-backed keyword burst detection."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordTrendDaily
from app.domain.keyword_burst import (
    KeywordBurstEvaluation,
    KeywordBurstInput,
    KeywordBurstPolicy,
    evaluate_keyword_burst,
)


MAX_BURST_KEYWORDS = 500


def _candidate_keywords(db: Session, *, keyword_ids: set[int] | None, start: date, end: date, limit: int) -> list[tuple[int, str]]:
    if keyword_ids is not None and not keyword_ids:
        return []
    stmt = (
        select(Keyword.id, Keyword.display_name)
        .join(KeywordTrendDaily, KeywordTrendDaily.keyword_id == Keyword.id)
        .where(KeywordTrendDaily.day >= start, KeywordTrendDaily.day < end)
        .distinct()
        .order_by(Keyword.id)
        .limit(limit)
    )
    if keyword_ids is not None:
        stmt = stmt.where(Keyword.id.in_(keyword_ids))
    return [(int(keyword_id), str(keyword)) for keyword_id, keyword in db.execute(stmt).all()]


def detect_keyword_bursts(
    db: Session,
    *,
    keyword_ids: set[int] | None = None,
    window_end: date | None = None,
    policy: KeywordBurstPolicy | None = None,
    limit: int = 100,
) -> list[KeywordBurstEvaluation]:
    """Evaluate bounded daily trend windows for selected or active keywords.

    The service is read-only and deterministic for a fixed database snapshot,
    window end, and policy. It deliberately returns non-anomalous evaluations as
    well so callers can audit why a candidate was rejected without inventing an
    alert event.
    """

    policy = policy or KeywordBurstPolicy()
    bounded_limit = max(1, min(MAX_BURST_KEYWORDS, int(limit)))
    window_end = window_end or utc_now().date()
    current_start = window_end - timedelta(days=policy.current_window_days)
    baseline_start = current_start - timedelta(days=policy.baseline_window_days)
    rows = _candidate_keywords(
        db,
        keyword_ids=keyword_ids,
        start=baseline_start,
        end=window_end,
        limit=bounded_limit,
    )
    if not rows:
        return []
    ids = {keyword_id for keyword_id, _keyword in rows}
    trend_rows = db.scalars(
        select(KeywordTrendDaily)
        .where(
            KeywordTrendDaily.keyword_id.in_(ids),
            KeywordTrendDaily.day >= baseline_start,
            KeywordTrendDaily.day < window_end,
        )
        .order_by(KeywordTrendDaily.keyword_id, KeywordTrendDaily.day)
    ).all()
    observations: dict[int, dict[date, int]] = defaultdict(dict)
    sources: dict[int, dict[date, int]] = defaultdict(dict)
    for row in trend_rows:
        observations[row.keyword_id][row.day] = max(0, int(row.observation_count or 0))
        sources[row.keyword_id][row.day] = max(0, int(row.source_count or 0))
    evaluated_at = utc_now()
    return [
        evaluate_keyword_burst(
            KeywordBurstInput(
                keyword_id=keyword_id,
                keyword=keyword,
                window_end=window_end,
                daily_observations=observations.get(keyword_id, {}),
                daily_sources=sources.get(keyword_id, {}),
            ),
            policy=policy,
            evaluated_at=evaluated_at,
        )
        for keyword_id, keyword in rows
    ]


def detect_anomalous_keyword_bursts(
    db: Session,
    *,
    keyword_ids: set[int] | None = None,
    window_end: date | None = None,
    policy: KeywordBurstPolicy | None = None,
    limit: int = 100,
) -> list[KeywordBurstEvaluation]:
    """Return only anomalous results while preserving the same detector contract."""

    return [
        evaluation
        for evaluation in detect_keyword_bursts(
            db,
            keyword_ids=keyword_ids,
            window_end=window_end,
            policy=policy,
            limit=limit,
        )
        if evaluation.anomalous
    ]
