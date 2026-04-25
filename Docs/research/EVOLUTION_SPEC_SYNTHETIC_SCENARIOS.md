# Evolution Spec: Autonomous Synthetic Scenario Generation (EV-001)

**Status**: Research/Draft
**Area**: Data Augmentation & Edge-Case Simulation

---

## 1. The Problem: "The Long Tail of Rare Events"
While we have 374 scenarios, the number of possible "Triple-Conflict" events (e.g., Bankruptcy + Coup + Medical Emergency) is millions. We cannot manually write them all. We need an **Autonomous Scenario Engine**.

## 2. The Solution: 'Scenario-Cross-Pollination' (SCP) Engine

The SCP engine takes existing "Primitive Scenarios" and combines them to create high-complexity "Compound Scenarios."

### SCP Algorithm:

1.  **Extract Primitives**: Identify core variables from Batch 01-05 (e.g., `Traveler_Type: MINOR`, `Disruption: INSOLVENCY`, `Location: HIGH_RISK`).
2.  **Intersection Engine**: Run a combinatorial generator to create a "Candidate Matrix" (e.g., `MINOR + INSOLVENCY + HIGH_RISK`).
3.  **Narrative Synthesis**: A Tier 3 LLM (o1) generates a 3,000-character narrative and `CanonicalPacket` for the candidate.
4.  **Consistency Check**: A "Validator-Agent" reviews the scenario for physical and logical possibility.
5.  **Library Injection**: Valid scenarios are added to the `Scenario_Library` as "Batch 06 (Synthetic)."

## 3. Data Schema: `Synthetic_Scenario_Metadata`

```json
{
  "scenario_id": "SYN-B6-001",
  "parent_scenarios": ["OE-001", "OE-010"],
  "conflict_complexity": 3,
  "variables": {
    "disruption": "CARRIER_INSOLVENCY",
    "risk_layer": "GEOPOLITICAL_UNREST",
    "pax_persona": "SOLO_MINOR"
  },
  "validation_status": "VERIFIED",
  "synthetic_confidence": 0.98
}
```

## 4. Operational Guardrails

- **Novelty Threshold**: Synthetic scenarios must have a < 60% similarity score to existing scenarios to avoid redundancy.
- **Safety Filtering**: The generator is blocked from creating scenarios involving PII or sensitive real-world individual data.
- **Human-in-the-Loop (Audit)**: Every 100th synthetic scenario is reviewed by a human operator to ensure "Semantic Sane-ness."

## 5. Success Metrics (Evolution)

- **Scenario Growth**: Increase in the size of the `Scenario_Library` from 374 to 10,000+ within 30 days.
- **Discovery Rate**: Number of "Critical Logic Gaps" found via synthetic simulation that were NOT present in manual research.
- **Agent Resilience**: Improvement in agent pass-rates on "Blind" synthetic tests.
