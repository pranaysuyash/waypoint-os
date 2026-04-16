# Discovery Gap Analysis: Configuration Management

**Date**: 2026-04-16
**Gap Register**: #16 (P2 — per-agency settings)
**Scope**: Per-agency configuration, margin policies, feature flags, brand settings, operational defaults. NOT: multi-tenant isolation (#08).

---

## 1. Executive Summary

The system has zero per-agency configuration. All budget estimates, margin targets, tone settings, operating hours, and operational defaults are hardcoded constants in `decision.py` and `strategy.py`. A 2-person boutique agency and a 50-person corporate travel firm would use identical settings. The frontend has a `SettingsPage` placeholder with a single "Save" button and no actual settings.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md` | Agency-level settings: `agency_id`, per-agency config | Docs/ |
| `DISCOVERY_GAP_DATA_PERSISTENCE` L92 | "No per-agency configuration or feature flags" | #02 deep-dive |
| `DISCOVERY_GAP_COMMUNICATION_CHANNELS` | Per-agency operating hours, channel preferences, tone settings | #03 deep-dive |
| `decision.py` L370-683 | 25+ hardcoded destination cost estimates, 20+ budget bucket ranges — all `maturity: "heuristic"` | src/ |
| `decision.py` L1484-1504 | Static `QUESTIONS` dict — no per-agency question customization | src/ |
| `strategy.py` L165-197 | Static `TONE_BY_CONFIDENCE` mapping — no per-agency tone config | src/ |
| `frontend` | `SettingsPage` component exists but is stub only | frontend/ |

### What's NOT Implemented

- No per-agency settings storage (no `agency_settings` table)
- No margin policy configuration (target margin % per component)
- No operating hours/days configuration
- No tone/brand settings per agency
- No feature flags (enable/disable specific features)
- No preferred supplier list per agency
- No default markups per component type
- No cancellation policy defaults per agency

---

## 3. Phase-In Recommendations

### Phase 1: Agency Settings Entity (P2, ~1 day, blocked by #02)

1. Create `agency_settings` table with key-value config
2. Add core settings: `target_margin_pct`, `default_currency`, `operating_hours`, `preferred_channels`
3. Wire budget feasibility to agency margin target instead of hardcoded values

```python
@dataclass
class AgencySettings:
    agency_id: str
    target_margin_pct: float = 15.0
    default_currency: str = "INR"
    operating_hours_start: str = "09:00"
    operating_hours_end: str = "21:00"
    operating_days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri", "sat"])
    preferred_channels: List[str] = field(default_factory=lambda: ["whatsapp", "email"])
    cancellation_policy_default: str = "flexible"  # "flexible" | "moderate" | "strict"
    feature_flags: dict = field(default_factory=dict)
    brand_name: str = ""
    brand_tone: str = "professional"  # "professional" | "friendly" | "casual"
```

**Acceptance**: Agency owner can set target margin to 18% and all budget estimates adjust accordingly.

### Phase 2: Feature Flags + Brand Settings (P3, ~1 day)

1. Add feature flags for enable/disable: LLM enhancement, email channel, customer portal, etc.
2. Add brand settings: name, tone, logo URL, WhatsApp template prefix
3. Build settings UI in frontend

**Acceptance**: Agency can enable/disable LLM enhancement and set their brand tone to "friendly."

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Settings storage | (a) JSONB column on agency table, (b) Separate key-value table, (c) Config file per agency | **(a) JSONB column** — flexible, queryable, one table |
| Default values | (a) Sensible defaults for Indian agencies, (b) No defaults, (c) Global config with agency overrides | **(c) Global defaults with agency overrides** — sensible base, per-agency customization |

**Out of Scope**: Multi-currency configuration (MVP is INR only), multi-language support, custom domain mapping, white-label theming.