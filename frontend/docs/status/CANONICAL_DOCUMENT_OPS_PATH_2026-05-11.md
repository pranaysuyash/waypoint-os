# Canonical Document Ops Path

Date: 2026-05-11  
Scope: Frontend module path clarity for document workflows

## Decision

Until the `/documents` navigation module is explicitly enabled, the canonical product workflow for document operations is:

1. Workbench Ops panel document upload
2. Document review (accept/reject/delete)
3. Extraction run/review
4. Extraction apply/reject

## Why

- Runtime capabilities already exist and are tested in one place (`OpsPanel` + BFF APIs).
- Parallel “temporary” document flows would duplicate behavior and drift validation/policy.
- Canonical-path reinforcement lowers onboarding ambiguity for parallel agents.

## Runtime Evidence

- Disabled nav module:
  - [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts)
    - `/documents` is `enabled: false`
- Current implemented workflow:
  - [`src/app/(agency)/workbench/OpsPanel.tsx`](../../src/app/(agency)/workbench/OpsPanel.tsx)
  - [`src/lib/api-client.ts`](../../src/lib/api-client.ts)
    - `uploadDocument`, `getDocuments`, `extractDocument`, `applyExtraction`, related review actions

## Guardrail

Do not add a second document operations path while `/documents` is disabled.  
Extend the existing Ops panel path first; enable `/documents` only when it is a route-level product surface over the same canonical contracts.

## Verification

- [`src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx`](../../src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx)
  - Includes explicit assertion for canonical path hint.

