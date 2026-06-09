"""Request-scoped tenant resolution.

The C-02 placeholder reads the `X-Tenant-Id` header (used by tests and the
smoke endpoint). C-03 replaces this with a JWT-derived resolver that ignores
the header entirely. The shape of `TenantContext` and the `ContextVar` storage
are stable across C-02 and C-03.

Rules enforced here:
- The current `tenant_id` is read from a `ContextVar` (per asyncio task).
- Repositories call `get_current_tenant_id()` which raises if no context is
  set — the failure mode is loud, never silent.
- The placeholder dependency only sets the context if no session-derived
  context is already active.
"""

from __future__ import annotations

import contextlib
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    """Immutable token identifying the active tenant for the current task."""

    tenant_id: UUID
    is_impersonating: bool = False


# Per-task context. Using ContextVar so concurrent asyncio tasks don't
# share tenant scopes (covered by tests/unit/test_tenant_context.py).
_ctx_var: ContextVar[TenantContext | None] = ContextVar(
    "activia_trace_tenant_context",
    default=None,
)


class TenantContextMissingError(RuntimeError):
    """Raised when a code path needs a tenant but no TenantContext is set.

    This is a *fail-closed* behavior: a repository or service that runs
    outside a request (background job, CLI, test misconfiguration) must
    surface this as a loud error, not a default to the first tenant.
    """


def set_tenant_context(ctx: TenantContext) -> object:
    """Set the current tenant context. Returns a token for `reset_tenant_context`."""
    return _ctx_var.set(ctx)


def reset_tenant_context(token: object) -> None:
    """Restore the previous context using the token returned by `set_tenant_context`."""
    _ctx_var.reset(token)  # type: ignore[arg-type]


@contextlib.contextmanager
def tenant_scope(ctx: TenantContext) -> Any:
    """Context manager: set the tenant for the duration of the block."""
    token = set_tenant_context(ctx)
    try:
        yield
    finally:
        reset_tenant_context(token)


def get_current_tenant_context() -> TenantContext:
    """Return the current `TenantContext`. Raises if none is set."""
    ctx = _ctx_var.get()
    if ctx is None:
        raise TenantContextMissingError(
            "no TenantContext is set for the current task; "
            "call set_tenant_context(...) or use the FastAPI dependency"
        )
    return ctx


def get_current_tenant_id() -> UUID:
    """Convenience: just the `tenant_id`. Raises if no context is set."""
    return get_current_tenant_context().tenant_id
