"""Equipos docentes service (C-08).

Operaciones batch sobre asignaciones: mis-equipos, asignacion masiva,
clonar entre cohortes, vigencia general y export CSV.
"""

from __future__ import annotations

import csv
import io
from datetime import date as DateType
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import ASIGNACION_MODIFICAR, audit_emit
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.rbac.models import Rol
from app.repositories.base import get_tenant_repository
from app.repositories.usuarios import decrypt_usuario_fields
from app.schemas.equipos import (
    AsignacionFallida,
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    ClonadoFallido,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    EquipoAsignacionResponse,
    VigenciaEquipoRequest,
    VigenciaEquipoResponse,
)


class EquipoService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _asignacion_repo(self):
        return get_tenant_repository(Asignacion, self._session)

    async def _get_usuario(self, usuario_id: UUID) -> Usuario | None:
        repo = get_tenant_repository(Usuario, self._session)
        return await repo.get_by_id(usuario_id)

    async def _get_rol(self, rol_id: UUID) -> Rol | None:
        repo = get_tenant_repository(Rol, self._session)
        return await repo.get_by_id(rol_id)

    async def _get_materia(self, materia_id: UUID) -> Materia | None:
        repo = get_tenant_repository(Materia, self._session)
        return await repo.get_by_id(materia_id)

    async def _get_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        repo = get_tenant_repository(Cohorte, self._session)
        return await repo.get_by_id(cohorte_id)

    async def _get_carrera(self, carrera_id: UUID) -> Carrera | None:
        repo = get_tenant_repository(Carrera, self._session)
        return await repo.get_by_id(carrera_id)

    async def _resolve_contexto_nombre(
        self, contexto_tipo: ContextoTipo, contexto_id: UUID | None
    ) -> str:
        if contexto_tipo == ContextoTipo.GLOBAL or contexto_id is None:
            return "Global"
        if contexto_tipo == ContextoTipo.CARRERA:
            obj = await self._get_carrera(contexto_id)
            return obj.nombre if obj else "Carrera (no encontrada)"
        if contexto_tipo == ContextoTipo.COHORTE:
            obj = await self._get_cohorte(contexto_id)
            return obj.nombre if obj else "Cohorte (no encontrada)"
        if contexto_tipo == ContextoTipo.MATERIA:
            obj = await self._get_materia(contexto_id)
            return obj.nombre if obj else "Materia (no encontrada)"
        return "Desconocido"

    async def _build_equipo_response(self, asignacion: Asignacion) -> EquipoAsignacionResponse:
        usuario = await self._get_usuario(asignacion.usuario_id)
        rol = await self._get_rol(asignacion.rol_id)
        nombre_contexto = await self._resolve_contexto_nombre(
            asignacion.contexto_tipo, asignacion.contexto_id
        )

        usuario_fields = decrypt_usuario_fields(usuario) if usuario else {}
        return EquipoAsignacionResponse(
            id=asignacion.id,
            tenant_id=asignacion.tenant_id,
            usuario_id=asignacion.usuario_id,
            rol_id=asignacion.rol_id,
            contexto_tipo=asignacion.contexto_tipo.value,
            contexto_id=asignacion.contexto_id,
            responsable_id=asignacion.responsable_id,
            desde=asignacion.desde,
            hasta=asignacion.hasta,
            estado_vigencia=asignacion.estado_vigencia,
            created_at=asignacion.created_at,
            updated_at=asignacion.updated_at,
            nombre_usuario=usuario.nombre if usuario else "",
            apellidos_usuario=usuario.apellidos if usuario else "",
            email_usuario=usuario_fields.get("email", ""),
            nombre_rol=rol.nombre if rol else "",
            nombre_contexto=nombre_contexto,
        )

    # ── mis_equipos ─────────────────────────────────────────────────────

    async def mis_equipos(
        self,
        usuario_id: UUID,
        *,
        cohorte_id: UUID | None = None,
        materia_id: UUID | None = None,
        estado_vigencia: str | None = None,
    ) -> list[EquipoAsignacionResponse]:
        repo = self._asignacion_repo()
        filters = [Asignacion.usuario_id == usuario_id]
        if materia_id is not None:
            filters.append(Asignacion.contexto_tipo == ContextoTipo.MATERIA)
            filters.append(Asignacion.contexto_id == materia_id)
        if cohorte_id is not None:
            filters.append(Asignacion.contexto_tipo == ContextoTipo.COHORTE)
            filters.append(Asignacion.contexto_id == cohorte_id)
        objs = await repo.list(limit=200, offset=0, filters=filters)
        result: list[EquipoAsignacionResponse] = []
        for obj in objs:
            if estado_vigencia is not None and obj.estado_vigencia != estado_vigencia:
                continue
            resp = await self._build_equipo_response(obj)
            result.append(resp)
        return result

    # ── asignacion_masiva ───────────────────────────────────────────────

    async def asignacion_masiva(
        self, data: AsignacionMasivaRequest
    ) -> AsignacionMasivaResponse:
        if data.hasta is not None and data.hasta < data.desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hasta debe ser posterior a desde",
            )

        contexto_tipo = ContextoTipo(data.contexto_tipo)

        rol = await self._get_rol(data.rol_id)
        if rol is None:
            fallidas = [
                AsignacionFallida(usuario_id=uid, motivo="El rol especificado no existe")
                for uid in data.usuarios_ids
            ]
            return AsignacionMasivaResponse(creadas=[], fallidas=fallidas)

        if contexto_tipo != ContextoTipo.GLOBAL and data.contexto_id is not None:
            ctx_exists = False
            if contexto_tipo == ContextoTipo.CARRERA:
                ctx_exists = (await self._get_carrera(data.contexto_id)) is not None
            elif contexto_tipo == ContextoTipo.COHORTE:
                ctx_exists = (await self._get_cohorte(data.contexto_id)) is not None
            elif contexto_tipo == ContextoTipo.MATERIA:
                ctx_exists = (await self._get_materia(data.contexto_id)) is not None

            if not ctx_exists:
                fallidas = [
                    AsignacionFallida(
                        usuario_id=uid,
                        motivo=f"El contexto {data.contexto_tipo} especificado no existe",
                    )
                    for uid in data.usuarios_ids
                ]
                return AsignacionMasivaResponse(creadas=[], fallidas=fallidas)

        if data.responsable_id is not None:
            responsable = await self._get_usuario(data.responsable_id)
            if responsable is None:
                fallidas = [
                    AsignacionFallida(usuario_id=uid, motivo="El responsable especificado no existe")
                    for uid in data.usuarios_ids
                ]
                return AsignacionMasivaResponse(creadas=[], fallidas=fallidas)

        repo = self._asignacion_repo()
        creadas: list[EquipoAsignacionResponse] = []
        fallidas: list[AsignacionFallida] = []

        for usuario_id in data.usuarios_ids:
            usuario = await self._get_usuario(usuario_id)
            if usuario is None:
                fallidas.append(
                    AsignacionFallida(
                        usuario_id=usuario_id, motivo="El usuario especificado no existe"
                    )
                )
                continue

            create_dict = {
                "usuario_id": usuario_id,
                "rol_id": data.rol_id,
                "contexto_tipo": contexto_tipo,
                "contexto_id": data.contexto_id,
                "responsable_id": data.responsable_id,
                "desde": data.desde,
                "hasta": data.hasta,
                "tenant_id": self._tenant_id,
            }
            try:
                obj = await repo.create(create_dict)
                resp = await self._build_equipo_response(obj)
                creadas.append(resp)
                audit_emit(
                    ASIGNACION_MODIFICAR,
                    entity="asignacion",
                    entity_id=obj.id,
                    tenant_id=self._tenant_id,
                    op="asignacion_masiva",
                )
            except Exception as e:
                fallidas.append(
                    AsignacionFallida(usuario_id=usuario_id, motivo=str(e))
                )

        return AsignacionMasivaResponse(creadas=creadas, fallidas=fallidas)

    # ── clonar_equipo ───────────────────────────────────────────────────

    async def clonar_equipo(self, data: ClonarEquipoRequest) -> ClonarEquipoResponse:
        if data.hasta is not None and data.hasta < data.desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hasta debe ser posterior a desde",
            )

        origen = await self._get_cohorte(data.cohorte_origen_id)
        if origen is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La cohorte origen especificada no existe",
            )

        destino = await self._get_cohorte(data.cohorte_destino_id)
        if destino is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La cohorte destino especificada no existe",
            )

        repo = self._asignacion_repo()
        # Obtener todas las asignaciones del cohorte origen (contexto Cohorte)
        # y tambien las de materia (ya que pueden ser parte del equipo)
        # Solo vigentes (filtrado post-query via estado_vigencia)
        origen_objs = await repo.list(
            limit=2000,
            offset=0,
            filters=[
                Asignacion.contexto_tipo == ContextoTipo.COHORTE,
                Asignacion.contexto_id == data.cohorte_origen_id,
            ],
        )

        # Filtrar solo vigentes
        vigentes = [a for a in origen_objs if a.estado_vigencia == "Vigente"]

        creados: list[Asignacion] = []
        omitidas = 0
        fallidas: list[ClonadoFallido] = []

        for orig in vigentes:
            # Determinar nuevo contexto_id
            nuevo_contexto_id = orig.contexto_id
            if orig.contexto_tipo == ContextoTipo.COHORTE:
                nuevo_contexto_id = data.cohorte_destino_id

            # Verificar duplicado en destino
            dup_filters = [
                Asignacion.usuario_id == orig.usuario_id,
                Asignacion.rol_id == orig.rol_id,
                Asignacion.contexto_tipo == orig.contexto_tipo,
                Asignacion.contexto_id == nuevo_contexto_id,
            ]
            dups = await repo.list(limit=1, offset=0, filters=dup_filters)
            if dups:
                omitidas += 1
                continue

            create_dict = {
                "usuario_id": orig.usuario_id,
                "rol_id": orig.rol_id,
                "contexto_tipo": orig.contexto_tipo,
                "contexto_id": nuevo_contexto_id,
                "responsable_id": orig.responsable_id,
                "desde": data.desde,
                "hasta": data.hasta,
                "tenant_id": self._tenant_id,
            }
            try:
                obj = await repo.create(create_dict)
                creados.append(obj)
                audit_emit(
                    ASIGNACION_MODIFICAR,
                    entity="asignacion",
                    entity_id=obj.id,
                    tenant_id=self._tenant_id,
                    op="clonar_equipo",
                )
            except Exception:
                # Rollback manual: soft-delete las ya creadas
                for creado in creados:
                    await repo.soft_delete(creado)
                fallidas.append(
                    ClonadoFallido(
                        asignacion_origen_id=orig.id,
                        motivo="Error inesperado durante el clonado; se revirtieron las asignaciones creadas",
                    )
                )
                return ClonarEquipoResponse(
                    creadas=0, omitidas=0, fallidas=fallidas
                )

        return ClonarEquipoResponse(
            creadas=len(creados), omitidas=omitidas, fallidas=[]
        )

    # ── modificar_vigencia ──────────────────────────────────────────────

    async def modificar_vigencia(
        self, data: VigenciaEquipoRequest
    ) -> VigenciaEquipoResponse:
        if data.hasta is not None and data.hasta < data.desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hasta debe ser posterior a desde",
            )

        materia = await self._get_materia(data.materia_id)
        if materia is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La materia especificada no existe",
            )

        cohorte = await self._get_cohorte(data.cohorte_id)
        if cohorte is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La cohorte especificada no existe",
            )

        if data.rol_id is not None:
            rol = await self._get_rol(data.rol_id)
            if rol is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El rol especificado no existe",
                )

        repo = self._asignacion_repo()

        # Encontrar asignaciones vigentes que coincidan con materia Y cohorte
        # Un equipo docente puede tener asignaciones con contexto Materia Y con contexto Cohorte
        filters = [
            or_(
                (Asignacion.contexto_tipo == ContextoTipo.MATERIA)
                & (Asignacion.contexto_id == data.materia_id),
                (Asignacion.contexto_tipo == ContextoTipo.COHORTE)
                & (Asignacion.contexto_id == data.cohorte_id),
            )
        ]
        if data.rol_id is not None:
            filters.append(Asignacion.rol_id == data.rol_id)

        objs = await repo.list(limit=2000, offset=0, filters=filters)
        vigentes = [a for a in objs if a.estado_vigencia == "Vigente"]

        actualizadas = 0
        for obj in vigentes:
            update_data = {"desde": data.desde, "hasta": data.hasta}
            await repo.update(obj, update_data)
            actualizadas += 1
            audit_emit(
                ASIGNACION_MODIFICAR,
                entity="asignacion",
                entity_id=obj.id,
                tenant_id=self._tenant_id,
                op="modificar_vigencia",
            )

        return VigenciaEquipoResponse(actualizadas=actualizadas)

    # ── exportar_equipo ─────────────────────────────────────────────────

    async def exportar_equipo_data(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        rol_id: UUID | None = None,
    ) -> list[dict[str, str]]:
        repo = self._asignacion_repo()

        filters = [
            or_(
                (Asignacion.contexto_tipo == ContextoTipo.MATERIA)
                & (Asignacion.contexto_id == materia_id),
                (Asignacion.contexto_tipo == ContextoTipo.COHORTE)
                & (Asignacion.contexto_id == cohorte_id),
            )
        ]
        if rol_id is not None:
            filters.append(Asignacion.rol_id == rol_id)

        objs = await repo.list(limit=5000, offset=0, filters=filters)

        materia = await self._get_materia(materia_id)
        cohorte = await self._get_cohorte(cohorte_id)
        nombre_materia = materia.nombre if materia else ""
        nombre_cohorte = cohorte.nombre if cohorte else ""
        nombre_carrera = ""
        if cohorte:
            carrera = await self._get_carrera(cohorte.carrera_id)
            nombre_carrera = carrera.nombre if carrera else ""

        rows: list[dict[str, str]] = []
        for asignacion in objs:
            usuario = await self._get_usuario(asignacion.usuario_id)
            if usuario is None:
                continue
            usuario_fields = decrypt_usuario_fields(usuario)

            rol = await self._get_rol(asignacion.rol_id)
            nombre_rol = rol.nombre if rol else ""

            rows.append(
                {
                    "nombre": usuario.nombre,
                    "apellidos": usuario.apellidos,
                    "email": usuario_fields.get("email", ""),
                    "rol": nombre_rol,
                    "materia": nombre_materia,
                    "carrera": nombre_carrera,
                    "cohorte": nombre_cohorte,
                    "desde": str(asignacion.desde),
                    "hasta": str(asignacion.hasta) if asignacion.hasta else "",
                    "estado_vigencia": asignacion.estado_vigencia,
                }
            )

        return rows

    def generate_csv(self, rows: list[dict[str, str]]) -> str:
        fieldnames = [
            "nombre",
            "apellidos",
            "email",
            "rol",
            "materia",
            "carrera",
            "cohorte",
            "desde",
            "hasta",
            "estado_vigencia",
        ]
        output = io.StringIO()
        output.write("\ufeff")  # BOM UTF-8
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return output.getvalue()
