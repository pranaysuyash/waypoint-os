# E-1: Typed-Enum Status Enforcement for Trip Status — Exploration

**Date:** 2026-09-02 (data refresh 2026-09-04)
**Status:** Exploration — read-only research, no code changed
**Feeds:** register items N-2-slice-2 (typed status vocabulary) and E-12 (contract hardening)
**Claim marking:** every claim is tagged **[V]** (verified — file:line or live query) or **[I]** (inferred — reasoning from verified evidence)

---

## 1. The Question

Should `Trip.status` become a typed enum (Python `StrEnum` + TS string-literal union + store-boundary rejection of unknowns), and if so, what is the exact vocabulary, the alias map, and the additive rollout?

The constraint that gated this decision — "don't legislate states from a whiteboard" (stated in `spine_api/core/trip_status.py:18-23` **[V]**) — is now half-satisfiable: this exploration captured the **actual status distribution** from the live test database and the file store, plus the complete writer inventory. The remaining gate is production (multi-agency) distribution, which no local dataset can supply.

The question is no longer "what statuses exist?" — that is answered below. It is: **"which of the ~25 status-ish tokens in the codebase are load-bearing, and do we enforce the surviving set at the store boundary?"**

---

## 2. Current State

### 2.1 What shipped this wave (the invariant layer) **[V]**

`spine_api/core/trip_status.py` provides:

| Symbol | Line | Purpose |
|---|---|---|
| `QUOTE_CAPABLE_STATUSES` | :35 | `{"ready_to_quote", "quote_ready", "ready_to_book"}` |
| `INTAKE_BLOCKED_STATUSES` | :39-41 | `{"incomplete", "needs_followup", "needs_clarification", "awaiting_customer_details", "escalated"}` |
| `normalize_trip_status()` | :71-82 | alias map (`""→new`, `inprogress→in_progress`, …); unknowns pass through with `logger.warning` |
| `enforce_status_transition()` | :93-105 | intake-blocked → quote-capable is illegal in one hop |
| `record_status_transition()` | :108-128 | appends `{from,to,at}` to `status_history` (cap 50) |

Enforcement is wired into **every** persistence write path — `spine_api/persistence.py:48-94` (`_apply_status_guard` / `_apply_status_guard_orm`), the file-store CAS write (:427-436), and the SQL update paths via `_status_guard_sql_predicate` (:131-140, applied at :1383-84, :1456-57, :1530-31). Frontend read-model mirror: `frontend/src/lib/trip-lifecycle.ts` (derives lifecycle from status/stage/decision_state/review_status; mirrors `INTAKE_BLOCKED_STATUSES` at :50, :89, :126).

### 2.2 Writer inventory — every status literal actually written to `Trip.status` **[V]**

| # | Writer | File:Line | Values written | Trigger |
|---|---|---|---|---|
| 1 | Inbound lead creation | `spine_api/routers/inbound.py:175` | `"new"` if missing_fields else `"active"` | POST /inbound |
| 2 | Inbound field sync promotion | `spine_api/routers/inbound.py:348-352,367` | `"active"`, `"new"`, or passthrough (promotable set: `INTAKE_BLOCKED_STATUSES - {"escalated"} ∪ {"new"}`, :62) | trip sync |
| 3 | Pipeline lead persistence (blocked path) | `spine_api/services/pipeline_execution_service.py:373` | `"incomplete"` (or existing status) | ESCALATE ADR early-exit |
| 4 | Pipeline lead persistence (partial reprocess) | `spine_api/services/pipeline_execution_service.py:453` | `"incomplete"` or existing | partial packet |
| 5 | Pipeline lead persistence (full) | `spine_api/services/pipeline_execution_service.py:529` | `"new"` or existing | full packet save |
| 6 | FollowUp overdue agent | `src/agents/runtime.py:878` | `"needs_followup"` | follow-up due |
| 7 | Legacy ops assign | `spine_api/routers/legacy_ops.py:229,754` | `"assigned"` | assign/reassign |
| 8 | Inbox bulk assign | `spine_api/routers/inbox.py:227` | `"assigned"` | bulk assign |
| 9 | Inbox bulk archive | `spine_api/routers/inbox.py:231` | `"archived"` | bulk archive |
| 10 | Operator PATCH (freeform) | `spine_api/server.py:2139-2140` → update at :2489 | **any string** (`TripPatchRequest.status: Optional[str]`, `spine_api/contract.py:1029-1032` — no Literal) | PATCH /trips/{id}; `"completed"` additionally gated by ready-gate (:2144-2163); `"new"` additionally unassigns (:2497) |
| 11 | Seed/scenario import | `spine_api/server.py:1542,1645` | passthrough, default `"new"` | seed loader |
| 12 | File store insert default | `spine_api/persistence.py:930` | `"new"` when status key absent | `save_trip` |
| 13 | ORM column default | `spine_api/models/trips.py:39` | `"new"` (`String(50)`, no CHECK) | SQL insert |

Status defaults that are **response-model** defaults, not writes (still vocabulary, and one is inconsistent): `spine_api/contract.py:1451` `ConciergeMonitorResponse.trip_status: str = "IN_PROGRESS"` — **uppercase**, matching nothing else in the system **[V]**; `spine_api/contract.py:1171` response mapping default `"new"` **[V]**.

### 2.3 Vocabulary consumers (readers that assume values, never write them) **[V]**

| Consumer | File:Line | Values assumed |
|---|---|---|
| Agent scan eligibility | `src/agents/runtime.py:647,855` | `{"", new, incomplete, needs_clarification, awaiting_customer_details}` |
| Agent terminal sets (7 copies) | `src/agents/runtime.py:769,852,983,1189,1391,2324,2482`; `src/agents/communicator_agent.py:52` | `{closed, cancelled, completed, archived, lost, booked}` (variants omit lost/booked) |
| Agent draft routing | `src/agents/runtime.py:832-840` | `quoted`, `proposal` |
| Metrics revenue/pipeline | `src/analytics/metrics.py:51,191,315` | `booked`, `delivered`, `completed` |
| Inbox projection stage map | `spine_api/services/inbox_projection.py:44-53` | 9 values incl. `snoozed` |
| Assignment routing state (⚠ different field) | `spine_api/services/routing_service.py:49,115,141,171,213,249,281` | `TripRoutingState.status ∈ {unassigned, assigned, escalated, returned}` — a **separate enum on a separate column**, not trip status |
| Follow-up status (different field) | `spine_api/routers/followups.py:46,132,188,230` | `follow_up_status ∈ {pending, completed, snoozed}` |
| Frontend status→state map | `frontend/src/lib/bff-trip-adapters.ts:10-25` | 12 values: new, incomplete, needs_followup, awaiting_customer_details, snoozed, assigned, in_progress, ready_to_quote, ready_to_book, blocked, completed, cancelled |
| Frontend workspace/inbox partitions | `frontend/src/lib/bff-trip-adapters.ts:59-73`; `frontend/src/lib/trip-domain.ts:1-9` | workspace: {assigned, in_progress, ready_to_quote, ready_to_book, blocked}; inbox: {new, incomplete, needs_followup, awaiting_customer_details, snoozed} |
| Frontend status mutation | `frontend/src/components/workspace/panels/IntakePanel.tsx:853` | `{ status: 'completed' }` via `updateTrip` (only frontend writer **[V]**) |
| Frontend type | `frontend/src/lib/api-client.ts:340` | `status?: string` — freeform |
| Generated API types | `frontend/src/types/generated/spine-api.ts:196` | `trip_status?: string` — freeform |

### 2.4 The observed distribution (2026-09-04, live read-only SQL + file store) **[V]**

RLS-scoped query against `waypoint_os` (test agency `d1e3b2b6-…`; 21,283 of ~21.5k total trips) and top-level keys of `data/trips/*.json`:

| status (lowercase) | SQL n | file-store n | has a backend writer? | handled by frontend STATUS_TO_STATE? |
|---|---:|---:|---|---|
| assigned | 18,527 | 495 | yes (inbox/legacy assign) | yes |
| new | 1,752 | 304 | yes (inbound, defaults) | yes |
| in_progress | 853 | 0 | only via operator PATCH | yes |
| incomplete | 132 | 21 | yes (pipeline) | yes |
| active | 76 | 978 | yes (inbound) | **NO — falls through to undefined state** |
| completed | 13 | 0 | operator PATCH + ready gate | yes |
| cancelled | 2 | 0 | operator PATCH only | yes |
| archived | 0 | 0 | yes (inbox) | **NO — not in STATUS_TO_STATE** |
| *(status key missing)* | — | 138 | legacy direct writes | — |

Findings from the data:

- **Zero case variants in SQL** (7 distinct lowercase values, `count(DISTINCT status)` = 1 per norm) **[V]** — case-fold fear is theoretical in the store, live only in the response default `"IN_PROGRESS"` and reader-side `.lower()` calls (runtime.py does `.lower()` everywhere).
- **Only 69 trips carry `status_history`** (all under `in_progress`) **[V]** — the guard shipped this wave; history is too thin to attribute distribution to writers yet.
- Three vocabulary families exist with **no writer at all**: the intake-blocked tokens `needs_clarification`/`awaiting_customer_details`/`escalated`, the quote-capable tokens `ready_to_quote`/`quote_ready`/`ready_to_book`, and the terminal tokens `closed`/`lost`/`booked`/`delivered`. `snoozed` (trip status) and `blocked` (trip status) are **frontend/read-model-only** inventions. **[V]**

### 2.5 Live inconsistencies the enum would pin down **[V] unless noted**

1. `active` and `archived` trips fall into **neither** `WORKSPACE_STATUSES` nor `INBOX_STATUSES` (`bff-trip-adapters.ts:59-73`) → they vanish from both views; `active` also renders an undefined state color. 76 SQL + 978 file-store rows are `active` today. **[V]**
2. `metrics.py` booked-revenue reads `status == "booked"` (:315) and `("booked","delivered","completed")` (:191) — **no writer ever sets `booked`**, so booked-revenue metrics are structurally zero except for trips moved via… nothing. Metrics vocabulary and writer vocabulary have drifted apart. **[V]**
3. `contract.py:1451` response default `"IN_PROGRESS"` (uppercase) matches nothing.
4. Seven divergent terminal-status sets across agents (runtime.py ×7 + communicator) — one agent's "terminal" is another agent's "eligible". **[V]**
5. `normalize_trip_status` has **zero callers** outside its own module **[V]** (rg across spine_api/src, non-test) — the alias normalization is currently dead code; unknown statuses are never funneled through it on any write path.
6. PATCH `/trips/{id}` accepts any string as status (only the invariant and the `"completed"` ready-gate constrain it) — the operator can invent `IN PROGRESS`, `Done`, `ready-to-quote` today. **[V]**

---

## 3. Data-Collection Plan (precondition for slice-2)

Goal: prove the vocabulary is closed *in production traffic*, not just the test agency, before Stage-2 rejection flips on.

| Instrument | What to add | Where it lands | Size |
|---|---|---|---|
| **Wire `normalize_trip_status` into TripStore** | Call it in `FileTripStore.save_trip` (:930) and `SQLTripStore` save/update paths before the guard; it already warns on unknowns | Existing `logger.warning` on `spine_api.core.trip_status` | S |
| **Unknown-status counter** | Module-level `Counter` in `trip_status.py` incremented in `normalize_trip_status`'s unknown branch; expose via an internal `/internal/status-vocab` read endpoint (list_trips already accepts `status=` filter, server.py:2032) | In-memory counter + log scrape | S |
| **Extend `trip_status_changed` audit to all writers** | Today only the manual PATCH emits `old_status/new_status/reason` (server.py:2493). Emit the same event (reason=writer name) from the inbox/legacy/agent/inbound write helpers, or fold it into `record_status_transition` | `audit_logs` table (AuditStore) — queryable, tenant-scoped | M |
| **status_history coverage** | Already durable on both stores (file key / `analytics._extra`, persistence.py:73-94) — no change; just let it accumulate | `trips.analytics._extra.status_history` / JSON | 0 |
| **Read-model unknown bucket** | In `trip-lifecycle.ts` derive functions and `bff-trip-adapters.ts` maps: statuses outside the union get `state: "unknown"` + one dev `console.warn` instead of silent fall-through | UI + console; optional count in an ops dashboard | S |
| **Prometheus hook** | `/metrics` is a stub today (server.py:2001-2003) — when it becomes real, add `spine_trip_status_unknown_total{value=…}` | `/metrics` | S (piggyback) |

Decision rule (carried from trip_status.py:18-23): after N weeks of Stage-0 data, if unknown-token count ≈ 0 and the alias map absorbs 100% of what remains, Stage 2 is safe.

## 4. Candidate Enum + Alias Table (draft)

### 4.1 Enum cut options

- **Option A — data-first (9 values):** `new, active, assigned, in_progress, incomplete, needs_followup, completed, cancelled, archived`. Everything with ≥1 writer. Smallest; but makes the frontend workspace filters (`ready_to_quote/ready_to_book/blocked`) inexpressible.
- **Option B — contract-first (12 values, recommended):** exactly the keys of `bff-trip-adapters.ts` STATUS_TO_STATE: `new, incomplete, needs_followup, awaiting_customer_details, snoozed, assigned, in_progress, ready_to_quote, ready_to_book, blocked, completed, cancelled` (+`active` and `archived` — see 4.2). One vocabulary, both sides; the dead-but-defensive sets in `trip_status.py` are subsets.
- **Option C — union-everything (17+):** adds `escalated, quote_ready, closed, lost, booked, delivered, quoted, proposal`. Over-legislated: `escalated` belongs to `TripRoutingState.status`/`review_status`, not trip status; `closed/lost` duplicate `cancelled/completed`; `quoted/proposal` are agent-draft routing, not lifecycle.

### 4.2 Alias table (canonical → absorbed legacy) **[I] for mappings, [V] for the source tokens**

| Canonical | Aliases absorbed | Rationale / evidence |
|---|---|---|
| `new` | `""`, `None`, `missing key` | persistence defaults; file-store 138 missing-key rows |
| `in_progress` | `inprogress`, `IN_PROGRESS`, `in-progress` | contract.py:1451 default + existing `_STATUS_ALIASES` |
| `ready_to_quote` | `quote_ready` | `QUOTE_CAPABLE_STATUSES` holds both (trip_status.py:35) |
| `completed` | `delivered`, `closed` | metrics.py:191 treats them together; terminal sets overlap |
| `active` | — (keep distinct, or alias → `in_progress`; **decision needed**) | inbound writes it as "intake complete, unassigned" — semantically distinct from `in_progress` ("owned, working") |
| `booked` | — (alias → `completed`, or promote to canonical; **decision needed**) | metrics booked-revenue reads it; no writer produces it |
| everything else | pass through + warn (Stage 0), 422/clamp (Stage 2+) | additive-first doctrine |

### 4.3 Read-model reporting of unknowns **[I]**

`trip-lifecycle.ts` gains an explicit `UNKNOWN` lifecycle bucket: `status` not in the union ⇒ `state: "unknown"`, `blockers` unchanged, one `console.warn` in dev, and the count surfaces in the same ops surface as §3 — so a new backend status is *visible in the UI on day one* instead of silently dropping trips from workspace/inbox partitions (the `active`/`archived` bug class, §2.5-1).

## 5. Additive Rollout Stages (each independently rollbackable)

| Stage | Change | Enforcement mode | Rollback |
|---|---|---|---|
| **0 — Instrument** | Wire `normalize_trip_status` into both store write paths; add unknown counter; extend audit event to all writers (§3). Zero behavior change — unknowns still persist | `warn` (current default behavior of the module) | Revert commit; no data migration |
| **1 — Enum-first** | Add `TripStatus` StrEnum + `TRIP_STATUS_ALIASES` in `spine_api/core/trip_status.py` (canonical module, no parallel system); switch all writers (§2.2 table) to enum members; TS union in `api-client.ts` Trip type. Unknown strings still accepted and stored | `warn` | Writers revert to literals; enum stays (additive) |
| **2 — Literal at store boundary** | `TripPatchRequest.status` validated server-side (enum ∪ aliases; unknown ⇒ 422 with allowed-values list — contract-visible, not silent); stores coerce via `normalize_trip_status` then **clamp+log** any residual unknown (data-loss-prevention pattern: never skip the write, preserve the record, log loudly). API responses expose `"IN_PROGRESS"→in_progress` normalized | `strict` at API edge, `clamp` at store | Env flag `TRIP_STATUS_ENFORCEMENT=warn\|strict`; flip back without deploy of new code |
| **3 — Reject unknowns** | DB `CHECK (status IN …)` migration — `ADD CONSTRAINT … NOT VALID` then `VALIDATE CONSTRAINT` (online, additive); align the 7 agent terminal sets to one exported constant; delete `IN_PROGRESS` default in contract.py:1451 | `reject` | Drop constraint (cheap); enum retains aliases so old rows still read |

Ordering rationale: writers before boundary (Stage 1) so the store never rejects its own code; API edge strict before DB constraint (Stage 3) so the constraint never fires on legit traffic. Dual-store note: both `FileTripStore` and `SQLTripStore` get the identical coercion call — no split-brain behavior (the 2026-05-03 lesson).

## 6. What It Unlocks / What It Risks

**Unlocks** **[I, grounded in §2.4-2.5 evidence]**

- `GET /trips?status=` becomes a validated enum parameter (today it passes any string to SQL equality — always zero rows for typos).
- Metrics vocabulary reunifies: booked-revenue either becomes real (if `booked` is canonical/aliased) or is deleted as dead logic — either way the current silent-zero is fixed.
- Workspace/inbox partition bug (active/archived invisibility) becomes impossible to reintroduce: union mismatch is a type error, not a runtime fall-through.
- The 7 agent terminal sets collapse to one constant; adding a terminal status is a one-line diff with compiler/checker enforcement.
- `status_history` + audit events become trustworthy time-series for the E-12 eval corpus (per-status transition fixtures).

### Risks

- **Test-data distortion [V]:** 87% of observed rows are `assigned`, overwhelmingly from bulk-assign test runs (Docs/KNOWN_TEST_DATA_ACCUMULATION.md class). A vocabulary "validated" on this distribution could still miss production states — hence the Stage-0 gate, not skipping it.
- **Operator freeform PATCH breaks at Stage 2:** any external script/habit PATCHing `"In progress"` starts getting 422. Mitigation: aliases + 422 body listing allowed values; flag to `warn` mode.
- **Frontend partition hard-coding [V]:** the enum freezes `WORKSPACE_STATUSES`/`INBOX_STATUSES`; product may want `ready_to_quote` trips in inbox. Enum doesn't decide this — it just makes the decision explicit and reviewable.
- **File-store legacy rows (138 missing status) [V]:** Stage-2 coercion defaults them to `new` — acceptable, but must be called out in the migration note, not discovered in production.

## 7. Concrete Next Tasks

| # | Task | Size | Gate |
|---|---|---|---|
| 1 | Wire `normalize_trip_status` into both store save/update paths + unknown counter + `/internal/status-vocab` | S | none — do now |
| 2 | Add `state: "unknown"` bucket + dev warn in `trip-lifecycle.ts` / `bff-trip-adapters.ts`; fix `active`/`archived` fall-through regardless of enum decision | S | none — live UI bug |
| 3 | Extend `trip_status_changed` audit emission to inbox/legacy/agent writers | M | none |
| 4 | Define `TripStatus` StrEnum + alias table (per Decision 1/2 below) in `spine_api/core/trip_status.py`; switch writers to enum members | M | after Stage-0 window |
| 5 | TS: `Trip['status']` union in `api-client.ts` + regenerate `types/generated/spine-api.ts` | S | with #4 |
| 6 | `TripPatchRequest.status` validation + 422 contract + `TRIP_STATUS_ENFORCEMENT` flag | M | after #4/#5 |
| 7 | DB CHECK constraint migration (NOT VALID → VALIDATE) + align 7 terminal sets to one constant + remove `IN_PROGRESS` default | L | after #6 soak |

## 8. Decisions Needed

- **Decision needed:** enum cut — Option A (9 writer-backed values), **Option B (12 = frontend STATUS_TO_STATE keys — recommended)**, or Option C (17 union incl. routing/draft tokens)?
- **Decision needed:** `active` — keep as canonical enum member (semantically "intake complete, unassigned") or alias → `in_progress`? 1,054 live rows across both stores depend on this.
- **Decision needed:** `booked` — promote to canonical (fixes booked-revenue metrics for real) or alias → `completed` (and delete the metric)?
- **Decision needed:** Stage-2 unknown policy — 422 at the API edge with `clamp+log` inside the store (recommended: contract-visible outside, never data-loss inside), or clamp everywhere?
- **Decision needed:** how long the Stage-0 `warn`-only window runs before strictness flips (proposal: 2 weeks of staging traffic + one prod deploy cycle).

---

*Exploration only — no code, schema, or config was modified. Distribution figures from read-only RLS-scoped SQL against `waypoint_os` (2026-09-04) and read-only scans of `data/trips/`.*
