# Research & Exploration: Game-Theoretic Multi-Party Preference Negotiation in Group Travel

**Persona:** `Family & Group Travel Architect`  
**System:** Waypoint OS (`pranaysuyash/travel_agency_agent`)  
**Date:** August 29, 2026  
**Status:** Canonical Specialist Exploration  

---

## 1. Problem Formulation: Group Travel Coordination Failure

Group travel planning is a classic multi-objective social choice problem with asymmetric information and non-convex utility functions:
* **The Dictator Failure**: Planning to satisfy the most vocal group member leaves others feeling alienated.
* **The Mean Failure**: Averaging preferences (e.g. averaging a \$500 budget and \$3,000 budget into \$1,750) creates an option that satisfies neither party.

---

## 2. Mathematical Solution: Pareto Frontier & Harmonic Dissatisfaction Penalty

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            MULTI-PARTY CONSENSUS OPTIMIZATION                               │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│ 1. Individual Utility Models  │ 2. Pareto Frontier Pruning    │ 3. Harmonic Group Scoring   │
│    - Budget constraint curve  │    - Drop dominated proposals │    - Penalize severe worst- │
│    - Activity interest vector │    - Preserve trade-off set   │      case dissatisfaction   │
│    - Pacing preference        │    - Guarantee efficiency     │    - Composite = 0.7μ + 0.3m│
└───────────────────────────────┴───────────────────────────────┴─────────────────────────────┘
```

### 2.1 The Harmonic Consensus Formula
$$\text{ConsensusScore} = 0.70 \times \left( \frac{1}{N} \sum_{i=1}^N u_i \right) + 0.30 \times \min_{i \in [1..N]} (u_i)$$

This mathematical formulation guarantees that no proposal can achieve a high group score if even one participant experiences severe dissatisfaction.
