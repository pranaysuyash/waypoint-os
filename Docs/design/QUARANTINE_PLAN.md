# Design System Quarantine Plan

Documenting competing design sources and establishing exactly one canonical path forward.

---

## 1. Inventory Classification

| # | File Path | Type | Current Role | Recommended Status | Reason |
|---|-----------|------|--------------|-------------------|--------|
| 1 | `frontend/src/app/globals.css` | CSS token file (live) | Runtime color/spacing/typography authority | **Canonical** | Loaded globally. All app components should reference `var(--*)` from this file. |
| 2 | `frontend/src/lib/tokens.ts` | TypeScript token file | Parallel OKLCH-based token source; imports exist in components | **Superseded / To be archived** | Audit already says "Remove all `@/lib/tokens` imports." OKLCH values at chroma 0.008 produce flat imperceptible colors. Hex in globals.css is the live authority. |
| 3 | `frontend/tailwind.config.js` | Tailwind config | Bridges CSS vars to utilities | **Canonical** | Must stay in sync with `globals.css`. Missing some tokens per audit, but structurally correct. |
| 4 | `frontend/src/stores/themeStore.ts` | Component logic | Runtime theme switching | **Canonical** | Live, but only supports density + debug mode currently. Direction is sound. |
| 5 | `frontend/src/lib/design-system.ts` | Component logic | Product copy, nav structure | **Canonical** | Not a visual token file, but part of app structure. |
| 6 | `frontend/src/components/marketing/marketing.module.css` | CSS module | Marketing page styles | **Reference only** | Isolated `--mk-*` namespace. Hardcoded hex, gradients, glassmorphism. Not app-facing. Must not influence app components. |
| 7 | `frontend/src/components/marketing/marketing-v2.module.css` | CSS module | Alternate marketing styles | **Superseded** | Same issues as v1. Not imported by app. Candidate for archiving. |
| 8 | `frontend/src/components/marketing/marketing.bak.module.css` | CSS module | Backup marketing styles | **Superseded** | Audit explicitly says delete. Backup files should not exist in active tree. |
| 9 | `frontend/src/app/page.module.css` | CSS module | Landing page layout | **Superseded** | Uses different variable namespace (`--background`, `--foreground`). Leftover from Next.js template. |
| 10 | `frontend/src/app/(auth)/auth.css` | CSS file | Auth page styles | **Live but to migrate** | Hardcoded hex values that match globals.css but don't reference vars. Should be migrated to globals.css tokens. |
| 11 | `frontend/src/app/workbench/workbench.module.css` | CSS module | Workbench UI styles | **Live but to migrate** | Uses different namespace (`--color-background`, `--color-primary`). Mini design system. Should converge to globals.css tokens. |
| 12 | `Docs/DESIGN.md` | Design doc | Comprehensive design spec v2.0 | **Reference only** | Dated 2026-04-15. OKLCH migration in newer docs partially supersedes. Still useful for philosophy and spatial reasoning. Not a token authority. |
| 13 | `Docs/design-typography-spec.md` | Design doc | Typography spec | **Canonical** | Dated 2026-04-29. Current font stack (Sora, Rubik, JetBrains Mono). Implementation in app is correct. |
| 14 | `Docs/design-audit-findings.md` | Audit artifact | 2026-04-29 audit snapshot | **Generated artifact** | Evidence of drift. Useful for understanding what broke, but not a design source. |
| 15 | `Docs/FRONTEND_AUDIT_REPORT_2026-04-29.md` | Audit artifact | Frontend technical audit | **Generated artifact** | Evidence. Not a design source. |
| 16 | `Docs/design/waypoint-os/wp-tokens.jsx` | Prototype | JSX showcase components | **Reference only** | Earlier design exploration. Left-border accent stripes — banned by typography spec. Not imported. |
| 17 | `Waypoint OS Design _offline_.html` | Prototype | Exported design page | **Reference only** | Not in build. For inspiration only. |
| 18 | `page_content.html` | Unknown | Generic HTML file | **Unknown / probably historical** | Not in build. |
| 19 | `Archive/context_ingest/meta_design_refs_*` | Archived context | HTML thinking artifacts | **Historical / archived** | Not in build. Reference only. |

---

## 2. Plan (No Moves Yet — For Review)

### Canonical Structure (to create)

| File | Purpose |
|------|---------|
| `Docs/design/CANONICAL_DESIGN_SYSTEM.md` | Single entry point for all future design questions. References globals.css variables + typography spec + severity grammar + component grammar. |
| `Docs/design/COMPONENT_GRAMMAR.md` | Card grammar, icon grammar, badge grammar, button grammar, empty-state grammar, tab grammar, right-rail grammar. |
| `Docs/design/VISUAL_REGRESSION_PROCESS.md` | Before/after screenshot workflow, comparison checklist, weakness tracking. |

### Archive Candidates (after approval)

| File | Destination |
|------|-------------|
| `Docs/DESIGN.md` | `Docs/design/references/DESIGN.md` |
| `Docs/design-audit-findings.md` | `Docs/design/audit-history/design-audit-findings.md` |
| `Docs/FRONTEND_AUDIT_REPORT_2026-04-29.md` | `Docs/design/audit-history/FRONTEND_AUDIT_REPORT_2026-04-29.md` |
| `frontend/src/lib/tokens.ts` | `Docs/design/archive/tokens.ts` (preserve for history) |
| `frontend/src/components/marketing/marketing.bak.module.css` | `Docs/design/archive/marketing.bak.module.css` then DELETE from tree |
| `frontend/src/components/marketing/marketing-v2.module.css` | `Docs/design/archive/marketing-v2.module.css` (if useful for marketing team) |
| `frontend/src/app/page.module.css` | `Docs/design/archive/page.module.css` or DELETE |
| `Docs/design/waypoint-os/wp-tokens.jsx` | `Docs/design/archive/wp-tokens.jsx` |
| `Waypoint OS Design _offline_.html` | `Docs/design/references/waypoint-offline.html` |
| `page_content.html` | DELETE |

### Files To Add Header Notices (if left in place)

| File | Notice |
|------|--------|
| `Docs/DESIGN.md` | "Superseded. Do not use for implementation. See Docs/design/CANONICAL_DESIGN_SYSTEM.md." |
| `frontend/src/lib/tokens.ts` | "Superseded. Do not import in new components. Use CSS custom properties from globals.css. See Docs/design/CANONICAL_DESIGN_SYSTEM.md." |
| `frontend/src/components/marketing/marketing.bak.module.css` | "Deprecated. Scheduled for removal." |

### Files To Migrate (not archive, but fix)

| File | Migration |
|------|-----------|
| `frontend/src/app/(auth)/auth.css` | Replace hardcoded hex with `var(--*)` from globals.css |
| `frontend/src/app/workbench/workbench.module.css` | Converge variable namespace to globals.css tokens |

---

## 3. Immediate Conflicts Resolved

1. **Hex vs OKLCH**: `globals.css` (hex) is canonical. `tokens.ts` (OKLCH) is superseded.
2. **Three CSS variable namespaces**:
   - App canonical: `--bg-canvas`, `--text-primary`, `--accent-blue` (globals.css)
   - Workbench isolated: `--color-background`, `--color-primary` (should migrate)
   - Marketing isolated: `--mk-*` (acceptable because marketing is isolated)
   - Auth hardcoded hex (should migrate)
3. **`components.json` for shadcn**: Missing but not blocking. Only needed if we add shadcn components.

---

## 4. Decision: Can We Delete `tokens.ts`?

**No.** Apply Supersession Workflow first.

- Step 1: Identify candidate (`tokens.ts`) and replacement (`globals.css` CSS vars).
- Step 2: Field comparison. `tokens.ts` has `STATE_COLORS`, `GEO_COLORS`, `SPACING`, `Z_INDEX`, `BREAKPOINTS` that `globals.css` doesn't have.
- Step 3: Call-site audit. `grep -r "@/lib/tokens" frontend/src` — still has imports.
- Step 4: Add missing tokens to `globals.css` or remove imports from components first. Then archive.

**Verdict**: Migrate missing values first, then archive. Do not delete in this pass.

---

## 5. Acceptance Criteria

- [x] Exactly one canonical CSS token file (`globals.css`).
- [x] All competing token sources classified.
- [x] Plan written, no files moved yet.
- [ ] User approves plan.
- [ ] After approval, create canonical docs.
- [ ] After approval, archive superseded files.
- [ ] After approval, add header notices to stale files left in tree.

---

## 6. Next Step

**Capture before screenshot of /overview, then write implementation plan.**
