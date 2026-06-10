"""Integration test for Alembic migration 001_tenant (C-02 §7).

Drops the test schema, applies the migration, validates that the
`tenant` table exists with the expected columns and indexes, then
reverts and validates the table is gone.

This test does NOT use the standard `db_session` fixture (which is wired
to `Base.metadata.create_all` and would conflict with Alembic). It runs
in its own loop with its own engine.
"""

from __future__ import annotations

import asyncio
import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/activia_trace_test",
)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ALEMBIC_EXE = r"C:\Users\edgar\AppData\Roaming\Python\Python312\Scripts\alembic.exe"


async def _drop_and_recreate_test_schema() -> None:
    """Drop and recreate the public schema in the test database."""
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    finally:
        await engine.dispose()


async def _alembic(*args: str) -> None:
    """Run the alembic CLI in a subprocess.

    We do this (not the Python API) to avoid a name clash between the
    project directory `backend/alembic/` and the `alembic` Python package.
    The subprocess is isolated from the test's sys.path.
    """
    env = os.environ.copy()
    proc = await asyncio.create_subprocess_exec(
        ALEMBIC_EXE,
        *args,
        cwd=REPO_ROOT,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise AssertionError(
            f"alembic {' '.join(args)} failed (rc={proc.returncode})\n"
            f"stdout: {stdout.decode(errors='replace')}\n"
            f"stderr: {stderr.decode(errors='replace')}"
        )


@pytest_asyncio.fixture(scope="module", autouse=True, loop_scope="module")
async def _isolated_db() -> None:
    """Reset the test schema before the module runs, then restore ORM tables after."""
    await _drop_and_recreate_test_schema()
    yield
    # Restore ORM-created tables (e.g. _smoke_tests, tenant, auth_*) for subsequent
    # modules. Without this, _apply_schema_once ran once at session start but the DROP
    # SCHEMA CASCADE wiped everything — subsequent tests got UndefinedTableError.
    # Cannot use conftest's _ensure_schema_sync() (uses asyncio.run() which fails
    # inside an existing event loop). Inline the async logic here.
    import app.models.tenant  # noqa: F401
    from app.models.mixins import TenantScopedMixin  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from tests._fakes import models as _smoke_models  # noqa: F401
    from app.core.database import Base
    from sqlalchemy.ext.asyncio import create_async_engine

    async def _restore_schema() -> None:
        engine = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    await _restore_schema()


@pytest.mark.asyncio
async def test_alembic_upgrade_creates_tenant_table() -> None:
    await _alembic("upgrade", "head")
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            # Table exists
            r = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='tenant'"
                )
            )
            assert r.scalar_one_or_none() == "tenant"
            # Columns
            r = await conn.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='tenant' ORDER BY ordinal_position"
                )
            )
            cols = {row[0]: row[1] for row in r.fetchall()}
            for required in (
                "id",
                "codigo",
                "nombre",
                "estado",
                "created_at",
                "updated_at",
                "deleted_at",
            ):
                assert required in cols, f"missing column: {required}"
            # Unique index
            r = await conn.execute(
                text(
                    "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
                    "AND tablename='tenant' AND indexname='ux_tenant_codigo'"
                )
            )
            assert r.scalar_one_or_none() == "ux_tenant_codigo"
            # Time indexes
            for ix in ("ix_tenant_created_at", "ix_tenant_deleted_at"):
                r = await conn.execute(
                    text(
                        "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
                        "AND tablename='tenant' AND indexname=:ix"
                    ),
                    {"ix": ix},
                )
                assert r.scalar_one_or_none() == ix
            # Check constraint
            r = await conn.execute(
                text("SELECT conname FROM pg_constraint WHERE conname='ck_tenant_estado'")
            )
            assert r.scalar_one_or_none() == "ck_tenant_estado"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_alembic_upgrade_then_downgrade_drops_table() -> None:
    await _alembic("upgrade", "head")
    await _alembic("downgrade", "base")
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            r = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='tenant'"
                )
            )
            assert r.scalar_one_or_none() is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_alembic_migration_is_reversible() -> None:
    """Up, then down, then up again: schema ends in the same shape."""
    await _alembic("upgrade", "head")
    await _alembic("downgrade", "base")
    await _alembic("upgrade", "head")
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            r = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='tenant'"
                )
            )
            cols = {row[0] for row in r.fetchall()}
            assert {
                "id",
                "codigo",
                "nombre",
                "estado",
                "created_at",
                "updated_at",
                "deleted_at",
            } <= cols
    finally:
        await engine.dispose()
