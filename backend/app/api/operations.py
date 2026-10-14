from __future__ import annotations

import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.security import require_admin_auth, require_observation_state_auth, require_read_auth
from app.db.models import AuditLog, Opportunity, RawObservation
from app.db.session import get_db
from app.domain.schemas import UserObservationStatePatch
from app.services.archive import archive_raw_payloads, restore_raw_payload_archive
from app.services.auth import Principal
from app.services.observation_state import (
    delete_user_observation_state,
    get_user_observation_state,
    serialize_user_observation_state,
    upsert_user_observation_state,
    user_observation_state_map,
)
from app.services.pagination import decode_cursor, observation_cursor
from app.services.research import research_state_map, serialize_research_state
from app.services.retention import run_retention
from app.services.worker_health import worker_health_report
from app.services.weekly_trend_persistence import get_weekly_trend_report

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_read_auth)])


def _observation_public_id(row: RawObservation) -> str:
    # content_hash is immutable and unique at ingestion time. Prefixing it gives
    # product URLs a stable ID without exposing the database sequence.
    return f"obs_{row.content_hash}"


def _observation_from_identifier(db: Session, identifier: str) -> RawObservation | None:
    if identifier.isdecimal():
        return db.get(RawObservation, int(identifier))
    if identifier.startswith("obs_") and len(identifier) == 68:
        return db.scalar(select(RawObservation).where(RawObservation.content_hash == identifier[4:]))
    return None


def _current_user_id(principal: Principal | None) -> int | None:
    """Resolve the calling user for per-user observation state.

    In development anonymous mode (AUTH_MODE=disabled) or for legacy API-key
    principals there is no real user identity; the API must return an explicit
    null user_state instead of attributing bookmarks to a synthetic user.
    """
    if principal is None or principal.user_id is None:
        return None
    return principal.user_id


@router.get("/observations")
def observations(
    q: str | None = Query(default=None, max_length=200),
    source_id: str | None = Query(default=None, max_length=100),
    item_type: str | None = Query(default=None, max_length=50),
    observed_after: datetime | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    cursor: str | None = Query(default=None, max_length=1000),
    limit: int = Query(default=100, ge=1, le=500),
    request: Request = None,
    db: Session = Depends(get_db),
):
    user_id = _current_user_id(getattr(request.state, "principal", None) if request is not None else None)
    filters = []
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(or_(RawObservation.title.ilike(pattern), RawObservation.text.ilike(pattern), RawObservation.query.ilike(pattern)))
    if source_id:
        filters.append(RawObservation.source_id == source_id)
    if item_type:
        filters.append(RawObservation.item_type == item_type.strip().upper())
    if observed_after:
        filters.append(RawObservation.observed_at >= observed_after)
    count_stmt = select(func.count(RawObservation.id))
    rows_stmt = select(RawObservation)
    if filters:
        count_stmt = count_stmt.where(*filters)
        rows_stmt = rows_stmt.where(*filters)
    total = db.scalar(count_stmt) or 0
    try:
        decoded = decode_cursor(cursor)
        if decoded:
            seen = datetime.fromisoformat(decoded["observed_at"])
            row_id = int(decoded["id"])
            rows_stmt = rows_stmt.where(or_(
                RawObservation.observed_at < seen,
                and_(RawObservation.observed_at == seen, RawObservation.id < row_id),
            ))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="invalid pagination cursor") from exc
    ordered = rows_stmt.order_by(RawObservation.observed_at.desc(), RawObservation.id.desc())
    if not cursor:
        ordered = ordered.offset(offset)
    rows = db.scalars(ordered.limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = observation_cursor(rows[-1].observed_at, rows[-1].id) if has_more and rows else None
    states = user_observation_state_map(db, user_id, [row.id for row in rows]) if user_id is not None else {}
    return {
        "total": total,
        "offset": offset if not cursor else None,
        "limit": limit,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "items": [
            {
                "id": row.id,
                "public_id": _observation_public_id(row),
                "source_id": row.source_id,
                "query": row.query,
                "item_type": row.item_type,
                "title": row.title,
                "text": row.text[:2000],
                "source_url": row.source_url,
                "evidence_quality": row.evidence_quality,
                "acquisition_method": row.acquisition_method,
                "observed_at": row.observed_at,
                "user_state": serialize_user_observation_state(states.get(row.id)),
            }
            for row in rows
        ],
    }


@router.get("/observations/{observation_id}")
def observation_detail(observation_id: str, request: Request = None, db: Session = Depends(get_db)):
    row = _observation_from_identifier(db, observation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="observation not found")
    user_id = _current_user_id(getattr(request.state, "principal", None) if request is not None else None)
    state = get_user_observation_state(db, user_id, row.id) if user_id is not None else None
    return {
        "public_id": _observation_public_id(row),
        "source_id": row.source_id,
        "external_id": row.external_id,
        "query": row.query,
        "item_type": row.item_type,
        "title": row.title,
        "text": row.text,
        "source_url": row.source_url,
        "observed_at": row.observed_at,
        "acquisition_method": row.acquisition_method,
        "evidence_quality": row.evidence_quality,
        "acquisition_risk": row.acquisition_risk,
        "user_state": serialize_user_observation_state(state),
    }


@router.get("/observations/{observation_id}/state")
def observation_state(observation_id: str, request: Request = None, db: Session = Depends(get_db)):
    row = _observation_from_identifier(db, observation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="observation not found")
    user_id = _current_user_id(getattr(request.state, "principal", None) if request is not None else None)
    if user_id is None:
        # Anonymous/development mode has no user identity to attach state to.
        # Explicit null is the contract; never fabricate bookmark defaults.
        raise HTTPException(status_code=401, detail="authenticated user required for observation state")
    state = get_user_observation_state(db, user_id, row.id)
    return {
        "observation_public_id": _observation_public_id(row),
        "user_id": user_id,
        "user_state": serialize_user_observation_state(state),
    }


@router.put("/observations/{observation_id}/state")
def observation_state_put(
    observation_id: str,
    payload: UserObservationStatePatch,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_observation_state_auth),
):
    row = _observation_from_identifier(db, observation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="observation not found")
    user_id = _current_user_id(principal)
    if user_id is None:
        raise HTTPException(status_code=403, detail="a real user identity is required to store observation state")
    try:
        state = upsert_user_observation_state(
            db,
            user_id,
            row.id,
            bookmarked=payload.bookmarked,
            dismissed=payload.dismissed,
            notes=payload.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return {
        "observation_public_id": _observation_public_id(row),
        "user_id": user_id,
        "user_state": serialize_user_observation_state(state),
        "request_id": getattr(request.state, "request_id", None),
    }


@router.delete("/observations/{observation_id}/state")
def observation_state_delete(
    observation_id: str,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_observation_state_auth),
):
    row = _observation_from_identifier(db, observation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="observation not found")
    user_id = _current_user_id(principal)
    if user_id is None:
        raise HTTPException(status_code=403, detail="a real user identity is required to delete observation state")
    delete_user_observation_state(db, user_id, row.id)
    db.commit()
    return {
        "observation_public_id": _observation_public_id(row),
        "user_id": user_id,
        "user_state": None,
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/audit")
def audit_log(
    action: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action.strip().upper())
    rows = db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "request_id": row.request_id,
            "actor": row.actor,
            "action": row.action,
            "resource": row.resource,
            "status_code": row.status_code,
            "detail": row.detail,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def _csv_cell(value: object) -> object:
    if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
        return "'" + value
    return value


def _csv_response(filename: str, headers: list[str], rows: list[list[object]]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows([[_csv_cell(value) for value in row] for row in rows])
    payload = "\ufeff" + buffer.getvalue()
    return StreamingResponse(
        iter([payload.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/workers")
def workers(db: Session = Depends(get_db), _auth=Depends(require_admin_auth)):
    return worker_health_report(db)


@router.post("/maintenance/retention")
def retention_run(
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    return run_retention(db, dry_run=dry_run)


@router.post("/maintenance/archive-raw-payloads")
def archive_raw_payloads_run(
    older_than_days: int = Query(default=90, ge=1, le=36500),
    limit: int = Query(default=1000, ge=1, le=10000),
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    return archive_raw_payloads(db, older_than_days=older_than_days, limit=limit, dry_run=dry_run)


@router.post("/maintenance/restore-raw-payload-archive")
def restore_raw_payload_archive_run(
    archive_file: str = Query(..., min_length=1, max_length=500),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    try:
        return restore_raw_payload_archive(db, archive_file)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/exports/opportunities.csv")
def export_opportunities_csv(
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Opportunity)
        .where(Opportunity.stage != "DORMANT", Opportunity.score >= min_score)
        .order_by(Opportunity.score.desc(), Opportunity.last_seen_at.desc())
        .limit(10_000)
    ).all()
    states = research_state_map(db, [row.id for row in rows])
    return _csv_response(
        "opportunities.csv",
        ["id", "title", "stage", "score", "risk_score", "evidence_count", "research_status", "starred", "priority", "tags", "summary", "first_seen_at", "last_seen_at"],
        [
            [
                row.id, row.title, row.stage, row.score, row.risk_score, row.evidence_count,
                serialize_research_state(states.get(row.id))["status"],
                serialize_research_state(states.get(row.id))["starred"],
                serialize_research_state(states.get(row.id))["priority"],
                ",".join(serialize_research_state(states.get(row.id))["tags"]),
                row.summary, row.first_seen_at.isoformat(), row.last_seen_at.isoformat(),
            ]
            for row in rows
        ],
    )


@router.get("/exports/observations.csv")
def export_observations_csv(
    source_id: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    stmt = select(RawObservation)
    if source_id:
        stmt = stmt.where(RawObservation.source_id == source_id)
    rows = db.scalars(stmt.order_by(RawObservation.observed_at.desc()).limit(50_000)).all()
    return _csv_response(
        "observations.csv",
        ["id", "source_id", "query", "item_type", "title", "source_url", "evidence_quality", "acquisition_method", "observed_at"],
        [[row.id, row.source_id, row.query, row.item_type, row.title, row.source_url or "", row.evidence_quality, row.acquisition_method, row.observed_at.isoformat()] for row in rows],
    )


@router.get("/exports/trends/weekly.csv")
def export_weekly_trends_csv(
    week_start: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        report = get_weekly_trend_report(db, week_start=week_start)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    headers = [
        "week_start", "week_end", "baseline_start", "baseline_end", "rank", "keyword", "comparison",
        "current_observations", "baseline_observations", "absolute_delta", "growth_rate", "momentum_score",
        "current_sources", "baseline_sources", "evidence_provenance", "trend_signature", "last_seen_at", "selection_reasons",
    ]
    rows = [
        [
            report.week_start.isoformat(), report.week_end.isoformat(), report.baseline_start.isoformat(), report.baseline_end.isoformat(),
            item.rank, item.keyword, item.comparison.value, item.current_observations, item.baseline_observations,
            item.absolute_delta, item.growth_rate if item.growth_rate is not None else "", item.momentum_score,
            item.current_sources, item.baseline_sources, item.evidence_provenance.value, item.trend_signature,
            item.last_seen_at.isoformat(), " | ".join(item.selection_reasons),
        ]
        for item in report.items
    ]
    return _csv_response("weekly-trends.csv", headers, rows)
