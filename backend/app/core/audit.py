"""Audit seam for activia-trace.

Audit events are persisted to the `audit_log` table through `audit_emit()`,
which is called from `TenantScopedRepository` (soft_delete, restore,
unsafe_*) and from domain services. The DEBUG-level logger fallback is
kept for local development and test assertions.

Action codes (fixed vocabulary):
- ROW_SOFT_DELETE: a row was soft-deleted.
- ROW_RESTORE: a soft-deleted row was restored.
- TENANT_CROSS_QUERY: a method bypassed the tenant filter.
- ROW_INCLUDE_DELETED: a method returned soft-deleted rows.
- ROW_HARD_DELETE: a row was physically removed from the database.
- ASIGNACION_MODIFICAR: a batch operation modified assignations (create, clone, vigencia).

Anything else must be added by extending this vocabulary, not by passing
free-form strings from call sites — code review rejects unknown codes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Final, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.audit.models import AuditLog

logger = logging.getLogger("activia_trace.audit")


# Action codes — fixed set, extend with care.
ROW_SOFT_DELETE: Final = "ROW_SOFT_DELETE"
ROW_RESTORE: Final = "ROW_RESTORE"
TENANT_CROSS_QUERY: Final = "TENANT_CROSS_QUERY"
ROW_INCLUDE_DELETED: Final = "ROW_INCLUDE_DELETED"
ROW_HARD_DELETE: Final = "ROW_HARD_DELETE"
ASIGNACION_MODIFICAR: Final = "ASIGNACION_MODIFICAR"
PADRON_CARGAR: Final = "PADRON_CARGAR"
PADRON_VACIAR: Final = "PADRON_VACIAR"
CALIFICACIONES_IMPORTAR: Final = "CALIFICACIONES_IMPORTAR"

ACTION_CODES: Final[frozenset[str]] = frozenset(
    {
        ROW_SOFT_DELETE,
        ROW_RESTORE,
        TENANT_CROSS_QUERY,
        ROW_INCLUDE_DELETED,
        ROW_HARD_DELETE,
        ASIGNACION_MODIFICAR,
        PADRON_CARGAR,
        PADRON_VACIAR,
        CALIFICACIONES_IMPORTAR,
    }
)

# Sentinel used when no user actor context is available (e.g. repository
# internal operations like soft_delete, restore).
SYSTEM_ACTOR_ID: Final = UUID("00000000-0000-0000-0000-000000000000")


async def audit_emit(
    db: AsyncSession,
    action: str,
    *,
    actor_id: UUID | None = None,
    entity: str | None = None,
    entity_id: UUID | None = None,
    tenant_id: UUID | None = None,
    **extra: object,
) -> AuditLog:
    """Emit an audit event.

    Persists to ``audit_log`` and logs at DEBUG level as fallback.

    Args:
        db: database session.
        action: one of the ``ACTION_CODES`` strings. Unknown codes are
            logged at DEBUG level as a development hint.
        actor_id: the user who performed the action. Falls back to
            ``SYSTEM_ACTOR_ID`` when ``None``.
        entity: name of the ORM model (e.g. ``"tenant"``, ``"smoke"``).
        entity_id: the row's UUID.
        tenant_id: the tenant scope of the operation.
        **extra: additional structured fields. Callers MUST NOT pass
            plaintext, ciphertext, or any PII through this channel.
    """
    # Lazy import to avoid circular dependency:
    #   app.core.audit → app.audit.models → app.repositories.base → app.core.audit
    from app.audit.models import AuditLog

    if action not in ACTION_CODES:
        logger.debug(
            "audit emit with unknown action code",
            extra={"action": action, "known_codes": sorted(ACTION_CODES)},
        )

    detalle: dict[str, object] = {}
    if entity is not None:
        detalle["entity"] = entity
    if entity_id is not None:
        detalle["entity_id"] = str(entity_id)
    detalle.update(extra)

    filas_afectadas_val = 0
    raw = detalle.get("filas_afectadas")
    if raw is not None:
        try:
            filas_afectadas_val = int(raw)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            pass

    try:
        entry = AuditLog(
            id=uuid4(),
            tenant_id=tenant_id if tenant_id is not None else SYSTEM_ACTOR_ID,
            fecha_hora=datetime.now(timezone.utc),
            actor_id=actor_id if actor_id is not None else SYSTEM_ACTOR_ID,
            accion=action,
            detalle=detalle if detalle else None,
            filas_afectadas=filas_afectadas_val,
            ip="system",
            user_agent="system",
        )
        db.add(entry)
        await db.flush()
        result = entry
    except Exception:
        logger.debug(
            "audit DB write failed, action=%s", action,
            extra={"action": action, "detalle": detalle},
        )
        result = None

    payload: dict[str, object] = {
        "action": action,
        "entity": entity,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "tenant_id": str(tenant_id) if tenant_id is not None else None,
    }
    payload.update(extra)
    logger.debug("audit %s", action, extra=payload)

    return result
