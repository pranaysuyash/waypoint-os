# Implementation Directive: P0 System Integrity & Data Pipeline Unification

**To**: Implementation Agent
**Objective**: Replace all fragmented, screen-specific mock data and client-side calculations with a **Canonical Backend Pipeline**.

## 1. Core Mandate
Stop all screen-specific data mocking and client-side arithmetic. Every dashboard count, inbox list, and analytics chart must be derived from a **Single Source of Truth (SSOT)**: a unified backend aggregator. If the data is inconsistent, the build fails.

## 2. Technical Execution

### A. Backend: The Truth Pipeline (Canonical Aggregator)
- **Delete Fragmented Mocks**: Remove all page-specific mock generators (e.g., `getMockInbox`, `getMockAnalytics`).
- **Implement `src/services/dashboard_aggregator.py`**:
    - Build a single, high-performance query that retrieves all trip data and aggregates metrics.
    - **Canonical Schema**: Return a unified object: `{"canonical_total": N, "stages": { ... }, "sla_breached": N, "orphans": [...]}`.
- **Expose Endpoint**: Update `spine-api/server.py` to expose `GET /api/system/unified-state`. All components (Inbox, Overview, Analytics) MUST call this endpoint.
- **Orphan Audit**: The aggregator must explicitly identify "orphans" (trips in DB with no valid stage) and expose them in the `orphans` array for recovery triage.

### B. Frontend: Thin Client Projection
- **Centralize Hooks**: Implement `useUnifiedState()` hook. This hook fetches from `/api/system/unified-state` and serves as the **only** source for all dashboard views.
- **Remove Logic**: Strip all client-side trip counting/math (e.g., `reduce`, `filter`, `length`) from `page.tsx` and component logic.
- **View Projection**: Components (Inbox, Overview, Analytics) act as "Thin Projections." They receive pre-calculated stats from the hook and display them. **They are forbidden from performing arithmetic.**

## 3. Strict Verification & Regression Guardrails
- **The Reconciliation Test (`tests/test_integrity.py`)**: 
    - Assert: `canonical_total === Object.values(stages).reduce((a, b) => a + b, 0)`.
    - This test MUST execute against the `data/fixtures/scenario_alpha.json` baseline.
- **Build-Fail Assert**: If stats derived from the pipeline are inconsistent, the integration test MUST fail. We prioritize system integrity over speed.
- **Atomic Rollout**: Transition from local mocks to the `UnifiedState` pipeline atomically per page. Verify Inbox consistency before touching Overview.

## 4. Operational Requirements
- **No Manual Sums**: Frontend components are prohibited from calculating totals.
- **Fail Loudly**: If data integrity is compromised (mismatch detected), the UI must render an "INTEGRITY ERROR" banner. Do not display wrong numbers.
- **No Regressions**: Ensure `TimelinePanel` and `SuitabilityAudit` remain functional and integrated with the new `UnifiedState` response.

---

**Execution Directive**: Proceed with backend aggregation first. Do not touch the frontend until the `unified-state` endpoint returns mathematically consistent data across all fixture scenarios. Report the audit result of your integration tests before finalizing.
