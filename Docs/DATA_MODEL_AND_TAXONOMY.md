# Data Model and Taxonomy: Detailed Catalog

## 1. Traveler Classification (The "Brackets")
The system assigns travelers into categories to drive routing and recommendation logic.

### A. Group Composition Brackets
- `solo`
- `couple`
- `friends`
- `family_with_toddler` (Triggers nap-time and stroller-access checks)
- `family_with_elderly` (Triggers mobility and accessibility checks)
- `mixed_group` (High complexity, requires per-person utility analysis)

### B. Budget Brackets
- `lean`: Value-driven, budget maximization.
- `mid`: Balance of comfort and cost.
- `premium`: High comfort, a few luxury splurges.
- `luxury`: Top-tier, exclusive, no-compromise.

### C. Intent/Vibe Brackets
- `sightseeing-first`: Maximizing landmarks.
- `shopping-first`: Focus on markets, brands, and logistics for shopping.
- `food-first`: Culinary discovery, fine dining, street food.
- `luxury-rest`: Slow travel, resorts, minimal movement.
- `activity-heavy`: Adventure, high-energy, high-effort.

### D. Planning Route Brackets
- `package_suitable`: Standard needs, fits existing bundles.
- `custom_supplier`: Special needs, uses preferred network.
- `network_assisted`: Complex needs, requires larger agency consortium.
- `open_market`: Niche requests, requires wide-web search.

---

## 2. The Budget Decomposition Model
A "Total Budget" is a lie. The system breaks it into functional buckets:
- **Flights**: International and internal.
- **Stay**: Hotels, villas, resorts.
- **Food**: Daily meals, fine dining, snacks.
- **Activities**: Entry fees, guides, experiences.
- **Local Transport**: Airport transfers, daily cabs, rail.
- **Shopping**: Explicitly tracked as a separate intent.
- **Buffer**: Insurance, visa, emergency.

---

## 3. Sourcing Hierarchy Entities
### A. Hotel Partner Profile
- **Basics**: Name, Destination, Area, Star Category.
- **Suitability**: `toddler_friendly`, `elderly_friendly`, `honeymoon_suitable`.
- **Commercials**: Commission band, Net cost, Markup potential.
- **Agency Notes**: "Rooms are tiny but breakfast is great," "Fast WhatsApp response."

### B. Internal Package
- **Template**: Fixed sequence of days and activities.
- **Flexibility**: Which parts are "hard" and which are "soft" for personalization.
- **Conversion Rate**: Historical success of this package.

---

## 4. Activity Utility Model
Activities are not just "liked" or "disliked"; they are scored by **Utility**.

**Utility Score Calculation:**
$\text{Final Score} = \text{Interest Fit} - (\text{Effort} + \text{Crowd Risk} + \text{Cost})$

**Per-Person Suitability Check:**
For every expensive activity, the system checks:
- `adult_usability`: High/Med/Low.
- `elderly_usability`: High/Med/Low.
- `toddler_usability`: High/Med/Low.
- **Wasted Spend Flag**: Triggered if $\text{Total Tickets Bought} > \text{Total High-Utility Users}$.

---

## 5. Canonical State Model (The Truth)
To prevent "hallucinated planning," the system maintains a strict separation of data types:

1. **Facts**: Explicitly stated by the agency or traveler (e.g., "Budget: 2.5L").
2. **Derived Signals**: Local, high-confidence implications (e.g., "Toddler present" $\rightarrow$ "Needs nap-time logistics").
3. **Hypotheses**: Soft, low-authority profiles (e.g., "Likely a comfort-first family").
4. **Unknowns/Conflicts**: Missing blocking fields or contradictions.

**JSON Schema:**
```json
{
  "trip_brief": {
    "departure_city": {"value": "...", "confidence": 0.9, "source": "explicit"},
    "destination_status": "open | fixed | semi-open",
    "candidate_destinations": [],
    "date_window": "...",
    "duration_nights": 0,
    "pace_preference": "relaxed | balanced | packed",
    "food_preferences": [],
    "shopping_intent": "low | med | high",
    "must_haves": [],
    "hard_nos": []
  },
  "traveler_profile": {
    "members": [
      {"type": "adult", "count": 0, "constraints": []},
      {"type": "elderly", "count": 0, "constraints": []},
      {"type": "toddler", "count": 0, "constraints": []}
    ],
    "classes": ["family_with_toddler", "shopping_first"]
  },
  "budget": {
    "total": 0,
    "currency": "INR",
    "splits": {
      "stay": 0,
      "activities": 0,
      "food": 0,
      "shopping": 0,
      "transport": 0,
      "buffer": 0
    }
  },
  "derived_signals": [
    {"signal": "nap_sensitivity", "reason": "toddler_present", "confidence": 0.95}
  ],
  "hypotheses": [
    {"label": "comfort_first", "reason": "elderly+toddler+relaxed_pace", "confidence": 0.7}
  ],
  "risk_flags": ["theme_park_waste_risk", "mobility_issue_detected"],
  "contradictions": [],
  "assumptions": []
}
```
