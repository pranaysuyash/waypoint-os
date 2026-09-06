# Proposal and Persona Council Truth Boundary — 2026-09-04

**Owner lane:** legacy public proposal preview and Persona Council demo console\
**Review lens:** PER-0164 Assumption Auditor / GM-01 honesty boundary\
**Scope:** `frontend/src/app/proposals/[proposalId]/page.tsx`,
`frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx`, and their focused
frontend honesty tests.  Duty-of-care, suppliers, and MRZ surfaces are outside
this slice and remain owned by their parallel lanes.

## Evidence boundary

This is local source and focused test evidence only. The proposal page has no
proposal-resource fetch or persistence path: its itinerary, add-ons, prices,
and acceptance state are local React data/state. The Persona Council calls
relative local API routes with fixed demo identifiers; its header explicitly
declares that no external systems are contacted. No supplier, DMC, pricing,
booking, payment, identity, or external provider evidence was used.

## Findings before this slice

The legacy public proposal route rendered hardcoded itinerary and pricing data
while presenting it as verified/live/held:

- `page.tsx` previously said “Loading verified proposal...”;
- the header said “48h Price Lock Active”;
- the operator field said “Direct DMC Verified”;
- the tier section said “Live Pricing Updated”;
- acceptance was a local timer/state transition, not a persisted event.

The proposal acceptance result had already been softened by the concurrent
truth-boundary work, but the route still had contradictory top-level claims.

The Persona Council header had already been corrected to demo language, but
selector labels still said “All Operational Engines” and “Autonomous Proposal
Compiler.” Its token preview also used the misleading hardcoded identifier
`trip_live_001`.

## Implemented local containment

The public proposal route now:

- renders a prominent `Sample proposal` badge and a notice that it is a local
  demonstration fixture, not a supplier-backed booking;
- says supplier availability, DMC verification, pricing holds, bookings, and
  acceptance are not connected to an external system;
- changes price-lock/status copy to “Illustrative pricing · no hold active”;
- changes supplier status to “Sample details — confirm availability”;
- changes “Live Pricing Updated” to “Illustrative pricing · not refreshed”;
- describes the itinerary and totals as illustrative and subject to
  confirmation;
- renames the action to “Simulate Proposal Acceptance”;
- reports a local acceptance preview without implying submission, booking, or
  inventory placement;
- changes the loading state to “Loading sample proposal preview...”.

The Persona Council now:

- uses `trip_demo_001` rather than `trip_live_001`;
- labels the aggregate view “All Demo Engines”;
- labels proposal compilation as “Proposal Compiler (Simulation)”;
- labels the private-jet, yield, IVR, IROPS, duty, GDS/NDC, negotiation,
  crisis, MRZ, and VCC selector entries as preview/simulation/demo surfaces;
- renames the token section to “Capability Token Preview & 5-Tier Authority
  Model Example”;
- renames token issuance to “Generate Sample HMAC Token”.

## Verification

Focused commands:

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend
npm test -- --run \
  src/app/proposals/__tests__/page.test.tsx \
  'src/app/(agency)/workbench/__tests__/simulated-panels-honesty.test.tsx'
```

The proposal tests assert the sample banner, illustrative pricing, absence of
verified/live/price-lock claims, and local-only acceptance result. The Persona
Council test asserts the demo labels, sample token action, demo identifier, and
absence of the retired operational labels.

Result on 2026-09-04: **2 test files passed, 13 tests passed**.

The same four changed frontend files were also checked with targeted ESLint;
it completed with no reported diagnostics. `git diff --check` completed with no
whitespace errors.

No production provider, booking, pricing-hold, payment, or acceptance behavior
was added. No Git staging, commit, push, reset, checkout, stash, or cleanup was
performed. Other dirty and untracked worktree paths were preserved.

## Alignment and remaining work

This local slice follows first principles: a client-side fixture may demonstrate
proposal composition and acceptance UX, but cannot claim that a supplier,
carrier, DMC, price engine, inventory system, or customer acceptance acted.
The correction is additive and reversible, and it preserves the demo’s useful
interaction while making its evidence boundary visible.

The long-term implementation remains separate:

1. Consolidate this route with one canonical persisted proposal resource.
2. Bind every displayed offer to source, freshness, supplier, and verification
   evidence.
3. Persist acceptance with authenticated actor, proposal revision/hash, and
   idempotency semantics.
4. Implement inventory/price holds only through an authorized provider adapter
   with expiration and reconciliation.
5. Keep Persona Council calculations and token examples explicitly separated
   from real agency-trip actions and production authority credentials.

These provider, commercial, identity, and operational integrations remain open
and require separate authorization; they are not implied by this frontend
containment or its passing tests.
