"""Read-only hiring surge detection with job/company de-duplication."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordMention, NormalizedItem, RawObservation
from app.domain.citations import evidence_id_for_content_hash
from app.domain.hiring_surge import (
    HIRING_SURGE_ALGORITHM_VERSION,
    HIRING_SURGE_CONTRACT_VERSION,
    HiringDiversityMetrics,
    HiringSurgeDetection,
    HiringSurgeInput,
    HiringSurgePolicy,
    evaluate_hiring_surge,
    hiring_windows,
)

HIRING_SURGE_MAX_KEYWORDS = 500
HIRING_SURGE_MAX_ROWS = 5_000
_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[^\w]+", re.UNICODE)
_COMPANY_RE = re.compile(r"(?:company|employer|organization|公司|雇主|招聘方)\s*[:：|]\s*([^,，;；|\n]+)", re.IGNORECASE)
_LOCATION_RE = re.compile(r"(?:location|city|region|地点|城市|地区)\s*[:：|]\s*([^,，;；|\n]+)", re.IGNORECASE)


@dataclass(frozen=True)
class _JobRecord:
    day: date
    identity: str
    company: str | None
    source: str
    evidence_id: str
    observed_at: datetime


def _stable_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return _SPACE_RE.sub(" ", normalized)


def _key_text(value: object) -> str:
    return " ".join(_TOKEN_RE.sub(" ", _stable_text(value)).split())


def _payload_text(payload: dict, *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for nested_key in ("job", "position", "metadata"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            for key in keys:
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def _company_and_location(item: NormalizedItem, raw: RawObservation) -> tuple[str | None, str]:
    payload = raw.raw_payload if isinstance(raw.raw_payload, dict) else {}
    company = _payload_text(payload, "company", "company_name", "employer", "organization")
    location = _payload_text(payload, "location", "city", "region") or ""
    combined = f"{item.title or ''} {item.text or ''}"
    if not company:
        match = _COMPANY_RE.search(combined)
        company = match.group(1).strip() if match else None
    if not location:
        match = _LOCATION_RE.search(combined)
        location = match.group(1).strip() if match else ""
    company_key = _key_text(company) if company else None
    location_key = _key_text(location)
    return company_key or None, location_key


def _job_record(item: NormalizedItem, raw: RawObservation) -> _JobRecord | None:
    title = _key_text(item.title or item.query)
    if not title:
        return None
    company, location = _company_and_location(item, raw)
    identity = "|".join((company or "unknown-company", title, location))
    return _JobRecord(
        day=item.observed_at.date(),
        identity=identity,
        company=company,
        source=item.source_id,
        evidence_id=evidence_id_for_content_hash(raw.content_hash),
        observed_at=item.observed_at,
    )


def _period_metrics(records: list[_JobRecord], *, start: date, end: date) -> tuple[dict[date, int], dict[date, int], dict[date, int], HiringDiversityMetrics]:
    daily_jobs: dict[date, set[str]] = defaultdict(set)
    daily_sources: dict[date, set[str]] = defaultdict(set)
    daily_evidence: dict[date, set[str]] = defaultdict(set)
    period_jobs: set[str] = set()
    companies: set[str] = set()
    unknown_jobs: set[str] = set()
    sources: set[str] = set()
    for record in records:
        if not start <= record.day < end:
            continue
        daily_jobs[record.day].add(record.identity)
        daily_sources[record.day].add(record.source)
        daily_evidence[record.day].add(record.evidence_id)
        period_jobs.add(record.identity)
        sources.add(record.source)
        if record.company:
            companies.add(record.company)
        else:
            unknown_jobs.add(record.identity)
    observation_count = sum(1 for record in records if start <= record.day < end)
    unique_daily_count = sum(len(values) for values in daily_jobs.values())
    unique_jobs = len(period_jobs)
    company_diversity = min(1.0, len(companies) / unique_jobs) if unique_jobs else 0.0
    source_diversity = min(1.0, len(sources) / unique_jobs) if unique_jobs else 0.0
    duplicate_count = max(0, observation_count - unique_daily_count)
    return (
        {day: len(values) for day, values in daily_jobs.items()},
        {day: len(values) for day, values in daily_sources.items()},
        {day: len(values) for day, values in daily_evidence.items()},
        HiringDiversityMetrics(
            current_unique_jobs=0,
            baseline_unique_jobs=0,
            current_duplicate_observations=0,
            baseline_duplicate_observations=0,
            current_company_count=0,
            baseline_company_count=0,
            current_unknown_company_count=0,
            baseline_unknown_company_count=0,
            current_source_count=0,
            baseline_source_count=0,
            current_company_diversity=0.0,
            baseline_company_diversity=0.0,
            current_source_diversity=0.0,
            baseline_source_diversity=0.0,
            current_duplicate_rate=round(duplicate_count / observation_count, 6) if observation_count else 0.0,
            baseline_duplicate_rate=0.0,
        ).model_copy(update={
            "current_unique_jobs": unique_jobs,
            "current_duplicate_observations": duplicate_count,
            "current_company_count": len(companies),
            "current_unknown_company_count": len(unknown_jobs),
            "current_source_count": len(sources),
            "current_company_diversity": round(company_diversity, 6),
            "current_source_diversity": round(source_diversity, 6),
        }),
    )


def _metrics_for_periods(records: list[_JobRecord], *, current_start: date, current_end: date, baseline_start: date, baseline_end: date) -> tuple[dict[date, int], dict[date, int], dict[date, int], HiringDiversityMetrics]:
    current_jobs, current_sources, current_evidence, current = _period_metrics(records, start=current_start, end=current_end)
    baseline_jobs, baseline_sources, baseline_evidence, baseline = _period_metrics(records, start=baseline_start, end=baseline_end)
    metrics = HiringDiversityMetrics(
        current_unique_jobs=current.current_unique_jobs,
        baseline_unique_jobs=baseline.current_unique_jobs,
        current_duplicate_observations=current.current_duplicate_observations,
        baseline_duplicate_observations=baseline.current_duplicate_observations,
        current_company_count=current.current_company_count,
        baseline_company_count=baseline.current_company_count,
        current_unknown_company_count=current.current_unknown_company_count,
        baseline_unknown_company_count=baseline.current_unknown_company_count,
        current_source_count=current.current_source_count,
        baseline_source_count=baseline.current_source_count,
        current_company_diversity=current.current_company_diversity,
        baseline_company_diversity=baseline.current_company_diversity,
        current_source_diversity=current.current_source_diversity,
        baseline_source_diversity=baseline.current_source_diversity,
        current_duplicate_rate=current.current_duplicate_rate,
        baseline_duplicate_rate=baseline.current_duplicate_rate,
    )
    daily_jobs = {**baseline_jobs, **current_jobs}
    daily_sources = {**baseline_sources, **current_sources}
    daily_evidence = {**baseline_evidence, **current_evidence}
    return daily_jobs, daily_sources, daily_evidence, metrics


def _detection_signature(detection: HiringSurgeDetection) -> str:
    payload = {
        "contract_version": HIRING_SURGE_CONTRACT_VERSION,
        "algorithm_version": HIRING_SURGE_ALGORITHM_VERSION,
        "evaluation": detection.evaluation.input_signature,
        "metrics": detection.metrics.model_dump(mode="json"),
        "evidence_ids": detection.evidence_ids,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def detect_hiring_surges(
    db: Session,
    *,
    keyword_ids: set[int] | None = None,
    window_end: date | None = None,
    policy: HiringSurgePolicy | None = None,
    anomalous_only: bool = False,
    limit: int = 100,
) -> list[HiringSurgeDetection]:
    """Detect hiring surges from JOB mentions without mutating the database."""

    if limit < 1 or limit > HIRING_SURGE_MAX_KEYWORDS:
        raise ValueError(f"limit must be between 1 and {HIRING_SURGE_MAX_KEYWORDS}")
    policy = policy or HiringSurgePolicy()
    window_end = window_end or utc_now().date()
    _current_start, current_end, baseline_start, _baseline_end = hiring_windows(window_end, policy)
    if keyword_ids is not None and not keyword_ids:
        return []
    keyword_stmt = (
        select(Keyword.id, Keyword.display_name)
        .join(KeywordMention, KeywordMention.keyword_id == Keyword.id)
        .join(NormalizedItem, NormalizedItem.id == KeywordMention.normalized_item_id)
        .where(
            NormalizedItem.item_type == "JOB",
            KeywordMention.observed_at >= datetime.combine(baseline_start, time.min),
            KeywordMention.observed_at < datetime.combine(current_end, time.min),
        )
        .distinct()
        .order_by(Keyword.id)
        .limit(limit)
    )
    if keyword_ids is not None:
        keyword_stmt = keyword_stmt.where(Keyword.id.in_(keyword_ids))
    keyword_rows = db.execute(keyword_stmt).all()
    if not keyword_rows:
        return []
    selected_ids = {row.id for row in keyword_rows}
    rows = db.execute(
        select(KeywordMention, NormalizedItem, RawObservation)
        .join(NormalizedItem, NormalizedItem.id == KeywordMention.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(
            KeywordMention.keyword_id.in_(selected_ids),
            NormalizedItem.item_type == "JOB",
            KeywordMention.observed_at >= datetime.combine(baseline_start, time.min),
            KeywordMention.observed_at < datetime.combine(current_end, time.min),
        )
        .order_by(KeywordMention.keyword_id, NormalizedItem.observed_at, NormalizedItem.id)
        .limit(HIRING_SURGE_MAX_ROWS)
    ).all()
    grouped: dict[int, list[_JobRecord]] = defaultdict(list)
    for mention, item, raw in rows:
        record = _job_record(item, raw)
        if record is not None:
            grouped[mention.keyword_id].append(record)
    results: list[HiringSurgeDetection] = []
    for keyword_id, keyword in keyword_rows:
        records = grouped.get(keyword_id, [])
        daily_jobs, daily_sources, daily_evidence, metrics = _metrics_for_periods(
            records,
            current_start=_current_start,
            current_end=current_end,
            baseline_start=baseline_start,
            baseline_end=_current_start,
        )
        evaluation = evaluate_hiring_surge(
            HiringSurgeInput(
                keyword_id=keyword_id,
                keyword=keyword,
                window_end=window_end,
                daily_jobs=daily_jobs,
                daily_sources=daily_sources,
                daily_evidence=daily_evidence,
            ),
            policy=policy,
        )
        evidence_ids = [record.evidence_id for record in sorted(records, key=lambda item: (item.observed_at, item.evidence_id), reverse=True)[:20]]
        detection = HiringSurgeDetection(evaluation=evaluation, metrics=metrics, evidence_ids=list(dict.fromkeys(evidence_ids)), detection_signature="0" * 64)
        detection = detection.model_copy(update={"detection_signature": _detection_signature(detection)})
        if anomalous_only and not evaluation.surge:
            continue
        results.append(detection)
    return results
