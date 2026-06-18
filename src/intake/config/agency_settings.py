import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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
        default_factory=lambda: {k: dict(v) for k, v in _DEFAULT_MODE_OVERRIDES.items()}
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
            k: v for k, v in self.approval_gates.items() if k in DECISION_STATES_FROZENSET
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

        for key in (
            "min_proceed_confidence",
            "min_draft_confidence",
            "auto_proceed_with_warnings",
            "learn_from_overrides",
            "auto_reprocess_on_edit",
            "allow_explicit_reassess",
        ):
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
    max_calls_per_model: Optional[Dict[str, int]] = None  # e.g. {"gemini-2.0-flash": 100}
    daily_budget: Optional[float] = None
    budget_mode: Literal["warn", "block"] = "warn"
    budget_warning_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.8, 1.0])


@dataclass(slots=True)
class AlertDestination:
    """A single alert delivery destination."""
    id: str = ""
    label: str = ""
    enabled: bool = True
    type: Literal["webhook", "email"] = "webhook"
    # Webhook-specific
    url: str = ""
    # Email-specific
    email_to: str = ""
    email_cc: str = ""
    smtp_host: str = ""
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""  # Encrypted at rest; plaintext in transit only
    smtp_use_tls: bool = True
    sender: str = "no-reply@waypoint.ai"
    # Severity filter — only deliver events at or above this level
    min_severity: Literal["warning", "critical"] = "warning"
    # Which event types to deliver (empty = all)
    event_types: List[str] = field(default_factory=list)


@dataclass(slots=True)
class AlertDestinationsSettings:
    """Per-agency alert delivery destinations for LLM guard and ops events."""
    enabled: bool = False
    destinations: List[AlertDestination] = field(default_factory=list)


@dataclass(slots=True)
class SupportSettings:
    """Per-agency support channel configuration (P4-08).

    Controls how customer support is handled: channels, routing,
    SLA targets, and escalation rules.
    """
    # Channel configuration
    enable_email_support: bool = True
    enable_chat_support: bool = False
    enable_phone_support: bool = False
    enable_whatsapp_support: bool = True

    # Routing
    default_response_sla_hours: int = 24
    urgent_response_sla_hours: int = 4
    auto_route_by_destination: bool = False
    auto_route_by_language: bool = False

    # Escalation
    escalation_after_sla_breach: bool = True
    escalation_contact_email: str = ""
    escalation_contact_phone: str = ""

    # Business hours
    support_hours_start: str = "09:00"
    support_hours_end: str = "21:00"
    support_days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri", "sat"])
    timezone: str = "Asia/Kolkata"

    # Auto-responses
    enable_auto_acknowledgement: bool = True
    auto_acknowledgement_message: str = "Thank you for reaching out. We'll get back to you within {sla_hours} hours."
    out_of_hours_message: str = "Our support team is currently offline. We'll respond on the next business day."

    # Satisfaction tracking
    enable_csat_survey: bool = False
    csat_trigger: Literal["after_resolution", "after_first_response", "never"] = "after_resolution"


@dataclass(slots=True)
class CommSettings:
    """Per-agency communication preferences (P4-09).

    Controls outbound communication: templates, scheduling,
    multi-language support, and channel preferences.
    """
    # Outbound channels
    default_outbound_channel: Literal["email", "whatsapp", "sms"] = "email"
    allow_channel_switching: bool = True

    # Templates
    enable_template_library: bool = True
    default_greeting: str = "Hello {customer_name},"
    default_sign_off: str = "Best regards,\n{agent_name}\n{agency_name}"

    # Scheduling
    respect_operating_hours: bool = True
    send_immediately_during_hours: bool = True
    queue_outside_hours: bool = True
    max_emails_per_day_per_trip: int = 3
    max_whatsapp_per_day_per_trip: int = 5

    # Language
    auto_detect_language: bool = True
    default_language: str = "en"
    supported_languages: List[str] = field(default_factory=lambda: ["en"])
    translate_outbound: bool = False

    # Follow-up automation
    enable_auto_followup: bool = True
    auto_followup_delay_days: int = 3
    max_auto_followups: int = 2
    followup_escalate_after_max: bool = True

    # Notification preferences
    notify_on_customer_reply: bool = True
    notify_on_sla_warning: bool = True
    notify_on_escalation: bool = True
    digest_frequency: Literal["realtime", "hourly", "daily", "never"] = "realtime"

    # Branding
    include_agency_signature: bool = True
    include_unsubscribe_link: bool = True
    compliance_footer: str = ""


@dataclass(slots=True)
class AiAgentSettings:
    """Per-agency AI agent behavior configuration (P4-07).

    Controls what the AI agent can do autonomously, which models it uses,
    and which features are enabled for the agency.
    """
    # Feature gates
    enable_auto_intake: bool = True
    enable_auto_shortlist: bool = True
    enable_auto_proposal: bool = True
    enable_auto_negotiation: bool = True
    enable_frontier_orchestration: bool = True
    enable_checker_agent: bool = True
    enable_call_capture: bool = True
    enable_document_extraction: bool = True

    # Model preferences
    preferred_model: str = "gemini-2.0-flash"
    fallback_model: str = "gemini-2.0-flash"
    extraction_model: str = "gemini-2.0-flash"
    checker_model: str = "gemini-2.0-flash"

    def is_enabled(self, gate_name: str) -> bool:
        """Check if a feature gate is enabled by name.

        Returns True (default) for unknown gate names so existing code
        that doesn't use gates continues to work.
        """
        return getattr(self, gate_name, True)

    # Behavior tuning
    max_negotiation_rounds: int = 3
    proposal_confidence_threshold: float = 0.6
    auto_advance_stages: bool = True
    require_owner_review_above_value: float = 5000.0  # USD equivalent
    brand_voice: Literal["professional", "friendly", "luxury", "budget"] = "professional"
    response_language: str = "en"
    max_follow_up_questions: int = 3


@dataclass(slots=True)
class SeasonalPlanningPolicy:
    """Campaign-and-season planning policy for long-horizon operations."""

    active_seasons_enabled: bool = True
    default_quarter_window_months: int = 3
    channel_mix: Dict[str, float] = field(
        default_factory=lambda: {"organic": 0.35, "email": 0.25, "social": 0.20, "paid": 0.20}
    )
    weather_risk_threshold: float = 0.45
    budget_guardrail_multiplier: float = 1.20
    micro_seasonality_window_days: int = 14
    quarterly_recalibration_enabled: bool = True
    prelaunch_blocklist: List[str] = field(
        default_factory=lambda: [
            "budget_violation",
            "destination_mismatch",
            "channel_underweight",
            "insufficient_coverage",
        ]
    )


class AgencyTier(str, Enum):
    """Commercial tier for an agency.

    Used by downstream items (feature gates, usage limits, UI rendering)
    to branch behaviour based on the agency's service level.
    """

    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ---------------------------------------------------------------------------
# Tier Feature Gating (P4-10)
# ---------------------------------------------------------------------------

_TIER_FEATURE_LIMITS: Dict[str, Dict[str, Any]] = {
    # Starter: core pipeline only. No frontier, negotiation, or call capture.
    "starter": {
        "max_trips_per_month": 50,
        "max_team_members": 3,
        "enable_auto_negotiation": False,
        "enable_frontier_orchestration": False,
        "enable_call_capture": False,
        "enable_auto_followup": False,
        "max_negotiation_rounds": 0,
        "require_owner_review_above_value": 1000.0,
    },
    # Pro: full pipeline, limited frontier.
    "pro": {
        "max_trips_per_month": 500,
        "max_team_members": 15,
        "enable_auto_negotiation": True,
        "enable_frontier_orchestration": True,
        "enable_call_capture": False,
        "enable_auto_followup": True,
        "max_negotiation_rounds": 3,
        "require_owner_review_above_value": 5000.0,
    },
    # Enterprise: everything enabled, higher limits.
    "enterprise": {
        "max_trips_per_month": None,  # unlimited
        "max_team_members": None,  # unlimited
        "enable_auto_negotiation": True,
        "enable_frontier_orchestration": True,
        "enable_call_capture": True,
        "enable_auto_followup": True,
        "max_negotiation_rounds": 5,
        "require_owner_review_above_value": 10000.0,
    },
}


def get_tier_limits(tier: AgencyTier) -> Dict[str, Any]:
    """Return the feature limits for a given agency tier.

    This is the single source of truth for tier-based feature gating.
    Downstream code should call this instead of hardcoding tier checks.
    """
    return dict(_TIER_FEATURE_LIMITS.get(tier.value, _TIER_FEATURE_LIMITS["starter"]))


def tier_allows_feature(tier: AgencyTier, feature_name: str) -> bool:
    """Check if a feature is allowed for the given tier.

    Returns True if the feature is not explicitly disabled by tier limits.
    """
    limits = get_tier_limits(tier)
    feature_value = limits.get(feature_name)
    if feature_value is None:
        # Feature not mentioned in tier limits — default to allowed
        return True
    if isinstance(feature_value, bool):
        return feature_value
    return True


@dataclass(slots=True)
class AgencySettings:
    """Configuration set for an agency."""

    agency_id: str

    # -- Tier --
    tier: AgencyTier = AgencyTier.STARTER

    # -- Profile --
    agency_name: str = ""
    sub_brand: str = ""
    plan_label: str = ""
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

    # -- Seasonal Planning --
    seasonal: SeasonalPlanningPolicy = field(default_factory=SeasonalPlanningPolicy)

    # -- Alert Destinations (P4-05/P4-11) --
    alert_destinations: AlertDestinationsSettings = field(default_factory=AlertDestinationsSettings)

    # -- AI Agent Settings (P4-07) --
    ai_agent: AiAgentSettings = field(default_factory=AiAgentSettings)

    # -- Support Settings (P4-08) --
    support: SupportSettings = field(default_factory=SupportSettings)

    # -- Communication Settings (P4-09) --
    comm: CommSettings = field(default_factory=CommSettings)

    @classmethod
    def from_dict(cls, data: dict) -> "AgencySettings":
        """Load from dictionary, ignoring unknown keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}

        # Coerce tier from string to enum
        raw_tier = data.get("tier")
        if isinstance(raw_tier, str):
            try:
                filtered["tier"] = AgencyTier(raw_tier)
            except ValueError:
                filtered["tier"] = AgencyTier.STARTER
        elif raw_tier is not None and not isinstance(raw_tier, AgencyTier):
            filtered["tier"] = AgencyTier.STARTER

        raw_autonomy = data.get("autonomy")
        if isinstance(raw_autonomy, dict):
            filtered["autonomy"] = AgencyAutonomyPolicy.from_legacy_dict(raw_autonomy)

        raw_seasonal = data.get("seasonal")
        if isinstance(raw_seasonal, dict):
            filtered["seasonal"] = SeasonalPlanningPolicy(**raw_seasonal)

        raw_llm_guard = data.get("llm_guard")
        if isinstance(raw_llm_guard, dict):
            filtered["llm_guard"] = LLMGuardSettings(**raw_llm_guard)

        raw_alert_dest = data.get("alert_destinations")
        if isinstance(raw_alert_dest, dict):
            raw_dests = raw_alert_dest.get("destinations", [])
            destinations = [
                AlertDestination(**d) if isinstance(d, dict) else d
                for d in raw_dests
            ]
            filtered["alert_destinations"] = AlertDestinationsSettings(
                enabled=raw_alert_dest.get("enabled", False),
                destinations=destinations,
            )

        raw_ai_agent = data.get("ai_agent")
        if isinstance(raw_ai_agent, dict):
            filtered["ai_agent"] = AiAgentSettings(**raw_ai_agent)

        raw_support = data.get("support")
        if isinstance(raw_support, dict):
            filtered["support"] = SupportSettings(**raw_support)

        raw_comm = data.get("comm")
        if isinstance(raw_comm, dict):
            filtered["comm"] = CommSettings(**raw_comm)

        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        d = asdict(self)
        # dataclasses.asdict keeps enum instances; coerce to str for JSON
        if isinstance(d.get("tier"), AgencyTier):
            d["tier"] = d["tier"].value
        return d


# =============================================================================
# SQLite-backed persistence store
# =============================================================================


def _init_db() -> None:
    """Create the SQLite DB and table if they don't exist."""
    os.makedirs(_DATA_ROOT, exist_ok=True)
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agency_settings (
                agency_id TEXT PRIMARY KEY,
                config_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
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
                "SELECT config_json FROM agency_settings WHERE agency_id = ?", (agency_id,)
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
                (settings.agency_id, data),
            )
            conn.commit()
        except Exception as exc:
            logger.error(f"Failed to save agency settings for {settings.agency_id}: {exc}")
            raise
        finally:
            conn.close()
