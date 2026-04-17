# Architecture Decision: D4 (Suitability Engine) + D6 (Audit Eval Suite)

**Date**: 2026-04-16
**Status**: Decision document — pending review
**Scope**: Full production architecture, phased by dependency
**Cross-references**:
- `V02_GOVERNING_PRINCIPLES.md` (layer ownership)
- `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` (build sequence)
- `Docs/architecture/SCENARIO_HANDLING_ARCHITECTURE.md` (existing `ActivitySuitability` spec)
- `DATA_MODEL_AND_TAXONOMY.md` (utility model, taxonomy)
- `Sourcing_And_Decision_Policy.md` (wasted spend rule)
- `DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` (discussion context)

---

## Governing Principle

> "Do not ask 'is this in scope?' — Ask only: 'Which layer owns this?'"
> — `V02_GOVERNING_PRINCIPLES.md`

Every component in this decision has an explicit layer owner. Every contract is designed to evolve without replacement.

---

## Part 1: The Shared Foundation — Analyzers vs. Routers

### The Core Architectural Split

The single most important decision: **separate analyzers from routing**.

- **Analyzers** compute typed artifacts (suitability scores, feasibility verdicts, pacing analysis)
- **Routers** decide what to do with those artifacts (set `decision_state`, emit risks, trigger follow-ups)

This means D4 (suitability) is an **analyzer**, and D6 (audit eval) is a **measurement system over analyzer outputs**. They share a common artifact layer but never duplicate logic.

### Layer Ownership (Locked)

| Layer | Owns | Does NOT Own |
|-------|------|--------------|
| **NB01** | Truth capture, normalization, traveler memory import, normalized audit subject | Scoring, judgment, quality measurement |
| **NB02** | Suitability scoring, wasted spend detection, audit rule evaluation, decision-state routing | Prompt wording, user-facing phrasing |
| **NB03** | Explaining findings to traveler/agent, phrasing follow-ups, presenting split-day options | Recomputing suitability or audit logic |
| **NB04** | Eval fixtures, precision/recall measurement, CI gates, trend tracking | Runtime decisions, production routing |

---

## Part 2: Shared Typed Contracts

These contracts are consumed by both D4 and D6. They are the stable API surface that enables independent evolution.

### 2.1 `ParticipantRef` — Who is being assessed

```python
@dataclass
class ParticipantRef:
    """Reference to a traveler unit — evolves from cohort → subgroup → person."""
    kind: Literal["group", "subgroup", "cohort", "person"]
    ref_id: str
    label: str  # "elderly", "toddler_1", "G1", "P003"
```

**Evolution path**: Today, suitability scores at `cohort` level ("elderly", "toddler"). As person-level data arrives, same contract supports `person` level without downstream changes.

### 2.2 `ActivityDefinition` — What is being assessed

```python
@dataclass
class ActivityDefinition:
    """Normalized activity — all sources (static, agency, external) reduce to this."""
    activity_id: str
    canonical_name: str
    source: Literal["static", "agency", "external_api"]
    source_ref: Optional[str] = None
    destination_keys: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)  # "physical_intense", "water_based", etc.
    intensity: Literal["light", "moderate", "high", "extreme"] = "moderate"
    duration_hours: Optional[float] = None
    cost_per_person: Optional[int] = None
    cost_band: Optional[Literal["low", "mid", "high", "premium"]] = None
    accessibility_tags: List[str] = field(default_factory=list)  # "wheelchair_accessible", "no_stairs"
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Critical rule**: Whether activity data comes from a hardcoded Python table, an agency-managed config file, or an external API — **everything normalizes to `ActivityDefinition` before scoring**. Downstream logic never knows the source.

### 2.3 `ActivitySuitability` — The assessment result (stable across all phases)

```python
@dataclass
class ActivitySuitability:
    """Per-participant assessment of one activity. Same shape across all three depth levels."""
    activity_id: str
    participant: ParticipantRef
    compatible: bool                  # L1: binary answer
    score: float                      # L1: 0.0 or 1.0. L2+: continuous 0.0-1.0
    tier: Literal[
        "exclude",       # hard safety exclusion — cannot participate
        "discourage",    # significant friction — flag but allow override
        "neutral",       # no strong signal either way
        "recommend",     # good fit
        "strong_recommend",  # excellent fit
    ] = "neutral"
    hard_exclusion_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score_components: Dict[str, float] = field(default_factory=dict)  # L2+: breakdown
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    scorer_id: str = "heuristic_v1"
    scorer_version: str = "1"
    maturity: Literal["stub", "heuristic", "verified", "ml_assisted"] = "heuristic"
```

**Why this works across all phases:**
- **Phase 1 (L1)**: `compatible=True/False`, `score` ∈ {0.0, 1.0}, `tier` ∈ {exclude, neutral, recommend}, `score_components` empty
- **Phase 2 (L2)**: `score` is continuous, `score_components` filled with breakdown, `tier` uses full range
- **Phase 3 (L3)**: Same object, now emitted per `ParticipantRef(kind="person")` instead of `kind="cohort"`

No contract replacement needed across phases.

### 2.4 `SuitabilityBundle` — The aggregate per-activity

```python
@dataclass
class SuitabilityBundle:
    """All assessments for one activity, plus group-level aggregate."""
    activity_id: str
    assessments: List[ActivitySuitability]
    group_score: float                    # weighted mean across participants
    high_utility_count: int               # participants with score > 0.7
    total_participants: int
    wasted_spend_ratio: float             # (total - high_utility) / total
    wasted_spend_amount: Optional[int]    # cost × wasted_spend_ratio
    generated_risks: List[StructuredRisk] = field(default_factory=list)
    schedule_hints: List[Dict[str, Any]] = field(default_factory=list)  # L3: split-day suggestions
```

### 2.5 `StructuredRisk` — The common finding contract (replaces loose dicts)

```python
@dataclass
class StructuredRisk:
    """Typed risk finding — used by both runtime decision engine and audit rules."""
    flag: str
    severity: Literal["low", "medium", "high", "critical"]
    category: Literal[
        "budget", "activity", "pacing", "logistics",
        "documents", "composition", "routing", "commercial",
        "seasonality",
    ]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_travelers: List[str] = field(default_factory=list)  # ParticipantRef.ref_id values
    mitigation_suggestions: List[str] = field(default_factory=list)
    maturity: Literal["stub", "heuristic", "verified", "ml_assisted"] = "heuristic"
    rule_id: Optional[str] = None  # which audit rule generated this
```

**Migration note**: Current `risk_flags` in `decision.py` uses `List[Dict[str, Any]]`. `StructuredRisk` replaces this as the real typed contract. The dict format remains as a backward-compatible projection until all consumers migrate.

---

## Part 3: D4 — Suitability Engine Architecture

### 3.1 Three Protocol Interfaces (Plugin Pattern)

```python
class ActivityCatalogProvider(Protocol):
    """Provides activity definitions. Multiple providers chain: static → agency → external."""
    provider_id: str
    def list_activities(
        self,
        destination_keys: List[str],
        agency_policy: Optional[AgencySuitabilityPolicy] = None,
    ) -> List[ActivityDefinition]: ...

class SuitabilityScorer(Protocol):
    """Scores one participant against one activity. Swappable: heuristic → ML."""
    scorer_id: str
    scorer_version: str
    def score(
        self,
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
    ) -> ActivitySuitability: ...

class ScheduleAllocator(Protocol):
    """Given suitability bundles, suggests schedule splits. Phase 3 capability."""
    allocator_id: str
    def build_schedule_hints(
        self,
        bundles: List[SuitabilityBundle],
        packet: CanonicalPacket,
    ) -> List[Dict[str, Any]]: ...
```

### 3.2 Context and Policy Objects

```python
@dataclass
class SuitabilityContext:
    """Everything a scorer needs — does NOT include the packet directly."""
    destination_keys: List[str]
    trip_duration_nights: Optional[int] = None
    pace_preference: Optional[Literal["relaxed", "balanced", "packed"]] = None
    traveler_memory: Optional[TravelerMemorySnapshot] = None
    agency_policy: Optional[AgencySuitabilityPolicy] = None

@dataclass
class AgencySuitabilityPolicy:
    """Per-agency customization — config, not code branches."""
    agency_id: str
    weight_overrides: Dict[str, float] = field(default_factory=dict)
    hard_exclusions: Dict[str, List[str]] = field(default_factory=dict)  # tag → reasons
    tag_aliases: Dict[str, str] = field(default_factory=dict)
    preferred_activity_tags: List[str] = field(default_factory=list)
    scorer_preference: str = "heuristic_v1"

@dataclass
class TravelerMemorySnapshot:
    """Repeat-client context — input to scoring, not a hidden side effect."""
    participant: ParticipantRef
    explicit_preferences: Dict[str, Any] = field(default_factory=dict)
    derived_preferences: Dict[str, float] = field(default_factory=dict)
    prior_activity_ids: List[str] = field(default_factory=list)
    prior_destination_ids: List[str] = field(default_factory=list)
    recency_days: Optional[int] = None
    confidence: float = 0.6
```

### 3.3 Authority Merge Order (for scoring inputs)

When multiple sources provide suitability-relevant data, merge in this order (highest authority first):

1. **Explicit traveler fact** (e.g., "grandmother has knee problems")
2. **Explicit agency/owner override** (e.g., "this family is fine with walking")
3. **Imported traveler memory** (e.g., "last trip, they skipped all physical activities")
4. **Agency policy weights** (e.g., "we always flag water activities for toddlers")
5. **Global heuristic / ML prior** (e.g., "elderly + roller coaster = exclude")

**Hard safety exclusions always win over score boosts.** An agency policy cannot override a hard exclusion (e.g., height requirement for a ride).

### 3.4 Registry Pattern

```python
# Registries — simple dict-based, no framework dependency
_catalog_providers: Dict[str, ActivityCatalogProvider] = {}
_scorers: Dict[str, SuitabilityScorer] = {}
_allocators: Dict[str, ScheduleAllocator] = {}

def register_catalog_provider(provider: ActivityCatalogProvider) -> None: ...
def register_scorer(scorer: SuitabilityScorer) -> None: ...
def register_allocator(allocator: ScheduleAllocator) -> None: ...
```

Default chain:
- Catalog: `static_v1` → (later) `agency_config` → (later) `external_api`
- Scorer: `heuristic_v1` → (later) `heuristic_weighted_v1` → (later) `ml_v1`
- Allocator: none initially → (Phase 3) `split_day_v1`

### 3.5 Evolution Path (No Contract Replacement)

| Phase | Catalog | Scorer | Allocator | ParticipantRef.kind |
|-------|---------|--------|-----------|---------------------|
| **Phase 1** | `static_v1` (hardcoded Python tables) | `heuristic_v1` (binary lookup) | None | `cohort`, `subgroup` |
| **Phase 2** | `static_v1` + `agency_config` | `heuristic_weighted_v1` (scored + components) | None | `cohort`, `subgroup` |
| **Phase 3** | + `external_api` | + `ml_v1` (optional) | `split_day_v1` | + `person` |

Each phase adds to registries. Nothing is replaced.

---

## Part 4: D6 — Audit Eval Suite Architecture

### 4.1 Runtime Audit vs. Offline Eval — Two Separate Systems

| System | Lives In | Purpose | Runs When |
|--------|----------|---------|-----------|
| **Runtime audit** | NB02 (`src/intake/audit/`) | Production judgment: run audit rules, emit findings | Every request with `operating_mode="audit"` |
| **Offline eval** | NB04 (`src/evals/audit/`) | Quality measurement: measure accuracy of runtime audit | CI, nightly, manual |

They share contracts (`StructuredRisk`, `AuditRule`) but never share execution paths.

### 4.2 `AuditRule` Protocol — Pluggable Categories

```python
class AuditRule(Protocol):
    """One audit category. Additive: new capabilities = new rules, not rewrites."""
    rule_id: str
    category: str  # "budget", "activity", "pacing", "logistics", "documents"
    maturity: Literal["stub", "heuristic", "verified", "ml_assisted"]
    dependencies: Tuple[str, ...]  # other rule_ids or analyzer names this needs

    def evaluate(
        self,
        subject: AuditSubject,
        derived: AuditDerivedState,
    ) -> List[StructuredRisk]: ...
```

### 4.3 `AuditSubject` and `AuditDerivedState` — Shared Cache

```python
@dataclass
class AuditSubject:
    """The thing being audited — an itinerary/proposal/quote. NOT inside CanonicalPacket.facts."""
    subject_id: str
    subject_type: Literal["itinerary", "proposal", "quote", "plan"]
    destination_keys: List[str]
    party_composition: Dict[str, int]
    budget_total: Optional[int] = None
    activities: List[Dict[str, Any]] = field(default_factory=list)
    accommodations: List[Dict[str, Any]] = field(default_factory=list)
    day_plans: List[Dict[str, Any]] = field(default_factory=list)
    documents_mentioned: List[str] = field(default_factory=list)
    raw_source: Optional[str] = None  # original text/PDF content
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditDerivedState:
    """Shared cache — analyzers write, rules read. Prevents recomputation."""
    feasibility: Optional[Dict[str, Any]] = None
    budget_breakdown: Optional[Dict[str, Any]] = None
    suitability_bundles: List[SuitabilityBundle] = field(default_factory=list)
    route_analysis: Optional[Dict[str, Any]] = None
    pacing_analysis: Optional[Dict[str, Any]] = None
    document_risk: Optional[Dict[str, Any]] = None
```

**Critical coupling point**: D4's `SuitabilityBundle` outputs feed directly into `AuditDerivedState.suitability_bundles`. The `activity` audit rule reads them — it does NOT re-score suitability.

### 4.4 Audit Rule Registry

```python
_audit_rules: Dict[str, AuditRule] = {}

def register_audit_rule(rule: AuditRule) -> None: ...
def get_active_rules() -> List[AuditRule]: ...
```

Initial rules:
- `BudgetAuditRule` (uses existing `check_budget_feasibility`)
- (Phase 2) `ActivityAuditRule` (uses D4 `SuitabilityBundle`)
- (Phase 2+) `PacingAuditRule`, `LogisticsAuditRule`, `DocumentsAuditRule`

### 4.5 Eval Suite — Manifest-Driven, Category-Native

#### Capability Manifest

```yaml
# src/evals/audit/manifest.yaml
categories:
  budget:
    status: gating          # CI-blocking
    min_precision: 0.95
    min_recall: 0.95
    min_severity_accuracy: 0.90
  activity:
    status: shadow           # scored and reported, not blocking yet
    min_precision: 0.90
    min_recall: 0.85
  pacing:
    status: planned          # fixtures exist, not scored yet
  logistics:
    status: planned
  documents:
    status: planned
```

**Status progression**: `planned` → `shadow` → `gating`

- **planned**: fixtures authored, capabilities not yet implemented. Tests show 0% recall — that's correct and useful as a progress tracker.
- **shadow**: capabilities implemented, accuracy measured and reported, but not PR-blocking.
- **gating**: accuracy must meet thresholds to pass CI.

#### Fixture Format

```python
@dataclass
class AuditFixture:
    """One test case for the audit eval suite."""
    fixture_id: str
    category: str                     # primary category being tested
    subject: AuditSubject
    expected_findings: List[ExpectedFinding]
    expected_absent_findings: List[ExpectedAbsentFinding]  # tests false positives
    expected_decision_state: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class ExpectedFinding:
    category: str
    flag: str
    severity: Literal["low", "medium", "high", "critical"]
    affected_refs: List[str] = field(default_factory=list)  # ParticipantRef.ref_id

@dataclass
class ExpectedAbsentFinding:
    """This should NOT be flagged — tests false positive rate."""
    category: str
    flag: str
    reason: str  # why this is expected to be absent
```

#### Metrics Computation

```python
@dataclass
class CategoryMetrics:
    category: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    severity_matches: int
    severity_total: int
    severity_accuracy: float
```

#### CI Gating (Two Tiers)

**PR-blocking:**
- Contract tests (schemas, types)
- Must-pass critical fixtures (zero tolerance for critical false negatives)
- Per-category regression against `gating` thresholds
- "No new critical false negatives" check

**Nightly/scheduled:**
- Full fixture matrix across all categories
- Trend reporting (are we improving?)
- Shadow category scoring
- Cross-fixture analysis (which fixture types are hardest?)

---

## Part 5: Module Layout

```
src/intake/
  decision.py              # NB02 router — calls analyzers, makes decisions
  structured_risks.py      # StructuredRisk + backward-compat projection

  suitability/
    __init__.py
    contracts.py           # ParticipantRef, ActivityDefinition, ActivitySuitability,
                           # SuitabilityBundle, SuitabilityContext, AgencySuitabilityPolicy,
                           # TravelerMemorySnapshot
    registry.py            # register_*/get_* for catalog, scorer, allocator
    service.py             # top-level: assess_activities(packet) → List[SuitabilityBundle]
    catalogs/
      __init__.py
      static.py            # Phase 1: hardcoded activity tables
      agency.py            # Phase 2: agency-configurable catalog
    scorers/
      __init__.py
      heuristic_v1.py      # Phase 1: binary lookup
      heuristic_weighted.py # Phase 2: scored + components
    scheduling/
      __init__.py
      split_day_v1.py      # Phase 3: split-day allocator

  audit/
    __init__.py
    contracts.py           # AuditSubject, AuditDerivedState, AuditRule protocol
    registry.py            # register_audit_rule, get_active_rules
    engine.py              # run_audit(packet, subject) → AuditReport
    rules/
      __init__.py
      budget.py            # Phase 1: wraps existing check_budget_feasibility
      activity.py          # Phase 2: reads SuitabilityBundles from derived state
      pacing.py            # Phase 2+
      logistics.py         # Phase 2+
      documents.py         # Phase 2+

src/evals/
  audit/
    __init__.py
    manifest.py            # loads manifest.yaml
    fixtures.py            # AuditFixture, ExpectedFinding, loaders
    metrics.py             # CategoryMetrics computation
    gates.py               # CI gate logic (gating vs shadow vs planned)
    runner.py              # run_eval_suite() → EvalReport

data/fixtures/
  audit/
    budget/                # budget-broken and budget-clean fixtures
    activity/              # suitability-broken and clean fixtures
    pacing/                # pacing-broken fixtures
    logistics/             # logistics-broken fixtures
    documents/             # document-risk fixtures
    multi_issue/           # combinations
    edge_cases/            # solo, large group, etc.
```

### Migration Path (Do NOT Move Everything At Once)

**Step 1** (immediate): Extract `StructuredRisk` from decision.py → `structured_risks.py`
**Step 2**: Create `suitability/contracts.py` + `suitability/service.py` + `suitability/catalogs/static.py` + `suitability/scorers/heuristic_v1.py`
**Step 3**: Create `audit/contracts.py` + `audit/rules/budget.py` (wrapping existing feasibility logic)
**Step 4**: Create `src/evals/audit/` framework + first budget-category fixtures
**Step 5**: Wire `decision.py` to call `suitability.service` and `audit.engine`

Each step is independently testable and deployable.

---

## Part 6: Runtime Flow

```
Input → NB01 (normalize) → CanonicalPacket + AuditSubject (if audit mode)
                               ↓
                          NB02 Analyzers
                            ├── check_budget_feasibility() → feasibility result
                            ├── suitability.service.assess_activities() → SuitabilityBundles
                            └── (future) pacing_analyzer, logistics_analyzer
                               ↓
                          AuditDerivedState (shared cache)
                               ↓
                    ┌──────────┴──────────┐
                    │                     │
              NB02 Router            NB02 Audit Engine
              (all modes)            (audit mode only)
                    │                     │
              decision_state         AuditRule evaluations
              risk_flags             → List[StructuredRisk]
                    │                     │
                    └──────────┬──────────┘
                               ↓
                          NB03 (explain)
                               ↓
                          NB04 (measure — offline only)
```

The key insight: **analyzers run for ALL operating modes**. Suitability scoring happens whether it's normal intake, audit, or emergency. The audit engine just adds category-specific rules on top of the same analyzer outputs.

---

## Part 7: Guardrails

| Risk | Guardrail |
|------|-----------|
| Agency customization turns into code forks | All agency variance flows through `AgencySuitabilityPolicy` — no `if agency_id ==` branches |
| ML scorer weakens trust | ML can adjust `score` but cannot bypass hard exclusions, document blockers, or operating-mode routing |
| External activity API contaminates core logic | Everything normalizes to `ActivityDefinition` before scoring — downstream never sees the source |
| Audit suite measures only aggregate pass/fail | Gate on **per-category** precision/recall + must-catch fixtures, not only overall score |
| Packet pollution from audit data | Audit artifacts live in `AuditSubject`, not in traveler `facts` |
| `risk_flags` grows as untyped dict soup | `StructuredRisk` is the real contract; dict format is backward-compat projection only |
| Traveler memory becomes hidden side effect | Memory enters as `TravelerMemorySnapshot` — explicit input to scoring, not injected state |

---

## Part 8: Open Sub-Decisions (For Next Discussion)

| # | Question | Options | Depends On |
|---|----------|---------|------------|
| D4.1 | Where does the static activity catalog start? | Destination-scoped tables (Singapore, Bali, etc.) vs. activity-type-only tables | Pilot agency destination coverage |
| D4.2 | How granular is the initial suitability matrix? | ~20 activity types × 5 traveler types (100 cells) vs. tag-based matching | Fixture authoring effort |
| D4.3 | Does `suitability/` go under `src/intake/` or `src/planning/`? | Intake (current layer) vs. new planning layer | Whether suitability is intake judgment or planning judgment |
| D6.1 | Who authors the first 40-60 fixtures? | Manual curation vs. semi-automated from real agency scenarios | Access to real itineraries |
| D6.2 | What's the fixture format? | Python dataclasses vs. JSON/YAML files | Tooling preference, CI integration |

---

*This architecture is designed to evolve. Each phase adds capabilities through registries and protocols without replacing contracts. The eval suite serves as both quality gate and roadmap — it shows exactly what the system can and cannot do at any point, and new capabilities are proven by moving their category from `planned` → `shadow` → `gating`.*
