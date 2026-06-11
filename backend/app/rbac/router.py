"""RBAC admin catalog router (C-04 §7).

All endpoints require admin:gestionar_roles permission.
Mounted at /api/admin in app/main.py.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.constants import (
    AUDIT_PERMISO_ASIGNAR,
    AUDIT_PERMISO_REVOCAR,
    AUDIT_ROL_CREAR,
    AUDIT_ROL_ACTUALIZAR,
    AUDIT_ROL_ELIMINAR,
)
from app.audit.decorator import audit
from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.rbac.models import Permiso, Rol, RolPermiso
from app.rbac.repositories import PermisoRepository, RolPermisoRepository, RolRepository
from app.rbac.schemas import (
    PermisoCreate,
    PermisoSummary,
    RolCreate,
    RolDetail,
    RolSummary,
    RolUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin", "rbac"])

ADMIN_PERM = "admin:gestionar_roles"


async def _get_rbac_repos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> tuple[RolRepository, PermisoRepository, RolPermisoRepository]:
    rol_repo = RolRepository(db, Rol, current_user.tenant_id)
    perm_repo = PermisoRepository(db, Permiso, current_user.tenant_id)
    rp_repo = RolPermisoRepository(db, RolPermiso, current_user.tenant_id)
    return rol_repo, perm_repo, rp_repo


@router.get(
    "/roles",
    response_model=list[RolSummary],
    summary="List roles",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
async def list_roles(
    request: Request,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> list[Rol]:
    rol_repo, _, _ = repos
    roles = await rol_repo.list_ordered()
    return roles


@router.post(
    "/roles",
    response_model=RolSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
@audit(AUDIT_ROL_CREAR)
async def create_role(
    request: Request,
    data: RolCreate,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> Rol:
    rol_repo, _, _ = repos
    existing = await rol_repo.get_by_nombre(data.nombre)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Ya existe un rol con ese nombre en este tenant"},
        )
    rol = await rol_repo.create({"nombre": data.nombre, "descripcion": data.descripcion})
    return rol


@router.get(
    "/roles/{role_id}",
    response_model=RolDetail,
    summary="Get role detail",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
async def get_role(
    request: Request,
    role_id: UUID,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> Rol:
    rol_repo, _, rp_repo = repos
    rol = await rol_repo.get_by_id(role_id)
    if rol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Rol no encontrado"})
    permisos = await rp_repo.get_permisos_by_rol(role_id)
    rol.permisos = permisos
    return rol


@router.patch(
    "/roles/{role_id}",
    response_model=RolSummary,
    summary="Update role",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
@audit(AUDIT_ROL_ACTUALIZAR)
async def update_role(
    request: Request,
    role_id: UUID,
    data: RolUpdate,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> Rol:
    rol_repo, _, _ = repos
    rol = await rol_repo.get_by_id(role_id)
    if rol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Rol no encontrado"})
    update_data = {}
    if data.nombre is not None:
        existing = await rol_repo.get_by_nombre(data.nombre)
        if existing is not None and existing.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"detail": "Ya existe un rol con ese nombre en este tenant"},
            )
        update_data["nombre"] = data.nombre
    if data.descripcion is not None:
        update_data["descripcion"] = data.descripcion
    if update_data:
        rol = await rol_repo.update(rol, update_data)
    return rol


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete role",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
@audit(AUDIT_ROL_ELIMINAR)
async def delete_role(
    request: Request,
    role_id: UUID,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> None:
    rol_repo, _, _ = repos
    rol = await rol_repo.get_by_id(role_id)
    if rol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Rol no encontrado"})
    await rol_repo.soft_delete(rol)


@router.get(
    "/permisos",
    response_model=list[PermisoSummary],
    summary="List permissions",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
async def list_permisos(
    request: Request,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> list[Permiso]:
    _, perm_repo, _ = repos
    permisos = await perm_repo.list_ordered()
    return permisos


@router.post(
    "/permisos",
    response_model=PermisoSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create permission",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
@audit(AUDIT_PERMISO_ASIGNAR)
async def create_permiso(
    request: Request,
    data: PermisoCreate,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> Permiso:
    _, perm_repo, _ = repos
    existing = await perm_repo.get_by_modulo_accion(data.modulo, data.accion)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Ya existe ese permiso en este tenant"},
        )
    permiso = await perm_repo.create({"modulo": data.modulo, "accion": data.accion})
    return permiso


@router.post(
    "/roles/{rol_id}/permisos/{permiso_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Attach permission to role",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
@audit(AUDIT_PERMISO_ASIGNAR)
async def attach_permiso(
    request: Request,
    rol_id: UUID,
    permiso_id: UUID,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> None:
    rol_repo, perm_repo, rp_repo = repos
    rol = await rol_repo.get_by_id(rol_id)
    if rol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Rol no encontrado"})
    permiso = await perm_repo.get_by_id(permiso_id)
    if permiso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Permiso no encontrado"})
    already_attached = await rp_repo.exists(rol_id, permiso_id)
    if already_attached:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "El permiso ya esta asociado a este rol"},
        )
    await rp_repo.attach(rol_id, permiso_id)


@router.delete(
    "/roles/{rol_id}/permisos/{permiso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Detach permission from role",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
@audit(AUDIT_PERMISO_REVOCAR)
async def detach_permiso(
    request: Request,
    rol_id: UUID,
    permiso_id: UUID,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> None:
    _, _, rp_repo = repos
    await rp_repo.detach(rol_id, permiso_id)


@router.get(
    "/roles/{rol_id}/permisos",
    response_model=list[PermisoSummary],
    summary="List permissions of a role",
    dependencies=[Depends(require_permission(ADMIN_PERM))],
)
async def list_role_permisos(
    request: Request,
    rol_id: UUID,
    repos: Annotated[tuple[RolRepository, PermisoRepository, RolPermisoRepository], Depends(_get_rbac_repos)],
) -> list[Permiso]:
    _, _, rp_repo = repos
    permisos = await rp_repo.get_permisos_by_rol(rol_id)
    return permisos
