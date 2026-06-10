"""RBAC package (C-04)."""

from app.rbac.models import Permiso, Rol, RolPermiso
from app.rbac.services import PermissionResolver

__all__ = ["Rol", "Permiso", "RolPermiso", "PermissionResolver"]
