"""Integration test for Alembic migration 007_programas_fechas (C-17 SS5.6).

Validates that: upgrade creates programa_materia and fecha_academica tables,
downgrade drops them.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test",
)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ALEMBIC_EXE = os.path.join(os.path.dirname(sys.executable), "Scripts", "alembic.exe")


async def _drop_and_recreate_test_schema() -> None:
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
    await _drop_and_recreate_test_schema()
    yield
    import app.models.tenant  # noqa: F401
    from app.models.mixins import TenantScopedMixin  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.models import (
        carrera, cohorte, materia,  # noqa: F401
        programa_materia, fecha_academica,  # noqa: F401
        usuario, asignacion,  # noqa: F401
        guardia, instancia_encuentro, slot_encuentro,  # noqa: F401
    )
    from app.rbac import models as _rbac_models  # noqa: F401
    from tests._fakes import models as _smoke_models  # noqa: F401
    from app.core.database import Base
    from sqlalchemy.ext.asyncio import create_async_engine as _ce

    async def _restore_schema() -> None:
        engine = _ce(TEST_DB_URL, pool_pre_ping=True)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    await _restore_schema()


@pytest.mark.asyncio
async def test_alembic_upgrade_creates_programas_fechas_tables() -> None:
    await _alembic("upgrade", "head")
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            for table_name in ("programa_materia", "fecha_academica"):
                r = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name=:t"
                    ),
                    {"t": table_name},
                )
                assert r.scalar_one_or_none() == table_name, f"Table {table_name} missing"

            r = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='programa_materia' "
                    "ORDER BY ordinal_position"
                )
            )
            cols = {row[0] for row in r.fetchall()}
            for required in (
                "id", "tenant_id", "materia_id", "carrera_id", "cohorte_id",
                "titulo", "referencia_archivo", "created_at", "updated_at", "deleted_at",
            ):
                assert required in cols, f"Missing column {required} in programa_materia"

            r = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='fecha_academica' "
                    "ORDER BY ordinal_position"
                )
            )
            cols = {row[0] for row in r.fetchall()}
            for required in (
                "id", "tenant_id", "materia_id", "cohorte_id",
                "tipo", "numero_instancia", "fecha", "titulo", "descripcion",
                "created_at", "updated_at", "deleted_at",
            ):
                assert required in cols, f"Missing column {required} in fecha_academica"

            for ix in ("ix_programa_materia_tenant_materia_carrera_cohorte", "ix_programa_materia_tenant_deleted"):
                r = await conn.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE schemaname='public' AND tablename='programa_materia' AND indexname=:ix"
                    ),
                    {"ix": ix},
                )
                assert r.scalar_one_or_none() == ix, f"Index {ix} missing"

            for ix in ("ix_fecha_academica_tenant_materia_cohorte_tipo_num", "ix_fecha_academica_tenant_deleted"):
                r = await conn.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE schemaname='public' AND tablename='fecha_academica' AND indexname=:ix"
                    ),
                    {"ix": ix},
                )
                assert r.scalar_one_or_none() == ix, f"Index {ix} missing"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_alembic_downgrade_drops_programas_fechas_tables() -> None:
    await _alembic("upgrade", "head")
    await _alembic("downgrade", "006_usuarios_asignaciones")
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            for table_name in ("programa_materia", "fecha_academica"):
                r = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name=:t"
                    ),
                    {"t": table_name},
                )
                assert r.scalar_one_or_none() is None, (
                    f"Table {table_name} still exists after downgrade"
                )
    finally:
        await engine.dispose()
