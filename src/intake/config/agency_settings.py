import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

from ..constants import DECISION_STATES_FROZENSET

# =============================================================================
# DATA ROOT — where the SQLite DB lives
# =============================================================================
_DATA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "settings"
)


def _db_path() -> str:
    """Compute DB path dynamically so tests can monkeypatch _DATA_ROOT."""
    return os.path.join(_DATA_ROOT, "agency_settings.db")

# =============================================================================
# D1 Autonomy Gradient — AgencyAutonomyPolicy v2 (ADR-aligned)
# =============================================================================

# Default per-decision-state gate decisions
_DEFAULT_APPROVAL_GATES: Dict[str, Literal["auto", "review", "block"]] = {
    "PROCEED_TRAVELER_SAFE": "review",
    "PROCEED_INTERNAL_DRAFT": "auto",
    "ASK_FOLLOWUP": "auto",
    "BRANCH_OPTIONS": "review",
    "STOP_NEEDS_REVIEW": "block",
}

# Re-assessment policy defaults (Auto + explicit re-run controls)
_DEFAULT_AUTO_REPROCESS_STAGES: Dict[str, bool] = {
    "discovery": True,
    "shortlist": True,
    "proposal": True,
    "booking": True,
}


# Default operating_mode overrides
_DEFAULT_MODE_OVERRIDES: Dict[str, Dict[str, str]] = {
    "emergency": {"PROCEED_TRAVELER_SAFE": "block"},
    "audit": {"PROCEED_INTERNAL_DRAFT": "review"},
}


@dataclass(slots=True)
class AgencyAutonomyPolicy:
    """
    Per-agency autonomy configuration.

    This is the D1 policy contract — the gate between NB02 judgment (raw verdict)
    and NB03 execution (what the agency allows).
    """
    approval_gates: Dict[str, Literal["auto", "review", "block"]] = field(
        default_factory=lambda: dict(_DEFAULT_APPROVAL_GATES)
    )

    mode_overrides: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            k: dict(v) for k, v in _DEFAULT_MODE_OVERRIDES.items()
        }
    )

    auto_proceed_with_warnings: bool = False
    learn_from_overrides: bool = True

    # Re-assessment controls (edit-driven + explicit reruns)
    auto_reprocess_on_edit: bool = True
    allow_explicit_reassess: bool = True
    auto_reprocess_stages: Dict[str, bool] = field(
        default_factory=lambda: dict(_DEFAULT_AUTO_REPROCESS_STAGES)
    )

    # Legacy compatibility fields
    min_proceed_confidence: float = 0.8
    min_draft_confidence: float = 0.5
    require_review_on_infeasible_budget: bool = True
    auto_escalate_high_risk: bool = True
    checker_audit_threshold: float = 0.9  # Threshold for triggering secondary agent review

    _STOP_NEEDS_REVIEW: str = field(default="block", repr=False)

    def __post_init__(self):
        if self.approval_gates.get("STOP_NEEDS_REVIEW") != "block":
            self.approval_gates["STOP_NEEDS_REVIEW"] = "block"

        for state in DECISION_STATES_FROZENSET:
            if state not in self.approval_gates:
                self.approval_gates[state] = _DEFAULT_APPROVAL_GATES.get(state, "review")

        self.approval_gates = {
            k: v for k, v in self.approval_gates.items()
            if k in DECISION_STATES_FROZENSET
        }

    def effective_gate(self, decision_state: str, operating_mode: str) -> str:
        base = self.approval_gates.get(decision_state, "review")
        overrides = self.mode_overrides.get(operating_mode, {})
        return overrides.get(decision_state, base)

    @classmethod
    def from_legacy_dict(cls, data: dict) -> "AgencyAutonomyPolicy":
        policy = cls()

        if not data.get("require_review_on_infeasible_budget", True):
            policy.approval_gates["PROCEED_INTERNAL_DRAFT"] = "auto"

        raw_gates = data.get("approval_gates")
        if isinstance(raw_gates, dict):
            for k, v in raw_gates.items():
                if k in DECISION_STATES_FROZENSET and v in ("auto", "review", "block"):
                    policy.approval_gates[k] = v

        raw_overrides = data.get("mode_overrides")
        if isinstance(raw_overrides, dict):
            policy.mode_overrides = {
                k: dict(v) if isinstance(v, dict) else v
                for k, v in raw_overrides.items()
                if isinstance(v, dict) or isinstance(v, str)
            }

        for key in ("min_proceed_confidence", "min_draft_confidence",
                    "auto_proceed_with_warnings", "learn_from_overrides",
                    "auto_reprocess_on_edit", "allow_explicit_reassess"):
            if key in data:
                setattr(policy, key, data[key])

        raw_reprocess_stages = data.get("auto_reprocess_stages")
        if isinstance(raw_reprocess_stages, dict):
            policy.auto_reprocess_stages = {
                stage: bool(enabled)
                for stage, enabled in raw_reprocess_stages.items()
                if stage in ("discovery", "shortlist", "proposal", "booking")
            }
            for stage, enabled in _DEFAULT_AUTO_REPROCESS_STAGES.items():
                policy.auto_reprocess_stages.setdefault(stage, enabled)

        policy.__post_init__()
        return policy


@dataclass(slots=True)
class LLMGuardSettings:
    """LLM usage guard configuration for an agency."""
    enabled: bool = True
    max_calls_per_hour: Optional[int] = None
    daily_budget: Optional[float] = None
    budget_mode: Literal["warn", "block"] = "warn"
    budget_warning_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.8, 1.0])


@dataclass(slots=True)
class AgencySettings:
    """Configuration set for an agency."""
    agency_id: str

    # -- Profile --
    agency_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    logo_url: str = ""
    website: str = ""

    # -- Operational --
    target_margin_pct: float = 15.0
    default_currency: str = "INR"
    operating_hours_start: str = "09:00"
    operating_hours_end: str = "21:00"
    operating_days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri", "sat"])
    preferred_channels: List[str] = field(default_factory=lambda: ["whatsapp", "email"])
    brand_tone: str = "professional"

    # -- Frontier & Agentic --
    enable_auto_negotiation: bool = True
    negotiation_margin_threshold: float = 10.0  # Min % savings to trigger haggle
    enable_checker_agent: bool = True

    # -- Autonomy --
    autonomy: AgencyAutonomyPolicy = field(default_factory=AgencyAutonomyPolicy)

    # -- LLM Usage Guard --
    llm_guard: LLMGuardSettings = field(default_factory=LLMGuardSettings)

    @classmethod
    def from_dict(cls, data: dict) -> "AgencySettings":
        """Load from dictionary, ignoring unknown keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}

        raw_autonomy = data.get("autonomy")
        if isinstance(raw_autonomy, dict):
            filtered["autonomy"] = AgencyAutonomyPolicy.from_legacy_dict(raw_autonomy)

        raw_llm_guard = data.get("llm_guard")
        if isinstance(raw_llm_guard, dict):
            filtered["llm_guard"] = LLMGuardSettings(**raw_llm_guard)

        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        return asdict(self)


# =============================================================================
# SQLite-backed persistence store
# =============================================================================

def _init_db() -> None:
    """Create the SQLite DB and table if they don't exist."""
    os.makedirs(_DATA_ROOT, exist_ok=True)
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agency_settings (
                agency_id TEXT PRIMARY KEY,
                config_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _migrate_from_json(agency_id: str) -> Optional[dict]:
    """If a legacy JSON file exists, read it and delete it."""
    legacy_path = os.path.join(_DATA_ROOT, f"agency_{agency_id}.json")
    if os.path.exists(legacy_path):
        try:
            with open(legacy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            os.remove(legacy_path)
            return data
        except Exception:
            return None
    return None


class AgencySettingsStore:
    """SQLite-backed persistence store for AgencySettings."""

    @classmethod
    def _ensure_db(cls) -> None:
        _init_db()

    @classmethod
    def defaults(cls, agency_id: str = "default") -> AgencySettings:
        return AgencySettings(agency_id=agency_id)

    @classmethod
    def load(cls, agency_id: str) -> AgencySettings:
        """Load settings for the agency. If not found, return defaults (and seed them)."""
        cls._ensure_db()

        # Try legacy migration first
        legacy_data = _migrate_from_json(agency_id)
        if legacy_data is not None:
            legacy_data["agency_id"] = agency_id
            settings = AgencySettings.from_dict(legacy_data)
            cls.save(settings)
            return settings

        conn = sqlite3.connect(_db_path())
        try:
            row = conn.execute(
                "SELECT config_json FROM agency_settings WHERE agency_id = ?",
                (agency_id,)
            ).fetchone()
            if row is None:
                # Seed defaults
                settings = cls.defaults(agency_id)
                cls.save(settings)
                return settings

            data = json.loads(row[0])
            data["agency_id"] = agency_id
            return AgencySettings.from_dict(data)
        except Exception:
            return cls.defaults(agency_id)
        finally:
            conn.close()

    @classmethod
    def save(cls, settings: AgencySettings) -> None:
        """Persist settings to SQLite."""
        cls._ensure_db()
        conn = sqlite3.connect(_db_path())
        try:
            data = json.dumps(settings.to_dict(), indent=2)
            conn.execute(
                """
                INSERT INTO agency_settings (agency_id, config_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(agency_id) DO UPDATE SET
                    config_json = excluded.config_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (settings.agency_id, data)
            )
            conn.commit()
        except Exception as exc:
            logger.error(f"Failed to save agency settings for {settings.agency_id}: {exc}")
            raise
        finally:
            conn.close()
