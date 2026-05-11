"""Manifest loading for D6 audit eval categories."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class EvalCategoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["planned", "shadow", "gating"]
    min_precision: float = Field(default=0.0, ge=0.0, le=1.0)
    min_recall: float = Field(default=0.0, ge=0.0, le=1.0)
    min_severity_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)


class EvalManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    categories: dict[str, EvalCategoryConfig]


def default_manifest_path() -> Path:
    return Path(__file__).with_name("manifest.yaml")


def load_manifest(path: Path | None = None) -> EvalManifest:
    manifest_path = path or default_manifest_path()
    payload = yaml.safe_load(manifest_path.read_text()) or {}
    return EvalManifest.model_validate(payload)
