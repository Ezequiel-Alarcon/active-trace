"""Strict TDD for estructura cohortes (C-06 §5.3).

Tests cover service layer: create, carrera inactiva/invalida, date validation,
duplicate, list, get, update, activate with inactive carrera, soft delete,
multi-tenant isolation.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.tenant import Tenant, TenantEstado
from app.schemas.estructura import CarreraCreate, CarreraUpdate, CohorteCreate, CohorteUpdate
from app.services.estructura import EstructuraService
from tests.estructura.conftest import (
    _create_tenant,
    _seed_global_tenant,
    db_setup,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


# ── Create ──────────────────────────────────────────────────────────

async def test_create_cohorte_succeeds(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ingenieria"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            cohorte = await svc.create_cohorte(CohorteCreate(
                carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()
            assert cohorte.id is not None
            assert cohorte.tenant_id == tid
            assert cohorte.carrera_id == carrera.id
            assert cohorte.nombre == "2025-A"
            assert cohorte.anio == 2025
            assert cohorte.vig_desde == date(2025, 3, 1)
            assert cohorte.vig_hasta is None
            assert cohorte.estado == CohorteEstado.ACTIVA
    finally:
        reset_tenant_context(token)


async def test_create_cohorte_carrera_inactiva_raises_422(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            await svc.update_carrera(carrera.id, CarreraUpdate(estado="Inactiva"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create_cohorte(CohorteCreate(
                    carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


async def test_create_cohorte_carrera_inexistente_raises_422(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create_cohorte(CohorteCreate(
                    carrera_id=uuid4(), nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


async def test_create_cohorte_vig_hasta_before_vig_desde_raises_422(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create_cohorte(CohorteCreate(
                    carrera_id=carrera.id, nombre="2025-B", anio=2025,
                    vig_desde=date(2025, 12, 1), vig_hasta=date(2025, 1, 1)
                ))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


async def test_create_cohorte_duplicate_nombre_raises_409(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            await svc.create_cohorte(CohorteCreate(
                carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()
            with pytest.raises(HTTPException) as exc:
                await svc.create_cohorte(CohorteCreate(
                    carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
                ))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


# ── List ────────────────────────────────────────────────────────────

async def test_list_cohortes_filtered_by_carrera(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c1 = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            c2 = await svc.create_carrera(CarreraCreate(codigo="DER", nombre="Derecho"))
            await svc.create_cohorte(CohorteCreate(
                carrera_id=c1.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await svc.create_cohorte(CohorteCreate(
                carrera_id=c2.id, nombre="2025-B", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            cohortes = await svc.list_cohortes(carrera_id=c1.id)
            assert len(cohortes) == 1
            assert cohortes[0].nombre == "2025-A"
    finally:
        reset_tenant_context(token)


# ── Get ─────────────────────────────────────────────────────────────

async def test_get_cohorte_not_found_raises_404(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_cohorte(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ── Update ──────────────────────────────────────────────────────────

async def test_update_cohorte_nombre(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            cohorte = await svc.create_cohorte(CohorteCreate(
                carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            updated = await svc.update_cohorte(cohorte.id, CohorteUpdate(nombre="2025-B"))
            await session.commit()
            assert updated.nombre == "2025-B"
    finally:
        reset_tenant_context(token)


async def test_activate_cohorte_with_inactive_carrera_raises_422(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            cohorte = await svc.create_cohorte(CohorteCreate(
                carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await svc.update_cohorte(cohorte.id, CohorteUpdate(estado="Inactiva"))
            await svc.update_carrera(carrera.id, CarreraUpdate(estado="Inactiva"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.update_cohorte(cohorte.id, CohorteUpdate(estado="Activa"))
            assert exc.value.status_code == 422
    finally:
        reset_tenant_context(token)


# ── Soft Delete ─────────────────────────────────────────────────────

async def test_delete_cohorte_soft_deletes(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carrera = await svc.create_carrera(CarreraCreate(codigo="ING", nombre="Ing"))
            cohorte = await svc.create_cohorte(CohorteCreate(
                carrera_id=carrera.id, nombre="2025-A", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.delete_cohorte(cohorte.id)
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            cohortes = await svc.list_cohortes()
            assert len(cohortes) == 0
    finally:
        reset_tenant_context(token)


# ── Multi-tenant Isolation ──────────────────────────────────────────

async def test_cohorte_from_tenant_b_not_visible_from_tenant_a(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant_a = await _create_tenant(session)
        await session.flush()
        tenant_b = Tenant(codigo="TENANT-B", nombre="Tenant B", estado=TenantEstado.ACTIVO)
        session.add(tenant_b)
        await session.commit()
        tid_a = tenant_a.id
        tid_b = tenant_b.id

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_a)
            ca = await svc.create_carrera(CarreraCreate(codigo="A-ING", nombre="Ing A"))
            await svc.create_cohorte(CohorteCreate(
                carrera_id=ca.id, nombre="A-COHORT", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_b)
            cb = await svc.create_carrera(CarreraCreate(codigo="B-ING", nombre="Ing B"))
            await svc.create_cohorte(CohorteCreate(
                carrera_id=cb.id, nombre="B-COHORT", anio=2025, vig_desde=date(2025, 3, 1)
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_a)
            cohortes = await svc.list_cohortes()
            nombres = {c.nombre for c in cohortes}
            assert "A-COHORT" in nombres
            assert "B-COHORT" not in nombres
    finally:
        reset_tenant_context(token_a)
