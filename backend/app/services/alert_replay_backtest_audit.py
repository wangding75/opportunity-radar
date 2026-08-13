"""Auditable temporal and idempotency checks for alerts and replays."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc_naive, utc_now
from app.db.models import (
    AlertEvaluationQueue,
    AlertEvent,
    AlertRule,
    EmailDeliveryRecord,
    Keyword,
    KeywordBurstRecord,
    Opportunity,
    OpportunityScoreSnapshot,
    RiskEscalationRecord,
    ScoreJumpRecord,
    ToolProductEntity,
    WebhookDeliveryRecord,
    WebhookEndpoint,
)
from app.domain.alert_lifecycle import VALID_ALERT_EVENT_STATUSES
from app.domain.keyword_burst import KeywordBurstPolicy, burst_windows
from app.services.scoring import backtest_summary, replay_snapshot


ALERT_REPLAY_BACKTEST_CONTRACT_VERSION = "alert-replay-backtest-v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _violation(violations: list[dict], rule: str, **details: object) -> None:
    violations.append({"rule": rule, **details})


def _valid_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _at_or_after(left: datetime | None, right: datetime | None) -> bool:
    return left is not None and right is not None and as_utc_naive(left) >= as_utc_naive(right)


def _audit_replay_boundaries(db: Session, snapshots: list[OpportunityScoreSnapshot], violations: list[dict]) -> int:
    """Check first/last persisted boundaries without writing replay records."""

    grouped: dict[int, list[OpportunityScoreSnapshot]] = defaultdict(list)
    for row in snapshots:
        grouped[row.opportunity_id].append(row)
    checks = 0
    for opportunity_id, rows in grouped.items():
        rows.sort(key=lambda row: (row.calculated_at, row.id))
        for boundary in (rows[0], rows[-1]):
            result = replay_snapshot(db, opportunity_id, as_of=boundary.calculated_at)
            checks += 1
            expected = max(
                (row for row in rows if row.calculated_at <= boundary.calculated_at),
                key=lambda row: (row.calculated_at, row.id),
            )
            if result is None:
                _violation(violations, "score_replay_boundary_has_snapshot", opportunity_id=opportunity_id)
                continue
            if result.get("replay_mode") != "persisted_snapshot":
                _violation(violations, "score_replay_is_persisted_snapshot", opportunity_id=opportunity_id)
            if result.get("calculated_at") != expected.calculated_at or result.get("score") != expected.score:
                _violation(violations, "score_replay_respects_as_of", opportunity_id=opportunity_id, as_of=boundary.calculated_at.isoformat())
            if as_utc_naive(result["calculated_at"]) > as_utc_naive(boundary.calculated_at):
                _violation(violations, "score_replay_has_no_future_state", opportunity_id=opportunity_id)
    return checks


def audit_alert_replay_backtest(db: Session) -> dict:
    """Audit persisted alert state and time-bounded replay/backtest behavior."""

    violations: list[dict] = []
    now = utc_now()
    opportunities = db.scalars(select(Opportunity).order_by(Opportunity.id)).all()
    opportunity_ids = {row.id for row in opportunities}
    keywords = db.scalars(select(Keyword).order_by(Keyword.id)).all()
    keyword_ids = {row.id for row in keywords}
    rules = db.scalars(select(AlertRule).order_by(AlertRule.id)).all()
    rule_by_id = {row.id: row for row in rules}
    entity_ids = {row.id for row in db.scalars(select(ToolProductEntity)).all()}

    for row in rules:
        if not row.name or not row.name.strip():
            _violation(violations, "alert_rule_name_present", rule_id=row.id)
        if not _valid_number(row.min_score) or not 0 <= float(row.min_score) <= 100:
            _violation(violations, "alert_rule_min_score_range", rule_id=row.id)
        if not _valid_number(row.max_risk_score) or not 0 <= float(row.max_risk_score) <= 100:
            _violation(violations, "alert_rule_max_risk_range", rule_id=row.id)
        if row.min_evidence_count < 0 or row.cooldown_minutes < 0:
            _violation(violations, "alert_rule_bounds", rule_id=row.id)
        if row.last_evaluated_at is not None and not _at_or_after(row.last_evaluated_at, row.created_at):
            _violation(violations, "alert_rule_evaluation_after_creation", rule_id=row.id)

    events = db.scalars(select(AlertEvent).order_by(AlertEvent.id)).all()
    event_by_id = {row.id: row for row in events}
    for key, count in Counter(row.event_key for row in events).items():
        if count > 1:
            _violation(violations, "alert_event_key_idempotency", event_key=key, count=count)
    for row in events:
        if row.alert_rule_id not in rule_by_id:
            _violation(violations, "alert_event_references_rule", event_id=row.id)
        if not _valid_sha(row.event_key):
            _violation(violations, "alert_event_key_format", event_id=row.id)
        if row.status not in VALID_ALERT_EVENT_STATUSES:
            _violation(violations, "alert_event_status_valid", event_id=row.id)
        if row.priority < 1 or row.priority > 5:
            _violation(violations, "alert_event_priority_range", event_id=row.id)
        if not _valid_number(row.score) or not 0 <= float(row.score) <= 100:
            _violation(violations, "alert_event_score_range", event_id=row.id)
        if not _valid_number(row.risk_score) or not 0 <= float(row.risk_score) <= 100:
            _violation(violations, "alert_event_risk_range", event_id=row.id)
        if row.created_at is None:
            _violation(violations, "alert_event_created_at_present", event_id=row.id)
        targets = int(row.opportunity_id is not None) + int(row.keyword_id is not None) + int(row.tool_product_entity_id is not None)
        if targets < 1:
            _violation(violations, "alert_event_has_target", event_id=row.id)
        if row.opportunity_id is not None and row.opportunity_id not in opportunity_ids:
            _violation(violations, "alert_event_opportunity_exists", event_id=row.id)
        if row.keyword_id is not None and row.keyword_id not in keyword_ids:
            _violation(violations, "alert_event_keyword_exists", event_id=row.id)
        if row.tool_product_entity_id is not None and row.tool_product_entity_id not in entity_ids:
            _violation(violations, "alert_event_tool_entity_exists", event_id=row.id)
        for changed_at in (row.acknowledged_at, row.dismissed_at, row.resolved_at):
            if changed_at is not None and not _at_or_after(changed_at, row.created_at):
                _violation(violations, "alert_lifecycle_time_after_creation", event_id=row.id)
        required_time = {"ACKNOWLEDGED": row.acknowledged_at, "DISMISSED": row.dismissed_at, "RESOLVED": row.resolved_at}.get(row.status)
        if row.status != "NEW" and required_time is None:
            _violation(violations, "alert_status_has_lifecycle_timestamp", event_id=row.id)

    queues = db.scalars(select(AlertEvaluationQueue).order_by(AlertEvaluationQueue.queued_at, AlertEvaluationQueue.opportunity_id)).all()
    for row in queues:
        if row.opportunity_id not in opportunity_ids:
            _violation(violations, "alert_queue_opportunity_exists", opportunity_id=row.opportunity_id)
        if not row.reason or not row.reason.strip() or row.revision < 1 or row.attempt_count < 0:
            _violation(violations, "alert_queue_state_bounds", opportunity_id=row.opportunity_id)
        if row.claim_until is not None and not _at_or_after(row.claim_until, row.queued_at):
            _violation(violations, "alert_queue_claim_after_queue", opportunity_id=row.opportunity_id)
        if row.next_retry_at is not None and not _at_or_after(row.next_retry_at, row.queued_at):
            _violation(violations, "alert_queue_retry_after_queue", opportunity_id=row.opportunity_id)

    emails = db.scalars(select(EmailDeliveryRecord).order_by(EmailDeliveryRecord.id)).all()
    email_statuses = {"QUEUED", "CLAIMED", "RETRY_WAIT", "ACCEPTED", "SENT", "PERMANENT_FAILURE", "SUPPRESSED", "INVALID"}
    for row in emails:
        event = event_by_id.get(row.alert_event_id)
        if event is None:
            _violation(violations, "email_delivery_alert_exists", delivery_id=row.id)
        if not row.message_id or not row.idempotency_key or not _valid_sha(row.input_signature):
            _violation(violations, "email_delivery_identity_present", delivery_id=row.id)
        if row.status not in email_statuses or row.attempt_count < 0:
            _violation(violations, "email_delivery_state_valid", delivery_id=row.id)
        if event is not None and not _at_or_after(row.created_at, event.created_at):
            _violation(violations, "email_delivery_created_after_alert", delivery_id=row.id)
        if row.sent_at is not None and not _at_or_after(row.sent_at, row.created_at):
            _violation(violations, "email_delivery_sent_after_creation", delivery_id=row.id)

    endpoint_ids = {row.id for row in db.scalars(select(WebhookEndpoint)).all()}
    webhooks = db.scalars(select(WebhookDeliveryRecord).order_by(WebhookDeliveryRecord.id)).all()
    webhook_statuses = {"QUEUED", "CLAIMED", "RETRY_WAIT", "SENT", "PERMANENT_FAILURE", "SUPPRESSED", "INVALID"}
    for row in webhooks:
        event = event_by_id.get(row.alert_event_id)
        if event is None or row.endpoint_id not in endpoint_ids:
            _violation(violations, "webhook_delivery_references_existing_rows", delivery_id=row.id)
        if not row.delivery_id or not row.event_id or not _valid_sha(row.input_signature):
            _violation(violations, "webhook_delivery_identity_present", delivery_id=row.id)
        if row.status not in webhook_statuses or row.attempt_count < 0:
            _violation(violations, "webhook_delivery_state_valid", delivery_id=row.id)
        if event is not None and not _at_or_after(row.created_at, event.created_at):
            _violation(violations, "webhook_delivery_created_after_alert", delivery_id=row.id)
        if row.sent_at is not None and not _at_or_after(row.sent_at, row.created_at):
            _violation(violations, "webhook_delivery_sent_after_creation", delivery_id=row.id)

    snapshots = db.scalars(select(OpportunityScoreSnapshot).order_by(OpportunityScoreSnapshot.opportunity_id, OpportunityScoreSnapshot.calculated_at, OpportunityScoreSnapshot.id)).all()
    snapshot_by_key = {(row.opportunity_id, row.input_signature): row for row in snapshots}
    for row in snapshots:
        if row.calculated_at is None:
            _violation(violations, "score_snapshot_calculated_at_present", snapshot_id=row.id)
        elif as_utc_naive(row.calculated_at) > now:
            _violation(violations, "score_snapshot_not_in_future", snapshot_id=row.id)
    replay_checks = _audit_replay_boundaries(db, snapshots, violations)

    score_jumps = db.scalars(select(ScoreJumpRecord).order_by(ScoreJumpRecord.id)).all()
    for row in score_jumps:
        current = snapshot_by_key.get((row.opportunity_id, row.current_snapshot_signature))
        previous = snapshot_by_key.get((row.opportunity_id, row.previous_snapshot_signature)) if row.previous_snapshot_signature else None
        if not _valid_sha(row.input_signature) or not _valid_sha(row.current_snapshot_signature):
            _violation(violations, "score_jump_signature_format", record_id=row.id)
        if current is None:
            _violation(violations, "score_jump_current_snapshot_exists", record_id=row.id)
        elif row.current_calculated_at != current.calculated_at:
            _violation(violations, "score_jump_current_timestamp_matches_snapshot", record_id=row.id)
        if row.previous_snapshot_signature and previous is None:
            _violation(violations, "score_jump_previous_snapshot_exists", record_id=row.id)
        if previous is not None and row.previous_calculated_at != previous.calculated_at:
            _violation(violations, "score_jump_previous_timestamp_matches_snapshot", record_id=row.id)
        if previous is not None and not _at_or_after(row.current_calculated_at, row.previous_calculated_at):
            _violation(violations, "score_jump_time_order", record_id=row.id)
        if row.evaluated_at is not None and not _at_or_after(row.evaluated_at, row.current_calculated_at):
            _violation(violations, "score_jump_evaluated_after_current", record_id=row.id)
        if row.alert_event_id is not None and row.alert_event_id not in event_by_id:
            _violation(violations, "score_jump_alert_exists", record_id=row.id)

    risk_records = db.scalars(select(RiskEscalationRecord).order_by(RiskEscalationRecord.id)).all()
    for row in risk_records:
        current_rows = [item for item in snapshots if item.opportunity_id == row.opportunity_id and item.calculated_at == row.current_calculated_at]
        if not _valid_sha(row.input_signature):
            _violation(violations, "risk_record_signature_format", record_id=row.id)
        if not current_rows:
            _violation(violations, "risk_record_current_snapshot_exists", record_id=row.id)
        if row.previous_calculated_at is not None and not _at_or_after(row.current_calculated_at, row.previous_calculated_at):
            _violation(violations, "risk_record_time_order", record_id=row.id)
        if row.evaluated_at is not None and not _at_or_after(row.evaluated_at, row.current_calculated_at):
            _violation(violations, "risk_record_evaluated_after_current", record_id=row.id)
        if row.alert_event_id is not None and row.alert_event_id not in event_by_id:
            _violation(violations, "risk_record_alert_exists", record_id=row.id)

    burst_records = db.scalars(select(KeywordBurstRecord).order_by(KeywordBurstRecord.id)).all()
    for row in burst_records:
        if row.keyword_id not in keyword_ids or not _valid_sha(row.input_signature):
            _violation(violations, "keyword_burst_identity_valid", record_id=row.id)
        try:
            policy = KeywordBurstPolicy.model_validate(row.policy or {})
            expected = burst_windows(row.current_end, policy)
            actual = (row.current_start, row.current_end, row.baseline_start, row.baseline_end)
            if expected != actual:
                _violation(violations, "keyword_burst_window_math", record_id=row.id)
        except (TypeError, ValueError):
            _violation(violations, "keyword_burst_policy_valid", record_id=row.id)
        if row.absolute_delta != row.current_observations - row.baseline_observations:
            _violation(violations, "keyword_burst_delta_math", record_id=row.id)
        if row.alert_event_id is not None and row.alert_event_id not in event_by_id:
            _violation(violations, "keyword_burst_alert_exists", record_id=row.id)

    backtest = backtest_summary(db, lookback_days=90, threshold=60.0)
    for field in ("candidate_signals", "immature_signals", "persisted_signals"):
        if not isinstance(backtest.get(field), int) or backtest[field] < 0:
            _violation(violations, "backtest_count_bounds", field=field)
    if backtest.get("persisted_signals", 0) > backtest.get("candidate_signals", 0):
        _violation(violations, "backtest_persisted_not_above_candidates")
    if backtest.get("candidate_signals", 0) and backtest.get("persistence_rate") != round(backtest["persisted_signals"] / backtest["candidate_signals"], 4):
        _violation(violations, "backtest_persistence_rate_math")
    if not backtest.get("candidate_signals", 0) and backtest.get("persistence_rate") is not None:
        _violation(violations, "backtest_empty_rate_is_null")

    return {
        "audit_id": "opportunity-radar-alert-replay-backtest",
        "contract_version": ALERT_REPLAY_BACKTEST_CONTRACT_VERSION,
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
        "summary": {
            "alert_rules": len(rules),
            "alert_events": len(events),
            "alert_evaluation_queue": len(queues),
            "email_deliveries": len(emails),
            "webhook_deliveries": len(webhooks),
            "score_snapshots": len(snapshots),
            "score_jump_records": len(score_jumps),
            "risk_escalation_records": len(risk_records),
            "keyword_burst_records": len(burst_records),
            "replay_boundary_checks": replay_checks,
            "backtest_candidate_signals": backtest["candidate_signals"],
            "backtest_immature_signals": backtest["immature_signals"],
            "real_data_collected": 0,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }
