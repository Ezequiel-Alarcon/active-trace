from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repositories import AuditLogRepository
from app.models.liquidacion import FacturaEstado, Liquidacion, LiquidacionEstado
from app.repositories.liquidaciones import FacturaRepository, GrillaSalarialRepository, LiquidacionRepository
from app.schemas.liquidaciones import (
    FacturaCreate,
    FacturaDescargaResponse,
    FacturaPagoConfirm,
    FacturaResponse,
    LiquidacionCalcularRequest,
    LiquidacionCerrarRequest,
    LiquidacionCierreResponse,
    LiquidacionItem,
    LiquidacionKpis,
    LiquidacionResultado,
    LiquidacionSegmentos,
    SalarioBaseCreate,
    SalarioPlusCreate,
)


def _periodo_ref(periodo: str) -> date:
    year, month = periodo.split("-")
    return date(int(year), int(month), 1)


def _overlaps(a_desde: date, a_hasta: date | None, b_desde: date, b_hasta: date | None) -> bool:
    return a_desde <= (b_hasta or date.max) and b_desde <= (a_hasta or date.max)


def _item(obj: Liquidacion) -> LiquidacionItem:
    return LiquidacionItem(
        id=obj.id,
        usuario_id=obj.usuario_id,
        rol=obj.rol,
        cohorte_id=obj.cohorte_id,
        periodo=obj.periodo,
        monto_base=obj.monto_base,
        monto_plus=obj.monto_plus,
        total=obj.total,
        comisiones=obj.comisiones,
        es_nexo=obj.es_nexo,
        excluido_por_factura=obj.excluido_por_factura,
        estado=obj.estado.value,
    )


def _factura_response(obj) -> FacturaResponse:
    return FacturaResponse(
        id=obj.id,
        tenant_id=obj.tenant_id,
        usuario_id=obj.usuario_id,
        periodo=obj.periodo,
        detalle=obj.detalle,
        referencia_archivo=obj.referencia_archivo,
        tamano_kb=obj.tamano_kb,
        estado=obj.estado.value,
        cargada_at=obj.cargada_at,
        abonada_at=obj.abonada_at,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


class GrillaSalarialService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._repo = GrillaSalarialRepository(session, tenant_id)
        self._tenant_id = tenant_id

    async def create_salario_base(self, data: SalarioBaseCreate):
        if data.rol not in {"PROFESOR", "TUTOR", "COORDINADOR", "NEXO"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol no liquidable")
        for row in await self._repo.list_base_for_overlap(data.rol):
            if _overlaps(row.desde, row.hasta, data.desde, data.hasta):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vigencia de salario base solapada")
        return await self._repo.base_repo.create({
            "tenant_id": self._tenant_id,
            "rol": data.rol,
            "monto": data.monto,
            "desde": data.desde,
            "hasta": data.hasta,
        })

    async def create_salario_plus(self, data: SalarioPlusCreate):
        await self._repo.ensure_plus_catalogue()
        if await self._repo.get_plus_categoria(data.grupo) is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Clave Plus inexistente")
        for row in await self._repo.list_plus_for_overlap(data.grupo, data.rol):
            if _overlaps(row.desde, row.hasta, data.desde, data.hasta):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vigencia de salario plus solapada")
        return await self._repo.plus_repo.create({
            "tenant_id": self._tenant_id,
            "grupo": data.grupo,
            "rol": data.rol,
            "descripcion": data.descripcion,
            "monto": data.monto,
            "desde": data.desde,
            "hasta": data.hasta,
        })


class LiquidacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = LiquidacionRepository(session, tenant_id)
        self._grilla = GrillaSalarialRepository(session, tenant_id)

    async def calcular(self, data: LiquidacionCalcularRequest) -> LiquidacionResultado:
        ref = _periodo_ref(data.periodo)
        if await self._repo.has_closed(data.cohorte_id, data.periodo):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La liquidacion del periodo esta cerrada")

        asignaciones = await self._repo.list_asignaciones_liquidables(data.cohorte_id, ref)
        grouped: dict[tuple[UUID, str, bool], list[dict]] = defaultdict(list)
        for row in asignaciones:
            asignacion = row["Asignacion"]
            grouped[(asignacion.usuario_id, row["rol"], bool(row["facturante"]))].append(row)

        rows = []
        for (usuario_id, rol, facturante), group in grouped.items():
            base = await self._grilla.vigente_base(rol, ref)
            if base is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"No hay salario base vigente para {rol}")
            monto_plus = Decimal("0")
            detalle = []
            for row in group:
                asignacion = row["Asignacion"]
                comisiones = asignacion.comisiones or ["Sin comisión"]
                grupo = row["plus_grupo"]
                plus_unit = Decimal("0")
                if grupo is not None:
                    plus = await self._grilla.vigente_plus(grupo, rol, ref)
                    if plus is not None:
                        plus_unit = plus.monto
                        monto_plus += plus.monto * len(comisiones)
                for comision in comisiones:
                    detalle.append({
                        "materia_id": str(asignacion.materia_id),
                        "materia_codigo": row["codigo"],
                        "plus_grupo": grupo,
                        "comision": comision,
                        "plus_unitario": str(plus_unit),
                    })
            total = base.monto + monto_plus
            rows.append({
                "tenant_id": self._tenant_id,
                "usuario_id": usuario_id,
                "rol": rol,
                "cohorte_id": data.cohorte_id,
                "periodo": data.periodo,
                "monto_base": base.monto,
                "monto_plus": monto_plus,
                "total": total,
                "comisiones": detalle,
                "es_nexo": rol == "NEXO",
                "excluido_por_factura": facturante,
                "estado": LiquidacionEstado.ABIERTA,
            })

        created = await self._repo.replace_open(data.cohorte_id, data.periodo, rows)
        return self._result(data.cohorte_id, data.periodo, created)

    async def cerrar(self, data: LiquidacionCerrarRequest, *, actor_id: UUID) -> LiquidacionCierreResponse:
        if not data.confirmar:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Confirmacion requerida")
        affected = await self._repo.close_open(data.cohorte_id, data.periodo)
        await AuditLogRepository(self._session, self._tenant_id).create(
            actor_id,
            "LIQUIDACION_CERRAR",
            detalle={"cohorte_id": str(data.cohorte_id), "periodo": data.periodo},
            filas_afectadas=affected,
        )
        return LiquidacionCierreResponse(cohorte_id=data.cohorte_id, periodo=data.periodo, filas_afectadas=affected)

    async def historial(self, usuario_id: UUID | None = None) -> list[LiquidacionItem]:
        return [_item(row) for row in await self._repo.list_historial(usuario_id)]

    async def exportar(self, cohorte_id: UUID, periodo: str) -> LiquidacionResultado:
        rows = await self._repo.list_periodo(cohorte_id, periodo)
        return self._result(cohorte_id, periodo, rows)

    def _result(self, cohorte_id: UUID, periodo: str, rows: list[Liquidacion]) -> LiquidacionResultado:
        total_sin_factura = sum((r.total for r in rows if not r.excluido_por_factura), Decimal("0"))
        total_facturantes = sum((r.total for r in rows if r.excluido_por_factura), Decimal("0"))
        nexo_total = sum((r.total for r in rows if r.es_nexo and not r.excluido_por_factura), Decimal("0"))
        general_total = sum((r.total for r in rows if not r.es_nexo and not r.excluido_por_factura), Decimal("0"))
        return LiquidacionResultado(
            cohorte_id=cohorte_id,
            periodo=periodo,
            items=[_item(r) for r in rows],
            kpis=LiquidacionKpis(total_sin_factura=total_sin_factura, total_facturantes=total_facturantes),
            segmentos=LiquidacionSegmentos(
                general_total=general_total,
                nexo_total=nexo_total,
                facturantes_total=total_facturantes,
            ),
        )


class FacturaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._repo = FacturaRepository(session, tenant_id)

    async def registrar(self, data: FacturaCreate, *, actor_id: UUID | None = None) -> FacturaResponse:
        facturante = await self._repo.usuario_facturante(data.usuario_id)
        if facturante is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        if not facturante:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario no es facturante")
        obj = await self._repo.create({
            "tenant_id": self._repo.tenant_id,
            "usuario_id": data.usuario_id,
            "periodo": data.periodo,
            "detalle": data.detalle,
            "referencia_archivo": data.referencia_archivo,
            "tamano_kb": data.tamano_kb,
            "estado": FacturaEstado.PENDIENTE,
            "cargada_at": date.today(),
        })
        if actor_id is not None:
            await AuditLogRepository(self._session, self._repo.tenant_id).create(
                actor_id,
                "FACTURA_REGISTRAR",
                detalle={"factura_id": str(obj.id), "periodo": obj.periodo},
                filas_afectadas=1,
            )
        return _factura_response(obj)

    async def listar(
        self,
        *,
        estado: str | None = None,
        usuario_id: UUID | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[FacturaResponse]:
        rows = await self._repo.listar_filtrado(estado=estado, usuario_id=usuario_id, desde=desde, hasta=hasta)
        return [_factura_response(row) for row in rows]

    async def marcar_abonada(
        self,
        factura_id: UUID,
        data: FacturaPagoConfirm,
        *,
        actor_id: UUID | None = None,
    ) -> FacturaResponse:
        if not data.confirmar:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Confirmacion requerida")
        obj = await self._repo.get_by_id(factura_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
        obj = await self._repo.update(obj, {"estado": FacturaEstado.ABONADA, "abonada_at": date.today()})
        await self._session.refresh(obj)
        if actor_id is not None:
            await AuditLogRepository(self._session, self._repo.tenant_id).create(
                actor_id,
                "FACTURA_ABONAR",
                detalle={"factura_id": str(obj.id), "periodo": obj.periodo},
                filas_afectadas=1,
            )
        return _factura_response(obj)

    async def resolver_descarga(self, factura_id: UUID) -> FacturaDescargaResponse:
        obj = await self._repo.get_by_id(factura_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
        return FacturaDescargaResponse(id=obj.id, referencia_archivo=obj.referencia_archivo)
