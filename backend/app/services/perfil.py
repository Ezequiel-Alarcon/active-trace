from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.usuarios import (
    UsuarioRepository,
    decrypt_usuario_fields,
    encrypt_usuario_fields,
)
from app.schemas.perfil import PerfilResponse, PerfilUpdate


class PerfilService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _repo(self) -> UsuarioRepository:
        return UsuarioRepository(self._session, self._tenant_id)

    async def get_profile(self, user_id: UUID) -> PerfilResponse:
        repo = self._repo()
        obj = await repo.get_by_id(user_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        fields = decrypt_usuario_fields(obj)
        return PerfilResponse(**fields)

    async def update_profile(
        self, user_id: UUID, data: PerfilUpdate
    ) -> PerfilResponse:
        repo = self._repo()
        obj = await repo.get_by_id(user_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        update_data = data.model_dump(exclude_unset=True)

        if update_data:
            encrypted = encrypt_usuario_fields(update_data, self._tenant_id)
            obj = await repo.update(obj, encrypted)
            await self._session.refresh(obj)

        fields = decrypt_usuario_fields(obj)
        return PerfilResponse(**fields)
