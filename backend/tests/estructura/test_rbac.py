"""Strict TDD for estructura RBAC permissions (C-06 §5.5).

Tests that require_permission("estructura:gestionar") correctly
enforces access: 403 without permission, 2xx with permission.
"""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test"
)

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.core.security.passwords import hash_password
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.main import app
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.constants import GLOBAL_TENANT_ID

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


@pytest_asyncio.fixture
async def db_setup():
    """Isolated schema for permission tests — module-scoped to avoid
    engine-disposal conflicts with the app's cached engine pool."""
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        # drop_all doesn't clean up custom enum types — purge them manually
        await conn.execute(sqlalchemy.text("DROP TYPE IF EXISTS contexto_tipo CASCADE"))
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _setup_with_permission(db_setup) -> tuple[str, UUID, UUID]:
    """Setup tenant + user WITH estructura:gestionar permission.
    Returns (jwt_token, tenant_id, user_id).
    """
    from app.auth.models import AuthSession, AuthUser
    from app.rbac.models import Permiso, Rol, RolPermiso

    async with db_setup() as session:
        # Global tenant
        t = Tenant(
            id=GLOBAL_TENANT_ID,
            codigo="GLOBAL",
            nombre="Global System Tenant",
            estado=TenantEstado.ACTIVO,
        )
        session.add(t)

        # ADMIN role
        admin_rol = Rol(
            id=UUID("00000000-0000-0000-0000-a00000000006"),
            tenant_id=GLOBAL_TENANT_ID,
            nombre="ADMIN",
            descripcion="Admin",
        )
        session.add(admin_rol)

        # estructura:gestionar permiso
        perm = Permiso(
            tenant_id=GLOBAL_TENANT_ID,
            modulo="estructura",
            accion="gestionar",
        )
        session.add(perm)
        await session.flush()

        rp = RolPermiso(
            tenant_id=GLOBAL_TENANT_ID,
            rol_id=admin_rol.id,
            permiso_id=perm.id,
        )
        session.add(rp)
        await session.flush()

        # Test tenant
        test_tenant = Tenant(codigo=f"TENANT-{uuid4().hex[:8]}", nombre="Test", estado=TenantEstado.ACTIVO)
        session.add(test_tenant)
        await session.flush()
        tid = test_tenant.id

        # Auth user
        uid = uuid4()
        u = AuthUser(
            id=uid,
            tenant_id=tid,
            email_enc=f"enc:admin@test.com",
            email_hash=hash_email_for_search("admin@test.com", tid),
            password_hash=hash_password("Pa55word!"),
        )
        session.add(u)
        await session.flush()

        # Session
        now = datetime.now(timezone.utc)
        sid = uuid4()
        s = AuthSession(
            tenant_id=tid,
            user_id=uid,
            refresh_token_hash="hash",
            jti=uuid4(),
            issued_at=now,
            expires_at=now + timedelta(days=1),
            id=sid,
        )
        session.add(s)
        await session.commit()

        token = encode_access_token(user_id=uid, tenant_id=tid, session_id=sid, jti=uuid4())
        return token, tid, uid


async def _setup_without_permission(db_setup) -> tuple[str, UUID, UUID]:
    """Setup tenant + user WITHOUT estructura:gestionar permission.
    The global tenant exists but has NO roles or permissions.
    Returns (jwt_token, tenant_id, user_id).
    """
    from app.auth.models import AuthSession, AuthUser

    async with db_setup() as session:
        # Global tenant (empty - no permissions)
        t = Tenant(
            id=GLOBAL_TENANT_ID,
            codigo="GLOBAL",
            nombre="Global System Tenant",
            estado=TenantEstado.ACTIVO,
        )
        session.add(t)

        # Test tenant
        test_tenant = Tenant(codigo="TENANT-NOPERM", nombre="NoPerm", estado=TenantEstado.ACTIVO)
        session.add(test_tenant)
        await session.flush()
        tid = test_tenant.id

        uid = uuid4()
        u = AuthUser(
            id=uid,
            tenant_id=tid,
            email_enc=f"enc:noperm@test.com",
            email_hash=hash_email_for_search("noperm@test.com", tid),
            password_hash=hash_password("Pa55word!"),
        )
        session.add(u)
        await session.flush()

        now = datetime.now(timezone.utc)
        sid = uuid4()
        s = AuthSession(
            tenant_id=tid,
            user_id=uid,
            refresh_token_hash="hash",
            jti=uuid4(),
            issued_at=now,
            expires_at=now + timedelta(days=1),
            id=sid,
        )
        session.add(s)
        await session.commit()

        token = encode_access_token(user_id=uid, tenant_id=tid, session_id=sid, jti=uuid4())
        return token, tid, uid


# ── With permission: 2xx ───────────────────────────────────────────


async def test_list_carreras_with_permission_returns_200(db_setup) -> None:
    token, tid, uid = await _setup_with_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


async def test_create_carrera_with_permission_returns_201(db_setup) -> None:
    token, tid, uid = await _setup_with_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/admin/carreras",
            json={"codigo": "ING-INF", "nombre": "Ingenieria Informatica"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201


async def test_list_cohortes_with_permission_returns_200(db_setup) -> None:
    token, tid, uid = await _setup_with_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/admin/cohortes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


async def test_list_materias_with_permission_returns_200(db_setup) -> None:
    token, tid, uid = await _setup_with_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ── Without permission: 403 ────────────────────────────────────────


async def test_list_carreras_without_permission_returns_403(db_setup) -> None:
    token, tid, uid = await _setup_without_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


async def test_create_carrera_without_permission_returns_403(db_setup) -> None:
    token, tid, uid = await _setup_without_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/admin/carreras",
            json={"codigo": "ING-INF", "nombre": "Ingenieria"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


async def test_list_cohortes_without_permission_returns_403(db_setup) -> None:
    token, tid, uid = await _setup_without_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/admin/cohortes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


async def test_list_materias_without_permission_returns_403(db_setup) -> None:
    token, tid, uid = await _setup_without_permission(db_setup)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
