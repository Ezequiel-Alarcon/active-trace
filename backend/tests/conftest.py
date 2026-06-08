import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import create_engine, create_session_factory, Base


os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("ENCRYPTION_KEY", "12345678901234567890123456789012")


_engine = None
_session_factory = None


def get_test_engine():
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_test_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_test_engine())
    return _session_factory


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_test_session_factory()
    async with factory() as session:
        yield session


@pytest.fixture(scope="function")
async def test_engine():
    engine = get_test_engine()
    yield engine
    await engine.dispose()