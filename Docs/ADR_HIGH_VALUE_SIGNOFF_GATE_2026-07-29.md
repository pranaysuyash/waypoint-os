# ADR: Agency Team Workflows & High-Value Signoff Gates

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Agency Governance & Quality Control (Priority #8)

---

## Context

High-value travel quotes (exceeding $10,000) carry significant financial and reputational exposure for travel agencies. Junior operators sending unreviewed high-ticket proposals risk margin errors, missing policy terms, or vendor liability.

---

## Decision

Implemented Agency Team Governance & High-Value Signoff Gates in `spine_api/routers/team_workflows.py`:

1. **High-Value Signoff Gate (`GET /api/v1/team/high-value-gate-check/{trip_id}`)**:
   - Enforces a mandatory governance policy: any proposal quote total $\ge \$10,000$ automatically blocks status progression to `PROPOSAL_SENT` until a formal senior planner approval is attached.
2. **Review Signoff Endpoint (`POST /api/v1/team/review-signoff`)**:
   - Allows managers and senior advisors to submit formal decisions (`APPROVED`, `CHANGES_REQUESTED`, `REJECTED`) with audit notes.
3. **Team Assignment Engine (`POST /api/v1/team/assign`)**:
   - Assigns trip packets to specific team members or specialized sub-agents with role attributes (`senior_planner`, `junior_agent`, `concierge`).

---

## Consequences

- Prevents unreviewed high-ticket quotes from being dispatched to clients.
- Enforces strict governance while keeping standard quotes ($<\$10,000$) automated and fast.
