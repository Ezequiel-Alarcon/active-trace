from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.avisos import AlcanceAviso, Aviso
from app.repositories.avisos import AvisoRepository
from app.schemas.avisos import (
    AcknowledgmentStatusResponse,
    AvisoCreate,
    AvisoResponse,
    AvisoUpdate,
)


class AvisoService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _repo(self) -> AvisoRepository:
        return AvisoRepository(self._session, self._tenant_id)

    async def _get_or_404(self, aviso_id: UUID) -> Aviso:
        repo = self._repo()
        aviso = await repo.get_by_id(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        return aviso

    # ── CRUD ──────────────────────────────────────────────────────────

    async def create(self, data: AvisoCreate) -> AvisoResponse:
        repo = self._repo()
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "titulo": data.titulo,
            "cuerpo": data.cuerpo,
            "alcance": AlcanceAviso(data.alcance),
            "severidad": data.severidad,
            "rol_destino": data.rol_destino,
            "materia_id": data.materia_id,
            "cohorte_id": data.cohorte_id,
            "inicio_en": data.inicio_en,
            "fin_en": data.fin_en,
            "orden": data.orden,
            "activo": data.activo,
            "requiere_ack": data.requiere_ack,
        })
        return self._to_response(obj)

    async def get(self, aviso_id: UUID) -> AvisoResponse:
        obj = await self._get_or_404(aviso_id)
        return self._to_response(obj)

    async def update(self, aviso_id: UUID, data: AvisoUpdate) -> AvisoResponse:
        repo = self._repo()
        obj = await self._get_or_404(aviso_id)
        update_data: dict = {}
        for field in ("titulo", "cuerpo", "rol_destino", "materia_id", "cohorte_id",
                       "inicio_en", "fin_en", "orden", "activo", "requiere_ack"):
            value = getattr(data, field, None)
            if value is not None:
                update_data[field] = value
        if data.alcance is not None:
            update_data["alcance"] = AlcanceAviso(data.alcance)
        if data.severidad is not None:
            update_data["severidad"] = data.severidad
        if update_data:
            obj = await repo.update(obj, update_data)
            await self._session.refresh(obj)
        return self._to_response(obj)

    async def delete(self, aviso_id: UUID) -> None:
        repo = self._repo()
        obj = await self._get_or_404(aviso_id)
        await repo.soft_delete(obj)

    async def list_all(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        alcance: str | None = None,
    ) -> tuple[list[AvisoResponse], int]:
        repo = self._repo()
        filters = []
        if alcance is not None:
            filters.append(Aviso.alcance == AlcanceAviso(alcance))
        total = await repo.count(filters=filters or None)
        offset = (page - 1) * per_page
        objs = await repo.list(
            limit=per_page,
            offset=offset,
            order_by=[Aviso.created_at.desc()],
            filters=filters or None,
        )
        return [self._to_response(o) for o in objs], total

    # ── Visibility ────────────────────────────────────────────────────

    async def list_visible(
        self,
        *,
        user_id: UUID,
        user_roles: list[str],
        materia_ids: list[UUID] | None = None,
        cohorte_ids: list[UUID] | None = None,
    ) -> list[AvisoResponse]:
        repo = self._repo()
        now = datetime.now(timezone.utc)

        from sqlalchemy import or_
        from app.models.avisos import AlcanceAviso

        # Base: visibility window
        audience = [
            Aviso.inicio_en <= now,
            Aviso.fin_en >= now,
        ]

        # Build audience filter: matches if alcance targets this user
        global_clause = Aviso.alcance == AlcanceAviso.GLOBAL

        rol_clause = Aviso.alcance == AlcanceAviso.POR_ROL
        if user_roles:
            rol_clause = rol_clause & (
                Aviso.rol_destino.is_(None) | Aviso.rol_destino.in_(user_roles)
            )

        materia_clause = Aviso.alcance == AlcanceAviso.POR_MATERIA
        if materia_ids:
            materia_clause = materia_clause & Aviso.materia_id.in_(materia_ids)

        cohorte_clause = Aviso.alcance == AlcanceAviso.POR_COHORTE
        if cohorte_ids:
            cohorte_clause = cohorte_clause & Aviso.cohorte_id.in_(cohorte_ids)

        audience.append(
            or_(global_clause, rol_clause, materia_clause, cohorte_clause)
        )

        objs = await repo.list_visible(
            audience_filters=audience,
            limit=100,
            offset=0,
        )
        return [self._to_response(o) for o in objs]

    # ── Acknowledgment ────────────────────────────────────────────────

    async def acknowledge(self, aviso_id: UUID, usuario_id: UUID) -> None:
        repo = self._repo()
        aviso = await self._get_or_404(aviso_id)
        if not aviso.requiere_ack:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este aviso no requiere confirmación",
            )
        already = await repo.user_has_acknowledged(aviso_id, usuario_id)
        if already:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya confirmó este aviso",
            )
        await repo.create_acknowledgment(aviso_id, usuario_id)

    async def get_acknowledgment_status(
        self, aviso_id: UUID, usuario_id: UUID
    ) -> AcknowledgmentStatusResponse:
        repo = self._repo()
        aviso = await self._get_or_404(aviso_id)
        total = await repo.count_acknowledgments(aviso_id)
        user_ack = await repo.user_has_acknowledged(aviso_id, usuario_id)
        return AcknowledgmentStatusResponse(
            total=total,
            user_acknowledged=user_ack,
            requiere_ack=aviso.requiere_ack,
        )

    # ── Helpers ───────────────────────────────────────────────────────

    def _to_response(self, obj: Aviso) -> AvisoResponse:
        return AvisoResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            titulo=obj.titulo,
            cuerpo=obj.cuerpo,
            alcance=obj.alcance.value if hasattr(obj.alcance, "value") else str(obj.alcance),
            severidad=obj.severidad.value if hasattr(obj.severidad, "value") else str(obj.severidad),
            rol_destino=obj.rol_destino,
            materia_id=obj.materia_id,
            cohorte_id=obj.cohorte_id,
            inicio_en=obj.inicio_en,
            fin_en=obj.fin_en,
            orden=obj.orden,
            activo=obj.activo,
            requiere_ack=obj.requiere_ack,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
