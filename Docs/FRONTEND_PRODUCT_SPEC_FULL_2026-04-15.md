# Frontend Product Spec (Full Scope)

Date: 2026-04-15 09:50:32 IST  
Status: Full product frontend spec (no Streamlit; implementation can phase, scope is not reduced)

## 1) Intent

Define the complete frontend product surface for the travel agency platform, grounded in:

- Archived HTML UI explorations (`Archive/context_ingest/meta_design_refs_2026-04-14_*/*.html`)
- Existing runtime spine and docs (`src/intake/*`, UX docs, frozen spine status)

This is a full-scope product spec, not an MVP-only brief.

## 2) Source-of-Truth Inputs Used

### HTML explorations (design references)

1. `Thinking-about-agentic-flow (1).html`  
   Pattern: trip review list + “what we know / need to clarify / next steps / confidence”.

2. `Thinking-about-agentic-flow (2).html`  
   Pattern: dark “operational command” with left/center/right panel composition.

3. `Thinking-about-agentic-flow (3).html`  
   Pattern: explicit `Ops` vs `Selling` mode switching + live activity + blockers/next actions.

4. `Thinking-about-agentic-flow (4).html`  
   Pattern: dual-view architecture (internal planning surface + traveler-facing output surface).

5. `Thinking-about-agentic-flow.html`  
   Pattern: full packet inspector with tabs for packet/decision/strategy and provenance/risk sections.

6. `Thinking-about-agentic-flow (6).html`  
   Pattern: public itinerary-checker UX (upload -> processing -> score/issues -> upsell).

7. `Thinking-about-agentic-flow (7).html`  
   Pattern: implementation-oriented funnel and rule-layer framing.

8. `Thinking-about-agentic-flow (8).html`  
   Pattern: SEO + Next.js component architecture and landing-page structure.

### Runtime and system references

- `src/intake/*` (NB01/NB02/NB03 + safety/leakage)
- `Docs/FROZEN_SPINE_STATUS.md`
- `Docs/status/OPERATOR_WORKBENCH_COMPONENT_SPEC_2026-04-15.md`
- `Docs/UX_*` strategy and flow documents

## 3) Product Surfaces (Full)

### Surface A: Internal Intelligence Workbench (Engineering + Product + QA)

Purpose:
- Deep inspectability of packet, decision, strategy, safety.
- Scenario replay, fixture compare, leakage validation.

Mode model:
- Workbench mode
- Flow Simulation mode

Runtime host:
- Product web app shell (Next.js) under an internal route namespace.
- Workbench is a first-class internal module, not a separate tool stack.

### Surface B: Agency Operator App (Primary internal product)

Personas:
- Solo agent
- Junior agent
- Senior/lead consultant

Core modules:
- Lead Inbox
- Intake Workspace
- Decision & Clarification
- Quote/Option Builder
- Booking Readiness
- Change Requests & Recovery
- Conversation Timeline

### Surface C: Agency Owner Console

Persona:
- Owner / manager

Core modules:
- Review queue
- Margin policy governance
- Quality and conversion diagnostics
- Team productivity + SLA visibility
- Exception/escalation center

### Surface D: Traveler-Facing Experience

Persona:
- End traveler / coordinator

Core modules:
- Traveler-safe proposal view
- Clarification response view
- Trip plan timeline
- Change request flow
- Status + confidence-friendly comms

### Surface E: Public Acquisition Layer

Persona:
- New inbound prospects

Core modules:
- Itinerary checker funnel
- SEO landing pages by destination/problem
- “Fix this plan” conversion flow

## 4) Information Architecture (Top-Level Navigation)

## Internal App (Operator + Owner)

Primary nav:
1. Inbox
2. Workspaces
3. Proposals
4. Trips in Progress
5. Insights
6. Settings

Secondary nav (workspace context):
- Intake
- Packet
- Decision
- Strategy
- Output
- Activity
- Safety

## Public Layer

Primary nav:
1. Itinerary Checker
2. Why This Works
3. For Agencies
4. Pricing
5. Case Studies

## 5) Canonical Screen Specs

### 5.1 Inbox

Goal:
- Prioritize incoming leads and active requests by urgency + readiness.

Key UI blocks:
- Queue segments: New, Waiting clarification, Ready to draft, Escalated.
- Trip cards: destination, date window, party size, budget signal, risk badge.
- Suggested next action chip from decision engine.

States:
- Empty, overloaded, stale, blocked.

### 5.2 Intake Workspace

Goal:
- Convert messy context into structured decisionable state.

Layout:
- Left: raw incoming notes/chats/docs
- Center: system understanding summary
- Right: recommended next action + traveler-safe draft preview

Includes:
- “What we know / Need to clarify / Next steps” pattern from HTML exploration.
- Clarification budget indicator.

### 5.3 Packet Inspector

Goal:
- Human-readable packet with raw toggle.

Sections:
- Facts
- Derived signals (+ maturity)
- Hypotheses
- Unknowns
- Contradictions
- Provenance/evidence coverage
- Validation outcomes

### 5.4 Decision View

Goal:
- Explain state transition and why.

Sections:
- Decision state (prominent)
- Hard blockers vs soft blockers
- Feasibility and urgency
- Risk flags
- Rationale
- Follow-up question set

### 5.5 Strategy View

Goal:
- Show plan-generation and communication sequencing.

Sections:
- Session objective
- Recommended opening
- Priority order
- Branches
- Assumptions and constraints
- Internal-only notes

### 5.6 Traveler Output View

Goal:
- Strict traveler-safe communication preview.

Sections:
- Message/itinerary preview
- Confidence framing
- Action requests
- Next milestone

### 5.7 Safety Center

Goal:
- Verify zero internal leakage to traveler channel.

Sections:
- Leakage status
- Blocked terms/fields diagnostics
- Sanitization diff
- Last run safety ledger

### 5.8 Owner Review Queue

Goal:
- Approve high-risk/high-value decisions and commercial exceptions.

Sections:
- Pending approvals
- Margin policy violations
- Discount/exception reasons
- Time-to-approve metrics

### 5.9 Owner Insight Dashboard

Goal:
- Operational and commercial truth.

Sections:
- Lead-to-quote conversion
- Quote turnaround
- Revision loops
- Margin adherence
- Agent utilization
- Escalation heatmap

### 5.10 Itinerary Checker (Public Funnel)

Goal:
- Acquire high-intent leads with immediate value.

Flow:
1. Upload or paste itinerary
2. Processing animation with transparent checks
3. Score + issues summary
4. Missing/included matrix
5. Email capture / “Fix my plan” CTA

## 6) Dual-Mode UX Contract (Ops vs Selling)

Based on exploration patterns, operator workspace must support explicit view mode:

- Ops mode:
  - execution risk
  - supplier readiness
  - timeline disruptions
  - escalation visibility

- Selling mode:
  - proposal polish
  - branch framing
  - traveler confidence messaging
  - conversion guidance

Mode switch changes emphasized blocks, not core data truth.

## 7) Design System Direction

Visual direction:
- High-density professional console for internal surfaces.
- Clean trust-forward layout for traveler/public surfaces.

State colors (reserved semantics only):
- Green: proceed traveler-safe
- Amber: internal draft/branch/needs input
- Red: blocked/escalated/risk critical
- Blue/neutral: follow-up collection

Typography:
- Distinct typographic hierarchy for:
  - operational alerts
  - decision rationale
  - traveler copy

Motion:
- Functional transitions only (mode switch, state transitions, progress runs).

## 8) Component System (Productized Frontend)

Core component families:
- `TripCard`
- `StateBadge`
- `ConfidenceBadge`
- `BlockerList`
- `ClarificationPanel`
- `DecisionRationaleCard`
- `StrategySequence`
- `TravelerPreview`
- `LeakagePanel`
- `DiffPanel`
- `ApprovalCard`
- `AuditIssueList`

Public funnel components:
- `Dropzone`
- `ProcessingChecks`
- `ScoreCard`
- `IssuesList`
- `CoverageMatrix`
- `EmailCapture`

## 9) Technical Frontend Architecture (Locked)

Recommended stack:
- Next.js App Router
- TypeScript
- Component library with strict state semantics
- Server-side API routes as BFF layer over shared orchestration services

State boundaries:
- UI state (local/session)
- Workspace state (fetched/run results)
- Scenario/fixture state (internal tooling)

No duplicated decision/business logic in frontend.
No Streamlit layer in the implementation path.

## 10) Route Map (Target)

Internal:
- `/app/inbox`
- `/app/workspace/[tripId]/intake`
- `/app/workspace/[tripId]/packet`
- `/app/workspace/[tripId]/decision`
- `/app/workspace/[tripId]/strategy`
- `/app/workspace/[tripId]/output`
- `/app/workspace/[tripId]/safety`
- `/app/workbench`
- `/app/owner/reviews`
- `/app/owner/insights`

Public:
- `/itinerary-checker`
- `/itinerary-checker/result/[sessionId]`
- `/destinations/[slug]/itinerary-check`
- `/problems/[slug]`

Traveler:
- `/trip/[shareToken]`
- `/trip/[shareToken]/changes`
- `/trip/[shareToken]/timeline`

## 11) “Coming Soon” Contract (Explicit Full Scope Signaling)

Allowed in initial productized frontend (while keeping full scope visible):

- “Coming soon” placeholders for:
  - supplier graph deep view
  - autonomous disruption planner
  - advanced owner cohort analytics
  - cross-trip recommendation feed

Rule:
- Placeholder must include:
  - purpose
  - expected value
  - dependency status
  - planned activation phase

## 12) End-to-End Journey Coverage (Must Exist in UI)

1. New inquiry -> intake -> follow-up -> proposal
2. Audit upload -> issue detection -> fix proposal
3. Group coordinator flow with subgroup constraints
4. Cancellation/replan flow
5. Emergency escalation flow
6. Owner policy override/approval flow
7. Repeat-customer memory-assisted planning flow

## 13) Scenario Set to Hardwire Early

Use these first in both workbench and productized mocks:
- clean family discovery
- semi-open destination discovery
- past customer with old-trip mention
- audit mode (self-booked)
- coordinator group
- cancellation
- emergency
- owner-review/internal-only

## 14) QA and Acceptance for Frontend Program

Frontend acceptance dimensions:
- Clarity of decision-state explanation
- Internal vs traveler-safe boundary correctness
- Operator actionability (next step always clear)
- Owner governance visibility
- Public funnel conversion instrumentation
- Zero silent data mutation in computed surfaces

## 15) Implementation Program (Full, Additive)

Wave 1:
- Internal workbench in productized web shell (`/app/workbench`)
- Operator core workspace in productized web shell
- Public itinerary checker v1

Wave 2:
- Owner governance + insights full coverage
- Traveler portal with change/timeline workflows
- SEO landing-page matrix

Wave 3:
- Supplier/knowledge overlays
- Advanced operations intelligence
- Full cross-surface consistency and design-system hardening

## 16) Key Decisions Locked

1. Full product frontend path is locked to Next.js (no Streamlit fallback).
2. Workbench is not throwaway; it is contract-validation infrastructure inside the product shell.
3. Product frontend will preserve dual-view model:
   - internal intelligence
   - traveler-safe communication
4. Public itinerary checker remains acquisition wedge integrated with operator pipeline.

---

This spec is intentionally full-scope and additive. Implementation can sequence delivery, but the target product surface remains complete.
