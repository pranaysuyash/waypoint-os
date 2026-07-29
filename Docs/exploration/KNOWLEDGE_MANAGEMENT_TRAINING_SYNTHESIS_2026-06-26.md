# Knowledge Management & Training — Synthesis (#23)

**Date**: 2026-06-26
**Status**: Exploration synthesis complete. Ready for scoping.
**Parent index**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) §23
**Priority**: 🟡 Medium Priority (Enables agency scale)

---

## 1. Executive Summary

Knowledge Management & Training (#23) has **directly applicable research existing** across six prior exploration documents. This synthesis consolidates that work into a unified framework covering three sub-domains:

1. **Institutional Memory** — How the system encodes and reuses agency-specific knowledge across trips, agents, and time
2. **Skill Capture & Propagation** — How tribal knowledge moves from senior agents into system rules, templates, and playbooks
3. **Training & Ramp-Up** — How junior agents learn the agency's way of doing things through AI-assisted guidance

**Key insight**: The project already has 80% of the architectural thinking needed. What's missing is a unified data model, a runtime for playbook execution, and a surfaced training mode in the operator workspace.

---

## 2. Existing Research Backlog

The following prior documents directly contribute to this topic. Each has been reviewed and its relevant content is synthesized below.

| Source | Date | Relevance to #23 |
|--------|------|-----------------|
| [INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS](../context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md) | 2026-04-14 | Core architecture — template genome, supplier intelligence, pricing memory, playbook engine, customer genome |
| [AGENCY_WORKFORCE_GAMIFICATION_AND_LEARNING](../product_features/AGENCY_WORKFORCE_GAMIFICATION_AND_LEARNING.md) | (undated) | Crisis simulation war games, knowledge bounty system, real-time coaching |
| [KDD_KNOWLEDGE_DISCOVERY_EXPLORATION](./KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md) | 2026-05-18 | Override mining → continuous improvement loop; suitability signal mining from successful trips |
| [PRIORITY_SCORING_LEARNING_LAYER_EXPLORATION](./PRIORITY_SCORING_LEARNING_LAYER_EXPLORATION_2026-05-18.md) | 2026-05-18 | Learning from operator behavior to adjust priority scoring — pattern applies to any learned adjustment |
| [TRAVEL_AI_CONTINUOUS_LEARNING_AND_FEEDBACK_LOOPS](../industry_domain/travel_technology/TRAVEL_AI_CONTINUOUS_LEARNING_AND_FEEDBACK_LOOPS.md) | (undated) | Continuous learning architecture, feedback loops, model monitoring |
| [SIMULATED_USER_INTERVIEW_AGENCY_OWNER](../SIMULATED_USER_INTERVIEW_AGENCY_OWNER_2026-04-28.md) | 2026-04-28 | Owner pain: junior training costs ₹2-3L per hire; juniors quit within 18 months |
| [AGENCY_INTERNAL_DATA](../research/AGENCY_INTERNAL_DATA.md) | (undated) | 7 categories of internal data: preferred suppliers, tribal knowledge, historical patterns, margins, customer memory, packages, reliability |
| [UX_USER_JOURNEYS_AND_AHA_MOMENTS](../UX_USER_JOURNEYS_AND_AHA_MOMENTS.md) | (undated) | Junior agent journey: "I'm learning, not just copying" — learning as a core product value |
| [P2_TRAINING_TIME_PROBLEM_OBSERVABILITY](../reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md) | 2026-04-23 | Training scenario partially validated; backend works, UX layer requires hardening |

---

## 3. Sub-Domain 1: Institutional Memory

### 3.1 Core Architecture (from INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS)

The foundational architecture proposes eight memory layers:

| Layer | Description | Current Status |
|-------|-------------|---------------|
| Template Genome | Reusable trip templates by destination × traveler profile × budget tier | Not implemented — additive schema proposed for `CanonicalPacket` |
| Supplier Intelligence Graph | Supplier reliability, issue rates, trip-type fit, commission strength | Partially covered by `spine_api/services/public_checker_service.py` decision baseline categories; no persistent graph |
| Pricing Memory Engine | Quoted vs actual costs + margin over time with seasonality | Not implemented — would feed from `FIN_SPEC_*` research docs |
| Customer Genome | Repeat-customer preferences, complaint history, LTV | Not implemented — travel history exists in TripStore but no structured profile |
| Playbook Engine | Codified recurring disruptions with resolution steps | Not implemented — proposed as `PlaybookExecution` event model |
| Content Block Library | Modular communication blocks (visa rules, packing advisories) | Not implemented — strategy briefs exist but are dynamically generated |
| Team Coverage Graph | Active load, expertise, backup assignees | Partially covered by assignment signals taxonomy |
| Post-Trip Learning Loop | Structured retrospectives feeding back into templates | Not implemented — no post-trip feedback mechanism |

### 3.2 Additive Data Model (from INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS)

Proposed additive fields on `CanonicalPacket` (no breaking changes):
```python
template_id: Optional[str]
template_match: Optional[TemplateMatch]
template_customizations: List[TemplateCustomization]
supplier_bookings: Dict[str, SupplierBooking]
customer_profile_ref: Optional[str]
playbook_events: List[PlaybookExecution]
```

Companion model groups (new modules):
- `template_models.py` — TemplateGenome, TemplateMatch, TemplateCustomization
- `supplier_models.py` — SupplierProfile, SupplierPerformance, SupplierBooking
- `pricing_models.py` — QuoteHistory, MarginDriftSignal
- `customer_models.py` — CustomerGenome
- `playbook_models.py` — Playbook, PlaybookExecution, ResolutionOutcome

### 3.3 Agency Internal Data (from AGENCY_INTERNAL_DATA research)

Seven categories of internal data that agencies possess:

1. **Preferred suppliers** — negotiated rates, relationships, known quality
2. **Tribal knowledge** — "reality checks" and hidden issues (which hotels deliver, which have thin walls)
3. **Historical booking patterns** — what customers actually book vs what they ask for
4. **Margins and commercial data** — actual vs quoted costs, hidden markup opportunities
5. **Customer memory** — past trips, preferences, complaint history
6. **Package templates** — successful itinerary combinations by destination/type
7. **Vendor reliability scores** — on-time delivery, customer satisfaction, issue rates

**Gap**: These data types are acknowledged but not yet modeled in the database or captured through the operator workflow.

---

## 4. Sub-Domain 2: Skill Capture & Propagation

### 4.1 The "Knowledge Bounty" System (from AGENCY_WORKFORCE_GAMIFICATION_AND_LEARNING)

How tribal knowledge moves from senior agents into the system:

- **Codification trigger**: When a senior agent discovers a reusable pattern (supplier hack, negotiation tactic, common issue workaround), they can capture it as a system rule
- **Incentive mechanism**: "Platform Credits" for codified knowledge that generates measurable value (time saved, margin preserved, issues avoided)
- **Routing by skill score**: High-complexity/high-margin leads routed to agents with highest verified skill score in that category
- **"Expertise Ledger"**: Immutable log of agent certifications, successful high-stakes resolutions, and demonstrated specializations

### 4.2 Override Mining → Continuous Improvement (from KDD exploration)

The highest-leverage KDD application feeds directly into skill capture:

- Every operator override of an AI decision is a labeled correction signal
- Clustering overrides by (decision_delta × intake_features) reveals systematic failure modes
- Each tight cluster becomes either a prompt patch, a new validation rule, or a training example
- Weekly digest: "this week the AI was systematically wrong about X, Y, Z"

**Gap**: The override audit schema needs a structured `decision_delta` field to enable effective mining. Current override logging captures reason text but not structured before/after comparison.

### 4.3 Real-Time Coaching (from AGENCY_WORKFORCE_GAMIFICATION_AND_LEARNING)

The system can teach while it works:

- **Compliance nudges**: "Did you check the Visa requirements for this 8-hour layover?" — surfaced at authoring time
- **Markup coaching**: "You're pricing this 10% below market average" — real-time margin awareness
- **Adaptive micro-learning**: System identifies weak points (e.g., frequent errors in split PNRs) and serves 5-minute training modules during idle moments
- **"Correct-as-you-Type"** : AI suggests improvements as the agent drafts itineraries

**Gap**: No runtime coaching engine exists. The existing strategy/preview layer generates output but doesn't evaluate or coach the operator during authoring.

---

## 5. Sub-Domain 3: Training & Ramp-Up

### 5.1 The Core Problem (from SIMULATED_USER_INTERVIEW_AGENCY_OWNER)

> "Most juniors quit within 18 months. The job is harder than they expected. I invest a year training someone, and they leave. That's the real cost."
> — Agency owner interview, 2026-04-28

**Key numbers from the interview**:
- 12-month ramp to full productivity for a junior agent
- ₹2-3L saved per hire if ramp reduces to 4 months
- ₹50K-1L saved per month by preventing 5 margin-leak incidents
- Willingness to pay ₹15,000-25,000/month for training + team features

### 5.2 Shadow Mode / Learning from Seniors (from interview)

> "Shadow Mode" (learning from senior decisions) should be prioritized as a distinguishing feature.

Proposed "Decision Capture" system:
- Every owner edit/suggestion on a proposal is logged with rationale
- Over time, this becomes a training corpus for the "Shadow Owner" mode
- Preserves the trust model: "Prepared by Waypoint, accepted by the operator"

### 5.3 Crisis Simulations (from AGENCY_WORKFORCE_GAMIFICATION_AND_LEARNING)

Synthetic disruptions for sandbox training:

- Generate "Ghost PNRs" with realistic crisis scenarios
  - "Client at the airport, flight cancelled, all hotels full"
  - "Medical emergency mid-trip"
  - "Natural disaster at destination"
- Agents solve in sandbox mode with speed + accuracy scoring
- Learning outcomes feed back into skill scores and training recommendations

### 5.4 Junior Agent Learning Journey (from UX journeys)

From the persona journey maps:
- **Before**: "I don't know what to do" → overwhelmed, afraid of mistakes
- **During**: Guided workflows with contextual help, best-practice suggestions, approval cues
- **After**: "I feel like I have a senior looking over my shoulder, but in a good way. I'm actually learning."

**Training mode UI concept** (from UX_DASHBOARDS_BY_PERSONA):
```
┌──────────────────────────────────────────────┐
│  TRAINING MODE: ON                           │
│                                              │
│  💡 LEARNING OPPORTUNITY: Repeat Customer     │
│  This client has booked 3 trips with us.      │
│  Check their travel history before quoting.    │
└──────────────────────────────────────────────┘
```

### 5.5 P2 Training Time Problem — Validation Status

The P2 scenario was validated in the 2026-04-23 observability report:
- Backend behavior: no blockers found in training-path code
- UX layer: "requires hardening" — the guided learning surfaces are not yet implemented
- Key tested behaviors:
  - Low-confidence → cautious tone (pass)
  - High-confidence → direct tone (pass)
  - Training scenario partially validated

---

## 6. Unified Data Model Proposal

### 6.1 New Tables / Collections

Drawing from all six sources, the minimal schema needed:

```python
# ---- Institutional Memory ----

@dataclass(slots=True)
class TripTemplate:
    """Reusable trip structure by context."""
    id: str
    agency_id: str
    destination: str
    trip_type: str
    budget_tier: str            # budget / mid / premium / luxury
    traveler_shape: str         # solo / couple / family / group
    base_itinerary: dict        # canonical day-by-day structure
    typical_margin_pct: float
    seasonality: dict           # best months, pricing multipliers
    issue_rate: float           # how often this template needs rework
    usage_count: int
    last_used: Optional[str]
    tags: list[str]             # keywords for search + matching


@dataclass(slots=True)
class SupplierMemory:
    """Agency-specific supplier performance and relationship."""
    supplier_id: str
    agency_id: str
    name: str
    category: str               # hotel / airline / transport / activity
    negotiated_rates: dict      # rate type → amount, valid through
    commission_pct: float
    reliability_score: float     # 0-1, computed from issue rate
    issue_rate: float           # fraction of bookings with issues
    trip_type_fit: dict         # trip type → fit score (0-1)
    last_used: Optional[str]
    notes: list[str]            # tribal knowledge capture


@dataclass(slots=True)
class Playbook:
    """Codified resolution for recurring operational scenarios."""
    id: str
    agency_id: str
    trigger_type: str           # driver_no_show / flight_cancellation / visa_urgency
    title: str
    steps: list[dict]           # ordered resolution steps with owner + SLA
    success_rate: float
    avg_resolution_time_min: int
    templates: list[str]        # communication templates
    last_triggered: Optional[str]


# ---- Skill & Training ----

@dataclass(slots=True)
class AgentSkill:
    """Verified skill record for an operator."""
    agent_id: str
    agency_id: str
    skill_category: str         # luxury_maldives / corporate_singapore / visa_processing
    proficiency: float          # 0-1, computed from outcomes
    certification_level: str    # trainee / competent / expert / authority
    case_count: int
    avg_margin_pct: float
    last_demonstrated: Optional[str]


@dataclass(slots=True)
class TrainingModule:
    """Micro-learning module served contextually."""
    id: str
    category: str               # gds_pnr / visa_rules / margin_calc
    title: str
    content_type: str           # text / video / interactive
    duration_min: int
    completion_rate: float
    effectiveness_score: float  # pre/post assessment delta
    trigger_pattern: str        # what error pattern triggers this module


# ---- Learning Loop ----

@dataclass(slots=True)
class OverrideEvent:
    """Structured record of an operator override of an AI decision."""
    trip_id: str
    agent_id: str
    ai_decision: dict           # what the AI decided
    operator_decision: dict     # what the operator chose instead
    decision_delta: dict        # structured diff (added fields)
    reason_category: str        # pricing / suitability / logistics / policy
    reason_text: str
    intake_features: dict       # context at time of decision
    created_at: str
```

### 6.2 Integration with Existing Models

| Existing Model | New Relationship |
|----------------|-----------------|
| `CanonicalPacket` | Gains `template_id`, `supplier_bookings`, `customer_profile_ref`, `playbook_events` (additive fields) |
| `DecisionResult` | Override events reference the AI decision path |
| `SpecialtyKnowledgeHit` (FrontierResult) | Existing structured risk knowledge — feeds into Skill model |
| `AssignmentStore` | Assignment signals → AgentSkill proficiency calculation |
| `AuditStore` | Override events extend existing audit trail with structured deltas |
| `TripStore` | Trips reference templates; template usage updates from trip completion |

---

## 7. Gaps Identified vs Existing Capabilities

| Capability | Existing | Gap |
|------------|----------|-----|
| Agent skill signals (assignment taxonomy) | ✅ `learning_only` signals defined | No runtime that computes or surfaces them |
| Override audit logging | ✅ Events written | No structured `decision_delta` — can't mine patterns without it |
| Trip templates | ❌ Not yet | No template model, no matching, no versioning |
| Playbook execution | ❌ Not yet | No playbook storage or runtime |
| Training mode UI | ❌ Not yet | No in-app guided learning surfaces |
| Knowledge bounty capture | ❌ Not yet | No workflow for senior agents to codify knowledge |
| Crisis simulations | ❌ Not yet | No sandbox environment with synthetic scenarios |
| Continuous learning loop (override → improvement) | 🔶 KDD pipeline designed | Not implemented; requires `decision_delta` field first |
| Post-trip learning | ❌ Not yet | No structured retrospective or template feedback loop |
| Customer memory | 🔶 Trip history exists | No structured profile model (CustomerGenome) |

---

## 8. Recommended Sequencing

### Phase 1 (2-3 days) — Foundation: Override Mining + Decision Delta
**Precondition for everything else.** Without structured override data, no learning loop exists.

1. Add `decision_delta` field to override audit schema
2. Ship KDD v0 override-corpus mining (see [KDD_V0_OVERRIDE_MINING_SCOPE](./KDD_V0_OVERRIDE_MINING_SCOPE_2026-05-18.md))
3. Surface weekly "systematic failure modes" digest

### Phase 2 (3-4 days) — Template + Supplier Memory
**Highest quick-win for operator productivity.**

1. Implement `TripTemplate` and `SupplierMemory` models
2. Add `template_id`, `supplier_bookings` to `CanonicalPacket`
3. Build template matching at intake time (NB02 shortlist)
4. Surface template + supplier memory in trip workspace

### Phase 3 (3-5 days) — Training Mode + Real-Time Coaching
**Directly addresses the P2 training problem.**

1. Add "Training Mode" toggle to operator workspace
2. Implement compliance nudges and markup coaching at strategy authoring time
3. Serve adaptive micro-learning modules from error pattern detection
4. Surface "Learning Opportunity" cards in trip workspace

### Phase 4 (5-7 days) — Playbook Engine + Crisis Simulations
**Longer-term differentiator for agency retention.**

1. Implement `Playbook` model and execution runtime
2. Build playbook-trigger-from-event wiring (disruption events auto-suggest playbook)
3. Create sandbox crisis scenario generator
4. Build speed + accuracy scoring for simulation mode

### Phase 5 (Ongoing) — Post-Trip Learning Loop
**Closes the cycle.**

1. Add post-trip structured retrospectives
2. Feed retrospective outcomes back into templates, supplier scores, pricing memory
3. Track agent skill proficiency over time from real outcomes

---

## 9. Architectural Constraints

From the existing research, these constraints must be respected:

| Constraint | Source | Rationale |
|------------|--------|-----------|
| Additive only on existing models | INSTITUTIONAL_MEMORY | No breaking changes to `CanonicalPacket` |
| Override layer is additive, not replacement | KDD | Rule-based score dominates; learned residual is bounded |
| No parallel analytics stack | KDD | Mining reads existing audit/analytics; does not duplicate |
| Training mode must not block production | Agency owner interview | Junior agents need guardrails, not gates |
| All learned adjustments must be explainable | PRIORITY_SCORING | Every decision decomposes into rule + learned + evidence count |
| Per-agency isolation for mined patterns | KDD | Cross-agency only on aggregated, anonymized features |
| Pattern support/confidence always surfaced | KDD | Avoids over-trust in low-N patterns |

---

## 10. Key Design Decisions Needed

1. **Where does the template matching run?** — In NB02 (shortlist) or as a separate service? If in NB02, needs to be a configurable gate (not required for prompt requests).
2. **Who owns the "Knowledge Bounty" moderation?** — Is codified knowledge auto-accepted, peer-reviewed, or owner-approved? Trust vs speed trade-off.
3. **Training mode: opt-in vs always-on for junior agents?** — Junior agents likely want it always-on; seniors may find it intrusive.
4. **Crisis simulations: pre-built library or LLM-generated?** — Pre-built ensures deterministic scoring; LLM-generated allows infinite variety but needs human-verified answer keys.
5. **Post-trip retrospective: mandatory or optional?** — Mandatory gives complete data; optional gets lower completion but higher signal quality from motivated respondents.
6. **Template versioning: git-based or database-based?** — Git handles branching/merging well; database handles per-agency isolation better.

---

## 11. Related Topics

| Topic | Relationship |
|-------|-------------|
| **Onboarding & Agency Setup (#22)** | First-mile user experience feeds into training mode; templates are created during setup |
| **Agency Internal Data (#16)** | Internal data categories directly map to Knowledge Management model |
| **Supplier Management (#31)** | Supplier memory model is a shared dependency |
| **KDD Exploration (#6b)** | Override mining is the learning loop engine; v0 must ship before Phase 1 |
| **Priority Scoring (#20)** | Learned residuals pattern (additive, bounded, explainable) applies here too |
| **Testing & QA (#24)** | Training simulations need answer keys and scoring rubrics |
| **Reporting & Analytics (#28)** | Agent skill proficiency and learning progress are owner dashboard inputs |
| **Real-World Validation (#7)** | Training effectiveness needs measurement against real operator outcomes |

---

## 12. Decision Recommendation

**Proceed to Phase 1 scoping immediately**, because:
- Override mining (the foundation) is already designed in KDD v0
- The `decision_delta` field is a small, backward-compatible schema change
- It directly feeds the AI-override launch blocker identified in AGENTS.md
- No other phase depends on new infrastructure

**Gate Phase 2 (templates + supplier memory) behind Phase 1 completion**, because:
- Templates need override-mining insights to know which trip patterns matter most
- Supplier memory needs the KDD pipeline to compute reliability scores from actual booking data
- Without the learning loop foundation, templates become static libraries — not knowledge management

**Defer Phases 3-5 until Phases 1-2 are in production with real usage data**, because:
- Training mode effectiveness can't be measured without real operator behavior
- Playbook engine needs real disruption patterns to codify
- Post-trip learning needs actual trip completions and outcomes

---

*This is a synthesis document consolidating existing research. Implementation decisions are recommendations, not commitments. Update with evidence as work progresses.*
