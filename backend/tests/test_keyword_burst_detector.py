from datetime import date

from app.db.models import Keyword, KeywordTrendDaily
from app.db.session import SessionLocal
from app.domain.keyword_burst import KeywordBurstPolicy
from app.services.keyword_burst import detect_anomalous_keyword_bursts, detect_keyword_bursts


WINDOW_END = date(2026, 8, 12)


def _seed_keyword(db, canonical: str, *, baseline: int, current: tuple[int, int, int]) -> int:
    keyword = Keyword(canonical=canonical, display_name=canonical.title(), status="ACTIVE")
    db.add(keyword)
    db.flush()
    for offset in range(6):
        db.add(KeywordTrendDaily(keyword_id=keyword.id, day=date(2026, 8, 3 + offset), observation_count=baseline, source_count=1))
    for offset, count in enumerate(current):
        db.add(KeywordTrendDaily(keyword_id=keyword.id, day=date(2026, 8, 9 + offset), observation_count=count, source_count=2))
    db.flush()
    return keyword.id


def test_database_detector_reads_daily_trends_and_returns_auditable_anomaly():
    policy = KeywordBurstPolicy(current_window_days=3, baseline_window_days=6, min_current_observations=6, min_absolute_delta=4, min_growth_rate=0.5, min_z_score=2.0)
    with SessionLocal() as db:
        keyword_id = _seed_keyword(db, "detector burst", baseline=1, current=(4, 5, 6))
        db.commit()
        results = detect_keyword_bursts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=policy)
        anomalies = detect_anomalous_keyword_bursts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=policy)

    assert len(results) == 1
    assert results[0].anomalous is True
    assert results[0].current_observations == 15
    assert results[0].input_signature == anomalies[0].input_signature
    assert results[0].current_sources == 2


def test_database_detector_is_empty_safe_and_repeatable_without_side_effects():
    policy = KeywordBurstPolicy(current_window_days=3, baseline_window_days=6, min_current_observations=2, min_absolute_delta=1, min_growth_rate=0.5, min_z_score=2.0)
    with SessionLocal() as db:
        keyword_id = _seed_keyword(db, "detector stable", baseline=2, current=(2, 2, 2))
        db.commit()
        first = detect_keyword_bursts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=policy)
        second = detect_keyword_bursts(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=policy)
        empty = detect_keyword_bursts(db, keyword_ids=set(), window_end=WINDOW_END, policy=policy)

    assert len(first) == len(second) == 1
    assert first[0].model_dump(exclude={"evaluated_at"}) == second[0].model_dump(exclude={"evaluated_at"})
    assert first[0].anomalous is False
    assert empty == []


def test_database_detector_respects_limit_and_missing_current_days():
    policy = KeywordBurstPolicy(current_window_days=3, baseline_window_days=6, min_current_observations=2, min_current_sources=1)
    with SessionLocal() as db:
        first_id = _seed_keyword(db, "first detector", baseline=0, current=(0, 3, 0))
        _seed_keyword(db, "second detector", baseline=0, current=(3, 0, 0))
        db.commit()
        limited = detect_keyword_bursts(db, window_end=WINDOW_END, policy=policy, limit=1)
        selected = detect_keyword_bursts(db, keyword_ids={first_id}, window_end=WINDOW_END, policy=policy)

    assert len(limited) == 1
    assert len(selected) == 1
    assert selected[0].current_observations == 3
    assert selected[0].anomalous is True
