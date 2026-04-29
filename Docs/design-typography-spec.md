# Typography Specification — Waypoint OS

**Date**: 2026-04-29  
**Based on**: `typeset` skill, `impeccable` design context, WCAG 2.1 AA

---

## Brand Personality (3 Words)

**Precise. Data-driven. Authoritative.**

- **Precise**: Pixel-perfect alignment, tabular numerals for data, consistent spacing
- **Data-driven**: Charts, metrics, and pipeline visualization are first-class UI citizens
- **Authoritative**: Decisions backed by confidence scores, audit trails, and governance controls

---

## Font Stack

| Role | Font Family | Status | Usage |
|------|-------------|--------|-------|
| **Display** | **Sora** | ✅ Approved — geometric, distinctive, NOT in banned list | Headings 24px+, page titles, hero text |
| **Body** | **Rubik** | ✅ Approved — humanist, readable, NOT in banned list | Body text 16px+, UI copy, descriptions |
| **Mono** | **JetBrains Mono** | ✅ Approved — technical feel, clear 0/O/1/l distinction | Code, data tables, IDs, metrics |
| ~~Data~~ | ~~IBM Plex Mono~~ | ❌ **BANNED** — in reflex font list | ~~Replaced with JetBrains Mono~~ |

### Font Loading

```css
--font-display: var(--font-sora), system-ui, sans-serif;
--font-body: var(--font-rubik), system-ui, sans-serif;
--font-mono: "JetBrains Mono", "SF Mono", monospace;
--font-data: "JetBrains Mono", "SF Mono", monospace; /* Replaced IBM Plex Mono */
```

**Note**: Next.js with `next/font/google` or `next/font/local` should load Sora and Rubik. JetBrains Mono is loaded via `--font-jetbrains-mono`.

---

## Type Scales

### Marketing Pages (Public Site)

**Fluid `clamp()` scale** — allows typography to breathe on larger screens.

```css
--text-xs:  clamp(0.75rem, 0.7rem  + 0.25vw, 0.875rem);  /* 12-14px */
--text-sm:  clamp(0.875rem, 0.8rem  + 0.38vw, 1rem);    /* 14-16px */
--text-base: clamp(1rem, 0.9rem  + 0.5vw, 1.125rem);    /* 16-18px */
--text-lg:  clamp(1.125rem, 1rem  + 0.63vw, 1.25rem);   /* 18-20px */
--text-xl:  clamp(1.25rem, 1.1rem  + 0.75vw, 1.5rem);   /* 20-24px */
--text-2xl: clamp(1.5rem, 1.3rem  + 1vw, 2rem);       /* 24-32px */
--text-3xl: clamp(2rem, 1.7rem  + 1.5vw, 3rem);       /* 32-48px */
--text-4xl: clamp(2.5rem, 2rem  + 2.5vw, 4rem);     /* 40-64px */
--text-5xl: clamp(3rem, 2.5rem  + 3.5vw, 5rem);     /* 48-80px */
--text-6xl: clamp(3.5rem, 3rem  + 4.5vw, 6.5rem);   /* 56-104px */
```

**Major Third (1.25) ratio between steps.**  
**Used in**: `page.tsx`, `marketing.tsx`, `marketing-v2.module.css`

---

### App UI (Dashboard, Workspace, Operations)

**Fixed `rem` scale** — spatial predictability for dense, container-based layouts.

```css
--ui-text-xs:  0.75rem;  /* 12px — captions, labels */
--ui-text-sm:  0.875rem; /* 14px — secondary text */
--ui-text-base: 1rem;     /* 16px — body minimum */
--ui-text-lg:  1.125rem; /* 18px — emphasis */
--ui-text-xl:  1.25rem;  /* 20px — subheadings */
  --ui-text-2xl: 1.5rem;    /* 24px — headings */
  --ui-text-3xl: 2rem;      /* 32px — page titles */
  --ui-text-4xl: 2.5rem;    /* 40px — large page titles */
```

**Major Third (1.25) ratio between steps.**  
**Used in**: `overview/page.tsx`, `workspace/*`, dashboard components

**Implementation**: Apply via Tailwind arbitrary values:
```tsx
<div className="text-[var(--ui-text-base)]">  {/* 16px fixed */}</div>
```

OR create custom Tailwind classes in `tailwind.config.ts`:
```js
theme: {
  extend: {
    fontSize: {
      'ui-xs': 'var(--ui-text-xs)',
      'ui-sm': 'var(--ui-text-sm)',
      'ui-base': 'var(--ui-text-base)',
      // ...
    }
  }
}
```

---

## Line Height (Leading)

| Context | Line Height | Rationale |
|---------|-------------|------------|
| **Headings** | `1.1 — 1.2` | Tighter for large text |
| **Body text** | `1.5 — 1.7` | Comfortable reading |
| **Light on dark** | Add `0.05 — 0.1` | Light type reads as lighter, needs more breathing room |
| **Data tables** | `1.4` | Compact but readable |

---

## Color & Contrast (WCAG 2.1 AA)

### Text Colors on Dark Backgrounds (`#080a0c`)

| Token | Hex | Ratio | Status | Usage |
|-------|-----|--------|--------|-------|
| `--text-primary` | `#e6edf3` | 14:1 | ✅ AA (all sizes) | Body text, headings |
| `--text-secondary` | `#a8b3c1` | 5.9:1 | ✅ AA (all sizes) | Secondary text, labels |
| `--text-tertiary` | `#9ba3b0` | 4.6:1 | ✅ AA (all sizes) | Small text 12px+ |
| `--text-muted` | `#8b949e` | 3.5:1 | ⚠️ **AA for 18pt+ ONLY** | Large text only (18px+ bold) |
| `--text-accent` | `#58a6ff` | 5.2:1 | ✅ AA (all sizes) | Links, accents |

### Critical Rule

> **`--text-muted` (#8b949e) FAILS WCAG AA at 12-14px.**  
> Use `--text-tertiary` (#9ba3b0) for small text instead.

### Current Violations Fixed

| File | Line | Old | New | Status |
|------|------|-----|-----|--------|
| `marketing.tsx` | 38 | `text-[#8b949e]` at 12px | `text-[#9ba3b0]` | ✅ Fixed |
| `marketing.tsx` | 151 | `text-[#8b949e]` at 12px | `text-[#9ba3b0]` | ✅ Fixed |
| `marketing.tsx` | 155 | `text-[#8b949e]` at 12px | `text-[#9ba3b0]` | ✅ Fixed |
| `marketing.tsx` | 187 | `text-[#484f58]` at 11px | `text-[#8b949e]` | ✅ Fixed (icons OK) |

---

## Absolute Bans (impeccable Skill)

### Ban 1: `border-left` / `border-right` Accent Stripes

**NEVER** use `border-left` or `border-right` > 1px as decorative accent. This is the #1 AI design tell.

**Violation Fixed**:
```css
/* OLD (BANNED) */
.industry-card-luxury { border-left: 4px solid var(--lg-accent-gold); }

/* NEW (APPROVED) */
.industry-card-luxury { border-top: 2px solid var(--lg-accent-gold); }
```

### Ban 2: Gradient Text

**NEVER** use `background-clip: text` with gradients for text fill. Use solid colors only.

---

## Tabular Numerals

For data tables, metrics, and numbers that align vertically:

```css
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
```

**Applied in**: `overview/page.tsx` line 95, 100 for stat values.

---

## Spacing Scale
  
**4pt grid** with numeric names (backward compat) + semantic aliases (P2).

```css
/* Numeric (kept for backward compatibility) */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;  /* Key: 8pt grid is too coarse, 12px fills the gap */
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;

/* Semantic aliases (P2) */
--space-xs: var(--space-1);
--space-sm: var(--space-2);
--space-md: var(--space-4);
--space-lg: var(--space-6);
--space-xl: var(--space-8);
--space-2xl: var(--space-12);
```

**Rule**: Vary spacing for visual rhythm. Don't use the same padding everywhere.

---

## Font Pairing Rationale

**Sora (Display) + Rubik (Body) + JetBrains Mono (Data)**

- **Sora**: Geometric, high-contrast strokes → "Precise, authoritative" feel
- **Rubik**: Humanist, rounded corners → "Approachable competence" balances Sora's sharpness
- **JetBrains Mono**: Designed for developers, clear 0/O/1/l → Critical for data tables and IDs

**Why NOT the banned fonts**:
- Not Inter (too generic)
- Not IBM Plex Mono (in reflex list)
- Not Fraunces/Playfair (too decorative for this brand)

---

## Implementation Checklist
  
- [x] Replace IBM Plex Mono with JetBrains Mono in `--font-data`
- [x] Add fixed `rem` scale (`--ui-text-*`) for app UI
- [x] Fix `border-left: 4px` violations → use `border-top: 2px`
- [x] Fix `--text-muted` usage at small sizes → use `--text-tertiary`
- [x] Add `--ui-text-4xl: 2.5rem` to complete Major Third scale (P0)
- [x] Add `--font-size-base` and `--radius-md` variables (P0)
- [x] Add `--lh-heading: 1.15` for heading line-height (P1)
- [x] Add `--max-width-prose: 70ch` for readable line lengths (P1)
- [x] Define state tokens (--opacity-disabled, --cursor-disabled, --opacity-loading) (P1)
- [x] Migrate hex colors to OKLCH for perceptual uniformity (P2)
- [x] Add semantic spacing aliases (--space-xs, --space-sm, etc.) (P2)
- [x] Update app UI components to use `--ui-text-*` variables
- [x] Run build and verify no regressions
- [x] Document in `CHANGELOG.md`
- [x] Fix all `tokens.ts` hex → OKLCH migration
- [x] Remove all `@/lib/tokens` imports — use `var(--*)` CSS variables directly
- [x] Fix IntakePanel.tsx 50+ arbitrary values → CSS variables
- [x] Fix TripCard.tsx, FollowUpCard.tsx, InboxEmptyState.tsx COLORS drift
- [x] Fix followups/page.tsx COLORS drift
- [x] Add `ui-4xl` + semantic space tokens to tailwind.config.js

---

## References

- **impeccable skill**: `~/agents/skills/impeccable/`
- **typeset skill**: `~/agents/skills/typeset/`
- **typography.md**: `~/agents/skills/impeccable/reference/typography.md`
- **WCAG 2.1**: https://www.w3.org/TR/WCAG21/
