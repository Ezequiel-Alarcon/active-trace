"""AuditLog service layer (C-05 §8, C-19)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import and_, func, select
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

        count_stmt = select(AuditLog.id)
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
        result = await self._session.execute(count_stmt)
        total = len(result.all())

        offset = (page - 1) * page_size
        stmt = select(AuditLog)
        for cond in conditions:
            stmt = stmt.where(cond)
        stmt = stmt.order_by(AuditLog.fecha_hora.desc()).limit(page_size).offset(offset)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ── C-19: Panel de Auditoría — Métricas ───────────────────────────

    async def get_actions_per_day(
        self,
        *,
        actor_id: UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        materia_ids: list[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Return action counts grouped by day, ordered ascending."""
        date_trunc_expr = func.date_trunc("day", AuditLog.fecha_hora)
        date_col = date_trunc_expr.label("date")

        cols = [
            date_col,
            func.count(AuditLog.id).label("count"),
        ]
        stmt = select(*cols).where(AuditLog.tenant_id == self._tenant_id)

        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if from_date is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= from_date)
        if to_date is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= to_date)
        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))

        stmt = stmt.group_by(date_trunc_expr)
        stmt = stmt.order_by(date_trunc_expr)

        result = await self._session.execute(stmt)
        return [{"date": row[0], "count": row[1]} for row in result.all()]

    async def get_comunicacion_status(
        self,
        *,
        materia_ids: list[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Return communication status counts grouped by materia and docente."""

        from app.audit.constants import (
            AUDIT_COMUNICACION_APROBAR,
            AUDIT_COMUNICACION_ENVIAR,
        )

        status_map = {
            "ok": "Enviado",
            "failed": "Error",
            "sending": "Enviando",
            "cancelled": "Cancelado",
        }

        # TODO: (FIX) Bug de precedencia de operadores resuelto: las tuplas
        # (condicion, valor) pasadas a sa.case() deben ir como argumentos
        # posicionales separados — no como una sola tupla anidada. En SQLAlchemy
        # 2.0, `sa.case((cond1, v1), (cond2, v2), else_=0)` es la forma correcta;
        # `sa.case([(cond1, v1), (cond2, v2)], else_=0)` ya no es válido.
        pending_col = func.coalesce(
            func.sum(
                sa.case(
                    (AuditLog.detalle["to"].astext.is_(None), 1),
                    (AuditLog.detalle["to"].astext == "", 1),
                    else_=0,
                )
            ),
            0,
        ).label("pending")

        status_cols = [
            pending_col,
            *(
                func.coalesce(
                    func.sum(
                        sa.case((AuditLog.detalle["to"].astext == v, 1), else_=0)
                    ),
                    0,
                ).label(k)
                for k, v in status_map.items()
            ),
        ]

        cols = [
            AuditLog.materia_id,
            AuditLog.actor_id.label("docente_id"),
            *status_cols,
        ]

        stmt = (
            select(*cols)
            .where(AuditLog.tenant_id == self._tenant_id)
            .where(
                AuditLog.accion.in_(
                    [AUDIT_COMUNICACION_ENVIAR, AUDIT_COMUNICACION_APROBAR]
                )
            )
        )

        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))

        stmt = stmt.group_by(AuditLog.materia_id, AuditLog.actor_id)
        result = await self._session.execute(stmt)
        return [
            {
                "materia_id": row[0],
                "docente_id": row[1],
                "pending": int(row[2]),
                "sending": int(row[3]),
                "ok": int(row[4]),
                "failed": int(row[5]),
                "cancelled": int(row[6]),
            }
            for row in result.all()
        ]

    async def get_interactions_summary(
        self,
        *,
        materia_ids: list[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Return interaction counts grouped by materia, docente, and action."""
        cols = [
            AuditLog.materia_id,
            AuditLog.actor_id.label("docente_id"),
            AuditLog.accion,
            func.count(AuditLog.id).label("count"),
        ]
        stmt = (
            select(*cols)
            .where(AuditLog.tenant_id == self._tenant_id)
            .group_by(AuditLog.materia_id, AuditLog.actor_id, AuditLog.accion)
        )

        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))

        result = await self._session.execute(stmt)
        return [
            {
                "materia_id": row[0],
                "docente_id": row[1],
                "accion": row[2],
                "count": row[3],
            }
            for row in result.all()
        ]

    async def get_last_actions(
        self,
        *,
        limit: int = 200,
        materia_ids: list[UUID] | None = None,
    ) -> list[AuditLog]:
        """Return the most recent audit entries."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.tenant_id == self._tenant_id)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(limit)
        )

        if materia_ids is not None:
            stmt = stmt.where(AuditLog.materia_id.in_(materia_ids))

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _resolve_scope_materias(
        self, usuario_id: UUID
    ) -> list[UUID]:
        """Resolve materia_ids where the user has assignments (COORDINADOR scope)."""
        from app.models.asignacion import Asignacion, ContextoTipo

        stmt = (
            select(Asignacion.contexto_id)
            .where(Asignacion.tenant_id == self._tenant_id)
            .where(Asignacion.usuario_id == usuario_id)
            .where(Asignacion.contexto_tipo == ContextoTipo.MATERIA)
            .where(Asignacion.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all() if row[0] is not None]

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