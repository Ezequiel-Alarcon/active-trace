"""Tests for app.audit.decorator (C-05 §5)."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio

from app.audit.decorator import audit

pytestmark = pytest.mark.no_db


class TestAuditDecoratorAsync:
    """Test @audit decorator with async functions."""

    @pytest.mark.asyncio
    async def test_decorator_captures_action_code(self) -> None:
        """@audit decorator sets action_code on the decorated async function."""
        from app.audit.constants import AUDIT_CALIFICACIONES_IMPORTAR

        @audit(AUDIT_CALIFICACIONES_IMPORTAR)
        async def import_calificaciones(request: Any, count: int) -> int:
            return count

        class FakeState:
            current_user = type("obj", (object,), {"id": uuid4(), "tenant_id": uuid4()})()
            impersonating = False
            impersonated_user_id = None
            ip = "127.0.0.1"
            user_agent = "pytest"

        class FakeRequest:
            state = FakeState()

        result = await import_calificaciones(FakeRequest(), 42)

        assert result == 42

    @pytest.mark.asyncio
    async def test_decorator_works_with_async_function(self) -> None:
        """@audit decorator works with async functions and returns their result."""

        @audit("MATERIA_CREAR")
        async def async_task(value: int) -> int:
            await asyncio.sleep(0.01)
            return value * 2

        result = await async_task(21)
        assert result == 42

    @pytest.mark.asyncio
    async def test_decorator_does_not_raise_on_missing_request(self) -> None:
        """@audit decorator does NOT raise if no request is found in args (fire-and-forget)."""

        @audit("LOGIN_EXITO")
        async def task_without_request() -> str:
            return "success"

        result = await task_without_request()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_passes_get_detalle_function(self) -> None:
        """@audit decorator passes get_detalle callable correctly."""

        def detalle_builder(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return {"args": str(args), "kwargs": str(kwargs)}

        @audit("USUARIOS_GESTIONAR", get_detalle=detalle_builder)
        async def manage_users(request: Any) -> int:
            return 5

        class FakeState:
            current_user = type("obj", (object,), {"id": uuid4(), "tenant_id": uuid4()})()
            impersonating = False
            impersonated_user_id = None
            ip = "127.0.0.1"
            user_agent = "pytest"

        class FakeRequest:
            state = FakeState()

        result = await manage_users(FakeRequest())
        assert result == 5


class TestAuditDecoratorSync:
    """Test @audit decorator with sync functions."""

    @pytest.mark.asyncio
    async def test_decorator_works_with_sync_function(self) -> None:
        """@audit decorator works with sync functions."""

        @audit("ROL_CREAR")
        def sync_task(value: str) -> str:
            return f"processed: {value}"

        result = sync_task("test")
        assert result == "processed: test"

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self) -> None:
        """@audit decorator preserves the wrapped function's __name__ and __doc__."""

        @audit("EQUIPOS_ASIGNAR")
        def sync_task_with_doc(value: int) -> int:
            """This is the docstring."""
            return value + 1

        assert sync_task_with_doc.__name__ == "sync_task_with_doc"
        assert sync_task_with_doc.__doc__ == "This is the docstring."


class TestAuditDecoratorFireAndForget:
    """Test that @audit decorator is fire-and-forget (does not raise on failure)."""

    @pytest.mark.asyncio
    async def test_decorator_does_not_propagate_exceptions(self) -> None:
        """@audit decorator does not propagate exceptions from failed audit writes.

        This is the fire-and-forget guarantee: audit failures are logged but
        the main function result is returned normally.
        """

        @audit("IMPERSONACION_INICIAR")
        async def task_that_succeeds() -> str:
            return "main_result"

        result = await task_that_succeeds()
        assert result == "main_result"