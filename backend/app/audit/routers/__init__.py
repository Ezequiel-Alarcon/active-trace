"""Audit routers package."""

from app.audit.routers.audit import router as audit_router
from app.audit.routers.impersonation import router as impersonation_router

__all__ = ["audit_router", "impersonation_router"]