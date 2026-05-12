# Documents Module Enablement Contract

Date: 2026-05-11  
Scope: `/documents` nav-module rollout criteria and sequencing

## Objective

Enable `/documents` only when it is a stable route-level product surface over existing canonical document contracts, without creating parallel behavior.

## Canonical Rule

Before `/documents` is enabled in navigation:

1. Keep document operations in the current Ops canonical path.
2. Build `/documents` as a surface over the same APIs/contracts.
3. Pass rollout gates and regression checks.

Reference implementations:

- [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts)
- [`src/app/(agency)/workbench/OpsPanel.tsx`](../../src/app/(agency)/workbench/OpsPanel.tsx)
- [`src/lib/api-client.ts`](../../src/lib/api-client.ts)

## Rollout Gates

Defined in code:
- `DOCUMENTS_MODULE_ROLLOUT_GATES` in [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts)

Current gates:

1. `ops-path-stable` (complete)
2. `privacy-redaction-enforced` (complete)
3. `route-level-shell-ready` (complete)
4. `contract-regression-suite` (complete)

Latest evidence:
- [PRIVACY_REDACTION_GATE_2026-05-12.md](./PRIVACY_REDACTION_GATE_2026-05-12.md)
- [ROUTE_SHELL_READY_GATE_2026-05-12.md](./ROUTE_SHELL_READY_GATE_2026-05-12.md)
- [CONTRACT_REGRESSION_SUITE_GATE_2026-05-12.md](./CONTRACT_REGRESSION_SUITE_GATE_2026-05-12.md)

## Enablement Mechanism

- `/documents` nav `enabled` is computed by `isDocumentsModuleEnabled()`.
- Gate flips are explicit, versioned code changes (not implicit assumptions).

## Verification Commands

1. `npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot`
2. `npm test -- "src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx" --reporter=dot`
3. `npm test -- "src/lib/__tests__/api-client-contract-surface.test.ts" --reporter=dot`

## Non-Goals

- No duplicate document APIs.
- No temporary parallel document workflow.
- No nav enablement based on docs-only readiness.
