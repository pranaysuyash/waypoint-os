# Ops Spec: Dynamic Seat-Map Watcher (OPS-REAL-014)

**Status**: Research/Draft
**Area**: Cabin Comfort & Tactical Seating

---

## 1. The Problem: "The Middle Seat Lottery"
Flight seating is dynamic. Between initial booking and departure, many travelers cancel or move. A flight that was "full" 24 hours ago might have empty rows or "Shadow-Empty-Middle-Seats" 4 hours before departure. Most travelers never check their seat map after initial selection, missing out on significantly better comfort (e.g., a row to themselves) that costs $0.

## 2. The Solution: 'Cabin-Density-Optimization-Protocol' (CDOP)

The CDOP allows the agent to act as a "Tactical-Seat-Stalker."

### Monitoring Actions:

1.  **Iterative-Map-Polling**:
    *   **Action**: Polling the GDS/NDC seat-map at strategic intervals (T-48h, T-24h, T-12h, T-4h).
2.  **Row-Density-Scoring**:
    *   **Action**: Assigning a "Density-Score" to available rows. (e.g., a row with 0/3 occupied is a "Perfect-Score"; 1/3 occupied with the traveler is an "Empty-Middle-Win").
3.  **Preferred-Zone-Sniping**:
    *   **Action**: Monitoring "Premium-No-Fee" zones (e.g., front of cabin or exit rows) that were previously occupied. If a "Shadow-Empty" appears (due to a status-upgrade of another passenger), the agent autonomously grabs it.
4.  **The 'Empty-Middle-Shield'**:
    *   **Action**: If the traveler is in an aisle/window, the agent monitors the middle seat. If the middle seat remains unbooked, the agent "holds" the position. If the middle seat is booked, the agent scans for another row where the middle is still empty.

## 3. Data Schema: `Seat_Watch_Engagement`

```json
{
  "engagement_id": "CDOP-88221",
  "traveler_id": "GUID_9911",
  "pnr": "XY77ZA",
  "current_seat": "12C",
  "target_density": "EMPTY_MIDDLE",
  "poll_history": [
    {"timestamp": "2026-11-12T10:00:00Z", "empty_rows": 2},
    {"timestamp": "2026-11-12T14:00:00Z", "empty_rows": 0}
  ],
  "autonomous_move_enabled": true,
  "max_row_distance_from_front": 10
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Window-Aisle-Preference'**: The agent MUST NOT move a traveler from their preferred seat type (e.g., Aisle) to a different type (e.g., Window) unless it results in a "Full-Empty-Row" (3 seats).
- **Rule 2: The 'Equipment-Swap-Audit'**: If the airline swaps aircraft (e.g., 737 to A320), the agent MUST immediately re-run the CDOP to ensure the traveler wasn't dumped into a "Default-Middle-Seat."
- **Rule 3: T-Minus-1h-Freeze**: The agent stops all autonomous moves 1 hour before departure to avoid gate-agent confusion during boarding.

## 5. Success Metrics (Comfort)

- **Empty-Seat-Capture-Rate**: % of flights where the agent successfully secured a seat with an adjacent empty seat.
- **Cabin-Proximity-Delta**: Difference in row number from original booking to final seat (lower is better).
- **Avoidance-of-Middle**: % of flights where the traveler avoided a middle seat despite a high-load factor.
