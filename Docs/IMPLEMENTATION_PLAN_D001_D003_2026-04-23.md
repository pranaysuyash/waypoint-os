# Implementation Plan: D-001 + D-003

**Date**: 2026-04-23
**Scope**: Remove card left-border accents (AI slop) + Add table view toggle to Workspace

---

## D-001: Remove Card Left-Border Accents

### Problem
`.data-card-accent` CSS class and `CardAccent` component implement colored left-border on cards — AI slop pattern #8. Creates visual noise. Status is already communicated via badge.

### Verification
- Searched codebase: `CardAccent` and `data-card-accent` are **only defined, never imported or used**
- Safe to remove with zero blast radius

### Changes
1. **Delete** `.data-card-accent` and `.data-card-accent::before` rules from `globals.css` (lines 361-375)
2. **Delete** `CardAccentProps` interface and `CardAccent` function from `card.tsx` (lines 106-128)
3. **Delete** `COLORS` import from `card.tsx` (now unused)

### Tests
- Run `npm run test` (vitest) — verify no regressions
- Run `npm run build` — verify no TypeScript errors

---

## D-003: Add Table View Toggle to Workspace

### Problem
Workspace page only shows card grid. Operators need to scan 20-50 trips quickly. Cards are low-density. No sorting/filtering.

### Solution
Add card/table view toggle with:
1. **View toggle** (icon buttons in header): Card view (default) / Table view
2. **Table view**: Dense rows with destination, type, state, age, id columns
3. **Sorting**: By state (blocked first), destination, age, type
4. **Blocked trip prominence**: Blocked trips always sort to top
5. **Persist view preference**: `localStorage` key `waypoint:workspace:view`

### Changes
1. **Modify** `workspace/page.tsx`:
   - Add `viewMode` state (`'card' | 'table'`)
   - Add `sortBy` state (`'state' | 'destination' | 'age' | 'type'`)
   - Add `sortDirection` state (`'asc' | 'desc'`)
   - Add view toggle buttons (header)
   - Add sort dropdown (header)
   - Add `WorkspaceTable` component
   - Promote blocked trips in sort logic

2. **New file** `workspace/WorkspaceTable.tsx`:
   - Table component with sortable headers
   - Responsive: horizontal scroll on mobile
   - Accessible: proper `<table>` markup, scope attributes

### Tests
- Run `npm run test` — existing tests pass
- Manual verification: toggle between views, sort by each column, verify blocked trips on top
- Build check: `npm run build`

---

## Implementation Order

1. D-001 first (small, zero risk, cleans up code)
2. D-003 second (builds on clean state)
3. Run tests after each
4. Review cycle
5. Document handoff
