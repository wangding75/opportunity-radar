from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_admin_auth, require_read_auth, require_write_auth
from app.db.models import ApiToken, User
from app.db.session import get_db
from app.domain.schemas import ApiTokenCreate, LoginRequest, UserCreate, UserPatch
from app.services.auth import (
    Principal,
    VALID_ROLES,
    authenticate_credentials,
    create_api_token,
    create_session,
    create_user,
    revoke_session,
    update_user_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "enabled": user.enabled,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
        "failed_login_count": user.failed_login_count,
        "locked_until": user.locked_until,
    }


@router.get("/config")
def auth_config():
    return {"auth_mode": settings.auth_mode, "csrf_cookie_name": settings.csrf_cookie_name}


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if settings.auth_mode != "rbac":
        raise HTTPException(status_code=409, detail="session login is available only when AUTH_MODE=rbac")
    user = authenticate_credentials(db, payload.username, payload.password)
    if user is None:
        # Persist failed-login counters / temporary lockout state while preserving a
        # generic response that does not reveal whether the username exists.
        db.commit()
        raise HTTPException(status_code=401, detail="invalid username or password")
    session_token, csrf_token, _session = create_session(db, user, ttl_hours=settings.session_ttl_hours)
    db.commit()
    secure = settings.app_env == "production"
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=secure,
        samesite="strict",
        max_age=max_age,
        path="/",
    )
    return {"user": _user_payload(user), "auth_mode": settings.auth_mode}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    _principal: Principal | None = Depends(require_write_auth),
    db: Session = Depends(get_db),
):
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        revoke_session(db, token)
        db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    return {"status": "logged_out"}


@router.get("/me")
def me(principal: Principal | None = Depends(require_read_auth), db: Session = Depends(get_db)):
    if settings.auth_mode == "disabled":
        return {"authenticated": False, "role": "OWNER", "actor": "development-anonymous", "auth_mode": "disabled"}
    if principal is None:
        raise HTTPException(status_code=401, detail="authentication required")
    user = db.get(User, principal.user_id) if principal.user_id else None
    return {
        "authenticated": True,
        "actor": principal.actor,
        "role": principal.role,
        "auth_type": principal.auth_type,
        "scopes": sorted(principal.scopes),
        "user": _user_payload(user) if user else None,
        "auth_mode": settings.auth_mode,
    }


@router.post("/tokens")
def issue_api_token(
    payload: ApiTokenCreate,
    principal: Principal | None = Depends(require_write_auth),
    db: Session = Depends(get_db),
):
    if principal is None or principal.user_id is None or principal.auth_type != "session":
        raise HTTPException(status_code=403, detail="interactive user session required to issue personal API tokens")
    user = db.get(User, principal.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    try:
        plain, row = create_api_token(db, user, name=payload.name, scopes=payload.scopes, expires_in_days=payload.expires_in_days)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    return {"id": row.id, "name": row.name, "token": plain, "scopes": row.scopes, "expires_at": row.expires_at}


@router.get("/tokens")
def list_api_tokens(principal: Principal | None = Depends(require_read_auth), db: Session = Depends(get_db)):
    if principal is None or principal.user_id is None:
        return []
    rows = db.scalars(select(ApiToken).where(ApiToken.user_id == principal.user_id).order_by(ApiToken.created_at.desc())).all()
    return [{"id": row.id, "name": row.name, "scopes": row.scopes, "created_at": row.created_at, "expires_at": row.expires_at, "last_used_at": row.last_used_at, "revoked_at": row.revoked_at} for row in rows]


@router.delete("/tokens/{token_id}")
def revoke_api_token(
    token_id: int,
    principal: Principal | None = Depends(require_write_auth),
    db: Session = Depends(get_db),
):
    if principal is None or principal.user_id is None:
        raise HTTPException(status_code=403, detail="user identity required")
    row = db.get(ApiToken, token_id)
    if row is None or row.user_id != principal.user_id:
        raise HTTPException(status_code=404, detail="token not found")
    from app.core.time import utc_now
    row.revoked_at = utc_now()
    db.commit()
    return {"status": "revoked"}


@admin_router.get("/users")
def list_users(_principal: Principal | None = Depends(require_admin_auth), db: Session = Depends(get_db)):
    return [_user_payload(row) for row in db.scalars(select(User).order_by(User.username)).all()]


@admin_router.post("/users")
def admin_create_user(
    payload: UserCreate,
    principal: Principal | None = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    requested_role = payload.role.strip().upper()
    if requested_role == "OWNER" and (principal is None or principal.role != "OWNER"):
        raise HTTPException(status_code=403, detail="only OWNER can create another OWNER")
    try:
        row = create_user(db, payload.username, payload.password, role=requested_role, enabled=payload.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    return _user_payload(row)


@admin_router.patch("/users/{user_id}")
def admin_patch_user(
    user_id: int,
    payload: UserPatch,
    principal: Principal | None = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    row = db.get(User, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    actor_is_owner = bool(principal and principal.role == "OWNER")
    if row.role == "OWNER" and not actor_is_owner:
        raise HTTPException(status_code=403, detail="only OWNER can modify an OWNER account")

    requested_role = payload.role.upper() if payload.role is not None else None
    if requested_role is not None:
        if requested_role not in VALID_ROLES:
            raise HTTPException(status_code=422, detail="invalid role")
        if requested_role == "OWNER" and not actor_is_owner:
            raise HTTPException(status_code=403, detail="only OWNER can grant OWNER role")

    removing_owner = row.role == "OWNER" and (requested_role not in {None, "OWNER"} or payload.enabled is False)
    if removing_owner:
        owner_count = db.scalar(select(func.count()).select_from(User).where(User.role == "OWNER", User.enabled.is_(True))) or 0
        if owner_count <= 1:
            raise HTTPException(status_code=409, detail="cannot remove or disable the last enabled OWNER")

    if requested_role is not None:
        row.role = requested_role
    if payload.enabled is not None:
        if principal and principal.user_id == row.id and payload.enabled is False:
            raise HTTPException(status_code=409, detail="cannot disable current user")
        row.enabled = payload.enabled
    if payload.password is not None:
        update_user_password(db, row, payload.password)
    from app.core.time import utc_now
    row.updated_at = utc_now()
    db.commit()
    return _user_payload(row)
