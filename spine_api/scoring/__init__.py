"""
Trip Priority Scoring Engine -- 2D model (urgency x importance).

Canonical computation. Replaces the old 1D formula in
inbox_projection.py:364-377 and bff-trip-adapters.ts:529-543.

Design doc: Docs/DESIGN_2D_PRIORITY_MODEL_2026-05-08.md
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


_SLA_DAYS_BREACHED = 7
_SLA_DAYS_AT_RISK = 4

_URGENCY_WEIGHTS = {
    "sla_breach": 0.22,
    "departure_proximity": 0.18,
    "client_recency": 0.12,
    "client_initiated": 0.10,
    "past_due_actions": 0.08,
    "operational_risk": 0.30,
}

_IMPORTANCE_WEIGHTS = {
    "revenue": 0.35,
    "client_tier": 0.25,
    "trip_complexity": 0.15,
    "referral_potential": 0.15,
    "repeat_client": 0.10,
}


def _as_int(val: Any, fallback: int = 0) -> int:
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    if isinstance(val, str):
        cleaned = val.replace("$", "").replace(",", "").replace("k", "000")
        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            return fallback
    if isinstance(val, float):
        return int(val)
    return fallback


def _as_str(val: Any, fallback: str = "") -> str:
    if isinstance(val, str) and val:
        return val
    if isinstance(val, (int, float, bool)):
        return str(val)
    return fallback


def _get_nested(data: Any, path: str, default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part, default)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default


def _first_present(*values: Any) -> Any:
    for v in values:
        if v is not None and v != "":
            return v
    return None


def _clamp(score: float) -> int:
    return max(0, min(100, int(round(score))))


def _linear(val: float, lo: float, hi: float) -> float:
    if val <= lo:
        return 0.0
    if val >= hi:
        return 100.0
    return ((val - lo) / (hi - lo)) * 100.0


# ---- Urgency ----

def _score_sla_breach(days_in_stage: int) -> float:
    if days_in_stage > _SLA_DAYS_BREACHED:
        return 100.0
    if days_in_stage > _SLA_DAYS_AT_RISK:
        return 60.0
    return 0.0


def _parse_departure_days(date_window: str, now: Optional[datetime] = None) -> Optional[int]:
    if not date_window or date_window == "TBD":
        return None
    if now is None:
        now = _now()
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    cleaned = date_window.lower().strip()
    year = now.year
    ym = re.search(r"\b(20\d\d)\b", cleaned)
    if ym:
        year = int(ym.group(1))
    months_found = [m for a, m in months_map.items() if a in cleaned]
    if not months_found:
        return None
    earliest = min(months_found)
    if earliest < now.month and year == now.year:
        year += 1
    try:
        departure = datetime(year, earliest, 1, tzinfo=timezone.utc)
    except ValueError:
        return None
    return (departure - now).days


def _score_departure_proximity(date_window: str, now: Optional[datetime] = None) -> float:
    days = _parse_departure_days(date_window, now)
    if days is None:
        return 50.0
    if days <= 0:
        return 100.0
    return max(0.0, 100.0 - _linear(days, 0, 90))


def _score_client_recency(days_in_stage: int) -> float:
    return _linear(days_in_stage, 0, 14)


def _score_client_initiated(source: Dict[str, Any]) -> float:
    s = _as_str(source.get("status"))
    if s in ("needs_followup", "awaiting_customer_details"):
        return 80.0
    esc = _as_str(_get_nested(source, "analytics.escalation_severity"))
    if esc == "critical":
        return 100.0
    events = _get_nested(source, "extracted.events", [])
    if isinstance(events, list) and events:
        return 40.0
    return 0.0


def _score_past_due_actions(source: Dict[str, Any], now: Optional[datetime] = None) -> float:
    actions = _get_nested(source, "decision.pending_actions", [])
    if not isinstance(actions, list):
        return 0.0
    if now is None:
        now = _now()
    past_due = 0
    for a in actions:
        if not isinstance(a, dict):
            continue
        due = _as_str(a.get("due_date") or a.get("dueDate"))
        if not due:
            continue
        try:
            if datetime.fromisoformat(due.replace("Z", "+00:00")) < now:
                past_due += 1
        except (ValueError, TypeError):
            continue
    return min(100.0, past_due * 33.0)


_EMERGENCY_KEYWORDS = (
    # Documentation & compliance
    "passport", "visa", "license", "permit", "certificate",
    "lost document", "expired document", "invalid document",
    # Medical
    "medical", "hospital", "injury", "illness", "surgery",
    "evacuation", "quarantine", "contagious", "pandemic",
    "pregnant", "disability", "special needs", "allergy",
    # Personal & family
    "death", "funeral", "family emergency", "family illness",
    "bereavement", "child", "elderly", "minor",
    # Safety & security
    "natural disaster", "earthquake", "flood", "hurricane", "cyclone",
    "tsunami", "wildfire", "storm", "extreme weather",
    "terrorism", "civil unrest", "war", "embassy", "stranded",
    "theft", "robbery", "assault", "kidnapping",
    "unsafe", "life threatening", "detained", "deported",
    # Travel operations
    "cancellation", "accident", "insurance claim",
    "lost ticket", "ticket issue", "booking failure",
    "denied boarding", "overbooking", "missed connection",
    "tight connection", "flight diverted", "flight delayed",
    # Vendor & supplier
    "vendor", "supplier", "hotel cancelled", "airline strike",
    "bankrupt", "insolvent", "ceased operations",
    "vendor failed", "supplier defaulted", "no show",
    # Financial emergencies
    "price change", "surcharge", "fee increase", "currency crash",
    "payment failed", "chargeback", "fraud", "refund dispute",
    "double charge", "overcharged", "deposit lost",
    "budget blown", "margin negative", "unprofitable",
    # Business impact
    "vip", "celebrity", "executive", "board member",
    "last minute", "urgent request", "emergency booking",
    "client threatening", "legal action", "lawsuit",
    "reputation risk", "bad review", "social media",
    "compensation claim", "demand letter",
    # Scope & planning failures
    "wrong destination", "wrong dates", "wrong travelers",
    "itinerary error", "miscommunication", "incorrect booking",
    "duration mismatch", "too short", "too long",
    "double booking", "overlap", "scheduling conflict",
    "missing traveler", "extra traveler", "wrong room type",
    # Internal operational
    "agent unavailable", "agent quit", "agent sick",
    "handoff needed", "unassigned critical",
    "system down", "data loss", "data corruption",
    "sync failure", "integration failure",
    "api failure", "webhook failure",
    # Legal & regulatory
    "regulatory", "compliance", "tax issue", "gst issue",
    "tds issue", "customs", "declaration",
    "audit notice", "legal notice",
    # Communication emergencies
    "client angry", "client upset", "client frustrated",
    "no response", "unreachable", "contact lost",
    "missed call", "escalated to management",
)

_SAFETY_KEYWORDS = (
    "blocker", "critical", "emergency", "severe", "life threatening",
    "unsafe", "evacuation", "warning", "extreme", "imminent",
    "fatal", "catastrophic", "irreversible", "permanent",
)


def _score_operational_risk(source: Dict[str, Any]) -> float:
    op_mode = _as_str(_first_present(
        source.get("operating_mode"),
        _get_nested(source, "raw_input.operating_mode"),
    )).lower()
    if op_mode == "emergency":
        return 100.0

    hard_blockers = _first_present(
        _get_nested(source, "decision.hard_blockers"),
        _get_nested(source, "decision.hardBlockers"),
        [],
    )
    if isinstance(hard_blockers, list):
        for hb in hard_blockers:
            hb_lower = _as_str(hb).lower().replace("_", " ").replace("-", " ")
            if any(kw in hb_lower for kw in _EMERGENCY_KEYWORDS):
                return 100.0

    safety = _get_nested(source, "safety", {})
    if isinstance(safety, dict):
        safety_flags = _first_present(
            safety.get("safety_flags"),
            safety.get("safetyFlags"),
            [],
        )
        if isinstance(safety_flags, list):
            for sf in safety_flags:
                sf_lower = _as_str(sf).lower()
                if any(kw in sf_lower for kw in _SAFETY_KEYWORDS):
                    return 100.0

        severity = _as_str(safety.get("severity") or safety.get("overall_severity")).lower()
        if severity in ("critical", "severe", "emergency"):
            return 100.0

    risk_flags = _first_present(
        _get_nested(source, "decision.risk_flags"),
        _get_nested(source, "decision.riskFlags"),
        [],
    )
    if isinstance(risk_flags, list):
        risk_text = " ".join(_as_str(r).lower() for r in risk_flags)
        if any(kw in risk_text for kw in _EMERGENCY_KEYWORDS):
            return 80.0

    escalation = _as_str(_get_nested(source, "analytics.escalation_severity")).lower()
    if escalation == "critical":
        return 80.0

    return 0.0


def _compute_days_in_stage(source: Dict[str, Any], now: Optional[datetime] = None) -> int:
    if now is None:
        now = _now()
    created = _as_str(_first_present(source.get("created_at"), source.get("createdAt")))
    if not created:
        return 0
    try:
        parsed = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return 0
    return max(0, int((now.timestamp() - parsed.timestamp()) // 86400))


def compute_urgency(source: Dict[str, Any], *, now: Optional[datetime] = None) -> Tuple[int, Dict[str, float]]:
    days = _compute_days_in_stage(source, now)
    sla_score = _score_sla_breach(days)
    dw = _as_str(_first_present(source.get("dateWindow"), source.get("date_window")))
    dep_score = _score_departure_proximity(dw, now)
    rec_score = _score_client_recency(days)
    init_score = _score_client_initiated(source)
    act_score = _score_past_due_actions(source, now)
    risk_score = _score_operational_risk(source)

    weighted = (
        sla_score * _URGENCY_WEIGHTS["sla_breach"]
        + dep_score * _URGENCY_WEIGHTS["departure_proximity"]
        + rec_score * _URGENCY_WEIGHTS["client_recency"]
        + init_score * _URGENCY_WEIGHTS["client_initiated"]
        + act_score * _URGENCY_WEIGHTS["past_due_actions"]
        + risk_score * _URGENCY_WEIGHTS["operational_risk"]
    )

    if risk_score == 100.0:
        weighted = max(weighted, 60.0)
    components = {
        "sla_breach": sla_score,
        "departure_proximity": dep_score,
        "client_recency": rec_score,
        "client_initiated": init_score,
        "past_due_actions": act_score,
        "operational_risk": risk_score,
    }
    return _clamp(weighted), components


# ---- Importance ----

def _score_revenue(value: int, *, cap: int = 50000) -> float:
    return _linear(value, 0, cap)


def _score_client_tier(source: Dict[str, Any]) -> float:
    signals = _as_str(_first_present(
        source.get("trip_priorities"),
        _get_nested(source, "raw_input.trip_priorities"),
        _get_nested(source, "extracted.facts.owner_priority_signals.value"),
    )).lower()

    urgent_words = ("urgent", "critical", "asap", "vip", "important")
    high_words = ("high", "priority", "fast")

    if any(w in signals for w in urgent_words):
        return 100.0
    if any(w in signals for w in high_words):
        return 70.0
    if signals:
        return 50.0
    return 30.0


def _score_trip_complexity(source: Dict[str, Any]) -> float:
    count = 0
    for key in ("is_multi_city", "flight_requirements", "accommodation",
                "activities", "visa_requirements"):
        val = _get_nested(source, f"extracted.facts.{key}")
        if val and val not in ([], None, False, ""):
            count += 1
    return _clamp(count * 20.0)


def _score_referral_potential(source: Dict[str, Any]) -> float:
    lead = _as_str(_first_present(
        source.get("lead_source"), _get_nested(source, "raw_input.lead_source")
    )).lower()
    if not lead:
        return 30.0
    if any(w in lead for w in ("referral", "referred", "recommend", "friend", "colleague", "word of mouth")):
        return 100.0
    if any(w in lead for w in ("repeat", "returning", "existing")):
        return 70.0
    if any(w in lead for w in ("web", "google", "search", "organic", "website", "online")):
        return 30.0
    if any(w in lead for w in ("social", "facebook", "instagram", "linkedin", "twitter")):
        return 40.0
    return 20.0


def _score_repeat_client(source: Dict[str, Any]) -> float:
    lead = _as_str(_first_present(
        source.get("lead_source"), _get_nested(source, "raw_input.lead_source")
    )).lower()
    if any(w in lead for w in ("repeat", "returning", "existing", "previous")):
        return 100.0
    return 0.0


def compute_importance(source: Dict[str, Any]) -> Tuple[int, Dict[str, float]]:
    value = _as_int(_first_present(
        source.get("value"), source.get("budget"),
        _get_nested(source, "extracted.facts.budget.value"),
    ), 0)

    rev_score = _score_revenue(value)
    tier_score = _score_client_tier(source)
    cx_score = _score_trip_complexity(source)
    ref_score = _score_referral_potential(source)
    rep_score = _score_repeat_client(source)

    weighted = (
        rev_score * _IMPORTANCE_WEIGHTS["revenue"]
        + tier_score * _IMPORTANCE_WEIGHTS["client_tier"]
        + cx_score * _IMPORTANCE_WEIGHTS["trip_complexity"]
        + ref_score * _IMPORTANCE_WEIGHTS["referral_potential"]
        + rep_score * _IMPORTANCE_WEIGHTS["repeat_client"]
    )
    components = {
        "revenue": rev_score,
        "client_tier": tier_score,
        "trip_complexity": cx_score,
        "referral_potential": ref_score,
        "repeat_client": rep_score,
    }
    return _clamp(weighted), components


# ---- Combined ----

def priority_level(urgency: int, importance: int) -> str:
    if urgency >= 80 or (urgency >= 60 and importance >= 60):
        return "critical"
    if urgency >= 60 or (urgency >= 30 and importance >= 60):
        return "high"
    if urgency >= 20 or importance >= 20:
        return "medium"
    return "low"


def combined_score(urgency: int, importance: int) -> int:
    return _clamp(urgency * 0.5 + importance * 0.5)


# ---- Top-level ----

class PriorityResult:
    __slots__ = ("urgency", "urgency_breakdown", "importance",
                 "importance_breakdown", "label", "score")

    def __init__(self, urgency: int, u_bd: Dict[str, float],
                 importance: int, i_bd: Dict[str, float]) -> None:
        self.urgency = urgency
        self.urgency_breakdown = u_bd
        self.importance = importance
        self.importance_breakdown = i_bd
        self.label = priority_level(urgency, importance)
        self.score = combined_score(urgency, importance)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "urgency": self.urgency,
            "urgencyBreakdown": self.urgency_breakdown,
            "importance": self.importance,
            "importanceBreakdown": self.importance_breakdown,
            "priority": self.label,
            "priorityScore": self.score,
        }


def score_trip(source: Dict[str, Any], *, now: Optional[datetime] = None) -> PriorityResult:
    urgency, u_bd = compute_urgency(source, now=now)
    importance, i_bd = compute_importance(source)
    return PriorityResult(urgency, u_bd, importance, i_bd)
