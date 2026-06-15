"""Integration tests for audit API endpoints (C-05 §9)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthSession, AuthUser
from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.main import app
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.models import Permiso, Rol, RolPermiso

pytestmark = pytest.mark.no_db


@pytest_asyncio.fixture
async def db_setup(_reset_app_engine_async):  # noqa: F811
    """Bring up an isolated schema in the test database and yield a session factory."""
    from app.models import tenant  # noqa: F401
    from app.models import usuario, asignacion, carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.audit import models as _audit_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        # TODO: (HACK) SQL raw con CASCADE en lugar de Base.metadata.drop_all() — ver
        # backend/tests/calificaciones/conftest.py para explicación completa.
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


async def _seed_tenant(session) -> Tenant:
    from app.rbac.constants import GLOBAL_TENANT_ID
    gid = GLOBAL_TENANT_ID

    existing = await session.get(Tenant, gid)
    if existing is None:
        g = Tenant(id=gid, codigo="GLOBAL", nombre="Global System Tenant", estado=TenantEstado.ACTIVO)
        session.add(g)
        await session.flush()

    t = Tenant(codigo="AUDIT-TEST", nombre="Audit Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _make_auth_user(session, tenant_id: UUID, email: str = "admin@test.com") -> AuthUser:
    u = AuthUser(
        tenant_id=tenant_id,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash="hash-placeholder",
    )
    session.add(u)
    await session.flush()
    return u


async def _make_session(session, user_id: UUID, tenant_id: UUID) -> AuthSession:
    now = datetime.now(timezone.utc)
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
    )
    session.add(s)
    await session.flush()
    return s


def _mint_jwt(user_id: UUID, tenant_id: UUID, session_id: UUID) -> str:
    return encode_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=uuid4(),
    )


async def _create_role_with_permission(
    session, tenant_id: UUID, role_name: str, modulo: str, accion: str
) -> Rol:
    rol = Rol(tenant_id=tenant_id, nombre=role_name, descripcion=f"{role_name} role")
    session.add(rol)
    await session.flush()

    perm = Permiso(tenant_id=tenant_id, modulo=modulo, accion=accion)
    session.add(perm)
    await session.flush()

    rp = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=perm.id)
    session.add(rp)
    await session.flush()

    return rol


# ── GET /api/audit/log ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_audit_log_returns_401_without_auth(db_setup) -> None:
    """GET /api/audit/log returns 401 when no Authorization header is provided."""
    async with db_setup() as session:
        await _seed_tenant(session)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/audit/log")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_audit_log_returns_403_without_permission(db_setup) -> None:
    """GET /api/audit/log returns 403 when user lacks auditoria:ver permission."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        user = await _make_auth_user(session, t.id, "noperm@test.com")
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await session.commit()
        user_id, tenant_id, session_id = user.id, t.id, sess.id

    token = _mint_jwt(user_id, tenant_id, session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/log",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_audit_log_returns_paginated_results(db_setup) -> None:
    """GET /api/audit/log returns paginated audit log entries."""
    from app.audit.repositories import AuditLogRepository

    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        user = await _make_auth_user(session, t.id, "viewer@test.com")
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "AUDITOR", "auditoria", "ver")
        await session.commit()
        user_id, tenant_id, session_id = user.id, t.id, sess.id

    token = _mint_jwt(user_id, tenant_id, session_id)

    async with db_setup() as session:
        repo = AuditLogRepository(session, tenant_id)
        for i in range(3):
            await repo.create(
                actor_id=user_id,
                accion="LOGIN_EXITO",
                detalle={"attempt": i},
            )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/log",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_get_audit_log_filters_by_actor_id(db_setup) -> None:
    """GET /api/audit/log filters by actor_id query parameter."""
    from app.audit.repositories import AuditLogRepository

    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        user = await _make_auth_user(session, t.id, "filter@test.com")
        other_user = AuthUser(
            tenant_id=t.id,
            email_enc="enc:other@test.com",
            email_hash=hash_email_for_search("other@test.com", t.id),
            password_hash="hash",
        )
        session.add(other_user)
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "AUDITOR2", "auditoria", "ver")
        await session.commit()
        user_id, other_id, tenant_id, session_id = user.id, other_user.id, t.id, sess.id

    token = _mint_jwt(user_id, tenant_id, session_id)

    async with db_setup() as session:
        repo = AuditLogRepository(session, tenant_id)
        await repo.create(actor_id=user_id, accion="LOGIN_EXITO")
        await repo.create(actor_id=other_id, accion="LOGOUT")
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/audit/log?actor={user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert all(item["actor_id"] == str(user_id) for item in data["items"])


@pytest.mark.asyncio
async def test_get_audit_log_filters_by_accion(db_setup) -> None:
    """GET /api/audit/log filters by accion query parameter."""
    from app.audit.repositories import AuditLogRepository

    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        user = await _make_auth_user(session, t.id, "filter2@test.com")
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "AUDITOR3", "auditoria", "ver")
        await session.commit()
        user_id, tenant_id, session_id = user.id, t.id, sess.id

    token = _mint_jwt(user_id, tenant_id, session_id)

    async with db_setup() as session:
        repo = AuditLogRepository(session, tenant_id)
        await repo.create(actor_id=user_id, accion="LOGIN_EXITO")
        await repo.create(actor_id=user_id, accion="LOGOUT")
        await repo.create(actor_id=user_id, accion="LOGIN_FALLO")
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/log?accion=LOGIN_EXITO",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert all(item["accion"] == "LOGIN_EXITO" for item in data["items"])


# ── POST /api/impersonation/start ────────────────────────────────────


@pytest.mark.asyncio
async def test_post_impersonation_start_returns_403_without_permission(db_setup) -> None:
    """POST /api/impersonation/start returns 403 when user lacks impersonacion:usar."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        user = await _make_auth_user(session, t.id, "noimp@test.com")
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await session.commit()
        user_id, tenant_id, session_id = user.id, t.id, sess.id

    token = _mint_jwt(user_id, tenant_id, session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/impersonation/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"target_user_id": str(uuid4())},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_impersonation_start_creates_audit_entry(db_setup) -> None:
    """POST /api/impersonation/start creates an audit log entry."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        admin = await _make_auth_user(session, t.id, "adminimp@test.com")
        target = AuthUser(
            tenant_id=t.id,
            email_enc="enc:target@test.com",
            email_hash=hash_email_for_search("target@test.com", t.id),
            password_hash="hash",
        )
        session.add(target)
        await session.flush()
        sess = await _make_session(session, admin.id, t.id)
        await _create_role_with_permission(session, t.id, "IMPERSONATOR", "impersonacion", "usar")
        await session.commit()
        admin_id, target_id, tenant_id, session_id = admin.id, target.id, t.id, sess.id

    token = _mint_jwt(admin_id, tenant_id, session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/impersonation/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"target_user_id": str(target_id)},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["impersonated_user_id"] == str(target_id)
    assert "message" in data

    async with db_setup() as session:
        from sqlalchemy import select
        from app.audit.models import AuditLog
        result = await session.execute(
            select(AuditLog).where(AuditLog.actor_id == admin_id)
        )
        entries = list(result.scalars().all())
        assert len(entries) >= 1
        impersonacion_entries = [e for e in entries if e.accion == "IMPERSONACION_INICIAR"]
        assert len(impersonacion_entries) >= 1


# ── DELETE /api/impersonation/end ────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_impersonation_end_returns_403_without_permission(db_setup) -> None:
    """DELETE /api/impersonation/end returns 403 when user lacks impersonacion:usar."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        user = await _make_auth_user(session, t.id, "noimp2@test.com")
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await session.commit()
        user_id, tenant_id, session_id = user.id, t.id, sess.id

    token = _mint_jwt(user_id, tenant_id, session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(
            "DELETE",
            "/api/impersonation/end",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_impersonation_end_creates_audit_entry(db_setup) -> None:
    """DELETE /api/impersonation/end creates an audit log entry."""
    from app.audit.impersonation import start_impersonation

    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.flush()
        admin = await _make_auth_user(session, t.id, "adminimp2@test.com")
        target = AuthUser(
            tenant_id=t.id,
            email_enc="enc:target2@test.com",
            email_hash=hash_email_for_search("target2@test.com", t.id),
            password_hash="hash",
        )
        session.add(target)
        await session.flush()
        sess = await _make_session(session, admin.id, t.id)
        await _create_role_with_permission(session, t.id, "IMPERSONATOR2", "impersonacion", "usar")
        await session.commit()
        admin_id, target_id, tenant_id, session_id = admin.id, target.id, t.id, sess.id

    start_impersonation(admin_id, target_id)

    token = _mint_jwt(admin_id, tenant_id, session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(
            "DELETE",
            "/api/impersonation/end",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 204

    async with db_setup() as session:
        from sqlalchemy import select
        from app.audit.models import AuditLog
        result = await session.execute(
            select(AuditLog).where(AuditLog.actor_id == admin_id)
        )
        entries = list(result.scalars().all())
        impersonacion_entries = [e for e in entries if e.accion == "IMPERSONACION_FINALIZAR"]
        assert len(impersonacion_entries) >= 1