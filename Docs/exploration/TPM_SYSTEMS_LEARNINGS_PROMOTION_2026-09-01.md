# TPM / Systems-Design Learning Promotion Record

**Date:** 2026-09-01
**Source:** `/Users/pranay/.codex/attachments/e76e3c61-aa77-44dc-bcbe-4f4180e61e30/pasted-text.txt`
**Target:** Waypoint OS (`/Users/pranay/Projects/travel_agency_agent`)
**Mode:** Evidence-backed extraction and bounded promotion; no product-code changes in this slice
**Doctrine basis:** Operating Doctrine 8.0; Architecture Doctrine 1.1; Inquiry and Analysis Doctrine 1.0; Testing and Documentation doctrines as applicable
**Status:** Active promotion record; implementation items remain governed by the existing findings register

## 1. Decision summary

Yes, this discussion can improve Waypoint and can become part of the operating
system around it. It should be promoted in layers:

| Layer | Decision | Why |
|---|---|---|
| Canonical doctrine | Promote only the generic architecture invariants: state/decision/action decomposition, progressive autonomy, and dependency/gate/parallelism distinction | These principles generalize beyond travel and protect future design work |
| Shared skill | Add `/Users/pranay/Projects/skills/conversation-to-operating-model/SKILL.md` | The lesson contains a repeatable method for turning discussion into evidence-bearing work across projects |
| Persona | Add a proposed TPM/system-designer overlay, pending Persona Council ratification | The lens is useful for review, but must not become a new authority or favorite persona |
| Product | Link to existing tasks; add only genuinely missing behavior after contract review | Much of the lesson is already present in the current code and recent audit queue |
| Learning loop | Use the method for future discussions and scenario reviews | This turns ChatGPT tutoring into repeatable organizational learning rather than transcript accumulation |

The Architecture Doctrine was amended from 1.0 to 1.1 with generic sections
13A and 13B. Its canonical manifest must be refreshed and project context
regenerated before treating the new version as propagated.

## 2. Evidence boundary and current-state inspection

The pasted discussion is a learning artifact, not authoritative product truth.
The following current surfaces were inspected:

- `README.md`: Waypoint is an operations/revenue co-pilot with intake,
  decision support, operator and traveler outputs, and persistence/audit.
- `src/intake/orchestration.py`: canonical spine from envelopes through
  extraction, validation, decision, strategy, safety, and optional frontier
  orchestration.
- `src/intake/packet_models.py` and `src/intake/validation.py`: structured
  packet facts, ambiguity/unknown handling, evidence coverage, and validation
  warnings.
- `src/memory/models.py` and `src/memory/retriever.py`: separate five-tier
  memory model with provenance, decay, sanitization, supersession, and token
  budgeting.
- `src/agents/runtime.py` and `src/agents/idempotency.py`: work status,
  execution leases, checkpoints, retries, dead letters, and idempotency records.
- `Docs/research/PER_0442_JOURNEY_GRAPH_OPERATING_SYSTEM_2026-09-01.md`:
  journey dependency graph and deterministic feasibility constraints.
- `Docs/research/PER_0700_AGENT_RUNTIME_AND_RESILIENCE_2026-09-01.md`:
  lease/checkpoint/poison-work resilience design.
- `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`: agency-level
  autonomy gates and the invariant that `STOP_NEEDS_REVIEW` remains blocked.
- `Docs/review/ALIGNMENT_EVALUATION_2026-08-31.md` and
  `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`: current evidence that
  several ideas are implemented, while epistemic labeling, memory wiring,
  retirement, stale obligations, provider/execution safety, and broader gates
  remain open or partial.
- `Understanding_Personas_29aug26/docs/ROUTING_MODEL.md` and
  `docs/DECISIONS.md`: Persona Council identity remains a separate canonical
  source; project overlays and retrieval indexes must not become a replacement.

No production, live-provider, or real-user evidence was established by this
inspection. Existing recent docs contain claims of targeted and live-demo
evidence; those claims remain project evidence to re-check before closure.

## 3. Learning ledger

The source discussion contains a progression from travel-business description
to system behavior. The following ledger captures explicit and implicit lessons.

| ID | Learning | Type | Waypoint disposition |
|---|---|---|---|
| L-01 | Describe system behavior, not only business activity | Explicit | Promote to skill; use in architecture reviews |
| L-02 | Raw inbound is multi-modal, partial, contradictory, and incremental | Explicit | Existing intake path; expand fixtures and provenance checks |
| L-03 | Current trip state is different from customer memory | Explicit | Existing separate modules; memory isolation/wiring remains open |
| L-04 | A decision chooses the next action, not merely the final itinerary | Explicit | Existing decision/gap layer; make next-action contract more visible |
| L-05 | Actions must distinguish research, recommendation, hold, booking, messaging, and escalation | Explicit | Extend action/permission matrix; link to autonomy work |
| L-06 | Mistake cost should determine autonomy | Explicit | Existing D1 autonomy gradient; retain progressive action ladder |
| L-07 | Validation needs feasibility, freshness, contradiction, permission, and source checks | Explicit | Existing validation and risk work; add freshness/authority closure |
| L-08 | Use AI for ambiguity/ranking; deterministic tools/rules for calculable truth | Explicit | Existing deterministic-first design; protect provider facts from model output |
| L-09 | “Best” is preference-sensitive, not always mathematically unique | Explicit | Existing strategy/ranking; require evidence and preserve alternatives |
| L-10 | Business failures and technical failures are both product failures | Explicit | Existing resilience and review queues; scenario coverage needed |
| L-11 | Retry after an unknown external outcome can duplicate a booking/payment | Explicit | Idempotency exists, but external commit ambiguity needs end-to-end proof |
| L-12 | Scale includes state consistency, providers, cost, observability, privacy, audit, reliability, and model drift | Explicit | Existing audit queue; keep as non-functional acceptance dimensions |
| L-13 | The architecture is a pipeline from messy input to feedback, not a single prompt | Explicit | Existing spine; use as boundary map, not replacement architecture |
| L-14 | Do not rush from messy input to itinerary generation; first establish reliable state | Explicit | Intake and epistemic backlog |
| L-15 | Independent work can run provisionally in parallel | Explicit | Add graph/policy analysis; do not fan out blindly |
| L-16 | Need-to-know eventually is not the same as must-complete-before | Explicit | Promote dependency/gate distinction to doctrine and skill |
| L-17 | Cheap authoritative feasibility checks may intentionally gate expensive work | Explicit | Product policy candidate; measure cost/latency/failure probability |
| L-18 | Short-circuiting avoids expensive work after a decisive failure | Explicit | Add to orchestration design and tests |
| L-19 | A failed current configuration is not necessarily a failed customer goal | Explicit | Existing counterfactual/recovery direction; make alternatives explicit |
| L-20 | Availability check, reservation/hold, and purchase have different contracts | Explicit | Action taxonomy and connectivity-tier work |
| L-21 | Route design has hard and soft dependencies and should refine incrementally | Explicit | JDG and plan-candidate work; verify re-planning semantics |
| L-22 | A state machine constrains allowed next actions and reduces LLM freedom | Explicit | Lifecycle/state work; map current stages/events before adding another machine |
| L-23 | Conversation-based tutoring can be turned into reusable organizational learning | Inferred | New skill + promotion record; apply to future discussions |
| L-24 | The tutor's exercise structure can expose reasoning quality, not just answers | Inferred | Scenario/eval opportunity; do not mistake self-reported scores for product proof |
| L-25 | The lesson is a cross-domain architecture pattern, not only a travel pattern | Inferred | Generic doctrine amendment; travel details stay in skill/persona |

## 4. Existing coverage versus real gaps

### Already represented or substantially represented

- deterministic-first extraction and packet validation;
- explicit decision states and agency-level autonomy policy;
- separate memory tiers with provenance and decay;
- journey dependency graph and feasibility constraints;
- retries, leases, checkpoints, dead-letter quarantine, and idempotency records;
- audit/telemetry and dual operator/traveler outputs;
- scenario/persona-based product evaluation;
- current doctrine on ownership, truth, contracts, concurrency, failure,
  recovery, AI boundaries, testing, and durable documentation.

### Partial, misleading, or unclosed

| Gap | Existing evidence | Promotion action |
|---|---|---|
| State versus memory in the real UI flow | Alignment audit says backend memory is real but frontend card is still mock/partially wired | Keep `NEW-06/F-23` as the canonical implementation path; do not add another memory store |
| Epistemic labels on extracted facts | Alignment audit says the primitive exists but extractor usage can claim `FACT` for derived/default values | Keep `NEW-01/F-22`; require negative tests and visible epistemic status |
| “What next?” as a first-class decision contract | Decision layer exists, but current surfaces mix outcome, strategy, and action concepts | Explore a decision/action envelope before implementation; link to D1 and existing `DecisionResult` |
| Gate policy versus dependency graph | JDG exists, and orchestration exists, but no inspected evidence proves cost-aware gate selection/cancellation | New exploration `TPM-EXP-01` below |
| Availability/reserve/purchase separation | Autonomy/connectivity docs discuss levels, but real provider execution is not established | Keep behind connectivity and provider gates; no booking claims |
| Unknown-result idempotency | Registry exists, but “timeout after possibly committed supplier action” needs integration proof | Extend resilience scenarios; link `R-11`, `F-01`, and `PER-0700` |
| Lifecycle state machine completeness | Lead lifecycle and pipeline stages exist, but a single end-to-end trip lifecycle/event contract is not yet established | Explore before adding a second state machine; link `TPM-EXP-02` |
| Scale economics and model drift | Runbook and audits name cost/observability/drift, but no production baseline here | Research/measure; do not hardcode one-million-trip assumptions |
| Persona promotion | Project has many personas and an operational council, but canonical identity is external to this repo | Keep `PER-TPM-WP-01` proposed until council review |

## 5. Sequenced task and exploration register

### P0/P1 product integrity and trust work already in the canonical register

These are not new tasks from this discussion; the discussion gives them a
clearer rationale and acceptance framing:

- `NEW-01/F-22`: correct authority/epistemic labeling;
- `NEW-06/F-23`: real, agency-scoped customer-memory wiring;
- `F-01`: idempotent/optimistic-concurrency protection for price-lock changes;
- `F-03`: bind approvals to authenticated actors and artifact versions;
- `F-07`: inspectable, permission-gated poison-work recovery;
- `F-13`: provenance-tiered memory writes and retrieval quarantine;
- `F-14` / `EX-14`: first-class temporal obligations and expiry sweeps;
- `R-11`: durable lease and fencing semantics;
- `R-06/A-03`: connectivity tier and honest provider/tool boundaries.

### New bounded explorations

| ID | Question | Deliverable | Falsifier / stop condition |
|---|---|---|---|
| TPM-EXP-01 | Should Waypoint choose a feasibility gate before parallel search for each workflow? | Gate policy contract with cost, latency, invalidation, reuse, cancellation, and UX fields | If no workflow has a cheap high-failure gate or reusable downstream results, keep simple parallel orchestration |
| TPM-EXP-02 | Can existing stages/events express one canonical trip lifecycle without another state machine? | Current-to-intended lifecycle map and migration decision | If existing lifecycle/stage contracts cover all transitions and recovery, do not add a new machine |
| TPM-EXP-03 | What is the canonical action taxonomy and permission matrix? | `observe/search/recommend/propose/hold/reserve/commit/message/escalate` contract mapped to D1 | If current contracts already distinguish these at every boundary, document and test rather than create a new type |
| TPM-EXP-04 | What evidence is required after a timeout where an external commit may have succeeded? | Provider-neutral unknown-outcome recovery scenario and idempotency verdict contract | If all current providers expose queryable idempotency/status, adapt existing interfaces instead of adding compensation blindly |
| TPM-EXP-05 | Which feedback may update trip state, customer memory, or autonomy policy? | Feedback routing and retention matrix | If pilot data shows no repeatable signal, keep policy static and do not introduce adaptive autonomy |
| TPM-EXP-06 | Does the TPM persona add distinct decisions beyond existing architecture/evidence personas? | Two scenario reviews and Persona Council routing evaluation | If it only renames existing lenses, reject the new persona |

### Product implementation candidates after exploration

- show current next action, blocking reason, owner, and allowed actions in the
  operator workbench;
- attach provenance/freshness/epistemic status to every material fact and
  proposed option;
- expose gate rationale and cancelled/speculative work in run telemetry;
- add explicit availability-versus-reservation-versus-purchase capability and
  approval states;
- add concurrency/version and unknown-outcome receipts to side-effecting work;
- add scenario fixtures for customer changes during planning, provider timeout,
  stale price, duplicate retry, and recoverable infeasibility;
- add cost/latency/provider-call budgets and model/prompt/version provenance to
  orchestration evidence.

### Executed bounded slice — 2026-09-01

The first implementation slice for `TPM-EXP-02` / `TPM-EXP-03` is complete:

- `src/intake/action_contract.py` defines the canonical derived action
  vocabulary: `observe`, `search`, `recommend`, `propose`, `hold`, `reserve`,
  `commit`, `message`, and `escalate`.
- `PlanCandidate` now carries an additive `action_contract` projection while
  preserving the existing decision-state `next_action` field for compatibility.
- The existing NB02 `AutonomyOutcome` is passed into the projection; no second
  autonomy policy or lifecycle state machine was introduced.
- `STOP_NEEDS_REVIEW` remains restricted to observation/escalation, follow-up
  messaging remains approval-gated, and hold/reserve/commit remain unavailable
  until provider, identity, authorization, freshness, idempotency, and recovery
  contracts exist.

Evidence is Tier 2 / S1 for the focused contract and PlanCandidate tests
(`41 passed`), Tier 2 / S1 for the orchestration/stage tests (`16 passed`), and
Tier 1 for Python compilation. This does not prove provider, browser, customer,
booking, payment, message-dispatch, or production behavior.

## 6. Doctrine / skill / persona boundaries

### Doctrine

The generic principles were promoted to `ARCHITECTURE_DOCTRINE.md` 1.1:

- decision-to-action decomposition;
- state versus memory separation;
- AI/deterministic truth boundary;
- progressive validation by consequence;
- dependency versus gate versus parallelism;
- short-circuiting with explicit policy rationale;
- current-plan infeasibility versus goal failure.

No travel-specific visa, flight, hotel, or Disney sequencing was promoted to
canonical doctrine.

### Skill

`/Users/pranay/Projects/skills/conversation-to-operating-model/SKILL.md` contains the reusable method,
artifact card, promotion rules, Waypoint questions, and evidence boundaries.
It is intentionally project-local because it names Waypoint surfaces and
current product conventions.

### Persona

`Docs/personas/PERSONA_TRAVEL_SYSTEMS_TPM_PROPOSAL_2026-09-01.md` defines a
bounded proposed overlay. It should not be added to the canonical Persona
Council registry until the ratification checks in that file pass.

## 7. Validation plan

### Completed in this slice

- Source discussion read in full: Tier 1 (direct artifact inspection).
- Current repository, docs, code seams, persona system, and dirty state
  inspected: Tier 1.
- Existing claims were mapped to current findings and architecture docs: Tier 1
  with inherited project evidence, not re-proven here.

### Required before claiming product improvement

- Refresh doctrine manifest and verify the canonical hash/version: Tier 1/2.
- Regenerate project context after doctrine change and verify provenance: Tier 1/2.
- Run focused tests for any implementation item; use S2 for reproduced defects.
- Add/execute scenario cases for gate short-circuit, stale state, retry after
  unknown outcome, concurrent updates, and customer goal recovery: Tier 2/3.
- Perform authenticated browser proof for operator next-action/uncertainty UI if
  that surface is implemented: Tier 4.
- Use real supplier/provider evidence only behind the existing connectivity and
  authorization gates: Tier 5.

## 8. Non-goals and unresolved decisions

- This record does not claim Waypoint is production-ready.
- It does not authorize booking, payment, visa submission, messaging, provider
  writes, deployment, or Git mutation.
- It does not create a new event-log-as-source-of-truth rewrite.
- It does not ratify a new Persona Council identity.
- It does not decide whether visa checks should always precede flight searches;
  that remains a workflow-specific cost/latency policy question.
- It does not assume the pasted tutor's numerical scores are objective product
  metrics.

## 9. Next owner actions

1. Project architecture/product owner: review `TPM-EXP-01` through `TPM-EXP-06`
   and select the first bounded exploration.
2. Backend owner: use the existing findings register for epistemic, memory,
   idempotency, lease, and temporal-obligation work; do not open duplicates.
3. Frontend owner: if exposing next-action or epistemic status, first inspect
   current dirty `IntakeTab`/workbench work and integrate into its canonical
   route.
4. Persona Council owner: evaluate `PER-TPM-WP-01` against existing personas;
   ratify, merge, or reject with provenance.
5. Verification owner: add the proposed scenario matrix only after the exact
   canonical lifecycle/action contracts are chosen.

## Completeness statement

**Established:** the lesson's core systems concepts are present in or strongly
aligned with the current Waypoint architecture and current audit backlog.

**Proposed:** the doctrine amendment, project skill, persona overlay, and new
exploration IDs in this record.

**Unknown:** whether the added TPM persona changes decisions in practice,
whether cost-aware gating materially improves Waypoint economics/latency, and
whether current runtime contracts prove unknown external outcomes safely.

**Revisit trigger:** after two scenario reviews using the skill, or when a real
provider/action integration is enabled, whichever comes first.
