"""Integration tests for TenantScopedRepository (C-02 §5, §6).

Covers the contract:
- Constructor refuses `tenant_id=None`.
- `get_by_id` of a row from another tenant returns None.
- `list`/`count` exclude soft-deleted rows.
- `create` with mismatched tenant_id raises.
- `update` preserves tenant_id; cannot change it.
- `restore` reverts `soft_delete`.
- `unsafe_list_all` returns rows from all tenants + audit.
- `unsafe_physical_delete` removes the row + audit.
- Isolation holds under concurrency (`asyncio.gather`).
- Two repos bound to different tenants, in the same request handler,
  see different data.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import (
    ROW_HARD_DELETE,
    ROW_RESTORE,
    ROW_SOFT_DELETE,
    TENANT_CROSS_QUERY,
)
from app.core.tenancy import (
    TenantContext,
    tenant_scope,
)
from app.repositories.base import (
    TenantIdRequiredError,
    TenantMismatchError,
    TenantScopedRepository,
    get_tenant_repository,
)
from tests._fakes.models import Smoke


# ---------- fixtures ----------


@pytest_asyncio.fixture
async def tenants(db_session: AsyncSession) -> tuple[Smoke, Smoke]:
    """Two real tenants persisted in the DB for cross-tenant tests."""
    from app.models.tenant import Tenant

    t_a = Tenant(id=uuid4(), codigo=f"TA-{uuid4().hex[:6]}", nombre="A", estado="Activo")
    t_b = Tenant(id=uuid4(), codigo=f"TB-{uuid4().hex[:6]}", nombre="B", estado="Activo")
    db_session.add_all([t_a, t_b])
    await db_session.flush()
    return t_a, t_b  # type: ignore[return-value]


@pytest_asyncio.fixture
async def smoke_a(db_session: AsyncSession, tenants: tuple[Smoke, Smoke]) -> Smoke:
    t_a, _ = tenants
    s = Smoke(id=uuid4(), tenant_id=t_a.id, label="alpha")
    db_session.add(s)
    await db_session.flush()
    return s


# ---------- constructor ----------


def test_constructor_requires_tenant_id() -> None:
    with pytest.raises(TenantIdRequiredError):
        TenantScopedRepository(session=None, model=Smoke, tenant_id=None)  # type: ignore[arg-type]


# ---------- get_by_id ----------


@pytest.mark.asyncio
async def test_get_by_id_returns_row_for_correct_tenant(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    got = await repo.get_by_id(smoke_a.id)
    assert got is not None
    assert got.id == smoke_a.id


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_other_tenant(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    _, t_b = tenants
    repo_b = TenantScopedRepository(db_session, Smoke, t_b.id)
    assert await repo_b.get_by_id(smoke_a.id) is None


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_soft_deleted(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.soft_delete(smoke_a)
    assert await repo.get_by_id(smoke_a.id) is None


# ---------- list / count ----------


@pytest.mark.asyncio
async def test_list_excludes_soft_deleted(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    assert len(await repo.list()) == 1
    await repo.soft_delete(smoke_a)
    assert await repo.list() == []


@pytest.mark.asyncio
async def test_count_excludes_soft_deleted(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    assert await repo.count() == 1
    await repo.soft_delete(smoke_a)
    assert await repo.count() == 0


# ---------- create ----------


@pytest.mark.asyncio
async def test_create_rejects_mismatched_tenant_id(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, t_b = tenants
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    with pytest.raises(TenantMismatchError):
        await repo_a.create({"tenant_id": t_b.id, "label": "cross"})


@pytest.mark.asyncio
async def test_create_persists_with_repo_tenant(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, _ = tenants
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    obj = await repo_a.create({"tenant_id": t_a.id, "label": "x"})
    assert obj.tenant_id == t_a.id
    assert obj.id is not None
    assert obj.deleted_at is None


# ---------- update ----------


@pytest.mark.asyncio
async def test_update_preserves_tenant_id(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo_a.update(smoke_a, {"label": "renamed"})
    assert smoke_a.label == "renamed"
    assert smoke_a.tenant_id == t_a.id


@pytest.mark.asyncio
async def test_update_rejects_tenant_change(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, t_b = tenants
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    with pytest.raises(TenantMismatchError):
        await repo_a.update(smoke_a, {"tenant_id": t_b.id})


# ---------- soft_delete + restore ----------


@pytest.mark.asyncio
async def test_soft_delete_emits_audit(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
    caplog,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    caplog.set_level(logging.WARNING, logger="activia_trace.audit")
    await repo.soft_delete(smoke_a)
    actions = [r.__dict__.get("action") for r in caplog.records if r.name == "activia_trace.audit"]
    assert ROW_SOFT_DELETE in actions


@pytest.mark.asyncio
async def test_restore_emits_audit(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
    caplog,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.soft_delete(smoke_a)
    caplog.clear()
    caplog.set_level(logging.WARNING, logger="activia_trace.audit")
    await repo.restore(smoke_a)
    actions = [r.__dict__.get("action") for r in caplog.records if r.name == "activia_trace.audit"]
    assert ROW_RESTORE in actions


@pytest.mark.asyncio
async def test_restore_reverts_soft_delete(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.soft_delete(smoke_a)
    assert await repo.get_by_id(smoke_a.id) is None
    await repo.restore(smoke_a)
    assert await repo.get_by_id(smoke_a.id) is not None


# ---------- unsafe methods ----------


@pytest.mark.asyncio
async def test_unsafe_list_all_includes_soft_deleted_and_cross_tenant(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
    caplog,
) -> None:
    t_a, t_b = tenants
    # Row in B
    row_b = Smoke(id=uuid4(), tenant_id=t_b.id, label="beta")
    db_session.add(row_b)
    await db_session.flush()
    # Soft-delete A
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo_a.soft_delete(smoke_a)
    # unsafe_list_all on A repo returns both A (deleted) and B (other tenant)
    caplog.clear()
    caplog.set_level(logging.WARNING, logger="activia_trace.audit")
    all_rows = await repo_a.unsafe_list_all()
    ids = {r.id for r in all_rows}
    assert smoke_a.id in ids
    assert row_b.id in ids
    actions = [r.__dict__.get("action") for r in caplog.records if r.name == "activia_trace.audit"]
    assert TENANT_CROSS_QUERY in actions


@pytest.mark.asyncio
async def test_unsafe_physical_delete_emits_audit_and_removes_row(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
    caplog,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    caplog.clear()
    caplog.set_level(logging.WARNING, logger="activia_trace.audit")
    await repo.unsafe_physical_delete(smoke_a)
    # Even unsafe_get should not see it
    assert await repo.unsafe_get(smoke_a.id) is None
    actions = [r.__dict__.get("action") for r in caplog.records if r.name == "activia_trace.audit"]
    assert ROW_HARD_DELETE in actions


# ---------- factory ----------


@pytest.mark.asyncio
async def test_get_tenant_repository_reads_current_tenant_context(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, _ = tenants
    with tenant_scope(TenantContext(tenant_id=t_a.id)):
        repo = get_tenant_repository(Smoke, db_session)
        assert repo.tenant_id == t_a.id


def test_get_tenant_repository_raises_outside_context() -> None:
    with pytest.raises(Exception):
        get_tenant_repository(Smoke, session=None)  # type: ignore[arg-type]


# ---------- concurrency: no leakage ----------


@pytest.mark.asyncio
async def test_concurrent_tasks_do_not_leak_tenant_context(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, t_b = tenants
    # Create one row in each tenant
    row_a = Smoke(id=uuid4(), tenant_id=t_a.id, label="A")
    row_b = Smoke(id=uuid4(), tenant_id=t_b.id, label="B")
    db_session.add_all([row_a, row_b])
    await db_session.flush()

    seen: dict[str, int] = {}

    async def worker(name: str, tid) -> None:
        with tenant_scope(TenantContext(tenant_id=tid)):
            await asyncio.sleep(0.01)
            repo = get_tenant_repository(Smoke, db_session)
            seen[name] = len(await repo.list())

    await asyncio.gather(
        worker("a", t_a.id),
        worker("b", t_b.id),
    )
    assert seen == {"a": 1, "b": 1}


# ---------- two repos in the same handler, different tenants ----------


@pytest.mark.asyncio
async def test_two_repos_same_session_different_tenants(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, t_b = tenants
    row_a = Smoke(id=uuid4(), tenant_id=t_a.id, label="A")
    row_b = Smoke(id=uuid4(), tenant_id=t_b.id, label="B")
    db_session.add_all([row_a, row_b])
    await db_session.flush()

    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    repo_b = TenantScopedRepository(db_session, Smoke, t_b.id)
    a_ids = {r.id for r in await repo_a.list()}
    b_ids = {r.id for r in await repo_b.list()}
    assert a_ids == {row_a.id}
    assert b_ids == {row_b.id}


# ---------- Coverage extras (target 90% on this module) ----------


@pytest.mark.asyncio
async def test_list_paginates_with_limit_and_offset(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    for i in range(7):
        await repo.create({"tenant_id": t_a.id, "label": f"row-{i}"})
    page1 = await repo.list(limit=3, offset=0)
    page2 = await repo.list(limit=3, offset=3)
    page3 = await repo.list(limit=3, offset=6)
    assert len(page1) == 3
    assert len(page2) == 3
    assert len(page3) == 1
    assert await repo.count() == 7


@pytest.mark.asyncio
async def test_count_with_filters(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.create({"tenant_id": t_a.id, "label": "alpha"})
    await repo.create({"tenant_id": t_a.id, "label": "beta"})
    n = await repo.count(filters=[Smoke.label.like("a%")])  # type: ignore[attr-defined]
    assert n == 1


@pytest.mark.asyncio
async def test_unsafe_get_returns_row_across_tenants(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    _, t_b = tenants
    repo_b = TenantScopedRepository(db_session, Smoke, t_b.id)
    got = await repo_b.unsafe_get(smoke_a.id)
    assert got is not None
    assert got.id == smoke_a.id


@pytest.mark.asyncio
async def test_unsafe_count_returns_total_across_tenants(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, t_b = tenants
    row_b = Smoke(id=uuid4(), tenant_id=t_b.id, label="B")
    db_session.add(row_b)
    await db_session.flush()
    repo_a = TenantScopedRepository(db_session, Smoke, t_a.id)
    assert await repo_a.unsafe_count() == 2


@pytest.mark.asyncio
async def test_unsafe_count_excludes_deleted_when_requested(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.soft_delete(smoke_a)
    assert await repo.unsafe_count(include_deleted=False) == 0
    assert await repo.unsafe_count(include_deleted=True) == 1


@pytest.mark.asyncio
async def test_unsafe_list_all_with_include_deleted_false(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.soft_delete(smoke_a)
    rows = await repo.unsafe_list_all(include_deleted=False)
    assert all(r.id != smoke_a.id for r in rows)


@pytest.mark.asyncio
async def test_unsafe_soft_delete_emits_audit(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
    caplog,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    caplog.set_level(logging.WARNING, logger="activia_trace.audit")
    # Re-fetch the row without soft-delete filter, then soft-delete via unsafe
    fresh = await repo.unsafe_get(smoke_a.id)
    assert fresh is not None
    await repo.unsafe_soft_delete(fresh)
    actions = [r.__dict__.get("action") for r in caplog.records if r.name == "activia_trace.audit"]
    assert "TENANT_CROSS_QUERY" in actions


@pytest.mark.asyncio
async def test_unsafe_restore_emits_audit(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
    smoke_a: Smoke,
    caplog,
) -> None:
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    await repo.soft_delete(smoke_a)
    caplog.clear()
    caplog.set_level(logging.WARNING, logger="activia_trace.audit")
    fresh = await repo.unsafe_get(smoke_a.id)
    assert fresh is not None
    await repo.unsafe_restore(fresh)
    actions = [r.__dict__.get("action") for r in caplog.records if r.name == "activia_trace.audit"]
    assert "TENANT_CROSS_QUERY" in actions


@pytest.mark.asyncio
async def test_create_accepts_model_instance(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    """`create` accepts either a dict or a model instance."""
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    obj = Smoke(id=uuid4(), tenant_id=t_a.id, label="z")
    out = await repo.create(obj)
    assert out.id == obj.id
    assert out.label == "z"


@pytest.mark.asyncio
async def test_create_rejects_when_row_has_no_tenant_id(
    db_session: AsyncSession,
    tenants: tuple[Smoke, Smoke],
) -> None:
    """If a row has no tenant_id, create() refuses — defense in depth."""
    t_a, _ = tenants
    repo = TenantScopedRepository(db_session, Smoke, t_a.id)
    with pytest.raises(TenantMismatchError):
        await repo.create({"label": "no-tenant"})  # type: ignore[arg-type]
