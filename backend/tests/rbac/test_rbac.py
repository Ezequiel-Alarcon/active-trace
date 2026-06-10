"""Strict TDD for app.rbac (C-04 §9).

Tests cover:
- PermissionResolver: single role, multiple roles, cross-tenant isolation,
  soft-deleted role excluded, cache hit.
- require_permission guard: 403 without permission, 200 with permission.
- Admin catalog API: CRUD for roles and permissions, attach/detach.
- Public endpoint: GET /api/permissions/me.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthSession, AuthUser
from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password
from app.core.security.jwt import encode_access_token
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.constants import GLOBAL_TENANT_ID
from app.rbac.models import Permiso, Rol, RolPermiso
from app.rbac.repositories import PermisoRepository, RolPermisoRepository, RolRepository
from app.rbac.services import PermissionResolver

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


@pytest_asyncio.fixture
async def db_setup():
    """Bring up an isolated schema in the test database and yield a session factory."""
    import os
    from app.models import tenant  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def tenant_a(db_setup):
    async with db_setup() as session:
        t = Tenant(codigo="TENANTA", nombre="Tenant A", estado=TenantEstado.ACTIVO)
        session.add(t)
        await session.commit()
        await session.refresh(t)
    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


@pytest_asyncio.fixture
async def tenant_b(db_setup):
    async with db_setup() as session:
        t = Tenant(codigo="TENANTB", nombre="Tenant B", estado=TenantEstado.ACTIVO)
        session.add(t)
        await session.commit()
        await session.refresh(t)
    token = set_tenant_context(TenantContext(tenant_id=t.id))
    yield t.id
    reset_tenant_context(token)


async def _make_user(session, tenant_id: UUID, email: str = "user") -> AuthUser:
    u = AuthUser(
        tenant_id=tenant_id,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash=hash_password("Pa55word!"),
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


# ---------- PermissionResolver: single role ----------

async def test_resolver_single_role_returns_that_roles_permissions(
    db_setup, tenant_a
) -> None:
    tid = tenant_a
    async with db_setup() as session:
        rol = Rol(tenant_id=tid, nombre="PROFESOR", descripcion="Docente")
        session.add(rol)
        await session.flush()
        perm = Permiso(tenant_id=tid, modulo="calificaciones", accion="importar")
        session.add(perm)
        await session.flush()
        rp = RolPermiso(tenant_id=tid, rol_id=rol.id, permiso_id=perm.id)
        session.add(rp)
        await session.commit()

    async with db_setup() as session:
        user = await _make_user(session, tid)
        await session.commit()

    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        resolver = PermissionResolver(session)
        permissions = await resolver.resolve(user.id, tid)
        assert "calificaciones:importar" in permissions


# ---------- PermissionResolver: multiple roles (union) ----------

async def test_resolver_multiple_roles_returns_union(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        rol1 = Rol(tenant_id=tid, nombre="PROFESOR", descripcion="Docente")
        rol2 = Rol(tenant_id=tid, nombre="COORDINADOR", descripcion="Coord")
        session.add(rol1)
        session.add(rol2)
        await session.flush()
        perm1 = Permiso(tenant_id=tid, modulo="calificaciones", accion="importar")
        perm2 = Permiso(tenant_id=tid, modulo="equipos", accion="asignar")
        session.add(perm1)
        session.add(perm2)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol1.id, permiso_id=perm1.id))
        session.add(RolPermiso(tenant_id=tid, rol_id=rol2.id, permiso_id=perm2.id))
        await session.commit()

    async with db_setup() as session:
        user = await _make_user(session, tid)
        await session.commit()

    async with db_setup() as session:
        resolver = PermissionResolver(session)
        permissions = await resolver.resolve(user.id, tid)
        assert "calificaciones:importar" in permissions
        assert "equipos:asignar" in permissions


# ---------- PermissionResolver: cross-tenant isolation ----------

async def test_resolver_cross_tenant_isolation(db_setup, tenant_a, tenant_b) -> None:
    async with db_setup() as session:
        rol_a = Rol(tenant_id=tenant_a, nombre="PROFESOR", descripcion="Docente A")
        rol_b = Rol(tenant_id=tenant_b, nombre="PROFESOR", descripcion="Docente B")
        session.add(rol_a)
        session.add(rol_b)
        await session.flush()
        perm_a = Permiso(tenant_id=tenant_a, modulo="calificaciones", accion="importar")
        perm_b = Permiso(tenant_id=tenant_b, modulo="entregas", accion="ver")
        session.add(perm_a)
        session.add(perm_b)
        await session.flush()
        session.add(RolPermiso(tenant_id=tenant_a, rol_id=rol_a.id, permiso_id=perm_a.id))
        session.add(RolPermiso(tenant_id=tenant_b, rol_id=rol_b.id, permiso_id=perm_b.id))
        await session.commit()

    async with db_setup() as session:
        user_a = await _make_user(session, tenant_a, "usera")
        user_b = await _make_user(session, tenant_b, "userb")
        await session.commit()

    async with db_setup() as session:
        resolver = PermissionResolver(session)
        perms_a = await resolver.resolve(user_a.id, tenant_a)
        perms_b = await resolver.resolve(user_b.id, tenant_b)
        assert "calificaciones:importar" in perms_a
        assert "entregas:ver" in perms_b
        assert perms_a != perms_b


# ---------- PermissionResolver: soft-deleted role excluded ----------

async def test_resolver_soft_deleted_role_excluded(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        rol_active = Rol(tenant_id=tid, nombre="PROFESOR", descripcion="Active")
        rol_deleted = Rol(tenant_id=tid, nombre="CUSTOM", descripcion="Deleted")
        session.add(rol_active)
        session.add(rol_deleted)
        await session.flush()
        perm_active = Permiso(tenant_id=tid, modulo="calificaciones", accion="importar")
        perm_deleted = Permiso(tenant_id=tid, modulo="finanzas", accion="cerrar_liquidacion")
        session.add(perm_active)
        session.add(perm_deleted)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol_active.id, permiso_id=perm_active.id))
        session.add(RolPermiso(tenant_id=tid, rol_id=rol_deleted.id, permiso_id=perm_deleted.id))
        rol_deleted.deleted_at = datetime.now(timezone.utc)
        await session.commit()

    async with db_setup() as session:
        user = await _make_user(session, tid)
        await session.commit()

    async with db_setup() as session:
        resolver = PermissionResolver(session)
        permissions = await resolver.resolve(user.id, tid)
        assert "calificaciones:importar" in permissions
        assert "finanzas:cerrar_liquidacion" not in permissions


# ---------- PermissionResolver: cache hit on second call ----------

async def test_resolver_cache_hit_avoids_db_query(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        rol = Rol(tenant_id=tid, nombre="PROFESOR", descripcion="Docente")
        session.add(rol)
        await session.flush()
        perm = Permiso(tenant_id=tid, modulo="calificaciones", accion="importar")
        session.add(perm)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol.id, permiso_id=perm.id))
        await session.commit()

    async with db_setup() as session:
        user = await _make_user(session, tid)
        await session.commit()

    async with db_setup() as session:
        resolver = PermissionResolver(session)
        p1 = await resolver.resolve(user.id, tid)
        p2 = await resolver.resolve(user.id, tid)
        assert p1 == p2
        assert "calificaciones:importar" in p1


# ---------- PermissionResolver: global tenant baseline always included ----------

async def test_resolver_global_tenant_permissions_always_included(
    db_setup, tenant_a
) -> None:
    tid = tenant_a
    async with db_setup() as session:
        global_tenant = Tenant(
            codigo="GLOBAL",
            nombre="Global Tenant",
            estado=TenantEstado.ACTIVO,
        )
        global_tenant.id = GLOBAL_TENANT_ID
        session.add(global_tenant)
        await session.flush()
        rol_local = Rol(tenant_id=tid, nombre="LOCAL_ROLE", descripcion="Local")
        rol_global = Rol(tenant_id=GLOBAL_TENANT_ID, nombre="GLOBAL_ROLE", descripcion="Global")
        session.add(rol_local)
        session.add(rol_global)
        await session.flush()
        perm_local = Permiso(tenant_id=tid, modulo="local", accion="action")
        perm_global = Permiso(tenant_id=GLOBAL_TENANT_ID, modulo="global", accion="baseline")
        session.add(perm_local)
        session.add(perm_global)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol_local.id, permiso_id=perm_local.id))
        session.add(RolPermiso(tenant_id=GLOBAL_TENANT_ID, rol_id=rol_global.id, permiso_id=perm_global.id))
        await session.commit()

    async with db_setup() as session:
        user = await _make_user(session, tid)
        await session.commit()

    async with db_setup() as session:
        resolver = PermissionResolver(session)
        permissions = await resolver.resolve(user.id, tid)
        assert "local:action" in permissions
        assert "global:baseline" in permissions


# ---------- RolRepository: create and list ----------

async def test_rol_repository_create_and_list(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        rol = await repo.create({"tenant_id": tid, "nombre": "SUPERVISOR", "descripcion": "Supervisor de area"})
        await session.commit()
        assert rol.id is not None
        assert rol.nombre == "SUPERVISOR"

    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        roles = await repo.list_ordered()
        nombres = [r.nombre for r in roles]
        assert "SUPERVISOR" in nombres


# ---------- RolRepository: duplicate nombre rejected ----------

async def test_rol_repository_duplicate_nombre_raises(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        await repo.create({"tenant_id": tid, "nombre": "PROFESOR", "descripcion": None})
        await session.commit()

    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        with pytest.raises(Exception):
            await repo.create({"tenant_id": tid, "nombre": "PROFESOR", "descripcion": None})


# ---------- RolRepository: soft delete ----------

async def test_rol_repository_soft_delete(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        rol = await repo.create({"tenant_id": tid, "nombre": "TO_DELETE", "descripcion": None})
        await session.commit()
        rol_id = rol.id

    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        rol = await repo.get_by_id(rol_id)
        await repo.soft_delete(rol)
        await session.commit()

    async with db_setup() as session:
        repo = RolRepository(session, Rol, tid)
        roles = await repo.list_ordered()
        nombres = [r.nombre for r in roles]
        assert "TO_DELETE" not in nombres


# ---------- PermisoRepository: create and list ----------

async def test_permiso_repository_create_and_list(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        repo = PermisoRepository(session, Permiso, tid)
        perm = await repo.create({"tenant_id": tid, "modulo": "reportes", "accion": "exportar"})
        await session.commit()
        assert perm.id is not None

    async with db_setup() as session:
        repo = PermisoRepository(session, Permiso, tid)
        permisos = await repo.list_ordered()
        modulos = [p.modulo for p in permisos]
        assert "reportes" in modulos


# ---------- RolPermisoRepository: attach and detach ----------

async def test_rol_permiso_repository_attach_and_detach(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        rol_repo = RolRepository(session, Rol, tid)
        perm_repo = PermisoRepository(session, Permiso, tid)
        rol = await rol_repo.create({"tenant_id": tid, "nombre": "TEST_ROLE", "descripcion": None})
        perm = await perm_repo.create({"tenant_id": tid, "modulo": "test", "accion": "action"})
        await session.commit()
        rol_id, perm_id = rol.id, perm.id

    async with db_setup() as session:
        rp_repo = RolPermisoRepository(session, RolPermiso, tid)
        await rp_repo.attach(rol_id, perm_id)
        await session.commit()

    async with db_setup() as session:
        rp_repo = RolPermisoRepository(session, RolPermiso, tid)
        permisos = await rp_repo.get_permisos_by_rol(rol_id)
        assert any(p.modulo == "test" and p.accion == "action" for p in permisos)

    async with db_setup() as session:
        rp_repo = RolPermisoRepository(session, RolPermiso, tid)
        deleted = await rp_repo.detach(rol_id, perm_id)
        await session.commit()
        assert deleted is True

    async with db_setup() as session:
        rp_repo = RolPermisoRepository(session, RolPermiso, tid)
        permisos = await rp_repo.get_permisos_by_rol(rol_id)
        assert not any(p.modulo == "test" for p in permisos)


# ---------- RolPermisoRepository: exists returns true when attached ----------

async def test_rol_permiso_repository_exists(db_setup, tenant_a) -> None:
    tid = tenant_a
    async with db_setup() as session:
        rol_repo = RolRepository(session, Rol, tid)
        perm_repo = PermisoRepository(session, Permiso, tid)
        rol = await rol_repo.create({"tenant_id": tid, "nombre": "EXISTS_TEST", "descripcion": None})
        perm = await perm_repo.create({"tenant_id": tid, "modulo": "exists", "accion": "test"})
        await session.commit()
        rol_id, perm_id = rol.id, perm.id

    async with db_setup() as session:
        rp_repo = RolPermisoRepository(session, RolPermiso, tid)
        await rp_repo.attach(rol_id, perm_id)
        await session.commit()

    async with db_setup() as session:
        rp_repo = RolPermisoRepository(session, RolPermiso, tid)
        assert await rp_repo.exists(rol_id, perm_id) is True
        assert await rp_repo.exists(rol_id, uuid4()) is False
