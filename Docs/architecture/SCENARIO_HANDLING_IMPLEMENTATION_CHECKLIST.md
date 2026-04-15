# Scenario Handling Implementation Checklist

**Project:** Enhanced Scenario Handling for NB02 Decision Engine  
**Target:** 6-Week Implementation  
**Status:** Not Started  
**Last Updated:** 2026-04-15  

---

## 📋 Quick Reference

| Document | Purpose | Location |
|----------|---------|----------|
| Architecture Plan | High-level design | [`SCENARIO_HANDLING_ARCHITECTURE.md`](SCENARIO_HANDLING_ARCHITECTURE.md) |
| Technical Spec | Detailed API/interfaces | [`specs/SCENARIO_HANDLING_SPEC.md`](../specs/SCENARIO_HANDLING_SPEC.md) |
| ADR | Decision records | [`adr/ADR-001-SCENARIO-HANDLING-ARCHITECTURE.md`](adr/ADR-001-SCENARIO-HANDLING-ARCHITECTURE.md) |
| This Checklist | Implementation tracking | Here |

---

## Phase 1: Foundation (Week 1)

### 1.1 Backend - Structured Risk Data Model

- [ ] Create `src/intake/models/risk_models.py`
  - [ ] Define `StructuredRisk` dataclass
  - [ ] Define `RiskCategory` enum
  - [ ] Define `RiskSeverity` enum
  - [ ] Add backward compatibility methods

- [ ] Update `src/intake/decision.py`
  - [ ] Import new risk models
  - [ ] Add `structured_risks` field to `DecisionResult`
  - [ ] Maintain `risk_flags: List[str]` for backward compatibility
  - [ ] Add helper: `_convert_to_structured_risk()`
  - [ ] Add helper: `_risks_to_strings()`

- [ ] Add tests
  - [ ] `tests/test_structured_risks.py`
  - [ ] Test backward compatibility
  - [ ] Test serialization/deserialization

**Files to Create:**
- `src/intake/models/__init__.py` (if not exists)
- `src/intake/models/risk_models.py`
- `tests/test_structured_risks.py`

**Files to Modify:**
- `src/intake/decision.py` (add imports, update DecisionResult)

---

### 1.2 Frontend - TypeScript Type Definitions

- [ ] Create `frontend/src/types/scenario.ts`
  - [ ] `StructuredRisk` interface
  - [ ] `RiskSeverity` union type
  - [ ] `RiskCategory` union type
  - [ ] `RouteSegment` interface
  - [ ] `RouteAnalysis` interface
  - [ ] `SeasonalConditions` interface
  - [ ] `ActivityProfile` interface
  - [ ] `SuitabilityMatch` interface

- [ ] Update `frontend/src/types/spine.ts`
  - [ ] Import from scenario.ts
  - [ ] Extend `SpineRunResponse` with new fields (optional for backward compat)

- [ ] Update `frontend/src/stores/workbench.ts`
  - [ ] Add typed fields for scenario data
  - [ ] Add setters for route/weather/activity data

**Files to Create:**
- `frontend/src/types/scenario.ts`

**Files to Modify:**
- `frontend/src/types/spine.ts`
- `frontend/src/stores/workbench.ts`

---

### 1.3 API - Response Schema Updates

- [ ] Update `spine-api/server.py`
  - [ ] Add structured risk serialization
  - [ ] Include scenario analysis in response

- [ ] Update `frontend/src/app/api/spine/run/route.ts`
  - [ ] Handle new response fields
  - [ ] Pass scenario data to frontend

**Files to Modify:**
- `spine-api/server.py`
- `frontend/src/app/api/spine/run/route.ts`

---

## Phase 2: Route Analysis (Week 2-3)

### 2.1 Backend - Route Parser Module

- [ ] Create `src/intake/scenario/__init__.py`

- [ ] Create `src/intake/scenario/route_analysis.py`
  - [ ] `GeoLocation` dataclass
  - [ ] `RouteSegment` dataclass
  - [ ] `RouteAnalysis` dataclass
  - [ ] `RouteRiskAssessment` dataclass
  - [ ] `parse_itinerary_text()` function
  - [ ] `_extract_destinations()` helper
  - [ ] `_determine_transport_mode()` helper
  - [ ] `calculate_complexity_score()` function
  - [ ] `analyze_route_complexity()` function
  - [ ] `generate_route_risks()` function

- [ ] Create `src/intake/scenario/data/destinations.py`
  - [ ] Known destinations list
  - [ ] Airport codes mapping
  - [ ] Transport keywords

- [ ] Create `src/intake/scenario/utils/geo_utils.py`
  - [ ] Distance calculation (haversine)
  - [ ] Duration estimation

- [ ] Add tests
  - [ ] `tests/scenario/test_route_analysis.py`
  - [ ] `tests/scenario/fixtures/sample_itineraries.py`

**Files to Create:**
- `src/intake/scenario/__init__.py`
- `src/intake/scenario/route_analysis.py`
- `src/intake/scenario/data/__init__.py`
- `src/intake/scenario/data/destinations.py`
- `src/intake/scenario/utils/__init__.py`
- `src/intake/scenario/utils/geo_utils.py`
- `tests/scenario/__init__.py`
- `tests/scenario/test_route_analysis.py`
- `tests/scenario/fixtures/sample_itineraries.py`

---

### 2.2 Frontend - RouteVisualizer Component

- [ ] Create `frontend/src/components/scenario/RouteVisualizer/`

- [ ] Create `RouteVisualizer.tsx`
  - [ ] Props interface with RouteAnalysis
  - [ ] Timeline visualization
  - [ ] Segment cards
  - [ ] Transfer indicators
  - [ ] Complexity score badge
  - [ ] Expand/collapse detail view

- [ ] Create `RouteSegmentCard.tsx`
  - [ ] Origin → Destination display
  - [ ] Transport mode icon
  - [ ] Duration display
  - [ ] Risk indicators
  - [ ] Transfer time (if applicable)

- [ ] Create `ComplexityBadge.tsx`
  - [ ] Score display (0.0-1.0)
  - [ ] Color coding (green/yellow/red)
  - [ ] Tooltip with factors

- [ ] Create CSS modules
  - [ ] `RouteVisualizer.module.css`
  - [ ] Responsive layout
  - [ ] Animation for expand/collapse

- [ ] Add Storybook stories (if using Storybook)
  - [ ] Simple route (1 leg)
  - [ ] Complex route (4+ legs)
  - [ ] Route with risks

- [ ] Add tests
  - [ ] `RouteVisualizer.test.tsx`

**Files to Create:**
- `frontend/src/components/scenario/RouteVisualizer/index.ts`
- `frontend/src/components/scenario/RouteVisualizer/RouteVisualizer.tsx`
- `frontend/src/components/scenario/RouteVisualizer/RouteSegmentCard.tsx`
- `frontend/src/components/scenario/RouteVisualizer/ComplexityBadge.tsx`
- `frontend/src/components/scenario/RouteVisualizer/RouteVisualizer.module.css`
- `frontend/src/components/scenario/RouteVisualizer/RouteVisualizer.test.tsx`

---

### 2.3 Integration - Wire Route Analysis

- [ ] Update `src/intake/decision.py`
  - [ ] Import route analysis module
  - [ ] In `generate_risk_flags()`, add:
    ```python
    if packet.facts.get("itinerary_text"):
        route = parse_itinerary_text(packet.facts["itinerary_text"].value)
        route_assessment = analyze_route_complexity(route, packet)
        risks.extend(generate_route_risks(route_assessment))
        result.route_analysis = route
    ```

- [ ] Update `DecisionResult` instantiation
  - [ ] Pass route_analysis to constructor

- [ ] Add integration tests
  - [ ] Test with itinerary text input
  - [ ] Test complexity scoring
  - [ ] Test risk generation

**Files to Modify:**
- `src/intake/decision.py`
- `tests/test_decision_policy_conformance.py`

---

## Phase 3: Weather Risk (Week 3-4)

### 3.1 Backend - Weather Risk Module

- [ ] Create `src/intake/scenario/weather_risk.py`
  - [ ] `SeasonalConditions` dataclass
  - [ ] `WeatherRiskAssessment` dataclass
  - [ ] `SEASONAL_RISK_DB` dictionary
  - [ ] `assess_weather_risk()` function
  - [ ] `generate_weather_risks()` function
  - [ ] `_get_month_risk()` helper
  - [ ] `_aggregate_risks()` helper

- [ ] Create `src/intake/scenario/data/seasonal_data.py`
  - [ ] Populate with destination data:
    - [ ] Bali (12 months)
    - [ ] Thailand (12 months)
    - [ ] Maldives (12 months)
    - [ ] Sri Lanka (12 months)
    - [ ] Singapore (12 months)
    - [ ] Dubai (12 months)
    - [ ] Japan (12 months)
    - [ ] Europe destinations (12 months)
  - [ ] Add risk type classifications
  - [ ] Add recommendations

- [ ] Add tests
  - [ ] `tests/scenario/test_weather_risk.py`
  - [ ] Test each destination for each month
  - [ ] Test edge cases (date ranges spanning months)

**Files to Create:**
- `src/intake/scenario/weather_risk.py`
- `src/intake/scenario/data/seasonal_data.py`
- `tests/scenario/test_weather_risk.py`

---

### 3.2 Frontend - WeatherRiskPanel Component

- [ ] Create `frontend/src/components/scenario/WeatherRiskPanel/`

- [ ] Create `WeatherRiskPanel.tsx`
  - [ ] Props interface with WeatherRiskAssessment
  - [ ] Calendar view with risk overlay
  - [ ] Risk list view
  - [ ] Alternative dates suggestion
  - [ ] Packing checklist

- [ ] Create `MonthRiskIndicator.tsx`
  - [ ] Mini calendar month view
  - [ ] Color-coded risk level
  - [ ] Risk type tooltip

- [ ] Create `RiskDetailCard.tsx` (if not created in Phase 2)
  - [ ] Expandable risk details
  - [ ] Mitigation suggestions
  - [ ] Alternative recommendations

- [ ] Create CSS modules
  - [ ] `WeatherRiskPanel.module.css`

- [ ] Add tests
  - [ ] `WeatherRiskPanel.test.tsx`

**Files to Create:**
- `frontend/src/components/scenario/WeatherRiskPanel/index.ts`
- `frontend/src/components/scenario/WeatherRiskPanel/WeatherRiskPanel.tsx`
- `frontend/src/components/scenario/WeatherRiskPanel/MonthRiskIndicator.tsx`
- `frontend/src/components/scenario/WeatherRiskPanel/WeatherRiskPanel.module.css`
- `frontend/src/components/scenario/WeatherRiskPanel/WeatherRiskPanel.test.tsx`

---

### 3.3 Integration - Wire Weather Analysis

- [ ] Update `src/intake/decision.py`
  - [ ] Import weather risk module
  - [ ] In `generate_risk_flags()`, add:
    ```python
    if destinations and date_window:
        weather = assess_weather_risk(destinations, start_date, end_date)
        risks.extend(generate_weather_risks(weather))
        result.weather_assessment = weather
    ```

**Files to Modify:**
- `src/intake/decision.py`

---

## Phase 4: Activity Matching (Week 4-5)

### 4.1 Backend - Activity Matcher Module

- [ ] Create `src/intake/scenario/activity_matcher.py`
  - [ ] `ActivityProfile` dataclass
  - [ ] `SuitabilityMatch` dataclass
  - [ ] `PartyActivityAssessment` dataclass
  - [ ] `ACTIVITY_DB` dictionary
  - [ ] `match_activities_to_party()` function
  - [ ] `generate_activity_risks()` function
  - [ ] `_calculate_suitability_score()` helper
  - [ ] `_check_age_restrictions()` helper

- [ ] Create `src/intake/scenario/data/activities.py`
  - [ ] Define activity profiles:
    - [ ] Light trekking
    - [ ] Beach activities
    - [ ] Snorkeling
    - [ ] City walking tour
    - [ ] Wildlife safari
    - [ ] Water sports
    - [ ] Cultural tours
    - [ ] Spa/wellness
    - [ ] Adventure sports

- [ ] Add tests
  - [ ] `tests/scenario/test_activity_matcher.py`
  - [ ] Test elderly + high intensity
  - [ ] Test toddlers + age restrictions
  - [ ] Test mixed party scenarios

**Files to Create:**
- `src/intake/scenario/activity_matcher.py`
- `src/intake/scenario/data/activities.py`
- `tests/scenario/test_activity_matcher.py`

---

### 4.2 Frontend - ActivitySuitabilityGrid Component

- [ ] Create `frontend/src/components/scenario/ActivitySuitabilityGrid/`

- [ ] Create `ActivitySuitabilityGrid.tsx`
  - [ ] Props interface with activities and party composition
  - [ ] Grid layout (activities × party segments)
  - [ ] Suitability indicators (check/warning/block)
  - [ ] Split group recommendations

- [ ] Create `ActivityCard.tsx`
  - [ ] Activity name and type
  - [ ] Intensity badge
  - [ ] Age restriction indicators

- [ ] Create `SuitabilityIndicator.tsx`
  - [ ] Icon-based suitability display
  - [ ] Tooltip with concerns
  - [ ] Alternatives link

- [ ] Create CSS modules
  - [ ] `ActivitySuitabilityGrid.module.css`

- [ ] Add tests
  - [ ] `ActivitySuitabilityGrid.test.tsx`

**Files to Create:**
- `frontend/src/components/scenario/ActivitySuitabilityGrid/index.ts`
- `frontend/src/components/scenario/ActivitySuitabilityGrid/ActivitySuitabilityGrid.tsx`
- `frontend/src/components/scenario/ActivitySuitabilityGrid/ActivityCard.tsx`
- `frontend/src/components/scenario/ActivitySuitabilityGrid/SuitabilityIndicator.tsx`
- `frontend/src/components/scenario/ActivitySuitabilityGrid/ActivitySuitabilityGrid.module.css`
- `frontend/src/components/scenario/ActivitySuitabilityGrid/ActivitySuitabilityGrid.test.tsx`

---

### 4.3 Integration - Wire Activity Analysis

- [ ] Update `src/intake/decision.py`
  - [ ] Import activity matcher module
  - [ ] In `generate_risk_flags()`, add activity risk generation

**Files to Modify:**
- `src/intake/decision.py`

---

## Phase 5: Integration & UI Polish (Week 5-6)

### 5.1 Enhanced DecisionTab

- [ ] Update `frontend/src/app/workbench/DecisionTab.tsx`
  - [ ] Import new scenario components
  - [ ] Add RouteVisualizer section (conditional on data presence)
  - [ ] Replace risk_flags string list with RiskDetailCards
  - [ ] Add tabs or sections for:
    - [ ] Summary view
    - [ ] Route details
    - [ ] Risk details (structured)
  - [ ] Add "Show/Hide Scenario Analysis" toggle

- [ ] Update styles
  - [ ] Import scenario component styles
  - [ ] Ensure responsive layout

**Files to Modify:**
- `frontend/src/app/workbench/DecisionTab.tsx`

---

### 5.2 New ItineraryTab (Optional)

- [ ] Create `frontend/src/app/workbench/ItineraryTab.tsx`
  - [ ] Combined route + weather + activity view
  - [ ] Visual timeline with all risk overlays
  - [ ] Summary recommendations

- [ ] Update `frontend/src/app/workbench/page.tsx`
  - [ ] Add ItineraryTab to tab list
  - [ ] Import new tab component

**Files to Create:**
- `frontend/src/app/workbench/ItineraryTab.tsx`

**Files to Modify:**
- `frontend/src/app/workbench/page.tsx`

---

### 5.3 Testing & QA

- [ ] Integration tests
  - [ ] `tests/test_scenario_integration.py`
  - [ ] End-to-end test with full scenario

- [ ] Test scenarios
  - [ ] SE Asia multi-city with monsoon risk
  - [ ] European tour with elderly
  - [ ] Family trip with toddlers
  - [ ] Adventure trip with mixed abilities

- [ ] Frontend tests
  - [ ] Component rendering tests
  - [ ] User interaction tests
  - [ ] API integration tests

- [ ] Performance tests
  - [ ] Measure latency added
  - [ ] Test with large itineraries
  - [ ] Verify no memory leaks

**Files to Create:**
- `tests/test_scenario_integration.py`

---

### 5.4 Documentation

- [ ] Update code documentation
  - [ ] Docstrings for all new functions
  - [ ] Type hints throughout
  - [ ] README in `src/intake/scenario/`

- [ ] Update API documentation
  - [ ] Document new response fields
  - [ ] Example requests/responses

- [ ] Update user documentation
  - [ ] Feature guide for scenario analysis
  - [ ] FAQ for common risk flags

**Files to Create/Modify:**
- `src/intake/scenario/README.md`
- `docs/api/scenario-analysis.md`
- `docs/user/scenario-risks.md`

---

## Phase 6: Deployment Preparation

### 6.1 Feature Flags

- [ ] Add feature flag configuration
  - [ ] `SCENARIO_ANALYSIS_ENABLED` env var
  - [ ] Per-module flags (route/weather/activity)

- [ ] Implement flag checks
  - [ ] In decision.py
  - [ ] In frontend (show/hide UI)

---

### 6.2 Monitoring & Observability

- [ ] Add metrics
  - [ ] Scenario detection count by category
  - [ ] Analysis latency (P50, P95, P99)
  - [ ] Risk flag conversion rate

- [ ] Add logging
  - [ ] Debug logs for route parsing
  - [ ] Warning logs for parsing failures
  - [ ] Info logs for risk generation

- [ ] Add alerting
  - [ ] High error rate in scenario analysis
  - [ ] Unusual latency spikes

---

### 6.3 Rollback Plan

- [ ] Document rollback procedure
  - [ ] Disable feature flags
  - [ ] Revert to string-only risk flags
  - [ ] Database compatibility check

- [ ] Create rollback scripts
  - [ ] Quick disable script
  - [ ] Data cleanup (if needed)

---

## ✅ Pre-Launch Checklist

### Code Quality
- [ ] All new code has tests (>80% coverage)
- [ ] Type checking passes (mypy, TypeScript)
- [ ] Linting passes (flake8, pylint, ESLint)
- [ ] No security vulnerabilities (bandit, npm audit)
- [ ] Code review completed

### Performance
- [ ] Latency budget met (<500ms additional)
- [ ] Memory usage acceptable
- [ ] Load tested with realistic traffic

### Documentation
- [ ] Architecture document updated
- [ ] API docs updated
- [ ] User docs updated
- [ ] Runbooks created

### Operations
- [ ] Feature flags configured
- [ ] Monitoring dashboards ready
- [ ] Alerts configured
- [ ] Rollback plan tested

### Sign-offs
- [ ] Backend team lead
- [ ] Frontend team lead
- [ ] QA team
- [ ] Product owner

---

## 📊 Progress Tracking

| Phase | Status | % Complete | Blocked By |
|-------|--------|------------|------------|
| Phase 1: Foundation | 🔴 Not Started | 0% | - |
| Phase 2: Route Analysis | 🔴 Not Started | 0% | Phase 1 |
| Phase 3: Weather Risk | 🔴 Not Started | 0% | Phase 1 |
| Phase 4: Activity Matching | 🔴 Not Started | 0% | Phase 1 |
| Phase 5: Integration | 🔴 Not Started | 0% | Phases 2-4 |
| Phase 6: Deployment Prep | 🔴 Not Started | 0% | Phase 5 |

**Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- ⚠️ Blocked

---

## 🐛 Known Issues / Blockers

| Issue | Description | Impact | Owner | Target Resolution |
|-------|-------------|--------|-------|-------------------|
| None | - | - | - | - |

---

## 📝 Notes & Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-15 | Created checklist | Initial planning complete |

---

*Maintained by: Implementation Team*  
*Review Schedule: Weekly*  
*Next Review: TBD*
