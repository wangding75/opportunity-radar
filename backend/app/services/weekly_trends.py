"""Aggregation and deterministic ranking for weekly emerging trends."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordMention, KeywordTrendDaily, NormalizedItem, RawObservation
from app.domain.citations import provenance_from_payload
from app.domain.weekly_trends import (
    WEEKLY_TREND_ALGORITHM_VERSION,
    WEEKLY_TREND_CONTRACT_VERSION,
    WEEKLY_TREND_MAX_CANDIDATES,
    TrendComparison,
    TrendEvidenceProvenance,
    WeeklyTrendItem,
    WeeklyTrendPolicy,
    WeeklyTrendReport,
    WeeklyTrendStatus,
    build_weekly_trend_input_signature,
    completed_week_window,
)


def _momentum_score(*, current: int, growth_rate: float | None, current_sources: int) -> float:
    growth_component = 60.0 if growth_rate is None else min(60.0, max(0.0, growth_rate) * 60.0)
    volume_component = min(30.0, current * 3.0)
    source_component = min(10.0, current_sources * 2.0)
    return round(min(100.0, growth_component + volume_component + source_component), 2)


def _trend_signature(keyword_id: int, *, week_start: date, week_end: date, current: int, baseline: int, current_sources: int, baseline_sources: int) -> str:
    payload = {
        "keyword_id": keyword_id,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "current": current,
        "baseline": baseline,
        "current_sources": current_sources,
        "baseline_sources": baseline_sources,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _source_sets(db: Session, keyword_ids: set[int], *, current_start: date, current_end: date, baseline_start: date) -> dict[int, tuple[int, int]]:
    if not keyword_ids:
        return {}
    current_start_at = datetime.combine(current_start, datetime.min.time())
    current_end_at = datetime.combine(current_end, datetime.min.time())
    baseline_start_at = datetime.combine(baseline_start, datetime.min.time())
    current_rows = db.execute(
        select(KeywordMention.keyword_id, KeywordMention.source_id)
        .where(
            KeywordMention.keyword_id.in_(keyword_ids),
            KeywordMention.observed_at >= current_start_at,
            KeywordMention.observed_at < current_end_at,
        )
        .distinct()
    ).all()
    baseline_rows = db.execute(
        select(KeywordMention.keyword_id, KeywordMention.source_id)
        .where(
            KeywordMention.keyword_id.in_(keyword_ids),
            KeywordMention.observed_at >= baseline_start_at,
            KeywordMention.observed_at < current_start_at,
        )
        .distinct()
    ).all()
    daily_rows = db.execute(
        select(KeywordTrendDaily.keyword_id, KeywordTrendDaily.day, KeywordTrendDaily.source_count)
        .where(
            KeywordTrendDaily.keyword_id.in_(keyword_ids),
            KeywordTrendDaily.day >= baseline_start,
            KeywordTrendDaily.day < current_end,
        )
    ).all()
    current = defaultdict(set)
    baseline = defaultdict(set)
    daily_current = defaultdict(int)
    daily_baseline = defaultdict(int)
    for keyword_id, source_id in current_rows:
        current[keyword_id].add(source_id)
    for keyword_id, source_id in baseline_rows:
        baseline[keyword_id].add(source_id)
    for keyword_id, day, source_count in daily_rows:
        if day >= current_start:
            daily_current[keyword_id] += max(0, int(source_count or 0))
        else:
            daily_baseline[keyword_id] += max(0, int(source_count or 0))
    return {
        keyword_id: (
            len(current[keyword_id]) or daily_current[keyword_id],
            len(baseline[keyword_id]) or daily_baseline[keyword_id],
        )
        for keyword_id in keyword_ids
    }


def _provenances(db: Session, keyword_ids: set[int], *, window_start: date, window_end: date) -> dict[int, TrendEvidenceProvenance]:
    if not keyword_ids:
        return {}
    rows = db.execute(
        select(KeywordMention.keyword_id, RawObservation.raw_payload)
        .join(NormalizedItem, NormalizedItem.id == KeywordMention.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(
            KeywordMention.keyword_id.in_(keyword_ids),
            KeywordMention.observed_at >= datetime.combine(window_start, datetime.min.time()),
            KeywordMention.observed_at < datetime.combine(window_end, datetime.min.time()),
        )
    ).all()
    by_keyword: dict[int, set[str]] = defaultdict(set)
    for keyword_id, payload in rows:
        by_keyword[keyword_id].add(provenance_from_payload(payload).value)
    result: dict[int, TrendEvidenceProvenance] = {}
    for keyword_id in keyword_ids:
        values = by_keyword.get(keyword_id) or {TrendEvidenceProvenance.OBSERVED.value}
        result[keyword_id] = TrendEvidenceProvenance(next(iter(values)) if len(values) == 1 else TrendEvidenceProvenance.MIXED.value)
    return result


def _as_utc_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)


def aggregate_weekly_trends(
    db: Session,
    *,
    anchor_date: date | None = None,
    now: datetime | None = None,
    policy: WeeklyTrendPolicy | None = None,
) -> WeeklyTrendReport:
    """Aggregate the previous complete week against its preceding baseline."""

    policy = policy or WeeklyTrendPolicy()
    now = now or utc_now()
    anchor = anchor_date or now.date()
    week_start, week_end, baseline_start, baseline_end = completed_week_window(anchor)
    current_count = func.coalesce(
        func.sum(case((KeywordTrendDaily.day >= week_start, KeywordTrendDaily.observation_count), else_=0)), 0
    ).label("current_observations")
    baseline_count = func.coalesce(
        func.sum(case((KeywordTrendDaily.day < week_start, KeywordTrendDaily.observation_count), else_=0)), 0
    ).label("baseline_observations")
    last_seen = func.max(
        case((KeywordTrendDaily.day >= week_start, KeywordTrendDaily.day), else_=None)
    ).label("last_seen_at")
    aggregate = (
        select(KeywordTrendDaily.keyword_id, Keyword.display_name.label("keyword"), current_count, baseline_count, last_seen)
        .join(Keyword, Keyword.id == KeywordTrendDaily.keyword_id)
        .where(KeywordTrendDaily.day >= baseline_start, KeywordTrendDaily.day < week_end)
        .group_by(KeywordTrendDaily.keyword_id, Keyword.display_name)
        .having(current_count >= policy.min_current_observations)
        .subquery()
    )
    total_candidates = int(db.scalar(select(func.count()).select_from(aggregate)) or 0)
    rows = db.execute(
        select(aggregate)
        .order_by(aggregate.c.current_observations.desc(), aggregate.c.keyword.asc(), aggregate.c.keyword_id.asc())
        .limit(WEEKLY_TREND_MAX_CANDIDATES)
    ).all()
    keyword_ids = {row.keyword_id for row in rows}
    sources = _source_sets(db, keyword_ids, current_start=week_start, current_end=week_end, baseline_start=baseline_start)
    provenances = _provenances(db, keyword_ids, window_start=baseline_start, window_end=week_end)
    candidates: list[WeeklyTrendItem] = []
    candidate_inputs: list[dict[str, Any]] = []
    for row in rows:
        current = int(row.current_observations or 0)
        baseline = int(row.baseline_observations or 0)
        delta = current - baseline
        growth = None if baseline == 0 else round(delta / baseline, 4)
        current_sources, baseline_sources = sources.get(row.keyword_id, (0, 0))
        comparison = (
            TrendComparison.NEW_SIGNAL if baseline == 0 else
            TrendComparison.GROWING if delta > 0 else
            TrendComparison.DECLINING if delta < 0 else
            TrendComparison.STABLE
        )
        signature = _trend_signature(
            row.keyword_id,
            week_start=week_start,
            week_end=week_end,
            current=current,
            baseline=baseline,
            current_sources=current_sources,
            baseline_sources=baseline_sources,
        )
        candidate_inputs.append({
            "keyword_id": row.keyword_id,
            "keyword": row.keyword,
            "current_observations": current,
            "baseline_observations": baseline,
            "current_sources": current_sources,
            "baseline_sources": baseline_sources,
            "absolute_delta": delta,
            "growth_rate": growth,
            "momentum_score": _momentum_score(current=current, growth_rate=growth, current_sources=current_sources),
            "trend_signature": signature,
            "last_seen_at": _as_utc_datetime(row.last_seen_at),
            "evidence_provenance": provenances.get(row.keyword_id, TrendEvidenceProvenance.OBSERVED),
        })
        qualifies = baseline == 0 and policy.include_new_signals
        if baseline > 0:
            qualifies = delta >= policy.min_absolute_delta and (growth or 0.0) >= policy.min_growth_rate
        if not qualifies:
            continue
        candidates.append(WeeklyTrendItem(
            rank=1,
            keyword_id=row.keyword_id,
            keyword=row.keyword,
            comparison=comparison,
            current_observations=current,
            baseline_observations=baseline,
            current_sources=current_sources,
            baseline_sources=baseline_sources,
            absolute_delta=delta,
            growth_rate=growth,
            momentum_score=_momentum_score(current=current, growth_rate=growth, current_sources=current_sources),
            trend_signature=signature,
            last_seen_at=_as_utc_datetime(row.last_seen_at),
            evidence_provenance=provenances.get(row.keyword_id, TrendEvidenceProvenance.OBSERVED),
            selection_reasons=[
                "new signal with zero baseline" if baseline == 0 else f"growth rate >= {policy.min_growth_rate:g}",
                f"current observations >= {policy.min_current_observations}",
                f"absolute delta = {delta}",
            ],
        ))
    candidates.sort(key=lambda item: (-item.momentum_score, -item.absolute_delta, -item.current_observations, item.keyword.casefold(), item.keyword_id))
    items = [item.model_copy(update={"rank": rank}) for rank, item in enumerate(candidates[: policy.max_items], start=1)]
    warnings = [f"candidate set truncated to {WEEKLY_TREND_MAX_CANDIDATES}"] if total_candidates > WEEKLY_TREND_MAX_CANDIDATES else []
    signature = build_weekly_trend_input_signature(
        week_start=week_start,
        week_end=week_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        candidates=candidate_inputs,
        policy=policy,
    )
    return WeeklyTrendReport(
        contract_version=WEEKLY_TREND_CONTRACT_VERSION,
        algorithm_version=WEEKLY_TREND_ALGORITHM_VERSION,
        week_start=week_start,
        week_end=week_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        generated_at=now,
        status=WeeklyTrendStatus.READY if items else WeeklyTrendStatus.EMPTY,
        policy=policy,
        total_candidates=min(total_candidates, WEEKLY_TREND_MAX_CANDIDATES),
        selected_count=len(items),
        input_signature=signature,
        items=items,
        warnings=warnings,
    )
