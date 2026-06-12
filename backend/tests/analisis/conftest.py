"""Fixtures para tests de analisis (C-11)."""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test",
)

from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security.hashing import hash_email_for_search
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado


@pytest_asyncio.fixture
async def db_setup():
    """Isolated schema with all tables, session factory yielded."""
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia  # noqa: F401
    from app.models import usuario, asignacion  # noqa: F401
    from app.models import padron  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.domain.calificaciones.models.calificacion import Calificacion  # noqa: F401
    from app.domain.calificaciones.models.umbral_materia import UmbralMateria  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_global_tenant(session) -> None:
    """Seed global tenant with roles and permissions."""
    from app.rbac.constants import GLOBAL_TENANT_ID

    gid = GLOBAL_TENANT_ID
    existing = await session.get(Tenant, gid)
    if existing is None:
        t = Tenant(id=gid, codigo="GLOBAL", nombre="Global System Tenant", estado=TenantEstado.ACTIVO)
        session.add(t)
        await session.flush()


async def _create_tenant(session, codigo="TENANT-TEST") -> Tenant:
    t = Tenant(codigo=codigo, nombre="Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_usuario(session, tenant_id: UUID, email: str) -> UUID:
    """Create a Usuario record."""
    from app.models.usuario import Usuario
    from app.repositories.usuarios import encrypt_usuario_fields

    uid = uuid4()
    enc = encrypt_usuario_fields(
        {"email": email, "dni": "11111111", "cuil": "20-11111111-9", "cbu": "1111111111111111111111"},
        tenant_id=tenant_id,
    )
    u = Usuario(id=uid, tenant_id=tenant_id, nombre="Test", apellidos="User", **enc)
    session.add(u)
    await session.flush()
    return uid


@pytest_asyncio.fixture
async def tenant_a(db_setup):
    """Tenant A for testing."""
    async with db_setup() as session:
        await _seed_global_tenant(session)
        t = await _create_tenant(session, "TENANTA")
        await session.commit()
        await session.refresh(t)
    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


@pytest_asyncio.fixture
async def tenant_b(db_setup):
    """Tenant B for testing."""
    async with db_setup() as session:
        await _seed_global_tenant(session)
        t = await _create_tenant(session, "TENANTB")
        await session.commit()
        await session.refresh(t)
    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


@pytest_asyncio.fixture
async def usuario_a(db_setup, tenant_a):
    """Usuario A belonging to tenant_a."""
    async with db_setup() as session:
        uid = await _create_usuario(session, tenant_a, "user-a@test.com")
    return uid


@pytest_asyncio.fixture
async def usuario_b(db_setup, tenant_a):
    """Usuario B belonging to tenant_a."""
    async with db_setup() as session:
        uid = await _create_usuario(session, tenant_a, "user-b@test.com")
    return uid


@pytest.fixture
async def materia_analisis(db_setup, tenant_a):
    """Materia de prueba para tests de analisis."""
    from app.models.materia import Materia, MateriaEstado

    async with db_setup() as session:
        materia = Materia(
            tenant_id=tenant_a,
            codigo="ANALISIS-101",
            nombre="Analisis Matematico I",
            estado=MateriaEstado.ACTIVA,
        )
        session.add(materia)
        await session.flush()
        mid = materia.id
    await session.commit()
    return mid


@pytest.fixture
async def umbral_analisis(db_setup, tenant_a, materia_analisis):
    """Umbral default 60% para la materia de analisis."""
    from app.domain.calificaciones.models.umbral_materia import UmbralMateria

    async with db_setup() as session:
        umbral = UmbralMateria(
            tenant_id=tenant_a,
            materia_id=materia_analisis,
            asignacion_id=None,
            umbral_pct=60,
            conjunto_aprobado=["A", "B+", "C", "7", "8", "9", "10"],
        )
        session.add(umbral)
        await session.flush()
        uid = umbral.id
    return uid


@pytest.fixture
async def calificaciones_analisis(db_setup, tenant_a, materia_analisis, usuario_a):
    """Calificaciones de prueba: 3 actividades, 2 aprobadas, 1 sin nota."""
    from app.domain.calificaciones.models.calificacion import Calificacion

    async with db_setup() as session:
        calif1 = Calificacion(
            tenant_id=tenant_a,
            materia_id=materia_analisis,
            usuario_id=usuario_a,
            asignacion_id=None,
            nota=7.5,
            origen="Importado",
        )
        calif2 = Calificacion(
            tenant_id=tenant_a,
            materia_id=materia_analisis,
            usuario_id=usuario_a,
            asignacion_id=None,
            nota=8.0,
            origen="Importado",
        )
        calif3 = Calificacion(
            tenant_id=tenant_a,
            materia_id=materia_analisis,
            usuario_id=usuario_a,
            asignacion_id=None,
            nota=None,
            origen="Importado",
        )
        session.add_all([calif1, calif2, calif3])
        await session.flush()
    await session.commit()