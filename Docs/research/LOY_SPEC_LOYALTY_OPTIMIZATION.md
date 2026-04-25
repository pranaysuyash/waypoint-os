# Loy Spec: Loyalty & Status-Optimization (LOY-REAL-001)

**Status**: Research/Draft
**Area**: Value Maximization & Elite Status

---

## 1. The Problem: "The Wasted Point"
Travelers often miss out on thousands of points and elite-status benefits because they don't know which frequent flyer program (FFP) to credit a flight to, or they fail to check for "Mileage-Runs" and "Status-Challenges." Most OTAs simply ask for a number; they don't provide "Strategic-Advisory."

## 2. The Solution: 'Points-Arbitrage-Protocol' (PAP)

The PAP allows the agent to act as a "Loyalty-Strategist" by optimizing every segment for maximum return-on-spend.

### Strategic Actions:

1.  **Earnings-Comparison-Audit**:
    *   **Action**: Comparing the earnings across multiple FFP partners (e.g., "Crediting this Qatar flight to British Airways earns 10k Avios vs 2k Qatar Miles"). The agent MUST recommend the "High-Yield" path.
2.  **Upgrade-Probability-Scouting**:
    *   **Action**: Continuously monitoring seat-maps and fare-buckets (e.g., 'R' or 'I' classes) to identify "Instrument-Upgrade" opportunities (using traveler's points or vouchers).
3.  **Status-Challenge-Triggering**:
    *   **Action**: If a traveler has high-status on one airline (e.g., Delta Platinum) and is booking with another (e.g., United), the agent MUST autonomously check for "Status-Match" or "Challenge" eligibility to grant the traveler immediate benefits.

## 3. Data Schema: `Loyalty_Strategy_Recommendation`

```json
{
  "recommendation_id": "PAP-88221",
  "itinerary_id": "ITIN-9911",
  "traveler_loyalty_profiles": ["BA_GOLD", "MARRIOTT_PLATINUM"],
  "segment_optimizations": [
    {
      "segment": "LHR-JFK",
      "best_credit_program": "BA_AVIOS",
      "est_earnings": 12500,
      "upgrade_eligible": true,
      "upgrade_cost_points": 25000
    }
  ],
  "status_benefit_audit": ["Lounge access confirmed", "Priority boarding available"]
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Tier-Point-Targeting' Rule**: If a traveler is within 10% of the next status tier, the agent MUST prioritize earning "Tier-Points" over "Redeemable-Miles."
- **Rule 2: Automated-Member-Enrollment**: If a traveler is booking with a new airline, the agent MUST offer to "Auto-Enroll" them to ensure no points are lost.
- **Rule 3: Hotel-Benefit-Stacking**: The agent MUST prioritize booking through "Preferred-Partner" channels (e.g., Virtuoso/FHR) that offer "Free-Breakfast" and "Upgrades" if the cost is equivalent to the public rate.

## 5. Success Metrics (Loyalty)

- **Total-Points-Captured**: Increase in aggregate loyalty currency earned per traveler vs baseline.
- **Upgrade-Success-Rate**: % of requested upgrades successfully cleared.
- **Status-Advancement-Speed**: Reduction in time/spend required for a traveler to reach the next elite tier.
