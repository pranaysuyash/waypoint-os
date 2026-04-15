# Scenario Handling Technical Specification

**Document ID:** SPEC-SCENARIO-001  
**Version:** 0.1-Draft  
**Date:** 2026-04-15  
**Status:** Draft - Awaiting Review  

---

## 1. Executive Summary

This specification defines the architecture for enhanced scenario handling in the travel agency decision engine. It extends NB02's existing risk detection capabilities to cover weather/seasonal risks, route complexity, transfer fatigue, and activity suitability.

**Reference:** Built on top of [`src/intake/decision.py`](../src/intake/decision.py) v0.2

---

## 2. Related Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Architecture Plan | High-level architecture | [`Docs/architecture/SCENARIO_HANDLING_ARCHITECTURE.md`](../Docs/architecture/SCENARIO_HANDLING_ARCHITECTURE.md) |
| Decision Policy | NB02 decision rules | [`specs/decision_policy.md`](decision_policy.md) |
| NB02 Implementation | Current implementation | [`Docs/NB02_V02_IMPLEMENTATION.md`](../Docs/NB02_V02_IMPLEMENTATION.md) |
| Frontend Types | TypeScript interfaces | [`frontend/src/types/spine.ts`](../frontend/src/types/spine.ts) |

---

## 3. Data Models

### 3.1 Route Analysis Model

```python
# src/intake/route_models.py

from dataclasses import dataclass
from typing import List, Optional, Literal
from datetime import datetime

@dataclass
class GeoLocation:
    """Geographic coordinates for routing."""
    city: str
    country: str
    iata_code: Optional[str]  # Airport code if applicable
    latitude: float
    longitude: float

@dataclass
class RouteSegment:
    """Single leg of a journey."""
    segment_id: str
    sequence: int  # 0-indexed position in journey
    origin: GeoLocation
    destination: GeoLocation
    transport_mode: Literal["flight", "train", "ferry", "car", "bus", "walking"]
    
    # Temporal
    estimated_duration_hours: float
    departure_time: Optional[datetime]
    arrival_time: Optional[datetime]
    
    # Transfer details
    transfer_from_previous: bool
    transfer_wait_hours: Optional[float]
    transfer_type: Optional[Literal["airport", "station", "port", "hotel"]]
    
    # Risks specific to this segment
    segment_risks: List[str]

@dataclass
class RouteAnalysis:
    """Complete journey analysis."""
    # Source
    parsed_from: Literal["itinerary_text", "structured_json", "inferred"]
    raw_input: Optional[str]
    
    # Route structure
    segments: List[RouteSegment]
    total_legs: int
    total_travel_time_hours: float
    total_transfer_wait_hours: float
    
    # Destinations visited
    destinations: List[str]  # Unique destination names
    country_count: int
    
    # Complexity scoring
    complexity_score: float  # 0.0-1.0
    complexity_factors: List[str]  # Reasons for score
    
    # Fatigue indicators
    fatigue_indicators: List[str]
    recommended_max_legs_per_day: int

@dataclass
class RouteRiskAssessment:
    """Risks derived from route analysis."""
    route_analysis: RouteAnalysis
    
    # Transfer risks
    transfer_overload_risk: bool
    min_connection_time_risk: List[RouteSegment]  # Segments with tight connections
    
    # Fatigue risks
    multi_leg_fatigue_risk: bool
    back_to_back_transfers: int
    
    # Complexity risks
    multi_country_complexity: bool
    visa_requirements: List[str]  # Countries requiring visas
```

### 3.2 Weather Risk Model

```python
# src/intake/weather_risk.py

@dataclass
class SeasonalConditions:
    """Weather patterns for destination + month."""
    destination: str
    month: int  # 1-12
    
    # Primary risk
    risk_level: Literal["none", "low", "medium", "high", "severe"]
    risk_type: Literal[
        "monsoon",
        "extreme_heat", 
        "extreme_cold",
        "cyclone_hurricane",
        "flooding",
        "wildfire",
        "sandstorm",
        "none"
    ]
    
    # Details
    description: str
    affected_activities: List[str]
    alternative_months: List[int]  # Better months to visit
    
    # Recommendations
    packing_suggestions: List[str]
    activity_warnings: List[str]
    should_avoid: bool

@dataclass
class WeatherRiskAssessment:
    """Complete weather risk for trip."""
    date_window_start: datetime
    date_window_end: datetime
    
    # Per-destination assessment
    destination_risks: List[SeasonalConditions]
    
    # Overall trip risk
    overall_risk_level: Literal["none", "low", "medium", "high", "severe"]
    blocking_risks: List[SeasonalConditions]  # Risks that should block proposal
    advisory_risks: List[SeasonalConditions]  # Risks to flag but allow
    
    # Recommendations
    suggested_alternative_dates: Optional[str]
    preparation_checklist: List[str]
```

### 3.3 Activity Suitability Model

```python
# src/intake/activity_models.py

@dataclass
class ActivityProfile:
    """Physical/mental demands of an activity."""
    activity_type: str
    activity_name: str
    
    # Physical demands
    intensity_level: Literal["sedentary", "light", "moderate", "high", "extreme"]
    walking_distance_km: Optional[float]
    elevation_gain_meters: Optional[float]
    duration_hours: float
    
    # Environmental factors
    outdoor: bool
    weather_dependent: bool
    altitude_effects: bool
    
    # Restrictions
    minimum_age: Optional[int]
    maximum_age: Optional[int]
    not_suitable_for: List[str]  # "pregnant", "heart_conditions", "mobility_limited", etc.
    requires_fit_to_travel: bool

@dataclass
class SuitabilityMatch:
    """Match between activity and traveler."""
    activity: ActivityProfile
    traveler_segment: str  # "elderly", "toddlers", "young_adults", etc.
    
    # Assessment
    suitable: bool
    suitability_score: float  # 0.0-1.0
    concerns: List[str]
    modifications_needed: List[str]
    
    # Alternative suggestions
    alternative_activities: List[str]

@dataclass
class PartyActivityAssessment:
    """Activity compatibility for entire party."""
    activities: List[ActivityProfile]
    party_composition: Dict[str, int]  # {"elderly": 2, "toddlers": 1, ...}
    
    # Per-activity assessment
    activity_matches: List[SuitabilityMatch]
    
    # Party-level concerns
    split_group_recommendations: List[str]  # When part of group should skip
    pacing_recommendations: List[str]
```

### 3.4 Enhanced Risk Flag (Structured)

```python
# src/intake/decision.py (enhancement)

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class StructuredRisk:
    """Enhanced risk flag with full metadata.
    
    Replaces/enhances string-only risk_flags with rich structured data.
    Maintains backward compatibility via string serialization.
    """
    
    # Identity
    flag: str  # Machine-readable ID (e.g., "elderly_mobility_risk")
    
    # Classification
    severity: Literal["low", "medium", "high", "critical"]
    category: Literal[
        "budget",
        "document",
        "weather",
        "routing",
        "activity",
        "composition",
        "visa",
        "timing"
    ]
    
    # Display
    title: str  # Short human-readable title
    message: str  # Full explanation
    short_message: str  # For badges/summaries
    
    # Details (flexible by category)
    details: Dict[str, Any]
    # Examples by category:
    # - weather: {"destination": "Bali", "month": 12, "risk_type": "monsoon"}
    # - routing: {"leg_count": 4, "transfer_time": "2h", "fatigue_score": 0.7}
    # - activity: {"activity": "trekking", "unsuitable_for": ["toddlers"]}
    
    # Affected parties
    affected_travelers: Optional[List[str]]  # Names or segments
    affected_destinations: Optional[List[str]]
    
    # Suggestions
    mitigation_suggestions: List[str]
    alternative_recommendations: List[str]
    
    # UI hints
    icon: Optional[str]  # Icon name for frontend
    color_code: Optional[str]  # "red", "orange", "yellow", "blue"
    
    # Metadata
    detected_at: datetime
    detected_by: str  # Module that generated this risk
    
    def to_string(self) -> str:
        """Backward compatibility: serialize to string."""
        return f"[{self.severity.upper()}] {self.category}: {self.message}"
```

---

## 4. API Specifications

### 4.1 Route Analysis API

```python
# src/intake/route_analysis.py

def parse_itinerary_text(
    itinerary_text: str,
    known_destinations: Optional[List[str]] = None
) -> RouteAnalysis:
    """Parse free-text itinerary into structured route.
    
    Args:
        itinerary_text: Raw itinerary from user (e.g., "Bangkok → Chiang Mai → Bali")
        known_destinations: List of valid destination names for validation
        
    Returns:
        RouteAnalysis with segments and complexity scoring
        
    Example:
        >>> text = "Fly Bangkok to Chiang Mai (2 nights), then Bali for 5 days"
        >>> analysis = parse_itinerary_text(text)
        >>> analysis.total_legs
        2
        >>> analysis.complexity_score
        0.6
    """
    pass

def analyze_route_complexity(
    route: RouteAnalysis,
    party_composition: Optional[Dict[str, Any]] = None
) -> RouteRiskAssessment:
    """Score route complexity and identify risks.
    
    Considers:
    - Number of legs and transfers
    - Party composition (elderly/toddlers = lower tolerance)
    - Connection times
    - Multi-country complexity
    
    Args:
        route: Parsed route analysis
        party_composition: Optional party constraints
        
    Returns:
        RouteRiskAssessment with detailed risk breakdown
    """
    pass

def generate_route_risks(
    assessment: RouteRiskAssessment
) -> List[StructuredRisk]:
    """Convert route assessment to structured risks.
    
    Returns list of risks that can be merged into decision.risk_flags.
    """
    pass
```

### 4.2 Weather Risk API

```python
# src/intake/weather_risk.py

# Static data: Seasonal risk database
SEASONAL_RISK_DB: Dict[str, List[SeasonalConditions]] = {
    # destination -> list of 12 months
    "Bali": [
        SeasonalConditions(
            destination="Bali",
            month=1,
            risk_level="high",
            risk_type="monsoon",
            description="Peak rainy season with frequent downpours",
            ...
        ),
        # ... months 2-12
    ],
    # ... other destinations
}

def assess_weather_risk(
    destinations: List[str],
    date_window_start: datetime,
    date_window_end: datetime,
    activities: Optional[List[str]] = None
) -> WeatherRiskAssessment:
    """Assess weather risks for proposed travel dates.
    
    Args:
        destinations: List of destinations in itinerary
        date_window_start: Earliest travel date
        date_window_end: Latest travel date
        activities: Optional planned activities (some weather-sensitive)
        
    Returns:
        WeatherRiskAssessment with blocking vs advisory risks
    """
    pass

def generate_weather_risks(
    assessment: WeatherRiskAssessment
) -> List[StructuredRisk]:
    """Convert weather assessment to structured risks."""
    pass
```

### 4.3 Activity Suitability API

```python
# src/intake/activity_matcher.py

# Activity database
ACTIVITY_DB: Dict[str, ActivityProfile] = {
    "light_trekking": ActivityProfile(
        activity_type="trekking",
        activity_name="Light Trekking",
        intensity_level="light",
        walking_distance_km=3.0,
        elevation_gain_meters=100,
        minimum_age=8,
        not_suitable_for=["mobility_limited", "severe_heart_conditions"],
        ...
    ),
    "snorkeling": ActivityProfile(
        activity_type="water_sport",
        activity_name="Snorkeling",
        intensity_level="light",
        minimum_age=6,
        not_suitable_for=["pregnant", "severe_respiratory_issues"],
        ...
    ),
    # ... more activities
}

def match_activities_to_party(
    activities: List[str],
    party_composition: Dict[str, Any]
) -> PartyActivityAssessment:
    """Check activity suitability for party composition.
    
    Args:
        activities: List of activity IDs or descriptions
        party_composition: Parsed party composition from packet
        
    Returns:
        PartyActivityAssessment with suitability scores
    """
    pass

def generate_activity_risks(
    assessment: PartyActivityAssessment
) -> List[StructuredRisk]:
    """Convert activity assessment to structured risks."""
    pass
```

---

## 5. Integration Points

### 5.1 Decision.py Integration

```python
# src/intake/decision.py

# Add to imports
from .route_analysis import analyze_route_complexity, generate_route_risks
from .weather_risk import assess_weather_risk, generate_weather_risks
from .activity_matcher import match_activities_to_party, generate_activity_risks

def generate_risk_flags(
    packet: CanonicalPacket,
    stage: str,
    cached_feasibility: Optional[Dict[str, Any]] = None,
    route_analysis: Optional[RouteAnalysis] = None,  # NEW
    weather_assessment: Optional[WeatherRiskAssessment] = None,  # NEW
    activity_assessment: Optional[PartyActivityAssessment] = None,  # NEW
) -> List[StructuredRisk]:  # Changed return type
    """Enhanced risk generation with scenario analysis.
    
    Maintains backward compatibility - still returns risks that can be
    rendered as strings, but now with full structured data.
    """
    risks: List[StructuredRisk] = []
    
    # Existing risks (converted to StructuredRisk)
    risks.extend(_generate_composition_risks(packet))  # elderly, toddlers
    risks.extend(_generate_document_risks(packet, stage))  # passport, visa
    risks.extend(_generate_budget_risks(packet, cached_feasibility))
    
    # NEW: Route/transfer risks
    if route_analysis:
        route_assessment = analyze_route_complexity(route_analysis, packet)
        risks.extend(generate_route_risks(route_assessment))
    
    # NEW: Weather/season risks
    if weather_assessment:
        risks.extend(generate_weather_risks(weather_assessment))
    
    # NEW: Activity suitability risks
    if activity_assessment:
        risks.extend(generate_activity_risks(activity_assessment))
    
    return risks
```

### 5.2 DecisionResult Enhancement

```python
# Add to DecisionResult dataclass

@dataclass
class DecisionResult:
    # ... existing fields ...
    
    # Enhanced risk fields (backward compatible)
    risk_flags: List[str] = field(default_factory=list)  # Legacy: string representations
    structured_risks: List[StructuredRisk] = field(default_factory=list)  # NEW
    
    # Scenario analysis results (NEW)
    route_analysis: Optional[RouteAnalysis] = None
    weather_assessment: Optional[WeatherRiskAssessment] = None
    activity_assessment: Optional[PartyActivityAssessment] = None
```

### 5.3 Frontend TypeScript Types

```typescript
// frontend/src/types/scenario.ts (NEW FILE)

export interface StructuredRisk {
  flag: string;
  severity: "low" | "medium" | "high" | "critical";
  category: "budget" | "document" | "weather" | "routing" | "activity" | "composition" | "visa" | "timing";
  title: string;
  message: string;
  short_message: string;
  details: Record<string, unknown>;
  affected_travelers?: string[];
  affected_destinations?: string[];
  mitigation_suggestions: string[];
  alternative_recommendations: string[];
  icon?: string;
  color_code?: string;
  detected_at: string;
  detected_by: string;
}

export interface RouteSegment {
  segment_id: string;
  sequence: number;
  origin: GeoLocation;
  destination: GeoLocation;
  transport_mode: "flight" | "train" | "ferry" | "car" | "bus" | "walking";
  estimated_duration_hours: number;
  departure_time?: string;
  arrival_time?: string;
  transfer_from_previous: boolean;
  transfer_wait_hours?: number;
  transfer_type?: "airport" | "station" | "port" | "hotel";
  segment_risks: string[];
}

export interface RouteAnalysis {
  parsed_from: "itinerary_text" | "structured_json" | "inferred";
  raw_input?: string;
  segments: RouteSegment[];
  total_legs: number;
  total_travel_time_hours: number;
  total_transfer_wait_hours: number;
  destinations: string[];
  country_count: number;
  complexity_score: number;
  complexity_factors: string[];
  fatigue_indicators: string[];
  recommended_max_legs_per_day: number;
}

export interface SeasonalConditions {
  destination: string;
  month: number;
  risk_level: "none" | "low" | "medium" | "high" | "severe";
  risk_type: "monsoon" | "extreme_heat" | "extreme_cold" | "cyclone_hurricane" | "flooding" | "wildfire" | "sandstorm" | "none";
  description: string;
  affected_activities: string[];
  alternative_months: number[];
  packing_suggestions: string[];
  activity_warnings: string[];
  should_avoid: boolean;
}

export interface ActivityProfile {
  activity_type: string;
  activity_name: string;
  intensity_level: "sedentary" | "light" | "moderate" | "high" | "extreme";
  walking_distance_km?: number;
  elevation_gain_meters?: number;
  duration_hours: number;
  outdoor: boolean;
  weather_dependent: boolean;
  altitude_effects: boolean;
  minimum_age?: number;
  maximum_age?: number;
  not_suitable_for: string[];
  requires_fit_to_travel: boolean;
}
```

---

## 6. Component Specifications

### 6.1 RouteVisualizer Component

```typescript
// frontend/src/components/scenario/RouteVisualizer.tsx

interface RouteVisualizerProps {
  analysis: RouteAnalysis;
  risks: StructuredRisk[];
  compact?: boolean;  // If true, show simplified version
}

// Renders:
// - Visual timeline of segments
// - Transfer points highlighted
// - Risk indicators on affected segments
// - Complexity score badge
// - "Expand" option for detailed view
```

### 6.2 RiskDetailCard Component

```typescript
// frontend/src/components/scenario/RiskDetailCard.tsx

interface RiskDetailCardProps {
  risk: StructuredRisk;
  defaultExpanded?: boolean;
}

// Renders:
// - Category icon
// - Severity badge (color-coded)
// - Title and message
// - Details section (expandable)
// - Mitigation suggestions
// - Alternative recommendations
```

### 6.3 WeatherRiskPanel Component

```typescript
// frontend/src/components/scenario/WeatherRiskPanel.tsx

interface WeatherRiskPanelProps {
  assessment: WeatherRiskAssessment;
}

// Renders:
// - Calendar view with risk overlay
// - Destination-specific warnings
// - Alternative date suggestions
// - Packing checklist
```

### 6.4 ActivitySuitabilityGrid Component

```typescript
// frontend/src/components/scenario/ActivitySuitabilityGrid.tsx

interface ActivitySuitabilityGridProps {
  activities: ActivityProfile[];
  partyComposition: Record<string, number>;
  matches: SuitabilityMatch[];
}

// Renders:
// - Grid: Activities × Party Segments
// - Suitability scores (checkmarks/warnings)
// - Split group recommendations
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Module | Test File | Coverage |
|--------|-----------|----------|
| Route Analysis | `tests/test_route_analysis.py` | Parsing, complexity scoring |
| Weather Risk | `tests/test_weather_risk.py` | Seasonal lookup, risk classification |
| Activity Matcher | `tests/test_activity_matcher.py` | Suitability scoring |
| Structured Risk | `tests/test_structured_risks.py` | Serialization, backward compat |

### 7.2 Integration Tests

| Scenario | Test File | Description |
|----------|-----------|-------------|
| Multi-city SE Asia | `tests/test_scenario_se_asia.py` | Bangkok→Chiang Mai→Bali with weather |
| Elderly European tour | `tests/test_scenario_elderly_europe.py` | Transfer fatigue with elderly |
| Family adventure | `tests/test_scenario_family_adventure.py` | Activity suitability for mixed ages |

### 7.3 Test Data

```python
# tests/fixtures/scenario_fixtures.py

TEST_ITINERARIES = {
    "se_asia_multi_city": {
        "text": "Bangkok → Chiang Mai → Bali",
        "expected_legs": 2,
        "expected_complexity": 0.6,
        "weather_month": 8,  # Monsoon risk
    },
    "european_tour": {
        "text": "London → Paris → Rome → Athens",
        "expected_legs": 3,
        "expected_complexity": 0.8,
        "visa_countries": ["UK", "Schengen", "Greece"],
    },
}
```

---

## 8. Migration Path

### Phase 1: Backend Foundation
1. Create new model files (don't modify existing yet)
2. Add structured risk alongside string flags
3. Update `DecisionResult` with new optional fields

### Phase 2: Frontend Types
1. Create new TypeScript type file
2. Update API response types
3. Maintain backward compatibility

### Phase 3: UI Components
1. Build new components in parallel
2. Feature-flag new UI
3. Gradual rollout

### Phase 4: Full Integration
1. Enable route/weather/activity modules
2. Remove feature flags
3. Deprecate string-only risk flags

---

## 9. Open Issues

| Issue | Status | Decision Needed |
|-------|--------|-----------------|
| Weather data source | Open | Static DB vs API integration |
| Route parsing approach | Open | Rule-based vs LLM-based |
| Activity taxonomy scope | Open | How many activities to support |
| Performance budget | Open | Max acceptable latency increase |

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **Structured Risk** | Risk flag with full metadata (severity, category, details, suggestions) |
| **Route Segment** | Single leg of journey (e.g., flight from A to B) |
| **Complexity Score** | 0.0-1.0 score indicating itinerary complexity |
| **Fatigue Indicator** | Signal that traveler may experience fatigue (back-to-back flights, etc.) |
| **Blocking Risk** | Risk that prevents progression to next stage |
| **Advisory Risk** | Risk to flag but doesn't block progression |

---

*Specification Owner: Architecture Team*  
*Reviewers: Backend Team, Frontend Team*  
*Approval: Pending*
