"""Tenant-scoped repository base.

This is the ONLY path for domain queries. Services and routers must use
`get_tenant_repository(model, session)` to obtain a bound repository, then
call its methods. They MUST NOT touch the AsyncSession directly.

Contract enforced by construction:
- The constructor raises if `tenant_id is None`.
- Public methods (`get`, `list`, `create`, `update`, `soft_delete`,
  `restore`, `count`) ALWAYS apply `WHERE tenant_id = :t AND deleted_at IS NULL`.
- Cross-tenant or include-deleted operations go through `unsafe_*` methods,
  which are visually distinct and emit an audit event via the seam.
- `unsafe_physical_delete` is the only path to hard-delete a row; it
  requires the same audit emission and is intended for admin scripts,
  not request handlers.

`unsafe_*` methods are NOT deleted in C-02; C-05 will plug the audit seam
into the real `AuditLog` table.
"""

from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone
from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import (
    ROW_HARD_DELETE,
    ROW_INCLUDE_DELETED,
    ROW_RESTORE,
    ROW_SOFT_DELETE,
    TENANT_CROSS_QUERY,
    audit_emit,
)
from app.core.tenancy import get_current_tenant_id
from app.models.base import Base

T = TypeVar("T", bound=Base)


class TenantIdRequiredError(ValueError):
    """Raised when a repository is constructed without a tenant_id."""


class TenantMismatchError(ValueError):
    """Raised when a `create()` tries to persist a row with a foreign tenant."""


class TenantScopedRepository(Generic[T], ABC):
    """Generic CRUD + soft-delete repository, scoped to a single tenant.

    Type parameter `T` is the ORM model. The model is expected to provide
    `id`, `tenant_id`, and `deleted_at` columns (i.e. to inherit
    `TenantScopedMixin`). The repository does not enforce that statically;
    if you pass a model without those columns, the queries will fail
    loudly at the SQL level.
    """

    def __init__(self, session: AsyncSession, model: type[T], tenant_id: UUID | None) -> None:
        if tenant_id is None:
            raise TenantIdRequiredError(
                "TenantScopedRepository requires a non-None tenant_id; "
                "use get_tenant_repository(model, session) to bind to the request tenant"
            )
        self._session = session
        self._model = model
        self._tenant_id = tenant_id

    @property
    def tenant_id(self) -> UUID:
        return self._tenant_id

    # ---------- scoped (tenant + not-deleted) ----------

    async def get_by_id(self, id: UUID) -> T | None:
        stmt = (
            select(self._model)
            .where(self._model.id == id)  # type: ignore[attr-defined]
            .where(self._model.tenant_id == self._tenant_id)  # type: ignore[attr-defined]
            .where(self._model.deleted_at.is_(None))  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(  # type: ignore[valid-type, misc]
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: list[Any] | None = None,
        filters: list[Any] | None = None,
    ) -> Sequence[T]:
        stmt = (
            select(self._model)
            .where(self._model.tenant_id == self._tenant_id)  # type: ignore[attr-defined]
            .where(self._model.deleted_at.is_(None))  # type: ignore[attr-defined]
        )
        if filters:
            stmt = stmt.where(*filters)
        if order_by:
            stmt = stmt.order_by(*order_by)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, filters: list[Any] | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(self._model)
            .where(self._model.tenant_id == self._tenant_id)  # type: ignore[attr-defined]
            .where(self._model.deleted_at.is_(None))  # type: ignore[attr-defined]
        )
        if filters:
            stmt = stmt.where(*filters)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, data: dict[str, Any] | T) -> T:
        if isinstance(data, self._model):
            obj = data
        else:
            # `data` is a dict[str, Any] here; the `| T` branch is handled above.
            obj = self._model(**data)  # type: ignore[arg-type]
        # Enforce tenant match — refuse to persist a row bound to a different tenant.
        obj_tenant = getattr(obj, "tenant_id", None)
        if obj_tenant is None:
            raise TenantMismatchError("create() requires tenant_id on the row")
        if obj_tenant != self._tenant_id:
            raise TenantMismatchError(
                f"create() tenant_id={obj_tenant} does not match "
                f"repository tenant_id={self._tenant_id}"
            )
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def update(self, obj: T, data: dict[str, Any]) -> T:
        # The row being updated must already belong to this tenant.
        obj_tenant = getattr(obj, "tenant_id", None)
        if obj_tenant != self._tenant_id:
            raise TenantMismatchError(
                "update() called on a row that does not belong to the repository's tenant"
            )
        # tenant_id is immutable from the repository's perspective.
        if "tenant_id" in data and data["tenant_id"] != self._tenant_id:
            raise TenantMismatchError("update() cannot change tenant_id")
        if "id" in data and data["id"] != getattr(obj, "id"):
            raise TenantMismatchError("update() cannot change id")
        for key, value in data.items():
            if key in ("tenant_id", "id"):
                continue
            setattr(obj, key, value)
        await self._session.flush()
        return obj

    async def soft_delete(self, obj: T) -> None:
        obj_id = getattr(obj, "id", None)
        obj_tenant = getattr(obj, "tenant_id", None)
        if obj_tenant != self._tenant_id:
            # The row does not belong to this tenant — refuse to act.
            raise TenantMismatchError(
                "soft_delete() called on a row that does not belong to the repository's tenant"
            )
        obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        await self._session.flush()
        audit_emit(
            ROW_SOFT_DELETE,
            entity=self._model.__tablename__,
            entity_id=obj_id,
            tenant_id=self._tenant_id,
        )

    async def restore(self, obj: T) -> None:
        obj_id = getattr(obj, "id", None)
        obj_tenant = getattr(obj, "tenant_id", None)
        if obj_tenant != self._tenant_id:
            raise TenantMismatchError(
                "restore() called on a row that does not belong to the repository's tenant"
            )
        obj.deleted_at = None  # type: ignore[attr-defined]
        await self._session.flush()
        audit_emit(
            ROW_RESTORE,
            entity=self._model.__tablename__,
            entity_id=obj_id,
            tenant_id=self._tenant_id,
        )

    # ---------- unsafe (cross-tenant / include-deleted / hard delete) ----------

    async def unsafe_get(self, id: UUID) -> T | None:
        """Get a row by id, ignoring both tenant and soft-delete filters."""
        audit_emit(
            TENANT_CROSS_QUERY,
            entity=self._model.__tablename__,
            entity_id=id,
            tenant_id=self._tenant_id,
            op="unsafe_get",
        )
        stmt = select(self._model).where(self._model.id == id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def unsafe_list_all(  # type: ignore[valid-type, misc]
        self,
        *,
        include_deleted: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[T]:
        """List rows across all tenants, optionally including soft-deleted."""
        audit_emit(
            TENANT_CROSS_QUERY,
            entity=self._model.__tablename__,
            tenant_id=self._tenant_id,
            op="unsafe_list_all",
            include_deleted=include_deleted,
        )
        stmt = select(self._model)
        if not include_deleted:
            stmt = stmt.where(self._model.deleted_at.is_(None))  # type: ignore[attr-defined]
        else:
            audit_emit(
                ROW_INCLUDE_DELETED,
                entity=self._model.__tablename__,
                tenant_id=self._tenant_id,
                op="unsafe_list_all",
            )
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def unsafe_count(self, *, include_deleted: bool = True) -> int:
        audit_emit(
            TENANT_CROSS_QUERY,
            entity=self._model.__tablename__,
            tenant_id=self._tenant_id,
            op="unsafe_count",
        )
        stmt = select(func.count()).select_from(self._model)
        if not include_deleted:
            stmt = stmt.where(self._model.deleted_at.is_(None))  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def unsafe_soft_delete(self, obj: T) -> None:
        """Soft-delete a row that may belong to any tenant. Audited."""
        obj_id = getattr(obj, "id", None)
        obj_tenant = getattr(obj, "tenant_id", None)
        obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        await self._session.flush()
        audit_emit(
            TENANT_CROSS_QUERY,
            entity=self._model.__tablename__,
            entity_id=obj_id,
            tenant_id=self._tenant_id,
            actual_tenant_id=str(obj_tenant) if obj_tenant else None,
            op="unsafe_soft_delete",
        )

    async def unsafe_restore(self, obj: T) -> None:
        obj_id = getattr(obj, "id", None)
        obj_tenant = getattr(obj, "tenant_id", None)
        obj.deleted_at = None  # type: ignore[attr-defined]
        await self._session.flush()
        audit_emit(
            TENANT_CROSS_QUERY,
            entity=self._model.__tablename__,
            entity_id=obj_id,
            tenant_id=self._tenant_id,
            actual_tenant_id=str(obj_tenant) if obj_tenant else None,
            op="unsafe_restore",
        )

    async def unsafe_physical_delete(self, obj: T) -> None:
        """Hard-delete a row. The ONLY place in the codebase that may
        call `session.delete(...)` on a domain row. Audited.
        """
        obj_id = getattr(obj, "id", None)
        obj_tenant = getattr(obj, "tenant_id", None)
        await self._session.delete(obj)
        await self._session.flush()
        audit_emit(
            ROW_HARD_DELETE,
            entity=self._model.__tablename__,
            entity_id=obj_id,
            tenant_id=self._tenant_id,
            actual_tenant_id=str(obj_tenant) if obj_tenant else None,
        )


def get_tenant_repository(model: type[T], session: AsyncSession) -> TenantScopedRepository[T]:
    """Factory: build a repository bound to the current task's tenant.

    Reads `get_current_tenant_id()` — raises if no `TenantContext` is set
    (fail-closed). Services and routers use this factory, never the
    constructor directly.
    """
    tenant_id = get_current_tenant_id()
    return TenantScopedRepository(session, model, tenant_id)
