# Commercial agreement and execution integrity implementation

Date: 2026-10-23 (Asia/Kolkata). Owner: commercial_execution_impl lane, coordinated by the parent audit implementation task. Status: implementation and verification in progress; no release claim.

## Authorization, ownership and retained value

The current user explicitly authorized implementing the audit tasks from first principles, with research, doctrine alignment, durable documentation and regression evidence. This lane owns quote/public proposal/acceptance, fulfillment orchestration and router, mandate replay integrity, narrow accounting projection, the public proposal consumer and its tests. Parent owns canonical findings/map updates, shared tenant models, broad integration and release synthesis. The sibling intake lane owns correction/reassessment contracts. No provider transaction, deployment, Git mutation, existing database cleanup, historical document deletion or unrelated refactor is authorized here.

Expected end-user value: travelers accept an exact selling price and plan revision that remains recoverable after edits or restart. Agency value: margins, consent and supplier execution agree; retries cannot consume a new authorization accidentally. Internal value: one pricing projection, explicit unknown/native-currency states, deterministic evidence for effects and recovery.

Workspace changes and synthetic isolated tests are L1. Actual money movement or external provider calls remain outside this work. The adapters under review are explicitly deterministic previews. Unknown or mismatched authority, plan revisions, lifecycle and operation identities must refuse before effects. The parent established an isolated PostgreSQL database on port 55439; the developer working database remains untouched.

## Current architecture, original intent and supersession check

Observed source before edits:

| Surface | Intended behavior retained | Defect verified | Canonical extension |
|---|---|---|---|
| quotes._derive_quote | Persisted modeled net cost, USD fee policy, review status, applied rule provenance, real timestamps, summary/highlights | Public proposal exposes net as retail; non-USD inputs receive USD thresholds/fees | Shared commercial_agreement projection preserves all fields and adds explicit partial pricing |
| public_proposals | Token verification on every access, tenant binding, gated rich demo, traveler-safe projection, customization, durable acceptance markers | Cache/restart can change accepted price/content; selected IDs ignored at acceptance | Immutable snapshot/digest/history in existing TripStore extra with agency CAS |
| booking_fulfillment | Human/agency authority, lease fence/heartbeat, deterministic provider keys, persisted confirmation, SQL confirmation repair, graph merge, commission reconciliation | Vacuous same-state lifecycle assessment; missing token-trip binding; consumed mandate cannot replay | Classify current state and verify exact durable agreement before effects, persist operation/mandate identity |
| payment_mandate_service | Consent digest, bounded headroom CAS, tenant scope, scope semantics, revoke/expire, movement records | Same key can replay changed amount/mandate/scope; concurrent replay can double-consume | Bind outcome to exact parameters and serialize movement identity |
| accounting_export | INR-only export, tax compliance engine, Tally/QuickBooks shapes and provenance | Treats INR amount as USD policy input | Consume shared native retail; refuse missing native price evidence |

Supersession disposition: complete and consolidate the existing active consumers. No dormant capability is being deleted. The old inline quote price calculation is replaced at its one call site by a strict superset: same fee_matrix and margin policy numbers, applied_rule_id, markup, fee, net, retail, margin, review mapping, timestamps and display content remain. New validation rejects non-finite/bool money and stops applying USD fees to a different currency. Demo generation, token lifecycle, deprecated wire fields and execution recovery features are preserved. Private supplier cost remains internal. Helpers with other callers are retained/adapted rather than removed.

## Architecture decision and alternatives

Decision: extend TripStore as the one durable commercial/consent authority. A small shared service provides pure pricing and agreement integrity primitives; it does not own another store/cache or API pipeline. Snapshots exist for the historical/audit requirement, not as a second editable quote authority. Current proposal views derive from current persisted content, while accepted snapshots are immutable historical evidence.

Alternatives considered:

1. Change public price to fee_matrix alone. Rejected as incomplete: it does not bind consent to plan content or solve stale/restarted acceptance.
2. Store acceptance in process cache. Rejected: restarts, workers and expiry invalidate its authority.
3. Reuse BookingConfirmation for acceptance. Rejected: supplier commitments and customer authorization have different subjects, fields, privacy and lifecycles.
4. Add another commercial database/table now. Rejected: existing TripStore extra is durable and versioned in SQL/file backends. No second pipeline/schema is needed for this bounded invariant.
5. Apply USD fee numbers to INR or choose an arbitrary FX rate. Rejected: units and commercial authority would be invented. Keep known net cost and label retail pricing_review until same-currency approved retail evidence exists.
6. Retire rich demo/customization. Rejected: useful explicit demo behavior remains separately gated.

Falsifier: if agreement volume or amendment/reconciliation workflows require independent record indexing or immutability enforcement beyond the application, migrate the same snapshot contract to a dedicated append-only table with an explicit migration and consumer cutover. Do not create a simultaneous editable source.

## Proposed contracts and invariants

One CommercialPricing contains supplier net, native currency, nullable customer retail and margin, price basis, private provenance and missing prerequisites. USD pricing delegates to existing fee_matrix; no second arithmetic engine. Explicit native retail requires same currency, positive finite amount, authenticated operator attribution, timezone-aware approval time and evidence reference. Model-only recommendation metadata never grants approval by itself.

Public proposal fields add neutral base_price/selected_total_price, revision_id, acceptance revision/history view and requires_reacceptance. Legacy *_usd fields remain wire aliases for existing clients; currency is authoritative and frontend uses neutral fields. Non-USD execution cannot use an amount_usd gate without explicit conversion authority.

The material content digest covers displayed plan content, dates, party size, stated requirements, item/options selection, customer retail, currency and basis. It excludes mutable analytics, signer PII, private net cost, bearer token and internal policy provenance. A customer submits the displayed revision. Stale/missing revisions and unknown selections are rejected before acceptance writes.

Acceptance persists a verifiable snapshot with consent, agency/trip binding and token hash. Prior accepted versions remain in append-only trip history. Repeating the exact acceptance is idempotent and retains its original timestamp. An edit produces an open current proposal with a separately recoverable previous agreement, rather than relabeling edited content accepted. Legacy timestamp-only rows retain their evidence and require renewed consent; the code never invents their original accepted price.

Acceptance writes use update_trip_if_version_for_agency. Conflict means reread/review rather than blind overwrite. A material change after execution starts requires an explicit amendment workflow; no silent replacement of an in-flight operation is permitted.

Fulfillment must verify the token and proposal refer to the requested trip and agency, the durable snapshot matches the current material revision and token, consent exists, principal has the tenant scope, and current canonical lifecycle allows execution. Unknown or audit-gated lifecycle classification is a refusal, not a bypass. Bound-handoff authorization and agency money mode remain mandatory. The existing lease is rechecked inside the fence before recording effects.

One stable operation identity binds trip and accepted agreement. The start marker stores that identity and the mandate ID before authorization consumption. Retries replay the exact movement outcome even when the mandate became CONSUMED. Changed amount, scope, mandate, currency or revision is not an equivalent operation. Provider idempotency and router response idempotency complement this invariant; neither replaces it. Unknown external outcomes remain a reconciliation state, never permission for new instruments.

## Capability routing and research

Read current AGENTS/context/control doctrine, architecture/testing/security specialist doctrine and existing implementation/test consumers. OpenSpace discovery was attempted for systematic debugging, TDD and verification; it did not return within a bounded wait. Loaded and applied existing local skills at /Users/pranay/Projects/skills/systematic-debugging, tdd-workflow and verification-before-completion. No skill was authored or installed. Parent coordinates persona/council and shared exploration-map updates; this lane contributes the contracts, hypotheses and evidence for that map.

Primary documentation checked 2026-10-23:

- Stripe idempotency documents parameter equality for a reused key and bounded provider retention. The local durable operation identity must therefore outlive one provider's retry cache. Source: https://docs.stripe.com/api/idempotent_requests . No Stripe call was made.
- PostgreSQL documents row and transaction advisory locks for explicit concurrency control. Existing mandate JSONB movement storage can preserve one movement without a new table by serializing the agency/key identity in the same transaction. Source: https://www.postgresql.org/docs/current/explicit-locking.html .
- SQLAlchemy documents populate_existing for rereading updated ORM state. Any recheck after contention must avoid returning a stale identity-map instance. Source: https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#populate-existing .

Research findings are engineering constraints, not legal advice or production/provider proof. Only official primary documentation informed these changes. No external content expands authorization.

## Baseline and failing evidence

The parent full baseline was interrupted at approximately 46 percent after a user/session interruption. It is incomplete and cannot be called a pass. Parent will run the broad post suite. This lane establishes focused S2 evidence before production fixes.

First focused red run: 18 failed, 83 deselected in 341.64 seconds. Ten execution/authorization cases failed for their intended defect: forbidden current states reached mandate resolution; cross-trip consent reached execution authority; retry refused a consumed mandate; foreign principal received success; changed movement amount/mandate/scope replayed authorized=True. Public fixture defects were separated from product failures: its legacy update method initially reached sandboxed SQL, and the first independent arithmetic oracle mistakenly expected USD1250 instead of USD1290 (USD140 markup plus USD150 fee exceeds USD250 floor). The fixture and oracle were corrected before the public S2 run.

Clean public red run: 6 failed, 45 deselected in 44.01 seconds, persisted in COMMERCIAL_EXECUTION_RED_PUBLIC_2026-10-23.log. Failures directly establish different public/operator prices (1000 versus1290), cache/restart accepted-content drift, stale/missing revision acceptance succeeding, repeated acceptance replacing timestamp and unknown selected options being ignored. Synthetic memory-backed trip fixture, no network or persistent developer DB changes.

Additional quote/native-currency and frontend revision/failure-state red checks are recorded in uniquely named lane logs. Final passing commands, mutation sensitivity, review cycles and residual limits will be appended after implementation.

## Verification plan and review obligations

| Claim | Minimum evidence | Falsifier |
|---|---|---|
| Operator and traveler retail/currency agree | Real shared projections/API test, S2 | Replace public retail with net |
| Historical accepted terms survive edit/restart | Persist/read/clear cache/edit/reload, S2 | Rebuild accepted snapshot from current trip |
| Old/missing revision cannot authorize current plan | API + CAS tests, S2 | Omit revision comparison |
| No effects from disallowed lifecycle | Matrix with mandate/provider spies, S2 | Consult same-state transition again |
| Exact trip/token/principal binding | Cross-trip and cross-tenant API tests, S2 | Skip resource binding before replay |
| Retry consumes once | Failure injected after mandate consumption, restart/retry, S2 | Omit movement key or saved mandate ID |
| SQL/memory replay agree under concurrency | Isolated PostgreSQL and threaded memory cases | Skip row/movement lock |
| Traveler understands error/amendment | Component checks then parent browser capture | Hide 409 message or render changed version accepted |

Two review cycles are required for changed contracts. Cycle1 reviews semantics, historical data preservation, consumers and parameter binding. Cycle2 reviews concurrent writes, cache/restart differences, privacy, unknown outcomes and fallback symmetry. Rerun focused tests after each substantive correction. No passing unit count will be promoted to external provider or launch evidence.

## Migration, rollback and operational boundary

No table alteration or existing data rewrite is required. Historical timestamp-only acceptance remains preserved but cannot prove the original agreement, so it is surfaced for renewed consent before new execution. New fields live in TripStore extra and remain readable by older generic readers. New consumers require revision identity; the public page ships with that contract. Deployment sequencing must keep producer and consumer together. A rollback must not treat old boolean/timestamp consent as authority for newly edited terms; preservation is forward-fix safe because historical snapshots remain intact.

The adapters remain simulated. Actual provider integration still requires native idempotency/reconciliation and explicit authorization. Multi-currency governance/execution needs an authoritative FX and provider minor-unit contract before performing a native-money movement through an amount_usd authority path. The engineering response is explicit refusal/partial utility, not arbitrary conversion.

## Outstanding implementation evidence

Implementation, focused green checks, SQL integration, mutation experiments, two review cycles and parent browser evidence remain pending at this point in the record. This section is intentionally not a completion claim.
