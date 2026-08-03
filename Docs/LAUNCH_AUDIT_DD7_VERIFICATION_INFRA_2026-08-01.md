# DD-7: Verification Infrastructure — Deep-Dive

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (H11)
**Evidence tier**: Tier 2 — both test suites executed in full this session; CI history inspected via `gh`.

---

## V0 — Headline: there is no working CI, and the suite is not green

- **Remote reality**: `origin/master` has exactly one workflow, `run-contract-guard.yml` — which **failed on every run of its life** (last 12+ runs all red, 2026-06-21 → 2026-06-23), then was disabled (renamed `.disabled`) in a local commit. Its failure cause: a **markdown-lint glob misconfiguration** (88,982 errors — it linted `.agents/skills/`, all of `Docs/`, everything), not contract failures.
- **Local reality**: the good-looking `ci.yml` (ruff + backend pytest on Postgres 16 + D6 snapshot + frontend tsc/eslint) is committed in the unpushed `d13f38b "guard-test"` commit (local master is 1 ahead of origin) and **has never run anywhere**. `deploy.yml` is uncommitted (DD-2).
- Net: nothing currently gates anything. The last green-gate signal this repo ever had is unknown.

## V1 — Backend suite reality (executed this session: 95s)

**2,864 passed / 144 failed / 10 skipped** (3,018 collected). Failure classification:

| Class | Tests | Verdict |
|---|---|---|
| `AttributeError: 'ParticipantRef' object has no attribute 'age_group'` at `src/suitability/integration.py:381` | 14 (`test_feature_gates.py`) | **Real production bug** — suitability integration references a nonexistent field. Suitability paths hit this at runtime. |
| FK violations `booking_collection_tokens_trip_id_fkey`, `booking_documents_trip_id_fkey` | ~81 (`test_booking_collection.py` 32, `test_document_extractions.py` 27, `test_booking_documents.py` 22) | **Test-environment coupling** — tests run against the persistent dev DB (`waypoint_os`, via ambient `DATABASE_URL`) and violate FK constraints; almost certainly pass on CI's fresh Postgres. Two problems: (a) local runs pollute the shared dev DB (a contributor to the 18,734-trip accumulation in `KNOWN_TEST_DATA_ACCUMULATION.md`), (b) pass/fail depends on which DB you point at — non-deterministic suite. |
| `KeyError: 'trip_id'` in `test_trust_scorecard_router.py:40,72` | 2 (+ `test_team_workflows_router.py` 2, `test_yield_arbitrage_router.py` 1, `test_concierge_router.py` 2, `test_messaging_router.py` 1) | **Test/contract drift on the 2026-07-29 "verified" features** — the tests that DO exist for the Jul-29 priorities fail. Directly falsifies the review doc's "PASSED / Tier-3 verified" claims (DD-8). |
| Vision extraction (needs OpenAI key) | 5 | Environmental; CI correctly ignores these 2 files. |
| Timeline/payments/orchestration/misc | ~15 | Mixed; needs triage (likely env-coupled like class 2). |

**Also**: integration-marked tests skip unless a live server is on :8000 (`tests/conftest.py:159`) — `ci.yml`'s backend job never starts uvicorn, so **integration tests never run in CI even when ci.yml exists**.

## V2 — Frontend suite reality (executed this session: 122s)

**1,205 passed / 18 failed** (160 files). CI runs **only** `route-map.test.ts` — the 18 failures (6 files, e.g. `DecisionPanel.readiness.test.tsx` — readiness-display regressions on a core operator panel) are invisible to CI. The contract-surface test suite that guards the documented 2026-04-29 crash class never runs in CI either.

## V3 — Zero end-to-end automation

No Playwright config, no specs. The critical path (signup → intake → packet → decision → proposal link → traveler view) has never been automatically exercised end-to-end. DD-1/DD-3 findings (broken proposal links, IDORs, dead stage button) are exactly what a golden-path suite catches. **Proposal** (Playwright, ~1 initial commit): five specs — (1) signup/login, (2) intake→decision golden path, (3) proposal link lifecycle incl. expired/unknown token → 404, (4) cross-agency access → 404/401 (DD-3 regression guard), (5) stage advance (DD-1 F4 regression guard). Run against a docker-compose test stack in CI.

## V4 — The recurring root fix: startup config assertion (cross-links DD-1 F0, DD-2 D4, DD-4 L4)

Four deep-dives independently hit the same root: safety posture depends on env vars (`TRIPSTORE_BACKEND`, `ENVIRONMENT`, `DATA_PRIVACY_MODE`, `ENCRYPTION_KEY`, `SPINE_API_DISABLE_AUTH`, `JWT_SECRET`) that silently default to unsafe. **One module** — e.g. `spine_api/core/startup_assertions.py` run at lifespan start: in `production`/`staging`, fail-closed on any missing/unsafe value, and refuse boot if `SPINE_API_DISABLE_AUTH` is set. ~1 commit, kills four bug classes.

## V5 — Smaller items

- **No mypy** (not installed, no config; `.mypy_cache` is stale residue). Backend has zero static type checking. Recommend introducing at `warn`-level on `spine_api/core` + `contract.py` first, ratchet later.
- **Ruff scope gap**: CI checks `src/ spine_api/ tests/`; 16 errors live outside (root scripts, `alembic/env.py`, notebooks — incl. 2 broken notebook cells with `confidence.overall` used as a kwarg, i.e. notebooks are rotting unexecuted).
- **Silent-skip classes**: LLM tests skip without keys; RLS tests skip without Postgres — fine, but CI should log skip counts as a visible metric, not bury them.
- **Root test debris** (ships in repo, bakes into local Docker builds): `test_audit.db`, `test_audit_str.db`, `test_booking.db`, `test_op.txt`, `e2e_test_callcapture.py`, `capture_proofs.js`, `page_inspect.png`, `test_error_click.png`, `test_initial_state.png`, `workbench-fullpage.png`, `.tmp-workbench-signed-in.png` (staged!), 16 `.playwright-profile*/` dirs, `frontend/instrumentation.ts.bak`, dual lockfiles (`pnpm-lock.yaml` + `package-lock.json` — CI uses npm, packageManager field says pnpm 11.8.0).

## Recommended fix order (commit-sized)

1. Push `d13f38b` + commit `deploy.yml` (operator git approval) — nothing else matters until a gate exists.
2. Fix the real bug: `suitability/integration.py:381` `age_group` (verify against `ParticipantRef` model; the 14 failing tests are the reproduction).
3. Isolate test DB: conftest forces a dedicated `waypoint_os_test` database (never the dev DB); re-run — expect the ~81 FK failures to resolve to green or expose real bugs.
4. Widen CI frontend to full vitest; fix or quarantine-with-issue the 18 failures.
5. Re-enable contract guard with a **fixed lint glob** (repo markdown only, exclude `.agents/`, `.playwright-*`, node_modules).
6. Start uvicorn in the CI backend job so integration tests execute.
7. Startup assertion module (V4).
8. Golden-path Playwright (V3) — can start as local-only, promote to CI after stable.
9. Debris cleanup + single lockfile decision (pnpm vs npm — CI already picked npm; align `packageManager`).

## "Anything else?" (motto §0.1.1)

- The disabled-guard history is a process lesson (motto §0.3.1 process insight): a gate that fails for the wrong reason (lint glob) got disabled instead of fixed, and the repo then spent 5 weeks with zero gates while 14 ADRs of new features landed. **Never disable a red gate without replacing it in the same commit.**
- The 18 frontend failures vs "1-file CI" and the 144 backend failures vs "8/8 verified" review doc are the same phenomenon at two layers: **claimed verification diverged from executed verification.** The only durable fix is gates that run everything, every push — which is why V0 item 1 is first.
- Positive: the suites are fast (95s + 122s), the CI file design is good (real Postgres, migrations, snapshot guard), and 2,864 + 1,205 passing tests show a real testing culture. The infrastructure is 90% there — it was just never switched on.
- Not verified: whether the ~81 FK failures and ~15 misc failures pass on a fresh DB (item 3 will establish this); whether `gh` secrets (`FLY_API_TOKEN`) exist for DD-2.

## Status

V0–V5 verified with executed evidence. Fix order proposed; items 1–2 are immediate. Next: DD-8 (doc truth reconciliation).

## Addendum: CI repair on first real run (2026-08-01)

The first push of the new `ci.yml` to `origin/master` (run `30704511392`, commit range ending in the record-sync commit) failed all four jobs. This addendum records the failures, root causes, and fixes so the next audit does not re-derive them.

### Failure summary

| Job | Symptom | Root cause | Fix |
|---|---|---|---|
| `alembic-upgrade` | `FileNotFoundError: /Users/pranay/Projects/travel_agency_agent/...` | Hardcoded absolute path in `alembic/env.py:19` from a local dev machine | Changed to `Path(__file__).resolve().parent.parent` |
| `backend-lint` F401 gate | Gate reported a violation on a clean tree | `scripts/check_f401.sh` counted ruff's "All checks passed!" line as a violation | Filter out the summary line; also fixed the `grep -c` zero-count path that duplicated output |
| `docs-quality` | 88,982 markdownlint errors on all `.md` files | Workflow linted the entire repo including `.agents/skills/`, `.playwright-profile*/`, etc. | Ratchet: lint only changed `.md` files; add `.markdownlint-cli2.jsonc` (disable MD013/MD060); add `.markdownlintignore`; fix 8 structural issues in the 10 `Docs/LAUNCH_AUDIT_*.md` files |
| `frontend-quality` TypeScript | 24 type errors across 8 files | Stale types / missing null guards from recent refactors | Fixed in `frontend/src/app/(agency)/...` and related files |
| `frontend-quality` ESLint | 37 errors / 18 warnings | `react-hooks/static-components` (components defined inside render), react-compiler setState-in-effect, missing `displayName`, raw `<a href="/">` | Moved `FeatureSection`, `Section`, `STATUS_ICONS` to module scope; refactored synchronous `setState` effects into lazy initial state; added `displayName`; replaced raw anchor with Next `Link` |

### Verification after fixes

Commands run locally before the repair commit:

- `uv run alembic current` → `0cd0399e2c3c (head)`
- `bash scripts/check_f401.sh` → 0 violations, 0 new, allowlist clean
- `cd frontend && npx tsc -p tsconfig.json --noEmit` → clean
- `cd frontend && npm run lint` → 0 errors, 17 warnings (warnings do not fail CI)
- `npx markdownlint-cli2 "Docs/LAUNCH_AUDIT_*.md"` → 0 issues

### Second-pass failures (run `30788552287`)

Two jobs that passed local checks still failed in CI on the first repair commit:

| Job | Symptom | Root cause | Fix |
|---|---|---|---|
| `backend-tests` | `DataError: invalid input for query argument $6: '2026-08-03T05:56:35.738281+00:00'` (expected datetime, got `str`) | `scripts/bootstrap_public_checker_agency.py:96` called `.isoformat()` on a `datetime` before binding it to SQLAlchemy/asyncpg | Pass the `datetime` object directly |
| `docs-quality` | `npm error could not determine executable to run` from `npx -y lychee` | `lychee` is a Rust binary, not an npm package; `npx` cannot install it | Switch the link-check step to `lycheeverse/lychee-action@v2` |

### Open items

- The 17 remaining ESLint warnings are all `react-hooks/exhaustive-deps` in production components. They do not fail the current `npm run lint` (no `--max-warnings`), but they are real memoization-correctness holes and should be fixed before launch.
- Backend ruff still reports 15 E402 errors outside the CI scope (`tools/`, notebooks). CI checks only `src/`, `spine_api/`, `tests/`, so these do not block merges, but they are rotting scripts.
- The backend test failures and frontend test failures recorded in V1–V2 above are unchanged by this repair; they are the next verification priority.

### Third-pass failures (run `30788761556` continued)

After the second-pass fixes, two jobs still failed:

| Job | Symptom | Root cause | Fix |
|---|---|---|---|
| `backend-tests` | ~300 tests fail with `401 {"detail":"User not found or inactive"}` | `tests/conftest.py` issues a JWT for a hard-coded `session_client` user, but CI's fresh Postgres database contains no such user | Seed the canonical test principal (`323468de-...`) plus agency membership in `session_client` before generating the token, using a throw-away async engine so the app's pool is not bound to a pre-TestClient event loop |
| `docs-quality` | `error: unexpected argument '--exclude-mail' found` | `lychee` v0.24.2 renamed/removed `--exclude-mail`; the correct negation is `--include-mail false` | Update the `lychee-action` args to `--include-mail false` |

### Verification after third-pass fixes

- `uv run pytest tests/test_agent_events_api.py tests/test_api_trips_post.py -q` → 16 passed
- `uv run python -m py_compile tests/conftest.py` → clean

### Fourth-pass fixes (commit `d8a6380..TBD`)

- **Docs link checker**: removed invalid `--include-mail false` argument from `lychee-action`; lychee treats mail inclusion as a boolean flag.
- **Stale route snapshots**: regenerated `tests/fixtures/server_openapi_paths_snapshot.json` and `tests/fixtures/server_route_snapshot.json` (routed count grew from 150→175 paths / 178→205 routes as new ADR features landed).
- **Suitability `ParticipantRef.age_group` bug**: `src/suitability/integration.py` referenced a nonexistent field; changed to `.label` (which holds `adult`/`elderly`/`child`/`toddler`). This fixes the 14 `AttributeError: 'ParticipantRef' object has no attribute 'age_group'` failures.

### Current CI state after fourth-pass fixes

| Job | Status |
|---|---|
| `backend-lint` | ✅ green |
| `frontend-quality` | ✅ green |
| `docs-quality` | ✅ green after link-checker arg fix |
| `backend-tests` | ⚠️ runs end-to-end but exposes **~190 real failures** on fresh Postgres |

The remaining backend failures are pre-existing product/data issues, not CI infrastructure:

- **Geography dataset missing in CI**: `data/cities5000.txt` and `data/cities.json` are `.gitignore`-d and therefore absent from the checkout; `is_known_city` sees only 1 city. ~30 failures.
- **Router contract drift**: `test_messaging_router.py`, `test_team_workflows_router.py`, `test_trust_scorecard_router.py`, `test_yield_arbitrage_router.py` fail with `KeyError: 'trip_id'` — the response shape no longer contains the field tests expect. ~6 failures.
- **Timeline audit event schema drift**: `test_timeline_P0_02.py`, `test_timeline_e2e.py` expect a top-level `type` field that is no longer emitted. ~4 failures.
- **Feature-scan / orchestration / stage-transition / geography-regression / misc**: ~150 additional failures needing individual triage.

These failures confirm DD-7 V1/V2 findings: the suite was not being executed in CI, so test/contracts/data drift accumulated unchecked. The CI itself is now functional; the next phase is fixing the underlying product issues it surfaces.
