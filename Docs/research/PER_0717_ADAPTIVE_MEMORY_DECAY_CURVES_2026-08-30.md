# PER-0717 Research Whitepaper 1: Mathematical Formulation of Adaptive Memory Half-Life Decay Curves

**Date:** 2026-08-30  
**Persona:** `PER-0717: Agent Memory Architect`  
**Classification:** Deep Exploration & Systems Design  
**Status:** Approved Architectural Formulation

---

## 1. Abstract & Problem Statement

Standard AI agent memory models suffer from **temporal amnesia** (dropping facts prematurely) or **stale context pollution** (treating 5-year-old transient preferences with equal weight to yesterday's instructions). In autonomous travel agency operations, memory facts span disparate durability domains:
- **Permanent Medical / Safety Constraints**: Life-threatening food allergies (e.g., severe peanut allergy) must never decay ($T_{1/2} = \infty$).
- **Structural Identity Credentials**: Passports, loyalty account numbers, and frequent flyer statuses remain valid across multi-year horizons ($T_{1/2} \approx 3\text{ years}$).
- **Seasonal & Transient Preferences**: Cabin class budget tolerance, pace preference, or romantic anniversary preferences decay and evolve rapidly ($T_{1/2} \approx 6\text{ months}$).

This paper establishes the mathematical modeling of adaptive half-life decay distributions comparing **Exponential** vs **Weibull** probability models.

---

## 2. Mathematical Models

### 2.1 Exponential Decay Model (Standard Baseline)

The standard exponential decay curve for memory activation $A(t)$ is defined as:
$$A(t) = A_0 \cdot \exp(-\lambda t) = A_0 \cdot 2^{-t / T_{1/2}}$$
Where:
- $A_0 \in [0.0, 1.0]$ is the initial confidence score derived from the source hierarchy.
- $t$ is the elapsed time in days since last positive confirmation.
- $T_{1/2}$ is the half-life period in days.
- $\lambda = \frac{\ln(2)}{T_{1/2}}$ is the decay constant.

**Property**: Constant hazard rate. Memory loses half its relative activation strength every $T_{1/2}$ days regardless of its age.

### 2.2 Weibull Distribution Model (Adaptive Aging)

Human preference drift frequently exhibits "infant stability" followed by accelerated aging. The two-parameter Weibull decay model accounts for variable hazard rates:
$$A_W(t) = A_0 \cdot \exp\left( -\left(\frac{t}{\eta}\right)^\beta \right)$$
Where:
- $\eta > 0$ is the scale parameter (characteristic lifespan).
- $\beta > 0$ is the shape parameter:
  - $\beta = 1.0 \implies$ Reduces to Exponential Decay.
  - $\beta < 1.0 \implies$ Heavy-tailed decay (facts proven over long periods become increasingly robust).
  - $\beta > 1.0 \implies$ Aging wear-out (fresh preferences remain stable initially, then rapidly expire).

---

## 3. Parametric Calibration for Travel Agent Workflows

| Fact Category | Optimal Model | Shape ($\beta$) | Half-Life ($T_{1/2}$) | Activation Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **Allergy & Medical Safety** | Degenerate Constant | N/A | $\infty$ | $0.00$ (Never Pruned) |
| **Loyalty & Passports** | Weibull ($\beta = 1.8$) | $1.8$ | $1,095\text{ days}$ ($3\text{ yr}$) | $0.20$ |
| **Seating & Cabin Preferences** | Exponential | $1.0$ | $730\text{ days}$ ($2\text{ yr}$) | $0.25$ |
| **Seasonal Destination Vibes** | Weibull ($\beta = 2.4$) | $2.4$ | $180\text{ days}$ ($6\text{ mo}$) | $0.30$ |
| **Disruption Tolerance History** | Exponential | $1.0$ | $365\text{ days}$ ($1\text{ yr}$) | $0.20$ |

---

## 4. Reinforcement & Re-Activation Mechanics

When a traveler explicitly re-confirms a preference on a new booking:
1. **Timestamp Reset**: $t \to 0$.
2. **Confidence Boost**: $A_0 \to \min(1.0, A_0 + 0.10)$.
3. **Half-Life Stretch**: $T_{1/2} \to T_{1/2} \cdot 1.25$ (multi-confirmation durability multiplier).

---

## 5. Architectural Implementation

Integrated directly into [`src/memory/decay_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/memory/decay_engine.py). Tested and validated against synthetic multi-year traveler timelines.
