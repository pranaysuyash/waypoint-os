# Decision Record — API Versioning Strategy (FND-0393)

**Date:** 2026-10-26 · **Decided by:** agent under delegated decision authority
(reversible design; owner revisit trigger noted) · **Status:** RATIFIED-FOR-NOW,
phases below.

## Context (census, 2026-10-26)

405 backend routes: 195 under `/api/v1/*`, 21 under `/api/public/*` (token-addressed
traveler surfaces), 96 legacy `/api/*` (trips, drafts, assignments, … — the
original pre-v1 domains), plus root-level (`/health`, `/metrics`, `/auth`, `/runs`).
The BFF route-map mirrors these 1:1. There is no written versioning contract; new
routes have defaulted to `/api/v1/` since ~2026-09 and legacy routes have stayed
put (additive evolution, no breaking changes shipped yet — pre-launch).

## First principles

1. A version boundary exists for CONSUMERS, and pre-launch the only consumers are
   our own BFF and token-bearing travelers. Internal-consumer versioning is a
   refactor chore, not an API contract problem — the cost of a breaking change is
   one BFF route-map edit plus in-repo callers, discoverable by the parity gate
   (`tests/test_bff_parity_gate.py`, FND-0340) and the route snapshots.
2. Breaking changes must never silently alter an existing path. Today that is
   enforced socially; it needs to be mechanical.
3. Public token-addressed surfaces (`/api/public/*`, `/a/[token]`, proposals) have
   lifetimes bound to their tokens, not to API versions — they need STABILITY and
   honesty (additive-only), not version numbers.
4. Compatibility shims are debt. Pre-launch (AGENTS.md: no backward-compatibility
   concerns), the correct breaking-change mechanism is move + delete in one
   commit, with the parity gate + snapshots proving nothing else broke.

## Decision

1. **`/api/v1/` is the single versioned contract namespace.** All NEW
   product-facing routes land there. It is currently ADDITIVE-ONLY: within v1,
   adding optional request fields, response fields, and new routes is
   non-breaking; removing/renaming/respelling anything is a breaking change and
   follows (2).
2. **Breaking changes pre-launch:** move to the new shape and DELETE the old path
   in the same commit, with (a) route snapshots regenerated, (b) parity gate
   green, (c) every in-repo caller migrated in the same pass (the E1/BFF-bypass
   sweep pattern). No v2 fork, no deprecation window, no shim — shims for a
   single in-repo consumer are pure debt. The deprecation protocol in the global
   rules (`@deprecated` → warn → one cycle → delete) applies the day an EXTERNAL
   consumer exists; until then it is deliberately not operative.
3. **Legacy `/api/*` (96 routes):** consolidate opportunistically — when a legacy
   domain is next touched for real work, its routes move to `/api/v1/` in that
   pass (move + delete + callers + snapshots, per (2)). No big-bang migration
   wave: 96 same-repo callers do not justify the churn risk. The route snapshots
   pin the inventory so drift is visible.
4. **`/api/public/*`:** version-exempt by design (capability-addressed). Changes
   are additive-only; anything breaking a traveler mid-flow (between link
   generation and submission) is a defect regardless of versioning.
5. **External-consumer future:** if/when a genuine external API consumer exists
   (partner integrations), ratify a formal v1 freeze + v2 overlap window in an
   ADR. That is the owner-ratification gate this record sets as its revisit
   trigger — the strategy above is chosen precisely so nothing built now blocks
   that future.

## Mechanical enforcement (added now, minimal)

- The two existing gates already pin the census: `server_route_snapshot.json` +
  `server_openapi_paths_snapshot.json` (fail on unstated route changes) and
  `test_bff_parity_gate.py` (fail on unmapped product-facing routes).
- This record is the referenced contract for code review: any PR that changes a
  `/api/v1/` path's shape must show move+delete+migrated-callers, not additive
  pretense.

## Revisit trigger

External API consumer appears; OR a v1 breaking change is genuinely required
while an external consumer exists; OR the legacy-consolidation opportunity cost
becomes measurable. Then: full ADR, owner ratification.
