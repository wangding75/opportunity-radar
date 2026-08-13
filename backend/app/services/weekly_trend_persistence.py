"""Persistence and reconstruction of versioned weekly trend reports."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import WeeklyTrendRecord
from app.domain.weekly_trends import WeeklyTrendReport


def _explanation_for_report(report: WeeklyTrendReport) -> dict:
    return {
        "status": report.status.value,
        "warnings": report.warnings,
        "generation_error": report.generation_error,
        "items": [
            {
                "rank": item.rank,
                "keyword_id": item.keyword_id,
                "keyword": item.keyword,
                "comparison": item.comparison.value,
                "absolute_delta": item.absolute_delta,
                "growth_rate": item.growth_rate,
                "trend_signature": item.trend_signature,
                "evidence_provenance": item.evidence_provenance.value,
                "selection_reasons": item.selection_reasons,
            }
            for item in report.items
        ],
    }


def _payload_for_report(report: WeeklyTrendReport) -> dict:
    data = report.model_dump(mode="json")
    return {
        "items": data["items"],
        "warnings": data["warnings"],
        "generation_error": data["generation_error"],
    }


def _contract_for_record(row: WeeklyTrendRecord) -> WeeklyTrendReport:
    payload = row.payload or {}
    return WeeklyTrendReport.model_validate({
        "contract_version": row.contract_version,
        "algorithm_version": row.algorithm_version,
        "timezone": row.timezone,
        "week_start": row.week_start,
        "week_end": row.week_end,
        "baseline_start": row.baseline_start,
        "baseline_end": row.baseline_end,
        "generated_at": row.generated_at,
        "status": row.status,
        "policy": row.selection_policy or {},
        "total_candidates": row.total_candidates,
        "selected_count": row.selected_count,
        "input_signature": row.input_signature,
        "items": payload.get("items", []),
        "warnings": payload.get("warnings", []),
        "generation_error": payload.get("generation_error"),
    })


def save_weekly_trend_report(db: Session, report: WeeklyTrendReport) -> WeeklyTrendRecord:
    """Upsert one complete UTC week while preserving explanation fields."""

    row = db.scalar(select(WeeklyTrendRecord).where(WeeklyTrendRecord.week_start == report.week_start))
    now = utc_now()
    data = report.model_dump(mode="json")
    values = {
        "week_start": report.week_start,
        "week_end": report.week_end,
        "baseline_start": report.baseline_start,
        "baseline_end": report.baseline_end,
        "contract_version": report.contract_version,
        "algorithm_version": report.algorithm_version,
        "timezone": report.timezone,
        "generated_at": report.generated_at,
        "status": report.status.value,
        "selection_policy": data["policy"],
        "total_candidates": report.total_candidates,
        "selected_count": report.selected_count,
        "input_signature": report.input_signature,
        "payload": _payload_for_report(report),
        "explanation": _explanation_for_report(report),
    }
    if row is None:
        row = WeeklyTrendRecord(**values, created_at=now, updated_at=now)
        db.add(row)
    elif row.input_signature != report.input_signature or row.algorithm_version != report.algorithm_version or row.contract_version != report.contract_version:
        for key, value in values.items():
            setattr(row, key, value)
        row.updated_at = now
    db.flush()
    return row


def get_weekly_trend_report(db: Session, week_start: date | None = None) -> WeeklyTrendReport:
    stmt = select(WeeklyTrendRecord)
    if week_start is None:
        stmt = stmt.order_by(WeeklyTrendRecord.week_start.desc()).limit(1)
        row = db.scalar(stmt)
    else:
        row = db.scalar(stmt.where(WeeklyTrendRecord.week_start == week_start))
    if row is None:
        raise KeyError("weekly trend report not found")
    return _contract_for_record(row)
