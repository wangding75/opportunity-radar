from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin_auth, require_read_auth
from app.db.models import Opportunity
from app.db.session import get_db
from app.services.scoring import SCORING_MODEL_VERSION, backtest_summary, replay_snapshot, score_history
from app.services.score_jumps import list_score_jump_records, materialize_score_jumps
from app.services.score_jump_alerts import materialize_score_jump_alerts
from app.services.score_jump_replay import replay_score_jump

router = APIRouter(prefix="/api/v1/scoring", tags=["scoring"], dependencies=[Depends(require_read_auth)])


@router.get("/models")
def models():
    return [{
        "version": SCORING_MODEL_VERSION,
        "status": "ACTIVE",
        "components": ["demand", "supply", "execution", "cross_source", "saturation"],
        "max_score": 100,
    }]


@router.get("/opportunities/{opportunity_id}/history")
def history(opportunity_id: int, limit: int = Query(default=200, ge=1, le=1000), db: Session = Depends(get_db)):
    if db.get(Opportunity, opportunity_id) is None:
        raise HTTPException(status_code=404, detail="opportunity not found")
    return score_history(db, opportunity_id, limit=limit)


@router.get("/opportunities/{opportunity_id}/replay")
def replay(
    opportunity_id: int,
    as_of: datetime = Query(..., description="ISO-8601 timestamp; returns the last persisted score snapshot at or before this time"),
    db: Session = Depends(get_db),
):
    if db.get(Opportunity, opportunity_id) is None:
        raise HTTPException(status_code=404, detail="opportunity not found")
    result = replay_snapshot(db, opportunity_id, as_of=as_of)
    if result is None:
        raise HTTPException(status_code=404, detail="no score snapshot exists at or before as_of")
    return result


@router.get("/backtest")
def backtest(
    lookback_days: int = Query(default=90, ge=1, le=3650),
    threshold: float = Query(default=60, ge=0, le=100),
    db: Session = Depends(get_db),
):
    return backtest_summary(db, lookback_days=lookback_days, threshold=threshold)


@router.post("/score-jumps/evaluate")
def evaluate_score_jumps(
    opportunity_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    result = materialize_score_jumps(
        db,
        opportunity_ids={opportunity_id} if opportunity_id is not None else None,
        limit=limit,
    )
    alerts = materialize_score_jump_alerts(
        db,
        opportunity_ids={opportunity_id} if opportunity_id is not None else None,
        limit=limit,
    )
    db.commit()
    return {"score_jumps": result, "alerts": alerts}


@router.post("/score-jumps/replay")
def replay_score_jumps(
    opportunity_id: int = Query(..., ge=1),
    as_of: datetime = Query(..., description="ISO-8601 timestamp; evaluates the latest two persisted snapshots at or before this time"),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_admin_auth),
):
    try:
        result = replay_score_jump(db, opportunity_id, as_of=as_of)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="no score snapshot exists at or before as_of")
    return result


@router.get("/score-jumps/records")
def score_jump_records(
    opportunity_id: int | None = Query(default=None, ge=1),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_score_jump_records(db, opportunity_id=opportunity_id, status=status, limit=limit)
