# Overview Action Required v1.4 - Action Context

Date: 2026-05-19

## Why this pass happened

The grouped Action Required card was better than repeated enquiry rows, but it still did not explain enough of the operator decision:

- why this group is critical,
- what is actually pending from the categorization,
- what action should happen next,
- and whether the card is borrowing the same criticality logic already used in the inbox trip cards.

The goal of this pass was to add actionable context without returning to tall, repeated record cards.

## Design Decision

Action Required now keeps the grouped work item model, then adds compact operator context:

- `criticalityLabel`: short reason the work is first, such as `Breached SLA`.
- `pendingActions`: derived pending work, such as `Qualify`, `Assign owner`, `Identify customer`, `Confirm basics`.
- `nextAction`: short operational instruction, such as `Open oldest, clear basics, continue by age.`
- Long-unassigned enquiries should include age in the assignment action, for example `Assign owner (25d waiting)`, because the issue is not merely missing ownership; it is stale unowned work.

For repeated enquiry groups, examples now avoid repeating `Leisure enquiry` on every row. The group title already says the issue is overdue enquiries, so the examples prioritize the useful blockers:

- waiting age,
- customer quality,
- party size,
- travel window,
- owner assignment,
- reference.

Follow-up exploration for suggested owner and auto-assignment policy:

- `Docs/exploration/ASSISTED_ENQUIRY_ASSIGNMENT_ROUTING_RESEARCH_2026-05-19.md`

## Data Boundary

Updated after first-principles review:

- `GET /inbox/stats` now carries richer queue-level aggregates for Overview.
- Overview no longer has to infer all pending categories from only the visible five inbox examples.
- The visible examples remain useful proof points, but group copy is driven by backend stats when available.

Current live example:

- `2,442 enquiries in queue · 2,316 unassigned · oldest 25d waiting`
- `Qualification overdue · Breached SLA · 1,420 breached · unassigned oldest 25d waiting`
- `Pending: Qualify · Assign 2,316 unowned (25d waiting) · Identify 2,039 customers · Complete 2,442 basics`

## Files Changed

- `frontend/src/app/(agency)/overview/buildActionRequiredItems.ts`
- `frontend/src/app/(agency)/overview/useOverviewSummary.ts`
- `frontend/src/components/overview/ActionRequiredList.tsx`
- `frontend/src/lib/governance-api.ts`
- `frontend/src/hooks/__tests__/useGovernance.contract-surface.test.tsx`
- `frontend/src/app/(agency)/overview/__tests__/buildActionRequiredItems.test.ts`
- `frontend/src/components/overview/__tests__/ActionRequiredList.test.tsx`
- `frontend/src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts`
- `spine_api/contract.py`
- `spine_api/routers/inbox.py`
- `tests/test_inbox_router_contract.py`
- `tests/test_overview_analytics_hardening.py`

## Verification

Commands run:

```bash
cd frontend
npx vitest run src/app/'(agency)'/overview/__tests__/buildActionRequiredItems.test.ts src/components/overview/__tests__/ActionRequiredList.test.tsx src/app/'(agency)'/overview/__tests__/useOverviewSummary.test.ts src/app/'(agency)'/overview/__tests__/page.test.tsx
npx vitest run src/app/'(agency)'/overview/__tests__/buildActionRequiredItems.test.ts src/components/overview/__tests__/ActionRequiredList.test.tsx src/app/'(agency)'/overview/__tests__/useOverviewSummary.test.ts src/app/'(agency)'/overview/__tests__/page.test.tsx src/hooks/__tests__/useGovernance.contract-surface.test.tsx
npm run typecheck
npx eslint src/app/'(agency)'/overview/buildActionRequiredItems.ts src/app/'(agency)'/overview/useOverviewSummary.ts src/components/overview/ActionRequiredList.tsx src/app/'(agency)'/overview/__tests__/buildActionRequiredItems.test.ts src/components/overview/__tests__/ActionRequiredList.test.tsx src/app/'(agency)'/overview/__tests__/useOverviewSummary.test.ts src/app/'(agency)'/overview/__tests__/page.test.tsx
uv run pytest tests/test_inbox_router_contract.py tests/test_overview_analytics_hardening.py
```

Results:

- 4 focused overview test files passed.
- 33 tests passed.
- 5 frontend test files passed.
- 35 frontend tests passed.
- 2 backend test files passed.
- 4 backend tests passed.
- TypeScript passed.
- Touched-file ESLint passed.

Browser validation:

- `http://localhost:3000/overview` desktop viewport: Action Required rendered with backend queue aggregates.
- `http://localhost:3000/overview` mobile viewport 390x844: Action Required rendered with backend queue aggregates and no overlap.

Screenshots:

- `overview-action-required-action-context-2026-05-19.png`
- `overview-action-required-action-context-mobile-2026-05-19.png`
- `overview-action-required-backend-summary-2026-05-19.png`
- `overview-action-required-backend-summary-mobile-2026-05-19.png`

## Remaining Product Gap

The next product gap is not more copy in the card. It is assignment routing:

- suggested owner,
- route reason,
- workload/fairness/speed/quality signals,
- bulk-assisted assignment,
- and eventually agency-configurable auto-assignment.

See `Docs/exploration/ASSISTED_ENQUIRY_ASSIGNMENT_ROUTING_RESEARCH_2026-05-19.md`.
