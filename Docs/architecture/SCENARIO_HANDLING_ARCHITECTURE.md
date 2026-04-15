# Scenario Handling Architecture Plan

**Date:** 2026-04-15  
**Status:** Draft - Pending Review  
**Related:** NB02 Decision Engine, Frontend Workbench, Risk Assessment

---

## 1. Current State Analysis

### 1.1 Existing Backend Components

Based on code review of [`src/intake/decision.py`](../../src/intake/decision.py), the following scenario handling logic exists:

#### Budget Feasibility (`check_budget_feasibility`, lines 371-436)
- **Location:** `src/intake/decision.py:371-436`
- **Table:** `BUDGET_FEASIBILITY_TABLE` (lines 317-347)
- **Functionality:** Compares `budget_min` against destination-specific minimum costs per person
- **Returns:** `feasible` | `tight` | `infeasible` | `unknown`
- **Coverage:** 24 destinations with heuristic costs

#### Risk Flag Generation (`generate_risk_flags`, lines 459-595)
Current risk detection includes:

| Risk Flag | Detection Logic | Line Reference |
|-----------|----------------|----------------|
| `elderly_mobility_risk` | Elderly travelers + risky destinations (Maldives, Andaman, Bhutan, Nepal) | lines 477-486 |
| `toddler_pacing_risk` | Children <4 years + destination | lines 487-496 |
| `visa_not_applied` | Visa required but not applied (booking stage) | lines 512-518 |
| `visa_timeline_risk` | High urgency + visa required | lines 519-525 |
| `document_risk` | Passport expired/expiring soon | lines 504-511 |
| `margin_risk` | Budget infeasible gap calculation | lines 528-536 |
| `coordination_risk` | Multi-party budget spread >30% | lines 539-557 |
| `traveler_safe_leakage_risk` | Internal data present in output | lines 561-593 |

### 1.2 Existing Frontend Components

#### DecisionTab (`frontend/src/app/workbench/DecisionTab.tsx`)
- **Location:** [`frontend/src/app/workbench/DecisionTab.tsx`](../../frontend/src/app/workbench/DecisionTab.tsx)
- **Capabilities:**
  - Displays `decision_state` with color-coded badges (lines 8-23)
  - Lists `hard_blockers`, `soft_blockers`, `contradictions` (lines 141-189)
  - Shows `risk_flags` as string array (lines 192-206)
  - Displays `feasibility` status from rationale (lines 96-97)
  - Renders `follow_up_questions` (lines 209-226)

#### SafetyTab (`frontend/src/app/workbench/SafetyTab.tsx`)
- **Location:** [`frontend/src/app/workbench/SafetyTab.tsx`](../../frontend/src/app/workbench/SafetyTab.tsx)
- **Capabilities:**
  - Leakage detection results (lines 60-83)
  - Traveler-safe vs Internal bundle split view (lines 112-188)
  - Assertion results display (lines 160-184)

#### StrategyTab (`frontend/src/app/workbench/StrategyTab.tsx`)
- **Location:** [`frontend/src/app/workbench/StrategyTab.tsx`](../../frontend/src/app/workbench/StrategyTab.tsx)
- **Capabilities:**
  - Session goals and priority sequences (lines 51-76)
  - Risk flags from strategy output (line 11)
  - Internal vs Traveler-safe bundle comparison (lines 111-188)

### 1.3 Data Types

**SpineRunRequest** ([`frontend/src/types/spine.ts`](../../frontend/src/types/spine.ts)):
```typescript
interface SpineRunRequest {
  raw_note?: string | null;
  owner_note?: string | null;
  structured_json?: Record<string, unknown> | null;
  itinerary_text?: string | null;  // ← For route analysis
  stage: SpineStage;
  operating_mode: OperatingMode;
  strict_leakage: boolean;
  scenario_id?: string | null;
}
```

---

## 2. Gap Analysis

### 2.1 Missing Scenario Detection (Backend)

| Scenario Type | Status | Impact | Priority |
|---------------|--------|--------|----------|
| **Weather/Season Risk** | ❌ Not Implemented | High for certain destinations | P1 |
| **Multi-leg Transfer Fatigue** | ❌ Not Implemented | Medium for complex itineraries | P1 |
| **Route Complexity Scoring** | ❌ Not Implemented | High for multi-city trips | P1 |
| **Activity Suitability Matching** | ⚠️ Partial (regex only) | Medium for adventure trips | P2 |
| **Multi-country Visa Complexity** | ❌ Not Implemented | High for SE Asia/Europe tours | P2 |
| **Timezone/Flight Duration Stress** | ❌ Not Implemented | Medium for long-haul | P3 |
| **Accommodation Transfer Burden** | ❌ Not Implemented | Low - nice to have | P3 |

### 2.2 Missing UI Components (Frontend)

| Component | Status | Purpose | Priority |
|-----------|--------|---------|----------|
| Route Visualizer | ❌ Not Implemented | Show multi-leg journey map | P1 |
| Risk Detail Cards | ❌ Not Implemented | Expandable risk explanations | P1 |
| Activity Suitability Panel | ❌ Not Implemented | Match activities to travelers | P2 |
| Weather/Season Indicator | ❌ Not Implemented | Show seasonal risk warnings | P2 |
| Transfer Fatigue Calculator | ❌ Not Implemented | Visual transfer complexity score | P2 |

### 2.3 Architectural Debt

1. **Risk Flags are String-Only:** Current `risk_flags: string[]` format lacks structured metadata
2. **No Itinerary Parser:** `itinerary_text` exists but has no structured parsing logic
3. **No Route Data Model:** Missing canonical representation for multi-stop itineraries
4. **Static Destination Table:** `BUDGET_FEASIBILITY_TABLE` is hardcoded, not data-driven

---

## 3. Proposed Architecture

### 3.1 Backend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scenario Analysis Layer                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Route Parser │  │ Weather Risk │  │ Activity     │       │
│  │  (New)       │  │  (New)       │  │ Matcher      │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                         ▼                                   │
│         ┌───────────────────────────────┐                  │
│         │   Structured Risk Generator   │                  │
│         │   (Enhances existing          │                  │
│         │    generate_risk_flags)       │                  │
│         └───────────────┬───────────────┘                  │
│                         │                                   │
│         ┌───────────────▼───────────────┐                  │
│         │     RiskEnrichmentResult      │                  │
│         │  (Typed risk with metadata)   │                  │
│         └───────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

#### 3.1.1 New Modules

**A. Route Parser Module (`src/intake/route_analysis.py`)**
```python
@dataclass
class RouteSegment:
    origin: str
    destination: str
    transport_mode: Literal["flight", "train", "ferry", "car"]
    estimated_duration_hours: float
    transfer_wait_hours: Optional[float]

@dataclass
class RouteAnalysis:
    segments: List[RouteSegment]
    total_legs: int
    total_travel_time_hours: float
    transfer_count: int
    complexity_score: float  # 0.0-1.0
```

**B. Weather Risk Module (`src/intake/weather_risk.py`)**
```python
@dataclass
class SeasonalRisk:
    destination: str
    travel_month: int
    risk_level: Literal["low", "medium", "high", "severe"]
    risk_type: Literal["monsoon", "extreme_heat", "cold", "cyclone", "none"]
    recommendation: str
```

**C. Activity Suitability Module (`src/intake/activity_matcher.py`)**
```python
@dataclass
class ActivitySuitability:
    activity_type: str
    suitable_for: List[str]  # "elderly", "toddlers", "pregnant", etc.
    intensity_level: Literal["light", "moderate", "high", "extreme"]
    warnings: List[str]
```

#### 3.1.2 Enhanced Risk Structure

Replace string-only risk flags with structured risks:

```python
@dataclass
class StructuredRisk:
    flag: str
    severity: Literal["low", "medium", "high", "critical"]
    category: Literal["budget", "document", "weather", "routing", "activity", "composition"]
    message: str
    details: Dict[str, Any]  # Flexible metadata
    affected_travelers: Optional[List[str]]  # Which party members
    mitigation_suggestions: List[str]
```

### 3.2 Frontend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Scenario UI Components                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Enhanced DecisionTab                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
│  │  │ RouteVisualizer│ │ RiskDetail  │  │ Feasibility │  │   │
│  │  │  (New)      │  │   Cards     │  │   Panel     │  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              New ItineraryTab                       │   │
│  │  (Visual route map + segment breakdown)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2.1 New Components

**A. RouteVisualizer Component**
```typescript
interface RouteVisualizerProps {
  segments: RouteSegment[];
  complexityScore: number;
  riskFlags: StructuredRisk[];
}

// Visual timeline showing:
// - Origin → Transfer → Destination flow
// - Duration bars
// - Risk indicators per segment
```

**B. RiskDetailCard Component**
```typescript
interface RiskDetailCardProps {
  risk: StructuredRisk;
  expanded: boolean;
  onToggle: () => void;
}

// Expandable card showing:
// - Risk category icon
// - Severity badge
// - Detailed explanation
// - Mitigation suggestions
```

**C. ActivitySuitabilityPanel**
```typescript
interface ActivitySuitabilityPanelProps {
  activities: ActivitySuitability[];
  partyComposition: PartyComposition;
}

// Grid showing activities × traveler compatibility
```

---

## 4. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create structured risk dataclass in `decision.py`
- [ ] Update `DecisionResult` to support `structured_risks: List[StructuredRisk]`
- [ ] Maintain backward compatibility with `risk_flags: List[str]`
- [ ] Update frontend types in `spine.ts`

### Phase 2: Route Analysis (Week 2-3)
- [ ] Implement `route_analysis.py` module
- [ ] Create itinerary text parser (regex + NLP)
- [ ] Add route complexity scoring
- [ ] Build RouteVisualizer component

### Phase 3: Weather Risk (Week 3-4)
- [ ] Implement `weather_risk.py` module
- [ ] Create seasonal risk database
- [ ] Add destination + month → risk mapping
- [ ] Build WeatherRiskIndicator component

### Phase 4: Activity Matching (Week 4-5)
- [ ] Implement `activity_matcher.py` module
- [ ] Create activity taxonomy
- [ ] Build ActivitySuitabilityPanel
- [ ] Integrate with existing elderly/toddler checks

### Phase 5: Integration & Polish (Week 5-6)
- [ ] Wire all new modules into `generate_risk_flags()`
- [ ] Enhance DecisionTab with new components
- [ ] Create new ItineraryTab
- [ ] Add tests and documentation

---

## 5. File References

### Backend
| File | Purpose | Key Lines |
|------|---------|-----------|
| [`src/intake/decision.py`](../../src/intake/decision.py) | Main decision engine | 1-1181 |
| [`src/intake/packet_models.py`](../../src/intake/packet_models.py) | Data models for packets | TBD |
| [`src/intake/extractors.py`](../../src/intake/extractors.py) | Text extraction utilities | 399 (adventure regex) |

### Frontend
| File | Purpose | Key Lines |
|------|---------|-----------|
| [`frontend/src/app/workbench/DecisionTab.tsx`](../../frontend/src/app/workbench/DecisionTab.tsx) | Decision display | 1-243 |
| [`frontend/src/app/workbench/SafetyTab.tsx`](../../frontend/src/app/workbench/SafetyTab.tsx) | Safety/leakage view | 1-217 |
| [`frontend/src/app/workbench/StrategyTab.tsx`](../../frontend/src/app/workbench/StrategyTab.tsx) | Strategy view | 1-205 |
| [`frontend/src/types/spine.ts`](../../frontend/src/types/spine.ts) | Type definitions | 1-46 |

### Documentation
| File | Purpose |
|------|---------|
| [`specs/decision_policy.md`](../../specs/decision_policy.md) | Decision engine specification |
| [`Docs/NB02_V02_IMPLEMENTATION.md`](../../Docs/NB02_V02_IMPLEMENTATION.md) | NB02 implementation notes |
| [`Docs/NB02_V02_PATCH_SUMMARY.md`](../../Docs/NB02_V02_PATCH_SUMMARY.md) | Recent patches to NB02 |

---

## 6. Open Questions

1. **Data Source for Weather:** Should we integrate with external weather APIs or maintain a static seasonal database?
2. **Route Parsing:** Should we use LLM-based extraction or rule-based parsing for itinerary text?
3. **Scope Boundaries:** Should scenario detection happen in NB02 (decision) or as a separate pre-processor?
4. **Real-time Updates:** Should weather risks update if travel dates change during conversation?

---

## 7. Decision Records

| Decision | Status | Rationale |
|----------|--------|-----------|
| Use structured risks alongside string flags | Proposed | Maintains backward compatibility while enabling rich UI |
| Create new itinerary-specific tab | Proposed | DecisionTab is already crowded |
| Phase implementation over 6 weeks | Proposed | Allows testing each module independently |

---

*Document maintained by: Architecture Team*  
*Last updated: 2026-04-15*
