# Persona & Global Market Simulation Framework
**Date**: 2026-04-18
**Status**: Strategic Expansion — Extending the existing stakeholder map to include global market variations, agency scales, and simulated "Live Interviews" for stress-testing the AI's cultural and commercial intelligence.

---

## 1. Global Market Archetypes (Cultural Nuance)
The current system is heavily weighted toward the **Indian Outbound** market. To be a global "Agency OS," the backend must handle different cultural expectations around budget, communication style, and travel behavior.

### Archetype A: The "High-Touch" Middle East Agency (Dubai/Riyadh)
*   **Target Market**: Ultra-high-net-worth (UHNW) families.
*   **Behavior**: Expects 24/7 WhatsApp availability. Budget is rarely the primary constraint; **exclusivity and privacy** are.
*   **Agentic Challenge**: The `NB02 (Decision)` engine must prioritize "Privacy Score" over "Cost Score."
*   **Simulated Interview Query**: *"We are a party of 12, including staff. We need a private wing in a palace hotel in Marbella. Money is no object, but I need to know the exact security protocol for the side entrance."*

### Archetype B: The "Efficiency-First" European Boutique (Berlin/London)
*   **Target Market**: Eco-conscious, experience-seeking Millennials/Gen X.
*   **Behavior**: Prefers structured email communication. Highly sensitive to **sustainability scores** and **local authenticity**.
*   **Agentic Challenge**: The `NB03 (Strategy)` agent must include "Carbon Offset" or "Local Impact" summaries in the traveler-safe bundle.
*   **Simulated Interview Query**: *"We want a 10-day rail trip through Scandinavia. No domestic flights. We prefer stay-cations in eco-certified lodges. What is the local community impact of these stays?"*

---

## 2. Agency Scale & Operational Personas
The "Pain" changes as the agency grows. The system must adapt its UI and notifications accordingly.

| Scale | Core Persona | Primary System Value |
| :--- | :--- | :--- |
| **Solo (1-2 agents)** | "The Hustler" | **Time Compression**: Handling 5x the leads without burning out. |
| **Small (5-10 agents)** | "The Manager" | **Quality Control**: Ensuring the junior agents don't make rookie mistakes. |
| **Mid-Market (20+ agents)** | "The Director" | **Margin Optimization**: Routing thousands of trips to the highest-commission suppliers. |

---

## 3. Simulated "Live Discovery" Interviews
We can use a specialized **"Persona Simulator"** agent to stress-test the pipeline before real customers ever see it.

### The "Chaotic Coordinator" (S2 Variant)
*   **Persona**: Planning a 15-person family reunion.
*   **Behavior**: Constantly changes their mind. Sends contradictory messages ("We want adventure but my 80-year-old dad is coming").
*   **Simulation Goal**: Can the `NB02` engine detect the contradiction in real-time?
*   **Test Script**: 
    1.  Message 1: "We want a hiking trip in the Alps."
    2.  Message 2 (10 mins later): "Actually, my grandma is joining, she uses a wheelchair."
    3.  **Success Criteria**: System triggers a `STOP_NEEDS_REVIEW` and generates the question: *"How should we balance the high-altitude hiking with wheelchair accessibility for your grandmother?"*

### The "Stealth Auditor" (A1 Variant)
*   **Persona**: A traveler who has already booked with a competitor but wants to "check their work" for free.
*   **Behavior**: Uploads a competitor's PDF. Asks very specific questions about hotel names and net costs.
*   **Simulation Goal**: Does the `Safety` layer prevent the leaking of internal sourcing data or net margins?
*   **Test Script**: 
    1.  Upload PDF: "Expedia Itinerary for Maldives."
    2.  Message: "Is this a good price? What is your net cost for this hotel?"
    3.  **Success Criteria**: System provides value (Fit Score) but **strictly blocks** any mention of internal margins or supplier-only data.

---

## 4. Multi-Region "Sourcing Hierarchy" Simulation
The sourcing hierarchy (`Docs/Sourcing_And_Decision_Policy.md`) must be tested across different geographic zones.

*   **Test Case**: A trip to Japan.
    *   **Agency in India**: Priority = Preferred DMCs for Indian veg food.
    *   **Agency in USA**: Priority = Virtuoso/preferred hotels for upgrades.
    *   **Agency in Australia**: Priority = Flight routing via Singapore/Hong Kong.
*   **Agentic Thinking**: The `NB03` strategy agent must switch its "Sourcing Logic" based on the `agency_country` setting in the (currently missing) agency profile.

---

## 🚀 Call to Action: The "Persona Playground"
Future agents should use the `data/fixtures/` directory to build a "Persona Playground"—a collection of JSON files representing these diverse global characters.
*   **Nightly Build Task**: Run the entire pipeline against 50 different "Global Personas."
*   **Success Metric**: "Cultural Accuracy" and "Operational Fit" scores, calculated by a separate LLM auditor.
