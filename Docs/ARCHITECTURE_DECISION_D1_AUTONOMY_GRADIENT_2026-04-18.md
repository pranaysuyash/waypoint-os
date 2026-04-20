# Architecture Decision: D1 — Agency Autonomy Gradient

**Date**: 2026-04-18
**Status**: Decision document — core decision locked, adaptive autonomy pending deep dive
**Source**: `Docs/DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` Thread 1 ("Copilot, Not Replacement")
**Cross-references**:
- `Docs/V02_GOVERNING_PRINCIPLES.md` (decision_state axis, operating_mode axis)
- `Docs/PRODUCT_VISION_AND_MODEL.md` L76 ("Workspace where AI is embedded, not a replacement")
- `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` L118 (human override protocol)
- `src/intake/decision.py` L145-151 (DECISION_STATES), L212-231 (DecisionResult)
- `src/intake/packet_models.py` L288-292 (operating_mode, decision_state fields)
- `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` (suitability scoring tiers)
- `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` (cache → rule graduation, feedback loops)

---

## The Problem

The system produces five `decision_state` values (`src/intake/decision.py` L145-151):
- `ASK_FOLLOWUP`
- `PROCEED_INTERNAL_DRAFT`
- `PROCEED_TRAVELER_SAFE`
- `BRANCH_OPTIONS`
- `STOP_NEEDS_REVIEW`

These drive what NB03 generates — but there is **no configurable gate** between the system's verdict and what happens next. The system exercises judgment (budget feasibility, suitability scoring, risk flags, commercial decisions) but the trust boundary between "system decided" and "human must approve" is implicit and hardcoded.

### The Tension (from Thesis Deep Dive Thread 1)

As the system's judgment capabilities grow (D4 suitability engine, D6 audit suite, LLM contextual scoring), the "copilot" framing bumps against reality:

| Scenario | Risk | Mitigation |
|----------|------|------------|
| System auto-proceeds on `PROCEED_TRAVELER_SAFE` without human review | Agency feels bypassed on quality control | Require explicit "approve and send" gate — configurable |
| System flags `STOP_NEEDS_REVIEW` on a trip the agent was confident about | Agent loses trust: "It doesn't understand my client" | Show evidence (not just verdict), let agent override with logged rationale |
| Junior agent uses system as crutch, never develops planning skill | Agency owner sees tool as replacing training, not augmenting | "Learning mode" that explains *why* — NB03 presentation concern, future |

### Three Open Questions (from Thread 1)

1. **Autonomy gradient**: Should the system have configurable autonomy levels? → **Answered below: Yes, agency-level policy.**
2. **Override dignity**: When an agent overrides the system, does the system remember? → **Answered below: Yes, feeds learning loop. Deep dive pending on customer+trip classification.**
3. **Positioning evolution**: At what scale does "copilot" become "operating system"? → **Open — marketing/positioning question, not architecture.**

---

## Decision: Agency-Level Autonomy Policy

### Core Contract

```python
@dataclass
class AgencyAutonomyPolicy:
    """Per-agency autonomy configuration — not per-agent, not per-trip."""
    agency_id: str

    # Per decision_state: does this require human approval before acting?
    approval_gates: Dict[str, Literal["auto", "review", "block"]] = field(
        default_factory=lambda: {
            "PROCEED_TRAVELER_SAFE": "review",    # default: agent reviews before send
            "PROCEED_INTERNAL_DRAFT": "auto",      # internal drafts auto-proceed
            "ASK_FOLLOWUP": "auto",                # follow-up questions auto-surface
            "BRANCH_OPTIONS": "review",            # options require agent selection
            "STOP_NEEDS_REVIEW": "block",          # always blocks — safety invariant
        }
    )

    # Per operating_mode: override gates for specific contexts
    mode_overrides: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            "emergency": {"PROCEED_TRAVELER_SAFE": "block"},  # never auto-proceed in emergency
            "audit": {"PROCEED_INTERNAL_DRAFT": "review"},    # audits always reviewed
        }
    )

    # Suitability-specific: auto-proceed even if suitability warnings exist?
    auto_proceed_with_warnings: bool = False  # False = any warning triggers review gate

    # Override learning: do agent overrides feed back into preferences?
    learn_from_overrides: bool = True
```

### Why Agency-Level (Not Per-Agent, Not Per-Trip)

- **Not per-agent**: The agency owner sets the trust boundary for the whole operation. A junior agent shouldn't be able to set themselves to "auto" mode — that's the owner's call.
- **Not per-trip**: Trip-level autonomy creates cognitive overhead ("did I set this trip to auto or review?"). Agency-wide defaults with `mode_overrides` for specific contexts covers real use cases.
- **Future per-agent layer**: If needed later, an `agent_role` field (e.g., `"senior_planner"` vs `"junior"`) can unlock role-based policy within the agency policy — but this is additive, not needed now.

### Safety Invariant (Non-Negotiable)

**`STOP_NEEDS_REVIEW` is always `"block"`.** No configuration can override this.

This state means the system detected a condition that requires human judgment — visa crisis, budget impossibility, safety exclusion, emergency. Auto-proceeding here is a liability risk. The config controls the *other* four states.

### Where It Lives Architecturally

This is NOT a new axis. It's a **policy layer on top of the existing two axes** (`decision_state` × `operating_mode`).

```
NB02 (judgment) produces → DecisionResult with decision_state + operating_mode
                                    ↓
                          AgencyAutonomyPolicy gate
                          ├── "auto"   → NB03 proceeds, output delivered
                          ├── "review" → NB03 generates draft, queued for agent approval
                          └── "block"  → NB03 generates explanation, agent must act
                                    ↓
                          NB03 (session behavior)
```

**Layer owner**: NB02/NB03 boundary. The policy sits between judgment and session behavior. NB02 doesn't know about it. NB03 reads it to determine presentation mode.

### How It Connects to Existing Code

- `DecisionResult` (`src/intake/decision.py` L212-231) already has `decision_state` and `operating_mode`. The autonomy policy reads these fields.
- Override events logged in packet `events` trail (`src/intake/packet_models.py` L315-320) with `event_type="agent_override"`, rationale, and timestamp.
- `AuthorityLevel.MANUAL_OVERRIDE` (`src/intake/packet_models.py` L37) is the highest authority — agent overrides already have the correct authority ranking.

---

## Discussion: Adaptive Autonomy via Customer+Trip Classification

### The Owner's Insight

> "We can fine-tune or give more autonomy based on learning. We start looking at the customer+trip classification problem and switch on/off controls later."

This reframes autonomy from a **static config** to a **learned adaptive policy**. The agency sets initial defaults, but the system can suggest loosening or tightening controls based on observed patterns.

### How This Would Work (Conceptual)

```
Phase 1 (Now): Static AgencyAutonomyPolicy
  → Agency owner sets "review" for PROCEED_TRAVELER_SAFE
  → All trips go through review gate

Phase 2 (After learning loop): Classification-informed suggestions
  → System observes: "For 'couple + Bali + mid-budget' trips,
     agent approved 47/50 without changes (94% pass-through)"
  → System suggests: "Auto-proceed for this trip classification?"
  → Owner approves → policy relaxes for that classification

Phase 3 (Mature): Adaptive policy with guardrails
  → Autonomy level varies by (customer_type × trip_classification × confidence)
  → High-confidence routine trips: auto-proceed
  → Novel/complex/high-value trips: always review
  → System tracks when auto-proceeded trips get post-hoc corrections → tightens
```

### The Customer+Trip Classification Problem (Deep Dive Needed)

This is the prerequisite for adaptive autonomy. The system needs to classify trips along dimensions that predict "does this need human review?":

**Classification dimensions (candidate)**:

| Dimension | Source | Examples |
|-----------|--------|----------|
| Trip complexity | Derived from packet | Solo/couple (simple) vs. mixed_group/coordinator_group (complex) |
| Destination familiarity | Agency history | "We've done 200 Bali trips" (high) vs. "First Tibet trip" (low) |
| Budget sensitivity | Budget vs. destination benchmarks | Comfortable margin (low) vs. borderline (high) |
| Customer type | Traveler memory + lifecycle | Repeat client (known preferences) vs. new referral (unknown) |
| Suitability risk | D4 tier outputs | No flags (low) vs. multiple warnings (high) |
| Composition complexity | Participant count + types | 2 adults (simple) vs. elderly + toddler + 3 families (complex) |
| Time pressure | Urgency signals | 6 months out (low) vs. 2 weeks (high) |

**The classification output would be**:
```python
@dataclass
class TripClassification:
    """Derived classification that informs autonomy policy."""
    complexity: Literal["routine", "moderate", "complex", "novel"]
    confidence: float  # how confident is the classification itself
    review_recommendation: Literal["auto", "review", "block"]
    reasoning: List[str]  # why this classification
```

**Connection to existing contracts**:
- `CanonicalPacket` already has composition (`SubGroup`), budget, destination, operating_mode
- `DecisionResult` already has `confidence_score` (L225), risk_flags, hard/soft blockers
- `TravelerMemorySnapshot` (D4 contract) has prior trips, preferences, recency
- `AgencySuitabilityPolicy` (D4 contract) has agency-level weights

**Connection to D5 (Override Learning)**:
- Agent overrides on classified-as-"auto" trips = signal that classification was wrong
- Override patterns feed `record_feedback()` on the classification cache (same pattern as `HybridDecisionEngine` success rate tracking)
- High override rate for a trip class → system tightens autonomy for that class
- Low override rate → system suggests loosening

### What Needs Deep Diving

| # | Question | Depends On |
|---|----------|------------|
| D1.1 | What are the exact classification dimensions and weights? | Real trip data from pilot — need to observe what correlates with "agent changed the output" |
| D1.2 | Is classification deterministic (rules) or ML-assisted? | Volume of training data. Rules first, ML when patterns emerge from cache. |
| D1.3 | Does classification happen at NB01 (intake) or NB02 (judgment)? | Whether classification needs judgment outputs (risk flags, suitability) or just intake facts |
| D1.4 | How does the owner approve/reject autonomy suggestions? | Frontend workspace — needs an "autonomy settings" surface |
| D1.5 | What's the feedback latency? | Does agent override immediately adjust, or batch-update weekly? |

These are **deferred for deep dive after pilot data is available**. The static `AgencyAutonomyPolicy` is the foundation — adaptive classification layers on top without replacing it.

---

## Implementation Timing

| Component | When | Depends On |
|-----------|------|------------|
| `AgencyAutonomyPolicy` contract (dataclass) | Design now, implement with agency config | `AgencySuitabilityPolicy` (D4) — similar config pattern |
| NB02/NB03 gate logic | Implement with frontend approval UX | `FRONTEND_WORKFLOW_IMPLEMENTATION_CHECKLIST_2026-04-16.md` |
| Override event logging | Implement with packet event trail | Already partially exists (`packet_models.py` events) |
| `TripClassification` contract | Design after pilot data | Real override patterns from running system |
| Adaptive autonomy (classification → policy adjustment) | After sufficient override data | D1.1-D1.5 deep dive, customer lifecycle (Gap #06) |

---

## Remaining Open Items (From Thesis Deep Dive)

| # | Decision | Status | Next Step |
|---|----------|--------|-----------|
| D1 | Autonomy gradient | ✅ Core decided (agency-level policy). Adaptive autonomy pending deep dive. | Deep dive customer+trip classification when pilot data available |
| D2 | Free engine target persona | ✅ Decided (`ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md`). Shared pipeline, empowerment framing. | Implementation sequenced by D6 eval precision gates |
| D3 | Sourcing hierarchy configurability | ✅ Contract decided (`ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY_2026-04-18.md`). Implementation blocked on Gap #01. | Implement with Gap #01 vendor/supplier models |
| D5 | Override learning | ✅ Contract decided (`ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`). Phased by Gap #02 + Gap #06. | Phase 1 with persistence, Phase 2 with lifecycle |
| — | Plugin system | ⬜ Draft exists (`PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md`) | Discuss — architecture decision needed |
| — | D4/D6 implementation | ⬜ Open | Migration Steps 1-5 from parent architecture doc |

---

*This decision establishes agency-level autonomy as a policy config, not code branches. The safety invariant (`STOP_NEEDS_REVIEW` always blocks) is non-negotiable. The adaptive autonomy layer — where the system learns which trip types need review and which can auto-proceed — is the compounding improvement path, gated on the customer+trip classification problem that requires pilot data to solve properly.*
