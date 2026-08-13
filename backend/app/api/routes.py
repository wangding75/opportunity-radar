from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorRateLimitError
from app.connectors.registry import SourceRegistry
from app.core.config import settings
from app.core.security import require_admin_auth, require_read_auth
from app.core.time import utc_now
from app.db.models import CollectionRun, Keyword, NormalizedItem, Opportunity, OpportunityResearch, RawObservation
from app.db.session import get_db
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, EvidenceQuality
from app.domain.schemas import (
    CollectorQuery, ImportRequest, InstrumentedAppObservation, SourcePreferencePatch,
    MAX_IMPORT_REQUEST_BYTES, observation_size_bytes,
)
from app.services.analysis import process_new_raw, refresh_derived_analysis
from app.services.analysis_queue import run_pending_opportunity_analysis
from app.services.opportunity_analysis import build_analysis_provider_registry, build_analysis_provider_router
from app.services.provider_registry import ProviderCapability
from app.services.app_observation import schema_drift_report
from app.services.dashboard import dashboard_summary
from app.services.digest import generate_daily_digest
from app.services.digest_persistence import get_daily_digest, save_daily_digest
from app.services.weekly_trends import aggregate_weekly_trends
from app.services.weekly_trend_persistence import get_weekly_trend_report, save_weekly_trend_report
from app.services.graph import keyword_graph
from app.services.ingestion import from_import, from_instrumented, store_collected
from app.services.opportunities import opportunity_detail
from app.services.pagination import decode_cursor, opportunity_cursor
from app.services.research import research_state_map, serialize_research_state
from app.services.execution import execute_collection
from app.services.probes import build_probe_plan, list_probe_tasks, run_due_probe_tasks, sync_probe_tasks
from app.services.source_health import source_health_report
from app.services.source_preferences import get_source_preference, set_source_preference, source_enabled
from app.services.trends import keyword_trend_summary
from app.services.tool_products import (
    list_tool_product_entities,
    normalize_tool_product_entities,
    tool_product_entity_detail,
)
from app.services.tool_product_occurrences import (
    list_tool_product_occurrences,
    materialize_tool_product_occurrences,
)
from app.domain.hiring_surge import HiringSurgePolicy
from app.services.hiring_surge import detect_hiring_surges
from app.domain.risk_escalation import RiskEscalationPolicy
from app.services.risk_escalation import detect_risk_escalations

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_read_auth)])
registry: SourceRegistry | None = None


def set_registry(value: SourceRegistry) -> None:
    global registry
    registry = value


def _registry() -> SourceRegistry:
    if registry is None:
        raise RuntimeError("source registry is not initialized")
    return registry


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    rows = []
    for connector in _registry().list():
        data = connector.descriptor.model_dump(mode="json")
        preference = get_source_preference(db, connector.descriptor.source_id)
        data["runtime_enabled"] = source_enabled(db, connector.descriptor.source_id, default=connector.descriptor.enabled)
        data["preference_note"] = preference.note if preference else ""
        rows.append(data)
    return rows


@router.get("/analysis/providers")
def analysis_providers():
    return build_analysis_provider_registry().snapshot()


@router.get("/analysis/providers/route")
def analysis_provider_route():
    return build_analysis_provider_router().snapshot(ProviderCapability.STRUCTURED_ANALYSIS)


@router.get("/digests/daily")
def daily_digest(digest_date: date | None = Query(default=None), db: Session = Depends(get_db)):
    try:
        return get_daily_digest(db, digest_date=digest_date).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/digests/daily/{digest_date}")
def daily_digest_by_date(digest_date: date, db: Session = Depends(get_db)):
    try:
        return get_daily_digest(db, digest_date=digest_date).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/digests/daily/generate")
def generate_daily_digest_endpoint(
    digest_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    digest = generate_daily_digest(db, digest_date=digest_date)
    save_daily_digest(db, digest)
    db.commit()
    return digest.model_dump(mode="json")


@router.get("/trends/weekly")
def weekly_trend_report(week_start: date | None = Query(default=None), db: Session = Depends(get_db)):
    try:
        return get_weekly_trend_report(db, week_start=week_start).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/trends/weekly/{week_start}")
def weekly_trend_report_by_week(week_start: date, db: Session = Depends(get_db)):
    try:
        return get_weekly_trend_report(db, week_start=week_start).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/trends/weekly/generate")
def generate_weekly_trend_report_endpoint(
    anchor_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    report = aggregate_weekly_trends(db, anchor_date=anchor_date)
    save_weekly_trend_report(db, report)
    db.commit()
    return report.model_dump(mode="json")


@router.get("/sources/health")
def source_health(
    request: Request,
    db: Session = Depends(get_db),
):
    connectors = _registry().list()
    runtime = {row["source_id"]: row for row in source_health_report(db, [c.descriptor.source_id for c in connectors])}
    principal = getattr(request.state, "principal", None)
    is_admin = principal is None or principal.has_scope("admin")
    rows = []
    for connector in connectors:
        row = {**connector.health(), **runtime.get(connector.descriptor.source_id, {})}
        if not is_admin:
            row["last_error"] = None
        rows.append(row)
    return rows


@router.post("/collect/{source_id}")
def collect(source_id: str, payload: CollectorQuery, db: Session = Depends(get_db), _auth=Depends(require_admin_auth)):
    try:
        connector = _registry().get(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    bounded = payload.model_copy(update={"limit": min(payload.limit, settings.max_collect_items)})
    try:
        return execute_collection(db, _registry(), source_id=source_id, query=bounded)
    except ConnectorRateLimitError as exc:
        db.rollback()
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"collector failed: {exc}") from exc


@router.post("/import")
def import_records(payload: ImportRequest, db: Session = Depends(get_db), _auth=Depends(require_admin_auth)):
    reserved_source_ids = {connector.descriptor.source_id for connector in _registry().list()}
    collisions = sorted({record.source_id for record in payload.records} & reserved_source_ids)
    if collisions:
        raise HTTPException(
            status_code=409,
            detail=f"manual import cannot use registered connector source_id(s): {', '.join(collisions)}",
        )
    inserted = 0
    duplicates = 0
    item_ids: set[int] = set()
    for source in payload.records:
        raw, is_new = store_collected(
            db,
            source_id=source.source_id,
            query=source.query,
            record=from_import(source),
            acquisition_method=source.acquisition_method,
            evidence_quality=source.evidence_quality,
            acquisition_risk=source.acquisition_risk,
        )
        if not is_new:
            duplicates += 1
            continue
        inserted += 1
        item = process_new_raw(db, raw)
        item_ids.add(item.id)
    if item_ids:
        refresh_derived_analysis(db, normalized_item_ids=item_ids)
    db.commit()
    return {"inserted": inserted, "duplicates": duplicates}


@router.post("/instrumented-app/observations")
def import_instrumented(payload: list[InstrumentedAppObservation], db: Session = Depends(get_db), _auth=Depends(require_admin_auth)):
    if not payload:
        raise HTTPException(status_code=422, detail="at least one observation is required")
    if len(payload) > 1000:
        raise HTTPException(status_code=422, detail="maximum 1000 observations per request")
    total_bytes = sum(observation_size_bytes(record) for record in payload)
    if total_bytes > MAX_IMPORT_REQUEST_BYTES:
        raise HTTPException(status_code=413, detail=f"instrumented observation request exceeds {MAX_IMPORT_REQUEST_BYTES} byte limit")
    reserved_source_ids = {connector.descriptor.source_id for connector in _registry().list()}
    collisions = sorted({record.source_id for record in payload} & reserved_source_ids)
    if collisions:
        raise HTTPException(
            status_code=409,
            detail=f"instrumented observations cannot impersonate registered connector source_id(s): {', '.join(collisions)}",
        )
    inserted = 0
    duplicates = 0
    item_ids: set[int] = set()
    for source in payload:
        raw, is_new = store_collected(
            db,
            source_id=source.source_id,
            query=source.query,
            record=from_instrumented(source),
            acquisition_method=AcquisitionMethod.INSTRUMENTED_APP,
            evidence_quality=EvidenceQuality.C,
            acquisition_risk=AcquisitionRisk.R4,
            app_meta={
                "app_package": source.app_package,
                "app_version": source.app_version,
                "emulator_profile": source.emulator_profile,
                "instrumentation_version": source.instrumentation_version,
                "session_id": source.session_id,
            },
        )
        if not is_new:
            duplicates += 1
            continue
        inserted += 1
        item = process_new_raw(db, raw)
        item_ids.add(item.id)
    if item_ids:
        refresh_derived_analysis(db, normalized_item_ids=item_ids)
    db.commit()
    return {"inserted": inserted, "duplicates": duplicates}


@router.get("/instrumented-app/schema-drift")
def instrumented_schema_drift(source_id: str = Query(min_length=1, max_length=100), db: Session = Depends(get_db)):
    return schema_drift_report(db, source_id)


@router.post("/analysis/refresh")
def refresh_analysis(db: Session = Depends(get_db), _auth=Depends(require_admin_auth)):
    refresh_derived_analysis(db)
    db.commit()
    pending = db.scalars(
        select(Opportunity.id).where(Opportunity.analysis_status.in_(["PENDING", "DEGRADED"]))
    ).all()
    return {"status": "ok", "pending_external_analysis": len(pending)}


@router.post("/analysis/run-pending")
def run_pending_analysis(
    limit: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    return run_pending_opportunity_analysis(db, limit=limit)


@router.post("/tool-products/normalize")
def normalize_tool_products(
    limit: int = Query(default=500, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    try:
        result = normalize_tool_product_entities(db, limit=limit)
        result["occurrences"] = materialize_tool_product_occurrences(db, limit=500)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/tool-products/entities")
def tool_product_entities(
    status: str | None = Query(default=None, max_length=30),
    kind: str | None = Query(default=None, max_length=20),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_tool_product_entities(db, status=status, kind=kind, limit=limit)


@router.get("/tool-products/entities/{entity_key}")
def tool_product_entity(entity_key: str, db: Session = Depends(get_db)):
    try:
        return tool_product_entity_detail(db, entity_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tool-products/occurrences")
def tool_product_occurrences(
    entity_key: str | None = Query(default=None, max_length=68),
    classification: str | None = Query(default=None, max_length=20),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_tool_product_occurrences(db, entity_key=entity_key, classification=classification, limit=limit)


@router.post("/tool-products/occurrences/materialize")
def materialize_tool_product_occurrences_endpoint(
    limit: int = Query(default=500, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    try:
        result = materialize_tool_product_occurrences(db, limit=limit)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/hiring/surges")
def hiring_surges(
    keyword_id: int | None = Query(default=None, ge=1),
    window_end: date | None = Query(default=None),
    anomalous_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        detections = detect_hiring_surges(
            db,
            keyword_ids={keyword_id} if keyword_id is not None else None,
            window_end=window_end,
            policy=HiringSurgePolicy(),
            anomalous_only=anomalous_only,
            limit=limit,
        )
        return [detection.model_dump(mode="json") for detection in detections]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/risk/escalations")
def risk_escalations(
    opportunity_id: int | None = Query(default=None, ge=1),
    escalated_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        evaluations = detect_risk_escalations(
            db,
            opportunity_ids={opportunity_id} if opportunity_id is not None else None,
            policy=RiskEscalationPolicy(),
            escalated_only=escalated_only,
            limit=limit,
        )
        return [evaluation.model_dump(mode="json") for evaluation in evaluations]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/keywords")
def keywords(
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Keyword)
    if status:
        stmt = stmt.where(Keyword.status == status)
    rows = db.scalars(stmt.order_by(desc(Keyword.score), desc(Keyword.last_seen_at)).limit(limit)).all()
    return [
        {
            "id": row.id,
            "keyword": row.display_name,
            "canonical": row.canonical,
            "status": row.status,
            "score": row.score,
            "observation_count": row.observation_count,
            "source_count": row.source_count,
            "first_seen_at": row.first_seen_at,
            "last_seen_at": row.last_seen_at,
        }
        for row in rows
    ]


@router.get("/keywords/{keyword_id}/trend")
def keyword_trend(keyword_id: int, db: Session = Depends(get_db)):
    try:
        return keyword_trend_summary(db, keyword_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/keyword-graph")
def graph(
    keyword_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    since_days: int = Query(default=90, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    return keyword_graph(db, keyword_id=keyword_id, limit=limit, since_days=since_days)


@router.get("/probes/plan")
def probe_plan(
    keyword_limit: int = Query(default=20, ge=1, le=100),
    max_queries: int = Query(default=60, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return build_probe_plan(db, _registry(), keyword_limit=keyword_limit, max_queries=max_queries)


@router.post("/probes/sync")
def probe_sync(
    keyword_limit: int = Query(default=20, ge=1, le=100),
    max_queries: int = Query(default=60, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    return sync_probe_tasks(db, _registry(), keyword_limit=keyword_limit, max_queries=max_queries)


@router.get("/probes/tasks")
def probe_tasks(
    active_only: bool = False,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    return list_probe_tasks(db, active_only=active_only, limit=limit)


@router.post("/probes/run-due")
def probe_run_due(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    return run_due_probe_tasks(db, _registry(), limit=limit)


@router.get("/collection-runs")
def collection_runs(
    source_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    stmt = select(CollectionRun)
    if source_id:
        stmt = stmt.where(CollectionRun.source_id == source_id)
    if status:
        stmt = stmt.where(CollectionRun.status == status)
    rows = db.scalars(stmt.order_by(CollectionRun.started_at.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "probe_task_id": row.probe_task_id,
            "source_id": row.source_id,
            "query": row.query,
            "intent": row.intent,
            "worker_id": row.worker_id,
            "status": row.status,
            "started_at": row.started_at,
            "finished_at": row.finished_at,
            "fetched": row.fetched,
            "inserted": row.inserted,
            "duplicates": row.duplicates,
            "normalized": row.normalized,
            "duration_ms": row.duration_ms,
            "error": row.error,
        }
        for row in rows
    ]


@router.get("/opportunities")
def opportunities(
    stage: str | None = None,
    include_dormant: bool = False,
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    q: str | None = Query(default=None, max_length=200),
    research_status: str | None = Query(default=None, max_length=30),
    starred: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Opportunity).where(Opportunity.score >= min_score)
    if stage:
        stmt = stmt.where(Opportunity.stage == stage)
    elif not include_dormant:
        stmt = stmt.where(Opportunity.stage != "DORMANT")
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Opportunity.title.ilike(pattern), Opportunity.summary.ilike(pattern)))
    if research_status is not None or starred is not None:
        stmt = stmt.outerjoin(OpportunityResearch, OpportunityResearch.opportunity_id == Opportunity.id)
        if research_status is not None:
            normalized = research_status.strip().upper()
            if normalized == "NEW":
                stmt = stmt.where(or_(OpportunityResearch.status == "NEW", OpportunityResearch.status.is_(None)))
            else:
                stmt = stmt.where(OpportunityResearch.status == normalized)
        if starred is True:
            stmt = stmt.where(OpportunityResearch.starred.is_(True))
        elif starred is False:
            stmt = stmt.where(or_(OpportunityResearch.starred.is_(False), OpportunityResearch.starred.is_(None)))
    rows = db.scalars(stmt.order_by(Opportunity.score.desc(), Opportunity.last_seen_at.desc()).offset(offset).limit(limit)).all()
    state_by_id = research_state_map(db, [row.id for row in rows])
    return [
        {
            "id": row.id,
            "title": row.title,
            "stage": row.stage,
            "score": row.score,
            "risk_score": row.risk_score,
            "demand_score": row.demand_score,
            "supply_score": row.supply_score,
            "execution_score": row.execution_score,
            "cross_source_score": row.cross_source_score,
            "saturation_score": row.saturation_score,
            "evidence_count": row.evidence_count,
            "related_keyword_count": row.related_keyword_count,
            "summary": row.summary,
            "analysis_status": row.analysis_status,
            "analysis_provider": row.analysis_provider,
            "analysis_attempt_count": row.analysis_attempt_count,
            "analysis_next_retry_at": row.analysis_next_retry_at,
            "research": serialize_research_state(state_by_id.get(row.id)),
            "first_seen_at": row.first_seen_at,
            "last_seen_at": row.last_seen_at,
        }
        for row in rows
    ]


@router.get("/opportunities/page")
def opportunities_page(
    stage: str | None = None,
    include_dormant: bool = False,
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    q: str | None = Query(default=None, max_length=200),
    research_status: str | None = Query(default=None, max_length=30),
    starred: bool | None = None,
    cursor: str | None = Query(default=None, max_length=1000),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Opportunity).where(Opportunity.score >= min_score)
    if stage:
        stmt = stmt.where(Opportunity.stage == stage)
    elif not include_dormant:
        stmt = stmt.where(Opportunity.stage != "DORMANT")
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Opportunity.title.ilike(pattern), Opportunity.summary.ilike(pattern)))
    if research_status is not None or starred is not None:
        stmt = stmt.outerjoin(OpportunityResearch, OpportunityResearch.opportunity_id == Opportunity.id)
        if research_status is not None:
            normalized = research_status.strip().upper()
            if normalized == "NEW":
                stmt = stmt.where(or_(OpportunityResearch.status == "NEW", OpportunityResearch.status.is_(None)))
            else:
                stmt = stmt.where(OpportunityResearch.status == normalized)
        if starred is True:
            stmt = stmt.where(OpportunityResearch.starred.is_(True))
        elif starred is False:
            stmt = stmt.where(or_(OpportunityResearch.starred.is_(False), OpportunityResearch.starred.is_(None)))
    try:
        decoded = decode_cursor(cursor)
        if decoded:
            score = float(decoded["score"])
            seen = datetime.fromisoformat(decoded["last_seen_at"])
            row_id = int(decoded["id"])
            stmt = stmt.where(or_(
                Opportunity.score < score,
                and_(Opportunity.score == score, Opportunity.last_seen_at < seen),
                and_(Opportunity.score == score, Opportunity.last_seen_at == seen, Opportunity.id < row_id),
            ))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="invalid pagination cursor") from exc
    rows = db.scalars(
        stmt.order_by(Opportunity.score.desc(), Opportunity.last_seen_at.desc(), Opportunity.id.desc()).limit(limit + 1)
    ).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    state_by_id = research_state_map(db, [row.id for row in rows])
    items = [{
        "id": row.id,
        "opportunity_key": row.opportunity_key,
        "title": row.title,
        "stage": row.stage,
        "score": row.score,
        "risk_score": row.risk_score,
        "evidence_count": row.evidence_count,
        "related_keyword_count": row.related_keyword_count,
        "summary": row.summary,
        "analysis_status": row.analysis_status,
        "research": serialize_research_state(state_by_id.get(row.id)),
        "first_seen_at": row.first_seen_at,
        "last_seen_at": row.last_seen_at,
    } for row in rows]
    next_cursor = opportunity_cursor(rows[-1].score, rows[-1].last_seen_at, rows[-1].id) if has_more and rows else None
    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


@router.get("/opportunities/{opportunity_id}")
def opportunity(
    opportunity_id: int,
    evidence_limit: int = Query(default=50, ge=1, le=100),
    evidence_text_chars: int = Query(default=2000, ge=0, le=5000),
    db: Session = Depends(get_db),
):
    try:
        return opportunity_detail(
            db,
            opportunity_id,
            evidence_limit=evidence_limit,
            evidence_text_chars=evidence_text_chars,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return dashboard_summary(db)


@router.patch("/sources/{source_id}/preference")
def update_source_preference(
    source_id: str,
    payload: SourcePreferencePatch,
    db: Session = Depends(get_db),
    _auth=Depends(require_admin_auth),
):
    try:
        connector = _registry().get(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    row = set_source_preference(db, source_id, enabled=payload.enabled, note=payload.note)
    if not payload.enabled:
        # Existing tasks are made inactive immediately; a later sync can recreate them if re-enabled.
        from app.db.models import ProbeTask
        tasks = db.scalars(select(ProbeTask).where(ProbeTask.source_id == source_id, ProbeTask.active.is_(True))).all()
        for task in tasks:
            task.active = False
            task.updated_at = utc_now()
    db.commit()
    return {
        "source_id": source_id,
        "descriptor_enabled": connector.descriptor.enabled,
        "runtime_enabled": row.enabled and connector.descriptor.enabled,
        "note": row.note,
        "updated_at": row.updated_at,
    }
