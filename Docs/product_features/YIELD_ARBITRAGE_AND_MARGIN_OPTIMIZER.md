# FEATURE: Yield Arbitrage & Margin Optimizer

## 1. Business Purpose
To maximize agency profitability by automatically identifying better pricing, inventory, or commission opportunities between the "Booking Date" and the "Travel Date". This turns the agency from a "Fixed Margin" business to a "Yield Managed" one.

## 2. User POV
- **Agency Owner (P2)**: Sees "Found Savings" or "Margin Upside" notifications in the dashboard.
- **Traveler (S1)**: Receives a "Complimentary Upgrade" (funded by the arbitrage) or a "Loyalty Refund".

## 3. Internal Logic & Workflows

### A. Price-Drop Monitoring (Shadow Booking)
1. **Initial Baseline**: Record the confirmed price and vendor.
2. **Periodic Re-scan**: The engine re-queries GDS/Direct APIs for the same inventory (or better) at regular intervals.
3. **Threshold Detection**: If price drops by > $X (net of cancellation fees), trigger an alert.
4. **Execution**: If "Auto-Execute" is on, re-book the lower rate and cancel the higher one.

### B. Commission Arbitrage
1. **Multi-Source Comparison**: Compare the same hotel across 3 suppliers (e.g., Expedia, Bedsonline, Direct).
2. **Margin Calculation**: Calculate `Net Price + Commission + Override`.
3. **Switch Logic**: If a different supplier offers > 3% extra margin for the same room type, notify the agent to "Switch & Save".

### C. Yield Re-Investment
- The system can automatically re-invest "Found Savings" into traveler delight.
- Example: "Saved $100 on the flight. Suggestion: Apply $50 to a VIP Lounge Pass (delight) and keep $50 (margin)."

## 4. Technical Constraints
- **Cancellation Policy Parser**: The engine MUST understand the "Non-Refundable" and "Last Date to Cancel" fields with 100% accuracy.
- **API Rate Limits**: Intelligent scheduling of re-scans to avoid GDS look-to-book penalties.
- **Inventory Parity**: Ensuring "Standard King" at Vendor A is identical to "Standard King" at Vendor B.

## 5. Success Metrics
- **Found Margin**: Total $ gained through arbitrage.
- **Upgrade Rate**: % of trips where arbitrage funded a traveler upgrade.
- **Risk Avoidance**: Number of "Near-Misses" where cancellation fees would have exceeded savings.
