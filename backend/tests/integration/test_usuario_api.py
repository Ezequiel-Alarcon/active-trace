"""Integration tests for Usuario API (C-07 §8).

Tests cover service layer with real DB:
- POST /api/admin/usuarios: creation, 409 duplicate, 422 invalid
- GET /api/admin/usuarios: list, search, pagination
- GET /api/admin/usuarios/{id}: 200 with decrypted PII, 404, cross-tenant 404
- PATCH /api/admin/usuarios/{id}: partial update, email re-encrypt
- DELETE /api/admin/usuarios/{id}: soft delete, GET returns 404 after
"""

from __future__ import annotations

import os
from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate
from app.services.usuarios import UsuarioService

pytestmark = pytest.mark.no_db

# ── Fixture ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_setup():
    from app.models import tenant  # noqa: F401
    from app.models import usuario, asignacion, carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

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

    t = Tenant(codigo="USR-TEST", nombre="Usuario API Test", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


# ── 8.2 POST /api/admin/usuarios ─────────────────────────────────────

@pytest.mark.asyncio
async def test_create_usuario_succeeds(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            created = await svc.create(UsuarioCreate(
                nombre="María", apellidos="García",
                email="maria@garcia.com", dni="40123456",
                cuil="20-40123456-9", cbu="2850590940090418135201",
            ))
            await session.commit()
            assert created.id is not None
            assert created.tenant_id == tid
            assert created.nombre == "María"
            assert created.apellidos == "García"
            assert created.email == "maria@garcia.com"
            assert created.dni == "40123456"
            assert created.cuil == "20-40123456-9"
            assert created.cbu == "2850590940090418135201"
            assert created.created_at is not None
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_usuario_with_optional_fields(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            created = await svc.create(UsuarioCreate(
                nombre="Juan", apellidos="Pérez",
                email="juan@test.com", dni="12345678",
                cuil="20-12345678-9", cbu="1111111111111111111111",
                legajo="L-9999", banco="Banco Test", regional="Norte",
                fecha_nacimiento=date(1990, 5, 15), genero="M",
                observaciones="Test user",
            ))
            await session.commit()
            assert created.legajo == "L-9999"
            assert created.banco == "Banco Test"
            assert created.regional == "Norte"
            assert created.fecha_nacimiento == date(1990, 5, 15)
            assert created.genero == "M"
            assert created.observaciones == "Test user"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_usuario_email_duplicate_409(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            await svc.create(UsuarioCreate(
                nombre="First", apellidos="User",
                email="dup@test.com", dni="11111111",
                cuil="20-11111111-9", cbu="1111111111111111111111",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(UsuarioCreate(
                    nombre="Second", apellidos="User",
                    email="dup@test.com", dni="22222222",
                    cuil="20-22222222-9", cbu="2222222222222222222222",
                ))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_usuario_with_nonexistent_auth_user_422(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(UsuarioCreate(
                    id=uuid4(),
                    nombre="Ghost", apellidos="User",
                    email="ghost@test.com", dni="11111111",
                    cuil="20-11111111-9", cbu="1111111111111111111111",
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


# ── 8.3 GET /api/admin/usuarios ─────────────────────────────────────

@pytest.mark.asyncio
async def test_list_usuarios_tenant_scoped(db_setup) -> None:
    async with db_setup() as session:
        t_a = await _seed_tenant(session)
        await session.flush()
        tid_a = t_a.id

        t_b = Tenant(codigo="USR-B", nombre="Tenant B", estado=TenantEstado.ACTIVO)
        session.add(t_b)
        await session.commit()
        tid_b = t_b.id

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid_a)
            await svc.create(UsuarioCreate(
                nombre="A1", apellidos="One",
                email="a1@test.com", dni="1", cuil="2", cbu="3",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid_b)
            await svc.create(UsuarioCreate(
                nombre="B1", apellidos="One",
                email="b1@test.com", dni="4", cuil="5", cbu="6",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid_a)
            result = await svc.list()
            assert len(result) == 1
            assert result[0].email == "a1@test.com"
    finally:
        reset_tenant_context(token_a)


@pytest.mark.asyncio
async def test_list_usuarios_with_search(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            await svc.create(UsuarioCreate(
                nombre="Carlos", apellidos="Martinez",
                email="carlos@test.com", dni="1", cuil="2", cbu="3",
            ))
            await svc.create(UsuarioCreate(
                nombre="Maria", apellidos="Garcia",
                email="maria@test.com", dni="4", cuil="5", cbu="6",
            ))
            await svc.create(UsuarioCreate(
                nombre="Luis", apellidos="Martini",
                email="luis@test.com", dni="7", cuil="8", cbu="9",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            result = await svc.list(busqueda="mart")
            assert len(result) == 2
            emails = {r.email for r in result}
            assert "carlos@test.com" in emails
            assert "luis@test.com" in emails
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_list_usuarios_pagination(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            for i in range(5):
                await svc.create(UsuarioCreate(
                    nombre=f"User{i}", apellidos=f"Last{i}",
                    email=f"user{i}@test.com", dni=f"{i}", cuil=f"{i}", cbu=f"{i}",
                ))
            await session.commit()

        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            page1 = await svc.list(limit=2, offset=0)
            page2 = await svc.list(limit=2, offset=2)
            page3 = await svc.list(limit=2, offset=4)
            assert len(page1) == 2
            assert len(page2) == 2
            assert len(page3) == 1
    finally:
        reset_tenant_context(token)


# ── 8.4 GET /api/admin/usuarios/{id} ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_usuario_with_decrypted_pii(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            created = await svc.create(UsuarioCreate(
                nombre="Ana", apellidos="Lopez",
                email="ana@lopez.com", dni="20123456",
                cuil="20-20123456-9", cbu="2850590940090418135201",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            retrieved = await svc.get_by_id(created.id)
            assert retrieved.email == "ana@lopez.com"
            assert retrieved.dni == "20123456"
            assert retrieved.cuil == "20-20123456-9"
            assert retrieved.cbu == "2850590940090418135201"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_get_usuario_not_found_404(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_by_id(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_get_usuario_other_tenant_404(db_setup) -> None:
    async with db_setup() as session:
        t_a = await _seed_tenant(session)
        await session.flush()
        tid_a = t_a.id
        t_b = Tenant(codigo="USR-C", nombre="Tenant C", estado=TenantEstado.ACTIVO)
        session.add(t_b)
        await session.commit()
        tid_b = t_b.id

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid_a)
            created = await svc.create(UsuarioCreate(
                nombre="TA", apellidos="User",
                email="ta@test.com", dni="1", cuil="2", cbu="3",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid_b)
            with pytest.raises(HTTPException) as exc:
                await svc.get_by_id(created.id)
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token_b)


# ── 8.5 PATCH /api/admin/usuarios/{id} ───────────────────────────────

@pytest.mark.asyncio
async def test_update_usuario_partial(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            created = await svc.create(UsuarioCreate(
                nombre="Original", apellidos="Name",
                email="orig@test.com", dni="11111111",
                cuil="20-11111111-9", cbu="1111111111111111111111",
            ))
            updated = await svc.update(created.id, UsuarioUpdate(nombre="Updated"))
            await session.commit()
            assert updated.nombre == "Updated"
            assert updated.apellidos == "Name"
            assert updated.email == "orig@test.com"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_update_usuario_email_reencrypts(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            created = await svc.create(UsuarioCreate(
                nombre="Change", apellidos="Email",
                email="old@test.com", dni="11111111",
                cuil="20-11111111-9", cbu="1111111111111111111111",
            ))
            updated = await svc.update(created.id, UsuarioUpdate(email="new@test.com"))
            await session.commit()
            assert updated.email == "new@test.com"

        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            retrieved = await svc.get_by_id(created.id)
            assert retrieved.email == "new@test.com"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_update_usuario_email_duplicate_409(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            await svc.create(UsuarioCreate(
                nombre="Existing", apellidos="User",
                email="exist@test.com", dni="11111111",
                cuil="20-11111111-9", cbu="1111111111111111111111",
            ))
            u2 = await svc.create(UsuarioCreate(
                nombre="Other", apellidos="User",
                email="other@test.com", dni="22222222",
                cuil="20-22222222-9", cbu="2222222222222222222222",
            ))
            await session.commit()

            with pytest.raises(HTTPException) as exc:
                await svc.update(u2.id, UsuarioUpdate(email="exist@test.com"))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


# ── 8.6 DELETE /api/admin/usuarios/{id} ──────────────────────────────

@pytest.mark.asyncio
async def test_delete_usuario_soft_delete(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            created = await svc.create(UsuarioCreate(
                nombre="Delete", apellidos="Me",
                email="delete@test.com", dni="11111111",
                cuil="20-11111111-9", cbu="1111111111111111111111",
            ))
            await svc.delete(created.id)
            await session.commit()

        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_by_id(created.id)
            assert exc.value.status_code == 404

            result = await svc.list()
            assert not any(r.id == created.id for r in result)
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_delete_usuario_not_found_404(db_setup) -> None:
    async with db_setup() as session:
        t = await _seed_tenant(session)
        await session.commit()
        tid = t.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = UsuarioService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.delete(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)
