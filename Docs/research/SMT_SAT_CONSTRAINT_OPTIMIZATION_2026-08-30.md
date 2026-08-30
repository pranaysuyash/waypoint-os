# SMT / SAT Constraint Optimization for Itinerary Synthesis

**Document Version:** 1.0.0  
**Date:** 2026-08-30  
**Author:** Waypoint OS Agentic Systems & Optimization Team  
**Status:** Active Specification (`RES-05`)

---

## 1. Problem Formulation: The Hard Geometry of Travel

Synthesizing a multi-city international itinerary is not merely a language generation task; it is a hard combinatorial satisfaction and optimization problem (NP-hard). Modern LLMs frequently hallucinate temporally impossible layovers, reverse time zones, violation of hotel check-in/check-out boundaries, or budget blowouts.

### Core Mathematical Constraints:
1. **Temporal Non-Overlap & Layover Bounds**:
   $$\forall i \in \{1 \dots n-1\}, \quad \text{Arrival}(F_i) + \text{MCT}(A_i) \le \text{Departure}(F_{i+1})$$
   where $\text{MCT}(A_i)$ is the Minimum Connection Time for airport $A_i$ (e.g. 90 min at CDG / LHR, 45 min at MUC).

2. **Circadian & Pacing Geometry**:
   $$\sum_{k=1}^m \text{ActivityDuration}(D_j, k) + \sum_{k=1}^{m-1} \text{TransitTime}(k, k+1) \le \text{MaxActiveHours}(T)$$
   where travelers with infant/senior tags enforce $\text{MaxActiveHours} \le 5.5\text{ hrs/day}$.

3. **Cumulative Budget & Currency Bounds**:
   $$\sum_{i=1}^n \text{FlightCost}_i + \sum_{j=1}^m \text{HotelCost}_j + \sum_{k=1}^p \text{ActivityCost}_k \le \text{TotalBudget}$$

---

## 2. Solver Architecture: Z3 / MiniZinc Integration

Waypoint OS decouples semantic intention extraction from deterministic constraint solving:

```
[ Traveler Prompt / Audio ] 
        │
        ▼ (LLM NER)
[ Abstract Constraint AST ] ──► [ Z3 SMT Solver Engine ] ──► [ Mathematically Feasible Skeleton ]
                                                                      │
                                                                      ▼ (LLM Synthesis)
                                                             [ Rich Written Proposal ]
```

### Z3 SMT Python Formulation Example:
```python
from z3 import Int, Solver, sat, Optimize

def solve_layover_and_hotel_windows(flights, hotel_nights, budget_limit):
    opt = Optimize()
    # Variables
    total_cost = Int('total_cost')
    
    # Assert Hard Feasibility Bounds
    opt.add(total_cost <= budget_limit)
    opt.maximize(-total_cost) # Maximize margin / optimize value
    
    if opt.check() == sat:
        model = opt.model()
        return True, model
    return False, None
```

---

## 3. Verification & Benchmark Standard

All synthesized itineraries must pass the `check_itinerary_feasibility()` gate prior to presenting proposals to advisors or travelers.
