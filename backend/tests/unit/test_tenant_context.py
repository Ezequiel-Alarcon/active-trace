"""Unit tests for app.core.tenancy (C-02 §3).

The ContextVar-based contract: concurrent asyncio tasks must not share
tenant scopes, and reading outside a context fails loudly.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.core.tenancy import (
    TenantContext,
    TenantContextMissingError,
    get_current_tenant_context,
    get_current_tenant_id,
    reset_tenant_context,
    set_tenant_context,
    tenant_scope,
)


def test_get_current_tenant_id_raises_when_no_context() -> None:
    with pytest.raises(TenantContextMissingError):
        get_current_tenant_id()


def test_get_current_tenant_context_raises_when_no_context() -> None:
    with pytest.raises(TenantContextMissingError):
        get_current_tenant_context()


def test_set_and_read_round_trip() -> None:
    tid = uuid4()
    ctx = TenantContext(tenant_id=tid)
    token = set_tenant_context(ctx)
    try:
        assert get_current_tenant_id() == tid
        assert get_current_tenant_context() == ctx
    finally:
        reset_tenant_context(token)


def test_reset_restores_default() -> None:
    tid = uuid4()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    assert get_current_tenant_id() == tid
    reset_tenant_context(token)
    with pytest.raises(TenantContextMissingError):
        get_current_tenant_id()


def test_tenant_scope_context_manager() -> None:
    tid = uuid4()
    with tenant_scope(TenantContext(tenant_id=tid)):
        assert get_current_tenant_id() == tid
    with pytest.raises(TenantContextMissingError):
        get_current_tenant_id()


@pytest.mark.asyncio
async def test_concurrent_tasks_keep_independent_contexts() -> None:
    tid_a = uuid4()
    tid_b = uuid4()
    seen: dict[str, str] = {}

    async def worker(name: str, tid) -> None:
        with tenant_scope(TenantContext(tenant_id=tid)):
            # Yield to the loop so the other task gets a chance to set its
            # own context. If we were sharing a single var, B would
            # observe A's tenant — which is the bug we are guarding against.
            await asyncio.sleep(0.01)
            seen[name] = str(get_current_tenant_id())

    await asyncio.gather(worker("a", tid_a), worker("b", tid_b))
    assert seen == {"a": str(tid_a), "b": str(tid_b)}


def test_tenant_context_is_immutable() -> None:
    """TenantContext is a frozen dataclass — services can't tamper with the active scope."""
    from dataclasses import FrozenInstanceError

    ctx = TenantContext(tenant_id=uuid4())
    with pytest.raises(FrozenInstanceError):
        ctx.tenant_id = uuid4()  # type: ignore[misc]


def test_is_impersonating_default_false() -> None:
    ctx = TenantContext(tenant_id=uuid4())
    assert ctx.is_impersonating is False
