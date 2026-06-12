"""Dispatch service — abstract interface to N8N/external email dispatcher."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DispatchResult:
    def __init__(self, success: bool, error_detail: str | None = None, retryable: bool = True) -> None:
        self.success = success
        self.error_detail = error_detail
        self.retryable = retryable


class DispatchService(ABC):
    """Abstract dispatch service."""

    @abstractmethod
    async def send(self, destinatario: str, asunto: str, cuerpo: str) -> DispatchResult:
        """Send an email. Returns success/failure and retry hint."""
        ...


class WebhookDispatchService(DispatchService):
    """Calls an external N8N webhook to perform the actual send."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def send(self, destinatario: str, asunto: str, cuerpo: str) -> DispatchResult:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "destinatario": destinatario,
                        "asunto": asunto,
                        "cuerpo": cuerpo,
                    },
                )
                if response.status_code in (429, 500, 502, 503, 504):
                    return DispatchResult(
                        success=False,
                        error_detail=f"HTTP {response.status_code}: {response.text[:200]}",
                        retryable=True,
                    )
                if response.status_code >= 400:
                    return DispatchResult(
                        success=False,
                        error_detail=f"HTTP {response.status_code}: {response.text[:200]}",
                        retryable=False,
                    )
                return DispatchResult(success=True)
        except httpx.TimeoutException:
            return DispatchResult(
                success=False,
                error_detail="Timeout contacting dispatch service",
                retryable=True,
            )
        except httpx.RequestError as exc:
            return DispatchResult(
                success=False,
                error_detail=f"Request error: {exc}",
                retryable=True,
            )


class NoOpDispatchService(DispatchService):
    """Development-only: always succeeds without sending."""

    async def send(self, destinatario: str, asunto: str, cuerpo: str) -> DispatchResult:
        return DispatchResult(success=True)