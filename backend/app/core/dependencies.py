from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import create_engine, create_session_factory
from app.core.tenancy import (
    TenantContext,
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
    request: Request,
    db: AsyncSession = None,  # type: ignore[assignment]
) -> TenantContext:
    """C-03 JWT-driven tenant resolver.

    C-02's `X-Tenant-Id` header placeholder is gone. The resolver reads the
    bearer token, decodes the access JWT, and sets the `TenantContext`
    from the `tid` claim. The `X-Tenant-Id` header is ignored.
    """
    from app.auth.deps import _resolve_from_token

    auth = request.headers.get("Authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    current = await _resolve_from_token(db, token)  # type: ignore[arg-type]
    return TenantContext(tenant_id=current.tenant_id)


# RESERVADO para C-04: verificación de permisos
# def require_permission(permission: str):
#     ...
