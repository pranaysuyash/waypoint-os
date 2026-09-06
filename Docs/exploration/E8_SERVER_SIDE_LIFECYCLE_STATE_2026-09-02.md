# E8: Server-Side Persisted TripLifecycleState — Exploration & Design

**Date:** 2026-09-02 (researched and verified against the working tree 2026-09-04)
**Type:** EXPLORE — research and design only. No code changed. One read-only DB/file probe (documented in §7.1); no writes anywhere.
**Trigger:** TPM blueprint 12-month horizon: "persisted server-side `TripLifecycleState` (superseding six-way inference); allowed-actions API" (`Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md:109`). Register N-4 shipped the client-side read-model (`frontend/src/lib/trip-lifecycle.ts`); this is its server-side successor, deliberately gated on E-1's real status-distribution data (`Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md:34`, gate discipline per `:52` C-03).
**Companion format:** `Docs/exploration/E2_ANALYTICS_JSON_TO_JSONB_MIGRATION_2026-09-02.md` (same exploration series conventions).

---

## 1. Question

Should the six-way client-side lifecycle inference become **one persisted, server-derived state** — the single read-model that overview counts, the trips list, queues, SLA aging, and an allowed-actions API all consume — and if so, where is it derived, where is it stored, how is existing data backfilled, and what must be true before persistence is honest?

---

## 2. The six vocabularies — evidence map

Everything below is **VERIFIED** by direct file read on 2026-09-04 unless marked otherwise. Line numbers refer to the current working tree.

### 2.1 `trip.status` — freeform string, invariant-guarded (not enumerated)

- **Column:** `status: Mapped[str] = mapped_column(String(50), default="new")` — `spine_api/models/trips.py:39`. Freeform; no DB enum, no CHECK constraint.
- **Guard:** `spine_api/core/trip_status.py` (register N-2):
  - `QUOTE_CAPABLE_STATUSES = {ready_to_quote, quote_ready, ready_to_book}` (`trip_status.py:35`)
  - `INTAKE_BLOCKED_STATUSES = {incomplete, needs_followup, needs_clarification, awaiting_customer_details, escalated}` (`trip_status.py:39-41`)
  - Alias normalization `"" → new`, `in_progress/inprogress → in_progress`, `active` (`trip_status.py:46-52`); unknown values **pass through with a warning** (`normalize_trip_status`, `:71-82`)
  - Invariant: intake-blocked can never become quote-capable in one hop (`enforce_status_transition`, `:93-105`)
  - History: `record_status_transition` appends `{from,to,at}` to `status_history`, cap 50 (`:108-128`, `STATUS_HISTORY_CAP` at `:43`)
- **Observed status values written today** (each site verified):

  | Value | Writer |
  |---|---|
  | `new` / `active` | `spine_api/routers/inbound.py:175` (`"new" if missing_fields else "active"`) |
  | `incomplete` / `new` | `spine_api/services/pipeline_execution_service.py:373,453,529` (`trip_status=` args into `_build_processed_trip`) |
  | `assigned` | `spine_api/routers/inbox.py:104-107`, `spine_api/routers/legacy_ops.py:229,754` |
  | `archived` | `spine_api/routers/inbox.py:231` |
  | `needs_followup` | `src/agents/runtime.py:878` |
  | `delivered` | `src/analytics/review.py:101` (on review approve) |
  | `recovery` | `src/analytics/review.py:268` (feedback recovery loop) |
  | `escalated` | ESCALATE lead-persistence patch (named as a writer class in `trip_status.py:5-23` docstring) |
  | generic PATCH | `PATCH /trips/{trip_id}` accepts any `status` string (`spine_api/server.py:2119-2134`: "status: Trip status (new, in_progress, completed, etc.)") |

- **Client-imagined vocabulary:** `STATUS_TO_STATE` in `frontend/src/lib/bff-trip-adapters.ts:10-25` enumerates `new, incomplete, needs_followup, awaiting_customer_details, snoozed, assigned, in_progress, ready_to_quote, ready_to_book, blocked, completed, cancelled`. **No backend writer for `snoozed`, `blocked`, `ready_to_quote`, `ready_to_book`, `completed`, `cancelled` was found in the write-site sweep above** (VERIFIED absence in sweep; INFERRED that some come from legacy/seed data — `completed` is written via `PATCH /trips/{trip_id}` by operator action and gated by `ready_gate_failures` at `server.py:2144-2149`).
- **Intake-blocked set drift:** backend includes `escalated` in `INTAKE_BLOCKED_STATUSES`; the frontend mirror `INTAKE_BLOCKED_STATUSES` (`trip-lifecycle.ts:51-56`) omits it (escalation is a separate, higher-precedence branch — functionally equivalent, structurally divergent; parity-relevant, §5.3).

### 2.2 `trip.stage` — enumerated, manually transitionable

- **Vocabulary:** `VALID_STAGES = {"discovery", "shortlist", "proposal", "booking"}` — `spine_api/services/trip_lifecycle_service.py:19`.
- **Column:** `stage: Mapped[str] = mapped_column(String(50), default="discovery", nullable=False)` — `spine_api/models/trips.py:40` (added by `add_stage_to_trips` migration).
- **Transition:** `transition_trip_stage` with `expected_current_stage` optimistic-concurrency guard + `stage_transition` audit event — `trip_lifecycle_service.py:153-201` (guard at `:165-175`, audit at `:186`).
- **Drift found:** the dashboard aggregator counts `stage in ("strategy", "output")` as ready-to-book (`src/services/dashboard_aggregator.py:252-253`) — **neither value exists in `VALID_STAGES`** (VERIFIED). The timeline endpoint validates yet another stage vocabulary `{intake, packet, decision, strategy, safety, discovery, booking}` (`spine_api/routers/trip_observability.py:67`) — a seventh vocabulary nobody reconciled.

### 2.3 `decision.decision_state` — typed Literal, stored in JSON

- **Vocabulary:** `DecisionState = Literal["ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT", "PROCEED_TRAVELER_SAFE", "BRANCH_OPTIONS", "STOP_NEEDS_REVIEW"]` — `src/intake/constants.py:92-98` (+ frozen tuple `DECISION_STATES` `:100-107`).
- **Storage:** inside `decision: Mapped[dict]` JSON column — `spine_api/models/trips.py:57`; producer logic in `src/intake/decision.py:2126-2252` (branch assignment sites).
- **Ghost values in the client derivation** (VERIFIED absent from the backend Literal and from `DECISION_STATES`):
  - `"STOP_REVIEW"` — matched in `trip-lifecycle.ts:63` (label map) and `:139` (state branch). No backend producer.
  - `"suitability_review_required"` — checked in `frontend/src/components/workspace/ReviewControls.tsx:39`. No backend producer.
  - `"PROCEED"` — appears in the backend test fixture `tests/test_state_contract_parity.py:69` (not a valid value; test-only).
- **Consumer:** `derive_action_contract(decision_state, effective_action)` maps each state to the allowed/next action set — `src/intake/action_contract.py:47-53, 75-118`. This is the kernel of the future allowed-actions API (§4.5).

### 2.4 `review_status` — not a column; stored in `analytics` JSON, with a dual-location drift

- **Canonical location:** `analytics["review_status"]` — written by the review state machine (`src/analytics/review.py:81`, default `"pending"` at `:74`, recovery variant at `:257`); read by the frontend BFF adapter (`frontend/src/lib/bff-trip-adapters.ts:506`: `review_status: analytics.review_status`).
- **Value vocabulary:** `VALID_ACTIONS = {approved, rejected, escalated, revision_needed, recovery, resolved}` — `review.py:22` (+ `ACTION_MAP` `:25-31`). Frontend type: `'pending' | 'approved' | 'rejected' | 'escalated' | 'revision_needed'` — `frontend/src/types/governance.ts:30` — **missing `recovery` and `resolved`** (VERIFIED).
- **Dual-location drift (VERIFIED):** `spine_api/services/agent_runtime_adapters.py:28-31` (`set_review_status`) writes a **top-level** `{"review_status": status}` via `update_trip`. The frontend reads only `analytics.review_status`, so agent-runtime review writes are **invisible to the UI** (on SQL they are folded into `analytics._extra.review_status` by `_fold_unmapped_updates`, `spine_api/persistence.py:99-128`; on file store they sit at top level — neither location is the one the adapter reads).
- There is **no `review_status` column** on `Trip` (VERIFIED against `spine_api/models/trips.py:24-80` column list).

### 2.5 Routing status — separate table, own state machine, unused by the lifecycle

- **Vocabulary:** `TripRoutingState.status ∈ {unassigned, assigned, escalated, returned}` — `spine_api/services/routing_service.py` (`unassigned` `:49`; `assigned` via assign/claim/reassign `:115,141,213`; `escalated` `:171`; `returned` `:249`; reset `:281`).
- **History:** `handoff_history` append-only entries — `routing_service.py:57-77`. Transitions validate current state (`:107-111,162,243`) and the service deliberately does not emit audit events itself — "caller logs audit event" (`routing_service.py:11`).
- **Key disconnect (VERIFIED):** the client lifecycle reads `review_status === "escalated" || status === "escalated"` (`trip-lifecycle.ts:77,122`) — it **never reads `TripRoutingState`**. Routing-escalated trips surface in the lifecycle only if some other vocabulary was also flipped. N-4 already flagged that escalated trips vanish from every queue via the `management_queue` synthetic assignee (`TPM_...2026-09-01.md` §5 N-4).

### 2.6 Readiness / agent_operations — two sub-vocabularies, partially typed

- **`validation.readiness` tiers (typed):** `ReadinessTier = Literal["intake_minimum", "quote_ready", "proposal_ready", "booking_ready"]` — `src/intake/readiness.py:39-46`; pure `compute_readiness` (`:276+`, "NEVER mutates stage", `:5`); persisted inside the `validation` JSON column (`spine_api/models/trips.py:56`; read pattern `trip["validation"]["readiness"]` at `trip_lifecycle_service.py:182,200`; field declared `src/intake/validation.py:89`).
- **`agent_operations` fields (untyped strings):** snake_case trip keys written by the agent runtime, e.g. `booking_readiness_assessment` / `booking_readiness_status` (`src/agents/runtime.py:2476,2517`); consumed client-side by `extractAgentOperations` (`bff-trip-adapters.ts:190-225`) into `AgentOperationsMetadata` (`frontend/src/lib/api-client.ts:409-439`). Values are freeform strings (the lifecycle only tests `bookingReadinessStatus !== "ready"`, `trip-lifecycle.ts:96-103`) — no enum exists backend-side (VERIFIED).
- The TS derivation consumes `bookingReadinessStatus` only for **blockers**, not for state selection — noted for scope: the server port needs blocker parity too, or blockers stay client-composed in phase 1.

---

## 3. Where lifecycle changes originate — write-path inventory (for event emission)

Every site below is a place a lifecycle transition can occur; all are **VERIFIED**.

**Store choke points (the enforcement layer already lives here — `TripStore`):**

| Path | Guard/history hook |
|---|---|
| `FileTripStore.save_trip` | inline guard + `status_history` append — `spine_api/persistence.py:427-437` |
| `SQLTripStore.save_trip` | guard + history into `analytics._extra.status_history` — `persistence.py:~985-1000` (via `_apply_status_guard_orm`, `:70-96`) |
| dict-record updates | `_apply_status_guard` — `persistence.py:48-67` |
| SQL update merge (incl. `update_trip_if_version_for_agency`) | merged-guard helper — `persistence.py:1300-1335` |
| raw-SQL atomic updates | `_status_guard_sql_predicate` WHERE-clause enforcement — `persistence.py:131-139` |

**Router/service mutation sites:**

- `PATCH /trips/{trip_id}` — generic status/stage writes; ready-gate on `completed` (`ready_gate_failures`, `src/analytics/policy_rules.py:57`); logs `trip_status_changed` audit event — `spine_api/server.py:2119-2149, 2493`.
- `POST /trips/{trip_id}/review/action` → `process_review_action` — status + `analytics.review_status` + audit event `review_action` with **pre_state/post_state deltas already captured** (`src/analytics/review.py:71-160`).
- `transition_trip_stage` — audit `stage_transition` (`trip_lifecycle_service.py:186`).
- Routing transitions (`routing_service.py`) — `handoff_history` in-table; audit emitted by callers (`trip_assigned`, `trip_unassigned` events exist in the audit-event inventory).
- Inbox triage bulk assign/archive (`spine_api/routers/inbox.py:104-107,227,231`); legacy ops assign (`legacy_ops.py:229,754`); follow-up snooze/complete (`spine_api/routers/followups.py:132,184,188,230` — note: sets `follow_up_status`, not `status`).
- Optimistic-sync merge — `spine_api/routers/inbound.py:346,367` (`update_trip_if_version_for_agency` with `new_status`).
- Agent runtime — `needs_followup` follow-up write (`src/agents/runtime.py:878`), booking-readiness fields (`:2517`), review-status adapter (`agent_runtime_adapters.py:31`).

**Existing event transport (reuse, do not build):**

- **AuditStore is the event log.** 28 distinct event names enumerated (grep inventory); lifecycle-relevant ones already exist: `trip_status_changed`, `stage_transition`, `review_action`, `trip_assigned`, `trip_unassigned`, `trip_snoozed`, `trip_reassess_queued`.
- **SSE exists:** `GET /api/trips/{trip_id}/events/stream` polls `AuditStore.get_events_for_trip` every 1s and streams new events — `spine_api/routers/trip_observability.py:149-192`. A new `lifecycle_changed` audit event **automatically appears** on this stream with zero new transport.
- **Timeline exists:** `GET /api/trips/{trip_id}/timeline` maps audit events via `TimelineEventMapper` with pre/post state (`trip_observability.py:60-145`).
- Undo/redo checkpoint stack exists for trip mutations (`spine_api/routers/trip_history.py`; `src/state/mutation_history_stack.py`) — lifecycle changes should ride the same checkpoint convention if they flow through mutation-tracked paths (INFERRED; wiring not verified).

**Conclusion of §3:** every lifecycle-relevant mutation already flows through `TripStore.save/update` (both backends), and every user-visible change already lands in `AuditStore`. There is exactly **one** place to derive-and-emit (the store choke points) and **zero** new transport needed.

---

## 4. Design options

| | **A. Derived-on-read (server-side)** | **B. Derived-on-write, persisted (recommended)** | **C. Persist-on-mutation, writer-owned** | **D. DB trigger** |
|---|---|---|---|---|
| Where derived | In `GET /trips`, projections, stats — from the six persisted vocabularies | Inside `TripStore.save/update` choke points (§3), result persisted alongside the trip | Each of the ~12 writer sites sets `lifecycle` explicitly | Postgres trigger on `trips` row update |
| Schema change | None | `lifecycle` + `lifecycle_changed_at` columns; history folded like `status_history` | Same as B | Same as B + trigger DDL |
| Queue/SLA filtering | Must recompute per row per request (projection already O(n) per agency — `inbox_projection.py` docstring) | `WHERE lifecycle = X` indexable; `lifecycle_changed_at` makes state-aging arithmetic | Same as B | Same as B |
| Drift risk vs client derivation | Same inputs → same outputs by construction if one shared function; but every consumer must call it | Parity test (§5.3) locks the port | Maximum: 12 writers × 9 states = the drift we are eliminating | None in-app, but invisible to file backend |
| Dual-store compatibility | Yes | Yes (file store: plain keys; SQL: columns + `_extra` fold — same pattern as `status_history`, `persistence.py:433-437, 990-1000`) | Yes but N-writer surface | **No** — file backend and tests bypass SQL; raw-SQL update path (`persistence.py:131`) wouldn't fire a row trigger on JSON-vocabulary changes reliably |
| Backfill | Not needed (derived at read) | One pass with the same pure function (§5.1) | One pass + audit every writer | One pass |
| Precedent in repo | Partially: `InboxProjectionService` already recomputes derived fields per request (`spine_api/services/inbox_projection.py`) | Exactly the N-2 pattern: guard+history inside the store, "so that *every* writer inherits it" (`trip_status.py:16-18`) | Rejected by N-2's own rationale | None in this repo |

**Why not A (server-side on-read):** it centralizes the logic (good) but keeps lifecycle unpersisted, so queues keep scanning all trips to classify (the `dashboard_aggregator` already logs a perf warning doing exactly this over `list_trip_summaries(limit=10000)` — `src/services/dashboard_aggregator.py:227-232`), and SLA aging still has no first-class `state_entered_at`. Why not C: the trip_status docstring already diagnosed this failure mode — freeform semantics "written by several independent paths" forced a hand-patched ADR (`trip_status.py:4-8`). Why not D: violates the dual-store parity contract that the repo just finished hardening (`AGENTS.md` "File-store backend parity (resolved 2026-05-12)") and the raw-SQL/JSON update paths.

### 4.1 The persisted record (Option B shape)

```python
# spine_api/core/trip_lifecycle.py (new, pure, no I/O)
TripLifecycleState = Literal[
    "intake", "needs_information", "feasibility", "planning",
    "awaiting_customer_approval", "booked_side", "in_trip", "completed", "escalated",
]

def derive_trip_lifecycle(trip: dict) -> str:
    """Port of frontend/src/lib/trip-lifecycle.ts:114-143 — byte-for-byte
    precedence: escalated > completed > needs_information >
    awaiting_customer_approval > booked_side > planning > feasibility > intake."""
```

- **Columns:** `lifecycle: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)` and `lifecycle_changed_at: Mapped[Optional[datetime]]` on `Trip` (`spine_api/models/trips.py`), via one Alembic migration appended to the verified single linear chain (see `E2_..._2026-09-02.md` §2.2 for the chain audit method).
- **History:** `lifecycle_history` entries `{from, to, at, trigger}` appended **in the same choke points that already append `status_history`** (`persistence.py:433-437` file; `analytics._extra.lifecycle_history` on SQL, mirroring the documented "no dedicated status_history column yet" compromise at `persistence.py:990-1000`). A dedicated SQL history column can come later without contract change because all reads go through `TripStore`.
- **Emission:** in the same guarded branch, if the derived state changed → `AuditStore.log_event("lifecycle_changed", actor, {trip_id, from, to, trigger, inputs_digest})`. The existing SSE poll loop (`trip_observability.py:164-185`) and `TimelineEventMapper` pick it up untouched; `trigger` names the writer (e.g. `review_action`, `stage_transition`, `optimistic_sync`) for the queue "why is this row here" requirement (TPM §6, 6-month goal).
- **File store:** same two keys written as plain JSON keys in `FileTripStore.save_trip`/`update_trip` — additive, parity by construction.

---

## 5. Recommendation

**Option B — derived-on-write at the existing `TripStore` guard choke points**, with the TS library demoted to the reference implementation and a pinned parity test as the drift gate. Sequenced behind E-1 data (§7).

Reasoning, first principles: the lifecycle is a **function of persisted state**, and this repo has already established that functions of persisted state which every writer must respect belong in the store layer with an audit trail (`trip_status.py` is precisely that, for one invariant). The client derivation proved the vocabulary join is real and useful (it is shipped and tested — `frontend/src/lib/__tests__/trip-lifecycle.test.ts`); what it cannot do is (a) index queues, (b) timestamp state entry for SLA arithmetic, (c) serve non-UI consumers (stats, agent runtime, allowed-actions), or (d) be trusted when the vocabularies underneath it drift silently — which §2 documents they already have (ghost `STOP_REVIEW`/`suitability_review_required`, invisible top-level `review_status`, out-of-vocab dashboard stages, three competing SLA rules).

### 5.1 Backfill

1. **Port first, backfill second.** The Python port must exist and pass the parity suite (§5.3) before any write.
2. **Tool:** `tools/backfill_trip_lifecycle.py` — idempotent, batched via `TripStore.list_trip_summaries_for_agency` / `list_trips` (not raw SQL: the `trips` table is under **FORCE ROW LEVEL SECURITY** — VERIFIED today: a direct `SELECT status, count(*) FROM trips` as table owner returns `ERROR: query would be affected by row-level security policy`; therefore backfill MUST run through the app's `TripStore` identity, which also keeps file/SQL parity for free).
3. **Semantics:** for each trip, `derived = derive_trip_lifecycle(trip)`; write only when `trip["lifecycle"]` is missing or ≠ derived; append history entry with `trigger: "backfill"`; **never** touch the source vocabularies; additive-only consistent with the test-data rule (`AGENTS.md`, "Test Data Must Be Additive" — no overwrite of any other field, resumable, dry-run report first).
4. **Order:** per-agency batches; the known test agency (`d1e3b2b6-...`, `AGENTS.md`) is expected to produce numbers that vary by session — that is accumulation, not a counting bug.

### 5.2 What the TS library becomes

`frontend/src/lib/trip-lifecycle.ts` stays, but its role flips: after each consumer cutover it is reduced to (a) a dev-mode assertion that `trip.lifecycle === deriveTripLifecycle(trip)` (surfacing drift loudly in development instead of silently), and (b) the reference for `label/tone/nextActions` presentation, which legitimately remains client-side. Per the Supersession Workflow (`AGENTS.md`), field-by-field comparison must confirm the server port covers state derivation; **`buildBlockers` is NOT superseded in phase 1** (it reads `agentOperations` freeform fields the server port does not yet classify) — it stays client-side until the readiness vocabulary is typed (§7 gate 3).

### 5.3 Parity test (the dual-write trap antidote)

The failure to prevent: server persists lifecycle=L while the client derivation, given the same raw trip, computes L′≠L — queues and chips disagree with no error anywhere.

- **Pattern mirror:** `tests/test_state_contract_parity.py` (note for the record: despite its name, that file tests encryption/storage parity; the *pattern* to mirror is its structure — shared fixtures, both paths exercised over the identical input, sentinel cases for unknown values).
- **New file:** `tests/test_lifecycle_parity.py` + shared fixtures `tests/fixtures/lifecycle/*.json` (one fixture per state, plus adversarial rows: missing `status`, unknown status string, ghost `STOP_REVIEW`, top-level-only `review_status`, escalated-only-in-routing, `stage="strategy"`).
- **Mechanism:** each fixture carries `expected_state` computed by the **TS implementation** (generated by a small vitest run over the same JSON at authoring time, or a `node -e` subprocess inside the pytest for live coupling). The Python port must return exactly `expected_state` for every fixture. Both implementations consume the **same file**, so any vocabulary edit must touch the fixture to keep CI green — the drift gate.
- **Runtime check:** a CI job (or the existing contract-surface test pattern, cf. `frontend/src/hooks/__tests__/useTrips.contract-surface.test.tsx`) asserting persisted `lifecycle` equals client derivation over a seeded trip corpus, until the last consumer cutover retires the client branch.

---

## 6. Consumer migration order

Rationale for the order: cheapest-and-most-broken first, each step independently verifiable, client fallback retained until the next step is proven.

1. **Overview counts** — today the frontend calls `GET /api/stats` (`frontend/src/lib/api-client.ts:490-492`) and **no such backend route exists** (VERIFIED: the only stats route is `/api/dashboard/stats`, `spine_api/routers/system_dashboard.py:66`; `asTripStats` therefore returns `null` on 404, `frontend/src/hooks/useTrips.ts:33-48,105`). Ship `GET /api/stats` as `GROUP BY lifecycle` over the persisted column (O(index) instead of the aggregator's 10k-row scan + per-trip parsing, `dashboard_aggregator.py:227-280`). This also fixes the aggregator's verified semantic bugs (`pending_review = len(trips) - completed` at `:274`; `stage in ("strategy","output")` at `:252-253`).
2. **Trips list / lifecycle chip** — `TripResponse` gains `lifecycle`; `LifecycleChip` reads the server field; client derivation kept as dev-only assertion (§5.2).
3. **Queues** — `InboxProjectionService` filters/prioritizes on `lifecycle` instead of re-deriving from `_STATUS_TO_INBOX_STAGE` (`spine_api/services/inbox_projection.py:59-70`), and the BFF's duplicate maps (`bff-trip-adapters.ts:27-42`) stop being load-bearing. Escalation becomes queue-visible by joining routing state into the derivation inputs server-side (fixes the routing-escalation blind spot, §2.5).
4. **SLA aging** — one source of truth: `lifecycle_changed_at`. Today there are **three competing implementations** (all VERIFIED): client BFF `computeSlaStatus` 4d/7d on days-since-`created_at`/events ignoring `status_history` (`bff-trip-adapters.ts:375-403`); `get_trip_sla_status` with hour thresholds new 3/4h, assigned 18/24h, in_progress 60/72h (`dashboard_aggregator.py:292-330`); `_SLA_DAYS_*` in inbox projection (`inbox_projection.py:76-78`). Consolidate to per-lifecycle-state thresholds resolved from `SupportSettings` (the aggregator already resolves agency SLA settings, `:237-240`) and delete the other two. This is the single largest correctness win: state entry time, not creation time, is what "aging in stage" means.
5. **Allowed-actions API** — extend the existing decision-only contract (`derive_action_contract(decision_state, effective_action)`, `src/intake/action_contract.py:75-118`) into a lifecycle-gated endpoint (e.g. extend the existing trip response or one route — never a parallel route, per the no-duplicate-routes rule): allowed/blocked actions per state, with the four-question contract (what is true / allowed / forbidden / out-transitions) answered from `lifecycle` + guard modules. `NEXT_ACTIONS` in the TS lib (`trip-lifecycle.ts:157-167`) is the seed vocabulary.

---

## 7. Prerequisites and gates (the E-1 discipline)

**"Name a state only when a validator exists."** The rule comes from `trip_status.py:21-24` itself: full enforcement was deliberately deferred "gated on the derived read-model … validating the real status distribution."

### 7.1 What the distribution says today (and why it is not enough)

- Direct SQL distribution: **blocked by design** — FORCE RLS denies even the table owner a naked aggregate (probed 2026-09-04, read-only, result documented above). Production truth must flow through the app path or live collectors.
- File-store dev corpus (read-only scan of `data/trips/*.json`, 1,936 files, 2026-09-04): `active` 978 · `assigned` 495 · `new` 304 · **no `status` key at all** 138 · `incomplete` 21. This is a dev/test corpus, not production truth — but it already proves two things: (a) **absent status is a real case** the derivation must tolerate (the TS lib does, `trip.status ?? ""`), and (b) the dev distribution concentrates in intake/assigned, so the higher states (`booked_side`, `completed`, `in_trip`) would be **unvalidated** if persisted today.
- Register mapping: E-1 here is **E-01** "Extraction/pipeline gate lanes 'expected-as-actual' → live collectors" (`Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md:34`), the same ground-truth lane that gates C-03's router design ("only after E-01…E-04 provide ground truth", `:52`). *(Mapping of "E-1" to register row E-01: INFERRED from the gate language; the task brief's "E-1's real status-distribution data" has no other candidate producer in the register.)*

### 7.2 Gates before the implementation slice

| # | Gate | Why | Status |
|---|---|---|---|
| 1 | **Review-status reconciliation**: one location (`analytics.review_status`), one value set (decide: are `recovery`/`resolved` canonical?), fix `agent_runtime_adapters.py:31` writing the invisible top-level key | Persisting a state derived from a two-location vocabulary bakes the drift in | Open — prerequisite micro-task (§8.1) |
| 2 | **Ghost-value purge**: delete `STOP_REVIEW` + `suitability_review_required` branches or produce them; backend fixtures stop using `"PROCEED"` | Parity test would permanently encode dead branches | Open |
| 3 | **Readiness typing**: `booking_readiness_status` et al. get a Literal (or are excluded from server state derivation phase 1 and blockers stay client-side) | Untyped inputs cannot be ported deterministically | Open |
| 4 | **E-01/E-04 live collectors emitting per-status/per-lifecycle counts** for ≥ some window | Honest vocabulary closure: states that never occur in production get no persisted name (and `in_trip` in particular has **no producer today** — declared dormant in the TS lib, `trip-lifecycle.ts:108-113`) | Blocked on E-01 (🛠, register `:34`) |
| 5 | **`in_trip` admission decision** | Only state with zero input signal; persisting a dormant name violates the discipline | ⚖ owner call (§9) |
| 6 | **Timeline stage-vocab reconciliation** (`trip_observability.py:67` vs `VALID_STAGES`) | History UX will display lifecycle alongside stage; three stage vocabularies is two too many | Open (can trail) |

---

## 8. Sized next tasks

Sequenced; each is independently verifiable; none starts before its gate.

| # | Task | Size | Depends on |
|---|---|---|---|
| 8.1 | Reconcile `review_status` location + value set; fix `set_review_status` write path; update `ReviewStatus` type | 0.5 d | — |
| 8.2 | Purge/produce ghost decision_states; fix `test_state_contract_parity.py:69` fixture value | 0.25 d | — |
| 8.3 | Port `deriveTripLifecycle` → `spine_api/core/trip_lifecycle.py` (pure fn + label/tone map), typed `TripLifecycleState` | 0.5 d | 8.1, 8.2 |
| 8.4 | Author `tests/fixtures/lifecycle/*.json` (one per state + adversarial set from §5.3) with TS-generated expectations | 0.5 d | 8.3 |
| 8.5 | `tests/test_lifecycle_parity.py` (mirror of the parity-test pattern) + CI drift gate | 0.5–1 d | 8.4 |
| 8.6 | Lifecycle-distribution collector (E-1 hook): app-path per-agency counts of raw status × derived lifecycle, emitted to metrics/eval lane | 0.5 d | 8.3 |
| 8.7 | Migration (`lifecycle`, `lifecycle_changed_at`) + derive-on-write wiring at the five store choke points (§3 table) + `lifecycle_changed` audit event | 1.5–2 d | 8.5, gate 4 |
| 8.8 | `tools/backfill_trip_lifecycle.py` (dry-run → per-agency batches, via TripStore, additive-only) | 0.5 d | 8.7 |
| 8.9 | Consumer 1: `GET /api/stats` from `lifecycle` (fixes the dead frontend call) | 0.5 d | 8.8 |
| 8.10 | Consumer 2–3: trips chip + inbox projection on persisted state; retire duplicate BFF maps to dev assertions | 1 d | 8.9 |
| 8.11 | Consumer 4: single SLA service on `lifecycle_changed_at`; delete the three legacy computations (Supersession Workflow documented) | 1 d | 8.10 |
| 8.12 | Consumer 5: allowed-actions endpoint extending `action_contract` with lifecycle gating | 1–1.5 d | 8.10, ⚖ |

Total: ≈ 8–10 focused days, of which the first ≈ 3 days (8.1–8.6) are **unblocked today**.

---

## 9. Decision needed

1. **Storage shape:** dedicated `lifecycle` + `lifecycle_changed_at` columns with history folded into `analytics._extra.lifecycle_history` (recommended — mirrors the `status_history` precedent, keeps both backends symmetric) vs. a first-class `trip_lifecycle_history` table now. The column route is cheaper and reversible; the table route pays off only if lifecycle history gains per-entry queries (SLA forensics).
2. **Backfill timing:** after gate 4 (E-1 data lands — recommended, so the vocabulary is closed once) vs. immediately with a dev-corpus-derived provisional vocabulary and a re-backfill later. Note the re-backfill is cheap by design (§5.1), so the cost of waiting is only the continued drift the parity test would otherwise catch.
3. **`in_trip`:** admit at launch (requires wiring disruption radar / crisis ops as its producer — 24-month horizon per TPM §6) or persist the other eight states and leave `in_trip` unnamable until a validator exists (recommended).
4. **Escalation unification:** should routing-escalated (`TripRoutingState.status == "escalated"`, `routing_service.py:171`) feed the lifecycle derivation as a first-class input (recommended — fixes the verified blind spot) or stay a separate axis surfaced only in queue filters?
5. **Review-status value set:** are `recovery`/`resolved` canonical states (backend writes them, `review.py:22`) or should they be retired from the vocabulary and re-mapped (frontend does not know they exist)?

---

## Appendix: verification ledger

- All file:line citations re-read on 2026-09-04 working tree. Six-vocabulary inventory: **VERIFIED**.
- Write-path inventory (§3): **VERIFIED** (grep-swept `update_trip`/`save_trip` across routers/services/agents; 17 router call sites; store choke points read directly).
- `/api/stats` dead-endpoint finding: **VERIFIED** (frontend call site + backend route sweep; `asTripStats` null fallback read).
- Three-SLA-implementations finding: **VERIFIED** (all three code paths read).
- File-store distribution scan (1,936 files): **VERIFIED** read-only probe; interpretation as dev-only proxy: **INFERRED** (files are test/roundtrip artifacts by name).
- FORCE RLS blocking direct SQL aggregates: **VERIFIED** by probe (error text captured; no ALTER attempted).
- Ghost vocabulary values (`STOP_REVIEW`, `suitability_review_required`, `PROCEED`, `snoozed`-as-status): **VERIFIED absent from backend vocabularies**; whether any legacy persisted rows carry them: **INFERRED possible** (E-1 collectors will confirm).
- E-1 = register E-01 mapping: **INFERRED** (see §7.1).
- `in_trip` having no producer: **VERIFIED** for the TS inputs; a future disruption-radar producer existing elsewhere: **INFERRED unlikely** (24-month horizon per TPM §6 names it as future work).
