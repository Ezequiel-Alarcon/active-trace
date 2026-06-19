"""Guardias service (C-18 §6).

Implements business rules for ABM of Guardia with role-based scope:
TUTOR sees/edits only own guardias; COORDINADOR/ADMIN see all.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia
from app.repositories.base import get_tenant_repository
from app.repositories.guardias import GuardiaRepository
from app.schemas.guardias import GuardiaCreate, GuardiaUpdate


class GuardiaService:
    """ABM service for guardias, scoped to a single tenant and current user.

    Role-based filtering:
    - TUTOR: only sees/edits own guardias (tutor_id == current_user_id).
    - COORDINADOR/ADMIN: see all guardias in the tenant.
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        current_user_id: UUID,
        current_user_permissions: set[str],
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._current_user_id = current_user_id
        self._current_user_permissions = current_user_permissions
        self._guardia_repo = GuardiaRepository(session, tenant_id)

    @property
    def _is_tutor_only(self) -> bool:
        return "encuentros:gestionar" not in self._current_user_permissions

    # ── CRUD ──────────────────────────────────────────────────────────

    async def create_guardia(self, data: GuardiaCreate) -> Guardia:
        repo = get_tenant_repository(Guardia, self._session)
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "tutor_id": self._current_user_id,
            "materia_id": data.materia_id,
            "cohorte_id": data.cohorte_id,
            "fecha": data.fecha,
            "hora_inicio": data.hora_inicio,
            "hora_fin": data.hora_fin,
            "titulo": data.titulo,
            "observaciones": data.observaciones,
        })
        return obj

    async def get_guardia(self, guardia_id: UUID) -> Guardia:
        repo = get_tenant_repository(Guardia, self._session)
        obj = await repo.get_by_id(guardia_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )
        if self._is_tutor_only and obj.tutor_id != self._current_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )
        return obj

    async def list_guardias(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[Guardia]:
        repo = get_tenant_repository(Guardia, self._session)
        filters = []
        if self._is_tutor_only:
            filters.append(Guardia.tutor_id == self._current_user_id)
        if materia_id is not None:
            filters.append(Guardia.materia_id == materia_id)
        if cohorte_id is not None:
            filters.append(Guardia.cohorte_id == cohorte_id)
        if fecha_desde is not None:
            filters.append(Guardia.fecha >= fecha_desde)
        if fecha_hasta is not None:
            filters.append(Guardia.fecha <= fecha_hasta)
        result = await repo.list(
            filters=filters if filters else None,
            order_by=[Guardia.fecha.desc()],
        )
        return list(result)

    async def update_guardia(self, guardia_id: UUID, data: GuardiaUpdate) -> Guardia:
        repo = get_tenant_repository(Guardia, self._session)
        obj = await repo.get_by_id(guardia_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )
        if self._is_tutor_only and obj.tutor_id != self._current_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )

        update_data: dict = {}
        if data.fecha is not None:
            update_data["fecha"] = data.fecha
        if data.hora_inicio is not None:
            update_data["hora_inicio"] = data.hora_inicio
        if data.hora_fin is not None:
            update_data["hora_fin"] = data.hora_fin
        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.observaciones is not None:
            update_data["observaciones"] = data.observaciones

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def delete_guardia(self, guardia_id: UUID) -> None:
        repo = get_tenant_repository(Guardia, self._session)
        obj = await repo.get_by_id(guardia_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )
        if self._is_tutor_only and obj.tutor_id != self._current_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )
        await repo.soft_delete(obj)

    # ── Export CSV ────────────────────────────────────────────────────

    async def export_guardias_csv(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> str:
        """Generate CSV string with guardias data, joining usuario.nombre,
        materia.codigo, cohorte.nombre. Only for COORDINADOR/ADMIN."""
        repo = get_tenant_repository(Guardia, self._session)
        filters = []
        if materia_id is not None:
            filters.append(Guardia.materia_id == materia_id)
        if cohorte_id is not None:
            filters.append(Guardia.cohorte_id == cohorte_id)
        if fecha_desde is not None:
            filters.append(Guardia.fecha >= fecha_desde)
        if fecha_hasta is not None:
            filters.append(Guardia.fecha <= fecha_hasta)

        guardias = await repo.list(
            filters=filters if filters else None,
            order_by=[Guardia.fecha.desc()],
            limit=10000,
        )

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "tutor_nombre",
                "materia_codigo",
                "cohorte_nombre",
                "fecha",
                "hora_inicio",
                "hora_fin",
                "titulo",
                "observaciones",
            ],
        )
        writer.writeheader()

        for g in guardias:
            tutor_nombre = await self._resolve_tutor_nombre(g.tutor_id)
            materia_codigo = await self._resolve_materia_codigo(g.materia_id)
            cohorte_nombre = await self._resolve_cohorte_nombre(g.cohorte_id)
            writer.writerow({
                "tutor_nombre": tutor_nombre,
                "materia_codigo": materia_codigo,
                "cohorte_nombre": cohorte_nombre,
                "fecha": g.fecha.isoformat(),
                "hora_inicio": g.hora_inicio.strftime("%H:%M"),
                "hora_fin": g.hora_fin.strftime("%H:%M"),
                "titulo": g.titulo or "",
                "observaciones": g.observaciones or "",
            })

        return output.getvalue()

    async def _resolve_tutor_nombre(self, tutor_id: UUID) -> str:
        return await self._guardia_repo.resolve_tutor_nombre(tutor_id)

    async def _resolve_materia_codigo(self, materia_id: UUID) -> str:
        return await self._guardia_repo.resolve_materia_codigo(materia_id)

    async def _resolve_cohorte_nombre(self, cohorte_id: UUID) -> str:
        return await self._guardia_repo.resolve_cohorte_nombre(cohorte_id)

    async def resolve_tutor_nombre(self, tutor_id: UUID) -> str:
        """Public method so the router can populate tutor_nombre in responses."""
        return await self._resolve_tutor_nombre(tutor_id)
