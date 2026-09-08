# Implementation Plan — PER-0700 Persona Audit Remediation (2026-09-06)

**Status:** Phase 0–2 EXECUTED same-day (2026-09-06). All 25 directed findings (P0 ×3, P1 ×7, P2 ×15) implemented and S2-verified locally by three parallel agents + lead integration; full disposition + evidence in audit doc §13, register Part 4g (canonical statuses). Nothing committed — owner gate stands. Remaining: Phase 3 (observability/eval depth), Phase 4 (DECIDE packages), and the verify-first hosted/multi-worker evidence for this wave.
**Derived from:** [PERSONA_AUDIT_PER0700](PERSONA_AUDIT_PER0700_AGENTIC_SYSTEMS_ARCHITECT_2026-09-06.md) (37 new findings PA-01…PA-37) + explicit register (91 open rows) + [LAUNCH_IMPLEMENTATION_PLAN_2026-09-02](LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md) (this plan slots into its Phase 1–2; it does not replace it)
**Standing commitments honored:** findings lifecycle (additive promotion, source-qualified IDs, no second status store) · TRIP_STATE_CONTRACT (`Docs/architecture/TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md`) · no-duplicate-routes (extend canonical routers, never fork) · supersession workflow before any removal · data-safety rules (canonical test agency read-only, additive seeds) · commit gate (motto attestation + trailers; no commit without explicit approval).

**Sizing convention:** S ≤ ½ day · M ≤ 2 days · L ≤ 1 week (single agent, focused). Verification standard per item: minimum S2 (failed-before/passed-after) on the touched behavior; items marked **S3** require end-to-end flow evidence before "done" claims (doctrine §3).

---

## Phase 0 — Repair the working tree (blocks everything)

The tree carries uncommitted capability including the audit's only P0. Do not build on top of it until dispositioned.

| # | Task | Findings | Files | Size | Verification |
|---|---|---|---|---|---|
| 0.1 | **De-fabricate the public journey-graph route**: return 404/draft-labeled when no stored graph; stop swallowing scoping errors; add signed-proposal-token requirement (or drop the public route and keep only the tenant-scoped one). **Pass-2 note: `tests/test_journey_graph_hydration.py` currently pins the fabricated-fallback path — it must be rewritten to pin abstain-not-synthesize, not just the route fixed.** | PA-01 (P0) = F-41 | `spine_api/routers/journey_graph.py`, `server.py:1468`, `tests/test_journey_graph_hydration.py` | S | S2: fabricated-PNR assertion replaced by not-found/abstain assertion; unauthenticated request without token → 401/404 |
| 0.2 | **Make proposal acceptance durable**: persist accept (timestamp, signer, token id, consent) on trip + audit event; fulfillment verifies durable record | PA-02 (P0) | `public_proposals.py`, `booking_fulfillment.py` | M | S3: accept → restart-free fulfillment path reads trip field, not registry; S2: restart simulation (new process) still sees acceptance |
| 0.2b | **Fix the broken fulfillment write path**: `booking_fulfillment.py:137,149` calls nonexistent `TripStore.get`/`TripStore.update` (real: `get_trip`/`update_trip`); the swallowed `AttributeError` means `FULFILLED_CONFIRMED` is returned with nothing persisted. Fix method calls + fail-loud + read-back before terminal status. | **PA-05 (upgraded to P0, pass 2)** | `src/orchestration/booking_fulfillment.py` | S | S2: S2-sensitivity test — fulfillment on a seeded trip persists `booking_confirmation` (read-back verified); missing-method path now raises, not confirms |
| 0.3 | **Compiler share-token honesty**: attach `TierMetadata` to compiled packages; share token only for non-synthetic inventory or token payload carries tier. **Pass-2 note: the panel's fulfill chain is dead wiring (BFF route-map 404s, F-42) — remove or gate the fake chain UI in the same slice.** | PA-25 (= F-42) | `proposal_compiler.py`, `ProposalCompilerPanel.tsx` (remove hardcoded `TRIP-LIVE-772` demo chain) | S | S2: synthetic package → tier field present in token view; UI renders sample labeling |
| 0.3b | **Escalation split-brain**: recovery agent writes `trips.review_status="escalated"` but the new queue reads `TripRoutingState.status` — converge to one surface (route recovery writes through `TripRoutingState`, or the queue reads both with provenance). | PA-38 (P2, pass 2; in-flight work) | `src/agents/recovery_agent.py`, `agent_runtime_adapters.py`, `spine_api/routers/assignments.py` | S | S2: recovery-escalated trip appears in `GET /queue/escalated` |
| 0.4 | **Disposition the rest of the diff** (escalated queue + tests, FreshnessCard, price-lock BFF, hook re-pins, agent_lease lint): clean to commit once 0.1–0.3b land | — | 12 modified + 5 untracked | S | Existing tests green; route snapshot regenerated (`scripts/snapshot_server_routes.py --write`) per no-duplicate-routes rule |

**Gate:** owner reviews Phase-0 diff; commit only on explicit approval (F-04/EV-11 standing gate). Register rows PA-01…PA-40 promoted into canonical register with evidence in-row (lifecycle rule: closure requires in-row evidence; no second status store — promotion is additive append).

## Phase 1 — Honesty + authority envelope (the doctrine §12/§13 repairs)

Highest doctrine-leverage, mostly small mechanical changes on primitives that already exist.

| # | Task | Findings | Size | Dependencies |
|---|---|---|---|---|
| 1.1 | Hybrid-engine default `"0"` + startup banner naming effective agency rung; amend map honesty note + G-03 row | PA-03 | S | DECIDE (default value) — code ready either way |
| 1.2 | `TierMetadata` envelope on fulfillment + price-lock + IVR + compiler responses (`core/reality_tier.py` extended to money path) | PA-05/PA-06/PA-28 | M | none |
| 1.3 | Auth fixes: internal dep on `subagent_payouts`; `_auth_or_skip` or explicit allowlist row for negotiation/crisis/distribution; `CAPABILITY_TOKEN_SECRET` fail-closed | PA-09/PA-24 | S | none |
| 1.4 | Wire `authorize(action, context)` seam (registry caps + dual-control) into fulfillment + payout pre-execution | PA-08 | M | 0.2 |
| 1.5 | Verify-after-execute in fulfillment: re-read trip + version check before `FULFILLED_CONFIRMED`; fail loud on store failure; price-lock abstains on missing rate source + required version/idempotency | PA-05/PA-06 | M | 1.2 |
| 1.6 | IVR `"status":"simulated"`; corporate override authenticated approver + role + threshold dual-control | PA-28/PA-26 | S | none |
| 1.7 | `/metrics` real exporter: run outcomes, failure classes (placeholder until 2.3), loop health, usage-guard spend | PA-10 | M | 2.3 for full value |

## Phase 2 — State, lifecycle, recovery (the long-term killers)

| # | Task | Findings | Size | Notes |
|---|---|---|---|---|
| 2.1 | Run-ledger lifecycle: retention (30d terminal-only), SQL read-model projection (feeds F-09/L4) | PA-12 | M/L | additive projection first, no file-format break |
| 2.2 | `Idempotency-Key` on POST /run + per-trip in-flight lease reuse | PA-13 | M | extends existing lease primitive, no new system |
| 2.3 | **Failure-class taxonomy**: ledger `failure_class` + class-routed recovery (tool→retry w/ backoff, verification→DLQ+human, state→quarantine, authority→escalate); persist `stage_at_failure` in meta | PA-07 | M/L | after E-B exploration (register Part C) |
| 2.4 | Sweep-race reconciliation: don't fail runs with live leases; `completed_after_failure` path | PA-17 | S | |
| 2.5 | Bounds: inbound SSE max-lifetime + listener pruning; collection-token CAS; undo/redo agency-scoped + guard-respecting | PA-14/PA-15/PA-16 | M | F-12 rides SSE |
| 2.6 | Terminal-row retention for leases/requeue; durable checkpoints (or honest naming + doc) | PA-29/PA-30 | S/M | |

## Phase 3 — Observability, evaluation, cost (prove, don't assert)

| # | Task | Findings | Size | Notes |
|---|---|---|---|---|
| 3.1 | Unified decision-event stream: emit decision/escalation events on production path, one id-space, trip-timeline join | PA-04 | M | after E-E exploration |
| 3.2 | Audit-chain hygiene: scheduled verification endpoint + re-anchor on compaction; single audited store for `/api/audit` | PA-19 | M | extends F-06 |
| 3.3 | Cost attribution: correlation ids on `usage_events` (run/trip/decision); cost-per-decision rollup | PA-20 | M | after E-C |
| 3.4 | Autoresearch honesty: wire composite scoring to live D6 lanes or mark lineage `simulated: true` | PA-11 | M | |
| 3.5 | Closed-loop verdicts require real fixture re-execution or `heuristic` label | PA-21 | M | |
| 3.6 | Evals gain cost/latency/human-intervention dims | PA-34 | M | after E-C |
| 3.7 | ESCALATE lead-save fail-loud + repair surface | PA-27 | S | |

## Phase 4 — Wire-or-archive decisions (DECIDE backlog, one coherent answer)

Owner-gated; each has an exploration package in register Part C so the decision is evidence-first.

| Decision | Findings | Recommendation |
|---|---|---|
| Council + model router + ghost workflows + CheckerAgent naming | PA-35, C-01/C-03 | **Archive** council + router (zero callers, no eval evidence), rename checker to "consistency heuristics", give ghost workflows a consumer or delete — per supersession workflow with ADR |
| Memory read-path | PA-18, F-13 | **Wire** preference memory → question generation first (highest value, lowest risk); suitability slot second |
| Tier-3 suitability scorer | PA-36, G-03 | **Wire behind flag** with its existing heuristic fallback, or archive — pick one in the agency-boundary ADR (E-A) |
| Judge calibration | PA-22, C-02 | Calibrate against human labels before any gating role; otherwise archive |
| Agency-boundary ADR (single answer for hybrid default, scorer, memory, theater) | PA-03/PA-18/PA-35/PA-36 | **Adopt** — one ADR answering "where is agency justified" ends the recurring class |

## Sequencing & critical path

```text
Phase 0 (tree repair)          ──► commit gate (owner)
   └─► Phase 1 (honesty+authority)  ~3-5 days
         └─► Phase 2 (state/lifecycle)  ~5-8 days   [2.1 + 2.3 are the long poles; E-B/E-C exploration in parallel]
               └─► Phase 3 (observability/eval)  ~5-7 days
                     └─► Phase 4 (DECIDE packages)  ~2-3 days + owner decisions
```

- Phase 1 items are independent of Phase 2 except 1.4 (needs 0.2) and 1.7 (best after 2.3). Parallelization: one agent on Phase 1, one on Phase 2 exploration docs (E-B/E-C/E-G), meeting at 2.3.
- **This plan addresses code/honesty/authority readiness. It does not by itself clear launch blockers L1/L2/L4/L6** (hosted envelope, backups, shared durable state, legal) — those remain owned by the 2026-09-02 launch plan; PA-12/2.1 and E-G are this plan's contributions to L4.
- Rollback posture: every phase is additive-first (new fields, new endpoints on canonical routers, flag-gated behavior changes); PA-03 default flip is the only behavior inversion and is one env var to revert.

## Explicit non-goals (this plan)

- No new routers for existing resources (all changes extend canonical routes; route snapshot regenerated each phase).
- No deletion without supersession analysis (Phase 4 removals each get an ADR + comparison table per repo rules).
- No commits/pushes — all work lands as reviewed trees with owner-gated commits (F-04/EV-11).
- No test-data mutations on the canonical agency (`d1e3b2b6-…`); per-test agencies for persistent stores.

## Ratification checklist for owner

1. Approve Phase 0 disposition (esp. PA-01 fix shape: token-gated public route vs removal).
2. DECIDE: hybrid-engine default (1.1) — recommend `"0"` until the agency-boundary ADR lands.
3. Approve E-B/E-C/E-G exploration starts in parallel with Phase 1.
4. Approve PA-row promotion into canonical register (source-qualified, additive).
5. Confirm Phase 4 recommendations or override (archive council/router; wire memory slot 1).
