"""Auth router: /api/auth/login, /api/auth/refresh, /api/auth/logout, /api/me."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.auth.errors import auth_error
from app.auth.models import AuthUser
from app.auth.repositories import AuthUserRepository
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshRequest,
    SessionResponse,
)
from app.auth.services.auth_service import AuthService
from app.core.dependencies import get_db
from app.core.rate_limit import get_login_rate_limiter
from app.core.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    settings = get_settings()
    limiter = get_login_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    key = (client_ip, payload.email.lower())
    if not await limiter.check(key):
        from app.auth.errors import AUTH_RATE_LIMITED

        raise auth_error(AUTH_RATE_LIMITED, 429, retry_after=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    service = AuthService(db)
    try:
        resp = await service.login(
            payload,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        await limiter.record(key)
        raise
    await limiter.record(key)
    return resp


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponse:
    service = AuthService(db)
    await service.logout(payload.refresh_token)
    return LogoutResponse()


@router.get("/session", response_model=SessionResponse)
async def get_session(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Devuelve identidad y permisos efectivos del usuario autenticado.

    Identidad extraída del JWT verificado. Roles y permisos resueltos desde
    las Asignaciones vigentes del usuario en su tenant.
    Nunca lee user_id ni tenant_id de parámetros de URL, body ni headers.
    """
    service = AuthService(db)
    data = await service.get_session_data(current.user_id, current.tenant_id)
    return SessionResponse(
        user_id=data.user_id,
        tenant_id=data.tenant_id,
        email=data.email,
        roles=data.roles,
        permissions=data.permissions,
    )


@router.get("/me")
async def me(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    repo = AuthUserRepository(db, AuthUser, current.tenant_id)
    user = await repo.get_by_id(current.user_id)
    return {
        "user_id": str(current.user_id),
        "tenant_id": str(current.tenant_id),
        "is_2fa_verified": user.totp_enabled if user else False,
        "totp_enabled": user.totp_enabled if user else False,
    }
