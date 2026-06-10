"""Strict TDD for estructura carreras (C-06 §5.2).

Tests cover service layer: create, duplicate, list, get, update, soft delete, multi-tenant isolation.
All write-heavy blocks commit before a new session reads them.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.carrera import Carrera, CarreraEstado
from app.models.tenant import Tenant, TenantEstado
from app.schemas.estructura import CarreraCreate, CarreraUpdate
from app.services.estructura import EstructuraService
from tests.estructura.conftest import (
    _create_tenant,
    _seed_global_tenant,
    db_setup,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


# ── Create ──────────────────────────────────────────────────────────

async def test_create_carrera_succeeds(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c = await svc.create_carrera(CarreraCreate(codigo="ING-INF", nombre="Ingenieria en Informatica"))
            await session.commit()
            assert c.id is not None
            assert c.tenant_id == tid
            assert c.codigo == "ING-INF"
            assert c.nombre == "Ingenieria en Informatica"
            assert c.estado == CarreraEstado.ACTIVA
            assert c.created_at is not None
    finally:
        reset_tenant_context(token)


async def test_create_carrera_duplicate_codigo_raises_409(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.create_carrera(CarreraCreate(codigo="ING-INF", nombre="Primera"))
            await session.commit()
            with pytest.raises(HTTPException) as exc:
                await svc.create_carrera(CarreraCreate(codigo="ING-INF", nombre="Segunda"))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


# ── List ────────────────────────────────────────────────────────────

async def test_list_carreras_returns_tenant_scoped(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.create_carrera(CarreraCreate(codigo="C1", nombre="Carrera 1"))
            await svc.create_carrera(CarreraCreate(codigo="C2", nombre="Carrera 2"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carreras = await svc.list_carreras()
            assert len(carreras) == 2
            codigos = {c.codigo for c in carreras}
            assert "C1" in codigos
            assert "C2" in codigos
    finally:
        reset_tenant_context(token)


async def test_list_carreras_filtered_by_estado(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c = await svc.create_carrera(CarreraCreate(codigo="ACT", nombre="Activa"))
            await svc.update_carrera(c.id, CarreraUpdate(estado="Inactiva"))
            await svc.create_carrera(CarreraCreate(codigo="ACT2", nombre="Activa 2"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            activas = await svc.list_carreras(estado="Activa")
            inactivas = await svc.list_carreras(estado="Inactiva")
            assert len(activas) == 1
            assert activas[0].codigo == "ACT2"
            assert len(inactivas) == 1
            assert inactivas[0].codigo == "ACT"
    finally:
        reset_tenant_context(token)


# ── Get ─────────────────────────────────────────────────────────────

async def test_get_carrera_by_id_succeeds(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            created = await svc.create_carrera(CarreraCreate(codigo="ING-INF", nombre="Ing"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            retrieved = await svc.get_carrera(created.id)
            assert retrieved.id == created.id
            assert retrieved.codigo == "ING-INF"
    finally:
        reset_tenant_context(token)


async def test_get_carrera_not_found_raises_404(db_setup) -> None:
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
                await svc.get_carrera(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ── Update ──────────────────────────────────────────────────────────

async def test_update_carrera_nombre(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c = await svc.create_carrera(CarreraCreate(codigo="ING-INF", nombre="Old Name"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            updated = await svc.update_carrera(c.id, CarreraUpdate(nombre="New Name"))
            await session.commit()
            assert updated.nombre == "New Name"
            assert updated.codigo == "ING-INF"
    finally:
        reset_tenant_context(token)


async def test_update_carrera_codigo_duplicate_raises_409(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c1 = await svc.create_carrera(CarreraCreate(codigo="C1", nombre="One"))
            c2 = await svc.create_carrera(CarreraCreate(codigo="C2", nombre="Two"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.update_carrera(c2.id, CarreraUpdate(codigo="C1"))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


async def test_update_carrera_estado_to_inactiva(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c = await svc.create_carrera(CarreraCreate(codigo="ING-INF", nombre="Ing"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            updated = await svc.update_carrera(c.id, CarreraUpdate(estado="Inactiva"))
            await session.commit()
            assert updated.estado == CarreraEstado.INACTIVA
    finally:
        reset_tenant_context(token)


# ── Soft Delete ─────────────────────────────────────────────────────

async def test_delete_carrera_soft_deletes(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            c = await svc.create_carrera(CarreraCreate(codigo="DEL", nombre="To Delete"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.delete_carrera(c.id)
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            carreras = await svc.list_carreras()
            codigos = {c_.codigo for c_ in carreras}
            assert "DEL" not in codigos
    finally:
        reset_tenant_context(token)


# ── Multi-tenant Isolation ──────────────────────────────────────────

async def test_carrera_from_tenant_b_not_visible_from_tenant_a(db_setup) -> None:
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
            await svc.create_carrera(CarreraCreate(codigo="A-ONLY", nombre="Tenant A"))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_b)
            await svc.create_carrera(CarreraCreate(codigo="B-ONLY", nombre="Tenant B"))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_a)
            carreras = await svc.list_carreras()
            codigos = {c.codigo for c in carreras}
            assert "A-ONLY" in codigos
            assert "B-ONLY" not in codigos
    finally:
        reset_tenant_context(token_a)
