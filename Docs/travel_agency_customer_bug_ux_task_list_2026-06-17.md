# Travel Agency Customer Bug / UX Task List - 2026-06-17

Source:

- live customer-only simulation on `/itinerary-checker`
- supporting owner/agent simulations where relevant

Primary goal:

- turn the customer live simulation into a concise product task list

## P0

### 1. Anonymous report-management mismatch

Problem:

- the traveler result screen exposed `Export JSON` and `Delete saved data`
- in the anonymous flow, both actions returned `401 Not authenticated`

Why it matters:

- this is a trust break
- the UI says these are available
- the traveler learns they are not by hitting an error path

Desired outcome:

- anonymous public-checker reports can be exported and deleted when they belong to the public checker flow
- or the controls are suppressed when unavailable

Status after this pass:

- fixed by aligning backend permissions with the anonymous public-checker flow

## P1

### 2. Thin extracted-summary state feels unfinished

Problem:

- after a real submission, the result panel showed:
  - score
  - blocker state
  - but `Trip Summary (Extracted)` only said the equivalent of “we are still waiting for parsed details”

Why it matters:

- the customer expects a useful brief, not a partial internal state
- this makes the result feel thinner than the landing page promise

Desired outcome:

- when extraction is thin, show a traveler-readable fallback:
  - what the system could do
  - what it could not confidently extract
  - what kind of clearer input would help

Status after this pass:

- improved wording shipped for thin-result fallback states

### 3. Internal/system wording leaks into traveler findings

Problem:

- the main visible finding was `extraction_quality`

Why it matters:

- this is model/internal language
- a traveler needs plain advice, not system labels

Desired outcome:

- replace internal labels with traveler-safe explanations
- example:
  - “We could not confidently read the key trip details from this plan yet.”

Status after this pass:

- improved traveler-facing wording shipped for `extraction_quality`

## P2

### 4. Result depth still trails the promise

Problem:

- the landing experience is polished and persuasive
- the first live result is structurally real, but still does not feel as rich or specific as the marketing promise suggests

Why it matters:

- this creates a conversion gap between expectation and payoff

Desired outcome:

- stronger first result with:
  - richer extracted trip summary
  - clearer route/date/traveler capture
  - more concrete findings

Current status (post-implementation pass):

- traveler fallback copy in extracted summary is now surfaced as a safe status line:
  - "We scored the plan, but we could not confidently pull out the key trip details yet."
- unknowns are now surfaced in both summary and clarifications (example: origin, date window, budget scope, purpose) so thin runs include next-step guidance.
- trip summary now includes richer parsed facts when present (destination candidates, travelers, purpose, notes, budget scope), improving first-screen depth.

### 5. Consent and data-management story could be clearer in paste mode

Problem:

- data-handling language is visible
- but the traveler may not fully understand what is stored in paste mode and which controls will matter afterward

Why it matters:

- public trust flows depend on clear consent, not only correct backend behavior

Desired outcome:

- explicit traveler-facing explanation of:
  - whether this specific run was retained
  - what “Delete saved data” will remove
  - when report export/delete is relevant

Current status (post-implementation pass):

- storage status now reads from report metadata (`/api/public-checker/{tripId}`) and is displayed consistently in the results actions panel.
- this reduces ambiguity for "Export JSON" and "Delete saved data" on anonymous runs, and avoids misleading assumptions about retention.

## Suggested sequencing

1. Keep anonymous report-management aligned with what the UI exposes
2. Improve traveler-facing wording for thin and extraction-limited states
3. Improve first-result richness so the output better matches the landing-page promise
4. Tighten consent/report-management explanation in the public flow

## Success criteria

- no visible traveler action should fail because of hidden auth requirements
- no internal extraction labels should appear as the main customer-facing finding
- thin results should still feel informative and deliberate
- the first customer result should feel closer to a helpful travel brief than a pipeline status screen
