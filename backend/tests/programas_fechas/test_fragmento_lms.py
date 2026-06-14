"""Strict TDD for Fragmento LMS (C-17 SS5.4).

Tests cover HTML generation, grouping by tipo, ordering, soft-deleted exclusion,
empty state, and multi-tenant isolation.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.schemas.programas_fechas import FechaAcademicaCreate
from app.services.programas_fechas import ProgramaFechasService
from tests.programas_fechas.conftest import (
    _create_tenant,
    _create_tenant_named,
    _create_carrera,
    _create_cohorte,
    _create_materia,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


async def test_fragmento_lms_con_fechas(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        cohorte = await _create_cohorte(session, tenant.id, carrera.id)
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
                titulo="Primer Parcial", descripcion="Unidades 1 a 4",
            ))
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=2, fecha=date(2025, 7, 20),
            ))
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="TP", numero_instancia=1, fecha=date(2025, 8, 10),
                titulo="Trabajo Practico 1",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            html = await svc.generar_fragmento_lms(materia.id, cohorte.id)
            assert "Primer Parcial" in html
            assert "Trabajo Practico 1" in html
            assert "Unidades 1 a 4" in html
            assert "2025-06-15" in html
            assert "2025-07-20" in html
            assert "2025-08-10" in html
            assert "Parcial" in html
            assert "TP" in html
            assert '<div class="fechas-academicas">' in html
    finally:
        reset_tenant_context(token)


async def test_fragmento_lms_sin_fechas(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        cohorte = await _create_cohorte(session, tenant.id, carrera.id)
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            html = await svc.generar_fragmento_lms(materia.id, cohorte.id)
            assert "No hay fechas registradas" in html
    finally:
        reset_tenant_context(token)


async def test_fragmento_lms_excluye_soft_deleted(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        cohorte = await _create_cohorte(session, tenant.id, carrera.id)
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
                titulo="Visible",
            ))
            f2 = await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=2, fecha=date(2025, 7, 20),
                titulo="SoftDeleted",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.delete_fecha(f2.id)
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            html = await svc.generar_fragmento_lms(materia.id, cohorte.id)
            assert "Visible" in html
            assert "SoftDeleted" not in html
    finally:
        reset_tenant_context(token)


async def test_fragmento_lms_agrupado_por_tipo(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        cohorte = await _create_cohorte(session, tenant.id, carrera.id)
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Coloquio", numero_instancia=1, fecha=date(2025, 10, 1),
            ))
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            html = await svc.generar_fragmento_lms(materia.id, cohorte.id)
            assert "<h3>Parcial</h3>" in html
            assert "<h3>Coloquio</h3>" in html
            assert html.count("<h3>") == 2
    finally:
        reset_tenant_context(token)


async def test_fragmento_lms_ordenado_por_numero_instancia(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        cohorte = await _create_cohorte(session, tenant.id, carrera.id)
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=2, fecha=date(2025, 7, 20),
                titulo="Parcial 2",
            ))
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
                titulo="Parcial 1",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            html = await svc.generar_fragmento_lms(materia.id, cohorte.id)
            pos1 = html.find("Parcial 1")
            pos2 = html.find("Parcial 2")
            assert pos1 < pos2, "Parcial 1 should appear before Parcial 2"
    finally:
        reset_tenant_context(token)


async def test_fragmento_lms_multi_tenant_isolation(db_setup) -> None:
    async with db_setup() as session:
        t_a = await _create_tenant_named(session, "TENANT-A", "Tenant A")
        t_b = await _create_tenant_named(session, "TENANT-B", "Tenant B")
        c_a = await _create_carrera(session, t_a.id)
        c_b = Carrera(tenant_id=t_b.id, codigo="ING-INF", nombre="Ingenieria Informatica", estado=CarreraEstado.ACTIVA)
        session.add(c_b)
        await session.flush()
        ch_a = await _create_cohorte(session, t_a.id, c_a.id)
        ch_b = Cohorte(
            tenant_id=t_b.id, carrera_id=c_b.id, nombre="Cohorte 2025",
            anio=2025, vig_desde=date(2025, 3, 1), vig_hasta=date(2025, 12, 31),
            estado=CohorteEstado.ACTIVA,
        )
        session.add(ch_b)
        await session.flush()
        m_a = await _create_materia(session, t_a.id)
        m_b = Materia(tenant_id=t_b.id, codigo="ALG-101", nombre="Algoritmos I", estado=MateriaEstado.ACTIVA)
        session.add(m_b)
        await session.flush()
        await session.commit()
        tid_a, tid_b = t_a.id, t_b.id

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid_a)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=m_a.id, cohorte_id=ch_a.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
                titulo="Fecha Tenant A",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid_b)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=m_b.id, cohorte_id=ch_b.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
                titulo="Fecha Tenant B",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid_a)
            html = await svc.generar_fragmento_lms(m_a.id, ch_a.id)
            assert "Fecha Tenant A" in html
            assert "Fecha Tenant B" not in html
    finally:
        reset_tenant_context(token_a)
