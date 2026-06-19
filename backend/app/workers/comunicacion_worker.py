"""Comunicacion worker — polls DB for Pendiente messages and dispatches them."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.constants import AUDIT_COMUNICACION_ENVIAR
from app.core.audit import audit_emit
from app.core.config import get_settings
from app.core.tenancy import TenantContext, set_tenant_context
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
from app.core.database import create_session_factory

# Build the session factory once at module level using the default engine.
async_session_maker = create_session_factory()

logger = logging.getLogger("activia_trace.worker.comunicacion")

MAX_RETRIES = 3


def _build_dispatch_service() -> WebhookDispatchService | NoOpDispatchService:
    settings = get_settings()
    if settings.COMUNICACION_DISPATCH_WEBHOOK_URL:
        return WebhookDispatchService(settings.COMUNICACION_DISPATCH_WEBHOOK_URL)
    return NoOpDispatchService()


def _get_worker_tenant_id() -> TenantContext:
    """Validate and return the tenant context for this worker.

    Raises RuntimeError if COMUNICACION_WORKER_TENANT_ID is not configured,
    ensuring fail-fast rather than processing messages from all tenants.
    """
    settings = get_settings()
    if not settings.COMUNICACION_WORKER_TENANT_ID:
        raise RuntimeError(
            "COMUNICACION_WORKER_TENANT_ID is not configured. "
            "Worker cannot start without a tenant_id — set it to the tenant UUID."
        )
    from uuid import UUID

    return TenantContext(tenant_id=UUID(settings.COMUNICACION_WORKER_TENANT_ID))


async def _process_message(
    session: AsyncSession,
    comm: Comunicacion,
    dispatch_svc: WebhookDispatchService | NoOpDispatchService,
) -> None:
    repo = ComunicacionRepository(session, comm.tenant_id)

    comm.transition_to(ComunicacionEstado.ENVIANDO)
    await session.flush()
    await audit_emit(
        session,
        AUDIT_COMUNICACION_ENVIAR,
        entity="comunicacion",
        entity_id=comm.id,
        tenant_id=comm.tenant_id,
        detalle={"from": "Pendiente", "to": "Enviando"},
    )

    result: DispatchResult = await dispatch_svc.send(
        comm.get_destinatario(),
        comm.asunto,
        comm.cuerpo,
    )

    if result.success:
        comm.transition_to(ComunicacionEstado.ENVIADO)
        await repo.update_estado(comm, ComunicacionEstado.ENVIADO)
        await audit_emit(
            session,
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
        result = await dispatch_svc.send(comm.get_destinatario(), comm.asunto, comm.cuerpo)
        if result.success:
            await repo.update_estado(comm, ComunicacionEstado.ENVIADO)
            await audit_emit(
                session,
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
            await audit_emit(
                session,
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
        await audit_emit(
            session,
            AUDIT_COMUNICACION_ENVIAR,
            entity="comunicacion",
            entity_id=comm.id,
            tenant_id=comm.tenant_id,
            detalle={"from": "Enviando", "to": "Error", "error": result.error_detail},
        )


async def _recovery_job(session: AsyncSession, tenant_id: UUID, timeout_minutes: int = 5) -> None:
    settings = get_settings()
    timeout = timeout_minutes or settings.COMUNICACION_WORKER_LOCK_TIMEOUT

    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout)
    stmt = (
        select(Comunicacion)
        .where(
            Comunicacion.tenant_id == tenant_id,
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
    # Fail-fast if tenant_id is not configured
    worker_tenant = _get_worker_tenant_id()
    worker_tenant_id = worker_tenant.tenant_id
    set_tenant_context(worker_tenant)

    dispatch_svc = _build_dispatch_service()
    settings = get_settings()
    poll_interval = settings.COMUNICACION_WORKER_POLL_INTERVAL

    logger.info("Worker started for tenant_id=%s", worker_tenant_id)

    while True:
        try:
            async with async_session_maker() as session:
                # Ensure tenant context is set for each session
                set_tenant_context(worker_tenant)

                await _recovery_job(session, worker_tenant_id, settings.COMUNICACION_WORKER_LOCK_TIMEOUT)

                stmt = (
                    select(Comunicacion)
                    .where(
                        Comunicacion.tenant_id == worker_tenant_id,
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