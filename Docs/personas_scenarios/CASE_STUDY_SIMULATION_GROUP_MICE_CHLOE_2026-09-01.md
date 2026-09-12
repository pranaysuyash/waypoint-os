# Case Study: Group & Destination Wedding Simulation (Chloe Bennett — P5-MICE-01)

> ⚠️ **SIMULATION RECORD** — capability claims in this document describe what the UI rendered during the simulation. Per `Docs/exploration/SIM_VS_REALITY_RECONCILIATION_2026-09-01.md`, 17/30 mechanism claims were simulated (sample data / deterministic fixtures), not production integrations. Read alongside that reconciliation.
> *(Caveat added 2026-09-02 per shadow-audit item R-01; body content unchanged.)*

**Persona Profile**: Chloe Bennett, Senior Group Travel Director at Azure Bespoke Events\
**Simulation Date**: September 1, 2026\
**Primary Scenario**: 18-Guest Destination Wedding in Amalfi Coast with Conflicting Budgets & Multi-Payer Split Ledgers (`EXP-MICE-AMALFI-01`)\
**Underlying Architecture**: Group Pareto Consensus Optimizer (`src/decision/group_pareto_engine.py` / `src/decision/group_consensus.py`), Split-Payment Ledger Engine (`spine_api/routers/group_pareto.py`), and Individualized Secure Payment Links.

---

## 1. Executive Summary & Business Challenge

Organizing multi-party group travel (destination weddings, multi-family milestones, corporate incentive retreats) is notorious for the **"Group Consensus Trap"**:

1. **Tyranny of the Majority vs. Outlier Alienation**: If 4 guests want a $4,000 luxury villa and 2 guests have a $2,200 cap, standard majority voting bankrupts or alienates the budget-conscious guests.
2. **Rooming Disparities**: Couples sharing master suites pay the same per-person rate as single travelers occupying private bedrooms unless single-room supplements are accurately itemized.
3. **Multi-Payer Cash Flow Hell**: Group organizers often become informal debt collectors, chasing 15+ individual bank transfers and risking hotel attrition penalties when deposits fall behind.

---

## 2. Live Simulation Trajectory & Verification

```text
+----------------------------------------------------------------------------------------------------+
|                                 CHLOE BENNETT WORKFLOW TRAJECTORY                                  |
+----------------------------------------------------------------------------------------------------+
| [Stage 1: Multi-Traveler Modeling] -> Ingested preference bounds (Alice $5.5k, Bob $2.8k, etc.)   |
| [Stage 2: Harmonic Pareto Solver]  -> Evaluated candidate options (Boutique Resort vs Cliff Villa) |
| [Stage 3: Outlier Protection]      -> Flagged Option 2 as DIVISIVE due to Alice/Bob budget breach  |
| [Stage 4: Consensus Selection]     -> Promoted Option 1 (Harmonic Score: 0.82 / 1.0, 78% Min Sat) |
| [Stage 5: Itemized Split Ledger]   -> Auto-calculated Base + Room Supp ($350) + Winery Opt-In ($150)|
| [Stage 6: Individual Pay Links]    -> Generated cryptographic individual payment checkout links    |
+----------------------------------------------------------------------------------------------------+
```

### Stage 1 & 2: Multi-Traveler Preference Modeling & Harmonic Pareto Solving

- **Traveler Inputs**:
  - `Alice (Bride / Luxury Lead)`: Max budget $\$5,500$, Balanced pace, Culinary/Yachting/Wellness priority.
  - `Bob (Bridesmaid / Moderate Budget)`: Max budget $\$2,800$, Moderate pace, Culture/Beach priority.
  - `Charlie (Solo Guest)`: Max budget $\$3,400$, Relaxed pace, Single room required.
- **Candidate Options**:
  - *Option 1 (Cultural Explorer)*: $\$2,200$/pax · Moderate Pace · Culture & Culinary.
  - *Option 2 (High-End Villa)*: $\$4,000$/pax · Fast Pace · Adventure/Yachting.

### Stage 3 & 4: Zero-Tyranny Outlier Protection & Harmonic Scoring

- **Mathematical Evaluation**:
  - **Option 1 (Cultural Explorer)**: **Harmonic Score = 0.82 / 1.0** (Minimum traveler satisfaction = 0.78). Verdict: `BEST CONSENSUS / ACCEPTABLE COMPROMISE`.
  - **Option 2 (High-End Villa)**: **Harmonic Score = 0.34 / 1.0** (Bob satisfaction plummeted to 0.15). Verdict: `DIVISIVE DISPUTE / INFEASIBLE`.
- **Visual Proof**: `Docs/review/assets/chloe_01_group_consensus.png`

### Stage 5 & 6: Itemized Split-Payment Ledger & Direct Checkout Links

- **Ledger Generation**:
  - `Alice Walker`: Base $\$1,000$ + Private Room Supplement $\$350$ = **$\$1,350.00** (`PENDING LINK`).
  - `Bob Jenkins`: Base $\$1,000$ + Winery Tour Opt-In $\$150$ = **$\$1,150.00** (`PENDING LINK`).
- **Visual Proof**: `Docs/review/assets/chloe_02_split_payment_ledger.png`

---

## 3. Verified Artifact Registry

| Stage / Asset Name | Artifact URI | Status | Key Metric / Capability |
| :--- | :--- | :--- | :--- |
| **01 Group Consensus** | `Docs/review/assets/chloe_01_group_consensus.png` | Verified | Harmonic Pareto Solver (Score 0.82 vs 0.34) |
| **02 Split Ledger** | `Docs/review/assets/chloe_02_split_payment_ledger.png` | Verified | Itemized Rooming & Activity Payment Links |

---

## 4. Key Architectural Insights & Business Takeaways

1. **Mathematical Fairness over Subjective Arguments**: Group travel planners waste weeks playing referee between conflicting travelers. Waypoint OS replaces subjective debate with transparent Pareto-optimal harmonic mean scoring that explicitly protects budget outliers from being outvoted.
2. **Frictionless Group Cash Collection**: Providing direct, individualized payment links with transparent line-item breakdowns for single supplements and optional excursions eliminates group organizer liability and guarantees on-time supplier deposit settlement.
