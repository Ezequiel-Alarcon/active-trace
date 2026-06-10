"""Strict TDD for ProgramaMateria CRUD (C-17 SS5.2).

Tests cover service layer: create, duplicate, list, get, update, soft delete, multi-tenant isolation.
Schema validation tests cover extra='forbid' enforcement.
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
from app.models.tenant import Tenant, TenantEstado
from app.schemas.programas_fechas import ProgramaCreate, ProgramaUpdate
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


async def test_create_programa_succeeds(db_setup) -> None:
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
            p = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                titulo="Programa Analitico 2025",
                referencia_archivo="/files/prog-001.pdf",
            ))
            await session.commit()
            assert p.id is not None
            assert p.tenant_id == tid
            assert p.materia_id == materia.id
            assert p.carrera_id == carrera.id
            assert p.cohorte_id == cohorte.id
            assert p.titulo == "Programa Analitico 2025"
            assert p.referencia_archivo == "/files/prog-001.pdf"
            assert p.created_at is not None
            assert p.updated_at is not None
    finally:
        reset_tenant_context(token)


async def test_create_programa_sin_referencia_archivo(db_setup) -> None:
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
            p = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                titulo="Programa 2025",
            ))
            await session.commit()
            assert p.referencia_archivo is None
    finally:
        reset_tenant_context(token)


async def test_create_programa_duplicado_409(db_setup) -> None:
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
            await svc.create_programa(ProgramaCreate(
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                titulo="Primero",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create_programa(ProgramaCreate(
                    materia_id=materia.id,
                    carrera_id=carrera.id,
                    cohorte_id=cohorte.id,
                    titulo="Segundo",
                ))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


async def test_create_programa_extra_fields_422() -> None:
    with pytest.raises(ValidationError):
        ProgramaCreate(
            materia_id=uuid4(),
            carrera_id=uuid4(),
            cohorte_id=uuid4(),
            titulo="Test",
            extra="no-permitido",
        )


async def test_list_programas_returns_tenant_scoped(db_setup) -> None:
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
            await svc.create_programa(ProgramaCreate(
                materia_id=m1.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                titulo="Prog 1",
            ))
            await svc.create_programa(ProgramaCreate(
                materia_id=m2.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                titulo="Prog 2",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            programas = await svc.list_programas()
            assert len(programas) == 2
    finally:
        reset_tenant_context(token)


async def test_list_programas_filtered_by_materia(db_setup) -> None:
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
            p1 = await svc.create_programa(ProgramaCreate(
                materia_id=m1.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="P1",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            result = await svc.list_programas(materia_id=m1.id)
            assert len(result) == 1
            assert result[0].id == p1.id
            result_empty = await svc.list_programas(materia_id=m2.id)
            assert len(result_empty) == 0
    finally:
        reset_tenant_context(token)


async def test_list_programas_filtered_by_carrera(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        c1 = await _create_carrera(session, tenant.id)
        c2 = Carrera(tenant_id=tenant.id, codigo="LIC-MAT", nombre="Lic en Matematicas", estado=CarreraEstado.ACTIVA)
        session.add(c2)
        await session.flush()
        cohorte = await _create_cohorte(session, tenant.id, c1.id)
        materia = await _create_materia(session, tenant.id)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            p1 = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id, carrera_id=c1.id, cohorte_id=cohorte.id, titulo="P1",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            result = await svc.list_programas(carrera_id=c1.id)
            assert len(result) == 1
            assert result[0].id == p1.id
            result_empty = await svc.list_programas(carrera_id=c2.id)
            assert len(result_empty) == 0
    finally:
        reset_tenant_context(token)


async def test_list_programas_filtered_by_cohorte(db_setup) -> None:
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
            p1 = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id, carrera_id=carrera.id, cohorte_id=ch1.id, titulo="P1",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            result = await svc.list_programas(cohorte_id=ch1.id)
            assert len(result) == 1
            assert result[0].id == p1.id
            result_empty = await svc.list_programas(cohorte_id=ch2.id)
            assert len(result_empty) == 0
    finally:
        reset_tenant_context(token)


async def test_get_programa_by_id_succeeds(db_setup) -> None:
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
            created = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Test",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            retrieved = await svc.get_programa(created.id)
            assert retrieved.id == created.id
            assert retrieved.titulo == "Test"
    finally:
        reset_tenant_context(token)


async def test_get_programa_not_found_404(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_programa(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_update_programa_titulo(db_setup) -> None:
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
            p = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Old",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            updated = await svc.update_programa(p.id, ProgramaUpdate(titulo="New Title"))
            await session.commit()
            assert updated.titulo == "New Title"
            assert updated.referencia_archivo is None
    finally:
        reset_tenant_context(token)


async def test_update_programa_referencia_archivo(db_setup) -> None:
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
            p = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="Test",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            updated = await svc.update_programa(p.id, ProgramaUpdate(referencia_archivo="/new/path/file.pdf"))
            await session.commit()
            assert updated.referencia_archivo == "/new/path/file.pdf"
            assert updated.titulo == "Test"
    finally:
        reset_tenant_context(token)


async def test_update_programa_extra_fields_422() -> None:
    with pytest.raises(ValidationError):
        ProgramaUpdate(materia_id=uuid4(), titulo="Test")


async def test_delete_programa_soft_delete(db_setup) -> None:
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
            p = await svc.create_programa(ProgramaCreate(
                materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="To Delete",
            ))
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            await svc.delete_programa(p.id)
            await session.commit()

        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid)
            programas = await svc.list_programas()
            ids = {prog.id for prog in programas}
            assert p.id not in ids
    finally:
        reset_tenant_context(token)


async def test_programa_multi_tenant_isolation(db_setup) -> None:
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
            await svc.create_programa(ProgramaCreate(
                materia_id=m_a.id, carrera_id=c_a.id, cohorte_id=ch_a.id, titulo="Prog A",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid_b)
            await svc.create_programa(ProgramaCreate(
                materia_id=m_b.id, carrera_id=c_b.id, cohorte_id=ch_b.id, titulo="Prog B",
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = ProgramaFechasService(session, tid_a)
            programas = await svc.list_programas()
            titulos = {p.titulo for p in programas}
            assert "Prog A" in titulos
            assert "Prog B" not in titulos
    finally:
        reset_tenant_context(token_a)
