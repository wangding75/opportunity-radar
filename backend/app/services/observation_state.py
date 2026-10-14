from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import RawObservation, UserObservationState

MAX_OBSERVATION_NOTES_CHARS = 50_000


def get_user_observation_state(db: Session, user_id: int, observation_id: int) -> UserObservationState | None:
    return db.scalar(
        select(UserObservationState).where(
            UserObservationState.user_id == user_id,
            UserObservationState.observation_id == observation_id,
        )
    )


def user_observation_state_map(db: Session, user_id: int, observation_ids: list[int]) -> dict[int, UserObservationState]:
    if not observation_ids:
        return {}
    rows = db.scalars(
        select(UserObservationState).where(
            UserObservationState.user_id == user_id,
            UserObservationState.observation_id.in_(observation_ids),
        )
    ).all()
    return {row.observation_id: row for row in rows}


def serialize_user_observation_state(state: UserObservationState | None) -> dict | None:
    """Return the current user's state, or explicit null when none exists.

    A null result is a contract: it means "this user has no bookmark/dismissal
    state for this observation". Consumers must not coerce it into defaults.
    """
    if state is None:
        return None
    return {
        "bookmarked": state.bookmarked,
        "dismissed": state.dismissed_at is not None,
        "dismissed_at": state.dismissed_at,
        "notes": state.notes,
        "updated_at": state.updated_at,
    }


def upsert_user_observation_state(
    db: Session,
    user_id: int,
    observation_id: int,
    *,
    bookmarked: bool | None = None,
    dismissed: bool | None = None,
    notes: str | None = None,
) -> UserObservationState:
    """Idempotently create or update the calling user's observation state.

    Only the fields explicitly provided are mutated, so repeating the same PUT
    converges on the same stored state instead of creating duplicate rows. The
    (user_id, observation_id) unique constraint keeps concurrent creates safe.
    """
    if db.get(RawObservation, observation_id) is None:
        raise KeyError(f"observation not found: {observation_id}")
    state = get_user_observation_state(db, user_id, observation_id)
    now = utc_now()
    if state is None:
        state = UserObservationState(
            user_id=user_id,
            observation_id=observation_id,
            created_at=now,
            updated_at=now,
        )
        db.add(state)
    if bookmarked is not None:
        state.bookmarked = bookmarked
    if dismissed is not None:
        state.dismissed_at = now if dismissed else None
    if notes is not None:
        if len(notes) > MAX_OBSERVATION_NOTES_CHARS:
            raise ValueError(f"notes exceeds {MAX_OBSERVATION_NOTES_CHARS} character limit")
        state.notes = notes
    state.updated_at = now
    db.flush()
    return state


def delete_user_observation_state(db: Session, user_id: int, observation_id: int) -> bool:
    """Remove the calling user's state row. Missing rows are a no-op (idempotent)."""
    state = get_user_observation_state(db, user_id, observation_id)
    if state is None:
        return False
    db.delete(state)
    db.flush()
    return True
