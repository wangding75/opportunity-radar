from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    Opportunity,
    OpportunityScoreSnapshot,
)

SCORING_MODEL_VERSION = "score-v1"


@dataclass(frozen=True)
class ScoreInputs:
    weighted_demand: float
    weighted_supply: float
    weighted_execution: float
    source_count: int
    recent_30_count: int
    trend_last_7: int
    trend_prev_7: int


def calculate_score(inputs: ScoreInputs) -> tuple[float, dict]:
    trend_growth = (inputs.trend_last_7 - inputs.trend_prev_7) / max(inputs.trend_prev_7, 1)
    growth_component = max(0.0, min(1.0, trend_growth)) if inputs.trend_last_7 >= 2 else 0.0
    demand = min(25.0, inputs.weighted_demand * 4.0 + growth_component * 10.0)
    supply = min(25.0, inputs.weighted_supply * 6.0)
    execution = min(20.0, inputs.weighted_execution * 8.0)
    cross_source = min(20.0, max(0, inputs.source_count - 1) * 5.0)
    saturation = min(15.0, max(0, inputs.recent_30_count - 20) * 0.5)
    total = round(min(100.0, max(0.0, demand + supply + execution + cross_source - saturation)), 2)
    breakdown = {
        "model_version": SCORING_MODEL_VERSION,
        "inputs": asdict(inputs),
        "components": {
            "demand": round(demand, 2),
            "supply": round(supply, 2),
            "execution": round(execution, 2),
            "cross_source": round(cross_source, 2),
            "saturation": round(saturation, 2),
        },
        "total": total,
    }
    return total, breakdown


def score_input_signature(breakdown: dict, *, risk_score: float, stage: str, evidence_count: int) -> str:
    payload = {"breakdown": breakdown, "risk_score": risk_score, "stage": stage, "evidence_count": evidence_count}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def record_score_snapshot(db: Session, opportunity: Opportunity, *, now: datetime | None = None) -> bool:
    now = now or utc_now()
    signature = score_input_signature(
        opportunity.score_breakdown or {},
        risk_score=opportunity.risk_score,
        stage=opportunity.stage,
        evidence_count=opportunity.evidence_count,
    )
    exists = db.scalar(
        select(OpportunityScoreSnapshot.id).where(
            OpportunityScoreSnapshot.opportunity_id == opportunity.id,
            OpportunityScoreSnapshot.model_version == opportunity.score_version,
            OpportunityScoreSnapshot.input_signature == signature,
        )
    )
    if exists is not None:
        return False
    db.add(
        OpportunityScoreSnapshot(
            opportunity_id=opportunity.id,
            model_version=opportunity.score_version,
            input_signature=signature,
            score=opportunity.score,
            risk_score=opportunity.risk_score,
            stage=opportunity.stage,
            evidence_count=opportunity.evidence_count,
            breakdown=opportunity.score_breakdown or {},
            calculated_at=now,
        )
    )
    return True


def score_history(db: Session, opportunity_id: int, *, limit: int = 200) -> list[dict]:
    rows = db.scalars(
        select(OpportunityScoreSnapshot)
        .where(OpportunityScoreSnapshot.opportunity_id == opportunity_id)
        .order_by(OpportunityScoreSnapshot.calculated_at.desc(), OpportunityScoreSnapshot.id.desc())
        .limit(max(1, min(1000, limit)))
    ).all()
    return [
        {
            "model_version": row.model_version,
            "score": row.score,
            "risk_score": row.risk_score,
            "stage": row.stage,
            "evidence_count": row.evidence_count,
            "breakdown": row.breakdown,
            "calculated_at": row.calculated_at,
        }
        for row in rows
    ]



def replay_snapshot(db: Session, opportunity_id: int, *, as_of: datetime) -> dict | None:
    """Return the latest persisted model output at or before ``as_of``.

    This is snapshot replay, not a re-computation against reconstructed raw state.
    It therefore reproduces what the scoring engine actually persisted at that time.
    """
    row = db.scalar(
        select(OpportunityScoreSnapshot)
        .where(
            OpportunityScoreSnapshot.opportunity_id == opportunity_id,
            OpportunityScoreSnapshot.calculated_at <= as_of,
        )
        .order_by(OpportunityScoreSnapshot.calculated_at.desc(), OpportunityScoreSnapshot.id.desc())
        .limit(1)
    )
    if row is None:
        return None
    return {
        "opportunity_id": opportunity_id,
        "model_version": row.model_version,
        "score": row.score,
        "risk_score": row.risk_score,
        "stage": row.stage,
        "evidence_count": row.evidence_count,
        "breakdown": row.breakdown,
        "calculated_at": row.calculated_at,
        "replay_mode": "persisted_snapshot",
    }

def backtest_summary(db: Session, *, lookback_days: int = 90, threshold: float = 60.0) -> dict:
    """Backtest threshold-entry signals using persisted score state changes.

    Score snapshots are change events, so the state at a 30-day horizon is the
    latest snapshot at or before that horizon (or the candidate itself when no
    change occurred). Only threshold *crossings* whose full 30-day horizon has
    elapsed are evaluated; recent signals are reported as immature rather than
    incorrectly counted as failures.
    """
    now = utc_now()
    lookback_days = max(1, min(3650, lookback_days))
    cutoff = now - timedelta(days=lookback_days)
    mature_cutoff = now - timedelta(days=30)
    rows = db.scalars(
        select(OpportunityScoreSnapshot)
        .where(
            OpportunityScoreSnapshot.calculated_at >= cutoff,
            OpportunityScoreSnapshot.calculated_at <= now,
            OpportunityScoreSnapshot.model_version == SCORING_MODEL_VERSION,
        )
        .order_by(OpportunityScoreSnapshot.opportunity_id, OpportunityScoreSnapshot.calculated_at, OpportunityScoreSnapshot.id)
    ).all()
    by_opportunity: dict[int, list[OpportunityScoreSnapshot]] = {}
    for row in rows:
        by_opportunity.setdefault(row.opportunity_id, []).append(row)

    # Determine the exact state immediately before the lookback window. A fixed
    # warmup interval is insufficient because snapshots are change events and an
    # unchanged state can legitimately be months old. The window function keeps
    # this set-based across SQLite/PostgreSQL without loading all history.
    ranked_prior = (
        select(
            OpportunityScoreSnapshot.opportunity_id.label("opportunity_id"),
            OpportunityScoreSnapshot.score.label("score"),
            func.row_number().over(
                partition_by=OpportunityScoreSnapshot.opportunity_id,
                order_by=(OpportunityScoreSnapshot.calculated_at.desc(), OpportunityScoreSnapshot.id.desc()),
            ).label("rn"),
        )
        .where(
            OpportunityScoreSnapshot.calculated_at < cutoff,
            OpportunityScoreSnapshot.model_version == SCORING_MODEL_VERSION,
        )
        .subquery()
    )
    prior_scores = {
        int(opportunity_id): float(score)
        for opportunity_id, score in db.execute(
            select(ranked_prior.c.opportunity_id, ranked_prior.c.score).where(ranked_prior.c.rn == 1)
        ).all()
    }

    candidates = 0
    immature = 0
    persisted = 0
    for opportunity_id, snapshots in by_opportunity.items():
        previous_score = prior_scores.get(opportunity_id)
        for idx, row in enumerate(snapshots):
            is_crossing = row.score >= threshold and (previous_score is None or previous_score < threshold)
            previous_score = row.score
            if not is_crossing:
                continue
            if row.calculated_at > mature_cutoff:
                immature += 1
                continue
            candidates += 1
            horizon = row.calculated_at + timedelta(days=30)
            state_at_horizon = row
            for later in snapshots[idx + 1:]:
                if later.calculated_at > horizon:
                    break
                state_at_horizon = later
            if state_at_horizon.score >= threshold:
                persisted += 1

    return {
        "model_version": SCORING_MODEL_VERSION,
        "lookback_days": lookback_days,
        "threshold": threshold,
        "candidate_signals": candidates,
        "immature_signals": immature,
        "persisted_signals": persisted,
        "persistence_rate": round(persisted / candidates, 4) if candidates else None,
        "horizon_days": 30,
        "definition": "threshold crossings with a completed 30-day horizon; state is carried forward between score-change snapshots",
    }
