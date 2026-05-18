# Trips Long-List Rail Layout Decision (2026-05-18)

## Problem

During long trip/workspace scrolling, the right rail ended early relative to the
main column, leaving a large visually dead area on the right side.

## Decision

Keep the rail visible and intentional by making it sticky within the page flow:

- Enable sticky rail on large layouts
- Anchor at top offset (`top-5`)
- Keep rail bounded to viewport via `max-h-[calc(100vh-140px)]`
- Preserve existing rail content and controls (no duplication)

## Why this behavior

- Least disruptive layout-only fix
- Maintains operator access to timeline suggestions while scrolling long content
- Avoids broad redesign or backend/data changes
- Keeps current interaction model and routes intact

## Scope boundary

- No backend changes
- No route changes
- No trip card redesign
- No data model changes
