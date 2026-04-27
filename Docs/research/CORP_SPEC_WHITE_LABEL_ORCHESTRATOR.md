# Corp Spec: Agentic 'Agency-White-Label' Orchestrator (CORP-REAL-030)

**Status**: Research/Draft
**Area**: Agency Revenue Expansion & Platform Reseller Architecture

---

## 1. The Problem: "The Single-Revenue-Stream Ceiling"
Successful agencies hit a "Revenue-Ceiling" when their growth is constrained by the number of bookings they can personally manage. They have built operational intelligence, vendor relationships, and brand equity — but no mechanism to "Productize" that intelligence and resell it to others. Without a "White-Label-Orchestration" capability, agencies can't become platforms in their own right.

## 2. The Solution: 'White-Label-Orchestration-Protocol' (WLOP)

The WLOP acts as the "Agency-Platform-Factory."

### Orchestration Actions:

1.  **White-Label-Instance-Provisioning**:
    *   **Action**: Allowing a parent agency to provision "Branded-Sub-Instances" of the AI platform for resale to partners (e.g., a hotel chain that wants to offer AI-powered trip planning for its guests, or a corporate HR team offering employee travel concierge).
2.  **Knowledge-Inheritance-Control**:
    *   **Action**: Defining which elements of the parent agency's knowledge base (vendor relationships, itinerary DNA, pricing logic) are "Inherited" by the sub-instance vs. which are "Proprietary-Walls" not accessible to the reseller.
3.  **Revenue-Share-Metering**:
    *   **Action**: Autonomously metering the sub-instance's usage (conversations, bookings, API calls) and calculating the revenue-share owed to the parent agency based on pre-agreed "License-Terms."
4.  **Brand-Governance-Enforcement**:
    *   **Action**: Ensuring the sub-instance operates within "Brand-Safety-Rails" defined by the parent agency — no competitor promotions, no policy violations, no off-brand communication styles.

## 3. Data Schema: `White_Label_Instance`

```json
{
  "instance_id": "WLOP-88221",
  "parent_agency_id": "AGENCY_ALPHA",
  "reseller_name": "LUXURY_HOTEL_GROUP_X",
  "inherited_knowledge": ["VENDOR_NETWORK", "REGIONAL_EXPERTISE_ASIA"],
  "proprietary_walls": ["PRICING_LOGIC", "COMMISSION_STRUCTURES"],
  "monthly_revenue_share_usd": 4500,
  "brand_rails_status": "COMPLIANT",
  "status": "INSTANCE_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Sovereignty-Preservation' Guarantee**: The parent agency's proprietary pricing logic and commission structures MUST be completely inaccessible to the white-label reseller under any condition.
- **Rule 2: Brand-Safety-Lockout**: If a sub-instance attempts to promote a competitor or violate brand rails, the agent MUST autonomously suspend the offending output and alert the parent agency owner.
- **Rule 3: Usage-Metering-Accuracy**: Revenue-share calculations MUST be based on cryptographically tamper-proof usage logs to prevent billing disputes.

## 5. Success Metrics (White-Label)

- **Reseller-Instance-Growth**: Number of active white-label sub-instances per parent agency.
- **White-Label-Revenue-Contribution**: % of parent agency revenue generated through white-label licensing vs. direct bookings.
- **Sub-Instance-Booking-Volume**: Total booking volume facilitated through white-label instances.
