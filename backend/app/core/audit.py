"""Audit seam for activia-trace.

C-02 implements this as a thin wrapper over the structured logger. C-05
will replace the body of `audit_emit` with a real write to the `AuditLog`
table. The action-code vocabulary and the function signature are STABLE —
do not change them in C-05, only the sink.

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
from typing import Final
from uuid import UUID

logger = logging.getLogger("activia_trace.audit")


# Action codes — fixed set, extend with care.
ROW_SOFT_DELETE: Final = "ROW_SOFT_DELETE"
ROW_RESTORE: Final = "ROW_RESTORE"
TENANT_CROSS_QUERY: Final = "TENANT_CROSS_QUERY"
ROW_INCLUDE_DELETED: Final = "ROW_INCLUDE_DELETED"
ROW_HARD_DELETE: Final = "ROW_HARD_DELETE"
ASIGNACION_MODIFICAR: Final = "ASIGNACION_MODIFICAR"
PADRON_CARGAR: Final = "PADRON_CARGAR"

ACTION_CODES: Final[frozenset[str]] = frozenset(
    {
        ROW_SOFT_DELETE,
        ROW_RESTORE,
        TENANT_CROSS_QUERY,
        ROW_INCLUDE_DELETED,
        ROW_HARD_DELETE,
        ASIGNACION_MODIFICAR,
    }
)


def audit_emit(
    action: str,
    *,
    entity: str | None = None,
    entity_id: UUID | None = None,
    tenant_id: UUID | None = None,
    **extra: object,
) -> None:
    """Emit an audit event.

    Args:
        action: one of the `ACTION_CODES` strings. Unknown codes are
            logged at WARNING level too, so callers can spot mis-use
            during development.
        entity: name of the ORM model (e.g. `"tenant"`, `"smoke"`).
        entity_id: the row's UUID.
        tenant_id: the tenant scope of the operation.
        **extra: additional structured fields. Callers MUST NOT pass
            plaintext, ciphertext, or any PII through this channel.
    """
    if action not in ACTION_CODES:
        logger.warning(
            "audit emit with unknown action code",
            extra={"action": action, "known_codes": sorted(ACTION_CODES)},
        )
    payload: dict[str, object] = {
        "action": action,
        "entity": entity,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "tenant_id": str(tenant_id) if tenant_id is not None else None,
    }
    payload.update(extra)
    logger.warning("audit %s", action, extra=payload)
