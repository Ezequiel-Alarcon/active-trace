"""Unit tests for PreviewService (Task 7.5 — simplified)."""

import pytest

from app.modules.comunicacion.services.preview import PreviewService


class TestPreviewService:
    @pytest.mark.asyncio
    async def test_preview_returns_same_content(self) -> None:
        svc = PreviewService()
        result = await svc.preview("Subject", "Body", "test@example.com")
        assert result["asunto"] == "Subject"
        assert result["cuerpo"] == "Body"
        assert result["destinatario"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_preview_is_idempotent(self) -> None:
        svc = PreviewService()
        r1 = await svc.preview("S", "B", "a@b.com")
        r2 = await svc.preview("S", "B", "a@b.com")
        assert r1 == r2