"""Padron service (C-09).

Orchestrates padron import: parse file → create version+entries atomically.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import PADRON_CARGAR, PADRON_VACIAR, audit_emit
from app.core.security.hashing import hash_email_for_search
from app.models.padron import VersionPadron
from app.repositories.padron import PadronRepository
from app.schemas.padron import (
    PadronPreviewResponse,
    PadronPreviewRow,
    VersionPadronCreate,
)
from app.services.padron_parser import PadronParseError, parse_padron_file

# Roles with global scope on padron:vaciar (can vaciar any version)
_GLOBAL_VACIAR_ROLES = frozenset({"COORDINADOR", "ADMIN"})


class PadronServiceError(Exception):
    pass


class FileTooLargeError(PadronServiceError):
    pass


class DangerousExtensionError(PadronServiceError):
    pass


_DANGEROUS_EXTENSIONS = frozenset([
    "exe", "php", "sh", "bat", "cmd", "ps1", "vbs", "js", "jar", "scr", "msi",
])
_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class PadronService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = PadronRepository(session, tenant_id)

    async def preview(
        self, file_content: bytes, filename: str, usuario_ids_by_email: dict[str, UUID],
    ) -> PadronPreviewResponse:
        """Parse file and return preview rows without persisting."""
        self._validate_file(file_content, filename)

        try:
            rows = parse_padron_file(file_content, filename)
        except PadronParseError as e:
            raise PadronServiceError(str(e)) from e

        preview_rows: list[PadronPreviewRow] = []
        for row in rows:
            email = row.get("email") or ""
            # usuario_ids_by_email is keyed by email_hash (deterministic, tenant-scoped)
            email_lower = email.strip().lower()
            email_hash = hash_email_for_search(email_lower, self._tenant_id) if email_lower else ""
            matched = usuario_ids_by_email.get(email_hash) if email_lower else None
            preview_rows.append(PadronPreviewRow(
                nombre=row.get("nombre") or "",
                apellidos=row.get("apellidos") or "",
                email=email,
                comision=row.get("comision"),
                regional=row.get("regional"),
                matched_usuario_id=matched,
            ))

        return PadronPreviewResponse(
            rows=preview_rows,
            total=len(preview_rows),
            filename=filename,
        )

    async def import_padron(
        self,
        data: VersionPadronCreate,
        cargado_por: UUID,
    ) -> VersionPadron:
        """Create new active version, deactivating any previous one. Atomic."""
        version = await self._repo.create_version_and_entries(
            materia_id=data.materia_id,
            cohorte_id=data.cohorte_id,
            cargado_por=cargado_por,
            entradas_data=[
                {
                    "nombre": e.nombre,
                    "apellidos": e.apellidos,
                    "email": e.email,
                    "usuario_id": e.usuario_id,
                    "comision": e.comision,
                    "regional": e.regional,
                }
                for e in data.entradas
            ],
        )

        # Deactivate previous versions for same materia-cohorte
        await self._repo.deactivate_all(
            materia_id=data.materia_id,
            cohorte_id=data.cohorte_id,
            version_id_except=version.id,
        )

        await audit_emit(
            self._session,
            PADRON_CARGAR,
            tenant_id=self._tenant_id,
            actor_id=cargado_por,
            filas_afectadas=len(data.entradas),
            detalle={"materia_id": str(data.materia_id), "cohorte_id": str(data.cohorte_id)},
        )

        return version

    async def _is_global_vaciar(self, user_id: UUID) -> bool:
        """Return True if the user has a COORDINADOR or ADMIN role in this tenant."""
        return await self._repo.user_has_global_role(user_id, _GLOBAL_VACIAR_ROLES)

    async def vaciar_datos(
        self, materia_id: UUID, cohorte_id: UUID, current_user: object,
    ) -> None:
        """Soft-delete all padron versions and entries for materia/cohorte.

        Authorization rules (RN-04 / RN-05):
        - COORDINADOR / ADMIN: can vaciar any version of the tenant.
        - PROFESOR (or any other role with padron:vaciar): can only vaciar
          versions that they loaded (cargado_por == current_user.user_id).
        The RBAC permission check (padron:vaciar) is enforced by the router.
        """
        user_id: UUID = getattr(current_user, "user_id", current_user)  # type: ignore[arg-type]
        is_global = await self._is_global_vaciar(user_id)

        if not is_global:
            # PROFESOR scope: verify all versions belong to this user before deleting
            version = await self._repo.get_active_version(materia_id, cohorte_id)
            if version is not None and version.cargado_por != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puede vaciar versiones que usted mismo cargó.",
                )
            # Also check non-active versions
            versions = await self._repo.list_by_materia_cohorte(materia_id, cohorte_id)
            for v in versions:
                if v.cargado_por != user_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Solo puede vaciar versiones que usted mismo cargó.",
                    )

        count = await self._repo.vaciar_datos(materia_id, cohorte_id)
        await audit_emit(
            self._session,
            PADRON_VACIAR,
            tenant_id=self._tenant_id,
            actor_id=user_id,
            filas_afectadas=count,
            detalle={
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "versions_deleted": count,
            },
        )

    async def activar_version(self, version_id: UUID) -> VersionPadron:
        """Activate a specific version, deactivating all others for same materia-cohorte."""
        version = await self._repo.get_version_by_id(version_id)
        if not version:
            raise PadronServiceError("Versión no encontrada")

        await self._repo.deactivate_all(
            materia_id=version.materia_id,
            cohorte_id=version.cohorte_id,
            version_id_except=version_id,
        )
        version.activa = True
        await self._session.flush()
        return version

    def _validate_file(self, content: bytes, filename: str) -> None:
        if len(content) > _MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(
                f"El archivo excede el tamaño máximo de 50 MB ({len(content) / 1024 / 1024:.1f} MB)"
            )
        ext = filename.lower().split(".")[-1]
        if ext in _DANGEROUS_EXTENSIONS:
            raise DangerousExtensionError(
                f"Tipo de archivo .{ext} no permitido. Use .xlsx, .xls o .csv"
            )