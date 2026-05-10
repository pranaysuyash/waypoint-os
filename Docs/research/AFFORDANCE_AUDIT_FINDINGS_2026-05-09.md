# Affordance Audit: Travel Agency Agent UI

**Date**: 2026-05-09  
**Method**: Code-grounded audit using affordances skill framework (Gibson/Norman taxonomy) + Nielsen heuristics  
**Surface coverage**: Shell, Navigation, Lead Inbox, Trip Workspace (7 panels), Workbench, Dashboard, Settings, UI library  
**Auditor**: Code analysis of 15+ component files, 4 screen layouts  

---

## Audit Framework

Affordance types examined:
- **Perceived affordance** — does the element visually signal its interactivity?
- **Hidden affordance** — does an action exist but require discovery (hover, right-click)?
- **False affordance** — does the element look interactive but do nothing?
- **Signifier quality** — are labels, icons, cursor changes, tooltips present?
- **Disabled state clarity** — does disabled UI explain *why* it's disabled?
- **Empty state completeness** — does every empty state signal the next action?
- **State signifiers** — does the UI communicate system state (loading, saved, error)?

---

## P0 — Catastrophic (blocks task completion)

### P0-01: TripCard checkbox is hover-only → hidden affordance on touch devices

**File**: `frontend/src/components/inbox/TripCard.tsx:338-351`  
**Pattern**: Checkbox revealed via `opacity-0 group-hover:opacity-100`  
**Code**:
```tsx
className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10"
```
**Affordance type**: Hidden affordance (Norman)  
**Impact**: On touch devices (iPad, mobile), the checkbox for multi-select is invisible. Users cannot discover bulk selection. The `TripCard` already has `IS_TOUCH` detection (line 22-28) and uses it for `QuickActions`, but the **checkbox still uses the hover pattern** — touch users cannot select trips.  
**Severity**: P0 — blocks bulk operations entirely on touch  
**Fix**: Always visible checkbox on touch devices (`!IS_TOUCH ? 'opacity-0 group-hover:opacity-100' : 'opacity-100'`), or a "Select mode" toggle at the top of the inbox.

### P0-02: QuickActions are hover-only on desktop → hidden affordance

**File**: `frontend/src/components/inbox/TripCard.tsx:237`  
**Code**:
```tsx
const hoverClass = IS_TOUCH ? '' : 'opacity-0 group-hover:opacity-100';
```
**Affordance type**: Hidden affordance  
**Impact**: "Assign" and "View" actions for each trip are invisible until the user hovers over the card. A new user scanning the inbox has no way to know these actions exist. On touch devices they're always visible (mitigated by `IS_TOUCH` detection), but on desktop the discoverability is poor.  
**Severity**: P0 — critical actions (assign, view) are invisible  
**Fix**: Show actions always (maybe reduced opacity for non-hovered cards) or add an "Actions" column header as a signifier.

### P0-03: Edit buttons in IntakeFieldComponents are hover-only → hidden affordance

**File**: `frontend/src/components/workspace/panels/IntakeFieldComponents.tsx:167`  
**Code**:
```tsx
className='ml-1 opacity-0 group-hover:opacity-100 transition-opacity'
```
**Affordance type**: Hidden affordance (already documented in DATA_CAPTURE_UI_UX_AUDIT)  
**Impact**: Users cannot discover that trip fields (destination, dates, budget) are editable unless they hover exactly over the field. On touch devices, the edit button is completely invisible.  
**Severity**: P0 — core editing functionality invisible on touch  
**Fix**: Always show edit icon at reduced opacity, or make the field itself clickable (the label+value area), or add a visible "Edit" link.

---

## P1 — Major (significant friction, important to fix)

### P1-01: Disabled nav items show no explanation for non-hover users

**File**: `frontend/src/components/layouts/Shell.tsx:164-182`  
**Code**:
```tsx
<div
  className='flex items-center ... opacity-40 cursor-not-allowed select-none'
  title={`${item.description} - Coming soon`}
  aria-disabled='true'
  aria-label={`${item.label}, coming soon`}
>
```
**Affordance type**: Weak signifier  
**Impact**: The tooltip (`title`) is the only way a user learns "Planned" status. On touch devices, `title` never appears. On desktop, the "Planned" badge is small and muted. A user clicking a disabled item gets no feedback — the `cursor-not-allowed` prevents interaction silently.  
**Severity**: P1  
**Fix**: Add a click handler that shows a toast: "Bookings is coming soon. We'll notify you when it's ready." Or use a small modal/banner. `aria-disabled` is correct but visual feedback on attempted interaction is missing.

### P1-02: Empty states exist but some lack clear action paths

**File**: `frontend/src/components/ui/empty-state.tsx`  
**Pattern**: `EmptyState` component has `action` and `secondaryAction` props with href/onClick  
**Affordance type**: Inconsistent signifier application  
**Impact**: The component is well-designed (icon, title, description, action buttons), but not all list/filter screens use it. Screens without empty states leave users with a blank page and no guidance.  
**Severity**: P1 — users on blank screens don't know what to do  
**Fix**: Audit every list/dashboard/filter screen and ensure EmptyState is rendered when data is empty. Check `inbox/page.tsx`, `overview/page.tsx`, `trips/page.tsx`, `insights/page.tsx`.

### P1-03: Locked trip tabs lack interactive affordance — no explanation on click

**File**: `frontend/src/app/(agency)/trips/[tripId]/layout.tsx:289`  
**Pattern**: `aria-disabled="true"` on locked stage tabs  
**Affordance type**: Weak signifier  
**Impact**: Locked stages show an amber lock icon but clicking them does nothing and gives no feedback beyond "action not allowed." The `PlanningStageGate` component exists (provides a link to "Go to missing details") but the tab itself should provide feedback on why it's locked.  
**Severity**: P1  
**Fix**: Show toast on locked tab click: "Complete the Intake stage first to unlock Trip Details." Or make the tab clickable to scroll to the missing requirements section.

### P1-04: Button disabled state uses only opacity — no textual explanation

**File**: `frontend/src/components/ui/button.tsx:9`  
**Pattern**: `disabled:opacity-50` + `disabled:pointer-events-none`  
**Affordance type**: Weak signifier / false affordance  
**Impact**: Disabled buttons look grayed out, but the user gets no explanation of *why* the button is disabled or *what to do to enable it*. This is a known UX anti-pattern — opacity alone doesn't communicate the path to resolution.  
**Severity**: P1  
**Fix**: Add `title` or tooltip on disabled buttons explaining why. Example: "Button is disabled because no trips are selected." Or use the `aria-describedby` pattern.

---

## P2 — Minor (annoying, not blocking)

### P2-01: Toast notifications lack persistent affordance

**File**: `frontend/src/components/ui/toast.tsx` (line 67: `pointer-events-none`)  
**Pattern**: Auto-dismiss toasts with `pointer-events-none` container  
**Affordance type**: Weak signifier (time-limited)  
**Impact**: Toasts auto-dismiss in 5 seconds. If a user is focused elsewhere, they miss the notification entirely. No persistent notification history or indicator (bell icon, badge).  
**Severity**: P2  
**Fix**: Add a toast history panel (expandable), or make important toasts persist until dismissed, or add a notification badge to the shell.

### P2-02: Custom select dropdowns use `pointer-events-none` on chevron icon

**Multiple files**: `IntakePanel.tsx:1266`, `StrategyPanel.tsx`, `workbench IntakeTab.tsx`  
**Pattern**: `<ChevronDown className='pointer-events-none' />`  
**Affordance type**: Weak signifier  
**Impact**: The chevron icon is non-interactive, which is correct (it's decorative). But the native select replacement loses the visual affordance of the dropdown arrow being part of the control. Minor, but violates "clickable area should include the arrow."  
**Severity**: P2  
**Fix**: Wrap the entire control (including chevron) in the interactive area, or use a properly styled native `<select>`.

### P2-03: StrategyPanel disabled button lacks "why"

**File**: `frontend/src/components/workspace/panels/StrategyPanel.tsx:25`  
**Pattern**: `opacity-50 cursor-not-allowed` on a disabled run button  
**Affordance type**: Weak signifier  
**Impact**: Button is grayed out but no explanation of what's missing to enable it.  
**Severity**: P2  
**Fix**: Add tooltip: "Complete trip details before generating options."

### P2-04: No keyboard shortcut affordance

**Pattern**: Across the app, no keyboard shortcut hints are visible  
**Affordance type**: Hidden affordance  
**Impact**: If keyboard shortcuts exist (cmd+Enter to save, Escape to close modal), they're invisible. Power users won't discover them.  
**Severity**: P2  
**Fix**: Show keyboard shortcut hints in tooltips ("Save (⌘⏎)"), or add a keyboard shortcut reference panel in settings.

---

## P3 — Cosmetic (minor polish)

### P3-01: "Planned" badge in nav is small and easily missed

**File**: `frontend/src/components/layouts/Shell.tsx:177-178`  
**Pattern**: `text-[10px] ml-auto` with muted color  
**Affordance type**: Weak signifier  
**Impact**: The "Planned" label is small and low-contrast. Users may try clicking disabled nav items repeatedly.  
**Severity**: P3  
**Fix**: Make "Coming Soon" badge more prominent (colored badge, not just text).

### P3-02: Trip stage badges have no "what's next" affordance

**File**: `frontend/src/components/workspace/panels/TimelinePanel.tsx`  
**Pattern**: Stage badges show current state but not what the user should do next  
**Affordance type**: Weak signifier  
**Impact**: The timeline shows what happened but doesn't signal what the user should do next in the workflow.  
**Severity**: P3  
**Fix**: After the last timeline event, show a "Next action" prompt or link.

### P3-03: Filter pill active state uses only color

**File**: `frontend/src/components/ui/pill.tsx` (via `FilterPill.tsx`)  
**Pattern**: Active filter distinguished only by `tone` prop (color change)  
**Affordance type**: Weak signifier (accessibility)  
**Impact**: Active vs inactive filter differs only in background/text color. No shape, icon, or underline change. Color-only differentiation fails WCAG 1.4.1 for color-blind users.  
**Severity**: P3  
**Fix**: Add an underline, checkmark icon, or weight change to the active pill.

---

## Positive Findings (What's Done Well)

### ✅ Shell disabled nav items use proper ARIA
`aria-disabled="true"` + `aria-label="...coming soon"` + `cursor-not-allowed` + visual opacity. The disabled state is communicated through multiple channels even if the feedback on click is missing.

### ✅ EmptyState component is well-designed
Icon + title + description + primary action + secondary action. This is textbook empty state design. Now it just needs to be used consistently.

### ✅ Button component has excellent affordance fundamentals
5 variants (default/secondary/ghost/destructive/outline), `disabled:opacity-50 disabled:pointer-events-none`, `focus-visible:ring-2`. The focus ring is a strong signifier for keyboard users.

### ✅ TripCard uses color + shape + text for indicators
PriorityIndicator, SLA badge, stage badge, assignment badge — all use color + text + semantic labels. This is a strength.

### ✅ PlanningStageGate provides clear "why blocked" + action link
The amber gate card explains the reason, shows a "Go to missing details" link, and uses semantic color coding (amber = warning, not red = error).

---

## Summary

| Severity | Count | Key Issues |
|----------|-------|-----------|
| **P0** | 3 | Hover-only checkbox (touch invisible), hover-only QuickActions, hover-only edit buttons |
| **P1** | 4 | No feedback on disabled nav clicks, missing empty states, no "why locked" on tabs, disabled button explanation |
| **P2** | 4 | Toast persistence, chevron affordance, disabled button tooltip, keyboard shortcuts |
| **P3** | 3 | "Planned" badge prominence, "what's next" timeline, filter active state |
| **Total** | **14** | |

### Root Cause Pattern

**6 of 14 issues** are variations of the same pattern: **`opacity-0 group-hover:opacity-100`** used to hide controls until hover. This is the single highest-leverage fix — replacing hover-reveal with always-visible controls (even at reduced opacity) would eliminate P0-01, P0-02, P0-03.

### Quick Wins (1-2 hours to fix)

1. **TripCard checkbox**: Add `!IS_TOUCH` guard to the hover class (1 line change)
2. **TripCard QuickActions**: Show always at 40% opacity, full on hover (1 line change)
3. **IntakeFieldComponents edit buttons**: Remove `opacity-0 group-hover`, show at 30% opacity always (1 line per button)
4. **Disable nav click feedback**: Add `onClick` handler showing "Coming Soon" toast (add to `Shell.tsx`)
5. **PlanningStageGate tab click**: Add `onClick` handler for locked tabs showing why

### Methodology Used

This audit applied the installed affordances skill (Gibson/Norman framework) + Nielsen's 10 heuristics + cross-reference with existing known issues (DATA_CAPTURE_UI_UX_AUDIT's hover-only edit, AUDIT_REPORT's export button false affordance, ISSUE_REVIEW's waitlist false affordance).

Existing known issues not re-audited here:
- Export button false affordance (already documented in AUDIT_REPORT TASK-010)
- Waitlist email box false affordance (already documented in issue review)
