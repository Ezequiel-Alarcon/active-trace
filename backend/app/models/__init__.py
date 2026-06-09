"""SQLAlchemy 2.0 declarative base for activia-trace.

All domain models MUST import `Base` from this package, never from
`app.core.database` directly — Alembic autogenerate scans `Base.metadata`
and only this `Base` carries the metadata.
"""

from app.core.database import Base

__all__ = ["Base"]
