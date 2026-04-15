# Trip Budget Reality Scenario

**Date:** 2026-04-15
**Type:** Synthetic budget investigation note
**Purpose:** Capture one realistic travel budget scenario, the investigation tasks the agent should run, the exact input assumptions, and the expected output structure for a budget reality check that goes beyond "high/low".

---

## Scenario

- **Destination:** Dubai + Maldives
- **Dates:** 10 October 2026 to 21 October 2026
- **Duration:** 11 nights
- **Group composition:** 2 adults, 2 teens, 1 toddler
- **Budget:** ₹5,50,000 total for 5 people
- **Planned itinerary:**
  - 10–13 October: Dubai city stay, desert safari, city tour
  - 13–17 October: Maldives resort island stay, snorkeling, spa
  - 17–21 October: Dubai return for shopping, museum, one-day Abu Dhabi shore excursion

---

## Input (I/P)

The agent should treat the following as the input assumptions for a budget reality analysis:

1. **Budget type:** total package budget in INR, fixed at ₹5,50,000. No separate currency conversion buffer is included.
2. **Group makeup:** 2 adults, 2 teens, 1 toddler. The toddler requires child seats/transfers and some low-intensity activities.
3. **Geographic scope:** two countries (UAE and Maldives) with different pricing regimes and visa/entry rules.
4. **Route:** round-trip international flights, one intra-UAE transfer, two island transfers in Maldives, and a return to Dubai.
5. **Accommodation standard:** midrange city hotel in Dubai, four-star beach resort in Maldives, family room or two adjacent rooms.
6. **Bucket expectations:** the budget must cover flights, stay, food, local transport, activities, visas, insurance, shopping, and buffer.
7. **Risk assumptions:** prices are expected to be higher than the destination baseline because of shoulder-season Maldives resort rates and family travel add-ons.

---

## Investigation Tasks

The feasibility check should verify the budget through these lenses.

### 1. Cost bucket decomposition

- Estimate likely costs for each bucket: international flights, resort stay, daily food, airport transfers, island transfers, activities, visas, insurance, shopping, and contingency buffer.
- Identify which buckets are missing from the stated budget scope.
- Mark any bucket that is usually omitted by customers but material for quote accuracy.

### 2. Flight and lodging realism

- Check whether ₹5,50,000 can plausibly cover return flights for 5 from India to Dubai + regional flights to Maldives plus a premium family resort.
- Estimate per-night resort pricing in the Maldives for a family-friendly midrange property in October.
- Validate whether the itinerary creates a two-night resort stay gap or an overstay risk relative to published package deals.

### 3. Transfer & insurance load

- Confirm transfer complexity: Dubai airport → city hotel, Dubai → Maldives flight, Maldives airport → resort boat/seaplane, Maldives → Dubai flight, Dubai → Abu Dhabi day tour, Dubai airport return.
- Check whether travel insurance and child-specific coverage are likely to fit this budget.

### 4. Activity and shopping realism

- Estimate reasonable activity spends for a desert safari, snorkeling, spa, Abu Dhabi excursion, and shopping allowance.
- Flag if the plan assumes "all inclusive" when the stated budget is only a package-level number.

### 5. Visa and payment risk

- Confirm visa requirements for Indian passport holders entering UAE and Maldives in October 2026.
- Flag whether visa fees, travel insurance, and currency exchange costs should be treated as separate mandatory buckets.

### 6. Sensitivity & buffer

- If the budget is tight, identify which buckets are most sensitive to price variance (flights, resort, transfers).
- Recommend a buffer percentage for a family group on a cross-country itinerary.

### 7. Alternative recommendation

- If the itinerary is not realistic on ₹5,50,000, suggest one safer path with lower transfers or a cheaper destination combination.

---

## Expected Output (O/P)

The evaluator should return a clear verdict with these output elements:

1. `verdict`: `realistic` | `borderline` | `not realistic`
2. `budget_breakdown`: list of buckets with estimated INR ranges and whether the bucket is covered.
3. `missing_buckets`: list of cost categories that are not represented in the raw budget statement.
4. `risks`: list of key risks such as `flight inflation`, `resort premium`, `transfer complexity`, `insurance gap`, `shopping underbudget`, `visa/entry fees`.
5. `critical_changes`: concrete items to change before any quote is built.
6. `must_confirm`: required checks before proposal or booking.
7. `alternative`: one safer itinerary if the current plan is too risky.

Example structure:

- `verdict`: `borderline`
- `budget_breakdown`: [
  `{bucket: "flights", estimate: "₹2,20,000 - ₹2,75,000", covered: true}`,
  `{bucket: "stay", estimate: "₹1,80,000 - ₹2,20,000", covered: true}`,
  `{bucket: "food", estimate: "₹35,000 - ₹50,000", covered: false}`,
  ...
]
- `missing_buckets`: [`food`, `insurance`, `shopping`, `buffer`]
- `risks`: [`tight flights`, `Maldives resort premium`, `insurance gap`, `visa fee omission`]
- `critical_changes`: ["Add explicit food and shopping allowance", "Use a 3-night Maldives stay instead of 4", "Confirm Maldives transfer cost before quoting"]
- `must_confirm`: [`flight quote for 5`, `Maldives resort family room availability`, `UAE visa fees for Indian passports`, `travel insurance premium`] 
- `alternative`: `Dubai + Abu Dhabi only, same dates, lower transfer and resort costs`

---

## Notes

- This scenario is intentionally focused on budget reality and missing cost buckets. It is not just a high/low feasibility check.
- It should surface the exact buckets that often cause customer shock and wasted quoting effort.
- ~~Current backend coverage in `src/intake/decision.py` is narrower than this scenario. `check_budget_feasibility()` only evaluates overall destination viability by total budget vs destination baseline. It does not model buckets such as flights, transfers, visas, insurance, shopping, or buffer.~~
- **IMPLEMENTED 2026-04-15**: `decompose_budget()` now provides full per-bucket decomposition across all 8 cost buckets (flights, stay, food, local_transport, activities, visa_insurance, shopping, buffer). The `BudgetBreakdownResult` includes verdict, bucket estimates with low/high ranges, covered/gap status, missing buckets, risks, critical changes, must-confirm items, and alternatives. Per-destination bucket ranges are in `BUDGET_BUCKET_RANGES` (27 destinations). Frontend DecisionTab shows a full breakdown table.

---

## Investigation Result

- `verdict`: `borderline`
- `budget_breakdown`:
  1. `{bucket: "flights", estimate: "₹2,20,000 - ₹2,80,000", covered: true}`
  2. `{bucket: "stay", estimate: "₹1,70,000 - ₹2,15,000", covered: true}`
  3. `{bucket: "food", estimate: "₹40,000 - ₹55,000", covered: false}`
  4. `{bucket: "local transport", estimate: "₹15,000 - ₹25,000", covered: false}`
  5. `{bucket: "activities", estimate: "₹30,000 - ₹45,000", covered: false}`
  6. `{bucket: "visa/insurance", estimate: "₹18,000 - ₹25,000", covered: false}`
  7. `{bucket: "shopping", estimate: "₹25,000 - ₹40,000", covered: false}`
  8. `{bucket: "buffer", estimate: "₹25,000 - ₹35,000", covered: false}`
- `missing_buckets`: [`food`, `local transport`, `activities`, `visa/insurance`, `shopping`, `buffer`]
- `risks`: [`flight inflation`, `Maldives resort premium`, `insurance gap`, `visa fee omission`, `shopping overage`, `tight buffer`] 
- `critical_changes`:
  1. Add explicit line items for food, local transport, insurance, and buffer before sending a quote.
  2. Swap Maldives resort for a budget family island stay or reduce Maldives nights to 3.
  3. Confirm whether the airfare quote includes 2 adults + 2 teens + 1 toddler pricing.
  4. Build in a 10% buffer for tour operator markup, exchange rate movement, and shopping.
- `must_confirm`: [`flight quote for 5`, `Maldives resort family room availability`, `UAE and Maldives visa fees`, `travel insurance premium`, `exchange rate assumption`] 
- `alternative`: `Dubai + Abu Dhabi only, same dates, lower transfers and a 3-star family hotel instead of Maldives resort.`
