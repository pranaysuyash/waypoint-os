# Launch Implementation Plan — Waypoint OS (2026-09-02)

*Derived from: `Docs/review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md` (PER-0100 audit, gate matrix §4) + carried items from `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md`.*
*Goal: reach CONDITIONAL-GO for a bounded invite-only pilot (≤3 design-partner agencies), then re-decide expansion. Public/paid launch remains NO-GO until Phases 1–3 + operator decision gates close.*
*Sequencing rule: security → durability → observability → record honesty → bounded exposure. Every task carries verification tier (S2 = failed-before/passed-after, S3 = mutation-tested or deployed-path proof) per `TESTING_DOCTRINE.md`/`RELEASE_READINESS_DOCTRINE.md` §11.*

**Ratification block (operator, blocks nothing except where marked):**

- ⚖ R-1 Exposure mechanism + pilot cohort (who are the 1–3 design-partner agencies?) — needed by Phase 4 only.
- ⚖ R-2 C-01 disposition: label all simulated panels (minimum) vs wire honest engine — label-minimum assumed in Phase 3.
- ⚖ R-3 PII minimization decision D-f + DPA/TOS engagement — needed before ANY external traveler data; blocks Phase 4.
- ⚖ R-4 Signup posture (email verification now vs later; "WORK EMAIL" framing) — Phase 3.
- ⚖ R-5 Business-model contradiction in `memory/MEMORY.md` (white-label vs platform-led) — record fix in Phase 3; strategy decision can trail the pilot.
- ⚖ R-6 Worker topology (workers=1 now vs PT-08 idempotency seam) — default assumed: workers=1 + pool right-sizing.

---

## Phase 0 — Land the tree (0.5 day) · *prerequisite for everything; LR-O02*

| # | Task | Files | Verify |
|---|---|---|---|
| 0.1 | Execute the F-04 commit split: **(A)** hardening stack + tests + `scripts/run_backend_tests.sh` + ci.yml env additions; **(B)** deploy artifacts (`Dockerfile.*`, compose, fly/render/Procfile) land only after Phase 1.1 fixes them; docs/untracked registers as (C) | 45 modified + selected untracked | Full suite green per commit; no doc deletions (guardrail) |
| 0.2 | Delete-or-adopt sweep of the 183 untracked files: source/tests → (A); deploy layer → hold; `.mimosa/`, `*.bak`, `instrumentation.ts.bak` → remove or gitignore (ask for anything ambiguous) | — | `git status` clean of ambiguity after |

*Gate: the release unit now exists — what would deploy is what CI verified.*

## Phase 1 — Launch-blocking hotfixes (~3–4 days)

### 1.1 Deployment envelope (closes G1–G6; highest severity cluster)

| # | Task | Evidence/Files | Verify |
|---|---|---|---|
| 1.1.1 | Fix auth kill-switch truthiness: treat `SPINE_API_DISABLE_AUTH` via the same normalizer as the assertion (`lower() in ("1","true","yes")`); apply in `middleware.py:39,72` + `core/auth.py:61,71,96` | LR-B01 | S2: boot with `=0` → auth enforced; add unit tests both parsers agree |
| 1.1.2 | Extend JWT secret blocklist to include the `.env.example` placeholder + generic `change-me`/`example` patterns; add `PROPOSAL_SIGNING_KEY` strength assertion (the `.env.example` already promises fail-fast) | LR-B02; `startup_assertions.py:61-71,119-126` | S2: boot with example file → hard fail |
| 1.1.3 | Make alembic read `DATABASE_URL`: env override in `env.py` (`os.environ.get("DATABASE_URL", config…)`, asyncpg dialect normalized); remove creds from `alembic.ini` | LR-B03 | S2: `DATABASE_URL=…fly-db alembic upgrade head` migrates the named DB |
| 1.1.4 | Fix compose env: `postgresql+asyncpg://`, add `JWT_SECRET`, `PROPOSAL_SIGNING_KEY`, `ENVIRONMENT`, `TRIPSTORE_BACKEND=sql`, `PUBLIC_CHECKER_AGENCY_ID`; delete dead `SPINE_API_SECRET_KEY`; fix `DATA_PRIVACY_MODE` to a valid value; remove host-published DB/Redis ports or add auth | LR-O01/B05 | S3: `docker compose up` → healthy stack, `curl /ready` 200 |
| 1.1.5 | Probe truth: switch all deploy configs to probe `/ready` (compose, Dockerfile HEALTHCHECK, fly, render); `/health` stops swallowing exceptions (or returns component status honestly) | LR-B08; `health.py`, `docker-compose.yml:25`, `Dockerfile.spine_api:33`, `fly.toml:43`, `render.yaml:19` | S2: stop postgres → probe flips unhealthy within one interval |
| 1.1.6 | `ENVIRONMENT` secure-by-default: production/staging refusal paths for missing declaration (assertion already has `_check_environment_declared` — extend to compose/Fly templates + document); close `ENABLE_TEST_TOKEN` (ENVIRONMENT guard + startup assertion) and `EXPOSE_RESET_TOKEN` prod guard | LR-B06/O07; `auth.py:377-430,337` | S2: assertions fire in staging sim |
| 1.1.7 | Durable security state: move proposal-token revocations + run ledger to Postgres (tables exist pattern: reuse alembic) or, if single-host is ratified, fly volume + documented constraint; either way `PROPOSAL_REVOCATIONS_PATH` caveat becomes a designed decision | LR-B07/S-11 | S2: revoke token → restart → still revoked |
| 1.1.8 | Topology: pin `WORKERS=1` in all artifacts + pool `pool_size=10, max_overflow=10`; add request timeouts (uvicorn `--timeout-keep-alive` + gunicorn-style hard cap decision recorded) | LR-B14/O03/R-6 | Config diff + compose boot |
| 1.1.9 | Non-root API container (`USER app`) after state moves off local disk (1.1.7 enables this) | LR-B15 | Image inspect |

### 1.2 Security register batch (closes G10–G11; ~2 days, already scoped in master inventory)

| # | Task | Ref |
|---|---|---|
| 1.2.1 | S-01…S-03: proposal-token secret from env-only (delete hardcoded fallback), kill ≥16-char legacy bypass, remove agency guess-loop + test-agency UUID, bind agency_id into signature | PT-01/02/03/04 |
| 1.2.2 | S-04: real Stripe webhook verification (or delete the control surface until payments are real) | GM-03 |
| 1.2.3 | S-05: tenant ownership check on draft-promote | G-09 |
| 1.2.4 | S-07: public-checker input caps (size/depth) — complements existing 12/min + 16KB limits | G-10 |
| 1.2.5 | LR-B10/11/12: webhook default-deny for unknown providers (align code with the comment at `messaging.py:137`); rate-limit `validate-code` + proposal-token GET/accept | LR table |
| 1.2.6 | LR-B13: proxy-aware rate-limit keying (trusted `X-Forwarded-For` per target platform) + REDIS_URL wired in fly/render | LR table |

### 1.3 Landing honesty (closes G14/G15 minimum; ~0.5 day)

| # | Task | Evidence/Files | Verify |
|---|---|---|---|
| 1.3.1 | Remove or clearly annotate the invented operator-proof metrics (`2m 14s` / `3` / `18%`) and fabricated testimonials; replace with real, defensible numbers or product claims | LR-F03/D08; `landing-v5.tsx:22-26,146-152` | Visual check + copy review |
| 1.3.2 | Rewrite the chatbot-voice CTA (:199) | LR-F04 | Copy |
| 1.3.3 | `/intake/fast` + `/corporate/offsites`: delete failure-fabrication fallbacks (show real errors) and the permanent "SLA: Active" badge; decide keep-vs-delist the orphan pages (recommend: delist until they're real features) | LR-F01/F02; `intake/fast/page.tsx:44-56`, `corporate/offsites/page.tsx:40,123` | S2: kill backend → page shows error, not fake success |

**Phase 1 exit gate:** all Phase-1 tasks S2-verified; `LAUNCH_STATUS.md` created (G18) citing the gate matrix with current statuses; blockers-for-pilot list empty.

## Phase 2 — Detect & recover (~4–6 days, overlaps Phase 1 tail)

| # | Task | Closes | Notes |
|---|---|---|---|
| 2.1 | Real metrics: `prometheus_client` counters (runs, escalations, gate hits, extraction latency histogram, auth failures, 429s); `/metrics` behind a scrape token (new `METRICS_TOKEN` or internal-only binding) | G9/LR-B09 | Honest-metrics-for-deterministic-core (audit §10.5) |
| 2.2 | Request-ID middleware + JSON structured logging; fix `logging_filter.py:28-35` tuple-args expansion bug | LR-B09 | S2 on the log bug |
| 2.3 | Error tracking (Sentry self-hosted or SaaS — free tier) wired in API + frontend | G9 | One real error observed in dashboard (S3) |
| 2.4 | Alert destinations for the existing budget-guard alerts; define 3 actionable alerts: error rate, /ready failures, escalation spike | G9/LR-B09 | Alerts have owners + response notes |
| 2.5 | Backups: nightly `pg_dump` to durable storage + documented restore procedure; **perform one restore drill** and record evidence | G8/LR-B04 | RRD §27: backup without restore evidence is weaker than assumed |
| 2.6 | Journey smoke in CI (E-04): signup → intake → blocked → inbox as pytest against a booted compose stack; wire `tools/runtime_smoke_matrix.py` `--preflight-local-stack` into a weekly/manual-release job | G24 | First deploy-smoke = converts unknown-unknowns |
| 2.7 | Eval core (E-01…E-03): live collectors for extraction/pipeline lanes, 30-scenario wiring, hidden-holdout directory | G23 | Per existing eval ADR |
| 2.8 | Findings gate into CI + single consolidated register (E-05/R-06): `scripts/check_findings_register.py` as a CI job; retire competing registers with archive pointers | G19/LR-D02 | Register count = 1 |

## Phase 3 — Product & record honesty (~2–3 days)

| # | Task | Closes |
|---|---|---|
| 3.1 | Simulated-surface labeling pass (C-01 minimum): badge every simulated panel incl. GDSSandboxPanel; sweep "Live/transmitted/issued/ACCEPTED BY SUPPLIER" copy strings | G16/F-03 |
| 3.2 | Regenerate `types/generated/spine-api.ts` + add the drift-enforcement job the contract header promises (openapi diff in CI) | LR-F05 |
| 3.3 | Frontend prod env contract: `SPINE_API_URL` added to chosen deploy config; fix SSE route env var + cookie name (dormant fix); decide keep/delist the two client-localhost pages; fix compose `NEXT_PUBLIC_API_URL` | LR-F06/F07 |
| 3.4 | `memory/MEMORY.md` rewrite (R-02/LR-D06): resolve business-model contradiction, deprecation markers on `SINGLE_TENANT_MVP_STRATEGY.md`, caveat falsified baselines | G19 |
| 3.5 | INDEX the 08-01 launch suite + GTM assessment (LR-D07); archive-point stale `SUPPORT_AND_CUSTOMER_SUCCESS.md`/`USER_GUIDE.md` rows | G19 |
| 3.6 | Minimum runbook + known-issues ledger (LR-D03/D02): one ops runbook (detect→diagnose→contain→rollback→escalate) + one known-issues doc the launch decision cites | G22 |
| 3.7 | User-guide MVP for agency admins (onboarding → first inquiry → review → proposal; 5–8 pages from existing EmptyStateOnboarding copy) | LR-D04 |
| 3.8 | Auth error regions `role="alert"`; guard the `.localeCompare` comparators | LR-F09 + advisory |
| 3.9 | Signup posture implementation per ⚖ R-4 | G20-adjacent |
| 3.10 | Legal layer per ⚖ R-3: TOS + privacy policy drafts (operator/legal review is a separate human gate — doctrine §45: never infer legal approval), PII minimization implementation for LLM paths per the D-f decision | G20 |

## Phase 4 — Bounded pilot launch (conditional go; ~1 day prep + 2-week window)

| # | Task |
|---|---|
| 4.1 | Publish `LAUNCH_STATUS.md` decision record: CONDITIONAL GO, constraints per audit §9, owner, rollback triggers, expansion criteria |
| 4.2 | Kill-switch inventory table (audit §10.8) + signup-pause capability verified |
| 4.3 | Onboard pilot agencies via invite codes; capture every correction as a fixture (failure-becomes-fixture, E-09); pilot feedback mapped to Waypoint personas (audit §10.6) |
| 4.4 | Daily observation cadence: error rate, run-completion, escalation count, support asks; 2-week checkpoint decides expansion (requires G23 eval core live) |
| 4.5 | Post-pilot: GTM D1–D8 answered with real evidence → public-launch re-decision against the full gate matrix |

## Effort & dependency summary

| Phase | Est. | Depends on | Unblocks |
|---|---|---|---|
| 0 Land the tree | 0.5d | — | everything |
| 1 Hotfixes | 3–4d | Phase 0 | pilot readiness (with 2.x observability minimum: 2.1–2.3) |
| 2 Detect/recover | 4–6d | Phase 0 (1.1 parallelizable) | expansion criteria, eval honesty |
| 3 Product/record honesty | 2–3d | Phase 0 | pilot trust surface, public-launch gates |
| 4 Pilot | 1d prep | Phase 1 + 2.1–2.5 + 3.1/3.6 + ⚖ R-1/R-3 | real-world evidence loop |

**Critical path: 0 → 1.1 → 1.2 → 2.1–2.5 → 4 ≈ 8–10 working days to a defensible invite-only pilot.** Public launch additionally requires Phase 3 complete + ⚖ R-3/R-4/R-5 + the D1–D8 operator decisions.

*Doctrine conformance: no task here implements an unratified ⚖ decision; every code task carries an S2-or-better verification; documentation tasks land in the same flow as behavior (Operating §14); the plan extends the canonical register rather than forking it (one register per E-05).*

---

## 2026-09-04 execution refresh

This refresh preserves the original plan and records what the retry wave
actually established. The current status overlay and complete task register
are in `Docs/review/EXECUTION_STATUS_2026-09-04.md`; custody and evidence
details are in `Docs/review/A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-03.md`.

### Phase gate status

| Phase | Current status | Evidence | What still prevents exit |
|---|---|---|---|
| 0 — preserve/land tree | **Partially complete** | 2026-09-04 ledger validates 401 source/concurrent paths (402 porcelain rows including the ledger); docs and findings lifecycle valid | 401 paths remain semantically unclassified; Git split/stage/commit/push is a separate explicit gate |
| 1.1 — deployment envelope | **Locally complete, release partial** | Startup/readiness/compose/static checks; 56 focused tests | Docker daemon/image inspection, hosted migration, secrets, rollback, restore, and platform decision |
| 1.2 — security register | **Mixed** | Proposal 40-test hardening; Stripe, draft-promote, and nonce-delimited egress suites; payload/tenant suites; full backend green | Live Stripe delivery/replay, provider-specific egress threat corpus, shared revocation, rate-limit abuse tests |
| 1.3 — landing honesty | **Locally complete, review partial** | Metrics replaced with capability claims; intake/offsites no longer fabricate success | Perform visual/copy review and browser-down verification |
| 2 — detect/recover | **Partial** | Findings checker, eval provenance, 30-scenario completeness, backend suite | Independent producers/holdouts, metrics/error tracking/alerts, backup restore, compose/browser smoke |
| 3 — product/record honesty | **Partial** | Simulated boundaries documented; route/type snapshots current | Label/copy sweep, generated-type drift CI, frontend env/SSE browser proof, runbook/user/legal docs |
| 4 — bounded pilot | **Not eligible** | No pilot/operator/provider evidence | Close all blocking rows and obtain R-1/R-3/R-4/R-5/R-6 decisions |

### Next implementation sequence (dependency-ordered)

1. **Decision correctness (completed locally):** X-04/X-05/X-06/X-13 now have
   defect-sensitive regressions and a 30/30 live synthetic corpus. Preserve
   pre-fix failures and keep public promotion bounded by independent evidence.
2. **Extraction safety (completed locally):** X-01/X-02/X-03/X-07/X-08 now
   sanitize, warn, or abstain on the confirmed adversarial cases; retain the
   7/318/52 receipts and add future failures as fixtures.
3. **Durability and trust:** X-11/N-06 fencing is complete locally/live-DB;
   next close N-07 shared revocations and production issuance durability. N-05
   persisted proposal/resource binding, S-04 webhook verification, and S-05
   tenant-promote authorization are locally complete; retain their
   provider/hosted evidence gates.
4. **Independent evaluation:** N-02 runnable raw extraction inputs, N-03
   deterministic pipeline producers, private holdouts, E-06/E-07 trajectory
   and shadow evaluation, E-08 red-team corpus, and E-10/E-11 gate extensions.
5. **Product and release honesty:** N-04 YieldArbitrage contract is locally
   complete; remaining work is the X-10 checker-model decision, simulated-copy sweep, visual review of the now
   honest landing/offline states,
   generated OpenAPI/type drift CI, BFF/SSE browser smoke, and the 12 lint
   warning remediations.
6. **Operational and human gates:** metrics/alerts, backup+restore drill,
   image scan/non-root inspection, migration release, rollback, provider
   credentials/webhooks, privacy/legal review, pilot cohort and business-model
   decisions. Only then prepare the conditional pilot decision record.

### Exit evidence required for the next plan revision

- Full backend and frontend gates remain green after each ordered group.
- A current ledger covers every path immediately before any Git mutation.
- Every promoted eval lane cites an independent producer, evidence tier, and
  holdout result; mirror lanes cannot become authoritative by score alone.
- Every external claim is backed by provider/browser/hosted/operator evidence,
  or is explicitly labeled simulated/unknown in the product and docs.
- The launch decision names an owner, exposure boundary, rollback trigger,
  restore proof, and unresolved-risk acceptance; no local test aggregate can
  substitute for those decisions.

## 2026-09-04 continuation addendum — exact-head readiness and F-07 inspection

This addendum preserves the original phased plan and records the two bounded
slices completed after the earlier refresh.

### Completed slices

1. **LR-B08/LR-B09 exact-head readiness (local):** `/ready` is public through
   the narrow health allowlist, deployment verification targets `/ready`, and
   the handler resolves the single Alembic head from the running artifact,
   queries every `alembic_version` row, and fails closed for stale, empty,
   multi-row, multi-head, or unreadable graphs. Focused readiness/auth tests:
   **13 passed, 15 deselected**.
2. **F-07 durable poison inspection (local):** the canonical SQL
   `RequeueJobStore` exposes a bounded, deterministic, payload-free poisoned-job
   projection with trip filtering and pagination. PostgreSQL-backed queue
   tests: **34 passed**. Replay, purge, tenant-facing API, and operator audit
   semantics remain separate tasks.

### Updated dependency order

1. Preserve and classify the mixed worktree; do not create a release snapshot
   from unknown ownership.
2. Keep exact-head readiness and metadata ownership ahead of any blocking
   migration gate; A-20 still has 37 visible operations and an untracked
   migration tail.
3. Add bounded DB/Redis timeout contracts and fault-injection tests.
4. Reconcile F-07 queue ownership with tenant scope before adding an HTTP
   inspection route; keep shadow `DLQInspector` replay/purge non-authoritative.
5. Implement shared revocation/run-ledger durability, then backups/restore and
   worker/multi-replica drills.
6. Add independent evaluation producers, holdouts, trajectory/red-team lanes,
   and calibrated judging.
7. Ratify metrics exposure/format and add real telemetry, alerts, and error
   tracking.
8. Complete provider, legal/privacy, browser/device, accessibility, and
   operator gates before the conditional pilot decision.

### Current evidence matrix

- Isolated backend run: **3,733 passed, 44 skipped, 0 failed**; no `:8000`
  server detected, so server-dependent integration paths were skipped.
- Broader server-present run: **3,760 passed, 10 skipped, 0 failed**; useful
  integration coverage, but explicitly non-hermetic.
- Frontend: **1,311 tests**, typecheck, build, and lint pass.
- Findings: **183 rows — 108 open, 69 closed, 6 deferred**.
- Custody: final29 validates **521 live paths / 522 porcelain rows including
  the ledger**.

Neither backend receipt substitutes for hosted/provider/legal/operator proof.
The plan remains a dependency graph toward a bounded invite-only pilot, not an
authorization to stage, commit, push, deploy, or expose external effects.
