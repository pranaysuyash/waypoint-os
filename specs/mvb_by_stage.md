# MVB by Stage v0.1 (Minimum Viable Brief)

## Purpose
Define the data sufficiency gates for each stage of the agency workflow. A "blocking field" prevents the system from moving to the next stage.

---

## Stage 1: Discovery (The "Screener")
**Goal**: Determine if the lead is coherent and a potential fit.

### Hard Blockers (Must have to proceed)
- **Traveler Composition**: (Count, Age Bands).
- **Origin City/Region**: Where they are starting from.
- **Rough Budget Band**: (e.g., Lean, Mid, Premium).
- **Date Window/Flexibility**: When they want to go.
- **High-Level Intent**: (e.g., "International nature trip").

### Soft Blockers (Nice to have)
- Hotel star preference.
- Specific meal restrictions.
- Airline preference.

**Decision**: If hard blockers are missing $\rightarrow$ `ASK_FOLLOWUP`.

---

## Stage 2: Shortlist (The "Sourcing" Gate)
**Goal**: Generate a viable list of destinations and properties.

### Hard Blockers
- **Confirmed Traveler Composition**.
- **Exact/Narrow Date Window**.
- **Specific Budget Range**.
- **Destination Interest / Openness**.
- **Major Hard Constraints** (e.g., "No flights over 6 hours").

### Soft Blockers
- Room configuration (e.g., "Need 2 beds").
- Neighborhood preferences.
- Activity intensity.

**Decision**: If hard blockers are missing $\rightarrow$ `ASK_FOLLOWUP`.

---

## Stage 3: Proposal (The "Traveler-Safe" Gate)
**Goal**: Produce a final, high-confidence itinerary.

### Hard Blockers
- **Resolved core contradictions** (e.g., Budget vs Luxury).
- **Confirmed Destination**.
- **Fixed Dates**.
- **Confirmed Budget**.
- **Confirmed Mobility/Medical Constraints**.
- **Hotel/Room Fit Feasibility**.

### Soft Blockers
- Minor activity nuances.
- Meal preferences for specific days.

**Decision**: If hard blockers are missing $\rightarrow$ `ASK_FOLLOWUP` or `INTERNAL_DRAFT`.

---

## Stage 4: Booking (The "Operational" Gate)
**Goal**: Execute the transaction.

### Hard Blockers
- **Full Legal Names** (matching passports).
- **Passport/Visa Status**.
- **Final Approval on Price**.
- **Payment Readiness**.

**Decision**: If hard blockers are missing $\rightarrow$ `STOP_NEEDS_REVIEW` or `ASK_FOLLOWUP`.
