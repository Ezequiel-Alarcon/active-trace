"""Preview service — renders message without persisting."""

from __future__ import annotations


class PreviewService:
    """Renders a message preview. No DB state is modified."""

    async def preview(self, asunto: str, cuerpo: str, destinatario: str) -> dict[str, str]:
        return {
            "asunto": asunto,
            "cuerpo": cuerpo,
            "destinatario": destinatario,
        }