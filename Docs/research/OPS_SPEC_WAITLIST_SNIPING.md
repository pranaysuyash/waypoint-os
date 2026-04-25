# Ops Spec: Waitlist-Management-Logic (OPS-REAL-006)

**Status**: Research/Draft
**Area**: Inventory Acquisition & Yield Optimization

---

## 1. The Problem: "The Sold-Out Dead End"
Travelers frequently find their "Ideal" flight or hotel is sold out. Most platforms simply show "Unavailable" and stop. However, cancellations happen constantly. A seat or room might open up for only 30 seconds before someone else grabs it. Human travelers cannot monitor availability 24/7.

## 2. The Solution: 'Inventory-Sniping-Protocol' (ISP)

The ISP allows the agent to act as a "High-Frequency-Inventory-Monitor" by polling the GDS/APIs for specific inventory releases.

### Sniping Actions:

1.  **Inventory-Delta-Polling**:
    *   **Action**: Continuously querying the GDS for specific fare classes (e.g., 'J' class on BA117) or hotel room categories at a high frequency (frequency determined by 'Trip-Urgency').
2.  **Pre-Authorized-Execution-Trigger**:
    *   **Action**: If a match is found, the agent MUST autonomously execute the booking immediately (using pre-authorized payment/identity from SIP-001) before the inventory is lost.
3.  **Shadow-Itinerary-Holding**:
    *   **Action**: While sniping the ideal option, the agent maintains a "Safety-Option" (refundable) and autonomously cancels it the second the sniped option is secured.

## 3. Data Schema: `Inventory_Snipe_Request`

```json
{
  "snipe_id": "ISP-88221",
  "traveler_id": "GUID_9911",
  "target_inventory": {
    "type": "FLIGHT",
    "airline": "EMIRATES",
    "flight_number": "EK201",
    "date": "2026-11-12",
    "required_class": ["J", "C"]
  },
  "max_price_usd": 4500.00,
  "execution_mode": "AUTO_BOOK",
  "safety_itinerary_id": "ITIN-REFUNDABLE-9911",
  "status": "ACTIVE_POLLING"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Millisecond-Race' Rule**: The agent MUST prioritize API-direct connections over screen-scraping to minimize latency during high-demand inventory releases.
- **Rule 2: Automated-Payment-Retry**: If the primary card fails during the snipe, the agent MUST immediately attempt the "Backup-Card" (FIN-002) within 2 seconds to avoid losing the slot.
- **Rule 3: Snipe-Window-Scaling**: For "High-Value" elite travelers (LOY-001), the agent scales the polling frequency to the maximum allowed by vendor rate-limits.

## 5. Success Metrics (Acquisition)

- **Snipe-Success-Rate**: % of requested sold-out items successfully captured.
- **Acquisition-Latency**: Time from "Inventory-Release" to "Booking-Confirmation" (Target: < 5 seconds).
- **Traveler-Value-Unlocked**: Estimated value of itineraries that would have been "Impossible" without sniping.
