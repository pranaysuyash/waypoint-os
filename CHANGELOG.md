# Changelog

All notable changes to Waypoint OS are documented in this file.

## [Unreleased]

### Platform Hardening & Findings Remediation (2026-09-14)
- **RAG Semantic Provider Abstraction**: Added `EmbeddingProvider` protocol, `HashEmbeddingProvider` (deterministic local), and `SemanticEmbeddingProvider` (OpenAI adapter) in `src/rag/embeddings.py` (FND-0018).
- **Motto Doctrine Re-homing**: Consolidated legacy `motto_v4.md` references into canonical `Docs/FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md` with zero dangling references verified via `scripts/check_dangling_docs.py` (FND-0024 / FND-0208).
- **Frontend API Client & Bare Fetch Banning**: Configured ESLint rule `no-restricted-globals` in `frontend/eslint.config.mjs` banning raw `fetch()` calls in components and establishing `frontend/src/lib/api-client.ts` as canonical data layer (FND-0021 / FND-0202).
- **Documentation Tree Authority**: Formally reconciled `frontend/docs/` as legacy spec tree under `Docs/` canonical authority per R-09 / A-07 (FND-0009 / FND-0023 / FND-0204).
- **Corporate Policy Authentication**: Enforced JWT-based auth dependencies (`get_current_agency_id`, `get_current_membership`, `get_current_user`) on corporate policy routes with multi-tenant isolation (FND-0117).
- **Colloquial Intake & Hinglish Routing**: Upgraded party size and origin extraction in `src/intake/extractors.py` handling partner phrasing, Hindi numerals, and origin-destination disambiguation (FND-0287 / FND-0288).
- **Perishable Sentinel**: Centralized tracking and financial exposure auditing for visas, ticketing limits, CFAR 14d, supplier deposits, and hotel cutoffs in `src/monitoring/perishable_sentinel.py` (FND-0051 / FND-0231).
- **Poisoned Requeue Queue Inspection**: Added secret redaction, DLQ mirroring, and replay management to `agent_requeue_jobs.py` and `DLQInspector` (FND-0044 / FND-0224).

### System & Security Hardening (2026-09-04)
- **Optimistic Concurrency & Replay Protection**: Added versioned optimistic locking (`expected_version`) and idempotency cache to `price_lock.py` (FND-0038 / FND-0218).
- **Public Proposals Security**: Replaced unbounded in-memory tokens with HMAC v2 capability tokens, cryptographic TTL expiration, and file-locked revocation store in `public_proposals.py` (FND-0039 / FND-0219).
- **Audit & Identity Consolidation**: Consolidated audit bridge into SQL `AuditStore`, unified team membership under `membership_service`, and bound `VisionClient` protocol (FND-0020 / FND-0201).
- **Edge Proxy Standardization**: Restored canonical Next.js middleware proxy in `frontend/src/middleware.ts` (FND-0028 / FND-0207).

### Design System Completeness (2026-04-29)

#### P0 - Critical Fixes
- **Added `--font-size-base: var(--text-base)`** (globals.css:87) — fixes undefined variable reference
- **Added `--radius-md: 8px`** (globals.css:88) — fixes undefined variable in accessibility utilities
- **Added `--ui-text-4xl: 2.5rem`** (globals.css:111) — completes Major Third (1.25) scale for App UI (40px page titles)
- **Fixed `--text-tertiary` typo** (was `--text-tertiary` at line 19) — now consistent across all references

#### P1 - Important Tokens
- **Added `--lh-heading: 1.15`** (globals.css:172) — tokenizes heading line-height per typeset spec
- **Added `--max-width-prose: 70ch`** (globals.css:173) — enforces readable line length (45-75ch ideal)
- **Added state tokens** (globals.css:174-177):
  - `--opacity-disabled: 0.5` + `--cursor-disabled: not-allowed` for disabled states
  - `--opacity-loading: 0.6` for loading state indicators

#### P2 - Nice to Have
- **OKLCH migration** (50+ color values) — migrated from hex to `oklch()` for perceptual uniformity:
  - Backgrounds: `--bg-*` (hue 260°, chroma 0.008-0.02)
  - Text: `--text-*` (hue 260°, chroma 0.006-0.012)
  - Accents: `--accent-*` (hues 155°, 80°, 25°, 265°, 295°, 210°, 50°)
  - Geographic: `--geo-*` (hues 260°, 210°, 80°, 155°)
  - Liquid Garden: `--lg-*` (hues 260°, 155°, 25°, 80°, 50°, 260°)
  - Industry gradients: `--grad-*` (using oklch in gradient stops)
- **Semantic spacing aliases** (globals.css:68-74):
  - `--space-xs: var(--space-1)` (4px)
  - `--space-sm: var(--space-2)` (8px)
  - `--space-md: var(--space-4)` (16px)
  - `--space-lg: var(--space-6)` (24px)
  - `--space-xl: var(--space-8)` (32px)
  - `--space-2xl: var(--space-12)` (48px)

#### UI Component Migration (16+ files)
All App UI components migrated from hardcoded Tailwind classes to `--ui-text-*` variables:
- **Text sizes**: `text-xs` → `text-[var(--ui-text-xs)]` (12px), `text-sm` → `text-[var(--ui-text-sm)]` (14px), `text-base` → `text-[var(--ui-text-base)]` (16px)
- **Colors**: All `#hex` values replaced with CSS variables (`--text-primary`, `--text-secondary`, `--accent-blue`, etc.)
- **Files updated**:
  - `components/ui/SmartCombobox.tsx` (12+ replacements)
  - `components/ui/button.tsx` (4 replacements)
  - `components/ui/badge.tsx` (3 replacements)
  - `components/ui/tabs.tsx` (2 replacements)
  - `components/ui/card.tsx` (4 replacements)
  - `components/ui/input.tsx` (2 replacements)
  - `components/ui/textarea.tsx` (2 replacements)
  - `components/ui/select.tsx` (2 replacements)
  - `components/error-boundary.tsx` (4 replacements)
  - `app/error.tsx` (3 replacements)
  - `app/v2/page.tsx` (1 replacement)
  - `components/layouts/Shell.tsx` (8+ replacements)
  - `components/layouts/UserMenu.tsx` (4 replacements)
  - `components/inbox/FilterPill.tsx` (2 replacements)
  - `components/inbox/TripCard.tsx` (4 replacements)
  - `components/inbox/InboxEmptyState.tsx` (5 replacements)
  - `app/settings/components/AutonomyTab.tsx` (20+ replacements)

#### Documentation Updates
- **Updated `Docs/design-typography-spec.md`**:
  - Added `--ui-text-4xl: 2.5rem` to App UI scale
  - Added semantic spacing aliases documentation
  - Updated implementation checklist (all P0/P1/P2 items marked [x])
  - Added state tokens to checklist

#### Build Verification
- ✅ Next.js 16.2.4 build passes (36 routes generated)
- ✅ TypeScript type-check passes
- ✅ No regressions in Marketing pages (fluid clamp() preserved)
- ✅ All 50+ OKLCH values verified

---

### Typography Overhaul (2026-04-29)

#### Font Stack Fixes
- **Replaced IBM Plex Mono** with **JetBrains Mono** in `--font-data` (globals.css:70)
  - IBM Plex Mono is in the banned reflex fonts list (impeccable skill)
  - JetBrains Mono already loaded via `--font-mono`, clear 0/O and 1/l distinction
  
#### Type Scale Architecture
- **Added fixed rem scale for App UI** (globals.css:83-92)
  - New tokens: `--ui-text-xs` through `--ui-text-3xl`
  - Major Third (1.25) ratio between steps
  - Spatial predictability for dashboards/workspaces
  
- **Preserved fluid `clamp()` scale for Marketing pages**
  - `--text-*` variables unchanged for public pages
  - Correct separation per typeset skill guidance
  
- **Updated Tailwind config** (tailwind.config.js:51-62)
  - Added `ui-xs` through `ui-3xl` font size utilities
  - Existing `fluid-*` classes preserved for marketing
  
#### App UI Migration
- **Migrated 50+ components to fixed rem scale**
  - `app/overview/page.tsx` and all dashboard pages
  - `components/workspace/**/*.tsx` (all workspace panels)
  - `app/workbench/**/*.tsx` (all workbench tabs)
  - `app/owner/**/*.tsx`, `app/settings/**/*.tsx`, `app/inbox/**/*.tsx`
  
- **Marketing pages unchanged** (correct behavior)
  - `app/page.tsx`, `components/marketing/**` still use fluid `clamp()`
  
#### Contrast Fixes (WCAG 2.1 AA)
- **Fixed `--text-muted` usage at small sizes** (marketing.tsx)
  - `--text-muted` (#8b949e) has 3.5:1 ratio — FAILS at 12-14px
  - Replaced with `--text-tertiary` (#9ba3b0, 4.6:1 ratio) for 12px text
  - Lines 38, 151, 155, 187 updated
  
#### Absolute Bans (impeccable Skill)
- **Removed `border-left: 4px` accent stripes** (globals.css:601-603)
  - Violated Ban #1: "border-left/right > 1px as decorative accent"
  - Replaced with `border-top: 2px solid` approach
  - Affects `.industry-card-luxury`, `.industry-card-crisis`, `.industry-card-mice`
  
#### Documentation
- **Created `Docs/design-typography-spec.md`**
  - Complete typography specification
  - Font stack rationale (Sora + Rubik + JetBrains Mono)
  - Both type scales documented (fluid + fixed)
  - Contrast matrix (all tokens tested against WCAG AA)
  - Spacing scale (4pt grid with semantic names)
  - Absolute bans with fixes documented
  
- **Created `.impeccable.md`** (project root)
  - Design context: "Precise. Data-driven. Authoritative."
  - User personas: travel agency operators, owners, managers
  - Aesthetic direction: dark-mode operations dashboard with cartographic inspiration
  - Anti-references: generic SaaS, travel booking sites, AI slop
  
#### Technical Details
- **Files modified**: 50+ `.tsx` files + 3 config files
- **Build status**: ✅ Next.js 16.2.4 passes (36 routes generated)
- **No regressions**: Marketing pages untouched, fluid typography preserved
- **Skills used**: `typeset`, `impeccable` (via `/skill` command)

#### Neuteral Tinting with OKLCH (2026-04-29)

##### Why OKLCH?
- **Perceptually uniform**: Equal steps in lightness *look* equal (unlike HSL)
- **Brand cohesion**: Even chroma 0.005-0.01 creates subconscious connection to brand blue (#58a6ff)
- **Modern CSS**: Native browser support (oklch() function)

##### Changes Made
- **Background neutrals** tinted toward hue 260° (brand blue):
  - `--bg-canvas`: `#080a0c` → `oklch(2.5% 0.008 260)`
  - `--bg-surface`: `#0f1115` → `oklch(4.5% 0.009 260)`
  - `--bg-elevated`: `#161b22` → `oklch(7% 0.009 260)`
  - `--bg-highlight`: `#1c2128` → `oklch(9% 0.01 260)`
  - `--bg-input`: `#111318` → `oklch(4.2% 0.008 260)`

- **Border neutrals** tinted:
  - `--border-default`: `#30363d` → `oklch(18% 0.01 260)`
  - `--border-hover`: `#8b949e` → `oklch(38% 0.012 260)`

- **Text neutrals** tinted:
  - `--text-primary`: `#e6edf3` → `oklch(90% 0.012 260)`
  - `--text-secondary`: `#a8b3c1` → `oklch(72% 0.01 260)`
  - `--text-tertiary`: `#9ba3b0` → `oklch(66% 0.009 260)`
  - `--text-muted`: `#8b949e` → `oklch(58% 0.008 260)`
  - `--text-placeholder`: `#484f58` → `oklch(38% 0.006 260)`
  - `--text-rationale`: `#c9d1d9` → `oklch(82% 0.01 260)`

##### Body Text Improvements
- **Line-height**: Increased from `1.6` to `1.65` for light-on-dark breathing room
- **Font-kerning**: Added `font-kerning: normal` to enable OpenType kerning
- **Text-rendering**: Added `text-rendering: optimizeLegibility` for better ligatures

##### New Utility Classes
- `.tabular-nums`: Align numbers in data tables
- `.text-container`: Cap line length at 65ch (typeset recommendation)
- `.tracking-widest`: Standardized `letter-spacing: 0.1em` for uppercase labels

##### Result
Subtle blue tint is now perceptible across all neutrals — creates cohesive "brand atmosphere" without being obviously colored.
