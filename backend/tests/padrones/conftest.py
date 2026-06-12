"""Fixtures para tests de padrones (C-09)."""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test"
)

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthSession, AuthUser
from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado


@pytest_asyncio.fixture
async def db_setup():
    """Isolated schema with all tables, session factory yielded."""
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia  # noqa: F401
    from app.models import asignacion  # noqa: F401
    from app.models import padron  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _seed_global_tenant(session) -> None:
    """Seed global tenant with roles and permissions."""
    from app.rbac.constants import GLOBAL_TENANT_ID

    gid = GLOBAL_TENANT_ID
    existing = await session.get(Tenant, gid)
    if existing is None:
        t = Tenant(
            id=gid,
            codigo="GLOBAL",
            nombre="Global System Tenant",
            estado=TenantEstado.ACTIVO,
        )
        session.add(t)
        await session.flush()


async def _create_tenant(session, codigo="TENANT-TEST") -> Tenant:
    t = Tenant(codigo=codigo, nombre="Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_auth_user(session, tenant_id: UUID, email: str) -> AuthUser:
    u = AuthUser(
        id=uuid4(),
        tenant_id=tenant_id,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(u)
    await session.flush()
    return u


async def _create_usuario_model(session, tenant_id: UUID, email: str) -> None:
    """Create a Usuario record with properly encrypted PII fields."""
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


@pytest_asyncio.fixture
async def tenant_a(db_setup):
    """Tenant A with admin user, tenant context set."""
    async with db_setup() as session:
        await _seed_global_tenant(session)
        t = await _create_tenant(session, "TENANTA")
        await session.commit()
        await session.refresh(t)

    # Set tenant context for the test
    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


@pytest_asyncio.fixture
async def tenant_b(db_setup):
    """Tenant B with admin user, tenant context set."""
    async with db_setup() as session:
        await _seed_global_tenant(session)
        t = await _create_tenant(session, "TENANTB")
        await session.commit()
        await session.refresh(t)

    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


@pytest_asyncio.fixture
async def user_admin_a(db_setup, tenant_a):
    """Admin AuthUser + Usuario for tenant A. Returns Usuario record."""
    async with db_setup() as session:
        await _create_auth_user(session, tenant_a, "admin-a@test.com")
        await _create_usuario_model(session, tenant_a, "admin-a@test.com")
        await session.commit()
        from app.models.usuario import Usuario
        result = await session.execute(
            sqlalchemy.select(Usuario).where(Usuario.tenant_id == tenant_a)
        )
        user = result.scalar_one()
        await session.refresh(user)
        # Return a simple dict with the user id since we can't return the model across sessions
        user_id = user.id
    return user_id


@pytest_asyncio.fixture
async def user_admin_b(db_setup, tenant_b):
    """Admin AuthUser + Usuario for tenant B."""
    async with db_setup() as session:
        await _create_auth_user(session, tenant_b, "admin-b@test.com")
        await _create_usuario_model(session, tenant_b, "admin-b@test.com")
        await session.commit()
        from app.models.usuario import Usuario
        result = await session.execute(
            sqlalchemy.select(Usuario).where(Usuario.tenant_id == tenant_b)
        )
        user = result.scalar_one()
        user_id = user.id
    return user_id