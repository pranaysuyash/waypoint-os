# Stash@{0} Useful Extracts

This document extracts the most valuable and low-risk stash fragments from `stash@{0}` as compared to the current `master` checkout. It is intentionally narrow: only the changes that appear clearly better or safe to adopt are included, with exact diff snippets where possible.

## Key useful stash fragments

### 1. `frontend/src/app/(agency)/inbox/page.tsx`

**Why it is useful**
- Consolidates single-card and bulk assignment logic into one callback.
- Fixes a broken bulk assign path that previously cleared selection without calling `assignTrips`.
- Simplifies callback wiring and makes `BulkActionsToolbar` use the same handler as card assignment.

**Selected diff**
```diff
-  const handleCardAssign = useCallback((tripId: string, agentId: string) => {
-    assignTrips({ tripIds: [tripId], assignTo: agentId, notifyAssignee: true });
-  }, [assignTrips]);
-
-  const handleBulkAssign = useCallback((agentId: string) => {
-      const tripIds = [...selectedTrips];
+  const handleAssign = useCallback((agentId: string) => {
+    assignTrips({ tripIds: Array.from(selectedTrips), assignTo: agentId, notifyAssignee: true });
     handleClearSelection();
   }, [selectedTrips, handleClearSelection, assignTrips]);
@@
-          onAssign={handleBulkAssign}
+          onAssign={handleAssign}
@@
-              onAssign={handleCardAssign}
-              agents={agents}
```

**Recommendation**
- Keep this stash fragment. It is a real behavior fix and simplifies the inbox assignment flow.

### 2. `frontend/src/app/(agency)/insights/page.tsx`

**Why it is useful**
- Adds explicit UI handling for missing or estimated analytics values.
- Prevents raw undefined numbers from surfacing to the operator experience.
- Improves clarity in pipeline, team metrics, stage exit rates, stage timing, and bottleneck analysis.

**Selected diff**
```diff
-        <span className='text-ui-sm text-[#e6edf3]'>{member.avgResponseTime}h</span>
+        <span className='text-ui-sm text-[#e6edf3]'>
+          {member.avgResponseTime == null ? 'Unavailable' : `${member.avgResponseTime}h`}
+        </span>
@@
-        <span className='text-ui-sm text-[#e6edf3]'>{member.customerSatisfaction}/5</span>
+        <span className='text-ui-sm text-[#e6edf3]'>
+          {member.customerSatisfactionDataStatus === 'evidence_backed'
+            ? `${member.customerSatisfaction}/5`
+            : 'Unavailable'}
+        </span>
@@
-        Taking {analysis.avgTimeInStage} hours on average (target: 24h)
+        Taking {analysis.avgTimeInStage} hours on average ({analysis.evidenceTrips} evidence trips)
+      </p>
+      {analysis.dataStatus !== 'evidence_backed' && (
+        <p className='text-ui-xs text-[#8b949e] mb-3'>
+          Metric confidence: {analysis.dataStatus === 'estimated' ? 'Estimated from coarse timestamps' : 'Unavailable'}
+        </p>
+      )}
@@
-          subtext='In progress'
+          subtext={
+            summary.pipelineValueDataStatus === 'evidence_backed'
+              ? 'In progress'
+              : summary.pipelineValueDataStatus === 'estimated'
+              ? 'Estimated'
+              : 'Unavailable'
+          }
@@
-                  <span className='text-ui-xs text-[#8b949e]'>{stage.tripCount} trips · {stage.exitRate}% exit</span>
+                    <span className='text-ui-xs text-[#8b949e]'>
+                      {stage.tripCount} trips · {stage.exitDataStatus === 'unavailable' ? 'Exit unavailable' : `${stage.exitRate}% exit`}
+                    </span>
@@
-                  {stage.avgTimeInStage}h
+                  {stage.timingDataStatus === 'unavailable' ? 'N/A' : `${stage.avgTimeInStage}h`}
```

**Recommendation**
- Keep this stash fragment. It hardens insights UI for incomplete analytics and is likely safe to adopt.

### 3. `frontend/src/lib/api-client.ts`

**Why it is useful**
- Adds a runtime guard for `NEXT_PUBLIC_SPINE_API_URL`.
- Prevents silent failure when the public API URL is not configured in the browser.

**Selected diff**
```diff
-const SPINE_API_URL = process.env.NEXT_PUBLIC_SPINE_API_URL || '';
+const SPINE_API_URL = (() => {
+  const url = process.env.NEXT_PUBLIC_SPINE_API_URL;
+  if (!url && typeof window !== 'undefined') {
+    throw new Error(
+      'NEXT_PUBLIC_SPINE_API_URL is not set. Public collection endpoints cannot function without it.',
+    );
+  }
+  return url || '';
+})();
```

**Recommendation**
- Keep this stash fragment. It is a small but meaningful runtime safety improvement.

### 4. `spine_api/server.py` — pipeline watchdog

**Why it is useful**
- Introduces a `PIPELINE_TIMEOUT_SECONDS` watchdog for `_execute_spine_pipeline`.
- Fails the run cleanly with `PipelineTimeout` when the pipeline hangs past the configured timeout.
- Cancels the timer in the `finally` block to avoid stray watchdog timers.

**Selected diff**
```diff
+    watchdog_timeout = int(os.environ.get("PIPELINE_TIMEOUT_SECONDS", "180"))
+
+    def _pipeline_watchdog() -> None:
+        """Fires if the pipeline does not complete within watchdog_timeout seconds."""
+        RunLedger.fail(
+            run_id,
+            error_type="PipelineTimeout",
+            error_message=f"Pipeline did not complete within {watchdog_timeout}s",
+        )
+
+    timer = threading.Timer(watchdog_timeout, _pipeline_watchdog)
+    timer.daemon = True
@@
+        timer.start()
@@
-        # Reset strict mode after every request to prevent state leaking to the next
+        timer.cancel()
         set_strict_mode(False)
```

**Recommendation**
- Keep this stash fragment if the team wants explicit runtime hardening for pipeline execution. It is a useful safety mechanism.

### 5. `spine_api/server.py` — `decision_output` compatibility

**Why it is useful**
- Makes suitability flag extraction tolerant of both `decision` and `decision_output` storage formats.
- Avoids breaking trips persisted with older or alternate field names.

**Selected diff**
```diff
-        decision_output = trip.get("decision")
+        # Get the decision output — stored as "decision" in DB, "decision_output" in file format
+        decision_output = trip.get("decision") or trip.get("decision_output")
```

**Recommendation**
- Keep this stash fragment. It is a compatibility hardening with a very low risk profile.

## Ambiguous or not recommended stash fragments

### `spine_api/server.py` — `RUNNING_TESTS` startup/shutdown bypass removal

**Why it is ambiguous**
- The stash removes the test-only bypass that prevented background agent startup during tests.
- Current `master` behavior preserves test isolation and avoids creating a TripStore SQL bridge during test runs.

**Recommendation**
- Treat this change as a behavior change, not a pure bug fix. Do not adopt it without a dedicated test impact review.

### `frontend/src/components/inbox/TripCard.tsx`

**Why it is ambiguous**
- The stash removes touch detection and the `QuickActions` assignment dropdown.
- This simplifies the component, but also removes richer per-card assignment actions.

**Recommendation**
- Do not automatically adopt this unless the product decision is to simplify inbox cards and remove quick assign interactions.

### Docs / tooling deletions

The stash deletes many docs and support tools, including `Docs/SAFE_STASH_RESET_RECOVERY_PROTOCOL_2026-05-05.md`, `tools/recovery_guard_report.py`, and several research/status docs.

**Recommendation**
- Do not adopt broad doc/tool deletions from the stash as part of a useful extract. They are not clearly better than current master and carry nontrivial information risk.

## Practical adoption guidance

- Apply the selected frontend diffs as targeted patches rather than importing the entire stash.
- Preserve current `master` behavior for test isolation and developer docs unless there is a strong reason to change them.
- Use this extract as a filter: keep the safety and compatibility hardenings, skip the broader runtime/test behavior churn and documentation pruning.
