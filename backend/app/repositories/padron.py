"""Padron repository (C-09).

Extends TenantScopedRepository with atomic version+entries creation,
active-version queries, and vaciar_datos (soft-delete all).
"""

from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import TenantScopedRepository


class PadronRepository(TenantScopedRepository[VersionPadron]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, VersionPadron, tenant_id)

    async def create_version_and_entries(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        cargado_por: UUID,
        entradas_data: list[dict[str, Any]],
    ) -> VersionPadron:
        version = VersionPadron(
            tenant_id=self._tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por,
            activa=True,
        )
        self._session.add(version)
        await self._session.flush()

        for entry_data in entradas_data:
            entry = EntradaPadron(
                tenant_id=self._tenant_id,
                version_id=version.id,
                nombre=entry_data["nombre"],
                apellidos=entry_data["apellidos"],
                email=entry_data["email"],
                usuario_id=entry_data.get("usuario_id"),
                comision=entry_data.get("comision"),
                regional=entry_data.get("regional"),
            )
            self._session.add(entry)

        await self._session.flush()
        return version

    async def get_active_version(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> VersionPadron | None:
        stmt = (
            select(VersionPadron)
            .where(VersionPadron.tenant_id == self._tenant_id)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.activa)
            .where(VersionPadron.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate_all(
        self, materia_id: UUID, cohorte_id: UUID, version_id_except: UUID
    ) -> None:
        stmt = (
            update(VersionPadron)
            .where(VersionPadron.tenant_id == self._tenant_id)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.id != version_id_except)
            .where(VersionPadron.activa)
            .where(VersionPadron.deleted_at.is_(None))
            .values(activa=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_entries_by_version(
        self, version_id: UUID
    ) -> Sequence[EntradaPadron]:
        stmt = (
            select(EntradaPadron)
            .where(EntradaPadron.tenant_id == self._tenant_id)
            .where(EntradaPadron.version_id == version_id)
            .where(EntradaPadron.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def vaciar_datos(self, materia_id: UUID, cohorte_id: UUID) -> int:
        stmt_versions = (
            select(VersionPadron.id)
            .where(VersionPadron.tenant_id == self._tenant_id)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt_versions)
        version_ids = [row[0] for row in result.all()]

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        count = 0
        if version_ids:
            stmt_entries = (
                update(EntradaPadron)
                .where(EntradaPadron.tenant_id == self._tenant_id)
                .where(EntradaPadron.version_id.in_(version_ids))
                .where(EntradaPadron.deleted_at.is_(None))
                .values(deleted_at=now)
            )
            await self._session.execute(stmt_entries)

            stmt_versions_update = (
                update(VersionPadron)
                .where(VersionPadron.tenant_id == self._tenant_id)
                .where(VersionPadron.materia_id == materia_id)
                .where(VersionPadron.cohorte_id == cohorte_id)
                .where(VersionPadron.deleted_at.is_(None))
                .values(deleted_at=now)
            )
            await self._session.execute(stmt_versions_update)

            count = len(version_ids)

        await self._session.flush()
        return count

    async def list_by_materia_cohorte(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> Sequence[VersionPadron]:
        stmt = (
            select(VersionPadron)
            .where(VersionPadron.tenant_id == self._tenant_id)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.deleted_at.is_(None))
            .order_by(VersionPadron.cargado_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_version_by_id(self, version_id: UUID) -> VersionPadron | None:
        stmt = (
            select(VersionPadron)
            .where(VersionPadron.id == version_id)
            .where(VersionPadron.tenant_id == self._tenant_id)
            .where(VersionPadron.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()