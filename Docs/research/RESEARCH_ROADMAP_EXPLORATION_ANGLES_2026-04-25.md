# Research Roadmap: Exploration Angles (2026-04-25)

This document expands on the foundational research in `Docs/personas_scenarios/` by identifying "High-Leverage Angles" that shift the system from standard travel automation to an **Autonomous Integrity Engine**.

---

## [ANGLE 01] Adversarial Integrity (Red-Teaming)
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_ADVERSARIAL_INTEGRITY.md)
**Focus**: What happens when the system's own intelligence becomes a risk?
- **Exploration Path**: 
  - **Scenario Cluster**: AI proposes a recovery plan that violates a non-obvious visa rule or uses a "ghost" inventory source.
  - **Logic Requirement**: `Double-Blind Verification`. The system must cross-reference its own "Creative" solutions against a "Constraint-Only" validator (e.g., official Timatic API).
  - **Goal**: Prevent "Hallucination-Driven Displacement."

## [ANGLE 02] Emotional Triage & Sentiment ROI
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_EMOTIONAL_TRIAGE.md)
**Focus**: Moving beyond "Time/Money" urgency to "Relationship" urgency.
- **Exploration Path**: 
  - **Scenario Cluster**: A honeymooning couple's minor restaurant cancellation vs. a business traveler's minor hotel delay.
  - **Logic Requirement**: `Emotional_Weight_Multiplier`. The system adjusts its `Urgency_Score` based on the persona's life-event status.
  - **Goal**: Maximize "Loyalty ROI" by solving high-emotion/low-cost problems first.

## [ANGLE 03] Temporal Drift (The 'Stale Info' Trap)
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_TEMPORAL_DRIFT.md)
**Focus**: Information decay between booking and arrival.
- **Exploration Path**: 
  - **Scenario Cluster**: A hotel's pool closes for renovation 3 days before a family arrival, but after the booking was confirmed.
  - **Logic Requirement**: `Recursive_Re_Validation`. A 48-hour "Liveness Check" before every major trip milestone.
  - **Goal**: Eliminate "Arrival Surprises" by surfacing changes proactively.

## [ANGLE 04] Fractional Sponsorship & Hybrid Finance
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_FRACTIONAL_SPONSORSHIP.md)
**Focus**: The complexity of "Who Pays for What."
- **Exploration Path**: 
  - **Scenario Cluster**: A corporate traveler brings their family. The company pays the base rate, but the traveler pays the "Extra Room" and "Meal Upgrades" separately.
  - **Logic Requirement**: `Shadow_Ledgers`. Maintaining a unified trip view that branches into separate financial settlement paths.
  - **Goal**: Clean separation of corporate liability vs. personal luxury.

## [ANGLE 05] Supplier 'Dark Pattern' Detection
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_SUPPLIER_DARK_PATTERNS.md)
**Focus**: Auditing the ethics and reliability of the supply chain.
- **Exploration Path**: 
  - **Scenario Cluster**: Detecting a hotel that consistently overbooks "Standard Rooms" to force upgrades, or an airline that uses "Hidden-City" ticketing logic.
  - **Logic Requirement**: `Supplier_Integrity_Audit`. Tracking "Systemic Drift" in supplier performance vs. stated promises.
  - **Goal**: Automated de-ranking of unreliable or predatory suppliers.

## [ANGLE 06] The 'Ghost Concierge' Handoff
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_GHOST_CONCIERGE.md)
**Focus**: Making the AI-to-Human handoff feel invisible.
- **Exploration Path**: 
  - **Scenario Cluster**: A traveler starts a conversation with the AI, and a human agent jumps in mid-sentence.
  - **Logic Requirement**: `Context_Tunneling`. Ensuring the human sees a "Real-Time Sentiment Graph" and "Summary-So-Far" before they send their first message.
  - **Goal**: Zero repetition for the traveler.

---

## [ANGLE 07] Geopolitical Resilience & Sovereign Duty of Care
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_GEOPOLITICAL_RESILIENCE.md)
**Focus**: Rapid response to sudden border closures, coups, or regional conflicts.
- **Exploration Path**: 
  - **Scenario Cluster**: A traveler is in a country where a coup occurs overnight. All commercial flights are cancelled.
  - **Logic Requirement**: `Safe-Harbor_Routing`. AI identifies the nearest land-border or private extraction point.
  - **Goal**: Physical safety over commercial convenience.

## [ANGLE 08] Sustainability & Carbon-Budgeting (The 'Green Ledger')
**Status**: [LOGIC SPEC DRAFTED](file:///Users/pranay/Projects/travel_agency_agent/Docs/research/OPERATIONAL_LOGIC_SPEC_SUSTAINABILITY.md)
**Focus**: Integrating environmental constraints into the commercial search.
- **Exploration Path**: 
  - **Scenario Cluster**: A corporate traveler has a "Carbon Budget" for the year. A proposed flight exceeds the remaining budget.
  - **Logic Requirement**: `Emission_Weighting`. AI proposes "Rail-First" or "Carbon-Offset" alternatives.
  - **Goal**: Operationalizing Net-Zero commitments at the individual trip level.
