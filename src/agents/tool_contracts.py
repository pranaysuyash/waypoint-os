"""
Shared contracts for agent tool evidence.

Tool-calling agents must normalize live/provider data into this shape before
another agent or reasoning layer consumes it. The raw provider response should
never be treated as canonical state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class ToolFreshnessPolicy:
    max_age_seconds: int
    fail_closed: bool = True


@dataclass(frozen=True, slots=True)
class ToolEvidence:
    source: str
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_reference: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    query: dict[str, Any]
    data: dict[str, Any]
    evidence: ToolEvidence
    expires_at: Optional[str] = None

    def is_fresh(self, now: Optional[datetime] = None) -> bool:
        if not self.expires_at:
            return True
        now = now or datetime.now(timezone.utc)
        expires = _parse_dt(self.expires_at)
        return bool(expires and now <= expires)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "query": self.query,
            "data": self.data,
            "evidence": self.evidence.to_dict(),
            "expires_at": self.expires_at,
            "fresh": self.is_fresh(),
        }

    @classmethod
    def from_static(
        cls,
        tool_name: str,
        query: dict[str, Any],
        data: dict[str, Any],
        source: str,
        freshness: ToolFreshnessPolicy,
        confidence: float = 1.0,
        raw_reference: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> "ToolResult":
        timestamp = now or datetime.now(timezone.utc)
        return cls(
            tool_name=tool_name,
            query=query,
            data=data,
            evidence=ToolEvidence(
                source=source,
                fetched_at=timestamp.isoformat(),
                raw_reference=raw_reference,
                confidence=confidence,
            ),
            expires_at=(timestamp + timedelta(seconds=freshness.max_age_seconds)).isoformat(),
        )


def _parse_dt(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
