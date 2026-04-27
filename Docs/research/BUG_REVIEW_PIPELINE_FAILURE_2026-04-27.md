# Bug Review: Pipeline Fails on Real-World Input — Extraction + Error Handling

**Date**: 2026-04-27
**Severity**: P0 — app is non-functional for any real input
**Status**: Unfixed
**Review requested for**: Root cause analysis and fix approach

---

## What Happens

User submits a real travel inquiry through the Workbench UI. The progress panel appears briefly, then disappears. No trip is created. The run hangs in `state: "running"` forever.

**Input used**:
```
Hi Ravi, I got your number from my wife who is a colleague of Divya.
We are planning to visit Singapore sometime in Jan or Feb 2025.
Tentative dates around 9th to 14th Feb, approx 5 days.
Me, my wife, our 1.7 year old kid, and my parents would be going.
We don't want it rushed. Interested in Universal Studios and nature parks.
```

---

## Root Cause Chain (2 bugs, 1 systemic issue)

### Bug 1: Regex extraction produces garbage → validation escalates → pipeline stops

**What happens**: The extraction pipeline is purely regex-based (no LLM). The regex patterns fail on this input and extract nonsense.

**Evidence from the run** (run `55c98736-bddc-4588-9b61-8a1f4c7b474f`):

| Field | Expected | Actually Extracted |
|-------|----------|--------------------|
| `destination_candidates` | `["Singapore"]` | `["Nov", "Caller", "Pace"]` |
| `origin_city` | any value | MISSING |
| `date_window` | `"9th to 14th Feb"` | MISSING |
| `budget_raw_text` | (absent) | MISSING |
| `trip_purpose` | `"leisure"` | MISSING |
| `hard_constraints` | `["not rushed"]` | `["it rushed"]` |

4 of 6 required MVB fields are MISSING → validation fails → NB01 gate escalates.

**Why the regex fails**:
1. **Destination regex** (`_extract_destination_candidates`): The "or" pattern (`r"\b([A-Z][a-z]+...)\s+(?:or|and)\s+([A-Z][a-z]+)...`) matches the FIRST two capitalized words connected by "or" — which happens to be `"Jan or Feb"` from the date sentence. It never reaches the general destination regex that would check `is_known_destination("Singapore")`.
2. **Origin city**: No regex pattern exists to extract origin city from agent-style notes.
3. **Date window**: The date regex handles `Month-Month YYYY` and `Month YYYY` but not `"9th to 14th Feb"` (day range without year).
4. **Negation**: `"not rushed"` is captured as `"it rushed"` because the constraint regex captures a word window around "rushed" without understanding negation.

### Bug 2: Pipeline early-exit not handled by caller → run hangs forever

**What happens**: When NB01 escalates, `run_spine_once()` returns a normal `SpineResult` (via `_create_empty_spine_result`). The caller `_execute_spine_pipeline()` treats this as a successful completion and tries to call `save_processed_trip()` with the empty result. This call appears to hang (process sits at 0% CPU indefinitely), and the run is NEVER marked as `completed`, `failed`, or `blocked`.

**Evidence**: Run `55c98736` has been in `state: "running"` for 7+ minutes. The multiprocessing child process (PID 68476) is alive at 0% CPU — stuck, not doing work.

**Why**: `SpineResult` has no `early_exit` or `escalated` flag. The caller has no way to distinguish a normal completion from an NB01 escalation.

### Bug 3 (Frontend): Progress panel disappears on timeout

**What happens**: `useSpineRun` polls every 2s with a 180s max. Since the run never reaches a terminal state (Bug 2), polling times out at 180s. The hook throws `RUN_TIMEOUT`, sets `error` and `isLoading = false`. The panel condition `isSpineRunning && spineRunState && spineRunId` becomes false, and the panel unmounts. The user sees the panel disappear with no explanation.

**Also**: Even if the run completed successfully, `handleProcessTrip` immediately calls `router.push()` on getting a `trip_id`, navigating away before the user sees the completion state.

---

## Files Involved

### Backend — Extraction (Root Cause)

**`src/intake/extractors.py`** (1352 lines)
- Line 119-208: `_extract_destination_candidates()` — The "or" regex pattern at line 136-148 matches `"Jan or Feb"` before the general destination regex at line 183 ever runs. Singapore is never checked.
- Line 760-812: `ExtractionPipeline` class — Pattern-based extraction only. `model_client=None` parameter is a dead hook (line 771), never used.
- Line 831-879: `_extract_from_freeform()` — Calls regex functions for each field. No NLP/LLM fallback.

### Backend — Validation (Gate that catches the bad extraction)

**`src/intake/validation.py`** (232 lines)
- Line 46-53: `DISCOVERY_MVB` — 6 required fields: `destination_candidates`, `origin_city`, `date_window`, `party_size`, `budget_raw_text`, `trip_purpose`
- Line 86-100: `validate_packet()` — Checks each MVB field exists in `packet.facts`. Any missing → error.

### Backend — Orchestration (Early exit not signaled to caller)

**`src/intake/orchestration.py`** (647 lines)
- Line 128-212: `run_spine_once()` — At line 191-212, NB01 escalation returns `_create_empty_spine_result()` which is a normal `SpineResult`. **No flag** tells the caller this was an early exit.
- Line 371-408: `_create_empty_spine_result()` — Returns a valid `SpineResult` with empty strategy/bundles. Indistinguishable from a real result.

### Backend — Server (Caller that hangs)

**`spine_api/server.py`** (1984 lines)
- Line 523-678: `_execute_spine_pipeline()` — At line 571, calls `run_spine_once()`. Then at line 594, calls `save_processed_trip()` with the result. When the result is from an NB01 escalation, `save_processed_trip()` appears to hang (no timeout, no error handling for this case).
- Line 639-678: Exception handlers catch `ValueError` (leakage) and generic `Exception`, but NB01 escalation returns NORMALLY (no exception thrown), so these handlers are never reached.

### Frontend — Polling + UI

**`frontend/src/hooks/useSpineRun.ts`** (114 lines)
- Line 22: `MAX_WAIT_MS = 180_000` — 3-minute timeout. If run never reaches terminal state, throws `RUN_TIMEOUT`.
- Line 72-86: Terminal state check — Only `["completed", "failed", "blocked"]` are terminal. If run stays in `"running"` forever, polling times out.

**`frontend/src/app/workbench/page.tsx`** (502 lines)
- Line 216-222: `handleProcessTrip` — On completion, immediately redirects to `/workspace/${trip_id}/intake`. Panel unmounts before user sees anything.
- Line 376-385: `RunProgressPanel` only rendered when `isSpineRunning && spineRunState && spineRunId`. When `isLoading` flips to false (timeout or completion), panel disappears.

---

## Suggested Fix Approach

### Fix 1 (Backend — Immediate): Signal early exit in SpineResult

In `src/intake/orchestration.py`:
- Add `early_exit: bool = False` and `early_exit_reason: Optional[str] = None` to `SpineResult` dataclass
- Set `early_exit=True` in `_create_empty_spine_result()`

In `spine_api/server.py`:
- After `run_spine_once()` returns, check `result.early_exit`
- If True: call `RunLedger.block(run_id, block_reason=...)` + `emit_run_blocked()` and return immediately — do NOT call `save_processed_trip()`

### Fix 2 (Backend — Root cause): Improve regex patterns

In `src/intake/extractors.py`:
- Fix `_extract_destination_candidates`: Check `is_known_destination()` for "or" pattern matches before returning them as candidates. If neither is a known destination, fall through to the general regex.
- Add date extraction for `"9th to 14th Feb"` day-range patterns.
- Add origin city extraction pattern.
- Fix negation handling in constraint extraction.

### Fix 3 (Frontend): Don't redirect immediately, don't hide progress on timeout

In `frontend/src/app/workbench/page.tsx`:
- Replace `router.push()` with `setCompletedTripId(result.trip_id)` 
- Show "View Trip →" button that navigates on explicit click
- Show progress panel even after timeout (with error state visible)

---

## Architecture Context

The extraction pipeline was designed as a 3-step hybrid system:
1. **Step 1**: Regex extraction (current — the only thing implemented)
2. **Step 2**: NER/LLM semantic candidate extraction (designed but not built)
3. **Step 3**: Reconciler to merge results (designed but not built)

This is documented in `Docs/PHASE_B_MERGE_CONTRACT_2026-04-15.md`. The `model_client` parameter in `ExtractionPipeline` is the dead hook intended for Step 2.

The immediate fix (Fix 1 + Fix 2) makes the existing regex pipeline work well enough to pass NB01 on real inputs. The full fix (Step 2 + Step 3) requires LLM integration, which is a larger effort tracked in `Docs/research/EXTRACTION_MULTI_TIER_ARCHITECTURE_2026-04-27.md`.
