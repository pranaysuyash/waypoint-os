# Scenario Handling Spec Coverage Status — 2026-05-05

## Scope Checked

- Spec: `specs/SCENARIO_HANDLING_SPEC.md`
- Code: `src/intake/decision.py`, `src/decision/rules/*`, `src/suitability/*`, `src/agents/runtime.py`, `src/public_checker/live_checks.py`
- Tests: `tests/test_agent_runtime.py` plus existing suitability/decision/runtime suites referenced in-repo

## Goal (Current Session)

Validate whether the spec claim is operationally covered:

- Monsoon/seasonality hazard detection with actionable suggestions
- Elderly travelers on 4-flight style transfer-heavy itineraries
- Toddlers on extreme activities/treks

Then implement gaps in the canonical runtime path (no parallel duplicate subsystem), verify with tests, and document handoff-ready status.

## Coverage Verdict

### 1) Monsoon / seasonality risk detection

Status: **Covered (agentic + checker layers), improved with explicit seasonal hints**

- `DestinationIntelligenceAgent` + `WeatherPivotAgent` already provide freshness-aware weather risk and pivot suggestions (`src/agents/runtime.py`).
- Public checker also computes climate/seasonal risk and suggestions from Open-Meteo (`src/public_checker/live_checks.py`), including tropical-storm season heuristics.
- Public checker now includes destination seasonal hint typing for known destinations (e.g., Bali monsoon windows) with suggested better-month alternatives.

Limit:
- Not yet a dedicated month-by-destination monsoon knowledge base with full `SeasonalConditions` model from spec.

### 2) Elderly + 4-flight / transfer fatigue

Status: **Covered in canonical feasibility agent (extended)**

Implemented in this session:

- `ConstraintFeasibilityAgent` now extracts route summary and party composition.
- Adds hard blocker when elderly context and `flight_legs >= 4`.
- Adds soft routing constraint for elderly when route complexity is elevated (`flight_legs >= 3` or transfer-heavy itinerary items).
- Adds tight-connection risk checks (layover/connection time thresholds) and escalates for vulnerable traveler composition.
- Adds multi-country hop density hard blocker for unrealistic same-day/multi-hop routing patterns.

Files:
- `src/agents/runtime.py`

### 3) Toddlers + extreme trek/activity mismatch

Status: **Covered in canonical feasibility agent (extended)**

Implemented in this session:

- `ConstraintFeasibilityAgent` now inspects itinerary/activity text for extreme-intensity terms.
- Adds hard blocker when toddler context is present and extreme activity signatures are detected.
- Adds elderly water-intensity activity review checks (e.g., snorkeling/scuba patterns) as explicit suitability constraints.

### 4) In-progress and pre-departure continuous risk updates

Status: **Covered for feasibility refresh cadence**

Implemented in this session:

- `ConstraintFeasibilityAgent` stage coverage now includes `ticketed`, `pre_departure`, `in_progress`, `traveling`.
- Existing feasibility snapshots are periodically refreshed for active stages based on configurable refresh hours.
- Safety-alert and flight-disruption snapshots are now consumed as first-class feasibility constraints.
- Cohort inference now distinguishes explicit elderly vs ambiguous parent cohorts, detects infant presence, and avoids over-triggering elderly hard risk when ages indicate younger parents.
- Public checker now includes basic regional advisory hints (non-weather hazard surface) for known high-risk destinations.
- Regional disruption heuristics now include conflict-zone signals and Europe summer high-friction hub pressure checks in feasibility routing/safety constraints.
- Added stage-aware risk action policy output (`risk_action_plan`) so pre-trip and in-trip handling diverge deterministically by severity.

Files:
- `src/agents/runtime.py`

## Code Changes This Session

1. Enhanced `ConstraintFeasibilityAgent` context extraction:
   - party composition extraction from facts
   - route summary extraction (`flight_legs`, transfer-like items, activity count)
   - itinerary activity title extraction
   - expanded `facts_marker` so re-assessment triggers when these inputs change

2. Added deterministic risk logic in `_assess(...)`:
   - elderly route-fatigue hard/soft constraints
   - toddler extreme-activity hard constraints
   - tight-connection hard constraints for vulnerable cohorts
   - multi-country hop density blockers
   - elderly water-intensity suitability constraints
   - safety and flight-disruption feasibility constraints
   - periodic refresh behavior for in-progress stages

3. Added/updated runtime tests:
   - New test: `test_constraint_feasibility_agent_flags_route_fatigue_and_toddler_extreme_activity`
   - Updated marker expectation in `test_constraint_feasibility_agent_skips_when_current_assessment_exists`
   - Added active-trip safety/flight disruption test
   - Added active-stage periodic refresh scan test

4. Added canonical route-analysis module:
   - `src/intake/route_analysis.py`
   - `tests/test_route_analysis.py`
   - Added `parse_itinerary_text(...)` fallback so route risk detection still works when structured flight/activity fields are missing.

5. Added shared structured-risk contract helpers:
   - `src/agents/risk_contracts.py`
   - Feasibility assessment now emits `structured_risks` derived from hard/soft constraints.
   - Public checker live weather signals now also emit `structured_risks` with weather taxonomy context.

## Verification

Command:

`pytest -q tests/test_agent_runtime.py tests/test_route_analysis.py tests/test_public_checker_live_checks.py tests/test_risk_contracts.py tests/test_regional_risk.py tests/test_risk_action_policy.py`

Result:

- `49 passed`

## What Is Still Pending vs `SCENARIO_HANDLING_SPEC.md`

These remain partially/unimplemented relative to the full spec document model:

1. **Formal RouteAnalysis model pipeline**
   - No dedicated `RouteSegment/RouteAnalysis/RouteRiskAssessment` dataclass module yet.
   - Current implementation uses runtime heuristics from existing trip fields.

2. **StructuredRisk full metadata contract parity**
   - Convergence started via `src/agents/risk_contracts.py` and emitted `structured_risks` in runtime/public checker.
   - Full end-to-end contract unification across NB02 decision output, suitability profile, frontend typed contracts, and API schemas is still pending.

3. **Formal weather risk taxonomy parity**
   - Current weather checks are operational and live-evidence based.
   - Full spec taxonomy (`monsoon`, `cyclone_hurricane`, `flooding`, etc.) with explicit typed outputs is not fully implemented.

4. **Dedicated itinerary text parser for route complexity**
   - Initial standalone parser now exists in `src/intake/route_analysis.py` and is wired as a fallback in feasibility route analysis.
   - Full typed `RouteSegment` extraction and timeline-level parsing is still pending.

## Recommended Next Implementation Stages (Canonical Path)

1. Add `src/intake/route_analysis.py` with typed `RouteAnalysis` and parser entrypoint used by `ConstraintFeasibilityAgent`.
2. Add a normalized weather risk taxonomy mapper so weather outputs emit consistent risk-type enums.
3. Unify risk structures into one canonical `StructuredRisk` contract used by:
   - NB02 decision risk flags
   - suitability flags
   - runtime feasibility/proposal/booking blocking risk packets
4. Add regression fixtures for:
   - monsoon-season destination swap suggestion
   - elderly 4-flight + short trip duration
   - toddler + trek/high-altitude activity

## Handoff Note

This session implemented the direct high-value scenario gap in the existing runtime feasibility agent (not a parallel system), verified test stability, and documented remaining work to reach full spec-level parity.

## Linked Exploration Track

For broader low-cost real-time tool-calling expansion (TinyFish + cost-effective live provider strategy), see:

- `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md`
