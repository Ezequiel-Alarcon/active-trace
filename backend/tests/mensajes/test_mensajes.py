from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.tenant import Tenant, TenantEstado
from app.schemas.mensajes import MensajeCreate, MensajeReply
from app.services.mensajes import MensajeService
from tests.mensajes.conftest import _create_tenant, _create_usuario

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


async def _setup_with_users(db_setup) -> tuple:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        remitente = await _create_usuario(session, tenant.id, nombre="Remitente")
        destinatario = await _create_usuario(session, tenant.id, nombre="Destinatario")
        otro = await _create_usuario(session, tenant.id, nombre="Otro")
        await session.commit()
        tid = tenant.id
    return tid, remitente.id, destinatario.id, otro.id


async def _setup_tenant_only(db_setup) -> UUID:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id
    return tid


# ═══════════════════════════════════════════════════════════════════════
# 1. MensajeService.send
# ═══════════════════════════════════════════════════════════════════════

async def test_send_creates_new_thread(db_setup) -> None:
    tid, rem_id, dest_id, _ = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            msg = await svc.send(
                MensajeCreate(
                    asunto="Revisión",
                    cuerpo="Hola, revisa esto",
                    destinatario_id=dest_id,
                ),
                rem_id,
            )
            await session.commit()

            assert msg.id is not None
            assert msg.hilo_id == msg.id
            assert msg.padre_id is None
            assert msg.asunto == "Revisión"
            assert msg.remitente_id == rem_id
            assert msg.destinatario_id == dest_id
    finally:
        reset_tenant_context(token)


async def test_send_with_existing_hilo_id(db_setup) -> None:
    tid, rem_id, dest_id, _ = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        hilo_id = uuid4()
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            msg = await svc.send(
                MensajeCreate(
                    asunto="Continuación",
                    cuerpo="Segundo mensaje",
                    destinatario_id=dest_id,
                    hilo_id=hilo_id,
                ),
                rem_id,
            )
            await session.commit()

            assert msg.hilo_id == hilo_id
            assert msg.id != hilo_id
    finally:
        reset_tenant_context(token)


async def test_send_to_nonexistent_user_raises_404(db_setup) -> None:
    tid = await _setup_tenant_only(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.send(
                    MensajeCreate(
                        asunto="Test",
                        cuerpo="Body",
                        destinatario_id=uuid4(),
                    ),
                    uuid4(),
                )
            assert exc.value.status_code == 404
            assert "Destinatario" in exc.value.detail
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 2. MensajeService.reply
# ═══════════════════════════════════════════════════════════════════════

async def test_reply_extends_thread(db_setup) -> None:
    tid, rem_id, dest_id, _ = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            parent = await svc.send(
                MensajeCreate(
                    asunto="Original", cuerpo="Mensaje original", destinatario_id=dest_id,
                ),
                rem_id,
            )
            await session.commit()
            parent_id = parent.id
            hilo_id = parent.hilo_id

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            reply = await svc.reply(
                parent_id,
                MensajeReply(asunto="RE: Original", cuerpo="Respuesta al mensaje"),
                dest_id,
            )
            await session.commit()

            assert reply.padre_id == parent_id
            assert reply.hilo_id == hilo_id
            assert reply.remitente_id == dest_id
            assert reply.destinatario_id == rem_id
    finally:
        reset_tenant_context(token)


async def test_reply_to_nonexistent_raises_404(db_setup) -> None:
    tid = await _setup_tenant_only(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.reply(
                    uuid4(),
                    MensajeReply(asunto="RE: Test", cuerpo="N/A"),
                    uuid4(),
                )
            assert exc.value.status_code == 404
            assert "original no encontrado" in exc.value.detail
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 3. MensajeService.list_inbox
# ═══════════════════════════════════════════════════════════════════════

async def test_list_inbox_shows_threads_for_recipient(db_setup) -> None:
    tid, rem_id, dest_id, otro_id = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            await svc.send(
                MensajeCreate(asunto="Primero", cuerpo="Mensaje 1", destinatario_id=dest_id),
                rem_id,
            )
            await svc.send(
                MensajeCreate(asunto="Segundo", cuerpo="Mensaje 2", destinatario_id=otro_id),
                rem_id,
            )
            await session.commit()

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            threads = await svc.list_inbox(dest_id)
            assert len(threads) == 1
            assert threads[0].ultimo_asunto == "Primero"

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            threads_rem = await svc.list_inbox(rem_id)
            assert len(threads_rem) == 2
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 4. MensajeService.read_thread
# ═══════════════════════════════════════════════════════════════════════

async def test_read_thread_marks_as_read(db_setup) -> None:
    tid, rem_id, dest_id, _ = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            msg = await svc.send(
                MensajeCreate(asunto="Leer", cuerpo="Para leer", destinatario_id=dest_id),
                rem_id,
            )
            await session.commit()
            hilo_id = msg.hilo_id

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            messages = await svc.read_thread(hilo_id, dest_id)
            await session.commit()

            assert len(messages) == 1
            assert messages[0].leido_at is not None
    finally:
        reset_tenant_context(token)


async def test_read_thread_returns_messages_ordered(db_setup) -> None:
    tid, rem_id, dest_id, _ = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            parent = await svc.send(
                MensajeCreate(asunto="Original", cuerpo="Primero", destinatario_id=dest_id),
                rem_id,
            )
            await session.commit()

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            reply = await svc.reply(
                parent.id, MensajeReply(asunto="RE: Original", cuerpo="Segundo"), dest_id,
            )
            await session.commit()

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            messages = await svc.read_thread(parent.hilo_id, rem_id)
            await session.commit()

            assert len(messages) == 2
            assert messages[0].id == parent.id
            assert messages[1].id == reply.id
    finally:
        reset_tenant_context(token)


async def test_read_thread_not_participant_raises_404(db_setup) -> None:
    tid, rem_id, dest_id, otro_id = await _setup_with_users(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            msg = await svc.send(
                MensajeCreate(asunto="Privado", cuerpo="Solo ellos", destinatario_id=dest_id),
                rem_id,
            )
            await session.commit()
            hilo_id = msg.hilo_id

        async with db_setup() as session:
            svc = MensajeService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.read_thread(hilo_id, otro_id)
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_read_thread_nonexistent_raises_404(db_setup) -> None:
    tid = await _setup_tenant_only(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.read_thread(uuid4(), uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 5. Cross-tenant isolation
# ═══════════════════════════════════════════════════════════════════════

async def test_cross_tenant_message_rejected(db_setup) -> None:
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
            user_a = await _create_usuario(session, tid_a, nombre="UserA")
            await session.commit()
            uid_a = user_a.id
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            user_b = await _create_usuario(session, tid_b, nombre="UserB")
            await session.commit()
            uid_b = user_b.id
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = MensajeService(session, tid_a)
            with pytest.raises(HTTPException) as exc:
                await svc.send(
                    MensajeCreate(
                        asunto="Cross", cuerpo="Should fail", destinatario_id=uid_b,
                    ),
                    uid_a,
                )
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token_a)
