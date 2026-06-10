"""Programas y Fechas Academicas service (C-17 §3).

Implements business rules for ABM of ProgramaMateria and FechaAcademica.
Validations (unicity, FK existence) live here. Fragmento LMS generation
is implemented server-side as string formatting, not Jinja2.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica
from app.models.programa_materia import ProgramaMateria
from app.repositories.base import get_tenant_repository
from app.schemas.programas_fechas import (
    FechaAcademicaCreate,
    FechaAcademicaUpdate,
    ProgramaCreate,
    ProgramaUpdate,
)


class ProgramaFechasService:
    """ABM service for programas and fechas, scoped to a single tenant."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── ProgramaMateria ───────────────────────────────────────────────

    async def create_programa(self, data: ProgramaCreate) -> ProgramaMateria:
        repo = get_tenant_repository(ProgramaMateria, self._session)
        existing = await repo.list(
            filters=[
                ProgramaMateria.materia_id == data.materia_id,
                ProgramaMateria.carrera_id == data.carrera_id,
                ProgramaMateria.cohorte_id == data.cohorte_id,
            ]
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un programa para esa materia, carrera y cohorte en este tenant",
            )
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "materia_id": data.materia_id,
            "carrera_id": data.carrera_id,
            "cohorte_id": data.cohorte_id,
            "titulo": data.titulo,
            "referencia_archivo": data.referencia_archivo,
        })
        return obj

    async def update_programa(self, programa_id: UUID, data: ProgramaUpdate) -> ProgramaMateria:
        repo = get_tenant_repository(ProgramaMateria, self._session)
        obj = await repo.get_by_id(programa_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa no encontrado",
            )

        update_data: dict = {}
        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.referencia_archivo is not None:
            update_data["referencia_archivo"] = data.referencia_archivo

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def get_programa(self, programa_id: UUID) -> ProgramaMateria:
        repo = get_tenant_repository(ProgramaMateria, self._session)
        obj = await repo.get_by_id(programa_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa no encontrado",
            )
        return obj

    async def list_programas(
        self,
        *,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[ProgramaMateria]:
        repo = get_tenant_repository(ProgramaMateria, self._session)
        filters = []
        if materia_id is not None:
            filters.append(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            filters.append(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            filters.append(ProgramaMateria.cohorte_id == cohorte_id)
        result = await repo.list(filters=filters if filters else None)
        return list(result)

    async def delete_programa(self, programa_id: UUID) -> None:
        repo = get_tenant_repository(ProgramaMateria, self._session)
        obj = await repo.get_by_id(programa_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa no encontrado",
            )
        await repo.soft_delete(obj)

    # ── FechaAcademica ────────────────────────────────────────────────

    async def create_fecha(self, data: FechaAcademicaCreate) -> FechaAcademica:
        repo = get_tenant_repository(FechaAcademica, self._session)
        existing = await repo.list(
            filters=[
                FechaAcademica.materia_id == data.materia_id,
                FechaAcademica.cohorte_id == data.cohorte_id,
                FechaAcademica.tipo == data.tipo,
                FechaAcademica.numero_instancia == data.numero_instancia,
            ]
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una fecha de tipo {data.tipo} #{data.numero_instancia} "
                       f"para esta materia y cohorte en este tenant",
            )
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "materia_id": data.materia_id,
            "cohorte_id": data.cohorte_id,
            "tipo": TipoFechaAcademica(data.tipo),
            "numero_instancia": data.numero_instancia,
            "fecha": data.fecha,
            "titulo": data.titulo,
            "descripcion": data.descripcion,
        })
        return obj

    async def update_fecha(self, fecha_id: UUID, data: FechaAcademicaUpdate) -> FechaAcademica:
        repo = get_tenant_repository(FechaAcademica, self._session)
        obj = await repo.get_by_id(fecha_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha academica no encontrada",
            )

        update_data: dict = {}
        if data.fecha is not None:
            update_data["fecha"] = data.fecha
        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.descripcion is not None:
            update_data["descripcion"] = data.descripcion

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def get_fecha(self, fecha_id: UUID) -> FechaAcademica:
        repo = get_tenant_repository(FechaAcademica, self._session)
        obj = await repo.get_by_id(fecha_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha academica no encontrada",
            )
        return obj

    async def list_fechas(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        tipo: str | None = None,
    ) -> list[FechaAcademica]:
        repo = get_tenant_repository(FechaAcademica, self._session)
        filters = []
        if materia_id is not None:
            filters.append(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            filters.append(FechaAcademica.cohorte_id == cohorte_id)
        if tipo is not None:
            filters.append(FechaAcademica.tipo == tipo)
        result = await repo.list(
            filters=filters if filters else None,
            order_by=[FechaAcademica.fecha.asc()],
        )
        return list(result)

    async def delete_fecha(self, fecha_id: UUID) -> None:
        repo = get_tenant_repository(FechaAcademica, self._session)
        obj = await repo.get_by_id(fecha_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha academica no encontrada",
            )
        await repo.soft_delete(obj)

    # ── Fragmento LMS ─────────────────────────────────────────────────

    async def generar_fragmento_lms(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> str:
        """Generate an HTML fragment with fechas grouped by tipo for the given
        materia and cohorte. Fechas are ordered by numero_instancia within
        each group. Returns raw HTML string."""
        repo = get_tenant_repository(FechaAcademica, self._session)
        fechas = await repo.list(
            filters=[
                FechaAcademica.materia_id == materia_id,
                FechaAcademica.cohorte_id == cohorte_id,
            ],
            order_by=[
                FechaAcademica.tipo.asc(),
                FechaAcademica.numero_instancia.asc(),
            ],
        )

        if not fechas:
            return "<p>No hay fechas registradas para esta materia y cohorte.</p>"

        lines: list[str] = []
        lines.append('<div class="fechas-academicas">')
        lines.append(f'<h2>Fechas Academicas</h2>')

        current_tipo: TipoFechaAcademica | None = None
        for f in fechas:
            if f.tipo != current_tipo:
                if current_tipo is not None:
                    lines.append("</ul>")
                current_tipo = f.tipo
                lines.append(f"<h3>{f.tipo.value}</h3>")
                lines.append("<ul>")

            lines.append("<li>")
            parts: list[str] = []
            parts.append(f"<strong>#{f.numero_instancia}: {f.fecha.isoformat()}</strong>")
            if f.titulo:
                parts.append(f" — {f.titulo}")
            lines.append("".join(parts))
            if f.descripcion:
                lines.append(f'<br><span class="descripcion">{f.descripcion}</span>')
            lines.append("</li>")

        if current_tipo is not None:
            lines.append("</ul>")
        lines.append("</div>")

        return "\n".join(lines)
