# P0/P1 Execution Queue — Feature List V2

Date: 2026-05-12  
Source: `Docs/status/FEATURE_LIST_V2_2026-05-12.md` + `.csv/.json`

## Queue Principles

1. Canonical-path only: no duplicate pipelines or parallel module stacks.
2. Contract-first: route map, API schema, and integration tests before surface enablement.
3. Risk-first: privacy/compliance and data integrity gates before growth features.

---

## P0 Queue (Immediate)

1. Documents module rollout completion (`F036`)
- Goal: clear final gate `contract-regression-suite` and enable `/documents`.
- Depends on: `F029`..`F035`, `F049`, `F050`.
- Acceptance:
- End-to-end tests cover upload/review/extract/apply across relevant role paths.
- `frontend/src/lib/nav-modules.ts` shows all documents gates complete.
- No regressions in workbench ops path.

2. Tenant and security hardening (`F004`, `F005`)
- Goal: enforce strict data boundaries and abuse resistance.
- Depends on: auth + membership + RLS + audit.
- Acceptance:
- RLS invariants validated for core multi-tenant entities.
- Rate-limit coverage reviewed for auth/public endpoints.
- Security-sensitive endpoints have explicit policy and tests.

3. Core pipeline trust loop hardening (`F014`..`F019`)
- Goal: protect decision correctness and operator safety.
- Depends on: run ledger + stage events + suitability.
- Acceptance:
- Contract tests validate run status payload shape and stage progression.
- Suitability acknowledge gate blocks unsafe approvals reliably.
- Reassess flow preserves traceability and does not mutate unrelated state.

4. Document and booking evidence reliability (`F029`..`F035`)
- Goal: make traveler submission -> agent review -> extraction apply reliable and auditable.
- Depends on: signed URL storage + extraction attempts ledger + pending booking workflow.
- Acceptance:
- Retry/apply/reject flows are deterministic and auditable.
- Sensitive fields stay policy-controlled across export/debug surfaces.
- Extraction attempt history is append-only and queryable.

5. BFF contract integrity (`F049`, `F050`)
- Goal: keep deny-by-default proxy and timeout contracts authoritative.
- Depends on: route-map tests + api-client contract tests.
- Acceptance:
- Unknown routes denied by default.
- Long-running endpoints have explicit timeout policies.
- Route contracts and backend surfaces remain synchronized.

---

## P1 Queue (Next)

1. Quote/output governance foundation (`F055`)
- Build canonical render contract + template versioning path.
- Avoid parallel renderer architecture.

2. Payments and settlement closure (`F056`)
- Integrate payment lifecycle with booking tasks/confirmations/pending data.

3. Supplier reliability intelligence (`F057`)
- Turn confirmation and risk signals into supplier trust scores used in decisions/reviews.

4. Policy-as-data compliance engine (`F060`)
- Begin jurisdiction-aware policy substrate for refunds, obligations, disclosures, and audit evidence.

5. Insights actionability uplift (`F040`..`F042`, `F044`)
- Add recommended actions and closed-loop outcomes to analytics surfaces.

6. Drafts backend evolution (`F026`..`F028`)
- Advance from file-centric behavior toward SQL-canonical durability and conflict-safe collaboration.

7. Traveler wedge conversion hardening (`F053`)
- Improve itinerary-checker -> agency handoff conversion and attribution tracking.

---

## Verification Baseline for Each Queue Item

1. Targeted backend tests for touched routers/services.
2. Targeted frontend tests for route-map/nav contracts and impacted UI module.
3. End-to-end smoke for affected user flow.
4. Doc/status update in `Docs/status/` with evidence and residual risks.

