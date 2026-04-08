# Detailed Agent Map: Boutique Travel Agency AI OS

This document provides an exhaustive catalog of every agent discussed in the project's development. It distinguishes between the **Core v1 Stack** (minimal viable automation) and the **Full Operational Stack** (complete agency lifecycle).

## 1. Agent Classification Logic
To avoid "token waste" and "conversational noise," agents are categorized by their functional role:
- **Conversationalist**: Directly interacts with the user to extract or explain information.
- **Extractor**: Converts unstructured text (call notes, WhatsApp) into structured data.
- **Scorer/Ranker**: Evaluates options against constraints and assigns a numerical fit score.
- **Validator/QA**: Checks for contradictions, errors, or policy violations.
- **Summarizer/Composer**: Aggregates data into client-facing or internal reports.

---

## 2. The Core v1 Stack (Minimal Viable System)
These agents are required to move a lead from discovery to a first usable proposal.

| Agent | Type | Purpose | Key Inputs | Key Outputs |
| :--- | :--- | :--- | :--- | :--- |
| **Client Intake Agent** | Conversational / Extractor | Collects raw inputs (where, when, who, budget, food, travel prefs). | User prompts / Call notes | `traveler_profile`, `trip_constraints` |
| **Constraint Resolver** | Validator / Extractor | Detects ambiguity, contradictions, and missing info. | `trip_brief`, `user_answers` | `missing_info_list`, `contradiction_flags` |
| **Destination Shortlist Agent** | Scorer / Ranker | Turns broad desire into candidate destinations. | `traveler_profile`, `budget`, `vibe` | `destination_candidates` (ranked list) |
| **Flight & Stay Research Agent** | Scorer / Ranker | Finds and evaluates flights and hotels based on preferred networks. | `candidate_destinations`, `budget_model` | `stay_candidates`, `flight_options` |
| **Activity & Dining Planner** | Scorer / Ranker | Finds activities and food that fit the traveler's profile. | `traveler_profile`, `destination` | `activity_candidates`, `dining_suggestions` |
| **Itinerary Composer** | Composer | Synthesizes research into a day-by-day plan. | All candidate lists, `pace_preference` | `itinerary_versions` (v1, v2) |
| **Itinerary QA Agent** | Validator | Sanity-checks for pacing, transit, and group-member suitability. | `itinerary_version`, `traveler_profile` | `qa_flags`, `suitability_warnings` |
| **Proposal Generator** | Composer | Turns the technical plan into a client-facing sales document. | `final_recommendation`, `budget_model` | `proposal_pdf`, `cost_breakdown` |
| **Ops Handover Agent** | Summarizer | Prepares the internal brief for the execution team. | `final_itinerary`, `visa_status` | `ops_handover_pack` |

---

## 3. The Full Operational Stack (End-to-End Lifecycle)

### A. Lead & Discovery Layer
- **Traveler Profiling Agent**: Infers "Traveler Type" (e.g., `honeymoon couple`, `toddler family`, `luxury slow traveler`). This dictates the itinerary logic.
- **Clarification Agent**: Specializes in detecting "impossible" requests (e.g., "Europe in 5 days on a budget").

### B. Feasibility & Constraint Layer
- **Feasibility Agent**: Checks season suitability, minimum practical duration, and internal transfer realism (e.g., "Is Bali with a toddler in 4 days realistic?").
- **Budget Allocation Agent**: Breaks the total budget into buckets (Flights, Hotels, Food, Activities, Visa/Insurance, Shopping).
- **Policy/Logistics Agent**: Rules-based layer for visa requirements, passport validity, and local closures.

### C. Research Layer (Deep Specialization)
- **Flight Strategy Agent**: Ranks routes by "pain score" (fatigue, layovers) not just price.
- **Stay Selection Agent**: Evaluates neighborhood suitability, commute burden, and accessibility.
- **Food/Dining Agent**: Flags food risks for picky eaters or specific diets (Jain, Vegan, Halal).
- **Activities Agent**: Scores activities by interest fit, effort, crowd risk, and cancellation flexibility.
- **Local Mobility Agent**: Optimizes daily routes and handles transfer feasibility (e.g., stroller-friendliness).

### D. Synthesis & Decisioning Layer
- **Trade-off/Ranking Agent**: Compares versions (e.g., "Cheaper" vs "Comfort-first") to help the agency upsell.
- **Personalization/Tone Agent**: Rewrites the same facts for different audiences (e.g., "Luxury" vs "Adventure").
- **Document Pack Agent**: Creates the final PDF, packing lists, and emergency contacts.

### E. Booking & Ops Layer
- **Booking Readiness Agent**: Ensures names match passports, DOBs are collected, and payment milestones are known.
- **Vendor Coordination Agent**: Handles hotel outreach and special requests (early check-in/late check-out).
- **Price Watch Agent**: Tracks fare shifts and hotel sellout risks.

### F. In-Trip Support Layer
- **Concierge Agent**: Live support for route adjustments and dinner suggestions.
- **Disruption Recovery Agent**: Handles delayed flights or hotel overbookings (the "Premium" value).

### G. Post-Trip Layer
- **Feedback/Memory Agent**: Captures what worked and what didn't for future repeat customers.
- **CRM/Upsell Agent**: Suggests the next trip (anniversary, long weekend) based on prior data.

---

## 4. Specialized "Agency-Specific" Agents (The Moat)
These agents implement the "hidden" logic of the agency:

- **Preferred Inventory Agent**: Shortlists from the agency's tie-up hotels first.
- **Margin/Commercial Agent**: Ensures the package is viable (Net Cost $\rightarrow$ Markup $\rightarrow$ Final Quote).
- **Benchmark Agent**: Compares preferred options vs. the broader market to justify the choice.
- **Negotiation/Escalation Agent**: Flags when a human needs to call a supplier for a better rate.
- **Hotel Fit QA Agent**: Catches partner hotels that look good but have "tiny rooms" or "bad breakfast."

---

## 5. Summary of Agent Roles by Output Type
- **Conversational**: Client Intake, Concierge, Proposal (Tone).
- **Extractor**: Intake, Constraint, Booking Readiness, Feedback.
- **Scorer/Ranker**: Destination, Stay, Activity, Trade-off, Preferred Inventory.
- **Validator**: QA, Feasibility, Policy, Hotel Fit QA, Verifier.
- **Composer**: Itinerary Architect, Proposal, Document Pack.
