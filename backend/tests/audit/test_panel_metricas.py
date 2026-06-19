"""Integration tests for audit metrics panel (C-19)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.models import AuthSession, AuthUser
from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.main import app
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.models import Permiso, Rol, RolPermiso

pytestmark = [pytest.mark.no_db, pytest.mark.asyncio]

_ALL_ENGINES: list[object] = []


@pytest.fixture(scope="session", autouse=True)
def _cleanup_engines():
    """Prevent engine GC across test boundaries — Windows asyncpg issue."""
    yield
    # At session end, all engines can be GC'd safely
    _ALL_ENGINES.clear()


@pytest_asyncio.fixture(scope="function")
async def db_setup(_reset_app_engine_async):  # noqa: F811
    """Bring up an isolated schema per test, yield a session factory."""
    from app.models import tenant  # noqa: F401
    from app.models import usuario, asignacion, carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.audit import models as _audit_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    _ALL_ENGINES.append(engine)
    async with engine.begin() as conn:
        # TODO: (HACK) SQL raw con CASCADE en lugar de Base.metadata.drop_all() — ver
        # backend/tests/calificaciones/conftest.py para explicación completa.
        # NullPool se usa aquí adicionalmente para evitar que asyncpg retenga
        # conexiones entre tests en Windows (GC issue con event loops).
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


async def _seed_tenant(session) -> Tenant:
    from app.rbac.constants import GLOBAL_TENANT_ID
    gid = GLOBAL_TENANT_ID

    existing = await session.get(Tenant, gid)
    if existing is None:
        g = Tenant(id=gid, codigo="GLOBAL", nombre="Global System Tenant", estado=TenantEstado.ACTIVO)
        session.add(g)
        await session.flush()

    t = Tenant(codigo="METRICS-TEST", nombre="Metrics Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _make_auth_user(session, tenant_id, email="admin@test.com"):
    u = AuthUser(
        tenant_id=tenant_id,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash="hash-placeholder",
    )
    session.add(u)
    await session.flush()
    return u


async def _make_session(session, user_id, tenant_id):
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


def _mint_jwt(user_id, tenant_id, session_id):
    return encode_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=uuid4(),
    )


async def _create_role_with_permission(
    session, tenant_id, role_name, modulo, accion, user_id=None,
):
    rol = Rol(tenant_id=tenant_id, nombre=role_name, descripcion=f"{role_name} role")
    session.add(rol)
    await session.flush()

    perm = Permiso(tenant_id=tenant_id, modulo=modulo, accion=accion)
    session.add(perm)
    await session.flush()

    rp = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=perm.id)
    session.add(rp)
    await session.flush()

    if user_id is not None:
        from datetime import date
        session.add(Asignacion(
            tenant_id=tenant_id, usuario_id=user_id, rol_id=rol.id,
            contexto_tipo=ContextoTipo.GLOBAL, desde=date(2024, 1, 1),
        ))

    return rol


async def _create_role_with_multiple_permissions(session, tenant_id, role_name, permissions, user_id=None):
    rol = Rol(tenant_id=tenant_id, nombre=role_name, descripcion=f"{role_name} role")
    session.add(rol)
    await session.flush()

    for modulo, accion in permissions:
        perm = Permiso(tenant_id=tenant_id, modulo=modulo, accion=accion)
        session.add(perm)
        await session.flush()

        rp = RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=perm.id)
        session.add(rp)
        await session.flush()

    if user_id is not None:
        from datetime import date
        session.add(Asignacion(
            tenant_id=tenant_id, usuario_id=user_id, rol_id=rol.id,
            contexto_tipo=ContextoTipo.GLOBAL, desde=date(2024, 1, 1),
        ))

    return rol


async def _seed_audit_entries(session, tenant_id, *,
                              actor_id,
                              materia_id_a=None,
                              materia_id_b=None,
                              other_actor_id=None):
    from app.audit.repositories import AuditLogRepository

    repo = AuditLogRepository(session, tenant_id)

    entry1 = await repo.create(actor_id=actor_id, accion="LOGIN_EXITO", materia_id=materia_id_a)
    entry1.fecha_hora = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

    entry2 = await repo.create(actor_id=actor_id, accion="LOGOUT", materia_id=materia_id_a)
    entry2.fecha_hora = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    entry3 = await repo.create(
        actor_id=actor_id if other_actor_id is None else other_actor_id,
        accion="LOGIN_EXITO", materia_id=materia_id_b,
    )
    entry3.fecha_hora = datetime(2025, 6, 2, 9, 0, 0, tzinfo=timezone.utc)

    entry4 = await repo.create(
        actor_id=actor_id, accion="COMUNICACION_ENVIAR",
        materia_id=materia_id_a, detalle={"from": "Enviando", "to": "Enviado"},
    )
    entry4.fecha_hora = datetime(2025, 6, 1, 14, 0, 0, tzinfo=timezone.utc)

    entry5 = await repo.create(
        actor_id=actor_id, accion="COMUNICACION_ENVIAR",
        materia_id=materia_id_a, detalle={"from": "Pendiente", "to": "Error"},
    )
    entry5.fecha_hora = datetime(2025, 6, 1, 15, 0, 0, tzinfo=timezone.utc)

    entry6 = await repo.create(
        actor_id=actor_id, accion="COMUNICACION_APROBAR",
        materia_id=materia_id_a, detalle={"from": "Pendiente", "to": "Enviando"},
    )
    entry6.fecha_hora = datetime(2025, 6, 2, 8, 0, 0, tzinfo=timezone.utc)

    entry7 = await repo.create(actor_id=actor_id, accion="MATERIA_CREAR", materia_id=materia_id_a)
    entry7.fecha_hora = datetime(2025, 6, 3, 10, 0, 0, tzinfo=timezone.utc)

    await session.flush()
    return [entry1, entry2, entry3, entry4, entry5, entry6, entry7]


# ── GET /api/audit/metrics/actions-per-day ───────────────────────────────────


async def test_actions_per_day_returns_grouped_counts(db_setup) -> None:
    """Returns actions grouped by day, ordered by date ascending."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "apd@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER", "auditoria", "ver", user_id=user.id)
        materia_id = uuid4()
        await _seed_audit_entries(session, t.id,
                                  actor_id=user.id,
                                  materia_id_a=materia_id,
                                  materia_id_b=uuid4())
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/actions-per-day",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    dates = [item["date"] for item in data]
    assert dates == sorted(dates)


async def test_actions_per_day_filters_by_actor(db_setup) -> None:
    """When actor_id is provided, only that actor's actions are counted."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "apd2@test.com")
        other = AuthUser(
            tenant_id=t.id,
            email_enc="enc:other_apd@test.com",
            email_hash=hash_email_for_search("other_apd@test.com", t.id),
            password_hash="hash",
        )
        session.add(other)
        await session.flush()
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER2", "auditoria", "ver", user_id=user.id)

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        e1 = await repo.create(actor_id=user.id, accion="LOGIN_EXITO")
        e1.fecha_hora = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        e2 = await repo.create(actor_id=other.id, accion="LOGOUT")
        e2.fecha_hora = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        e3 = await repo.create(actor_id=user.id, accion="LOGIN_FALLO")
        e3.fecha_hora = datetime(2025, 6, 2, 9, 0, 0, tzinfo=timezone.utc)
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/audit/metrics/actions-per-day?actor_id={user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    total = sum(item["count"] for item in data)
    assert total == 2


async def test_actions_per_day_respects_tenant_scope(db_setup) -> None:
    """Data from other tenants is not visible."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        t2 = Tenant(codigo="METRICS-OTHER", nombre="Other Tenant", estado=TenantEstado.ACTIVO)
        session.add(t2)
        await session.flush()
        user = await _make_auth_user(session, t.id, "apd3@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER3", "auditoria", "ver", user_id=user.id)

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        e1 = await repo.create(actor_id=user.id, accion="LOGIN_EXITO")
        e1.fecha_hora = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        repo2 = AuditLogRepository(session, t2.id)
        e2 = await repo2.create(actor_id=user.id, accion="LOGIN_EXITO")
        e2.fecha_hora = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/actions-per-day",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    total = sum(item["count"] for item in data)
    assert total == 1


# ── GET /api/audit/metrics/comunicacion-status ───────────────────────────────


async def test_comunicacion_status_returns_grouped_counts(db_setup) -> None:
    """Returns communication status counts grouped by materia and docente."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "coms@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER4", "auditoria", "ver", user_id=user.id)

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        materia_id = uuid4()
        await repo.create(actor_id=user.id, accion="COMUNICACION_ENVIAR",
                          materia_id=materia_id, detalle={"from": "Enviando", "to": "Enviado"})
        await repo.create(actor_id=user.id, accion="COMUNICACION_ENVIAR",
                          materia_id=materia_id, detalle={"from": "Pendiente", "to": "Error"})
        await repo.create(actor_id=user.id, accion="COMUNICACION_APROBAR",
                          materia_id=materia_id, detalle={"from": "Pendiente", "to": "Enviando"})
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/comunicacion-status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    item = data[0]
    assert item["docente_id"] == str(user.id)
    assert item["materia_id"] == str(materia_id)
    assert item["pending"] >= 0
    assert item["sending"] >= 1
    assert item["ok"] >= 1
    assert item["failed"] >= 1


# ── GET /api/audit/metrics/interactions ─────────────────────────────────────


async def test_interactions_summary_returns_grouped_counts(db_setup) -> None:
    """Returns interaction counts grouped by materia, docente, and action."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "inter@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER5", "auditoria", "ver", user_id=user.id)

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        materia_id = uuid4()
        await repo.create(actor_id=user.id, accion="LOGIN_EXITO", materia_id=materia_id)
        await repo.create(actor_id=user.id, accion="LOGIN_EXITO", materia_id=materia_id)
        await repo.create(actor_id=user.id, accion="LOGOUT", materia_id=materia_id)
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/interactions",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    login_items = [i for i in data if i["accion"] == "LOGIN_EXITO"]
    logout_items = [i for i in data if i["accion"] == "LOGOUT"]
    assert len(login_items) >= 1
    assert login_items[0]["count"] >= 2
    assert len(logout_items) >= 1
    assert logout_items[0]["count"] >= 1


# ── GET /api/audit/metrics/last-actions ──────────────────────────────────────


async def test_last_actions_returns_most_recent(db_setup) -> None:
    """Returns the most recent audit entries ordered by fecha_hora descending."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "last@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER6", "auditoria", "ver", user_id=user.id)

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        e1 = await repo.create(actor_id=user.id, accion="FIRST")
        e1.fecha_hora = datetime(2025, 1, 1, tzinfo=timezone.utc)
        e2 = await repo.create(actor_id=user.id, accion="SECOND")
        e2.fecha_hora = datetime(2025, 6, 1, tzinfo=timezone.utc)
        e3 = await repo.create(actor_id=user.id, accion="THIRD")
        e3.fecha_hora = datetime(2025, 12, 1, tzinfo=timezone.utc)
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/last-actions",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    acciones = [item["accion"] for item in data]
    assert acciones == ["THIRD", "SECOND", "FIRST"]


async def test_last_actions_respects_limit(db_setup) -> None:
    """The limit parameter is respected."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "last2@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_permission(session, t.id, "VIEWER7", "auditoria", "ver", user_id=user.id)

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        for i in range(5):
            e = await repo.create(actor_id=user.id, accion=f"ACTION_{i}")
            e.fecha_hora = datetime(2025, 6, i + 1, tzinfo=timezone.utc)
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/last-actions?limit=3",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


# ── COORDINADOR scope ────────────────────────────────────────────────────────


async def test_coordinador_scope_filters_by_materia(db_setup) -> None:
    """COORDINADOR (without ver_todos) only sees data for their assigned materias."""
    from app.audit.repositories import AuditLogRepository
    from app.models.asignacion import Asignacion, ContextoTipo

    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "coord@test.com")
        sess = await _make_session(session, user.id, t.id)
        rol = await _create_role_with_permission(session, t.id, "COORDINADOR", "auditoria", "ver")
        materia_a = uuid4()
        materia_b = uuid4()
        asig = Asignacion(
            tenant_id=t.id,
            usuario_id=user.id,
            rol_id=rol.id,
            contexto_tipo=ContextoTipo.MATERIA,
            contexto_id=materia_a,
            desde=datetime(2025, 1, 1).date(),
        )
        session.add(asig)

        repo = AuditLogRepository(session, t.id)
        await repo.create(actor_id=user.id, accion="LOGIN_EXITO", materia_id=materia_a)
        await repo.create(actor_id=user.id, accion="LOGIN_EXITO", materia_id=materia_b)
        await repo.create(actor_id=user.id, accion="LOGOUT", materia_id=materia_a)
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/actions-per-day",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    total = sum(item["count"] for item in data)
    assert total == 2


async def test_admin_sees_all_data(db_setup) -> None:
    """ADMIN with auditoria:ver_todos sees all materias."""
    async with db_setup() as session:
        t = await _seed_tenant(session)
        user = await _make_auth_user(session, t.id, "admin@test.com")
        sess = await _make_session(session, user.id, t.id)
        await _create_role_with_multiple_permissions(
            session, t.id, "ADMIN",
            [("auditoria", "ver"), ("auditoria", "ver_todos")],
            user_id=user.id,
        )

        from app.audit.repositories import AuditLogRepository
        repo = AuditLogRepository(session, t.id)
        await repo.create(actor_id=user.id, accion="LOGIN_EXITO", materia_id=uuid4())
        await repo.create(actor_id=user.id, accion="LOGIN_EXITO", materia_id=uuid4())
        await repo.create(actor_id=user.id, accion="LOGOUT", materia_id=uuid4())
        await session.commit()
        token = _mint_jwt(user.id, t.id, sess.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/audit/metrics/actions-per-day",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    total = sum(item["count"] for item in data)
    assert total == 3
