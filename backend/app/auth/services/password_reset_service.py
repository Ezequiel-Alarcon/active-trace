"""Password reset service (C-03 §4, D3)."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.errors import (
    AUTH_PASSWORD_REUSED,
    AUTH_PASSWORD_RESET_EXPIRED,
    AUTH_PASSWORD_RESET_INVALID,
    AUTH_PASSWORD_RESET_USED,
    AUTH_PASSWORD_TOO_SHORT,
    auth_error,
)
from app.auth.models import AuthPasswordReset, AuthSession, AuthUser
from app.auth.repositories import (
    AuthPasswordResetRepository,
    AuthSessionRepository,
    AuthUserRepository,
)
from app.core.audit import audit_emit
from app.core.config import get_settings
from app.core.security.passwords import hash_password, verify_password
from app.integrations.email import dispatch_email
from app.models.tenant import Tenant
from sqlalchemy import select

logger = logging.getLogger("activia_trace.auth.password_reset")

_TOKEN_BYTES = 32
_SELECTOR_LEN = 8
_MIN_CONSTANT_TIME_MS = 200


def _now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


@dataclass
class PasswordResetService:
    session: AsyncSession

    async def get_tenant_by_codigo(self, codigo: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.codigo == codigo)
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None or row.estado.value != "Activo" or row.deleted_at is not None:
            return None
        return row

    async def _find_user(
        self, tenant: Tenant, email_lower: str
    ) -> AuthUser | None:
        repo = AuthUserRepository(self.session, AuthUser, tenant.id)
        return await repo.find_by_email(tenant.id, email_lower)

    async def forgot(self, payload) -> None:
        """Issue a recovery token if the user exists; never reveal whether they do."""
        start = _now_ms()
        tenant = await self.get_tenant_by_codigo(payload.tenant_codigo)
        if tenant is None or tenant.estado.value != "Activo" or tenant.deleted_at is not None:
            # Constant-time wait so the response time is identical for known
            # and unknown tenants.
            self._wait_constant_time(start)
            return
        user = await self._find_user(tenant, payload.email.lower())
        if user is None:
            self._wait_constant_time(start)
            return
        # Issue token
        token = secrets.token_urlsafe(_TOKEN_BYTES)
        selector = secrets.token_urlsafe(_SELECTOR_LEN)[:_SELECTOR_LEN].replace("_", "A")
        token_hash = hash_password(token)
        now = datetime.now(timezone.utc)
        ttl_min = get_settings().PASSWORD_RESET_TOKEN_TTL_MINUTES
        row = AuthPasswordReset(
            tenant_id=tenant.id,
            user_id=user.id,
            selector=selector,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=ttl_min),
        )
        self.session.add(row)
        await self.session.flush()
        await dispatch_email(
            to=payload.email,
            subject="Recuperación de contraseña",
            body=(
                f"Use este enlace para restablecer su contraseña: "
                f"/reset?selector={selector}&token={token}"
            ),
        )
        await audit_emit(
            self.session,
            "AUTH_PASSWORD_RESET_REQUEST",
            entity="auth_user",
            entity_id=user.id,
            tenant_id=tenant.id,
        )
        self._wait_constant_time(start)

    async def reset(self, payload) -> None:
        settings = get_settings()
        # Resolve the tenant
        tenant = await self.get_tenant_by_codigo(payload.tenant_codigo)
        if tenant is None or tenant.estado.value != "Activo" or tenant.deleted_at is not None:
            raise auth_error(AUTH_PASSWORD_RESET_INVALID, 400)
        if len(payload.new_password) < settings.PASSWORD_MIN_LENGTH:
            raise auth_error(AUTH_PASSWORD_TOO_SHORT, 400)
        repo = AuthPasswordResetRepository(self.session, AuthPasswordReset, tenant.id)
        row = await repo.find_by_selector(payload.selector)
        if row is None or row.tenant_id != tenant.id:
            raise auth_error(AUTH_PASSWORD_RESET_INVALID, 400)
        if row.used_at is not None:
            raise auth_error(AUTH_PASSWORD_RESET_USED, 400)
        if row.expires_at < datetime.now(timezone.utc):
            raise auth_error(AUTH_PASSWORD_RESET_EXPIRED, 400)
        if not verify_password(payload.token, row.token_hash):
            raise auth_error(AUTH_PASSWORD_RESET_INVALID, 400)
        # Look up the user
        user_repo = AuthUserRepository(self.session, AuthUser, tenant.id)
        user = await user_repo.get_by_id(row.user_id)
        if user is None:
            raise auth_error(AUTH_PASSWORD_RESET_INVALID, 400)
        if verify_password(payload.new_password, user.password_hash):
            raise auth_error(AUTH_PASSWORD_REUSED, 400)
        user.password_hash = hash_password(payload.new_password)
        row.used_at = datetime.now(timezone.utc)
        # Revoke all active sessions for the user
        session_repo = AuthSessionRepository(self.session, AuthSession, tenant.id)
        await session_repo.revoke_active_for_user(user.id)
        await self.session.flush()
        await audit_emit(
            self.session,
            "AUTH_PASSWORD_RESET_OK",
            entity="auth_user",
            entity_id=user.id,
            tenant_id=tenant.id,
        )

    def _wait_constant_time(self, start_ms: int) -> None:
        """Pad the response to a minimum duration to avoid timing oracles."""
        elapsed = _now_ms() - start_ms
        if elapsed < _MIN_CONSTANT_TIME_MS:
            # Busy-wait; CPU is the trade-off for a real constant-time gap.
            import time as _t

            _t.sleep((_MIN_CONSTANT_TIME_MS - elapsed) / 1000.0)
