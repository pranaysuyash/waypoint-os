# Notebook 04: Response Generation — Contract Definition

**Status**: 🟡 Historical specification — superseded for new implementation by `TRAVELER_PROPOSAL_BOUNDARY_CONTRACT_2026-05-11.md`  
**Topic ID**: 17  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Depends On**: NB01, NB02, NB03, INTERNAL_DATA_INTEGRATION  
**Last Updated**: 2026-04-09

> 2026-05-11 implementation note: new work must use the semantic stage `traveler_proposal`, semantic gate `proposal_quality`, and user label "Build Proposal". The examples below preserve historical notebook terminology, but must not be implemented literally. In particular, do not serialize combined traveler/internal proposal objects with raw `asdict()`. Use the explicit public/internal boundary in `Docs/research/TRAVELER_PROPOSAL_BOUNDARY_CONTRACT_2026-05-11.md` and `src/intake/traveler_proposal.py`.

---

## Purpose

Transform `SessionOutput` (from NB03) into **traveler-ready deliverables**:

1. **Proposal Document** — Formatted itinerary with options
2. **Internal Quote Sheet** — Cost breakdown, margins, vendor contacts
3. **Follow-up Actions** — What happens next, who does what

This is the **"Last Mile"** compiler stage. Everything before was planning. This is production.

**Design principle**: Generate structured output that can be:
- Reviewed by agent before sending
- Sent directly to traveler (if PROCEED_TRAVELER_SAFE)
- Tracked for conversion analytics
- Stored for learning

---

## Inputs

| Input | Type | Source | Description |
|-------|------|--------|-------------|
| `session_output` | SessionOutput | NB03 | Strategy, prompts, decision state |
| `packet` | CanonicalPacket | NB01 | All facts, signals, hypotheses |
| `internal_data` | AgencyData | External | Preferred suppliers, tribal knowledge, margins |
| `template_library` | TemplateLibrary | External | Package templates, formatting rules |

---

## Outputs

### 1. TravelerProposal

```python
@dataclass
class TravelerProposal:
    """Customer-facing proposal document."""
    
    # Identity
    proposal_id: str
    packet_id: str
    created_at: str
    version: int  # For revision tracking
    
    # Content
    title: str  # e.g., "Singapore Family Adventure — 5 Nights"
    summary: str  # One-paragraph overview
    highlights: List[str]  # 3-5 bullet points
    
    # Itinerary (day-by-day)
    days: List[DayPlan]
    
    # Options (if multiple tiers)
    options: List[ProposalOption]
    
    # Pricing
    pricing: PricingBreakdown
    
    # Trust signals
    why_this_fits: str  # Personalization rationale
    agency_notes: str  # Why we recommend this
    
    # Actions
    next_steps: List[str]
    expiry_date: str  # Quote valid until
    
    # Metadata
    decision_state: str  # How this was generated
    confidence_score: float
    assumptions_made: List[str]  # Transparent about gaps


@dataclass
class DayPlan:
    day_number: int
    date: Optional[str]
    title: str
    activities: List[Activity]
    meals: List[str]  # What's included
    accommodation: Optional[HotelInfo]
    transfers: List[TransferInfo]
    free_time: Optional[str]


@dataclass
class Activity:
    name: str
    description: str
    duration: str
    included: bool
    price_per_person: Optional[float]
    why_included: str  # Rationale based on customer profile
    booking_ref: Optional[str]  # Internal reference


@dataclass
class HotelInfo:
    name: str
    room_type: str
    nights: int
    check_in: str
    check_out: str
    amenities: List[str]
    why_chosen: str  # e.g., "Pool for kids, Jain food nearby"
    images: List[str]  # URLs


@dataclass 
class ProposalOption:
    """Multiple tier presentation (Standard, Premium, Luxury)."""
    tier_name: str  # "Comfort", "Premium", "Luxury"
    tagline: str  # "Great value", "Best balance", "Ultimate experience"
    total_price: float
    whats_different: str  # Key differences from base
    ideal_for: str  # Customer segment


@dataclass
class PricingBreakdown:
    currency: str  # INR
    total_per_person: float
    total_for_group: float
    
    # Component breakdown
    components: List[PriceComponent]
    
    # Inclusions/exclusions
    includes: List[str]
    excludes: List[str]
    
    # Payment terms
    payment_schedule: List[PaymentMilestone]
    cancellation_policy: str


@dataclass
class PriceComponent:
    category: str  # "Flights", "Hotels", "Activities", "Transfers"
    description: str
    cost: float
    margin_percent: Optional[float]  # Internal only (marked in _internal)


@dataclass
class PaymentMilestone:
    trigger: str  # "Booking confirmation", "30 days before", etc.
    amount: float
    percent_of_total: float
```

### 2. InternalQuoteSheet

```python
@dataclass
class InternalQuoteSheet:
    """Agent-facing operational document."""
    
    proposal_id: str
    
    # Vendor details (for booking)
    vendors: List[VendorContact]
    
    # True cost breakdown (with margins exposed)
    cost_breakdown: DetailedCostBreakdown
    
    # Risk assessment
    risks: List[RiskItem]
    
    # Margins
    total_margin_amount: float
    total_margin_percent: float
    margin_by_component: Dict[str, float]
    
    # Booking checklist
    booking_checklist: List[ChecklistItem]
    
    # Follow-up tasks
    follow_up_tasks: List[Task]


@dataclass
class VendorContact:
    supplier_type: str  # "hotel", "airline", "activity", "transfer"
    supplier_name: str
    contact_name: str
    phone: str
    email: str
    booking_ref: str
    net_rate: float
    margin_percent: float
    reliability_score: float
    notes: str


@dataclass
class RiskItem:
    severity: str  # "low", "medium", "high", "critical"
    category: str  # "availability", "pricing", "operational", "customer"
    description: str
    mitigation: str
    owner: str  # Who handles this


@dataclass
class ChecklistItem:
    item: str
    required_by: str  # Date
    status: str  # "pending", "in_progress", "done"
    owner: str
```

### 3. ResponseGenerationResult

```python
@dataclass
class ResponseGenerationResult:
    """Complete output of NB04."""
    
    # Main outputs
    traveler_proposal: TravelerProposal
    internal_quote_sheet: InternalQuoteSheet
    
    # Processing metadata
    generation_time_ms: int
    template_used: Optional[str]
    customizations_applied: List[str]
    
    # Quality metrics
    completeness_score: float  # Did we fill all sections?
    personalization_score: float  # How well tailored?
    
    # Audit trail
    data_sources_used: List[str]  # Which internal data contributed
    assumptions_documented: List[str]
    
    # Next action
    recommended_next_step: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "traveler_proposal": asdict(self.traveler_proposal),
            "internal_quote_sheet": asdict(self.internal_quote_sheet),
            "quality_metrics": {
                "completeness": self.completeness_score,
                "personalization": self.personalization_score,
            },
            "audit": {
                "sources": self.data_sources_used,
                "assumptions": self.assumptions_documented,
            },
        }
```

---

## Generation Modes

### Mode 1: Package-Based (High Confidence, Common Pattern)

**When to use**: Customer matches a known package template

```python
# Input: Family of 4, Singapore, 5 nights, mid-budget
# Matches: "singapore_family_classic" template

def generate_from_template(
    packet: CanonicalPacket,
    template: PackageTemplate,
    internal_data: AgencyData
) -> TravelerProposal:
    """
    Start with template, customize for specific customer.
    """
    # 1. Load template structure
    proposal = template.to_proposal()
    
    # 2. Customize dates
    proposal = apply_dates(proposal, packet.facts["travel_dates"])
    
    # 3. Customize for composition
    proposal = apply_traveler_composition(proposal, packet.facts["traveler_composition"])
    
    # 4. Apply internal data optimizations
    proposal = optimize_with_internal_data(proposal, internal_data)
    #    - Select preferred hotel room type
    #    - Add preferred vendor transfers
    #    - Include "tribal knowledge" tips
    
    # 5. Generate pricing
    proposal.pricing = calculate_pricing(proposal, internal_data.margin_data)
    
    return proposal
```

**Characteristics**:
- Fast (template → customize)
- High quality (proven package)
- Predictable margins
- Easy to explain ("our most popular family package")

### Mode 2: Constraint-Based Assembly (Medium Confidence)

**When to use**: No exact template match, but constraints clear

```python
# Input: Couple, Vietnam, 7 nights, luxury, foodie focus
# No exact template, but constraints guide selection

def generate_by_assembly(
    packet: CanonicalPacket,
    internal_data: AgencyData
) -> TravelerProposal:
    """
    Assemble proposal component by component based on constraints.
    """
    proposal = TravelerProposal()
    
    # 1. Select accommodation
    hotels = internal_data.get_hotels(
        destination=packet.facts["destination_city"].value,
        tier="luxury",
        tags=["romantic", "dining"]
    )
    proposal.hotel = rank_and_select(hotels, criteria=["reliability", "margin", "fit"])
    
    # 2. Select activities
    activities = internal_data.get_activities(
        destination=packet.facts["destination_city"].value,
        tags=["food", "culture", "couple-friendly"]
    )
    proposal.activities = select_top_n(activities, n=5, budget=remaining_budget)
    
    # 3. Arrange transfers
    proposal.transfers = internal_data.get_preferred_transfers(
        destination=packet.facts["destination_city"].value
    )
    
    # 4. Sequence into days
    proposal.days = sequence_into_days(proposal.activities, pace="relaxed")
    
    return proposal
```

**Characteristics**:
- Moderate speed
- Flexible for custom requests
- Requires more validation
- May need agent review

### Mode 3: Research-Intensive (Low Confidence, Novel Request)

**When to use**: Unfamiliar destination, unusual requirements

```python
# Input: "Armenia", "wine tourism", "archaeological sites"
# Agency has no preferred suppliers, no templates

def generate_with_research(
    packet: CanonicalPacket,
    research_tools: ResearchToolkit
) -> TravelerProposal:
    """
    Generate with external research assistance.
    """
    # 1. Research destinations
    destinations = research_tools.search_destinations(
        interests=packet.facts["trip_purpose"].value,
        constraints=packet.facts
    )
    
    # 2. Research accommodations
    hotels = research_tools.search_hotels(
        destination=packet.facts["destination_city"].value,
        criteria=extract_criteria(packet)
    )
    
    # 3. Build skeleton proposal
    proposal = build_skeleton_proposal(destinations, hotels)
    
    # 4. Flag for agent review
    proposal._internal["needs_agent_review"] = True
    proposal._internal["research_sources"] = research_tools.get_sources()
    
    return proposal
```

**Characteristics**:
- Slow (requires external research)
- Lower confidence
- **Always internal draft** (never PROCEED_TRAVELER_SAFE)
- Agent must validate

---

## Component Selection Logic

### Hotel Selection

```python
def select_hotel(
    destination: str,
    packet: CanonicalPacket,
    internal_data: AgencyData
) -> HotelInfo:
    """
    Multi-factor hotel selection.
    """
    # Get candidate pool
    candidates = internal_data.preferred_hotels.get(destination, [])
    
    if not candidates:
        # Fallback to open market (with warning)
        candidates = search_open_market(destination)
    
    # Score each candidate
    scored = []
    for hotel in candidates:
        score = 0.0
        
        # Fit score (0-40)
        score += score_traveler_fit(hotel, packet) * 40
        
        # Margin score (0-30)
        score += score_margin(hotel, internal_data) * 30
        
        # Reliability score (0-20)
        score += hotel.reliability_score / 10 * 20
        
        # Availability score (0-10)
        score += score_availability(hotel, packet.facts.get("travel_dates")) * 10
        
        scored.append((hotel, score))
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[0][0]


def score_traveler_fit(hotel: Hotel, packet: CanonicalPacket) -> float:
    """
    Score how well hotel fits traveler profile (0-1).
    """
    score = 0.0
    composition = packet.facts.get("traveler_composition", {}).value
    
    # Family with kids needs pool/family amenities
    if "family" in composition and hotel.has_family_amenities:
        score += 0.3
    
    # Elderly needs elevator, accessible
    if "elderly" in composition and hotel.is_accessible:
        score += 0.3
    
    # Check dietary needs
    dietary = packet.facts.get("dietary_requirements", {}).value
    if dietary and hotel.supports_dietary(dietary):
        score += 0.4
    
    return min(score, 1.0)
```

### Activity Selection

```python
def select_activities(
    destination: str,
    packet: CanonicalPacket,
    internal_data: AgencyData,
    max_days: int
) -> List[Activity]:
    """
    Select activities that fit the trip profile.
    """
    # Get all activities for destination
    all_activities = internal_data.activities.get(destination, [])
    
    # Filter by suitability
    composition = packet.facts.get("traveler_composition", {}).value
    suitable = [a for a in all_activities if is_suitable(a, composition)]
    
    # Sort by relevance to trip purpose
    purpose = packet.facts.get("trip_purpose", {}).value
    scored = [(a, score_activity_relevance(a, purpose)) for a in suitable]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Select top N based on trip length
    # Rule: 1 major activity per day, 2-3 minor
    num_major = max_days
    num_minor = max_days * 2
    
    selected = []
    selected.extend([s[0] for s in scored[:num_major] if s[0].category == "major"])
    selected.extend([s[0] for s in scored[:num_minor] if s[0].category == "minor"])
    
    return selected
```

---

## Personalization Engine

### The "Why This Fits" Rationale

Every proposal must explain why it fits THIS customer:

```python
def generate_personalization_rationale(
    proposal: TravelerProposal,
    packet: CanonicalPacket
) -> str:
    """
    Generate the "why this fits you" explanation.
    """
    facts = packet.facts
    parts = []
    
    # Composition-based
    composition = facts.get("traveler_composition", {}).value
    if composition:
        parts.append(f"Designed for {composition}")
    
    # Purpose-based
    purpose = facts.get("trip_purpose", {}).value
    if purpose:
        parts.append(f"Focus on {purpose}")
    
    # Budget-based
    budget = facts.get("budget_range", {}).value
    if budget:
        parts.append(f"Within your ₹{budget/1000:.0f}K budget")
    
    # Historical (if repeat customer)
    if packet.customer_history:
        parts.append(f"Based on your love of {packet.customer_history.preferred_activity_type}")
    
    # Specific accommodations
    if "elderly" in str(composition) and proposal.hotel.is_accessible:
        parts.append("Elevator-accessible hotel for comfort")
    
    if "kids" in str(composition) and proposal.hotel.has_pool:
        parts.append("Pool for kids to enjoy downtime")
    
    return " | ".join(parts)
```

---

## Quality Gates

Before a proposal is returned, it must pass:

```python
PROPOSAL_QUALITY_GATES = {
    "completeness": {
        "required_fields": [
            "title", "summary", "days", "pricing.total_for_group",
            "next_steps", "expiry_date"
        ],
        "min_days_documented": lambda packet: packet.facts.get("duration_nights", 3),
    },
    
    "pricing": {
        "must_have_breakdown": True,
        "total_must_be_reasonable": lambda total, packet: (
            packet.facts.get("budget_range", {}).value * 0.8 <= total <= 
            packet.facts.get("budget_range", {}).value * 1.3
        ),
    },
    
    "personalization": {
        "must_reference_customer_facts": True,
        "why_this_fits_min_length": 50,
    },
    
    "internal": {
        "must_have_vendor_contacts": True,
        "must_have_margin_breakdown": True,
        "risks_documented": True,
    }
}


def run_quality_gates(proposal: TravelerProposal, packet: CanonicalPacket) -> Dict:
    """
    Run all quality gates, return pass/fail with reasons.
    """
    results = {}
    
    for gate_name, checks in PROPOSAL_QUALITY_GATES.items():
        gate_passed = True
        failures = []
        
        for check_name, check in checks.items():
            if callable(check):
                try:
                    passed = check(proposal, packet)
                except:
                    passed = False
            else:
                passed = bool(check)  # Simple boolean check
            
            if not passed:
                gate_passed = False
                failures.append(check_name)
        
        results[gate_name] = {
            "passed": gate_passed,
            "failures": failures
        }
    
    return results
```

---

## Error Handling & Fallbacks

```python
class ProposalGenerationError(Exception):
    """Base class for generation failures."""
    pass


class InsufficientDataError(ProposalGenerationError):
    """Not enough data to generate proposal."""
    pass


class VendorUnavailableError(ProposalGenerationError):
    """Preferred vendors not available for dates."""
    pass


class BudgetMismatchError(ProposalGenerationError):
    """Cannot meet budget constraints."""
    pass


def generate_with_fallbacks(
    packet: CanonicalPacket,
    session_output: SessionOutput,
    internal_data: AgencyData
) -> ResponseGenerationResult:
    """
    Generate proposal with fallback strategies.
    """
    try:
        # Try template-based first
        if session_output.template_match:
            proposal = generate_from_template(packet, session_output.template_match, internal_data)
        else:
            # Try constraint-based assembly
            proposal = generate_by_assembly(packet, internal_data)
        
    except VendorUnavailableError:
        # Fallback: Expand vendor search
        proposal = generate_with_expanded_vendors(packet, internal_data)
        proposal._internal["fallback_used"] = "expanded_vendors"
        
    except BudgetMismatchError:
        # Fallback: Generate options at different tiers
        proposal = generate_tiered_options(packet, internal_data)
        proposal._internal["fallback_used"] = "tiered_options"
        
    except InsufficientDataError:
        # Cannot generate — escalate
        return ResponseGenerationResult(
            traveler_proposal=None,
            internal_quote_sheet=None,
            error="INSUFFICIENT_DATA",
            recommended_next_step="ASK_FOLLOWUP",
        )
    
    # Run quality gates
    quality = run_quality_gates(proposal, packet)
    if not all(g["passed"] for g in quality.values()):
        # Flag for agent review
        proposal._internal["quality_gates_failed"] = quality
    
    return build_result(proposal, quality)
```

---

## Test Requirements

### Unit Tests

```python
# Test 1: Template-based generation
def test_template_generation():
    packet = make_packet(
        destination="Singapore",
        composition="family_with_kids",
        nights=5,
        budget=300000
    )
    result = generate_from_template(packet, "singapore_family_classic", agency_data)
    
    assert result.traveler_proposal.title is not None
    assert len(result.traveler_proposal.days) == 5
    assert result.traveler_proposal.pricing.total_for_group <= 300000 * 1.1


# Test 2: Personalization rationale
def test_personalization():
    packet = make_packet(composition="family_with_elderly")
    proposal = generate_proposal(packet, agency_data)
    
    assert "elderly" in proposal.why_this_fits.lower()
    assert proposal.hotel.is_accessible  # Should select accessible hotel


# Test 3: Margin preservation
def test_margin_preservation():
    packet = make_packet(destination="Singapore", budget=200000)
    result = generate_proposal(packet, agency_data)
    
    # Should prioritize hotels with better margins
    internal_sheet = result.internal_quote_sheet
    assert internal_sheet.total_margin_percent >= 10.0


# Test 4: Quality gates
def test_quality_gates():
    incomplete_proposal = TravelerProposal(days=[], pricing=None)
    results = run_quality_gates(incomplete_proposal, make_packet())
    
    assert results["completeness"]["passed"] is False
    assert "required_fields" in results["completeness"]["failures"]
```

### Integration Tests

```python
# Test 5: End-to-end pipeline
def test_full_pipeline():
    # NB01 → NB02 → NB03 → NB04
    raw_input = "Family of 4, Singapore, March 15-20, budget 3L"
    
    packet = run_nb01(raw_input)
    decision = run_nb02(packet)
    session = run_nb03(decision, packet)
    result = run_nb04(session, packet, agency_data)
    
    assert result.traveler_proposal is not None
    assert result.quality_metrics["completeness"] > 0.9
```

---

## Files

- **This contract**: `Docs/research/NOTEBOOK_04_CONTRACT.md`
- **Related**: NB03 contract, INTERNAL_DATA_INTEGRATION

---

*This is a specification ready for implementation.*
