from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.db.models import ApiToken, LoginRateLimit, User, UserSession
from app.services.permissions import (
    ROLE_LEVEL,
    SCOPE_MINIMUM_ROLE,
    VALID_ROLES,
    required_role_for_scope,
    scopes_for_role,
)

PASSWORD_SCHEME = "scrypt-v1"
PASSWORD_N = 2**14
PASSWORD_R = 8
PASSWORD_P = 1
PASSWORD_DKLEN = 32
VALID_TOKEN_SCOPES = {"read", "write", "admin"}
LOGIN_FAILURE_LIMIT = 5
LOGIN_LOCK_MINUTES = 15


@dataclass(frozen=True)
class Principal:
    actor: str
    role: str
    user_id: int | None
    auth_type: str
    scopes: frozenset[str]
    session_id: int | None = None

    def can(self, required_role: str) -> bool:
        return ROLE_LEVEL.get(self.role, -1) >= ROLE_LEVEL[required_role]

    def has_scope(self, scope: str) -> bool:
        required_role = required_role_for_scope(scope)
        # The live account role is always the upper permission bound. Personal
        # tokens can narrow privileges, never preserve privileges after demotion.
        if not self.can(required_role):
            return False
        if self.auth_type == "session":
            return True
        return scope in self.scopes or "admin" in self.scopes


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

_DUMMY_PASSWORD_HASH = f"{PASSWORD_SCHEME}${PASSWORD_N}${PASSWORD_R}${PASSWORD_P}${_b64(bytes(16))}${_b64(hashlib.scrypt(b'invalid-password', salt=bytes(16), n=PASSWORD_N, r=PASSWORD_R, p=PASSWORD_P, dklen=PASSWORD_DKLEN))}"


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=PASSWORD_N, r=PASSWORD_R, p=PASSWORD_P, dklen=PASSWORD_DKLEN
    )
    return f"{PASSWORD_SCHEME}${PASSWORD_N}${PASSWORD_R}${PASSWORD_P}${_b64(salt)}${_b64(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = encoded.split("$", 5)
        if scheme != PASSWORD_SCHEME:
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(_b64decode(expected)),
        )
        return hmac.compare_digest(actual, _b64decode(expected))
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(db: Session, username: str, password: str, *, role: str = "VIEWER", enabled: bool = True) -> User:
    username = username.strip().lower()
    if not username or len(username) > 120:
        raise ValueError("invalid username")
    role = role.upper()
    if role not in VALID_ROLES:
        raise ValueError("invalid role")
    if db.scalar(select(User.id).where(User.username == username)) is not None:
        raise ValueError("username already exists")
    row = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        enabled=enabled,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(row)
    db.flush()
    return row


def update_user_password(db: Session, user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    user.failed_login_count = 0
    user.locked_until = None
    user.updated_at = utc_now()
    revoke_user_sessions(db, user.id)
    revoke_user_api_tokens(db, user.id)


def _login_rate_limit_keys(client_ip: str, username: str) -> tuple[str, str]:
    normalized_ip = client_ip.strip().lower()[:128] or "unknown"
    normalized_username = username.strip().lower()[:120]
    subject = hashlib.sha256(normalized_username.encode("utf-8")).hexdigest()[:32]
    source = hashlib.sha256(f"{normalized_ip}|{normalized_username}".encode("utf-8")).hexdigest()[:32]
    return (
        f"ip:{hashlib.sha256(normalized_ip.encode('utf-8')).hexdigest()[:32]}",
        f"subject:{source}:{subject}",
    )


def _prune_login_rate_limits(db: Session, now) -> None:
    cutoff = now - timedelta(seconds=settings.login_rate_limit_window_seconds)
    db.execute(delete(LoginRateLimit).where(LoginRateLimit.updated_at <= cutoff))


def login_rate_limit_retry_after(db: Session, client_ip: str, username: str, *, now=None) -> int | None:
    now = now or utc_now()
    _prune_login_rate_limits(db, now)
    rows = db.scalars(
        select(LoginRateLimit).where(LoginRateLimit.key.in_(_login_rate_limit_keys(client_ip, username)))
    ).all()
    retry_after: int | None = None
    for row in rows:
        if row.blocked_until is not None and row.blocked_until > now:
            seconds = int((row.blocked_until - now).total_seconds()) + 1
        elif row.attempt_count >= settings.login_rate_limit_max_attempts:
            seconds = settings.login_rate_limit_block_seconds
        else:
            continue
        retry_after = max(retry_after or 0, seconds)
    return retry_after


def record_login_failure(db: Session, client_ip: str, username: str, *, now=None) -> None:
    """Record source failures in shared SQL storage for all API workers.

    The per-account counter remains on ``User``. Source counters are keyed by
    one-way digests so rate-limit rows do not retain raw usernames or IPs, and
    stale rows are pruned on the request path plus the worker retention path.
    """
    now = now or utc_now()
    _prune_login_rate_limits(db, now)
    table = LoginRateLimit.__table__
    block_until = now + timedelta(seconds=settings.login_rate_limit_block_seconds)
    initial_block = block_until if settings.login_rate_limit_max_attempts <= 1 else None
    for key in _login_rate_limit_keys(client_ip, username):
        values = {
            "key": key,
            "window_started_at": now,
            "attempt_count": 1,
            "blocked_until": initial_block,
            "updated_at": now,
        }
        statement = postgres_insert(table) if db.get_bind().dialect.name == "postgresql" else sqlite_insert(table)
        statement = statement.values(**values).on_conflict_do_update(
            index_elements=[table.c.key],
            set_={
                "attempt_count": table.c.attempt_count + 1,
                "blocked_until": (
                    block_until
                    if settings.login_rate_limit_max_attempts <= 1
                    else case(
                        (table.c.attempt_count + 1 >= settings.login_rate_limit_max_attempts, block_until),
                        else_=table.c.blocked_until,
                    )
                ),
                "updated_at": now,
            },
        )
        db.execute(statement)


def clear_login_rate_limits(db: Session, client_ip: str, username: str) -> None:
    db.execute(delete(LoginRateLimit).where(LoginRateLimit.key.in_(_login_rate_limit_keys(client_ip, username))))


def authenticate_credentials(db: Session, username: str, password: str) -> User | None:
    now = utc_now()
    stmt = select(User).where(User.username == username.strip().lower())
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    row = db.scalar(stmt)
    if row is None:
        # Spend roughly the same password verification work for unknown users to
        # reduce username-enumeration timing differences.
        verify_password(password, _DUMMY_PASSWORD_HASH)
        return None
    if not row.enabled:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        return None
    if row.locked_until is not None and row.locked_until > now:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        return None
    if row.locked_until is not None and row.locked_until <= now:
        row.locked_until = None
        row.failed_login_count = 0
    if not verify_password(password, row.password_hash):
        row.failed_login_count = int(row.failed_login_count or 0) + 1
        if row.failed_login_count >= settings.login_failure_limit:
            row.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
        row.updated_at = now
        return None
    row.failed_login_count = 0
    row.locked_until = None
    row.last_login_at = now
    row.updated_at = now
    return row


def create_session(db: Session, user: User, *, ttl_hours: int) -> tuple[str, str, UserSession]:
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    now = utc_now()
    row = UserSession(
        user_id=user.id,
        token_hash=token_hash(session_token),
        csrf_hash=token_hash(csrf_token),
        created_at=now,
        expires_at=now + timedelta(hours=ttl_hours),
        last_seen_at=now,
    )
    db.add(row)
    db.flush()
    return session_token, csrf_token, row


def revoke_session(db: Session, session_token: str) -> None:
    row = db.scalar(select(UserSession).where(UserSession.token_hash == token_hash(session_token)))
    if row is not None and row.revoked_at is None:
        row.revoked_at = utc_now()


def revoke_user_sessions(db: Session, user_id: int) -> int:
    now = utc_now()
    rows = db.scalars(select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))).all()
    for row in rows:
        row.revoked_at = now
    return len(rows)


def principal_from_session(db: Session, session_token: str) -> Principal | None:
    now = utc_now()
    row = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_hash(session_token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )
    if row is None:
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.enabled:
        return None
    if row.last_seen_at < now - timedelta(minutes=5):
        row.last_seen_at = now
        db.commit()
    return Principal(
        actor=f"user:{user.username}",
        role=user.role,
        user_id=user.id,
        auth_type="session",
        scopes=scopes_for_role(user.role),
        session_id=row.id,
    )


def validate_csrf(db: Session, session_id: int, csrf_token: str | None) -> bool:
    if not csrf_token:
        return False
    row = db.get(UserSession, session_id)
    now = utc_now()
    return bool(
        row
        and row.revoked_at is None
        and row.expires_at > now
        and hmac.compare_digest(row.csrf_hash, token_hash(csrf_token))
    )


def create_api_token(
    db: Session,
    user: User,
    *,
    name: str,
    scopes: list[str],
    expires_in_days: int | None = None,
) -> tuple[str, ApiToken]:
    normalized = sorted(set(scopes))
    if not normalized or any(scope not in VALID_TOKEN_SCOPES for scope in normalized):
        raise ValueError("invalid token scopes")
    if "admin" in normalized and user.role not in {"OWNER", "ADMIN"}:
        raise ValueError("admin scope requires ADMIN role")
    if "write" in normalized and user.role == "VIEWER":
        raise ValueError("write scope requires RESEARCHER role")
    clean_name = name.strip()[:120]
    if not clean_name:
        raise ValueError("token name is required")
    existing = db.scalar(select(ApiToken).where(ApiToken.user_id == user.id, ApiToken.name == clean_name))
    if existing is not None and existing.revoked_at is None:
        raise ValueError("active token name already exists")
    plain = "or_pat_" + secrets.token_urlsafe(32)
    now = utc_now()
    if existing is not None:
        # Preserve the stable token record/name while allowing a revoked token name
        # to be issued again. The old secret remains permanently invalid because
        # the stored hash is replaced with a freshly generated value.
        row = existing
        row.token_hash = token_hash(plain)
        row.scopes = normalized
        row.created_at = now
        row.expires_at = now + timedelta(days=expires_in_days) if expires_in_days else None
        row.last_used_at = None
        row.revoked_at = None
    else:
        row = ApiToken(
            user_id=user.id,
            name=clean_name,
            token_hash=token_hash(plain),
            scopes=normalized,
            created_at=now,
            expires_at=now + timedelta(days=expires_in_days) if expires_in_days else None,
        )
        db.add(row)
    db.flush()
    return plain, row


def revoke_user_api_tokens(db: Session, user_id: int) -> int:
    now = utc_now()
    rows = db.scalars(select(ApiToken).where(ApiToken.user_id == user_id, ApiToken.revoked_at.is_(None))).all()
    for row in rows:
        row.revoked_at = now
    return len(rows)


def principal_from_api_token(db: Session, token: str) -> Principal | None:
    now = utc_now()
    row = db.scalar(select(ApiToken).where(ApiToken.token_hash == token_hash(token), ApiToken.revoked_at.is_(None)))
    if row is None or (row.expires_at is not None and row.expires_at <= now):
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.enabled:
        return None
    # Avoid turning every authenticated API request into a database write.
    if row.last_used_at is None or row.last_used_at < now - timedelta(minutes=5):
        row.last_used_at = now
        db.commit()
    return Principal(
        actor=f"token:{user.username}/{row.name}",
        role=user.role,
        user_id=user.id,
        auth_type="api_token",
        scopes=frozenset(row.scopes or []),
    )


def cleanup_auth_records(db: Session, *, retention_days: int = 90, dry_run: bool = True) -> dict:
    """Remove expired/revoked session and token records after a retention window."""
    from sqlalchemy import delete, func
    now = utc_now()
    cutoff = now - timedelta(days=max(1, min(3650, retention_days)))
    session_filter = (
        (UserSession.expires_at < cutoff)
        | ((UserSession.revoked_at.is_not(None)) & (UserSession.revoked_at < cutoff))
    )
    token_filter = (
        ((ApiToken.expires_at.is_not(None)) & (ApiToken.expires_at < cutoff))
        | ((ApiToken.revoked_at.is_not(None)) & (ApiToken.revoked_at < cutoff))
    )
    sessions = db.scalar(select(func.count()).select_from(UserSession).where(session_filter)) or 0
    tokens = db.scalar(select(func.count()).select_from(ApiToken).where(token_filter)) or 0
    rate_cutoff = now - timedelta(seconds=settings.login_rate_limit_window_seconds)
    login_rate_limits = db.scalar(
        select(func.count()).select_from(LoginRateLimit).where(LoginRateLimit.updated_at <= rate_cutoff)
    ) or 0
    if not dry_run:
        db.execute(delete(UserSession).where(session_filter))
        db.execute(delete(ApiToken).where(token_filter))
        db.execute(delete(LoginRateLimit).where(LoginRateLimit.updated_at <= rate_cutoff))
        db.commit()
    return {
        "dry_run": dry_run,
        "retention_days": retention_days,
        "expired_sessions": int(sessions),
        "expired_or_revoked_tokens": int(tokens),
        "expired_login_rate_limits": int(login_rate_limits),
    }
