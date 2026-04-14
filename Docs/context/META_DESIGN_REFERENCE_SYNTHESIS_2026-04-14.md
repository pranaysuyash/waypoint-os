# Meta Design Reference Synthesis (2026-04-14 IST)

## Source Files Reviewed

Original files in Downloads (all around 5:45 PM IST):
- `/Users/pranay/Downloads/Thinking-about-agentic-flow.html` (`17:45:15`)
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (1).html` (`17:45:26`)
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (2).html` (`17:45:33`)
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (3).html` (`17:45:51`)
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (4).html` (`17:46:00`)

Archived copy inside repo for traceability:
- `Archive/context_ingest/meta_design_refs_2026-04-14_1745/`

## What These Files Contain

These are UI/interaction prototype HTML artifacts (not production architecture docs). They are still valuable as operational UX references for:
- trip ops cockpit structure
- triage and risk handling UX
- next-action orchestration patterns
- customer-facing transparency surfaces

## High-Value Patterns Extracted

### 1) Operational Trip Lanes and Triage
- Explicit work queues by stage: `Needs Action`, `Ready`, `In Progress`, `Traveling`, `Completed`.
- Good fit for agency daily operations and SLA management.

### 2) Action-First Agent Workflow
- `Next Action` card pattern with:
  - urgency state (`urgent`/`not urgent`)
  - due/SLA status (`on track` vs `breached`)
  - one-click execution and templated comms
- This aligns with an agent-first B2B OS instead of passive dashboards.

### 3) Risk + Confidence Surfacing
- Structured risk flags with simple severity semantics (`green/amber/red`).
- Risk module next to execution controls improves decision speed.

### 4) Communication Intelligence Fields
- Per-trip comm metadata model in UI concepts:
  - channel
  - last touch
  - unread count
  - sentiment
- Useful for escalation and follow-up routing.

### 5) Explainability and Provenance UX
- Activity feed with typed actors/events (`sys`, `ai`, `you`, `customer`) and timestamps.
- Helps with auditability and post-mortem learning.

### 6) Trip Context Enrichment
- Watchers/followers and related-trip linking patterns are useful for team operations and pattern reuse.
- Customer profile summary fields (past trips, spend, preferences, risk tier) are practical for personalization.

### 7) Fast Interaction Layer
- Slash/command palette + keyboard shortcuts are strong for power users (agents and owners).

### 8) Dual-View Pattern (Agent + Traveler)
- Dual-view concept (operations console + customer-facing trip experience) is a strong B2B2C UX direction.
- Should be approached as phased rollout.

### 9) In-Trip Incident Handling UX
- Incident timeline + ETA + escalation controls are specifically useful for “traveling now” cases.

## Do Now / Do Later / Discuss

## Do Now (P0)
- Add an explicit `next_action` object and SLA fields to the canonical packet/output model.
- Add a lightweight `risk_flags` structure with normalized severity.
- Add an `activity_feed` schema with actor + event type + timestamp.
- Add `comm_state` fields (`channel`, `last_touch`, `unread`, `sentiment`) to trip state.
- Add fixture cases for:
  - ambiguous destination + clarification template
  - urgent in-trip disruption requiring escalation

## Do Later (P1/P2)
- Build command palette and keyboard-driven workflows in UI.
- Add watchers/related-trips recommendation layer.
- Build full dual-view customer experience beyond MVP.
- Add richer in-trip operations board (ETA timeline, driver/vendor coordination).

## Discuss Before Build
- Exact ownership model for SLA breach routing (who is default owner, reassign rules).
- Sentiment source policy (LLM-only vs deterministic heuristics + LLM).
- Whether dual-view ships in MVP or phase-2 after single-tenant validation.
- Minimal safe set of customer-visible data in shared traveler view.

## Completed Tasks
- Reviewed all five Meta reference files from 5:45 PM.
- Archived source files inside repository for future reference.
- Extracted reusable product/UX patterns.
- Converted patterns into actionable priority buckets (`Do now`, `Do later`, `Discuss`).

## Pending Tasks
- Reflect P0 schema updates in technical docs/specs (packet schema + fixtures).
- Convert `Do now` items into tracked implementation tasks in roadmap docs.
- Validate these patterns against current codebase and test fixtures.
- Cross-link with institutional-memory synthesis for template/supplier/pricing/customer/playbook layers:
  - `Docs/context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md`

## Date Validation
- Environment date/time used for this update: `2026-04-14 17:49 IST`.
