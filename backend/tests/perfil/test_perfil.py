from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.tenant import Tenant, TenantEstado
from app.schemas.perfil import PerfilUpdate
from app.services.perfil import PerfilService
from tests.perfil.conftest import _create_auth_user_and_session, _create_tenant, _create_usuario

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


async def _setup(db_setup) -> tuple:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id
    return tid


async def _setup_with_user(db_setup, tid) -> tuple[UUID, UUID, UUID]:
    async with db_setup() as session:
        usuario = await _create_usuario(session, tid)
        user_id2, session_id2 = await _create_auth_user_and_session(session, tid, usuario.id)
        await session.commit()
    return usuario.id, tid, session_id2


# ═══════════════════════════════════════════════════════════════════════
# 1. PerfilService.get_profile
# ═══════════════════════════════════════════════════════════════════════

async def test_get_profile_returns_decrypted_fields(db_setup) -> None:
    tid = await _setup(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            usuario = await _create_usuario(session, tid)
            await session.commit()
            uid = usuario.id

        async with db_setup() as session:
            svc = PerfilService(session, tid)
            profile = await svc.get_profile(uid)

            assert profile.id == uid
            assert profile.tenant_id == tid
            assert profile.nombre == "Juan"
            assert profile.apellidos == "Pérez"
            assert profile.email.startswith("juan.perez.")
            assert profile.dni == "12345678"
            assert profile.cuil == "20-12345678-9"
            assert profile.cbu == "0000003100012345678901"
            assert profile.banco == "Banco Test"
            assert profile.regional == "CABA"
            assert profile.legajo == "LEG-001"
    finally:
        reset_tenant_context(token)


async def test_get_profile_not_found_raises_404(db_setup) -> None:
    tid = await _setup(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = PerfilService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get_profile(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 2. PerfilService.update_profile
# ═══════════════════════════════════════════════════════════════════════

async def test_update_profile_partial_update(db_setup) -> None:
    tid = await _setup(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            usuario = await _create_usuario(session, tid)
            await session.commit()
            uid = usuario.id

        async with db_setup() as session:
            svc = PerfilService(session, tid)
            updated = await svc.update_profile(
                uid, PerfilUpdate(nombre="Nuevo Nombre", banco="Nuevo Banco")
            )
            await session.commit()

            assert updated.nombre == "Nuevo Nombre"
            assert updated.banco == "Nuevo Banco"
            assert updated.apellidos == "Pérez"
    finally:
        reset_tenant_context(token)


async def test_update_profile_empty_update_succeeds(db_setup) -> None:
    tid = await _setup(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            usuario = await _create_usuario(session, tid)
            await session.commit()
            uid = usuario.id

        async with db_setup() as session:
            svc = PerfilService(session, tid)
            updated = await svc.update_profile(uid, PerfilUpdate())
            await session.commit()

            assert updated.nombre == "Juan"
            assert updated.apellidos == "Pérez"
    finally:
        reset_tenant_context(token)


async def test_update_profile_encryption_round_trip(db_setup) -> None:
    tid = await _setup(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            usuario = await _create_usuario(session, tid)
            await session.commit()
            uid = usuario.id

        async with db_setup() as session:
            svc = PerfilService(session, tid)
            updated = await svc.update_profile(
                uid, PerfilUpdate(email="nuevo.email@test.com", cbu="9999999999999999999999")
            )
            await session.commit()

            assert updated.email == "nuevo.email@test.com"
            assert updated.cbu == "9999999999999999999999"

        async with db_setup() as session:
            svc = PerfilService(session, tid)
            profile = await svc.get_profile(uid)
            assert profile.email == "nuevo.email@test.com"
            assert profile.cbu == "9999999999999999999999"
    finally:
        reset_tenant_context(token)


async def test_update_profile_not_found_raises_404(db_setup) -> None:
    tid = await _setup(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = PerfilService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.update_profile(uuid4(), PerfilUpdate(nombre="X"))
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 3. Multi-tenant isolation
# ═══════════════════════════════════════════════════════════════════════

async def test_cross_tenant_isolation(db_setup) -> None:
    async with db_setup() as session:
        t_a = await _create_tenant(session)
        t_b = Tenant(codigo="T-B", nombre="Tenant B", estado=TenantEstado.ACTIVO)
        session.add(t_b)
        await session.flush()
        tid_a, tid_b = t_a.id, t_b.id
        await session.commit()

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            usuario_a = await _create_usuario(session, tid_a)
            await session.commit()
            uid_a = usuario_a.id
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = PerfilService(session, tid_b)
            with pytest.raises(HTTPException) as exc:
                await svc.get_profile(uid_a)
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token_b)
