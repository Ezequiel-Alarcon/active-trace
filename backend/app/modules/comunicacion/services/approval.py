"""Approval threshold logic per tenant."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


class ApprovalService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def requires_approval(self, recipient_count: int) -> bool:
        threshold = await self._get_threshold()
        return recipient_count > threshold

    async def _get_threshold(self) -> int:
        stmt = select(Tenant.umbral_aprobacion).where(Tenant.id == self._tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row if row is not None else 10