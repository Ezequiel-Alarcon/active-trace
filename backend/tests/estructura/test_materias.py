"""Strict TDD for estructura materias (C-06 §5.4).

Tests cover service layer: create, duplicate, list, get, update, soft delete,
multi-tenant isolation.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.materia import MateriaEstado
from app.models.tenant import Tenant, TenantEstado
from app.schemas.estructura import MateriaCreate, MateriaUpdate
from app.services.estructura import EstructuraService
from tests.estructura.conftest import (
    _create_tenant,
    _seed_global_tenant,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


# ── Create ──────────────────────────────────────────────────────────

async def test_create_materia_succeeds(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            m = await svc.create_materia(MateriaCreate(codigo="MAT-101", nombre="Matematica Discreta"))
            await session.commit()
            assert m.id is not None
            assert m.tenant_id == tid
            assert m.codigo == "MAT-101"
            assert m.nombre == "Matematica Discreta"
            assert m.estado == MateriaEstado.ACTIVA
            assert m.created_at is not None
    finally:
        reset_tenant_context(token)


async def test_create_materia_duplicate_codigo_raises_409(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.create_materia(MateriaCreate(codigo="MAT-101", nombre="Primera"))
            await session.commit()
            with pytest.raises(HTTPException) as exc:
                await svc.create_materia(MateriaCreate(codigo="MAT-101", nombre="Segunda"))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


# ── List ────────────────────────────────────────────────────────────

async def test_list_materias_returns_tenant_scoped(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.create_materia(MateriaCreate(codigo="M1", nombre="Materia 1"))
            await svc.create_materia(MateriaCreate(codigo="M2", nombre="Materia 2"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            materias = await svc.list_materias()
            assert len(materias) == 2
            codigos = {m.codigo for m in materias}
            assert "M1" in codigos
            assert "M2" in codigos
    finally:
        reset_tenant_context(token)


async def test_list_materias_filtered_by_estado(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            m = await svc.create_materia(MateriaCreate(codigo="ACT", nombre="Activa"))
            await svc.update_materia(m.id, MateriaUpdate(estado="Inactiva"))
            await svc.create_materia(MateriaCreate(codigo="ACT2", nombre="Activa 2"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            activas = await svc.list_materias(estado="Activa")
            inactivas = await svc.list_materias(estado="Inactiva")
            assert len(activas) == 1
            assert activas[0].codigo == "ACT2"
            assert len(inactivas) == 1
            assert inactivas[0].codigo == "ACT"
    finally:
        reset_tenant_context(token)


# ── Get ─────────────────────────────────────────────────────────────

async def test_get_materia_by_id_succeeds(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            created = await svc.create_materia(MateriaCreate(codigo="MAT-101", nombre="Mat"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            retrieved = await svc.get_materia(created.id)
            assert retrieved.id == created.id
            assert retrieved.codigo == "MAT-101"
    finally:
        reset_tenant_context(token)


async def test_get_materia_not_found_raises_404(db_setup) -> None:
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
                await svc.get_materia(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ── Update ──────────────────────────────────────────────────────────

async def test_update_materia_nombre(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            m = await svc.create_materia(MateriaCreate(codigo="MAT-101", nombre="Old Name"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            updated = await svc.update_materia(m.id, MateriaUpdate(nombre="New Name"))
            await session.commit()
            assert updated.nombre == "New Name"
            assert updated.codigo == "MAT-101"
    finally:
        reset_tenant_context(token)


async def test_update_materia_codigo_duplicate_raises_409(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.create_materia(MateriaCreate(codigo="M1", nombre="One"))
            m2 = await svc.create_materia(MateriaCreate(codigo="M2", nombre="Two"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.update_materia(m2.id, MateriaUpdate(codigo="M1"))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


# ── Soft Delete ─────────────────────────────────────────────────────

async def test_delete_materia_soft_deletes(db_setup) -> None:
    async with db_setup() as session:
        await _seed_global_tenant(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id

    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            m = await svc.create_materia(MateriaCreate(codigo="DEL", nombre="To Delete"))
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            await svc.delete_materia(m.id)
            await session.commit()

        async with db_setup() as session:
            svc = EstructuraService(session, tid)
            materias = await svc.list_materias()
            codigos = {m_.codigo for m_ in materias}
            assert "DEL" not in codigos
    finally:
        reset_tenant_context(token)


# ── Multi-tenant Isolation ──────────────────────────────────────────

async def test_materia_from_tenant_b_not_visible_from_tenant_a(db_setup) -> None:
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
            await svc.create_materia(MateriaCreate(codigo="A-MAT", nombre="Tenant A"))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_b)
            await svc.create_materia(MateriaCreate(codigo="B-MAT", nombre="Tenant B"))
            await session.commit()
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = EstructuraService(session, tid_a)
            materias = await svc.list_materias()
            codigos = {m.codigo for m in materias}
            assert "A-MAT" in codigos
            assert "B-MAT" not in codigos
    finally:
        reset_tenant_context(token_a)
