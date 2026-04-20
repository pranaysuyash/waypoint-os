# Architecture Decision: D5 — Override Learning (Feedback Bus)

**Date**: 2026-04-18
**Status**: Decision document — contract designed, implementation phased by persistence + lifecycle dependencies
**Source**: `Docs/DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` Thread 1 (Override Dignity), D1 (Adaptive Autonomy)
**Cross-references**:
- `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md` (adaptive autonomy, `learn_from_overrides`, `TripClassification`)
- `Docs/ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY_2026-04-18.md` (sourcing overrides → `SourcingPolicy` refinement)
- `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` (`TravelerMemorySnapshot`, `AgencySuitabilityPolicy`)
- `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` (three-tier suitability scoring, LLM cache → rule graduation)
- `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` (`LLMCacheable` protocol, `PromotionCandidate`, cache → rule graduation)
- `Docs/DISCOVERY_GAP_CUSTOMER_LIFECYCLE_2026-04-16.md` (Gap #06 — customer entity, lifecycle state machine, cross-trip memory)
- `Docs/DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md` (Gap #02 — session persistence, event storage)
- `src/decision/hybrid_engine.py` (cache → rule → LLM → cache pattern, `success_rate` tracking, `CachedDecision`)
- `src/intake/packet_models.py` L37 (`AuthorityLevel.MANUAL_OVERRIDE`), L315-322 (`_emit_event` audit trail)
- `src/intake/packet_models.py` L185-231 (`LifecycleInfo` — 16-state lifecycle, engagement metrics)

---

## The Problem

The system exercises judgment across three domains:
- **Decision gating** (D1): proceed/review/block verdicts per `decision_state`
- **Suitability scoring** (D4): per-person activity fit, tour-context coherence
- **Sourcing ranking** (D3): supplier tier selection, margin evaluation

When the agent disagrees with the system and overrides, that disagreement is a **learning signal**. Today, overrides are either not tracked at all (suitability, sourcing don't exist yet) or tracked only as event trail entries (`packet_models.py` L315-322) with no feedback loop.

D5 is not a standalone feature — it's the **feedback bus** that makes D1, D3, and D4 compound over time. Without it, those policies are static config forever. With it, the system learns the agency's real preferences from observed behavior.

### The Thesis Deep Dive Framing (Thread 1)

> "Override dignity: When an agent overrides the system, does the system remember? → Yes, feeds learning loop."

The key insight from D1 discussion: the owner said autonomy should be fine-tuned based on learning. Override patterns are the primary training signal for that learning.

---

## Decision: Three Override Categories, Three Learning Destinations

### Override Taxonomy

| Override Type | What Happens | Learning Destination | Example |
|---|---|---|---|
| **Decision override** | Agent changes system's `decision_state` verdict | `AgencyAutonomyPolicy` adaptive layer (D1) + `TripClassification` training | System says `STOP_NEEDS_REVIEW`, agent overrides to proceed — "I know this client, it's fine" |
| **Suitability override** | Agent says "system is wrong about this person/activity" | `TravelerMemorySnapshot` (D4) + per-traveler learned capabilities | System flags elderly parent can't do the hike — agent says "she's very fit, she did Kilimanjaro last year" |
| **Sourcing override** | Agent picks a different tier than the policy recommended | `SourcingPolicy` refinement (D3) + supplier quality signals | System recommends preferred supplier, agent picks open market — "their Bali properties are terrible right now" |

### Why Three Categories (Not One Generic Override)

Each category has different:
- **Learning destinations** — decision overrides feed autonomy policy; suitability overrides feed traveler memory; sourcing overrides feed supplier quality
- **Outcome signals** — decision outcomes take days/weeks; suitability outcomes emerge post-activity; sourcing outcomes emerge post-booking
- **Override authority** — suitability overrides may be per-traveler knowledge; sourcing overrides may be per-destination knowledge; decision overrides are judgment calls
- **Rationale patterns** — "client knowledge" is a suitability rationale; "supplier issue" is a sourcing rationale; "system too conservative" is a decision rationale

A generic override contract would lose these distinctions and produce noise in the learning loop.

---

## Core Contract

### OverrideEvent

```python
@dataclass
class OverrideEvent:
    """Structured record of an agent overriding a system verdict.
    
    Every override MUST include rationale — override without rationale
    is noise that pollutes the learning loop. The rationale_tags provide
    structured classification for pattern detection.
    """
    override_id: str                   # unique ID
    timestamp: str                     # ISO 8601
    agent_id: str                      # who overrode
    agency_id: str                     # agency context (for agency-level learning)
    trip_id: str                       # trip context

    # ── What was overridden ──
    override_category: Literal["decision", "suitability", "sourcing"]
    system_verdict: Dict[str, Any]     # what the system recommended
    agent_verdict: Dict[str, Any]      # what the agent chose instead

    # ── Why (required — non-negotiable) ──
    rationale: str                     # free-text explanation
    rationale_tags: List[str]          # structured tags for pattern detection

    # ── Context for learning ──
    # Which fields are populated depends on override_category
    traveler_id: Optional[str] = None          # suitability overrides → links to TravelerMemory
    activity_id: Optional[str] = None          # suitability overrides → which activity was misjudged
    destination_key: Optional[str] = None      # sourcing overrides → destination context
    supplier_id: Optional[str] = None          # sourcing overrides → which supplier was rejected/chosen
    decision_state: Optional[str] = None       # decision overrides → which decision_state was overridden
    trip_classification: Optional[str] = None  # decision overrides → routine/moderate/complex/novel

    # ── Outcome tracking (filled in post-hoc) ──
    outcome_recorded: bool = False
    outcome_positive: Optional[bool] = None    # did the override turn out well?
    outcome_notes: Optional[str] = None        # what happened
    outcome_recorded_at: Optional[str] = None  # when outcome was recorded
```

### Rationale Tags (Structured Vocabulary)

Override rationale is free-text for human readability, but `rationale_tags` provide structured classification for pattern detection:

**Decision override tags:**
- `client_knowledge` — "I know this client, they're fine with this"
- `system_too_conservative` — "The system flagged this but it's standard for this trip type"
- `system_too_aggressive` — "The system auto-proceeded but this needs review"
- `urgency_context` — "Client needs an answer today, can't wait for full review"
- `system_error` — "The system's analysis is factually wrong"

**Suitability override tags:**
- `traveler_capability` — "This person is more capable than their age suggests"
- `traveler_limitation` — "This person has a condition the system doesn't know about"
- `activity_misjudged` — "The system scored this activity incorrectly"
- `local_knowledge` — "I've done this trip, the hike is easier than it sounds"
- `preference_override` — "Client specifically requested this despite the warning"

**Sourcing override tags:**
- `supplier_quality_issue` — "This supplier's quality has dropped recently"
- `supplier_relationship` — "We have a special deal with this supplier"
- `price_better_elsewhere` — "Open market has significantly better pricing right now"
- `availability_issue` — "Preferred supplier is sold out for these dates"
- `client_brand_preference` — "Client specifically wants this brand/property"

The tag vocabulary grows over time as override patterns emerge. New tags are added via the standard D6 eval manifest `planned → shadow → gating` progression — a tag must appear in `N` overrides before it becomes a standard tag.

---

## Learning Mechanism

### Pattern: Reuse Existing Cache → Rule Graduation

The learning mechanism reuses the proven pattern from `src/decision/hybrid_engine.py`:

```
Override recorded → aggregated by (category, context_hash)
                  → frequency tracking (how often does this override pattern occur?)
                  → success_rate tracking (when outcome data available)
                  → threshold check: use_count > N AND success_rate > threshold
                  → PromotionCandidate (per ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06)
                  → owner approves → policy adjustment
```

This is the same `CachedDecision.success_rate` + `PromotionCandidate` pattern from the LLM cache architecture, applied to override patterns instead of LLM outputs.

### Per-Category Learning Loops

**Decision override loop → D1 adaptive autonomy:**

```
Agent consistently overrides STOP_NEEDS_REVIEW for "couple + Bali + mid-budget" trips
  → Override pattern aggregated: (decision, "couple_bali_midbudget") use_count=47/50 (94%)
  → System generates suggestion: "Auto-proceed for this trip classification?"
  → Agency owner approves → AgencyAutonomyPolicy loosens for that TripClassification
  → System tracks: do auto-proceeded trips get post-hoc corrections? If yes → tighten back
```

**Suitability override loop → D4 traveler memory:**

```
Agent overrides "elderly can't do the hike" for traveler_id="traveler_042"
  → Override recorded with rationale_tag="traveler_capability"
  → TravelerMemorySnapshot updated: traveler_042.physical_capability_override = "high_fitness"
  → Next trip for traveler_042: suitability scorer reads memory, adjusts scores upward
  → If override was wrong (complaint post-trip) → memory entry flagged, reverts
```

**Sourcing override loop → D3 supplier quality:**

```
Multiple agents override preferred_supplier for Bali hotels, tag="supplier_quality_issue"
  → Override pattern aggregated: (sourcing, "preferred_supplier_X_bali") use_count=12
  → System surfaces to owner: "Supplier X Bali properties overridden 12 times in 30 days"
  → Owner investigates → moves supplier to blocked or adjusts SourcingPolicy
```

### Critical: Suggestions, Not Auto-Adjustments

**Override patterns generate suggestions. They do NOT auto-adjust policy.**

The agency owner approves or rejects policy changes. This is the same principle as D1 (autonomy gradient): the system proposes, the owner disposes. Auto-adjustment from override patterns would mean agents can effectively rewrite agency policy by consistently overriding — that's a governance violation.

The one exception: **per-traveler suitability memory** can update automatically from overrides, because it's scoped to one person's capabilities, not agency-wide policy. If agent says "this elderly person is very fit," that's traveler-specific knowledge, not a policy change.

---

## Outcome Tracking: The Feedback Quality Problem

### The Problem

The system can record override *frequency* immediately. But it can't assess override *quality* without outcome data — and outcomes arrive days to weeks later.

| Override Type | Outcome Signal | Latency | Source |
|---|---|---|---|
| Decision override | Trip proceeded successfully? Client satisfied? | Days to weeks | Post-trip feedback, complaint/compliment events |
| Suitability override | Person managed the activity? Any complaints? | Days (post-activity) | In-trip feedback, post-trip survey, complaint events |
| Sourcing override | Supplier reliable? Margin preserved? | Days to weeks (post-booking) | Booking confirmation, post-trip supplier rating |

### Two-Phase Learning (Phased by Outcome Availability)

**Phase 1: Frequency-based learning (ships with persistence)**
- Count overrides per pattern
- Detect consistent patterns (same override type × same context)
- Surface frequency reports to agency owner
- No quality assessment — just "agents override this a lot"
- Useful for: identifying overly conservative system settings, detecting consistent mismatches

**Phase 2: Outcome-based learning (ships with customer lifecycle)**
- Track whether overrides led to good or bad outcomes
- Compute `success_rate` per override pattern
- Quality-informed suggestions: "agents override X, and it works 94% of the time → loosen"
- Also: "agents override Y, but it fails 40% of the time → maybe the system was right"

Phase 1 is valuable on its own — an agency owner seeing "agents override suitability warnings 80% of the time" knows the system is too conservative, even without outcome data. Phase 2 adds confidence.

---

## Where It Lives Architecturally

### Event Recording

Override events extend the existing `_emit_event` mechanism in `CanonicalPacket` (`packet_models.py` L315-322):

```python
# Example: recording a decision override
packet._emit_event("agent_override", {
    "override_category": "decision",
    "system_verdict": {"decision_state": "STOP_NEEDS_REVIEW", "reasons": [...]},
    "agent_verdict": {"decision_state": "PROCEED_TRAVELER_SAFE"},
    "rationale": "Known repeat client, standard Bali trip",
    "rationale_tags": ["client_knowledge"],
    "traveler_id": "traveler_042",
})
```

The `OverrideEvent` dataclass is the structured form that gets persisted (when persistence exists). The packet event trail is the immediate audit record.

### Layer Ownership

Per `V02_GOVERNING_PRINCIPLES.md`:

| Component | Layer | Rationale |
|-----------|-------|-----------|
| Override event recording | NB02/NB03 boundary | Override happens when agent interacts with system verdict — same boundary as D1 autonomy gate |
| Override persistence | Persistence layer (Gap #02) | Events must survive sessions |
| Pattern aggregation | Analytics/learning layer | Aggregation over time is not per-trip judgment |
| Suggestion generation | Agency config layer | Policy suggestions live alongside `AgencyAutonomyPolicy`, `SourcingPolicy`, `AgencySuitabilityPolicy` |
| Owner approval UX | Frontend workspace | Owner reviews and approves/rejects suggestions |

### Connection to Existing `AuthorityLevel.MANUAL_OVERRIDE`

`AuthorityLevel.MANUAL_OVERRIDE` (`packet_models.py` L37) is already the highest authority level. When an agent overrides:
1. The overridden slot's `authority_level` becomes `MANUAL_OVERRIDE`
2. The `_emit_event` records the override in the packet's event trail
3. The `OverrideEvent` dataclass captures the structured learning signal
4. The persistence layer stores the `OverrideEvent` for pattern aggregation

Step 1-2 already work. Steps 3-4 are the D5 additions.

---

## Cross-Decision Connections (Complete Map)

```
D5 (Override Learning) — The Feedback Bus
│
├── D1 (Autonomy) ←── Decision overrides
│   ├── Override patterns feed TripClassification training
│   ├── High pass-through rate → suggest loosening autonomy for that classification
│   ├── Post-hoc corrections on auto-proceeded trips → suggest tightening
│   └── Owner approves policy changes via autonomy settings surface
│
├── D3 (Sourcing) ←── Sourcing overrides
│   ├── Supplier quality signals from "supplier_quality_issue" tags
│   ├── Category-level override patterns → suggest category_tier_overrides
│   ├── Margin floor override frequency → suggest floor adjustment
│   └── Owner reviews supplier quality dashboard
│
├── D4 (Suitability) ←── Suitability overrides
│   ├── Per-traveler capability overrides → TravelerMemorySnapshot (auto-updates)
│   ├── Activity scoring overrides → activity catalog refinement signals
│   ├── Tour-context overrides → Tier 2 sequence rule calibration
│   └── Agency-level suitability weight adjustments → AgencySuitabilityPolicy
│
├── D6 (Audit) ←── Override accuracy measurement
│   ├── Audit eval suite tracks: do overridden verdicts match ground truth?
│   ├── False positive rate reduction: if agents consistently override a finding → finding is wrong
│   └── Audit rule refinement fed by override patterns on audit-specific findings
│
└── Gap #06 (Customer Lifecycle) ←── Outcome tracking
    ├── Post-trip feedback closes the override outcome loop
    ├── Customer satisfaction signals validate/invalidate overrides
    └── Cross-trip override patterns per customer → TravelerMemory enrichment
```

---

## Implementation Phasing

| Phase | Component | Depends On | Ships With |
|-------|-----------|------------|------------|
| **Now** | `OverrideEvent` contract (dataclass) | Nothing | This decision document |
| **Now** | Rationale tag vocabulary (initial set) | Nothing | This decision document |
| **With persistence** (Gap #02) | Override event persistence + retrieval | Database schema, event store | Gap #02 implementation |
| **With persistence** | Phase 1 learning: frequency-based pattern aggregation | Override persistence | Gap #02 implementation |
| **With frontend** | Override recording UX (rationale input, tag selection) | Frontend workspace | Frontend workflow implementation |
| **With customer lifecycle** (Gap #06) | Phase 2 learning: outcome tracking + success_rate | Customer entity, post-trip events | Gap #06 implementation |
| **With pilot data** | Suggestion generation + owner approval UX | Phase 1+2 running, real override data | Pilot-phase feature |

---

## Safety Invariants

1. **Rationale is required.** An override without rationale is noise. The system does not record overrides with empty rationale. This is a data quality gate, not a UX burden — the agent must explain why they disagree.

2. **Override patterns generate suggestions, not auto-adjustments.** The agency owner approves policy changes. Exception: per-traveler suitability memory can auto-update (scoped to one person, not agency-wide policy).

3. **`STOP_NEEDS_REVIEW` overrides are always logged at elevated severity.** This state means safety concern — overriding it is the agent's right (they have `MANUAL_OVERRIDE` authority) but the system records it prominently and the owner sees it in reports.

4. **Override outcomes are optional.** The system functions with Phase 1 (frequency-based) learning alone. Outcome tracking (Phase 2) adds quality assessment but is not required for override recording to be useful.

---

## Remaining Open Items (Updated)

| # | Decision | Status | Next Step |
|---|----------|--------|-----------|
| D1 | Autonomy gradient | ✅ Core decided. Adaptive autonomy pending deep dive. | Deep dive customer+trip classification when pilot data available |
| D2 | Free engine target persona | ✅ Decided. Shared pipeline, empowerment framing. | Implementation sequenced by D6 eval precision gates |
| D3 | Sourcing hierarchy configurability | ✅ Contract decided. Implementation blocked on Gap #01. | Implement with Gap #01 vendor/supplier models |
| D4 | Suitability depth + sub-decisions | ✅ Decided. Three-tier scoring architecture. | Migration Steps 1-5 from parent architecture doc |
| D5 | Override learning | ✅ Contract decided. Implementation phased by Gap #02 + Gap #06. | Phase 1 ships with persistence, Phase 2 with lifecycle |
| D6 | Audit eval suite | ✅ Decided. Manifest-driven, fixture-tiered. | Fixture authoring + eval runner implementation |
| — | Plugin system | ⬜ Draft exists (`PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md`) | Architecture decision needed |
| — | Customer+trip classification | ⬜ Identified during D1 | Separate deep dive thread |

---

*D5 is the feedback bus that makes D1, D3, and D4 compound. Override patterns are the primary learning signal — frequency first (what do agents consistently disagree with?), outcome quality second (were they right to disagree?). The system proposes policy adjustments; the owner approves. Per-traveler suitability memory is the one exception that auto-updates, because it's scoped to individual knowledge, not agency-wide policy.*
