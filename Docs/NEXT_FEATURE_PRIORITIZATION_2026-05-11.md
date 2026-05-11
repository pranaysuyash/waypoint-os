# Next Feature Prioritization Review

Date: 2026-05-11  
Status: Planning / evidence review  
Scope: Ten next features selected from current docs, code, route inventory, tests, and external market signals.  
Instruction sources applied: `/Users/pranay/AGENTS.md`, `/Users/pranay/Projects/AGENTS.md`, `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`, `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`, `/Users/pranay/Projects/travel_agency_agent/.impeccable.md`, `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`, `Docs/context/agent-start/SESSION_CONTEXT.md`, and `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`.

## Baseline And Drift Check

This review was performed against an active worktree with many May 11 changes from parallel agents. No code changes were made. This document is additive.

Read-only status evidence:

- `git status --short --branch` showed modified and untracked work in docs, frontend pages, router extraction, RLS, D6 audit scaffolding, and tests.
- `tools/architecture_route_inventory.py --format json` reported 146 backend routes, 50 still owned by `spine_api/server.py`, 96 in router modules, 71 BFF route-map entries, 0 unmatched BFF backend paths, and 0 exact duplicate backend routes.
- `tools/feature_scan.py . --json` reported the scoped D6 / suitability / itinerary progression catalog at `current_overall=1.0`, but that catalog is narrow and does not mean the product is feature-complete.
- `Docs/PHASE2_STATUS_2026-05-11.md` records React Doctor improvement to score 91 with 111 warnings remaining after metadata and async-state work.
- `Docs/RLS_TENANT_ISOLATION_2026-05-04.md` now includes a May 11 live PostgreSQL finding: local runtime role owns protected tables and bypasses RLS unless a separate runtime role or `FORCE ROW LEVEL SECURITY` path is implemented.

Important freshness notes:

- Older docs such as `Docs/BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` correctly identify large product gaps, but several items have advanced since then. For example, canonical `ItineraryOption`, per-person utility, wasted-spend economics, D6 scaffold, booking tasks, confirmations, document/extraction lifecycle events, router extraction, and Product B analytics now exist partially or fully.
- `Docs/MASTER_GAP_REGISTER_2026-04-16.md` was last updated 2026-05-04 and remains useful as a gap map, but its document/visa and booking-readiness percentages are stale after Phase 5A-5C work.
- External 2026 market research supports the repo thesis: travelers are using AI more for planning, but still prefer trusted brands/agents at booking time. That favors evidence-backed operator workflows and forwardable action packets over autonomous booking as the next priority.

External sources consulted:

- Deloitte 2026 Travel Industry Outlook: gen AI trip-planning adoption has accelerated, and personalization raises consent/transparency/compliance needs.
- Expedia Group / YouGov 2026 AI Trust Gap: travelers are comfortable using AI for planning but still prefer trusted travel brands over AI agents/chatbots at purchase.
- Skift 2026 AI travel coverage: agentic AI in travel is constrained by trust, provenance, and authoritative operational data.
- Phocuswright 2026 travel technology updates: travel businesses are moving from AI experimentation to execution.

## Prioritization Principles

The selected features optimize for:

1. **Trust before autonomy**: the product should make operators and travelers believe the output, not hide uncertainty.
2. **Workflow compression**: every feature should reduce real agency time from messy inquiry to safe next action.
3. **Commercial truth**: margin, supplier reliability, and quote readiness must become first-class, not prose.
4. **No parallel systems**: extend canonical BFF route maps, backend routers, D6 evals, execution events, and trip state contracts.
5. **Contract-driven verification**: every feature must have API-shape tests and at least one runtime/UI validation path before completion claims.

## Ranked Ten Features

### 1. Product B Action Packet And KPI Closure

Why now:

- `Docs/NEXT_STEPS_PRODUCTB_WEDGE_EXECUTION_2026-05-07.md` locks Product B as audit + action packet + re-audit compare, with success tied to agency revision and Product A pull-through.
- Code evidence exists for Product B events and analytics (`spine_api/product_b_events.py`, `spine_api/routers/product_b_analytics.py`, `tests/test_product_b_events.py`, `tests/test_product_b_analytics_router_behavior.py`), but the May 7 doc still lists KPI closure and full API tests as queued TODOs.
- External market signals say AI is useful in planning, but trust breaks at purchase. A forwardable packet fits that trust boundary: it helps the traveler ask the current agent better questions instead of pretending the AI can transact.

Value:

- Creates the fastest GTM proof loop.
- Measures real pull-through instead of vanity usage.
- Produces shareable output that can create demand for Product A.

Implementation shape:

- Lock event dictionary and KPI formulas in one Product B analytics contract.
- Ensure frontend and backend emit `first_credible_finding_shown`, `action_packet_copied/shared`, `agency_revision_reported`, `re_audit_started`, and `product_a_interest_signal`.
- Add qualified-sample filtering and dashboard visibility for observed revision, inferred/unknown, and dark-funnel/non-return cases.

Acceptance:

- Product B KPI endpoint returns numerator, denominator, window, and qualified-sample filters for every launch KPI.
- Public checker flow can produce a forward-ready packet in one pass.
- Tests cover malformed events, auth failures, and KPI formula edge cases.

Verification:

- `uv run pytest -q tests/test_product_b_events.py tests/test_product_b_analytics_router_behavior.py tests/test_public_checker_agency_config.py tests/test_public_checker_path_safety.py`
- Frontend route/API contract tests for copy/share/re-audit UI once wired.

### 2. D6 Public-Authority Gate Expansion

Why now:

- `Docs/status/D6_ITINERARY_OPTION_PROGRESS_2026-05-11.md` says D6 now has activity fixtures, manifest progression, an activity rule runner, and manifest gate decisions.
- The same doc is explicit that activity is still only `shadow`, fixture corpus is tiny, and public checker output does not yet consume D6 gate decisions.
- Without this, Product B may show findings with more authority than the eval harness justifies.

Value:

- Converts the audit engine from clever demo to measurable trust system.
- Prevents high-severity false positives from damaging credibility.
- Gives every future finding category a promotion path from planned to shadow to gating.

Implementation shape:

- Add clean and broken fixtures for budget, pacing, logistics, documents, and multi-issue cases.
- Implement non-activity rule runners by reusing runtime analyzers/contracts instead of eval-only logic.
- Add public-checker gating: only categories with `status=gating` and thresholds met may be labeled authoritative; planned/shadow findings remain advisory/internal.

Acceptance:

- Each D6 category has at least one positive and one clean fixture before promotion.
- Public checker responses include authority status per finding.
- Gate failures block authority labels without blocking the whole audit output.

Verification:

- `uv run pytest -q tests/evals/test_d6_audit_scaffold.py tests/test_itinerary_option_model.py tests/test_public_checker_live_checks.py`
- `python3 tools/feature_scan.py . --json`

### 3. Rendered Itinerary Option Output

Why now:

- The May 2 baseline audit identified structured itinerary output as the largest product gap.
- May 11 code added `ItineraryOption`, `PersonUtility`, `SuitabilityBundle`, and wasted-spend calculations in `src/suitability/models.py` and `src/suitability/options.py`.
- The model is now present, but the operator/traveler still needs a rendered artifact with days, costs, suitability, tradeoffs, and waste.

Value:

- This is the core "aha": turning messy notes into a professional option, not a text blob.
- It makes per-person utility and wasted spend visible to agencies.
- It is a prerequisite for proposals, re-audits, revisions, booking tasks, and commercial workflows.

Implementation shape:

- Build a backend response shape that exposes itinerary option artifacts without leaking internal-only fields.
- Add operator UI in Workbench/trip workspace to render option cards, per-person fit, waste, and tradeoffs.
- Add a public/traveler-safe rendering path later through Product B or proposal links.

Acceptance:

- A representative trip with activities renders at least one `ItineraryOption` with total cost, utility by person, low-utility flags, and wasted-spend summary.
- Missing cost data does not erase suitability evidence.
- UI displays current contract defensively with optional chaining and null fallbacks.

Verification:

- `uv run pytest -q tests/test_itinerary_option_model.py tests/test_suitability.py tests/test_suitability_wave_12.py`
- Frontend TypeScript and focused component tests for the rendered option.
- Browser screenshot QA after implementation.

### 4. Source Adapter Protocol Plus PDF/URL Audit Intake

Why now:

- The product spec and Product B wedge depend on accepting pasted text, uploads, and existing itineraries.
- `Docs/BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` identifies source adapters as the missing primitive for PDF, URL, voice, WhatsApp, and form input.
- Current code has document upload/extraction infrastructure, but no canonical intake adapter layer that unifies source formats into the same audit/run contract.

Value:

- Unlocks the highest-value audit mode: "upload/paste your existing itinerary and get risks."
- Prevents the extraction monolith from absorbing every new channel.
- Creates an extensible architecture for WhatsApp text, email, PDF, URL, and future voice transcript ingestion.

Implementation shape:

- Define `SourceAdapter` protocol: parse source input to normalized source envelopes plus evidence refs.
- Implement PDF adapter using existing document/extraction services where possible.
- Implement URL/text adapter with explicit provenance and failure modes.
- Keep adapters as input translators, not decision engines.

Acceptance:

- Freeform text and uploaded itinerary produce the same downstream audit-ready source envelope contract.
- Adapter output includes evidence pointers for public-checker findings.
- Failed adapter parsing returns actionable errors without poisoning the trip/run.

Verification:

- Backend adapter unit tests with sample PDF/text fixtures.
- API contract tests for public checker or trip intake endpoint consuming adapter output.

### 5. Packet Fact Editing With Durable Event History

Why now:

- `Docs/PACKET_FACTS_EDITING_ARCHITECTURE_2026-05-01.md` and `Docs/EVENT_STORE_ARCHITECTURE_2026-05-01.md` define the right contract: current fact truth lives in `extracted.facts[field]`; history lives in durable events.
- Current product has several event systems and a newer execution-event ledger, but packet fact editing still needs an operator-safe correction path.
- Without this, agents cannot safely fix bad extraction and rerun downstream decisions with a known audit trail.

Value:

- Makes extraction trustworthy because operators can correct it.
- Enables revision diffs and learning loops.
- Reduces bad downstream decisions caused by stale or wrong packet facts.

Implementation shape:

- Implement the whitelisted `PATCH /api/trips/{trip_id}/packet-facts` contract using canonical validation.
- Emit durable event history with previous and new slot values, actor, correlation id, and idempotency.
- Mark validation stale and require reassessment before consuming derived signals.
- Avoid a parallel `manual_overrides` truth layer.

Acceptance:

- Edited fields update `extracted.facts` directly with `authority_level=manual_override`.
- Prior values are visible through event history.
- Unknown fields and type mismatches are rejected.
- Revalidation stale state is explicit and visible.

Verification:

- Backend tests listed in `Docs/PACKET_FACTS_EDITING_ARCHITECTURE_2026-05-01.md`.
- Timeline/event projection test once UI reads the history.

### 6. Manual WhatsApp / Email Message Composer And Communication Log

Why now:

- `Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md` recommends manual copy-paste for MVP, not WhatsApp Business API automation.
- `Docs/UNIFIED_COMMUNICATION_AND_CHANNEL_STRATEGY.md` still lists "Copy-for-WhatsApp formatter" and secure link generation as next implementation threads.
- This is lower-risk than a full messaging integration and directly maps to how small agencies work today.

Value:

- Compresses follow-up communication immediately without requiring external verification or paid API setup.
- Creates communication history and follow-up reminders.
- Preserves human control, which is important for trust and agency adoption.

Implementation shape:

- Add an operator message composer for clarification questions, action packets, document requests, and booking reminders.
- Support copy, optional WhatsApp deep link, mark-sent, and scheduled follow-up.
- Log metadata-only communication events; avoid storing uncontrolled PII in event metadata.

Acceptance:

- Operator can copy/open a forward-ready message and mark it sent.
- Message event appears in trip timeline with channel, source, actor, and timestamp.
- Follow-up reminder is created when configured.

Verification:

- Backend communication event tests.
- Frontend component tests for copy/open/mark-sent.
- Manual browser validation.

### 7. Booking Execution Master Record

Why now:

- Phase 5A-5C implemented booking tasks, confirmations, document/extraction lifecycle events, and execution timeline pieces.
- The product vision needs a "Trip Master Record"; current work is close but still fragmented across tasks, documents, confirmations, and timelines.
- This should follow the existing booking task and confirmation routers, not create another workflow surface.

Value:

- Turns booking readiness into an operational control panel.
- Reduces name/date/document/confirmation mismatch risk.
- Creates agency confidence after proposal acceptance.

Implementation shape:

- Create a trip-level execution view that aggregates booking tasks, confirmations, accepted/rejected documents, extraction status, pending booking data, and execution events.
- Add confirmation parser/import as a later slice inside the same master record, not a separate system.
- Use metadata-only execution events and PII boundaries from `Docs/PHASE5C_CLOSURE_2026-05-10.md`.

Acceptance:

- One trip page answers: what is booked, what is missing, what is blocked, what changed, and who owns the next action.
- No payment gateway or supplier booking API is introduced in this phase.
- Existing booking task state machine remains backend-enforced.

Verification:

- `uv run pytest -q tests/test_booking_task_service.py tests/test_confirmation_service.py tests/test_document_events.py tests/test_extraction_events.py tests/test_execution_event_service.py`
- Frontend execution panel tests.

### 8. Customer Entity And Cross-Trip Memory

Why now:

- `Docs/MASTER_GAP_REGISTER_2026-04-16.md` marks customer lifecycle/cross-trip memory as infra-ready but still gapped.
- Product thesis depends on repeat-client memory and post-trip learning, but there is no customer entity.
- Drafts and future merge/link workflows already anticipate duplicate detection by hashed phone/email.

Value:

- Converts one-off trip processing into a compounding agency memory system.
- Enables repeat-client recognition, retention, and better follow-up.
- Builds a defensible data moat from agency-specific operating knowledge.

Implementation shape:

- Add a privacy-safe customer entity with tenant scoping, hashed contact identifiers, display snapshots, and trip links.
- Link drafts, trips, communication events, and post-trip feedback to customers.
- Start with deterministic duplicate suggestions; avoid automatic merges.

Acceptance:

- A trip can be linked to an existing or new customer.
- Duplicate candidates are suggested with evidence, not silently merged.
- Cross-tenant isolation is enforced in app queries and RLS posture.

Verification:

- Backend customer model/service/router tests.
- Cross-tenant tests.
- UI tests for link/create/select duplicate candidates.

### 9. Supplier, Cost, Margin, And Sourcing Policy Ledger

Why now:

- The product thesis says real agencies optimize within preferred supply, not global search.
- `Docs/MASTER_GAP_REGISTER_2026-04-16.md` still lists vendor/cost/sourcing/margin as foundational and blocking commercial features.
- Wasted-spend economics now exist at the activity level; commercial truth needs supplier/cost ledgers to make it useful for agency owners.

Value:

- Moves Waypoint OS from planning helper to agency operating system.
- Enables margin-aware recommendations, supplier reliability memory, and quote confidence.
- Unlocks financial state, cancellation/refund, seasonality, and post-trip supplier scoring later.

Implementation shape:

- Define canonical supplier profile, cost component, margin policy, and sourcing policy contracts.
- Start with manual/internal inventory, not GDS or live booking APIs.
- Attach cost components to itinerary options and booking tasks.

Acceptance:

- An itinerary option can show component-level estimated cost and margin metadata.
- Sourcing order is explicit: internal package, preferred supplier, network/consortium, open market.
- Unknown cost/margin is shown as unknown, not zero.

Verification:

- Backend model and service tests.
- Scenario tests showing sourcing policy affects option ranking/explanation.

### 10. Production Trust Hardening: SQL-Only Trip State, RLS Runtime Role, Redis LLM Guard

Why now:

- The repo has already suffered split-brain risk from `TRIPSTORE_BACKEND` fallback.
- `Docs/RLS_TENANT_ISOLATION_2026-05-04.md` now documents live local RLS owner-bypass risk.
- `Docs/MASTER_PHASE_ROADMAP.md` marks Redis-backed LLM usage guard as P0 before production enforcement.
- These are not glamorous features, but they determine whether pilot data, tenant isolation, and AI cost controls are credible.

Value:

- Prevents tenant data leaks and trip invisibility.
- Makes production behavior deterministic.
- Controls AI spend and gives agencies confidence in privacy/cost governance.

Implementation shape:

- Create separate DB owner/admin and runtime roles, or a complete `FORCE ROW LEVEL SECURITY` rollout with every SQL path verified.
- Converge TripStore to PostgreSQL as the sole runtime persistence path; keep file store only for explicit dev fixtures or migration tests.
- Move LLM guard storage from in-memory to Redis before production rate-limit enforcement.

Acceptance:

- Runtime DB role cannot bypass RLS on protected tenant tables.
- Startup posture check warns locally and fails in staging/production when RLS is not enforceable.
- `TRIPSTORE_BACKEND` cannot silently fall back in staging/production.
- LLM guard counters survive process restart and work across workers.

Verification:

- `uv run pytest -q tests/test_rls.py tests/test_rls_live_postgres.py tests/test_server_startup_invariants.py`
- TripStore SQL/file fallback tests.
- LLM guard Redis tests once implemented.

## Recommended Sequence

Do not build these in ten parallel branches. The safest order is:

1. Product B Action Packet And KPI Closure.
2. D6 Public-Authority Gate Expansion.
3. Rendered Itinerary Option Output.
4. Source Adapter Protocol Plus PDF/URL Audit Intake.
5. Packet Fact Editing With Durable Event History.
6. Manual WhatsApp / Email Message Composer And Communication Log.
7. Booking Execution Master Record.
8. Production Trust Hardening can run in controlled slices alongside the above, but not as broad schema churn during UI-heavy work.
9. Customer Entity And Cross-Trip Memory.
10. Supplier, Cost, Margin, And Sourcing Policy Ledger.

The reason for this sequence is dependency and business impact: prove the wedge, make public findings trustworthy, render the core artifact, then widen ingestion and correction paths. Customer memory and supplier economics become much more valuable once the product has real trip artifacts and operational events to attach them to.

## Items Not Recommended As Next Ten

- Full WhatsApp Business API automation: useful later, but manual copy/open/mark-sent delivers the workflow value now without verification and vendor overhead.
- GDS/Amadeus/Sabre booking APIs: explicitly not MVP per `Docs/INTEGRATIONS_AND_DATA_SOURCES.md`; agencies already know how to book.
- Microservices: `Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md` correctly recommends modular monolith plus service-ready boundaries, not premature microservices.
- Autonomous payment/booking: market trust signals and repo docs both point away from transaction automation as the next move.
- Broad dead-code deletion: `Docs/PHASE2_STATUS_2026-05-11.md` says remaining dead-code surfaces are mostly public/API/future-facing and require supersession workflow, not blanket removal.

## Task Packages For Implementation Agents

### Task Package A: Product B Launch Evidence

Objective: close Product B event/KPI instrumentation and make the action packet measurable.  
Scope in: event schema, KPI formulas, qualified sample filters, API tests, UI event emission.  
Scope out: agency-side Product A handoff automation, payments, supplier APIs.  
Expected files: `spine_api/product_b_events.py`, `spine_api/routers/product_b_analytics.py`, public checker frontend page/components, related tests, Product B docs.  
Acceptance: every launch KPI has numerator/denominator/window/data source and at least one test with qualified and unqualified traffic.  
Verification: Product B and public checker pytest targets plus frontend build/tests.

### Task Package B: D6 Authority Gate

Objective: prevent public audit findings from overstating authority.  
Scope in: fixtures, non-activity rule runners, manifest gate public response mapping.  
Scope out: LLM judge, broad all-category perfection.  
Expected files: `src/evals/audit/`, `data/fixtures/audit/`, public checker service/contracts, tests.  
Acceptance: public output labels planned/shadow/gating correctly and only gating-passing findings are authoritative.  
Verification: D6 tests, public checker tests, feature scanner.

### Task Package C: Itinerary Option Renderer

Objective: make canonical itinerary option artifacts visible and useful.  
Scope in: backend serialization, operator UI component, defensive FE types, tests.  
Scope out: live hotel/flight booking, payment.  
Expected files: `src/suitability/`, `spine_api/contract.py` or route serializer, workspace/trip frontend panels.  
Acceptance: a real trip can render option cost, utility by person, warnings, and wasted spend.  
Verification: suitability tests, TypeScript, focused component tests, browser screenshot.

### Task Package D: Source Adapter Foundation

Objective: support pasted text and uploaded/linked itineraries through one normalized input contract.  
Scope in: `SourceAdapter` protocol, PDF/text/url first adapters, evidence refs.  
Scope out: voice, WhatsApp API, supplier booking APIs.  
Expected files: `src/intake/`, public checker/trip intake services, document extraction integration tests.  
Acceptance: same audit flow can consume freeform text and uploaded itinerary with evidence pointers.  
Verification: adapter tests and public checker API contract tests.

### Task Package E: Trust And State Hardening

Objective: remove the highest-risk production trust gaps.  
Scope in: RLS runtime posture enforcement, SQL TripStore convergence plan/implementation slice, Redis LLM guard storage.  
Scope out: unrelated route extraction or UI refactors.  
Expected files: `spine_api/core/rls.py`, startup checks, persistence tests, LLM guard modules.  
Acceptance: staging/production fail fast on insecure tenant posture; TripStore cannot silently split-brain; Redis guard survives restart.  
Verification: RLS/startup/TripStore/guard tests.

## Review Verdict

Verdict: **B+ foundation, with the next value concentrated in trust-backed output and audit loops.**

The codebase has moved meaningfully since the May 2 baseline. The right next move is not to add random new surfaces. It is to make the existing wedge and operator workflow produce evidence-backed, forwardable, correction-friendly artifacts.

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
