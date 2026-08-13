from __future__ import annotations

from datetime import timedelta
from collections.abc import Callable

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.db.models import Opportunity
from app.domain.citations import validate_analysis_citations
from app.services.opportunities import build_analysis_input_for_opportunity
from app.services.opportunity_analysis import OpportunityAnalyzer, build_opportunity_analyzer

ANALYSIS_STALE_MINUTES = 10
MAX_RETRY_MINUTES = 24 * 60


def _recover_stale_analysis(db: Session, *, now) -> int:
    cutoff = now - timedelta(minutes=ANALYSIS_STALE_MINUTES)
    rows = db.scalars(
        select(Opportunity).where(
            Opportunity.analysis_status == "ANALYZING",
            Opportunity.analysis_last_attempt_at.is_not(None),
            Opportunity.analysis_last_attempt_at < cutoff,
        )
    ).all()
    for row in rows:
        row.analysis_status = "DEGRADED"
        row.analysis_next_retry_at = now
        row.analysis_error = "analysis worker interrupted or exceeded stale-run threshold"
    if rows:
        db.commit()
    return len(rows)


def _claim_analysis(db: Session, opportunity_id: int, *, now) -> bool:
    result = db.execute(
        update(Opportunity)
        .where(
            Opportunity.id == opportunity_id,
            Opportunity.analysis_status.in_(["PENDING", "DEGRADED"]),
            or_(
                Opportunity.analysis_next_retry_at.is_(None),
                Opportunity.analysis_next_retry_at <= now,
            ),
        )
        .values(
            analysis_status="ANALYZING",
            analysis_last_attempt_at=now,
            analysis_next_retry_at=None,
            analysis_attempt_count=Opportunity.analysis_attempt_count + 1,
        )
        .execution_options(synchronize_session=False)
    )
    db.commit()
    return result.rowcount == 1


def _retry_minutes(attempt_count: int) -> int:
    base = max(1, settings.analysis_retry_base_minutes)
    return min(MAX_RETRY_MINUTES, base * (2 ** min(max(0, attempt_count - 1), 6)))


def run_pending_opportunity_analysis(
    db: Session,
    *,
    limit: int | None = None,
    analyzer: OpportunityAnalyzer | None = None,
    progress_callback: Callable[[], None] | None = None,
) -> dict:
    if settings.analysis_provider == "heuristic" and analyzer is None:
        return {"enabled": False, "due": 0, "claimed": 0, "executed": 0, "recovered_stale": 0, "results": []}

    now = utc_now()
    recovered = _recover_stale_analysis(db, now=now)
    batch_limit = max(1, min(100, limit or settings.analysis_batch_limit))
    opportunity_ids = db.scalars(
        select(Opportunity.id)
        .where(
            Opportunity.stage != "DORMANT",
            Opportunity.analysis_status.in_(["PENDING", "DEGRADED"]),
            or_(
                Opportunity.analysis_next_retry_at.is_(None),
                Opportunity.analysis_next_retry_at <= now,
            ),
        )
        .order_by(Opportunity.score.desc(), Opportunity.analysis_next_retry_at, Opportunity.id)
        .limit(batch_limit)
    ).all()
    # Finish the scheduler read transaction before any external request.
    db.commit()

    owns_analyzer = analyzer is None
    active_analyzer = analyzer or build_opportunity_analyzer()
    results: list[dict] = []
    claimed = 0
    try:
        for opportunity_id in opportunity_ids:
            claim_time = utc_now()
            if not _claim_analysis(db, opportunity_id, now=claim_time):
                continue
            claimed += 1
            opportunity = db.get(Opportunity, opportunity_id)
            if opportunity is None:
                continue
            expected_signature = opportunity.analysis_signature
            try:
                payload = build_analysis_input_for_opportunity(db, opportunity_id)
                # Release the read transaction before the network call.
                db.commit()
                result = active_analyzer.analyze(payload)
                citations = validate_analysis_citations(
                    result.citations,
                    allowed_evidence_ids={row["evidence_id"] for row in payload.evidence},
                )

                current = db.get(Opportunity, opportunity_id)
                if current is None:
                    db.rollback()
                    continue
                if current.analysis_signature != expected_signature:
                    current.analysis_status = "PENDING"
                    current.analysis_next_retry_at = utc_now()
                    current.analysis_error = "discarded stale analysis result because evidence changed during analysis"
                    db.commit()
                    results.append({"opportunity_id": opportunity_id, "status": "STALE_DISCARDED"})
                    continue

                current.summary = result.summary
                current.target_user = result.target_user
                current.business_model = result.business_model
                current.monetization = result.monetization
                current.risk_notes = result.risk_notes
                current.analysis_provider = result.provider
                current.analysis_citations = citations
                current.analysis_conflict = dict(result.conflict_report or {})
                current.analysis_status = "READY"
                current.analysis_error = None
                current.analysis_next_retry_at = None
                current.analyzed_at = utc_now()
                db.commit()
                results.append({"opportunity_id": opportunity_id, "status": "READY", "provider": result.provider})
            except Exception as exc:
                db.rollback()
                current = db.get(Opportunity, opportunity_id)
                if current is None:
                    continue
                failed_at = utc_now()
                current.analysis_status = "DEGRADED"
                current.analysis_error = str(exc)[:20_000]
                current.analysis_next_retry_at = failed_at + timedelta(minutes=_retry_minutes(current.analysis_attempt_count))
                db.commit()
                results.append(
                    {
                        "opportunity_id": opportunity_id,
                        "status": "DEGRADED",
                        "attempt_count": current.analysis_attempt_count,
                        "next_retry_at": current.analysis_next_retry_at,
                        "error": current.analysis_error,
                    }
                )
            finally:
                if progress_callback is not None:
                    progress_callback()
    finally:
        if owns_analyzer:
            active_analyzer.close()

    return {
        "enabled": True,
        "due": len(opportunity_ids),
        "claimed": claimed,
        "executed": len(results),
        "recovered_stale": recovered,
        "results": results,
    }
