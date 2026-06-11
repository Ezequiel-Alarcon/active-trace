"""Impersonation session management (C-05 §6).

Server-side impersonation state stored in process memory (per-worker).
A dictionary keyed by the ADMIN's user_id (actor_id).

Security model:
- Only users with `impersonacion:usar` permission can start impersonation.
- The impersonation record is stored server-side (not in JWT, not in a header).
- The admin's JWT identifies the admin; the impersonation record identifies the target.
- Every audit entry records both `actor_id` (real admin) and `impersonado_id` (target).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from weakref import WeakValueDictionary

import logging

logger = logging.getLogger(__name__)


@dataclass
class ImpersonationContext:
    """Active impersonation session."""

    actor_id: UUID          # the admin who is impersonating
    target_user_id: UUID   # the user being impersonated
    started_at: datetime


# Per-worker in-memory store. Key = actor_id (UUID as string for dict stability).
_store: dict[str, ImpersonationContext] = {}


def start_impersonation(actor_id: UUID, target_user_id: UUID) -> ImpersonationContext:
    """Start an impersonation session. Overwrites any existing session for the same actor."""
    record = ImpersonationContext(
        actor_id=actor_id,
        target_user_id=target_user_id,
        started_at=datetime.now(timezone.utc),
    )
    _store[str(actor_id)] = record
    logger.info("Impersonation started: %s → %s", actor_id, target_user_id)
    return record


def end_impersonation(actor_id: UUID) -> bool:
    """End an impersonation session for the given actor. Returns True if a session was active."""
    key = str(actor_id)
    if key in _store:
        del _store[key]
        logger.info("Impersonation ended for %s", actor_id)
        return True
    return False


def get_impersonation_record(actor_id: UUID) -> ImpersonationContext | None:
    """Return the active impersonation record for the given actor, or None."""
    return _store.get(str(actor_id))


def is_impersonating(actor_id: UUID) -> bool:
    """Return True if the given user is currently impersonating someone."""
    return str(actor_id) in _store


def get_impersonated_user_id(actor_id: UUID) -> UUID | None:
    """Return the impersonated user's ID, or None if not impersonating."""
    record = _store.get(str(actor_id))
    return record.target_user_id if record else None


def get_current_impersonation(request) -> ImpersonationContext | None:
    """Read active impersonation from a FastAPI Request.

    Looks up the impersonation record using the current user's ID
    from request.state.current_user.id.
    """
    current_user = getattr(request.state, "current_user", None)
    if current_user is None:
        return None
    return get_impersonation_record(getattr(current_user, "id", None) or current_user.user_id)