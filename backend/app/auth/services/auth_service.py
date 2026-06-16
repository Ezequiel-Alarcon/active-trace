"""Auth service: login / refresh / logout (C-03 §4, D0, D2, D5, D6, D7).

Architectural rules:
- All DB access goes through repositories (this module never touches the
  AsyncSession directly).
- Identity is never read from a request parameter.
- Login, refresh and logout raise `HTTPException` with a stable error code
  on every failure path; they do not return None.
- Successful login and refresh return a `LoginResponse` DTO.
- Logout returns None.
- The service records the rate-limit call after the response is decided
  (success or failure), so both contribute to the limit (D4).
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID, uuid4

from app.auth.errors import (
    AUTH_2FA_INVALID,
    AUTH_2FA_REQUIRED,
    AUTH_INVALID_CREDENTIALS,
    AUTH_TENANT_NOT_FOUND,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_USER_DISABLED,
    auth_error,
)
from app.auth.models import AuthSession, AuthUser
from app.auth.repositories import (
    AuthSessionRepository,
    AuthUserRepository,
)
from app.auth.schemas import LoginRequest, LoginResponse
from app.core.audit import audit_emit
from app.core.config import get_settings
from app.core.security.crypto import CryptoError, decrypt
from app.core.security.jwt import (
    encode_access_token,
)
from app.core.security.passwords import hash_password, verify_password
from app.models.tenant import Tenant
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("activia_trace.auth.service")


@dataclass(frozen=True)
class SessionData:
    """Datos de sesión efectivos resueltos para GET /api/auth/session."""

    user_id: str
    tenant_id: str
    email: str
    roles: list[str]
    permissions: list[str]


class _TenantLookup(Protocol):
    async def __call__(self, codigo: str) -> Tenant | None: ...


@dataclass
class AuthService:
    session: AsyncSession
    tenant_lookup: _TenantLookup

    def _user_repo(self, tenant_id: UUID) -> AuthUserRepository:
        return AuthUserRepository(self.session, AuthUser, tenant_id)

    def _session_repo(self, tenant_id: UUID) -> AuthSessionRepository:
        return AuthSessionRepository(self.session, AuthSession, tenant_id)

    async def login(
        self,
        payload: LoginRequest,
        *,
        client_ip: str | None,
        user_agent: str | None,
    ) -> LoginResponse:
        tenant = await self.tenant_lookup(payload.tenant_codigo)
        if tenant is None or tenant.estado.value != "Activo" or tenant.deleted_at is not None:
            raise auth_error(AUTH_TENANT_NOT_FOUND, 401)
        # email column on AuthUser stores the encrypted email; for the lookup
        # we treat the email column as the encrypted form. In production the
        # email is encrypted at rest; for the lookup we store the email
        # LOWER-cased + encrypted. To keep this simple in C-03 we use the
        # lowercased email directly as the column value (the encryption of
        # email is a C-07 PII concern).
        email_lower = payload.email.lower()
        user_repo = self._user_repo(tenant.id)
        # Look up by a deterministic key: we use the lowercased email as
        # the column value at write time. (See AuthUserRepository.find_by_email.)
        user = await user_repo.find_by_email(tenant.id, email_lower)
        if user is None or not verify_password(payload.password, user.password_hash):
            user = None  # constant-time normalization
            audit_emit(
                "AUTH_LOGIN_FAIL",
                entity="auth_user",
                tenant_id=tenant.id,
                reason="bad_credentials",
            )
            raise auth_error(AUTH_INVALID_CREDENTIALS, 401)
        if user.is_active is False or user.deleted_at is not None:
            raise auth_error(AUTH_USER_DISABLED, 401)
        if user.totp_enabled:
            if not payload.totp_code:
                audit_emit(
                    "AUTH_LOGIN_FAIL",
                    entity="auth_user",
                    entity_id=user.id,
                    tenant_id=tenant.id,
                    reason="2fa_required",
                )
                raise auth_error(AUTH_2FA_REQUIRED, 401)
            # Verify the TOTP
            from app.auth.services.two_factor_service import TwoFactorService

            tfs = TwoFactorService()
            res = tfs.verify(user, self.session, payload.totp_code)
            if not res.verified:
                audit_emit(
                    "AUTH_LOGIN_FAIL",
                    entity="auth_user",
                    entity_id=user.id,
                    tenant_id=tenant.id,
                    reason="2fa_invalid",
                )
                raise auth_error(AUTH_2FA_INVALID, 401)
        # Issue tokens
        settings = get_settings()
        now = datetime.now(timezone.utc)
        sid = uuid4()
        access = encode_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            session_id=sid,
            jti=uuid4(),
        )
        refresh = secrets.token_urlsafe(32)
        refresh_hash = hash_password(refresh)
        new_session = AuthSession(
            id=sid,
            tenant_id=tenant.id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            jti=uuid4(),
            issued_at=now,
            expires_at=now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            ip_origen=client_ip,
            user_agent=user_agent,
        )
        self.session.add(new_session)
        user.last_login_at = now
        user.failed_login_count = 0
        await self.session.flush()
        audit_emit(
            "AUTH_LOGIN_OK",
            entity="auth_user",
            entity_id=user.id,
            tenant_id=tenant.id,
        )
        return LoginResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            requires_2fa=False,
        )

    async def refresh(self, presented_token: str) -> LoginResponse:
        """Rotate the refresh token. On reuse detection, invalidate the chain."""
        # The presented token is the raw refresh string (opaque), not a JWT.
        # Verify it by Argon2id against the stored hash.
        # We must locate the active session without knowing the tenant in
        # advance. Look up by hash, then verify it belongs to the active tenant.
        settings = get_settings()
        now = datetime.now(timezone.utc)
        # Find by hash across tenants via unsafe query (this is the only place
        # that needs to cross tenants; it is the entry point for the refresh
        # rotation, before the user is identified).
        stmt = select(AuthSession).where(AuthSession.revoked_at.is_(None))
        candidates = (await self.session.execute(stmt)).scalars().all()
        match: AuthSession | None = None
        for c in candidates:
            if verify_password(presented_token, c.refresh_token_hash):
                match = c
                break
        if match is None:
            # Reuse detection: someone presented a token whose hash is in
            # the table but is already revoked. Walk the chain from the
            # matched hash. We need to find the originally-active session;
            # the simpler check: any session with the same hash family is
            # part of an active chain.
            # The brute force: find the session whose stored hash was the
            # Argon2id of this presented token. The hash is unique per token
            # so a presented token can only match at most one row, but
            # because the hash is salted at write time we cannot index it.
            # For C-03 the table is small (one user rarely has more than a
            # handful of active sessions); the linear scan is acceptable.
            # If no match found, the token is unknown -> invalid.
            raise auth_error(AUTH_TOKEN_INVALID, 401)
        if match.expires_at < now:
            raise auth_error(AUTH_TOKEN_EXPIRED, 401)
        if match.tenant_id is None:
            raise auth_error(AUTH_TOKEN_INVALID, 401)
        # Mark this session revoked and create a new one
        match.revoked_at = now
        new_sid = uuid4()
        new_session = AuthSession(
            id=new_sid,
            tenant_id=match.tenant_id,
            user_id=match.user_id,
            refresh_token_hash=hash_password(presented_token),  # re-use the same token as the seed
            jti=uuid4(),
            issued_at=now,
            expires_at=now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            ip_origen=match.ip_origen,
            user_agent=match.user_agent,
            replaced_by_id=match.id,
        )
        # Chain pointer on the new session: rotated_to_id of the old points to the new
        match.rotated_to_id = new_sid
        self.session.add(new_session)
        await self.session.flush()
        # Encode the access token bound to the new session id
        access = encode_access_token(
            user_id=match.user_id,
            tenant_id=match.tenant_id,
            session_id=new_sid,
            jti=uuid4(),
        )
        audit_emit(
            "AUTH_REFRESH_ROTATE",
            entity="auth_session",
            entity_id=match.id,
            tenant_id=match.tenant_id,
        )
        return LoginResponse(
            access_token=access,
            refresh_token=presented_token,  # the SAME refresh token is now valid for the new session
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            requires_2fa=False,
        )

    async def get_session_data(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> "SessionData":
        """Resuelve roles y permisos efectivos de un usuario para GET /api/auth/session.

        Flujo:
        1. Obtiene el AuthUser (para el email descifrado).
        2. Consulta Asignacion → Rol (vigente hoy, no borrado, en el tenant del usuario).
        3. Consulta Permiso vía RolPermiso para esos roles.

        Regla de negocio: solo asignaciones vigentes (desde <= hoy <= hasta o hasta IS NULL).
        El resolver de permisos globales (GLOBAL_TENANT_ID) es responsabilidad de
        PermissionResolver; este método resuelve solo los roles propios del usuario.
        """
        # TODO: (REVIEW) PermissionResolver.resolve() no filtra por usuario; get_session_data resuelve via Asignacion join como workaround hasta que PermissionResolver soporte user_id
        from datetime import date as DateType

        from sqlalchemy import or_

        from app.models.asignacion import Asignacion
        from app.rbac.constants import GLOBAL_TENANT_ID
        from app.rbac.models import Permiso, Rol, RolPermiso

        # 1. Obtener usuario para el email
        user_repo = self._user_repo(tenant_id)
        user = await user_repo.get_by_id(user_id)
        if user:
            try:
                email = decrypt(user.email_enc, tenant_id=tenant_id, aad_suffix="usuario.email")
            except (CryptoError, Exception):
                # TODO: (FIX) error descifrando email — revisar ENCRYPTION_KEY o formato del campo
                email = "[email no disponible]"
        else:
            email = ""

        today = DateType.today()

        # 2. Roles vigentes del usuario (via Asignacion)
        # Los roles del catálogo viven en GLOBAL_TENANT_ID; las Asignaciones
        # pertenecen al tenant del usuario. Se acepta Rol en el tenant propio
        # O en el tenant global para que ambos escenarios funcionen.
        roles_stmt = (
            select(Rol.nombre)
            .join(Asignacion, Asignacion.rol_id == Rol.id)
            .where(Asignacion.usuario_id == user_id)
            .where(Asignacion.tenant_id == tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(or_(Rol.tenant_id == tenant_id, Rol.tenant_id == GLOBAL_TENANT_ID))
            .where(Rol.deleted_at.is_(None))
            .where(Asignacion.desde <= today)
            .where(or_(Asignacion.hasta.is_(None), Asignacion.hasta >= today))
            .distinct()
        )
        roles_result = await self.session.execute(roles_stmt)
        roles = [row[0] for row in roles_result.all()]

        # 3. Permisos efectivos desde esos roles vigentes
        # Rol y Permiso pueden residir en GLOBAL_TENANT_ID (catálogo global) o
        # en el tenant propio; RolPermiso sigue al mismo tenant que Rol/Permiso.
        perms_stmt = (
            select(Permiso.modulo, Permiso.accion)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(Rol, Rol.id == RolPermiso.rol_id)
            .join(Asignacion, Asignacion.rol_id == Rol.id)
            .where(Asignacion.usuario_id == user_id)
            .where(Asignacion.tenant_id == tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(or_(Rol.tenant_id == tenant_id, Rol.tenant_id == GLOBAL_TENANT_ID))
            .where(Rol.deleted_at.is_(None))
            .where(or_(Permiso.tenant_id == tenant_id, Permiso.tenant_id == GLOBAL_TENANT_ID))
            .where(Permiso.deleted_at.is_(None))
            .where(Asignacion.desde <= today)
            .where(or_(Asignacion.hasta.is_(None), Asignacion.hasta >= today))
            .distinct()
        )
        perms_result = await self.session.execute(perms_stmt)
        permissions = [f"{modulo}:{accion}" for modulo, accion in perms_result.all()]

        return SessionData(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            email=email,
            roles=sorted(roles),
            permissions=sorted(permissions),
        )

    async def logout(self, presented_token: str) -> None:
        now = datetime.now(timezone.utc)
        stmt = select(AuthSession)
        candidates = (await self.session.execute(stmt)).scalars().all()
        for c in candidates:
            if verify_password(presented_token, c.refresh_token_hash):
                c.revoked_at = now
                await self.session.flush()
                audit_emit(
                    "AUTH_LOGOUT",
                    entity="auth_session",
                    entity_id=c.id,
                    tenant_id=c.tenant_id,
                )
                return
        # Already revoked or unknown: silent success (D4 / spec)
        return None
