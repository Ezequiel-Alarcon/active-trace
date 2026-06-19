"""Strict TDD para GET /api/auth/session (C-21 frontend session endpoint).

Escenarios cubiertos:
- test_get_session_returns_401_without_auth: sin token → 401
- test_get_session_returns_user_and_permissions: usuario con roles y permisos → 200 con datos completos
- test_get_session_returns_empty_roles_and_permissions_without_assignments: usuario sin asignaciones → 200 con listas vacías

El endpoint devuelve identidad desde JWT verificado. Nunca desde parámetros de
URL, body ni headers adicionales.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthSession, AuthUser
from app.auth.routers.auth import router as auth_router
from app.core.dependencies import get_db
from app.core.security.crypto import encrypt
from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.core.security.passwords import hash_password
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.models import Permiso, Rol, RolPermiso

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test"
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_setup():
    """Esquema aislado por test con todas las tablas necesarias."""
    from app.models import tenant as _tenant_module  # noqa: F401
    from app.models import asignacion as _asig_module  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("""
            DO $$ DECLARE r RECORD; BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def app_client(db_setup):
    """Cliente HTTP con el router de auth montado y db override."""
    app = FastAPI()
    app.include_router(auth_router)

    async def override_get_db():
        async with db_setup() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _create_tenant(session, codigo: str = "SES-TEST") -> Tenant:
    t = Tenant(codigo=codigo, nombre="Session Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_user(session, tenant_id, email: str = "session@test.com") -> AuthUser:
    u = AuthUser(
        tenant_id=tenant_id,
        email_enc=encrypt(email, tenant_id=tenant_id, aad_suffix="usuario.email"),
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(u)
    await session.flush()
    return u


async def _create_auth_session(session, tenant_id, user_id) -> AuthSession:
    now = datetime.now(timezone.utc)
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        # TODO: (HACK) refresh_token_hash almacena texto plano intencional en fixtures de test; el endpoint /session no valida el refresh token, solo el JWT
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
    )
    session.add(s)
    await session.flush()
    return s


def _mint_jwt(user_id, tenant_id, session_id) -> str:
    return encode_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=uuid4(),
    )


# ── RED → GREEN → TRIANGULATE ─────────────────────────────────────────────────


async def test_get_session_returns_401_without_auth(app_client) -> None:
    """Sin token → 401. Independiente de DB — no necesita datos."""
    resp = await app_client.get("/api/auth/session")
    assert resp.status_code == 401


async def test_get_session_returns_user_and_permissions(app_client, db_setup) -> None:
    """Usuario con rol ADMIN que tiene permiso auditoria:ver → 200 con datos completos."""
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        tid = tenant.id

        # Crear rol con permiso
        rol = Rol(tenant_id=tid, nombre="ADMIN", descripcion="Administrador")
        session.add(rol)
        await session.flush()

        perm = Permiso(tenant_id=tid, modulo="auditoria", accion="ver")
        session.add(perm)
        await session.flush()

        session.add(RolPermiso(tenant_id=tid, rol_id=rol.id, permiso_id=perm.id))
        await session.flush()

        # Crear usuario con asignacion vigente al rol
        user = await _create_user(session, tid, email="admin@test.com")
        today = date.today()
        asig = Asignacion(
            tenant_id=tid,
            usuario_id=user.id,
            rol_id=rol.id,
            contexto_tipo=ContextoTipo.GLOBAL,
            contexto_id=None,
            desde=today - timedelta(days=30),
            hasta=None,
        )
        session.add(asig)
        auth_sess = await _create_auth_session(session, tid, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tid, auth_sess.id)

    resp = await app_client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["user_id"] == str(user.id)
    assert data["tenant_id"] == str(tid)
    assert data["email"] == "admin@test.com"
    assert "ADMIN" in data["roles"]
    assert "auditoria:ver" in data["permissions"]


async def test_get_session_returns_empty_roles_and_permissions_without_assignments(
    app_client, db_setup
) -> None:
    """Usuario sin asignaciones → 200 con roles=[] y permissions=[]."""
    async with db_setup() as session:
        tenant = await _create_tenant(session, codigo="SES-EMPTY")
        tid = tenant.id
        user = await _create_user(session, tid, email="norolls@test.com")
        auth_sess = await _create_auth_session(session, tid, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tid, auth_sess.id)

    resp = await app_client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["user_id"] == str(user.id)
    assert data["tenant_id"] == str(tid)
    assert data["email"] == "norolls@test.com"
    assert data["roles"] == []
    assert data["permissions"] == []


async def test_get_session_excludes_expired_assignments(app_client, db_setup) -> None:
    """Asignaciones vencidas (hasta en el pasado) no se incluyen en roles/permisos."""
    async with db_setup() as session:
        tenant = await _create_tenant(session, codigo="SES-EXP")
        tid = tenant.id

        rol = Rol(tenant_id=tid, nombre="PROFESOR", descripcion="Profesor")
        session.add(rol)
        await session.flush()

        perm = Permiso(tenant_id=tid, modulo="estructura", accion="gestionar")
        session.add(perm)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol.id, permiso_id=perm.id))

        user = await _create_user(session, tid, email="expired@test.com")
        yesterday = date.today() - timedelta(days=1)
        # Asignacion ya vencida
        asig = Asignacion(
            tenant_id=tid,
            usuario_id=user.id,
            rol_id=rol.id,
            contexto_tipo=ContextoTipo.GLOBAL,
            contexto_id=None,
            desde=date.today() - timedelta(days=60),
            hasta=yesterday,
        )
        session.add(asig)
        auth_sess = await _create_auth_session(session, tid, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tid, auth_sess.id)

    resp = await app_client.get(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["roles"] == []
    assert data["permissions"] == []
