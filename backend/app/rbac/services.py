"""RBAC services (C-04 §4).

PermissionResolver: server-side resolution of effective permissions per user
per request. Computes the union of all permissions from all roles assigned
to the user, scoped to tenant + global baseline.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.rbac.constants import GLOBAL_TENANT_ID
from app.rbac.models import Permiso, Rol, RolPermiso


class PermissionResolver:
    """Resolves effective permissions for a user in a tenant.

    Resolution is cached per-request (instance-level dict keyed by
    (user_id, tenant_id)). The cache lifetime is the request lifecycle.

    C-04 implements the resolver with global tenant baseline + per-tenant
    roles via the asignacion join. The asignacion table (C-07) adds temporal
    validity (desde/hasta). C-04 resolves all roles unconditionally.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._cache: dict[tuple[UUID, UUID], set[str]] = {}

    async def resolve(self, user_id: UUID, tenant_id: UUID) -> set[str]:
        """Resolve effective permissions for (user_id, tenant_id).

        Returns permissions from the user's roles in their tenant (via asignacion).
        Filters by user assignment, temporal validity (desde/hasta), and soft-delete.

        The global tenant baseline (GLOBAL_TENANT_ID) is included so that all
        tenants get the universal permission matrix without per-tenant seed
        duplication. This mirrors design decision D2: seed is universal but
        stored under the global tenant; the resolver adds it to every tenant.
        """
        cache_key = (user_id, tenant_id)
        if cache_key in self._cache:
            return self._cache[cache_key]

        permissions: set[str] = set()

        stmt = (
            select(Permiso.modulo, Permiso.accion)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(Rol, Rol.id == RolPermiso.rol_id)
            .join(Asignacion, Asignacion.rol_id == Rol.id)
            .where(
                (Rol.tenant_id == tenant_id) | (Rol.tenant_id == GLOBAL_TENANT_ID)
            )
            .where(Asignacion.usuario_id == user_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.desde <= func.current_date())
            .where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= func.current_date())
            )
            .where(Rol.deleted_at.is_(None))
            .where(Permiso.deleted_at.is_(None))
        )
        result = await self._db.execute(stmt)
        for modulo, accion in result.all():
            permissions.add(f"{modulo}:{accion}")

        self._cache[cache_key] = permissions
        return permissions
