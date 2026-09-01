# DEMO-01 — Lead Routing Gap: Blocked Drafts Never Reach the Lead Inbox

*Date: 2026-08-31*
*Source: EX-DEMO-01 (covers DEMO-01 + DEMO-09 banner specificity), from `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md`.*
*Method: read-only code trace (backend `spine_api/`, pipeline `src/intake/`, frontend `frontend/src/`) + live GET verification of `:8000/openapi.json`. No product code, tests, fixtures, or DB touched.*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## 1. Executive Summary

- The Lead Inbox has **no "Lead" entity** — it is a projected read model over **Trips** whose status is one of `new, incomplete, needs_followup, awaiting_customer_details, snoozed` (`spine_api/routers/inbox.py:38,66-70`).
- When the NB01 intake gate returns **ESCALATE** (intake minimum missing), the pipeline takes the `early_exit` branch: it writes `blocked_result` to the run ledger and updates the **draft** to `status="blocked"` — then **returns without ever calling `save_processed_trip`** (`spine_api/services/pipeline_execution_service.py:279-302`). No trip is created, so the inbox query returns 0 rows. **Root cause is (a): blocked drafts are never promoted to leads.**
- The banner's promise actually *does* hold for the gentler DEGRADE path (intake minimum met, quote-ready fields missing): that branch saves a trip with `status="incomplete"`, which lands in the inbox (`pipeline_execution_service.py:304-350`, esp. `:338`). The demo note failed the harder way because extraction missed the date window (`date_window` is part of `INTAKE_MINIMUM`, `src/intake/validation.py:46-49`) — so it ESCALATED and dead-ended.
- **Recommendation: Option A** — extend the canonical pipeline so ESCALATE runs also persist a trip (`status="incomplete"`) into the inbox, rather than editing the banner to stop promising what the product should do. The seam already exists: the DEGRADE branch shows exactly how, and `_update_draft_for_terminal_state()` already receives a `trip_id` parameter it explicitly discards (`pipeline_execution_service.py:29`). No new routes needed.
- Secondary (DEMO-09): the blocked banner's copy builder (`frontend/src/lib/workbench-blocking-copy.ts`) already receives the validation report; the missing-field *names* are already client-side (rendered in `PacketTab.tsx:126,156`), so adding "Missing: Travel Dates, Trip Purpose" to the banner is a small, low-risk change — do it in the same pass.

---

## 2. Root Cause (evidence chain)

### 2.1 What the Lead Inbox actually queries

| Layer | Evidence |
|---|---|
| Backend canonical inbox endpoint | `GET /inbox` → `TripStore.list_trip_summaries(status=_INBOX_STATUSES, agency_id=...)` where `_INBOX_STATUSES = "new,incomplete,needs_followup,awaiting_customer_details,snoozed"` — `spine_api/routers/inbox.py:41-86` (statuses at `:38`, query at `:66-70`). |
| Frontend read | `/inbox` page → `useInboxTrips` (`frontend/src/hooks/useGovernance.ts:305-317`) → `getInboxTrips` → `api.get('/api/inbox?...')` (`frontend/src/lib/governance-api.ts:226`). |
| "0 leads total" string | `leadCountLabel()` renders `total` from the inbox envelope — `frontend/src/app/(agency)/inbox/PageClient.tsx:35-37`. |
| "No new leads" empty state | `frontend/src/components/inbox/InboxEmptyState.tsx:30,40`. |

**Conclusion:** a "lead" is any Trip in one of the five inbox statuses. There is no separate lead table/entity and no second feed.

### 2.2 What happens after `blocked_result`

Pipeline trace for the demo run (`draft_22c74baae1d8`, run `de9c10ef`, stages `packet → validation → decision → strategy → blocked_result`):

1. NB01 gate: `NB01CompletionGate` returns **ESCALATE** when structural validation fails or `INTAKE_MINIMUM` is not met; **DEGRADE** when intake minimum is met but `QUOTE_READY` fields are incomplete (`src/intake/gates.py:101-153`, verdict docs at `:106-111`).
   - `INTAKE_MINIMUM = ["destination_candidates", "date_window"]` (`src/intake/validation.py:45-49`).
   - The demo note lost `date_window` ("next spring, late march" never extracted) and `trip_purpose` → intake minimum failed → **ESCALATE**.
2. ESCALATE builds a result with `early_exit=True` (`src/intake/orchestration.py:325`, helper `_create_empty_spine_result` sets `early_exit=True` at `:722`).
3. In `pipeline_execution_service.py`, the `early_exit` branch (`:279-302`) does exactly three durable things and returns:
   - `run_ledger.save_step(run_id, "blocked_result", ...)` (`:286`) and `run_ledger.block(...)` (`:294`);
   - `_update_draft_for_terminal_state(run_id, "blocked", ...)` (`:295`) — which only calls `DraftStore.update_run_state(...)`, setting the **draft** `status="blocked"` (`pipeline_execution_service.py:15-47`; `spine_api/draft_store.py:407-416`, specifically `:412-413`);
   - `emit_run_blocked_fn(...)` (`:296-301`) — telemetry.
   - **`save_processed_trip` is never called on this path.** No Trip row exists for the run.
4. Contrast — the two paths that DO create inbox-visible trips:
   - **DEGRADE / `partial_intake`** branch: `save_processed_trip(..., trip_status=existing_trip_status or "incomplete", preserve_trip_id=target_trip_id)` (`pipeline_execution_service.py:304-350`, status at `:338`). `"incomplete"` is an inbox status → lands in Lead Inbox.
   - **Full success**: `save_processed_trip(..., trip_status=existing_trip_status or "new", ...)` (`:411-412`). `"new"` is an inbox status → lands in Lead Inbox.

### 2.3 The blocked draft has no recovery surface

- `Draft.status` supports `open | processing | blocked | failed | promoted | merged | discarded` (`spine_api/draft_store.py:69`), but **no UI lists drafts**: the client wrapper `listDrafts` exists (`frontend/src/lib/api-client.ts:1140`) yet no component calls it (repo-wide `rg listDrafts` outside api-client/tests: zero hits). The blocked draft is visible only as the status chip inside the currently-open workbench session (`frontend/src/app/(agency)/workbench/PageClient.tsx:1051`).
- The existing `POST /api/drafts/{draft_id}/promote` endpoint **cannot** rescue a blocked draft: it requires a caller-supplied `trip_id` of an already-saved trip and only flips the draft flag (`spine_api/routers/drafts.py:263-282`; `DraftStore.promote` at `spine_api/draft_store.py`).

### 2.4 Verdict on the three hypotheses

- **(a) Drafts with BLOCKED status never get promoted to leads — CONFIRMED.** The ESCALATE path terminates at draft-level state; no trip is created (`pipeline_execution_service.py:279-302`).
- (b) Leads are created but filtered out of the inbox default view — REJECTED. The inbox query includes `incomplete`/`new` and `filterCounts` are computed over the full projected dataset (`spine_api/routers/inbox.py:37-38,60-64`); the problem is upstream (no row).
- (c) Something else — partial nuance: the banner copy is *accidentally true* for DEGRADE outcomes and *false* only for ESCALATE outcomes. The demo note happened to ESCALATE because `date_window` was missed (DEMO-02 extraction gap is a direct co-factor: fix the extraction and the same note DEGRADES into a visible lead).

---

## 3. Fix Options

### Option A — Promote blocked drafts into the Lead Inbox (fix the behavior)

**A1 (recommended): persist a trip on ESCALATE, reusing the canonical pipeline.**
In the `early_exit` branch of `spine_api/services/pipeline_execution_service.py` (after `:294`), call `save_processed_trip(...)` exactly as the `partial_intake` branch does (`:313-341`), with `trip_status=existing_trip_status or "incomplete"` and `preserve_trip_id=target_trip_id`. Pass the returned `trip_id` into `_update_draft_for_terminal_state(..., trip_id=trip_id_saved)` — the parameter already exists and is currently discarded with `_ = trip_id` (`:29`). Optionally mark the draft `promoted` instead of `blocked`, or keep `blocked` + `promoted_trip_id` for repair-loop semantics (decision needed, §8).

- State mapping: ESCALATE trip → `status="incomplete"` (existing inbox status, no enum change; the inbox already surfaces an "incomplete" flag and a `missingTripBasics` stat for rows with unknown destination/date — `spine_api/routers/inbox.py:161-164,169-172`). Lead label in UI: the existing TripCard rendering applies unchanged.
- **Pros:** matches the banner promise and the product reality (an incomplete first inquiry is exactly the lead an agency must not lose); reuses the canonical save path — no new route, no parallel read model (no-duplicate-routes rule); the inbox projection already handles missing basics; small blast radius (one branch + one function's ignored parameter + tests).
- **Cons / tradeoffs:** deliberately contradicts the current design comment "Fields that MUST be present to even save an intake trip" (`src/intake/validation.py:45`) — today ESCALATE is a *don't-save-garbage* stance. Saving date-less/destination-less trips increases inbox noise if extraction degrades badly; mitigations exist (the `incomplete` flag + urgency sort) but this is a product posture change that Pranay should ratify (§8, Q1). Also needs an idempotency check on reprocess (see §8, Q3).

**A2 (rejected): make the inbox read blocked drafts directly.** Would fork the inbox read model across two stores (TripStore + DraftStore), duplicating projection/sort/filter logic. Violates single-read-model and no-parallel-systems rules.

### Option B — Change the banner copy (fix the promise)

Rewrite `frontend/src/app/(agency)/workbench/PageClient.tsx:964` to something like "After processing: requests missing only optional details appear in Lead Inbox · blocked requests stay in your workbench until completed · quotes needing approval appear in Quote Review", and align `InboxEmptyState.tsx:40` description.

- **Pros:** trivial (1–2 strings + a state gate); zero backend risk; honest for today's behavior.
- **Cons / tradeoffs:** it doesn't fix the dead-end — it relocates the broken promise. "Stays in your workbench" is only true within the current session because **no drafts list exists** (§2.3): navigate away and the blocked draft is unreachable from any nav surface. The first-run loop still ends in "Blocked" + nothing anywhere. This was the exact failure the persona demo punished (`SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` §6, fix 1).

---

## 4. Recommendation

**Option A (A1), shipped together with the DEMO-09 banner specificity change and a small copy touch-up.**

Reasoning: the banner promise is the *correct* product behavior — an agency's highest-value moment is a new inquiry that needs a human follow-up; silently dropping it contradicts the product's own claim and the DEGRADE precedent (the pipeline already trusts itself to save a trip missing `trip_purpose`, `party_size`, `budget`; extending that trust to a date-less trip is a policy call, not an engineering leap). Option B leaves the core loop dead-ended and would still require new copy explaining a destination ("workbench") that has no listing UI. Implementation order: (1) A1 backend branch + draft linkage + pytest; (2) banner missing-fields line (DEMO-09); (3) copy sweep only where wording is now stale.

---

## 5. Banner-Specificity Note (DEMO-09)

Today the blocked banner renders generic reasons only: `getWorkbenchBlockCopy()` humanizes `validation.reasons` / `runState.block_reason` (`frontend/src/lib/workbench-blocking-copy.ts` — `collectReasons` + `humanizeReason`; the literal "Trip details are incomplete" mapping mirrors backend `_BLOCK_COPY` at `src/intake/orchestration.py:649`). The per-field names ("Travel Dates, Trip Purpose") are already in the client — `PacketTab.tsx` renders them from the packet's unknown fields (`:126`, `:156` — capped at 3 with a "+N more" affordance at `:127`).

**Change:** in the banner block (`frontend/src/app/(agency)/workbench/PageClient.tsx:968-998`), append a line built from the same packet unknown-fields source the PacketTab uses, e.g. `Missing: Travel Dates, Trip Purpose`, before the existing "Open the Trip Details repair surface…" sentence (`:995-997`). Data is already loaded; no new API call. Cap at 3 fields + overflow count to match PacketTab behavior.

---

## 6. Test Plan

**Contract baseline (do first):** `curl -s http://localhost:8000/openapi.json | python3 -m json.tool | head` — `/inbox` and `/api/drafts/...` shapes per §2.1/§2.3. Never write to the DB; `TRIPSTORE_BACKEND=sql` stays in `.env`.

**Backend (pytest):**
1. Unit: ESCALATE run persists a trip with `status="incomplete"` and links `draft.promoted_trip_id`/`trip_id`; draft reaches `blocked` (or promoted, per §8 Q2) — `tests/` covering `pipeline_execution_service` early_exit branch.
2. Regression: PROCEED still saves `"new"`; DEGRADE still saves `"incomplete"`; hard-failure (`failed`) path still saves nothing (`pipeline_execution_service.py:466-499`).
3. Reprocess idempotency: re-running the same draft after field repair updates the existing trip (`preserve_trip_id=target_trip_id` at `:339/:412`), never duplicates.
4. Inbox contract: after ESCALATE, `GET /inbox` `total` increments and `filterCounts` include the item; `GET /inbox/stats` `incomplete`/`missingTripBasics` counts reflect it.

**E2E (fresh tenant → process → blocked → inbox shows lead):**
1. Sign up a brand-new tenant; open `/workbench`; paste a note missing dates + purpose (the demo input is a good fixture candidate).
2. Click Process → run trace ends in `blocked_result`; banner shows "Missing: Travel Dates, Trip Purpose".
3. Navigate to `/inbox` → expect ≥1 lead ("1 lead total"), rendered via TripCard with incomplete flag; not the "No new leads" empty state (`InboxEmptyState.tsx:30`).
4. Verify the Overview inbox-stats card reflects the new lead; verify no stranger-profile rendering (out of scope here — DEMO-04).
5. Screenshot evidence at each step; view screenshots before claiming pass (strict visual E2E standard).

---

## 7. Effort Estimate

| Item | Effort |
|---|---|
| A1 backend branch (save on ESCALATE + draft linkage + tests) | 0.5–1 day |
| DEMO-09 banner specificity (copy + tests) | 2–4 h |
| Copy sweep (only stale wording left after A1) | 1–2 h |
| Option B alone (for comparison) | 1–2 h, but leaves the loop broken |
| Full A + DEMO-09 + E2E evidence | ~1–1.5 days |

Risk class: touches lead lifecycle → 2 review cycles per the schema/contract-change rule; contract-driven E2E evidence required (Evidence-Tier 3).

---

## 8. Open Questions for Pranay

1. **Product posture:** should ESCALATE-grade (missing `destination_candidates` or `date_window`) inquiries be saved as inbox leads, overriding the "must be present to even save" stance (`src/intake/validation.py:45`)? Alternatives: save all ESCALATE leads; or save only when ≥1 of the two minimum fields exists (partial-ESCALATE).
2. **Status/label mapping:** reuse existing `incomplete` status (zero schema change), or introduce a distinct blocked-derived label so agents can distinguish "missing optional details" from "blocked on basics"?
3. **Draft↔trip linkage:** on ESCALATE, mark draft `promoted` (terminal) vs keep `blocked` + record `promoted_trip_id` so the workbench repair flow keeps mutating the draft and re-syncs the trip? (Reprocess idempotency depends on this — `preserve_trip_id` mechanics at `pipeline_execution_service.py:339,412`.)
4. **Inbox noise guard:** if A1 lands, do we need a visibility rule (e.g., ESCALATE leads default-filtered into an "Needs basics" tab) so a burst of low-signal extractions doesn't bury good leads?
5. **Copy:** once A1 is live, keep the current banner line verbatim (it becomes true), or tighten it to name the blocked-lead behavior explicitly?
6. **Register:** confirm proposed finding IDs (F-19 for DEMO-01, banner item folding into the DEMO-06/09 cluster) before integration into `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`.

---

*Explore-only deliverable per EX-DEMO-01. No product code, tests, fixtures, or database state were modified. All file references verified against the working tree on 2026-08-31.*
