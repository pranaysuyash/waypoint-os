# Review Packet: Drafts System Phase 0

**Project:** Waypoint OS — travel_agency_agent  
**Date:** 2026-04-29  
**Scope:** Backend draft persistence (Phase 0 only) + auto-tab-switch fix  
**Reviewer:** ChatGPT / Claude / Codex  

---

## Context in 2 Minutes

The Workbench is the pre-trip workspace where agents paste customer messages, pick scenarios, and click "Process Trip" to run an AI pipeline. Today the Workbench is **ephemeral** — everything lives in browser memory. If a run ends in `blocked` (validation errors) or `failed`, the errors render in the `Trip Details` tab but the user stays wherever they were. Poor UX.

The user wants to fix this AND make the Workbench **persistent** via a `Draft` entity that survives refresh, links to runs, and eventually supports merging/linking between agents.

**Existing persistence patterns:**
- File-based JSON: `FileTripStore`, `RunLedger`, `AuditStore` — all one-JSON-file-per-entity with `file_lock()` concurrency
- PostgreSQL: `SQLTripStore`, `Trip` SQLAlchemy model — optional via env var, used in production path

---

## Files to Review (in order)

### 1. `Docs/DRAFTS_SYSTEM_ARCHITECTURE_PLAN_2026-04-29.md`
**The main architecture document. Read this first.**

Key sections:
- Section 3: Storage Medium Decision — **Contains a corrected ADR note** resolving a contradiction between JSON-only and hybrid SQL+JSONB
- Section 7: Data Model — Shows both long-term SQL schema and Phase 0 file representation
- Section 9: Audit Integration — Append-only events, never destroy draft-era events
- Section 11: Implementation Phases — What I'm building now (Phase 0 backend only)

### 2. `spine_api/draft_store.py` (NEW — my implementation)
**What to check:**
- Is the `Draft` model future-proof? Does it include all fields needed for SQL migration?
- Is `FileDraftStore` atomic-write safe? (temp file + rename, file_lock)
- Is the index rebuildable from files? (corruption recovery)
- Is the `DraftStore` facade clean enough to swap in `SQLDraftStore` later?
- Is `patch()` with `expected_version` correct for optimistic concurrency?
- Any missing methods that Phase 0 needs?

### 3. `spine_api/contract.py` (MODIFIED)
**Change:** Added `draft_id: Optional[str] = None` to `SpineRunRequest`.

**What to check:**
- Is this the right place? Any downstream impact?
- Does `model_config = {"extra": "forbid"}` still work with the new field?

### 4. `spine_api/server.py` (EXISTING — context only)
**Key areas:**
- `POST /run` (line ~1011): Where runs are created. Currently `trip_id=None`. Should this also store `draft_id` in `RunLedger.create()`?
- `_execute_spine_pipeline` (line ~705): Where run lifecycle happens. Where should draft status updates be wired? At `RunLedger.set_state()` calls? At completion?

### 5. `spine_api/persistence.py` (EXISTING — context)
**What to check:**
- `file_lock()` — is it sufficient for draft file concurrency?
- `FileTripStore` — any patterns I should have copied but didn't?
- PII guard — should `DraftStore` call `check_trip_data()` too?

### 6. `spine_api/models/trips.py` (EXISTING — SQL comparison)
**Shows how the existing `Trip` SQLAlchemy model is structured.**

### 7. `frontend/src/app/workbench/page.tsx` (MODIFIED)
**Change:** Added auto-tab-switch `useEffect` when run ends in `blocked`/`failed`.

**What to check:**
- Does the `useEffect` have the right guards? Could it fight user manual tab changes?
- Is `prevRunStateRef` the right pattern for transition detection under polling?
- Any edge cases with hydration/refresh?

---

## Specific Questions

### Architecture

1. **Draft model completeness:** The `Draft` model (in `draft_store.py`) includes identity, metadata, customer hashes, run tracking, promotion, lifecycle, payload, and linking cache. Are there fields missing that would force a schema change when we migrate to SQL?

2. **Storage abstraction quality:** `DraftStore` is a static facade that delegates to `FileDraftStore._backend`. When we later create `SQLDraftStore`, will the interface hold? Specifically:
   - `save()` returns a `Draft` object — SQL backend would do UPDATE then SELECT
   - `patch()` does partial update with optimistic concurrency — SQL backend would need `UPDATE ... WHERE version=$v`
   - `list_by_agency()` returns `list[Draft]` — SQL backend would do `SELECT * FROM drafts WHERE agency_id=$1`

3. **Index strategy:** The `index.json` is rebuildable from files. Is this over-engineered? Should I skip the index and just glob `data/drafts/*.json` on every `list_by_agency()` call? (Current code: load index, filter by agency. Without index: glob all files, filter in memory.)

### Code

4. **Auto-tab-switch edge cases:** In `page.tsx`, the `useEffect` switches tab when `spineRunState` transitions to `blocked`/`failed`. Could this override a user's manual tab choice? The code compares `prevRunStateRef.current` to detect transitions, but `spineRunState` is updated by polling. If the user manually switched tabs after the run blocked, then a new poll arrives with the same `blocked` state — the effect should be a no-op because `currentState === prevState`. Is this reasoning correct?

5. **file_lock contention:** `FileDraftStore` uses `file_lock()` with 10-second timeout on every write. If auto-save fires every 5 seconds while the user is typing, and a write takes 500ms, is there risk of lock queue buildup? Should I use a different concurrency approach (e.g., in-memory queue with single writer thread)?

### Integration

6. **Run lifecycle wiring:** Where in `_execute_spine_pipeline` should I call `DraftStore.update_run_state()`? My thinking:
   - After `RunLedger.set_state(run_id, RunState.RUNNING)` → update draft status to `processing`
   - After `RunLedger.block()` → update draft status to `blocked`
   - After `RunLedger.fail()` → update draft status to `failed`
   - After `RunLedger.complete()` → update draft status to `open` (not promoted yet — promotion is a separate explicit step)
   - Is this too invasive for Phase 0? Should I defer run-draft wiring to Phase 1?

7. **AuditStore integration:** Should `draft_store.py` directly call `AuditStore.log_event()`, or should the API layer (`server.py`) do the logging? The `FileDraftStore` currently has no AuditStore dependency. Should I keep it that way?

---

## What I Haven't Built Yet (Intentionally Deferred)

- API endpoints (`POST /api/drafts`, `GET /api/drafts`, etc.) — next after model/store review
- Frontend draft store extensions — Phase 1
- Auto-save hook — Phase 1
- Drafts list page/sidebar — Phase 2
- Timeline integration (promotion-time link event) — Phase 3
- Merge/link UI — Phase 4

---

## Deliverable Expected from Reviewer

Please answer the 7 questions above. Flag any **blocking concern** that should stop Phase 0 implementation. Suggest any **significant simplification** that reduces scope without breaking future SQL migration.

---

*End of packet.*
