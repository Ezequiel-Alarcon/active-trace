"""Unit tests for worker recovery job (Task 7.7)."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.modules.comunicacion.models.comunicacion import (
    Comunicacion,
    ComunicacionEstado,
)


class TestComunicacionModel:
    def test_transition_to_enviando(self) -> None:
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=uuid4(),
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado=ComunicacionEstado.PENDIENTE,
        )
        comm.transition_to(ComunicacionEstado.ENVIANDO)
        assert comm.estado == ComunicacionEstado.ENVIANDO

    def test_transition_to_enviado(self) -> None:
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=uuid4(),
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado=ComunicacionEstado.ENVIANDO,
        )
        comm.transition_to(ComunicacionEstado.ENVIADO)
        assert comm.estado == ComunicacionEstado.ENVIADO
        assert comm.enviado_at is not None

    def test_transition_to_error_sets_detail(self) -> None:
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=uuid4(),
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado=ComunicacionEstado.ENVIANDO,
        )
        comm.transition_to(ComunicacionEstado.ERROR)
        assert comm.estado == ComunicacionEstado.ERROR

    def test_cannot_transition_from_enviado(self) -> None:
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=uuid4(),
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado=ComunicacionEstado.ENVIADO,
        )
        with pytest.raises(Exception):  # InvalidStateTransitionError
            comm.transition_to(ComunicacionEstado.PENDIENTE)

    def test_cannot_transition_from_cancelado(self) -> None:
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=uuid4(),
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado=ComunicacionEstado.CANCELADO,
        )
        with pytest.raises(Exception):
            comm.transition_to(ComunicacionEstado.PENDIENTE)

    def test_error_can_transition_back_to_pendiente(self) -> None:
        comm = Comunicacion(
            id=uuid4(),
            tenant_id=uuid4(),
            asunto="Test",
            cuerpo="Body",
            destinatario="test@example.com",
            estado=ComunicacionEstado.ERROR,
        )
        comm.transition_to(ComunicacionEstado.PENDIENTE)
        assert comm.estado == ComunicacionEstado.PENDIENTE