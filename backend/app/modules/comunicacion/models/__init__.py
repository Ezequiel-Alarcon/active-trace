"""Comunicacion domain models."""

from __future__ import annotations

from app.modules.comunicacion.models.comunicacion import (
    Comunicacion,
    ComunicacionEstado,
    InvalidStateTransitionError,
    TERMINAL_STATES,
    STATE_TRANSITIONS,
    validate_transition,
)

__all__ = [
    "Comunicacion",
    "ComunicacionEstado",
    "InvalidStateTransitionError",
    "TERMINAL_STATES",
    "STATE_TRANSITIONS",
    "validate_transition",
]