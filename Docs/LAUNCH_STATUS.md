# Waypoint OS Launch Status

**Decision date:** 2026-09-04\
**Decision owner:** Product owner / agency operator (human ratification required)\
**Evidence basis:** [Execution Status 2026-09-04](review/EXECUTION_STATUS_2026-09-04.md), [Launch Readiness Audit PER-0100](review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md), and the linked evidence records below.

## Current decision

**Public or paid launch: NO-GO.**

**Invite-only local or tightly bounded pilot: CONDITIONAL GO only after the
pilot gates below are explicitly accepted by the owner.** This is not a
production approval and does not authorize external provider, customer,
financial, legal, or deployment mutations.

The decision is based on the strongest demonstrated evidence, not on the
largest green test aggregate. The local code and test gates are substantially
green, but hosted deployment, shared durability, provider connectivity,
operator recovery, legal/privacy review, and semantic ownership are not yet
demonstrated.

## Evidence snapshot

> **Refreshed 2026-09-11** (FND-0265): the 2026-09-04 numbers below were two findings-store
> generations and three suite-total generations stale. Each row now carries its date and
> source; the decision verdict and blocker set are unchanged by the refresh.
>
> **Refreshed 2026-09-14** (council readiness check): ADR-008 fully ratified (items 2–7
> amended+ratified by owner-directed council; commit `91c6d418`), which closed the sole
> open P0 (FND-0185). ~30 commits landed since the 2026-09-11 receipt (trip-lifecycle
> write gate, MarginPolicy, extraction realignment, gap-closure G1–G6); connectivity-tier
> and RAG-embedding-provider work is in flight uncommitted. Deployment gate note: an
> active `deploy.yml` CD workflow deploys to Fly.io on every push to master while the
> decision below remains NO-GO public — see blocker 8. Decision verdict and blocker set
> are unchanged.

| Surface | Evidence (dated) | Interpretation |
|---|---|---|
| Backend | 2026-09-11 full suite at remediation tree (final gate): **4,593 passed / 22 skipped / 0 failed** (106s). Session runs also surfaced 2 test-contract updates (A4 plaintext-lane minimization) and 1 intermittent concurrency flake (`test_reconciliation_no_payouts`, failed 1 of 4 runs, passes isolated). Collected inventory receipt: 4,563 via `tools/test_inventory.py` (10 skip-marked files / 32 markers / 2 CI-excluded). 2026-09-14 targeted receipts: 77 focused tests passed (startup assertions, `/ready` contract, connectivity-tier routing, RAG embedding provider, memory-slot wiring) + `ruff` clean; full suite re-run pending because the dev server on :8000 would contend | Local contract green; not hosted proof; cite the receipt, not a bare total (FND-0264) |
| Frontend | 2026-09-11: 184 files / 1,382 tests passed; `tsc --noEmit` clean. 2026-09-14: `tsc --noEmit` clean again at current tree | Local UI contract green; browser/device proof remains |
| Frontend lint | 2026-09-11: `ruff check src/ spine_api/ tests/ tools/` — all checks passed | Backend lint-clean at the same tree |
| RAG | 14 focused tests passed; implementation claims corrected to local hash-vector/lexical heuristics | Truthful local behavior; no semantic-provider claim |
| RLS | Live rollback-only write probe plus mock/catalog checks pass | Local PostgreSQL evidence; role/replica/hosted proof remains |
| Simulator truth | Crisis 8, bookings 2, GDS/distribution 11, FX/IROPS API 8, financial routes 9, duty-of-care API 2, proposal/persona 13, suppliers/MRZ 4, simulated-panel suite 11, IROPS panel 3 focused tests | Local preview/label containment; provider-backed booking, GDS, FX, financial, IROPS, duty-of-care, supplier, and proposal state remains unproven |
| Feature inventory | 2026-09-11: 117 features — 94 LIVE / 14 PARTIAL / 6 GATED / 2 SIMULATED / 1 STUB (regenerated after FND-0261 corrections; wiring-evidence rule in the V3 Method) | Per-surface wiring truth lives in `Docs/status/FEATURE_LIST_V3_2026-09-10.md`; this file's blocker list (below) governs launch, not per-row labels |
| Worktree | 2026-09-14: ~30 commits since the 09-11 receipt (ADR-008 items 2–7 ratified `91c6d418`, trip-lifecycle write gate `6bf7465b`, MarginPolicy ×4, extraction realignment wave, gap-closure G1–G6); connectivity-tier + RAG-embedding-provider slice in flight uncommitted; no release snapshot | Preserved custody; semantic ownership and release split remain open |
| Findings | 2026-09-14 (`findings.py validate` OK): 289 lifecycle rows — 171 closed, 12 deferred, **106 open (0 P0 / ~54 P1)**; sole P0 FND-0185 closed today with ADR-008 ratification evidence | The system is not launch-complete; P1 mass is the dominant open exposure |

## Blockers before any public exposure

1. Choose and provision the deployment target (Fly or Render), real secrets,
   workers, Redis/PostgreSQL, webhook endpoints, alerts, and durable storage.
2. Prove migration, rollback, backup, restore, failover, RPO/RTO, and
   multi-replica convergence.
3. Replace or explicitly gate simulator/provider surfaces and remove remaining
   “live”, “issued”, “accepted”, or customer-visible fabricated claims.
   This includes the legacy suppliers/proposal pages and backend disruption,
   GDS, VCC, IROPS, FX, duty-of-care, and ghost-concierge routes. Bookings,
   crisis, disruption, GDS/distribution, FX, IROPS, and duty-of-care now have
   local preview/abstention containment, but still lack provider-backed state;
   VCC, ghost-concierge, and residual legacy copy require further containment.
4. Promote proposal revocation/issuance and run-ledger state to shared durable
   storage; verify concurrent workers and restart behavior.
5. Add independent extraction/pipeline producers, hidden holdouts, trajectory
   evaluation, and calibrated judging before using quality aggregates as
   promotion authority.
6. Complete traveler PII, retention, consent, DPA/TOS, provider-processing,
   and simulated-data disclosure review with a human owner.
7. Run authenticated browser/device smoke over the canonical frontend/BFF,
   SSE, auth, and provider-facing routes.
8. Establish semantic Git ownership and a separately authorized release
   snapshot; the current dirty tree is not a release boundary.

## Conditional pilot gates

An invite-only pilot may be considered only when all of the following have
written evidence and an identified owner:

- pilot cohort, exposure mechanism, support channel, and data-processing scope;
- real or explicitly sandboxed provider contracts with cost and failure limits;
- shared durable state and a tested recovery path;
- `/ready` dependency checks, worker health, alerts, and rollback trigger;
- browser journey: signup → intake → blocked/repair → inbox → proposal;
- proposal token issuance, revocation, expiry, and tenant-binding checks;
- documented known-issues acceptance with no unowned P0/P1 blocker;
- legal/privacy sign-off for the pilot data and retention window;
- rollback owner and a tested disable/quiesce procedure.

## Stop, rollback, and escalation triggers

Immediately pause exposure and escalate when any of these occurs:

- a tenant can read or mutate another tenant's resource;
- a token or proposal is issued without a persisted, agency-bound resource;
- a provider result, payment state, or confirmation is represented as live when
  it is simulated or unverified;
- a run is duplicated, orphaned, or resumed under an incompatible pipeline
  version;
- backup/restore or migration rollback cannot be demonstrated;
- PII is sent to an unapproved provider or retained outside the approved scope;
- a quality gate has no independent producer or its holdout is contaminated;
- the operator cannot identify the current truth, owner, or recovery action.

## Canonical evidence links

- [Execution status and findings/tasks register](review/EXECUTION_STATUS_2026-09-04.md)
- [Known-issues ledger](review/KNOWN_ISSUES_LEDGER_2026-09-04.md)
- [Deployment and launch envelope](review/DEPLOYMENT_LAUNCH_ENVELOPE_2026-09-03.md)
- [RLS write probe](review/S12_RLS_WRITE_PROBE_2026-09-04.md)
- [Proposal resource binding](review/PROPOSAL_RESOURCE_BINDING_N05_F03_2026-09-04.md)
- [Run-ledger durability](review/S11_N07_LRB07_LOCAL_DURABILITY_2026-09-04.md)
- [RAG retrieval honesty](review/RAG_RETRIEVAL_HONESTY_A02_R03_2026-09-04.md)
- [GDS/distribution preview truth boundary](review/GDS_DISTRIBUTION_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md)
- [FX/IROPS preview truth boundary](review/FX_IROPS_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md)
- [Duty-of-care preview truth boundary](review/DUTY_OF_CARE_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md)
- [Proposal and Persona Council truth boundary](review/PROPOSAL_PERSONA_TRUTH_BOUNDARY_2026-09-04.md)
- [Suppliers and MRZ truth containment](review/SUPPLIERS_MRZ_FRONTEND_TRUTH_CONTAINMENT_2026-09-04.md)

This document must be refreshed whenever the exposure boundary, evidence
snapshot, blocker set, or recovery posture changes. Historical audits remain
preserved and are not silently rewritten.
