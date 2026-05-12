# Route Shell Ready Gate Update

Date: 2026-05-12  
Gate: `route-level-shell-ready`

## Outcome

Gate moved to complete in [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts).

## Implemented Surface

Added dedicated route-level shell:

- [`src/app/(agency)/documents/page.tsx`](../../src/app/(agency)/documents/page.tsx)
- [`src/app/(agency)/documents/PageClient.tsx`](../../src/app/(agency)/documents/PageClient.tsx)

The shell:

1. Provides trip selection for active workspace trips.
2. Reuses canonical document operations via `OpsPanel` in `mode='documents'`.
3. Avoids creating any parallel document APIs or duplicate workflow logic.

## Canonical Reuse

- Reused component path:
  - [`src/app/(agency)/workbench/OpsPanel.tsx`](../../src/app/(agency)/workbench/OpsPanel.tsx)
- Added focused mode:
  - `mode: 'full' | 'documents'`
  - `documents` mode bypasses non-document sections while keeping document contracts intact.

## Verification

1. `npm test -- "src/app/(agency)/documents/__tests__/page.test.tsx" --reporter=dot`
2. `npm test -- "src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx" --reporter=dot`
3. `npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot`

## Remaining Gate

- None for `/documents` nav enablement. `contract-regression-suite` is now complete.
