# Ratings Write-Surface — Consent Flow Design (TRV-DP-07, delegated)

**Decision (delegated per TRV-DP-05 ruling):** the ratings WRITE route ships
only with a two-step consent gate; the design below is ratified as the
implementation contract. Revisit trigger: pilot-agency feedback on consent UX,
or a DPDP/cookie-banner legal review that changes the mechanics.

**Context:** `FederatedIntelligenceService.report_rating` is durable,
hash-anonymized, and audit-mirrored (2026-10-30 wave). The missing layer is
the write API + the consent contract, because traveler contributions are
PII-adjacent (DPDP Act obligation; BD matrix: "own contributions owned w/
consent").

## Design

1. **Route:** `POST /api/v1/destination-intelligence/ratings/{location}`
   body `{dimension, score, trip_month?, note?, consent: true}`.
2. **Consent is explicit per submission** — the client sends `consent: true`
   only when the traveler checked the consent checkbox in the UI; the route
   rejects `consent != true` with 422 (no server-side "remembered" consent —
   consent is per-act, revocable by not contributing).
3. **No PII in the pool:** the route strips/ignores any identity fields;
   only the dimension/score/month/note pass through; agency identity is
   hash-anonymized in the service layer (already implemented). `note` gets a
   length cap (280 chars) and the same PII-scrub treatment as message
   metadata (FND-0326 scrubber at the boundary).
4. **Anonymity is non-reversible at the surface:** responses never echo
   contributor identity; queries aggregate only.
5. **Audit:** every accepted rating is already mirrored into the RULE_015
   chain — consent acts are auditable without being linkable.

## Implementation order (next tranche)

Route + Pydantic models + consent validation + note scrubber + contract
tests → frontend checkbox on the ratings card. Estimated: half a day.

## Revisit triggers

- DPDP counsel review changes consent mechanics (per-act vs session-level).
- Product adds identity attribution ("verified traveler" badges) — that
  reintroduces identity and reopens this decision.
