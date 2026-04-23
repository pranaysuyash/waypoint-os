# FEATURE: Operational Stress Digital Twin (Chaos Simulation)

## 1. Overview
High-stakes travel requires agents who can handle extreme pressure without panic. The **Operational Stress Digital Twin** is a "War Games" environment that uses the OS to simulate complex, multi-variable crises. It creates a "Digital Twin" of the current agency state (active PNRs, supplier contracts, agent shifts) and injects synthetic "Chaos Events" to test system and human resilience.

## 2. Business POV (Agency/Business)
- **Problem**: Agencies only find out how their team handles a crisis *during* a crisis. This leads to costly errors and reputation damage.
- **Solution**: A simulation engine that runs in a "Sandbox" mode, allowing agents to practice rebooking 50 groups during a synthetic volcanic ash cloud or airline strike.
- **Value**:
    - **Resilience Benchmarking**: Quantify which agents remain calm and efficient under load.
    - **Workflow Optimization**: Identify bottlenecks in the "Crisis Dashboard" before they cost real money.
    - **Onboarding Acceleration**: Junior agents "experience" 5 years of crises in their first 2 weeks.

## 3. User POV (Traveler/Admin)
- **Problem**: Travelers feel like guinea pigs when their agent is handling their first major disruption.
- **Solution**: The agent handling their crisis has already solved this exact problem 100 times in simulation.
- **Value**:
    - **Confidence in Crisis**: "Don't worry, I've handled this exact airline bankruptcy scenario in our simulator—here are the 3 steps we take now."
    - **Zero-Error Execution**: Reduced risk of missed connections or lost refunds during the "Fog of War".

## 4. Technical Specifications
- **Chaos Injection Engine**: A library of "Failure Primitives" (e.g., `LINK_FAILURE`, `SUPPLIER_BANKRUPTCY`, `MEDICAL_EMERGENCY`) that can be combined into scenarios.
- **Reality-in-the-Loop**: Uses actual GDS layouts and UI components, but redirects API calls to a "Mock GDS" responder.
- **Agent Performance Scoring (APS)**: Tracks time-to-resolution, cost-to-rebook, and "Sentiment Preservation" (how well they communicated with the simulated customer).
- **Red-Team Automation**: AI agents play the role of "Difficult Customers" or "Uncooperative Suppliers" during the simulation.

## 5. High-Stakes Scenarios
- **Scenario 317 (Silent Handoff Failure)**: Simulator drops an agent-to-agent handoff notification during a shift change to see if the secondary agent detects the gap via the dashboard.
- **Scenario 321 (Medical Oxygen Fail)**: Simulator triggers an equipment failure notification for a medical transit 4 hours before departure to test the agent's speed in sourcing a local alternative.

## 6. Implementation Status
- [ ] [NEW] Mock API response library for GDS/NDC failures.
- [ ] [NEW] Scenario Designer UI for Agency Owners.
- [ ] [NEW] Leaderboard and Training Path integration.
