from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario


class GuardiaRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def resolve_tutor_nombre(self, tutor_id: UUID) -> str:
        stmt = (
            select(Usuario.nombre, Usuario.apellidos)
            .where(Usuario.id == tutor_id)
            .where(Usuario.tenant_id == self._tenant_id)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row:
            return f"{row.nombre} {row.apellidos}"
        return ""

    async def resolve_materia_codigo(self, materia_id: UUID) -> str:
        stmt = (
            select(Materia.codigo)
            .where(Materia.id == materia_id)
            .where(Materia.tenant_id == self._tenant_id)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        return row.codigo if row else ""

    async def resolve_cohorte_nombre(self, cohorte_id: UUID) -> str:
        stmt = (
            select(Cohorte.nombre)
            .where(Cohorte.id == cohorte_id)
            .where(Cohorte.tenant_id == self._tenant_id)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        return row.nombre if row else ""
