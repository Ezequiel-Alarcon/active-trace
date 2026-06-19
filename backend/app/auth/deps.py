"""Auth dependencies: get_current_user, get_optional_current_user, CurrentUser.

Identity is resolved exclusively from the JWT. Headers, query parameters,
body fields, and path parameters are NEVER consulted. The test
`tests/auth/test_identity_immutability.py` enforces this by surface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.errors import (
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_TOKEN_MISSING,
    AUTH_TOKEN_REVOKED,
    auth_error,
)
from app.auth.models import AuthSession, AuthUser
from app.auth.repositories import AuthSessionRepository, AuthUserRepository
from app.core.security.jwt import (
    InvalidTokenError,
    decode_access_token,
)
from app.core.tenancy import TenantContext, set_tenant_context
from app.core.dependencies import get_db
from app.rbac.services import PermissionResolver

logger = logging.getLogger("activia_trace.auth.deps")


async def resolve_user_roles(
    db: AsyncSession,
    user_id: UUID,
    tenant_id: UUID,
) -> list[str]:
    """Resolve effective roles for a user via PermissionResolver.

    Used by routers that need roles for service-layer authorization
    (e.g. TareaService) when CurrentUser doesn't carry roles directly.
    """
    resolver = PermissionResolver(db)
    resolved = await resolver.resolve(user_id, tenant_id)
    return list(resolved)


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    tenant_id: UUID
    session_id: UUID
    is_2fa_verified: bool
    totp_enabled: bool


async def _resolve_from_token(
    db: AsyncSession, token: str | None
) -> CurrentUser:
    if not token:
        raise auth_error(AUTH_TOKEN_MISSING, 401)
    try:
        claims = decode_access_token(token)
    except InvalidTokenError as exc:
        msg = str(exc)
        if "expired" in msg:
            raise auth_error(AUTH_TOKEN_EXPIRED, 401) from exc
        raise auth_error(AUTH_TOKEN_INVALID, 401) from exc
    sub = UUID(claims["sub"])
    tid = UUID(claims["tid"])
    sid = UUID(claims["sid"])
    user_repo = AuthUserRepository(db, AuthUser, tid)
    user = await user_repo.get_by_id(sub)
    if user is None or user.deleted_at is not None or not user.is_active:
        raise auth_error(AUTH_TOKEN_REVOKED, 401)
    session_repo = AuthSessionRepository(db, AuthSession, tid)
    sess = await session_repo.get_by_id(sid)
    if sess is None or sess.revoked_at is not None or sess.deleted_at is not None:
        raise auth_error(AUTH_TOKEN_REVOKED, 401)
    if sess.tenant_id != user.tenant_id:
        raise auth_error(AUTH_TOKEN_INVALID, 401)
    set_tenant_context(TenantContext(tenant_id=user.tenant_id))
    return CurrentUser(
        user_id=user.id,
        tenant_id=user.tenant_id,
        session_id=sid,
        is_2fa_verified=user.totp_enabled,
        totp_enabled=user.totp_enabled,
    )


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    return await _resolve_from_token(db, token)


async def get_optional_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser | None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        return await _resolve_from_token(db, token)
    except HTTPException:
        return None
