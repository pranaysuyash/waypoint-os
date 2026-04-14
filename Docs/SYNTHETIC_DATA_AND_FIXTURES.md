# Synthetic Data and Fixtures

**Date**: 2026-04-14
**Purpose**: Test data, examples, and fixtures for development and testing

---

## Overview

This document provides:
1. Data schemas for all entities
2. Synthetic examples for testing
3. Edge cases and boundary conditions
4. Generator logic for creating test data

### Fixture Files in Repository

- `data/fixtures/product_persona_flows_synthetic_v1.json`
  - Purpose: PM/UX synthetic scenarios for role-based journeys.
  - Coverage:
    - agency owner / senior agent / junior agent / end traveler personas
    - functional/emotional/social JTBD per persona
    - aha moments and metric proxies per persona
    - end-to-end persona flow steps
    - flywheel instrumentation fields and open PM questions
  - Primary use:
    - acceptance criteria planning
    - scenario-driven QA and rehearsal
    - PM prioritization workshops

---

## Part 1: Core Data Schemas

### Agency Schema

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class AgencyTier(str, Enum):
    SOLO = "solo"
    SMALL = "small"
    MEDIUM = "medium"
    HOST = "host"

class Agency(BaseModel):
    id: str = Field(default_factory=lambda: f"agency_{uuid4()}")
    name: str
    slug: str  # URL-friendly identifier
    tier: AgencyTier
    created_at: datetime = Field(default_factory=datetime.now)

    # Preferences
    primary_markets: List[str] = []  # ["domestic", "international"]
    typical_budget_range: Optional[str] = None  # "₹1L-₹3L"
    specialize_destinations: List[str] = []

    # Metadata
    owner_name: str
    owner_email: str
    billing_email: str
    phone: Optional[str] = None

    # Status
    is_active: bool = True
    trial_ends_at: Optional[datetime] = None
    subscription_plan: Optional[str] = None
```

### Example: Agency Data

```python
# Solo Agency
solo_agency = Agency(
    name="Priya Travels",
    slug="priya-travels",
    tier=AgencyTier.SOLO,
    owner_name="Priya Sharma",
    owner_email="priya@priyatravels.com",
    billing_email="priya@priyatravels.com",
    phone="+91 98765 43210",
    primary_markets=["international"],
    typical_budget_range="₹1L-₹3L",
    specialize_destinations=["Europe", "Southeast Asia"]
)

# Small Agency
small_agency = Agency(
    name="Sky High Tours",
    slug="sky-high-tours",
    tier=AgencyTier.SMALL,
    owner_name="Rajesh Kumar",
    owner_email="rajesh@skyhigh.com",
    billing_email="billing@skyhigh.com",
    phone="+91 98765 12345",
    primary_markets=["domestic", "international"],
    typical_budget_range="₹50K-₹2L",
    specialize_destinations=["India", "Thailand", "Dubai"]
)
```

---

### User/Agent Schema

```python
class AgentRole(str, Enum):
    OWNER = "owner"
    SENIOR = "senior"
    JUNIOR = "junior"

class Agent(BaseModel):
    id: str = Field(default_factory=lambda: f"agent_{uuid4()}")
    agency_id: str
    name: str
    email: str
    role: AgentRole
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    # Performance tracking
    trips_processed: int = 0
    avg_processing_time_min: float = 0
    client_rating: float = 0.0
```

### Example: Agent Data

```python
# Senior Agent
senior_agent = Agent(
    id="agent_priya_001",
    agency_id="agency_priya_travels",
    name="Priya Sharma",
    email="priya@priyatravels.com",
    role=AgentRole.SENIOR,
    phone="+91 98765 43210",
    trips_processed=234,
    avg_processing_time_min=18.5,
    client_rating=4.9
)

# Junior Agent
junior_agent = Agent(
    id="agent_amit_001",
    agency_id="agency_sky_high",
    name="Amit Kumar",
    email="amit@skyhigh.com",
    role=AgentRole.JUNIOR,
    phone="+91 87654 32109",
    trips_processed=45,
    avg_processing_time_min=32.0,
    client_rating=4.3
)
```

---

### Trip Schema

```python
class TripStatus(str, Enum):
    NEW = "new"
    INTAKE = "intake"
    QUESTIONS_SENT = "questions_sent"
    AWAITING_RESPONSE = "awaiting_response"
    BRIEF_COMPLETE = "brief_complete"
    OPTIONS_GENERATED = "options_generated"
    SENT_TO_CLIENT = "sent_to_client"
    CLIENT_REVIEWING = "client_reviewing"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    BOOKED = "booked"
    CANCELLED = "cancelled"

class Trip(BaseModel):
    id: str = Field(default_factory=lambda: f"trip_{uuid4()}")
    agency_id: str
    agent_id: str
    status: TripStatus = TripStatus.NEW

    # Client info
    client_name: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client whatsapp: Optional[str] = None

    # Trip details (extracted)
    destination: Optional[str] = None
    destinations_list: List[str] = []
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None

    # Travelers
    travelers_count_adults: int = 0
    travelers_count_children: int = 0
    travelers_ages: List[int] = []

    # Budget
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_currency: str = "INR"

    # Preferences
    preferences: List[str] = []
    avoid_list: List[str] = []
    constraints: Dict[str, Any] = {}

    # Metadata
    source_channel: str = "whatsapp"  # whatsapp, email, phone, in_person
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # AI processing
    raw_input: Optional[str] = None
    extracted_constraints: Optional[Dict] = None
    contradictions: List[str] = []
    blockers: List[str] = []
    feasibility_verdict: Optional[str] = None
    confidence_score: Optional[float] = None
```

---

### Option Schema

```python
class Option(BaseModel):
    id: str = Field(default_factory=lambda: f"option_{uuid4()}")
    trip_id: str

    # Content
    name: str  # "France Focus", "Italy Focus"
    description: str
    destinations: List[str]

    # Rationale
    why_this_fits: str
    trade_offs: List[str]

    # Logistics
    estimated_budget_min: int
    estimated_budget_max: int
    estimated_currency: str = "INR"
    duration_days: int

    # Itinerary skeleton
    itinerary: List[Dict] = []  # [{"day": 1, "location": "Paris", "activities": [...]}]

    # Scoring
    pace: str  # "relaxed", "moderate", "active"
    culture_score: int  # 1-5
    beach_score: int  # 1-5
    adventure_score: int  # 1-5
    kid_friendly_score: int  # 1-5

    # Agent edits
    agent_edited: bool = False
    agent_notes: Optional[str] = None
```

---

## Part 2: Synthetic Message Examples

### Category A: Clean Messages (Easy)

```python
CLEAN_MESSAGES = [
    {
        "category": "clean",
        "difficulty": "easy",
        "message": """
Hi, we want to plan a trip to Thailand for 2 people.
Dates: March 15-22, 2025.
Budget: ₹1.5 lakh.
We like beaches and nightlife.
        """,
        "expected_extraction": {
            "destination": "Thailand",
            "dates": {"start": "2025-03-15", "end": "2025-03-22"},
            "travelers": {"adults": 2, "children": 0},
            "budget": {"min": 150000, "max": 150000},
            "preferences": ["beaches", "nightlife"]
        }
    },
    {
        "category": "clean",
        "difficulty": "easy",
        "message": """
We are a family of 4 (2 adults, 2 kids ages 8 and 12)
wanting to visit Dubai during summer holidays.
Budget around 3 lakhs. We're interested in
theme parks and shopping.
        """,
        "expected_extraction": {
            "destination": "Dubai",
            "dates_hint": "summer holidays",
            "travelers": {"adults": 2, "children": 2, "ages": [8, 12]},
            "budget": {"min": 250000, "max": 350000},
            "preferences": ["theme parks", "shopping"]
        }
    }
]
```

---

### Category B: Moderate Messages (Some ambiguity)

```python
MODERATE_MESSAGES = [
    {
        "category": "moderate",
        "difficulty": "moderate",
        "message": """
Hey, thinking about Europe trip sometime in May or June.
Family of 4, kids are teenagers (14, 16).
Budget is flexible but maybe around 5 lakhs?
We've done Paris before, want something different.
Not too rushed please.
        """,
        "expected_extraction": {
            "destination": "Europe",
            "dates": {"approx": "May-June 2025"},
            "travelers": {"adults": 2, "children": 2, "ages": [14, 16]},
            "budget": {"min": 400000, "max": 600000, "flexible": True},
            "preferences": ["not rushed", "not Paris"],
            "ambiguities": ["specific dates", "specific countries"]
        }
    },
    {
        "category": "moderate",
        "difficulty": "moderate",
        "message": """
Planning honeymoon for October.
Looking at Maldives, Bali, or Thailand.
5-6 nights. Budget not an issue but
want something romantic and private.
Not interested in party places.
        """,
        "expected_extraction": {
            "destinations_options": ["Maldives", "Bali", "Thailand"],
            "dates": {"month": "October", "nights": 5-6},
            "travelers": {"adults": 2, "children": 0, "type": "honeymoon"},
            "budget": {"flexible": True, "high": True},
            "preferences": ["romantic", "private", "not party"],
            "ambiguities": ["which destination"]
        }
    }
]
```

---

### Category C: Messy Messages (Hard)

```python
MESSY_MESSAGES = [
    {
        "category": "messy",
        "difficulty": "hard",
        "message": """
hiiii so me and my friends maybe 4-5 people
were thinking goa but also maybe andaman??
not sure when maybe dec or jan
budget is like 2-3 lakh per person
we want party but also some chill days
some want adventure some just beach
what do u suggest?? also 1 person has
knee issue so cant do much hiking
        """,
        "expected_extraction": {
            "destinations_options": ["Goa", "Andaman"],
            "dates": {"approx": "Dec-Jan"},
            "travelers": {"adults": 4-5, "friends": True},
            "budget": {"per_person": [200000, 300000]},
            "preferences": ["party", "beach", "adventure"],
            "constraints": ["knee issue - no hiking"],
            "contradictions": ["party vs chill", "adventure vs mobility constraint"],
            "ambiguities": ["dates", "destination choice", "group consensus"]
        }
    },
    {
        "category": "messy",
        "difficulty": "hard",
        "message": """
We want to do Europe trip. There's 6 of us -
me, wife, our 2 kids (5 and 9), my parents.
Parents are 65+ so can't walk too much.
We have 10 days in April.
Budget is tricky - maybe 6 lakhs? Can stretch
if needed. We like culture but kids get bored
of museums. Want balance. Oh and my mom
has knee problems. Dad uses walker sometimes.
We've done Switzerland before.
        """,
        "expected_extraction": {
            "destination": "Europe",
            "dates": {"duration_days": 10, "month": "April"},
            "travelers": {
                "adults": 4,
                "children": 2,
                "ages": [5, 9],
                "seniors": 2,
                "senior_ages": [65, 65],
                "mobility": ["knee problems", "walker"]
            },
            "budget": {"min": 550000, "max": 700000, "flexible": True},
            "preferences": ["culture", "kid-friendly"],
            "constraints": ["limited walking", "not Switzerland"],
            "blockers": ["high walking destinations"],
            "feasibility_concerns": ["budget may be tight for 6 people Europe", "mobility constraints"]
        }
    }
]
```

---

### Category D: Contradictory Messages

```python
CONTRADICTORY_MESSAGES = [
    {
        "category": "contradictory",
        "difficulty": "hard",
        "message": """
We want a budget Europe trip, around 1 lakh total
for 4 people for 10 days. But we want to visit
3 countries and stay in 4-star hotels.
Also want private tours everywhere.
        """,
        "expected_extraction": {
            "destination": "Europe (multiple countries)",
            "travelers": {"adults": 4},
            "budget": {"total": 100000, "per_person": 25000},
            "preferences": ["3 countries", "4-star hotels", "private tours"],
            "contradictions": [
                "Budget ₹1L for 4 people Europe = impossible",
                "4-star + private tours incompatible with budget"
            ],
            "feasibility": "IMPOSSIBLE as stated",
            "blockers": ["budget"]
        }
    },
    {
        "category": "contradictory",
        "difficulty": "hard",
        "message": """
Planning a solo trip to Leh-Ladakh for 2 days in January.
Want to see Pangong Lake and Nubra Valley.
Budget is ₹30,000 including flights.
        """,
        "expected_extraction": {
            "destination": "Leh-Ladakh",
            "dates": {"month": "January", "duration_days": 2},
            "travelers": {"adults": 1},
            "budget": {"total": 30000, "includes_flights": True},
            "preferences": ["Pangong Lake", "Nubra Valley"],
            "contradictions": [
                "January = many roads closed",
                "2 days = insufficient for Pangong + Nubra",
                "₹30K including flights may be tight"
            ],
            "feasibility": "HIGHLY PROBLEMATIC",
            "blockers": ["season", "duration"]
        }
    }
]
```

---

### Category E: Edge Cases

```python
EDGE_CASE_MESSAGES = [
    {
        "category": "edge_case",
        "type": "very_vague",
        "message": "I want to go somewhere nice.",
        "expected_extraction": {
            "destination": None,
            "preferences": ["somewhere nice"],
            "ambiguities": ["everything"],
            "feasibility": "INSUFFICIENT_INFO"
        }
    },
    {
        "category": "edge_case",
        "type": "overspecified",
        "message": """
I want to visit Paris. Exact dates: June 15, 2025 to June 22, 2025.
Exact hotels: Hotel Fabric for 3 nights, Hotel Henriette for 4 nights.
Exact restaurants: Le Comptoir, Cafe de Flore, L'As du Fallafel.
Exact museums: Louvre (Monday 9 AM), Musee d'Orsay (Wednesday 2 PM).
Exact budget: ₹2,34,567. I need exact flight timings too.
        """,
        "expected_extraction": {
            "destination": "Paris",
            "dates": {"exact": "2025-06-15 to 2025-06-22"},
            "preferences": ["very specific itinerary"],
            "overspecified": True,
            "feasibility": "FEASIBLE but agent should confirm availability"
        }
    },
    {
        "category": "edge_case",
        "type": "large_group",
        "message": """
Planning a family reunion trip. About 40-50 people.
Multi-generational from ages 3 to 85.
Some in wheelchairs. Budget around ₹15 lakh.
We're thinking Thailand but open.
        """,
        "expected_extraction": {
            "destination": "Thailand (preferred)",
            "travelers": {"count": 40-50, "ages": "3-85", "mobility": ["wheelchairs"]},
            "budget": {"total": 1500000},
            "feasibility_concerns": ["large group logistics", "mobility", "budget per person"],
            "blockers": ["logistics complexity"]
        }
    },
    {
        "category": "edge_case",
        "type": "multi_trip",
        "message": """
We want to do Europe in June and Japan in October.
Same group of 4 people. Budget 10 lakhs for both combined.
Is this possible?
        """,
        "expected_extraction": {
            "destinations": ["Europe", "Japan"],
            "dates": [{"month": "June"}, {"month": "October"}],
            "travelers": {"adults": 4},
            "budget": {"total": 1000000, "for": "both trips"},
            "feasibility_concerns": ["budget for 2 international trips"]
        }
    }
]
```

---

## Part 3: Fixture Data for Testing

### Complete Trip Fixture

```python
COMPLETE_TRIP_FIXTURE = {
    "trip": {
        "id": "trip_sharma_europe_001",
        "agency_id": "agency_priya_travels",
        "agent_id": "agent_priya_001",
        "status": "options_generated",
        "client_name": "Raj Sharma",
        "client_email": "raj.sharma@email.com",
        "client_whatsapp": "+91 98765 43210",
        "destination": "Europe",
        "destinations_list": ["France", "Italy"],
        "start_date": "2025-06-15",
        "end_date": "2025-06-25",
        "duration_days": 10,
        "travelers_count_adults": 2,
        "travelers_count_children": 2,
        "travelers_ages": [7, 10],
        "budget_min": 350000,
        "budget_max": 400000,
        "budget_currency": "INR",
        "preferences": ["culture", "beaches", "family-friendly", "moderate pace"],
        "avoid_list": ["too much walking", "early morning starts"],
        "source_channel": "whatsapp",
        "raw_input": "Hi Priya, we want to go to Europe...",
        "extracted_constraints": {
            "season": "peak",
            "budget_tightness": "medium",
            "mobility_constraints": "moderate",
            "age_appropriateness": "kids 7-10"
        },
        "contradictions": [],
        "blockers": [],
        "feasibility_verdict": "FEASIBLE",
        "confidence_score": 0.85
    },
    "options": [
        {
            "id": "option_001",
            "name": "France Focus",
            "description": "Classic Europe with Paris and French Riviera",
            "destinations": ["France"],
            "why_this_fits": "Perfect first Europe trip, kid-friendly, good balance",
            "trade_offs": ["Less beach time", "Peak season pricing"],
            "estimated_budget_min": 400000,
            "estimated_budget_max": 420000,
            "pace": "moderate",
            "culture_score": 5,
            "beach_score": 3,
            "kid_friendly_score": 5,
            "itinerary": [
                {"day": 1, "location": "Paris", "activities": ["Arrival", "Eiffel Tower"]},
                {"day": 2, "location": "Paris", "activities": ["Louvre", "Seine cruise"]},
                {"day": 3, "location": "Paris", "activities": ["Disneyland day trip"]},
                {"day": 4, "location": "Lyon", "activities": ["City tour", "Food tour"]},
                {"day": 5, "location": "Lyon", "activities": ["Local markets"]},
                {"day": 6, "location": "Nice", "activities": ["Promenade des Anglais"]},
                {"day": 7, "location": "Nice", "activities": ["Old Town", "Beach"]},
                {"day": 8, "location": "Nice", "activities": ["Monaco day trip"]},
                {"day": 9, "location": "Nice", "activities": ["Beach day"]},
                {"day": 10, "location": "Nice", "activities": ["Departure"]}
            ]
        },
        {
            "id": "option_002",
            "name": "Italy Focus",
            "description": "Culture and coast with Rome and Amalfi",
            "destinations": ["Italy"],
            "why_this_fits": "Best culture+beach combo, under budget",
            "trade_offs": ["More walking", "Hilly terrain in Amalfi"],
            "estimated_budget_min": 360000,
            "estimated_budget_max": 380000,
            "pace": "moderate_to_active",
            "culture_score": 5,
            "beach_score": 4,
            "kid_friendly_score": 4,
            "itinerary": [
                {"day": 1, "location": "Rome", "activities": ["Arrival", "Colosseum area"]},
                {"day": 2, "location": "Rome", "activities": ["Vatican", "St. Peter's"]},
                {"day": 3, "location": "Rome", "activities": ["Pantheon", "Trevi Fountain"]},
                {"day": 4, "location": "Rome", "activities": ["Food tour", "Spanish Steps"]},
                {"day": 5, "location": "Florence", "activities": ["Train to Florence", "Duomo"]},
                {"day": 6, "location": "Florence", "activities": ["Uffizi", "Ponte Vecchio"]},
                {"day": 7, "location": "Florence", "activities": ["Pisa day trip"]},
                {"day": 8, "location": "Amalfi", "activities": ["Drive to Amalfi", "Positano"]},
                {"day": 9, "location": "Amalfi", "activities": ["Boat trip", "Beach"]},
                {"day": 10, "location": "Amalfi", "activities": ["Departure from Naples"]}
            ]
        },
        {
            "id": "option_003",
            "name": "Greece Focus",
            "description": "Islands and history with Athens and Santorini",
            "destinations": ["Greece"],
            "why_this_fits": "Best value, relaxed pace, less crowded",
            "trade_offs": ["Less 'classic Europe'", "More travel time between islands"],
            "estimated_budget_min": 330000,
            "estimated_budget_max": 350000,
            "pace": "relaxed",
            "culture_score": 3,
            "beach_score": 5,
            "kid_friendly_score": 5,
            "itinerary": [
                {"day": 1, "location": "Athens", "activities": ["Arrival", "Plaka"]},
                {"day": 2, "location": "Athens", "activities": ["Acropolis", "Acropolis Museum"]},
                {"day": 3, "location": "Athens", "activities": ["Delphi day trip"]},
                {"day": 4, "location": "Naxos", "activities": ["Ferry to Naxos", "Beach"]},
                {"day": 5, "location": "Naxos", "activities": ["Village tour", "Beach day"]},
                {"day": 6, "location": "Naxos", "activities": ["Local cooking class"]},
                {"day": 7, "location": "Santorini", "activities": ["Ferry to Santorini", "Oia sunset"]},
                {"day": 8, "location": "Santorini", "activities": ["Beach", "Boat trip"]},
                {"day": 9, "location": "Santorini", "activities": ["Volcano tour", "Fira"]},
                {"day": 10, "location": "Santorini", "activities": ["Departure"]}
            ]
        }
    ]
}
```

---

## Part 4: Generator Functions

### Random Message Generator

```python
import random
from typing import Dict, List

DESTINATIONS = [
    "Thailand", "Dubai", "Europe", "Singapore", "Malaysia",
    "Maldives", "Bali", "Japan", "Vietnam", "Sri Lanka",
    "Goa", "Rajasthan", "Kerala", "Andaman", "Ladakh"
]

PREFERENCES = [
    "beaches", "culture", "nightlife", "adventure", "food",
    "history", "nature", "shopping", "relaxation", "romantic"
]

TRIP_TYPES = ["family", "honeymoon", "friends", "solo", "group"]

def generate_random_message() -> Dict:
    """Generate a random but realistic trip inquiry message."""

    # Random parameters
    destination = random.choice(DESTINATIONS)
    trip_type = random.choice(TRIP_TYPES)
    num_people = random.randint(1, 6)
    budget_range = random.choice([
        (50000, 100000), (100000, 200000), (200000, 500000),
        (500000, 1000000)
    ])

    # Build message based on trip type
    if trip_type == "family":
        message = f"""Hi, we're a family of {num_people} planning a trip to {destination}.
Our budget is around {budget_range[0]//1000}-{budget_range[1]//1000}K.
We like {random.sample(PREFERENCES, 2)}."""
    elif trip_type == "honeymoon":
        message = f"""Planning honeymoon for {random.choice(['October', 'November', 'December'])}.
Looking at {destination} or {random.choice(DESTINATIONS)}.
Budget is flexible, want something romantic and private."""
    elif trip_type == "friends":
        message = f"""Me and {num_people-1} friends planning a trip to {destination}.
{random.choice(['March', 'April', 'May'])} maybe.
Budget around {budget_range[0]//1000}K per person.
We want {random.sample(PREFERENCES, 3)}."""
    else:
        message = f"""I want to go to {destination} for {random.randint(3, 10)} days.
Budget is around {budget_range[0]//1000}-{budget_range[1]//1000}K.
Interested in {random.sample(PREFERENCES, 2)}."""

    return {
        "message": message,
        "destination": destination,
        "trip_type": trip_type,
        "num_people": num_people,
        "budget": budget_range,
        "category": random.choice(["clean", "moderate", "messy"])
    }

def generate_edge_case(case_type: str) -> Dict:
    """Generate specific edge case messages."""

    edge_cases = {
        "very_vague": "I want to go somewhere nice.",
        "no_budget": "We want to do Europe. 4 people. 10 days. No budget in mind.",
        "impossible_dates": "Want to visit Leh in July for 2 days. Budget 20k.",
        "overspecified": "I want Paris, exact dates June 1-7, Hotel X, Restaurant Y...",
        "large_group": "50 people family reunion. Multi-generational. Budget 10L.",
        "contradictory": "Europe trip, 1L budget for 4 people, 5-star, private tours."
    }

    return {
        "type": case_type,
        "message": edge_cases.get(case_type, "Unknown edge case"),
        "category": "edge_case"
    }
```

---

### Random Trip Generator

```python
from datetime import datetime, timedelta
import random

def generate_random_trip(agency_id: str, agent_id: str) -> Dict:
    """Generate a complete random trip record."""

    statuses = ["new", "intake", "questions_sent", "brief_complete",
                "options_generated", "sent_to_client", "booked"]

    trip = {
        "id": f"trip_{random.randint(10000, 99999)}",
        "agency_id": agency_id,
        "agent_id": agent_id,
        "status": random.choice(statuses),
        "client_name": f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=1))}{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))} {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=1))}{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=4))}",
        "client_email": f"{random.choice(['priya', 'raj', 'amit', 'neha', 'rahul'])}{random.randint(1, 999)}@email.com",
        "destination": random.choice(DESTINATIONS),
        "travelers_count_adults": random.randint(1, 4),
        "travelers_count_children": random.randint(0, 3),
        "budget_min": random.randint(50000, 300000),
        "budget_max": random.randint(100000, 500000),
        "source_channel": random.choice(["whatsapp", "email", "phone", "in_person"]),
        "created_at": datetime.now() - timedelta(days=random.randint(0, 30)),
        "confidence_score": round(random.uniform(0.5, 1.0), 2)
    }

    if trip["travelers_count_children"] > 0:
        trip["travelers_ages"] = [random.randint(3, 15) for _ in range(trip["travelers_count_children"])]

    return trip
```

---

## Part 5: Test Data Sets

### Set 1: Regression Testing (Predictable)

```python
REGRESSION_TEST_SET = [
    {
        "name": "Simple Thailand Query",
        "input": "Thailand trip for 2 people in March. Budget 1.5L. Like beaches.",
        "expected": {
            "destination": "Thailand",
            "dates_approx": "March",
            "travelers": 2,
            "budget": 150000,
            "feasibility": "FEASIBLE"
        }
    },
    {
        "name": "Europe Family with Constraints",
        "input": "Europe trip, family of 4, June. Elderly parents with mobility issues.",
        "expected": {
            "destination": "Europe",
            "dates_approx": "June",
            "travelers": 4,
            "constraints": ["mobility_issues", "elderly"],
            "feasibility_concerns": ["mobility"]
        }
    },
    {
        "name": "Budget Mismatch",
        "input": "Europe 4 people 10 days budget 1 lakh",
        "expected": {
            "destination": "Europe",
            "feasibility": "PROBLEMATIC",
            "blockers": ["budget"]
        }
    }
]
```

---

### Set 2: Quality Testing (Varied)

```python
QUALITY_TEST_SET = [
    {
        "name": "Multi-country ambiguity",
        "input": "Want to do France-Italy-Switzerland in 7 days. Budget 3L for 2 people.",
        "quality_check": "Should flag as too rushed"
    },
    {
        "name": "Seasonal awareness",
        "input": "Planning Leh Ladakh in January for family with kids.",
        "quality_check": "Should flag winter closure risk"
    },
    {
        "name": "Budget realism",
        "input": "Maldives 5-star resort for week, budget 50k for couple.",
        "quality_check": "Should flag budget mismatch"
    }
]
```

---

## Summary

**For development**: Use synthetic data to test extraction, feasibility checks, and option generation

**For testing**: Create predictable test sets for regression testing

**For edge cases**: Comprehensive collection of messy, contradictory, and edge case messages

**For demos**: Clean, realistic examples that show the product well

**Key files**:
- Schemas: Define data structures
- Fixtures: Complete example records
- Generators: Create unlimited test data
- Test sets: Validate specific behaviors
