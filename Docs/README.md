# Waypoint OS — Durable Documentation Index

**Status:** canonical navigation surface (routing only, not a source of truth)
**Last reviewed:** 2026-08-29
**Owner:** Technical documentation

This file is the single entry point for Waypoint OS's durable knowledge. It routes to canonical sources and explains how the documentation tree is organized. It does **not** duplicate canonical content — it points to it.

## How to navigate

Every knowledge type is owned by exactly one canonical artifact. If you are looking for a decision, architecture, review, exploration, or operational procedure, go to the canonical location below. Do not search the conversation history — the durable record is here.

| Knowledge type | Canonical location |
|---|---|
| **Operating doctrine** (authority, authorization, evidence, canonical paths) | `/Users/pranay/Projects/agent-start/doctrines/OPERATING_DOCTRINE.md` (v8.0). Project copies under frontend/, frontend/src/, spine_api/ are labeled mirror pointers — not authoritative. |
| **Project instructions** | `AGENTS.md` (root, canonical). `CLAUDE.md` is a symlink to `AGENTS.md`. |
| **Architecture** | `Docs/architecture/` (ADRs, system design, migration plans) |
| **Decisions** | `Docs/decisions/` (decision records) and `Docs/ADR_*.md` (dated architecture decision records) |
| **Reviews** | `Docs/review/` (audits, implementation reviews, readiness contracts) |
| **Exploration maps** | `Docs/exploration/` and `Docs/explorations/` |
| **Product features** | `Docs/product_features/` and `Docs/product_features/INDEX.md` |
| **Industry domain** | `Docs/industry_domain/INDEX.md` |
| **Agent intelligence graph** | `Docs/context/AGENT_INTELLIGENCE_GRAPH.md` |
| **Agent generated context** | `Docs/context/agent-start/` (SESSION_CONTEXT, AGENT_KICKOFF_PROMPT — generated, not canonical) |
| **Test & eval evidence** | `Docs/validation/`, `src/evals/` (manifest + gate snapshots) |
| **Runbooks / operations** | `Docs/operations/` and, for tool-specific procedures, runbooks |
| **Launch readiness** | `Docs/agent-artifacts/launch_readiness_report.md`, `Docs/waypoint_os_launch_readiness_audit_2026-08-03.md` |

## Canonical review (2026-08-29)

- **[Refactor Architect Evidence Audit & Doctrine Alignment](review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md)** — First-principles / long-term / doctrine-alignment audit led by `PER-0001 Refactor Decision Architect`. 16 findings (R-01..R-16), evidence ledger, priority matrix, implementation sequencing.
- **[Audit worklog & decision record](review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29_WORKLOG.md)** — Full discussion trail, rationale, rejected directions, handoffs.

## Project tree relationship: Docs/ vs frontend/docs/

There are two documentation trees in the repository:
- **`Docs/`** — the system-wide durable documentation (architecture, decisions, reviews, exploration, product, domain, validation). This is the **canonical** system documentation.
- **`frontend/docs/`** — historically a second, separate spec/roadmap tree derived for the frontend build. Many of its files are aspirational (marked TBD/not-implemented) and duplicate or diverge from `Docs/`.

**Reconciliation rule (R-09):** `Docs/` is authoritative for system architecture, decisions, reviews, and domain knowledge. `frontend/docs/` should be treated as a **historical/legacy spec tree** and should be reconciled into `Docs/` or archived rather than treated as a competing source of truth. When `Docs/` and `frontend/docs/` disagree, `Docs/` wins. As a migration path is executed, `frontend/docs/` files that are genuinely current should be linked (not copied) from `Docs/`; stale/aspirational files should be archived.

## Freshness

This index is refreshed when the durable knowledge structure materially changes. If you add a new canonical artifact (a decision, architecture doc, review, or exploration map), add a link here so the next engineer or agent can find it by concept, not by remembered filename.
