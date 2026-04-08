# Voice Intake and Orchestration: Detailed Specification

## 1. The Session Experience
The system replaces the static "intake form" with a dynamic, voice-guided discovery session.

### A. The Two-Screen Model
1. **The Agency Screen (The Seeder)**:
   - The planner enters initial lead context (notes from a 2-minute call, referral source, rough budget).
   - The planner chooses a **Session Objective** (e.g., `Destination Discovery`, `Itinerary Audit`, `Budget Clarification`).
   - The system generates a unique session link sent to the traveler.

2. **The Traveler Screen (The Interface)**:
   - The traveler joins a voice session.
   - **The Live Brief Panel**: A side-panel that updates in real-time. As the traveler speaks, fields (Destination, Budget, Pace) are filled and tagged (Explicit, Inferred, or Assumed).
   - **The Unresolved Questions Panel**: Shows what the system still needs to know.

---

## 2. The Backend Orchestration (The Brain)
The system does not follow a script. It follows a **State-Based Routing** logic.

### The "Compiler" Orchestration Loop
The system does not follow a script. It follows a state-machine logic:
`Input` $\rightarrow$ `Normalization` $\rightarrow$ `Validation (MVB)` $\rightarrow$ `Inference` $\rightarrow$ `Decision Policy` $\rightarrow$ `Strategy Generation` $\rightarrow$ `Modular Prompting` $\rightarrow$ `Voice Output`.


### B. Key Orchestration Components
- **Conversation Orchestrator**: The "Conductor." Decides if the session should continue or stop based on the **Stopping Criteria**.
- **State Extraction Module**: Normalizes voice input into the `Shared State Model` (e.g., "Maybe Singapore or Thailand" $\rightarrow$ `destination_status: semi-open`).
- **Classification Module**: Assigns the traveler to "Brackets" (e.g., `family_with_toddler`, `shopping_first`).
- **Gap Detection Module**: Identifies missing critical fields (e.g., "We know the budget, but not the departure city").
- **Specialist Reasoners**: Modules that advise the orchestrator on specific risks (e.g., the `Pacing Agent` flags that 3 cities in 5 days is too much for a toddler).

---

## 3. The "Brackets" Logic (Classification)
The system classifies the trip into categories to determine the planning route:
- **Traveler Brackets**: Solo, Couple, Friends, Family+Toddler, Family+Elderly, Mixed Group.
- **Budget Brackets**: Lean, Mid, Premium, Luxury.
- **Pace Brackets**: Relaxed, Balanced, Packed.
- **Intent Brackets**: Sightseeing-first, Shopping-first, Food-first, Luxury-rest, Activity-heavy.
- **Route Brackets**: `Package-suitable`, `Custom-supplier`, `Network-assisted`, `Open-market`.

---

## 4. Next-Question Policy (Heuristics)
The orchestrator selects the next question based on a **Priority Stack**:
1. **Blocking Unknowns**: Critical info needed to move forward (e.g., "Who is traveling?").
2. **Contradiction Resolution**: "You mentioned a luxury budget but want hostel-style stays. Could you clarify?"
3. **Route-Changing Fields**: Questions that shift the project from a "Package" to a "Custom" build.
4. **High-Risk Suitability**: "Since you have elderly parents, are you okay with long walking days?"
5. **Low-Value Refinements**: "Do you prefer breakfast at the hotel or local cafes?"

---

## 5. The "Audit Mode" (Comparison Flow)
When a user uploads an existing itinerary or URL, the session shifts to **Audit Mode**.

### The Audit Workflow:
1. **Ingestion**: Extract hotels, activities, and prices from the PDF/URL.
2. **Preference Match**: Ask the user for their specific constraints (e.g., "Toddler age? Mobility issues?").
3. **The "Wasted Spend" Analysis**:
   - **Check**: Is this activity usable by everyone?
   - **Example**: "Universal Studios is included for all 5 people, but the toddler and elderly parents cannot use 60% of the rides."
   - **Flag**: `High Wasted Spend Risk`.
4. **Output**: 
   - **Fit Score**: (Destination Fit, Hotel Fit, Activity Fit, Budget Fit).
   - **Missing Buckets**: "Your package doesn't include local transport or shopping buffer."
   - **Smarter Alternative**: "Swap Day 3 for a relaxed botanical garden visit; reallocate the saved budget to a premium dinner."

---

## 6. Stopping Criteria
The session ends when the **Minimum Viable Brief (MVB)** is complete:
- Destination fixed or sufficiently narrowed.
- Date window established.
- Group composition known.
- Rough budget range known.
- Departure city known.
- Pace and priority signals captured.
- Basic food/stay preferences known.

**Hard Stop**: When the user repeats uncertainty or the session objective is satisfied.
