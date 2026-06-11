"""Tests for app.audit.impersonation (C-05 §6)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.audit.impersonation import (
    end_impersonation,
    get_impersonated_user_id,
    get_impersonation_record,
    is_impersonating,
    start_impersonation,
)

pytestmark = pytest.mark.no_db


class TestStartImpersonation:
    """Test start_impersonation()."""

    def test_creates_record(self) -> None:
        """start_impersonation creates a record with actor_id and target_user_id."""
        actor_id = uuid4()
        target_id = uuid4()

        record = start_impersonation(actor_id, target_id)

        assert record is not None
        assert record.actor_id == actor_id
        assert record.target_user_id == target_id
        assert record.started_at is not None

    def test_overwrites_existing_record_for_same_actor(self) -> None:
        """Multiple start calls for the same actor overwrite the previous record."""
        actor_id = uuid4()
        target_a = uuid4()
        target_b = uuid4()

        record_a = start_impersonation(actor_id, target_a)
        record_b = start_impersonation(actor_id, target_b)

        assert record_a.target_user_id == target_a
        assert record_b.target_user_id == target_b
        assert record_b != record_a


class TestIsImpersonating:
    """Test is_impersonating()."""

    def test_returns_true_after_start(self) -> None:
        """is_impersonating returns True after start_impersonation is called."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)

        assert is_impersonating(actor_id) is True

    def test_returns_false_for_unknown_actor(self) -> None:
        """is_impersonating returns False for an actor with no impersonation record."""
        unknown_actor = uuid4()

        assert is_impersonating(unknown_actor) is False

    def test_returns_false_after_end(self) -> None:
        """is_impersonating returns False after end_impersonation is called."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)
        end_impersonation(actor_id)

        assert is_impersonating(actor_id) is False


class TestGetImpersonatedUserId:
    """Test get_impersonated_user_id()."""

    def test_returns_correct_target(self) -> None:
        """get_impersonated_user_id returns the target user ID set by start_impersonation."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)

        assert get_impersonated_user_id(actor_id) == target_id

    def test_returns_none_when_not_impersonating(self) -> None:
        """get_impersonated_user_id returns None when actor has no active impersonation."""
        unknown_actor = uuid4()

        assert get_impersonated_user_id(unknown_actor) is None

    def test_returns_none_after_end(self) -> None:
        """get_impersonated_user_id returns None after end_impersonation."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)
        end_impersonation(actor_id)

        assert get_impersonated_user_id(actor_id) is None


class TestEndImpersonation:
    """Test end_impersonation()."""

    def test_removes_record(self) -> None:
        """end_impersonation removes the impersonation record."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)
        result = end_impersonation(actor_id)

        assert result is True
        assert is_impersonating(actor_id) is False

    def test_returns_false_if_no_active_session(self) -> None:
        """end_impersonation returns False if there is no active impersonation session."""
        actor_id = uuid4()

        result = end_impersonation(actor_id)

        assert result is False

    def test_multiple_ends_return_false_after_first(self) -> None:
        """Calling end_impersonation multiple times returns False after the first."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)
        first_result = end_impersonation(actor_id)
        second_result = end_impersonation(actor_id)

        assert first_result is True
        assert second_result is False


class TestGetImpersonationRecord:
    """Test get_impersonation_record()."""

    def test_returns_context_for_active_impersonation(self) -> None:
        """get_impersonation_record returns the ImpersonationContext for active sessions."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)
        record = get_impersonation_record(actor_id)

        assert record is not None
        assert record.actor_id == actor_id
        assert record.target_user_id == target_id

    def test_returns_none_for_unknown_actor(self) -> None:
        """get_impersonation_record returns None for actors with no session."""
        unknown_actor = uuid4()

        assert get_impersonation_record(unknown_actor) is None

    def test_returns_none_after_end(self) -> None:
        """get_impersonation_record returns None after end_impersonation."""
        actor_id = uuid4()
        target_id = uuid4()

        start_impersonation(actor_id, target_id)
        end_impersonation(actor_id)

        assert get_impersonation_record(actor_id) is None


class TestImpersonationIntegration:
    """Full impersonation lifecycle tests."""

    def test_full_lifecycle(self) -> None:
        """Complete impersonation lifecycle: start -> check -> use -> end."""
        actor_id = uuid4()
        target_id = uuid4()

        assert is_impersonating(actor_id) is False
        assert get_impersonated_user_id(actor_id) is None

        start_impersonation(actor_id, target_id)

        assert is_impersonating(actor_id) is True
        assert get_impersonated_user_id(actor_id) == target_id

        record = get_impersonation_record(actor_id)
        assert record is not None
        assert record.target_user_id == target_id

        end_impersonation(actor_id)

        assert is_impersonating(actor_id) is False
        assert get_impersonated_user_id(actor_id) is None
        assert get_impersonation_record(actor_id) is None

    def test_multiple_actors_independent(self) -> None:
        """Multiple actors can have independent impersonation sessions."""
        actor_a = uuid4()
        actor_b = uuid4()
        target_a = uuid4()
        target_b = uuid4()

        start_impersonation(actor_a, target_a)
        start_impersonation(actor_b, target_b)

        assert is_impersonating(actor_a) is True
        assert is_impersonating(actor_b) is True
        assert get_impersonated_user_id(actor_a) == target_a
        assert get_impersonated_user_id(actor_b) == target_b

        end_impersonation(actor_a)

        assert is_impersonating(actor_a) is False
        assert is_impersonating(actor_b) is True
        assert get_impersonated_user_id(actor_b) == target_b