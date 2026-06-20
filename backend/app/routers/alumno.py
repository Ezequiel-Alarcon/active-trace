"""Alumno router — estado académico propio.

GET /api/alumno/estado  → calificaciones + estado de aprobación del alumno autenticado.
Permiso requerido: academico:ver_estado_propio
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.domain.calificaciones.models.calificacion import Calificacion
from app.domain.calificaciones.models.umbral_materia import UmbralMateria
from app.models.materia import Materia

router = APIRouter(prefix="/api/alumno", tags=["alumno"])

PERM = "academico:ver_estado_propio"


class CalificacionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    materia_codigo: str
    materia_nombre: str
    nota: float | str | None
    aprobado: bool | None
    origen: str


class EstadoAcademicoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    calificaciones: list[CalificacionItem]


def _compute_aprobado(
    nota: float | int | str | list | None,
    umbral_pct: int,
    conjunto: list[str] | None,
) -> bool | None:
    if nota is None:
        return None
    if conjunto:
        return str(nota) in conjunto
    if isinstance(nota, (int, float)):
        return nota >= umbral_pct / 10
    return None


@router.get(
    "/estado",
    response_model=EstadoAcademicoResponse,
    summary="Mi estado académico",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_estado_academico(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EstadoAcademicoResponse:
    tenant_id = current_user.tenant_id
    user_id = current_user.user_id

    # Fetch calificaciones for this user
    stmt_cal = (
        select(Calificacion)
        .where(Calificacion.tenant_id == tenant_id)
        .where(Calificacion.usuario_id == user_id)
        .where(Calificacion.deleted_at.is_(None))
        .order_by(Calificacion.created_at)
    )
    result_cal = await db.execute(stmt_cal)
    calificaciones = result_cal.scalars().all()

    if not calificaciones:
        return EstadoAcademicoResponse(usuario_id=user_id, calificaciones=[])

    materia_ids = list({c.materia_id for c in calificaciones})

    # Fetch materias
    stmt_mat = (
        select(Materia)
        .where(Materia.tenant_id == tenant_id)
        .where(Materia.id.in_(materia_ids))
        .where(Materia.deleted_at.is_(None))
    )
    result_mat = await db.execute(stmt_mat)
    materias = {m.id: m for m in result_mat.scalars().all()}

    # Fetch umbrales
    stmt_umb = (
        select(UmbralMateria)
        .where(UmbralMateria.tenant_id == tenant_id)
        .where(UmbralMateria.materia_id.in_(materia_ids))
        .where(UmbralMateria.asignacion_id.is_(None))
        .where(UmbralMateria.deleted_at.is_(None))
    )
    result_umb = await db.execute(stmt_umb)
    umbrales = {u.materia_id: u for u in result_umb.scalars().all()}

    items: list[CalificacionItem] = []
    for cal in calificaciones:
        materia = materias.get(cal.materia_id)
        if not materia:
            continue
        umbral = umbrales.get(cal.materia_id)
        umbral_pct = umbral.umbral_pct if umbral else 60
        conjunto = umbral.conjunto_aprobado if umbral else None
        items.append(
            CalificacionItem(
                materia_id=cal.materia_id,
                materia_codigo=materia.codigo,
                materia_nombre=materia.nombre,
                nota=cal.nota,
                aprobado=_compute_aprobado(cal.nota, umbral_pct, conjunto),
                origen=cal.origen,
            )
        )

    return EstadoAcademicoResponse(usuario_id=user_id, calificaciones=items)
