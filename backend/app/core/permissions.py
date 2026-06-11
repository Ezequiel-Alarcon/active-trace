"""RBAC permission guard (C-04 §5, C-05 §6).

require_permission(permission: str) — FastAPI dependency that checks
the user's effective permissions and returns 403 if missing.
Also populates request.state with impersonation context.
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.audit.impersonation import (
    get_impersonation_record,
    is_impersonating,
)
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

        # Populate impersonation state on request.state (C-05 §6)
        impersonating = is_impersonating(current_user.user_id)
        request.state.impersonating = impersonating
        if impersonating:
            record = get_impersonation_record(current_user.user_id)
            request.state.impersonated_user_id = record.target_user_id if record else None
        else:
            request.state.impersonated_user_id = None

        request.state.permissions = resolved
        request.state.current_user = current_user
        return current_user

    return _guard
