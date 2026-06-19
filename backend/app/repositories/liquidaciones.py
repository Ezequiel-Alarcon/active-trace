from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Select, and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.liquidacion import (
    Factura,
    FacturaEstado,
    Liquidacion,
    LiquidacionEstado,
    PlusCategoria,
    SalarioBase,
    SalarioPlus,
)
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.rbac.models import Rol
from app.repositories.base import TenantScopedRepository


PLUS_CATEGORIAS_INICIALES = {
    # TODO: (REVIEW) Reemplazar estos seeds iniciales por el catalogo fijo exacto del programa antes de cargar datos reales.
    "PROG": "Materias de programacion",
    "MAT": "Materias matematicas",
    "IDI": "Materias de idiomas",
}


def vigencia_filter(model, ref: date):
    return and_(model.desde <= ref, (model.hasta.is_(None)) | (model.hasta >= ref))


class GrillaSalarialRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self.base_repo = TenantScopedRepository(session, SalarioBase, tenant_id)
        self.plus_repo = TenantScopedRepository(session, SalarioPlus, tenant_id)

    async def ensure_plus_catalogue(self) -> None:
        for grupo, descripcion in PLUS_CATEGORIAS_INICIALES.items():
            if await self.get_plus_categoria(grupo) is None:
                self._session.add(PlusCategoria(grupo=grupo, descripcion=descripcion))
        await self._session.flush()

    async def get_plus_categoria(self, grupo: str) -> PlusCategoria | None:
        result = await self._session.execute(select(PlusCategoria).where(PlusCategoria.grupo == grupo))
        return result.scalar_one_or_none()

    async def list_base_for_overlap(self, rol: str) -> list[SalarioBase]:
        return list(await self.base_repo.list(limit=500, filters=[SalarioBase.rol == rol]))

    async def list_plus_for_overlap(self, grupo: str, rol: str) -> list[SalarioPlus]:
        return list(await self.plus_repo.list(limit=500, filters=[SalarioPlus.grupo == grupo, SalarioPlus.rol == rol]))

    async def vigente_base(self, rol: str, ref: date) -> SalarioBase | None:
        rows = await self.base_repo.list(
            limit=1,
            filters=[SalarioBase.rol == rol, vigencia_filter(SalarioBase, ref)],
            order_by=[SalarioBase.desde.desc()],
        )
        return rows[0] if rows else None

    async def vigente_plus(self, grupo: str, rol: str, ref: date) -> SalarioPlus | None:
        rows = await self.plus_repo.list(
            limit=1,
            filters=[SalarioPlus.grupo == grupo, SalarioPlus.rol == rol, vigencia_filter(SalarioPlus, ref)],
            order_by=[SalarioPlus.desde.desc()],
        )
        return rows[0] if rows else None


class LiquidacionRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self.repo = TenantScopedRepository(session, Liquidacion, tenant_id)

    async def list_periodo(self, cohorte_id: UUID, periodo: str) -> list[Liquidacion]:
        return list(await self.repo.list(
            limit=1000,
            filters=[Liquidacion.cohorte_id == cohorte_id, Liquidacion.periodo == periodo],
        ))

    async def list_historial(self, usuario_id: UUID | None = None) -> list[Liquidacion]:
        filters = [Liquidacion.estado == LiquidacionEstado.CERRADA]
        if usuario_id is not None:
            filters.append(Liquidacion.usuario_id == usuario_id)
        return list(await self.repo.list(limit=1000, filters=filters))

    async def has_closed(self, cohorte_id: UUID, periodo: str) -> bool:
        rows = await self.repo.list(
            limit=1,
            filters=[
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.estado == LiquidacionEstado.CERRADA,
            ],
        )
        return bool(rows)

    async def replace_open(self, cohorte_id: UUID, periodo: str, rows: list[dict]) -> list[Liquidacion]:
        stmt = delete(Liquidacion).where(
            Liquidacion.tenant_id == self._tenant_id,
            Liquidacion.cohorte_id == cohorte_id,
            Liquidacion.periodo == periodo,
            Liquidacion.estado == LiquidacionEstado.ABIERTA,
        )
        await self._session.execute(stmt)
        created = []
        for row in rows:
            created.append(await self.repo.create(row))
        await self._session.flush()
        return created

    async def close_open(self, cohorte_id: UUID, periodo: str) -> int:
        stmt = (
            update(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.estado == LiquidacionEstado.ABIERTA,
                Liquidacion.deleted_at.is_(None),
            )
            .values(estado=LiquidacionEstado.CERRADA)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return int(result.rowcount or 0)

    async def list_asignaciones_liquidables(self, cohorte_id: UUID, ref: date) -> list[dict]:
        stmt: Select = (
            select(Asignacion, Rol.nombre.label("rol"), Usuario.facturante, Materia.codigo, Materia.plus_grupo)
            .join(Rol, (Rol.id == Asignacion.rol_id) & (Rol.tenant_id == self._tenant_id) & (Rol.deleted_at.is_(None)))
            .join(Usuario, (Usuario.id == Asignacion.usuario_id) & (Usuario.tenant_id == self._tenant_id) & (Usuario.deleted_at.is_(None)))
            .join(Materia, (Materia.id == Asignacion.materia_id) & (Materia.tenant_id == self._tenant_id) & (Materia.deleted_at.is_(None)))
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.materia_id.is_not(None),
                Asignacion.desde <= ref,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
                Rol.nombre.in_(["PROFESOR", "TUTOR", "COORDINADOR", "NEXO"]),
            )
        )
        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]


class FacturaRepository(TenantScopedRepository[Factura]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, Factura, tenant_id)
        self._session = session

    async def usuario_facturante(self, usuario_id: UUID) -> bool | None:
        stmt = select(Usuario.facturante).where(
            Usuario.tenant_id == self._tenant_id,
            Usuario.id == usuario_id,
            Usuario.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def listar_filtrado(
        self,
        *,
        estado: str | None = None,
        usuario_id: UUID | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[Factura]:
        filters = []
        if estado is not None:
            filters.append(Factura.estado == FacturaEstado(estado))
        if usuario_id is not None:
            filters.append(Factura.usuario_id == usuario_id)
        if desde is not None:
            filters.append(Factura.cargada_at >= desde)
        if hasta is not None:
            filters.append(Factura.cargada_at <= hasta)
        return list(await self.list(limit=1000, filters=filters if filters else None))
