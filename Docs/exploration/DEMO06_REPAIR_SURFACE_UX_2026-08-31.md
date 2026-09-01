# DEMO-06 — Repair-Surface UX Trace + Copy & Label Audit (EX-DEMO-06 / EX-DEMO-07)

*Date: 2026-08-31*
*Source demo: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` (step 10 finding, P2) + DEMO-07 (P3 copy drift), per `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md`.*
*Method: read-only code trace (`rg` + file reads). No product code changed. Cites are `file:line` against the working tree as of 2026-08-31.*
*Covers: DEMO-06 (repair discoverability), DEMO-09 UX angle (banner specificity), DEMO-07 (copy/label audit).*

---

## Executive Summary

1. **An editable repair form DOES exist** — but only on the Trip Workspace intake page (`/trips/{tripId}/intake`, `IntakePanel`), not on the workbench `?tab=packet` "Trip Details" tab, which is 100% read-only (alerts + tables, zero inputs).
2. **In exactly the state where repair is needed, the editable form is unreachable**: blocked runs never persist a Trip (backend returns before `save_processed_trip`), so every "Open Trip Details" link — which requires `trip?.id` — is conditionally absent. The repair loop dead-ends for draft-only blocked state.
3. **Root cause of the demo no-op**: on a blocked run the app auto-switches to the packet tab (`PageClient.tsx:540-544`); clicking "Review Missing Fields" then just re-sets the same `?tab=packet` with `scroll: false` and no focus management — a genuine visual no-op.
4. Recommended design: button navigates to the editable field (auto-opens first required editor, reusing the existing `openPlanningEditor` machinery) and the banner lists missing field names inline (data already rendered in PacketTab:156 — reuse at banner level). ~0.5–1 day, frontend-only, provided the draft→trip persistence question is settled separately (overlaps EX-DEMO-01).
5. Copy audit: rename "Work email"→"Email" + `you@agency.com`→`you@example.com` (5 surfaces); sidebar label needs a single source of truth (`agencySettings.profile.agency_name`, with the fallback string only as last resort — "Waypoint HQ" does not exist anywhere in code, it is session data); gate the `runtime · development` chip to dev builds via an env flag (precedent: `NEXT_PUBLIC_ENABLE_SCENARIO_LAB`).

---

## Part 1 — Repair-Surface Trace

### 1.1 What each control is supposed to do (designed behavior)

| Control | Intended behavior | Evidence |
|---|---|---|
| **"Review Missing Fields"** (blocked banner button) | Switch the in-page workbench tab to `packet` ("Trip Details") | `frontend/src/app/(agency)/workbench/PageClient.tsx:1002-1007` → `onClick={() => handleTabChange('packet')}`; `handleTabChange` at `PageClient.tsx:399-407` writes `?tab=packet` via `router.replace(..., { scroll: false })`. It does **not** scroll, focus, or open anything. |
| **"Open Trip Details"** (banner secondary link) | Navigate to the canonical repair route `/trips/{tripId}/intake` | `PageClient.tsx:1008-1015` renders a `<Link href={tripRepairHref}>` **only when `tripRepairHref` is truthy**; `tripRepairHref = trip?.id ? getTripRepairRoute(trip.id) : null` (`PageClient.tsx:281`); `getTripRepairRoute` = `getTripRoute(id, 'intake')` → `/trips/{id}/intake` (`frontend/src/lib/routes.ts:62-71`). Without a Trip, the link simply does not render. |
| **"View details"** expander (packet tab alert card) | Purely local state toggle: expands inline legacy errors/warnings + unknown-field list inside the same card | `frontend/src/app/(agency)/workbench/PacketTab.tsx:166-174` (`setShowValidationDetails`), expanded content at `PacketTab.tsx:184-239`. No navigation. |
| **Trip Details tab (`?tab=packet`)** | Renders `PacketTab` — validation alert card, summary cards, "Extracted Information" table, Unknowns/Ambiguities lists. **All read-only.** | Tab render switch at `PageClient.tsx:1333-1334`. PacketTab contains zero `<input>/<textarea>/<select>` elements; every repair affordance inside it is a `<Link>` to `/trips/{tripId}/intake` (`PacketTab.tsx:175-182`, `411-418`), each gated on `trip?.id`. |
| Auto-navigation on block | When a run ends `blocked`/`failed`, the app **already** switches to the packet tab on the user's behalf | `PageClient.tsx:519-544`: "Auto-switch to the tab containing errors when a run ends in blocked/failed state" → `handleTabChange('packet')` at line 544. |

### 1.2 Editable-Form Existence verdict

**Verdict: YES, an editable repair form exists — but it lives one route away, and only for Trips (not drafts).**

- The editable surface is `IntakePanel` mounted at `/trips/[tripId]/intake` (`frontend/src/app/(agency)/trips/[tripId]/intake/PageClient.tsx:11` → `frontend/src/components/workspace/panels/IntakePanel.tsx`).
  - "Missing customer details" panel with Required rows and per-field editors: `IntakePanel.tsx:1202`, `1388` (`PlanningDetailSection` with `required` rows; `dates` opens the date-window editor).
  - Click-to-edit fields including **Purpose** (`EditableField field='tripPurpose'`, `IntakePanel.tsx:1470-1474`) and **Dates** (`IntakePanel.tsx:1494`); the generic editor inputs live in `frontend/src/components/workspace/panels/IntakeFieldComponents.tsx:26-182` (`EditableField`) and `:197-277` (`BudgetField`).
  - Focus machinery already exists: `openPlanningEditor` (`IntakePanel.tsx:1032`), editor refs (`IntakePanel.tsx:439-445`), and a "Add {first required field}" button that auto-opens the first required editor (`IntakePanel.tsx:1231-1237`) — this is exactly the behavior IMP-05 wants, already implemented for the in-page path.
- **The workbench has no structured editors.** The workbench `?tab=intake` (`IntakeTab.tsx`) is the capture surface: two textareas (`IntakeTab.tsx:174, 198`) and a read-only "Captured Details" chip row (Dates shown read-only at `IntakeTab.tsx:118-120`). The packet tab is read-only (§1.1). So from a blocked workbench state, the *only* structured repair path is `/trips/{id}/intake`.
- **The killer gap:** on the demo's blocked run, **no Trip was ever persisted**, so `trip` is `undefined` and every route to the editable form is absent:
  - Backend: blocked branches in `spine_api/services/pipeline_execution_service.py` (early-exit ~lines 285-305; validation-invalid ~lines 408-440) call `run_ledger.block(...)`, update the draft to `blocked`, and `emit_run_blocked_fn(..., trip_id=None)` — then `return` **before** `save_processed_trip` (which runs only on the `partial_intake` ~line 313 and success ~line 386 paths).
  - Frontend consequence: `tripRepairHref = null` (`PageClient.tsx:281`) → banner "Open Trip Details" hidden (`PageClient.tsx:1008`), PacketTab "Open Trip Details" hidden (`PacketTab.tsx:175`), Unknowns "Open trip details" link hidden (`PacketTab.tsx:411`).
  - **Net effect: for a draft-only blocked state, the UI offers zero paths to any editable field. The loop cannot be completed in the UI.** This is bigger than a discoverability bug and is the same root condition as EX-DEMO-01 (blocked drafts never become leads/trips). The two fixes should be decided together.

### 1.3 Root-Cause Hypothesis (demo no-op)

Primary (high confidence), two layers:

1. **The button fired but was a visual no-op.** When the run transitioned to `blocked`, the auto-switch effect had already moved the user to the packet tab (`PageClient.tsx:540-544`). Clicking "Review Missing Fields" then executed `handleTabChange('packet')` again — writing the identical `?tab=packet` URL via `replace(..., { scroll: false })` (`PageClient.tsx:404`). No scroll, no focus, no content change → "did not visibly scroll or navigate."
2. **Even a successful "navigation" lands on a read-only dead end.** The destination (`PacketTab`) has no editable fields, and in draft-only blocked state all three "Open Trip Details" escape hatches are conditionally hidden (§1.2). The demo user — whether they clicked the banner button or the packet-tab links — could never reach an editable input. That matches the demo log: the session ended on the red alert card + read-only "Extracted Information" table.

Secondary contributor: the banner itself renders *above* the tab strip (`PageClient.tsx:974` vs `1305`), so a tab swap below the fold-line of attention is easy to miss; and `scroll: false` guarantees no viewport movement even when the tab actually changes.

### 1.4 Recommended Design + Acceptance Criteria

**Design (IMP-05, aligned with the brief):**

1. **Button behavior — navigate to the editable field, not to a read-only table.**
   - If a Trip exists: "Review Missing Fields" routes to `/trips/{tripId}/intake` with a field param (e.g. `?repair=<field_name>`) and `IntakePanel` auto-opens + focus-rings the first empty required editor. Reuse `openPlanningEditor` / `planningEditorRefs` (`IntakePanel.tsx:1032, 439-445`) and the existing "Add {first required field}" pattern (`IntakePanel.tsx:1231-1237`); do not build a parallel mechanism.
   - If no Trip exists (draft-only blocked state): keep the user in the workbench, switch to the packet tab **and** move keyboard focus to the "Missing fields" list in the alert card (give it `tabIndex={-1}` + a visible focus ring), and show a truthful next step (per EX-DEMO-01's decision: either "your request is saved in Drafts — reopen it to add details" copy, or real trip persistence). Never leave the current silent no-op.
   - Same treatment for "Open Trip Details": it must never render as a link to a surface that cannot exist for the current state.
2. **Banner specificity (DEMO-09).** The banner already has the data: render missing field names inline at banner level by reusing the exact expression PacketTab uses (`PacketTab.tsx:154-159`): `Missing fields: {unknowns.map(labelOrTitle(FIELD_LABELS, ...)).join(', ')}` from `store.result_validation`/`result_packet.unknowns`.
3. **Focus affordance.** The focused field gets a highlight ring (`focus-visible` outline, consistent with `focus:border-[var(--accent-blue)]` used in `IntakeFieldComponents.tsx:125, 138`); button remains keyboard-operable (it is a `<button>`/`<Link>`, so Enter triggers the same path).

**Acceptance criteria (Given/When/Then):**

- **AC1 — Banner names the fields.** Given a run ends blocked with unknowns `date_window`, `trip_purpose`, When the persistent banner renders, Then it shows "Missing fields: Travel Dates, Trip Purpose" inline (no click-through required).
- **AC2 — Button produces a visible, useful change from any tab.** Given the user is already on the packet tab (post-auto-switch), When they click "Review Missing Fields", Then focus moves to the missing-fields list (focus ring visible, `document.activeElement` is the list) — not a silent URL rewrite.
- **AC3 — Reaches an editable field when a Trip exists.** Given a blocked state with a persisted trip, When the user clicks "Review Missing Fields" (via mouse or keyboard), Then they land on `/trips/{id}/intake` with the first empty required field's editor open and focused.
- **AC4 — No dead ends without a Trip.** Given a draft-only blocked state, When any repair affordance renders, Then it is either absent-with-explainer or routes to a working draft repair path; zero controls render that cannot function.
- **AC5 — Keyboard reachable.** All of the above achievable with Tab + Enter only; focused elements expose the focus ring to `prefers-reduced-motion` and screen readers (aria-live on the banner already exists via adjacent patterns).

### 1.5 Effort Estimate

| Slice | Estimate | Notes |
|---|---|---|
| Banner missing-field names (AC1) | ~1–2 h | Data + label map already exist; reuse `PacketTab.tsx:154-159` expression + `FIELD_LABELS` at banner level. |
| Button behavior + focus management (AC2, AC4, AC5) | ~3–4 h | `handleTabChange` variant with focus target; packet-tab missing-list `tabIndex` + ring; truthful copy for draft-only state. |
| Trip-route deep link with auto-open editor (AC3) | ~3–4 h | Param plumbing + `useEffect` in `IntakePanel` calling existing `openPlanningEditor`; needs the trip-persistence question answered (below). |
| Tests (jest/RTL per existing suites `PacketTab.test.tsx`, `IntakePanel.test.tsx`, `page.test.tsx`) | ~2–3 h | AC1–AC5 each get one test. |
| **Total (frontend-only, post-EX-DEMO-01 decision)** | **~0.5–1 day** | Blocked on one product decision: should blocked runs persist a Trip (EX-DEMO-01's lead-loop call) or should draft repair be built in-workbench? That decision is a prerequisite for AC3's route target; everything else is unblocked. |

---

## Part 2 — Copy & Label Audit (EX-DEMO-07)

| String (as rendered) | Location | Issue | Suggested replacement |
|---|---|---|---|
| **"WORK EMAIL"** label | `frontend/src/app/(auth)/signup/page.tsx:100` (source text `Work email`; rendered uppercase by `.auth-field label { text-transform: uppercase }`, `frontend/src/app/(auth)/auth.css:87-93`). Same string on sibling surfaces: `login/page.tsx:84` (placeholder), `forgot-password/page.tsx:64` (placeholder), `join/[code]/page.tsx:183,189`, `components/auth/AuthProvider.tsx:135`. | Agency-only framing on a self-serve product: the pricing page (`/pricing`) positions "Workspace Access" as self-serve for anyone, and the demo persona (hobbyist dev) read it as "not for me." Also inconsistent: signup uses label+placeholder, login/forgot only placeholder. | Label **"Email"**; placeholder **`you@example.com`**. Apply uniformly to all five surfaces listed. (Zero logic change; matches pricing page's self-serve positioning.) |
| **"Waypoint HQ" vs "Agency Workspace"** (sidebar workspace name) | Both resolve to one line: `frontend/src/components/layouts/Shell.tsx:169` — `agencyName = agencySettings?.profile?.agency_name \|\| 'Agency Workspace'`. **"Waypoint HQ" appears nowhere in the repo** (verified via `rg` across code + backend) — it is *data*: the `agency_name` value served by agency settings in the first demo session (local dev DB / seeded profile; backend signup naming lives at `spine_api/services/auth_service.py:62` — `"{name}'s Agency"` — and `:108-111`, email-domain title-case). The second session's "Agency Workspace" is the hardcoded fallback shown when the settings query returned nothing (`useAgencySettings` empty/error). | Two different labels for the same slot across sessions = the slot has no guaranteed source of truth at first paint, and the fallback string leaks a generic placeholder. | Single source of truth = `agencySettings.profile.agency_name`. Guarantee it is seeded at signup (auth_service already sets it) and cached; treat `'Agency Workspace'` strictly as a loading/error fallback (e.g. render `agencyName` only when the query succeeds, or show a skeleton). Do not introduce a third constant. Recommend confirming the demo's first-session data origin before changing any string (see Open Questions). |
| **"runtime · development"** chip | Rendered under "Operations live" in the sidebar status footer: `frontend/src/components/layouts/Shell.tsx:333-341` (`detailsLabel`); label built in `frontend/src/hooks/useRuntimeVersion.ts:57-63` — `` `runtime · ${payload.environment} · ${sha}` `` from the public `/api/version` endpoint. Visible to **every logged-in user**. | Exposes backend environment name + git SHA to all authenticated users (demo observers included); leaks ops metadata with zero operator value for end users. | Gate visibility: render `detailsLabel` only when `process.env.NEXT_PUBLIC_SHOW_RUNTIME_META === '1'` (set in local dev `.env`), following the existing flag precedent `NEXT_PUBLIC_ENABLE_SCENARIO_LAB === '1'` (`workbench/PageClient.tsx:1291`). Keep the "Operations live" pulse (`Shell.tsx:327-331`) for everyone. Alternative (weaker): role-gate to owner/admin — but env-flag is simpler and matches how the repo already hides dev surfaces. |

---

## Open Questions for Pranay

1. **Draft-state repair target (prerequisite for IMP-05 AC3):** Should blocked runs persist a Trip so `/trips/{id}/intake` repair works (this is EX-DEMO-01's lead-loop decision wearing a different hat), or should the workbench gain an inline draft repair editor? Recommendation: decide once, in EX-DEMO-01, and have IMP-05 consume the outcome — building draft repair twice would violate the no-duplicate-pipeline rule.
2. **"Waypoint HQ" origin:** The string is not in the repo. Can you confirm it came from an `agency_name` value in the local dev DB (seed/test accumulation) rather than a removed build artifact? If it is test data, the fix is the §Part 2 fallback policy, not a string change.
3. **Focus vs auto-open editor:** On reaching the repair surface, should the first empty required field's editor auto-open (like the existing "Add …" button at `IntakePanel.tsx:1231-1237`) or should focus land on the field row with the editor opening on Enter? Recommendation: auto-open — fewer clicks for a user who arrived here explicitly to fill it.
4. **Runtime chip in staging:** Should the flag also expose `runtime · staging · <sha>` to internal testers, or keep it strictly dev (`NEXT_PUBLIC_SHOW_RUNTIME_META=1` only in local envs)?

---

*Exploration doc only — no product code changed, no register edits (F-IDs pending ratification per `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md`).*
