# Audit and Intelligence Engine: Detailed Specification

## 1. Purpose
The Audit Engine is the "intelligence" layer that converts a generic itinerary into a tailored, high-utility plan. It serves as both a consumer-facing validation tool (lead-gen) and an agency-facing quality assurance tool.

## 2. Input Ingestion (The "Bring Any Plan" Model)
The system must support five entry modes to capture the market's messy data:
1. **File Upload**: PDF, Word, Images (Screenshots).
2. **Text Paste**: Copied itineraries, WhatsApp messages, email quotes.
3. **URL Ingestion**: MakeMyTrip package pages, hotel sites, travel blogs.
4. **Image/Screenshot**: OCR-based extraction of quotes and schedules.
5. **Hybrid**: URL + manual user notes.

### Extraction targets:
- **Entities**: Hotel names, specific activities, flight routes.
- **Structure**: Day-by-day sequence, city split.
- **Financials**: Total price, inclusions (meals, transfers), exclusions.
- **Implied Target**: Who was this package designed for? (e.g., "Budget Backpackers").

---

## 3. The "Wasted Spend" Detection Logic
This is the core differentiator. The engine evaluates the **Utility per Person**.

### The Logic:
$\text{Utility} = \text{Activity Value} \times \text{Group Member Suitability}$

**Example Case: Universal Studios (US)**
- **Group**: 2 Adults, 2 Elderly, 1 Toddler.
- **Cost**: Full price for 5 tickets.
- **Suitability Analysis**:
    - Adults: 100% usability.
    - Elderly: 30% usability (limited mobility, noise, queues).
    - Toddler: 20% usability (nap times, height restrictions).
- **Verdict**: 3/5 people are "low-utility."
- **Flag**: `Wasted Spend Risk - High`.
- **Recommendation**: "Only book tickets for the adults; provide a relaxed 'city stroll' alternative for the elderly and toddler."

---

## 4. The Fit-Score Framework
The engine scores the itinerary across five dimensions:

| Dimension | What is checked? | Red Flag Example |
| :--- | :--- | :--- |
| **Group Fit** | Age/Mobility vs Activities | "8km walking day with a toddler." |
| **Pacing Fit** | Transit time vs Rest time | "3 hotel changes in 4 days." |
| **Budget Fit** | Package cost vs Real-world spend | "Budget says 2L, but shopping is not factored." |
| **Food Fit** | Diet constraints vs Local options | "Strict vegetarian in a seafood-centric area." |
| **Operational Fit** | Logical flow of movement | "Hotel is in North, Activity is in South, Hotel is in North." |

---

## 5. Intelligence Capture (The Market Flywheel)
Every audit is a data point for the agency's "Market Intelligence Layer."

### Supply-Side Learning:
- Which hotels are most commonly pushed by OTAs (MakeMyTrip, etc.)?
- What are the "standard" itinerary shapes for a 6-day Singapore trip?
- Where do generic packages consistently fail?

### Demand-Side Learning:
- What do travelers actually question after getting a quote?
- Which activities are most frequently flagged as "too expensive/useless"?
- What "hidden" needs (e.g., shopping, specific food) are missing from standard plans?

---

## 6. The Audit Output (The Report)
The user receives a structured "Trip Audit Report":
1. **The Verdict**: (e.g., "Decent, but flawed for a family with elderly parents").
2. **The Waste Map**: Visual highlight of activities with low group utility.
3. **The Gap Analysis**: "Your plan is missing a budget for local transport and visa fees."
4. **The "Smarter Alternative"**: A revised version of the plan that optimizes for the specific group.
5. **The Agency Handoff**: "Click here to have [Agency Name] fix these risks and book a guaranteed better version."
