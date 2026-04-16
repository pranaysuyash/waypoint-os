# Activity Suitability Matrix - Web Research Findings

**Date:** 2026-04-16
**Product:** Product B (GTM audit/lead-gen)
**Purpose:** Identify existing APIs and datasets for age-based activity suitability scoring

---

## Executive Summary

No single mainstream API provides a ready-made "age suitability score." Best practice is to derive scores from structured fields across multiple sources.

**Key Finding:** OTAs provide rich age and accessibility signals, but they must be combined and normalized into a composite suitability score.

---

## 1. Activity Database/APIs with Age Suitability Signals

### Primary Source: Viator Partner API

**Strengths:**
- Richest explicit age modeling
- Fields: `ageFrom`, `ageTo`, traveler mix constraints, adult-required flags
- Includes booking constraints + policy data
- Production-ready (not beta)

**Use Case:** Primary source for age-based suitability logic

**Data Signals:**
```
- age_bands: infant, child, teen, adult, senior
- ageFrom/ageTo: explicit min/max ages
- requires_adult: boolean flag
- traveler_mix: composition constraints
- cancellation_policy: flexibility data
```

---

### Secondary Source: Booking.com Demand API v3.2 Beta

**Endpoints:**
- `POST /attractions/search`
- `POST /attractions/details`
- `POST /attractions/reviews`
- `POST /attractions/reviews/scores`

**Strengths:**
- OTA-grade activity inventory
- Review/scores overlay capability

**Caveats:**
- **Beta status**: Schema and behavior may change
- Age scoring less explicit than Viator
- Details endpoint does not include pricing

**Use Case:** Commercial inventory breadth + review sentiment overlay

---

### Secondary Source: Klook API (OCTO-style)

**Strengths:**
- Unit-level restrictions: `minAge`, `maxAge`
- Quantity limits
- `accompanied-by` constraints

**Caveats:**
- Requires partner access
- Documentation availability varies by region

**Use Case:** Secondary age-signal source where partner access exists

---

### Secondary Source: Musement Partner API

**Strengths:**
- Ticket-holder normalization: `ADULT`, `CHILDREN`, `INFANT`, `SENIOR`, `FAMILY`
- Name field includes age ranges (e.g., "child 3-17")
- Restrictions embedded in ticket definitions

**Use Case:** Age-band normalization and labeling

---

## 2. OTA Activity Data Structure Patterns

**Common Pattern Across All OTAs:**

1. **Search endpoint** - Geo/city/country/IDs + date range + currency + pagination
2. **Details endpoint** - Static content: name, description, media, language
3. **Reviews endpoint** - User sentiment/rating stream
4. **Booking flow** - Availability, restrictions, pricing/cancellation

**Concrete Signals:**
- Query by location IDs or coordinates
- Date windows (start_date, end_date)
- Currency and localization in request
- Pagination token model (next_page)
- Separate review/scores endpoints
- Static details distinct from pricing (Booking.com pattern)

---

## 3. Family Travel + Elderly/Disability Resources

### Sentiment Layer: Tripadvisor Content API

**Endpoints:**
- Location details/search
- Reviews
- Photos

**Strengths:**
- Review segmentation signals (including family trip types)
- Large review volume for sentiment proxy

**Caveats:**
- Not a direct age suitability score
- Must derive family affinity from review metadata

**Use Case:** Family/review sentiment proxy

---

### Mobility Layer: Wheelmap

**What it is:**
- Community accessibility map built on OpenStreetMap
- Traffic-light wheelchair status: yes/limited/no

**Use Case:** Elderly/mobility suitability overlay

**Data Model:**
```
- wheelchair_accessibility: fully/partially/not wheelchair_accessible
- step_free_access: boolean
- toilet_access: boolean
```

---

### Accessibility Layer: Euan's Guide

**What it is:**
- Review platform focused on disabled access
- Venue-level accessibility context + user reviews

**Use Case:** Qualitative accessibility layer for inclusive travel

---

## 4. Recommended Provider Stack

| Layer | Provider | Priority | Notes |
|-------|----------|----------|-------|
| **Age Suitability** | Viator | Primary | Rich explicit age modeling |
| **Age Signals** | Klook/Musement | Secondary | Where partner access exists |
| **Inventory** | Booking Attractions | Tertiary | Beta caveat, good breadth |
| **Sentiment** | Tripadvisor | Overlay | Family proxy via reviews |
| **Mobility** | Wheelmap | Overlay | OSM-based wheelchair data |
| **Accessibility** | Euan's Guide | Overlay | Disabled access reviews |

---

## 5. Normalized Schema for Suitability Matrix

**Canonical Internal Model:**

```json
{
  "activity_id": "string",
  "source": "viator|booking|klook|musement",
  "source_activity_id": "string",
  "title": "string",
  "category": "string",
  "location": {"lat": float, "lon": float, "city": "string"},
  "duration_minutes": integer,

  // Age signals
  "age_min": integer,
  "age_max": integer,
  "age_band_labels": ["infant", "child", "teen", "adult", "senior"],
  "requires_adult": boolean,
  "group_constraints": {
    "min_pax": integer,
    "max_pax": integer,
    "child_adult_ratio": "string"
  },

  // Mobility signals
  "mobility_access": {
    "wheelchair": "yes|limited|no|unknown",
    "step_free": boolean,
    "toilet_access": boolean
  },

  // Intensity signals
  "intensity_level": "low|medium|high",

  // Policy signals
  "cancellation_flexibility": {
    "free_cancel_window_hours": integer,
    "refund_type": "string"
  },

  // Language
  "language_options": ["string"],

  // Sentiment signals
  "family_signal_score": float,
  "review_score": float,
  "review_count": integer,

  // Pricing
  "price_min": float,
  "currency": "string",

  // Meta
  "confidence_score": float,
  "last_updated": "ISO8601"
}
```

---

## 6. Derived Score Formula

**First-pass scoring approach:**

```
suitability_score = 0.35*A + 0.20*M + 0.15*D + 0.15*C + 0.15*R
```

Where:
- **(A)** age-fit score: explicit min/max + adult requirement
- **(M)** mobility/accessibility score: wheelchair, step-free
- **(D)** duration/intensity fit: activity intensity level
- **(C)** cancellation flexibility: free cancellation window
- **(R)** family/review sentiment proxy: family-tagged reviews

---

## 7. Source Confidence Table

| Source | Confidence | Reasoning |
|--------|------------|-----------|
| Viator | High | Production API, rich age signals |
| Wheelmap | High | Community-validated, OSM-based |
| Klook | Medium | Partner access dependent |
| Musement | Medium | Good age bands, less inventory |
| Booking Attractions | Medium | Beta status, schema flux risk |
| Tripadvisor | Medium | Review proxy, not direct scores |
| Euan's Guide | Medium | Niche but high-quality accessibility |

---

## 8. Caveats for Product/GTM

1. **Booking Attractions v3.2-beta**: Schema and behavior may change
2. **Tripadvisor docs split**: Older location docs show rich examples; current content API is operational source
3. **No universal score**: No provider gives "kid-safe/elderly-safe score" out-of-box—must be computed
4. **MakeMyTrip**: Structured API evidence weak publicly (likely private partner channels)

---

## 9. Source Appendix URLs

- Viator Partner API: Partner portal documentation
- Booking.com Demand API: Developer portal (beta section)
- Klook API: Partner documentation (region-specific)
- Musement: Partner API documentation
- Tripadvisor Content API: Content API docs
- Wheelmap: https://wheelmap.org/
- Euan's Guide: https://www.euansguide.com/

---

## Next Steps

1. Ingest Viator age signals as primary backbone
2. Map Wheelmap wheelchair data to locations
3. Derive first-pass suitability scores using formula
4. Validate with manual review of edge cases
5. Expand to secondary sources (Klook/Musement) based on coverage gaps
