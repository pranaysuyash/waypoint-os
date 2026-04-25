# Ops Spec: Dynamic Baggage-Forwarding (OPS-REAL-009)

**Status**: Research/Draft
**Area**: Logistics & Personal Comfort

---

## 1. The Problem: "The Check-In Friction"
Checking bags is one of the highest friction points in travel (lines, loss-risk, wait-times). However, for many trips, it's the "Default." Travelers often don't realize that shipping their bags ahead (e.g., via LuggageForward, ShipStick) is often comparable in cost to airline "Excess-Baggage-Fees" but provides a "Hands-Free" experience.

## 2. The Solution: 'Luggage-Separation-Protocol' (LSP)

The LSP allows the agent to act as a "Personal-Logistics-Coordinator."

### Optimization Actions:

1.  **Total-Baggage-Cost-Comparison**:
    *   **Action**: Calculating the "Real-Cost" of checked bags (including taxi-size upgrades for large suitcases) vs "Forwarding-Services" for the specific route and weight.
2.  **Autonomous-Service-Booking**:
    *   **Action**: If "Forwarding" is chosen, the agent autonomously coordinates the courier pick-up from the traveler's home/office and ensures the bags are delivered *inside* the destination hotel room before the traveler arrives.
3.  **Sync-With-Itinerary-Shift**:
    *   **Action**: If the flight is delayed or rerouted, the agent MUST autonomously update the baggage-forwarding carrier to ensure the luggage doesn't sit unattended in a hotel lobby.
4.  **Customs-Documentation-Automation**:
    *   **Action**: For international forwarding, the agent autonomously generates and signs the necessary "Unaccompanied-Baggage-Customs-Declarations."

## 3. Data Schema: `Baggage_Logistics_Audit`

```json
{
  "audit_id": "LSP-88221",
  "traveler_id": "GUID_9911",
  "logistics_mode": "THIRD_PARTY_FORWARDING",
  "carrier": "LUGGAGE_FORWARD",
  "est_checked_bag_cost_usd": 150.00,
  "forwarding_cost_usd": 175.00,
  "premium_paid_for_convenience": 25.00,
  "pickup_confirmed": "2026-11-10T10:00:00Z",
  "delivery_target": "HOTEL_ROOM_302",
  "customs_packet_status": "SUBMITTED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Margin-of-Convenience'**: The agent is authorized to choose "Forwarding" if the cost is within 20% of the "Checked-Bag" fee, assuming the traveler has opted for "Premium-Comfort" settings.
- **Rule 2: The 'Hotel-Verified-Receipt'**: The agent MUST NOT consider a bag "Delivered" until it receives a "Room-Placement-Verification" from the destination hotel's concierge API.
- **Rule 3: Dangerous-Goods-Filter**: The agent MUST autonomously audit the traveler's "Packing-Template" to ensure no prohibited items (e.g., lithium batteries, aerosols) are included in forwarded luggage that might be transported via cargo aircraft.

## 5. Success Metrics (Logistics)

- **Hands-Free-Trip-Ratio**: % of trips where the traveler did not have to touch a suitcase between home and hotel.
- **Delivery-Precision**: % of bags waiting in-room *before* traveler check-in.
- **Logistics-Yield**: $ saved by avoiding peak-season airline excess-baggage gouging.
