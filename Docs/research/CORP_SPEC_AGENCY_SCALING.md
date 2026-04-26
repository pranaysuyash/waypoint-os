# Corp Spec: Agentic 'Agency-Scaling' Advisor (CORP-REAL-020)

**Status**: Research/Draft
**Area**: Agency Business Intelligence & Scaling

---

## 1. The Problem: "The Growth Blind-Spot"
Agency owners often struggle to identify where they are losing money or where the next growth opportunity lies. They may be unaware of "Unmet-Traveler-Demand" (e.g., travelers searching for destinations the agency doesn't serve) or "Inefficient-Vendor-Spending" (e.g., booking via high-cost aggregators instead of direct-partner agreements). Without "Agentic-Insights," scaling is a process of trial and error.

## 2. The Solution: 'Business-Growth-Intelligence-Protocol' (BGIP)

The BGIP acts as the "Strategic-Growth-Partner."

### Scaling Actions:

1.  **Demand-Gap Analysis**:
    *   **Action**: Analyzing traveler search queries and "Failed-Booking-Attempts" to identify missing service areas (e.g., "20% of your travelers are asking for luxury villas in Bali, but you have no villa partners in that region").
2.  **Partnership-Matchmaking**:
    *   **Action**: Suggesting specific "Strategic-Partnerships" within the SaaS ecosystem (e.g., "Connecting with 'Bali-Villas-Specialist' agency to handle these high-value requests via the Inter-Agency-Handoff-Protocol").
3.  **Vendor-Optimality Audit**:
    *   **Action**: Comparing the agency's current vendor costs against ecosystem benchmarks. If the agency is overpaying for a specific route or hotel chain, the agent identifies the "Lower-Cost-Partner-Path."
4.  **Operational-Bottleneck Detection**:
    *   **Action**: Identifying "High-Friction" workflows that are limiting scaling (e.g., "Your human agents are spending 40% of their time on visa queries; consider enabling the 'Visa-Watchdog' autonomous tier to increase capacity").

## 3. Data Schema: `Agency_Growth_Insight`

```json
{
  "insight_id": "BGIP-99221",
  "agency_id": "AGENCY_ALPHA",
  "opportunity_type": "DEMAND_GAP_DETECTED",
  "identified_market": "BALI_LUXURY_VILLAS",
  "estimated_revenue_loss_usd": 15000.00,
  "recommended_partner_id": "BALI_VILLA_EXPERTS",
  "status": "INSIGHT_PUBLISHED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Suitability-Retention' Guardrail**: Scaling advice MUST prioritize maintaining the agency's "Quality-Standard." The agent MUST NOT suggest high-volume/low-quality partners if the agency's brand is "Luxury-Concierge."
- **Rule 2: Confidentiality-Boundary**: Demand-gap data MUST be aggregated and anonymized at the ecosystem level. Agencies see their *own* gaps but only see the *capability* of potential partners, not their specific traveler data.
- **Rule 3: Actionable-Recommendations**: Insights MUST include a specific "Execution-Path" (e.g., "Click here to initiate a partnership request" or "Enable this automation tier now").

## 5. Success Metrics (Scaling)

- **Unmet-Demand-Capture**: % of identified revenue gaps that are successfully closed through new partnerships or automation.
- **Operational-Capacity-Increase**: Number of additional travelers the agency can support after implementing agentic scaling advice.
- **Margin-Expansion-Rate**: Increase in net profit margin through vendor optimization and automation.
