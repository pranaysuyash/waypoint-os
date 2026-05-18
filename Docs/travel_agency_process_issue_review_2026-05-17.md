# Travel Agency Agent – UI Interaction Patterns Audit
**Date:** 2026-05-17
**Scope:** Frontend interaction patterns (combobox/menu/dialog/drawer primitives and auth gate UX)
**Primary skill used:** `ui-interaction-patterns`
**Skill source:** `/Users/pranay/.hermes/skills/ui-interaction-patterns/SKILL.md`

## 1) Governance & context review

Performed before changes per mandate in:
- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/AGENTS.md`
- `/Users/pranay/AGENTS.md`
- `/Users/pranay/.codex/AGENTS.md`
- `/Users/pranay/Projects/agent-start`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
- `motto.md` (root of repo)

Instruction review sweep also included:
- `CLAUDE.md` files at `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md` and `frontend/CLAUDE.md`
- `frontend/AGENTS.md`
- Explicit skill inventory sweep in `/Users/pranay/.hermes/skills`, `/Users/pranay/Projects/skills`, and supporting `rg` discovery.
- Status/review context refresh from current working tree (`git status --short`).

No repo-local `QWEN.md`, `copilot-instructions.md`, or `CODEX.md` were found in `travel_agency_agent`; instruction files present were reviewed where available.

## 2) Why the audit was needed

The earlier implementation had interactive-risk symptoms in high-traffic UI surfaces:
- menu disclosure without robust keyboard/focus behavior,
- brittle auth gate assertions coupled to label formatting changes,
- and interaction helpers not being treated as shared canonical surfaces.

The task objective was explicitly to deliver first-principles improvements, not one-off patches, and to apply UI interaction pattern discipline consistently across existing abstractions.

## 3) Pattern scan (beyond first hit)

Search was run across frontend interaction surfaces:
- `rg` over `frontend/src/components/ui`, `frontend/src/components/layouts`, and `frontend/src/components/auth`
for:
  - `role='menu'`, `role='menuitem'`, `role='combobox'`, `role='listbox'`,
  - `aria-expanded`, `aria-haspopup`, `aria-activedescendant`,
  - keyboard handlers (`onKeyDown`), focus management points.

Observed pattern scope:
- Additional adjacent custom-button pattern hotspots were found in:
  - `frontend/src/components/visual/TeamPerformanceChart.tsx`
  - `frontend/src/components/workspace/panels/SuitabilitySignal.tsx`
- Menu semantics and interactive state were concentrated in:
  - `frontend/src/components/layouts/UserMenu.tsx`
- Combobox semantics now consolidated in:
  - `frontend/src/components/ui/SmartCombobox.tsx`
- Inbox list/menu filters were implemented in:
  - `frontend/src/components/inbox/ComposableFilterBar.tsx`
- Overlay surfaces:
  - `frontend/src/components/ui/modal.tsx`
  - `frontend/src/components/ui/drawer.tsx`
- Auth gate and login prompt path:
  - `frontend/src/components/auth/AuthProvider.tsx`
- Trip assignment quick actions were isolated to:
  - `frontend/src/components/inbox/TripCard.tsx`

No parallel duplicate menu or combobox implementations were found in sibling components at this pass, so the implementation could be fixed at canonical points with low migration risk.

## 4) Findings and decisions (first-principles classification)

### Finding A (closed): `SmartCombobox` APG contract gaps
**Root cause:** earlier interactions had incomplete role/ARIA and navigation certainty for assistive tech and robust pointer/keyboard parity.

**Remediation validated in code and tests:**
- `frontend/src/components/ui/SmartCombobox.tsx` now uses:
  - `role='combobox'` with `aria-expanded`, `aria-haspopup='listbox'`,
    `aria-controls`, `aria-autocomplete`, `aria-activedescendant`
  - explicit `role='listbox'` container + `role='option'` options
  - stable option ids through `optionId`
  - Home/End and robust arrow navigation

**Why this is not patchy:** this aligns behavior to canonical APG interaction patterns in one shared component; downstream forms gain correctness from one canonical fix instead of repeated consumers.

### Finding B (closed): `UserMenu` interaction model was incomplete
**Root cause:** menu was visually presentable but did not consistently implement keyboard and focus contracts expected for action menus.

**Remediation validated in code and tests:**
- `frontend/src/components/layouts/UserMenu.tsx` now adds:
  - explicit trigger/menu ids with `aria-controls` / `aria-labelledby`,
  - managed `open`, `close`, and `toggle` transitions,
  - roving focus state with `activeItemIndex`,
  - trigger and menu-level keyboard contracts (`ArrowUp/Down`, `Home`, `End`, `Tab`, `Escape`),
  - Enter/Space activation on menuitems,
  - deterministic focus restore to trigger on Escape/close.
- New interaction tests in:
  - `frontend/src/components/layouts/__tests__/UserMenu.test.tsx`

**Why this is not patchy:** behavior is centralized in one shared user menu component and tested through keyboard + focus lifecycle cases.

### Finding C (closed): Auth-provider test contract mismatch was brittle
**Root cause:** assertion was anchored to literal destination label formatting instead of runtime-intent text normalization.

**Remediation validated in code and tests:**
- `frontend/src/components/auth/__tests__/AuthProvider.test.tsx` now asserts against normalized destination intent with regex `/continue to trips in planning/i`.

**Why this is not patchy:** not behavior-changing runtime code, but removes fragility that can block true regressions from surfacing while preserving behavioral intent.

### Finding D (closed): `Tab` key handling could trap focus
**Root cause:** both combobox and menu surfaces intercepted `Tab` and prevented default without guaranteeing focus progression, causing keyboard traps in controlled focus contexts.

**Remediation validated in code and tests:**
- `frontend/src/components/ui/SmartCombobox.tsx` now treats `Tab` as `Close + Next`:
  - closes the listbox,
  - computes the next external focusable control via shared focus utility,
  - moves focus to the next control outside the combobox.
  - `frontend/src/components/layouts/UserMenu.tsx` now treats `Tab` as `Close + Next`:
  - closes the menu without restoring focus to the trigger,
  - computes the next external focusable control via shared focus utility.
- Regression coverage was added in:
  - `frontend/src/components/ui/__tests__/SmartCombobox.test.tsx`
  - `frontend/src/components/layouts/__tests__/UserMenu.test.tsx`

**Why this is not patchy:** both fixes live in canonical interaction components and enforce the same keyboard contract across menu/listbox patterns instead of ad-hoc per-page workarounds.

### Finding E (closed): `TripCard` assignment action menu and inbox filter bar required keyboard parity
**Root cause:** assignment control and composable filters exposed interactive popups with pointer-first behavior and incomplete keyboard semantics.

**Remediation validated in code and tests:**
- `frontend/src/components/inbox/TripCard.tsx` now implements:
  - `aria-haspopup='menu'`, `aria-expanded`, and `aria-controls` on assignment trigger,
  - menu `role='menu'` + `role='menuitem'` with roving `tabIndex`,
  - Arrow/Home/End/Enter/Space navigation, `Escape` and `Tab` close/focus paths.
  - focus return behavior using `getFocusableElements(...)` so `Tab` exits the surface without trap.
- `frontend/src/components/inbox/ComposableFilterBar.tsx` now has:
  - filter triggers with `aria-expanded`/`aria-controls`,
  - listbox surfaces with `role='listbox'`, `aria-activedescendant`, `role='option'`, and focused option activation,
  - menu/preset popup with roving focus and Enter/Space activation.
- New interaction assertions are added in:
  - `frontend/src/components/inbox/__tests__/TripCard.test.tsx`
  - `frontend/src/components/inbox/__tests__/ComposableFilterBar.test.tsx`

**Why this is not patchy:** both updates were made at recurring interaction surfaces in `inbox` domain and validated with contract-focused tests rather than local one-off handlers.

### Finding F (closed): Custom non-native button surfaces removed from chart/signal surfaces
**Root cause:** chart and signal surfaces used `div role='button'` patterns with manual Enter/Space handling and `aria-disabled`, creating sustained accessibility debt and inconsistent focus/activation semantics.

**Evidence:**
- `frontend/src/components/visual/TeamPerformanceChart.tsx`
  - Now fully migrated to native `<button type='button'>` with native disabled handling.
- `frontend/src/components/workspace/panels/SuitabilitySignal.tsx`
  - Refactored `FlagItem` from custom role/button handling to split action model:
    - primary drill row button with native interaction semantics
    - optional dedicated acknowledge action button.

**Why this is not patchy:** these are repeated domain surfaces used by operators and agents in nontrivial workflows; using native controls where possible (or a canonical button utility) reduces long-term maintenance risk and future AT regression likelihood.

**Closure evidence and validation intent achieved in this pass:**
- `TeamPerformanceChart`: ✅ completed.
- `SuitabilitySignal`: ✅ completed.
- Added and updated interaction assertions for native button activation semantics in corresponding tests.

### Finding G (closed): Page upload drop-zone in itinerary checker migrated to native control
**Root cause:** The upload drop-zone in itinerary checker relied on `div role='button'` plus manual `onKeyDown` handling, creating the same non-native interactive anti-pattern in the traveler app shell.

**Evidence:**
- `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx`
  - Replaced drop-zone wrapper with native `<button type='button'>`.
  - Removed custom keyboard interception (`onKeyDown` + `role='button'` + `tabIndex`) and preserved drag/drop + click activation behavior via the native button control.
  - Removed nested `<button>` inside the interaction surface by rendering a visually styled non-interactive label element for the “Choose file to score” callout.

**Why this is not patchy:** this fix applies the same accessibility principle to a large user-flow surface (upload/score), not merely a cosmetic fix in a single chart card.

## 5) What remains unchanged (and why)

- `frontend/src/components/ui/modal.tsx` and `frontend/src/components/ui/drawer.tsx` already include:
  - portal mounting
  - `role='dialog'`
  - `aria-modal='true'`
  - inert sibling handling
  - focus trap + escape handling in current implementation

No duplicate route, duplicate interaction primitive, or ad-hoc menu clone was found; canonical ownership remains in the existing components above.

## 6) Validation evidence

### Unit / interaction test evidence
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/inbox/__tests__/TripCard.test.tsx src/components/inbox/__tests__/ComposableFilterBar.test.tsx`
  - Historical result: **2 passed (22 tests)**
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/inbox/__tests__/ComposableFilterBar.test.tsx`
  - Historical result: **passed; added additional `Tab`-to-exit assertion for quick presets**
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/ui/__tests__/SmartCombobox.test.tsx src/components/auth/__tests__/AuthProvider.test.tsx src/components/layouts/__tests__/UserMenu.test.tsx`
  - Historical result: **13 tests passed**
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/ui/__tests__ src/components/layouts/__tests__ src/components/auth/__tests__`
  - Historical result: **16 test files, 132 tests passed**
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/ui/__tests__/modal.test.tsx src/components/ui/__tests__/drawer.test.tsx src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx src/components/ui/__tests__/SmartCombobox.test.tsx`
  - Historical result: **4 passed (36 tests)**
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/ui/__tests__ src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`
  - Historical result: **16 test files, 153 tests passed**
- `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/ui/__tests__/SmartCombobox.test.tsx src/components/layouts/__tests__/UserMenu.test.tsx src/components/ui/__tests__/modal.test.tsx src/components/ui/__tests__/drawer.test.tsx src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`
  - Historical result: **5 passed (41 tests)**

- Current revalidation (2026-05-17):
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && rm -rf node_modules && npm install`
    - Result: ✅ clean install completed (627 packages).
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm test -- --run src/components/ui/__tests__/SmartCombobox.test.tsx src/components/layouts/__tests__/UserMenu.test.tsx src/components/inbox/__tests__/TripCard.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/components/workspace/panels/__tests__/SuitabilitySignal.test.tsx`
    - Result: ✅ 5 files / 68 tests passed.
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm run test -- --run src/components/workspace/panels/__tests__/SuitabilitySignal.phase3.test.tsx`
    - Result: ✅ 1 file / 18 tests passed.
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && ./node_modules/.bin/eslint src/app/'(traveler)/itinerary-checker/PageClient.tsx' src/components/visual/TeamPerformanceChart.tsx src/components/workspace/panels/SuitabilitySignal.tsx`
    - Result: ✅ passed.
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && ./node_modules/.bin/eslint src/components/visual/TeamPerformanceChart.tsx src/components/workspace/panels/SuitabilitySignal.tsx src/components/workspace/panels/__tests__/SuitabilitySignal.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/components/layouts/__tests__/UserMenu.test.tsx src/components/ui/__tests__/SmartCombobox.test.tsx`
    - Result: ✅ passed.
  - Structural anti-pattern sweep:
    - `cd /Users/pranay/Projects/travel_agency_agent && rg -n "role=['\\\"]button['\\\"]" frontend/src`
    - Result: no remaining `role=\"button\"` matches in component and app code.
  - Historical (2026-05-17): `npm run typecheck` was previously blocked in this sandbox by missing/hidden type declarations and was not part of that pass.

### Current revalidation (2026-05-18)
- Additional repo-wide module consistency and compile pass:
  - `cd /Users/pranay/Projects/travel_agency_agent && npm install`
    - Result: ✅ command completed; root has no third-party dependency set to install, so no persistent `node_modules` directory is expected.
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && rm -rf node_modules && npm install`
    - Result: ✅ clean install completed.
  - `cd /Users/pranay/Projects/travel_agency_agent/tools && rm -rf node_modules && npm install`
    - Result: ✅ clean install completed (`playwright` dependency graph).
  - `cd /Users/pranay/Projects/travel_agency_agent/tools/benchmarks/rg_vs_fff && rm -rf node_modules && npm install`
    - Result: ✅ clean install completed (`@ff-labs/fff-node` dependency graph).
- Full frontend verification after cleanup:
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm run test -- --run src/components/ui/__tests__/SmartCombobox.test.tsx src/components/layouts/__tests__/UserMenu.test.tsx src/components/inbox/__tests__/TripCard.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/components/workspace/panels/__tests__/SuitabilitySignal.test.tsx`
    - Result: ✅ 5 passed (68 tests).
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm run test -- --run src/components/workspace/panels/__tests__/SuitabilitySignal.phase3.test.tsx`
    - Result: ✅ 1 passed (18 tests).
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm run test -- --run src/components/ui/__tests__/drawer.test.tsx src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`
    - Result: ✅ 2 passed (28 tests).
  - `cd /Users/pranay/Projects/travel_agency_agent/frontend && npm run typecheck`
    - Result: ✅ no TypeScript errors.

### Structural verification
- `git status --short` was rechecked before/after edits; this audit is scoped to frontend interaction layer changes, with pre-existing untracked and modified files left untouched.
- `rg` search showed no second canonical menu implementation requiring simultaneous migration.
- `eslint` on touched frontend interaction files had been validated clean in this task thread:
  - `src/components/ui/SmartCombobox.tsx`
  - `src/components/layouts/UserMenu.tsx`
  - `src/components/ui/__tests__/SmartCombobox.test.tsx`
  - `src/components/layouts/__tests__/UserMenu.test.tsx`
  - `src/app/'(traveler)/itinerary-checker/PageClient.tsx`
  - `src/components/visual/TeamPerformanceChart.tsx`
  - `src/components/workspace/panels/SuitabilitySignal.tsx`

## 7) 11-dimension audit (this feature slice)

| Dimension | Status | Notes |
|---|---|---|
| Code | ✅ | Focus/menu/ARIA/keyboard paths are implemented in shared user-facing interaction components and covered by targeted tests. |
| Operational | ✅ | User menu flow and combobox control now have deterministic close/open/focus behavior, reducing UI failure modes during keyboard use. |
| User Experience | ✅ | Interaction intent is clearer for keyboard users; settings/sign-out actions can be activated without pointer. |
| Logical Consistency | ✅ | Canonical interaction contracts are local to shared primitives and menu component, not duplicated per call site. |
| Commercial | 🟡 | No direct commercial feature added here; this work improves retention/support risk from interaction failures. |
| Data Integrity | ✅ | No user data mutation logic changed. |
| Quality & Reliability | ✅ | Interaction behavior is validated by focused suite runs on a clean install; unresolved environment issues are now in outer repository state only. |
| Compliance | ✅ | Better ARIA and keyboard behavior reduces accessibility regressions relative to previous state. |
| Operational Readiness | ✅ | Manual keyboard smoke on real pages is recommended, but interaction surfaces are now test-covered and lint-clean in a clean dependency state. |
| Critical Path | ✅ | Changes are isolated, low blast radius, and targeted at high-traffic components. |
| Final Verdict | ✅ | Merge-ready for feature-surface delivery; verification is complete on clean local install and can proceed to full-suite execution. |

## 8) Remaining follow-ups (non-blocking)

1. ~~Add one real-page keyboard accessibility smoke test for `SmartCombobox` usage in intake flows (focus + arrow + add custom path).~~ ✅ Closed: Added in `frontend/src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx` as a keyboard flow through `EditableField`/trip type `SmartCombobox`.
2. ~~Add one assertion in modal/drawer tests for focus restoration in overlay close paths and overlay-click closure sequence.~~ ✅ Closed:
   - `frontend/src/components/ui/__tests__/modal.test.tsx` now covers dialog open, overlay `onMouseDown` close callback wiring, and Escape + focus restoration.
   - `frontend/src/components/ui/__tests__/drawer.test.tsx` now covers panel open, overlay `onMouseDown` close callback wiring, and Escape + focus restoration.
3. ~~Consider documenting menu/focus conventions as a small shared pattern note under `frontend/src/lib/accessibility.tsx` comments (without changing runtime behavior).~~ ✅ Closed:
   - Added focus pattern notes in `frontend/src/lib/accessibility.tsx` under focus-management helpers.
4. ~~Add architectural cleanup for remaining native-interop button debt (open): `frontend/src/components/workspace/panels/SuitabilitySignal.tsx`: replace div-based custom button pattern with canonical shared interaction component or split-action row model.~~ ✅ Completed:
   - `frontend/src/components/workspace/panels/SuitabilitySignal.tsx` now uses native `<button type="button">` for drill actions and dedicated acknowledgment actions.
   - Duplicate custom/non-native button behavior for this surface is removed.
5. ~~Add architectural cleanup for remaining page-shell interaction debt: `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx` drop-zone wrapper role/button migration.~~ ✅ Completed:
   - `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx` now uses a native `<button type='button'>` drop-zone control with keyboard semantics from the browser and preserved drag/drop behavior.

## 9) Final risk posture and recommendation

The interaction fixes are **long-term and architectural** for this feature area because they land in shared UI primitives and shared interaction components rather than ad-hoc per-route patches. The audit also converted a brittle auth test to intent-driven assertion to reduce test noise and improve signal quality.

As of this update, primary follow-ups for the audited core surfaces are complete; no additional interaction debt items remain open in the audited scope.

Checklist applied: `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`
