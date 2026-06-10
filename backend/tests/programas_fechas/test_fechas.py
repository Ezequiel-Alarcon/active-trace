"""Strict TDD for FechaAcademica CRUD (C-17 SS5.3).

Tests cover service layer: create, list ordered, filtered, get, update, soft delete,
multi-tenant isolation. Schema validation tests for tipo and immutable fields.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.schemas.programas_fechas import FechaAcademicaCreate, FechaAcademicaUpdate
from app.services.programas_fechas import ProgramaFechasService
from tests.programas_fechas.conftest import (
    _create_tenant,
    _create_tenant_named,
    _create_carrera,
    _create_cohorte,
    _create_materia,
    db_setup,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


async def test_create_fecha_succeeds(db_setup) -> None:
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
            f = await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id,
                cohorte_id=cohorte.id,
                tipo="Parcial",
                numero_instancia=1,
                fecha=date(2025, 6, 15),
                titulo="Primer Parcial",
                descripcion="Unidades 1 a 4",
            ))
            await session.commit()
            assert f.id is not None
            assert f.tenant_id == tid
            assert f.materia_id == materia.id
            assert f.cohorte_id == cohorte.id
            assert f.tipo.value == "Parcial"
            assert f.numero_instancia == 1
            assert f.fecha == date(2025, 6, 15)
            assert f.titulo == "Primer Parcial"
            assert f.descripcion == "Unidades 1 a 4"
            assert f.created_at is not None
            assert f.updated_at is not None
    finally:
        reset_tenant_context(token)


async def test_create_fecha_minimal_fields(db_setup) -> None:
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
            f = await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id,
                cohorte_id=cohorte.id,
                tipo="TP",
                numero_instancia=1,
                fecha=date(2025, 7, 1),
            ))
            await session.commit()
            assert f.titulo is None
            assert f.descripcion is None
    finally:
        reset_tenant_context(token)


async def test_create_fecha_invalid_tipo_422() -> None:
    with pytest.raises(ValidationError):
        FechaAcademicaCreate(
            materia_id=uuid4(),
            cohorte_id=uuid4(),
            tipo="ExamenFinal",
            numero_instancia=1,
            fecha=date(2025, 6, 15),
        )


async def test_create_fecha_extra_fields_422() -> None:
    with pytest.raises(ValidationError):
        FechaAcademicaCreate(
            materia_id=uuid4(),
            cohorte_id=uuid4(),
            tipo="Parcial",
            numero_instancia=1,
            fecha=date(2025, 6, 15),
            extra="no-permitido",
        )


async def test_create_fecha_duplicado_409(db_setup) -> None:
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
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create_fecha(FechaAcademicaCreate(
                    materia_id=materia.id, cohorte_id=cohorte.id,
                    tipo="Parcial", numero_instancia=1, fecha=date(2025, 7, 1),
                ))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


async def test_list_fechas_ordered_by_fecha(db_setup) -> None:
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
            ))
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            fechas = await svc.list_fechas()
            assert len(fechas) == 2
            assert fechas[0].fecha <= fechas[1].fecha
    finally:
        reset_tenant_context(token)


async def test_list_fechas_filtered_by_materia(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        cohorte = await _create_cohorte(session, tenant.id, carrera.id)
        m1 = await _create_materia(session, tenant.id)
        m2 = Materia(tenant_id=tenant.id, codigo="ALG-102", nombre="Algoritmos II", estado=MateriaEstado.ACTIVA)
        session.add(m2)
        await session.flush()
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=m1.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            result = await svc.list_fechas(materia_id=m1.id)
            assert len(result) == 1
            result_empty = await svc.list_fechas(materia_id=m2.id)
            assert len(result_empty) == 0
    finally:
        reset_tenant_context(token)


async def test_list_fechas_filtered_by_cohorte(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        carrera = await _create_carrera(session, tenant.id)
        ch1 = await _create_cohorte(session, tenant.id, carrera.id)
        ch2 = Cohorte(
            tenant_id=tenant.id, carrera_id=carrera.id, nombre="Cohorte 2024",
            anio=2024, vig_desde=date(2024, 3, 1), vig_hasta=date(2024, 12, 31),
            estado=CohorteEstado.ACTIVA,
        )
        session.add(ch2)
        await session.flush()
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=ch1.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            result = await svc.list_fechas(cohorte_id=ch1.id)
            assert len(result) == 1
            result_empty = await svc.list_fechas(cohorte_id=ch2.id)
            assert len(result_empty) == 0
    finally:
        reset_tenant_context(token)


async def test_list_fechas_filtered_by_tipo(db_setup) -> None:
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
            ))
            await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="TP", numero_instancia=1, fecha=date(2025, 8, 10),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            parciales = await svc.list_fechas(tipo="Parcial")
            assert len(parciales) == 1
            assert parciales[0].tipo.value == "Parcial"
            tps = await svc.list_fechas(tipo="TP")
            assert len(tps) == 1
            assert tps[0].tipo.value == "TP"
    finally:
        reset_tenant_context(token)


async def test_get_fecha_by_id_succeeds(db_setup) -> None:
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
            created = await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Coloquio", numero_instancia=1, fecha=date(2025, 9, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            retrieved = await svc.get_fecha(created.id)
            assert retrieved.id == created.id
            assert retrieved.tipo == created.tipo
    finally:
        reset_tenant_context(token)


async def test_get_fecha_not_found_404(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_fecha(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_update_fecha_fields(db_setup) -> None:
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
            f = await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            updated = await svc.update_fecha(f.id, FechaAcademicaUpdate(
                fecha=date(2025, 7, 15),
                titulo="Nuevo titulo",
                descripcion="Nueva descripcion",
            ))
            await session.commit()
            assert updated.fecha == date(2025, 7, 15)
            assert updated.titulo == "Nuevo titulo"
            assert updated.descripcion == "Nueva descripcion"
    finally:
        reset_tenant_context(token)


async def test_update_fecha_attempt_change_tipo_422() -> None:
    with pytest.raises(ValidationError):
        FechaAcademicaUpdate(tipo="Coloquio")


async def test_update_fecha_attempt_change_numero_instancia_422() -> None:
    with pytest.raises(ValidationError):
        FechaAcademicaUpdate(numero_instancia=2)


async def test_delete_fecha_soft_delete(db_setup) -> None:
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
            f = await svc.create_fecha(FechaAcademicaCreate(
                materia_id=materia.id, cohorte_id=cohorte.id,
                tipo="Parcial", numero_instancia=1, fecha=date(2025, 6, 15),
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.delete_fecha(f.id)
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            fechas = await svc.list_fechas()
            ids = {fe.id for fe in fechas}
            assert f.id not in ids
    finally:
        reset_tenant_context(token)


async def test_fecha_multi_tenant_isolation(db_setup) -> None:
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
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid_a)
            fechas = await svc.list_fechas()
            assert len(fechas) == 1
            assert fechas[0].tenant_id == tid_a
    finally:
        reset_tenant_context(token_a)
