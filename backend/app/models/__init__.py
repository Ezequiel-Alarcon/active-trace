"""SQLAlchemy 2.0 declarative base for activia-trace.

All domain models MUST import `Base` from this package, never from
`app.core.database` directly — Alembic autogenerate scans `Base.metadata`
and only this `Base` carries the metadata.
"""

from app.core.database import Base

from app.models.carrera import Carrera, CarreraEstado  # noqa: F401
from app.models.cohorte import Cohorte, CohorteEstado  # noqa: F401
from app.models.materia import Materia, MateriaEstado  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.asignacion import Asignacion, ContextoTipo  # noqa: F401
from app.models.slot_encuentro import SlotEncuentro, DiaSemana  # noqa: F401
from app.models.instancia_encuentro import InstanciaEncuentro, EstadoEncuentro  # noqa: F401
from app.models.guardia import Guardia  # noqa: F401
from app.models.programa_materia import ProgramaMateria  # noqa: F401
from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica  # noqa: F401
from app.audit.models import AuditLog  # noqa: F401

# NOTE: Calificacion and UmbralMateria live in app.domain.calificaciones.models.
# They are NOT imported here because calificacion.py imports TenantScopedMixin
# from app.models.mixins, which triggers app.models.__init__ execution.
# Importing domain models here would create a circular import:
#   app.models.__init__ -> domain.calificacion -> app.models.mixins -> app.models (cycle)
# Domain models import Base directly from app.core.database.

__all__ = [
    "Base",
    "Carrera", "CarreraEstado",
    "Cohorte", "CohorteEstado",
    "Materia", "MateriaEstado",
    "Usuario",
    "Asignacion", "ContextoTipo",
    "SlotEncuentro", "DiaSemana",
    "InstanciaEncuentro", "EstadoEncuentro",
    "Guardia",
    "ProgramaMateria",
    "FechaAcademica", "TipoFechaAcademica",
]