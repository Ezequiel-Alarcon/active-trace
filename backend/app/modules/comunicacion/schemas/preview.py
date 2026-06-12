"""Pydantic schemas for message preview (no persistence)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str = Field(..., min_length=1, max_length=500)
    cuerpo: str = Field(..., min_length=1)
    destinatario: EmailStr


class PreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str
    destinatario: str