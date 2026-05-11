"""Fixture contracts and loaders for D6 audit evals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ExpectedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    flag: str
    severity: Literal["low", "medium", "high", "critical"]
    affected_refs: list[str] = Field(default_factory=list)


class ExpectedAbsentFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    flag: str
    reason: str


class AuditFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    category: str
    subject: dict[str, Any]
    expected_findings: list[ExpectedFinding] = Field(default_factory=list)
    expected_absent_findings: list[ExpectedAbsentFinding] = Field(default_factory=list)
    expected_decision_state: str | None = None
    notes: str | None = None

    @computed_field
    @property
    def primary_expected_flags(self) -> set[str]:
        return {finding.flag for finding in self.expected_findings if finding.category == self.category}


def load_fixtures(path: Path) -> list[AuditFixture]:
    if path.is_file():
        candidates = [path]
    else:
        candidates = sorted(path.rglob("*.json"))
    fixtures = []
    for candidate in candidates:
        fixtures.append(AuditFixture.model_validate(json.loads(candidate.read_text())))
    return fixtures
