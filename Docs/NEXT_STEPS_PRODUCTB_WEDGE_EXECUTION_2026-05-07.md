# Product B Wedge - Next Steps Execution Plan (2026-05-07)

## Objective
Prove or kill Product B as a GTM wedge for Product A using behavior evidence, not vanity engagement.

## Locked decision boundary
1. Product B scope: audit + action packet + re-audit compare only.
2. Primary success event: traveler gets agency revision using Product B findings.
3. Launch gate: credibility + forwardability + pull-through.
4. Kill logic: calibrated thresholds with qualified sample criteria.

## Phase 0 (next 48 hours): instrumentation contract

### Task 0.1 - Event schema lock
Define and implement event schema for:
- intake_started
- first_credible_finding_shown
- finding_evidence_opened
- action_packet_copied
- action_packet_shared
- agency_revision_reported
- re_audit_started
- product_a_interest_signal

Acceptance:
- Events written consistently from frontend and backend.
- Event dictionary documented in one place.

### Task 0.2 - KPI definitions lock
Finalize exact formulas and windows:
- Time-to-first-credible-finding (p50/p90)
- Forward-without-edit rate
- Agency revision rate (within 7 days)
- Product A pull-through rate

Acceptance:
- No ambiguous KPI naming.
- Every KPI has numerator, denominator, time window, and data source.

### Task 0.3 - Qualified sample rule
Define inclusion criteria for kill tests:
- Real trip intent
- Sufficient input quality
- Not internal test traffic

Acceptance:
- Kill tests explicitly use qualified sample only.

## Phase 1 (next 3-5 days): core flow hardening

### Task 1.1 - First-value SLA
Enforce <= 60-90s first credible finding.

### Task 1.2 - Evidence-first findings
Every finding includes:
- severity
- why it matters
- confidence
- evidence pointer
- exact question to ask existing agent

### Task 1.3 - Action packet primacy
Default output is forward-ready message for the current agent.

Acceptance:
- Findings are sendable without rewrite.
- Median user reaches a forwardable output in one pass.

## Phase 2 (next 1 week): re-audit proof loop

### Task 2.1 - Before vs after delta
Show resolved, unresolved, and worsened items after agency revision.

### Task 2.2 - Revision quality scoring
Add revision delta score tied to risk reduction.

Acceptance:
- Re-audit clearly shows whether the agency revision improved plan quality.

## Phase 3 (go/no-go checkpoint)

Run calibrated kill test after first qualified cohort.

Go criteria:
- Forwardability threshold met
- Revision threshold met
- Pull-through signal statistically meaningful

No-go criteria:
- Thresholds fail after calibrated test windows
- Trust-risk threshold breached (high-severity false positives)

## Immediate next move (today)
1. Implement Task 0.1 event schema and wire events.
2. Implement Task 0.2 KPI formulas in docs and analytics queries.
3. Implement Task 0.3 qualified sample filter for evaluation dashboards.
4. Freeze any non-core feature work until Phase 0 is complete.

## Queued TODOs (added 2026-05-07 after public-checker hardening)
1. Lock deployment config: add `PUBLIC_CHECKER_AGENCY_ID` to `.env.example`, deployment env templates, and startup runbooks with SQL preflight (`agencies.id` must exist).
2. Add API-level tests for `/api/public-checker/run`, `/api/public-checker/events`, and `/analytics/product-b/kpis` including auth failures and malformed payloads.
3. Run full verification sweep: full backend pytest, frontend lint + build, and one SQL-seeded end-to-end smoke run.
4. Remove environment ambiguity: choose one canonical non-prod public-checker agency id and seed it in dev/staging bootstrap.
5. KPI closure check: verify dashboard/query visibility for observed revision, inferred/unknown, and dark-funnel/non-return; add instrumentation if gaps remain.
