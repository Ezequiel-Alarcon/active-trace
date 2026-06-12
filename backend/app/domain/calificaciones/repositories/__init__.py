"""Calificaciones domain repositories (C-10)."""

from app.domain.calificaciones.repositories.calificacion import CalificacionRepository
from app.domain.calificaciones.repositories.umbral_materia import (
    UmbralMateriaRepository,
)

__all__ = ["CalificacionRepository", "UmbralMateriaRepository"]