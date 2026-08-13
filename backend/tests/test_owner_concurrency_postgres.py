from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.api import auth as auth_api
from app.db.models import ApiToken, User, UserSession
from app.domain.schemas import UserPatch
from app.services.auth import Principal, create_user


pytestmark = pytest.mark.postgres_integration


@pytest.fixture(scope="module")
def postgres_sessions():
    database_url = os.getenv("OPPORTUNITY_RADAR_TEST_DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        pytest.skip("set OPPORTUNITY_RADAR_TEST_DATABASE_URL to run PostgreSQL integration tests")

    engine = create_engine(database_url, future=True, pool_pre_ping=True, pool_size=8, max_overflow=8)
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


def _owner_principal() -> Principal:
    return Principal(
        actor="integration-owner",
        role="OWNER",
        user_id=None,
        auth_type="integration",
        scopes=frozenset({"read", "write", "admin"}),
    )


def _create_owners(factory, count: int) -> tuple[str, list[int]]:
    prefix = f"t131-{uuid4().hex}"
    with factory() as db:
        rows = [
            create_user(db, f"{prefix}-{index}", "OwnerPassword-2026!", role="OWNER")
            for index in range(count)
        ]
        db.commit()
        return prefix, [row.id for row in rows]


def _cleanup(factory, prefix: str) -> None:
    with factory() as db:
        ids = list(db.scalars(select(User.id).where(User.username.like(f"{prefix}-%"))))
        if ids:
            db.execute(delete(UserSession).where(UserSession.user_id.in_(ids)))
            db.execute(delete(ApiToken).where(ApiToken.user_id.in_(ids)))
            db.execute(delete(User).where(User.id.in_(ids)))
        db.commit()


def _patch_owner(factory, user_id: int, payload: UserPatch) -> tuple[str, int | None]:
    with factory() as db:
        try:
            result = auth_api.admin_patch_user(
                user_id,
                payload,
                principal=_owner_principal(),
                db=db,
            )
            return "committed", result["id"]
        except HTTPException as exc:
            db.rollback()
            return f"http-{exc.status_code}", None


def _run_concurrently(factory, user_ids: list[int], payload_factory) -> list[tuple[str, int | None]]:
    barrier = Barrier(len(user_ids))

    def invoke(user_id: int):
        barrier.wait()
        return _patch_owner(factory, user_id, payload_factory())

    with ThreadPoolExecutor(max_workers=len(user_ids)) as executor:
        return list(executor.map(invoke, user_ids))


def _enabled_owner_count(factory, prefix: str) -> int:
    with factory() as db:
        return db.scalar(
            select(func.count()).select_from(User).where(
                User.username.like(f"{prefix}-%"),
                User.role == "OWNER",
                User.enabled.is_(True),
            )
        ) or 0


def test_two_owners_concurrent_demotion_preserves_enabled_owner(postgres_sessions):
    prefix, owner_ids = _create_owners(postgres_sessions, 2)
    try:
        results = _run_concurrently(
            postgres_sessions,
            owner_ids,
            lambda: UserPatch(role="ADMIN"),
        )
        assert sorted(status for status, _ in results) == ["committed", "http-409"]
        assert _enabled_owner_count(postgres_sessions, prefix) >= 1
    finally:
        _cleanup(postgres_sessions, prefix)


def test_two_owners_concurrent_disable_preserves_enabled_owner(postgres_sessions):
    prefix, owner_ids = _create_owners(postgres_sessions, 2)
    try:
        results = _run_concurrently(
            postgres_sessions,
            owner_ids,
            lambda: UserPatch(enabled=False),
        )
        assert sorted(status for status, _ in results) == ["committed", "http-409"]
        assert _enabled_owner_count(postgres_sessions, prefix) >= 1
    finally:
        _cleanup(postgres_sessions, prefix)


def test_three_owners_concurrent_demotions_leave_one_enabled_owner(postgres_sessions):
    prefix, owner_ids = _create_owners(postgres_sessions, 3)
    try:
        results = _run_concurrently(
            postgres_sessions,
            owner_ids,
            lambda: UserPatch(role="ADMIN"),
        )
        assert sorted(status for status, _ in results) == ["committed", "committed", "http-409"]
        assert _enabled_owner_count(postgres_sessions, prefix) >= 1
    finally:
        _cleanup(postgres_sessions, prefix)


def test_single_thread_legal_owner_demotion_commits(postgres_sessions):
    prefix, owner_ids = _create_owners(postgres_sessions, 2)
    try:
        status, _ = _patch_owner(postgres_sessions, owner_ids[0], UserPatch(role="ADMIN"))
        assert status == "committed"
        assert _enabled_owner_count(postgres_sessions, prefix) == 1
    finally:
        _cleanup(postgres_sessions, prefix)
