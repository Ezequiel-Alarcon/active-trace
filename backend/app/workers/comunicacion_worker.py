"""Comunicacion worker — polls DB for Pendiente messages and dispatches them."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.constants import AUDIT_COMUNICACION_ENVIAR
from app.core.audit import audit_emit
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.modules.comunicacion.models.comunicacion import (
    Comunicacion,
    ComunicacionEstado,
)
from app.modules.comunicacion.repositories.comunicacion import ComunicacionRepository
from app.modules.comunicacion.services.dispatch import (
    DispatchResult,
    NoOpDispatchService,
    WebhookDispatchService,
)

logger = logging.getLogger("activia_trace.worker.comunicacion")

MAX_RETRIES = 3


def _build_dispatch_service() -> WebhookDispatchService | NoOpDispatchService:
    settings = get_settings()
    if settings.COMUNICACION_DISPATCH_WEBHOOK_URL:
        return WebhookDispatchService(settings.COMUNICACION_DISPATCH_WEBHOOK_URL)
    return NoOpDispatchService()


async def _process_message(
    session: AsyncSession,
    comm: Comunicacion,
    dispatch_svc: WebhookDispatchService | NoOpDispatchService,
) -> None:
    repo = ComunicacionRepository(session, comm.tenant_id)

    comm.transition_to(ComunicacionEstado.ENVIANDO)
    await session.flush()
    audit_emit(
        AUDIT_COMUNICACION_ENVIAR,
        entity="comunicacion",
        entity_id=comm.id,
        tenant_id=comm.tenant_id,
        detalle={"from": "Pendiente", "to": "Enviando"},
    )

    result: DispatchResult = await dispatch_svc.send(
        comm.destinatario,
        comm.asunto,
        comm.cuerpo,
    )

    if result.success:
        comm.transition_to(ComunicacionEstado.ENVIADO)
        await repo.update_estado(comm, ComunicacionEstado.ENVIADO)
        audit_emit(
            AUDIT_COMUNICACION_ENVIAR,
            entity="comunicacion",
            entity_id=comm.id,
            tenant_id=comm.tenant_id,
            detalle={"from": "Enviando", "to": "Enviado"},
        )
    elif result.retryable and comm.retry_count < MAX_RETRIES:
        await repo.increment_retry(comm)
        backoff = 2**comm.retry_count
        await asyncio.sleep(backoff)
        result = await dispatch_svc.send(comm.destinatario, comm.asunto, comm.cuerpo)
        if result.success:
            await repo.update_estado(comm, ComunicacionEstado.ENVIADO)
            audit_emit(
                AUDIT_COMUNICACION_ENVIAR,
                entity="comunicacion",
                entity_id=comm.id,
                tenant_id=comm.tenant_id,
                detalle={"from": "Enviando", "to": "Enviado", "retry": comm.retry_count},
            )
        else:
            await repo.update_estado(
                comm, ComunicacionEstado.ERROR, error_detail=result.error_detail
            )
            audit_emit(
                AUDIT_COMUNICACION_ENVIAR,
                entity="comunicacion",
                entity_id=comm.id,
                tenant_id=comm.tenant_id,
                detalle={"from": "Enviando", "to": "Error", "error": result.error_detail},
            )
    else:
        await repo.update_estado(
            comm, ComunicacionEstado.ERROR, error_detail=result.error_detail
        )
        audit_emit(
            AUDIT_COMUNICACION_ENVIAR,
            entity="comunicacion",
            entity_id=comm.id,
            tenant_id=comm.tenant_id,
            detalle={"from": "Enviando", "to": "Error", "error": result.error_detail},
        )


async def _recovery_job(session: AsyncSession, timeout_minutes: int = 5) -> None:
    settings = get_settings()
    timeout = timeout_minutes or settings.COMUNICACION_WORKER_LOCK_TIMEOUT

    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout)
    stmt = (
        select(Comunicacion)
        .where(
            Comunicacion.estado == ComunicacionEstado.ENVIANDO,
            Comunicacion.deleted_at.is_(None),
        )
        .where(Comunicacion.updated_at < cutoff)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    stuck = list(result.scalars().all())

    for comm in stuck:
        comm.estado = ComunicacionEstado.PENDIENTE
        comm.error_detail = None
        await session.flush()
        logger.info("Recovered stuck message %s", comm.id)


async def run_poll_loop() -> None:
    dispatch_svc = _build_dispatch_service()
    settings = get_settings()
    poll_interval = settings.COMUNICACION_WORKER_POLL_INTERVAL

    while True:
        try:
            async with async_session_maker() as session:
                await _recovery_job(session, settings.COMUNICACION_WORKER_LOCK_TIMEOUT)

                stmt = (
                    select(Comunicacion)
                    .where(
                        Comunicacion.estado == ComunicacionEstado.PENDIENTE,
                        Comunicacion.deleted_at.is_(None),
                    )
                    .order_by(Comunicacion.created_at)
                    .limit(10)
                    .with_for_update(skip_locked=True)
                )
                result = await session.execute(stmt)
                messages = list(result.scalars().all())

                if not messages:
                    await asyncio.sleep(poll_interval)
                    continue

                for comm in messages:
                    try:
                        await _process_message(session, comm, dispatch_svc)
                    except Exception as exc:
                        logger.exception("Error processing message %s: %s", comm.id, exc)

                await session.commit()
        except Exception as exc:
            logger.exception("Worker poll error: %s", exc)
            await asyncio.sleep(poll_interval)