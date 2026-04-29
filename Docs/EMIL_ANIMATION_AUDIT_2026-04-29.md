# Emil Kowalski Animation & Micro-Interaction Audit

**Date:** 2026-04-29
**Scope:** Shell, TripCard, FilterPill, FrontierDashboard, Button — plus cascading impact on all `transition-colors` consumers
**Philosophy:** Emil Kowalski — "unseen details compound into stunning"

---

## 1. Current State Summary

| Component | File | Lines | Current Transition | Has `:active`? | Has entry animation? |
|-----------|------|-------|-------------------|----------------|----------------------|
| Shell nav links | `Shell.tsx:169` | 277 | `transition-all duration-200` | ❌ | ❌ |
| Shell breadcrumb | `Shell.tsx:235` | — | `transition-colors` | ❌ | ❌ |
| FilterPill (default) | `FilterPill.tsx:56` | 81 | `transition-colors` | ❌ | ❌ |
| FilterPill (role) | `FilterPill.tsx:38` | — | `transition-all` | ❌ | ❌ |
| FilterPill font | `FilterPill.tsx:38` | — | `text-[10px]` | — | — |
| TripCard wrapper | `TripCard.tsx:222` | 414 | `transition-all duration-200 ease-out` | ❌ | ❌ |
| TripCard hover actions | `TripCard.tsx:243,390` | — | `transition-opacity` (no duration/easing) | — | — |
| Button | `button.tsx:9` | 53 | `transition-all` | ❌ | ❌ |
| FrontierDashboard | `FrontierDashboard.tsx:21` | 95 | `animate-fade-in` (not staggered) | ❌ | ❌ (bento grid only) |
| UserMenu trigger | `UserMenu.tsx:64` | 132 | `transition-colors` | ❌ | ❌ |
| UserMenu dropdown items | `UserMenu.tsx:113,122` | — | `transition-colors` | ❌ | ❌ |

---

## 2. Issue Inventory (Emil Kowalski Framework)

### Issue 1: No tactile press feedback on interactive elements

**Problem:** Every button, pill, nav link, and interactive card lacks an `:active` scale transform. The entire OS feels "static" — no physical response to clicks.

**Emil's rule:** "Add `transform: scale(0.97)` on `:active`. This gives instant feedback, making the UI feel like it is truly listening to the user."

**Files affected:**
- `Shell.tsx:169` — nav links: add `active:scale-[0.98]`
- `FilterPill.tsx:38,56` — both variants: add `active:scale-[0.97]`
- `TripCard.tsx:222` — card wrapper: add `active:scale-[0.99]` (subtle, since it's a link container)
- `button.tsx:9` — all buttons: add `active:scale-[0.97]`
- `FrontierDashboard` bento items (globals.css `.bento-item`): add `active:scale-[0.98]`
- `UserMenu.tsx:64` — trigger: add `active:scale-[0.97]`
- `UserMenu.tsx:113,122` — menu items: add `active:scale-[0.97]`

### Issue 2: `transition-all` laziness

**Problem:** Multiple components use `transition-all` instead of specifying exact properties. This is expensive (triggers paint/layout on every property) and imprecise.

**Emil's rule:** "Specify exact properties: `transition: transform 200ms ease-out`"

**Files affected:**
- `Shell.tsx:169`: `transition-all duration-200` → `transition-colors duration-150 ease-out`
- `FilterPill.tsx:38`: `transition-all` → `transition-colors duration-125 ease-out`
- `button.tsx:9`: `transition-all` → `transition-colors duration-150 ease-out` (color is the only changing property)
- `TripCard.tsx:222`: `transition-all duration-200 ease-out` → `transition-[border-color,opacity] duration-150 ease-out`

### Issue 3: Duration discipline — micro-interactions too slow

**Problem:** Current `duration-200` (200ms) across nearly all hover/click transitions. Emil's rule: hover/click should be 125-160ms.

**Emil's duration table:**
| Element | Duration |
|---------|----------|
| Button press feedback | 100-160ms |
| Tooltips, small popovers | 125-200ms |
| Dropdowns, selects | 150-250ms |
| Rule: UI under 300ms | Micro-interactions should be 125-160ms |

**Changes:**
- All `duration-200` on hover/color transitions → `duration-150` (150ms)
- FilterPill → `duration-125` (125ms — it's a small, frequent target)
- Button hover → `duration-150`
- Shell nav hover → `duration-150`

### Issue 4: Easing — standard Tailwind lacks signature

**Problem:** Project uses standard `ease-out` (cubic-bezier(0.4, 0, 0.2, 1)). This is safe but not distinctive. Emil recommends `cubic-bezier(0.23, 1, 0.32, 1)` — Strong Ease Out.

**Files affected:**
- `globals.css:114-117`: transition custom properties → add new `--ease-out-strong`
- Add to `tailwind.config.js` as `ease-out-strong`
- Replace `ease-out` with `ease-out-strong` on micro-interactions globally

**Note:** This is an opt-in, not a blanket replacement. The existing `--transition-base` (200ms, ease-out) and `--transition-slow` can coexist. Micro-interactions get the strong curve; entry/macro animations can keep the standard curve or be evaluated separately.

### Issue 5: FilterPill `text-[10px]` is illegible

**Problem:** The role variant FilterPill uses `text-[10px]` — below the 12px minimum for interactive labels in professional apps.

**File:** `FilterPill.tsx:38`: `text-[10px]` → `text-[var(--ui-text-xs)]` (12px)

### Issue 6: `animate-pulse-dot` uses standard ease

**Problem:** The status pulse animation in Shell uses simple 50% opacity keyframes with no easing. Emil says "default pulses feel 'synthetic'."

**File:** `globals.css:264-274` and `tailwind.config.js:109`: Replace with a custom cubic-bezier pulse that uses a stronger ease-out-quart feel.

```css
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
/* → custom cubic-bezier version */
```

### Issue 7: Hover-reveal actions lack proper transition properties

**Problem:** TripCard's hover-reveal actions (checkbox at line 243, quick actions at line 390) use `transition-opacity` without explicit duration and easing. Emil says duration + easing must be explicit.

**File:** `TripCard.tsx:243,390`:
- Line 243: `transition-opacity` → `transition-opacity duration-150 ease-out`
- Line 390: `transition-opacity duration-200 ease-out` → `transition-opacity duration-150 ease-out`

### Issue 8: FrontierDashboard lacks staggered entry

**Problem:** The bento grid uses `animate-fade-in` on the container, so all 4 items appear simultaneously. Emil says "stagger your entries" (30-80ms between items).

**File:** `FrontierDashboard.tsx:21`: Container animation → per-item stagger using existing `animate-stagger-container` pattern or explicit nth-child delays.

The existing `animate-stagger-container` in `globals.css:388-397` already provides this pattern with 80ms delays. Apply it to the bento grid items.

### Issue 9: No active state on Shell nav items

**Problem:** Navigation links are the most frequently clicked targets in the app. They need tactile feedback.

**File:** `Shell.tsx:169`: Add `active:scale-[0.98]` to nav link className.

### Issue 10: Trust Anchor and bento items use `transition: all`

**Problem:** `globals.css:574` (`.trust-anchor`) and `globals.css:640` (`.bento-item:hover`) use `transition: all var(--transition-base)`. Emil says be specific.

**Changes:**
- `.trust-anchor`: `transition: all var(--transition-base)` → `transition: transform var(--transition-base), border-color var(--transition-base), box-shadow var(--transition-base)`
- `.bento-item:hover`: `transition: all var(--transition-base)` → `transition: transform var(--transition-base), border-color var(--transition-base), box-shadow var(--transition-base)`

---

## 3. Implementation Plan

### Phase 1: Foundation (globals.css + tailwind.config.js)
1. Add `--ease-out-strong: cubic-bezier(0.23, 1, 0.32, 1)` to `globals.css:113-117`
2. Add `ease-out-strong` to `tailwind.config.js` transitionTimingFunction
3. Refactor `pulse-dot` keyframes to use custom cubic-bezier timing
4. Fix `.trust-anchor` and `.bento-item:hover` `transition: all` → specific properties
5. Add `active:scale-[0.98]` to `.bento-item`

### Phase 2: Input Components (button.tsx, FilterPill.tsx)
1. **button.tsx**: `transition-all` → `transition-colors duration-150 ease-out-strong`, add `active:scale-[0.97]`
2. **FilterPill.tsx**: 
   - Role variant: `transition-all` → `transition-colors duration-125 ease-out-strong`, `text-[10px]` → `text-[var(--ui-text-xs)]`, add `active:scale-[0.97]`
   - Default variant: `transition-colors` → `transition-colors duration-125 ease-out-strong`, add `active:scale-[0.97]`

### Phase 3: Navigation (Shell.tsx, UserMenu.tsx)
1. **Shell.tsx:169**: `transition-all duration-200` → `transition-colors duration-150 ease-out-strong`, add `active:scale-[0.98]`
2. **Shell.tsx:235**: breadcrumb `transition-colors` → `transition-colors duration-150 ease-out-strong`
3. **UserMenu.tsx:64**: `transition-colors` → `transition-colors duration-150 ease-out-strong`, add `active:scale-[0.97]`
4. **UserMenu.tsx:73**: chevron `transition-transform` → `transition-transform duration-150 ease-out-strong`
5. **UserMenu.tsx:113,122**: `transition-colors` → `transition-colors duration-150 ease-out-strong`, add `active:scale-[0.97]`

### Phase 4: Data Components (TripCard.tsx)
1. **TripCard.tsx:222**: `transition-all duration-200 ease-out` → `transition-[border-color,opacity] duration-150 ease-out-strong`, add `active:scale-[0.99]`
2. **TripCard.tsx:243**: `transition-opacity` → `transition-opacity duration-150 ease-out`
3. **TripCard.tsx:390**: `transition-opacity duration-200 ease-out` → `transition-opacity duration-150 ease-out`
4. **TripCard.tsx:399**: `transition-colors` → `transition-colors duration-150 ease-out-strong`

### Phase 5: Workspace (FrontierDashboard.tsx)
1. **FrontierDashboard.tsx:21**: Container `animate-fade-in` stays; add staggered entry to children using `.animate-stagger-container`
2. **FrontierDashboard.tsx:42**: sentiment bar `transition-all duration-1000` → `transition-[width] duration-1000 ease-out` (or keep as-is — it's a macro animation, not micro)

---

## 4. Cascading Impact Analysis

These changes touch foundational classes (`transition-all`, `transition-colors`, `transition-opacity` patterns) that are used broadly. The grep found **186 occurrences** across the full codebase.

**Safe to batch-replace:**
- `transition-colors` without explicit duration → add `duration-150` is safe (it's the new default duration for color transitions). But since Tailwind's `transition-colors` defaults to 150ms already, the main benefit here is adding the strong easing curve.

**Replace `transition-colors` → `transition-colors duration-150 ease-out-strong` globally:**
- This is a mechanical change. The strong easing is strictly better for hover states — it starts faster (responsive feel) and decelerates smoothly (polished settling).
- 100+ occurrences in buttons, pills, nav items, links, menu items

**Replace `transition-all` → specific properties:**
- Need to understand what properties actually change in each context
- `Shell.tsx:169`: `background` + `color` → `transition-colors`
- `button.tsx:9`: `background` + `color` → `transition-colors`
- `FilterPill.tsx:38`: `background` + `color` → `transition-colors`
- `TripCard.tsx:222`: `border-color` + `opacity` → `transition-[border-color,opacity]`
- `globals.css .trust-anchor`: `transform` + `border-color` + `box-shadow` → explicit list

**Skip for now:**
- `transition-all duration-1000` in sentiment bar (macro animation, different category)
- Form inputs with `transition-colors` (may need different treatment)
- `transition-transform` on chevrons (keep as-is, it's already specific)

---

## 5. Verification Plan

After each phase:
1. `npm run build` — must pass with zero errors
2. `npm run lint` — must pass
3. Manual verification:
   - Click buttons → feel the scale feedback
   - Hover nav items → notice faster, snappier color transitions
   - Open UserMenu → smooth easing on items
   - Hover TripCard → quick action fade-in at 150ms
   - View FrontierDashboard → staggered entry with 80ms delays
4. `prefers-reduced-motion` test: Ensure `scale()` and `translateY()` animations respect the media query (add `@media (prefers-reduced-motion: reduce)` rules where needed)

---

## 6. Before/After Reference Table

| Component | Before | After | Emil Principle |
|-----------|--------|-------|----------------|
| Button | `transition-all` | `transition-colors duration-150 ease-out-strong` | Specify exact properties; fast duration |
| Button | No `:active` | `active:scale-[0.97]` | Tactile press feedback |
| FilterPill (role) | `transition-all text-[10px]` | `transition-colors duration-125 ease-out-strong text-ui-xs` | Readable labels; fast micro-interaction |
| FilterPill (role) | No `:active` | `active:scale-[0.97]` | Tactile press feedback |
| FilterPill (default) | `transition-colors` | `transition-colors duration-125 ease-out-strong` | Strong easing for snappy feel |
| FilterPill (default) | No `:active` | `active:scale-[0.97]` | Tactile press feedback |
| Shell nav links | `transition-all duration-200` | `transition-colors duration-150 ease-out-strong` | Avoid `all`; reduce duration |
| Shell nav links | No `:active` | `active:scale-[0.98]` | Navigation items need tactile feedback |
| TripCard wrapper | `transition-all duration-200 ease-out` | `transition-[border-color,opacity] duration-150 ease-out-strong` | Specify exact properties |
| TripCard wrapper | No `:active` | `active:scale-[0.99]` | Subtle card press feedback |
| TripCard hover actions | `transition-opacity` (no duration) | `transition-opacity duration-150 ease-out` | Explicit duration on all transitions |
| .trust-anchor | `transition: all var(--transition-base)` | `transition: transform var(--transition-base), border-color var(--transition-base), box-shadow var(--transition-base)` | Never use `all` |
| .bento-item:hover | `transition: all var(--transition-base)` | Same specificity fix + `active:scale-[0.98]` | Never use `all` |
| animate-pulse-dot | Ease-in-out keyframes | Custom cubic-bezier pulse | Natural "breath" feel |
| FrontierDashboard | Single `animate-fade-in` on container | Staggered with `animate-stagger-container` | Stagger prevents visual pop |
| UserMenu trigger | `transition-colors` | `transition-colors duration-150 ease-out-strong` | Fast, snappy hover |
| UserMenu chevron | `transition-transform` | `transition-transform duration-150 ease-out-strong` | Add strong easing |
| UserMenu items | `transition-colors` | `transition-colors duration-150 ease-out-strong` + `active:scale-[0.97]` | Tactile + snappy |
| Easing system | Standard `ease-out` | Add `--ease-out-strong: cubic-bezier(0.23, 1, 0.32, 1)` | Signature "snap" curve |

---

## 7. Effort Estimate

| Phase | Files | Changes | Risk | Estimate |
|-------|-------|---------|------|----------|
| 1. Foundation | `globals.css`, `tailwind.config.js` | 3-5 declarations | Low | 15min |
| 2. Input Components | `button.tsx`, `FilterPill.tsx` | ~6 changes | Low | 10min |
| 3. Navigation | `Shell.tsx`, `UserMenu.tsx` | ~7 changes | Low | 15min |
| 4. Data Components | `TripCard.tsx` | ~4 changes | Low | 10min |
| 5. Workspace | `FrontierDashboard.tsx` | ~2 changes | Low | 10min |
| 6. Global sweep | All files with `transition-colors` | 100+ occurrences | Medium | 30min |
| **Total** | **10+ files** | **~120+ changes** | **Low-Medium** | **~90min** |

**Risk Assessment:** Low. All changes are CSS-only (no logic changes). The `active:scale` transforms and easing curve changes are purely cosmetic. The `transition-all` → specific property refactors are safe because each component only changes the specified properties.

**Rollback:** Trivial — revert the commit.
