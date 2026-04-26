# Fin Spec: Agentic 'Vendor-Negotiation' Pulse (FIN-REAL-027)

**Status**: Research/Draft
**Area**: Agency Vendor Management & Margin Optimization

---

## 1. The Problem: "The Aggregator-Markup-Tax"
Early-stage agencies rely heavily on aggregators (GDS, bed-banks, wholesalers) to access inventory. While convenient, these aggregators take a "Markup-Tax" that eats into the agency's margin. As an agency scales its volume with a specific vendor (e.g., a hotel chain or a cruise line), they often cross a threshold where a "Direct-Contract" would yield significantly better margins and exclusive perks. Without "Agentic-Monitoring," these thresholds are often missed.

## 2. The Solution: 'Direct-Contract-Optimization-Protocol' (DCOP)

The DCOP acts as the "Margin-Maximizer."

### Negotiation Actions:

1.  **Volume-Threshold-Monitoring**:
    *   **Action**: Monitoring the agency's aggregate booking volume and spend with specific vendors across all aggregators.
2.  **Negotiation-Leverage-Alert**:
    *   **Action**: Identifying when the agency has reached a "Critical-Mass" (e.g., $100k annual spend with Vendor X) that warrants a direct negotiation.
3.  **Margin-Impact-Analysis**:
    *   **Action**: Calculating the "Projected-Margin-Increase" if the agency moves from an aggregator to a direct contract (e.g., "Moving to a direct contract with Marriott would increase your net margin by 4%").
4.  **Autonomous-Inquiry-Drafting**:
    *   **Action**: Drafting a professional "Partnership-Inquiry" to the vendor's sales team, backed by the agency's verified volume data, to initiate the direct contract discussion.

## 3. Data Schema: `Vendor_Negotiation_Opportunity`

```json
{
  "opportunity_id": "DCOP-88221",
  "vendor_name": "LUXURY_HOTEL_GROUP_X",
  "current_annual_spend": 125000,
  "leverage_score": 0.85,
  "projected_margin_lift": 0.045,
  "status": "NEGOTIATION_OPPORTUNITY_IDENTIFIED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Verified-Volume' Mandate**: Negotiation alerts MUST be based on verified booking data from the agency's own operational history.
- **Rule 2: Aggregator-Relationship-Balance**: The agent MUST consider the "Total-Ecosystem-Benefit" (e.g., volume discounts across multiple vendors) provided by an aggregator before suggesting a direct break for a single vendor.
- **Rule 3: Owner-Execution-Gate**: The agent MUST NOT initiate contact with a vendor without explicit owner approval. The agent drafts the strategy; the owner executes the relationship.

## 5. Success Metrics (Negotiation)

- **Direct-Contract-Conversion-Rate**: % of identified opportunities that result in a successful direct contract.
- **Net-Margin-Expansion**: Total increase in agency net margin attributed to moving bookings to direct contracts.
- **Vendor-Perk-Unlock-Count**: Number of exclusive perks (e.g., "Free Breakfast for all Agency travelers") negotiated through direct contracts.
