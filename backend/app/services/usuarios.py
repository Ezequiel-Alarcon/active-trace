"""Usuario and Asignacion services (C-07).

Implements business rules for ABM of users and assignments.
Validations (email uniqueness, PII encryption, vigencia, contexto) live here.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthUser
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.rbac.models import Rol
from app.repositories.base import get_tenant_repository
from app.repositories.usuarios import (
    UsuarioRepository,
    decrypt_usuario_fields,
)
from app.schemas.usuarios import (
    AsignacionCreate,
    AsignacionResponse,
    AsignacionUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)


class UsuarioService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _repo(self) -> UsuarioRepository:
        return UsuarioRepository(self._session, self._tenant_id)

    async def create(self, data: UsuarioCreate) -> UsuarioResponse:
        repo = self._repo()
        email_lower = data.email.strip().lower()

        existing = await repo.find_by_email(self._tenant_id, email_lower)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese email en este tenant",
            )

        if data.id is not None:
            auth_repo = get_tenant_repository(AuthUser, self._session)
            auth_user = await auth_repo.get_by_id(data.id)
            if auth_user is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El AuthUser especificado no existe",
                )

        create_dict = data.model_dump(exclude_unset=True)
        obj = await repo.create(create_dict)
        fields = decrypt_usuario_fields(obj)
        return UsuarioResponse(**fields)

    async def get_by_id(self, usuario_id: UUID) -> UsuarioResponse:
        repo = self._repo()
        obj = await repo.get_by_id(usuario_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        fields = decrypt_usuario_fields(obj)
        return UsuarioResponse(**fields)

    async def list(
        self,
        *,
        busqueda: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UsuarioResponse]:
        repo = self._repo()
        filters = []
        if busqueda:
            pattern = f"%{busqueda}%"
            from sqlalchemy import or_
            filters.append(
                or_(
                    Usuario.nombre.ilike(pattern),
                    Usuario.apellidos.ilike(pattern),
                )
            )
        objs = await repo.list(limit=limit, offset=offset, filters=filters if filters else None)
        return [UsuarioResponse(**decrypt_usuario_fields(o)) for o in objs]

    async def update(self, usuario_id: UUID, data: UsuarioUpdate) -> UsuarioResponse:
        repo = self._repo()
        obj = await repo.get_by_id(usuario_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] is not None:
            email_lower = update_data["email"].strip().lower()
            existing = await repo.find_by_email(self._tenant_id, email_lower)
            if existing is not None and existing.id != obj.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un usuario con ese email en este tenant",
                )

        if update_data:
            obj = await repo.update(obj, update_data)
            await self._session.refresh(obj)
        fields = decrypt_usuario_fields(obj)
        return UsuarioResponse(**fields)

    async def delete(self, usuario_id: UUID) -> None:
        repo = self._repo()
        obj = await repo.get_by_id(usuario_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        await repo.soft_delete(obj)


class AsignacionService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _repo(self):
        return get_tenant_repository(Asignacion, self._session)

    async def _validate_contexto(
        self, contexto_tipo: ContextoTipo, contexto_id: UUID | None
    ) -> None:
        if contexto_tipo == ContextoTipo.GLOBAL:
            return
        if contexto_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"contexto_id es requerido para tipo {contexto_tipo.value}",
            )
        entity_map = {
            ContextoTipo.CARRERA: Carrera,
            ContextoTipo.COHORTE: Cohorte,
            ContextoTipo.MATERIA: Materia,
        }
        model = entity_map[contexto_tipo]
        repo = get_tenant_repository(model, self._session)
        obj = await repo.get_by_id(contexto_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El contexto {contexto_tipo.value} especificado no existe",
            )

    async def _validate_usuario(self, usuario_id: UUID) -> None:
        repo = get_tenant_repository(Usuario, self._session)
        obj = await repo.get_by_id(usuario_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El usuario especificado no existe",
            )

    async def _validate_rol(self, rol_id: UUID) -> None:
        repo = get_tenant_repository(Rol, self._session)
        obj = await repo.get_by_id(rol_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El rol especificado no existe",
            )

    async def _validate_responsable(self, responsable_id: UUID) -> None:
        repo = get_tenant_repository(Usuario, self._session)
        obj = await repo.get_by_id(responsable_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El responsable especificado no existe",
            )

    async def create(self, data: AsignacionCreate) -> AsignacionResponse:
        if data.hasta is not None and data.hasta < data.desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hasta debe ser posterior a desde",
            )

        contexto_tipo = ContextoTipo(data.contexto_tipo)
        await self._validate_usuario(data.usuario_id)
        await self._validate_rol(data.rol_id)
        await self._validate_contexto(contexto_tipo, data.contexto_id)
        if data.responsable_id is not None:
            await self._validate_responsable(data.responsable_id)

        repo = self._repo()
        create_dict = data.model_dump(exclude_unset=True)
        create_dict["contexto_tipo"] = contexto_tipo
        create_dict["tenant_id"] = self._tenant_id
        obj = await repo.create(create_dict)
        return AsignacionResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            usuario_id=obj.usuario_id,
            rol_id=obj.rol_id,
            contexto_tipo=obj.contexto_tipo.value,
            contexto_id=obj.contexto_id,
            responsable_id=obj.responsable_id,
            desde=obj.desde,
            hasta=obj.hasta,
            estado_vigencia=obj.estado_vigencia,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    async def get_by_id(self, asignacion_id: UUID) -> AsignacionResponse:
        repo = self._repo()
        obj = await repo.get_by_id(asignacion_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignacion no encontrada",
            )
        return AsignacionResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            usuario_id=obj.usuario_id,
            rol_id=obj.rol_id,
            contexto_tipo=obj.contexto_tipo.value,
            contexto_id=obj.contexto_id,
            responsable_id=obj.responsable_id,
            desde=obj.desde,
            hasta=obj.hasta,
            estado_vigencia=obj.estado_vigencia,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    async def list(
        self,
        *,
        usuario_id: UUID | None = None,
        rol_id: UUID | None = None,
        contexto_tipo: str | None = None,
        contexto_id: UUID | None = None,
        estado_vigencia: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AsignacionResponse]:
        repo = self._repo()
        filters = []
        if usuario_id is not None:
            filters.append(Asignacion.usuario_id == usuario_id)
        if rol_id is not None:
            filters.append(Asignacion.rol_id == rol_id)
        if contexto_tipo is not None:
            filters.append(Asignacion.contexto_tipo == ContextoTipo(contexto_tipo))
        if contexto_id is not None:
            filters.append(Asignacion.contexto_id == contexto_id)
        objs = await repo.list(limit=limit, offset=offset, filters=filters if filters else None)
        result = []
        for obj in objs:
            vigencia = obj.estado_vigencia
            if estado_vigencia is not None and vigencia != estado_vigencia:
                continue
            result.append(
                AsignacionResponse(
                    id=obj.id,
                    tenant_id=obj.tenant_id,
                    usuario_id=obj.usuario_id,
                    rol_id=obj.rol_id,
                    contexto_tipo=obj.contexto_tipo.value,
                    contexto_id=obj.contexto_id,
                    responsable_id=obj.responsable_id,
                    desde=obj.desde,
                    hasta=obj.hasta,
                    estado_vigencia=vigencia,
                    created_at=obj.created_at,
                    updated_at=obj.updated_at,
                )
            )
        return result

    async def update(self, asignacion_id: UUID, data: AsignacionUpdate) -> AsignacionResponse:
        repo = self._repo()
        obj = await repo.get_by_id(asignacion_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignacion no encontrada",
            )

        update_data: dict = {}

        if data.contexto_tipo is not None:
            new_tipo = ContextoTipo(data.contexto_tipo)
            ctx_id = data.contexto_id if data.contexto_id is not None else obj.contexto_id
            await self._validate_contexto(new_tipo, ctx_id)
            update_data["contexto_tipo"] = new_tipo

        if data.contexto_id is not None:
            tipo = (
                ContextoTipo(data.contexto_tipo) if data.contexto_tipo
                else obj.contexto_tipo
            )
            await self._validate_contexto(tipo, data.contexto_id)
            update_data["contexto_id"] = data.contexto_id

        if data.rol_id is not None:
            await self._validate_rol(data.rol_id)
            update_data["rol_id"] = data.rol_id

        if data.responsable_id is not None:
            await self._validate_responsable(data.responsable_id)
            update_data["responsable_id"] = data.responsable_id

        if data.desde is not None:
            update_data["desde"] = data.desde

        if data.hasta is not None:
            update_data["hasta"] = data.hasta

        nuevo_desde = update_data.get("desde", obj.desde)
        nuevo_hasta = update_data.get("hasta", obj.hasta)
        if nuevo_hasta is not None and nuevo_hasta < nuevo_desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hasta debe ser posterior a desde",
            )

        if update_data:
            obj = await repo.update(obj, update_data)
            await self._session.refresh(obj)

        return AsignacionResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            usuario_id=obj.usuario_id,
            rol_id=obj.rol_id,
            contexto_tipo=obj.contexto_tipo.value,
            contexto_id=obj.contexto_id,
            responsable_id=obj.responsable_id,
            desde=obj.desde,
            hasta=obj.hasta,
            estado_vigencia=obj.estado_vigencia,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    async def delete(self, asignacion_id: UUID) -> None:
        repo = self._repo()
        obj = await repo.get_by_id(asignacion_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignacion no encontrada",
            )
        await repo.soft_delete(obj)
