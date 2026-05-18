# Travel Agency Agent – UI Interaction Patterns Audit
**Date:** 2026-05-16
**Scope:** Frontend interaction layers (dialogs, drawers, comboboxes, menus, keyboard/accessibility helpers)
**Primary skill used:** `ui-interaction-patterns` from `/Users/pranay/.hermes/skills/ui-interaction-patterns`
**Context:** Pre-change review before any UI code edits.

## 1) Instruction + Context Review
- Repo instruction stack re-read before this audit:
  - `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
  - `/Users/pranay/Projects/AGENTS.md`
  - `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
  - `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
  - `/Users/pranay/.codex/AGENTS.md`
  - `/Users/pranay/.claude/CLAUDE.md`
- Additional instruction sources consulted per your requested breadth:
  - `/Users/pranay/.hermes/skills/ui-interaction-patterns/SKILL.md` and references:
    - `references/dropdowns-selects.md`
    - `references/aria-keyboard-patterns.md`
    - `references/dialogs-modals.md`
    - `references/drawers-sheets.md`
  - skill inventory under `/Users/pranay/.qwen/skills` (observed for cross-agent parity)
- Repo status was re-checked with read-only `git status --short`; current tree has existing unrelated in-flight docs/tests.
- Code state reviewed in the frontend UI surface and interaction utility layer with `rg` + file walkthroughs.

## 2) Architecture Surface Mapped
### Core shared primitives (single ownership candidates)
- `frontend/src/components/ui/modal.tsx`
- `frontend/src/components/ui/drawer.tsx`

### Shared accessibility utilities (underused)
- `frontend/src/lib/accessibility.tsx`

### Combobox implementation
- `frontend/src/components/ui/SmartCombobox.tsx`
- Used in intake UI: `frontend/src/components/workspace/panels/IntakeFieldComponents.tsx`
- Basic tests in `frontend/src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`

### Modal/drawer consumers
- `frontend/src/components/workspace/modals/OverrideModal.tsx`
- `frontend/src/components/workspace/cards/FollowUpCard.tsx`
- `frontend/src/components/ui/confirm-dialog.tsx`
- `frontend/src/components/workspace/panels/MetricDrillDownDrawer.tsx`

### Menu-like component
- `frontend/src/components/layouts/UserMenu.tsx`

### Auth gating modal path (custom focus behavior)
- `frontend/src/components/auth/AuthProvider.tsx`

## 3) High-confidence findings (ranked)

### F1 — High: SmartCombobox ARIA/keyboard pattern is incomplete and not APG-compliant
**Severity:** `High` (repeated in core intake flows; affects form completion and user assistive-tech correctness)

- `SmartCombobox` does not set combobox roles/attributes required by reference guidance:
  - missing `role="combobox"` on input
  - missing `aria-expanded`, `aria-controls`, `aria-autocomplete`, `aria-activedescendant`
  - popup/options missing `role="listbox"` and `role="option"`
  - missing `id`/selection linkage (`aria-selected`) for options
- Combobox keyboard handling omits `Home/End` and does not expose selected count to screen readers.
- Current input focus is moved during interaction but no explicit `aria-activedescendant` strategy is used.

**Evidence anchors**
- `frontend/src/components/ui/SmartCombobox.tsx:206-267` (input and popup markup)
- `frontend/src/components/ui/SmartCombobox.tsx:267-349` (popup render path with nested fragments)
- `frontend/src/lib/accessibility.tsx` provides the helpers needed but only partially/indirectly used in this flow.

### F2 — High: Modal/drawer primitives are insufficient for true modal interaction parity
**Severity:** `High` (broad blast radius: every modal and drawer in app)

- `Modal` and `Drawer` both set dialog roles but do not implement robust modal lifecycle controls:
  - no explicit body inert/scroll lock
  - focus restoration depends on `document.activeElement` restore only at unmount; no restore target validation
  - focus trap exists only for keydown key but no edge-case handling with dynamic focusable changes
  - no portal layering strategy (`role="presentation"` wrapper is unnecessary for children semantics)
  - no `id`-linked labeling fallback if title missing
  - close logic tied only to keydown on document; interactions are not fully standardized.
- Auth overlay in `AuthProvider` reimplements a custom focus trap and duplicate keyboard handling instead of consuming the shared utility, creating future inconsistency.

**Evidence anchors**
- `frontend/src/components/ui/modal.tsx:39-60` and `65-117`
- `frontend/src/components/ui/drawer.tsx:35-56` and `64-110`
- `frontend/src/components/auth/AuthProvider.tsx:62-108`

### F3 — High: User menu is menu-role styled but missing keyboard accessibility and consistent menu semantics
**Severity:** `High` (directly affects account/settings access and global nav workflow)

- Trigger lacks explicit Enter/Space/Arrow handling and no keyboard open-close focus behavior.
- Menu item list does not expose consistent roving/tab index management for menu semantics.
- Popup container is not keyboard anchored by `aria-controls`/id nor explicit return-focus contract from trigger.

**Evidence anchors**
- `frontend/src/components/layouts/UserMenu.tsx:62-84`
- `frontend/src/components/layouts/UserMenu.tsx:78-129`

### F4 — Medium: Accessibility utility layer is not systemically reused
**Severity:** `Medium` (pattern drift risk)

- `frontend/src/lib/accessibility.tsx` defines reusable utilities and role constants, but production usage is low relative to what exists.
- Tests validate helper behavior, but components currently duplicate ad-hoc handlers (e.g. auth modal).

**Evidence anchors**
- `frontend/src/lib/accessibility.tsx:11-260`
- `frontend/src/lib/__tests__/accessibility.test.tsx:1-120`
- `frontend/src/components/auth/AuthProvider.tsx:39-108`

### F5 — Medium: Combobox dropdown render has fragile nested fragment structure and unclear semantic boundaries
**Severity:** `Medium`

- Nested empty fragments in the open-state section create harder-to-verify DOM structures and increase chance of accidental role leakage when refactoring.
- This does not always break now, but it increases bug surface for keyboard traversal and future maintenance.

**Evidence anchors**
- `frontend/src/components/ui/SmartCombobox.tsx:267-349`

## 4) Pattern propagation map (where the issues repeat)
- Combobox gap appears in all intake combobox usage via `EditableField` (trip type/destination flows) through `IntakeFieldComponents.tsx`.
- Modal/drawer gaps propagate to override/snooze/reschedule/confirmation flows because all depend on shared primitives.
- Accessibility utility duplication risk appears both in core utility tests and custom runtime logic (`AuthProvider`).

## 5) Recommended architecture direction (first-principles)
1. **Treat `Modal` and `Drawer` as canonical interaction shells**: fix them once with a small shared focus + inert/backdrop + restore contract.
2. **Refactor `SmartCombobox` to APG combobox/listbox contract** and optional fallback where input remains focused with `aria-activedescendant`.
3. **Normalize menu semantics in `UserMenu`**: implement keyboard control + explicit close/restore behavior and preserve trigger state.
4. **Adopt `accessibility.tsx` helpers progressively**:
   - `trapFocus` for modal/drawer/open overlays
   - `handleListNavigation` + `handleActivation` for menu/combobox list navigation
   - `liveRegionProps` + lightweight result count live text for filtered combobox lists
5. **Keep changes in 1) primitives-first + 2) high-traffic consumers pass-through**, avoiding one-off fixes that bypass shared components.

## 6) Suggested implementation plan (non-blocking sequencing)
- **Phase A (required):** Modal/drawer hardening
  - body scroll lock + focus return contract
  - escape and overlay close invariants
  - focus trap on open
- **Phase B (required):** SmartCombobox accessibility upgrade
  - ARIA contract + keyboard contract + result announcement
- **Phase C (required):** UserMenu keyboard semantics and focus restoration
- **Phase D (recommended):** Remove auth-specific focus helper duplication by using shared primitive behavior or shared helper.

## 7) Validation protocol before coding done
- Unit/integration tests:
  - update/add combobox a11y and keyboard tests
  - add/extend modal tests for focus restore and Escape
  - add menu keyboard tests for `UserMenu`
- Manual validation (required):
  - keyboard-only tab/arrow through menu and combobox
  - screen-reader smoke checks
  - verify no focus leakage from modals/drawers while open

## 8) Long-term follow-up (if not fixed in this pass)
- Standardize reusable keyboard behavior with small shared hooks:
  - `useDisclosureFocus`, `useComboboxA11y`, `useMenuKeyboard`
- Track whether future feature work introduces additional popover/menu-like primitives and redirect them into existing shells.

## 9) Verdict for this audit
- This is a **canonical UX accessibility risk class** with shared-component blast radius, so fixing the primitives first is strongly preferable and lower risk than ad-hoc component patching.
- No code changes made in this pass; this is the review package only.

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
