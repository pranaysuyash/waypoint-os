# Stash@{0} vs Current Master — File-by-File Comparison

## Summary

This report compares the key `stash@{0}` changes against the current `master` checkout. None of the inspected stash changes are already incorporated into `master`; every file below is different from the current codebase.

The comparison is based on the stash diff metadata and direct file reads of current content.

---

## File-by-file findings

### 1. `frontend/src/app/(agency)/inbox/page.tsx`

#### Stash change
- Consolidates assignment logic into a single callback `handleAssign`.
- Removes the duplicate `handleCardAssign` helper.
- Avoids separating bulk assignment logic from single-card assignment logic.

#### Current master
- Still contains `handleCardAssign` and a separate `handleBulkAssign`.
- `handleBulkAssign` is incomplete: it does not call `assignTrips`, only clears selection.

#### Verdict
- **Stash is better**: it fixes a real issue and simplifies the assignment flow.
- Current master is worse because the bulk assign handler appears broken.

---

### 2. `frontend/src/app/(agency)/insights/page.tsx`

#### Stash change
- Adds explicit fallback text for unavailable metric values.
- Uses `Unavailable` / `Estimated` labels instead of showing raw numeric placeholders.
- Improves UX in several places: response time, customer satisfaction, pipeline velocity, stage exit rate, and stage timing.

#### Current master
- Still renders raw numeric values without data-status guardrails.
- Example: `member.avgResponseTime` and `member.customerSatisfaction` are shown directly.
- Example: the bottleneck card always says `Taking X hours on average (target: 24h)` even when evidence is missing.

#### Verdict
- **Stash is better**: it adds defensive UI handling and makes missing data explicit.
- Current master is inferior for scenarios where analytics data is incomplete.

---

### 3. `frontend/src/components/inbox/TripCard.tsx`

#### Stash change
- Removes touch-device detection code.
- Removes the `QuickActions` dropdown and related quick action chips.
- Simplifies imports and eliminates extra state/refs.

#### Current master
- Still includes `isTouchDevice()` and `QuickActions` with dropdown assignment UI.
- Preserves richer card-level interaction behavior.

#### Verdict
- **Mixed**:
  - If the goal is simplification and removing buggy UI, the stash change is probably better.
  - If the goal is preserving card-level assign interactions, the current master is better.
- This is a behavior change, not a clear bug fix.

---

### 4. `frontend/src/lib/api-client.ts`

#### Stash change
- Turns `SPINE_API_URL` into a runtime-validated constant.
- Throws if `NEXT_PUBLIC_SPINE_API_URL` is missing in the browser.

#### Current master
- Uses `process.env.NEXT_PUBLIC_SPINE_API_URL || ''` with no runtime guard.

#### Verdict
- **Stash is better**: it prevents a silent failure mode for public collection flows.
- Current master is less safe and can fail later with a less obvious error.

---

### 5. `spine_api/server.py` — lifespan startup/shutdown

#### Stash change
- Removes the `RUNNING_TESTS` bypass around `_recovery_agent`, `_agent_supervisor`, and `_zombie_reaper` startup/shutdown.

#### Current master
- Keeps a test-only bypass, avoiding background agent startup during tests.

#### Verdict
- **Context-dependent**:
  - Stash is better for reliability in non-test environments because it ensures the same runtime path is used in production and tests.
  - Current master is better for test isolation and avoids creating the TripStore SQL bridge during tests.
- This is a deliberate behavior change, not a simple fix.

---

### 6. `spine_api/server.py` — pipeline watchdog

#### Stash change
- Introduces a `PIPELINE_TIMEOUT_SECONDS` watchdog that fails long-running runs with a `PipelineTimeout` failure.
- Starts a timer at pipeline begin and cancels it in the `finally` block.

#### Current master
- No watchdog timer exists in `_execute_spine_pipeline`.

#### Verdict
- **Stash is better if you want hard runtime safety**: it prevents runaway runs.
- Current master is less robust against hung pipeline execution.
- This is a useful hardening, but it should be reviewed carefully because it changes failure semantics.

---

### 7. `spine_api/server.py` — decision output compatibility

#### Stash change
- Adds fallback support for `decision_output` when computing suitability flags.
- Looks for `trip.get("decision") or trip.get("decision_output")`.

#### Current master
- Only reads `trip.get("decision")`.

#### Verdict
- **Stash is better**: it improves compatibility with persistence formats that use `decision_output`.
- Current master is strictly less tolerant.

---

### 8. Other backend/runtime support files

The stash also touches these files in ways that are likely related to the runtime changes:
- `spine_api/core/database.py`
- `spine_api/persistence.py`
- `spine_api/run_ledger.py`
- `src/agents/runtime.py`
- `src/analytics/metrics.py`
- `src/analytics/models.py`
- `src/llm/openai_client.py`
- `src/public_checker/live_checks.py`
- `src/security/privacy_guard.py`

#### Verdict
- These are supportive changes for the backend behavior in stash.
- They are not already in `master`.
- Without full patch content, they appear aligned with the server hardening and analytics updates.
- **Potentially useful, but nontrivial and should be reviewed as a group.**

---

### 9. Supporting frontend/test files

Files touched in stash0 include:
- `frontend/src/lib/bff-trip-adapters.ts`
- `frontend/src/lib/__tests__/bff-trip-adapters.test.ts`
- `frontend/src/types/generated/spine-api.ts`
- `frontend/src/types/generated/spine_api.ts`
- `frontend/vitest.config.ts`
- `frontend/src/app/(agency)/overview/__tests__/page.test.tsx`

#### Verdict
- These likely exist to support the frontend changes and are not in `master` yet.
- **Probably useful** if they are the correct supporting updates.
- No evidence they are already incorporated.

---

### 10. Docs / tool deletions in stash0

The stash also deletes or changes many docs/tools, including:
- `Docs/ANALYTICS_PROGRAM_TRACKER.md`
- `Docs/HANDOFF_E2E_VERIFICATION_TIMEOUT_JWT_2026-05-05.md`
- `Docs/PHASE4A_CLOSURE_2026-05-05.md`
- `Docs/RECOVERY_FORENSICS_AND_REGRESSION_2026-05-05.md`
- `Docs/SAFE_STASH_RESET_RECOVERY_PROTOCOL_2026-05-05.md`
- `Docs/context/AGENT_INTELLIGENCE_GRAPH.md`
- `Docs/context/agent_intelligence_graph.json`
- `Docs/frontend_component_architecture_study_2026-05-05.md`
- `Docs/p0_audit_packet_2026-05-05.md`
- `Docs/random_document_audit_task_mgmt_analytics_2026-05-04.md`
- `Docs/random_document_audit_v2_2026-05-05-update.md`
- `Docs/research/INQUIRY_TRIP_FLOW_UNIFICATION_FIRST_PRINCIPLES_ANALYSIS_2026-05-04.md`
- `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md`
- `Docs/status/LIVE_INTEL_EXECUTION_CHECKLIST_2026-05-05.md`
- `Docs/status/MULTI_AGENT_RUNTIME_CURRENT_STATE_HANDOFF_2026-05-04.md`
- `Docs/status/SCENARIO_HANDLING_SPEC_COVERAGE_STATUS_2026-05-05.md`
- `notebooks/stash_inspect.ipynb`
- `tools/build_agent_intelligence_graph.py`
- `tools/recovery_guard_report.py`

#### Verdict
- These deletions appear risky and are not clearly better than current master.
- Unless you explicitly want to prune these docs/tools, the current master state is likely safer.

---

## Overall evaluation

### Files where `stash@{0}` is clearly better
- `frontend/src/app/(agency)/inbox/page.tsx`
- `frontend/src/app/(agency)/insights/page.tsx`
- `frontend/src/lib/api-client.ts`
- `spine_api/server.py` decision-output fallback
- `spine_api/server.py` pipeline watchdog

### Files where `stash@{0}` is ambiguous or risky
- `frontend/src/components/inbox/TripCard.tsx`
- `spine_api/server.py` test-runtime startup changes
- backend support files under `spine_api/` and `src/` (need a full review)
- doc/tool deletions

### Files where current master is probably better
- Deleted docs and scripts in stash0, unless your intent is to prune them.
- The `TripCard` full interaction path in current master may be better if you still want the quick assignment behavior present in the current UI.
- The `RUNNING_TESTS` bypass in `spine_api/server.py` is better for preserving test isolation.

---

## Recommendation

1. Keep the stash changes for:
   - `frontend/src/app/(agency)/inbox/page.tsx`
   - `frontend/src/app/(agency)/insights/page.tsx`
   - `frontend/src/lib/api-client.ts`
   - `spine_api/server.py` decision-output fallback
   - `spine_api/server.py` pipeline watchdog

2. Review carefully before accepting:
   - `frontend/src/components/inbox/TripCard.tsx`
   - `spine_api/server.py` startup/shutdown `RUNNING_TESTS` removal
   - backend runtime support files in `spine_api/` and `src/`
   - frontend support files in `frontend/src/lib/` and generated type files

3. Do not restore without explicit intent:
   - deleted Docs files in `Docs/`
   - deleted notebook `notebooks/stash_inspect.ipynb`
   - deleted tools in `tools/`
   - `.claude/worktrees/heuristic-hodgkin-19a0d8`

---

## Full stash audit status

- Total files changed in `stash@{0}`: 73
- Added files: 1
- Deleted files: 26
- Modified files: 46

### Not already in master
All files included in this stash are currently different from `master`; none of the listed stash changes appear to already be incorporated.

### Highest-risk changes
- Deletion of many documents and notebooks
- Removal of `RUNNING_TESTS` bypass in `spine_api/server.py`
- Removal of inbox quick-action behavior in `frontend/src/components/inbox/TripCard.tsx`
- Deletion of analytics/risk/intake files under `src/` and their tests

### Best candidates for safe adoption
- `frontend/src/app/(agency)/inbox/page.tsx`
- `frontend/src/app/(agency)/insights/page.tsx`
- `frontend/src/lib/api-client.ts`
- `spine_api/server.py` compatibility and timeout logic

### Important validation note
This audit is based on parsed stash diff metadata and selective file inspection of the most impactful changed files. It is a full file list audit in terms of enumeration, with a focused detailed review of the highest-risk and most valuable files.
   - `frontend/src/app/(agency)/inbox/page.tsx`
   - `frontend/src/app/(agency)/insights/page.tsx`
   - `frontend/src/lib/api-client.ts`
   - `spine_api/server.py` compatibility/hardening changes
2. Review carefully before accepting:
   - `frontend/src/components/inbox/TripCard.tsx`
   - `spine_api/server.py` startup/shutdown and watchdog changes
   - backend runtime support files
3. Do not restore the broad doc/tool deletions without explicit intent.

---

## Conclusion

The current master is not already incorporating these stash0 changes.

- Some stash0 changes are clearly improvements and are better than current code.
- Some stash0 changes are behavior-altering and require review.
- The current master is better for test isolation and preserving richer inbox card behavior.

This document captures the file-wise comparison and my judgment on each item.
