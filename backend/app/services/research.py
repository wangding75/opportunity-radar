from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Opportunity, OpportunityResearch

VALID_RESEARCH_STATUSES = {"NEW", "REVIEWING", "TRACKING", "DISMISSED", "ARCHIVED"}


def get_research_state(db: Session, opportunity_id: int) -> OpportunityResearch | None:
    return db.get(OpportunityResearch, opportunity_id)


def upsert_research_state(
    db: Session,
    opportunity_id: int,
    *,
    status: str | None = None,
    starred: bool | None = None,
    priority: int | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
) -> OpportunityResearch:
    if db.get(Opportunity, opportunity_id) is None:
        raise KeyError(f"opportunity not found: {opportunity_id}")
    state = db.get(OpportunityResearch, opportunity_id)
    if state is None:
        now = utc_now()
        state = OpportunityResearch(opportunity_id=opportunity_id, created_at=now, updated_at=now)
        db.add(state)
        db.flush()
    if status is not None:
        normalized = status.strip().upper()
        if normalized not in VALID_RESEARCH_STATUSES:
            raise ValueError(f"invalid research status: {status}")
        state.status = normalized
    if starred is not None:
        state.starred = starred
    if priority is not None:
        if not 0 <= priority <= 5:
            raise ValueError("priority must be between 0 and 5")
        state.priority = priority
    if notes is not None:
        state.notes = notes[:50_000]
    if tags is not None:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in tags[:30]:
            value = str(raw).strip()[:80]
            if not value or value.lower() in seen:
                continue
            seen.add(value.lower())
            cleaned.append(value)
        state.tags = cleaned
    state.updated_at = utc_now()
    db.flush()
    return state


def serialize_research_state(state: OpportunityResearch | None) -> dict:
    if state is None:
        return {"status": "NEW", "starred": False, "priority": 0, "notes": "", "tags": []}
    return {
        "status": state.status,
        "starred": state.starred,
        "priority": state.priority,
        "notes": state.notes,
        "tags": state.tags or [],
        "updated_at": state.updated_at,
    }


def research_state_map(db: Session, opportunity_ids: list[int]) -> dict[int, OpportunityResearch]:
    if not opportunity_ids:
        return {}
    rows = db.scalars(select(OpportunityResearch).where(OpportunityResearch.opportunity_id.in_(opportunity_ids))).all()
    return {row.opportunity_id: row for row in rows}
