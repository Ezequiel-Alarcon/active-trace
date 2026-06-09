from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import create_engine, create_session_factory
from app.core.tenancy import (
    TenantContext,
    TenantContextMissingError,
    get_current_tenant_context,
    set_tenant_context,
)


_async_engine = None
_async_session_factory = None


def get_engine():
    global _async_engine
    if _async_engine is None:
        _async_engine = create_engine()
    return _async_engine


def get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = create_session_factory(get_engine())
    return _async_session_factory


async def dispose_engine() -> None:
    """Dispose the cached async engine at application shutdown.

    Public seam so the FastAPI lifespan in `app.main` doesn't have to
    reach into module-level globals. C-02 introduced module-level caching
    of the engine and session factory; this function centralizes cleanup.
    """
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
    _async_engine = None
    _async_session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()


# RESERVADO para C-03: implementación de auth JWT
# async def get_current_user(token: str, ...) -> User:
#     ...


async def tenant_context_dep(
    x_tenant_id: UUID | None = Header(default=None, alias="X-Tenant-Id"),
) -> TenantContext:
    """C-02 placeholder dependency: tenant_id from the `X-Tenant-Id` header.

    C-03 will replace this with a JWT-derived resolver. The contract of
    this dependency is stable: it returns a `TenantContext` and sets it
    on the per-task ContextVar. Services call `get_current_tenant_id()`
    to read it.

    If the request is unauthenticated AND no header is present, we raise
    `TenantContextMissingError` so the request fails fast at the boundary
    instead of leaking a default tenant into a repository.
    """
    if x_tenant_id is None:
        # Honor a context that may already be set by a parent dependency
        # (e.g. when a higher-level dependency or a test fixture set it).
        try:
            return get_current_tenant_context()
        except TenantContextMissingError:
            raise TenantContextMissingError(
                "X-Tenant-Id header is required in C-02; C-03 will resolve from JWT"
            ) from None
    ctx = TenantContext(tenant_id=x_tenant_id)
    set_tenant_context(ctx)
    return ctx


# RESERVADO para C-04: verificación de permisos
# def require_permission(permission: str):
#     ...
