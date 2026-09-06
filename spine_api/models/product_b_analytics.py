"""Typed response models for scoped Product-B KPI projections."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProductBKpiScope(BaseModel):
    """The authority/data boundary represented by a KPI response."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["agency", "global"]
    workspace_id: str | None = None
    workspace_count: int = Field(default=0, ge=0)


class ProductBKpiProvenance(BaseModel):
    """Source and freshness metadata for a KPI read."""

    model_config = ConfigDict(extra="forbid")

    data_source: str
    generated_at: str


class ProductBKpiResponse(BaseModel):
    """Common contract shared by agency and platform Product-B KPI routes."""

    model_config = ConfigDict(extra="forbid")

    scope: ProductBKpiScope
    window_days: int = Field(ge=1, le=365)
    qualified_only: bool
    sample: dict[str, Any]
    kpis: dict[str, Any]
    confidence_tiers: dict[str, int]
    counts: dict[str, int]
    definitions: dict[str, Any]
    provenance: ProductBKpiProvenance
