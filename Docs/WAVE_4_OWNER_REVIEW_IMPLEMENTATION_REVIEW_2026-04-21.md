# Wave 4 Owner Review Workflows — Implementation Review

**Date:** 2026-04-21  
**Reviewer:** GitHub Copilot (GPT-5.3-Codex)  
**Scope:** Evidence-based review of Wave 4 owner review workflow implementation against locked Hybrid Policy B

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

---

## Executive Verdict

**Overall:** **PASS WITH NOTES** (after targeted fixes)

Initial review found 3 blockers and 2 partial-compliance gaps. All were remediated and re-verified in-session.

---

## Deliverable Verdict Matrix

| Deliverable | Verdict | Notes |
|---|---|---|
| `spine-api/server.py` review endpoints | PASS | Endpoints present and wired: `GET /analytics/reviews`, `POST /trips/{trip_id}/review/action` |
| `frontend/src/app/api/reviews/route.ts` | PASS | BFF proxy correctly targets backend reviews endpoint |
| `frontend/src/app/api/reviews/action/route.ts` | PASS | BFF action proxy correctly maps `reassignTo -> reassign_to` |
| `src/analytics/review.py` | FAIL → FIXED | `request_changes` status normalization incorrect (`request_changes` vs required `revision_needed`) |
| `frontend/src/app/owner/reviews/page.tsx` | PARTIAL → FIXED | Dead `MOCK_REVIEWS` remained; `revision_needed` badge missing |
| `tests/test_review_logic.py` | FAIL → FIXED | 3/3 failing due to fixture setup + wrong monkeypatch target + status assertion mismatch |

---

## Findings and Root Causes

### 1) Hybrid B status mismatch in review state machine

- **Spec requirement:** `request_changes` action must persist `analytics.review_status = "revision_needed"`
- **Observed pre-fix:** `ACTION_MAP["request_changes"] = "request_changes"`
- **Impact:** Semantic divergence from locked policy; frontend/type contract drift risk

### 2) Broken test setup pattern in `tests/test_review_logic.py`

- **Observed pre-fix:** tests used `TripStore.update_trip(...)` to create new trips
- **Actual store behavior:** `update_trip` only updates existing trips; returns `None` if file absent
- **Impact:** `process_review_action` raised `KeyError` because trip fixture was never created

### 3) Wrong monkeypatch target for audit file

- **Observed pre-fix:** patched `persistence.AUDIT_FILE`
- **Actual implementation:** audit path lives at `persistence.AuditStore.AUDIT_FILE`
- **Impact:** `AttributeError` in audit delta test

### 4) UI/status drift

- **Observed pre-fix:** owner review page still contained hardcoded `MOCK_REVIEWS`; no `revision_needed` badge style
- **Impact:** stale code path confusion + incomplete status visualization for policy-compliant state

---

## Remediations Applied

### Backend / logic

- Updated `src/analytics/review.py`:
  - `VALID_ACTIONS` now includes `revision_needed`
  - `ACTION_MAP["request_changes"] = "revision_needed"`
  - policy branch now checks `normalised == "revision_needed"`

### Tests

- Updated `tests/test_review_logic.py`:
  - fixture creation now writes trip JSON files directly into temp `trips/` dir
  - audit monkeypatch now targets `persistence.AuditStore.AUDIT_FILE`
  - request-changes assertion now expects `revision_needed`

### Frontend types + UI

- Updated `frontend/src/types/governance.ts`:
  - `ReviewStatus` now includes `'revision_needed'`

- Updated `frontend/src/app/owner/reviews/page.tsx`:
  - removed stale `MOCK_REVIEWS`
  - added `revision_needed` style + icon handling in `StatusBadge`

---

## Verification Evidence

All checks executed after fixes:

1. Focused Wave 4 review tests
   - Command: `PYTHONPATH=spine-api uv run pytest tests/test_review_logic.py -v`
   - Result: **3 passed**

2. Full backend suite
   - Command: `uv run pytest tests/ -q`
   - Result: **476 passed, 13 skipped**

3. Frontend type-check
   - Command: `npx tsc --noEmit` (from `frontend/`)
   - Result: **passed** (no output)

4. Frontend tests
   - Command: `npm test -- --run` (from `frontend/`)
   - Result: **97 passed**

---

## Implementer Handoff Notes

Wave 4 owner review workflows are now aligned with Hybrid Policy B and are test-verified.

If extending this workflow next, preserve these invariants:

1. `request_changes` must always normalize to `revision_needed`
2. Review action tests must create explicit trip fixtures (do not rely on `update_trip` for creation)
3. Audit tests must patch `AuditStore.AUDIT_FILE` (class attribute)
4. Frontend `ReviewStatus` union and status badges must remain in sync with backend status vocabulary

---

## Final Acceptance

**Wave 4 status:** **Accepted (PASS WITH NOTES, all notes resolved in this patch set).**
