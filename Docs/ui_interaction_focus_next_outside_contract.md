# UI Interaction Contract: `focusNextOutside`

## Purpose

`focusNextOutside` is the canonical helper for moving keyboard focus from a closed popup surface back into the surrounding page flow.

## Contract

- File: `frontend/src/lib/accessibility.tsx`
- Function: `focusNextOutside(container, { from?, fallbackFrom? })`
- Use when:
  - a popup/listbox/modal-adjacent surface handles `Tab` as an exit action
  - focus must continue in DOM order to the next focusable control outside the surface
- Inputs:
  - `container`: root node of the interactive surface to escape from
  - `from`: explicit preferred anchor (typically current focused element)
  - `fallbackFrom`: safe fallback anchor when `from` is not reliable
- Behavior:
  1. If `from` exists, use it; otherwise use `fallbackFrom`.
  2. If no usable anchor is available in this step, fall back to the last focusable
     element inside the container.
  3. Move to the first focusable node after the anchor that is outside `container`.
  4. If none exists at all, blur the anchor.

## Required Usage Pattern (before `Tab` close/escape)

- `TripCard`, `ComposableFilterBar`, `UserMenu`, and `SmartCombobox` should continue to call this helper instead of implementing local scan logic.
- This keeps behavior deterministic across overlays and avoids nested duplicate scan logic.

## Anti-patterns

- Scanning `querySelectorAll` directly inside each component.
- Calling `focus()` on fixed node IDs without validating membership in `container`.
- Failing to provide `fallbackFrom` when event timing can make `from` stale.

## Validation Note

- Add targeted regression tests in `frontend/src/lib/__tests__/accessibility.test.tsx` for:
  - anchored escape from inside container
  - fallback scan behavior
  - no-outside-target blur fallback
