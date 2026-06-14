"""Tests for app.audit.models and AuditLogRepository (C-05 §2, §3)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.audit.models import AuditLog
from app.audit.repositories import AuditLogRepository

pytestmark = pytest.mark.no_db


class TestAuditLogModel:
    """Test AuditLog model creation and structure."""

    def test_audit_log_all_fields(self) -> None:
        """AuditLog can be created with all fields populated."""
        now = datetime.now(timezone.utc)
        actor_id = uuid4()
        tenant_id = uuid4()
        impersonado_id = uuid4()
        materia_id = uuid4()

        entry = AuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            fecha_hora=now,
            actor_id=actor_id,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            accion="MATERIA_CREAR",
            detalle={"key": "value"},
            filas_afectadas=5,
            ip="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        assert entry.id is not None
        assert entry.tenant_id == tenant_id
        assert entry.fecha_hora == now
        assert entry.actor_id == actor_id
        assert entry.impersonado_id == impersonado_id
        assert entry.materia_id == materia_id
        assert entry.accion == "MATERIA_CREAR"
        assert entry.detalle == {"key": "value"}
        assert entry.filas_afectadas == 5
        assert entry.ip == "192.168.1.1"
        assert entry.user_agent == "TestAgent/1.0"

    def test_audit_log_optional_fields_none(self) -> None:
        """AuditLog can be created with optional fields as None."""
        entry = AuditLog(
            id=uuid4(),
            tenant_id=uuid4(),
            fecha_hora=datetime.now(timezone.utc),
            actor_id=uuid4(),
            impersonado_id=None,
            materia_id=None,
            accion="LOGIN_EXITO",
            detalle=None,
            filas_afectadas=0,
            ip="0.0.0.0",
            user_agent="unknown",
        )

        assert entry.impersonado_id is None
        assert entry.materia_id is None
        assert entry.detalle is None

    def test_audit_log_repr(self) -> None:
        """AuditLog __repr__ includes id, accion, actor_id, impersonado_id."""
        entry_id = uuid4()
        actor_id = uuid4()
        impersonado_id = uuid4()

        entry = AuditLog(
            id=entry_id,
            tenant_id=uuid4(),
            fecha_hora=datetime.now(timezone.utc),
            actor_id=actor_id,
            impersonado_id=impersonado_id,
            materia_id=None,
            accion="CARRERA_CREAR",
            detalle=None,
            filas_afectadas=0,
            ip="0.0.0.0",
            user_agent="unknown",
        )

        repr_str = repr(entry)
        assert "AuditLog" in repr_str
        assert str(entry_id) in repr_str
        assert "CARRERA_CREAR" in repr_str
        assert str(actor_id) in repr_str
        assert str(impersonado_id) in repr_str


@pytest.mark.asyncio
async def test_repository_create(db_session, set_tenant_context) -> None:
    """AuditLogRepository.create() succeeds and returns an AuditLog entry."""
    tenant_id = uuid4()
    set_tenant_context(tenant_id)

    repo = AuditLogRepository(db_session, tenant_id)
    actor_id = uuid4()

    entry = await repo.create(
        actor_id=actor_id,
        accion="USUARIOS_GESTIONAR",
        impersonado_id=None,
        materia_id=None,
        detalle={"count": 3},
        filas_afectadas=3,
        ip="10.0.0.1",
        user_agent="pytest/1.0",
    )

    assert entry.id is not None
    assert entry.tenant_id == tenant_id
    assert entry.actor_id == actor_id
    assert entry.accion == "USUARIOS_GESTIONAR"
    assert entry.detalle == {"count": 3}
    assert entry.filas_afectadas == 3
    assert entry.ip == "10.0.0.1"
    assert entry.user_agent == "pytest/1.0"
    assert entry.fecha_hora is not None


@pytest.mark.asyncio
async def test_repository_create_minimal(db_session, set_tenant_context) -> None:
    """AuditLogRepository.create() works with only required fields."""
    tenant_id = uuid4()
    set_tenant_context(tenant_id)

    repo = AuditLogRepository(db_session, tenant_id)
    actor_id = uuid4()

    entry = await repo.create(
        actor_id=actor_id,
        accion="LOGIN_EXITO",
    )

    assert entry.id is not None
    assert entry.tenant_id == tenant_id
    assert entry.actor_id == actor_id
    assert entry.accion == "LOGIN_EXITO"
    assert entry.impersonado_id is None
    assert entry.materia_id is None
    assert entry.detalle is None
    assert entry.filas_afectadas == 0
    assert entry.ip == "0.0.0.0"
    assert entry.user_agent == "unknown"


@pytest.mark.asyncio
async def test_repository_update_raises_not_implemented(
    db_session, set_tenant_context
) -> None:
    """AuditLogRepository.update() raises NotImplementedError."""
    tenant_id = uuid4()
    set_tenant_context(tenant_id)

    repo = AuditLogRepository(db_session, tenant_id)

    with pytest.raises(NotImplementedError) as exc_info:
        await repo.update(uuid4(), {})

    assert "append-only" in str(exc_info.value).lower() or "update" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_repository_delete_raises_not_implemented(
    db_session, set_tenant_context
) -> None:
    """AuditLogRepository.delete() raises NotImplementedError."""
    tenant_id = uuid4()
    set_tenant_context(tenant_id)

    repo = AuditLogRepository(db_session, tenant_id)

    with pytest.raises(NotImplementedError) as exc_info:
        await repo.delete(uuid4())

    assert "append-only" in str(exc_info.value).lower() or "delete" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_repository_soft_delete_raises_not_implemented(
    db_session, set_tenant_context
) -> None:
    """AuditLogRepository.soft_delete() raises NotImplementedError."""
    tenant_id = uuid4()
    set_tenant_context(tenant_id)

    repo = AuditLogRepository(db_session, tenant_id)

    with pytest.raises(NotImplementedError) as exc_info:
        await repo.soft_delete(uuid4())

    assert "append-only" in str(exc_info.value).lower() or "soft_delete" in str(exc_info.value).lower()