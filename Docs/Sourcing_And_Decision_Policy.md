# Sourcing and Decision Policy

## 1. The Sourcing Hierarchy
The system does not search the open web first. It follows a strict hierarchy to preserve agency margins and operational reliability:

1. **Internal Standard Packages**: High-conversion, operationally familiar bundles.
2. **Preferred Supplier Inventory**: Contracted partners with known reliability and margins.
3. **Network/Consortium Inventory**: Access via larger agency networks/DMCs.
4. **Open Market**: Last resort for specific brand requests or niche needs.

## 2. The Decision Policy (The "Gating" Logic)
Before moving from "Intake" to "Planning," the system must evaluate the `Canonical Packet` against the `Minimum Viable Brief (MVB)`.

### A. The Decision Matrix
| State | Action | Rationale |
| :--- | :--- | :--- |
| **All Blocking Fields Complete & No Fatal Contradictions** | `PROCEED` | Enough signal to build a high-confidence first draft. |
| **Blocking Fields Missing** | `ASK_FOLLOWUP` | Cannot determine sourcing route or feasibility without these. |
| **Preferences Fuzzy but Non-Blocking** | `PRESENT_BRANCHES` | Offer 2-3 variants (e.g., "Budget" vs "Comfort") to narrow intent. |
| **Critical Contradictions / Low Confidence** | `ESCALATE` | Human planner must intervene to resolve conflict. |

### B. Blocking Fields (MVB)
A session cannot proceed to planning without:
- **Origin City**
- **Travel Window / Dates**
- **Approximate Budget**
- **Traveler Composition (Count and Age Bands)**

## 3. The "Wasted Spend" Decision Rule
The system must evaluate activity utility at a **per-person level**, not a group level.

**Rule**: If $\text{Group Size} > \text{High-Utility Users}$ for a high-cost activity $\rightarrow$ Flag as `High Wasted Spend Risk`.
**Action**: Suggest split-day alternatives (e.g., Adults do the theme park, Elderly/Toddler do a relaxed botanical garden visit).
