"""Comunicacion module — message dispatch, preview, and worker queue."""

from app.modules.comunicacion.models.comunicacion import (
    Comunicacion,
    ComunicacionEstado,
    InvalidStateTransitionError,
    TERMINAL_STATES,
    STATE_TRANSITIONS,
    validate_transition,
)
from app.modules.comunicacion.repositories.comunicacion import ComunicacionRepository
from app.modules.comunicacion.services.approval import ApprovalService
from app.modules.comunicacion.services.dispatch import (
    DispatchResult,
    DispatchService,
    NoOpDispatchService,
    WebhookDispatchService,
)
from app.modules.comunicacion.services.preview import PreviewService

__all__ = [
    "Comunicacion",
    "ComunicacionEstado",
    "InvalidStateTransitionError",
    "TERMINAL_STATES",
    "STATE_TRANSITIONS",
    "validate_transition",
    "ComunicacionRepository",
    "ApprovalService",
    "DispatchResult",
    "DispatchService",
    "NoOpDispatchService",
    "WebhookDispatchService",
    "PreviewService",
]