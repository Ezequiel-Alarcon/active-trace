"""AuditLogRepository — append-only (C-05 §3)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog

# NOTE: does NOT inherit TenantScopedRepository to break the circular chain
# app.repositories.base → app.models.__init__ → app.audit.models → app.audit.__init__
# → app.audit.repositories → app.repositories.base.
# All callers only use __init__() and create() — no base class methods are needed.
class AuditLogRepository:
    """Append-only audit log repository.

    Contract: ONLY `create()` exists. No `update`, `delete`, or `soft_delete`.
    This is a hard constraint — the append-only audit guarantee depends on it.

    NOTE: does NOT inherit TenantScopedRepository to avoid circular imports
    (app.repositories → app.models → app.audit → app.repositories).
    """

    __slots__ = ("_session", "_tenant_id")

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def create(
        self,
        actor_id: UUID,
        accion: str,
        *,
        impersonado_id: UUID | None = None,
        materia_id: UUID | None = None,
        detalle: dict[str, Any] | None = None,
        filas_afectadas: int = 0,
        ip: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> AuditLog:
        """Create an audit log entry.

        This is the ONLY mutating operation on AuditLog.
        """
        entry = AuditLog(
            id=uuid4(),
            tenant_id=self._tenant_id,
            fecha_hora=datetime.now(timezone.utc),
            actor_id=actor_id,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            accion=accion,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    # ── Explicitly remove mutators to make append-only contract unambiguous ──

    async def update(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("AuditLog is append-only: update is not permitted")

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("AuditLog is append-only: delete is not permitted")

    async def soft_delete(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("AuditLog is append-only: soft_delete is not permitted")