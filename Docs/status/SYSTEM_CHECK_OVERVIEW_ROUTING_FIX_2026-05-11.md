# System Check Overview Routing Fix - 2026-05-11

## Context

User reported that clicking the `System Check` card in `Overview` opened the New Inquiry workbench with the system check drawer on the right. The URL was `/workbench?panel=integrity`.

## Root Cause

- `frontend/src/app/(agency)/overview/useOverviewSummary.ts` routed both the `System Check` metric card and the `Jump To` nav item to `/workbench?panel=integrity`.
- `frontend/src/app/(agency)/workbench/PageClient.tsx` treated `panel=integrity` as a workbench side panel, so the base page remained the New Inquiry workbench.
- This made a system-level health action appear inside an inquiry-processing context.

## Decision

System Check belongs to Overview/system health, not the New Inquiry workbench. The canonical route is now:

```text
/overview?panel=system-check
```

Because the product has not launched, there is no backward-compatibility requirement for the bad `/workbench?panel=integrity` URL. The clean contract is that System Check opens only from the Overview route.

## Changed Files

- `frontend/src/app/(agency)/overview/useOverviewSummary.ts`
  - Added `SYSTEM_CHECK_HREF`.
  - Routed metric and quick-nav System Check links to `/overview?panel=system-check`.
- `frontend/src/app/(agency)/overview/PageClient.tsx`
  - Reads `panel=system-check`.
  - Opens the system-owned `SystemCheckPanel` from the Overview page context.
  - Closes by removing the `panel` search param while staying on Overview.
- `frontend/src/app/(agency)/workbench/PageClient.tsx`
  - Removed Workbench rendering of the integrity panel.
  - Does not preserve or redirect `/workbench?panel=integrity`; pre-launch cleanup should not teach stale URLs as supported contracts.
- `frontend/src/components/system/SystemCheckPanel.tsx`
  - New canonical component location for system health checks.
- `frontend/src/app/(agency)/workbench/IntegrityMonitorPanel.tsx`
  - Removed after supersession by `SystemCheckPanel`.
- Tests updated:
  - `frontend/src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts`
  - `frontend/src/app/(agency)/overview/__tests__/page.test.tsx`
  - `frontend/src/app/(agency)/workbench/__tests__/page.test.tsx`
  - `frontend/src/app/(agency)/workbench/__tests__/integrity-panels.test.tsx`
  - `frontend/src/components/system/__tests__/SystemCheckPanel.test.tsx`

## Supersession Analysis

Removal: `frontend/src/app/(agency)/workbench/IntegrityMonitorPanel.tsx` - superseded by `frontend/src/components/system/SystemCheckPanel.tsx`.

Comparison:

- Props: `open` and `onClose` preserved.
- Data contract: `useIntegrityIssues()` and `IntegrityAction` handling preserved.
- UI states: loading, error, empty, and issue-list states preserved.
- Behavior: read-only display preserved; no repair/status mutation added.
- Ownership: moved from Workbench route ownership to system component ownership.

Call sites: Overview migrated to `SystemCheckPanel`; Workbench no longer imports or renders the system check panel.

## Verification

```bash
cd frontend && npm run -s test -- --run 'src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts' 'src/app/(agency)/overview/__tests__/page.test.tsx' 'src/app/(agency)/workbench/__tests__/page.test.tsx'
```

Earlier result before component ownership cleanup: 3 test files passed, 15 tests passed.

Fresh result after moving the panel to `components/system`:

```bash
cd frontend && npm run -s test -- --run 'src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts' 'src/app/(agency)/overview/__tests__/page.test.tsx' 'src/app/(agency)/workbench/__tests__/page.test.tsx' 'src/app/(agency)/workbench/__tests__/integrity-panels.test.tsx' 'src/components/system/__tests__/SystemCheckPanel.test.tsx'
```

Result: 5 test files passed, 16 tests passed.

```bash
cd frontend && npm run -s build
```

Fresh result after component ownership cleanup: build passed, TypeScript passed, static page generation completed for 42 routes.

## Notes For Future Agents

- Do not route system health/status actions through `/workbench`; that route is an inquiry-processing compatibility surface.
- If a durable admin/system page is introduced later, move the System Check panel to a shared module and route Overview to that page. Avoid duplicating the integrity UI or creating a parallel API route.
- Pre-launch stale URLs should be removed, not preserved, unless the user explicitly asks for compatibility.
- If `/overview` or `/workbench` shows a blank page after this supersession while source imports are correct, check for stale `.next/dev` artifacts referencing `IntegrityMonitorPanel` and run `npm run dev:reset` before changing source.
