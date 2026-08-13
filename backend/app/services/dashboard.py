from __future__ import annotations

from datetime import timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvent, CollectionRun, Keyword, NormalizedItem, Opportunity, OpportunityResearch, ProbeTask, RawObservation, SourceHealthState


def dashboard_summary(db: Session) -> dict:
    now = utc_now()
    total_observations = db.scalar(select(func.count(RawObservation.id))) or 0
    total_keywords = db.scalar(select(func.count(Keyword.id))) or 0
    total_opportunities = db.scalar(select(func.count(Opportunity.id)).where(Opportunity.stage != "DORMANT")) or 0
    sources = db.scalar(select(func.count(func.distinct(RawObservation.source_id)))) or 0
    active_probe_tasks = db.scalar(select(func.count(ProbeTask.id)).where(ProbeTask.active.is_(True))) or 0
    failed_runs_24h = db.scalar(
        select(func.count(CollectionRun.id)).where(
            CollectionRun.status == "FAILED",
            CollectionRun.started_at >= now - timedelta(days=1),
        )
    ) or 0
    open_source_circuits = db.scalar(
        select(func.count(SourceHealthState.source_id)).where(
            SourceHealthState.status == "CIRCUIT_OPEN",
            SourceHealthState.circuit_open_until > now,
        )
    ) or 0
    pending_analysis = db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.analysis_status == "PENDING")
    ) or 0
    degraded_analysis = db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.analysis_status == "DEGRADED")
    ) or 0
    unread_alerts = db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.status == "NEW")) or 0
    starred_opportunities = db.scalar(select(func.count(OpportunityResearch.opportunity_id)).where(OpportunityResearch.starred.is_(True))) or 0
    tracking_opportunities = db.scalar(select(func.count(OpportunityResearch.opportunity_id)).where(OpportunityResearch.status == "TRACKING")) or 0
    recent = db.scalar(
        select(func.count(RawObservation.id)).where(RawObservation.observed_at >= now - timedelta(days=7))
    ) or 0
    top_keywords = db.scalars(select(Keyword).order_by(desc(Keyword.score), desc(Keyword.last_seen_at)).limit(20)).all()
    top_opportunities = db.scalars(
        select(Opportunity)
        .where(Opportunity.stage != "DORMANT")
        .order_by(desc(Opportunity.score), desc(Opportunity.last_seen_at))
        .limit(12)
    ).all()
    latest_items = db.scalars(select(NormalizedItem).order_by(desc(NormalizedItem.observed_at)).limit(20)).all()
    return {
        "totals": {
            "observations": total_observations,
            "keywords": total_keywords,
            "opportunities": total_opportunities,
            "sources": sources,
            "observations_7d": recent,
            "active_probe_tasks": active_probe_tasks,
            "failed_collection_runs_24h": failed_runs_24h,
            "open_source_circuits": open_source_circuits,
            "pending_external_analysis": pending_analysis,
            "degraded_external_analysis": degraded_analysis,
            "unread_alerts": unread_alerts,
            "starred_opportunities": starred_opportunities,
            "tracking_opportunities": tracking_opportunities,
        },
        "top_keywords": [
            {
                "id": kw.id,
                "keyword": kw.display_name,
                "status": kw.status,
                "score": kw.score,
                "observations": kw.observation_count,
                "sources": kw.source_count,
                "last_seen_at": kw.last_seen_at,
            }
            for kw in top_keywords
        ],
        "top_opportunities": [
            {
                "id": opp.id,
                "title": opp.title,
                "stage": opp.stage,
                "score": opp.score,
                "risk_score": opp.risk_score,
                "evidence_count": opp.evidence_count,
                "related_keyword_count": opp.related_keyword_count,
                "summary": opp.summary[:500],
                "analysis_status": opp.analysis_status,
                "last_seen_at": opp.last_seen_at,
            }
            for opp in top_opportunities
        ],
        "latest_items": [
            {
                "source": item.source_id,
                "query": item.query,
                "type": item.item_type,
                "title": item.title,
                "url": item.source_url,
                "observed_at": item.observed_at,
            }
            for item in latest_items
        ],
    }
