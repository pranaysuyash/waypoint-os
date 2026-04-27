# Agency Scope Audit

Date: 2026-04-27

## Purpose

This audit verifies whether the current application flows are scoped to an agency/workspace model or are generic consumer-facing flows. It is based on repository evidence, user-facing UI naming, backend tenancy services, and strategic docs.

## Executive Summary

- The app is **agency-scoped**, not a generic direct-to-consumer travel app.
- The primary product experience is built for **operators, agency owners, and internal workflows**.
- The current architecture uses a **Workspace/Agency model** and includes explicit agency tenancy, membership, and owner review logic.
- The UI and docs refer to an **Operator Workbench / Agency Flow Simulator**, not traveler self-service.
- The `SINGLE_TENANT_MVP_STRATEGY.md` document is marked as **deprecated** and the project direction is now a **multi-tenant platform**, but still anchored in agency/workspace scope.

## Findings

### 1. Product positioning and strategy

- `memory/MEMORY.md` explicitly states: "This is a white-label B2B SaaS platform, NOT a direct-to-consumer agency."
- `README.md` and `app.py` describe the product as:
  - Intake & Normalization for agency inboxes
  - Strategy and internal operator packets
  - Workbench UI for operators to review and execute the pipeline
- `Docs/SINGLE_TENANT_MVP_STRATEGY.md` remains in the repo as a historical draft, but it is clearly marked as **deprecated** and superseded by a multi-tenant direction.

### 2. App flow and UI evidence

- `app.py` is titled **Operator Workbench — Agency Flow Simulator**.
- The sidebar feeds and labels are operator-centric:
  - "Operating Mode"
  - "Owner Note (optional)"
  - "Paste agency notes, traveler messages, or CRM entries..."
- Input is captured as `SourceEnvelope.from_freeform(... source="agency_notes", actor="agent")` and owner notes are explicitly actor="owner".
- Tabs include intake, decision, strategy, safety, and flow simulation — all consistent with an operator workflow rather than consumer booking steps.

### 3. Backend tenancy and agency/workspace model

- `spine_api/services/workspace_service.py` defines a workspace as synonymous with an `Agency`.
- Workspace CRUD and code generation operate on `Agency` and `WorkspaceCode`, not generic user sessions.
- `spine_api/services/auth_service.py` bootstraps a new agency during signup and attaches membership records.
- Auth tokens are created with `agency_id` and role information, indicating multi-tenant agency governance.

### 4. User-facing role separation

- Product docs and code separate internal vs traveler outputs:
  - `Traveler-safe output` is explicitly sanitized and separated from internal bundles.
  - Internal bundles are described as `Agent-Only`.
- This confirms the app is designed around an internal agency workflow with traveler-safe release, not an end-user consumer checkout flow.

### 5. Existing multi-tenant and ownership controls

- The current app is not just single-tenant agency-only; it includes explicit workspace/agency isolation and owner approval/workflow patterns.
- The `SINGLE_TENANT_MVP_STRATEGY` document is clearly archived as an exploratory draft, meaning current intent is to support agency tenancy more formally.

## User-level audit conclusions

### As an operator

- The product reads as an agency tool.
- The primary flow is: ingest agency notes, run the spine, review packet/decision/strategy, enforce traveler-safe output.
- Operator-facing controls (`owner_note`, `strict mode`, `workflow stage`) are front and center.

### As a traveler

- There is no consumer-facing booking or search funnel visible in the main repo UX.
- Traveler interaction is likely downstream of internal strategy output and is intentionally separated.

## Conclusion

The current app flow is clearly scoped to an agency/workspace model and operator-centric experience. It does not present as a generic direct-to-consumer travel booking flow.

## Recommendation

- Maintain the agency/workspace terminology consistently in UI, API routes, and docs.
- Remove or archive any remaining generic consumer-facing language to avoid confusion.
- If the goal is to validate this from the actual frontend UX, a follow-up audit should inspect the `frontend/src/app` routes and rendered pages directly.
