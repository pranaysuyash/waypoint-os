# Multi-Currency Hedging & Dynamic FX Slippage Protection

**Document Version:** 1.0.0  
**Date:** 2026-08-30  
**Author:** Waypoint OS Financial Operations Architecture  
**Status:** Active Specification (`RES-07`)

---

## 1. FX Slippage & Agency Margin Degradation

High-touch travel agencies frequently operate across multi-currency settlement cycles:
1. **Day 0**: Traveler is quoted \$10,000 USD (based on €9,200 EUR supplier cost at 1.087 EUR/USD + \$800 margin).
2. **Day 0**: Traveler pays 25% deposit (\$2,500 USD).
3. **Day 45**: Traveler pays remaining 75% balance (\$7,500 USD).
4. **Day 50**: Agency settles wholesale invoice with Italian DMC in EUR (€9,200).

If EUR strengthens to 1.150 USD/EUR by Day 50, the wholesale cost increases from \$10,000 to \$10,580 USD, **completely wiping out agency profit and creating an operational loss**.

---

## 2. Dynamic Forward Spread Buffer Algorithm

Waypoint OS calculates an automated **Dynamic FX Volatility Buffer** $\sigma_{\text{FX}}$ integrated into quoted retail markups:

$$\text{QuotedRate}(C_{\text{retail}}, C_{\text{supplier}}, \Delta t) = \text{SpotRate} \times \left(1 + \beta_{\text{base}} + \gamma \cdot \sqrt{\frac{\Delta t}{365}} \cdot \text{Vol}_{30}(C_{\text{supplier}})\right)$$

where:
- $\text{Vol}_{30}$ is the 30-day historical annualized volatility of the foreign currency pair.
- $\Delta t$ is the days remaining until final supplier settlement.
- $\gamma$ is the agency risk tolerance coefficient (default 1.96 for 95% Value-at-Risk confidence).

---

## 3. Automated Hedging & Early Forward Settlement Triggers

When the tracked exposure on active itineraries exceeds \$50,000 in a foreign currency:
1. The engine triggers an advisory alert to lock in wholesale forward contracts via integrated banking APIs (e.g. Wise for Business / Airwallex).
2. For refundable bookings with favorable cancellation terms, early settlement is recommended when spot rates cross the lower bound threshold.
