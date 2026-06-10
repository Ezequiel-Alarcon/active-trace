"""Strict TDD for equipos docentes (C-08 SS6).

Tests cover EquipoService: mis_equipos, asignacion_masiva, clonar_equipo,
modificar_vigencia, exportar_equipo_data, generate_csv, and audit events.
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security.hashing import hash_email_for_search
from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.base import Base
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.models.tenant import Tenant, TenantEstado
from app.models.usuario import Usuario
from app.rbac.models import Rol
from app.repositories.usuarios import encrypt_usuario_fields
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    ClonarEquipoRequest,
    VigenciaEquipoRequest,
)
from app.services.equipos import EquipoService

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]

# ── Helpers ──────────────────────────────────────────────────────────

_AAD_EMAIL = "usuario.email"

_today = date.today()
_past = _today - timedelta(days=365)
_future = _today + timedelta(days=365)
_very_past_start = date(2020, 1, 1)
_very_past_end = date(2020, 12, 31)


def _enc_email(tenant_id: UUID, email: str) -> str:
    from app.core.security.crypto import encrypt
    return encrypt(email, tenant_id=tenant_id, aad_suffix=_AAD_EMAIL)


def _hash_email(tenant_id: UUID, email: str) -> str:
    return hash_email_for_search(email, tenant_id)


async def _seed_tenant(session) -> UUID:
    t = Tenant(codigo="EQ-TEST", nombre="Equipo Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t.id


async def _create_rol(session, tid: UUID, nombre: str) -> Rol:
    r = Rol(tenant_id=tid, nombre=nombre, descripcion=f"Rol {nombre}")
    session.add(r)
    await session.flush()
    return r


async def _create_carrera(session, tid: UUID) -> Carrera:
    c = Carrera(tenant_id=tid, codigo="TEST-ING", nombre="Ingenieria Test", estado=CarreraEstado.ACTIVA)
    session.add(c)
    await session.flush()
    return c


async def _create_cohorte(session, tid: UUID, carrera_id: UUID, nombre: str, anio: int) -> Cohorte:
    c = Cohorte(
        tenant_id=tid,
        carrera_id=carrera_id,
        nombre=nombre,
        anio=anio,
        vig_desde=date(anio, 3, 1),
        vig_hasta=date(anio, 12, 31),
        estado=CohorteEstado.ACTIVA,
    )
    session.add(c)
    await session.flush()
    return c


async def _create_materia(session, tid: UUID, codigo: str, nombre: str) -> Materia:
    m = Materia(tenant_id=tid, codigo=codigo, nombre=nombre, estado=MateriaEstado.ACTIVA)
    session.add(m)
    await session.flush()
    return m


async def _create_usuario(session, tid: UUID, nombre: str, apellidos: str, email: str) -> Usuario:
    uid = uuid4()
    enc = encrypt_usuario_fields(
        {"email": email, "dni": "11111111", "cuil": "20-11111111-9", "cbu": "1111111111111111111111"},
        tenant_id=tid,
    )
    u = Usuario(id=uid, tenant_id=tid, nombre=nombre, apellidos=apellidos, **enc)
    session.add(u)
    await session.flush()
    return u


async def _create_asignacion(
    session,
    tid: UUID,
    usuario_id: UUID,
    rol_id: UUID,
    contexto_tipo: ContextoTipo,
    contexto_id: UUID | None,
    desde: date,
    hasta: date | None = None,
) -> Asignacion:
    a = Asignacion(
        tenant_id=tid,
        usuario_id=usuario_id,
        rol_id=rol_id,
        contexto_tipo=contexto_tipo,
        contexto_id=contexto_id,
        desde=desde,
        hasta=hasta,
    )
    session.add(a)
    await session.flush()
    return a


# ── Fixture ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_setup():
    """Bring up an isolated schema with all tables and return a session factory."""
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia, asignacion, usuario  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        # Drop all FK constraints first (Alembic-added FKs not in ORM models)
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


# ── 6.2 mis_equipos ──────────────────────────────────────────────────

async def test_mis_equipos_ve_solo_sus_asignaciones(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u1 = await _create_usuario(session, tid, "Juan", "Perez", "juan@test.com")
        u2 = await _create_usuario(session, tid, "Maria", "Gomez", "maria@test.com")
        await _create_asignacion(session, tid, u1.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past)
        await _create_asignacion(session, tid, u1.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past)
        await _create_asignacion(session, tid, u2.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            result = await svc.mis_equipos(u1.id)
            assert len(result) == 2
            assert all(r.usuario_id == u1.id for r in result)
    finally:
        reset_tenant_context(token)


async def test_mis_equipos_filtra_por_cohorte(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh_a = await _create_cohorte(session, tid, carrera.id, "Cohorte A", 2024)
        coh_b = await _create_cohorte(session, tid, carrera.id, "Cohorte B", 2025)
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.COHORTE, coh_a.id, _past)
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.COHORTE, coh_b.id, _past)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            result = await svc.mis_equipos(u.id, cohorte_id=coh_a.id)
            assert len(result) == 1
            assert result[0].contexto_id == coh_a.id
    finally:
        reset_tenant_context(token)


async def test_mis_equipos_filtra_por_vigencia(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        # Vigente: no tiene hasta (indefinida) y desde en pasado
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        # Vencida: fecha hasta en pasado lejano
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _very_past_start, _very_past_end)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            result_vigentes = await svc.mis_equipos(u.id, estado_vigencia="Vigente")
            assert len(result_vigentes) == 1

            result_vencidas = await svc.mis_equipos(u.id, estado_vigencia="Vencida")
            assert len(result_vencidas) == 1
    finally:
        reset_tenant_context(token)


async def test_mis_equipos_sin_asignaciones_vacio(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        u = await _create_usuario(session, tid, "Sin", "Asign", "sin@test.com")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            result = await svc.mis_equipos(u.id)
            assert result == []
    finally:
        reset_tenant_context(token)


# ── 6.3 asignacion_masiva ────────────────────────────────────────────

async def test_asignacion_masiva_exitosa(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u1 = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        u2 = await _create_usuario(session, tid, "B", "Dos", "b@test.com")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = AsignacionMasivaRequest(
                usuarios_ids=[u1.id, u2.id],
                rol_id=rol_p.id,
                contexto_tipo="Materia",
                contexto_id=materia.id,
                desde=_past,
                hasta=_future,
            )
            resp = await svc.asignacion_masiva(req)
            await session.commit()
            assert len(resp.creadas) == 2
            assert resp.fallidas == []
            assert resp.creadas[0].usuario_id in (u1.id, u2.id)
            assert resp.creadas[0].nombre_rol == "PROFESOR"
    finally:
        reset_tenant_context(token)


async def test_asignacion_masiva_usuario_inexistente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u1 = await _create_usuario(session, tid, "Valido", "User", "valido@test.com")
        await session.commit()
        fake_id = uuid4()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = AsignacionMasivaRequest(
                usuarios_ids=[u1.id, fake_id],
                rol_id=rol_p.id,
                contexto_tipo="Materia",
                contexto_id=materia.id,
                desde=_past,
                hasta=_future,
            )
            resp = await svc.asignacion_masiva(req)
            await session.commit()
            assert len(resp.creadas) == 1
            assert len(resp.fallidas) == 1
            assert resp.fallidas[0].usuario_id == fake_id
            assert "no existe" in resp.fallidas[0].motivo.lower()
    finally:
        reset_tenant_context(token)


async def test_asignacion_masiva_rol_inexistente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u1 = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = AsignacionMasivaRequest(
                usuarios_ids=[u1.id],
                rol_id=uuid4(),
                contexto_tipo="Materia",
                contexto_id=materia.id,
                desde=_past,
                hasta=_future,
            )
            resp = await svc.asignacion_masiva(req)
            assert len(resp.creadas) == 0
            assert len(resp.fallidas) == 1
            assert "rol" in resp.fallidas[0].motivo.lower()
    finally:
        reset_tenant_context(token)


async def test_asignacion_masiva_contexto_inexistente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        u1 = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = AsignacionMasivaRequest(
                usuarios_ids=[u1.id],
                rol_id=rol_p.id,
                contexto_tipo="Materia",
                contexto_id=uuid4(),
                desde=_past,
                hasta=_future,
            )
            resp = await svc.asignacion_masiva(req)
            assert len(resp.creadas) == 0
            assert len(resp.fallidas) == 1
            assert "Materia" in resp.fallidas[0].motivo
    finally:
        reset_tenant_context(token)


async def test_asignacion_masiva_fechas_invalidas(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u1 = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = AsignacionMasivaRequest(
                usuarios_ids=[u1.id],
                rol_id=rol_p.id,
                contexto_tipo="Materia",
                contexto_id=materia.id,
                desde=_future,
                hasta=_past,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.asignacion_masiva(req)
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


# ── 6.4 clonar_equipo ────────────────────────────────────────────────

async def test_clonar_exitoso(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh_origen = await _create_cohorte(session, tid, carrera.id, "Origen", 2024)
        coh_destino = await _create_cohorte(session, tid, carrera.id, "Destino", 2025)
        u1 = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        u2 = await _create_usuario(session, tid, "B", "Dos", "b@test.com")
        u3 = await _create_usuario(session, tid, "C", "Tres", "c@test.com")
        for u in [u1, u2, u3]:
            await _create_asignacion(
                session, tid, u.id, rol_p.id, ContextoTipo.COHORTE, coh_origen.id, _past, None
            )
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=coh_origen.id,
                cohorte_destino_id=coh_destino.id,
                desde=_future,
                hasta=None,
            )
            resp = await svc.clonar_equipo(req)
            await session.commit()
            assert resp.creadas == 3
            assert resp.omitidas == 0
            assert resp.fallidas == []
    finally:
        reset_tenant_context(token)


async def test_clonar_omite_duplicados(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh_origen = await _create_cohorte(session, tid, carrera.id, "Origen", 2024)
        coh_destino = await _create_cohorte(session, tid, carrera.id, "Destino", 2025)
        u1 = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        u2 = await _create_usuario(session, tid, "B", "Dos", "b@test.com")
        await _create_asignacion(session, tid, u1.id, rol_p.id, ContextoTipo.COHORTE, coh_origen.id, _past, None)
        await _create_asignacion(session, tid, u2.id, rol_p.id, ContextoTipo.COHORTE, coh_origen.id, _past, None)
        # Pre-existing in destino (same user+rol+contexto_tipo+Cohorte destino)
        await _create_asignacion(session, tid, u1.id, rol_p.id, ContextoTipo.COHORTE, coh_destino.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=coh_origen.id,
                cohorte_destino_id=coh_destino.id,
                desde=_future,
                hasta=None,
            )
            resp = await svc.clonar_equipo(req)
            await session.commit()
            assert resp.creadas == 1
            assert resp.omitidas == 1
            assert resp.fallidas == []
    finally:
        reset_tenant_context(token)


async def test_clonar_cohorte_origen_inexistente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh_destino = await _create_cohorte(session, tid, carrera.id, "Destino", 2025)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=uuid4(),
                cohorte_destino_id=coh_destino.id,
                desde=_past,
                hasta=_future,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.clonar_equipo(req)
            assert exc.value.status_code == 422
            assert "origen" in exc.value.detail.lower()
    finally:
        reset_tenant_context(token)


async def test_clonar_cohorte_destino_inexistente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh_origen = await _create_cohorte(session, tid, carrera.id, "Origen", 2024)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=coh_origen.id,
                cohorte_destino_id=uuid4(),
                desde=_past,
                hasta=_future,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.clonar_equipo(req)
            assert exc.value.status_code == 422
            assert "destino" in exc.value.detail.lower()
    finally:
        reset_tenant_context(token)


async def test_clonar_fechas_invalidas(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh_origen = await _create_cohorte(session, tid, carrera.id, "Origen", 2024)
        coh_destino = await _create_cohorte(session, tid, carrera.id, "Destino", 2025)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=coh_origen.id,
                cohorte_destino_id=coh_destino.id,
                desde=_future,
                hasta=_past,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.clonar_equipo(req)
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


async def test_clonar_origen_sin_asignaciones(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh_origen = await _create_cohorte(session, tid, carrera.id, "Origen", 2024)
        coh_destino = await _create_cohorte(session, tid, carrera.id, "Destino", 2025)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=coh_origen.id,
                cohorte_destino_id=coh_destino.id,
                desde=_past,
                hasta=_future,
            )
            resp = await svc.clonar_equipo(req)
            assert resp.creadas == 0
            assert resp.omitidas == 0
            assert resp.fallidas == []
    finally:
        reset_tenant_context(token)


# ── 6.5 modificar_vigencia ───────────────────────────────────────────

async def test_modificar_vigencia_actualiza_vigentes(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        for _ in range(5):
            await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            new_desde = _future
            new_hasta = _future + timedelta(days=180)
            req = VigenciaEquipoRequest(
                materia_id=materia.id,
                cohorte_id=coh.id,
                rol_id=None,
                desde=new_desde,
                hasta=new_hasta,
            )
            resp = await svc.modificar_vigencia(req)
            await session.commit()
            assert resp.actualizadas == 5
    finally:
        reset_tenant_context(token)


async def test_modificar_vigencia_no_afecta_vencidas(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        for _ in range(5):
            await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        for _ in range(3):
            await _create_asignacion(
                session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _very_past_start, _very_past_end
            )
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = VigenciaEquipoRequest(
                materia_id=materia.id,
                cohorte_id=coh.id,
                desde=_future,
                hasta=_future + timedelta(days=180),
            )
            resp = await svc.modificar_vigencia(req)
            await session.commit()
            assert resp.actualizadas == 5
    finally:
        reset_tenant_context(token)


async def test_modificar_vigencia_filtra_por_rol(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        rol_t = await _create_rol(session, tid, "TUTOR")
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        for _ in range(3):
            await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        for _ in range(2):
            await _create_asignacion(session, tid, u.id, rol_t.id, ContextoTipo.MATERIA, materia.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = VigenciaEquipoRequest(
                materia_id=materia.id,
                cohorte_id=coh.id,
                rol_id=rol_p.id,
                desde=_future,
                hasta=_future + timedelta(days=180),
            )
            resp = await svc.modificar_vigencia(req)
            await session.commit()
            assert resp.actualizadas == 3
    finally:
        reset_tenant_context(token)


async def test_modificar_vigencia_sin_asignaciones(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = VigenciaEquipoRequest(
                materia_id=materia.id,
                cohorte_id=coh.id,
                desde=_past,
                hasta=_future,
            )
            resp = await svc.modificar_vigencia(req)
            assert resp.actualizadas == 0
    finally:
        reset_tenant_context(token)


async def test_modificar_vigencia_fechas_invalidas(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = VigenciaEquipoRequest(
                materia_id=materia.id,
                cohorte_id=coh.id,
                desde=_future,
                hasta=_past,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.modificar_vigencia(req)
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


async def test_modificar_vigencia_materia_inexistente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = VigenciaEquipoRequest(
                materia_id=uuid4(),
                cohorte_id=coh.id,
                desde=_past,
                hasta=_future,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.modificar_vigencia(req)
            assert exc.value.status_code == 422
            assert "materia" in exc.value.detail.lower()
    finally:
        reset_tenant_context(token)


# ── 6.6 exportar_equipo ──────────────────────────────────────────────

async def test_exportar_csv_con_datos(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte 2024", 2024)
        materia = await _create_materia(session, tid, "M1", "Algoritmos")
        u = await _create_usuario(session, tid, "Juan", "Perez", "juan@test.com")
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            rows = await svc.exportar_equipo_data(materia.id, coh.id)
            csv_content = svc.generate_csv(rows)
            # Check BOM
            assert csv_content.startswith("\ufeff")
            # Check headers
            assert "nombre" in csv_content
            assert "apellidos" in csv_content
            assert "email" in csv_content
            assert "rol" in csv_content
            # Check data
            assert "Juan" in csv_content
            assert "Perez" in csv_content
            assert "juan@test.com" in csv_content
            assert "PROFESOR" in csv_content
            assert "Algoritmos" in csv_content
            assert "Ingenieria Test" in csv_content
    finally:
        reset_tenant_context(token)


async def test_exportar_filtra_por_rol(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        rol_t = await _create_rol(session, tid, "TUTOR")
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        await _create_asignacion(session, tid, u.id, rol_t.id, ContextoTipo.MATERIA, materia.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            rows = await svc.exportar_equipo_data(materia.id, coh.id, rol_id=rol_p.id)
            assert len(rows) == 1
            assert rows[0]["rol"] == "PROFESOR"
    finally:
        reset_tenant_context(token)


async def test_exportar_sin_asignaciones_headers(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            rows = await svc.exportar_equipo_data(materia.id, coh.id)
            assert rows == []
            csv_content = svc.generate_csv(rows)
            csv_lines = csv_content.strip().split("\r\n")
            assert len(csv_lines) == 1  # header only
            assert "nombre" in csv_lines[0]
    finally:
        reset_tenant_context(token)


async def test_exportar_bom_presente(db_setup) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            rows = await svc.exportar_equipo_data(materia.id, coh.id)
            csv_content = svc.generate_csv(rows)
            assert csv_content[0] == "\ufeff"
    finally:
        reset_tenant_context(token)


# ── 6.7 auditoria ────────────────────────────────────────────────────

async def test_audit_asignacion_masiva(db_setup, caplog) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = AsignacionMasivaRequest(
                usuarios_ids=[u.id],
                rol_id=rol_p.id,
                contexto_tipo="Materia",
                contexto_id=materia.id,
                desde=_past,
                hasta=_future,
            )
            with caplog.at_level(logging.WARNING, logger="activia_trace.audit"):
                await svc.asignacion_masiva(req)
                await session.commit()
            audit_records = [r for r in caplog.records if r.name == "activia_trace.audit"]
            actions = [getattr(r, "action", None) for r in audit_records if hasattr(r, "action")]
            assert "ASIGNACION_MODIFICAR" in actions
    finally:
        reset_tenant_context(token)


async def test_audit_clonar_equipo(db_setup, caplog) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh_origen = await _create_cohorte(session, tid, carrera.id, "Origen", 2024)
        coh_destino = await _create_cohorte(session, tid, carrera.id, "Destino", 2025)
        u = await _create_usuario(session, tid, "A", "Uno", "a@test.com")
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.COHORTE, coh_origen.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = ClonarEquipoRequest(
                cohorte_origen_id=coh_origen.id,
                cohorte_destino_id=coh_destino.id,
                desde=_future,
                hasta=None,
            )
            with caplog.at_level(logging.WARNING, logger="activia_trace.audit"):
                await svc.clonar_equipo(req)
                await session.commit()
            audit_records = [r for r in caplog.records if r.name == "activia_trace.audit"]
            actions = [getattr(r, "action", None) for r in audit_records if hasattr(r, "action")]
            assert "ASIGNACION_MODIFICAR" in actions
    finally:
        reset_tenant_context(token)


async def test_audit_modificar_vigencia(db_setup, caplog) -> None:
    async with db_setup() as session:
        tid = await _seed_tenant(session)
        rol_p = await _create_rol(session, tid, "PROFESOR")
        carrera = await _create_carrera(session, tid)
        coh = await _create_cohorte(session, tid, carrera.id, "Cohorte", 2024)
        materia = await _create_materia(session, tid, "M1", "Materia 1")
        u = await _create_usuario(session, tid, "Prof", "Uno", "prof@test.com")
        await _create_asignacion(session, tid, u.id, rol_p.id, ContextoTipo.MATERIA, materia.id, _past, None)
        await session.commit()

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EquipoService(session, tid)
            req = VigenciaEquipoRequest(
                materia_id=materia.id,
                cohorte_id=coh.id,
                desde=_future,
                hasta=_future + timedelta(days=180),
            )
            with caplog.at_level(logging.WARNING, logger="activia_trace.audit"):
                await svc.modificar_vigencia(req)
                await session.commit()
            audit_records = [r for r in caplog.records if r.name == "activia_trace.audit"]
            actions = [getattr(r, "action", None) for r in audit_records if hasattr(r, "action")]
            assert "ASIGNACION_MODIFICAR" in actions
    finally:
        reset_tenant_context(token)
