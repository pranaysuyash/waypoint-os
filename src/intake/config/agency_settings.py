import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal

# Define the data root dynamically
_DATA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "settings"
)

# =============================================================================
# D1 Autonomy Gradient — AgencyAutonomyPolicy v2 (ADR-aligned)
# =============================================================================

# Canonical decision states that the policy can gate
_DECISION_STATES = frozenset([
    "ASK_FOLLOWUP",
    "PROCEED_INTERNAL_DRAFT",
    "PROCEED_TRAVELER_SAFE",
    "BRANCH_OPTIONS",
    "STOP_NEEDS_REVIEW",
])

# Default per-decision-state gate decisions
_DEFAULT_APPROVAL_GATES: Dict[str, Literal["auto", "review", "block"]] = {
    "PROCEED_TRAVELER_SAFE": "review",  # default: agent reviews before send
    "PROCEED_INTERNAL_DRAFT": "auto",   # internal drafts auto-proceed
    "ASK_FOLLOWUP": "auto",             # follow-up questions auto-surface
    "BRANCH_OPTIONS": "review",          # options require agent selection
    "STOP_NEEDS_REVIEW": "block",        # always blocks — safety invariant
}

# Default operating_mode overrides
_DEFAULT_MODE_OVERRIDES: Dict[str, Dict[str, str]] = {
    "emergency": {"PROCEED_TRAVELER_SAFE": "block"},  # never auto-proceed in emergency
    "audit": {"PROCEED_INTERNAL_DRAFT": "review"},    # audits always reviewed
}


@dataclass
class AgencyAutonomyPolicy:
    """
    Per-agency autonomy configuration.

    This is the D1 policy contract — the gate between NB02 judgment (raw verdict)
    and NB03 execution (what the agency allows).
    """
    # Per decision_state: does this require human approval before acting?
    approval_gates: Dict[str, Literal["auto", "review", "block"]] = field(
        default_factory=lambda: dict(_DEFAULT_APPROVAL_GATES)
    )

    # Per operating_mode: override gates for specific contexts
    mode_overrides: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            k: dict(v) for k, v in _DEFAULT_MODE_OVERRIDES.items()
        }
    )

    # Suitability-specific: auto-proceed even if suitability warnings exist?
    auto_proceed_with_warnings: bool = False  # False = any warning triggers review gate

    # Override learning: do agent overrides feed back into preferences?
    learn_from_overrides: bool = True

    # --- Legacy compatibility fields (still loaded from old JSON) ---
    # These remain for backward compat with existing callers. They are NOT
    # serialized by default if they match defaults. Internal gate logic uses
    # approval_gates, not these thresholds.
    min_proceed_confidence: float = 0.8
    min_draft_confidence: float = 0.5
    require_review_on_infeasible_budget: bool = True
    auto_escalate_high_risk: bool = True

    # Safety invariant: STOP_NEEDS_REVIEW must always be "block"
    _STOP_NEEDS_REVIEW: str = field(default="block", repr=False)

    def __post_init__(self):
        # Enforce safety invariant: STOP_NEEDS_REVIEW must never be anything but block
        if self.approval_gates.get("STOP_NEEDS_REVIEW") != "block":
            self.approval_gates["STOP_NEEDS_REVIEW"] = "block"

        # Ensure all known decision states have a gate entry
        for state in _DECISION_STATES:
            if state not in self.approval_gates:
                self.approval_gates[state] = _DEFAULT_APPROVAL_GATES.get(state, "review")

        # Normalize any unknown decision-state keys out
        self.approval_gates = {
            k: v for k, v in self.approval_gates.items()
            if k in _DECISION_STATES
        }

    def effective_gate(self, decision_state: str, operating_mode: str) -> str:
        """
        Compute the effective autonomy action for a given decision_state
        and operating_mode, respecting mode overrides.
        Returns one of: 'auto', 'review', 'block'.
        """
        base = self.approval_gates.get(decision_state, "review")
        overrides = self.mode_overrides.get(operating_mode, {})
        return overrides.get(decision_state, base)

    @classmethod
    def from_legacy_dict(cls, data: dict) -> "AgencyAutonomyPolicy":
        """
        Upgrade a legacy threshold-only dict to the new ADR-aligned policy.
        Preserves threshold fields as compatibility layer.
        """
        # Start with defaults
        policy = cls()

        # Map old threshold booleans to gate adjustments
        if not data.get("require_review_on_infeasible_budget", True):
            # Legacy disabled review on infeasible budget → tighten to auto for draft
            policy.approval_gates["PROCEED_INTERNAL_DRAFT"] = "auto"

        # Pull through any explicitly-set gate dict if present
        raw_gates = data.get("approval_gates")
        if isinstance(raw_gates, dict):
            for k, v in raw_gates.items():
                if k in _DECISION_STATES and v in ("auto", "review", "block"):
                    policy.approval_gates[k] = v

        # Pull through mode overrides if present
        raw_overrides = data.get("mode_overrides")
        if isinstance(raw_overrides, dict):
            policy.mode_overrides = {
                k: dict(v) if isinstance(v, dict) else v
                for k, v in raw_overrides.items()
                if isinstance(v, dict) or isinstance(v, str)
            }

        # Pull through scalar compat fields
        for key in ("min_proceed_confidence", "min_draft_confidence",
                    "auto_proceed_with_warnings", "learn_from_overrides"):
            if key in data:
                setattr(policy, key, data[key])

        # Re-run post-init for safety invariant
        policy.__post_init__()
        return policy


@dataclass
class AgencySettings:
    """Configuration set for an agency."""
    agency_id: str
    target_margin_pct: float = 15.0
    default_currency: str = "INR"
    operating_hours_start: str = "09:00"
    operating_hours_end: str = "21:00"
    operating_days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri", "sat"])
    preferred_channels: List[str] = field(default_factory=lambda: ["whatsapp", "email"])
    brand_tone: str = "professional"  # cautious | measured | confident | direct | professional
    autonomy: AgencyAutonomyPolicy = field(default_factory=AgencyAutonomyPolicy)

    @classmethod
    def from_dict(cls, data: dict) -> "AgencySettings":
        """Load from dictionary, ignoring unknown keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}

        # Handle autonomy upgrade from legacy dict
        raw_autonomy = data.get("autonomy")
        if isinstance(raw_autonomy, dict):
            filtered["autonomy"] = AgencyAutonomyPolicy.from_legacy_dict(raw_autonomy)

        return cls(**filtered)


class AgencySettingsStore:
    """File-backed persistence store for AgencySettings."""

    @staticmethod
    def _path(agency_id: str) -> str:
        return os.path.join(_DATA_ROOT, f"agency_{agency_id}.json")

    @classmethod
    def defaults(cls, agency_id: str = "default") -> AgencySettings:
        return AgencySettings(agency_id=agency_id)

    @classmethod
    def load(cls, agency_id: str) -> AgencySettings:
        """Load settings for the agency. If not found, return defaults."""
        path = cls._path(agency_id)
        if not os.path.exists(path):
            return cls.defaults(agency_id)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Ensure the loaded object retains the requested ID
            data["agency_id"] = agency_id
            return AgencySettings.from_dict(data)
        except Exception:
            return cls.defaults(agency_id)

    @classmethod
    def save(cls, settings: AgencySettings) -> None:
        """Persist settings to the file system."""
        os.makedirs(_DATA_ROOT, exist_ok=True)
        path = cls._path(settings.agency_id)
        data = asdict(settings)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
