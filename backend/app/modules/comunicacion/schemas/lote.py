"""Pydantic schemas for lote approval/rejection."""

from __future__ import annotations


from pydantic import BaseModel, ConfigDict


class LoteRechazarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    razon: str | None = None


class LoteAprobarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pass