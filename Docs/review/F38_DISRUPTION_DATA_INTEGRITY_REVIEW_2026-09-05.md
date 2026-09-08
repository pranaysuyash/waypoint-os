# F-38 disruption data integrity and verification review

**Date:** 2026-09-05
**Status:** partial; removal of fabricated alerts observed, residual contract open.
**Lifecycle owner:** `FINDINGS_REGISTER_2026-08-31.md::F-38`.

## September 8 current-source refresh and implementation refinement

A bounded Luna/high read-only review reconfirmed all nine residual requirements
against the current router and storage facade. No F-38 code was changed in this
continuation. The current full backend run is tracked separately in execution
status; a green aggregate count would not verify these missing regressions.

Two implementation assumptions were resolved from source:

- `TripStore.list_trips` supports limit/offset, but file storage silently skips
  unreadable rows and orders reverse filenames; SQL orders only creation time,
  without an ID tie-breaker. A successful short list is not evidence of a
  complete readable agency corpus. Adding a loop around the existing list
  cannot repair that information loss or guarantee stable concurrent paging.
- No implemented `resolve_trip_window`, `TripWindow`, or `in_trip_basis` helper
  was found. `services/inbox_projection.py::_date_window_value` resolves a
  display phrase, not authoritative start/end dates. E-9 is a design dependency,
  not a reusable runtime resolver. Do not fabricate a dependency on it or treat
  the legacy social-inbound flat packet fields as the canonical date model.

**Accepted implementation direction:** keep one canonical radar/store and
introduce an explicit read envelope with healthy `alerts`, separate
`observed_at`, allowlisted issues and bounded coverage. Event `created_at` is
nullable with known/unknown/invalid provenance. System-generated preview
metadata overrides stored capability claims; source records remain untouched.
Canonical membership resolution owns tenant scope, with optional exact-trip
lookup returning the same 404 for missing/foreign trips.

**Corrected reviewer example:** `coverage.status=complete` must never coexist
with `has_more=true` when status refers to the whole selected agency scope.
Page completion and agency-scan completion need distinct names. Store read
errors or omitted malformed alerts also prevent a whole-scope complete claim.
An offset endpoint must disclose non-snapshot consistency; a tie-breaker alone
does not prevent shifting boundaries under concurrent inserts.

The next coherent implementation package is:

1. Extend the existing persistence facade with a bounded page result that
   preserves safe read-error counts/codes and exhaustion evidence for both
   backends. Define deterministic ordering and explicit concurrency semantics;
   do not add an unbounded scan or a second store.
2. Implement the radar envelope and non-mutating projection, including mapping
   validation before field access, time/identity diagnostics, canonical tenant
   scope and system-owned capability fields. Keep all-stored-alerts as the
   existing default for this integrity slice; do not hide known disruptions
   using an unimplemented date resolver. E-9 in-window prioritization remains
   a separate documented product decision.
3. Migrate the two known test consumers (wave F-30–F-40 and strategic phases
   6–9), preserving exact seeded identity and rebooking-denial assertions.
   Add more-than-100-trip, unreadable-file, concurrent-boundary, mixed-invalid,
   sensitive-sentinel, forged-capability and real-auth positive/negative cases.
   Review actual serialized schema twice and regenerate only artifacts that
   genuinely derive this router; no current frontend consumer/type was found.
4. Document the response migration and operator recovery. Unknown external
   consumers are a release/migration uncertainty, not proof of absence.
   Malformed source records are preserved; no invented timestamp, silent
   ownership reassignment, provider feed or live rebooking is introduced.

This refines the existing F-38 package rather than opening a competing ledger.
F-38 remains partial/P1. The separate concierge disruption surface uses another
business input and is not merged merely because its endpoint name is similar.

## Objective, scope and evidence

Operators need to distinguish no disruption from unreadable disruption data,
and known event time from an inferred observation time. Removing a default
CRITICAL cancellation is useful, but is not sufficient if the replacement can
hide alerts or invent freshness. User value is reliable risk visibility; team
value is explainable recovery; internal value is one truthful projection of
stored evidence with explicit completeness and capability boundaries.

This review covers the current disruption router, stored-alert fixtures and
the full-suite failure. Main owns this evidence record; the delegated reviewer
was read-only. No product changes below are attributed to this team. No provider
connection, customer record review, production test or deployment was performed.
Operating 8.0, Review 1.1, Testing 1.1, Security/Privacy/Safety 1.0 and
Documentation 1.1 govern the review. The current execution overlay supersedes
historical readiness summaries for the receipts below.

Source checkpoint, SHA-256:

- `spine_api/routers/disruption_radar.py`:
  `87c3eb44d504a354f769c34f9e51b968261e96f79ed6e35c13934f6de37d32d8`.
- `tests/test_strategic_phases_6_to_9.py`:
  `63573604c21c0ba2b001c90d3a90ebc9e9ceb31525a51a51f5705d9d80867c2f`.

The full backend run, session `27931`, ended **exit 1: 1 failed, 3,817 passed,
44 skipped, 8 warnings in 886.97s**. The strategic-phases lifecycle test raised
a Pydantic validation error because `DisruptionAlert.created_at` was missing.
Source changed during that run: the handler now backfills timestamps/catches
errors and the test now explicitly supplies `created_at`. A later selected
retry, session `19827`, passed **8 tests, 3,854 deselected in 31.43s**, exit 0:

```bash
USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -k 'strategic_phases_6_to_9 or f31 or f38' -p no:cacheprovider
```

This is local selected-test evidence (Tier 2/3, S1 depending on the exercised
boundary), not an S2 regression for missing timestamps: the passing test changed
its fixture and no longer exercises that condition. It is not a new full-suite,
production-auth or provider receipt. The full-run source fingerprint mismatch
is preserved in `EXECUTION_STATUS_2026-09-04.md`.

## Current findings and required work

All implementation findings below are Tier 1 source observations; consequences
are inferred unless a runtime receipt is explicitly stated. These are scoped
F-38 subrequirements, not another lifecycle register.

| Requirement / risk | Source evidence | Required behavior and falsifying test |
|---|---|---|
| Preserve unknown event time — high | `disruption_radar.py:102-103` uses trip update time or request time as missing event `created_at`; field at 35 is an unconstrained string | Define known/unknown/invalid event time separately from observation time, with provenance. Repeated requests and unrelated trip edits must not make an old alert newly created. Test missing/null/empty/invalid/valid time and clock changes. |
| Never report an incomplete scan as authoritative empty — high | `.items()` at 101 precedes the try; validation failures at 104-107 are caught and rows omitted from a successful bare list | Validate mapping shape before accessing fields. Report incomplete coverage explicitly, preserving healthy alerts where the selected response contract permits. Test mixed healthy/malformed, malformed-only, truthy non-mappings, empty mappings and absent data. Response omission is observed; persistent deletion is not claimed. |
| Redact validation diagnostics — high | Warning at 107 formats the full exception; Pydantic errors may contain stored input | Emit allowlisted error codes/field paths and a suitable correlation ID, not raw records or exception strings. Test a sensitive sentinel in malformed input and assert it is absent from logs and client diagnostics. |
| Derive capability truth from the system — high | Sanitization retains all model fields, including overridable `reality_tier`, `provider_connected`, `effects` | Stored preview fields cannot assert a connected provider, executed effects or higher evidence tier. Test attempted metadata promotion and preserve explicit unperformed effects. |
| Validate owning-trip identity — high | Alert's stored `trip_id` is not checked against containing trip; F-38 fixture saves `trip_x` inside a differently identified trip | Bind or reconcile the association explicitly; reject/flag contradictory identity. Test exact returned trip/disruption identities, not only list length. |
| Enforce authenticated tenant scope — high | Header/test-agency selection remains at 78/87; SQL list scopes RLS from the provided agency | Extend the canonical membership-derived resolver, with the production-equivalent test requirements in the F-31 package. Prove anonymous denial, authenticated positive control and spoofed cross-tenant header denial. This weakness predates the new timestamp fallback. |
| Make tests attributable and isolated — medium | Strategic test uses a fixed agency and selects the first item from a list with `len >= 1` | Use isolated agencies/storage or select the exact newly seeded identity. Historical stored rows must not satisfy a test for a different newly seeded alert. |
| Bound and disclose scan coverage — high | The handler calls `TripStore.list_trips` without pagination; facade and file/SQL implementations default to 100 trips (`persistence.py:471/1104/1893`) | Define stable pagination or explicit bounded coverage; do not imply all agency trips were scanned. Test more than 100 trips with the only alert beyond the first page, and concurrent page-boundary changes. Do not replace the cap with an unbounded materialization. |
| Retain original trip-window scope — medium, E-9 dependency | Original F-38 called for in-window scoping; the current handler has no time/window or single-trip filter | Revalidate the existing E9.1/E9.3 resolver/scope plan; test before/start/end/after-window, missing/uncertain window and explicit trip scope using source-qualified date evidence. Unknown trip dates must not silently hide a known stored disruption. Default scope is an explicit operator/product decision, not implied by removing fabricated alerts. |

The original scope work is retained through the
[E-9 trip-window exploration](../exploration/E9_IN_TRIP_DISRUPTION_WIRING_2026-09-02.md).
That document's September 4 default-fabrication description is historical after
the current removal. Its derived-window and evidence-basis design remains a
dependency to revalidate, not implemented truth: avoid a second date resolver
or treating an uncertain extracted window as provider-confirmed travel. The
seven newly reviewed integrity/test requirements plus pagination and the
retained E-9 scope make **nine explicit requirements** in this package.

## Implementation sequence and alternatives

1. **Define the complete read contract and migration.** Inspect all consumers,
   generated schemas and snapshots. A bounded search of `frontend/src` found
   no direct `/disruptions/alerts`, `DisruptionAlert` or `active_disruption`
   consumer, but that is not proof that no external consumer exists. Prefer a
   response that retains valid alerts while explicitly exposing incomplete
   coverage and sanitized issues. Preserve unknown event time. Define how
   clients must display incomplete coverage and what operators reconcile.
   Specify pagination/coverage and coordinate optional trip/window scope with
   E9.1/E9.3, preserving visibility for known alerts with unknown trip dates.
2. **Implement the canonical projection with failing-first regressions.** Keep
   the existing router/store; validate mapping, time and identity before
   projection. Derive capability metadata from actual system capability. Do not
   create a replacement data store or silently persist inferred timestamps.
   Test every row in the table, plus a deliberate mutation restoring false-empty
   behavior or stored capability promotion (S3).
3. **Close tenant and HTTP integration.** Migrate the router to canonical tenant
   resolution and production-equivalent fixtures; prove tenant/RLS agreement.
   Verify actual serialized response and incomplete/error behavior, then update
   generated contract artifacts and all identified consumers. Require two
   schema-review cycles and a fresh full backend gate on the final candidate.
4. **Document operator recovery and release.** Distinguish no alerts, partial
   coverage, unreadable evidence and provider unavailable. Correct stored
   evidence only from an authorized factual source; preserve original evidence
   and record actor/reason. Provider feeds, production rollout and live rebooking
   remain separate gates, not implied by this local read-path repair.

**Reject:** filling missing creation time with now without provenance; catching
everything and returning `200 []`; trusting stored claims of provider authority;
weakening tests to accept any historical alert; retrying the full suite until a
green count substitutes for a defect regression.

**Accept with modification:** no fabricated default cancellations and tolerance
for incomplete legacy data, provided tolerance means explicit uncertainty and
recoverability rather than hidden omission. Under an unchanged bare-list API,
an explicit incomplete-data error is safer than false empty; that alternative
loses healthy-alert availability, so it is not the preferred final response
contract without an operator-impact assessment.

**Recovery:** no deletion or persistent backfill was performed. Before response
migration, preserve old field semantics and identify affected clients; recovery
must not reintroduce fabricated cancellations, freshness or silent omissions.
Revisit after source drift, consumer discovery or provider adoption. This review
does not authorize branch changes, external effects or a deployment.

## Verdict and next gate

F-38 is **partial**, not closed: the default-fabrication branch is gone, while
data integrity, uncertainty, authorization and regression coverage remain open.
The earlier remediation addendum is a historical implementation claim, not
proof of the complete current contract. Correctness, architecture and doctrine
review all retain these residual requirements. No feature-ready or launch-ready
claim is made.

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## Verification and review receipt

Six changed documentation files passed Markdown lint with zero issues before
the final pagination/window-scope refinement. Main's canonical lifecycle check
returned 145 rows / 91 open / 53 closed / one deferred / zero warnings; the
40 lifecycle-parser tests passed in 7.91s. These instrument checks do not prove
the proposed product requirements. The research package retains its separate
Allianz HTTP 403 link limitation; no full documentation-link pass is claimed.

An initial CLI invocation incorrectly supplied `FINDINGS_LIFECYCLE` (the policy
document) as a second register; the checker correctly rejected it with two
violations. Main corrected the arguments to the canonical register and CI's
actual historical companion `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`; both
the canonical-only and CI-companion checks passed. No checker was weakened.

Independent review accepted the receipt/status boundaries and requested the
retained E-9 requirement and 100-trip pagination coverage now documented above.
Insurance documentation received a separate read-only approval. These are
documentation reviews, not approvals of the unimplemented product contracts.
