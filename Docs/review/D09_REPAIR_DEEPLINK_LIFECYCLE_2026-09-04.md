# D-09 Repair Deep-Link Lifecycle — 2026-09-04

**Disposition:** locally implemented and regression-verified; browser/device and
hosted release evidence remain open.

**Scope:** the canonical trip intake route and its repair query contract:
`/trips/{tripId}/intake?repair=<field>`. This slice owns the `IntakePanel`
mount/synchronization/focus behavior only. Workbench banner routing, draft
promotion, and provider effects are separate contracts.

## Contract

The canonical query key is `repair`; `field` remains accepted as a legacy alias.
Machine names are resolved by `frontend/src/lib/repair-deep-link.ts` into the
existing editor IDs. A recognized target must, once its Trip/editor is mounted:

1. open the existing editor;
2. scroll the editor anchor into view; and
3. focus the first editable control.

An unrecognized value must not open an arbitrary editor or claim repair success.
The query cleanup removes only `repair` and `field`, preserving unrelated route
state such as capture mode, entry provenance, and future parameters.

## Defect found in the prior implementation

The prior effect marked the deep-link as handled before querying the DOM. If the
route rendered before the asynchronous Trip payload arrived, the effect saw no
anchor and never retried. The same route also did not react when navigation
changed `?repair=` without remounting the component. Finally, planning editors
for valid fields such as an already-populated budget or contact name were not
mounted when the missing-details panel had no corresponding row.

These were lifecycle and reachability defects, not new product-field semantics.

## Implementation

`frontend/src/components/workspace/panels/IntakePanel.tsx` now:

- synchronizes planning versus inline editor state when the resolved repair
  target changes while the route remains mounted;
- retries the DOM handoff while the target is being hydrated, with a bounded
  animation-frame loop;
- marks a target handled only after its `[data-intake-editor]` anchor exists;
- keys the focus handoff by Trip plus resolved field, preventing duplicate
  focus while permitting a later repair target;
- preserves unrelated query parameters while removing consumed repair aliases;
- mounts one standalone planning editor when the valid target is not represented
  by the current missing-details rows or summary editor;
- avoids duplicate summary/editor mounts for priorities and flexibility when the
  missing-details panel already owns that editor.

No save endpoint, field schema, validation rule, or provider behavior changed.

## Evidence

Focused command:

```text
cd frontend && npm test -- --run \
  src/components/workspace/panels/__tests__/IntakePanel.repairDeepLink.test.tsx \
  src/lib/__tests__/repair-deep-link.test.ts \
  src/components/workspace/panels/__tests__/IntakePanel.test.tsx \
  --reporter=dot
```

Result on 2026-09-04:

```text
Test Files  3 passed (3)
Tests       41 passed (41)
```

The D-09 tests cover:

- canonical `?repair=budget` auto-open, scroll, and focus;
- legacy `?field=priorities` compatibility;
- machine-name mapping such as `date_window`;
- unknown-field abstention;
- late Trip hydration after the route first mounts;
- changing from one repair target to another without a route remount;
- a valid budget repair when no missing-details panel is present.

Static checks:

```text
npx eslint <four owned frontend files>  -> exit 0
npx tsc --noEmit                         -> exit 0
```

## Evidence boundary and remaining work

This is Tier 2 local DOM/unit evidence. It establishes the component contract in
JSDOM and static type/lint checks; it does not establish:

- real browser layout or scroll geometry;
- keyboard traversal and visible focus-ring rendering in Chromium/WebKit;
- screen-reader announcements or accessibility-tree behavior;
- mobile viewport behavior;
- authenticated hosted-route behavior;
- draft-only blocked-run repair, which still depends on the separate decision
  about persisting a Trip or providing an inline draft editor;
- semantic ownership or release readiness of the dirty worktree.

The next evidence step is a real authenticated browser/device run on the
canonical route, including a delayed Trip hydration case where practical. The
workbench banner and draft-only state must be verified against their own
contracts before D-09 is called product/release complete.

## Files changed in this slice

- `frontend/src/components/workspace/panels/IntakePanel.tsx`
- `frontend/src/components/workspace/panels/__tests__/IntakePanel.repairDeepLink.test.tsx`
- `Docs/review/D09_REPAIR_DEEPLINK_LIFECYCLE_2026-09-04.md`

Git staging, commit, push, reset, checkout, stash, clean, deletion, and branch
operations were not performed.
