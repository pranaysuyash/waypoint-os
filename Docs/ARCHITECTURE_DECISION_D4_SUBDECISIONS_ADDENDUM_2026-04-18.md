# Architecture Decision Addendum: D4/D6 Sub-Decisions (D4.1–D4.3, D6.1–D6.2)

**Date**: 2026-04-18
**Status**: Decision addendum — evolves `ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` Part 8
**Parent document**: `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`
**Cross-references**:
- `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` (LLMCacheable protocol, cache → rule graduation)
- `Docs/context/TRIP_ACTIVITY_PACING_SCENARIO_2026-04-15.md` (Costa Rica pacing scenario — key tour-coherence test case)
- `Docs/status/ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md` (external API provider mapping, scoring pseudocode)
- `Docs/V02_GOVERNING_PRINCIPLES.md` (layer ownership: NB02 = judgment)
- `Docs/DATA_MODEL_AND_TAXONOMY.md` (activity utility model, per-person suitability, wasted spend formula)
- `src/decision/hybrid_engine.py` (existing cache → rule → LLM → cache pattern)
- `src/intake/decision.py` (budget feasibility tables, composition modifiers)

---

## What Triggered This Evolution

The parent document (`ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`) left five sub-decisions open in Part 8. During discussion of D4.1 (activity catalog scope), the initial recommendation was **activity-type-only tables with destination tags** — a purely deterministic, per-activity approach.

The owner challenged this with a critical observation:

> "Shouldn't we also look at a hybrid LLM-based strategy for D4.1, and define the rest based on that? I don't want later that the logic breaks within the same tour."

This exposed a fundamental gap in the original framing: **suitability was being evaluated per-activity in isolation**. The `SuitabilityScorer` protocol takes `(activity, participant, context)` but the `SuitabilityContext` had no awareness of other activities in the trip. A temple walk scores "suitable for elderly" on its own — but a temple walk AFTER a 3-hour rainforest hike in tropical humidity on the same day, for the same elderly person, is a different verdict.

The parent document's `ActivitySuitability` contract, `SuitabilityBundle`, and `StructuredRisk` all remain valid. What evolves is the **scoring architecture** and the **context surface** — and this cascade reshapes all five sub-decisions.

### Why This Was Missed Initially

The parent document correctly separated analyzers from routers, and defined the three depth levels (L1 binary → L2 scored → L3 per-person scheduling). But the depth levels were framed as **per-activity depth**, not **per-tour depth**. The Costa Rica pacing scenario (`Docs/context/TRIP_ACTIVITY_PACING_SCENARIO_2026-04-15.md`) already demonstrated the need — "3 consecutive high-intensity days with senior + child" — but the architecture didn't structurally connect that scenario to the scorer's input contract.

### What Made This Evolution Possible

Three things from the parent architecture enabled this evolution without contract replacement:

1. **The `SuitabilityScorer` protocol is already swappable.** Adding a tour-context-aware scorer requires no changes to the protocol interface — only richer `SuitabilityContext` input.

2. **The `LLMCacheable` protocol** from `ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` already specified `(activity_id, participant_ref, context_hash)` as the cache key for suitability. Adding `day_activities_hash` to the context hash is an extension, not a replacement.

3. **The `SuitabilityBundle` already has `generated_risks` and `schedule_hints`.** Tour-level coherence findings (e.g., "cumulative fatigue risk across Day 3-4") can be expressed as `StructuredRisk` entries in the bundle without any new contract.

---

## D4.1 Decision: Hybrid Three-Tier Scoring Architecture

### Original Options (from parent Part 8)
- Destination-scoped tables (Singapore, Bali, etc.)
- Activity-type-only tables

### Evolved Decision: Activity-type tables + tour-context deterministic layer + LLM contextual layer

The activity **catalog** (what activities exist) stays destination-agnostic in Phase 1 and gains destination-specificity via external APIs in Phase 2. But the **scoring** operates in three tiers, all producing the same `ActivitySuitability` output.

### Tier 1: Per-Activity Deterministic Rules (always runs, instant, ₹0)

The safety floor. Evaluates one activity against one participant using tag predicates and hard constraints.

- **Hard exclusions** (no override possible):
  - `activity.min_age > participant_age` → `tier="exclude"`
  - `activity.tags contains "height_required"` AND participant fails height → `tier="exclude"`
- **Tag-predicate suitability rules** (~40-60 rules):
  - `"water_based" + participant.kind=="toddler"` → `tier="exclude", reason="drowning risk"`
  - `"physical_intense" + participant.kind=="elderly"` → `tier="discourage", reason="mobility strain"`
  - `"seated_show" + participant.kind=="toddler"` → `tier="recommend", reason="low physical demand"`

This is identical to the original D4.1 recommendation. What's new is that it's explicitly **Tier 1** — a necessary but insufficient layer.

### Tier 2: Tour-Context Deterministic Rules (always runs, instant, ₹0)

The coherence layer. Evaluates one activity in the context of other activities on the same day and across the trip. This is the evolution the owner's challenge unlocked.

**Required contract evolution** — extend `SuitabilityContext`:

```python
@dataclass
class SuitabilityContext:
    """Everything a scorer needs — does NOT include the packet directly."""
    destination_keys: List[str]
    trip_duration_nights: Optional[int] = None
    pace_preference: Optional[Literal["relaxed", "balanced", "packed"]] = None
    traveler_memory: Optional[TravelerMemorySnapshot] = None
    agency_policy: Optional[AgencySuitabilityPolicy] = None
    # ── Tour-context fields (added by this addendum) ──
    day_activities: List[ActivityDefinition] = field(default_factory=list)
    trip_activities: List[ActivityDefinition] = field(default_factory=list)
    day_index: Optional[int] = None
    season_month: Optional[int] = None
    destination_climate: Optional[Literal[
        "tropical_humid", "arid_hot", "temperate", "cold", "alpine", "coastal_humid"
    ]] = None
```

**Sequence rules** (~15-20 rules, expandable):

| Rule | Condition | Participant | Output |
|------|-----------|-------------|--------|
| Cumulative intensity | Sum of `intensity_score` for same-day activities > threshold | elderly | `tier="discourage"`, `warning="cumulative fatigue risk: {X} high-intensity activities on Day {N}"` |
| Back-to-back high-intensity | Two consecutive `"physical_intense"` activities on same day | elderly, toddler | `StructuredRisk(flag="back_to_back_strain", severity="medium")` |
| Rest day gap | No `intensity="light"` day between two `intensity="high"` days | elderly | `StructuredRisk(flag="insufficient_recovery", severity="medium")` |
| Climate × intensity | `"tropical_humid"` + `"walking_heavy"` | elderly | Severity boost (+1 level) on existing walking activity discourage |
| Duration overload | Sum of `duration_hours` for same-day activities > 8 hours | toddler, elderly | `warning="day duration exceeds comfort threshold"` |
| Nap window conflict | Activity scheduled 12:00-15:00 + `participant.kind=="toddler"` | toddler | `warning="conflicts with typical nap window"` |

**Why this is deterministic, not LLM**: These rules are arithmetic and predicate-based. "Sum intensity scores for the day" is a loop. "Check if rest day exists between high-intensity days" is a scan. No world knowledge needed — just the activity data that's already in the `ActivityDefinition` contract.

**Where destination context enters**: The `destination_climate` field comes from existing destination data (partially in `src/intake/geography.py`, partially in the budget feasibility tables). Singapore → `tropical_humid`. Kashmir → `alpine`. This is a mapping table, not a per-activity catalog change.

### Tier 3: LLM Contextual Scoring (runs when Tiers 1+2 produce borderline or ambiguous results)

For cases deterministic rules can't handle. Plugs into the existing `HybridDecisionEngine` (`src/decision/hybrid_engine.py`) via the `LLMCacheable` protocol from `ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md`.

**When Tier 3 fires** (trigger conditions):
- Tier 1+2 produce `tier="neutral"` but the combination of factors suggests a non-obvious risk
- Activity has low `source_confidence` (per `ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md` confidence model)
- Participant has specific medical/physical constraints from traveler memory that don't map to standard tag predicates
- Agency policy requests LLM validation for specific activity types (`AgencySuitabilityPolicy.scorer_preference = "llm_contextual_v1"`)

**What it evaluates** (examples that need world knowledge):
- "Is white-water rafting safe for an 8-year-old in Costa Rica in December?" — needs knowledge of Grade III rapids norms
- "Given this family did 4 high-intensity days in a row, is Day 5 zipline too much?" — contextual fatigue reasoning beyond simple summation
- "This temple requires 2km uphill walking at 2,400m altitude — feasible for elderly with knee problems?" — altitude + terrain + medical history interaction

**Cache strategy** (extends existing pattern):
- Cache key: `(activity_id, participant_ref, day_activities_hash, destination_key, season_month)`
- The `day_activities_hash` ensures that the same activity scored in a different day context produces a different cache entry
- Cache → rule graduation: when a cached LLM verdict has `use_count > 20` + `success_rate > 0.95`, the pattern is a candidate for promotion to a Tier 2 deterministic rule via `PromotionCandidate` (per `ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` Part 1)

**Scorer implementation** (uses existing protocol):

```python
class LLMContextualScorer:
    """Tier 3 scorer — implements both SuitabilityScorer and LLMCacheable protocols."""
    scorer_id: str = "llm_contextual_v1"
    scorer_version: str = "1"
    cache_namespace: str = "suitability"

    def score(self, activity, participant, context) -> ActivitySuitability:
        # 1. Compute cache key including tour context
        key = self.compute_cache_key({
            "activity_id": activity.activity_id,
            "participant": participant.ref_id,
            "day_activities": [a.activity_id for a in context.day_activities],
            "destination": context.destination_keys,
            "season": context.season_month,
        })
        # 2. Check cache → return if hit
        # 3. Try deterministic rule promotion candidates → return if match
        # 4. Format LLM prompt with full tour context
        # 5. Extract structured ActivitySuitability from LLM response
        # 6. Cache result
        # 7. Return
        ...
```

### The Coherence Guarantee

Because ALL three tiers receive the same `SuitabilityContext` (which now includes `day_activities` and `trip_activities`), every scorer evaluates in context. The same activity WILL get different scores on different days with different companion activities. This is by design — "temple walk on a rest day" ≠ "temple walk after rainforest hike."

The `SuitabilityBundle.generated_risks` carries tour-level findings:
```python
SuitabilityBundle(
    activity_id="temple_walk_001",
    assessments=[...],
    generated_risks=[
        StructuredRisk(
            flag="cumulative_fatigue_risk",
            severity="high",
            category="activity",
            message="3 consecutive high-intensity days with elderly participant; temple walk adds to cumulative strain",
            affected_travelers=["elderly_1"],
            mitigation_suggestions=["Insert rest day before Day 5", "Move temple walk to Day 6 morning"],
        ),
    ],
)
```

### Activity Catalog Scope (The Original D4.1 Question)

The catalog itself (what activities exist) remains **activity-type tables with destination tags**, not destination-scoped:

- **Phase 1 static catalog**: ~25-30 activity types with tags, intensity, duration, age constraints. Destination-agnostic. Examples: `theme_park_rides`, `snorkeling`, `temple_visit`, `city_walking_tour`, `rainforest_hike`, `fine_dining`, `cooking_class`, `hot_springs`, `white_water_rafting`, `canopy_zipline`, `beach_day`, `shopping_tour`, `cultural_show`, `boat_cruise`, `safari_drive`.
- **Phase 2 agency catalog**: Agency-configurable additions/overrides via `ActivityCatalogProvider` protocol.
- **Phase 2+ external API catalog**: Viator, Booking Attractions, Musement, Klook instances normalize to `ActivityDefinition` (per `ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md`).

The destination-context (climate, terrain, altitude, seasonal patterns) enters through `SuitabilityContext`, NOT through the catalog. The catalog answers "what exists." The context answers "what's the environment." The scorer combines both.

---

## D4.2 Decision: Tag-Based Matching with Two Rule Sections

### Original Options (from parent Part 8)
- ~20 activity types × 5 traveler types (100 cells)
- Tag-based matching

### Decision: Tag-based matching with per-activity rules + sequence rules

The tag-based approach wins, but now explicitly structured as two rule sections that serve different tiers:

**Section A: Per-Activity Rules** (~40-60 rules) — feeds Tier 1
- `(tag_predicate, participant_kind) → (tier, reasons)`
- Examples: `("water_based", "toddler") → ("exclude", ["drowning risk, cannot self-rescue"])`
- Evaluated for each activity × each participant independently
- Backed by `ActivityDefinition.tags`, `.intensity`, `.min_age`, `.max_age`, `.accessibility_tags`

**Section B: Sequence Rules** (~15-20 rules) — feeds Tier 2
- `(cumulative_condition, participant_kind) → (risk_flag, severity)`
- Examples: `(sum_intensity > 2.5 for same_day, "elderly") → ("cumulative_fatigue_risk", "high")`
- Evaluated with full `SuitabilityContext.day_activities` / `.trip_activities`
- Backed by `ActivityDefinition.intensity`, `.duration_hours` + `SuitabilityContext.destination_climate`, `.season_month`

**Tag vocabulary** (must serve both sections):

Activity tags for per-item scoring:
- Physical: `physical_intense`, `walking_heavy`, `water_based`, `height_required`, `altitude_sensitive`
- Comfort: `seated_show`, `air_conditioned`, `shaded`, `indoor`
- Access: `wheelchair_accessible`, `no_stairs`, `stroller_friendly`
- Age: `min_age_required`, `adult_supervision_required`
- Type: `nature_walk`, `cultural_visit`, `adventure_sport`, `dining`, `shopping`, `beach`, `spa_wellness`

Intensity/duration signals for cumulative scoring:
- `ActivityDefinition.intensity`: `light` (0.25) / `moderate` (0.5) / `high` (0.75) / `extreme` (1.0) — numeric mapping for summation
- `ActivityDefinition.duration_hours`: actual hours for day-total calculation

**Why not a flat matrix**: Adding "pregnant" as a participant type or "zip-lining" as an activity type adds rules to the relevant section — it doesn't require restructuring a 2D grid. The `AgencySuitabilityPolicy.weight_overrides` can adjust individual rule weights. The `AgencySuitabilityPolicy.hard_exclusions` can add agency-specific tag exclusions.

---

## D4.3 Decision: `src/intake/suitability/` — Stays Under Intake

### Decision: `src/intake/suitability/`

Unchanged from initial recommendation. The tour-context evolution reinforces this — Tier 2 sequence rules are NB02 judgment ("is this day plan safe for this person?"), not NB03/planning ("what should we schedule instead?").

**Layer ownership** per `V02_GOVERNING_PRINCIPLES.md`:
- **NB02** (judgment/routing) owns: "Is this activity suitable? Is this day plan coherent? What risks exist?" → `src/intake/suitability/`
- **Future planning layer** owns: "Given these suitability bundles, what alternative itinerary should we propose?" → `src/planning/` (does not exist yet)

The `ScheduleAllocator` protocol (parent doc Part 3.1) is the one piece that may migrate to `src/planning/` when Stage 3 ships. For now, it's a protocol definition without implementation — no module needed.

**LLM integration point**: The Tier 3 `LLMContextualScorer` calls into `src/decision/hybrid_engine.py` for cache/rule/LLM orchestration. This is a cross-cutting dependency, not a module placement concern — `src/intake/decision.py` already imports from `src/decision/` (L43-44).

---

## D6.1 Decision: Manual Curation with Tour-Context Fixtures

### Original Options (from parent Part 8)
- Manual curation
- Semi-automated from real agency scenarios

### Decision: Manual curation, seeded from existing scenarios, structured with tour-context fixtures

The tour-context evolution from D4.1 impacts fixture requirements. Fixtures now need three tiers of complexity:

**Tier A: Isolated Activity Fixtures** (tests Tier 1 rules)
- Single activity × single participant. "Is roller coaster suitable for toddler?"
- Source: Domain knowledge, straightforward to author.
- Count: ~15-20

**Tier B: Day-Sequence Fixtures** (tests Tier 2 rules)
- Multiple activities on same day × participant(s). "Is zipline suitable for elderly AFTER 3-hour hike?"
- Source: Constructed from domain knowledge + existing pacing scenario patterns.
- Count: ~15-20

**Tier C: Trip-Sequence Fixtures** (tests Tier 2+3 interaction)
- Multi-day itinerary × mixed group. "Is 14-day Costa Rica itinerary with 4 high-intensity regions feasible for senior + child?"
- Source: Directly adapted from the 5 synthetic scenarios in `Docs/context/`:
  - `TRIP_ACTIVITY_PACING_SCENARIO_2026-04-15.md` → Costa Rica family pacing
  - `TRIP_FEASIBILITY_SCENARIO_2026-04-15.md` → multi-country logistics
  - `TRIP_BUDGET_REALITY_SCENARIO_2026-04-15.md` → budget constraints
  - `TRIP_VISA_DOCUMENT_RISK_SCENARIO_2026-04-15.md` → document/visa risks
  - `TRIP_TRANSFER_COMPLEXITY_SCENARIO_2026-04-15.md` → transfer friction
- Count: ~10-15

**Authoring strategy** (phased):

| Phase | What | Count | Source | Blocked On |
|-------|------|-------|--------|------------|
| Now | Budget-category fixtures (clean + broken) | 10-12 | Domain knowledge + existing feasibility tests | Nothing — `check_budget_feasibility` works today |
| Now | Tier A isolated activity fixtures (clean + broken) | 15-20 | Domain knowledge, activity tag definitions | Nothing — can author against tag vocabulary before runtime exists |
| With Tier 2 implementation | Tier B day-sequence fixtures | 15-20 | Constructed from pacing scenario patterns | Tier 2 rule definitions (this addendum) |
| With Tier 3 implementation | Tier C trip-sequence fixtures | 10-15 | Adapted from `Docs/context/` scenarios | `SuitabilityContext` tour fields, LLM scorer |
| Post-pilot | Real-world fixtures from anonymized inputs | Ongoing | NB06 shadow collector, pilot agency data | Running pilot |

Total initial fixture target: ~50-65 (expanded from parent doc's 40-60 to account for tour-context tiers).

---

## D6.2 Decision: YAML Files + Python Schema/Loading

### Decision: YAML for fixture data, Python dataclasses for schema and loading

Unchanged from initial recommendation, with one structural addition: tour-context fixtures need a `day_plan` section.

**Fixture directory structure** (extends parent doc Part 5):

```
data/fixtures/audit/
  budget/
    budget_infeasible_singapore_family.yaml
    budget_clean_bali_couple.yaml
    budget_borderline_vietnam_group.yaml
  activity/
    isolated/                    # Tier A — single activity × single participant
      suitability_roller_coaster_toddler.yaml
      suitability_snorkeling_elderly.yaml
      suitability_clean_nature_walk_family.yaml
    day_sequence/                # Tier B — multiple activities same day
      day_overload_elderly_hike_then_temple.yaml
      day_clean_morning_museum_afternoon_rest.yaml
      day_climate_tropical_walking_elderly.yaml
    trip_sequence/               # Tier C — multi-day coherence
      trip_costa_rica_pacing_senior_child.yaml
      trip_singapore_family_theme_park_split.yaml
      trip_clean_relaxed_bali_couple.yaml
  pacing/
  logistics/
  documents/
  multi_issue/
  edge_cases/
```

**Tier B fixture example** (`day_overload_elderly_hike_then_temple.yaml`):

```yaml
fixture_id: day_overload_elderly_hike_then_temple
category: activity
notes: >
  Tests Tier 2 cumulative intensity rule. Rainforest hike (high intensity, 3h)
  followed by temple visit (moderate intensity, 2h walking) on same day in
  tropical humid climate. Elderly participant should trigger cumulative fatigue.

subject:
  destination_keys: [Singapore]
  destination_climate: tropical_humid
  season_month: 7
  trip_duration_nights: 5
  pace_preference: balanced
  participants:
    - kind: elderly
      ref_id: elderly_1
      label: grandmother
    - kind: adult
      ref_id: adult_1
      label: parent
  day_plan:
    - day_index: 3
      activities:
        - activity_id: rainforest_hike_001
          canonical_name: Rainforest Trail Hike
          tags: [physical_intense, walking_heavy, nature_walk]
          intensity: high
          duration_hours: 3.0
        - activity_id: temple_visit_001
          canonical_name: Temple Heritage Walk
          tags: [cultural_visit, walking_heavy]
          intensity: moderate
          duration_hours: 2.0

expected_findings:
  - category: activity
    flag: cumulative_fatigue_risk
    severity: high
    affected_refs: [elderly_1]
  - category: activity
    flag: climate_intensity_amplifier
    severity: medium
    affected_refs: [elderly_1]

expected_absent_findings:
  - category: activity
    flag: cumulative_fatigue_risk
    reason: "adult_1 has no intensity limitations for this combination"
    affected_refs: [adult_1]
```

**Python schema** (in `src/evals/audit/fixtures.py`) — the `AuditFixture` dataclass from the parent document gains a `day_plan` field in `AuditSubject`:

```python
@dataclass
class AuditSubjectDayPlan:
    """One day's activities for tour-context testing."""
    day_index: int
    activities: List[ActivityDefinition]

# AuditSubject (parent doc) gains:
#   day_plan: List[AuditSubjectDayPlan] = field(default_factory=list)
```

The loader reads YAML, validates against the dataclass schema, and returns typed `AuditFixture` objects. The eval runner, metrics computation, and CI gates all operate on typed objects — they never see YAML.

---

## Impact on Parent Architecture Document

This addendum does NOT replace any contracts from the parent document. Specifically:

| Parent Document Component | Status | Change |
|--------------------------|--------|--------|
| `ParticipantRef` | ✅ Unchanged | — |
| `ActivityDefinition` | ✅ Unchanged | Tags and intensity already sufficient |
| `ActivitySuitability` | ✅ Unchanged | All three tiers produce this same output |
| `SuitabilityBundle` | ✅ Unchanged | `generated_risks` carries tour-level findings |
| `StructuredRisk` | ✅ Unchanged | Sequence rules emit these |
| `SuitabilityContext` | 🔄 Extended | Added `day_activities`, `trip_activities`, `day_index`, `season_month`, `destination_climate` |
| `SuitabilityScorer` protocol | ✅ Unchanged | Protocol was already swappable by design |
| `ActivityCatalogProvider` protocol | ✅ Unchanged | Catalog scope is independent of scoring tiers |
| `ScheduleAllocator` protocol | ✅ Unchanged | Phase 3, not affected |
| `AuditSubject` | 🔄 Extended | Added `day_plan` for tour-context fixtures |
| Module layout (`src/intake/suitability/`) | ✅ Unchanged | — |
| Eval suite manifest | ✅ Unchanged | Category progression `planned → shadow → gating` applies per-tier |

The parent document's migration path (Steps 1-5) remains valid. This addendum adds detail to Step 2 (what scorers to build) and Step 4 (what fixture tiers to author).

---

## Evolution Summary

```
Original D4/D6 Architecture (2026-04-16)
│
│  Per-activity scoring in isolation
│  SuitabilityContext has destination + pace + memory
│  D4.1-D6.2 left as open questions
│
├── Owner challenge: "logic breaks within the same tour"
│   Exposed: scorer evaluates activities independently
│   Missing: day-level and trip-level coherence
│
▼
This Addendum (2026-04-18)
│
│  Three-tier scoring: per-activity → day-sequence → LLM contextual
│  SuitabilityContext gains tour-level fields
│  All five sub-decisions resolved with coherence as primary driver
│
│  No contract replacement — only extensions to SuitabilityContext + AuditSubject
│  Enabled by: swappable SuitabilityScorer protocol, LLMCacheable protocol,
│  existing HybridDecisionEngine cache→rule→LLM pattern
```

---

## Pending: Tier 3 LLM Contextual Scorer — Detailed Spec

**Status**: Deferred — spec when Tiers 1+2 are implemented and borderline cases are observable.

**What's defined** (in this addendum + parent LLM cache doc):
- Trigger conditions (borderline Tier 1+2 output, low source confidence, specific traveler memory constraints, agency policy override)
- Cache key shape: `(activity_id, participant_ref, day_activities_hash, destination_key, season_month)`
- Protocol interface: `LLMContextualScorer` implementing both `SuitabilityScorer` and `LLMCacheable`
- Graduation path: cached LLM verdicts with `use_count > 20` + `success_rate > 0.95` → `PromotionCandidate` → Tier 2 deterministic rule

**What needs specifying later**:
- Prompt templates for suitability LLM calls (system prompt + structured context injection)
- Structured output JSON schema (analogous to `HybridDecisionEngine.SCHEMAS` in `src/decision/hybrid_engine.py` L132-178)
- Trigger threshold calibration (what exact Tier 1+2 score ranges / ambiguity patterns invoke Tier 3)
- Per-call cost guardrails and monthly budget caps (per `DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md` L246)
- Eval fixtures specifically targeting Tier 3 edge cases (requires Tier 1+2 to be running to identify real borderline inputs)

**Why deferred**: Tier 3's value is in handling what Tiers 1+2 can't. Until those tiers run on real data, we can't know which borderline cases actually occur — specifying prompts and thresholds now would be guesswork. The protocol and cache contracts are locked; the implementation details wait for empirical signal.

---

*This addendum documents how a production concern about intra-tour coherence evolved the scoring architecture from per-activity to tour-context-aware, without replacing any contracts from the parent document. The three-tier approach ensures deterministic safety (Tier 1), deterministic coherence (Tier 2), and LLM depth for edge cases (Tier 3) — with every LLM call cached and graduated toward deterministic rules over time.*
