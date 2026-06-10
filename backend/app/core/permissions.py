"""RBAC permission guard (C-04 §5).

require_permission(permission: str) — FastAPI dependency that checks
the user's effective permissions and returns 403 if missing.
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.rbac.services import PermissionResolver


def require_permission(permission: str) -> Callable:
    """Factory: returns a FastAPI dependency that checks the required permission.

    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_permission("calificaciones:importar"))])
    """

    async def _guard(
        request: Request,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> CurrentUser:
        resolver = PermissionResolver(db)
        resolved = await resolver.resolve(current_user.user_id, current_user.tenant_id)
        if permission not in resolved:
            raise HTTPException(
                status_code=403,
                detail={"detail": f"No tiene el permiso: {permission}"},
            )
        request.state.permissions = resolved
        request.state.current_user = current_user
        return current_user

    return _guard
