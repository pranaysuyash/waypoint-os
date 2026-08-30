# frontend/docs — Legacy Spec Tree (Reconciled)

**Status:** historical / legacy spec tree. NOT canonical.
**Last reconciled:** 2026-08-29
**Canonical documentation tree:** [`Docs/`](../Docs/) (the repository-wide durable documentation)

## What this directory is

This directory historically held ~930 generated/spec Markdown files for the frontend build. Many of these are **aspirational** (marked TBD / not-implemented) and duplicate or diverge from the canonical system documentation in `Docs/`.

Per the Refactor Architect audit (finding **R-09**) and the doctrine's "one canonical source per instruction surface" rule:

- **`Docs/` is authoritative** for system architecture, decisions, reviews, exploration, product features, and domain knowledge.
- **`frontend/docs/` is a legacy spec tree.** It is **not** a source of truth and must not be treated as a competing canonical record.

## Reconciliation rule

1. When `frontend/docs/` and `Docs/` disagree, **`Docs/` wins**.
2. Files in `frontend/docs/` that are genuinely current should be **linked (not copied)** to from `Docs/`.
3. Stale/aspirational files in `frontend/docs/` should be **archived** rather than edited in place.
4. Do not create new competing spec documents here — put frontend architecture/decisions in `Docs/architecture/` and `Docs/decisions/`.

## Canonical navigation

Use the canonical index: [`Docs/README.md`](../Docs/README.md)

To find a frontend-specific decision, review, architecture doc, or exploration, search `Docs/architecture/`, `Docs/decisions/`, `Docs/review/`, and `Docs/exploration/` rather than this tree.
