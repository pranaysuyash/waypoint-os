# Scenario Master Atlas — 2026-05-05

## Purpose

This is the canonical handoff map for scenario coverage across:

- implemented scenarios,
- currently-planned scenarios,
- and not-yet-explored scenarios.

It is structured so any agent can start from any section without re-auditing the whole repo.

## Canonical Paths (Do Not Fork)

- Runtime risk checks: `src/agents/runtime.py` (`ConstraintFeasibilityAgent` + related agents)
- Live/public weather wedge: `src/public_checker/live_checks.py`
- Shared risk contracts: `src/agents/risk_contracts.py`
- Route heuristics and parsing: `src/intake/route_analysis.py`
- Regional disruption heuristics: `src/intake/regional_risk.py`
- Risk-action stage policy: `src/intake/risk_action_policy.py`
- Scenario policy/config: `src/intake/scenario_policy.py`

## Verified Baseline

Latest focused verification command:

`pytest -q tests/test_agent_runtime.py tests/test_route_analysis.py tests/test_public_checker_live_checks.py tests/test_risk_contracts.py tests/test_regional_risk.py tests/test_risk_action_policy.py`

Latest result:

- `49 passed`

---

## A) Implemented Scenarios (Live in Code)

### A1. Weather / Seasonality Hazards

Covered:
- destination weather signals and pivots (`DestinationIntelligenceAgent`, `WeatherPivotAgent`)
- seasonal hint windows for known destinations in public checker (e.g., Bali monsoon)
- weather `structured_risks` emitted in public checker output

Primary files:
- `src/agents/runtime.py`
- `src/public_checker/live_checks.py`

Primary tests:
- `tests/test_agent_runtime.py`
- `tests/test_public_checker_live_checks.py`

---

### A2. Elderly + Multi-Leg Route Fatigue

Covered:
- hard/soft route fatigue checks by leg count and transfer density
- tight-connection risk escalation for vulnerable composition
- stress-hub-aware tight-connection threshold adjustment

Primary files:
- `src/agents/runtime.py`
- `src/intake/route_analysis.py`
- `src/intake/scenario_policy.py`

Primary tests:
- `tests/test_agent_runtime.py`
- `tests/test_route_analysis.py`

---

### A3. Toddler / Infant Activity-Pacing Mismatch

Covered:
- toddler + extreme activity hard block
- infant pacing sensitivity soft constraints
- elderly water-intensity activity soft constraints

Primary files:
- `src/agents/runtime.py`
- `src/intake/scenario_policy.py`

Primary tests:
- `tests/test_agent_runtime.py`

---

### A4. Parent/Age Ambiguity Handling

Covered:
- no automatic “parents => elderly” assumption
- explicit distinction:
  - ambiguous parents (soft review),
  - older-adult cohort (soft caution),
  - elderly/grandparents (elderly risk path)

Primary files:
- `src/agents/runtime.py`

Primary tests:
- `tests/test_agent_runtime.py`:
  - parent-not-elderly case
  - grandparents as elderly case

---

### A5. Regional Security / Disruption Pressure

Covered:
- conflict-zone high-risk signal
- Europe summer high-friction hub disruption pressure
- multi-leg + hub compound pressure
- public checker regional advisory hints

Primary files:
- `src/intake/regional_risk.py`
- `src/agents/runtime.py`
- `src/public_checker/live_checks.py`

Primary tests:
- `tests/test_regional_risk.py`
- `tests/test_agent_runtime.py`
- `tests/test_public_checker_live_checks.py`

---

### A6. In-Progress / Pre-Departure Continuous Updates

Covered:
- active stages include `ticketed`, `pre_departure`, `in_progress`, `traveling`
- periodic refresh logic with stage-aware cadence
- safety and flight snapshots consumed as feasibility constraints

Primary files:
- `src/agents/runtime.py`
- `src/intake/scenario_policy.py`

Primary tests:
- `tests/test_agent_runtime.py`

---

### A7. Stage-Aware Risk Action Policy

Covered:
- `risk_action_plan` emitted in feasibility output
- distinct behavior pre-commit vs in-trip incident mode

Primary files:
- `src/intake/risk_action_policy.py`
- `src/agents/runtime.py`

Primary tests:
- `tests/test_risk_action_policy.py`
- `tests/test_agent_runtime.py`

---

## B) Planned Next Scenarios (Partially Modeled, Not Complete)

### B1. Typed Route Segments (Spec-Parity Path)

Goal:
- move from aggregate route heuristics to typed `RouteSegment` extraction with per-segment transfer risk and timeline semantics.

Current state:
- aggregate parser exists (`parse_itinerary_text`) but no full segment graph yet.

Implementation slices:
1. Add `RouteSegment`-like internal model in `src/intake/route_analysis.py`
2. Parse sequence-level segments from structured + text
3. Emit segment-level risk details into feasibility `structured_risks`

---

### B2. Full Weather Taxonomy Normalization

Goal:
- normalize risk types to canonical enums (`monsoon`, `cyclone_hurricane`, `flooding`, `extreme_heat`, etc.)
across runtime + public checker.

Current state:
- partial taxonomy exists; not complete/parity.

Implementation slices:
1. Add taxonomy mapper module (new `src/intake/weather_taxonomy.py`)
2. Map climate/current signals to canonical types
3. Ensure `structured_risks.details.risk_type` always canonical

---

### B3. Unified Structured Risk Contract End-to-End

Goal:
- one risk contract shape across:
  - runtime feasibility/proposal/booking,
  - NB02 decision payload,
  - suitability outputs,
  - frontend typed surfaces.

Current state:
- convergence started (`risk_contracts.py`) but not fully unified.

Implementation slices:
1. Align backend API payload shape
2. Update frontend types (`frontend/src/types/spine.ts`)
3. Add schema/contract tests for compatibility

---

### B4. Regular In-Trip Auto-Recheck Orchestration

Goal:
- predictable background risk refresh during active travel windows.

Current state:
- periodic refresh logic exists in feasibility scan but orchestration cadence/persistence can be made explicit.

Implementation slices:
1. Add explicit “next due” timestamp in feasibility payload
2. Add metrics counters for stale/refresh outcomes
3. Expose in PacketPanel/ops UI

---

## C) Not-Yet-Explored Scenario Buckets

These are not implemented yet but are high-value from first principles.

### C1. Transit Visa Trap Scenarios
- multi-country route where connection airport requires transit visa for some passports
- dynamic policy drift close to departure

Why:
- high cancellation and disruption risk

---

### C2. Medical Capability Mismatch
- destination/itinerary intensity incompatible with declared health limitations
- medicine cold-chain / oxygen / dialysis / mobility equipment logistics

Why:
- severe safety and liability exposure

---

### C3. Family Split-Itinerary Viability
- one cohort can do high-intensity activities while elderly/toddlers cannot
- enforce split-plan recommendations with synchronized transfer windows

Why:
- common in family bookings; reduces dissatisfaction/refund risk

---

### C4. Strike/ATC/Seasonal Flight Disruption Patterns
- airport or carrier-level recurring disruption windows
- suggest route alternatives at proposal time

Why:
- strong operational differentiation and trust signal

---

### C5. Extreme Heat/Humidity Physiological Risk Profiles
- combine cohort + weather + activity timing to block unsafe daytime plans

Why:
- catches silent hazards junior agents miss

---

### C6. Event/Crowd Surge Risk
- religious festivals, sporting events, trade fairs causing transport/hotel stress

Why:
- major source of hidden cost and itinerary fragility

---

## D) Tooling / Data Dependency Matrix

### Already in use
- Open-Meteo weather/climate
- runtime live tool abstractions (`src/agents/live_tools.py`)

### Exploration-ready
- TinyFish and low-cost live search/fetch track:
  - `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md`
  - `Docs/status/LIVE_INTEL_EXECUTION_CHECKLIST_2026-05-05.md`

---

## E) Agent Pickup Protocol (Fast Start)

If you are a new agent picking this up:

1. Read:
   - `Docs/status/SCENARIO_HANDLING_SPEC_COVERAGE_STATUS_2026-05-05.md`
   - this file
2. Run verification:
   - `pytest -q tests/test_agent_runtime.py tests/test_route_analysis.py tests/test_public_checker_live_checks.py tests/test_risk_contracts.py tests/test_regional_risk.py tests/test_risk_action_policy.py`
3. Choose one unfinished bucket from section B or C.
4. Implement in canonical modules only (no parallel route/path).
5. Add focused tests and update this atlas + coverage status doc.

---

## F) Business Value Mapping

### Error Reduction
- catches weather/route/activity/regional risks before they become cancellations/refunds.

### Premium Tier Justification
- risk intelligence + dynamic updates supports higher pricing tiers vs plain CRM.

### Public Wedge Conversion
- itinerary checker hazard surfacing can drive lead capture and paid conversion.

### Junior Agent Enablement
- systemized safety/operational heuristics reduce tribal-knowledge dependency.

---

## G) Open Questions (For Next Agent Decisions)

1. Should conflict-zone destination presence always hard-block, or can agency policy downgrade in special workflows?
2. What is the canonical source of truth for airport hub risk lists (static config vs external feed)?
3. Should in-progress incident-response actions trigger specific workflow entities (tickets/tasks) in DB?
4. Where should full structured risk schema live for backend/frontend contract generation?

