# Design Audit Findings Report
**Project:** Travel Agency Agent (Waypoint OS)  
**Date:** 2026-04-29  
**Audit Type:** Visual Design Quality (Findings Only)  
**Scope:** Frontend UI code at `/frontend/src/`

---

## Executive Summary

The project has a well-defined dual-theme design system (Cartographic Dark + Minimalist Document) documented in two DESIGN.md files, with an active OKLCH color migration in `globals.css`. However, implementation shows significant drift from design specs:

- **Tailwind config is incomplete**: Uses CSS variables but missing extended config from DESIGN.md (full spacing, font sizes, shadows)
- **No shadcn/ui initialization**: Components exist in `components/ui/` but `components.json` is missing
- **Widespread hardcoded values**: Hex codes and arbitrary Tailwind values are used instead of design tokens
- **Deprecated files present**: `.bak` files indicate incomplete cleanup
- **Marketing pages use isolated CSS modules**: Hardcoded values separate from the Tailwind/token system
- **Inline styles are common**: Workspace panels use hardcoded colors instead of token references

**Overall Assessment**: The design system has strong documentation but inconsistent implementation, with moderate-to-severe visual drift in operational components.

---

## Visual Inconsistency Findings

### 1. Color Mismatches vs Design Specs
| Component | Current Implementation | DESIGN.md Spec | Status |
|-----------|---------------------|-------------------|--------|
| `Card.tsx` default/bordered border | `border-highlight` (#1c2128) | `border-default` (#30363d) | ❌ Mismatch |
| `TripCard.tsx` priority bar | Inline `COLORS` from tokens.ts (hex) | CSS variables per DESIGN.md | ⚠️ Inline vs token |
| `IntakePanel.tsx` edit states | Arbitrary `border-[#58a6ff]` | `border-accent-blue` token | ❌ Hardcoded |
| `Badge.tsx` variants | Uses `badge-explicit-user` CSS classes | Should use token references | ⚠️ Mixed approach |
| `marketing.module.css` | Hardcoded hex (#9ba3b0, #e6edf3) | CSS variables from globals.css | ❌ Isolated system |

### 2. OKLCH Migration Incompleteness
- `globals.css` uses OKLCH for all color variables (per P2 migration)
- `tokens.ts` still uses hardcoded hex values (not synced with OKLCH)
- Components like `TripCard.tsx` import `COLORS` from `tokens.ts` (hex) instead of using CSS variables

### 3. State Color Application
- `IntakePanel.tsx` uses inline `bg-[#3fb950]` (accent green) instead of `bg-accent-green`
- `TimelinePanel.tsx` uses `bg-[rgb(var(--accent-blue-rgb)/0.06)]` which is correct, but inconsistent with other panels
- Active tab in `Tabs.tsx` uses `text-text-primary` which is correct, but inactive tabs use `text-text-muted` instead of `text-text-secondary`

---

## Spacing & Layout Issues

### 1. Spacing Token Compliance
| Location | Current Value | Token Equivalent | Compliance |
|----------|---------------|-------------------|-------------|
| `TripCard.tsx` padding | `p-4` (16px) | `space-4` | ✅ Correct |
| `IntakePanel.tsx` field gaps | `gap-3` (12px) | `space-3` | ✅ Correct |
| `IntakePanel.tsx` section gaps | `gap-4` (16px) | `space-4` | ✅ Correct |
| `TripCard.tsx` metric row | `my-3` (12px) | `space-3` | ✅ Correct |
| `marketing.module.css` | Hardcoded `gap: 24px` | `space-6` (24px) | ⚠️ Not using token |

### 2. Layout Misalignments
- **Max-width mismatch**: `marketing.module.css` `.shell` uses `1320px` (matches DESIGN.md marketing spec), but `tailwind.config.js` defines `app: '1400px'` (correct for app)
- **Column count exceedance**: `IntakePanel.tsx` uses `lg:grid-cols-6` (6 columns) which exceeds DESIGN.md's 3-column max for app UI
- **Marketing breakpoints**: `marketing.module.css` has custom media queries (`max-width: 1100px`, `720px`) separate from Tailwind's breakpoint system

### 3. Responsive Behavior
- Tailwind config uses default breakpoints which match DESIGN.md (sm: 640px, md: 768px, etc.)
- `Shell.tsx` sidebar correctly collapses to 72px on mobile, expands to 220px on desktop
- TripCard grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`) matches DESIGN.md spec

---

## Typography & Hierarchy Problems

### 1. Font Size Token Discrepancy
| Token | DESIGN.md Spec | globals.css Token | Component Usage | Status |
|-------|----------------|-------------------|-----------------|--------|
| xs (10px) | 10px | `--ui-text-xs: 0.75rem` (12px) | `TripCard.tsx` uses `text-[10px]` | ❌ 10px vs 12px mismatch |
| sm (14px) | 14px | `--ui-text-sm: 0.875rem` (14px) | `IntakePanel.tsx` uses `text-ui-sm` | ✅ Correct |
| base (16px) | 16px | `--ui-text-base: 1rem` (16px) | `globals.css` body uses `var(--text-base)` | ✅ Correct |

### 2. Typography Hierarchy Issues
- **Missing token usage**: `TripCard.tsx` StageBadge uses `text-[10px]` instead of `--ui-text-xs` token
- **Inline font sizes**: `IntakePanel.tsx` uses `text-[11px]` in multiple places, which isn't in the token scale
- **Font weight consistency**: Buttons use `font-medium` (500) correctly, but some labels use `font-bold` (700) incorrectly for non-heading text
- **Line height**: `globals.css` body `line-height: 1.65` matches DESIGN.md (1.5-1.82), but some components use `leading-tight` (1.25) correctly for headings

### 3. Font Family Implementation
- `globals.css` correctly defines `--font-display: var(--font-sora)` and `--font-body: var(--font-rubik)`
- `tokens.ts` `FONT_FAMILY` uses `var(--font-display)` etc. which is correct
- Components like `Button.tsx` use `text-[var(--ui-text-sm)]` which inherits font family correctly

---

## Component Usage Analysis

### 1. Existing Components (components/ui/)
| Component | Status | Notes |
|-----------|--------|-------|
| `Button.tsx` | ✅ Good | Uses `cva` with variants, matches DESIGN.md specs |
| `Card.tsx` | ⚠️ Border issue | Variants exist, but border uses `highlight` instead of `default` |
| `Tabs.tsx` | ✅ Good | Implements keyboard navigation, ARIA attributes |
| `Badge.tsx` | ✅ Good | Uses `cva` with authority variants |
| `Select.tsx` | ✅ Good | Radix-based select component |
| `Textarea.tsx` | ✅ Good | Standard textarea with design tokens |
| `Input.tsx` | ✅ Good | Standard input with design tokens |
| `Loading.tsx` | ✅ Good | Loading spinner component |
| `Icon.tsx` | ✅ Good | Lucide icon wrapper |
| `SmartCombobox.tsx` | ✅ Good | Custom combobox for destinations/types |

### 2. Missing Components
| Component | Priority | Reason |
|-----------|----------|--------|
| `Skeleton.tsx` | Medium | DESIGN.md mentions loading skeleton states |
| `Tooltip.tsx` | Low | DESIGN.md mentions evidence tooltips |
| `DatePicker.tsx` | Low | Used in forms but not present |
| `components.json` | High | Required for shadcn/ui management, missing entirely |

### 3. Deprecated Files (Should Be Archived/Deleted)
- `/frontend/src/components/marketing/marketing.bak.tsx`
- `/frontend/src/components/marketing/marketing.bak.module.css`
- `/frontend/src/app/page.bak.tsx`

### 4. Component Inconsistencies
- **Card variant border**: `Card.tsx` applies `border-highlight` for default/bordered variants, but DESIGN.md specifies `border-default`
- **Badge usage**: `IntakePanel.tsx` doesn't use the `Badge` component, instead uses inline styles for state badges
- **Button sizes**: `Button.tsx` uses `h-8` (32px) for default, which matches DESIGN.md md size, but `sm` is `h-7` (28px) which is correct

---

## AI Slop Pattern Detection

### 1. Hardcoded Value Overuse
- **IntakePanel.tsx**: 50+ instances of arbitrary Tailwind values (`bg-[#0f1115]`, `border-[#58a6ff]`, `text-[#3fb950]`)
- **TripCard.tsx**: Inline styles using `COLORS` from tokens.ts instead of CSS variables
- **marketing.module.css**: 2000+ lines of hardcoded hex values instead of design tokens

### 2. Repetitive Code Patterns
- **IntakePanel.tsx EditableField**: Repeated code blocks for different field types (destination, type, party, etc.) that could be consolidated
- **Inline style objects**: Frequent `style={{ color: meta.color, background: meta.bg }}` patterns instead of using component variants

### 3. Generic AI-Generated Patterns
- **Marketing CSS module**: Large, monolithic CSS file with no apparent structure or token alignment (classic AI-generated CSS dump)
- **Deprecated file remnants**: `.bak` files indicate rushed generation without cleanup
- **Mixed import patterns**: Some components use `@/lib/utils` for `cn`, others use direct Tailwind classes inconsistently

### 4. Design System Violations
- Arbitrary Tailwind values (`bg-[#...]`, `text-[#...]`) instead of using predefined colors in `tailwind.config.js`
- Inline styles instead of component variants (e.g., `IntakePanel.tsx` edit buttons use `bg-[#3fb950]` instead of `bg-accent-green`)
- No usage of `cva` (class-variance-authority) outside of Button, Card, Tabs, Badge - other components use inline styles

---

## Recommended Actions (Prioritized)

### High Priority (Blocking Design System Coherence)
1. **Delete/archive .bak files**  
   - Remove `marketing.bak.tsx`, `marketing.bak.module.css`, `page.bak.tsx` to clean deprecated code

2. **Create components.json**  
   - Initialize shadcn/ui properly to enable component management  
   - Run `npx shadcn@latest init` in `/frontend` directory

3. **Replace hardcoded marketing CSS**  
   - Migrate `marketing.module.css` values to use CSS variables from `globals.css`  
   - Example: Replace `#9ba3b0` with `var(--text-tertiary)`

4. **Sync tokens.ts with OKLCH**  
   - Update `tokens.ts` to use OKLCH values matching `globals.css` or remove tokens.ts and use CSS variables directly

### Medium Priority (Fixing Inconsistencies)
5. **Fix Card border color**  
   - Update `Card.tsx` to use `border-border-default` instead of `border-highlight` per DESIGN.md

6. **Replace arbitrary Tailwind values**  
   - Audit `IntakePanel.tsx`, `TripCard.tsx`, `TimelinePanel.tsx` for `bg-[#...]`, `border-[#...]`, `text-[#...]`  
   - Replace with token references: `bg-surface`, `border-accent-blue`, `text-text-primary`

7. **Consolidate EditableField**  
   - Refactor `IntakePanel.tsx` to reduce repetitive code for field editing

8. **Use existing Badge component**  
   - Update `IntakePanel.tsx` to use `Badge` component instead of inline styles for state badges

### Low Priority (Polish & Alignment)
9. **Resolve typography token discrepancy**  
   - Align 10px (DESIGN.md xs) vs 12px (globals.css `--ui-text-xs`) for consistency

10. **Add missing components**  
    - Implement `Skeleton.tsx` and `Tooltip.tsx` if needed per DESIGN.md

11. **Unify marketing styles**  
    - Migrate `marketing.module.css` to Tailwind classes or add CSS variables to the module

12. **Audit all inline styles**  
    - Replace inline `style={{}}` objects with component variants or token references

---

*Audit completed on 2026-04-29. No code changes were made. This report documents findings only per audit constraints.*
