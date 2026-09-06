# TPM Blueprint Tasks — Implementation Handoff (N-1..N-4)

**Date:** 2026-09-01 (implemented), 2026-09-02 (review cycles 1–2 completed)
**Source mandate:** Pranay approved "do all" on the four net-new tasks from `Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md` (the one-time gap-diff against the ChatGPT TPM-training blueprint — no blueprint initiative; these four rows are the entire sanctioned output).
**Register intake:** F-27, F-28, F-29 filed as IMPLEMENTED/closed in `Docs/review/FINDINGS_REGISTER_2026-08-31.md` Part 4b; `scripts/check_findings_register.py` → **66 rows, lifecycle valid, 0 warnings**.
**Doctrine applied:** 4-phase workflow, 2 review cycles (schema/contract change), API-contract verification before FE code, additive-first preservation, findings-lifecycle intake, no commits (awaiting explicit approval).

---

## 1. Executive Summary

All four tasks are implemented, tested, and review-hardened. The backend gained three structural guarantees that previously existed only as conventions or hand-patched ADR clauses: **no silent field clobbering** on trip updates (merge precedence + provenance + optimistic concurrency), **no duplicate intake** from provider retries (idempotent `/parse` and webhook dedup), and **no one-hop promotion of intake-blocked trips to quote-capable** (status invariant enforced at every persistence write path). The frontend gained the first joined read-model of the six unjoined status vocabularies (derived lifecycle chip + escalated queue slice). Backend touched-area tests: **123 passed**; frontend touched-area: **63 passed** (19 new + 44 existing trips-area); register + lint clean.

Verdict shape: **Code ready: YES** (pending review cycle 2 verdict + full-suite run). **Feature-ready: YES for the propose-only stage** — the booking-side lifecycle states remain deliberately absent (validated deferral, mapping doc §4). **Launch-ready: UNCHANGED** — this wave changes no launch gating; it hardens the trust surface under the existing one.

## 2. Technical Changes

### N-3 — Merge precedence + provenance on `/optimistic-sync` (F-27)

- `spine_api/services/field_merge.py` (NEW): canonical precedence contract — preference fields **customer > operator**, commercial/unknown fields **operator > customer**; unattributed pre-existing commercial values treated operator-owned (conservative); every applied overwrite records `{actor, actor_id, at, superseded}` under packet `_field_provenance` (reserved key, client-proof); rejections returned as conflicts with the kept value — nothing silently lost.
- `spine_api/routers/inbound.py`: optimistic-sync rewritten — precedence merge, 409 on stale `expected_packet_version`, **store-level CAS** via `update_trip_if_version(expected_updated_at=...)` (review-cycle-1 fix: the original check-then-save was TOCTOU-racy), no-regression rule (the shallow missing-field re-check can demote `READY_FOR_STRATEGY` only when *this* update cleared a required field; label→key mapping: budget→`budget_scope`/`budget_max`, dates→`start_date`/`dates`, destination→`destination`), audit + SSE payloads carry conflicts.
- `spine_api/contract.py`: `OptimisticSyncRequest` += optional `actor_role`, `expected_packet_version`; `OptimisticSyncResponse` += optional `conflicts`, `packet_version`. All additive/optional — old clients unaffected (verified by existing FE tests passing unchanged).

### N-1 — Intake-boundary idempotency (F-28)

- `src/agents/idempotency.py`: `threading.Lock` around `try_acquire`/`mark_completed`/`mark_failed` (the docstring claimed thread-safety; the check-then-set race would have mattered the moment the registry became load-bearing) + double-checked lock on singleton creation; multi-worker limitation documented as the pluggable-backend seam.
- `spine_api/routers/inbound.py` `/parse`: dedup keyed on (agency, channel, raw_text, customer_name/contact, agent_notes, strict_leakage). COMPLETED → replay the original trip (no duplicate); PENDING → 409 `duplicate_intake_in_flight`; FAILED → retry allowed. Response is built *before* `save_trip`; `mark_completed` fires immediately after persist; audit + SSE are best-effort afterwards (review-cycle-1 fix: a post-save failure could previously un-complete the key and a retry would mint a duplicate trip).
- `spine_api/services/messaging_webhooks.py`: dedup per provider `message_id` — replay original reply, or `duplicate_suppressed` while first delivery is in flight.

### N-2 — Trip-status invariant (F-29)

- `spine_api/core/trip_status.py` (NEW): `INTAKE_BLOCKED_STATUSES` (incomplete, needs_followup, needs_clarification, awaiting_customer_details, escalated) can never become `QUOTE_CAPABLE_STATUSES` (ready_to_quote, quote_ready, ready_to_book) in one hop; `IllegalTripStatusTransition`; `status_history` audit (cap 50, `{from,to,at}`); `normalize_trip_status` alias map with warn-on-unclassified. Deliberately additive-first: full typed-enum/Literal enforcement deferred until the derived read-model validates the real status distribution (mapping doc discipline: *name a state only when a validator exists for entering it*).
- `spine_api/persistence.py` — enforced on **every** write path (review-cycle-1 found the original save_trip-only enforcement bypassable via `update_trip*` / `server.py:2401`):
  - `FileTripStore.save_trip` + `_apply_status_guard` inside all three locked update methods (`update_trip`, `update_trip_if_version`, `update_trip_if_version_for_agency`; `update_trip_for_agency` delegates);
  - `SQLTripStore.save_trip` guard + history seeding **on every save of an existing trip** (cycle-1 P2: stale caller copies could regress the audit trail);
  - `SQLTripStore.update_trip` (ORM) via `_apply_status_guard_orm` (history folded into `analytics._extra`, DB-authoritative seeding);
  - the three raw-SQL update methods get an atomic `_status_guard_sql_predicate` WHERE clause (no row load needed; rejection is a no-op UPDATE).
  - Raw-SQL `analytics` writes changed from **replace** to **JSONB merge** (`COALESCE … || :param::jsonb`) — closes a pre-existing wipe hazard for every caller passing partial analytics.

### N-4 — Derived lifecycle read-model (companion UX slice)

- `frontend/src/lib/trip-lifecycle.ts` (NEW): `deriveTripLifecycle` joins trip.status + stage + decision_state + review_status + readiness snapshots onto the blueprint states (intake → needs_information → feasibility → planning → awaiting_customer_approval → booked_side → completed, escalated reachable from anywhere; `in_trip` declared dormant — no input signal exists yet). Unified `getTripBlockers` (merges the previously scattered blocker computations) + per-state next actions. Written only against **verified** API contract fields (API Contract Verification rule; one TS-caught defect — a `decisionState` camelCase guess — fixed to the verified snake_case).
- `frontend/src/components/workspace/LifecycleChip.tsx` (NEW): state chip + blocker count + next action tooltip; rendered in `trips/[tripId]/layout.tsx` header (one-line additive insertion).
- `frontend/src/app/(agency)/trips/PageClient.tsx`: escalated count + URL-persisted `?filter=escalated` toggle chip (client-side slice over the workspace list — **honest limitation**: server-side escalation filtering needs a routing-state join and is the documented next slice); list/table consume `visibleTrips`.

## 3. Code Review Findings (2 cycles — schema/contract change)

**Cycle 1 (logic, data loss, breaking changes) — verdict FIX-FIRST.** Two P1s, both real:

1. *Status invariant bypassable via `update_trip*`* — the operator manual-update endpoint (`server.py:2401`) could PATCH incomplete→ready_to_quote in one hop. → Fixed with guards on all six write paths + 6 new tests.
2. *`expected_packet_version` TOCTOU* — concurrent syncs could both pass the advisory check and silently drop a writer's fields. → Fixed with store-level CAS + dual-backend packet_version carriage + analytics JSONB-merge.
Plus P2s fixed: parse mark-timing (post-save failure can't mint duplicates), `agent_notes` in the idempotency key, SQL status_history staleness, singleton lock, normalize warning. Six items verified-correct (precedence table, provenance capture, regression logic, file-store history seeding, guard-in-lock placement, contract backward compatibility).

**Cycle 2 (defensive gaps, fallback consistency) — verdict: see §8** (this section is completed by the cycle-2 verdict below).

**Test fixes during the work (doctrine: failures are findings):** my first `newly_missing` check compared the missing-*label* to packet keys (label≠key) — caught by test, fixed with the was-present map; status promotion initially regressed `new→active`; a CAS test used `saved_at` vs `updated_at` incorrectly; one loop test recorded no-ops. All fixed; all lessons are of the "the test caught the bug before runtime" kind.

## 4. Test Results (evidence)

| Suite | Result |
|---|---|
| Baseline (pre-change, touched areas) | 19 passed |
| `tests/test_optimistic_sync_merge.py` (new) | 10 passed |
| `tests/test_intake_idempotency.py` (new) | 8 passed |
| `tests/test_trip_status_machine.py` (new) | 36 passed (incl. 15-case blocked×capable matrix, update-path guards, ORM helper units, SQL predicate) |
| All touched areas combined (incl. parity, SQL coverage, ESCALATE, messaging, inbound regressions) | **123 passed** |
| Frontend `trip-lifecycle` + `LifecycleChip` (new) | 19 passed |
| Frontend trips area (existing: layout, gated pages, packet, followups, ops) | 44 passed |
| `tsc --noEmit` | clean |
| `ruff check` (all changed backend files) | clean |
| `scripts/check_findings_register.py` | 66 rows, lifecycle valid, 0 warnings |
| Full backend suite (canonical runner) | running — result recorded in §8 |

Known caveats: (1) a dev server is running on :8000 (parallel agent's preview), so full-suite numbers may carry F-19 contention noise — the runner warns; touched-area runs are the citable signal. (2) Mid-implementation, a parallel agent's change added an import-time `PROPOSAL_SIGNING_KEY` requirement — direct pytest invocations must export the runner's env vars (drift handled; documented here so the next agent doesn't misread it as breakage).

## 5. 11-Dimension Audit

| Dimension | Verdict | Notes |
|---|---|---|
| Code | ✅ | 123 touched-area tests, lint clean, typecheck clean, 2 review cycles |
| Operational | ✅ | Conflicts + status_history are visible to operators (audit trail); escalated trips now visible in a queue; no new ops burden |
| User Experience | ✅ | Operators stop losing silent field corrections; "where is this trip?" has one answer; escalated trips no longer vanish |
| Logical Consistency | ✅ | Precedence rules documented + tested; no-regression rule covers the historical-gap case; `in_trip` honestly dormant |
| Commercial | ✅ | Prevents ~4x-class commercial errors from clobbered budgets/party sizes; duplicate-intake LLM spend eliminated |
| Data Integrity | ✅ | Nothing dropped without a conflict record or superseded capture; history capped + DB-authoritative on SQL |
| Quality & Reliability | ✅ | Guards on every write path (verified by cycle 1); CAS race closed; registry thread-safe |
| Compliance | 🟡 | `status_history`/`_field_provenance` persist operator/customer actor labels — same self-asserted-identity class as F-03; real identity binding is F-03's fix, not duplicated here |
| Operational Readiness | 🟡 | In-process idempotency backend is single-process correct; multi-worker deployments need the pluggable backend (documented seam) — same stage-appropriate posture as the rest of the stack |
| Critical Path | ✅ | No launch blockers introduced; next slices enumerated in §7 |
| Final Verdict | **Merge: YES** (after cycle-2 verdict + full-suite). Feature-ready: YES (propose-only stage). Launch-ready: unchanged | |

## 6. Launch Readiness

- **Code ready: ✅ YES** — all guarantees tested at the touched-area level; full-suite result in §8.
- **Feature-ready: ✅ YES** for the current propose-only product: the four tasks harden exactly the surfaces operators touch today. Booking-side lifecycle states remain deliberately absent — that is the *correct* state, per the mapping doc's validator-exists discipline.
- **Launch-ready: ➖ UNCHANGED** — this wave neither unblocks nor blocks the existing launch gates (reality-boundary work, F-series P1s). It removes one silent-data-loss class from the demo/trust surface.

## 7. Next Phase

1. **Server-side escalated queue** — routing-state join so `?filter=escalated` is server-accurate under pagination (backend: trips list endpoint joining `TripRoutingState`; the FE chip already consumes the shape).
2. **Freshness card** on Quote Assessment (existing `/api/v1/price-lock` + `/trips/{id}/reassess`) — closes the approval-drift loop in UI; still gated by F-14/EX-14 for the execution-side story.
3. **Typed-enum status enforcement** — after the read-model has observed production status distributions (mapping-doc discipline).
4. **Multi-worker idempotency backend** — SQL/Redis implementation of the registry seam when deployment topology requires it.
5. **Actor identity on provenance/history** — resolve together with F-03 (self-asserted identity), not separately.

## 8. Review Cycle 2 Verdict + Full Suite

**Cycle 2 (independent reviewer, completed after quota-reset retry) — verdict FIX-FIRST, all findings fixed in the same pass:**

- **A (P1):** On the SQL backend (the pinned production store) the CAS update silently dropped `packet`/`decision_state`/`missing_fields` — they aren't Trip columns and raw-SQL updates had no unmapped-key folding; the sync reported success and the merged packet vanished on refetch. → Fixed: `_fold_unmapped_updates` mirrors `save_trip`'s folding in **all four** SQL update paths; `_row_to_dict` now folds `_extra` to top level like `_to_dict`; regression test `test_sql_cas_update_folds_unmapped_keys_and_returns_read_shape` (Postgres-marked). Root-caused why cycle 1 missed it: every new test pinned the file store — the SQL-backend test gap is itself a finding.
- **B (P1):** optimistic-sync unconditionally rewrote status → un-escalated escalated trips and demoted quote-capable/in-progress statuses on routine preference syncs. → Fixed: promotions only from the endpoint's own intake vocabulary; **escalated deliberately excluded even though it is intake-blocked** — escalation is operator-owned and only a human resolve/reassign clears it (my first fix got this wrong; the new preservation test caught it). Three preservation tests (escalated/ready_to_quote/in_progress).
- **C (P2):** the SQL idempotency backend's FAILED→retry reclaim was an unguarded UPDATE (concurrent retries could both win → duplicate effects). → Fixed with the same guarded-UPDATE + rowcount pattern the expired-TTL path already used.
- **D (P2):** guard rejections surfaced as raw 500s (raise paths) or misleading 409s (raw-SQL no-ops). → Fixed: FastAPI handler maps `IllegalTripStatusTransition` → 422; raw-SQL paths now pre-SELECT and raise the same exception (history append rides along — also fixes E).
- **E (P2):** raw-SQL status transitions were never audited into `status_history`. → Fixed via the pre-SELECT + analytics-merge append (file/ORM paths already audited).
- **F (P2):** optimistic-sync moved to the tenant-scoped `update_trip_if_version_for_agency` canonical path.
- **G (P2):** post-CAS audit/broadcast now best-effort (mirrors /parse; a side-effect failure can't turn a persisted sync into a retry-into-409).

**Shared-tree engagement (per the all-tree-work-is-shared doctrine — flagging is not fixing):** the full-suite failures were engaged, not deferred:

- `test_party_underdetected_warning` — **fixed**: `_PARTY_GROUP_SIGNAL_RE` now captures kinship/social plurals ("3 cousins") as raw `group_signals`, so unrecognized group words still trigger `PARTY_UNDERDETECTED` instead of silently sizing the party as 1. Test suite green.
- `test_tax_compliance_api_endpoints` (401≠200) — **not reproducing** in isolation or in the original failing combination with the current tree; all auth-bypass checks are call-time (verified middleware/auth/startup-assertions). Consistent with F-19-class order/contention flake or the parallel agent's in-flight PT-09 auth hardening settling. Reproduction command recorded; if it recurs in the final run it gets root-caused, not skipped.
- The other 3 failures were live-server contention phantoms (pass in isolation).

**Final verification:** touched-area backend suites 141 passed (incl. 9 new cycle-2 regression tests); frontend TSC clean + 63/63; ruff clean; full suite via canonical runner — result below.

**Final full-suite result (canonical runner, 2026-09-02):** **3,596 passed / 10 skipped / 1 failed** in 658s. The single failure (`test_full_tenant_scope_not_limited_to_initial_5000`, payments queue) **passes in isolation** — verified F-19 order-dependence phantom; mock-based pagination test unrelated to this change set. Two cycle-2 regressions the full suites caught and I fixed during verification: (1) asyncpg rejects `::jsonb` casts adjacent to text() binds → replaced with `CAST(x AS jsonb)`; (2) root cause discovered after that fix: `trips.analytics` is **JSON, not JSONB** — no `||` merge operator exists — so the analytics merge moved fully into Python inside `_prepare_raw_update` (one pre-SELECT doing status-enforce + history-append + deep-merge; DB authoritative for `status_history`; CAS WHERE still owns concurrency). These are exactly the class of defects the SQL-backend tests (finding A's test gap) now exist to catch.

**Verdicts:** Merge: YES (backend + FE change set, both review cycles processed, all P1/P2 fixed, full-suite verified). Feature-ready: YES for the propose-only stage. Launch-ready: unchanged. Not committed — awaiting Pranay's explicit approval.
