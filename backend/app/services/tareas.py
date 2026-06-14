from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import EstadoTarea, Tarea
from app.repositories.tareas import ComentarioTareaRepository, TareaRepository
from app.schemas.tareas import (
    ComentarioCreate,
    ComentarioResponse,
    TareaCreate,
    TareaResponse,
    TareaUpdate,
)

ROLES_CON_TODO = {"COORDINADOR", "ADMIN"}

TRANSICIONES_VALIDAS = {
    EstadoTarea.PENDIENTE: {EstadoTarea.EN_PROGRESO, EstadoTarea.CANCELADA},
    EstadoTarea.EN_PROGRESO: {EstadoTarea.RESUELTA, EstadoTarea.CANCELADA},
    EstadoTarea.RESUELTA: set(),
    EstadoTarea.CANCELADA: set(),
}


class TareaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _repo(self) -> TareaRepository:
        return TareaRepository(self._session, self._tenant_id)

    def _comentario_repo(self) -> ComentarioTareaRepository:
        return ComentarioTareaRepository(self._session, self._tenant_id)

    def _es_admin(self, roles: list[str]) -> bool:
        return bool(set(roles) & ROLES_CON_TODO)

    def _verificar_acceso(self, tarea: Tarea, user_id: UUID, roles: list[str]) -> None:
        if not self._es_admin(roles) and tarea.asignado_a != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )

    async def _get_or_404(self, tarea_id: UUID) -> Tarea:
        repo = self._repo()
        tarea = await repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        return tarea

    async def create(self, data: TareaCreate, *, user_id: UUID | None = None, roles: list[str] | None = None) -> TareaResponse:
        if roles is not None and not self._es_admin(roles):
            if data.asignado_a != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permiso para crear tareas para otros docentes",
                )
        repo = self._repo()
        create_data = {
            "tenant_id": self._tenant_id,
            "asignado_a": data.asignado_a,
            "asignado_por": user_id or data.asignado_a,
            "descripcion": data.descripcion,
            "estado": EstadoTarea.PENDIENTE,
        }
        if data.materia_id:
            create_data["materia_id"] = data.materia_id
        if data.contexto_id:
            create_data["contexto_id"] = data.contexto_id
        obj = await repo.create(create_data)
        return self._to_response(obj)

    async def get(self, tarea_id: UUID, *, user_id: UUID, roles: list[str]) -> TareaResponse:
        obj = await self._get_or_404(tarea_id)
        self._verificar_acceso(obj, user_id, roles)
        return self._to_response(obj)

    async def update(self, tarea_id: UUID, data: TareaUpdate, *, user_id: UUID, roles: list[str]) -> TareaResponse:
        repo = self._repo()
        obj = await self._get_or_404(tarea_id)
        self._verificar_acceso(obj, user_id, roles)

        update_data: dict = {}
        if data.descripcion is not None:
            update_data["descripcion"] = data.descripcion
        if data.estado is not None:
            nuevo = EstadoTarea(data.estado)
            actual = obj.estado
            if nuevo not in TRANSICIONES_VALIDAS.get(actual, set()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transicion de estado invalida: {actual.value} -> {nuevo.value}",
                )
            update_data["estado"] = nuevo

        if update_data:
            obj = await repo.update(obj, update_data)
            await self._session.refresh(obj)
        return self._to_response(obj)

    async def delete(self, tarea_id: UUID, *, user_id: UUID, roles: list[str]) -> None:
        if not self._es_admin(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo coordinadores y admins pueden eliminar tareas",
            )
        repo = self._repo()
        obj = await self._get_or_404(tarea_id)
        await repo.soft_delete(obj)

    async def list_mis_tareas(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        estado: str | None = None,
        materia_id: UUID | None = None,
    ) -> tuple[list[TareaResponse], int]:
        repo = self._repo()
        offset = (page - 1) * per_page
        filters = {"user_id": user_id}
        if estado:
            filters["estado"] = estado
        if materia_id:
            filters["materia_id"] = materia_id
        total = await repo.count_filtered(**filters)
        objs = await repo.list_filtered(**filters, limit=per_page, offset=offset)
        return [self._to_response(o) for o in objs], total

    async def list_all(
        self,
        *,
        user_id: UUID,
        roles: list[str],
        page: int = 1,
        per_page: int = 20,
        estado: str | None = None,
        materia_id: UUID | None = None,
        asignado_a: UUID | None = None,
        q: str | None = None,
    ) -> tuple[list[TareaResponse], int]:
        if not self._es_admin(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para listar todas las tareas",
            )
        repo = self._repo()
        offset = (page - 1) * per_page
        filters = {}
        if estado:
            filters["estado"] = estado
        if materia_id:
            filters["materia_id"] = materia_id
        if asignado_a:
            filters["asignado_a"] = asignado_a
        if q:
            filters["q"] = q
        total = await repo.count_filtered(**filters)
        objs = await repo.list_filtered(**filters, limit=per_page, offset=offset)
        return [self._to_response(o) for o in objs], total

    async def agregar_comentario(
        self,
        tarea_id: UUID,
        data: ComentarioCreate,
        *,
        user_id: UUID,
        roles: list[str],
    ) -> ComentarioResponse:
        tarea = await self._get_or_404(tarea_id)
        self._verificar_acceso(tarea, user_id, roles)
        repo = self._comentario_repo()
        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "tarea_id": tarea_id,
            "autor_id": user_id,
            "texto": data.texto,
        })
        return ComentarioResponse(
            id=obj.id,
            tarea_id=obj.tarea_id,
            autor_id=obj.autor_id,
            texto=obj.texto,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    async def listar_comentarios(
        self,
        tarea_id: UUID,
        *,
        user_id: UUID,
        roles: list[str],
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[ComentarioResponse], int]:
        tarea = await self._get_or_404(tarea_id)
        self._verificar_acceso(tarea, user_id, roles)
        repo = self._comentario_repo()
        offset = (page - 1) * per_page
        total = await repo.count_by_tarea(tarea_id)
        objs = await repo.list_by_tarea(tarea_id, limit=per_page, offset=offset)
        items = [
            ComentarioResponse(
                id=o.id,
                tarea_id=o.tarea_id,
                autor_id=o.autor_id,
                texto=o.texto,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            for o in objs
        ]
        return items, total

    def _to_response(self, obj: Tarea) -> TareaResponse:
        return TareaResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            materia_id=obj.materia_id,
            asignado_a=obj.asignado_a,
            asignado_por=obj.asignado_por,
            estado=obj.estado.value if hasattr(obj.estado, "value") else str(obj.estado),
            descripcion=obj.descripcion,
            contexto_id=obj.contexto_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
