# Contract Regression Suite Gate Update

Date: 2026-05-12  
Gate: `contract-regression-suite`

## Outcome

Gate moved to complete in [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts).

## What Was Verified

Canonical document contracts are now explicitly covered by regression tests across existing suites:

1. Endpoint contract surface for document operations:
   - [`src/lib/__tests__/api-client-contract-surface.test.ts`](../../src/lib/__tests__/api-client-contract-surface.test.ts)
   - Verifies canonical BFF paths for:
     - upload
     - list
     - download URL
     - accept / reject / delete
     - extract / apply / reject extraction
2. Integration behavior for extraction apply flow:
   - [`src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx`](../../src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx)
3. Route-shell canonical wiring:
   - [`src/app/(agency)/documents/__tests__/page.test.tsx`](../../src/app/(agency)/documents/__tests__/page.test.tsx)

## Verification

1. `npm test -- "src/lib/__tests__/api-client-contract-surface.test.ts" --reporter=dot`
2. `npm test -- "src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx" --reporter=dot`
3. `npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot`

## Notes

- This closes the final `/documents` rollout gate without creating any parallel route or API path.
- `/documents` nav enablement remains fully gate-driven and deterministic.
