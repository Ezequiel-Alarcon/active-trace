"""Cross-tenant isolation contract (C-02 §6).

The repository of tenant A MUST NEVER read or write data that belongs to
tenant B. This is a defense-in-depth spec test that exercises every public
and unsafe method to make sure isolation holds end-to-end.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.repositories.base import (
    TenantMismatchError,
    TenantScopedRepository,
    get_tenant_repository,
)
from app.core.tenancy import TenantContext, tenant_scope
from tests._fakes.models import Smoke


@pytest_asyncio.fixture
async def two_tenants_with_rows(db_session: AsyncSession) -> tuple[Smoke, Smoke, Tenant, Tenant]:
    t_a = Tenant(id=uuid4(), codigo=f"TA-{uuid4().hex[:6]}", nombre="A", estado="Activo")
    t_b = Tenant(id=uuid4(), codigo=f"TB-{uuid4().hex[:6]}", nombre="B", estado="Activo")
    db_session.add_all([t_a, t_b])
    await db_session.flush()
    row_a = Smoke(id=uuid4(), tenant_id=t_a.id, label="A")
    row_b = Smoke(id=uuid4(), tenant_id=t_b.id, label="B")
    db_session.add_all([row_a, row_b])
    await db_session.flush()
    return row_a, row_b, t_a, t_b  # type: ignore[return-value]


# (a) get_by_id with B's id from A returns None
@pytest.mark.asyncio
async def test_get_by_id_cross_tenant_returns_none(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    row_a, row_b, t_a, _t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    assert await repo_a.get_by_id(row_b.id) is None
    assert await repo_a.get_by_id(row_a.id) is not None


# (b) list of A does not contain B
@pytest.mark.asyncio
async def test_list_does_not_contain_other_tenant(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    row_a, row_b, t_a, _t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    rows = await repo_a.list()
    assert {r.id for r in rows} == {row_a.id}


# (c) count of A does not count B
@pytest.mark.asyncio
async def test_count_does_not_count_other_tenant(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    _row_a, _row_b, t_a, _t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    assert await repo_a.count() == 1


# (d) create with tenant_id=B from A raises
@pytest.mark.asyncio
async def test_create_with_other_tenant_id_raises(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    _row_a, _row_b, t_a, t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    with pytest.raises(TenantMismatchError):
        await repo_a.create({"tenant_id": t_b.id, "label": "x"})


# (e) update/soft_delete on B's id from A does not affect the row
@pytest.mark.asyncio
async def test_update_cross_tenant_target_does_not_affect_row(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    row_a, row_b, t_a, _t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    # Try to update B's row through A's repo by using a wrong-tenant object.
    # The repository enforces tenant_id match on create, but update takes an
    # object — we verify the object is not silently mutated.
    with pytest.raises(TenantMismatchError):
        await repo_a.update(row_b, {"label": "hacked"})
    await db_session.refresh(row_b)
    assert row_b.label == "B"


@pytest.mark.asyncio
async def test_soft_delete_cross_tenant_target_raises(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    _row_a, row_b, t_a, _t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    with pytest.raises(TenantMismatchError):
        await repo_a.soft_delete(row_b)


# (f) factory wires the right tenant
@pytest.mark.asyncio
async def test_factory_wires_request_tenant(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    row_a, row_b, t_a, t_b = two_tenants_with_rows
    with tenant_scope(TenantContext(tenant_id=t_a.id)):
        repo = get_tenant_repository(Smoke, db_session)
        assert {r.id for r in await repo.list()} == {row_a.id}
    with tenant_scope(TenantContext(tenant_id=t_b.id)):
        repo = get_tenant_repository(Smoke, db_session)
        assert {r.id for r in await repo.list()} == {row_b.id}


# Cross-tenant list/count for unsafe paths STILL crosses, but they are
# explicit (`unsafe_*`) and audited. This test is the design intent.
@pytest.mark.asyncio
async def test_unsafe_paths_remain_the_only_way_to_cross_tenant(
    db_session: AsyncSession,
    two_tenants_with_rows,
) -> None:
    _row_a, _row_b, t_a, _t_b = two_tenants_with_rows
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    all_rows = await repo_a.unsafe_list_all()
    assert len(all_rows) == 2  # both A and B
