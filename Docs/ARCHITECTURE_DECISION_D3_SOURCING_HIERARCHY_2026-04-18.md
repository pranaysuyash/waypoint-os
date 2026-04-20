# Architecture Decision: D3 — Sourcing Hierarchy Configurability

**Date**: 2026-04-18
**Status**: Decision document — contract designed, implementation blocked on Gap #01
**Source**: `Docs/DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` Thread 3 ("Sourcing Hierarchy — Fixed or Configurable?")
**Cross-references**:
- `Docs/Sourcing_And_Decision_Policy.md` (4-tier hierarchy definition, wasted spend rule)
- `Docs/PRODUCT_VISION_AND_MODEL.md` L35 ("best acceptable option within preferred supply chain")
- `Docs/DATA_MODEL_AND_TAXONOMY.md` L27-31 (planning route brackets: `package_suitable`, `custom_supplier`, `network_assisted`, `open_market`)
- `Docs/VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md` (Gap #01 — zero production sourcing logic)
- `Docs/V02_GOVERNING_PRINCIPLES.md` L14-21 (layer ownership)
- `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md` (autonomy gate connection)
- `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` (suitability data trust connection)
- `Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md` (audit commercial rules connection)
- `src/intake/extractors.py` L1209-1220 (sourcing_path stub — always returns `open_market` or `network`, confidence 0.3)
- `src/intake/validation.py` L32-33 (`sourcing_path`, `preferred_supplier_available` in derived_signals set)

---

## The Problem

The 4-tier sourcing hierarchy is the agency's competitive advantage:

1. **Internal Standard Packages** — high-conversion, operationally familiar bundles
2. **Preferred Supplier Inventory** — contracted partners with known reliability and margins
3. **Network/Consortium Inventory** — access via larger agency networks/DMCs
4. **Open Market** — last resort for specific brand requests or niche needs

This hierarchy is documented across 98 files (`VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md` §1). It appears in the product vision, the thesis, the data model, the spec, the UX dashboards, and the persona scenarios. It is the #1 differentiator: "the system plans the way YOUR agency plans."

**Zero production logic exists.** The current implementation (`src/intake/extractors.py` L1209-1220) is a stub that always returns `open_market` or `network` with confidence 0.3 and an explicit note: `"Stub — enrich with internal package lookup and preferred supplier data"`.

### What the Thesis Deep Dive Thread 3 Identified

The hierarchy is specified as fixed (Internal → Preferred → Network → Open). But for the system to be a per-agency workspace, the hierarchy must be configurable:

| Aspect | Fixed (Current Docs) | Configurable (Production Target) |
|--------|---------------------|----------------------------------|
| Hierarchy order | Internal → Preferred → Network → Open | Agency defines own priority order |
| Margin thresholds | Not implemented | Agency sets minimum margin per tier |
| Supplier blacklist/whitelist | Not modeled | Agency marks specific vendors as preferred/blocked |
| "Widen search" trigger | "Unless explicitly asked" (`PRODUCT_VISION_AND_MODEL.md` L35) | Agency sets rules: e.g., "always check open market for flights" |

---

## Decision: Per-Agency `SourcingPolicy` Config Object

### Core Principle

Sourcing is the agency's competitive advantage. The system must plan the way **their** agency plans — not impose a generic hierarchy. The `SourcingPolicy` is a per-agency config that drives sourcing behavior, analogous to `AgencyAutonomyPolicy` (D1) and `AgencySuitabilityPolicy` (D4).

### Contract

```python
@dataclass
class SourcingPolicy:
    """Per-agency sourcing hierarchy configuration.
    
    Drives how options are discovered, ranked, and presented.
    This is config, not code branches — the sourcing engine reads this
    policy to determine search order, margin gates, and supplier preferences.
    """
    agency_id: str

    # ── Hierarchy Priority ──
    # Order determines search sequence. Agency can reorder.
    # System searches tiers in this order, stopping when acceptable options found
    # (unless auto_widen_on_no_match is True, in which case it falls through).
    tier_priority: List[Literal[
        "internal_package", "preferred_supplier", "network_consortium", "open_market"
    ]] = field(default_factory=lambda: [
        "internal_package", "preferred_supplier", "network_consortium", "open_market"
    ])

    # ── Margin Floors ──
    # Per-tier minimum acceptable margin %.
    # If a sourcing option from a tier doesn't meet the floor, it's flagged
    # (not excluded — agency can override with logged rationale).
    margin_floors: Dict[str, float] = field(default_factory=lambda: {
        "internal_package": 0.15,
        "preferred_supplier": 0.10,
        "network_consortium": 0.08,
        "open_market": 0.05,
    })

    # ── Category-Level Tier Overrides ──
    # Override the default tier_priority for specific service categories.
    # e.g., "always check open_market for flights" regardless of hierarchy.
    # Key = service category, Value = tier list for that category.
    category_tier_overrides: Dict[str, List[str]] = field(default_factory=dict)
    # Example: {"flights": ["open_market", "network_consortium", "preferred_supplier"]}

    # ── Supplier Preferences ──
    preferred_supplier_ids: List[str] = field(default_factory=list)
    blocked_supplier_ids: List[str] = field(default_factory=list)

    # ── Widen Search Behavior ──
    # When no acceptable option found in current tier:
    auto_widen_on_no_match: bool = True    # fall through to next tier automatically
    widen_requires_approval: bool = False   # if True, agent must approve before widening
    # widen_requires_approval connects to D1 AgencyAutonomyPolicy —
    # when True, widening triggers a "review" gate in the autonomy policy.
```

### Why Per-Agency (Not Per-Agent, Not Per-Trip)

Same reasoning as D1 (`ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`):

- **Not per-agent**: The agency owner decides sourcing strategy for the business. A junior agent doesn't get to skip preferred suppliers because it's faster.
- **Not per-trip**: Trip-level sourcing overrides create inconsistency. Category-level overrides (`category_tier_overrides`) handle the real use case ("flights are always open market").
- **Future per-trip layer**: If needed later, a trip-level `sourcing_hints` field can override specific tiers for specific trips — but this is additive, not needed now.

### Safety Invariants

1. **Margin floors are advisory, not hard blocks.** The system flags options below the margin floor but doesn't hide them. The agent can override with logged rationale (feeds D5 override learning). Hiding options silently would erode trust — "why didn't it show me this hotel?"
2. **Blocked suppliers are hard blocks.** If a supplier is in `blocked_supplier_ids`, the system never surfaces options from them. No override possible at the agent level — only the agency owner can unblock.
3. **Tier order is a search sequence, not an exclusion rule.** Setting `tier_priority = ["preferred_supplier", "open_market"]` means "search preferred first, then open market." It does NOT mean internal packages are excluded — it means they're not actively searched. If an internal package matches opportunistically, it's still surfaced.

### Where It Lives Architecturally

Per `V02_GOVERNING_PRINCIPLES.md` layer ownership:

- **NB02** (judgment/routing) reads `SourcingPolicy` to determine sourcing path and flag margin risks
- **Future sourcing engine** (Stage 3 — option generation) uses `SourcingPolicy` to drive actual supplier queries
- **NB03** (session behavior) presents sourcing results with appropriate framing per tier

The `SourcingPolicy` sits alongside `AgencyAutonomyPolicy` (D1) and `AgencySuitabilityPolicy` (D4) as agency-level configuration. All three are read by NB02 but not owned by NB02 — they're agency config.

```
Agency Configuration Layer
├── AgencyAutonomyPolicy (D1)  — what gates does the system enforce?
├── SourcingPolicy (D3)        — how does the system find options?
└── AgencySuitabilityPolicy (D4) — how does the system evaluate fit?
         ↓
NB02 (judgment) reads all three to produce DecisionResult
         ↓
NB03 (session) reads DecisionResult to determine presentation
```

---

## Connection to Existing Code

### Current State (Stub)

`src/intake/extractors.py` L1209-1220:
```python
# sourcing_path (stub)
if "destination_candidates" in packet.facts:
    default_path = "open_market"
    if "owner_constraints" in packet.facts:
        default_path = "network"
    packet.set_derived_signal("sourcing_path", self._make_slot(
        default_path, 0.3, AuthorityLevel.DERIVED_SIGNAL,
        "Stub — enrich with internal package lookup and preferred supplier data",
        "derived", extraction_mode="derived", maturity="stub",
        notes="Stub signal — no real supplier data available yet",
    ))
```

This stub is correct in shape — it produces a `sourcing_path` derived signal. When `SourcingPolicy` is implemented, this stub gets replaced by policy-driven logic:

1. Read `SourcingPolicy` for the agency
2. Check `category_tier_overrides` for the trip's service categories
3. Walk `tier_priority` in order, checking supplier availability per tier
4. Set `sourcing_path` to the first tier with available options
5. If no tier has options and `auto_widen_on_no_match` is True, record that widening occurred
6. If `widen_requires_approval` is True, set `decision_state` to trigger review gate (D1 connection)

### Planning Route Brackets

`DATA_MODEL_AND_TAXONOMY.md` L27-31 defines planning route brackets:
```
- package_suitable    → Internal Standard Packages
- custom_supplier     → Preferred Supplier Inventory
- network_assisted    → Network/Consortium
- open_market         → Last resort
```

These map 1:1 to `SourcingPolicy.tier_priority` entries:
| Taxonomy Bracket | SourcingPolicy Tier |
|-----------------|---------------------|
| `package_suitable` | `internal_package` |
| `custom_supplier` | `preferred_supplier` |
| `network_assisted` | `network_consortium` |
| `open_market` | `open_market` |

The bracket assignment in NB02 will be driven by `SourcingPolicy` tier resolution, not hardcoded logic.

---

## Cross-Decision Connections

### D1 (Autonomy Gradient)

`widen_requires_approval` maps directly to the autonomy gate. When the system needs to widen search beyond the agency's preferred tiers:
- `widen_requires_approval = False` → system widens automatically, logs the widening
- `widen_requires_approval = True` → system queues for agent approval before widening, using D1's `AgencyAutonomyPolicy` gate mechanism

### D4 (Suitability)

Preferred suppliers provide higher-trust activity data. When `ActivityCatalogProvider` (D4 parent doc) resolves activities:
- Activities from `preferred_supplier` tier carry higher `source_confidence` than `open_market` activities
- This feeds Tier 3 LLM scorer trigger conditions (D4 addendum) — low source confidence from open market suppliers may trigger LLM validation

### D5 (Override Learning — Pending)

Agent overrides on sourcing decisions feed learning:
- Agent consistently picks open market over preferred supplier for a specific destination → signal that preferred supplier quality is poor for that destination
- Agent consistently overrides margin floor flags → signal that floor is set too tight
- Override patterns feed `SourcingPolicy` refinement suggestions (same adaptive pattern as D1 autonomy)

### D6 (Audit)

Commercial audit rules verify sourcing compliance:
- "Did this trip use the preferred sourcing hierarchy?" — compares actual sourcing path against `SourcingPolicy.tier_priority`
- "Is the margin above the floor?" — compares actual margin against `SourcingPolicy.margin_floors`
- These become `gating` category audit rules once supplier data exists (D6 eval suite manifest)

---

## Implementation Blocking: Gap #01

Implementation of `SourcingPolicy` is strictly gated on Gap #01 (Vendor/Cost Tracking):

| What's Needed | Gap #01 Component | Status |
|--------------|-------------------|--------|
| Supplier database | `suppliers` table with destination coverage, commission bands, reliability scores | ❌ No schema, no data |
| Internal packages | Package template system with cost basis and margin | ❌ No template system |
| Margin calculation | Cost basis + markup → margin %, tracked per component | ❌ Budget is a raw number, no cost decomposition |
| Network/consortium data | Consortium membership, negotiated rates, volume commitments | ❌ Not modeled |
| Preferred supplier matching | Destination × budget tier × category → supplier ranking | ❌ Always returns `preferred_supplier_available: false` |

**Per `VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md` §1**: "The system can discover trips but cannot determine if they are profitable, which suppliers to use, or whether the agency should pursue them."

The `SourcingPolicy` contract is the deliverable now. The implementation layers onto Gap #01 data models when they ship.

---

## Open Questions (For Future Resolution)

### OQ-1: Per-Category Margin Floors

The current contract has margin floors per tier only (`internal_package: 0.15`, `preferred_supplier: 0.10`, etc.). In practice, margins vary significantly by service category:
- Hotels: 15-20% commission typical
- Flights: 1-3% commission typical
- Activities: 20-30% commission typical
- Transfers: 10-15% typical

Should the contract support `tier × category → margin_floor`? E.g., "10% minimum on hotels from preferred suppliers, 2% minimum on flights from open market."

**Current stance**: Per-tier margin floors are the starting shape. Per-category refinement is an evolution — add a `category_margin_floors: Dict[str, Dict[str, float]]` field when real margin data from the pilot reveals whether per-tier floors are sufficient or whether category-level granularity is needed. The contract shape allows this extension without breaking existing fields.

### OQ-2: Supplier Preference Scoping

`preferred_supplier_ids` and `blocked_supplier_ids` are flat lists. Agencies have destination-specific and category-specific supplier relationships — "use Supplier X for Bali hotels, Supplier Y for European transfers."

Should preferences be scoped by destination/category from the start?

**Current stance**: Flat lists are the starting shape. Scoped preferences are an evolution — replace flat `List[str]` with a `List[SupplierPreference]` where `SupplierPreference` has `supplier_id`, `scope_destinations: Optional[List[str]]`, `scope_categories: Optional[List[str]]`. This is additive — flat list behavior is equivalent to "all destinations, all categories." Design the scoped contract when real supplier data from Gap #01 reveals preference patterns.

### OQ-3: Network/Consortium Tier Semantics

The `network_consortium` tier implies the agency is part of a buying group with negotiated rates and volume commitments. Is this just another supplier tier in the priority list, or does it have special semantics (e.g., volume-based pricing tiers, consortium membership verification, shared inventory pools)?

**Current stance**: Treat as another tier in the priority list for now. Special semantics emerge from pilot agency's actual consortium relationships. If the pilot agency isn't part of a consortium, this tier is effectively empty — which is fine, the system skips empty tiers.

---

## Remaining Open Items (Updated from D1)

| # | Decision | Status | Next Step |
|---|----------|--------|-----------|
| D1 | Autonomy gradient | ✅ Core decided. Adaptive autonomy pending deep dive. | Deep dive customer+trip classification when pilot data available |
| D2 | Free engine target persona | ✅ Decided. Shared pipeline, empowerment framing. | Implementation sequenced by D6 eval precision gates |
| D3 | Sourcing hierarchy configurability | ✅ Contract decided. Implementation blocked on Gap #01. | Implement with Gap #01 vendor/supplier models |
| D4 | Suitability depth + sub-decisions | ✅ Decided. Three-tier scoring architecture. | Migration Steps 1-5 from parent architecture doc |
| D5 | Override learning | ⬜ Open | Next discussion — feedback bus connecting D1, D3, D4, Gap #06 |
| D6 | Audit eval suite | ✅ Decided. Manifest-driven, fixture-tiered. | Fixture authoring + eval runner implementation |
| — | Plugin system | ⬜ Draft exists (`PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md`) | Architecture decision needed |
| — | Customer+trip classification | ⬜ Identified during D1 | Separate deep dive thread |

---

*Sourcing is the agency's competitive advantage. The `SourcingPolicy` contract ensures the system plans the way each agency plans — their hierarchy, their margins, their suppliers. The contract is designed configurable from day one. Implementation is blocked on Gap #01 (vendor/supplier/cost/margin data models), which is the honest current state: zero production sourcing logic exists. The contract is the deliverable now.*
