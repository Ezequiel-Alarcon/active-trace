import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base


os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("ENCRYPTION_KEY", "12345678901234567890123456789012")


_schema_applied = False


def _ensure_schema_sync() -> None:
    """Apply ORM-declared tables using a private engine + private loop.

    pytest-asyncio 1.4 + SQLAlchemy 2.0 async + asyncpg don't play well
    with session-scoped async fixtures: the session loop is torn down
    before function-scope teardown can complete. Running schema setup in
    a sync wrapper keeps the loop lifetime local to the call.
    """

    async def _go() -> None:
        import app.models.tenant  # noqa: F401  (register on Base.metadata)
        from app.models.mixins import TenantScopedMixin  # noqa: F401  (register on Base.metadata)
        from tests._fakes import models as _smoke  # noqa: F401  (register _smoke_tests)

        engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    asyncio.run(_go())


@pytest.fixture(scope="session", autouse=True)
def _apply_schema_once() -> None:
    """Create all ORM-declared tables once per test session.

    C-02 brings the first models; we don't have a full Alembic pipeline yet,
    so tests share `Base.metadata.create_all` to set up the schema. Migration
    tests (`test_alembic_migration_001`) apply and revert Alembic explicitly
    on a different schema path.
    """
    global _schema_applied
    if not _schema_applied:
        _ensure_schema_sync()
        _schema_applied = True


def _make_session_factory_per_test() -> tuple[AsyncEngine, async_sessionmaker]:
    """Build a per-test session factory bound to a fresh engine + loop.

    Caching the engine across tests on pytest-asyncio 1.4 leaks the
    previous event loop into the next test ("Event loop is closed" from
    asyncpg). So we build a fresh engine per test and dispose it on
    teardown.
    """
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A session per test, with a per-test engine to avoid loop leakage."""
    engine, factory = _make_session_factory_per_test()
    try:
        async with factory() as session:
            yield session
            try:
                await session.rollback()
            except Exception:
                pass
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()
