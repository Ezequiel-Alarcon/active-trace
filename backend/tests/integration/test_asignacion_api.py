"""Integration tests for Asignacion API (C-07 §8).

Tests cover service layer with real DB:
- POST /api/asignaciones: create with each contexto_tipo, desde≤hasta validation, 422 missing context
- GET /api/asignaciones: list, filter by usuario/contexto/estado_vigencia
- PATCH /api/asignaciones: update hasta, update context
- DELETE /api/asignaciones/{id}: soft delete 204
- Multi-tenant isolation: tenant A can't see tenant B's assignments
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.base import Base
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.models.tenant import Tenant, TenantEstado
from app.repositories.usuarios import encrypt_usuario_fields
from app.schemas.usuarios import AsignacionCreate, AsignacionUpdate
from app.services.usuarios import AsignacionService

pytestmark = pytest.mark.no_db

_today = date.today()
_yesterday = _today - timedelta(days=1)
_tomorrow = _today + timedelta(days=1)
_future = _today + timedelta(days=365)
_past = _today - timedelta(days=365)

# ── Fixture ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_setup():
    from app.models import tenant  # noqa: F401
    from app.models import usuario, asignacion, carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        fk_result = await conn.execute(sqlalchemy.text(
            "SELECT conrelid::regclass::text AS tbl, conname "
            "FROM pg_constraint WHERE contype = 'f'"
        ))
        for tbl, conname in fk_result:
            await conn.execute(sqlalchemy.text(
                f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {conname} CASCADE"
            ))
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _seed_tenant_and_context(session) -> tuple:
    from app.rbac.models import Rol
    from app.models.usuario import Usuario

    t = Tenant(codigo="ASG-TEST", nombre="Asignacion Test", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    tid = t.id

    # Create role
    rol = Rol(tenant_id=tid, nombre="PROFESOR", descripcion="Profesor")
    session.add(rol)
    await session.flush()

    # Create usuario
    enc = encrypt_usuario_fields(
        {"email": "prof@test.com", "dni": "40123456", "cuil": "20-40123456-9", "cbu": "2850590940090418135201"},
        tenant_id=tid,
    )
    usuario = Usuario(id=uuid4(), tenant_id=tid, nombre="Prof", apellidos="Uno", **enc)
    session.add(usuario)
    await session.flush()

    # Create carrera
    carrera = Carrera(tenant_id=tid, codigo="ING-INF", nombre="Ingenieria Informatica", estado=CarreraEstado.ACTIVA)
    session.add(carrera)
    await session.flush()

    # Create cohorte
    cohorte = Cohorte(
        tenant_id=tid, carrera_id=carrera.id,
        nombre="Cohorte 2025", anio=2025,
        vig_desde=date(2025, 3, 1), vig_hasta=date(2025, 12, 31),
        estado=CohorteEstado.ACTIVA,
    )
    session.add(cohorte)
    await session.flush()

    # Create materia
    materia = Materia(tenant_id=tid, codigo="ALG-101", nombre="Algoritmos I", estado=MateriaEstado.ACTIVA)
    session.add(materia)
    await session.flush()

    # Create second user (as responsible)
    enc2 = encrypt_usuario_fields(
        {"email": "resp@test.com", "dni": "22222222", "cuil": "20-22222222-9", "cbu": "2222222222222222222222"},
        tenant_id=tid,
    )
    responsable = Usuario(id=uuid4(), tenant_id=tid, nombre="Coord", apellidos="Dos", **enc2)
    session.add(responsable)
    await session.flush()

    return tid, rol.id, usuario.id, carrera.id, cohorte.id, materia.id, responsable.id


# ── 8.8 POST /api/asignaciones ────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_asignacion_global(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()
            assert created.id is not None
            assert created.contexto_tipo == "Global"
            assert created.contexto_id is None
            assert created.estado_vigencia == "Vigente"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_carrera(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, carrera_id, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Carrera", contexto_id=carrera_id,
                desde=_past, hasta=None,
            ))
            await session.commit()
            assert created.contexto_tipo == "Carrera"
            assert created.contexto_id == carrera_id
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_cohorte(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, cohorte_id, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Cohorte", contexto_id=cohorte_id,
                desde=_past, hasta=None,
            ))
            await session.commit()
            assert created.contexto_tipo == "Cohorte"
            assert created.contexto_id == cohorte_id
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_materia(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, materia_id, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Materia", contexto_id=materia_id,
                desde=_past, hasta=None,
            ))
            await session.commit()
            assert created.contexto_tipo == "Materia"
            assert created.contexto_id == materia_id
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_con_responsable(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, materia_id, responsable_id = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Materia", contexto_id=materia_id,
                responsable_id=responsable_id,
                desde=_past, hasta=None,
            ))
            await session.commit()
            assert created.responsable_id == responsable_id
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_desde_gt_hasta_422(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(AsignacionCreate(
                    usuario_id=usuario_id, rol_id=rol_id,
                    contexto_tipo="Global", contexto_id=None,
                    desde=_future, hasta=_past,
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_contexto_inexistente_422(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(AsignacionCreate(
                    usuario_id=usuario_id, rol_id=rol_id,
                    contexto_tipo="Carrera", contexto_id=uuid4(),
                    desde=_past, hasta=None,
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_usuario_inexistente_422(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, _, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(AsignacionCreate(
                    usuario_id=uuid4(), rol_id=rol_id,
                    contexto_tipo="Global", contexto_id=None,
                    desde=_past, hasta=None,
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_create_asignacion_rol_inexistente_422(db_setup) -> None:
    async with db_setup() as session:
        tid, _, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(AsignacionCreate(
                    usuario_id=usuario_id, rol_id=uuid4(),
                    contexto_tipo="Global", contexto_id=None,
                    desde=_past, hasta=None,
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


# ── 8.9 GET /api/asignaciones ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_asignaciones_all(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            result = await svc.list()
            assert len(result) == 2
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_list_asignaciones_filter_by_usuario(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, responsable_id = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            result = await svc.list(usuario_id=usuario_id)
            assert len(result) == 1
            assert result[0].usuario_id == usuario_id
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_list_asignaciones_filter_by_contexto(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, carrera_id, _, materia_id, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Carrera", contexto_id=carrera_id,
                desde=_past, hasta=None,
            ))
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Materia", contexto_id=materia_id,
                desde=_past, hasta=None,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            result = await svc.list(contexto_tipo="Carrera", contexto_id=carrera_id)
            assert len(result) == 1
            assert result[0].contexto_tipo == "Carrera"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_list_asignaciones_filter_by_estado_vigencia(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            # Vigente: sin hasta + desde en pasado
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            # Vencida: hasta en pasado
            await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=date(2020, 1, 1), hasta=date(2020, 12, 31),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            vigentes = await svc.list(estado_vigencia="Vigente")
            vencidas = await svc.list(estado_vigencia="Vencida")
            assert len(vigentes) == 1
            assert len(vencidas) == 1
    finally:
        reset_tenant_context(token)


# ── 8.10 PATCH /api/asignaciones/{id} ─────────────────────────────────

@pytest.mark.asyncio
async def test_update_asignacion_hasta(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            updated = await svc.update(created.id, AsignacionUpdate(hasta=_yesterday))
            await session.commit()
            assert updated.hasta == _yesterday
            assert updated.estado_vigencia == "Vencida"
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_update_asignacion_contexto(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, materia_id, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            updated = await svc.update(created.id, AsignacionUpdate(
                contexto_tipo="Materia", contexto_id=materia_id,
            ))
            await session.commit()
            assert updated.contexto_tipo == "Materia"
            assert updated.contexto_id == materia_id
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_update_asignacion_desde_gt_hasta_422(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()

            with pytest.raises(HTTPException) as exc:
                await svc.update(created.id, AsignacionUpdate(hasta=date(2020, 1, 1)))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


# ── 8.11 DELETE /api/asignaciones/{id} ────────────────────────────────

@pytest.mark.asyncio
async def test_delete_asignacion_soft(db_setup) -> None:
    async with db_setup() as session:
        tid, rol_id, usuario_id, _, _, _, _ = await _seed_tenant_and_context(session)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_id, rol_id=rol_id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            await svc.delete(created.id)
            await session.commit()

        async with db_setup() as session:
            svc = AsignacionService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_by_id(created.id)
            assert exc.value.status_code == 404

            result = await svc.list()
            assert not any(r.id == created.id for r in result)
    finally:
        reset_tenant_context(token)


# ── 8.12 Multi-tenant Isolation ───────────────────────────────────────

@pytest.mark.asyncio
async def test_asignacion_multitenant_isolation(db_setup) -> None:
    async with db_setup() as session:
        from app.rbac.models import Rol
        from app.models.usuario import Usuario

        t_a = Tenant(codigo="ASG-A", nombre="Asignacion Tenant A", estado=TenantEstado.ACTIVO)
        t_b = Tenant(codigo="ASG-B", nombre="Asignacion Tenant B", estado=TenantEstado.ACTIVO)
        session.add_all([t_a, t_b])
        await session.flush()
        tid_a = t_a.id
        tid_b = t_b.id

        # Same setup for both tenants
        rol_a = Rol(tenant_id=tid_a, nombre="PROFESOR", descripcion="Prof")
        rol_b = Rol(tenant_id=tid_b, nombre="PROFESOR", descripcion="Prof")
        session.add_all([rol_a, rol_b])
        await session.flush()

        enc_a = encrypt_usuario_fields(
            {"email": "a@test.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=tid_a
        )
        usuario_a = Usuario(id=uuid4(), tenant_id=tid_a, nombre="A", apellidos="User", **enc_a)
        session.add(usuario_a)
        await session.flush()

        enc_b = encrypt_usuario_fields(
            {"email": "b@test.com", "dni": "4", "cuil": "5", "cbu": "6"}, tenant_id=tid_b
        )
        usuario_b = Usuario(id=uuid4(), tenant_id=tid_b, nombre="B", apellidos="User", **enc_b)
        session.add(usuario_b)
        await session.commit()

    # Create assignments in tenant A
    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid_a)
            await svc.create(AsignacionCreate(
                usuario_id=usuario_a.id, rol_id=rol_a.id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    # Create assignments in tenant B
    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid_b)
            await svc.create(AsignacionCreate(
                usuario_id=usuario_b.id, rol_id=rol_b.id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    # Tenant A sees only its own
    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid_a)
            result = await svc.list()
            assert len(result) == 1
            assert result[0].usuario_id == usuario_a.id
            assert result[0].tenant_id == tid_a
    finally:
        reset_tenant_context(token_a)

    # Tenant B sees only its own
    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid_b)
            result = await svc.list()
            assert len(result) == 1
            assert result[0].usuario_id == usuario_b.id
            assert result[0].tenant_id == tid_b
    finally:
        reset_tenant_context(token_b)


@pytest.mark.asyncio
async def test_asignacion_cross_tenant_get_404(db_setup) -> None:
    async with db_setup() as session:
        from app.rbac.models import Rol
        from app.models.usuario import Usuario

        t_a = Tenant(codigo="ASG-C", nombre="Tenant C", estado=TenantEstado.ACTIVO)
        t_b = Tenant(codigo="ASG-D", nombre="Tenant D", estado=TenantEstado.ACTIVO)
        session.add_all([t_a, t_b])
        await session.flush()
        tid_a = t_a.id
        tid_b = t_b.id

        rol_a = Rol(tenant_id=tid_a, nombre="PROFESOR", descripcion="Prof")
        session.add(rol_a)
        await session.flush()

        enc_a = encrypt_usuario_fields(
            {"email": "c@test.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=tid_a
        )
        usuario_a = Usuario(id=uuid4(), tenant_id=tid_a, nombre="C", apellidos="User", **enc_a)
        session.add(usuario_a)
        await session.commit()

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid_a)
            created = await svc.create(AsignacionCreate(
                usuario_id=usuario_a.id, rol_id=rol_a.id,
                contexto_tipo="Global", contexto_id=None,
                desde=_past, hasta=None,
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    # Tenant B tries to access tenant A's assignment
    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = AsignacionService(session, tid_b)
            with pytest.raises(HTTPException) as exc:
                await svc.get_by_id(created.id)
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token_b)
