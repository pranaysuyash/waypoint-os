# Trip Lifecycle — Four-Question State Contracts

**File:** `Docs/architecture/TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md`
**Authored:** 2026-09-04 (environment date checked; filename retains the 2026-09-02 task-spec date per E-14)
**Origin:** E-14 in `Docs/review/TPM_BLUEPRINT_TASKS_INVENTORY_2026-09-02.md:40` — four-question contracts for all 11 blueprint states. This doc is the **spec input for E-8** (server-side `TripLifecycleState` persistence, same file `:34`) and the worked example set for the TPM training thread (`Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md` §7).

**Purpose (doubles two ways):**

1. **Operator mental model** — for every lifecycle state: what is true, what an operator may do, what is forbidden, and what moves the trip out.
2. **Honest gap ledger** — every row cites the file that enforces or displays the rule *today*. Where nothing enforces it, the doc says so. That honesty is the deliverable: it is exactly what E-8 needs before a server-side persisted state can be trusted.

---

## 0. How to read this document

### The four questions

For each state, the contract answers:

1. **What is true here?** — the invariants a trip satisfies while in the state.
2. **What actions are allowed?** — operator and system actions the state permits.
3. **What actions are forbidden?** — actions the state must block (the enforcement question).
4. **Which events move us out, and to where?** — the out-transition table.

Each contract also carries two audit columns:

- **Implementation anchors** — `file:line` where this state's semantics live today (enforcement, derivation, or display).
- **Dormant gaps** — what is missing before this contract is *enforceable* rather than merely *described*.

### Enforcement vocabulary (used in the matrix at the end)

| Term | Meaning |
| --- | --- |
| **exists** | A code artifact names this state (enum, string set, router, label). |
| **enforced** | A validator raises, blocks, or refuses the action (`IllegalTripStatusTransition`, `RoutingError`, `GateVerdict.ESCALATE`, HTTP 4xx). |
| **derived** | The state is *inferred* at read time from six backend vocabularies — not persisted. |
| **displayed** | An operator sees it (`LifecycleChip`, inbox stage, blockers list). |

### The six vocabularies the derivation joins

The blueprint state does not exist as a column anywhere. `frontend/src/lib/trip-lifecycle.ts:1-19` (register N-4) joins, per trip:

| # | Vocabulary | Field | Canonical vocabulary file |
| --- | --- | --- | --- |
| 1 | Trip status | `trip.status` | `spine_api/core/trip_status.py:35-52` (quote-capable / intake-blocked sets, alias map) |
| 2 | Stage | `trip.stage` | `spine_api/services/trip_lifecycle_service.py:19` (`VALID_STAGES = discovery, shortlist, proposal, booking`) |
| 3 | Decision state | `trip.decision.decision_state` | `src/intake/constants.py:93-105` (`ASK_FOLLOWUP, PROCEED_INTERNAL_DRAFT, PROCEED_TRAVELER_SAFE, BRANCH_OPTIONS, STOP_NEEDS_REVIEW, STOP_REVIEW`) |
| 4 | Review status | `trip.analytics.review_status` | `src/analytics/review.py:22-29` (`pending, approved, rejected, escalated, revision_needed, recovery, resolved`) |
| 5 | Routing status | `TripRoutingState.status` | `spine_api/services/routing_service.py:14-19` (`unassigned, assigned, escalated, returned`) |
| 6 | Readiness / gate snapshots | `validation.readiness`, booking readiness, confirmation statuses | `src/intake/validation.py:50-66`, `spine_api/models/tenant.py:528-537`, `spine_api/services/confirmation_service.py:1-14` |

**Gates (the upstream producers):** `src/intake/gates.py`

- `GateVerdict` (gates.py:26-32): `PROCEED / RETRY / ESCALATE / DEGRADE`.
- **NB01 `intake_completion`** (gates.py:101-153): structural validity + MVB completeness. `ESCALATE` on structural failure (:124-129), `DEGRADE` when intake-minimum met but quote-ready fields missing (:132-144, driven by the `QUOTE_READY_INCOMPLETE` warning, `src/intake/validation.py:126`), `PROCEED` when full quote-ready fields present (:146-153).
- **NB02 `decision_readiness`** (gates.py:156-253): reads the raw decision state, applies the agency autonomy policy, and returns an `AutonomyOutcome` (gates.py:47-92) with `effective_action ∈ {auto, review, block}`. Safety invariant: `STOP_NEEDS_REVIEW` always blocks (:209-215).

**The one structural transition invariant (register N-2 / F-29):** `spine_api/core/trip_status.py:93-105` — a trip whose status is intake-blocked (`incomplete, needs_followup, needs_clarification, awaiting_customer_details, escalated`, :39-41) may **never** become quote-capable (`ready_to_quote, quote_ready, ready_to_book`, :35) in one hop. It is enforced inside every store write path (`spine_api/persistence.py:60,77,433-436,990,1317`), so router, pipeline, agent, and generic-update writers all inherit it. Every legal change is appended to `status_history` (trip_status.py:108-128, cap 50).

---

## 1. State diagram (ASCII)

Implemented/derived states in solid boxes; declared-dormant states in dashed boxes. `ESCALATED` is cross-cutting (Section 10).

```text
                         ┌──────────────┐
        customer inquiry │              │  NB01 PROCEED (full QUOTE_READY)
   ─────────────────────►│    INTAKE    │──────────────────────────────┐
   (pipeline run)        │              │                              │
                         └──────┬───────┘                              ▼
                                │                                 ┌─────────┐
                NB01 DEGRADE    │  pipeline run + NB01 PROCEED    │PLANNING │◄──────────────┐
                (saved, unquotable)                    (re-entry)  │         │               │
                                ▼                                └────┬────┘               │
                         ┌────────────────────┐    review approved    │                    │
   ┌────────────────────►│  NEEDS_INFORMATION │──────────┐            │ NB02: PROCEED_     │
   │  ASK_FOLLOWUP       │  (intake-blocked)  │          │            │ INTERNAL_DRAFT /   │
   │  from NB02          └─────────┬──────────┘          │            │ BRANCH_OPTIONS /   │
   │                               ▲                     │            │ STOP_*             │
   │                               │  customer details   │            ▼                    │
   │                               │  received →         │      ┌────────────┐             │
   │                               │  idempotent         └─────►│FEASIBILITY │             │
   │                               │  re-assess                 └─────┬──────┘             │
   │                               │                                  │ review approved /  │
   │                               │                                  │ re-run PROCEED     │
   │                               │                                  ▼                    │
   │                               │                        ┌────────────────────────┐     │
   │                               │                        │AWAITING_CUSTOMER_APPROV│─────┘
   │                               │                        │ (quote out, 72h lock)  │
   │                               │                        └───────────┬────────────┘
   │                               │                                    │ customer accepts
   │                               │                                    ▼
   │                               │                          ┌──────────────────┐
   │                               │                          │    BOOKED_SIDE   │
   │                               │                          │ (stage=booking / │
   │                               │                          │  ready_to_book)  │
   │                               │                          └───────┬──────────┘
   │                               │                                  │ review "approved"
   │                               │                                  ▼
   │                               │                          ┌──────────────────┐
   └───────────────────────────────┼──────────────────────────┤     COMPLETED*   │
                                   │                          └──────────────────┘
                                   │
                          ╔════════╧═══════════════════════════╗
                          ║  DORMANT (declared, no validator): ║
                          ║  ╌╌ IN_TRIP ╌╌   ╌╌ BOOKED ╌╌      ║
                          ║  ╌╌ BOOKING_IN_PROGRESS ╌╌         ║
                          ║  ╌╌ CHANGE_REQUESTED ╌╌            ║
                          ╚════════════════════════════════════╝

   ═════════════════════════════════════════════════════════════════════
   ESCALATED — reachable from any implemented state (Section 10).
   Resolution paths: return_for_changes → assigned/returned; reassign →
   assigned; review action resolved/recovery.
```

`*` COMPLETED is the only implemented state with **no writer** (Section 8, gaps).

**Orthogonal axis (not drawn):** the routing/assignment machine (`unassigned → assigned → escalated → returned`, plus `reassign`/`unassign` from any state) runs in parallel with the lifecycle above; it answers "who owns this trip", not "where is the trip". It interacts with the lifecycle at exactly one token: `escalated`.

---

## 2. INTAKE

| Question | Contract |
| --- | --- |
| **What is true** | A trip record exists (or an inquiry draft), and its packet is **not yet trustworthy enough to quote**. The status is unclassified-or-new (`"" → "new"` alias, `spine_api/core/trip_status.py:46-52`); no NB01 verdict is on record, or the last one predates the current packet. Operators see tone `neutral` with blockers "Review extracted packet". |
| **Allowed actions** | Run the pipeline (`POST /run`, `POST /trips/{trip_id}/reassess` subject to `allow_explicit_reassess` policy, `spine_api/routers/trip_lifecycle.py:39+`); edit packet fields (any edit to a reassess-trigger field queues re-processing — `spine_api/services/trip_lifecycle_service.py:21-39`); advance stage manually (`transition_trip_stage`, trip_lifecycle_service.py:153-201, with `expected_current_stage` optimistic concurrency :169-174); assignment ops if routing state is `unassigned` (`routing_service.py:97-148`). |
| **Forbidden actions** | Quote generation against an unvalidated packet (NB01 structural-failure path returns `GateVerdict.ESCALATE`, gates.py:124-129). If the trip's persisted status is intake-blocked, *any* one-hop write to quote-capable raises `IllegalTripStatusTransition` (trip_status.py:93-105, enforced at persistence.py:60/77/433/990/1317). |
| **Out-transitions** | `pipeline PROCEED with full QUOTE_READY fields` → PLANNING or FEASIBILITY (NB02 verdict decides which); `NB01 DEGRADE (QUOTE_READY_INCOMPLETE)` → NEEDS_INFORMATION (partial-intake save, `pipeline_execution_service.py:416-456`, status `"incomplete"`); `NB01 ESCALATE` → NEEDS_INFORMATION via the ESCALATE lead-persistence path (:324-414, status `"incomplete"`, `meta.blocked=true`); `stage transition to shortlist/proposal` → PLANNING. |
| **Anchors** | Derivation fallback: `frontend/src/lib/trip-lifecycle.ts:141-142` (`else → intake`); labels/actions :146, :158-159; status writers: `spine_api/services/pipeline_execution_service.py:373,453,529`; stage transition: `spine_api/services/trip_lifecycle_service.py:153-201`; display: `frontend/src/components/workspace/LifecycleChip.tsx:24`. |
| **Dormant gaps** | (a) INTAKE is the derivation's **catch-all** — any unknown status string lands here, so a `"delivered"` or `"snoozed"` trip *displays as Intake* (see gaps in Sections 8 and 15). (b) No server-side persisted state; the truth is six-way client inference (E-8). (c) Unknown status values pass through `normalize_trip_status` with only a warning (trip_status.py:71-82) — the typed enum slice is explicitly deferred (trip_status.py:19-24). |

---

## 3. NEEDS_INFORMATION

| Question | Contract |
| --- | --- |
| **What is true** | Intake is blocked and a human must close the loop. The packet (or a valid-but-thin one) is **persisted as an incomplete lead** — a customer contact exists regardless of completeness (ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31, `pipeline_execution_service.py:324-332`). Concretely: `trip.status ∈ {incomplete, needs_followup, needs_clarification, awaiting_customer_details}` or `decision.decision_state == ASK_FOLLOWUP` (`trip-lifecycle.ts:126`); the intake-blocked set is mirrored server-side (`trip_status.py:39-41`). Missing quote-ready fields are enumerable (`validation.py:50-66` + `QUOTE_READY_INCOMPLETE` warning :119-132). |
| **Allowed actions** | Ask the customer (follow-up creation), snooze/reschedule follow-ups (`spine_api/routers/inbox.py:38` carries `snoozed` in the inbox filter), manual operator field fill, queue re-assessment — the re-run is idempotent against the existing record (`pipeline_execution_service.py:332-343`), and every edit to a trigger field re-fires it (`trip_lifecycle_service.py:21-39`). |
| **Forbidden actions** | **Quote generation** — NB01 DEGRADE explicitly blocks it ("quote generation blocked", gates.py:132-144). **One-hop promotion to quote-capable** — structurally refused by `enforce_status_transition` for every writer (N-2 invariant). **Overwrite of any existing linked trip** — the ESCALATE/partial path never saves over an existing record; it preserves the trip ID (`pipeline_execution_service.py:332-343`). |
| **Out-transitions** | `CUSTOMER_DETAILS_RECEIVED` (follow-up response / `/optimistic-sync` merge / manual fill + re-assess) → re-run with full fields → NB01 PROCEED → FEASIBILITY or PLANNING (decision-state dependent). `human abandons` → remains (no TTL today — see gaps). `escalation of the follow-up itself` → ESCALATED. |
| **Anchors** | Derivation: `trip-lifecycle.ts:51-56, 89-91, 126`; blocker "Customer information missing" :89-91. Gate: `gates.py:133-144`. Persistence of incomplete lead: `pipeline_execution_service.py:373-377` (status `"incomplete"`, `meta.blocked=true` at :366-367). Inbox projection maps `needs_followup → options`, `awaiting_customer_details → details` (`spine_api/services/inbox_projection.py:45-46`). Mapping-doc worked example: `Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:117-123`. |
| **Dormant gaps** | (a) **No freshness/TTL policy** — nothing ages a stuck lead or fires `quote expired`-style reassess automatically (inventory I-2: `price_lock_expires_at` and quote expiry "never feed trip state; nothing fires reassess"). (b) `needs_clarification` is set by inbox projection heuristics (:391) but is not a canonical writer target of the pipeline — the vocabulary token exists in the guard set without a first-class producer. (c) The mapping doc's named event `CUSTOMER_DETAILS_RECEIVED` has **no first-class event object** — it is realized as "someone re-runs the pipeline"; there is no persisted event to audit. (d) E-8: state is derived, not persisted. |

---

## 4. FEASIBILITY

| Question | Contract |
| --- | --- |
| **What is true** | Extraction is complete enough to quote, but the **judgment layer says the agency is not yet free to act**: `decision.decision_state ∈ {PROCEED_INTERNAL_DRAFT, BRANCH_OPTIONS, STOP_NEEDS_REVIEW, STOP_REVIEW}` (`trip-lifecycle.ts:134-140`). The NB02 autonomy gate has run and (typically) returned `effective_action = review\|block`(`gates.py:156-253`);`approval_required` is true for review/block (:228). Operator tone is `info`; label "Needs Attention" / "Draft Quote" / "Needs Options" (`trip-lifecycle.ts:58-65`). |
| **Allowed actions** | Review options; run quote assessment; reviewer actions `approve / reject / request_changes(→revision_needed) / escalate` on `POST /trips/{trip_id}/review/action` (`spine_api/routers/trip_actions.py:32-63`, contract `spine_api/contract.py:273-283`); re-run the pipeline (re-assess) to produce a fresh judgment; reviewer adjudication of the escalation outcome (`escalation_outcome ∈ {false_escalation, missed_escalation, correct_escalation, not_applicable}`, contract.py:278-283). |
| **Forbidden actions** | Customer-facing delivery in traveler-safe framing (the trip is not `PROCEED_TRAVELER_SAFE`). `STOP_NEEDS_REVIEW` **cannot be auto-passed by any policy** — the safety invariant forces `effective_action = block` regardless of mode overrides (gates.py:209-215, `safety_invariant_applied=true`). A risky-trip auto path with risk flags is downgraded auto→review when `auto_proceed_with_warnings=false` (:218-225). |
| **Out-transitions** | `reviewer approve` (or a re-run whose fresh verdict is `PROCEED_TRAVELER_SAFE`) → AWAITING_CUSTOMER_APPROVAL; `reviewer reject` → review_status `rejected` with blocker "Quote declined by reviewer" (`trip-lifecycle.ts:80-82`, review.py:125-127) — **stays in FEASIBILITY** (no dedicated terminal); `request_changes` → review_status `revision_needed`, mandatory reassignment back to the agent (:110-121), repeated loops auto-escalate (:115-121) → ESCALATED; `ASK_FOLLOWUP` on re-run → NEEDS_INFORMATION. |
| **Anchors** | Derivation: `trip-lifecycle.ts:134-140`; decision-state vocabulary: `src/intake/constants.py:93-105`; autonomy gate: `gates.py:156-253`; review action handler: `src/analytics/review.py:62-137`; routing endpoint: `trip_actions.py:32-63`. |
| **Dormant gaps** | (a) `rejected` has **no out-transition of its own** — the trip stays in FEASIBILITY wearing a danger blocker; there is no DEAD/DECLINED lifecycle state (blueprint has none either; flagging the modeling hole). (b) FEASIBILITY and PLANNING are nearly indistinguishable to the operator (identical `nextActions` lists, `trip-lifecycle.ts:160-161`) — the split is judgment-layer, not workflow-layer, and is not explained in the UI. (c) E-8: derived only. |

---

## 5. PLANNING

| Question | Contract |
| --- | --- |
| **What is true** | The trip is **quote-capable** (`status = ready_to_quote`) and/or front-office work is in `stage ∈ {shortlist, proposal}` (`trip-lifecycle.ts:132`). Options and proposals are being assembled; per-quote negotiation may run (`NegotiationLog.status ∈ {OPEN, NEGOTIATING, WON, LOST}`, `spine_api/contract.py:56`). This is the only lifecycle state whose *entry from a blocked state is structurally guarded* (must pass through an active state first — trip_status.py:60-66 error message). |
| **Allowed actions** | Manual stage transitions along `discovery → shortlist → proposal → booking` (`transition_trip_stage`, `trip_lifecycle_service.py:153-201`); price-lock monitoring within the 72-hour window (`spine_api/routers/price_lock.py:4, 65-83`); supplier negotiation; NB02 re-runs that refine the verdict; assignment/ownership ops. |
| **Forbidden actions** | Same intake guards as everywhere (intake-blocked never → quote-capable in one hop). Booking-execution-tier money actions are **not gated by anything in this state** (that is the BOOKING_IN_PROGRESS gap, Section 12) — nothing in PLANNING itself forbids them because booking ops live downstream of stage `booking`; the stage transition is manual and unaudited against readiness. |
| **Out-transitions** | `NB02 verdict → PROCEED_TRAVELER_SAFE` → AWAITING_CUSTOMER_APPROVAL; `NB02 verdict → ASK_FOLLOWUP` → NEEDS_INFORMATION; `NB02 verdict → STOP_*/BRANCH/INTERNAL_DRAFT` → FEASIBILITY; `stage → booking` → BOOKED_SIDE (manual, no approval precondition — gap); escalation → ESCALATED. |
| **Anchors** | Derivation: `trip-lifecycle.ts:132`; stage vocabulary + transition: `trip_lifecycle_service.py:19, 153-201`; price-lock window: `price_lock.py:65-83`; negotiation vocabulary: `contract.py:56`; dashboard counter: `contract.py:996` (`ready_to_book`) via `src/services/dashboard_aggregator.py:243-291`. |
| **Dormant gaps** | (a) **Stage ≠ quote-capability**: `stage` and `status` advance independently; `ready_to_quote` status is written only as the *absence default* in the success path (`pipeline_execution_service.py:529` writes `"new"` unless overridden — the `ready_to_quote`/`ready_to_book` tokens are defined in the guard sets at trip_status.py:35 but **no pipeline writer ever sets them**; they arrive only via manual/legacy writes). The derived model still treats them as the PLANNING signal, so real trips reach PLANNING via `stage` alone. (b) Price-lock 72h is computed but **unwired to state** (I-2; mapping doc §7 :126-127 "exists but unwired to trip state"). (c) No audit trail on *why* a stage changed beyond the generic `stage_transition` audit event (trip_lifecycle_service.py:186-193). |

---

## 6. AWAITING_CUSTOMER_APPROVAL

| Question | Contract |
| --- | --- |
| **What is true** | The judgment layer has cleared the quote for the traveler: `decision.decision_state == PROCEED_TRAVELER_SAFE` (`trip-lifecycle.ts:128-129`, operator label "Ready to Book"). A price-lock window is nominally ticking: default 72h from save/creation (`price_lock.py:65-83`). |
| **Allowed actions** | Send the quote to the customer; await response; monitor/re-shop on rate drops inside the window (`price_lock.py:87+` list, `:141+` audit); re-lock on favorable drift (`:237-252`, `price_lock_re_locked_at`, `price_lock_arbitrage_saved` audit event); follow up via normal channels. |
| **Forbidden actions** | **Booking execution before customer acceptance — named by this contract but enforced by nothing.** This is the mapping doc's champion point: "the operator must sign off before supplier action means nothing unless the trip *cannot leave AWAITING_APPROVAL without the sign-off event*" (`Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:63`). There is no persisted customer-acceptance event and no validator tying stage `booking` to it. Re-locking outside the 72h window is not blocked — the window is advisory. |
| **Out-transitions** | `customer accepts` → BOOKED_SIDE *(event not yet modeled; today realized as the operator manually moving stage → booking)*; `customer asks changes` → FEASIBILITY (re-judgment) or NEEDS_INFORMATION (re-intake); `price-lock expiry without response` → *nothing today* (no timer; I-2) — contract says it should → FEASIBILITY re-quote; escalation → ESCALATED. |
| **Anchors** | Derivation: `trip-lifecycle.ts:128-129`, label map :59, actions :162; price-lock window: `price_lock.py:65-83`; mapping-doc framing: `TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:63, 120-124`. |
| **Dormant gaps** | (a) **The acceptance event does not exist** — the entire state's exit is operator discretion, i.e., the state currently *records* a judgment rather than *gating* an action. (b) No expiry timer → the 72h window can silently lapse. (c) E-8: derived only. |

---

## 7. BOOKED_SIDE

| Question | Contract |
| --- | --- |
| **What is true** | Booking work is underway: `stage == "booking"` or `status == "ready_to_book"` (`trip-lifecycle.ts:130`; operator tone `success`, label "Booked Side"). Per-component confirmations exist in the draft→recorded→verified saga (`spine_api/models/tenant.py:530, 532-537`); booking-readiness snapshots ride on `agentOperations.bookingReadinessStatus` and surface as a blocker when ≠ `ready` (`trip-lifecycle.ts:96-103`, mapped from `booking_readiness_status` at `frontend/src/lib/bff-trip-adapters.ts:205`). |
| **Allowed actions** | Execute booking tasks (task event stream: `task_created/blocked/ready/started/waiting/completed/cancelled`, `models/tenant.py:551-554`); record and verify confirmations per component type `flight\|hotel\|insurance\|payment\|other`(`tenant.py:528-530`); payment-queue operations (`spine_api/server.py:2540-2654`: payment/refund vocabularies are typed Literals); reviewer approve →`status = "delivered"`+ proactive feedback ask (`src/analytics/review.py:99-108`). |
| **Forbidden actions** | **Confirmation-saga skips**: `draft → verified` is illegal (must pass `recorded`); `verified → recorded` is illegal; only `draft → {recorded, voided}`, `recorded → {verified, voided}`, `verified → {voided}` are legal, and `voided` is terminal (`tenant.py:532-537`, enforced in `confirmation_service.py` state machine). **Post-delivery money moves** are typed, not forbidden (payment queue is a vocabulary, not a gate). |
| **Out-transitions** | `reviewer approve` → **`status = "delivered"`** (review.py:101) — *which no longer maps to any lifecycle state and will display as INTAKE* (gap below); `booking-blocked failure` → blocker surfaces via readiness snapshot (no state change); escalation → ESCALATED; `stage reverts to proposal` → PLANNING (manual, no precondition). |
| **Anchors** | Derivation: `trip-lifecycle.ts:130, 163`; confirmation state machine: `models/tenant.py:532-537` + `spine_api/services/confirmation_service.py:1-14` ("CRUD, encryption, state machine, event emission"); delivery writer: `src/analytics/review.py:99-108`; display: `LifecycleChip.tsx:24`. |
| **Dormant gaps** | (a) **`delivered` breaks the read-model**: `trip-lifecycle.ts` recognizes `completed` (:124-125) but *not* `delivered`; the only writer that ends a booking writes `delivered`, so approved trips **fall back to the INTAKE chip** — a live derivation/production divergence. (b) `ready_to_book` status has no producer (same as Section 5a). (c) No supplier rails: confirmations record *facts about* bookings; no validator prevents "booking actions" that were never authorized (NG-01/NG-03, EX-05 — mapping doc :76). (d) E-8: derived only. |

---

## 8. COMPLETED

| Question | Contract |
| --- | --- |
| **What is true** | The engagement is finished: `status == "completed"` (`trip-lifecycle.ts:124-125`, tone `success`). Operator next-actions: archive, collect feedback (:165). |
| **Allowed actions** | Archive; feedback collection (the proactive feedback ask fires at *delivery*, review.py:104-108); read-only analytics (dashboard aggregation, `spine_api/contract.py:992-997`). |
| **Forbidden actions** | **Nothing enforces closure.** No transition refuses writes into/out of a completed trip; `update_trip` paths remain open; only the N-2 invariant continues to apply mechanically. |
| **Out-transitions** | **None defined.** The blueprint treats COMPLETED as terminal; no code does. |
| **Anchors** | Derivation: `trip-lifecycle.ts:124-125, 165`. That is all — see gaps. |
| **Dormant gaps** | (a) **`completed` has no writer anywhere in the backend.** The review-approval path writes `delivered` (review.py:101); the pipeline writes `new`/`incomplete` (pipeline_execution_service.py:373/453/529); nothing writes `completed`. The state is reachable only by hand-edited data. (b) No terminal-state write protection (a "completed" trip can be freely re-edited and re-quoted into existence). (c) `delivered`/`completed` vocabulary conflict is the single sharpest enforcement gap in this ledger — **Decision needed** (Section 15). (d) E-8: derived only. |

---

## 9. IN_TRIP — DORMANT (declared, no input signal)

**DORMANT.** No validator exists for entering this state; naming a state without a validator recreates the freeform-string problem the repo spent register N-2/F-29 closing (`trip_status.py:4-24`).

| Question | Contract (as declared; enforcement = none) |
| --- | --- |
| **What is true** | The customer is actively traveling. Declared in the derived model with tone `info` and the explicit comment: "`in_trip` is declared but has no input signal yet (no disruption/crisis field feeds it today) — documented dormant" (`trip-lifecycle.ts:110-112`, :152, :164). |
| **Allowed actions (intended)** | Monitor disruptions (disruption radar, `spine_api/routers/disruption_radar.py`; crisis ops, `crisis_ops.py`); stand by for traveler requests. |
| **Forbidden actions (intended)** | Any quote-machinery mutation of a live itinerary without a change contract (CHANGE_REQUESTED, Section 13). Enforced by: **nothing**. |
| **Out-transitions (intended)** | `trip dates pass` → COMPLETED; `disruption` → ESCALATED (or the blueprint's replan branch). No event exists. |
| **Anchors** | `trip-lifecycle.ts:30, 110-112, 152, 164`; dormant-state discipline: `TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:76`; 24-month intent: `:110`. |
| **Dormant gaps** | No input signal (no field feeds it); no entry validator; no exit event; disruption/crisis routers exist but write nothing into `trip.status`. |

---

## 10. ESCALATED (cross-cutting)

ESCALATED is the one token that exists in **all three independent state machines** — trip status (`trip_status.py:40`), routing status (`routing_service.py:171`), and review status (`review.py:28`) — plus the gate vocabulary (`GateVerdict.ESCALATE`, gates.py:30). That triple-writing is its strength (any layer can flag it) and its hazard (Section 15, decision 3).

### 10.1 Reachable FROM which states

| From | Trigger | Anchor |
| --- | --- | --- |
| Any pipeline run | NB01 `ESCALATE` verdict (structural failure) — blocked result + lead persisted | `gates.py:124-129`; `pipeline_execution_service.py:324-414` |
| INTAKE / NEEDS_INFORMATION / FEASIBILITY / PLANNING / AWAITING_CUSTOMER_APPROVAL / BOOKED_SIDE | Reviewer action `escalate` on `/trips/{trip_id}/review/action` → `review_status = "escalated"`, assignee → `management_queue`, `requires_review = true` | `trip_actions.py:32-63`; `review.py:130-132` |
| Any trip repeated in revision loops | Automatic owner escalation policy on `revision_needed` cycles | `review.py:115-121` (`apply_owner_escalation_policy` at :116) |
| Routing: `assigned` or `returned` | `escalate_trip` — escalation owner added, primary assignee **preserved** | `routing_service.py:151-185` (guard at :162-166) |
| Derived display | `review_status == "escalated" OR status == "escalated"` → state `escalated`, danger tone, blocker "Escalated — needs an owner" | `trip-lifecycle.ts:77-79, 122-123, 179-181` |

### 10.2 Resolution paths BACK

| Path | To | Semantics | Anchor |
| --- | --- | --- | --- |
| `return_for_changes` | routing `returned` (assignment-wise "assigned state"; primary stays responsible) | Clears escalation owner + timestamp; handoff logged; re-escalation from `returned` is legal (routing_service.py:162) | `routing_service.py:229-262` |
| `reassign` | routing `assigned` | New primary owner; **clears escalation owner entirely** (escalation is resolved by transfer of ownership) | `routing_service.py:188-226` (clears :210-212) |
| Review action `recovery` / `resolved` | review_status `recovery` / `resolved` | Escalation outcome adjudicated via `escalation_outcome` taxonomy | `review.py:22, 257`; `contract.py:278-283` |
| Re-run with fixed packet | back through gates | Fresh NB01/NB02 verdicts re-derive the state | `trip_lifecycle.py:39+`; `pipeline_execution_service.py` reprocess target :332-334 |

### 10.3 What is true / allowed / forbidden while escalated

- **True:** a human owner is named (escalation owner on the routing row; `management_queue` synthetic assignee on the review row); danger blocker shown (`trip-lifecycle.ts:77-79`).
- **Allowed:** reviewer/routing resolution actions above; re-assessment; all read paths.
- **Forbidden:** **quote-capability in one hop.** `escalated` is a member of `INTAKE_BLOCKED_STATUSES` (trip_status.py:40), so an escalated trip can never be written to `ready_to_quote/ready_to_book` without first passing through a non-blocked status — every writer inherits this (persistence.py guard sites).
- **Dormant gaps:** (a) The review-axis escalation (`review_status`) and routing-axis escalation (`TripRoutingState.status`) are **not synchronized** — resolving one leaves the other stale, and the derived model ORs them (`trip-lifecycle.ts:122`), so a trip stays "Escalated" until *both* axes agree. (b) The `management_queue` synthetic assignee has no operator surface (inventory I-1: "management_queue synthetic assignee has no surface"). (c) The escalated queue is a **client-side slice of the workspace list only** — not server-accurate under pagination (I-1, same file `:34` row above it). (d) **Design hazard:** `escalated ∈ INTAKE_BLOCKED` couples a *mid-lifecycle crisis flag* to *intake trust semantics*. Escalating a trip that sits in BOOKED_SIDE silently revokes its quote-capability, and — since FEASIBILITY-resolutions do not rewrite status — the trip can remain permanently one-hop-barred from booking until a writer touches status through an intermediate value. Intended safety, unexamined side effect. **Decision needed** (Section 15).

---

## 11. BOOKING_IN_PROGRESS — DORMANT (declared; partial artifacts exist)

**DORMANT.** The blueprint's BOOKING state. The repo holds the *per-component* saga but **no trip-level BOOKING state, therefore no validator for entering it**.

| Question | Contract (as declared; enforcement = partial, per-component only) |
| --- | --- |
| **What is true (intended)** | Money-touching execution is underway under an approval that is *bound* — today approval is defined but not bound (`TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:63`). What exists: confirmation saga per component (`models/tenant.py:532-537`), booking-task gates (`BookingExecutionPanel` task gates), the 72h freshness window (`price_lock.py:65-83`). |
| **Allowed (intended)** | Execute booked supplier actions within authority tiers (`AuthorityTier`/`ScopedCapabilityToken`, `src/schemas/boundary_contracts.py:17-58` — currently **zero pipeline callers**, mapping doc :35). |
| **Forbidden (intended)** | Money/supplier actions above the operator's authority tier; execution without a bound approval. **Enforced by: nothing** — "there is no 'what cannot happen' enforcement, because money-touching autonomy is unbound" (mapping doc §7 :127-128). The live heuristic ceiling (`evaluate_autonomy_dispatch_gate`, `spine_api/services/autonomy_gates.py:31+`) is a $10k-style heuristic, not a state gate. |
| **Out-transitions (intended)** | `all components verified` → BOOKED → IN_TRIP; `component failure/cancellation` → ESCALATED. No event objects exist. |
| **Anchors** | `confirmation_service.py` saga; `models/tenant.py:528-544`; `autonomy_gates.py`; `src/schemas/boundary_contracts.py:17-58`; mapping doc :76, :117-128; inventory I-2/F-14/EX-14. |
| **Dormant gaps** | No trip-level status; no bound approval validator; no compensating actions for a saga (mapping doc :76: "a saga with no compensating action is untestable theater"); authority tiers unwired. Per the repo's own discipline, this state must remain a placeholder until a validator for *entering* it exists. |

---

## 12. BOOKED — DORMANT (declared; no artifact)

**DORMANT.** All bookings confirmed, travel not yet started.

| Question | Contract (as declared; enforcement = none) |
| --- | --- |
| **What is true (intended)** | Every component verified (confirmation saga terminal state `verified` per component) and paid per the payment queue (`payment_status = "paid"`, `spine_api/server.py:2554-2563`). |
| **Allowed (intended)** | Pre-trip logistics: documents, passes (`pass_generator.py`), duty-of-care snapshots; read-only itinerary ops. |
| **Forbidden (intended)** | Any component mutation without CHANGE_REQUESTED. Enforced by: **nothing** — no trip-level BOOKED status exists; `ready_to_book` (the nearest token) is guard-vocabulary with no producer (trip_status.py:35). |
| **Out-transitions (intended)** | `travel starts` → IN_TRIP. No event exists. |
| **Anchors** | Blueprint vocabulary: `TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:29` (L2). Nothing else — this state has no code artifact beyond the derived enum's absence of it. |
| **Dormant gaps** | Entire contract is aspirational; booking rails absent (NG-01/NG-03, EX-05). Declare dormant and do not ship UI for it until the entry validator (all-components-verified ∧ paid) exists. |

---

## 13. CHANGE_REQUESTED — DORMANT (declared; nearest live analog is routing `returned`)

**DORMANT.** Customer requests a change to a booked trip.

| Question | Contract (as declared; enforcement = none) |
| --- | --- |
| **What is true (intended)** | A booked trip has an open customer change request; the itinerary is frozen pending re-plan; cancellation/penalty exposure is live. |
| **Allowed (intended)** | Capture the change request; re-price (re-enter FEASIBILITY/PLANNING against the *new* constraints while the old booking stays cancelable); saga compensation (cancel/rebook). |
| **Forbidden (intended)** | Mutating the live booking outside a compensating action. Enforced by: **nothing**. The nearest live analog is `return_for_changes` on the *routing* axis (`routing_service.py:229-262`) — but that changes ownership, not the trip, and is why the two axes must not be conflated (Section 15, decision 5). |
| **Out-transitions (intended)** | `change re-planned and approved` → BOOKED (new itinerary); `change withdrawn` → BOOKED (original); `cancel` → terminal refund path (`refund_status` vocabulary, server.py:2564-2573). |
| **Anchors** | Blueprint vocabulary: `TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:29, 76`; refund vocabulary: `spine_api/server.py:2564-2573`. |
| **Dormant gaps** | No event object, no validator, no saga compensation. Untestable theater until booking rails exist (repo's own :76 discipline). |

---

## 14. Enforcement-gap matrix

Legend: **✅** exists/enforced/displayed · **🟡** partial (what's missing noted) · **❌** absent.

| Contract row (state) | Exists in code? | Enforced? | Displayed to operator? |
| --- | --- | --- | --- |
| INTAKE — definition | ✅ derivation fallback `trip-lifecycle.ts:141` | n/a (residual state) | ✅ `LifecycleChip.tsx:24` (trips list + detail) |
| INTAKE — forbid quote on unvalidated packet | ✅ NB01 gate | ✅ `GateVerdict.ESCALATE` raises/blocks (`gates.py:126-129`) | 🟡 blocker only after escalation; raw gate reasons not shown per-trip |
| NEEDS_INFORMATION — definition | ✅ `trip-lifecycle.ts:51-56,126` | ✅ mirrored in `INTAKE_BLOCKED_STATUSES` (trip_status.py:39-41) | ✅ warn chip + blocker |
| NEEDS_INFORMATION — forbid quote generation | ✅ NB01 DEGRADE | ✅ "quote generation blocked" (`gates.py:132-144`) | 🟡 reason string only in gate metadata, not chip |
| NEEDS_INFORMATION — forbid one-hop promotion to quote-capable | ✅ N-2 invariant | ✅ `enforce_status_transition` in every store writer (`persistence.py:60,77,433,990,1317`) | ❌ operators see only a generic save failure, not the invariant message (raises server-side; message not surfaced in UI) |
| NEEDS_INFORMATION — forbid overwriting existing trip | ✅ ESCALATE ADR | ✅ never-overwrite + dead-ID guard (`pipeline_execution_service.py:332-343`) | ✅ "ESCALATE skipped lead save" is log-only; operator sees preserved record |
| FEASIBILITY — definition | ✅ `trip-lifecycle.ts:134-140` | ✅ decision states are typed (`constants.py:93-105`) | ✅ chip labels "Needs Attention"/"Draft Quote"/"Needs Options" |
| FEASIBILITY — forbid bypassing STOP_NEEDS_REVIEW | ✅ safety invariant | ✅ forced block (`gates.py:209-215`) | ❌ `safety_invariant_applied` not displayed |
| FEASIBILITY — reject/revision outcomes | ✅ review actions | ✅ typed actions + mandatory reassignment (`review.py:110-121`) | 🟡 blockers shown ("Quote declined by reviewer", "Revisions requested") but no DEAD state; trip lingers in FEASIBILITY |
| PLANNING — definition | ✅ `trip-lifecycle.ts:132` | ❌ no gate ties `ready_to_quote` to NB01-PROCEED freshness | ✅ chip |
| PLANNING — stage transitions legal-set + concurrency | ✅ `VALID_STAGES` + `expected_current_stage` | ✅ 422/conflict (`trip_lifecycle_service.py:165-174`) | ❌ conflict surfaced as HTTP error, not explained in UI |
| PLANNING — 72h price-lock window | ✅ `price_lock.py:65-83` | ❌ advisory only; expiry changes nothing | ✅ price-lock endpoints exist; ❌ no state card (I-2) |
| AWAITING_CUSTOMER_APPROVAL — definition | ✅ `trip-lifecycle.ts:128-129` | ❌ derived from judgment only | ✅ chip "Ready to Book" |
| AWAITING_CUSTOMER_APPROVAL — forbid booking before acceptance | 🟡 named in this doc + mapping doc | ❌ **no acceptance event, no validator** (the champion gap) | ❌ nothing tells the operator booking is premature |
| BOOKED_SIDE — definition | ✅ `trip-lifecycle.ts:130` | ❌ stage `booking` is manual, no approval precondition | ✅ chip |
| BOOKED_SIDE — confirmation saga transitions | ✅ `tenant.py:532-537` | ✅ state machine in `confirmation_service.py` | 🟡 per-component status visible in booking panels; illegal-transition errors not surfaced as lifecycle blockers |
| BOOKED_SIDE → COMPLETED via approval | ✅ review approve writes `delivered` | ❌ `delivered` **not recognized** by the read-model → approved trips display as INTAKE | ❌ **wrong chip after approval** (live display bug) |
| COMPLETED — definition | 🟡 derived branch only (`trip-lifecycle.ts:124-125`) | ❌ no writer for `status="completed"` anywhere | 🟡 chip exists; state is effectively unreachable |
| COMPLETED — terminal write protection | ❌ | ❌ no transition refuses edits post-completion | ❌ |
| IN_TRIP — declared | ✅ enum + comment (`trip-lifecycle.ts:30,110-112`) | ❌ **no validator** (deliberately dormant) | 🟡 label/next-actions defined; unreachable in practice |
| BOOKING_IN_PROGRESS — declared | 🟡 per-component artifacts only | ❌ money autonomy unbound (`autonomy_gates.py` heuristic; `boundary_contracts.py` zero callers) | 🟡 task/confirmation panels; no trip-level state |
| BOOKED — declared | ❌ (vocabulary only, mapping doc L2) | ❌ | ❌ |
| CHANGE_REQUESTED — declared | ❌ (routing `returned` is an analog on the wrong axis) | ❌ | ❌ |
| ESCALATED — reachability (routing axis) | ✅ | ✅ only `assigned`/`returned` escalate (`routing_service.py:162-166`) | 🟡 FE chip is a client-side slice, not server-accurate (I-1); `handoff_history` persisted, zero UI |
| ESCALATED — reachability (review axis) | ✅ | ✅ typed action (`review.py:130-134`) | ❌ `management_queue` assignee has no surface (I-1) |
| ESCALATED — resolution paths | ✅ return/reassign/recovery | ✅ guards at `routing_service.py:203, 243` | ❌ no escalation console; resolution is invisible to operators |
| ESCALATED — forbid one-hop quote-capable | ✅ member of intake-blocked set | ✅ same N-2 invariant | ❌ invariant message not surfaced (and see coupling hazard, §10.3) |
| ALL — server-side persisted lifecycle state | ❌ **E-8 not built** | ❌ six-way client inference only | — |

---

## 15. Decisions needed

Each line is a decision the enforcement-gap matrix forces; none has a current owner.

1. **Decision needed: unify the delivery/completion vocabulary.** Review approval writes `status = "delivered"` (`src/analytics/review.py:101`) but the lifecycle read-model recognizes only `"completed"` (`frontend/src/lib/trip-lifecycle.ts:124-125`) and no backend writer ever emits `completed`. Today, approving a trip demotes it to the INTAKE chip. Either (a) add `delivered` → COMPLETED to the derivation as a stopgap, or (b) rename the review writer to `completed` — but (b) must first check `spine_api/core/trip_status.py` alias coverage and every consumer of `delivered` (Supersession Workflow applies; the vocabulary is load-bearing in `dashboard_aggregator.py`).

2. **Decision needed: bind the approval event.** AWAITING_CUSTOMER_APPROVAL currently *records* a judgment; it does not *gate* booking. Ship a persisted customer-acceptance event and a validator requiring it before `stage → booking` — this is the single highest-leverage contract row in the doc (mapping doc :63).

3. **Decision needed: decouple `escalated` from `INTAKE_BLOCKED_STATUSES`.** Its membership in the intake-blocked set (trip_status.py:40) means a mid-booking crisis silently revokes quote-capability, and any recovery path must route status through an intermediate value. Options: keep the coupling and document it as intended hard-stops; or split into `INTAKE_BLOCKED` (trust semantics) vs `HARD_STOPPED` (crisis semantics) sets sharing one guard but distinct recovery protocols. The one-hop guard itself should survive either way.

4. **Decision needed: dual escalation axes.** `review_status.escalated` and `TripRoutingState.status == "escalated"` resolve independently, while the derived state ORs them (`trip-lifecycle.ts:122`). Decide the canonical axis and make the other a projection of it, or build the sync rule — otherwise escalated trips stay escalated until two teams both act.

5. **Decision needed: keep the routing axis out of the lifecycle.** `returned` is a routing state, not a trip state; CHANGE_REQUESTED must not be "implemented" by reusing it. Document the two-axis model (this doc §1) in operator onboarding so nobody "fixes" CHANGE_REQUESTED by overloading `return_for_changes`.

6. **Decision needed: producers for the quote-capable statuses.** `ready_to_quote` / `quote_ready` / `ready_to_book` are enforced-against (guard sets, trip_status.py:35) but written by nothing in the pipeline (`pipeline_execution_service.py:529` defaults to `"new"`). Either the pipeline should set them on NB01-PROCEED/NB02-auto (making the N-2 invariant meaningful for real traffic), or the guard sets should shrink to the statuses that actually occur. Asymmetric vocabularies make the invariant vacuous on the happy path.

7. **Decision needed: unclassified-status policy.** `delivered`, `snoozed`, `blocked`, `needs_clarification` and any future token pass through `normalize_trip_status` with only a warning (trip_status.py:71-82) and display as INTAKE. Decide: typed enum now (the deferred slice, trip_status.py:19-24), or an operator-visible "UNKNOWN STATUS" blocker so silent mis-derivation stops.

8. **Decision needed: sequencing E-8 against this ledger.** E-8 (server-side persistence of the derived state) should not be built until decisions 1, 3, and 6 land — otherwise E-8 persists the current divergences as truth. The inventory itself notes the dependency: "Needs read-model distribution data + I-1/I-3 usage first" (`TPM_BLUEPRINT_TASKS_INVENTORY_2026-09-02.md:34`).

---

## Appendix A — Source-of-truth files cited in this document

| File | Role |
| --- | --- |
| `frontend/src/lib/trip-lifecycle.ts` | Derived lifecycle read-model (N-4): state derivation :114-143, intake-blocked set :51-56, decision labels :58-65, blockers :72-106, in_trip dormancy :110-112 |
| `frontend/src/components/workspace/LifecycleChip.tsx` | Operator display of the derived state (chip + blockers + next action) |
| `frontend/src/lib/bff-trip-adapters.ts` | Workspace/inbox status partitions (:59-75); booking-readiness mapping (:205) |
| `spine_api/core/trip_status.py` | Quote-capable & intake-blocked sets (:35-41), aliases (:46-52), transition invariant (:93-105), status_history (:108-128) |
| `spine_api/persistence.py` | Invariant enforcement at every write path (:60, :77, :433-436, :990, :1317) |
| `spine_api/services/routing_service.py` | Assignment state machine: assign/claim/escalate/reassign/return/unassign with guards and handoff history |
| `spine_api/services/trip_lifecycle_service.py` | `VALID_STAGES` (:19), reassess trigger fields (:21-39), stage transition with optimistic concurrency (:153-201) |
| `spine_api/routers/trip_lifecycle.py` | Explicit re-assess endpoint, policy-gated (`allow_explicit_reassess`) |
| `spine_api/routers/trip_actions.py` | Review action endpoint (`:32-63`) |
| `src/intake/gates.py` | `GateVerdict` (:26-32), `AutonomyOutcome` (:47-92), NB01 (:101-153), NB02 (:156-253) |
| `src/intake/validation.py` | `INTAKE_MINIMUM` (:50), `QUOTE_READY` (:56), `QUOTE_READY_INCOMPLETE` warning (:119-132) |
| `src/intake/constants.py` | `PipelineStage` (:23-31), `GateIdentifier` (:38-45), decision states (:93-105) |
| `src/analytics/review.py` | Review action vocabulary + handlers (:22-29, :99-137), auto-escalation on revision loops (:118-121), `delivered` writer (:101), recovery (:257) |
| `spine_api/services/pipeline_execution_service.py` | ESCALATE lead persistence / never-overwrite (:324-414), partial-intake incomplete save (:416-456), defense-in-depth validation block (:467-488), success save (:529) |
| `spine_api/models/tenant.py` | Confirmation types/statuses/valid transitions (:528-537), task event types (:551-554) |
| `spine_api/services/confirmation_service.py` | Per-component confirmation state machine + event emission (:1-14) |
| `spine_api/routers/price_lock.py` | 72h window computation (:65-83), re-shop/re-lock audit (:237-252) |
| `spine_api/contract.py` | Negotiation quote statuses (:56), `ReviewActionRequest` + escalation_outcome (:273-283), dashboard counters (:992-997) |
| `spine_api/routers/inbox.py` / `spine_api/services/inbox_projection.py` | Inbox status filter incl. `snoozed` (:38); status→stage projection (:45-46, :391) |
| `spine_api/server.py` | Payment/refund typed vocabularies (:2540-2573) |
| `Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md` | Blueprint L2 vocabulary (:29), authority binding champion point (:63), dormant-state discipline (:76), §7 answer key (:117-128) |
| `Docs/review/TPM_BLUEPRINT_TASKS_INVENTORY_2026-09-02.md` | E-8 (:34), E-14 (:40), I-1/I-2 sequencing inputs |
