"""V1 main router (C-03 §6). Mounts the three auth routers and the health router.

# TODO: (REVIEW) Estructura de routers inconsistente. Coexisten rutas en:
#   app/routers/ (usuarios, estructura, equipos, encuentros, etc.)
#   app/api/v1/ (calificaciones, umbral_materia, analisis)
#   app/auth/routers/ (auth, password_reset, two_factor)
#   app/audit/routers/ (audit, impersonation, metrics)
#   app/modules/comunicacion/router.py
#   app/rbac/router.py + public_router.py
# Unificar bajo un criterio único.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers.health import router as health_router
from app.audit.routers import audit_router, impersonation_router, metrics_router
from app.auth.routers.auth import router as auth_login_router
from app.auth.routers.password_reset import router as auth_password_reset_router
from app.auth.routers.two_factor import router as auth_two_factor_router
from app.rbac.router import router as rbac_admin_router
from app.rbac.public_router import router as rbac_public_router
from app.routers.estructura import router as estructura_router
from app.routers.usuarios import router as usuarios_router
from app.routers.usuarios import asignacion_router
from app.routers.equipos import equipo_router
from app.routers.encuentros import router as encuentros_router
from app.routers.guardias import router as guardias_router
from app.routers.programas_fechas import router as programas_fechas_router
from app.routers.padrones import router as padrones_router
from app.api.v1.calificaciones import router as calificaciones_router
from app.api.v1.umbral_materia import router as umbral_materia_router
from app.api.v1.analisis import router as analisis_router
from app.modules.comunicacion.router import router as comunicacion_router
from app.routers.avisos import router as avisos_router
from app.routers.coloquios import router as coloquios_router
from app.routers.tareas import router as tareas_router
from app.routers.perfil import router as perfil_router
from app.routers.mensajes import router as mensajes_router

main_router = APIRouter()
main_router.include_router(health_router)
main_router.include_router(auth_login_router)
main_router.include_router(auth_password_reset_router)
main_router.include_router(auth_two_factor_router)
main_router.include_router(rbac_admin_router)
main_router.include_router(rbac_public_router)
main_router.include_router(estructura_router)
main_router.include_router(usuarios_router)
main_router.include_router(asignacion_router)
main_router.include_router(equipo_router)
main_router.include_router(encuentros_router)
main_router.include_router(guardias_router)
main_router.include_router(programas_fechas_router)
main_router.include_router(padrones_router)
main_router.include_router(calificaciones_router)
main_router.include_router(umbral_materia_router)
main_router.include_router(analisis_router)
main_router.include_router(audit_router)
main_router.include_router(impersonation_router)
main_router.include_router(metrics_router)
main_router.include_router(comunicacion_router)
main_router.include_router(avisos_router)
main_router.include_router(coloquios_router)
main_router.include_router(tareas_router)
main_router.include_router(perfil_router)
main_router.include_router(mensajes_router)
