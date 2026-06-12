"""Calificaciones domain schemas (C-10)."""

from app.domain.calificaciones.schemas.calificacion import (
    CalificacionBase,
    CalificacionConfirmRequest,
    CalificacionConfirmResponse,
    CalificacionCreate,
    CalificacionOrigen,
    CalificacionPreviewResponse,
    CalificacionPreviewRow,
    CalificacionRead,
)
from app.domain.calificaciones.schemas.umbral_materia import (
    UmbralMateriaBase,
    UmbralMateriaCreate,
    UmbralMateriaRead,
    UmbralMateriaUpdate,
)

__all__ = [
    "CalificacionBase",
    "CalificacionConfirmRequest",
    "CalificacionConfirmResponse",
    "CalificacionCreate",
    "CalificacionOrigen",
    "CalificacionPreviewResponse",
    "CalificacionPreviewRow",
    "CalificacionRead",
    "UmbralMateriaBase",
    "UmbralMateriaCreate",
    "UmbralMateriaRead",
    "UmbralMateriaUpdate",
]