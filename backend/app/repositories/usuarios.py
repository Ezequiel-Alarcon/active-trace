"""Usuario repository (C-07).

Extends TenantScopedRepository[Usuario] with PII encryption/decryption,
email uniqueness via email_hash, and tenant-scoped queries.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.crypto import decrypt, encrypt
from app.core.security.hashing import hash_email_for_search
from app.models.usuario import Usuario
from app.repositories.base import TenantScopedRepository


_AAD_EMAIL = "usuario.email"
_AAD_DNI = "usuario.dni"
_AAD_CUIL = "usuario.cuil"
_AAD_CBU = "usuario.cbu"
_AAD_ALIAS = "usuario.alias_cbu"


def encrypt_usuario_fields(data: dict[str, Any], tenant_id: UUID) -> dict[str, Any]:
    result = dict(data)
    if "email" in result and result["email"] is not None:
        email_lower = result["email"].strip().lower()
        result["email_hash"] = hash_email_for_search(email_lower, tenant_id)
        result["email_enc"] = encrypt(email_lower, tenant_id=tenant_id, aad_suffix=_AAD_EMAIL)
        del result["email"]
    if "dni" in result and result["dni"] is not None:
        result["dni_enc"] = encrypt(result["dni"], tenant_id=tenant_id, aad_suffix=_AAD_DNI)
        del result["dni"]
    if "cuil" in result and result["cuil"] is not None:
        result["cuil_enc"] = encrypt(result["cuil"], tenant_id=tenant_id, aad_suffix=_AAD_CUIL)
        del result["cuil"]
    if "cbu" in result and result["cbu"] is not None:
        result["cbu_enc"] = encrypt(result["cbu"], tenant_id=tenant_id, aad_suffix=_AAD_CBU)
        del result["cbu"]
    if "alias_cbu" in result and result["alias_cbu"] is not None:
        result["alias_cbu_enc"] = encrypt(
            result["alias_cbu"], tenant_id=tenant_id, aad_suffix=_AAD_ALIAS
        )
        del result["alias_cbu"]
    return result


def decrypt_usuario_fields(usuario: Usuario) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": usuario.id,
        "tenant_id": usuario.tenant_id,
        "nombre": usuario.nombre,
        "apellidos": usuario.apellidos,
        "banco": usuario.banco,
        "regional": usuario.regional,
        "legajo": usuario.legajo,
        "legajo_profesional": usuario.legajo_profesional,
        "fecha_nacimiento": usuario.fecha_nacimiento,
        "genero": usuario.genero,
        "observaciones": usuario.observaciones,
        "created_at": usuario.created_at,
        "updated_at": usuario.updated_at,
    }
    if usuario.email_enc:
        fields["email"] = decrypt(
            usuario.email_enc, tenant_id=usuario.tenant_id, aad_suffix=_AAD_EMAIL
        )
    if usuario.dni_enc:
        fields["dni"] = decrypt(
            usuario.dni_enc, tenant_id=usuario.tenant_id, aad_suffix=_AAD_DNI
        )
    if usuario.cuil_enc:
        fields["cuil"] = decrypt(
            usuario.cuil_enc, tenant_id=usuario.tenant_id, aad_suffix=_AAD_CUIL
        )
    if usuario.cbu_enc:
        fields["cbu"] = decrypt(
            usuario.cbu_enc, tenant_id=usuario.tenant_id, aad_suffix=_AAD_CBU
        )
    if usuario.alias_cbu_enc:
        fields["alias_cbu"] = decrypt(
            usuario.alias_cbu_enc, tenant_id=usuario.tenant_id, aad_suffix=_AAD_ALIAS
        )
    return fields


class UsuarioRepository(TenantScopedRepository[Usuario]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, Usuario, tenant_id)

    async def find_by_email(self, tenant_id: UUID, email_lower: str) -> Usuario | None:
        email_hash = hash_email_for_search(email_lower, tenant_id)
        stmt = (
            select(Usuario)
            .where(Usuario.tenant_id == tenant_id)
            .where(Usuario.email_hash == email_hash)
            .where(Usuario.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: dict[str, Any] | Usuario) -> Usuario:
        if isinstance(data, dict):
            data = encrypt_usuario_fields(data, self._tenant_id)
            if "tenant_id" not in data:
                data["tenant_id"] = self._tenant_id
        return await super().create(data)

    async def update(self, obj: Usuario, data: dict[str, Any]) -> Usuario:
        processed = encrypt_usuario_fields(data, self._tenant_id)
        return await super().update(obj, processed)
