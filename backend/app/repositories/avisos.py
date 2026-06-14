from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.avisos import AcknowledgmentAviso, Aviso
from app.repositories.base import TenantScopedRepository
from sqlalchemy.sql.elements import BinaryExpression


class AvisoRepository(TenantScopedRepository[Aviso]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, Aviso, tenant_id)

    async def list_visible(
        self,
        *,
        audience_filters: list[BinaryExpression] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Aviso]:
        stmt = (
            select(Aviso)
            .where(Aviso.tenant_id == self._tenant_id)
            .where(Aviso.deleted_at.is_(None))
            .where(Aviso.activo.is_(True))
            .where(Aviso.inicio_en.is_not(None))
            .where(Aviso.fin_en.is_not(None))
            .order_by(Aviso.orden.asc(), Aviso.created_at.desc())
        )
        if audience_filters:
            stmt = stmt.where(*audience_filters)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_acknowledgments(self, aviso_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(AcknowledgmentAviso.tenant_id == self._tenant_id)
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
            .where(AcknowledgmentAviso.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def user_has_acknowledged(self, aviso_id: UUID, usuario_id: UUID) -> bool:
        stmt = (
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(AcknowledgmentAviso.tenant_id == self._tenant_id)
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
            .where(AcknowledgmentAviso.usuario_id == usuario_id)
            .where(AcknowledgmentAviso.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one()) > 0

    async def create_acknowledgment(self, aviso_id: UUID, usuario_id: UUID) -> AcknowledgmentAviso:
        obj = AcknowledgmentAviso(
            tenant_id=self._tenant_id,
            aviso_id=aviso_id,
            usuario_id=usuario_id,
        )
        self._session.add(obj)
        await self._session.flush()
        return obj
