"""fees.margin_policy — dimensioned, versioned margin-policy resolution.

Owner-ratified design (2026-09-14, blueprint Addendum 12): margins are a
negotiated commercial outcome, so the policy parameters are configurable per
dimension — agency → vendor (id or class) → location → category → value
band — with longest-prefix (most-specific) resolution and fail-safe
fallthrough to platform defaults.

Exploration record (options considered):
  A. Global-only literals (status quo) — rejected: ignores negotiated
     reality; wrong the day an agency signs its own vendor deal.
  B. Free-form per-quote margins — rejected: ungovernable; pricing authority
     must stay with MarginOptimizer, floors with the signed-off table.
  C. Dimensioned versioned rules table with specificity resolution
     (THIS) — governed, audited, and doubles as the "versioned rules table
     with sign-off" the ADR-008 council made a precondition for the floor
     gate (FND-0268 amendment).

Two-sided covenant (Addendum 11): negotiated vendor prices are COST
(net_rate_usd via adapters, cost_basis provenance); margin policy is PRICE
SIDE only (floors, markups, fee, take-rate clamp bounds).

Governance: platform defaults are platform-owned and fail-safe; agency
overrides live on the agency's settings record (AgencySettingsStore — one
store, tenant-scoped, audited on change via its save path). Evaluation
always records which rule version + rule id produced the numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PLATFORM_RULESET_VERSION = "platform-v1-2026-09-14"

_WILDCARD = "*"


@dataclass(slots=True)
class MarginPolicyRule:
    """One policy row. Any dimension set to '*' is a wildcard (default)."""

    rule_id: str
    category: str = _WILDCARD
    vendor_id: str = _WILDCARD
    vendor_class: str = _WILDCARD
    location: str = _WILDCARD
    agency_id: str = _WILDCARD
    min_package_value_usd: float = 0.0
    max_package_value_usd: float = float("inf")
    markup_pct: float = 0.14
    min_margin_floor_pct: float = 0.08
    min_margin_floor_usd: float = 250.0
    flat_planning_fee_usd: float = 150.0
    take_rate_clamp_min: float = 0.10
    take_rate_clamp_max: float = 0.28
    ruleset_version: str = PLATFORM_RULESET_VERSION
    created_by: str = "platform"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def specificity(self) -> float:
        """Higher = more specific. agency (4) > vendor_id (3) >
        vendor_class (2) > location (1) > category (0.5). Value band is a
        filter, not a specificity dimension."""
        score = 0.0
        if self.agency_id != _WILDCARD:
            score += 4
        if self.vendor_id != _WILDCARD:
            score += 3
        if self.vendor_class != _WILDCARD:
            score += 2
        if self.location != _WILDCARD:
            score += 1
        if self.category != _WILDCARD:
            score += 0.5
        return score


# Platform defaults: seeded 1:1 from fee_matrix's current literals so default
# behavior is UNCHANGED by this module's introduction. New platform rulesets
# are additive versions, never in-place edits.
PLATFORM_DEFAULT_RULES: List[MarginPolicyRule] = [
    MarginPolicyRule(
        rule_id="platform.custom_tour.0-10k",
        category="custom_tour",
        min_package_value_usd=0.0,
        max_package_value_usd=10000.0,
        markup_pct=0.14,
        min_margin_floor_pct=0.08,
        min_margin_floor_usd=250.0,
        flat_planning_fee_usd=150.0,
    ),
    MarginPolicyRule(
        rule_id="platform.custom_tour.10k-100k",
        category="custom_tour",
        min_package_value_usd=10000.0,
        max_package_value_usd=100000.0,
        markup_pct=0.11,
        min_margin_floor_pct=0.08,
        min_margin_floor_usd=1200.0,
        flat_planning_fee_usd=250.0,
    ),
    MarginPolicyRule(
        rule_id="platform.flights.standalone",
        category="flights",
        min_package_value_usd=0.0,
        max_package_value_usd=50000.0,
        markup_pct=0.03,
        min_margin_floor_pct=0.08,
        min_margin_floor_usd=50.0,
        flat_planning_fee_usd=50.0,
    ),
]


def rules_from_dicts(datas: List[Dict[str, Any]], agency_id: str) -> List[MarginPolicyRule]:
    """Hydrate override rows (e.g., from AgencySettings.margin_policy_overrides)
    scoped to their agency."""
    known = {f.name for f in fields(MarginPolicyRule)}
    rules: List[MarginPolicyRule] = []
    for data in datas or []:
        scoped = {k: v for k, v in data.items() if k in known}
        scoped["agency_id"] = agency_id
        rules.append(MarginPolicyRule(**scoped))
    return rules


def resolve_margin_policy(
    *,
    category: str = "custom_tour",
    package_value_usd: float = 0.0,
    agency_id: Optional[str] = None,
    vendor_id: Optional[str] = None,
    vendor_class: Optional[str] = None,
    location: Optional[str] = None,
    override_rules: Optional[List[MarginPolicyRule]] = None,
) -> MarginPolicyRule:
    """Longest-prefix resolution: most specific rule wins (atomic — a rule's
    ruleset version never mixes with another's). Fail-safe: no match → the
    most specific platform default for the category/value."""
    candidates: List[MarginPolicyRule] = list(PLATFORM_DEFAULT_RULES)
    if override_rules:
        candidates.extend(override_rules)

    agency_token = agency_id or _WILDCARD
    matching = [
        r for r in candidates
        if r.agency_id in (_WILDCARD, agency_token)
        and r.vendor_id in (_WILDCARD, vendor_id or _WILDCARD)
        and r.vendor_class in (_WILDCARD, vendor_class or _WILDCARD)
        and r.location in (_WILDCARD, location or _WILDCARD)
        and r.category in (_WILDCARD, category)
        and r.min_package_value_usd <= package_value_usd < r.max_package_value_usd
    ]
    if not matching:
        matching = [
            r for r in PLATFORM_DEFAULT_RULES
            if r.category in (_WILDCARD, category)
            and r.min_package_value_usd <= package_value_usd < r.max_package_value_usd
        ] or PLATFORM_DEFAULT_RULES
    return max(matching, key=lambda r: (r.specificity(), r.ruleset_version))


def applied_policy_provenance(rule: MarginPolicyRule) -> Dict[str, Any]:
    """Provenance block for evaluations: which rule + version produced the
    numbers (the applied_rule_id hook fee_matrix already emits)."""
    return {
        "margin_policy_rule_id": rule.rule_id,
        "margin_policy_version": rule.ruleset_version,
        "margin_policy_specificity": rule.specificity(),
    }
