import hashlib
from datetime import date, datetime

from app.db.models import Keyword, KeywordMention, KeywordTrendDaily, NormalizedItem, RawObservation
from app.db.session import SessionLocal
from app.domain.weekly_trends import TrendComparison, WeeklyTrendPolicy, WeeklyTrendStatus
from app.services.weekly_trends import aggregate_weekly_trends


def _keyword(db, name: str) -> Keyword:
    row = Keyword(canonical=name, display_name=name, status="ACTIVE", first_seen_at=datetime(2026, 7, 1), last_seen_at=datetime(2026, 8, 10), score=80)
    db.add(row)
    db.flush()
    return row


def _point(db, keyword_id: int, day: date, count: int, sources: int = 1):
    db.add(KeywordTrendDaily(keyword_id=keyword_id, day=day, observation_count=count, source_count=sources))


def test_aggregate_weekly_trends_uses_complete_week_baseline_and_deterministic_rank():
    with SessionLocal() as db:
        fast = _keyword(db, "fast trend")
        steady = _keyword(db, "steady trend")
        _point(db, fast.id, date(2026, 7, 27), 1)
        _point(db, fast.id, date(2026, 8, 3), 4)
        _point(db, fast.id, date(2026, 8, 4), 4)
        _point(db, steady.id, date(2026, 7, 27), 2)
        _point(db, steady.id, date(2026, 8, 3), 3)
        _point(db, steady.id, date(2026, 8, 4), 3)
        db.commit()
        report = aggregate_weekly_trends(db, anchor_date=date(2026, 8, 12), policy=WeeklyTrendPolicy(min_current_observations=3))
    assert report.status == WeeklyTrendStatus.READY
    assert (report.week_start, report.week_end, report.baseline_start, report.baseline_end) == (date(2026, 8, 3), date(2026, 8, 10), date(2026, 7, 27), date(2026, 8, 3))
    assert [item.keyword for item in report.items] == ["fast trend", "steady trend"]
    assert report.items[0].comparison == TrendComparison.GROWING
    assert report.items[0].absolute_delta == 7
    assert report.items[0].growth_rate == 7.0


def test_aggregate_weekly_trends_includes_new_signal_without_infinite_growth():
    with SessionLocal() as db:
        keyword = _keyword(db, "new signal")
        _point(db, keyword.id, date(2026, 8, 3), 3)
        db.commit()
        report = aggregate_weekly_trends(db, anchor_date=date(2026, 8, 12))
    assert report.status == WeeklyTrendStatus.READY
    assert report.items[0].comparison == TrendComparison.NEW_SIGNAL
    assert report.items[0].growth_rate is None


def test_aggregate_weekly_trends_returns_empty_for_below_threshold_or_no_rows():
    with SessionLocal() as db:
        keyword = _keyword(db, "small signal")
        _point(db, keyword.id, date(2026, 8, 3), 2)
        db.commit()
        report = aggregate_weekly_trends(db, anchor_date=date(2026, 8, 12))
    assert report.status == WeeklyTrendStatus.EMPTY
    assert report.items == []


def test_aggregate_weekly_trends_uses_distinct_sources_and_explicit_provenance():
    with SessionLocal() as db:
        keyword = _keyword(db, "source-backed trend")
        for index, (source_id, marker) in enumerate((("source-a", "MOCK"), ("source-b", "SYNTHETIC"))):
            observed_at = datetime(2026, 8, 3, 8 + index)
            content_hash = hashlib.sha256(f"source-backed-{index}".encode()).hexdigest()
            raw = RawObservation(
                source_id=source_id,
                external_id=str(index),
                query="source-backed trend",
                item_type="TREND",
                title="source-backed trend",
                text="marked evidence",
                observed_at=observed_at,
                acquisition_method="TEST",
                evidence_quality="B",
                acquisition_risk="R1",
                content_hash=content_hash,
                raw_payload={"data_class": marker},
            )
            db.add(raw)
            db.flush()
            item = NormalizedItem(
                raw_observation_id=raw.id,
                canonical_key=f"source-backed-{index}",
                source_id=source_id,
                query=raw.query,
                item_type=raw.item_type,
                title=raw.title,
                text=raw.text,
                observed_at=observed_at,
            )
            db.add(item)
            db.flush()
            db.add(KeywordMention(keyword_id=keyword.id, normalized_item_id=item.id, source_id=source_id, observed_at=observed_at))
        _point(db, keyword.id, date(2026, 8, 3), 2, sources=2)
        _point(db, keyword.id, date(2026, 8, 4), 1, sources=1)
        db.commit()
        report = aggregate_weekly_trends(db, anchor_date=date(2026, 8, 12))
    item = report.items[0]
    assert item.current_sources == 2
    assert item.baseline_sources == 0
    assert item.evidence_provenance.value == "MIXED"
