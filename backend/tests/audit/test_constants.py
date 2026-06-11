"""Tests for app.audit.constants (C-05 §4)."""

from __future__ import annotations

import inspect

import pytest

from app.audit import constants as c
from app.audit.constants import is_valid_action_code

pytestmark = pytest.mark.no_db


class TestIsValidActionCode:
    """Test is_valid_action_code() validation."""

    def test_returns_true_for_known_codes(self) -> None:
        """is_valid_action_code returns True for all AUDIT_* string constants."""
        known_codes = [
            value
            for name, value in inspect.getmembers(c)
            if name.startswith("AUDIT_") and isinstance(value, str)
        ]
        # We have 42+ action codes defined
        assert len(known_codes) >= 40, f"Expected ≥40 action codes, got {len(known_codes)}"

        for code in known_codes:
            assert is_valid_action_code(code) is True, f"Expected True for {code}"

    def test_returns_false_for_unknown_codes(self) -> None:
        """is_valid_action_code returns False for unknown codes."""
        unknown_codes = [
            "INVALID_CODE",
            "UNKNOWN_ACTION",
            "",
            "USER_LOGIN",
            "SYSTEM_EVENT",
            "FOOBAR",
            "IMPERSONACION_INICIAR_EXTRA",
        ]

        for code in unknown_codes:
            assert is_valid_action_code(code) is False, f"Expected False for {code}"

    def test_returns_false_for_random_strings(self) -> None:
        """is_valid_action_code returns False for random strings."""
        random_strings = [
            "abc123",
            "ZZZZZZZZZZZ",
            "x" * 64,
            "IMPERSONACION",
            "AUDIT",
        ]

        for code in random_strings:
            assert is_valid_action_code(code) is False, f"Expected False for {code}"