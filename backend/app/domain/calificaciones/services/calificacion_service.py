"""Calificacion service (C-10).

Servicio para gestionar calificaciones con logica de aprobado derivada.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calificaciones.repositories.calificacion import CalificacionRepository
from app.domain.calificaciones.repositories.umbral_materia import UmbralMateriaRepository
from app.domain.calificaciones.schemas.calificacion import CalificacionRead
from app.domain.calificaciones.services.aprobado import derivar_aprobado


class CalificacionServiceError(Exception):
    pass


class CalificacionNotFoundError(CalificacionServiceError):
    pass


class CalificacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = CalificacionRepository(session, tenant_id)
        self._umbral_repo = UmbralMateriaRepository(session, tenant_id)

    async def list_calificaciones(
        self,
        *,
        materia_id: UUID | None = None,
        usuario_id: UUID | None = None,
        asignacion_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CalificacionRead]:
        calificaciones = await self._repo.get_filtered(
            materia_id=materia_id,
            usuario_id=usuario_id,
            asignacion_id=asignacion_id,
            limit=limit,
            offset=offset,
        )
        results: list[CalificacionRead] = []
        for c in calificaciones:
            umbral = await self._umbral_repo.get_by_materia_asignacion(
                c.materia_id,
                c.asignacion_id,
            )
            if umbral is None:
                default = await self._umbral_repo.get_default_for_materia(c.materia_id)
                umbral_pct = default["umbral_pct"]
                conjunto = default["conjunto_aprobado"]
            else:
                umbral_pct = umbral.umbral_pct
                conjunto = umbral.conjunto_aprobado
            aprobado = derivar_aprobado(c.nota, umbral_pct, conjunto)
            results.append(CalificacionRead(
                id=c.id,
                tenant_id=c.tenant_id,
                materia_id=c.materia_id,
                usuario_id=c.usuario_id,
                asignacion_id=c.asignacion_id,
                version_padron_id=c.version_padron_id,
                nota=c.nota,
                origen=c.origen,
                import_batch_id=c.import_batch_id,
                created_at=c.created_at,
                updated_at=c.updated_at,
                aprobado=aprobado,
            ))
        return results

    async def create_calificacion(
        self,
        data: dict[str, Any],
        created_by: UUID,
    ) -> CalificacionRead:
        data["created_by"] = created_by
        obj = await self._repo.create(data)
        umbral = await self._umbral_repo.get_by_materia_asignacion(
            obj.materia_id,
            obj.asignacion_id,
        )
        if umbral is None:
            default = await self._umbral_repo.get_default_for_materia(obj.materia_id)
            umbral_pct = default["umbral_pct"]
            conjunto = default["conjunto_aprobado"]
        else:
            umbral_pct = umbral.umbral_pct
            conjunto = umbral.conjunto_aprobado
        aprobado = derivar_aprobado(obj.nota, umbral_pct, conjunto)
        return CalificacionRead(
            id=obj.id,
            tenant_id=obj.tenant_id,
            materia_id=obj.materia_id,
            usuario_id=obj.usuario_id,
            asignacion_id=obj.asignacion_id,
            version_padron_id=obj.version_padron_id,
            nota=obj.nota,
            origen=obj.origen,
            import_batch_id=obj.import_batch_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            aprobado=aprobado,
        )

    async def get_calificacion_by_id(self, calificacion_id: UUID) -> CalificacionRead:
        obj = await self._repo.get_by_id(calificacion_id)
        if obj is None:
            raise CalificacionNotFoundError(f"Calificacion {calificacion_id} no encontrada")
        umbral = await self._umbral_repo.get_by_materia_asignacion(
            obj.materia_id,
            obj.asignacion_id,
        )
        if umbral is None:
            default = await self._umbral_repo.get_default_for_materia(obj.materia_id)
            umbral_pct = default["umbral_pct"]
            conjunto = default["conjunto_aprobado"]
        else:
            umbral_pct = umbral.umbral_pct
            conjunto = umbral.conjunto_aprobado
        aprobado = derivar_aprobado(obj.nota, umbral_pct, conjunto)
        return CalificacionRead(
            id=obj.id,
            tenant_id=obj.tenant_id,
            materia_id=obj.materia_id,
            usuario_id=obj.usuario_id,
            asignacion_id=obj.asignacion_id,
            version_padron_id=obj.version_padron_id,
            nota=obj.nota,
            origen=obj.origen,
            import_batch_id=obj.import_batch_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            aprobado=aprobado,
        )