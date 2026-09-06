# Insurance timing and eligibility contract — F-31

**Date:** 2026-09-05
**Status:** researched implementation requirements; product implementation incomplete.
**Lifecycle owner:** `../review/FINDINGS_REGISTER_2026-08-31.md::F-31`.
**Decision:** do not promote a deposit-countdown patch to insurance eligibility.

## Scope, value and method

Question: what must the quote route know before showing a deadline or an
affirmative waiver/CFAR eligibility result? This bounded review covers the live
insurance router, the new F-30–F-40 test module, deterministic date arithmetic,
and first-party US product pages. It is not advice about a person's coverage,
an approved insurance product selection, a jurisdiction-wide legal assessment,
or a provider quote. No customer/provider state was read or changed.

User value is avoiding false reassurance about coverage. Team value is a
testable policy contract instead of repeated countdown fixes. Internal value is
preserving missing/invalid/expired/verified states and their evidence lineage.

Main agent applied Operating 8.0, Review 1.1, Research 1.0, Testing 1.1,
Security/Privacy/Safety 1.0 and Documentation 1.1. The independent reviewer
inspected source/tests and reproduced arithmetic without importing the app.
Main independently repeated those arithmetic checks and inspected primary
pages. Two Travelex pages are one provider evidence chain, not two independent
authorities. Search snippets and old policy PDFs were discovery only.

Existing [FIN-REAL-005 claims draft](FIN_SPEC_INSURANCE_CLAIMS.md) concerns
post-loss evidence assembly, not this quote/eligibility contract. Neither draft
proves actual coverage, dispatch, insurer acceptance or claim payment.

## Source checkpoint and transient changes

Reviewed source SHA-256 at the main arithmetic check:

- `spine_api/routers/insurance.py`:
  `61390d295f91ee49e11c0563ea4ef8efa975b62fa4438d9ef2466bfa0c0898cf`.
- `tests/test_register_wave_f30_f40.py`:
  `0b009beb964d4ef377eefab91f3753a64ca411e39d18f2396efffd5d2cbe9916`.

The checkout is changing outside this delivery lane; reread before implementing.
The earlier undefined `Header` import and an intermediate `max(int, timedelta)`
expression have been corrected in later observed source. They are historical
failures, not current defects. A subsequent two-router Ruff check passed;
neither that result nor source inspection proves the full app/HTTP contract.

## Observed defects and verification boundaries

| Concern | Evidence at reviewed source | Consequence and required contract |
|---|---|---|
| Invalid versus missing deposit | `insurance.py:84-95` resets invalid input to quote time; `test_register_wave_f30_f40.py:104-111` expects that fallback | The test encodes the misleading behavior. Invalid supplied evidence must not silently become a new eligibility window; reject it or represent invalid/unknown explicitly. |
| Affirmative waiver claim without proof | All three plans set `pre_existing_waiver_eligible=True` near 111/123/135 regardless of date | A timing estimate cannot establish coverage. Preserve unknown/not evaluated separately from ineligible and verified eligible. |
| Date-zone inconsistency | Deadline calendar date uses input offset; current calendar date uses UTC near 99 | The same instant can produce different remaining days. Choose elapsed duration or calendar days in a named policy zone, then normalize consistently. |
| Parseable extreme input | Date addition near 96 is outside parse exception handling | `9999-12-31` parses but adding 14 days raises `OverflowError`; bound supported dates and return a deliberate contract error. |
| Input provenance | Quote function accepts `trip_id` but does not resolve stored deposit evidence | Omitted request field does not establish no deposit recorded. Bind authenticated trip facts where applicable and show source/verification state. |
| Auth proof | `Depends(get_current_agency_id)` is now declared; new tests force auth bypass and use an agency header | Wiring is observed, but anonymous denial, valid membership, spoofed headers and cross-tenant attachment are not verified by those tests. |
| Attachment contract | Body includes a `trip_id` while the handler uses the path ID; success test only asserts 200 | Define/reject path/body disagreement; verify actual persisted fields, actor/audit identity, idempotency and rejected writes. |

### Follow-up: is the canonical dependency the long-term solution?

The user's annotation asked whether replacing the missing `Header` reference
with the canonical agency dependency was a first-principles, long-term solution.
**Verdict: accept the shared dependency, not an end-to-end closure claim.**
Tenant identity, action permission, resource access and audit attribution are
different invariants; satisfying one does not establish the others.

Live recheck on 2026-09-05 retained the insurance source hash above.
`spine_api/core/auth.py` SHA-256 was
`84a70d7ad5826eeacac7db550bb1f768c21201da21c82c7226576d9d85d0755d`.
Additional Tier 1 findings and implementation obligations:

| Invariant / task | Observed evidence | Acceptance and canonical implementation seam |
|---|---|---|
| Action permission | Attach handler declares agency resolution but no action-specific permission; `auth.py` already defines `ROLE_PERMISSIONS` and `require_permission` | Apply the existing write permission/resource-assignment contract. Prove viewer denial, authorized writer success, and assigned-versus-unassigned behavior where that role is supported. Membership alone must not grant mutation rights. Do not build a second permission framework. |
| Authenticated audit actor | `insurance.py:174` passes `user_id=agency_id` | Derive actor from the authenticated user/membership and retain agency as a separate tenant dimension. Verify two users in one agency produce distinct actor identities and neither body nor headers can spoof them. |
| Production-equivalent security tests | `auth.py:182` accepts an agency header when `PYTEST_CURRENT_TEST` is present, independently of the explicit auth-bypass flag | Remove implicit test-framework detection from the production authority decision through a coordinated fixture migration. Use explicit fixture overrides for behavior tests, and exercise the unmodified production resolver in security tests. Simply disabling `SPINE_API_DISABLE_AUTH` under pytest is insufficient. |
| Durable mutation plus audit | Handler invokes `TripStore.save_trip` and then `AuditStore.log_event` as separate calls | Trace both real persistence implementations before selecting a transaction/outbox/recovery design. Demonstrate policy and audit behavior on save failure, audit failure, retry and concurrent updates. Separate calls are observed; complete storage semantics have not yet been audited here. |

These are F-31 subrequirements, not newly closed findings or a duplicate
lifecycle register. The historical import crash is repaired in current source;
that does not resolve the product, authorization or persistence contract.

Independent follow-up verified that SQL trip save commits separately
(`persistence.py:1022`) and `AuditStore.log_event` appends a JSONL event using
the supplied `user_id` (`persistence.py:2398-2434`). Main inspected those seams.
This establishes separate durability boundaries, not a runtime failure receipt.
The existing version-scoped trip update is a candidate concurrency seam;
`core/audit.py` is not automatically an atomicity fix merely because it provides
an audit context. Its best-effort behavior needs explicit review.

The pytest condition does **not itself bypass upstream authentication**. It
overrides the tenant returned after membership resolution, which can also
disagree with the RLS context already set from membership. Security tests must
assert agreement among principal, membership agency, returned agency and RLS
context. No anonymous production exploit is claimed from this static evidence.

`require_permission` already returns a FastAPI dependency; the existing
`membership=require_permission("trips:write")` convention should be reused,
not wrapped again in `Depends`. Assigned-junior attachment rights must follow
an explicit action policy; blindly requiring the broader permission would
silently reject their separate `trips:write:assigned` capability.

Main's standard-library-only check, with `now=2026-09-05T12:00:00Z`, compared
`2026-09-04T23:30:00-02:00` with its UTC representation. They are equal instants,
but the current date formula returns **13 and 14** days respectively. A second
check reproduced **OverflowError** for `9999-12-31 + 14 days`. These are Tier 2
arithmetic counterexamples, not route-level HTTP receipts. Other findings above
are Tier 1 source/test observations with consequences explicitly inferred.

## Primary-source research and counter-evidence

Pages were opened and inspected on 2026-09-05. No stable publication/update date
was established for the Travelex summaries. They are current observations of
published product descriptions, not the policy forms applicable to a customer.

| Claim investigated | Inspected primary source | Evidence and limitation |
|---|---|---|
| Every CFAR purchase window is 14 days | [Travelex Ultimate CFAR upgrade](https://www.travelexinsurance.com/travel-insurance/upgrades/cancel-for-any-reason) | Published summary specifies purchase within 21 days of first trip payment, other purchase/cancellation conditions, and policy/state variation. This counterexample rejects a universal 14-day constant; it does not justify using 21 days universally. |
| Deposit age alone proves a pre-existing-condition waiver | [Travelex pre-existing-condition coverage](https://www.travelexinsurance.com/travel-insurance/benefits/pre-existing-conditions) | Ultimate summary includes purchase timing, added-cost timing and medical ability to travel; other plans differ. A countdown alone is insufficient. |
| A 14-day rule can apply to a particular product family | [Allianz existing-condition explanation](https://www.allianztravelinsurance.com/travel/medical/existing-medical-conditions-coverage.htm) | Describes 14 days or the period in the plan, plus other conditions and US scope. Extracted page also includes a test-environment banner/template text; provenance of that banner was not resolved. Use as qualified reference, not an adopted production rule source. |

The Travelex CFAR page explicitly makes the policy controlling over its website
summary. It also separates subsequent-arrangement deadlines from the initial
purchase window. These distinctions reinforce a versioned, plan-specific rule
model rather than one deadline field reused for unrelated benefits.

**Research conclusion:** the original finding was directionally right about
deposit provenance but over-specific about a universal rule. CFAR and a
pre-existing-condition exclusion waiver are separate benefits with separately
applicable conditions. Determine the actual product, jurisdiction, version and
facts before returning an eligibility assessment.

## First-principles and long-term implementation package

### 1. Input and time semantics — implement after coordinating source ownership

- Canonical surface: existing request model and quote route, plus their tests.
- Distinguish omitted, blank, malformed, out-of-range, future and sourced dates.
- Reject invalid submitted input or return an explicitly typed invalid result;
  never silently reset historical timing to now.
- Choose a documented temporal contract and inject/freeze the clock for tests.
  Do not mix input-offset dates with UTC dates.
- Acceptance: equivalent instants agree; month/leap/year boundaries, exact expiry,
  future dates, maximum supported date and invalid text cannot create a false
  fresh window or an unhandled server error.
- Non-goal: no live policy purchase, claim submission or eligibility guarantee.

### 2. Evidence-bearing result contract — design and implement end to end

- Reuse the existing quote response; distinguish illustrative price, timing
  evaluation and provider/policy eligibility rather than adding a shadow quote API.
- Represent not evaluated/unknown/invalid explicitly. Do not replace unconditional
  true with unconditional false: that would turn unknown into a negative claim.
- Associate rule evaluation with provider, product/plan version, jurisdiction,
  source/reference, applicable time zone, evidence inputs and unresolved predicates.
- Keep CFAR and pre-existing-waiver predicates separate. A sourced rule may
  establish one condition without establishing every condition for coverage.
- Minimize health-related data: prefer opaque evidence references or a scoped
  provider determination over collecting diagnosis details. Define access,
  retention and redacted telemetry before adding sensitive rule inputs.
- Identify actual API consumers before migration; a bounded frontend search
  found no direct references to the current deadline/eligibility fields, which
  is not proof that no external consumer exists. Regenerate canonical API types
  and test real response shapes at the BFF/API boundary where consumed.
- Acceptance: static demos cannot emit verified eligibility; missing facts stay
  visible; the operator can explain the result and required next evidence.

### 3. Authenticated attachment and audit — extend existing tests

- Use isolated fixtures with auth enabled and real membership/agency resolution.
- First remove the implicit `PYTEST_CURRENT_TEST` authority switch via explicit
  fixture migration; a bypass-disabled pytest run alone is not production parity.
- Extend existing role/action/resource permissions, including assignment checks
  where applicable, and bind the audit actor to the authenticated principal.
  Test viewer denial and two distinct users within one agency as well as tenants.
- Test anonymous/invalid-token denial, valid positive control, header spoofing,
  cross-tenant trip access and path/body identity disagreement.
- Assert no policy-state mutation or success audit on rejection; retain safe
  denied-attempt security auditing without sensitive payloads. Assert persisted
  fields and authenticated attribution on success; test replay/conflicting writes.
- Trace canonical file/SQL save and audit implementations and their failure
  semantics. Choose one durable consistency/recovery contract; test injected
  save/audit failure, retries and stale concurrent changes before closing it.
- Distinguish user/operator-recorded policy details from provider-verified binding
  or coverage. Store verification state/provenance and tenant-bound plan/policy
  association. HTTP 200 plus persistence is not confirmation of coverage; add
  positive tests that explicitly preserve unknown/unverified attachment states.
- Existing auth-bypass tests remain local behavior tests, not security proof.

### 4. Provider/rule adoption and release — separately gated

- Product/operator owner selects supported plan/jurisdiction scope; qualified
  insurance/legal review validates policy interpretation where required.
- Obtain versioned policy forms and approved provider contract evidence, including
  changes, invalidation, unavailability and operator escalation.
- Test contract migration/recovery before exposing changed response semantics.
  Keep an explicit not-ready result when policy facts or provider evidence are absent.
- No production deployment, provider adoption or external transaction is authorized
  by this research record. A1-1 Git delivery and EV-11 remain separate.

Suggested focused commands after fixture/isolation review:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_register_wave_f30_f40.py -k 'f31' -q -p no:cacheprovider
.venv/bin/ruff check spine_api/routers/insurance.py tests/test_register_wave_f30_f40.py
```

The first command is a proposed next check, not a claimed pass. Add failing-first
regressions for the revised contract and a mutation that restores the invalid-date
fallback or unconditional eligibility to ensure the critical checks fail.

## Alternatives, recovery and completeness

- **Reject:** merely import `Header`, move parentheses, or anchor every response to
  a deposit while retaining unsupported affirmative eligibility. These repair
  symptoms, not the end-user claim.
- **Reject:** globally replace 14 with 21. The inspected counterexample proves
  variation; it does not select the product this application should sell.
- **Accept with modification:** retain useful deterministic quote illustrations
  behind explicit evidence states and a plan-specific rule contract.
- **Preservation:** no changing product source was overwritten by this review.
  The original finding asserted that the deadline ignored deposit date and
  universally required 14 days from deposit. That assertion is retained here
  as historical rationale and corrected above, not silently promoted to policy.
  Prior failure receipts remain in the request trace. Existing insurance claims
  research is linked, not replaced.
- **Established:** source-level claim/input gaps and arithmetic counterexamples;
  published product variation sufficient to reject a universal timing rule.
- **Unknown:** actual offered policy, jurisdiction, purchase evidence, external
  consumers, authenticated HTTP behavior and provider verification.
- **Not researched:** global insurance regulation, licensed-distribution posture,
  individual medical eligibility, claims adjudication or actual pricing accuracy.
- **Revisit trigger:** source changes, product/plan selection, policy revision or
  provider integration. Re-run review against the actual candidate before closing.
- **Verdict:** F-31 remains partial; direction needs the revised contract above.
  There is no insurance feature-ready or launch-ready claim.

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## Documentation verification receipt

The nine-document continuation lint passed with zero issues. A focused link
check reported 17 total, 15 OK, one excluded and one error: the Allianz article
returned HTTP 403 to Lychee, although the research browser tool returned its
content. This is a documented access/provenance limitation, not a claim that
all links pass. The source is retained with its uncertainty; no 403 acceptance
override or blanket exclusion was added. Travelex's inspected plan-specific
counterexample independently supports rejecting the universal 14-day premise.
Retry link availability or verify an authoritative replacement before declaring
the whole documentation delivery gate green.

Independent documentation review accepted the scoped research conclusion and
requested the denied-attempt-audit, recorded-versus-verified attachment, and
sensitive-input minimization refinements now included above.
