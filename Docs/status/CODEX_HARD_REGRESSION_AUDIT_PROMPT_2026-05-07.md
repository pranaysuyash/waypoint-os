# Codex Hard Regression Audit Prompt (server.py refactor)

Use this prompt after every refactor phase.

```
You are reviewing a refactor of `spine_api/server.py` in repo `travel_agency_agent`.

Your job is not to praise the refactor. Your job is to prove whether it preserved behavior, reduced risk, and improved architecture without regressions.

## Context

Original goal:
- Refactor `spine_api/server.py`, currently ~5k LOC with 100+ route decorators.
- Use phased extraction only.
- No rewrite-from-scratch.
- No API contract changes.
- Preserve startup fail-fast behavior.
- Preserve auth/rate-limit/audit/Product B side effects.

Critical behavior that must remain unchanged:
1. `PUBLIC_CHECKER_AGENCY_ID` env resolution.
2. SQL-mode public checker agency fail-fast startup invariant.
3. Product B event instrumentation.
4. Product B KPI endpoint behavior.
5. Public checker reduced persistence contract.
6. Authenticated `/run` lifecycle behavior.
7. Run ledger/event/draft side effects.
8. Auth, permission, rate-limit, and audit behavior.
9. Route method/path/response-model parity.
10. `uvicorn spine_api.server:app` compatibility.

## Files to inspect
Inspect all changed files in this branch/PR, especially:
- `spine_api/server.py`
- any new `spine_api/app_factory.py`
- any new `spine_api/bootstrap/*`
- any new `spine_api/routes/*`
- any new `spine_api/services/*`
- tests added/changed
- docs under `Docs/status/`

Also compare against the pre-refactor baseline from the previous commit.

## Required analysis

### 1. Regression check
Compare before vs after and answer:
- Did any endpoint method/path disappear or change?
- Did any response model change?
- Did any auth/dependency behavior change?
- Did any rate-limit decorator move/disappear?
- Did any audit side effect disappear?
- Did any Product B event side effect change?
- Did startup behavior change?
- Does `spine_api.server:app` still work?
- Did public checker persistence include private/internal compartments?
- Did authenticated `/run` preserve run ledger/event/draft/strict leakage reset and agency/user scoping?

For each item, provide:
- PASS / FAIL / UNCLEAR
- evidence from code/tests
- file/line references
- exact fix if FAIL/UNCLEAR

### 2. Architecture improvement check
Evaluate:
- Is `server.py` thinner?
- Are route handlers thinner?
- Did orchestration move into services?
- Are startup guards isolated cleanly?
- Are routers grouped coherently?
- Are services independent from `spine_api.server`?
- Are dependencies explicit or still hidden globals?
- Did duplication reduce without merging distinct security contracts?

For each, provide:
- Improved / Same / Worse / Unclear
- evidence
- recommended next step

### 3. Verification evidence check
Required evidence:
- route parity snapshot before/after
- OpenAPI path parity or schema diff
- startup invariant tests
- public checker agency config tests
- Product B event tests
- public checker run smoke
- public checker events smoke
- Product B KPI smoke
- authenticated `/run` lifecycle smoke
- docs/status evidence for the phase

Mark each:
- PRESENT / MISSING / INSUFFICIENT

### 4. Hidden coupling check
Look for:
- service imports back into `spine_api.server`
- circular imports
- startup objects initialized at import-time unexpectedly
- background agents started in tests
- strict leakage global state not reset
- auth/public checker assumption mixing
- dependency loss during APIRouter movement
- pydantic model drift from `spine_api.contract`
- env loading order drift
- middleware/instrumentation ordering drift

For each issue:
- severity (blocker/high/medium/low)
- evidence
- fix

### 5. Test commands
Run or specify:
```bash
python scripts/snapshot_server_routes.py
pytest tests/test_public_checker_agency_config.py -q
pytest tests/test_product_b_events.py -q
pytest tests/test_agent_events_api.py -q
pytest tests/test_spine_pipeline_unit.py -q
pytest tests/test_server_route_parity.py -q
pytest tests/test_server_startup_invariants.py -q
```
If not run, state exactly why and what evidence is missing.

### 6. Output format
Return exactly:
1. Verdict: Accept / Accept with modifications / Reject
2. Regression Matrix (Area, Status, Evidence, Risk, Fix)
3. Architecture Delta (Area, Before, After, Improved?, Notes)
4. Top 10 Findings (ranked with evidence and exact fix)
5. Missing Verification
6. Required Before Merge
7. Safe Next PR

## Non-negotiable review rules
- Do not approve based on intent.
- Missing evidence is UNCLEAR, not PASS.
- Do not recommend rewrites/framework migration.
- Do not suggest API contract changes in this PR unless flagging a future bug-fix PR.
```
