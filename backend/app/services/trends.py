from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordMention, KeywordTrendDaily


def _rebuild_days(db: Session, keyword_ids: set[int], days: set[date]) -> None:
    if not keyword_ids or not days:
        return
    min_day = min(days)
    max_day = max(days)
    start_at = datetime.combine(min_day, time.min)
    end_at = datetime.combine(max_day + timedelta(days=1), time.min)
    db.execute(
        delete(KeywordTrendDaily).where(
            KeywordTrendDaily.keyword_id.in_(keyword_ids),
            KeywordTrendDaily.day.in_(days),
        )
    )
    mentions = db.execute(
        select(KeywordMention.keyword_id, KeywordMention.source_id, KeywordMention.observed_at).where(
            KeywordMention.keyword_id.in_(keyword_ids),
            KeywordMention.observed_at >= start_at,
            KeywordMention.observed_at < end_at,
        )
    ).all()
    buckets: dict[tuple[int, date], dict[str, object]] = defaultdict(lambda: {"count": 0, "sources": set()})
    for keyword_id, source_id, observed_at in mentions:
        day = observed_at.date()
        if day not in days:
            continue
        key = (keyword_id, day)
        buckets[key]["count"] = int(buckets[key]["count"]) + 1
        sources = buckets[key]["sources"]
        assert isinstance(sources, set)
        sources.add(source_id)
    for (keyword_id, day), values in buckets.items():
        sources = values["sources"]
        assert isinstance(sources, set)
        db.add(
            KeywordTrendDaily(
                keyword_id=keyword_id,
                day=day,
                observation_count=int(values["count"]),
                source_count=len(sources),
            )
        )
    db.flush()


def refresh_trends(
    db: Session,
    *,
    days: int = 90,
    keyword_ids: set[int] | None = None,
    observed_days: set[date] | None = None,
) -> None:
    """Refresh daily keyword trends.

    Incremental callers pass changed keyword IDs and observed dates. A maintenance
    caller can omit them to rebuild the bounded 90-day materialization.
    """
    if days < 1 or days > 366:
        raise ValueError("days must be between 1 and 366")
    today = utc_now().date()
    start_day = today - timedelta(days=days - 1)
    if keyword_ids is not None:
        target_days = {d for d in (observed_days or {today}) if start_day <= d <= today}
        _rebuild_days(db, set(keyword_ids), target_days)
        return

    start_at = datetime.combine(start_day, time.min)
    db.execute(delete(KeywordTrendDaily))
    mentions = db.execute(
        select(KeywordMention.keyword_id, KeywordMention.source_id, KeywordMention.observed_at).where(
            KeywordMention.observed_at >= start_at
        )
    ).all()
    buckets: dict[tuple[int, date], dict[str, object]] = defaultdict(lambda: {"count": 0, "sources": set()})
    for keyword_id, source_id, observed_at in mentions:
        key = (keyword_id, observed_at.date())
        buckets[key]["count"] = int(buckets[key]["count"]) + 1
        sources = buckets[key]["sources"]
        assert isinstance(sources, set)
        sources.add(source_id)
    for (keyword_id, day), values in buckets.items():
        sources = values["sources"]
        assert isinstance(sources, set)
        db.add(
            KeywordTrendDaily(
                keyword_id=keyword_id,
                day=day,
                observation_count=int(values["count"]),
                source_count=len(sources),
            )
        )
    db.flush()


def _window_count(points: list[KeywordTrendDaily], *, end: date, days: int, offset_days: int = 0) -> int:
    upper = end - timedelta(days=offset_days)
    lower = upper - timedelta(days=days - 1)
    return sum(p.observation_count for p in points if lower <= p.day <= upper)


def keyword_trend_summary(db: Session, keyword_id: int) -> dict:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise KeyError(f"unknown keyword id: {keyword_id}")
    points = db.scalars(
        select(KeywordTrendDaily)
        .where(KeywordTrendDaily.keyword_id == keyword_id)
        .order_by(KeywordTrendDaily.day)
    ).all()
    today = utc_now().date()

    def growth(days: int) -> float | None:
        current = _window_count(points, end=today, days=days)
        previous = _window_count(points, end=today, days=days, offset_days=days)
        if previous == 0:
            return None if current == 0 else 1.0
        return round((current - previous) / previous, 4)

    return {
        "keyword": keyword.display_name,
        "canonical": keyword.canonical,
        "windows": {
            "7d": _window_count(points, end=today, days=7),
            "30d": _window_count(points, end=today, days=30),
            "90d": _window_count(points, end=today, days=90),
        },
        "growth": {"7d": growth(7), "30d": growth(30)},
        "points": [
            {"day": p.day.isoformat(), "observations": p.observation_count, "sources": p.source_count}
            for p in points
        ],
    }
