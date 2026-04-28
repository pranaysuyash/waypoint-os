# Waypoint OS — Issue Review: Ravi/Pranay Singapore Trip Live Test
**Date:** 2026-04-28
**Test Type:** Real-world phone call scenario — End-to-end pipeline test
**Test Participants:** Ravi (agent), Pranay (customer)
**Document Status:** Internal review, frank and evidence-first

---

## 1. Executive Summary

We subjected the Waypoint OS intake pipeline to a real-world phone call scenario: a family of 5 (2 adults + 1 toddler + 2 elderly parents) inquiring about a Singapore trip for Jan/Feb 2025. The pipeline failed catastrophically at its core job — extracting and preserving basic trip facts from customer input. Of the 12 issues identified, one (P0) is an architectural data destruction bug that makes the entire extraction pipeline unreliable. The remaining issues span fragile regex heuristics, broken analytics, UX papercuts, and missing product fundamentals like date inference and trip summaries. **This app is not ready for operator-facing use until the P0 pipeline merge bug is fixed and verified.**

**Verdict at a glance:**
- Pipeline data integrity: **FAILED** — data is silently destroyed
- Extraction accuracy: **FAILED** — destination and dates lost
- Analytics truthfulness: **FAILED** — hardcoded fiction
- UX robustness: **PARTIAL** — some fixes applied but unverified
- Product completeness: **INCOMPLETE** — missing summary view, date context

---

## 2. Issues Found

### ISSUE-01 — Pipeline Extraction Destroys Data (CRITICAL)
**Severity:** P0 | **Status:** Partially fixed, needs verification | **Component:** Extraction Pipeline (`src/intake/packet_models.py`)

**Evidence:**
- `src/intake/packet_models.py:352` — `set_fact` blindly overwrites existing facts with no merge logic.
- When the customer message extracts `destination_candidates=["Singapore"]`, a later envelope (e.g., agent notes that don't mention Singapore) overwrites with `[]`.
- Same destructive behavior confirmed for: `pace`, `budget`, `duration`, `party_composition`.
- The `ExtractionPipeline` processes multiple envelopes sequentially. Each envelope runs its own extraction and calls `set_fact`, which replaces whatever was there before — it does NOT merge or preserve prior extractions.

**Concrete test result:**
- Extraction from customer text alone → returns `"Singapore"`
- Extraction from agent notes alone → returns `"Singapore"` (because agent notes mention it)
- Combined pipeline run → returns `[]` (empty)

**Root Cause:** `ExtractionPacket.set_fact()` is a straight assignment. There is no union/merge logic across envelopes. A later extraction output that lacks a field wipes out an earlier correct extraction of that same field. The pipeline assumes each envelope is self-contained; it is not.

**Impact:** ANY pipeline run with multiple text sources (customer + agent notes, or multiple messages) will silently lose data. Operators cannot trust extracted fields. The "AI extraction" feature is worse than useless — it creates false confidence while destroying correct data.

**Fix direction:** Add packet-level merge semantics. `set_fact` should append to lists (with deduplication), prefer non-empty over empty values, and for scalar conflicts, use a confidence score or first-seen rule. Never overwrite a populated field with an empty one.

---

### ISSUE-02 — Destination Regex Is Fragile
**Severity:** P1 | **Status:** Unfixed | **Component:** Intake Extractors (`src/intake/extractors.py`)

**Evidence:**
- `src/intake/extractors.py:68` — `_DESTINATION_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")`
- This regex matches EVERY capitalized word, not just destinations. In the customer message:
  - "Hi **Ravi**" → raw match = "Ravi"
  - The extractor then uses `raw_match` (the first hit) instead of the actual destination.
- 582,957 cities are loaded in the destination database.
- `is_known_destination("Singapore")` returns `True` at the database layer.
- Yet the pipeline still loses Singapore because of Issue-01 (overwritten by empty agent notes).

**Root Cause:** Two problems compound:
1. The regex is too broad — it does not anchor on destination-context keywords ("visit", "go to", "travel to", "planning a trip to").
2. There is no disambiguation step that filters raw matches against the known-destination database before accepting them.

**Impact:** False positives from names, brand names, and other capitalized words compete with real destinations. The extractor's signal-to-noise ratio is poor.

**Fix direction:** Post-process regex matches through `is_known_destination()` before populating `destination_candidates`. Limit regex hits to words within 5 words of travel verbs.

---

### ISSUE-03 — Progress Panel UX Issues
**Severity:** P2 | **Status:** Fixed in code, may have stale copies | **Component:** Frontend — `RunProgressPanel.tsx`

**Evidence:**
- Returns `null` when `runState` is null (the "Queued" state was missed).
- Steps don't render during early polling — the panel is blank while the pipeline is initializing.
- Fix applied in canonical `RunProgressPanel.tsx`, but frontend may still load old/stale component copies in certain routes.

**Root Cause:** Defensive coding against null `runState` hid a legitimate UI state. Early polling responses don't yet have `runState` populated.

**Impact:** Operators see a blank or absent progress panel for the first few seconds of every pipeline run. Looks broken.

**Fix direction:** Propagate the fix to all component copies if any exist. Add a storybook/visual test for the `runState === null` branch.

---

### ISSUE-04 — Double-Click Creates Multiple Trips
**Severity:** P1 | **Status:** Fixed in code, needs real-world verification | **Component:** Frontend — `handleProcessTrip`

**Evidence:**
- `handleProcessTrip` had no in-flight guard.
- One click created **3 duplicate trips** in the database.
- Fix applied using `inFlightRef` (or equivalent guard).
- NOT yet verified under real network latency.

**Root Cause:** No debounce or idempotency key on the "Process Trip" button. Standard frontend bug.

**Impact:** Data pollution, duplicate work for operators, confusing UI state.

**Fix direction:** Disable button and show loading state while the request is in flight. Verify with a 3G-throttled connection.

---

### ISSUE-05 — Missing `user_id` in Trips
**Severity:** P1 | **Status:** Fixed in code, needs verification | **Component:** Backend — persistence layer

**Evidence:**
- `save_processed_trip()` did not accept a `user_id` parameter.
- `_execute_spine_pipeline` did not pass `user_id` to the persistence step.
- A trip created via the pipeline had `user_id = null` (or default), breaking ownership queries and audit trails.
- Fix applied: added `user_id` parameter to `save_processed_trip` and wired it through `_execute_spine_pipeline`.
- Backend restart required to pick up changes; NOT yet verified.

**Root Cause:** Persistence contract was written before auth/user context was fully threaded through the pipeline.

**Impact:** Trips are orphaned. Cannot show "My Trips" for a logged-in user. Cannot enforce access control. Audit trail is broken.

**Fix direction:** Restart backend, run a fresh pipeline, query database to confirm `user_id` is populated.

---

### ISSUE-06 — Analytics Shows Dummy Data
**Severity:** P1 | **Status:** Partially fixed | **Component:** Backend — `src/analytics/metrics.py`

**Evidence:**
- `src/analytics/metrics.py:47` — `averageTotal=9.3` is **hardcoded**.
- Pipeline velocity, stage times — all hardcoded regardless of actual trip count.
- Even with **0 trips** in the system, the dashboard showed:
  - Pipeline velocity: 29h / 58h / 98h (fake numbers)
  - Stage times: fabricated
- Partial fix applied: returns `0` for empty trips, but metrics for actual data are **still hardcoded**.

**Root Cause:** Analytics layer was scaffolded with placeholder values and never replaced with real aggregation queries.

**Impact:** Operators and stakeholders see fiction. Decision-making based on these numbers is actively dangerous. Trust in the system erodes immediately.

**Fix direction:** Remove every hardcoded number. Replace with real SQL aggregations against the trips/runs tables. Add a test that asserts no numeric literals > 1000 exist in `metrics.py`.

---

### ISSUE-07 — Party Size Count Wrong / Ambiguous
**Severity:** P2 | **Status:** Requires clarification | **Component:** Extraction + Business Rules

**Evidence:**
- **Input:** "me, my wife, our 1.7 year old kid, and my parents" = **5 people** (2 adults + 1 toddler + 2 elderly).
- **Agent notes said:** "6 pax (2 adults, 1 toddler aged 1.7y, 2 elderly parents)" — miscounted as 6.
- **Pipeline extracted:** 5 from customer message, OR was overwritten by agent notes (Issue-01), so final count is uncertain.
- **Question unresolved:** Is a toddler counted as a "pax"? In airline/hotel terminology, infants under 2 may travel free and not count as a paying passenger. But for itinerary sizing (stroller, nap times, attractions), the toddler MUST be counted.

**Root Cause:** The extraction pipeline has no domain model for party composition. It extracts a number, not a structured breakdown. The "pax" summary conflates paying passengers with physical travelers.

**Impact:** Wrong party size leads to wrong hotel room bookings, wrong vehicle sizing, and wrong attraction suitability scoring.

**Fix direction:** Change extraction target from a single `party_size` integer to a structured object:
```json
{
  "adults": 2,
  "toddlers": 1,
  "seniors": 2,
  "total_travelers": 5,
  "paying_pax": 4
}
```

---

### ISSUE-08 — Date Context Missing
**Severity:** P2 | **Status:** Unfixed | **Component:** Extraction Pipeline

**Evidence:**
- Customer said: "Jan or Feb 2025"
- Agent notes said: "Call received: Nov 25, 2024 ... travel Feb"
- The app has **no notion of the current date**.
- Regex extracts "Jan or Feb 2025" correctly, but:
  - If the user said "Jan or Feb" without a year (common in conversation), the pipeline cannot infer the year.
  - Year gap logic absent: "Call Nov 2024, travel Feb" → should infer Feb **2025** (the next year), but the pipeline does not reason about temporal ordering.

**Root Cause:** Extraction is regex-only with no temporal reasoning layer. There is no injected "today" context.

**Impact:** Dates without explicit years are stranded. Trip planning for dates near year boundaries fails silently.

**Fix direction:** Inject a reference date (today or call-received date) into the extraction context. Add a disambiguation layer: if month < current month and no year stated, assume next year.

---

### ISSUE-09 — Jargon in UI (Claimed Fixed, Not Verified)
**Severity:** P2 | **Status:** Claimed fixed, unverified | **Component:** Frontend terminology

**Evidence:**
- "Workbench" instead of industry-standard terms (CRM, Trip Builder, Inbox).
- "Guest Intake" — customers are not "guests" in this context; they are leads or customers.
- User noted this was discussed in a prior session, but there is **no evidence** of the fix in the codebase or deployment.

**Root Cause:** Early product terminology was chosen without reference to travel-agency industry norms.

**Impact:** Operators learning the tool must mentally translate jargon. Onboarding friction. Perceived amateurism.

**Fix direction:** Do a full UI string audit. Replace "Workbench" with "Trip Builder" or "Lead Workspace". Replace "Guest Intake" with "New Lead" or "Customer Intake".

---

### ISSUE-10 — Tab Switch Not Working in Workbench
**Severity:** P1 | **Status:** Unfixed | **Component:** Frontend routing / state

**Evidence:**
- User clicked "View Trip" → workspace opened.
- **Trip Details tab was empty**.
- **Intake tab was selected** but showed "No trip loaded".
- State mismatch: the trip ID is in the URL or a parent component, but the tab-level component is not receiving it.

**Root Cause:** Likely a React state prop-drilling failure. The workspace container knows the trip ID, but the child tab panels are initialized with `tripId = null` or are reading from a different state slice.

**Impact:** Operators cannot view a trip they just processed. Core workflow is broken.

**Fix direction:** Trace the `tripId` from route → workspace → tab panel. Ensure it is passed as a required prop or read from a shared state atom (URL param is safest for deep-linking).

---

### ISSUE-11 — Overall Result / Summary Not Shown
**Severity:** P2 | **Status:** Unfixed — missing feature | **Component:** Product / UX

**Evidence:**
- User explicitly asked: "an overall result should also be there."
- After pipeline completion, there is **no summary view**.
- The pipeline runs (operators see progress), but the final state is not presented as a digestible summary.

**Root Cause:** Feature gap. The product has a "process" view but no "result" view.

**Impact:** Operators must manually piece together what the pipeline extracted. This defeats the purpose of automation.

**Fix direction:** Add a "Trip Summary" card or panel that surfaces:
- Destination(s)
- Dates (with confidence)
- Party composition (structured)
- Pace, budget, interests
- Confidence scores per field
- CTA: "Edit" or "Confirm and Build Itinerary"

---

### ISSUE-12 — Customer Notes and Agent Notes Both Mandatory
**Severity:** P2 | **Status:** Unfixed | **Component:** Frontend validation

**Evidence:**
- The workbench disables the "Process Trip" button if **both** Customer Notes and Agent Notes are empty.
- User noted: both needn't be mandatory. A single source should be sufficient.
- In the test scenario, only one field might be filled (e.g., a quick WhatsApp message parsed as customer notes, with no agent notes yet).

**Root Cause:** Overly strict form validation. Logic assumes both fields are always present.

**Impact:** Operators cannot process a trip if one source is missing. Blocks legitimate workflows.

**Fix direction:** Change validation to: enable "Process Trip" if `customer_notes.trim().length > 0 OR agent_notes.trim().length > 0`.

---

## 3. Test Data Used

### Customer Message (as entered)
```
Hi Ravi, I got your number from my wife who is a colleague of Divya.
We are planning to visit Singapore sometime in Jan or Feb 2025.
Tentative dates around 9th to 14th Feb, approx 5 days.
Me, my wife, our 1.7 year old kid, and my parents would be going.
We don't want it rushed.
Interested in Universal Studios and nature parks.
```

### Agent Notes (as entered)
```
Call received: Nov 25, 2024
Caller: Pranay Suyash
Referral: Wife's colleague → Divya (Ravi's wife)
Party: 6 pax (2 adults, 1 toddler aged 1.7y, 2 elderly parents)
Pace preference: Relaxed, not rushed
Budget: Not discussed
Interests: Universal Studios, nature parks
Follow-up: Promised draft itinerary in 1-2 days
Toddler needs: Stroller-friendly, nap time considerations
Elderly needs: Accessible transport, moderate walking only
```

### What the pipeline SHOULD have extracted (ground truth)
| Field | Expected Value | Source |
|-------|----------------|--------|
| Destination | `Singapore` | Customer msg, agent notes |
| Dates | `Feb 9-14, 2025` | Customer msg |
| Duration | `5 days` | Customer msg |
| Party (adults) | `2` | Both |
| Party (toddlers) | `1` | Both |
| Party (seniors) | `2` | Agent notes |
| Total travelers | `5` | Arithmetic |
| Pace | `Relaxed` | Both |
| Budget | `Not discussed` | Agent notes |
| Interests | `Universal Studios, nature parks` | Both |
| Special needs | `Stroller-friendly, accessible transport` | Agent notes |

---

## 4. What Worked vs What Didn't

### What Worked
| Item | Evidence |
|------|----------|
| Basic intake form loads | UI rendered, fields accepted input |
| Destination database is populated | `is_known_destination("Singapore")` returned `True` (582,957 cities loaded) |
| Individual extraction from single text | Extracting from customer text alone → found Singapore |
| Pipeline runs end-to-end | No 500 errors, response returned |
| Progress panel exists | Visual component renders after the null-state fix (but see ISSUE-03) |

### What Didn't Work
| Item | Failure Mode |
|------|--------------|
| Multi-envelope extraction | Data destroyed by later empty envelope (ISSUE-01) |
| Destination regex precision | "Ravi" treated as destination candidate (ISSUE-02) |
| Progress panel early state | Blank on first poll (ISSUE-03) |
| Button idempotency | 3 trips from 1 click (ISSUE-04) |
| User ownership | `user_id` missing in DB (ISSUE-05) |
| Analytics | Hardcoded fiction regardless of real data (ISSUE-06) |
| Party size accuracy | Count uncertain due to overwrite + no toddler model (ISSUE-07) |
| Date inference | No current-date context, no year-gap reasoning (ISSUE-08) |
| Tab routing | Trip details empty after redirect (ISSUE-10) |
| Processing prerequisites | Both fields mandatory when one should suffice (ISSUE-12) |

---

## 5. Recommended Next Steps (Grouped by Priority)

### P0 — Block Launch
1. **Fix and verify ISSUE-01 (Data Destruction)**
   - Implement packet-level merge semantics in `ExtractionPacket`
   - Add targeted test: multi-envelope extraction preserves Singapore/pace/duration
   - Confirm with the exact test data above
   - No launch without this.

### P1 — High Priority (Fix Before Operator Demo)
2. **Verify ISSUE-05 fix** (`user_id` persistence)
   - Restart backend, run pipeline, inspect DB row
3. **Fix ISSUE-06** (Remove hardcoded analytics)
   - Replace with real SQL aggregations
   - Add automated test: assert no hardcoded metrics
4. **Verify ISSUE-04 fix under real latency**
   - Throttle network, confirm no duplicate trips
5. **Fix ISSUE-10** (Tab state / routing)
   - Trace `tripId` prop, ensure Trip Details hydrates correctly
6. **Fix ISSUE-02** (Destination regex disambiguation)
   - Filter regex matches through `is_known_destination()`
   - Add test: "Hi Ravi" must NOT produce a destination candidate

### P2 — Product Polish (Fix Before External Users)
7. **Fix ISSUE-12** (Mandatory field validation)
   - Accept either customer or agent notes
8. **Fix ISSUE-08** (Date context)
   - Inject reference date, add year-gap inference
9. **Implement ISSUE-11** (Summary view)
   - Post-pipeline summary panel with extracted facts
10. **Fix ISSUE-09** (Jargon audit)
    - Scan all UI strings, replace jargon with industry terms
11. **Resolve ISSUE-07** (Party model)
    - Define structured party composition, clarify toddler/senior counting
12. **Verify ISSUE-03** (Progress panel stale copies)
    - Ensure fix is present in all component instances

---

## 6. Architecture Concerns

### 6.1 Pipeline Merge Logic (Root cause of ISSUE-01)
The `ExtractionPipeline` was designed with an implicit assumption: each envelope is a self-contained source of truth. This is wrong for real-world intake where information is **complementary**, not **redundant**. Customer messages and agent notes together form a composite signal. The architecture must be updated to treat extraction as an **accumulative** process:

- **Current model:** `Envelope → Extract → Packet.set_fact() → Overwrite`
- **Required model:** `Envelope → Extract → Packet.merge_facts() → Union with preference for non-empty`

**Specific rule set to implement:**
1. Never overwrite a non-empty list with an empty list.
2. For destination candidates, take the union of all sources, deduplicated.
3. For scalar fields (budget, pace), prefer the source that explicitly states it. If both do, prefer customer message for preferences, agent notes for metadata.
4. For dates, merge and deduplicate date ranges; apply temporal disambiguation (see ISSUE-08).

### 6.2 Regex-Only Extraction Is a Ceiling
Issues 02 and 08 share a root cause: extraction is regex-driven with no semantic layer. The app has 582,957 destinations loaded but does NOT use that knowledge during extraction — it only validates post-hoc. A better architecture:
- **NER layer:** Use the destination database as a whitelist during extraction, not just after.
- **Temporal layer:** Inject a reference date and apply constraint solving ("Feb" + call_date=Nov2024 → Feb 2025).

### 6.3 Hardcoded Analytics Is a Trust Killer
Issue 06 is not a bug, it is a **process failure**. Hardcoded metrics should never have been merged. Recommend adding a CI check: any PR touching `src/analytics/` must include a test that asserts metrics are derived from database queries, not literals. The fact that this shipped means pre-merge review missed it.

### 6.4 State Propagation Anti-Pattern
Issue 10 (tab routing) and Issue 03 (progress panel stale copies) suggest a frontend architecture where state is not propagated through a single source of truth. Recommend:
- Use URL params for trip IDs (deep-linkable, survives refresh).
- Audit for duplicated component code — if `RunProgressPanel` exists in multiple directories with divergent code, consolidate to a single source.

---

## 7. Closing Statement

This test revealed that Waypoint OS's core value proposition — "AI extracts trip details from conversations" — is **architecturally broken at the merge layer**. The individual components (regex, destination DB, UI panels) mostly exist and sometimes work in isolation, but the integration point (the pipeline) destroys data instead of combining it.

Fixing ISSUE-01 is non-negotiable before any operator-facing demo. The remaining issues are serious but do not undermine the fundamental product claim in the same way.

**Recommendation:** Allocate the next engineering cycle exclusively to:
1. Pipeline merge semantics (P0)
2. End-to-end verification with the Singapore scenario test data (re-run after fix)
3. Frontend tab state fix (P1)

Only after these three are verified should work resume on new features.

---
*Document saved per issue review naming convention: `travel_agency_process_issue_review_<date>.md`*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*
