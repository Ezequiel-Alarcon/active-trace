"""Repository for Comunicacion — worker-facing queries with locking."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.crypto import CryptoError, decrypt
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

    async def list_lotes_grouped(
        self,
        tenant_id: UUID,
        estado: ComunicacionEstado | None = None,
    ) -> list[dict[str, object]]:
        if tenant_id != self._tenant_id:
            raise ValueError("tenant_id must match repository tenant scope")

        scoped_filters = [
            Comunicacion.tenant_id == tenant_id,
            Comunicacion.deleted_at.is_(None),
            Comunicacion.lote_id.is_not(None),
        ]
        eligible_lotes_stmt = select(Comunicacion.lote_id).where(*scoped_filters)
        if estado is not None:
            eligible_lotes_stmt = eligible_lotes_stmt.where(Comunicacion.estado == estado)
        eligible_lotes = eligible_lotes_stmt.group_by(Comunicacion.lote_id).subquery()

        recipient_value = case(
            (Comunicacion.destinatario_enc != "", Comunicacion.destinatario_enc),
            else_=Comunicacion.destinatario,
        )
        aggregated = (
            select(
                Comunicacion.lote_id.label("lote_id"),
                Comunicacion.tenant_id.label("tenant_id"),
                func.count().label("total"),
                func.count().filter(Comunicacion.estado == ComunicacionEstado.PENDIENTE).label("pendientes"),
                func.count().filter(Comunicacion.estado == ComunicacionEstado.ENVIANDO).label("enviando"),
                func.count().filter(Comunicacion.estado == ComunicacionEstado.ENVIADO).label("enviados"),
                func.count().filter(Comunicacion.estado == ComunicacionEstado.ERROR).label("errores"),
                func.count().filter(Comunicacion.estado == ComunicacionEstado.CANCELADO).label("cancelados"),
                func.max(Comunicacion.created_at).label("latest_created_at"),
                func.array_agg(func.distinct(recipient_value)).label("destinatarios_raw"),
            )
            .where(*scoped_filters)
            .where(Comunicacion.lote_id.in_(select(eligible_lotes.c.lote_id)))
            .group_by(Comunicacion.lote_id, Comunicacion.tenant_id)
            .subquery()
        )
        first_message_ranked = (
            select(
                Comunicacion.lote_id.label("lote_id"),
                Comunicacion.asunto.label("asunto"),
                Comunicacion.cuerpo.label("cuerpo"),
                func.row_number()
                .over(
                    partition_by=Comunicacion.lote_id,
                    order_by=(Comunicacion.created_at.asc(), Comunicacion.id.asc()),
                )
                .label("row_num"),
            )
            .where(*scoped_filters)
            .subquery()
        )
        first_message = (
            select(
                first_message_ranked.c.lote_id,
                first_message_ranked.c.asunto,
                first_message_ranked.c.cuerpo,
            )
            .where(first_message_ranked.c.row_num == 1)
            .subquery()
        )

        stmt = (
            select(
                aggregated.c.lote_id,
                aggregated.c.tenant_id,
                aggregated.c.total,
                aggregated.c.pendientes,
                aggregated.c.enviando,
                aggregated.c.enviados,
                aggregated.c.errores,
                aggregated.c.cancelados,
                first_message.c.asunto,
                first_message.c.cuerpo,
                aggregated.c.destinatarios_raw,
            )
            .join(first_message, first_message.c.lote_id == aggregated.c.lote_id)
            .order_by(aggregated.c.latest_created_at.desc(), aggregated.c.lote_id.desc())
        )
        result = await self._session.execute(stmt)

        lotes: list[dict[str, object]] = []
        for row in result.mappings().all():
            lotes.append(
                {
                    "lote_id": row["lote_id"],
                    "tenant_id": row["tenant_id"],
                    "total": row["total"],
                    "pendientes": row["pendientes"],
                    "enviando": row["enviando"],
                    "enviados": row["enviados"],
                    "errores": row["errores"],
                    "cancelados": row["cancelados"],
                    "asunto": row["asunto"],
                    "cuerpo": row["cuerpo"],
                    "destinatarios": self._decode_destinatarios(
                        row["destinatarios_raw"] or [],
                        tenant_id,
                    ),
                }
            )
        return lotes

    def _decode_destinatarios(
        self,
        destinatarios_raw: list[str],
        tenant_id: UUID,
    ) -> list[str]:
        destinatarios: set[str] = set()
        for raw_value in destinatarios_raw:
            if not raw_value:
                continue
            try:
                destinatario = decrypt(
                    raw_value,
                    tenant_id=tenant_id,
                    aad_suffix="comunicacion.destinatario",
                )
            except CryptoError:
                destinatario = raw_value
            destinatarios.add(destinatario)
        return sorted(destinatarios)

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
