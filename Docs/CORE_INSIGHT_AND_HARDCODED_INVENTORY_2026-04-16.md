# Core Insight & Hardcoded Values Inventory

**Date**: 2026-04-16
**Focus**: Strategic positioning analysis and technical debt audit

---

## Part 1: Refined Core Insight

### The Product Strategy (User Clarification)

| Dimension | Product A | Product B |
|-----------|-----------|-----------|
| **Role** | What you SELL | How you GET customers |
| **Type** | B2B SaaS | GTM / Lead-gen |
| **Name** | Intake Copilot | Free Audit Intelligence |
| **Value** | Workflow compression for agencies | Convert leads by auditing their quotes |
| **Status** | ✅ 70% implemented | 🔴 10% implemented |

### The Flywheel (As Intended)

```
[Traveler has a quote from elsewhere]
           ↓
[Upload to Waypoint Audit Engine] ← Product B (GTM)
           ↓
[Audit Report: Wasted Spend, Fit Issues, Risks]
           ↓
[Click: "Have an agency fix this"]
           ↓
[Agency uses Waypoint Copilot] ← Product A (B2B)
           ↓
[Better quote, faster]
           ↓
[Happy customer, agency revenue]
```

**Current Reality**: The flywheel is broken at step 2. Product B doesn't function.

### Why This Matters

- **Product A alone** = One of many CRM tools, weak differentiation
- **Product B + Product A** = Unique acquisition channel + retention tool
- **Without Product B**, you're competing on features, not on a unique wedge

---

## Part 2: Complete Hardcoded Values Inventory

### Category 1: Destination-Based Logic

#### Elderly Mobility Risk
**File**: `src/intake/decision.py:1052`
```python
risky_dests = {"Maldives", "Andaman", "Andamans", "Bhutan", "Nepal"}
```
**Issues**:
- Why these 5? What makes Bhutan risky but not Switzerland (mountains)?
- No data backing — just "seems right"
- Doesn't account for elderly fitness level (active 70yo vs frail 75yo)

**Should Be**:
```python
# data/destination_profiles.json
{
  "Maldives": {
    "elderly_risk_factors": ["limited_medical", "island_access", "humidity"],
    "elderly_base_score": 0.7,
    "conditions": ["good_mobility_required", "medical_access_limited"]
  },
  ...
}
```

#### Maldives Resort Premium
**File**: `src/intake/decision.py:952-954`
```python
if stay_b and budget_min < stay_b.high and "Maldives" in dests:
    risks.append("resort_premium")
    critical_changes.append("Consider 3-night Maldives stay instead of 4")
```
**Issues**:
- Only Maldives flagged — what about Seychelles? Fiji?
- Assumes all Maldives stays are equal (water villa vs beach villa)

---

### Category 2: Age & Composition Thresholds

#### Toddler Definition
**File**: `src/intake/extractors.py:417`
```python
# "toddler" implies age < 3
```
**Issues**:
- Arbitrary cutoff — why not 4 or 5?
- Some activities cut off at 90cm height, others at 100cm
- Doesn't account for developmental differences

#### Child Age Thresholds
**File**: `src/intake/decision.py:1062`
```python
young_ages = [a for a in ages.value if a < 4]
```
**Issues**:
- Hardcoded 4 years — should be activity-specific
- A 4-year-old can do things a 3-year-old can't

---

### Category 3: Scoring Constants

#### Lifecycle Risk Scores
**File**: `src/intake/decision.py:1196-1210`
```python
if lifecycle.quote_opened and (lifecycle.days_since_last_reply or 0) >= 3:
    score += 0.35
if lifecycle.options_viewed_count == 1 and lifecycle.quote_open_count >= 2:
    score += 0.15
if lifecycle.links_clicked_count > 0:
    score += 0.10
```
**Issues**:
- Why 0.35? Why 0.15? No data backing
- 3 days threshold — why not 2 or 5?
- Same weights for all industries? Travel is different from SaaS

#### Commercial Decision Thresholds
**File**: `src/intake/decision.py:1323-1339`
```python
if ghost >= 0.70:
    return "SEND_FOLLOWUP", "SEND_TARGETED_FOLLOWUP"
if window >= 0.75:
    if lifecycle and lifecycle.payment_stage == "none":
        return "REQUEST_TOKEN", "REQUEST_TOKEN_OR_PLANNING_FEE"
```
**Issues**:
- 0.70, 0.75, 0.65, 0.40 — all arbitrary
- Should be learned from actual conversion data

---

### Category 4: Budget & Pricing

#### Per-Destination Cost Tables
**File**: `src/intake/decision.py:370-430`
```python
BUDGET_FEASIBILITY_TABLE = {
    "Singapore": {"min_per_person": 60000, "maturity": "heuristic"},
    "Japan": {"min_per_person": 120000, "maturity": "heuristic"},
    "Dubai": {"min_per_person": 80000, "maturity": "heuristic"},
    "Thailand": {"min_per_person": 45000, "maturity": "heuristic"},
    "Maldives": {"min_per_person": 90000, "maturity": "heuristic"},
    ...
}
```
**Issues**:
- INR amounts hardcoded — no inflation adjustment
- No seasonality factor (these are peak? shoulder? off-peak?)
- No quality tier (budget vs luxury trips)
- No duration adjustment (3 days vs 7 days)

#### Cost Bucket Ranges
**File**: `src/intake/decision.py:430-560`
```python
BUDGET_BUCKET_RANGES = {
    "Singapore": {
        "flights": (6000, 12000, 1.0),
        "stay": (5000, 12000, 1.5),
        "food": (2000, 4000, 1.0),
        ...
    },
    ...
}
```
**Issues**:
- 8 destinations have ranges, everything else falls back to defaults
- Weight factors (1.0, 1.5, 0.8) arbitrary
- Doesn't account for hotel category, meal preferences

#### Composition Modifiers
**File**: `src/intake/decision.py:696-702`
```python
_CHILD_SURCHARGE = 0.75
_TODDLER_SURCHARGE = 0.30
_ELDERLY_SURCHARGE = 0.05
_SEASON_MULTIPLIER_SHOULDER = 1.15
_SEASON_MULTIPLIER_PEAK = 1.30
_MULTI_COUNTRY_PENALTY = 1.10
_FAMILY_BUFFER_BUMP = 0.02
```
**Issues**:
- Why 75% for child? Why 30% for toddler?
- Season multipliers don't vary by destination
- Multi-country penalty doesn't account for distance (Singapore+Bali vs Singapore+Thailand)

---

### Category 5: Urgency & Timing

#### Urgency Classification
**File**: `src/intake/normalizer.py:244-250`
```python
if days < 0:
    return {"level": "high", "days_until": 0, "confidence": 0.9}
elif days <= 7:
    return {"level": "high", "days_until": days, "confidence": 0.95}
elif days <= 21:
    return {"level": "medium", "days_until": days, "confidence": 0.9}
else:
    return {"level": "low", "days_until": days, "confidence": 0.95}
```
**Issues**:
- 7 days, 21 days — arbitrary thresholds
- Visa processing times vary wildly by destination (Schengen vs Thailand)
- Should be destination-aware

---

### Category 6: Stage Gating

#### Strict Budget Stages
**File**: `src/intake/decision.py:1693-1696`
```python
if feasibility["status"] == "infeasible":
    strict_budget_stages = {"proposal", "booking"}
    if stage in strict_budget_stages:
```
**Issues**:
- Why is budget blocking at proposal but not discovery? (Intentional design, but should be documented)
- No configurability per agency

---

### Category 7: Business Logic Rules

#### Ambiguity Severity Table
**File**: `src/intake/decision.py:248-260`
```python
AMBIGUITY_SEVERITY: Dict[str, str] = {
    ("destination_candidates", "unresolved_alternatives"): "blocking",
    ("destination_candidates", "destination_open"): "blocking",
    ("destination_candidates", "value_vague"): "blocking",
    ("party_size", "value_vague"): "blocking",
    ...
}
```
**Issues**:
- Not inherently bad — this IS business logic
- But should be configurable per agency
- Some agencies work with vague inputs, others need precision

---

## Part 3: What SHOULD Be Data-Driven (Priority Matrix)

| Priority | Item | Current State | Should Be | Complexity |
|----------|------|---------------|-----------|------------|
| **P0** | Per-destination costs | Hardcoded table | Destination pricing API + seasonality | Medium |
| **P0** | Cost bucket ranges | Hardcoded per destination | Dynamic from supplier inventory | High |
| **P0** | Activity suitability (toddler/elderly) | Age thresholds only | Activity × age-band utility matrix | High |
| **P1** | Risk scoring thresholds | Magic numbers (0.70, 0.75) | Learned from conversion data | Medium |
| **P1** | Lifecycle scoring | Fixed weights | Calibrated per agency | Medium |
| **P2** | Elderly mobility risk | 5 hardcoded destinations | Destination attribute database | Low |
| **P2** | Urgency thresholds | Fixed (7/21 days) | Destination visa times | Low |
| **P3** | Ambiguity severity | Fixed mapping | Agency-configurable | Low |

---

## Part 4: Un-Hardcoding Strategy

### Phase 1: Low-Hanging Fruit (P2-P3, Easy Wins)

1. **Extract destination attributes**
   ```python
   # data/destination_attributes.json
   {
     "Maldives": {
       "elderly_mobility_risk": "high",
       "medical_access": "limited",
       "physical_demand": "low"
     },
     "Switzerland": {
       "elderly_mobility_risk": "medium",
       "medical_access": "excellent",
       "physical_demand": "high"
     }
   }
   ```

2. **Extract visa processing times**
   ```python
   # data/visa_requirements.json
   {
     "Singapore": {
       "visa_required": false,
       "processing_days": 0
     },
     "Schengen": {
       "visa_required": true,
       "processing_days": 15
     }
   }
   ```

3. **Make thresholds configurable**
   ```python
   # config/scoring.yaml
   lifecycle_scoring:
     ghost_threshold: 0.70  # was hardcoded
     window_threshold: 0.75
     reply_days_threshold: 3
   ```

### Phase 2: Medium Complexity (P1, Data Infrastructure)

4. **Build destination pricing service**
   - Fetch live pricing from supplier APIs
   - Cache with TTL
   - Fallback to seasonal averages

5. **Implement scoring calibration**
   - Track actual conversions
   - A/B test different thresholds
   - Per-agency calibration

### Phase 3: High Value, High Complexity (P0, Core Differentiator)

6. **Activity suitability matrix** (This is Product B!) - **PARTIALLY IMPLEMENTED 2026-04-18**
   ```python
   # data/activity_suitability.json
   {
     "universal_studios_singapore": {
       "toddler": {"utility": 0.2, "reasons": ["height_restrictions", "noise"]},
       "elderly": {"utility": 0.3, "reasons": ["walking", "queues"]},
       "adult": {"utility": 1.0, "reasons": []}
     },
     "gardens_by_the_bay": {
       "toddler": {"utility": 0.9, "reasons": ["stroller_friendly"]},
       "elderly": {"utility": 0.95, "reasons": ["accessible_paths"]},
       "adult": {"utility": 0.9, "reasons": []}
     }
   }
   ```
   **Status**: Tier 1 and Tier 2 scoring implemented in `src/suitability/`. Static activity catalog with 18 activities. Integrated with decision pipeline. See `Docs/SUITABILITY_IMPLEMENTATION_SUMMARY_2026-04-18.md` for details.

7. **Supplier inventory integration** (Sourcing hierarchy!)
   - Internal packages database
   - Preferred partner rates
   - Network/consortium access
   - Open market fallback

---

## Part 5: The Missing Middle Layer

Current code jumps straight from "I have a toddler" → "toddler_pacing_risk".

**What's missing**:

```
I have a toddler
     ↓
Singapore destination
     ↓
[GAP: No data about what Singapore activities are toddler-friendly]
     ↓
Generic "toddler_pacing_risk" flag
```

**Should be**:

```
I have a toddler
     ↓
Singapore destination
     ↓
[Activity Database: Universal Studios (20% toddler utility),
 Gardens by the Bay (90%), Night Safari (40%)]
     ↓
Specific recommendations: "Skip US, maximize Gardens"
     ↓
Quantified waste: "Universal Studios tickets: ₹10,000 × 20% = ₹8,000 waste"
```

**This gap IS Product B.** Without it, the audit engine is a fantasy.

---

## Part 6: Immediate Actions

### Before Building More

1. **Define your minimum viable destination** — don't try to cover everywhere
2. **Build the activity database for ONE destination** (Singapore? Bali?)
3. **Test the audit flow end-to-end with real itineraries**
4. **Calibrate pricing thresholds with real agency data**

### Decision Point

Can you build Product B with:
- **Option A**: Manual curation (you research and code activities)
- **Option B**: ML extraction (scrape OTA sites, classify activities)
- **Option C**: Partner data (get it from suppliers/consortiums)

**Option A** is slow but accurate. **Option B** is fast but noisy. **Option C** is ideal but requires partnerships.

---

## Summary

| What You Have | What You Need For Thesis |
|---------------|-------------------------|
| Generic intake spine | Activity suitability intelligence |
| Age-based risk flags | Per-person utility scoring |
| Hardcoded pricing | Dynamic supplier integration |
| CRM lifecycle scoring | Trip quality audit engine |

**The hardcoding isn't the problem** — it's a symptom. The problem is that the domain intelligence layer doesn't exist yet.

Build that layer, and the hardcoded values become configuration. Skip it, and you're forever tuning magic numbers that don't match reality.
