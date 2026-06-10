"""Fixtures compartidos para tests de estructura (C-06 §5)."""

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

from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.constants import GLOBAL_TENANT_ID
from app.rbac.models import Permiso, Rol, RolPermiso


@pytest_asyncio.fixture
async def db_setup():
    """Bring up an isolated schema with all tables and return a session factory."""
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia  # noqa: F401
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
    """Seed the global tenant with all RBAC roles and permissions."""
    from app.rbac.constants import GLOBAL_TENANT_ID

    gid = GLOBAL_TENANT_ID

    # Global tenant record — only if not exists
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

    # ADMIN role — only if not exists
    admin_rol_id = UUID("00000000-0000-0000-0000-a00000000006")
    existing_rol = await session.get(Rol, admin_rol_id)
    if existing_rol is None:
        admin_rol = Rol(
            id=admin_rol_id,
            tenant_id=gid,
            nombre="ADMIN",
            descripcion="Administrador del sistema dentro del tenant",
        )
        session.add(admin_rol)

    # estructura:gestionar permiso — only if not exists
    perm_id = UUID("00000000-0000-0000-0001-a00000000015")
    existing_perm = await session.get(Permiso, perm_id)
    if existing_perm is None:
        perm = Permiso(
            id=perm_id,
            tenant_id=gid,
            modulo="estructura",
            accion="gestionar",
        )
        session.add(perm)
    await session.flush()

    # RolPermiso — only if not exists
    from sqlalchemy import select
    existing_rp = await session.execute(
        select(RolPermiso).where(
            RolPermiso.tenant_id == gid,
            RolPermiso.rol_id == admin_rol_id,
            RolPermiso.permiso_id == perm_id,
        )
    )
    rp = existing_rp.scalar_one_or_none()
    if rp is None:
        rp = RolPermiso(
            tenant_id=gid,
            rol_id=admin_rol_id,
            permiso_id=perm_id,
        )
        session.add(rp)
    await session.flush()


async def _create_tenant(session) -> Tenant:
    t = Tenant(codigo="TENANT-TEST", nombre="Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_user_and_session(session, tenant_id: UUID) -> tuple[UUID, UUID, UUID]:
    """Create auth user and session, return (user_id, tenant_id, session_id)."""
    from app.auth.models import AuthSession, AuthUser

    user_id = uuid4()
    u = AuthUser(
        id=user_id,
        tenant_id=tenant_id,
        email_enc=f"enc:test@test.com",
        email_hash=hash_email_for_search("test@test.com", tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(u)
    await session.flush()

    now = datetime.now(timezone.utc)
    session_id = uuid4()
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
        id=session_id,
    )
    session.add(s)
    await session.flush()
    return user_id, tenant_id, session_id
