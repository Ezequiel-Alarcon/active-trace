"""Estructura academica service (C-06 §3).

Implements business rules for ABM of carrera, cohorte and materia.
Validations (unicity, active carrera for cohortes, date ranges) live here.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.repositories.base import get_tenant_repository
from app.schemas.estructura import (
    CarreraCreate,
    CarreraUpdate,
    CohorteCreate,
    CohorteUpdate,
    MateriaCreate,
    MateriaUpdate,
)


class EstructuraService:
    """ABM service for estructura academica, scoped to a single tenant."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── Carrera ──────────────────────────────────────────────────────

    async def create_carrera(self, data: CarreraCreate) -> Carrera:
        repo = get_tenant_repository(Carrera, self._session)
        existing = await repo.list(filters=[Carrera.codigo == data.codigo])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una carrera con ese codigo en este tenant",
            )
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "codigo": data.codigo,
            "nombre": data.nombre,
        })
        return obj

    async def update_carrera(self, carrera_id: UUID, data: CarreraUpdate) -> Carrera:
        repo = get_tenant_repository(Carrera, self._session)
        obj = await repo.get_by_id(carrera_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")

        update_data: dict = {}
        if data.codigo is not None and data.codigo != obj.codigo:
            existing = await repo.list(filters=[Carrera.codigo == data.codigo])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una carrera con ese codigo en este tenant",
                )
            update_data["codigo"] = data.codigo
        if data.nombre is not None:
            update_data["nombre"] = data.nombre
        if data.estado is not None:
            update_data["estado"] = CarreraEstado(data.estado)

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def get_carrera(self, carrera_id: UUID) -> Carrera:
        repo = get_tenant_repository(Carrera, self._session)
        obj = await repo.get_by_id(carrera_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
        return obj

    async def list_carreras(self, *, estado: str | None = None) -> list[Carrera]:
        repo = get_tenant_repository(Carrera, self._session)
        filters = []
        if estado is not None:
            filters.append(Carrera.estado == estado)
        result = await repo.list(filters=filters if filters else None)
        return list(result)

    async def delete_carrera(self, carrera_id: UUID) -> None:
        repo = get_tenant_repository(Carrera, self._session)
        obj = await repo.get_by_id(carrera_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrera no encontrada")
        await repo.soft_delete(obj)

    # ── Cohorte ──────────────────────────────────────────────────────

    async def _get_carrera_or_raise(self, carrera_id: UUID) -> Carrera:
        repo = get_tenant_repository(Carrera, self._session)
        carrera = await repo.get_by_id(carrera_id)
        if carrera is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La carrera especificada no existe",
            )
        return carrera

    async def create_cohorte(self, data: CohorteCreate) -> Cohorte:
        carrera = await self._get_carrera_or_raise(data.carrera_id)
        if carrera.estado != CarreraEstado.ACTIVA:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede crear una cohorte para una carrera inactiva",
            )
        if data.vig_hasta is not None and data.vig_hasta < data.vig_desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="vig_hasta debe ser posterior a vig_desde",
            )

        repo = get_tenant_repository(Cohorte, self._session)
        existing = await repo.list(
            filters=[
                Cohorte.carrera_id == data.carrera_id,
                Cohorte.nombre == data.nombre,
            ]
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cohorte con ese nombre para esta carrera en este tenant",
            )

        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "carrera_id": data.carrera_id,
            "nombre": data.nombre,
            "anio": data.anio,
            "vig_desde": data.vig_desde,
            "vig_hasta": data.vig_hasta,
        })
        return obj

    async def update_cohorte(self, cohorte_id: UUID, data: CohorteUpdate) -> Cohorte:
        repo = get_tenant_repository(Cohorte, self._session)
        obj = await repo.get_by_id(cohorte_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")

        update_data: dict = {}
        if data.nombre is not None and data.nombre != obj.nombre:
            existing = await repo.list(
                filters=[
                    Cohorte.carrera_id == obj.carrera_id,
                    Cohorte.nombre == data.nombre,
                ]
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una cohorte con ese nombre para esta carrera en este tenant",
                )
            update_data["nombre"] = data.nombre
        if data.anio is not None:
            update_data["anio"] = data.anio
        if data.vig_desde is not None:
            update_data["vig_desde"] = data.vig_desde
        if data.vig_hasta is not None:
            update_data["vig_hasta"] = data.vig_hasta
        if data.estado is not None:
            new_estado = CohorteEstado(data.estado)
            if new_estado == CohorteEstado.ACTIVA and obj.estado != CohorteEstado.ACTIVA:
                carrera = await self._get_carrera_or_raise(obj.carrera_id)
                if carrera.estado != CarreraEstado.ACTIVA:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="No se puede activar una cohorte si la carrera esta inactiva",
                    )
            update_data["estado"] = new_estado

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def get_cohorte(self, cohorte_id: UUID) -> Cohorte:
        repo = get_tenant_repository(Cohorte, self._session)
        obj = await repo.get_by_id(cohorte_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")
        return obj

    async def list_cohortes(
        self, *, carrera_id: UUID | None = None, estado: str | None = None
    ) -> list[Cohorte]:
        repo = get_tenant_repository(Cohorte, self._session)
        filters = []
        if carrera_id is not None:
            filters.append(Cohorte.carrera_id == carrera_id)
        if estado is not None:
            filters.append(Cohorte.estado == estado)
        result = await repo.list(filters=filters if filters else None)
        return list(result)

    async def delete_cohorte(self, cohorte_id: UUID) -> None:
        repo = get_tenant_repository(Cohorte, self._session)
        obj = await repo.get_by_id(cohorte_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")
        await repo.soft_delete(obj)

    # ── Materia ──────────────────────────────────────────────────────

    async def create_materia(self, data: MateriaCreate) -> Materia:
        repo = get_tenant_repository(Materia, self._session)
        existing = await repo.list(filters=[Materia.codigo == data.codigo])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una materia con ese codigo en este tenant",
            )
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "codigo": data.codigo,
            "nombre": data.nombre,
        })
        return obj

    async def update_materia(self, materia_id: UUID, data: MateriaUpdate) -> Materia:
        repo = get_tenant_repository(Materia, self._session)
        obj = await repo.get_by_id(materia_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")

        update_data: dict = {}
        if data.codigo is not None and data.codigo != obj.codigo:
            existing = await repo.list(filters=[Materia.codigo == data.codigo])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una materia con ese codigo en este tenant",
                )
            update_data["codigo"] = data.codigo
        if data.nombre is not None:
            update_data["nombre"] = data.nombre
        if data.estado is not None:
            update_data["estado"] = MateriaEstado(data.estado)

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def get_materia(self, materia_id: UUID) -> Materia:
        repo = get_tenant_repository(Materia, self._session)
        obj = await repo.get_by_id(materia_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
        return obj

    async def list_materias(self, *, estado: str | None = None) -> list[Materia]:
        repo = get_tenant_repository(Materia, self._session)
        filters = []
        if estado is not None:
            filters.append(Materia.estado == estado)
        result = await repo.list(filters=filters if filters else None)
        return list(result)

    async def delete_materia(self, materia_id: UUID) -> None:
        repo = get_tenant_repository(Materia, self._session)
        obj = await repo.get_by_id(materia_id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
        await repo.soft_delete(obj)
