"""Password reset router: /api/auth/forgot, /api/auth/reset."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import ForgotRequest, ResetRequest
from app.auth.services.password_reset_service import PasswordResetService
from app.core.dependencies import get_db

router = APIRouter(prefix="/api/auth", tags=["PasswordReset"])


@router.post("/forgot", status_code=200)
async def forgot(
    payload: ForgotRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    service = PasswordResetService(db)
    await service.forgot(payload)
    return {"ok": "true"}


@router.post("/reset", status_code=200)
async def reset(
    payload: ResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    service = PasswordResetService(db)
    await service.reset(payload)
    return {"ok": "true"}
