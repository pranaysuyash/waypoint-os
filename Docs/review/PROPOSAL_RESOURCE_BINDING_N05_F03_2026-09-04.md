# Proposal resource binding — N-05 / F-03 bounded implementation

**Date:** 2026-09-04\
**Status:** locally implemented and verified; deployment/release gates remain open\
**Owner/lane:** proposal public-resource boundary\
**Related:** `F-02`, `F-03`, `N-05`, `PT-01..PT-06`, `LR-B07`\
**Canonical implementation:** `spine_api/routers/public_proposals.py`

**Adjacent public implementation audited:** `spine_api/routers/trust_scorecard.py`

## Problem observed

Before this slice, `/api/public/proposals/{token}` verified an HMAC claim and
then generated a fixed, in-memory Italy itinerary, traveler name, prices, and
option catalogue. The signed `trip_id` and `agency_id` were not used to
resolve or authorize a persisted proposal resource. Consequently, a validly
shaped claim could receive plausible proposal content even when the referenced
trip was absent or belonged to no persisted agency resource.

This was a truth-boundary and tenant-boundary defect, not merely a demo-copy
issue: possession of a signing capability does not establish that the resource
exists, is owned by the claimed agency, or is proposal-ready.

## Chosen first-principles behavior

The public route now applies two separate gates:

1. **Capability gate:** existing HMAC, TTL, canonical agency-field, and
   revocation verification remains authoritative.
2. **Resource gate:** the verified `trip_id` and decoded `agency_id` are passed
   to `TripStore.get_trip_for_agency`. Only an agency-matching persisted trip
   is then projected with `TripStore.get_trip_for_public_access`.

The persisted projection requires observed destination, recommendation title,
finite non-negative recommendation cost, and a positive date-derived duration.
Missing or malformed proposal content returns the same public 404 boundary as
an absent resource. No generic destination, price, itinerary, traveler name,
or options are invented. The safe projection uses the neutral label
`Traveler` rather than exposing an unobserved or unapproved name.

The three historical rich fixtures remain available only when
`PUBLIC_PROPOSAL_DEMO_MODE` is explicitly set to `1`, `true`, or `yes`.
This is a local compatibility seam, not a production fallback. An allowlisted
token without that flag is denied.

## Files changed in this lane

- `spine_api/routers/public_proposals.py`
  - separated `_build_demo_proposal` from the normal path;
  - added explicit `_demo_mode_enabled` gate;
  - added canonical agency claim recovery after verification;
  - added finite-price and date-derived-duration validation;
  - added persisted agency-bound, traveler-safe projection;
  - changed `_get_or_create_proposal` so signed claims cannot mint content.
- `tests/test_public_proposals.py`
  - explicitly enables the legacy fixture seam per test;
  - proves the seam is denied when the flag is absent;
  - proves a valid signed token resolves only when an agency-bound persisted
    projection exists;
  - proves missing/foreign resources fail closed;
  - updates the former synthetic HTTP happy path to assert the new contract.
- `tests/test_p1_findings_hardening.py`
  - explicitly enables the fixture seam where the historical lifecycle test
    needs it;
  - updates the unpersisted signed-token assertion to the fail-closed contract.
- `spine_api/routers/trust_scorecard.py`
  - removes fabricated public projection defaults;
  - rejects malformed public-link expiry values instead of serving indefinitely.
- `tests/test_trust_scorecard_honesty.py` and `tests/test_trust_scorecard_router.py`
  - cover unknown-fact preservation, malformed-expiry denial, and issuance
    round-trip back to the requesting agency-owned trip.
- `spine_api/core/startup_assertions.py` and `tests/test_startup_assertions.py`
  - reject `PUBLIC_PROPOSAL_DEMO_MODE` in staging/production while preserving
    explicit local/test usage.

## Verification evidence

Executed from the repository root on 2026-09-04:

```text
PROPOSAL_SIGNING_KEY=test-proposal-signing-key-for-pytest-32bytes \
DATABASE_URL=postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os \
TRIPSTORE_BACKEND=file ENVIRONMENT=test \
.venv/bin/pytest -q tests/test_public_proposals.py tests/test_p1_findings_hardening.py
50 passed in 2.84s

PROPOSAL_SIGNING_KEY=test-proposal-signing-key-for-pytest-32bytes \
DATABASE_URL=postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os \
TRIPSTORE_BACKEND=file ENVIRONMENT=test \
.venv/bin/pytest -q tests/test_public_proposals.py tests/test_p1_findings_hardening.py \
  tests/test_trust_scorecard_honesty.py tests/test_trust_scorecard_router.py \
  tests/test_public_proposal_http.py
  65 passed in 5.47s

.venv/bin/ruff check spine_api/routers/public_proposals.py \
  spine_api/routers/trust_scorecard.py tests/test_public_proposals.py \
  tests/test_p1_findings_hardening.py tests/test_trust_scorecard_honesty.py \
  tests/test_trust_scorecard_router.py tests/test_public_proposal_http.py
All checks passed!

git diff --check -- spine_api/routers/public_proposals.py \
  spine_api/routers/trust_scorecard.py tests/test_public_proposals.py \
  tests/test_p1_findings_hardening.py tests/test_trust_scorecard_honesty.py \
  tests/test_trust_scorecard_router.py tests/test_public_proposal_http.py \
  Docs/review/PROPOSAL_RESOURCE_BINDING_N05_F03_2026-09-04.md
pass
```

Startup configuration gate:

```text
.venv/bin/pytest -q tests/test_startup_assertions.py tests/test_production_boot.py
49 passed in 2.61s
```

Evidence classification:

- **Tier 1:** static inspection confirms no normal-path generic Italy fixture
  construction and confirms the agency-filtered persistence call.
- **Tier 2 / S1:** 65 focused tests pass, including valid, malformed, expired,
  revoked, demo-gated, missing-resource, and agency-bound paths.
- **Tier 2 / S1 (adjacent route):** the combined proposal/public-resource
  suite passes **65 tests**, including persisted-token public projection,
  acceptance, unknown-resource, and malformed-expiry cases on both read and
  acceptance paths.
- **S2 intent:** the two old tests failed before the assertion correction
  because they encoded the removed fabricated fallback; they now pass against
  the corrected contract. A full mutation run was not performed in this lane.
- **Unknown:** this does not prove hosted multi-replica behavior, real provider
  issuance, browser behavior, or production secret/revocation deployment.

## Adjacent route decision (ACCEPT+MODIFY / DEFER)

The separate `/api/v1/proposals/generate-link` and
`/api/v1/proposals/token/{token}` route was re-opened during this lane. It
already persists a random capability token (and SHA-256 lookup hash) on the
agency-filtered trip, then resolves the public view through
`get_trip_for_public_access`; it does not use the HMAC route's in-memory
registry. That persisted token-to-trip relationship is a valid capability
model for the current contract.

The route did, however, emit invented defaults for missing facts (`Bespoke
Travel`, `TBD`, party size `1`, and current time), and malformed expiry values
were previously treated as valid. Those behaviors are now removed: unknown
values remain `null`, and malformed expiry fails closed with 404. This is
covered by `tests/test_trust_scorecard_honesty.py`.

The two token formats should not be silently merged in this bounded lane. The
long-term decision is to select one canonical public proposal issuance path and
migrate the other with an explicit compatibility window, database migration,
revocation semantics, and browser/client contract review. Until that decision,
both routes are documented and each independently binds to persisted resource
state.

## Remaining boundary

The explicit demo seam is now rejected by the local startup assertion in
staging/production. Hosted configuration/secret-manager proof is still open.
PostgreSQL-backed proposal-resource issuance, durable acceptance state,
cross-replica revocation, and external/browser evidence remain open launch
work. The current trust-scorecard route also needs a future check that link
generation is restricted to proposal-ready lifecycle states; changing that
policy is a product/owner decision because existing intake links are used for
early-stage workflows.

No Git staging, commit, push, reset, checkout, stash, or cleanup was performed.
