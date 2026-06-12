"""Tests for dispatch service (Task 7.3)."""

import pytest

from app.modules.comunicacion.services.dispatch import (
    DispatchResult,
    NoOpDispatchService,
)


class TestNoOpDispatchService:
    @pytest.mark.asyncio
    async def test_send_always_succeeds(self) -> None:
        svc = NoOpDispatchService()
        result = await svc.send("test@example.com", "Subject", "Body")
        assert result.success is True
        assert result.error_detail is None


class TestDispatchResult:
    def test_success_result(self) -> None:
        r = DispatchResult(success=True)
        assert r.success is True
        assert r.error_detail is None
        assert r.retryable is True

    def test_retryable_failure(self) -> None:
        r = DispatchResult(success=False, error_detail="timeout", retryable=True)
        assert r.success is False
        assert r.error_detail == "timeout"
        assert r.retryable is True

    def test_non_retryable_failure(self) -> None:
        r = DispatchResult(success=False, error_detail="bad request", retryable=False)
        assert r.success is False
        assert r.retryable is False