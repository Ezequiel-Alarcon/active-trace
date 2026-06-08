from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import create_engine, create_session_factory


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


# RESERVADO para C-02/C-04: resolución de tenant desde request
# async def get_tenant(request: Request, ...) -> Tenant:
#     ...


# RESERVADO para C-04: verificación de permisos
# def require_permission(permission: str):
#     ...