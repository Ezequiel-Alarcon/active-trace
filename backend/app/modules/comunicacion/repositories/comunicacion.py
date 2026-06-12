"""Repository for Comunicacion — worker-facing queries with locking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.comunicacion.models.comunicacion import (
    Comunicacion,
    ComunicacionEstado,
)
from app.repositories.base import TenantScopedRepository


class ComunicacionRepository(TenantScopedRepository[Comunicacion]):
    """Repository with worker-optimized queries."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, Comunicacion, tenant_id)

    async def get_pending_messages(self, limit: int = 10) -> list[Comunicacion]:
        stmt = (
            select(Comunicacion)
            .where(
                and_(
                    Comunicacion.tenant_id == self._tenant_id,
                    Comunicacion.estado == ComunicacionEstado.PENDIENTE,
                    Comunicacion.deleted_at.is_(None),
                )
            )
            .order_by(Comunicacion.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_lote_id(self, lote_id: UUID) -> list[Comunicacion]:
        stmt = (
            select(Comunicacion)
            .where(
                and_(
                    Comunicacion.tenant_id == self._tenant_id,
                    Comunicacion.lote_id == lote_id,
                    Comunicacion.deleted_at.is_(None),
                )
            )
            .order_by(Comunicacion.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_lote_and_estado(
        self, lote_id: UUID
    ) -> dict[ComunicacionEstado, int]:
        stmt = (
            select(Comunicacion.estado, Comunicacion.id)
            .where(
                and_(
                    Comunicacion.tenant_id == self._tenant_id,
                    Comunicacion.lote_id == lote_id,
                    Comunicacion.deleted_at.is_(None),
                )
            )
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        counts: dict[ComunicacionEstado, int] = {}
        for row in rows:
            counts[row] = counts.get(row, 0) + 1
        return counts

    async def update_estado(
        self,
        obj: Comunicacion,
        estado: ComunicacionEstado,
        error_detail: str | None = None,
    ) -> None:
        obj.estado = estado
        if error_detail is not None:
            obj.error_detail = error_detail
        if estado == ComunicacionEstado.ENVIADO:
            obj.enviado_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def increment_retry(self, obj: Comunicacion) -> None:
        obj.retry_count += 1
        await self._session.flush()

    async def reset_to_pendiente(self, obj: Comunicacion) -> None:
        obj.estado = ComunicacionEstado.PENDIENTE
        obj.error_detail = None
        await self._session.flush()

    async def get_stuck_sending(self, timeout_minutes: int = 5) -> list[Comunicacion]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        stmt = (
            select(Comunicacion)
            .where(
                and_(
                    Comunicacion.tenant_id == self._tenant_id,
                    Comunicacion.estado == ComunicacionEstado.ENVIANDO,
                    Comunicacion.deleted_at.is_(None),
                )
            )
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_update_estado(
        self,
        lote_id: UUID,
        estado: ComunicacionEstado,
        error_detail: str | None = None,
    ) -> None:
        stmt = (
            update(Comunicacion)
            .where(
                and_(
                    Comunicacion.tenant_id == self._tenant_id,
                    Comunicacion.lote_id == lote_id,
                    Comunicacion.deleted_at.is_(None),
                )
            )
            .values(estado=estado, error_detail=error_detail)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def bulk_cancel(self, lote_id: UUID, razon: str | None = None) -> None:
        await self.bulk_update_estado(
            lote_id, ComunicacionEstado.CANCELADO, error_detail=razon
        )