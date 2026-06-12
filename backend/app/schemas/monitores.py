"""Schemas para monitores (C-11)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class MonitoreoGeneralResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    datos: list[dict[str, Any]]


class MonitoreoCoordinacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    desde: str
    hasta: str
    datos: list[dict[str, Any]]