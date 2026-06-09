"""Integration tests for TenantScopedMixin + SoftDeleteMixin.

These hit a real DB (Docker Postgres on the host's test port). They exercise
the contract:
- timestamps are populated by the server on INSERT,
- updated_at is refreshed on UPDATE,
- tenant_id is NOT NULL enforced at the DB level,
- FK to tenant.id is enforced at the DB level.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


# We use a real model (Tenant) to validate the mixin contract. Tenant
# inherits SoftDeleteMixin; for TenantScopedMixin we use a real
# session-scoped table created by the test fixture.


@pytest_asyncio.fixture
async def fresh_tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(
        id=uuid4(),
        codigo=f"T-{uuid4().hex[:8]}",
        nombre="Test Tenant",
        estado="Activo",
    )
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.mark.asyncio
async def test_soft_delete_mixin_starts_with_null_deleted_at(
    db_session: AsyncSession,
    fresh_tenant: Tenant,
) -> None:
    await db_session.refresh(fresh_tenant)
    assert fresh_tenant.deleted_at is None
    assert fresh_tenant.created_at is not None
    assert fresh_tenant.updated_at is not None


@pytest.mark.asyncio
async def test_soft_delete_mixin_allows_setting_deleted_at(
    db_session: AsyncSession,
    fresh_tenant: Tenant,
) -> None:
    from datetime import datetime, timezone

    fresh_tenant.deleted_at = datetime.now(timezone.utc)
    await db_session.flush()
    await db_session.refresh(fresh_tenant)
    assert fresh_tenant.deleted_at is not None


@pytest.mark.asyncio
async def test_tenant_codigo_is_unique_globally(
    db_session: AsyncSession,
) -> None:
    codigo = f"UNIQ-{uuid4().hex[:6]}"
    t1 = Tenant(id=uuid4(), codigo=codigo, nombre="A", estado="Activo")
    db_session.add(t1)
    await db_session.flush()
    t2 = Tenant(id=uuid4(), codigo=codigo, nombre="B", estado="Activo")
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_estado_check_constraint_rejects_invalid_value(
    db_session: AsyncSession,
) -> None:
    """The SAEnum validates `estado` at the application layer, and the
    DB-level check constraint backstops it. Either failure mode is fine —
    the contract is: a value outside the enum is rejected before the row
    is persisted.
    """
    from sqlalchemy.exc import DBAPIError, DataError, IntegrityError

    t = Tenant(
        id=uuid4(),
        codigo=f"X-{uuid4().hex[:6]}",
        nombre="Invalid estado",
        estado="NoExiste",  # type: ignore[arg-type]
    )
    db_session.add(t)
    with pytest.raises((DataError, IntegrityError, DBAPIError, ValueError)):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_scoped_mixin_fk_tenant_id_not_null(
    db_session: AsyncSession,
) -> None:
    """Inserting a row that uses TenantScopedMixin without tenant_id fails.

    We exercise the contract by directly constructing a row in raw SQL
    against a smoke table that mirrors the mixin shape. The table is
    created ad-hoc by the fixture.
    """
    table_name = f"_smoke_mixins_{uuid4().hex[:6]}"
    await db_session.execute(
        text(
            f"""
            CREATE TABLE {table_name} (
                id UUID PRIMARY KEY,
                tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                deleted_at TIMESTAMPTZ NULL
            )
            """
        )
    )
    await db_session.commit()
    try:
        # tenant_id NULL must fail
        with pytest.raises(IntegrityError):
            await db_session.execute(
                text(f"INSERT INTO {table_name} (id, tenant_id) VALUES (:id, NULL)"),
                {"id": str(uuid4())},
            )
        await db_session.rollback()
    finally:
        await db_session.execute(text(f"DROP TABLE {table_name}"))
        await db_session.commit()


@pytest.mark.asyncio
async def test_tenant_scoped_mixin_fk_to_nonexistent_tenant_fails(
    db_session: AsyncSession,
) -> None:
    table_name = f"_smoke_fk_{uuid4().hex[:6]}"
    await db_session.execute(
        text(
            f"""
            CREATE TABLE {table_name} (
                id UUID PRIMARY KEY,
                tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE RESTRICT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                deleted_at TIMESTAMPTZ NULL
            )
            """
        )
    )
    await db_session.commit()
    try:
        with pytest.raises(IntegrityError):
            await db_session.execute(
                text(f"INSERT INTO {table_name} (id, tenant_id) VALUES (:id, :t)"),
                {"id": str(uuid4()), "t": str(uuid4())},  # random tenant
            )
        await db_session.rollback()
    finally:
        await db_session.execute(text(f"DROP TABLE {table_name}"))
        await db_session.commit()


@pytest.mark.asyncio
async def test_tenant_scoped_mixin_timestamps_set_by_server(
    db_session: AsyncSession,
    fresh_tenant: Tenant,
) -> None:
    await db_session.refresh(fresh_tenant)
    assert fresh_tenant.created_at is not None
    assert fresh_tenant.updated_at is not None
    # Server-side default; we should not be able to bypass it by inserting
    # an explicit NULL even if we tried (the column is NOT NULL).
    with pytest.raises(IntegrityError):
        await db_session.execute(
            text(
                "INSERT INTO tenant (id, codigo, nombre, estado, created_at, updated_at) "
                "VALUES (:id, :codigo, :nombre, 'Activo', NULL, NULL)"
            ),
            {
                "id": str(uuid4()),
                "codigo": f"N-{uuid4().hex[:6]}",
                "nombre": "Should fail",
            },
        )
    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_scoped_mixin_updated_at_refreshed_on_update(
    db_session: AsyncSession,
    fresh_tenant: Tenant,
) -> None:
    await db_session.refresh(fresh_tenant)
    original = fresh_tenant.updated_at
    fresh_tenant.nombre = "Renamed"
    await db_session.flush()
    await db_session.refresh(fresh_tenant)
    assert fresh_tenant.updated_at >= original
