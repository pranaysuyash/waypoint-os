# System Integrity & Data Unification Plan

**Date**: Wednesday, April 22, 2026
**Status**: Critical / Immediate
**Goal**: Eliminate data discrepancies across the cockpit by mandating a Single Source of Truth (SSOT).

---

## 1. The Discrepancy Registry (Known Gaps)
- **Inbox vs. Overview**: Overview shows 1074 pending, Inbox shows 20 total. Gap: 1054.
- **Trip Status Breakdown**: Stages don't add up to the total trip count.
- **Orphan States**: Trips exist in backend/analytics but are not "triaged" into the Inbox.

## 2. Immediate Directives (Tasks)

| Task ID | Action Item | Priority | Owner |
| :--- | :--- | :--- | :--- |
| **INT-01** | **Create Scenario Manager**: Create a unified `ScenarioProvider` that feeds all UI components. Delete all page-specific `getMock*` functions. | P0 | Frontend Agent |
| **INT-02** | **Audit Fixture File**: Map `data/fixtures/scenario_alpha.json` to be the SSOT. All stats must be calculated from this array at runtime. | P0 | Backend Agent |
| **INT-03** | **Lifecycle Reconciliation**: Implement a check: `Sum(Inbox) == Sum(Overview) == Sum(Analytics)`. If false, trigger a UI "Data Integrity Alert." | P1 | Frontend Agent |
| **INT-04** | **Orphan Trip Scan**: Expose an endpoint `GET /api/system/audit/orphans` to identify trips in the DB that don't match any active pipeline stage. | P1 | Backend Agent |

---

## 3. Implementation Guardrails
- **No Manual Sums**: Never calculate dashboard counts on the frontend. Everything must be `deriveState(scenario_data)`.
- **Atomic Seeding**: When a test scenario is loaded, it must seed the `store` globally.
- **Fail Loudly**: If UI counts don't match the source fixture, render an "INTEGRITY ERROR" banner. Do not show wrong numbers.

---

## 4. Verification Protocol
1. **Fixture-Driven Verification**: Load `scenario_alpha`. The Inbox total, Overview "Pending" count, and Analytics "Total Inquiries" must match exactly.
2. **Orphan Audit**: Ensure no trip ID appears in the Overview count that is not present in the Inbox search results.
