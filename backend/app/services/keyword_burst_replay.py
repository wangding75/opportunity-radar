"""Bounded, read-only historical replay for keyword burst evaluations."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Keyword, KeywordTrendDaily
from app.domain.keyword_burst import KeywordBurstInput, KeywordBurstPolicy, evaluate_keyword_burst

MAX_REPLAY_WINDOWS = 52


def replay_keyword_bursts(
    db: Session,
    *,
    keyword_id: int,
    start_window_end: date,
    end_window_end: date,
    policy: KeywordBurstPolicy | None = None,
    max_windows: int = MAX_REPLAY_WINDOWS,
) -> dict:
    """Replay complete historical windows without persistence or alert side effects."""

    policy = policy or KeywordBurstPolicy()
    if end_window_end < start_window_end:
        raise ValueError("end_window_end must not precede start_window_end")
    requested_windows = ((end_window_end - start_window_end).days // 7) + 1
    if requested_windows > min(MAX_REPLAY_WINDOWS, max_windows):
        raise ValueError(f"replay window exceeds {min(MAX_REPLAY_WINDOWS, max_windows)} weekly windows")
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise KeyError(f"unknown keyword id: {keyword_id}")
    earliest = start_window_end - timedelta(days=policy.current_window_days + policy.baseline_window_days)
    latest = end_window_end
    rows = db.scalars(
        select(KeywordTrendDaily)
        .where(KeywordTrendDaily.keyword_id == keyword_id, KeywordTrendDaily.day >= earliest, KeywordTrendDaily.day < latest)
        .order_by(KeywordTrendDaily.day)
    ).all()
    observations = {row.day: max(0, int(row.observation_count or 0)) for row in rows}
    sources = {row.day: max(0, int(row.source_count or 0)) for row in rows}
    results = []
    window_end = start_window_end
    while window_end <= end_window_end:
        evaluation = evaluate_keyword_burst(
            KeywordBurstInput(keyword_id=keyword.id, keyword=keyword.display_name, window_end=window_end, daily_observations=observations, daily_sources=sources),
            policy=policy,
            evaluated_at=datetime.combine(window_end, time.min),
        )
        results.append(evaluation.model_dump(mode="json"))
        window_end += timedelta(days=7)
    return {
        "keyword_id": keyword.id,
        "keyword": keyword.display_name,
        "contract_version": results[0]["contract_version"] if results else "1",
        "algorithm_version": results[0]["algorithm_version"] if results else "keyword-burst-v1",
        "policy": policy.model_dump(mode="json"),
        "start_window_end": start_window_end,
        "end_window_end": end_window_end,
        "windows": len(results),
        "anomalous_windows": sum(1 for result in results if result["anomalous"]),
        "input_signatures": [result["input_signature"] for result in results],
        "results": results,
    }
