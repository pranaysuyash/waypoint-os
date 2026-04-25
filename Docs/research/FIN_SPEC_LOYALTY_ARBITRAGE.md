# Fin Spec: Dynamic Loyalty-Cash-Ratio (FIN-REAL-008)

**Status**: Research/Draft
**Area**: Financial Optimization & Loyalty Yield

---

## 1. The Problem: "The Devalued Point"
Travelers often waste high-value points on low-value redemptions (e.g., using 50k points for a $300 flight) or, conversely, pay cash for expensive bookings where points would offer extreme leverage. The "Cents-Per-Point" (CPP) value changes daily based on dynamic pricing, making manual arbitrage impossible for most travelers.

## 2. The Solution: 'Points-Vs-Cash-Arbitrage-Protocol' (PCAP)

The PCAP allows the agent to act as a "Loyalty-Portfolio-Manager."

### Optimization Actions:

1.  **Real-Time CPP-Calculation**:
    *   **Action**: For every booking, the agent autonomously queries the cash price and the point price (across all available programs) to calculate the "Current-CPP."
2.  **Autonomous-Payment-Decision**:
    *   **Action**: If the "Current-CPP" exceeds the traveler's "Leverage-Threshold" (e.g., > 2.0 cents), the agent autonomously uses points. If not, it uses cash to preserve the points for future high-leverage opportunities.
3.  **Transfer-Partner-Optimization**:
    *   **Action**: If points are needed, the agent autonomously audits all "Transfer-Partners" (e.g., Chase Sapphire to Hyatt vs. Marriott) to find the absolute lowest point-cost for the specific inventory.
4.  **Points-Re-Shop-Watchdog**:
    *   **Action**: Even after booking with cash, the agent continues to monitor for "Point-Award-Availability." If a high-value point redemption becomes available, it autonomously cancels the cash booking (if refundable) and re-books with points.

## 3. Data Schema: `Loyalty_Arbitrage_Audit`

```json
{
  "audit_id": "PCAP-88221",
  "traveler_id": "GUID_9911",
  "booking_target": "PARK_HYATT_PARIS",
  "cash_price_usd": 950.00,
  "point_price": 40000,
  "current_cpp": 2.37,
  "traveler_cpp_threshold": 1.8,
  "execution_verdict": "BOOK_WITH_POINTS",
  "transfer_source": "CHASE_ULTIMATE_REWARDS",
  "transfer_ratio": "1:1"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Opportunity-Cost' Filter**: The agent MUST NOT use points if the traveler is planning a specific "High-Value" future trip where those points are already earmarked (e.g., "Honeymoon-Business-Class").
- **Rule 2: Point-Expiry-Protection**: The agent MUST prioritize using points that are nearing expiry, even if the CPP is slightly below the threshold.
- **Rule 3: Status-Earning-Audit**: The agent MUST calculate the "Loyalty-Earnings" (Elite Nights/Points) lost by booking with points vs. cash and factor this into the net arbitrage calculation.

## 5. Success Metrics (Arbitrage)

- **Average-CPP-Yield**: The average value achieved per point across all redemptions (Target: > 2.0).
- **Portfolio-Health**: Increase in "Liquid-Point-Value" for the traveler.
- **Arbitrage-Savings**: Total $ value saved by using points for high-leverage redemptions.
