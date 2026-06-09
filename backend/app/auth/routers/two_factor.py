"""2FA router: /api/auth/2fa/enroll, /api/auth/2fa/verify."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.auth.errors import auth_error
from app.auth.repositories import AuthUserRepository
from app.auth.models import AuthUser
from app.auth.schemas import (
    TwoFactorEnrollResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
)
from app.auth.services.two_factor_service import TwoFactorService
from app.core.dependencies import get_db

router = APIRouter(prefix="/api/auth/2fa", tags=["TwoFactor"])


@router.post("/enroll", response_model=TwoFactorEnrollResponse)
async def enroll(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TwoFactorEnrollResponse:
    repo = AuthUserRepository(db, AuthUser, current.tenant_id)
    user = await repo.get_by_id(current.user_id)
    if user is None:
        raise auth_error("AUTH_USER_NOT_FOUND", 404)
    svc = TwoFactorService()
    return svc.enroll(user, db)


@router.post("/verify", response_model=TwoFactorVerifyResponse)
async def verify(
    payload: TwoFactorVerifyRequest,
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TwoFactorVerifyResponse:
    repo = AuthUserRepository(db, AuthUser, current.tenant_id)
    user = await repo.get_by_id(current.user_id)
    if user is None:
        raise auth_error("AUTH_USER_NOT_FOUND", 404)
    svc = TwoFactorService()
    return svc.verify(user, db, payload.code)
