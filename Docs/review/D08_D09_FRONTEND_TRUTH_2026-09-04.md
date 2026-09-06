# D-08 / D-09 Frontend Truth Evidence — 2026-09-04

## D-08 sibling sample panels

`MemoryArchitectPanel`, `MemorySettingsTab`, and `CrisisEvacuationPanel` now
identify client-local sample state and remove live-looking claims:

- persistence and compliance actions are labelled preview/local-only;
- erasure output is explicitly simulated and performs no deletion;
- crisis incidents, drivers, vehicles, beacons, slots, embassy transmission,
  and dispatch statuses are sample/draft/not-dispatched;
- sample traveler identities and provider identifiers replace fabricated
  customer/provider claims;
- the shared simulated-data badge is present.

The implementation preserves the existing panel interactions while making the
reality boundary visible in every relevant view.

## D-09 repair deep-link

The canonical route is now:

```text
/trips/<trip_id>/intake?repair=<field>
```

Behavior:

- canonical editor IDs and machine packet names resolve through one mapping;
- legacy `?field=<field>` remains supported;
- planning and inline editors open from the same resolver;
- route changes while the component remains mounted are handled;
- async trip hydration is handled without losing the requested editor;
- the target scroll anchor is brought into view;
- focus moves into the mounted input;
- only consumed `repair`/`field` parameters are removed from browser history;
- unrelated query state is preserved;
- unknown repair fields fail closed and leave the normal intake surface intact.

## Verification

Focused frontend command:

```text
npm test -- --run \
  src/app/(agency)/workbench/__tests__/D08_sibling_sample_panels.test.tsx \
  src/components/workspace/panels/__tests__/IntakePanel.repairDeepLink.test.tsx \
  src/lib/__tests__/repair-deep-link.test.ts
```

Result: **3 files / 21 tests passed** for the combined D-08/D-09 subset.

The broader D-09 lifecycle command, which also includes the existing
`IntakePanel.test.tsx` contract suite, passes **3 files / 41 tests**.

The focused suite covers sample-label/state containment, canonical and legacy
repair parameters, machine-name mapping, unknown-field abstention, async
hydration, route updates without remounting, scroll anchoring, and focus.

## D-10 reconciliation

D-10 is already closed in the canonical findings register. The VCC panel uses
the BFF-relative `/api/v1/settlement/vcc/issue` path and `route-map.ts` maps it
to the backend route. The historical hardcoded-localhost defect is retained as
lineage only.

## Remaining evidence boundary

These are local frontend/unit contracts. They do not prove hosted browser
behavior, provider-backed persistence, screen-reader conformance, contrast,
or authenticated multi-tenant behavior. Those remain separate A-16/A-17 and
provider/hosted gates.
