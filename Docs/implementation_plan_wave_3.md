# Implementation Plan: A++ Hardening & Frontend Wave 3

This plan addresses the remaining architectural debt in the backend (path hacks) and executes the Wave 3 frontend transition (panel extraction and stage routing).

## User Review Required

> [!IMPORTANT]
> **Import Hardening**: Removing `sys.path.insert` from production code ensures architectural purity but requires the project root to be in the `PYTHONPATH` during execution (e.g., `PYTHONPATH=. python spine-api/server.py`).
> **Wave 3 Transition**: This moves the app to a "Routed Stage" architecture, allowing deep-linking into specific pipeline steps (Intake, Decision, etc.).

## Proposed Changes

### Phase 1: Backend "A++" Hardening (Import Boundary Cleanup)

We will remove manual `sys.path` manipulations from library modules and entry points.

#### [MODIFY] [hybrid_engine.py](file:///Users/pranay/Projects/travel_agency_agent/src/decision/hybrid_engine.py)
#### [MODIFY] [cache_key.py](file:///Users/pranay/Projects/travel_agency_agent/src/decision/cache_key.py)
#### [MODIFY] [decision/rules/*.py](file:///Users/pranay/Projects/travel_agency_agent/src/decision/rules/budget_feasibility.py) [and others]
#### [MODIFY] [server.py](file:///Users/pranay/Projects/travel_agency_agent/spine-api/server.py)

---

### Phase 2: Frontend Wave 3 (Panel Extraction & Stage Routing)

Migrating monolithic workbench tabs into atomic, reusable panels.

#### [NEW] [Panels Directory](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/)
- `IntakePanel.tsx`, `PacketPanel.tsx`, `DecisionPanel.tsx`, `StrategyPanel.tsx`, `SafetyPanel.tsx`.

#### [MODIFY] [Legacy Workbench](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/page.tsx)
- Refactor to use the new reusable Panels.

#### [MODIFY] [Stage Routes](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workspace/[tripId]/intake/page.tsx) [and others]
- Replace "Compatibility Redirects" with real functional pages.

## Verification Plan

### Automated Tests
- **Backend**: `pytest -q tests/test_agency_settings.py tests/test_run_state_unit.py tests/test_settings_behavioral.py`
- **Grep Check**: `grep -r "sys.path.insert" src/ spine-api/` should return zero hits in production code.

### Manual Verification
- Verify high-fidelity rendering of all 5 stages in the new routed workspace.
- Confirm "Process Trip" action parity with legacy workbench.
