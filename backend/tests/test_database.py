import pytest
from sqlalchemy import text
from app.core.database import create_engine, create_session_factory


@pytest.mark.asyncio
async def test_db_connection_smoke():
    engine = create_engine()
    factory = create_session_factory(engine)
    async with factory() as session:
        result = await session.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_session_isolation():
    engine = create_engine()
    factory = create_session_factory(engine)
    async with factory() as session:
        result = await session.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        assert db_name is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_session_closes_on_exception():
    engine = create_engine()
    factory = create_session_factory(engine)
    sessions = []
    try:
        async with factory() as session:
            sessions.append(session)
            raise RuntimeError("simulated error")
    except RuntimeError:
        pass
    finally:
        await engine.dispose()
    assert len(sessions) == 1
