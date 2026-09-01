# Journey Dependency Graph & Multi-Modal Travel Operating System

**Document ID:** `PER-0442-WP-01`
**Date:** 2026-09-01
**Authors:** Waypoint OS Core Architecture Team
**Persona Alignment:** `PER-0442: Travel Operating Systems Architect`, `PER-0964: Durable Travel Workflow Architect`, `PER-0965: Travel Action Grammar Architect`
**Status:** Approved & Canonical

---

## 1. Abstract

Traditional travel management software treats itineraries as flat, chronological lists of booking confirmation numbers. When an irregular operation (IROPS) occurs—such as a 90-minute flight delay or an airspace closure—flat models fail to compute ripple effects across inter-modal connections (flights, co-terminal shuttles, high-speed rail, cruise cutoffs, and hotel check-ins).

This paper formalizes Waypoint OS's **Journey Dependency Graph (JDG)**, a directed acyclic graph (DAG) representation supporting topological ordering, cycle detection (Kahn's algorithm), co-terminal cushion variance, and automated ripple cascade severity scoring.

---

## 2. Mathematical Graph Model

Let a journey itinerary be modeled as a directed acyclic graph $G = (V, E)$, where $V$ is the set of journey nodes (flights, rail legs, transfers, hotel nights, activities) and $E$ is the set of dependency edges:

$$e = (u, v) \in E \implies t_{\text{start}}(v) \ge t_{\text{end}}(u) + \text{MCT}(u, v)$$

Where $\text{MCT}(u, v)$ represents the Minimum Connect Time buffer between nodes $u$ and $v$.

```mermaid
graph LR
    F1["Inbound Flight (LHR)"] -->|Transfer Connects| T1["Co-Terminal Shuttle (LHR → LGW)"]
    T1 -->|Requires Arrival Before| F2["Outbound Flight (LGW)"]
    F2 -->|Hotel Night For| H1["Hotel Check-in"]
    H1 -->|Same Day Activity| A1["VIP Event / Show"]
```

---

## 3. Co-Terminal Buffer & Cushion Variance Metric

For inter-airport co-terminal transfers (e.g. LHR $\leftrightarrow$ LGW, JFK $\leftrightarrow$ EWR, NRT $\leftrightarrow$ HND), transfer time must account for ground transit plus security re-screening:

$$\Delta t_{\text{cushion}} = \big( t_{\text{start}}(v) - t_{\text{end}}(u) \big) - \text{MCT}_{\text{co-terminal}}(u, v)$$

* $\Delta t_{\text{cushion}} \ge 0$: Feasible transfer with surplus buffer.
* $\Delta t_{\text{cushion}} < 0$: Infeasible connection requiring automated re-routing or departure shift.

---

## 4. Empirical Evaluation & Verification

* Topological sorting verified in $O(|V| + |E|)$ with instant cycle detection.
* Validated in `tests/test_journey_graph_operating_system.py`.
