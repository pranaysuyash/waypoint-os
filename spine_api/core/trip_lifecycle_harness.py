"""trip_lifecycle harness — distribution report + graduation gate (Addendum 8).

The lifecycle write gate (persistence._consult_lifecycle_machine) classifies
every trip-status write and LOGs machine-illegal pairs into counters. This
module is the harness the runtime module's own docstring demanded: it reads
those counters plus a persisted distribution snapshot, and answers the only
question that matters for the staged ratchet:

    which LOG classes have accumulated enough evidence to graduate to RAISE?

Graduation policy (ratified posture, Addendum 8): a LOG class graduates when
(a) the counter shows the class occurs in practice AND (b) an explicit review
marks it raise-worthy. Counters alone never flip enforcement — the flip is a
reviewed act recorded here via `graduate_class`, so evidence accumulation and
enforcement changes are separable events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class GraduationLedger:
    """Which machine-violation classes have been reviewed and promoted."""

    raised: Dict[str, str] = field(default_factory=dict)  # class -> reason
    reviewed_keep_logged: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raised": dict(self.raised),
            "reviewed_keep_logged": dict(self.reviewed_keep_logged),
        }


_LEDGER = GraduationLedger()


def graduate_class(violation_class: str, reason: str) -> None:
    """Reviewed promotion of a LOG class to RAISE (enforcement flip)."""
    _LEDGER.raised[violation_class] = reason
    _LEDGER.reviewed_keep_logged.pop(violation_class, None)


def keep_logged(violation_class: str, reason: str) -> None:
    """Reviewed decision to keep a class at LOG (with the why)."""
    _LEDGER.reviewed_keep_logged[violation_class] = reason
    _LEDGER.raised.pop(violation_class, None)


def should_raise(violation_class: str) -> bool:
    return violation_class in _LEDGER.raised


def distribution_report(
    violation_counts: Dict[str, int],
    status_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """The distribution harness snapshot: what the runtime actually writes.

    status_counts: optional persisted-status frequency map (from the trip
    store read model) so the report shows the real vocabulary distribution
    alongside the violation counters.
    """
    total_violations = sum(violation_counts.values())
    ranked = sorted(violation_counts.items(), key=lambda kv: -kv[1])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "violation_total": total_violations,
        "violation_classes": [
            {
                "class": cls,
                "count": count,
                "share": round(count / total_violations, 4) if total_violations else 0.0,
                "enforcement": "raise" if should_raise(cls) else "log",
                "review_note": _LEDGER.raised.get(cls)
                or _LEDGER.reviewed_keep_logged.get(cls),
            }
            for cls, count in ranked
        ],
        "graduated_classes": sorted(_LEDGER.raised),
        "status_distribution": dict(sorted(
            (status_counts or {}).items(), key=lambda kv: -kv[1]
        )),
    }


def graduation_ready(violation_counts: Dict[str, int], min_samples: int = 5) -> List[str]:
    """LOG classes with enough samples to be worth a graduation review."""
    return sorted(cls for cls, n in violation_counts.items() if n >= min_samples)
