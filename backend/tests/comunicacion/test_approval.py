"""Tests for ApprovalService (Task 7.2)."""

import pytest
from uuid import uuid4

from app.modules.comunicacion.services.approval import ApprovalService


class TestApprovalService:
    @pytest.mark.asyncio
    async def test_requires_approval_returns_false_when_count_below_threshold(
        self, db_session, set_tenant_context
    ):
        from app.models.tenant import Tenant, TenantEstado

        tenant_id = uuid4()
        # Create tenant with umbral_aprobacion = 10
        tenant = Tenant(id=tenant_id, codigo="TEST-A", nombre="Test", estado=TenantEstado.ACTIVO, umbral_aprobacion=10)
        db_session.add(tenant)
        await db_session.flush()

        set_tenant_context(tenant_id)
        svc = ApprovalService(db_session, tenant_id)
        result = await svc.requires_approval(5)
        assert result is False

    @pytest.mark.asyncio
    async def test_requires_approval_returns_true_when_count_exceeds_threshold(
        self, db_session, set_tenant_context
    ):
        from app.models.tenant import Tenant, TenantEstado

        tenant_id = uuid4()
        tenant = Tenant(id=tenant_id, codigo="TEST-B", nombre="Test", estado=TenantEstado.ACTIVO, umbral_aprobacion=10)
        db_session.add(tenant)
        await db_session.flush()

        set_tenant_context(tenant_id)
        svc = ApprovalService(db_session, tenant_id)
        result = await svc.requires_approval(15)
        assert result is True

    @pytest.mark.asyncio
    async def test_requires_approval_exactly_at_threshold_returns_false(
        self, db_session, set_tenant_context
    ):
        from app.models.tenant import Tenant, TenantEstado

        tenant_id = uuid4()
        tenant = Tenant(id=tenant_id, codigo="TEST-C", nombre="Test", estado=TenantEstado.ACTIVO, umbral_aprobacion=10)
        db_session.add(tenant)
        await db_session.flush()

        set_tenant_context(tenant_id)
        svc = ApprovalService(db_session, tenant_id)
        result = await svc.requires_approval(10)
        assert result is False