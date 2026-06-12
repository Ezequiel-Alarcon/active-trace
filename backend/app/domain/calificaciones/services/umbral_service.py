"""UmbralMateria service (C-10).

Servicio para gestionar umbrales de aprobacion.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calificaciones.models.umbral_materia import UmbralMateria
from app.domain.calificaciones.repositories.umbral_materia import UmbralMateriaRepository
from app.domain.calificaciones.schemas.umbral_materia import (
    UmbralMateriaRead,
    UmbralMateriaUpdate,
)


class UmbralServiceError(Exception):
    pass


class UmbralNotFoundError(UmbralServiceError):
    pass


class UmbralDuplicateError(UmbralServiceError):
    pass


class UmbralService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = UmbralMateriaRepository(session, tenant_id)

    async def get_umbral_for_asignacion(
        self,
        materia_id: UUID,
        asignacion_id: UUID | None,
    ) -> dict[str, Any]:
        umbral = await self._repo.get_by_materia_asignacion(materia_id, asignacion_id)
        if umbral is None:
            return await self._repo.get_default_for_materia(materia_id)
        return {
            "umbral_pct": umbral.umbral_pct,
            "conjunto_aprobado": umbral.conjunto_aprobado,
        }

    async def list_umbrales(
        self,
        *,
        materia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UmbralMateriaRead]:
        filters = []
        if materia_id is not None:
            filters.append(UmbralMateria.materia_id == materia_id)
        objects = await self._repo.list(limit=limit, offset=offset, filters=filters)
        return [self._to_read(o) for o in objects]

    async def create_umbral(self, data: dict[str, Any]) -> UmbralMateriaRead:
        existing = await self._repo.get_by_materia_asignacion(
            data["materia_id"],
            data.get("asignacion_id"),
        )
        if existing is not None:
            raise UmbralDuplicateError(
                "Ya existe un umbral para esta materia y asignación"
            )
        obj = await self._repo.create(data)
        return self._to_read(obj)

    async def update_umbral(
        self,
        umbral_id: UUID,
        data: UmbralMateriaUpdate,
    ) -> UmbralMateriaRead:
        obj = await self._repo.get_by_id(umbral_id)
        if obj is None:
            raise UmbralNotFoundError(f"Umbral {umbral_id} no encontrado")
        update_data = data.model_dump(exclude_unset=True)
        obj = await self._repo.update(obj, update_data)
        return self._to_read(obj)

    def _to_read(self, obj: UmbralMateria) -> UmbralMateriaRead:
        return UmbralMateriaRead(
            id=obj.id,
            tenant_id=obj.tenant_id,
            materia_id=obj.materia_id,
            asignacion_id=obj.asignacion_id,
            umbral_pct=obj.umbral_pct,
            conjunto_aprobado=obj.conjunto_aprobado,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )