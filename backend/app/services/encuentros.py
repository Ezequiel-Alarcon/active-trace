"""Encuentros service (C-18 §5).

Implements business rules for ABM of SlotEncuentro and InstanciaEncuentro.
Slot creation auto-generates cant_semanas instances via date arithmetic.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import EstadoEncuentro, InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import get_tenant_repository
from app.schemas.encuentros import (
    InstanciaEncuentroBrief,
    InstanciaEncuentroCreate,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroUpdate,
)


class EncuentrosService:
    """ABM service for encuentros (slots + instancias), scoped to a single tenant."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── SlotEncuentro ─────────────────────────────────────────────────

    async def create_slot(self, data: SlotEncuentroCreate) -> SlotEncuentro:
        repo = get_tenant_repository(SlotEncuentro, self._session)
        slot = await repo.create({
            "tenant_id": self._tenant_id,
            "materia_id": data.materia_id,
            "cohorte_id": data.cohorte_id,
            "titulo": data.titulo,
            "dia_semana": data.dia_semana,
            "hora_inicio": data.hora_inicio,
            "hora_fin": data.hora_fin,
            "fecha_inicio": data.fecha_inicio,
            "cant_semanas": data.cant_semanas,
            "meet_url": data.meet_url,
            "video_url": data.video_url,
        })

        instancia_repo = get_tenant_repository(InstanciaEncuentro, self._session)
        for i in range(data.cant_semanas):
            fecha = data.fecha_inicio + timedelta(weeks=i)
            await instancia_repo.create({
                "tenant_id": self._tenant_id,
                "slot_id": slot.id,
                "materia_id": data.materia_id,
                "cohorte_id": data.cohorte_id,
                "fecha": fecha,
                "hora_inicio": data.hora_inicio,
                "hora_fin": data.hora_fin,
                "titulo": data.titulo,
                "estado": EstadoEncuentro.PROGRAMADO,
                "meet_url": data.meet_url,
                "video_url": data.video_url,
            })

        return slot

    async def get_slot(self, slot_id: UUID) -> SlotEncuentro:
        repo = get_tenant_repository(SlotEncuentro, self._session)
        obj = await repo.get_by_id(slot_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot de encuentro no encontrado",
            )
        return obj

    async def list_slots(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[SlotEncuentro]:
        repo = get_tenant_repository(SlotEncuentro, self._session)
        filters = []
        if materia_id is not None:
            filters.append(SlotEncuentro.materia_id == materia_id)
        if cohorte_id is not None:
            filters.append(SlotEncuentro.cohorte_id == cohorte_id)
        result = await repo.list(filters=filters if filters else None)
        return list(result)

    async def update_slot(self, slot_id: UUID, data: SlotEncuentroUpdate) -> SlotEncuentro:
        repo = get_tenant_repository(SlotEncuentro, self._session)
        obj = await repo.get_by_id(slot_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot de encuentro no encontrado",
            )

        update_data: dict = {}
        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.dia_semana is not None:
            update_data["dia_semana"] = data.dia_semana
        if data.hora_inicio is not None:
            update_data["hora_inicio"] = data.hora_inicio
        if data.hora_fin is not None:
            update_data["hora_fin"] = data.hora_fin
        if data.meet_url is not None:
            update_data["meet_url"] = data.meet_url
        if data.video_url is not None:
            update_data["video_url"] = data.video_url

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def delete_slot(self, slot_id: UUID) -> None:
        repo = get_tenant_repository(SlotEncuentro, self._session)
        obj = await repo.get_by_id(slot_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot de encuentro no encontrado",
            )
        await repo.soft_delete(obj)

    # ── InstanciaEncuentro ────────────────────────────────────────────

    async def _get_instancias_for_slot(self, slot_id: UUID) -> list[InstanciaEncuentro]:
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        result = await repo.list(
            filters=[InstanciaEncuentro.slot_id == slot_id],
            limit=100,
        )
        return list(result)

    async def create_instancia_unica(self, data: InstanciaEncuentroCreate) -> InstanciaEncuentro:
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "slot_id": None,
            "materia_id": data.materia_id,
            "cohorte_id": data.cohorte_id,
            "fecha": data.fecha,
            "hora_inicio": data.hora_inicio,
            "hora_fin": data.hora_fin,
            "titulo": data.titulo,
            "estado": EstadoEncuentro.PROGRAMADO,
            "meet_url": data.meet_url,
            "video_url": data.video_url,
            "comentario": data.comentario,
        })
        return obj

    async def get_instancia(self, instancia_id: UUID) -> InstanciaEncuentro:
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        obj = await repo.get_by_id(instancia_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia de encuentro no encontrada",
            )
        return obj

    async def list_instancias(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[InstanciaEncuentro]:
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        filters = []
        if materia_id is not None:
            filters.append(InstanciaEncuentro.materia_id == materia_id)
        if cohorte_id is not None:
            filters.append(InstanciaEncuentro.cohorte_id == cohorte_id)
        if estado is not None:
            filters.append(InstanciaEncuentro.estado == estado)
        if fecha_desde is not None:
            filters.append(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta is not None:
            filters.append(InstanciaEncuentro.fecha <= fecha_hasta)
        result = await repo.list(
            filters=filters if filters else None,
            order_by=[InstanciaEncuentro.fecha.asc()],
        )
        return list(result)

    async def update_instancia(self, instancia_id: UUID, data: InstanciaEncuentroUpdate) -> InstanciaEncuentro:
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        obj = await repo.get_by_id(instancia_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia de encuentro no encontrada",
            )

        if data.fecha is not None and obj.fecha < date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede modificar la fecha de un encuentro pasado",
            )

        update_data: dict = {}
        if data.estado is not None:
            update_data["estado"] = EstadoEncuentro(data.estado)
        if data.fecha is not None:
            update_data["fecha"] = data.fecha
        if data.hora_inicio is not None:
            update_data["hora_inicio"] = data.hora_inicio
        if data.hora_fin is not None:
            update_data["hora_fin"] = data.hora_fin
        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.meet_url is not None:
            update_data["meet_url"] = data.meet_url
        if data.video_url is not None:
            update_data["video_url"] = data.video_url
        if data.comentario is not None:
            update_data["comentario"] = data.comentario

        if update_data:
            obj = await repo.update(obj, update_data)
        return obj

    async def delete_instancia(self, instancia_id: UUID) -> None:
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        obj = await repo.get_by_id(instancia_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia de encuentro no encontrada",
            )
        await repo.soft_delete(obj)

    # ── Fragmento LMS ─────────────────────────────────────────────────

    async def generar_fragmento_lms(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> str:
        """Generate an HTML fragment with instancias for the given materia and
        cohorte, ordered by date. If meet_url exists, it is rendered as a link.
        Canceled instances are marked visually."""
        repo = get_tenant_repository(InstanciaEncuentro, self._session)
        instancias = await repo.list(
            filters=[
                InstanciaEncuentro.materia_id == materia_id,
                InstanciaEncuentro.cohorte_id == cohorte_id,
            ],
            order_by=[InstanciaEncuentro.fecha.asc()],
        )

        if not instancias:
            return "<p>Sin encuentros programados</p>"

        lines: list[str] = []
        lines.append('<div class="encuentros-sincronicos">')
        lines.append('<h2>Encuentros Sincronicos</h2>')
        lines.append('<table class="encuentros-tabla">')
        lines.append("<thead><tr>")
        lines.append("<th>Fecha</th><th>Horario</th><th>Titulo</th><th>Enlace</th><th>Estado</th>")
        lines.append("</tr></thead>")
        lines.append("<tbody>")

        for inst in instancias:
            row_class = "encuentro-cancelado" if inst.estado == EstadoEncuentro.CANCELADO else ""
            lines.append(f'<tr class="{row_class}">')

            lines.append(f"<td>{inst.fecha.isoformat()}</td>")
            lines.append(f"<td>{inst.hora_inicio.strftime('%H:%M')} - {inst.hora_fin.strftime('%H:%M')}</td>")
            lines.append(f"<td>{inst.titulo}</td>")

            if inst.meet_url:
                lines.append(f'<td><a href="{inst.meet_url}" target="_blank" rel="noopener">Unirse</a></td>')
            else:
                lines.append("<td>—</td>")

            estado_label = inst.estado.value if isinstance(inst.estado, EstadoEncuentro) else inst.estado
            lines.append(f"<td>{estado_label}</td>")

            lines.append("</tr>")

        lines.append("</tbody>")
        lines.append("</table>")
        lines.append("</div>")

        return "\n".join(lines)
