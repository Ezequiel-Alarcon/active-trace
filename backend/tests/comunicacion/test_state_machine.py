"""Tests for Comunicacion state machine transitions (Task 7.1)."""

import pytest

from app.modules.comunicacion.models.comunicacion import (
    ComunicacionEstado,
    InvalidStateTransitionError,
    STATE_TRANSITIONS,
    TERMINAL_STATES,
    validate_transition,
)


class TestValidateTransition:
    def test_pendiente_to_enviando_is_valid(self) -> None:
        validate_transition(ComunicacionEstado.PENDIENTE, ComunicacionEstado.ENVIANDO)

    def test_pendiente_to_cancelado_is_valid(self) -> None:
        validate_transition(ComunicacionEstado.PENDIENTE, ComunicacionEstado.CANCELADO)

    def test_enviando_to_enviado_is_valid(self) -> None:
        validate_transition(ComunicacionEstado.ENVIANDO, ComunicacionEstado.ENVIADO)

    def test_enviando_to_error_is_valid(self) -> None:
        validate_transition(ComunicacionEstado.ENVIANDO, ComunicacionEstado.ERROR)

    def test_enviando_to_cancelado_is_valid(self) -> None:
        validate_transition(ComunicacionEstado.ENVIANDO, ComunicacionEstado.CANCELADO)

    def test_error_to_pendiente_is_valid(self) -> None:
        validate_transition(ComunicacionEstado.ERROR, ComunicacionEstado.PENDIENTE)

    def test_pendiente_to_enviado_is_invalid(self) -> None:
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            validate_transition(ComunicacionEstado.PENDIENTE, ComunicacionEstado.ENVIADO)
        assert "Cannot transition from Pendiente to Enviado" in str(exc_info.value)

    def test_enviado_to_any_state_is_invalid(self) -> None:
        for target in ComunicacionEstado:
            if target != ComunicacionEstado.ENVIADO:
                with pytest.raises(InvalidStateTransitionError) as exc_info:
                    validate_transition(ComunicacionEstado.ENVIADO, target)
                assert "terminal state" in str(exc_info.value)

    def test_cancelado_to_any_state_is_invalid(self) -> None:
        for target in ComunicacionEstado:
            if target != ComunicacionEstado.CANCELADO:
                with pytest.raises(InvalidStateTransitionError) as exc_info:
                    validate_transition(ComunicacionEstado.CANCELADO, target)
                assert "terminal state" in str(exc_info.value)

    def test_pendiente_to_error_is_invalid(self) -> None:
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(ComunicacionEstado.PENDIENTE, ComunicacionEstado.ERROR)


class TestTerminalStates:
    def test_enviado_is_terminal(self) -> None:
        assert ComunicacionEstado.ENVIADO in TERMINAL_STATES

    def test_cancelado_is_terminal(self) -> None:
        assert ComunicacionEstado.CANCELADO in TERMINAL_STATES

    def test_pendiente_is_not_terminal(self) -> None:
        assert ComunicacionEstado.PENDIENTE not in TERMINAL_STATES

    def test_enviando_is_not_terminal(self) -> None:
        assert ComunicacionEstado.ENVIANDO not in TERMINAL_STATES


class TestStateTransitionsMap:
    def test_pendiente_has_expected_transitions(self) -> None:
        expected = {ComunicacionEstado.ENVIANDO, ComunicacionEstado.CANCELADO}
        assert set(STATE_TRANSITIONS[ComunicacionEstado.PENDIENTE]) == expected

    def test_enviado_has_no_transitions(self) -> None:
        assert STATE_TRANSITIONS[ComunicacionEstado.ENVIADO] == set()

    def test_cancelado_has_no_transitions(self) -> None:
        assert STATE_TRANSITIONS[ComunicacionEstado.CANCELADO] == set()