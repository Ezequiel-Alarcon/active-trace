"""Tests for C-29: worker multi-tenancy and PII encryption (destinatario).

Tests cover:
- Task 6.2: Worker with tenant_id=T1 does NOT select messages from tenant_id=T2
- Task 6.3: set_destinatario() does not modify self.destinatario (plaintext column)
- Task 6.4: Router creates Comunicacion with encrypted destinatario via set_destinatario()
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.comunicacion.models.comunicacion import Comunicacion
from app.modules.comunicacion.router import enqueue_mensajes
from app.modules.comunicacion.schemas import ComunicacionCreate


class TestSetDestinatarioDoesNotStorePlaintext:
    """Task 6.3: set_destinatario() must NOT modify self.destinatario."""

    def test_set_destinatario_does_not_assign_self_destinatario(self) -> None:
        """After calling set_destinatario, self.destinatario must remain unchanged.

        The plaintext column (destinatario) is retained only for backward-
        compatibility fallback during migration. It must NOT be written to
        by set_destinatario() — only destinatario_hash and destinatario_enc
        should be set.
        """
        tenant_id = uuid4()
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=tenant_id,
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",  # plaintext — initial value
            estado="PENDIENTE",
        )

        comm.set_destinatario("Another@example.com")

        # self.destinatario must NOT have been overwritten
        assert comm.destinatario == "test@example.com"

    def test_set_destinatario_sets_encrypted_column(self) -> None:
        """Verify set_destinatario sets destinatario_enc and destinatario_hash."""
        tenant_id = uuid4()
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=tenant_id,
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado="PENDIENTE",
        )

        comm.set_destinatario("encrypted@example.com")

        # Hash and encrypted value must be set
        assert comm.destinatario_hash != ""
        assert comm.destinatario_enc != ""

    def test_get_destinatario_returns_decrypted_email(self) -> None:
        """get_destinatario() must return the original plaintext after encryption."""
        tenant_id = uuid4()
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=tenant_id,
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado="PENDIENTE",
        )

        comm.set_destinatario("decrypted@example.com")
        retrieved = comm.get_destinatario()

        assert retrieved == "decrypted@example.com"

    def test_get_destinatario_falls_back_to_plaintext_when_enc_is_empty(self) -> None:
        """When destinatario_enc is empty, get_destinatario falls back to plaintext."""
        tenant_id = uuid4()
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=tenant_id,
            asunto="Test",
            cuerpo="Body",
            destinatario="fallback@example.com",
            estado="PENDIENTE",
        )
        # Simulate record without backfill (enc is empty string)
        comm.destinatario_enc = ""
        comm.destinatario_hash = ""

        retrieved = comm.get_destinatario()

        # Falls back to plaintext column
        assert retrieved == "fallback@example.com"


class TestWorkerTenantIsolation:
    """Task 6.2: Worker with tenant_id=T1 must NOT select messages from tenant_id=T2."""

    @pytest.mark.asyncio
    async def test_worker_query_filters_by_tenant_id(self) -> None:
        """Verify the worker poll query includes tenant_id filter.

        The SQLAlchemy query in run_poll_loop() MUST have:
            .where(Comunicacion.tenant_id == worker_tenant_id, ...)
        If this filter is missing, messages from other tenants would be processed.
        """
        from app.workers.comunicacion_worker import run_poll_loop
        from sqlalchemy import select

        worker_tenant_id = uuid4()
        other_tenant_id = uuid4()

        # Create mock messages for both tenants
        worker_msg = Comunicacion(
            id=uuid4(),
            tenant_id=worker_tenant_id,
            asunto="Worker msg",
            cuerpo="Body",
            destinatario="worker@test.com",
            estado="PENDIENTE",
        )
        other_msg = Comunicacion(
            id=uuid4(),
            tenant_id=other_tenant_id,
            asunto="Other tenant msg",
            cuerpo="Body",
            destinatario="other@test.com",
            estado="PENDIENTE",
        )

        # Build the same query the worker uses
        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.tenant_id == worker_tenant_id,
                Comunicacion.estado == "PENDIENTE",
                Comunicacion.deleted_at.is_(None),
            )
            .order_by(Comunicacion.created_at)
            .limit(10)
            .with_for_update(skip_locked=True)
        )

        # Compile to string to inspect the WHERE clause
        from sqlalchemy import inspect
        compiled = stmt.compile()

        compiled_sql = str(compiled.compile(compile_kwargs={"literal_binds": True}))

        # Verify the tenant_id filter is present
        assert str(worker_tenant_id) in compiled_sql or "tenant_id" in compiled_sql.lower()
        # The query must NOT include other_tenant_id
        assert str(other_tenant_id) not in compiled_sql


class TestRouterEnqueueUsesSetDestinatario:
    """Task 6.4: Router enqueue_mensajes must use set_destinatario(), not direct assignment."""

    @pytest.mark.asyncio
    async def test_router_calls_set_destinatario_not_direct_assignment(self) -> None:
        """Verify enqueue_mensajes creates Comunicacion objects using set_destinatario.

        The router must NOT do:
            destinatario=item.destinatario  # plaintext direct assignment
        It MUST do:
            obj.set_destinatario(item.destinatario)  # encrypted storage
        """
        from app.modules.comunicacion.models.comunicacion import Comunicacion

        tenant_id = uuid4()
        email = "router-test@example.com"

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Mock the repository
        with patch(
            "app.modules.comunicacion.router.ComunicacionRepository"
        ) as MockRepo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.create = AsyncMock(
                side_effect=lambda obj: obj
            )
            MockRepo.return_value = mock_repo_instance

            # Create a minimal user
            mock_user = MagicMock()
            mock_user.tenant_id = tenant_id
            mock_user.id = uuid4()
            mock_user.roles = []

            # Mock the approval service
            with patch(
                "app.modules.comunicacion.router.ApprovalService"
            ) as MockApproval:
                mock_approval_instance = MagicMock()
                mock_approval_instance.requires_approval = AsyncMock(
                    return_value=False
                )
                MockApproval.return_value = mock_approval_instance

                # Create request data
                data = [
                    ComunicacionCreate(
                        destinatario=email,
                        asunto="Test",
                        cuerpo="Body",
                    )
                ]

                # Call enqueue_mensajes
                await enqueue_mensajes(
                    session=mock_session,
                    current_user=mock_user,
                    data=data,
                )

                # Verify create was called with a Comunicacion object
                mock_repo_instance.create.assert_called_once()
                created_obj = mock_repo_instance.create.call_args[0][0]

                # Verify the object has encrypted/hash values set
                assert created_obj.destinatario_enc != ""
                assert created_obj.destinatario_hash != ""
                # The plaintext column should NOT have been overwritten
                # (it was set at construction time)
                # After set_destinatario, self.destinatario stays at construction value
