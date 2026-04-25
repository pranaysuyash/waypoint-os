# Ops Spec: Secondary-Equipment-Rental (OPS-REAL-013)

**Status**: Research/Draft
**Area**: Logistics & Specialized Equipment

---

## 1. The Problem: "The Logistics of Gear"
Travelers with specialized needs (photographers, parents, athletes) often struggle with the logistics of transporting high-end or bulky equipment. Shipping it is risky (damage/loss), and checking it is expensive and physically taxing. However, sourcing reliable, high-quality rentals in a foreign destination is a time-consuming vetting process.

## 2. The Solution: 'Destination-Gear-Sourcing-Protocol' (DGSP)

The DGSP allows the agent to act as a "Virtual-Equipment-Manager."

### Sourcing Actions:

1.  **Vertical-Inventory-Search**:
    *   **Action**: Identifying the exact equipment required (e.g., "Sony Alpha 7S III with 24-70mm GM II lens" or "Bugaboo Fox 5 stroller") and querying vetted local rental houses.
2.  **Quality-Verification-Audit**:
    *   **Action**: Verifying the "Condition-Standard" of the gear (e.g., shutter count for cameras, safety-check dates for strollers) via the vendor's API or a direct verification ping.
3.  **In-Room-Delivery-Coordination**:
    *   **Action**: Autonomously coordinating with the destination hotel to receive the equipment and have it waiting in the traveler's room before check-in.
4.  **Rental-Insurance-Bonding**:
    *   **Action**: Autonomously auditing the rental contract for damage-waivers and ensuring the traveler's existing umbrella insurance covers the high-value rental.

## 3. Data Schema: `Equipment_Rental_Engagement`

```json
{
  "engagement_id": "DGSP-88221",
  "traveler_id": "GUID_9911",
  "equipment_class": "PROFESSIONAL_CINEMA_GEAR",
  "item_list": ["SONY_A7SIII", "GM_24_70_LENS", "SHOGUN_MONITOR"],
  "vendor": "PRO_CAM_RENTALS_NYC",
  "delivery_target": "HOTEL_ROOM_404",
  "rental_window": "2026-11-12T10:00:00Z - 2026-11-15T18:00:00Z",
  "insurance_verified": true,
  "contract_status": "SIGNED_PAID"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Spec-Match' Rule**: The agent MUST NOT book equipment that does not perfectly match the traveler's technical requirements (e.g., specific lens mounts or firmware versions).
- **Rule 2: The 'Sanitization-Verification'**: For health-sensitive gear (e.g., baby strollers, CPAP machines), the agent MUST receive a "Sanitization-Certificate" from the vendor before final check-out.
- **Rule 3: Return-Logistics-Automation**: The agent autonomously coordinates the courier pick-up from the hotel lobby at the end of the trip, ensuring the traveler is "Hands-Free" upon departure.

## 5. Success Metrics (Logistics)

- **Gear-Match-Precision**: % of rentals that met 100% of the traveler's technical specifications.
- **Hands-Free-Ratio**: % of specialized trips where the traveler did not have to transport their own primary gear.
- **Delivery-On-Time**: % of gear waiting in-room at the exact check-in timestamp.
