from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import timedelta
from collections.abc import Callable

from sqlalchemy import delete, desc, or_, select, update
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.services.locks import acquire_alert_evaluation_lock
from app.db.models import AlertEvaluationQueue, AlertEvent, AlertRule, Keyword, Opportunity, OpportunityKeyword
from app.domain.alert_lifecycle import derive_alert_priority, validate_alert_status_transition
from app.domain.high_signal import HighSignalTriggerPolicy
from app.services.high_signal import evaluate_opportunity_high_signal

ALERT_CLAIM_MINUTES = 5
MAX_ALERT_RETRY_MINUTES = 12 * 60
HIGH_SIGNAL_RULE_NAME = "HIGH_SIGNAL_IMMEDIATE"


def _alert_retry_minutes(attempt_count: int) -> int:
    return min(MAX_ALERT_RETRY_MINUTES, 5 * (2 ** min(max(0, attempt_count - 1), 7)))


def enqueue_alert_evaluations(db: Session, opportunity_ids: set[int], *, reason: str = "OPPORTUNITY_CHANGED") -> int:
    if not opportunity_ids:
        return 0
    now = utc_now()
    existing = {
        row.opportunity_id: row
        for row in db.scalars(select(AlertEvaluationQueue).where(AlertEvaluationQueue.opportunity_id.in_(opportunity_ids))).all()
    }
    created = 0
    for opportunity_id in opportunity_ids:
        row = existing.get(opportunity_id)
        if row is None:
            db.add(AlertEvaluationQueue(
                opportunity_id=opportunity_id,
                reason=reason,
                queued_at=now,
                revision=1,
                next_retry_at=now,
            ))
            created += 1
        else:
            # Revision prevents a worker from deleting a newer evaluation request
            # that arrived while the older revision was being processed.
            row.revision = int(row.revision or 0) + 1
            row.reason = reason
            row.queued_at = now
            # A new opportunity revision is fresh work. It must not inherit a
            # poison/backoff history from an older signal revision.
            row.attempt_count = 0
            row.next_retry_at = now
            row.last_error = None
    db.flush()
    return created


def _keyword_map(db: Session, opportunity_ids: set[int]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = defaultdict(list)
    if not opportunity_ids:
        return result
    rows = db.execute(
        select(OpportunityKeyword.opportunity_id, Keyword.display_name)
        .join(Keyword, OpportunityKeyword.keyword_id == Keyword.id)
        .where(OpportunityKeyword.opportunity_id.in_(opportunity_ids))
    ).all()
    for opportunity_id, name in rows:
        result[opportunity_id].append(name)
    return result


def _matches(rule: AlertRule, opportunity: Opportunity, keywords: list[str]) -> bool:
    if opportunity.stage == "DORMANT":
        return False
    if opportunity.score < rule.min_score or opportunity.risk_score > rule.max_risk_score:
        return False
    if opportunity.evidence_count < rule.min_evidence_count:
        return False
    stages = {str(v).upper() for v in (rule.stages or []) if str(v).strip()}
    if stages and opportunity.stage.upper() not in stages:
        return False
    required = [str(v).strip().lower() for v in (rule.keyword_contains or []) if str(v).strip()]
    if required:
        haystack = " ".join([opportunity.title, *keywords]).lower()
        if not any(term in haystack for term in required):
            return False
    return True


def _ensure_high_signal_rule(db: Session, *, now) -> AlertRule:
    rule = db.scalar(select(AlertRule).where(AlertRule.name == HIGH_SIGNAL_RULE_NAME))
    if rule is None:
        rule = AlertRule(
            name=HIGH_SIGNAL_RULE_NAME,
            enabled=True,
            min_score=80.0,
            max_risk_score=40.0,
            min_evidence_count=3,
            stages=[],
            keyword_contains=[],
            cooldown_minutes=1_440,
            created_at=now,
            updated_at=now,
        )
        db.add(rule)
        db.flush()
    return rule


def _evaluate_high_signal_alerts(
    db: Session,
    *,
    opportunities: list[Opportunity],
    rule: AlertRule,
    now,
    policy: HighSignalTriggerPolicy,
    existing_events: list[AlertEvent],
) -> dict:
    by_key = {event.event_key for event in existing_events if event.alert_rule_id == rule.id}
    latest_by_opportunity: dict[int, AlertEvent] = {}
    for event in existing_events:
        if event.alert_rule_id != rule.id:
            continue
        previous = latest_by_opportunity.get(event.opportunity_id)
        if previous is None or event.created_at > previous.created_at:
            latest_by_opportunity[event.opportunity_id] = event
    matched = 0
    created = 0
    suppressed = 0
    evaluations = []
    cooldown = timedelta(minutes=policy.cooldown_minutes)
    for opportunity in opportunities:
        evaluation = evaluate_opportunity_high_signal(opportunity, now=now, policy=policy)
        evaluations.append(evaluation)
        if not evaluation.eligible:
            continue
        matched += 1
        if evaluation.dedupe_key in by_key:
            suppressed += 1
            continue
        latest = latest_by_opportunity.get(opportunity.id)
        if latest and latest.created_at > now - cooldown:
            suppressed += 1
            continue
        event = AlertEvent(
            alert_rule_id=rule.id,
            opportunity_id=opportunity.id,
            event_key=evaluation.dedupe_key,
            status="NEW",
            title=f"High signal: {opportunity.title}",
            message=(
                f"High-signal trigger for {opportunity.opportunity_key}; "
                f"reasons: {'; '.join(evaluation.trigger_reasons)}; "
                f"dedupe_key={evaluation.dedupe_key}"
            )[:10_000],
            score=opportunity.score,
            risk_score=opportunity.risk_score,
            priority=derive_alert_priority(score=opportunity.score, risk_score=opportunity.risk_score, evidence_count=opportunity.evidence_count, high_signal=True),
            created_at=now,
        )
        db.add(event)
        by_key.add(evaluation.dedupe_key)
        latest_by_opportunity[opportunity.id] = event
        created += 1
    rule.last_evaluated_at = now
    rule.updated_at = now
    db.flush()
    return {"matched": matched, "created": created, "suppressed": suppressed, "evaluations": evaluations}


def trigger_high_signal_alerts(
    db: Session,
    *,
    opportunity_ids: set[int] | None = None,
    now=None,
    policy: HighSignalTriggerPolicy | None = None,
) -> dict:
    """Materialize eligible high-signal opportunities as idempotent events."""

    acquire_alert_evaluation_lock(db)
    policy = policy or HighSignalTriggerPolicy()
    now = now or utc_now()
    rule = _ensure_high_signal_rule(db, now=now)
    stmt = select(Opportunity).where(Opportunity.stage != "DORMANT")
    if opportunity_ids is not None:
        if not opportunity_ids:
            return {"rule": HIGH_SIGNAL_RULE_NAME, "opportunities": 0, "matched": 0, "created": 0, "suppressed": 0}
        stmt = stmt.where(Opportunity.id.in_(opportunity_ids))
    opportunities = db.scalars(stmt.order_by(Opportunity.id)).all()
    existing_events = db.scalars(select(AlertEvent).where(AlertEvent.alert_rule_id == rule.id)).all()
    result = _evaluate_high_signal_alerts(
        db,
        opportunities=opportunities,
        rule=rule,
        now=now,
        policy=policy,
        existing_events=existing_events,
    )
    result.pop("evaluations", None)
    return {"rule": HIGH_SIGNAL_RULE_NAME, "opportunities": len(opportunities), **result}


def evaluate_alert_rules(db: Session, *, opportunity_ids: set[int] | None = None) -> dict:
    acquire_alert_evaluation_lock(db)
    now = utc_now()
    rules = db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True)).order_by(AlertRule.id)).all()
    stmt = select(Opportunity).where(Opportunity.stage != "DORMANT")
    if opportunity_ids is not None:
        if not opportunity_ids:
            return {"rules": len(rules), "opportunities": 0, "matched": 0, "created": 0}
        stmt = stmt.where(Opportunity.id.in_(opportunity_ids))
    opportunities = db.scalars(stmt).all()
    high_signal_rule = _ensure_high_signal_rule(db, now=now)
    rules = db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True)).order_by(AlertRule.id)).all()
    opp_ids = {row.id for row in opportunities}
    keywords = _keyword_map(db, opp_ids)

    existing_events = db.scalars(
        select(AlertEvent).where(AlertEvent.opportunity_id.in_(opp_ids))
    ).all() if opp_ids else []
    event_keys = {row.event_key for row in existing_events}
    latest_by_pair: dict[tuple[int, int], AlertEvent] = {}
    for event in existing_events:
        key = (event.alert_rule_id, event.opportunity_id)
        current = latest_by_pair.get(key)
        if current is None or event.created_at > current.created_at:
            latest_by_pair[key] = event

    created = 0
    matched = 0
    for rule in rules:
        if rule.id == high_signal_rule.id:
            continue
        for opportunity in opportunities:
            if not _matches(rule, opportunity, keywords.get(opportunity.id, [])):
                continue
            matched += 1
            signature = opportunity.analysis_signature or f"{opportunity.updated_at.isoformat()}:{opportunity.score}"
            key = hashlib.sha256(f"{rule.id}|{opportunity.id}|{signature}".encode()).hexdigest()
            if key in event_keys:
                continue
            latest = latest_by_pair.get((rule.id, opportunity.id))
            if latest and latest.created_at > now - timedelta(minutes=max(1, rule.cooldown_minutes)):
                continue
            event = AlertEvent(
                alert_rule_id=rule.id,
                opportunity_id=opportunity.id,
                event_key=key,
                status="NEW",
                title=f"{rule.name}: {opportunity.title}",
                message=(opportunity.summary or f"Opportunity score {opportunity.score}")[:10_000],
                score=opportunity.score,
                risk_score=opportunity.risk_score,
                priority=derive_alert_priority(score=opportunity.score, risk_score=opportunity.risk_score, evidence_count=opportunity.evidence_count),
                created_at=now,
            )
            db.add(event)
            event_keys.add(key)
            latest_by_pair[(rule.id, opportunity.id)] = event
            created += 1
        rule.last_evaluated_at = now
        rule.updated_at = now
    high_signal = _evaluate_high_signal_alerts(
        db,
        opportunities=opportunities,
        rule=high_signal_rule,
        now=now,
        policy=HighSignalTriggerPolicy(),
        existing_events=existing_events,
    )
    created += high_signal["created"]
    db.flush()
    return {
        "rules": len(rules),
        "opportunities": len(opportunities),
        "matched": matched + high_signal["matched"],
        "created": created,
        "high_signal_matched": high_signal["matched"],
        "high_signal_created": high_signal["created"],
        "high_signal_suppressed": high_signal["suppressed"],
    }


def _claim_alert_evaluation(db: Session, opportunity_id: int, revision: int, *, now) -> bool:
    result = db.execute(
        update(AlertEvaluationQueue)
        .where(
            AlertEvaluationQueue.opportunity_id == opportunity_id,
            AlertEvaluationQueue.revision == revision,
            or_(AlertEvaluationQueue.claim_until.is_(None), AlertEvaluationQueue.claim_until <= now),
            or_(AlertEvaluationQueue.next_retry_at.is_(None), AlertEvaluationQueue.next_retry_at <= now),
        )
        .values(claim_until=now + timedelta(minutes=ALERT_CLAIM_MINUTES))
        .execution_options(synchronize_session=False)
    )
    db.commit()
    return result.rowcount == 1


def run_pending_alert_evaluations(db: Session, *, limit: int = 200, progress_callback: Callable[[], None] | None = None) -> dict:
    now = utc_now()
    candidates = db.execute(
        select(AlertEvaluationQueue.opportunity_id, AlertEvaluationQueue.revision)
        .where(
            or_(AlertEvaluationQueue.claim_until.is_(None), AlertEvaluationQueue.claim_until <= now),
            or_(AlertEvaluationQueue.next_retry_at.is_(None), AlertEvaluationQueue.next_retry_at <= now),
        )
        .order_by(AlertEvaluationQueue.queued_at)
        .limit(max(1, min(2_000, limit)))
    ).all()
    db.commit()
    if not candidates:
        return {"queued": 0, "claimed": 0, "processed": 0, "created": 0, "failed": 0, "results": []}

    claimed = 0
    processed = 0
    created = 0
    failed = 0
    results: list[dict] = []
    for opportunity_id, revision in candidates:
        claim_time = utc_now()
        if not _claim_alert_evaluation(db, opportunity_id, revision, now=claim_time):
            continue
        claimed += 1
        try:
            result = evaluate_alert_rules(db, opportunity_ids={opportunity_id})
            deleted = db.execute(
                delete(AlertEvaluationQueue).where(
                    AlertEvaluationQueue.opportunity_id == opportunity_id,
                    AlertEvaluationQueue.revision == revision,
                )
            )
            if deleted.rowcount == 0:
                # A newer revision arrived while this one was evaluated. Keep it
                # queued and release the lease for immediate re-evaluation.
                db.execute(
                    update(AlertEvaluationQueue)
                    .where(AlertEvaluationQueue.opportunity_id == opportunity_id)
                    .values(claim_until=None, next_retry_at=utc_now(), last_error=None)
                )
            db.commit()
            processed += 1
            created += int(result["created"])
            results.append({"opportunity_id": opportunity_id, "revision": revision, "status": "SUCCEEDED", "created": result["created"]})
        except Exception as exc:
            db.rollback()
            row = db.get(AlertEvaluationQueue, opportunity_id)
            if row is not None:
                if row.revision == revision:
                    row.attempt_count += 1
                    row.last_error = str(exc)[:20_000]
                    row.next_retry_at = utc_now() + timedelta(minutes=_alert_retry_minutes(row.attempt_count))
                else:
                    # A newer signal supersedes the failed revision; retry the new
                    # revision immediately without inheriting the old backoff.
                    row.last_error = None
                    row.next_retry_at = utc_now()
                row.claim_until = None
                db.commit()
            failed += 1
            results.append({"opportunity_id": opportunity_id, "revision": revision, "status": "FAILED", "error": str(exc)[:20_000]})
        finally:
            if progress_callback is not None:
                progress_callback()

    return {
        "queued": len(candidates),
        "claimed": claimed,
        "processed": processed,
        "created": created,
        "failed": failed,
        "results": results,
    }


def set_alert_event_status(db: Session, event_id: int, status: str, *, actor: str = "local", now=None) -> AlertEvent:
    event = db.scalar(select(AlertEvent).where(AlertEvent.id == event_id).with_for_update())
    if event is None:
        raise KeyError(f"alert event not found: {event_id}")
    current, normalized = validate_alert_status_transition(event.status, status)
    if current == normalized:
        return event
    event.status = normalized
    changed_at = now or utc_now()
    changed_by = (str(actor or "local").strip() or "local")[:200]
    if normalized == "ACKNOWLEDGED":
        event.acknowledged_at = changed_at
        event.acknowledged_by = changed_by
    elif normalized == "DISMISSED":
        event.dismissed_at = changed_at
        event.dismissed_by = changed_by
    elif normalized == "RESOLVED":
        event.resolved_at = changed_at
        event.resolved_by = changed_by
    db.flush()
    return event
