from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_admin_auth, require_read_auth, require_write_auth
from app.core.time import utc_now
from app.db.models import AlertEvent, AlertRule, Opportunity, SeedKeyword
from app.db.session import get_db
from app.domain.schemas import AlertEventStatusPatch, AlertRuleCreate, AlertRulePatch, EmailDeliveryEnqueueRequest, EmailDeliveryProcessRequest, OpportunityResearchPatch, WatchKeywordCreate, WatchKeywordPatch, WebhookDeliveryEnqueueRequest, WebhookDeliveryProcessRequest
from app.services.auth import Principal
from app.services.alerts import enqueue_alert_evaluations, evaluate_alert_rules, run_pending_alert_evaluations, set_alert_event_status, trigger_high_signal_alerts
from app.services.keyword_burst_alerts import list_keyword_burst_records, materialize_keyword_burst_alerts
from app.services.keyword_burst_replay import replay_keyword_bursts
from app.services.tool_product_alerts import materialize_tool_product_alerts
from app.services.hiring_surge_alerts import list_hiring_surge_records, materialize_hiring_surge_alerts
from app.services.risk_escalation_alerts import list_risk_escalation_records, materialize_risk_escalations
from app.services.risk_escalation_replay import replay_risk_escalation
from app.services.cross_source_confirmations import list_cross_source_confirmations, materialize_cross_source_confirmations
from app.services.cross_source_alerts import materialize_cross_source_alerts
from app.services.email_delivery_queue import enqueue_alert_emails, list_email_delivery_records, process_email_delivery_queue
from app.services.webhook_delivery_queue import enqueue_alert_webhooks, list_webhook_delivery_records, process_webhook_delivery_queue
from app.services.webhook_endpoints import create_webhook_endpoint, delete_webhook_endpoint, list_webhook_endpoints, patch_webhook_endpoint, serialize_webhook_endpoint
from app.domain.webhook import WebhookEndpointCreate, WebhookEndpointPatch
from app.services.research import serialize_research_state, upsert_research_state
from app.services.watch_keywords import create_watch_keyword, patch_watch_keyword

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_read_auth)])


@router.get("/webhooks/endpoints")
def webhook_endpoints(db: Session = Depends(get_db)):
    return list_webhook_endpoints(db)


@router.post("/webhooks/endpoints")
def webhook_endpoint_create(
    payload: WebhookEndpointCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        row = create_webhook_endpoint(db, payload)
        db.commit()
        return serialize_webhook_endpoint(row)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409 if "already exists" in str(exc) else 422, detail=str(exc)) from exc


@router.patch("/webhooks/endpoints/{endpoint_id}")
def webhook_endpoint_patch(
    endpoint_id: int,
    payload: WebhookEndpointPatch,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        row = patch_webhook_endpoint(db, endpoint_id, payload)
        db.commit()
        return serialize_webhook_endpoint(row)
    except KeyError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409 if "already exists" in str(exc) else 422, detail=str(exc)) from exc


@router.delete("/webhooks/endpoints/{endpoint_id}")
def webhook_endpoint_delete(
    endpoint_id: int,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        delete_webhook_endpoint(db, endpoint_id)
        db.commit()
        return {"id": endpoint_id, "deleted": True}
    except KeyError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/opportunities/{opportunity_id}/research")
def update_opportunity_research(
    opportunity_id: int,
    payload: OpportunityResearchPatch,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_auth),
):
    try:
        state = upsert_research_state(
            db,
            opportunity_id,
            status=payload.status,
            starred=payload.starred,
            priority=payload.priority,
            notes=payload.notes,
            tags=payload.tags,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return {"opportunity_id": opportunity_id, **serialize_research_state(state)}


def _serialize_alert_rule(row: AlertRule) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "enabled": row.enabled,
        "min_score": row.min_score,
        "max_risk_score": row.max_risk_score,
        "min_evidence_count": row.min_evidence_count,
        "stages": row.stages or [],
        "keyword_contains": row.keyword_contains or [],
        "cooldown_minutes": row.cooldown_minutes,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "last_evaluated_at": row.last_evaluated_at,
    }


@router.get("/alerts/rules")
def alert_rules(db: Session = Depends(get_db)):
    return [_serialize_alert_rule(row) for row in db.scalars(select(AlertRule).order_by(AlertRule.id)).all()]


@router.post("/alerts/rules")
def create_alert_rule(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_auth),
):
    if db.scalar(select(AlertRule.id).where(func.lower(AlertRule.name) == payload.name.strip().lower())) is not None:
        raise HTTPException(status_code=409, detail="alert rule name already exists")
    now = utc_now()
    row = AlertRule(
        name=payload.name.strip(),
        enabled=payload.enabled,
        min_score=payload.min_score,
        max_risk_score=payload.max_risk_score,
        min_evidence_count=payload.min_evidence_count,
        stages=[str(v).strip().upper() for v in payload.stages if str(v).strip()],
        keyword_contains=[str(v).strip()[:100] for v in payload.keyword_contains if str(v).strip()],
        cooldown_minutes=payload.cooldown_minutes,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    active_ids = set(db.scalars(select(Opportunity.id).where(Opportunity.stage != "DORMANT")).all())
    enqueue_alert_evaluations(db, active_ids, reason="ALERT_RULE_CREATED")
    db.commit()
    db.refresh(row)
    return _serialize_alert_rule(row)


@router.patch("/alerts/rules/{rule_id}")
def patch_alert_rule(
    rule_id: int,
    payload: AlertRulePatch,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_auth),
):
    row = db.get(AlertRule, rule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="alert rule not found")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        name = str(values["name"]).strip()
        collision = db.scalar(select(AlertRule.id).where(func.lower(AlertRule.name) == name.lower(), AlertRule.id != rule_id))
        if collision is not None:
            raise HTTPException(status_code=409, detail="alert rule name already exists")
        row.name = name
    for field in ("enabled", "min_score", "max_risk_score", "min_evidence_count", "cooldown_minutes"):
        if field in values:
            setattr(row, field, values[field])
    if "stages" in values:
        row.stages = [str(v).strip().upper() for v in values["stages"] if str(v).strip()]
    if "keyword_contains" in values:
        row.keyword_contains = [str(v).strip()[:100] for v in values["keyword_contains"] if str(v).strip()]
    row.updated_at = utc_now()
    active_ids = set(db.scalars(select(Opportunity.id).where(Opportunity.stage != "DORMANT")).all())
    enqueue_alert_evaluations(db, active_ids, reason="ALERT_RULE_UPDATED")
    db.commit()
    return _serialize_alert_rule(row)


@router.post("/alerts/evaluate")
def alerts_evaluate(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    result = evaluate_alert_rules(db)
    db.commit()
    return result


@router.post("/alerts/high-signal/evaluate")
def high_signal_alerts_evaluate(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    result = trigger_high_signal_alerts(db)
    db.commit()
    return result


@router.post("/alerts/keyword-burst/evaluate")
def keyword_burst_alerts_evaluate(
    keyword_id: int | None = Query(default=None, ge=1),
    window_end: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    result = materialize_keyword_burst_alerts(
        db,
        keyword_ids={keyword_id} if keyword_id is not None else None,
        window_end=window_end,
        limit=limit,
    )
    db.commit()
    return result


@router.post("/alerts/tool-products/evaluate")
def tool_product_alerts_evaluate(
    entity_key: str | None = Query(default=None, max_length=68),
    limit: int = Query(default=500, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    result = materialize_tool_product_alerts(
        db,
        entity_keys={entity_key} if entity_key else None,
        limit=limit,
    )
    db.commit()
    return result


@router.get("/alerts/keyword-burst/records")
def keyword_burst_records(
    keyword_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_keyword_burst_records(db, keyword_id=keyword_id, status=status, limit=limit)


@router.post("/alerts/keyword-burst/replay")
def keyword_burst_replay(
    keyword_id: int = Query(ge=1),
    start_window_end: date = Query(...),
    end_window_end: date = Query(...),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        return replay_keyword_bursts(db, keyword_id=keyword_id, start_window_end=start_window_end, end_window_end=end_window_end)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/alerts/hiring/evaluate")
def hiring_surge_alerts_evaluate(
    keyword_id: int | None = Query(default=None, ge=1),
    window_end: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    result = materialize_hiring_surge_alerts(
        db,
        keyword_ids={keyword_id} if keyword_id is not None else None,
        window_end=window_end,
        limit=limit,
    )
    db.commit()
    return result


@router.get("/alerts/hiring/records")
def hiring_surge_records(
    keyword_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_hiring_surge_records(db, keyword_id=keyword_id, status=status, limit=limit)


@router.post("/alerts/cross-source/evaluate")
def cross_source_alerts_evaluate(
    opportunity_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    confirmation = materialize_cross_source_confirmations(
        db,
        opportunity_ids={opportunity_id} if opportunity_id is not None else None,
        limit=limit,
    )
    alerts = materialize_cross_source_alerts(
        db,
        opportunity_ids={opportunity_id} if opportunity_id is not None else None,
        limit=limit,
    )
    db.commit()
    return {"confirmation": confirmation, "alerts": alerts}


@router.get("/alerts/cross-source/records")
def cross_source_records(
    opportunity_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_cross_source_confirmations(db, opportunity_id=opportunity_id, status=status, limit=limit)


@router.post("/alerts/risk/evaluate")
def risk_escalations_evaluate(
    opportunity_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        result = materialize_risk_escalations(db, opportunity_ids={opportunity_id} if opportunity_id is not None else None, limit=limit)
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/alerts/risk/records")
def risk_escalation_records(
    opportunity_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_risk_escalation_records(db, opportunity_id=opportunity_id, status=status, limit=limit)


@router.post("/alerts/risk/replay")
def risk_escalation_replay(
    opportunity_id: int = Query(..., ge=1),
    as_of: datetime = Query(..., description="ISO-8601 timestamp; evaluates the latest two risk snapshots at or before this time"),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        result = replay_risk_escalation(db, opportunity_id, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="no risk snapshot exists at or before as_of")
    return result


@router.post("/alerts/run-pending")
def alerts_run_pending(
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    return run_pending_alert_evaluations(db, limit=limit)


@router.post("/alerts/email/enqueue")
def email_delivery_enqueue(
    payload: EmailDeliveryEnqueueRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        result = enqueue_alert_emails(
            db,
            alert_event_ids=set(payload.alert_event_ids) if payload.alert_event_ids is not None else None,
            recipients=payload.recipients,
            data_class=payload.data_class,
            limit=payload.limit,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/alerts/email/process")
def email_delivery_process(
    payload: EmailDeliveryProcessRequest | None = None,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        result = process_email_delivery_queue(db, limit=payload.limit if payload else 100)
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/alerts/email/records")
def email_delivery_records(
    alert_event_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_email_delivery_records(db, alert_event_id=alert_event_id, status=status, limit=limit)


@router.post("/alerts/webhooks/enqueue")
def webhook_delivery_enqueue(
    payload: WebhookDeliveryEnqueueRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        result = enqueue_alert_webhooks(
            db,
            alert_event_ids=set(payload.alert_event_ids) if payload.alert_event_ids is not None else None,
            endpoint_ids=set(payload.endpoint_ids) if payload.endpoint_ids is not None else None,
            data_class=payload.data_class,
            limit=payload.limit,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/alerts/webhooks/process")
def webhook_delivery_process(
    payload: WebhookDeliveryProcessRequest | None = None,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        return process_webhook_delivery_queue(db, limit=payload.limit if payload else 100)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/alerts/webhooks/records")
def webhook_delivery_records(
    alert_event_id: int | None = Query(default=None, ge=1),
    endpoint_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_webhook_delivery_records(db, alert_event_id=alert_event_id, endpoint_id=endpoint_id, status=status, limit=limit)


@router.get("/alerts/events")
def alert_events(
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(AlertEvent)
    if status:
        stmt = stmt.where(AlertEvent.status == status.strip().upper())
    rows = db.scalars(stmt.order_by(AlertEvent.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "alert_rule_id": row.alert_rule_id,
            "opportunity_id": row.opportunity_id,
            "keyword_id": row.keyword_id,
            "tool_product_entity_id": row.tool_product_entity_id,
            "event_key": row.event_key,
            "status": row.status,
            "priority": row.priority,
            "title": row.title,
            "message": row.message,
            "score": row.score,
            "risk_score": row.risk_score,
            "created_at": row.created_at,
            "acknowledged_at": row.acknowledged_at,
            "acknowledged_by": row.acknowledged_by,
            "dismissed_at": row.dismissed_at,
            "dismissed_by": row.dismissed_by,
            "resolved_at": row.resolved_at,
            "resolved_by": row.resolved_by,
        }
        for row in rows
    ]


@router.patch("/alerts/events/{event_id}")
def patch_alert_event(
    event_id: int,
    payload: AlertEventStatusPatch,
    request: Request,
    db: Session = Depends(get_db),
    _auth: Principal = Depends(require_write_auth),
):
    try:
        actor = getattr(_auth, "actor", None) or getattr(request.state, "actor", None) or "local"
        row = set_alert_event_status(db, event_id, payload.status, actor=actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return {
        "id": row.id,
        "status": row.status,
        "priority": row.priority,
        "acknowledged_at": row.acknowledged_at,
        "acknowledged_by": row.acknowledged_by,
        "dismissed_at": row.dismissed_at,
        "dismissed_by": row.dismissed_by,
        "resolved_at": row.resolved_at,
        "resolved_by": row.resolved_by,
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/watch-keywords")
def watch_keywords(db: Session = Depends(get_db)):
    rows = db.scalars(select(SeedKeyword).order_by(SeedKeyword.enabled.desc(), SeedKeyword.priority.desc(), SeedKeyword.updated_at.desc())).all()
    return [
        {
            "id": row.id,
            "keyword": row.display_name,
            "canonical": row.canonical,
            "enabled": row.enabled,
            "priority": row.priority,
            "notes": row.notes,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


@router.post("/watch-keywords")
def add_watch_keyword(
    payload: WatchKeywordCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_auth),
):
    try:
        row = create_watch_keyword(db, payload.keyword, priority=payload.priority, notes=payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    return {
        "id": row.id,
        "keyword": row.display_name,
        "canonical": row.canonical,
        "enabled": row.enabled,
        "priority": row.priority,
        "notes": row.notes,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.patch("/watch-keywords/{watch_id}")
def update_watch_keyword(
    watch_id: int,
    payload: WatchKeywordPatch,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_auth),
):
    values = payload.model_dump(exclude_unset=True)
    try:
        row = patch_watch_keyword(db, watch_id, **values)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return {
        "id": row.id,
        "keyword": row.display_name,
        "canonical": row.canonical,
        "enabled": row.enabled,
        "priority": row.priority,
        "notes": row.notes,
        "updated_at": row.updated_at,
    }
