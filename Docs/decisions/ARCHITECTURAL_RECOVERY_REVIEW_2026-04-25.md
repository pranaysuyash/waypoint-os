# Architectural Recovery Review - 2026-04-25

## Scope

This review was requested after evidence of stash/reset activity and concern that good work, docs, or architectural improvements may have been lost or regressed.

Rules applied:

- No destructive git operations.
- No wholesale stash apply.
- Preserve documentation history.
- Recover only changes that are additive, better, comprehensive, and compatible with current architecture.
- Reject duplicate API route shapes, stale imports, catch-all passthrough regressions, and lower-quality legacy paths.
- Use repo-local `AGENTS.md`, `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`, `Docs/context/agent-start/SESSION_CONTEXT.md`, and relevant skills: systematic debugging, search-first, and verification-before-completion.

## Findings

### 0. Review basis: code inventory, not docs alone

Verdict: expanded and corrected.

Evidence checked:

- Enumerated real files under `frontend/src/app/api`, `frontend/src/lib`, `frontend/src/components`, `spine_api`, `src`, and `tests`.
- Searched production code for route handlers, direct backend `fetch()` calls, `request.json()`, `proxyRequest()`, `sys.path`, bare `persistence` imports, duplicate catch-all mappings, `as any`, and suitability contract fields.
- Compared explicit Next API route shapes against `frontend/src/lib/route-map.ts`.

Decision:

- Treat docs as evidence only when they match code.
- Fix code mismatches where low-risk and document larger route/API consolidation findings explicitly.

### 1. Catch-all route map had one stale regression risk

Verdict: fixed.

Evidence:

- `frontend/src/lib/route-map.ts` is the deny-by-default registry for backend-backed catch-all proxy paths.
- The old stash included broader route-map behavior that would make frontend-local or explicit routes look backend-backed.
- The current architecture needs only `spine/run -> run` because the old explicit `/api/spine/run` route was deleted and the catch-all now owns that backend handoff.
- `scenarios` and `version` are frontend-local or explicit concerns and must not be added to the catch-all map.

Decision:

- Keep `["spine/run", "run"]`.
- Reject stale `scenarios`, `version`, and fallback passthrough mappings.
- Add route-map tests that prove `spine/run` resolves and `version`/`scenarios` return `null`.

Files:

- `frontend/src/lib/route-map.ts`
- `frontend/src/lib/__tests__/route-map.test.ts`

### 2. Catch-all route map duplicated explicit route ownership

Verdict: fixed for discovered overlaps.

Evidence:

- Actual explicit routes exist for:
  - `frontend/src/app/api/pipeline/route.ts`
  - `frontend/src/app/api/insights/agent-trips/route.ts`
  - `frontend/src/app/api/inbox/route.ts`
  - `frontend/src/app/api/runs/route.ts`
  - `frontend/src/app/api/trips/[id]/route.ts`
- `route-map.ts` also mapped the same frontend shapes through the catch-all proxy.
- Next.js explicit routes win, so those catch-all entries were dead duplicate ownership.

Decision:

- Remove duplicate route-map entries for `pipeline`, `insights/agent-trips`, `inbox`, `runs`, and `trips/{id}`.
- Keep subresource catch-all mappings such as `trips/{id}/timeline`, `runs/{id}`, and `runs/{id}/events` where no explicit route owns that path.
- Add tests proving explicit/local route shapes resolve to `null` in the catch-all registry.

Files:

- `frontend/src/lib/route-map.ts`
- `frontend/src/lib/__tests__/route-map.test.ts`

### 3. Explicit BFF routes bypassed shared BFF helpers

Verdict: improved without removing route-specific transformations.

Evidence:

- `frontend/src/app/api/pipeline/route.ts` and `frontend/src/app/api/runs/route.ts` were simple backend passthroughs but manually used `fetch`.
- `runs` also failed to forward auth headers.
- `proxy-core.ts` already owns timeout, auth forwarding, response header allowlist, cookie handling, no-store cache behavior, and proxy error mapping.
- Transform-heavy routes (`trips`, `inbox`, `reviews`, `reviews/action`, `inbox/[tripId]/snooze`, and `insights/agent-trips`) still need explicit BFF behavior because they adapt backend data into frontend presentation contracts.

Decision:

- Convert `pipeline` and `runs` explicit routes to `proxyRequest`.
- Move duplicated `trips` and `inbox` trip-shaping logic into `frontend/src/lib/bff-trip-adapters.ts`.
- Use `bffFetchOptions()` for transform-heavy explicit routes so auth forwarding, no-store behavior, timeout, and JSON body handling are shared.
- Keep route-specific transformations where they are still business/presentation adapters, rather than forcing those routes through the generic catch-all proxy.

Files:

- `frontend/src/app/api/pipeline/route.ts`
- `frontend/src/app/api/runs/route.ts`
- `frontend/src/app/api/trips/route.ts`
- `frontend/src/app/api/trips/[id]/route.ts`
- `frontend/src/app/api/inbox/route.ts`
- `frontend/src/app/api/reviews/route.ts`
- `frontend/src/app/api/reviews/action/route.ts`
- `frontend/src/app/api/inbox/[tripId]/snooze/route.ts`
- `frontend/src/app/api/insights/agent-trips/route.ts`
- `frontend/src/lib/proxy-core.ts`
- `frontend/src/lib/bff-auth.ts`
- `frontend/src/lib/bff-trip-adapters.ts`
- `frontend/src/lib/__tests__/bff-trip-adapters.test.ts`
- `frontend/src/lib/__tests__/bff-auth.test.ts`

### 4. Suitability rendering had a duplicate type shape

Verdict: fixed.

Evidence:

- `frontend/src/types/spine.ts` defines the frontend `SuitabilityProfile` shape used by `DecisionOutput`.
- The new `SuitabilityCard` had its own local duplicate `SuitabilityProfile` interface, which could drift from the canonical panel contract.

Decision:

- Use `type { SuitabilityProfile }` from `@/types/spine`.
- Render `decision.suitability_profile` as a typed field in `DecisionPanel`.
- Preserve backward compatibility by falling back to flat `suitability_flags` if the structured profile is absent.

Files:

- `frontend/src/types/spine.ts`
- `frontend/src/components/workspace/panels/DecisionPanel.tsx`
- `frontend/src/components/workspace/panels/SuitabilityCard.tsx`

### 4b. Workspace panel contracts used local schemas and `any` trip props

Verdict: fixed for the decision/timeline/change-history workspace flow.

Evidence:

- `DecisionPanel` accepted `trip?: any` and cast the active decision to `DecisionOutput`.
- `TimelinePanel` duplicated `TimelineEvent` and `TimelineResponse` locally even though generated backend contract types already exist.
- Generated `TimelineResponse.events` is optional, while the local panel schema treated it as always present.
- `ChangeHistoryPanel` accepted `trip?: any`.

Decision:

- Use `Trip` from `frontend/src/lib/api-client.ts` for workspace panel trip props.
- Use generated `TimelineEvent` and `TimelineResponse` from `@/types/spine`.
- Guard `TimelineResponse.events` with an empty-array fallback.
- Add logical-flow tests proving structured suitability profile precedence and timeline stage-filter fetching.

Files:

- `frontend/src/components/workspace/panels/DecisionPanel.tsx`
- `frontend/src/components/workspace/panels/TimelinePanel.tsx`
- `frontend/src/components/workspace/panels/ChangeHistoryPanel.tsx`
- `frontend/src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx`
- `frontend/src/components/workspace/panels/__tests__/TimelinePanel.test.tsx`

### 5. Production analytics modules still used bare persistence imports

Verdict: fixed for `src/analytics`; remaining path setup in server/watchdog is startup-path handling and was not changed in this pass.

Evidence:

- `src/analytics/review.py` mutated `sys.path` and imported `TripStore`/`AuditStore` from bare `persistence`.
- `src/analytics/logger.py` attempted bare `from persistence import AuditStore`.
- `src/analytics/metrics.py` imported bare `TripStore` inside alert persistence branches.

Decision:

- Replace production analytics imports with canonical `spine_api.persistence` imports.
- Remove now-unneeded `sys.path` mutation from `src/analytics/review.py`.
- Update review tests to patch `spine_api.persistence`, because patching bare `persistence` no longer validates the production import path.

Files:

- `src/analytics/review.py`
- `src/analytics/logger.py`
- `src/analytics/metrics.py`
- `tests/test_review_logic.py`
- `tests/test_review_policy_escalation.py`

### 6. Dashboard aggregator still had cwd-dependent import fallback

Verdict: fixed.

Evidence:

- `Docs/decisions/SESSION_CLOSURE_2026-04-24.md` said the `sys.path` fallback was removed.
- `src/services/dashboard_aggregator.py` still contained `sys.path.append(os.path.join(os.getcwd(), "spine_api"))` fallback blocks.
- The canonical import path is `from spine_api.persistence import AuditStore, TripStore`.

Decision:

- Remove the fallback import blocks.
- Import `AuditStore` and `TripStore` once at module load.
- This keeps dashboard aggregation on the canonical package path and avoids cwd-dependent behavior.

Files:

- `src/services/dashboard_aggregator.py`
- `Docs/decisions/SESSION_CLOSURE_2026-04-24.md`

### 7. Recovery docs did not show lost documentation in the stash/reset candidates

Verdict: confirmed; no doc recovery was needed from those candidates.

Evidence:

- The reset-lost commit `e03ae7e` touched only `frontend/src/app/globals.css` and `frontend/src/app/workbench/PipelineFlow.tsx`.
- The active stash touched only:
  - `frontend/src/app/api/[...path]/route.ts`
  - `frontend/src/lib/route-map.ts`
  - `spine_api/server.py`
  - `src/decision/hybrid_engine.py`
- Read-only checks found no deleted files under `Docs/` or `frontend/docs/` in the relevant recovery candidates.

Decision:

- Do not invent doc recovery where the stash/reset evidence does not contain docs.
- Preserve all current docs and reject doc deletions in any future recovery candidate by default.

Files:

- `Docs/status/GIT_RECOVERY_AUDIT_2026-04-25.md`
- `AGENTS.md`

### 8. Stale duplicate budget feasibility table was already consolidated

Verdict: kept and documented.

Evidence:

- The audit closure test expects `BUDGET_FEASIBILITY_TABLE` to be canonical in `src.decision.rules`.
- `src/intake/decision.py` now aliases the canonical rules table instead of maintaining a duplicate local table.

Decision:

- Keep canonical table ownership in `src.decision.rules`.
- Keep intake as a consumer.

Files:

- `src/decision/rules/__init__.py`
- `src/intake/decision.py`

## Rejected Recovery Fragments

- Stale catch-all fallback passthrough behavior.
- Duplicate explicit API route shapes.
- Route-map entries for frontend-local or explicit routes such as `/api/version` and `/api/scenarios`.
- Any doc deletion or doc-history loss.
- Any stale import path that duplicates canonical package imports.

## Residual Risks

- `DecisionOutput.suitability_profile` is a frontend contract type layered over the current backend decision dict. It is compatible with the shadow-field rollout, but a future generated backend response contract should formalize this nested decision shape.
- `DecisionPanel` still has broader typing weaknesses around `trip?: any`; this review did not expand scope into a full workspace panel type migration.
- Review-specific and insight-specific presentation adapters still live inside their route files. That is acceptable for now because they are not duplicated like the old trip/inbox transforms, but they should move to typed adapter modules if they grow.
- `reviews/action` and `inbox/[tripId]/snooze` still parse request JSON locally because they translate frontend field names to backend field names. They now use shared BFF fetch options for the outbound call.
- `spine_api/server.py` and `spine_api/watchdog.py` still adjust `sys.path` for application startup contexts. This pass removed production analytics fallbacks, but did not rewrite startup path bootstrapping.
- This review used targeted backend/frontend tests and TypeScript checks. A full repository test run remains useful before a release checkpoint.

## Verification

Commands run after the review changes:

- `PYTHONPATH=. uv run pytest -q tests/test_audit_closure_2026_04_24.py tests/test_integrity.py tests/test_review_logic.py tests/test_review_policy_escalation.py` -> `36 passed`
- `cd frontend && npx tsc --noEmit` -> passed
- `cd frontend && npx vitest run src/lib/__tests__/route-map.test.ts src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx src/components/workspace/panels/__tests__/SuitabilityPanel.test.tsx` -> `3 files passed, 30 tests passed`
- `cd frontend && npx vitest run src/lib/__tests__/bff-trip-adapters.test.ts src/lib/__tests__/bff-auth.test.ts src/lib/__tests__/route-map.test.ts src/lib/__tests__/inbox-helpers.test.ts src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx src/components/workspace/panels/__tests__/SuitabilityPanel.test.tsx` -> `6 files passed, 91 tests passed`
- `cd frontend && npx vitest run src/components/workspace/panels/__tests__/TimelinePanel.test.tsx src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx` -> `2 files passed, 23 tests passed`
- `cd frontend && npm run build` -> passed
- Explicit/catch-all route overlap check -> `no explicit/catch-all route overlaps`
- `git diff --check` -> passed

## Architectural Verdict

Recovery status: successful for the inspected stash/reset candidates.

No docs were lost from the inspected candidates. The useful code was either already present, selectively recovered, or reworked into the current architecture. Lower-quality fragments were rejected rather than merged blindly.

Merge readiness: pending final fresh verification and user approval to commit.
