# Waypoint OS — External Review Brief
**For: ChatGPT / Claude / Gemini or any external reviewer**  
**Date**: 2026-04-28  
**Author**: Project team  
**Format**: Self-contained. No prior context required. Read top to bottom.

---

## 0. How to Use This Brief

This document is a comprehensive brief for an AI model or technical reviewer to evaluate the architecture, product decisions, and strategic direction of Waypoint OS. It is intentionally detailed and opinionated. We want critical, first-principles feedback — not validation.

At the end of each section are **specific review questions**. Please answer all of them. Do not soften your answers. Point out what's broken, what's over-engineered, and what's missing.

---

## 1. What Is This System?

**Waypoint OS** is an AI-assisted operations platform for boutique travel agencies. It is explicitly NOT a consumer trip planner.

### The Target User

A solo travel agent — call her Priya — runs a boutique agency. She has 12 WhatsApp conversations open right now. Three new inquiries came in last night. A family called the Sharmas needs a proposal by noon.

Her current stack: WhatsApp for communication, Google Sheets for tracking, and her own memory for everything else. All the knowledge about which vendors she trusts, which hotels work for Indian families in Singapore, which clients are window-shoppers vs. serious buyers — it lives entirely in her head. When she quits or gets sick, it's gone.

**The agency model she operates within:**
- She doesn't search the internet for the "best" hotel. She has preferred suppliers she has negotiated rates with, and she books from those first.
- Her sourcing hierarchy is: Internal Standard Packages → Preferred Suppliers → Network/Consortium Partners → Open Market (last resort, squeezes margin).
- A trip to Singapore for a family of 5 (2 adults, 1 elderly parent, 1 child age 8, 1 toddler age 2) involves: per-person activity suitability checks (grandma can't do Universal Studios, toddler ticket is wasted), budget decomposition by bucket (flights, hotel, food, activities, shopping, buffer), visa checks for the nationality mix, and pacing logic (6 activities in one day = disaster for that group).
- She operates under real commercial pressure: margin, conversion rate, and not wasting client time on impossible itineraries.

**What Priya actually needs the system to do:**
1. Read her messy WhatsApp note and extract the structured facts (party composition, budget, dates, constraints, signals)
2. Tell her what's missing or contradictory before she wastes time
3. Tell her if the budget is even feasible for the destination and group type
4. Draft the clarification questions she'd ask anyway
5. Build the first-pass itinerary structure so she's editing, not starting from scratch
6. Flag that grandma can't do the theme park before the Sharma family books
7. Proactively tell her that the Johnson lead has been silent for 72 hours and draft a follow-up
8. Surface which trips are stuck or at risk across all her open conversations simultaneously

**What the system is NOT for:**
- Autonomous trip booking without human approval
- Consumer-facing trip planning (no B2C)
- Replacing Priya's relationship with the client — she owns that

---

## 2. Why "Agentic" (The Strategic Bet)

The product was conceived as an "Agency Copilot" — AI embedded in Priya's workflow. The language has evolved toward "agentic." We need honest feedback on whether this bet is correct.

### The Agentic Hypothesis
> The system should be able to take initiative on routine, well-defined sub-tasks — fetching missing data, flagging risks, drafting follow-ups, detecting ghost leads — without Priya explicitly asking each time.

This is NOT claiming full autonomy. The model is:
- **Narrow scope**: Each "agent" handles one class of task (communication drafts, external data lookup, quality audit)
- **Event-triggered**: Agents activate when a lifecycle state change occurs, not on every input
- **Suggestion posture**: Agents produce drafts/suggestions for human approval, not autonomous actions
- **Auditable**: Every agent action is logged with rationale

The alternative to agentic behavior would be a pure "tool" model — Priya explicitly asks for everything. We believe the value gap between "tool you call" and "copilot that notices things" is large enough to justify the architectural complexity.

### The Core Agentic Design Questions We Need Answered
1. Is this the right framing of "agentic" for this use case?
2. Should the first version be tools-only (explicit invocation), with agentic behavior added after trust is established?
3. Where does "initiative" create more risk than value in this specific domain?

---

## 3. What Has Actually Been Built

Be honest here. The documentation is far ahead of the implementation.

### ✅ What Works End-to-End Today

**The Spine Pipeline** (`src/intake/orchestration.py`):
- NB01: Extracts structured facts from freeform text (party composition, budget, dates, travel purpose, constraints, urgency signals)
- NB02: Gap analysis and decision engine — identifies missing/contradictory data, evaluates budget feasibility, assigns decision state
- NB03: Strategy and follow-up — generates targeted clarification questions, builds strategy bundle
- Safety layer: Leakage detection — ensures internal pricing/margin data doesn't appear in traveler-facing outputs
- Fee calculation: Risk-adjusted per-person fee calculation

**The Hybrid Decision Engine** (`src/decision/hybrid_engine.py`):
- Implements a cost-optimized decision hierarchy: Deterministic Rules → LLM Cache → LLM API → Safe Default
- 18 rules covering 5 decision types (budget, destination, visa, mobility, trip type)
- LLM outcomes are cached and promoted to rules after validation ("learning")
- ~34% of decisions handled by deterministic rules (avoiding LLM cost)

**Decision State System** (2 axes, cross-classified):
- `decision_state` axis: `ASK_FOLLOWUP | PROCEED_INTERNAL_DRAFT | PROCEED_TRAVELER_SAFE | BRANCH_OPTIONS | STOP_NEEDS_REVIEW`
- `operating_mode` axis: `normal_intake | audit | emergency | follow_up | cancellation | post_trip | coordinator_group | owner_review`

**Suitability Scoring** (`src/suitability/`):
- Tier 1: Tag-based rules (toddler can't do roller coasters, elderly can't do 6km hikes)
- Tier 2: Trip-context sequence rules (3+ strenuous activities on same day for elderly = flag)
- 23 passing tests, 18-activity catalog

**Lead Lifecycle State Machine** (`src/intake/decision.py` + `packet_models.py`):
- 16 states from `NEW_LEAD` to `LOST/DORMANT`
- Deterministic scoring for ghost risk, window-shopper risk, repeat likelihood, churn risk
- `COMMERCIAL_DECISION` output: `SEND_FOLLOWUP | SET_BOUNDARY | REQUEST_TOKEN | MOVE_TO_NURTURE | REACTIVATE_REPEAT | CLOSE_LOST | ESCALATE_RECOVERY`

**FastAPI Service** (`spine_api/server.py`):
- 4-worker uvicorn server
- File-based persistence (JSON, with `fcntl` + `threading.Lock` for concurrency)
- Multi-tenant model (per-agency data isolation via agency_id routing) — **partially broken, see §4**

**Frontend Shell** (`frontend/`):
- Next.js with 5-screen workbench: Intake, Decision, Strategy, Safety, Feedback
- Dashboard showing pipeline state, recent trips
- Inbox (currently mock data)

**Test Coverage**:
- 53 test files, ~618 backend tests
- Strong coverage of spine stages, decision engine, suitability scoring
- Weak/zero coverage of: API contract integration, frontend pages, E2E flows

### ❌ What Is Documented But Not Built

This is the most important part to understand. The documentation is deeply detailed — 276 documents, full state machine specs, persona process maps, sourcing hierarchy design — but the following are entirely unimplemented:

| System | Status | Business Impact |
|--------|--------|-----------------|
| Persistent trip entity with lifecycle | ❌ Each run is stateless | No memory across sessions |
| Quote/proposal generation | ❌ | Core value prop unmet |
| Output delivery (WhatsApp copy, PDF, share link) | ❌ | Proposal can't be sent |
| Customer entity (repeat detection) | ❌ | Every returning client is a stranger |
| Sourcing hierarchy as decision driver | ❌ (label only) | Doesn't actually prefer preferred suppliers |
| Vendor/supplier model | ❌ | No preferred network exists |
| Activity_matcher.py (wasted spend detection) | ❌ | Suitability flags don't detect wasted ticket spend |
| Owner review queue | ❌ (8-line stub) | Can't supervise junior agents |
| Multi-agent routing / assignment | ❌ | Single-user only |
| Traveler portal (proposal view) | ❌ | Client still gets WhatsApp paste |
| WhatsApp integration | ❌ | Primary channel unconnected |
| Real LLM in the pipeline | ❌ | Pipeline is entirely deterministic rules |
| `src/agents/` (all agents) | ❌ (empty `__init__.py`) | No autonomous behavior exists |

### ⚠️ What Exists as Stub / Mock

| System | Reality |
|--------|---------|
| `frontier_orchestrator.py` ("Ghost Concierge") | Keyword-count heuristic, synchronous, in-memory |
| `checker_agent.py` | 3 if-statements, not an agent |
| `federated_intelligence.py` | In-memory Python list, lost on restart |
| `negotiation_engine.py` | Hardcoded fake prices, no API |
| Frontend inbox and dashboard | Hardcoded mock data, not connected to spine |
| Agency settings (multi-tenant) | `agency_id` always resolves to None in production |

---

## 4. Known Production Bugs

### P0 — Breaks in Live Usage

**Bug 1: agency_id is always None**
```python
# server.py:560
agency_settings = AgencySettingsStore.load("waypoint-hq")  # hardcoded!
# All multi-tenant routing is broken; every run uses the same agency config
```

**Bug 2: LLMUsageGuard not shared across workers**
The daily budget guard for LLM API calls is an in-memory singleton. 4 uvicorn workers = 4 independent guards. Effective limit is 4× configured budget. Currently, there is no way to enforce per-day LLM spend limits in production.

### P1 — Important

**Bug 3: Frontier orchestration blocks the HTTP request thread**
`run_spine_once()` calls `frontier_orchestrator.py` synchronously inside the request. This adds latency to every `/run` call even though the frontier results are not used by the caller.

**Bug 4: No correlation key across three event stores**
`AuditStore`, `TripEventLogger`, and `RunLedger` all emit events independently. Reconstructing "what happened to trip X" requires querying three separate stores with no shared correlation key.

---

## 5. The Core Architectural Decisions Made

### Decision A: Deterministic-First, LLM-Second

The spine pipeline is deterministic. LLMs are used only for: ambiguity compression, follow-up question drafting, and rationale narrative. Hard constraints and gate decisions cannot be overridden by LLM output without human override.

**Rationale**: Agency value is judgment + trust. An incorrect AI decision on budget feasibility or activity suitability damages the relationship. Deterministic rules are explainable, auditable, and free.

**The bet**: This is correct until you hit the ceiling of what rules can handle (nuanced intent, cultural context, traveler preference inference). The hybrid engine's "LLM output graduates to rule" mechanism is the learning path.

### Decision B: Agency-Configurable Sourcing Hierarchy

Each agency has a `SourcingPolicy` that defines their preferred supplier order, margin floors, and category overrides. The system optimizes for "best option within your preferred supply chain," not "global optimum."

**Current state**: The data model exists; the runtime logic does not. The sourcing hierarchy is a label, not a decision driver. There are no suppliers in the system.

### Decision C: Operating Mode × Decision State (2-Axis Classification)

Every trip is classified on two independent axes. This allows the same pipeline to handle emergency re-routing, audit mode, group coordination, owner review, and normal intake using the same data contract — just different routing and output templates.

**The bet**: This elegantly handles scope without monolith growth. The pipeline doesn't change; the mode changes what the pipeline emphasizes.

### Decision D: Per-Person Suitability Over Group-Level Planning

The system evaluates activity utility at an individual level, not a group level. A ₹25,000 Universal Studios day where 3 of 5 people get zero value is flagged as wasted spend.

**Current state**: Binary flags (Tier 1) implemented. Scored compatibility (Tier 2, 0.0–1.0 per person per activity) and wasted spend calculation require `activity_matcher.py` which is not built.

### Decision E: Suggestion Posture for All Agentic Actions

Agents produce suggestions, not autonomous actions. Override requires human approval + logged rationale. Autonomy is configurable per agency (e.g., "always require review" vs. "auto-proceed on PROCEED_TRAVELER_SAFE trips under ₹5L").

**Current state**: The D1 autonomy gradient is specified in `src/intake/gates.py` and tested. The UI controls are not built.

### Decision F: Offline Eval Loop for Safe Learning

An offline eval harness (separate from the live pipeline) evaluates prompt/rule mutations against a golden fixture set before promoting changes. This prevents live regression.

**Current state**: `data/evals/` is empty. The eval harness is not built.

---

## 6. The Agentic Sequencing Problem (The Core Debate)

This is the central tension we want external perspective on.

### What the Current Plan Says
Build the agent infrastructure (`src/agents/` — base agent, orchestrator, registry, state manager, then Scout Agent, Communicator Agent, QA Agent) on top of the existing spine. The agents will be triggered post-spine via async background tasks.

### The Structural Objection
**Real agents require events. Events require persistent state. Persistent state requires a trip lifecycle. The trip lifecycle does not exist.**

The Communicator Agent is supposed to fire when a trip has been `BLOCKED_AWAITING_CLARIFICATION` for >2 hours. But:
- There is no persistent trip entity. Each spine run is stateless.
- The system doesn't know a trip was processed 2 hours ago, because that run's data exists only in a JSON file that is not indexed by time or state.
- There is no event emission when a trip enters a blocking state.
- There is no background scheduler watching for time-elapsed conditions.

The Scout Agent is supposed to fetch real visa/weather data when NB02 flags a data gap. But:
- There is no mechanism to re-run the spine with enriched data after the Scout fetches it.
- The Scout has nowhere to write its results for the next spine run to pick up.

**Without the OS layer (persistent trips, lifecycle states, event emission, state-aware background jobs), the agents have nothing to respond to and nowhere to write.**

### The Counter-Argument
The agent infrastructure (base class, orchestrator, messages, registry) can be built independently of persistence. It defines the contracts. When persistence arrives, the contracts are already in place.

### The Question for External Reviewers
1. Is the counter-argument valid — can you safely build agent infrastructure before persistence?
2. What is the minimum persistence layer that makes agentic behavior genuinely possible (not just structurally possible)?
3. Has this sequencing problem been solved in other systems you know of? How?

---

## 7. First-Principles Questions We Are Asking

### 7.1 Product-Level

1. **Is the "copilot, not replacement" framing durable?** The system already makes significant automated judgments (PROCEED/STOP/ESCALATE). At what point does "copilot" become a marketing fiction vs. the operational reality? Does the agent trust the copilot, or does the copilot become the agent?

2. **Which jobs-to-be-done have been over-engineered?** We have a deeply specified suitability engine. We have zero quote generation. Is the current investment allocation right?

3. **The sourcing hierarchy is the commercial differentiator — should it be built before any agent infrastructure?** A system that recommends from the agency's preferred supplier network first (even with a simple supplier list) is immediately more valuable to an agency owner than agentic ghost risk detection. Is this wrong?

4. **What does the free "audit mode" wedge actually need to work?** We have an `operating_mode: audit` that routes differently. But the audit surface (upload your itinerary, get a risk report) has no wasted spend detection, no pacing analysis, no hotel-activity distance checks. None of the capabilities that make the audit credible are implemented. What's the minimum viable audit that converts?

5. **The persona analysis shows Priya can create a trip but can't: persist it, generate a quote from it, or send it to a client. Is that actually the right MVP scope?** Or should the "workbench" be the whole product for now — a power tool for solo agents who paste into it manually — before we build the OS layer?

### 7.2 Architecture-Level

6. **Is the 2-axis classification system (decision_state × operating_mode) the right abstraction?** It's elegant on paper. In practice, every new scenario requires deciding which axis owns the routing. Does this scale, or does it collapse into a mapping table?

7. **The hybrid decision engine graduates LLM outputs into deterministic rules.** This is essentially a manual online learning mechanism. Is there a risk that promoted rules accumulate technical debt? When does a rule base become unmanageable vs. a model?

8. **The sourcing hierarchy is designed as per-agency configurable (`SourcingPolicy` config object).** But the data model assumes the system has a catalog of suppliers to rank. Without a supplier catalog, the config has nothing to act on. What's the minimum supplier model that makes the sourcing hierarchy real — even for a single agency?

9. **Persistence is currently file-based JSON with `fcntl` and `threading.Lock`.** The plan is PostgreSQL when real user data arrives. At what point does file-based persistence become the bottleneck — is it request volume, concurrency, or PII concerns that force the migration?

10. **The pipeline processes one inquiry synchronously in ~200-800ms.** The agentic model imagines background agents running on multiple trips simultaneously. Is the FastAPI/uvicorn stack the right foundation for that, or does it require a fundamentally different runtime (Celery, ARQ, Temporal)?

### 7.3 Agentic Design-Level

11. **The "suggestion posture" for agents — every agent action requires human approval — is it right for all cases?** Ghost risk detection and follow-up drafting seem right for suggestions. But Scout Agent fetching visa data from Sherpa API is a pure tool call with no ambiguity. Is requiring human approval for non-consequential data fetches the right posture, or does it create approval fatigue?

12. **The agents are imagined as: Scout (data fetching), Communicator (message drafting), QA/Checker (pre-send review), Budget Optimizer, Experience Maximizer, Trip Architect.** Is this the right decomposition? The committee (Budget/Experience/Architecture) sounds like multi-agent deliberation for option generation — but option generation doesn't exist yet. Is building deliberation agents before you have options to deliberate on the right sequence?

13. **The "federated intelligence" concept — agents sharing learned risk signals across trips** (e.g., "Maldives vendors are unreliable during monsoon based on 12 recent trips") — requires cross-trip data. This is inherently a multi-tenant privacy challenge. How do you share aggregate intelligence without leaking trip-specific client data? Has the privacy model for this been designed?

14. **What does "agentic" unlock that a well-designed deterministic pipeline doesn't?** List the specific capabilities that are ONLY possible with autonomous agents and CANNOT be done with explicit tool calls + a smart pipeline. If the list is short, is the complexity justified?

### 7.4 Commercial / GTM-Level

15. **The business model is B2B SaaS, priced by trip volume.** At ₹6,000/month per agency (the current draft pricing), you need ~150 agencies to reach ₹9L/month. How many Indian boutique agencies can actually afford ₹6,000/month for a planning tool, and what's the addressable market at that price point?

16. **The GTM wedge is a free itinerary audit.** But the audit requires: wasted spend detection, pacing analysis, logistics checks, visa risk flags — none of which are implemented. If you launched the audit surface today, what would it actually tell a user that Google or ChatGPT couldn't?

17. **The sourcing hierarchy means the system plans from a supplier network.** But for a new agency customer, their "supplier network" is empty. What's the cold-start experience for a new agency with no supplier data, no preferred hotels, and no standard packages? Does the system have value for them before they've onboarded their suppliers?

18. **The product is built for Indian boutique agencies as the primary market.** The destination catalog, budget tables, visa logic, and examples all center on India-outbound travel (Singapore, Maldives, Europe). Is this the right beachhead, and what changes if you want to expand to Southeast Asian agencies, UK agencies, or US agencies?

---

## 8. The Current Architecture Snapshot

```
Waypoint OS — Current State (2026-04-28)

┌─────────────────────────────────────────────────────────┐
│                    BUILT & WORKING                       │
├─────────────────────────────────────────────────────────┤
│  NB01 Intake         NB02 Gap+Decision    NB03 Strategy  │
│  (extraction)        (feasibility,        (questions,    │
│                      blockers,            bundles,       │
│                      suitability,         safety)        │
│                      lifecycle scores)                   │
│                                                          │
│  Hybrid Decision Engine: Rules → Cache → LLM → Default  │
│  Suitability: Tier 1 (binary) + Tier 2 (sequence)       │
│  Safety: Leakage guard (internal/traveler split)         │
│  Fees: Risk-adjusted per-person calculation              │
│  File-based persistence (TripStore, AuditStore)          │
└─────────────────────────────────────────────────────────┘
                           │
                     single /run endpoint
                           │
┌─────────────────────────────────────────────────────────┐
│                STUBS / MOCKS / FACADES                   │
├─────────────────────────────────────────────────────────┤
│  frontier_orchestrator.py  → keyword heuristic, sync    │
│  checker_agent.py          → 3 if-statements            │
│  federated_intelligence.py → in-memory list             │
│  negotiation_engine.py     → hardcoded prices           │
│  Frontend inbox/dashboard  → hardcoded mock data        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              DESIGNED BUT NOT BUILT                      │
├─────────────────────────────────────────────────────────┤
│  src/agents/          → empty __init__.py               │
│  Persistent trip entity + lifecycle state machine       │
│  Quote/proposal generation                              │
│  Output delivery (WhatsApp, PDF, share link)            │
│  Customer entity (repeat detection)                     │
│  Sourcing hierarchy as runtime decision driver          │
│  Vendor/supplier model                                  │
│  Activity_matcher.py (wasted spend detection)           │
│  Owner review queue                                     │
│  Multi-agent routing / assignment                       │
│  Real LLM calls in the pipeline                         │
│  Eval harness / offline loop                            │
│  Auth + multi-tenancy (currently broken)                │
└─────────────────────────────────────────────────────────┘
```

---

## 9. The Build Sequence Debate

We are at a decision point. Two paths:

### Path A: Agent Infrastructure First (Current Direction)
Build `src/agents/` — base agent, orchestrator, registry, state manager, then Scout, Communicator, QA, Committee agents. Assume persistence layer follows.

**Proponent argument**: The architectural contracts need to be defined before the persistence layer so the persistence layer is designed to serve the agents' needs, not the other way around.

**Critic argument**: Building agent infrastructure before you have persistent state is building a dispatch system with nothing to dispatch to. The agents will be functional in code and useless in practice until persistence exists.

### Path B: OS Foundation First (Alternative)
Build: persistent trip entity → lifecycle state machine → event emission → background job scheduler. Then wire existing spine output into this lifecycle. Then add agents that respond to lifecycle events.

**Proponent argument**: Every agent capability requires knowing what happened before. Without the OS layer, agents are just named functions. With it, they become genuinely useful.

**Critic argument**: Persistence is a yak-shave that will take 3-4 months and delay any agentic capability. You can demonstrate agent value in a demo environment without production persistence.

### Path C: Hybrid (Proposed)
Fix P0 bugs → build minimum viable persistence (SQLite trip table with status + timestamps) → wire existing lifecycle state machine to it → then build Communicator Agent (triggered by lifecycle events) as first real agent. Only then build agent infrastructure for the second agent.

**Argument**: This delivers a working agent capability (Communicator) in 6-8 weeks with minimum infrastructure build. It also proves the pattern before investing in the full agent framework.

**Q for reviewer: Which path is right? Is there a Path D we're missing?**

---

## 10. What We Want From This Review

Please address each of the following, in order, with specific and opinionated answers:

### A. Product Thesis Validity
- Is "copilot for boutique travel agencies" a viable product thesis at this stage of AI capability?
- What comparable products exist and what can we learn from their success/failure?

### B. Agentic Architecture Assessment
- Is the 2-axis (decision_state × operating_mode) classification system a good foundation?
- Is the "suggestion posture" the right default, or should some agent actions be autonomous?
- Is the agent decomposition (Scout / Communicator / QA / Committee) correct?

### C. Build Sequence Critique
- Which of the three paths (A/B/C) is right, and why?
- What is the single most dangerous mistake in the current build plan?

### D. Structural Gaps
- What critical capability is missing that is not mentioned in this brief?
- What has been over-built relative to the current stage?

### E. Commercial Viability
- Is the pricing model realistic for the Indian boutique agency market?
- What is the GTM wedge that actually works, given what's built vs. what's documented?

### F. Risk Assessment
- What could kill this product that we're not taking seriously enough?
- What's the biggest technical bet and is it the right one?

---

## 11. Key Documents Available for Deep-Dive

If you want more detail on any specific area, these documents exist in the project:

| Document | What It Contains |
|----------|-----------------|
| `Docs/PROJECT_THESIS.md` | 1-page core thesis |
| `Docs/PRODUCT_VISION_AND_MODEL.md` | Full business model, sourcing hierarchy, JTBDs |
| `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` | 7-stage build sequence, ground truths |
| `Docs/V02_GOVERNING_PRINCIPLES.md` | 2-axis classification, governing rules |
| `Docs/LEAD_LIFECYCLE_AND_RETENTION.md` | 16-state machine, ghost/churn/window-shopper scoring |
| `Docs/PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md` | Day-in-the-life walkthrough for 5 personas, gap tables |
| `Docs/DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` | 4-thread deep dive: copilot line, lead-gen, sourcing, suitability |
| `Docs/AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md` | Full agent build plan |
| `Docs/FIRST_PRINCIPLES_AGENTIC_AUDIT_2026-04-27.md` | First-principles critique of current agentic approach |
| `Docs/AGENTIC_PIPELINE_CODE_AUDIT_2026-04-27.md` | Code-level audit findings |
| `src/intake/orchestration.py` | The spine pipeline (source of truth for what's built) |
| `src/decision/hybrid_engine.py` | The hybrid decision engine |
| `src/intake/frontier_orchestrator.py` | The current "agent" stubs |

---

*This document was prepared for external review. All claims about system state are verified against the actual codebase. The documentation-to-implementation gap is real and intentional — the documentation represents the product vision; the code represents the current build stage.*

*Date: 2026-04-28*
