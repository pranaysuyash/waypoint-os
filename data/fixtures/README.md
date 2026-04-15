# Fixture Files Documentation

**Date**: 2026-04-15
**Purpose**: Documentation for synthetic data fixtures and datasets in `data/`

---

## Overview

Fixture files provide sample/test data for development, testing, and demonstration. They are designed to be realistic representations of actual user interactions while maintaining privacy.

---

## Directory Structure

```
data/
├── fixtures/           # Test fixtures for PM/UX scenarios and test messages
├── cities.json         # world-cities.json dataset (MIT license)
├── cities5000.txt      # GeoNames dataset (CC-BY 4.0 license)
└── accumulated_cities.json # Organically added cities from user messages
```

---

## Geography Datasets

### cities5000.txt (GeoNames)

**Source**: https://download.geonames.org/export/dump/
**License**: CC-BY 4.0 (attribution required)
**Size**: ~68,000 cities (population > 5000)
**Format**: Tab-separated values

**Fields**: geonameid, name, asciiname, alternatenames, feature class, feature code,
country code, cc2, admin1, admin2, admin3, admin4, admin5, population, elevation, dem, timezone

**Usage**: Primary city database for origin/destination extraction in `src/intake/geography.py`

**Attribution**: Any UI using this data must include:

```html
Location data © <a href="https://www.geonames.org/">GeoNames</a>
```

---

### cities.json (world-cities.json)

**Source**: https://github.com/dr5hn/countries-states-cities-database
**License**: ODbL-1.0 (Open Database License) — share-alike obligations apply
**Size**: ~150,000 cities
**Format**: JSON array

**Usage**: Supplemental city database, fills gaps in GeoNames coverage

**⚠️ License Note**: This dataset is ODbL-1.0, not MIT as previously documented.
ODbL-1.0 requires share-alike for derivative databases, which conflicts with proprietary licensing.
If proprietary licensing is required, replace with an MIT/CC0-licensed alternative.

---

### accumulated_cities.json

**Purpose**: Organic accumulation of cities seen in real user messages
**License**: Project license
**Format**: JSON array of city names (strings)
**Initial state**: Empty array `[]`

**How cities are added**:

- Confidence score > 0.7 (reasonably sure it's a city)
- Not already in baseline datasets
- Not a blacklisted term (common travel words)
- Added via `record_seen_city()` in `src/intake/geography.py`

---

## Fixture Files

### 1. `product_persona_flows_synthetic_v1.json`

**Purpose**: PM/UX scenarios for role-based journeys

**Coverage**:

- 4 personas: Agency Owner, Senior Agent, Junior Agent, End Traveler
- Jobs to be Done (functional, emotional, social)
- Aha moments and metric proxies
- End-to-end flow steps
- Product flywheel instrumentation
- Open PM questions

**Use cases**:

- Acceptance criteria planning
- Scenario-driven QA and rehearsals
- PM prioritization workshops
- User journey documentation

---

### 2. `test_messages.json`

**Purpose**: Test messages for intake processing, extraction, and feasibility testing

**Categories**:

- **Clean** (5 examples): Clear, well-formed inquiries
- **Moderate** (5 examples): Some ambiguity but workable
- **Messy** (5 examples): Poorly structured, informal
- **Contradictory** (5 examples): Incompatible requirements
- **Edge Cases** (10 examples): Unusual or boundary-pushing requests

**Total**: 30 test messages covering all categories

**Use cases**:

- Testing intake extraction
- Validating feasibility detection
- Testing contradiction identification
- Edge case coverage
- Demo scenarios

**Example categories**:

| Category      | Count | Difficulty |
| ------------- | ----- | ---------- |
| Clean         | 5     | Easy       |
| Moderate      | 5     | Medium     |
| Messy         | 5     | Hard       |
| Contradictory | 5     | Hard       |
| Edge Cases    | 10    | Varies     |

---

### 3. `trip_examples.json`

**Purpose**: Complete trip examples for development and demo purposes

**Trips included**:

1. **Sharma Family Europe** - Successful moderate complexity flow
2. **Mehta Thailand** - Clean, straightforward booking
3. **Patel Honeymoon Maldives** - High-value options selection
4. **Gupta Family Reunion Europe** - Contradictory requirements (educational)
5. **Impossible Ladakh** - Seasonal/Duration impossibilities (educational)
6. **Last Minute Getaway** - Time/cost constrained options

**Each trip contains**:

- Client information
- Raw input message
- Extracted data
- Processing results (confidence, flags, contradictions, feasibility)
- Generated options with itineraries
- Outcome data

**Use cases**:

- End-to-end flow testing
- Demo scenarios
- API response examples
- Acceptance criteria validation

---

## Usage Examples

### For Testing Intake Extraction

```python
import json

with open('data/fixtures/test_messages.json') as f:
    data = json.load(f)

# Get a clean message
msg = data['messages']['clean'][0]['input']
assert msg['id'] == 'msg_clean_001'
assert 'Thailand' in msg['input']
assert msg['expected_extraction']['feasibility'] == 'FEASIBLE'
```

### For Testing Feasibility Detection

```python
# Test contradictory message
msg = data['messages']['contradictory'][0]
assert msg['id'] == 'msg_contra_001'
assert msg['expected_extraction']['feasibility'] == 'IMPOSSIBLE as stated'
assert len(msg['expected_extraction']['contradictions']) > 0
```

### For Demo Purposes

```python
# Load complete trip example
with open('data/fixtures/trip_examples.json') as f:
    data = json.load(f)

trip = data['trips']['sharma_family_europe']
print(f"Client: {trip['client']['name']}")
print(f"Destination: {trip['extracted']['destinations_list']}")
print(f"Budget: ₹{trip['extracted']['budget']['min']:,} - ₹{trip['extracted']['budget']['max']:,}")
print(f"Options: {len(trip['options'])} options generated")
```

---

## Data Structure

### Persona Structure

```json
{
  "persona_id": "string",
  "role": "senior_agent | junior_agent | agency_owner | traveler",
  "primary_outcome": "string",
  "jobs_to_be_done": {
    "functional": ["array of jobs"],
    "emotional": ["array of feelings"],
    "social": ["array of perceptions"]
  },
  "aha_moment": "string describing the aha moment",
  "metric_proxies": {
    "leading": ["metrics to watch"],
    "lagging": ["outcomes to measure"]
  }
}
```

### Message Structure

```json
{
  "id": "msg_category_###",
  "category": "clean | moderate | messy | contradictory | edge_case",
  "input": "raw message text",
  "expected_extraction": {
    "destination": "string or array",
    "dates": "object",
    "travelers": "object",
    "budget": "object",
    "feasibility": "string verdict"
  }
}
```

### Trip Structure

```json
{
  "id": "trip_###",
  "client": {
    "name": "string",
    "email": "string",
    "phone": "string"
  },
  "input": {
    "channel": "whatsapp | email | phone | in_person",
    "raw_message": "string",
    "received_at": "ISO timestamp"
  },
  "extracted": {
    "destination": "string",
    "dates": "object",
    "travelers": "object",
    "budget": "object",
    "preferences": ["array"]
  },
  "processing": {
    "confidence_score": "0-1",
    "flags": ["array"],
    "contradictions": ["array"],
    "feasibility": "string verdict"
  },
  "options": ["array of option objects"],
  "outcome": {
    "selected": "option_id",
    "booking_status": "string"
  }
}
```

---

## Maintenance

### Adding New Test Messages

1. Choose appropriate category
2. Assign unique ID: `msg_category_###`
3. Include raw input
4. Document expected extraction
5. Add `expected_extraction` with all fields
6. Consider edge cases and contradictions

### Updating Personas

When updating personas:

1. Update `product_persona_flows_synthetic_v1.json`
2. Add new persona or update existing
3. Include JTBD for all three dimensions
4. Document aha moment with trigger
5. Add metric proxies
6. Include open PM questions

---

## Versioning

Fixtures follow semantic versioning:

- **Major version** (1.x → 2.x): Breaking changes to schema
- **Minor version** (1.0 → 1.1): Additions compatible with existing
- **Patch version** (1.0.0 → 1.0.1): Bug fixes, documentation updates

---

## Notes

- All personal data in fixtures is fictional
- Phone numbers, emails are not real
- Budgets are in INR (₹) unless specified
- Dates are examples; update current year as needed
- Destinations and scenarios are realistic but not based on actual clients
