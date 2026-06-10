"""V1 main router (C-03 §6). Mounts the three auth routers and the health router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers.health import router as health_router
from app.auth.routers.auth import router as auth_login_router
from app.auth.routers.password_reset import router as auth_password_reset_router
from app.auth.routers.two_factor import router as auth_two_factor_router
from app.rbac.router import router as rbac_admin_router
from app.rbac.public_router import router as rbac_public_router

main_router = APIRouter()
main_router.include_router(health_router)
main_router.include_router(auth_login_router)
main_router.include_router(auth_password_reset_router)
main_router.include_router(auth_two_factor_router)
main_router.include_router(rbac_admin_router)
main_router.include_router(rbac_public_router)
