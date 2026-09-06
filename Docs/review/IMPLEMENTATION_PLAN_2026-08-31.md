# Implementation Plan — Waypoint OS Persona Council Audit (2026-08-31)

**Date:** 2026-08-31 · **Companion to:** `PERSONA_COUNCIL_AUDIT_2026-08-31.md`, `FINDINGS_REGISTER_2026-08-31.md`, `ALIGNMENT_EVALUATION_2026-08-31.md`
**Doctrine basis:** `OPERATING_DOCTRINE.md` §3 (proportional rigor), §4 (authorization), §5 (canonical paths), §6 (semantic salvage), §15 (completion contract) · `REVIEW_DOCTRINE.md` §76 (sequencing).

---

## 0. Ordering principle

### Active execution correction — 2026-09-05

Historical waves below retain rationale, but do not reopen locally verified
fixes or create a second approval ritual. Canonical EV-01–EV-11 capture the
retry's evidence-system and delivery findings.

1. Complete the already-authorized A1-1 artifact review, full hooks/gates,
   staging/commit/push receipts. Before push, resolve EV-11: current master/main
   push triggers Fly deployment. Do not silently change branch or deploy.
2. Repair canonical inventory parsing (EV-01) and the RLS-scoped vocabulary
   reporter (EV-06/07), with failing-first regressions and durable receipts.
   Main agent owns parser/review records; delegated worker owns reporter/tests/
   E12 evidence. These independent safe repairs can proceed during Git audit.
   **Locally verified 2026-09-05:** 40 parser tests, 28 reporter tests,
   canonical gate 145 rows/91 open/53 closed/1 deferred, independent scoped
   SQL receipt 21,937 rows. Full-worktree gates and delivery remain separate.
3. Reconcile source-qualified IDs and status overlays (EV-02/03), retaining
   discovery history and exact closure tiers. Replace unsupported custody
   ownership language and identify one current ledger (EV-04/05).
   **Progress 2026-09-05:** all 15 master-inventory F/R label collisions now
   have explicit reviewed relationships in FINDINGS_LIFECYCLE; active overlay
   references are qualified. A-06/A-20/F-17 and lease-test follow-ups were
   reconciled from source evidence. Complete other source mappings, unmapped
   identities and mechanical derived-view coverage before closing EV-02/03.
4. Complete actor/policy/epistemic truth and HTTP evidence (F-03/F-30/F-22/
   F-37/EV-08/09), then durable execution, independent evaluation, canonical
   product contracts and consumer migrations, browser/operator/provider proof.
5. Research candidates remain visible with falsifiers and dependencies; no
   generic research completion or local suite count authorizes external effects.

F-31 refinement: use the current
[insurance contract research package](../research/INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md)
for date semantics, evidence-bearing eligibility and authenticated attachment.
The earlier universal 14-day premise is superseded by plan-specific evidence
requirements. Sequence input/time correctness, response/consumer migration,
auth/audit proof and separately gated provider/rule adoption. Coordinate the
changing source owner before modifying that in-flight implementation.

2026-09-05 follow-up to the user's long-term-solution question: the canonical
agency dependency is accepted, but attachment also needs action/resource
permission, distinct authenticated audit actor and tenant, production-equivalent
security tests (no implicit `PYTEST_CURRENT_TEST` authority switch), and durable
save/audit failure/retry semantics. These are explicit F-31 subrequirements in
the linked package, not optional hardening or a second auth system.

Delivery recheck: the full backend run ended with one missing-disruption-
timestamp failure; frontend typecheck/lint/tests/build passed. The source
fingerprint changed during the run. A subsequent eight-test focused retry
passed after externally observed source/test changes, but neither full-candidate
verification nor F-38's legacy-data/freshness contract is closed. Preserve these
receipts and revalidate the current implementation before marking it complete.
The [F-38 data-integrity package](F38_DISRUPTION_DATA_INTEGRITY_REVIEW_2026-09-05.md)
defines nine residual requirements and sequences response/consumer migration,
validated projection, tenant/HTTP proof and operator recovery. Prefer retaining
healthy alerts with explicit incomplete coverage; do not equate caught errors
and an empty list with a completed reliable read path.

Each task must state invariant, canonical owner, accepted contract, evidence
tier/sensitivity, migration/recovery, residual risk, and next action. Full
scope remains the original project goal; this sequence is not a substitute
completion definition. Acceptance of EV-01 means the parser protects lifecycle
semantics, not that every product finding has been semantically reverified.

Sequenced by **blast radius × dependency**:

> **Finish a canonical path before starting a new one.** · **Make the instrument honest before changing what reads it.** · **Seal the tenant boundary before consolidating over it.**

Each wave has an **exit gate**. Do not start wave N+1 until N's gate passes.

---

## Wave 0 — Preserve & document (do this first; de-risks everything)

**Rationale:** A-14 originally identified P0 remediation that lived only in the
dirty working tree. That preservation risk is now closed: the authorized
commit/push produced `2f9a638`, and A1-1 records the immutable 167-path commit
inventory plus the later concurrent live-worktree snapshot. Product and release
claims remain governed by their own gates.

| # | Action | Invariant | Acceptance evidence |
|---|---|---|---|
| 0.1 | Write the 4 docs (§0 audit, register, alignment-eval, plan) | Findings are durable, evidence-cited | Files exist under `Docs/review/` |
| 0.2 | Re-verify each P0/P1 claim with a targeted command before coding (no absence-from-grep) | No claim rests on grep alone | Each fix cites a passing/failing test |
| 0.3 | Capture current baseline via `scripts/run_backend_tests.sh` (server stopped, fresh `--basetemp`) | Baseline is reproducible | Committed, dated baseline number |
| 0.4 | ~~Classify every dirty file (remediation / WIP / generated) before any edit~~ **CLOSED 2026-09-01** | No dirty file deleted unclassified; unknown authorship remains explicit | `A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-01.md`; both CSV ledgers pass `tools/check_worktree_classification.py` |

> ⚠️ **Authorization (doctrine §4/§4.2).** "Docs + plan + implement" authorizes **L0 (read)** + **L1 (reversible workspace edits)**. **Git mutations (L3)** — staging/commit/push — still require **explicit in-session authorization from Pranay**. Every edit must re-read the live file immediately before writing (doctrine §10) to avoid clobbering parallel work.

**Exit gate 0:** **Partially open.** Documentation and working-tree
classification are complete. Item 0.3 still requires a new current baseline
before the whole Wave 0 exit gate can be called green; historical suite results
are preserved as historical evidence, not promoted to current truth.

---

## Wave 1 — Stop silently-wrong data (P0/P1 — highest real-world value)

**Rationale:** NEW-02. A quote built on `party_size=1 @0.9`, `budget_scope="total"`, `destination_candidates=[]` when the truth is 4 pax × per-person × Japan+Tokyo/Kyoto/Osaka is a **~4x commercial error**. Fixing this before any consolidation means the instrument that drives quotes is honest.

| # | Finding | Action | Invariant | Acceptance |
|---|---|---|---|---|
| 1.1 | NEW-02 / F-21 | **Colloquial extraction:** extend `_TRAVEL_VERB_DEST_RE` (`do/hit/cover/check out/keen on/down for`); lowercase + `+`/`,`-separated city-set pass; country+city resolution (flat cities + `destination_country`, no schema break); party group patterns (`me and N friends`, `N of us`, `the four of us`, `party of N`) **+ `PARTY_UNDERDETECTED`/`PARTY_UNPARSED_GROUP` validation warnings** (warn, never silent — Pattern 5); season/`late <month>`/"plus or minus"/"dates flexible"; budget `each`/`a head`/`pp` → `per_person`; tighten `somewhere`→`open` trigger; guard `no idea of the name` negation | No silently-wrong slot survives | New colloquial fixtures (from `DEMO02`) pass; existing golden dataset green; **S2** each; `scripts/run_backend_tests.sh` baseline no worse |
| 1.2 | NEW-01 / F-22 | **Authority/epistemic relabel:** reserve `explicit_user/FACT` for values whose evidence excerpt is a verbatim user span; pass `epistemic_status=INFERRED` for pattern-inferred, `ASSUMED` for default-filled; forbid canned excerpts on `explicit_user` | The trust labels are truthful | Slot audit shows derived/default no longer claim FACT; `tests/test_epistemic_integrity.py` extended; **S3**: pattern-derived assert FACT fails |
| 1.3 | F-21 (duration) | **Add `trip_duration`/`duration_days` fact** (contract addition → 2 review cycles per repo discipline) + `date_flex_window_days`; wire into `QUOTE_READY` candidacy per Pranay | New fact round-trips | Schema/spec mirror updated; golden baseline green |
| 1.4 | NEW-02 | **Surface captured-but-hidden fields** in the demo's Trip Details table (meal_preferences, hard_constraints, trip_priorities were in the packet but not in the UI) | The "wow moment" is visible | UI subset renders all non-empty facts |

**Exit gate 1:** A quote built on the demo note yields party=4, budget=per-person, destinations Japan+Tokyo/Kyoto/Osaka; every fact's epistemic status is true; captured-but-hidden fields are visible.

---

## Wave 2 — Trust, isolation, and truth-telling (P1)

| # | Finding | Action | Acceptance |
|---|---|---|---|
| 2.1 | NEW-06 / F-23 | Fix legacy `CUSTOMER_MEMORY_STORE` agency-scoping (retire in favor of `_MEMORY_STORE`); add `getCustomerMemory()` to `api-client.ts`; gate the Alex Morgan card on a real recall hit, badge as sample, strip real-loyalty numbers, **block** fake-facts "Apply to Proposal" injection; empty-state 5-state machine driven by `store.draft_status` | Fresh-tenant E2E shows no fabricated profile; no fake-facts injection; legacy store scoped |
| 2.2 | F-25 | Repair-surface UX: banner names missing fields (reuse `PacketTab` expression + `FIELD_LABELS`); "Review Missing Fields" navigates to editable field / focus-rings missing list (never a silent no-op); keyboard-reachable (AC1–AC5) | AC1–AC5 each pass |
| 2.3 | A-18 | Rotate `OPENAI_API_KEY`; remove committed `DATABASE_URL` default password; make `SPINE_API_DISABLE_AUTH` hard-fail outside test | No live credential in repo; auth kill switch fail-closed |
| 2.4 | F-01 | Price-lock `re_lock_lower_rate`: add `strategy.version` + Idempotency-Key + compensating-action records | Concurrent re-locks don't double-book; **S2** |
| 2.5 | F-03 | Bind signoffs to authenticated JWT subject + artifact-version hash (team_workflows / corporate_policy) | Signoffs not self-asserted; **S3** mutation fails |

**Exit gate 2:** Fresh-tenant E2E shows no fabricated profile / no silent no-op; no live credential; auth kill switch fail-closed; signoffs bound to actor.

---

## Wave 3 — Consolidate canonical paths + enforcement gates (P1 — the systemic fix)

**Rationale:** NEW-03. Doctrine §5 is the most-violated rule; these are one problem with many instances. Each consolidation ships with a **deletion date** for the retired side.

| # | Finding | Action | Retire (with date) | Acceptance |
|---|---|---|---|---|
| 3.1 | NEW-03 / A-04 | **BaseSettings config module** (replace 156 scattered `os.getenv`) | ad-hoc `os.getenv` | **S2**: unset a required var → fail fast startup |
| 3.2 | A-04 | **One pydantic contract layer** (server.py's 19 inline models → `contract.py`/routers) | inline `BaseModel`s | FE/BE contract equality; golden-set parity |
| 3.3 | A-04 | Retire `TeamStore` (membership_service is source of truth) | `persistence.py:2564 TeamStore` | No import remains; marker removed by deletion |
| 3.4 | A-04 | One audit store: Postgres `audit_logs` + hash chain (preserve verification; F-06 sign + extend to run-ledger) | file hash-chain path | Chain verification preserved; **S3**: tamper → verify fails |
| 3.5 | A-05 | One frontend API client; migrate the ad-hoc `fetch(` files | 80 raw `fetch(` sites | New ESLint bare-fetch ban is CI-blocking |
| 3.6 | A-06 / A-20 | **Drift gates in CI:** type `generate_types.py` → diff → fail; `alembic check` | hand-written `types/*.ts` | **S3**: add a column/model → CI fails |
| 3.7 | O-8 / O-10 | Wire `check_findings_register.py` into CI; ESLint bare-`fetch` ban + `any` threshold | — | Register gate is CI-blocking |
| 3.8 | A-11 | One marketing surface (retire v2/v3/v4, keep v5) | `app/v2`–`v4` | 3 dirs deleted; routes removed |
| 3.9 | A-09 | ADR template `Supersedes:`/`Superseded-By:`; back-fill 22 ADRs; renumber 003/004/005 | ad-hoc ADR naming | 22 ADRs back-filled; lineage preserved |
| 3.10 | O-1 | **Retirement gate** (target + deletion date; CI fails on overdue `DEPRECATED` files) | — (the new control) | **S3**: overdue `DEPRECATED` → CI fails |

**Exit gate 3:** Every duplicate pair has one survivor + one deletion date; retirement gate + drift gates enforced mechanically.

---

## Wave 4 — Quality & regression protection (P1)

| # | Finding | Action |
|---|---|---|
| 4.1 | F-19 | Default-exclude integration tests (opt-in flag) or per-test DB namespacing so live-server contention can't manufacture phantom failures |
| 4.2 | F-17 | Fix TimelinePanel race (waitFor); triage 49 unhandled vitest errors; clear 4 lint errors + 17 exhaustive-deps warnings |
| 4.3 | A-16 | Ratcheting vitest coverage thresholds + first booking-path smoke e2e |
| 4.4 | A-15 | Reduce `any` in prod code; resolve/justify the 4 `eslint-disable`s |
| 4.5 | A-08/A-07/A-10 | Repoint `motto_v4` references; CI dangling-reference check; fix `index.md`/`INDEX.md` collision; backfill CHANGELOG; reconcile IDEA pad; one doc tree |

**Exit gate 4:** Backend + frontend suites green (or documented triage with owners); coverage/drift gates enforced; no dangling doctrine references.

---

## Wave 5 — Complete the epistemic layer (P1)

| # | Action |
|---|---|
| 5.1 | Attach `EpistemicStatus` to every TripPacket slot (wiring is the remaining work); `AssumptionRecord` populated from intake |
| 5.2 | Surface epistemic status in UI — UNKNOWN must look unknown (a11y) |
| 5.3 | Compose `assert_tier_capability` into every endpoint that writes success events / makes financial claims |

**Exit gate 5:** A packet can be inspected and every field's truth-state read; no financial claim from a MOCK/SIMULATED tier.

---

## Wave 6 — Extensions & agent runtime (P2)

| # | Finding | Action |
|---|---|---|
| 6.1 | R-11 / F-10 | Durable lease heartbeat/fencing/STALE sweep, agency scoping, **pipeline-version stamp** (checkpoint-and-defer on mismatch) per `DURABLE_AGENT_LEASE` design |
| 6.2 | R-12 | IROPS trigger for JDG (measure segment-count distribution as falsifier first) |
| 6.3 | R-16 | Trace-correlation reader + CI event-flow assertion |
| 6.4 | R-14 | Frontend styling unification per design doc |
| 6.5 | A-17 | WelcomeModal a11y (role/aria-modal) |
| 6.6 | R-13 | Nav rollout-gate drift — product decision |
| 6.7 | R-10 | Server decomposition per plan (`create_app()` factory; rejects microservices) |

**Exit gate 6:** Agent lease is version-fenced; IROPS ripple wired; trace spans have a consumer.

---

## Sequencing rationale (why this order)

1. **Wave 0** because uncommitted P0 security/lead-loop work is the largest loss risk, and the deliverables are what you asked for.
2. **Wave 1 before Wave 3** — fixing the extractor's silent-wrong data (party=1, budget=total) is higher real-world value than consolidating internals, and it makes the quote instrument honest first.
3. **Wave 2 before Wave 3** — trust/isolation (memory scoping, secrets, repairo-surface) over an unsealed boundary risks reintroducing R-02/R-03.
4. **Wave 3 before Wave 6** — every Wave-6 extension would otherwise build on a duplicated foundation.
5. **Wave 5 last-but-one** — the epistemic completion depends on stable canonical paths to attach to.

---

## Deliberately excluded (and why)

| Candidate | Why excluded |
|---|---|
| Rewriting the backend | Doctrine §1/§6/§83 — deterministic core, RLS, reality tiers, gates are real assets. **Do not rewrite.** |
| Replacing the eval framework | The framework is fine; the wiring is now correct. |
| Bulk-renaming all ADRs | Wait until `Supersedes:` exists, or lineage is destroyed. |
| Committing anything | Git mutation (L3) requires explicit in-session authorization from Pranay. |
| Deleting `data/trips/*.json` | Now understood as gitignored test effluent; no production split-brain. |
| NG-01…NG-04 (event-log-as-SSOT, A2A negotiation, JIT ticketing, RFQ rounds) | Recorded no-go-for-now from backlog; re-open only after connectivity tier. |

---

## Residual risk / open decisions (owner: Pranay)

| # | Risk / decision | Why | Next |
|---|---|---|---|
| 1 | Wave 1.3 `trip_duration` contract — add as fact + join `QUOTE_READY`? | Sets 2 review cycles + FE types | Decide at Wave 1 |
| 2 | Wave 2.1 customer-memory posture — demo asset (badge) vs replace with real wiring? | Recommendations B+ now, A follow-through | Decide at Wave 2 |
| 3 | Wave 3.4 audit store final form | Postgres + hash chain recommended | Decide at Wave 3 |
| 4 | Wave 6.6 nav rollout-gate | Product decision, not code | Decide at Wave 6 |
| 5 | F-19 phantom failures | Live-server contention; need opt-in flag / namespacing | Wave 4 |
| 6 | Register integration F-19…F-26 | Pending Pranay's ratification before merging into `FINDINGS_TASKS_CONSOLIDATED` | Before Wave 1 |

---

## Verification strategy (doctrine §3/§15)

- **S2** per defect fix (fails before, passes after).
- **S3** for load-bearing invariants (authority-label rule, budget gate, retirement gate, drift gate).
- **Contract-driven E2E** for the demo loop (fresh tenant → process → blocked → inbox → repair → reprocess idempotent).
- **Baseline via `scripts/run_backend_tests.sh` only** (server stopped; fresh `--basetemp`); never cite a count from a run with the dev server up.
- **Frontend** `npm run typecheck && npm run lint && npm test -- --run` before claiming frontend green.
- **Docs** updated in the same coherent flow (doctrine §14); register validated.

---

## Docs/artifacts updated or preserved

- New: the 4 docs under `Docs/review/` (this plan + audit + register + alignment-eval).
- Preserved: the existing 08-29/30/31 corpus (canonical; not superseded by date). This plan **corrects** stale rows (R-03, R-08, A-02, A-13, R-15, S1–S6 over-claim) rather than deleting them.
- Preserved: ALL current dirty work (doctrine §10) — no overwrite without re-reading live state.

---

## 2026-09-04 execution addendum — dependency-ordered next wave

This addendum is the current plan overlay. Earlier waves remain historical
lineage; they are not silently rewritten. The live status and evidence
receipts are maintained in `Docs/review/EXECUTION_STATUS_2026-09-04.md`.

### Gate 0 — custody and ownership (always first)

1. Re-snapshot the dirty worktree with the classification validator.
2. Keep implementation, tests, generated state, runtime data, screenshots,
   and audit artifacts separately owned.
3. Do not stage or release a path until its semantic owner, coherent slice,
   verification receipt, and rollback path are recorded.

**Stop condition:** any new unclassified path, ownership collision, or
destructive recovery request pauses the wave.

### Wave A — local truth and contract correctness

1. Finish the remaining deterministic extraction contract work, including the
   country-versus-city model and explicit ambiguity behavior.
2. Ratify and implement D‑01 (`trip_duration`) only after deciding whether it
   is quote-blocking or informational; update packet schema, extractor,
   validation, API, frontend types, fixtures, and browser evidence together.
3. Ratify and implement D‑02 (`flights_inclusiveness`) as an explicit
   tri-state/unknown contract; never coerce uncertainty into a binary value.
4. Ratify and implement D‑03 country/city multi-destination semantics using a
   canonical reference-data relationship, not duplicated destination lists.

**Exit evidence:** contract tests, migration/type snapshots, adversarial
fixtures, and an authenticated browser journey showing the user-facing
resolution state.

### Wave B — runtime/evaluation parity

1. Close X‑09 by making production hybrid configuration explicit and ensuring
   D6/evaluation records the mode it actually ran; retain a ratified owner
   decision on default ON versus default OFF.
2. Keep X‑10 `checker_model` reserved until a provider registry, T0/T1/T2
   router, advisory proposal contract, consent/spend guard, telemetry,
   holdout, and rollback package exists.
3. Add independent producers for N‑02/N‑03 and private holdouts before using
   quality aggregates as promotion authority.
4. Add E‑06/E‑07/E‑08/E‑10/E‑11 trajectory, calibrated-judge, adversarial,
   warning-capable, and mixed-language evaluation lanes.
5. Keep X‑14 as a shadow prototype until the canonical retention design has a
   durable cross-store inventory, policy versioning, legal holds, lifecycle
   anchors, provider purge semantics, reconciliation, audit/RLS coverage, and
   recovery evidence.

**Exit evidence:** parity-mode metadata, independent producer provenance,
calibration agreement, holdout separation, and a reproducible promotion or
rollback decision.

### Wave C — deployment and container hardening

1. Complete X‑12/F‑05 image hardening: pinned lock build, `.dockerignore`
   exclusions, non-root runtime inspection, vulnerability scan, and measured
   startup/healthcheck evidence.
2. Prove `/ready`, migration ownership, worker crash/reacquire, shared
   revocation/run-ledger state, backup/restore, failover, RPO/RTO, and
   multi-replica convergence.
3. Produce a deployment-specific runbook with stop, quiesce, rollback, and
   recovery triggers.

**Exit evidence:** image and compose checks, deployed smoke, fault injection,
restore drill, and operator sign-off. Local Docker checks alone are not
release proof.

### Wave D — provider, legal, and bounded-pilot gates

1. Replace or explicitly gate simulator surfaces behind real provider
   contracts, credentials, webhook verification, idempotency, reconciliation,
   cost limits, and external references.
2. Complete privacy, consent, DPA/TOS, retention, deletion, and customer-data
   review with a human owner.
3. Run authenticated browser/device journeys over intake, repair, inbox,
   proposal, SSE/BFF, and provider-facing paths.
4. Split the dirty tree into owner-approved release slices and run the full
   hook/gate only on the exact authorized slice.

**Exit evidence:** provider/hosted/browser/legal/operator receipts and an
explicit launch decision. Until then, public/paid launch remains NO-GO and an
invite-only pilot remains conditional.

### Deliberate non-actions

- Do not wire `checker_model` cosmetically into the deterministic checker.
- Do not silently choose D‑01/D‑02/D‑03 semantics from existing code shape.
- Do not treat sample/provider fields as live business effects.
- Do not use `git add -A` on the current broad dirty tree as a release split.
- Do not delete historical docs, fixtures, or concurrent artifacts to make
  the inventory smaller.

### 2026-09-04 enforcement checkpoint — A-06 / A-20

- **A-06 generated API types:** the backend-lint CI job now regenerates the
  canonical TypeScript mirror and fails on a diff. Treat a clean-commit
  regeneration as the acceptance receipt; a dirty checkout comparison is
  custody evidence only.
- **A-20 migration drift:** do not add `alembic check` as a blocking job yet.
  The post-`upgrade head` probe reports removed legacy tables/indexes,
  nullability/type changes, and `trips.destination` removal. First inventory
  each delta, classify retain/additively-migrate/retire, and prove a clean
  disposable baseline plus rollback/restore. Only then wire the check into CI.
- **D-08/D-09:** local implementation is complete; the next gate is
  authenticated browser/device evidence, not more route or sample-state code.
