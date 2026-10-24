"""
spine_api/services/visa_radar.py — Visa & Passport Validity Radar (IDEA-130).

HEURISTIC SCOPE (VA-02, 2026-09-09): this radar is NOT a live data service.
Visa requirements come from a small hardcoded sample registry below (7
passport x destination pairs) with a conservative fallback for unknown pairs;
passport-validity math is the only computed logic. For any pair outside the
registry, results are flagged `registry_match=False` (VA-03) so consumers can
distinguish a data hit from the fallback heuristic. Live-source integration
(Timatic/Sherpa-class) is tracked as register item VD-02.

Audits traveler passport expiry dates against destination 6-month / 3-month entry rules,
evaluates e-Visa, ESTA, ETA, and Schengen visa requirements, and alerts advisors 60 days before travel.
"""

from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class VisaCheckRequest(BaseModel):
    # No default nationality (VA-01, 2026-09-09): an omitted passport country
    # must fail validation rather than silently assume US — same abstain
    # doctrine as the AT-11 trip-requirements fix.
    passport_country: str
    destination_country: str
    passport_expiry_date: str
    travel_date: str


class VisaCheckResult(BaseModel):
    ok: bool = True
    passport_country: str
    destination_country: str
    months_validity_remaining: float
    passport_validity_compliant: bool
    requires_visa: bool
    visa_type_required: str  # NONE, ESTA, ETA, SCHENGEN, E_VISA, CONSULAR_VISA
    action_required: str
    warnings: List[str] = Field(default_factory=list)
    # FND-0339 / roadmap invariant 3: this field is REQUIRED with no default —
    # a writer who cannot say whether the corridor came from the registry or
    # from the conservative default cannot construct the result. True when
    # (passport_country, destination_country) hit the registry; False means
    # the determination is a heuristic, not data (VA-03), and the visa type
    # must be UNKNOWN_VERIFY with Timatic verification language.
    registry_match: bool


# Visa rules registry by (passport_country, destination_country)
VISA_RULES_REGISTRY: Dict[tuple, Dict[str, Any]] = {
    ("US", "FR"): {"requires_visa": False, "visa_type": "NONE", "min_months": 3},
    ("US", "GB"): {"requires_visa": True, "visa_type": "ETA", "min_months": 6},
    ("US", "JP"): {"requires_visa": False, "visa_type": "NONE", "min_months": 6},
    ("UK", "US"): {"requires_visa": True, "visa_type": "ESTA", "min_months": 6},
    ("IN", "US"): {"requires_visa": True, "visa_type": "CONSULAR_VISA", "min_months": 6},
    ("IN", "FR"): {"requires_visa": True, "visa_type": "SCHENGEN", "min_months": 6},
    ("IN", "TH"): {"requires_visa": True, "visa_type": "E_VISA", "min_months": 6},
}


def audit_visa_and_passport_validity(req: VisaCheckRequest) -> VisaCheckResult:
    """Audit passport expiry date and visa rules against destination country regulations."""
    p_country = req.passport_country.upper().strip()
    d_country = req.destination_country.upper().strip()

    p_exp_dt = datetime.fromisoformat(req.passport_expiry_date.replace("Z", "+00:00"))
    t_dt = datetime.fromisoformat(req.travel_date.replace("Z", "+00:00"))

    delta_days = (p_exp_dt - t_dt).days
    months_remaining = round(delta_days / 30.4375, 1)

    registry_match = (p_country, d_country) in VISA_RULES_REGISTRY
    rule = VISA_RULES_REGISTRY.get((p_country, d_country), {"requires_visa": True, "visa_type": "E_VISA", "min_months": 6})
    min_months = rule.get("min_months", 6)

    passport_compliant = months_remaining >= min_months
    requires_visa = rule.get("requires_visa", False)
    visa_type = rule.get("visa_type", "NONE")

    warnings: List[str] = []
    if not passport_compliant:
        warnings.append(
            f"Passport expires in {months_remaining:.1f} months. {d_country} requires minimum {min_months} months validity remaining."
        )

    if requires_visa:
        if registry_match:
            warnings.append(f"Traveler holding {p_country} passport requires {visa_type} to enter {d_country}.")
        else:
            # FND-0339 (Sim #4): a registry miss returned the conservative
            # default asserted as a determination ("requires E_VISA") —
            # identical language to a genuine registry hit. Wrong-but-confident
            # on a legal surface; disclose the miss and route to verification.
            warnings.append(
                f"No curated rule for {p_country}→{d_country} in the visa registry: the "
                f"visa determination is a conservative default (assume a visa is required) — "
                f"verify the entry visa type with the airline/Timatic before booking."
            )

    if not passport_compliant:
        action = "URGENT: Expedite passport renewal immediately before travel"
    elif requires_visa and registry_match:
        action = f"Apply for {visa_type} prior to departure"
    elif requires_visa:
        action = "Visa likely required (conservative default) — verify entry visa type with the airline/Timatic"
    else:
        action = "No visa action required. Passport validity compliant."

    if not registry_match and visa_type != "NONE":
        visa_type = "UNKNOWN_VERIFY"

    return VisaCheckResult(
        ok=True,
        passport_country=p_country,
        destination_country=d_country,
        months_validity_remaining=months_remaining,
        passport_validity_compliant=passport_compliant,
        requires_visa=requires_visa,
        visa_type_required=visa_type,
        action_required=action,
        warnings=warnings,
        registry_match=registry_match,
    )
