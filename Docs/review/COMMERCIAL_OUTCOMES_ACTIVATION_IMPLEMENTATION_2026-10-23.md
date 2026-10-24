# Commercial outcomes and first-value activation implementation

Date: 2026-10-23 (Asia/Kolkata). Owner: outcome/activation implementation lane.
Status: implementation in progress. No release or real-user acceptance claim.

## Authorization, scope, and boundaries

The current user's request to implement the audit tasks authorizes reversible
project-local implementation, tests, and documentation. This lane owns analytics
models/reducers/review behavior, the canonical analytics router's read paths,
the generated analytics client contract, the Insights and Overview consumers,
and their regression tests. The parent owns the shared findings register,
exploration map, persona council, browser captures, final integration review,
and the public proposal/fulfillment work. No Git mutation, provider call,
customer message, financial movement, deployment, destructive cleanup, or
persistent developer-database change is authorized by this lane.

The intended outcomes are:

- For an agency operator: distinguish customer budgets, confirmed customer
  commitments, recorded customer collections, and agency earnings without
  invented dollars, conversion, delivery, or payment claims.
- For the agency owner: see commercial progress supported by the right
  evidence; avoid making decisions from model quality or internal review
  activity presented as business results.
- For a new solo operator: reach a verified useful brief, with the next action
  still visible when the first inquiry is blocked.
- For maintainers: retain one projection and one generated contract, with
  regression tests at the producer, reducer, API, and rendered consumer seams.

Stop conditions are contested shared ownership, evidence that a proposed
change would lose useful behavior, an effect outside the authorized envelope,
or a required business/accounting policy that cannot be inferred responsibly.
Ordinary implementation choices inside the envelope are not approval gates.

## Current source and consumer map

Current architecture, refreshed from source before editing:

| Meaning | Existing owner | Consumers / limitation |
| --- | --- | --- |
| Canonical inquiry record | `TripStore`, `spine_api/persistence.py` | Analytics router; summaries omit some full-record evidence. |
| Budget | Canonical packet `budget.value` / `budget.currency` | Current revenue reducer mistakenly treats it as booked revenue. |
| Internal review decision | `src/analytics/review.py` | Currently writes `delivered` and claims feedback was sent, without transport evidence. |
| Fulfillment receipt projection | `booking_confirmation` written by `src/orchestration/booking_fulfillment.py` | Current writer explicitly identifies deterministic preview and no provider connection. |
| Durable component confirmation | `BookingConfirmation`, `confirmation_service` | Records/verification are useful evidence of a component, but have no commercial amount/currency fields. |
| Customer payment tracking | `booking_data.payment_tracking` | Explicit `tracking_only=True`; operator-recorded amount, status, reference/proof, currency. |
| Advisor payout/reconciliation | `commission_reconciliation`, `AdvisorPayoutStore` | Advisor movements and a fixed assumed agency commission rate do not establish actual earned agency revenue. |
| Analytics API schema | `src/analytics/models.py`, re-exported by `spine_api/contract.py` | Canonical generated `frontend/src/types/generated/spine-api.ts`, governance API/hooks, Insights page and RevenueChart. |
| Overview facts | `useOverviewSummary` domain queries | Currently only page-sized lists are available to the guide. |
| Onboarding progress | `EmptyStateOnboarding` click handlers and a global localStorage key | Not tenant-bound, not workflow completion, disappears after a lead is created. |

The planned architecture retains the canonical TripStore and analytics route.
It adds an evidence projection, not a second financial ledger, lifecycle state
machine, or activation store. Completeness belongs to the backend's tenant-bound
read path. UI navigation cannot become proof that work happened.

## Invariants and acceptance obligations

1. An internal quality score, owner review approval, and a lifecycle label do
   not independently establish a booking, customer collection, earned revenue,
   delivered output, or dispatched feedback request.
2. A booking amount requires a durable successful receipt, provenance that
   permits real financial claims, a finite nonnegative amount, and a known
   currency. Preview/sandbox fulfillment remains visible as excluded evidence.
3. Customer collections remain labeled operator-recorded tracking and cannot
   promote the inquiry to booked or become agency earnings.
4. Money aggregates preserve currencies independently. No implicit FX rate,
   USD default, or sum of incompatible units is allowed. Unknown/malformed
   values are counted as missing evidence rather than coerced into real zero.
5. Legacy aggregate keys preserve their public locations but become null when
   no honest scalar can be represented. Consumers must render that uncertainty.
6. Historical approvals and records are preserved. This task does not rewrite
   persisted trips or reclassify old deliveries by bulk migration.
7. New-operator progress derives from canonical persisted work. A saved first
   inquiry remains actionable if important details block the brief. Team
   invitation remains available as an optional collaborative path.
8. A time-range control must state the period the API actually applies. No
   period label may imply an unimplemented date filter.
9. Tenant-bound pagination must cover all records needed by the projection;
   passing only the first 1,000 records is not an aggregate contract.

## Supersession and original intent

No historical documentation or persisted data is a removal candidate. Existing
regressions contain useful coverage for empty data, monthly grouping, status
timing, and team workload; retain and adapt those cases. Only expectations that
encode budget-as-revenue or approval-as-delivery are superseded by explicit
commercial evidence assertions.

The click-based checklist's useful intent is orientation, persistence across
visits, canonical intake/inbox destinations, and a route to team invitations.
All remain in the canonical component. Its localStorage completion authority
is superseded by persisted agency facts: the database survives visits and
isolates tenants. Clicking a link still navigates, but does not complete work.
The old storage key does not need deleting; it simply ceases to be an authority.
No browser profile or other user storage is cleaned.

The approval branch's useful intent is clearing review, preserving reviewer
identity/time/notes, returning useful review state, and recording an audit
event. Preserve those. Synthetic delivery, feedback dispatch, and revenue
implications have no matching effect and are superseded by factual review
metadata. Actual transport producers retain responsibility for delivery proof.

## Capability and doctrine use

The instruction stack was refreshed from `/Users/pranay/AGENTS.md`,
`/Users/pranay/Projects/AGENTS.md`, repo and frontend `AGENTS.md`, the generated
Operating Doctrine 8.2 and context pack, and relevant architecture, testing,
documentation, and AI evaluation guidance. The parent refreshed the context
pack; this lane deliberately does not rerun the generator or install hooks.

Local skills applied: `systematic-debugging`, `tdd-workflow`,
`verification-before-completion`, and `agentic-eval-loop` under
`/Users/pranay/Projects/skills/`. OpenSpace skill searches were attempted, but
did not return within the bounded lookup; the request was cancelled and the
configured canonical local skill files were used. No new skill was authored.

## Research: gross customer value versus agency revenue

Primary-source check on 2026-10-23: the IFRS Foundation explains that principal
versus agent treatment depends on the nature of the promise/control, and that
an agent's revenue is its fee/commission rather than automatically the gross
customer consideration. This supports keeping operational customer value
distinct from agency revenue; it does not decide this application's accounting
policy or establish that a particular agency is principal or agent.

Source: [IFRS Foundation, IFRS 15 post-implementation review staff paper,
principal versus agent considerations](https://www.ifrs.org/content/dam/ifrs/meetings/2023/march/iasb/ap6d-ifrs-15-pir-feedback-other-areas.pdf).
The source is a staff paper, not a bespoke accounting ruling. The software
must avoid inventing an accounting conclusion from this research.

Observed source evidence: the current commission service uses a documented
fixed 10% pool; analytics margin is calculated from heuristic adjustments;
neither is a contract-specific earned-fee record. Existing advisor payouts
measure an outflow to advisors, not agency receipts. The correct immediate
disposition is an explicit unavailable agency earned/realized measure and a
named producer gap. No new parallel manual ledger is justified.

## Research: genuine operator outcome measurement

Canonical existing owners are `Docs/PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md`
and `Docs/research/REAL_WORLD_VALIDATION.md` (Topic 19), with the AI workflow
evidence contract in `Docs/research/AGENTIC_FLOW_EVAL_AUDIT_2026-06-18.md`.
Extend these through a dated addendum linked by the parent's exploration map;
do not create another pilot program or commercial evidence store.

The historical `Docs/audits/PERSONA_SIMULATION_2026-10-21.md` contains simulated
NPS proxies, willingness-to-pay estimates, retention hypotheses, and a strong
product-market-fit conclusion. Preserve it as historical evidence of agent
reasoning, but classify those statements as hypotheses until actual operator
behavior and buying evidence establish them. Browser screenshots and simulated
persona transcripts establish neither a real respondent nor a purchase.

Proposed study, pending actual operator recruitment and consent:

| Question | Observation | Comparison / falsifier |
| --- | --- | --- |
| Does the first inquiry become useful? | From saved raw request to owner-approved useful brief; include blocked/abandoned work. | Fail if approvals mask unresolved required facts, or guidance becomes inaccessible after inquiry creation. |
| Does Waypoint reduce active work? | Operator active handling minutes, interruption/wait minutes separately, across a real inquiry and later follow-ups. | Compare a matched existing workflow; fail if time shifts into correction/review/support. |
| Are outputs accepted? | Accepted unchanged / accepted after material correction / rejected, reviewer reason, input and output revision identifiers. | Fail if quality scores rise while acceptance falls or corrections repeat. |
| Does it reduce clarification burden? | Customer questions sent, replies needed, missing-required-fact count and resolution time. | Fail if fewer questions leave material unknowns or combine incompatible customer facts. |
| Do operators choose to return? | Independent second and subsequent eligible inquiries with assistance level recorded. | Fail if repeat use requires researcher prompting or hidden concierge work. |
| Is business value preserved? | Source-linked quote, accepted terms, confirmed components, cancellations/refunds and actual agency fee/commission records. | Fail if agreement drift, wrong currency, or unsupported margin appears. |

Sample by existing project personas: solo owner, junior with reviewing owner,
and experienced multi-inquiry operator. The parent resolves canonical seats;
these are study segments, not invented authority identities. Include messy
follow-ups, a blocked inquiry, and at least one correction/retry per operator.
Use redacted inputs, minimum necessary identifiers, clear consent, and the
existing workflow-unit evidence record. No outreach is authorized in this task.

Do not adopt the old numerical study targets as proven thresholds. Before a
real pilot, the owner chooses participants, supported destination/workflow
scope, assistance conditions, data retention/consent, price experiment, and
business acceptance criteria. Record observed denominators and uncertainty;
avoid inferring retention from a short test or willingness to pay from praise.

## Verification log

- Baseline: parent owns the isolated full-backend and frontend baseline.
- RED fixture: `tests/test_commercial_outcome_truth.py` contains synthetic,
  effect-patched regressions for the invariants above. First run uses the
  parent-provided task database, never the persistent developer database.
- BEFORE/AFTER rendered captures: parent-owned and required before visible
  source edits; not yet recorded in this lane at this document's first write.
- Contract review cycles, focused results, generated-schema checks, mutation
  sensitivity, and browser observations will be appended after execution.

### Backend implementation and first verification cycle

Observed implementation: a cohesive `src/analytics/commercial.py` owns the
money/provenance projection, exact Decimal accumulator, currency registry,
window semantics, and lifetime activation reducer. `metrics.py` composes this
into the existing summary/revenue models; owner review retains factual review
metadata without synthesizing delivery or feedback dispatch. The canonical
analytics router pages full trip records and reuses the existing batched
payment-record reader, projecting only aggregates and never returning private
traveler/payer data.

The initial full baseline was interrupted at approximately 46 percent during
the user retry. This is a partial baseline, not a full-suite pass. The parent
owns reconciliation of external concurrent runners and the final broad check.

Commands and observed outcomes:

```text
DATABASE_URL=postgresql+asyncpg://waypoint@127.0.0.1:55439/waypoint_audit_20261023
TRIPSTORE_BACKEND=sql PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m pytest tests/test_commercial_outcome_truth.py -q -p no:cacheprovider
RED: 18 failed in 127.16s. The first assertions reproduced quality->conversion
and approval->delivered; additive-contract cases failed because it did not exist.

Same isolated environment, after implementation:
tests/test_commercial_outcome_truth.py
GREEN: 18 passed in 13.58s.

tests/test_commercial_outcome_truth.py tests/test_analytics_outcome_contract.py
GREEN: 26 passed in 58.55s.

tests/test_commercial_outcome_truth.py tests/test_analytics_outcome_contract.py
tests/test_revenue_analytics.py tests/test_analytics_truth_hardening.py
tests/test_team_metrics_contract.py tests/test_review_logic.py
tests/test_review_policy_escalation.py
GREEN: 60 passed in 119.60s.

.venv/bin/python -m ruff check <scoped source/test files>
All checks passed.
```

The HTTP checks combine the actual router, reducers, and Pydantic response
models with explicitly effect-free paged readers. This is API contract
integration evidence, not SQL persistence or live-provider evidence. They
prove records beyond the first 1,000 contribute, source reads remain explicitly
tenant scoped, traveler PII is absent from output, custom windows reject invalid
bounds before accessing the store, old inquiries with new booking receipts use
the receipt's event date, lifetime activation survives a selected short date
window, and a nonadvancing reader returns 503 instead of hanging.

Package decision: direct `babel>=2.17,<3` was added narrowly to the existing
dependencies, preserving the dirty dependency list. Installed Babel is 2.18.0.
The parent owns the shared `uv.lock` reconciliation. The installed currency
registry recognizes USD/INR/JPY/KWD and excludes XYZ; precision metadata is 0
digits for JPY and 3 for KWD. Recorded `1.2345 KWD` remains exact as the new
`amountDecimal` string; no recorded precision is erased by display minor units.
Primary package documentation:
[Babel numbers and currencies](https://babel.pocoo.org/en/latest/api/numbers.html).

The preserved historical metrics tests now use actual synthetic receipt
evidence for booked values, explicit currencies for pipeline values, and
separate tests asserting terminal statuses cannot manufacture outcomes. Team
workload/completed-work and real feedback behavior remain; booking conversion
uses receipt evidence. No old task or historical trip was deleted.

Parent review cycles, shared lossless budget-resolver integration, mutation
sensitivity, generated frontend contract, frontend checks/build, and browser
capture verification are still pending. These results do not close that work.

## Owner decisions and remaining gates

1. Actual agency earned/realized revenue policy: define fee/commission contract,
   recognition event, settlement/reversal source, and principal/agent treatment
   with the agency owner/accounting adviser. Recommendation: integrate the
   canonical financial records after the policy is ratified, rather than
   infer a percentage from trip value. Falsifier: an existing contract-specific
   authoritative producer already covers these fields; integrate it if found.
2. Real-operator study: choose participants, consent/retention scope, assistance
   limits, and commercial experiment. Recommendation: a small observed cohort
   progressing to independent repeat inquiries. No agent-generated NPS/PMF
   estimate substitutes for this decision or its evidence.

All code and tests from this lane remain uncommitted. Other agents' dirty and
untracked work is preserved.
