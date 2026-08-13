from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import Keyword, KeywordMention, NormalizedItem, RawObservation
from app.db.session import SessionLocal
from app.domain.hiring_surge import HiringSurgePolicy
from app.main import app
from app.services.hiring_surge import detect_hiring_surges


client = TestClient(app)
WINDOW_END = date(2026, 8, 12)


def _seed_job(db, keyword: Keyword, *, day: date, title: str, company: str, source: str, index: int) -> None:
    observed_at = datetime.combine(day, datetime.min.time())
    raw = RawObservation(
        source_id=source,
        external_id=f"synthetic-job-{index}",
        query=keyword.display_name,
        item_type="JOB",
        title=title,
        text=f"MOCK company: {company} location: Remote hiring",
        source_url=f"https://synthetic.invalid/jobs/{index}",
        observed_at=observed_at,
        acquisition_method="MANUAL_IMPORT",
        evidence_quality="E",
        acquisition_risk="R2",
        content_hash=f"{index:064x}",
        raw_payload={"data_class": "SYNTHETIC", "company": company, "location": "Remote"},
    )
    db.add(raw)
    db.flush()
    item = NormalizedItem(
        raw_observation_id=raw.id,
        canonical_key=f"synthetic-job-item-{index}",
        source_id=source,
        query=keyword.display_name,
        item_type="JOB",
        title=title,
        text=raw.text,
        source_url=raw.source_url,
        observed_at=observed_at,
    )
    db.add(item)
    db.flush()
    db.add(KeywordMention(keyword_id=keyword.id, normalized_item_id=item.id, source_id=source, observed_at=observed_at))


def _seed_surge() -> int:
    with SessionLocal() as db:
        keyword = Keyword(canonical="synthetic-hiring", display_name="Synthetic Hiring", status="ACTIVE")
        db.add(keyword)
        db.flush()
        index = 1
        for offset in range(6):
            _seed_job(db, keyword, day=date(2026, 8, 3 + offset), title="Baseline Engineer", company="Baseline Co", source="synthetic-baseline", index=index)
            index += 1
        for day_offset, company in ((9, "Acme A"), (10, "Acme B"), (11, "Acme C")):
            for role_offset in range(4):
                _seed_job(db, keyword, day=date(2026, 8, day_offset), title=f"Growth Engineer {role_offset}", company=company, source="synthetic-jobs-a", index=index)
                index += 1
            if day_offset == 9:
                _seed_job(db, keyword, day=date(2026, 8, day_offset), title="Growth Engineer 0", company=company, source="synthetic-jobs-b", index=index)
                index += 1
        db.commit()
        return keyword.id


def _policy() -> HiringSurgePolicy:
    return HiringSurgePolicy(current_window_days=3, baseline_window_days=6, min_current_jobs=5, min_absolute_delta=3, min_growth_rate=0.5, min_z_score=2.0, min_current_evidence=1)


def test_detector_deduplicates_jobs_and_reports_company_source_diversity():
    keyword_id = _seed_surge()
    with SessionLocal() as db:
        before = db.scalar(select(func.count(KeywordMention.id)))
        first = detect_hiring_surges(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=_policy())
        second = detect_hiring_surges(db, keyword_ids={keyword_id}, window_end=WINDOW_END, policy=_policy())
        after = db.scalar(select(func.count(KeywordMention.id)))

    assert len(first) == len(second) == 1
    detection = first[0]
    assert detection.evaluation.surge is True
    assert detection.evaluation.current_jobs == 12
    assert detection.evaluation.baseline_jobs == 6
    assert detection.metrics.current_unique_jobs == 12
    assert detection.metrics.baseline_unique_jobs == 1
    assert detection.metrics.current_duplicate_observations == 1
    assert detection.metrics.current_company_count == 3
    assert detection.metrics.current_source_count == 2
    assert detection.metrics.current_duplicate_rate > 0
    assert detection.detection_signature == second[0].detection_signature
    assert len(detection.evidence_ids) <= 20
    assert before == after


def test_detector_empty_and_anomalous_filter_are_read_only_and_rbac_protected():
    with SessionLocal() as db:
        assert detect_hiring_surges(db, keyword_ids=set(), window_end=WINDOW_END, policy=_policy()) == []
        assert detect_hiring_surges(db, window_end=WINDOW_END, policy=_policy(), anomalous_only=True) == []

    from dataclasses import replace
    import app.core.security as security
    from app.core.config import settings

    original = security.settings
    security.settings = replace(settings, auth_mode="rbac")
    try:
        response = client.get("/api/v1/hiring/surges")
    finally:
        security.settings = original
    assert response.status_code == 401


def test_detector_api_returns_versioned_diversity_output():
    keyword_id = _seed_surge()
    response = client.get("/api/v1/hiring/surges", params={"keyword_id": keyword_id, "window_end": WINDOW_END.isoformat(), "anomalous_only": True})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["evaluation"]["algorithm_version"] == "hiring-surge-v1"
    assert payload[0]["metrics"]["current_duplicate_observations"] == 1
