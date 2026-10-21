# Open Items Audit — travel_agency_agent (Waypoint OS)

- Author: Claude `nightly-thread-orchestrator`, run 2026-10-12 01:03 IST
- Scope: read-only inspection plus this doc. No code edits, no git (scheduled-task rule), no provider calls.
- Evidence tier: S0 static inspection (file reads, `grep`, `find -newer`). Nothing here is runtime, hosted, or production proof.

## Canonical stores (this audit indexes them and does not duplicate them)
The project already has canonical trackers. Per doctrine ("one canonical store"), open items live there:
- Launch decision and blockers: `Docs/LAUNCH_STATUS.md` (NO-GO public, CONDITIONAL GO pilot; 8 blockers, lines ~50–78)
- Findings lifecycle store: the `findings.py validate` register referenced in LAUNCH_STATUS (2026-09-14 snapshot: 106 open, 0 P0, ~54 P1)
- Execution/tasks: `Docs/review/EXECUTION_STATUS_2026-09-04.md`, `Docs/review/KNOWN_ISSUES_LEDGER_2026-09-04.md`
- Exploration: `Docs/EXPLORATION_TOPICS.md` (Codex already noted that E1/E2 exist as topics 36/37)
- Business TODOs: `TODO.md` (2026-04-30; customer discovery P0)

## Findings from this run

| ID | Finding | Evidence | Type | Assessment |
|---|---|---|---|---|
| TRV-N01 | LAUNCH_STATUS evidence snapshot is stale. The last refresh is 2026-09-14 (file mtime is 2026-09-30), but tests, tools, and sims changed after that. | `find -newer Docs/LAUNCH_STATUS.md` lists `tools/sim3_runner.py`, `tools/sim3_sims.py`, `Docs/sims/` (Oct 5), and about 15 `tests/test_*.py` files, e.g. `test_sim3_claim_framework.py`, `test_cross_tenant_router_probe.py`, `test_audit_log_chain_verify.py`. The doc says it "must be refreshed whenever the evidence snapshot … changes". | documentation | Doctrine-aligned rule that isn't being followed. Needs a fresh receipt run by whoever owns the current in-flight work. |
| TRV-N02 | 15 in-code TODO markers, all tagged to tracked IDs (PA-10, PA-13, PA-29, KDD-3, frontier FK normalization, IVR WebSocket push, legacy_ops cache key P1). | `grep -rnE "TODO\|FIXME\|HACK" spine_api src frontend/src`, e.g. `spine_api/metrics_registry.py:97`, `spine_api/server.py:2211`, `spine_api/models/frontier.py:36`, `spine_api/routers/legacy_ops.py:667`, `spine_api/routers/ivr_gateway.py:266`, `src/analytics/kdd/jobs.py:126` | implementation | They follow the long-term pattern (each references a tracker ID). Unverified: whether every ID still has an open row in the findings store. |
| TRV-N03 | `legacy_ops.py:667` TODO(P1) cache-invalidation key is a P1 correctness item buried in code. | file:line above | implementation | Check that a findings row exists. If not, add one (owner-side). |
| TRV-N04 | Root-level clutter: ad-hoc artifacts at repo root (`test_*.db`, `*.png`, `page_content.html`, `dogfood_cookies.txt`, `audit_test_results.txt`, `requirements..venv.snapshot.txt`, `CLAUDE.md.legacy-20260826`, `uv-*.lock`). | `ls` of the project root | owner decision | NOT deleted. `dogfood_cookies.txt` may hold session cookies, so it is a privacy/secret-hygiene concern. Content was not opened. Listed for owner review. |
| TRV-N05 | Blocker 8 says the dirty tree is not a release boundary, and an active `deploy.yml` deploys to Fly on every push to master while public launch is NO-GO. | LAUNCH_STATUS 2026-09-14 refresh note | owner decision | High-risk gate mismatch. It is already recorded in LAUNCH_STATUS, so it is re-surfaced here only. |
| TRV-N06 | `TODO.md` P0 is customer discovery (outreach). That is external-facing work and outside this orchestrator's lane. | `TODO.md:9-18` | owner decision | No agent action. External messaging is prohibited for the nightly task. |

## Best-in-class gaps (inferred, not verified)
- The findings store, LAUNCH_STATUS, and in-code TODO tags aren't cross-checked automatically. A small read-only check (each `TODO(<ID>)` must resolve to an open findings row) would stop drift. This is a candidate implementation task that needs an owner, because the tree has active parallel ownership.
- LAUNCH_STATUS refresh could be generated from `findings.py` and test-inventory receipts instead of hand-edited.

## Why no implementation tonight
The Codex register (line 129) records that the checkout is "heavily dirty and owner state unclear". Files changed as recently as Oct 5, so there is active parallel ownership. The doctrine says to preserve parallel work until it's classified, so this run made doc-only changes.
