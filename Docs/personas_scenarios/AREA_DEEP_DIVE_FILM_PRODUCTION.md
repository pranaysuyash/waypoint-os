# Area Deep Dive: Film & Production Travel

## High-Level Objective
To manage the chaotic, time-critical, and logistically heavy travel needs of film, TV, and advertising productions.

## Stakeholder Mapping
*   **P3 (Junior Agent/Assistant)**: Manages the heavy "grind" of manifest changes and last-minute booking shifts.
*   **P1 (Solo Agent)**: Orchestrates the "ATA Carnet" and OBC (On-Board Courier) logistics.
*   **S2 (Supplier)**: Media-specific airline desks (excess baggage experts), "Fixers" on the ground, and secure transport providers.
*   **S1 (Production Manager)**: The primary commercial contact concerned with "Budget vs. Schedule."

## Critical Logistics & Logic
### 1. The ATA Carnet (Equipment Passport)
*   **Logic**: Equipment manifest must match the customs document exactly.
*   **Trigger**: Inventory items tagged as `FILM_GEAR`.
*   **System Check**: Automated reminders for carnet stamps at every border crossing. Failure to stamp triggers a `Risk_Compliance` alert.

### 2. Excess Baggage & Media Rates
*   **Logic**: System must automatically apply "Media Rates" (which allow for higher baggage counts and lower change fees) during the quoting phase.
*   **P3 Support**: Automated calculation of weight/volume for camera packages to pre-book cargo space.

### 3. On-Board Courier (OBC) Dispatch
*   **Logic**: For sensitive assets (dailies, unique props), the system can dispatch a certified OBC.
*   **Frontier Trigger**: `GhostConcierge` monitors flight delays; if a delay risks a "Shoot Day," it automatically searches for the next available OBC route to bypass cargo holds.

## Specialized Scenarios

### Scenario 330: The "Last-Minute Location Pivot"
*   **Context**: Director decides the weather in Iceland is bad and wants to move the 50-person crew to Morocco overnight.
*   **Frontier Logic**: `FrontierOrchestrator` triggers a "Mass Handoff" to multiple agents simultaneously to handle the 50+ cancellations and re-bookings in under 2 hours.

### Scenario 331: The "Gear Seizure" at Customs
*   **Context**: A $500k lens package is held at customs due to a carnet typo.
*   **Immune Response**: System identifies the "Fixer" with the highest clearance in that jurisdiction and automatically initiates a "Priority Resolution" workflow.

## Commercial Mechanics
*   **Billing**: Often "Open Account" or high-limit corporate credit lines.
*   **Transparency**: Production Managers need real-time "Spend-to-Date" vs. "Budget" visualization.
*   **Audit**: Detailed reconciliation of "Additional Baggage Fees" paid at the airport vs. pre-paid estimates.

## Design Identity (Film Noir / Production Ready)
*   **Aesthetic**: "Dailies/Clapboard" (high-contrast, metadata-heavy).
*   **Imagery**: Behind-the-scenes photography, location scouts, gear manifests.
*   **Trust Anchor**: "Schedule Confidence Meter"—showing the probability of the crew arriving before the "Call Time."
