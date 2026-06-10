"""RBAC public router (C-04 §8).

Public endpoints that require auth but no specific permission.
Mounted at /api/permissions in app/main.py.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.rbac.schemas import PermissionsMeResponse
from app.rbac.services import PermissionResolver

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.get(
    "/me",
    response_model=PermissionsMeResponse,
    summary="Get my effective permissions",
)
async def get_my_permissions(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PermissionsMeResponse:
    """Return the current user's effective permissions.

    Any authenticated user can see their own permissions — no specific
    permission required beyond being authenticated.
    """
    resolver = PermissionResolver(db)
    permissions = await resolver.resolve(current_user.user_id, current_user.tenant_id)
    return PermissionsMeResponse(permissions=sorted(permissions))
