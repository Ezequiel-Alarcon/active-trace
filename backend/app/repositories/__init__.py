"""Repositories package.

Public entry points: `TenantScopedRepository` and `get_tenant_repository`.
"""

from app.repositories.base import (
    TenantIdRequiredError,
    TenantMismatchError,
    TenantScopedRepository,
    get_tenant_repository,
)

__all__ = [
    "TenantIdRequiredError",
    "TenantMismatchError",
    "TenantScopedRepository",
    "get_tenant_repository",
]
