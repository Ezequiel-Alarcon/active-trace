"""RBAC repositories (C-04 §3).

- RolRepository: CRUD for roles, tenant-scoped.
- PermisoRepository: CRUD for permissions, tenant-scoped.
- RolPermisoRepository: attach/detach permission↔role, tenant-scoped.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select, func

from app.rbac.models import Permiso, Rol, RolPermiso
from app.repositories.base import TenantScopedRepository


class RolRepository(TenantScopedRepository[Rol]):
    async def get_by_nombre(self, nombre: str) -> Rol | None:
        stmt = (
            select(Rol)
            .where(Rol.tenant_id == self._tenant_id)
            .where(Rol.nombre == nombre)
            .where(Rol.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_ordered(self, limit: int = 50, offset: int = 0) -> list[Rol]:
        stmt = (
            select(Rol)
            .where(Rol.tenant_id == self._tenant_id)
            .where(Rol.deleted_at.is_(None))
            .order_by(Rol.nombre)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class PermisoRepository(TenantScopedRepository[Permiso]):
    async def get_by_modulo_accion(
        self, modulo: str, accion: str
    ) -> Permiso | None:
        stmt = (
            select(Permiso)
            .where(Permiso.tenant_id == self._tenant_id)
            .where(Permiso.modulo == modulo)
            .where(Permiso.accion == accion)
            .where(Permiso.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_ordered(
        self, limit: int = 100, offset: int = 0
    ) -> list[Permiso]:
        stmt = (
            select(Permiso)
            .where(Permiso.tenant_id == self._tenant_id)
            .where(Permiso.deleted_at.is_(None))
            .order_by(Permiso.modulo, Permiso.accion)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class RolPermisoRepository(TenantScopedRepository[RolPermiso]):
    async def attach(self, rol_id: UUID, permiso_id: UUID) -> RolPermiso:
        obj = RolPermiso(
            tenant_id=self._tenant_id,
            rol_id=rol_id,
            permiso_id=permiso_id,
        )
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def detach(self, rol_id: UUID, permiso_id: UUID) -> bool:
        stmt = (
            delete(RolPermiso)
            .where(RolPermiso.tenant_id == self._tenant_id)
            .where(RolPermiso.rol_id == rol_id)
            .where(RolPermiso.permiso_id == permiso_id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return int(result.rowcount or 0) > 0

    async def get_permisos_by_rol(self, rol_id: UUID) -> list[Permiso]:
        stmt = (
            select(Permiso)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .where(RolPermiso.tenant_id == self._tenant_id)
            .where(RolPermiso.rol_id == rol_id)
            .where(Permiso.tenant_id == self._tenant_id)
            .where(Permiso.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_roles_by_permiso(self, permiso_id: UUID) -> list[Rol]:
        stmt = (
            select(Rol)
            .join(RolPermiso, RolPermiso.rol_id == Rol.id)
            .where(RolPermiso.tenant_id == self._tenant_id)
            .where(RolPermiso.permiso_id == permiso_id)
            .where(Rol.tenant_id == self._tenant_id)
            .where(Rol.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def exists(self, rol_id: UUID, permiso_id: UUID) -> bool:
        stmt = select(
            func.count()
        ).select_from(RolPermiso).where(
            RolPermiso.tenant_id == self._tenant_id,
            RolPermiso.rol_id == rol_id,
            RolPermiso.permiso_id == permiso_id,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one()) > 0
