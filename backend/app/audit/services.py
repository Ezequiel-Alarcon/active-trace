"""AuditLog service layer (C-05 §8)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.repositories import AuditLogRepository


class AuditLogService:
    """Service for querying audit log entries."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = AuditLogRepository(session, tenant_id)

    async def get_logs(
        self,
        tenant_id: UUID,
        actor_id: UUID | None,
        accion: str | None,
        from_date: datetime | None,
        to_date: datetime | None,
        impersonado_id: UUID | None,
        page: int,
        page_size: int,
        is_admin: bool = False,
    ) -> tuple[list[AuditLog], int]:
        """Query audit log entries with filters.

        Args:
            tenant_id: Tenant scope. Ignored if is_admin and all_tenants is True.
            actor_id: Filter by actor.
            accion: Filter by action code.
            from_date: Filter entries after this datetime.
            to_date: Filter entries before this datetime.
            impersonado_id: Filter by impersonated user.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            is_admin: If True, bypass tenant filter for all_tenants queries.

        Returns:
            Tuple of (results list, total count).
        """
        conditions: list[Any] = []

        if not is_admin:
            conditions.append(AuditLog.tenant_id == tenant_id)
        else:
            pass

        if actor_id is not None:
            conditions.append(AuditLog.actor_id == actor_id)

        if accion is not None:
            conditions.append(AuditLog.accion == accion)

        if from_date is not None:
            conditions.append(AuditLog.fecha_hora >= from_date)

        if to_date is not None:
            conditions.append(AuditLog.fecha_hora <= to_date)

        if impersonado_id is not None:
            conditions.append(AuditLog.impersonado_id == impersonado_id)

        where_clause = and_(*conditions) if conditions else None

        count_stmt = select(AuditLog.id)
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        result = await self._session.execute(count_stmt)
        total = len(result.all())

        offset = (page - 1) * page_size
        stmt = (
            select(AuditLog)
            .where(where_clause) if where_clause else select(AuditLog)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_impersonation_history(
        self,
        tenant_id: UUID,
        actor_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Return impersonation start/end audit entries.

        Args:
            tenant_id: Tenant scope.
            actor_id: Optional filter by impersonating actor.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (results list, total count).
        """
        from app.audit.constants import (
            AUDIT_IMPERSONACION_FINALIZAR,
            AUDIT_IMPERSONACION_INICIAR,
        )

        impersonation_actions = [
            AUDIT_IMPERSONACION_INICIAR,
            AUDIT_IMPERSONACION_FINALIZAR,
        ]

        conditions = [AuditLog.accion.in_(impersonation_actions)]

        if actor_id is not None:
            conditions.append(AuditLog.actor_id == actor_id)

        where_clause = and_(*conditions)

        count_stmt = select(AuditLog.id).where(
            and_(where_clause, AuditLog.tenant_id == tenant_id)
        )
        result = await self._session.execute(count_stmt)
        total = len(result.all())

        offset = (page - 1) * page_size
        stmt = (
            select(AuditLog)
            .where(and_(where_clause, AuditLog.tenant_id == tenant_id))
            .order_by(AuditLog.fecha_hora.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return items, total