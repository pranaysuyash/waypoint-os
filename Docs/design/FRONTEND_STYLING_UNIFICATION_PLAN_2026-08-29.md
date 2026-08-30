# Frontend Styling Unification Plan — R-14

**Status:** Proposed design (not yet implemented)
**Date:** 2026-08-29
**Owner:** Frontend design system
**Associated finding:** R-14 (literal-hex page styling coexists with a shadcn-style CSS-variable primitive layer — a two-generation styling surface)

## Problem

The frontend has two coexisting styling generations:

1. **Primitive layer** (`frontend/src/components/ui/*`) — a shadcn-style kit using CSS variables (`--accent-blue`, `text-[var(--ui-text-sm)]`, `bg-elevated`, `border-default`) via `class-variance-authority`, `cn`, and `@radix-ui/react-slot`. This is the canonical system.
2. **Page-level inline hardcoding** — many page components bypass the primitive layer and hardcode literal GitHub-dark hex values: `bg-[#0d1117]`, `text-[#e6edf3]`, `border-[#30363d]`, `#58a6ff`. Concentrated in `insights`, `reviews`, `overview`, and the rollout pages (`quotes`, `bookings`, `suppliers`, `knowledge`).
3. **Workspace/panel layer** (`frontend/src/components/workspace/panels/*`) — a parallel panel layer used by `OpsPanel` that also has its own styling.

This produces:
- **Visual inconsistency** — the same semantic concept (surface, border, text-muted) maps to different token values on different pages.
- **No single token source of truth** — a change to the theme requires touching hex values scattered across many files.
- **Theme-store mismatch** — `themeStore.ts` supports `travel`/`agency`/`agent` themes and variants, but literal-hex pages ignore the theme entirely.

## Target

Unify all page styling onto the **CSS-variable primitive layer** as the single source of truth. Literal hex values should map to semantic CSS variables. The `globals.css` token set should be the only place hex/Tailwind-config color values live.

## Migration path (safe, incremental)

1. **Map literal hex → semantic token** — build a one-off mapping table:
   - `#0d1117` → `--surface-bg` (or the theme's `bg-elevated`/`bg-default`)
   - `#e6edf3` → `--text-primary`
   - `#30363d` → `--border-default`
   - `#58a6ff` → `--accent-blue` / `--accent-link`
2. **Establish the token set in `globals.css`** — ensure every literal hex used across pages has a named CSS variable (or Tailwind theme token) equivalent.
3. **Migrate page-by-page, icon-group by icon-group** — replace each literal-hex usage with the corresponding `var(--token)` or Tailwind semantic class. Prioritize: `insights`, `reviews`, `overview` (most concentrated), then the rollout pages.
4. **Verify** — run `npm run lint` + `npm test -- --run` + a visual check of each migrated page (dark mode + each theme variant).
5. **Test theme-store integration** — confirm the theme selector (`travel`/`agency`/`agent`) changes the migrated pages, proving they now read from the token system.

## Non-goals (deliberately excluded)

- **No wholesale component rewrite.** Keep the shadcn-style primitive layer and the workspace/panel layer; only unify the *token* source. Do not rebuild components.
- **No new design system.** The primitive + globals.css token set is the system; this work reconciles onto it.
- **No visual redesign.** Identity of pages is preserved; only the styling source is unified.

## Acceptance criteria

- Zero literal `#0d1117`/`#e6edf3`/`#30363d`/`#58a6ff` hex values in page (non-component) files — all replaced by CSS variables or semantic tokens.
- The theme selector visibly changes migrated pages.
- Lint + tests pass.

## Risks / open questions

- Some literal-hex values may not have a clean semantic equivalent (e.g., a specific accent used once). Those should get a named token rather than staying literal.
- The workspace/panel layer styling may need a separate mapping pass; it may intentionally differ from the primitive layer and should be reconciled only where the semantics match.
- Whether to consolidate the `.commandcode`/`compact` density variants into the token system (deferring).
