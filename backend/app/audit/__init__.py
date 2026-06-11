"""Audit subsystem (C-05).

Exports:
    AuditLog model
    AuditLogRepository
    AuditLogService
    audit decorator
    impersonation context
    schemas
"""

from app.audit.models import AuditLog
from app.audit.repositories import AuditLogRepository
from app.audit.services import AuditLogService
from app.audit.decorator import audit
from app.audit.impersonation import (
    ImpersonationContext,
    get_impersonation_record as get_current_impersonation,
    start_impersonation,
    end_impersonation,
    is_impersonating,
    get_impersonated_user_id,
)
from app.audit import schemas

__all__ = [
    "AuditLog",
    "AuditLogRepository",
    "AuditLogService",
    "audit",
    "ImpersonationContext",
    "get_current_impersonation",
    "start_impersonation",
    "end_impersonation",
    "is_impersonating",
    "get_impersonated_user_id",
    "schemas",
]