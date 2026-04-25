# Ops Spec: Agentic Asset-Inventory-Watchdog (OPS-REAL-020)

**Status**: Research/Draft
**Area**: Personal Security & Loss Prevention

---

## 1. The Problem: "The Left-Behind Asset"
Travelers are frequently distracted in high-friction environments (airports, train stations, busy cafes). Forgetting a passport, wallet, or phone can derail an entire trip. Even with Bluetooth tags (AirTags, Tile), travelers often miss the "Left-Behind" notification from their phone if they are in a rush or the notification is buried among others.

## 2. The Solution: 'Loss-Prevention-Protocol' (LPP)

The LPP allows the agent to act as a "Digital-Asset-Guardian."

### Watchdog Actions:

1.  **Tag-Inventory-Sync**:
    *   **Action**: Syncing with the traveler's "Find-My" or "Tile" APIs to catalog all tagged essentials (Passport-Holder, Wallet, Laptop-Bag, Keys).
2.  **Context-Aware Separation-Alert**:
    *   **Action**: If the traveler's phone GPS moves >50m from a "High-Value-Tag" while in a "Transit-Hub" or "Hospitality-Zone," the agent triggers a **High-Severity-Voice-Alert** ("Stop! You left your Passport at Cafe Nero").
3.  **Autonomous Recovery-Coordination**:
    *   **Action**: If an item is confirmed "Left-Behind," the agent autonomously calls the venue (using the `CON-REAL-001` expert sourcing logic) to request the item be held at the front desk.
4.  **Security-Wipe-Trigger**:
    *   **Action**: If a "Smart-Device" (Phone/Laptop) is detected as "Stolen" (moving rapidly away from the traveler in an unplanned direction), the agent autonomously initiates a "Remote-Lock" or "Secure-Wipe" based on pre-approved traveler policy.

## 3. Data Schema: `Asset_Watchdog_Engagement`

```json
{
  "engagement_id": "LPP-44221",
  "traveler_id": "GUID_9911",
  "asset_name": "PASSPORT_CASE",
  "tag_id": "UWB-7721-Z",
  "separation_detected_utc": "2026-11-15T10:05:00Z",
  "traveler_location": { "lat": 48.8566, "lng": 2.3522 },
  "asset_location": { "lat": 48.8564, "lng": 2.3520 },
  "action_taken": "VOICE_ALERT_TRIGGERED",
  "venue_contacted": "LE_COMPTOIR_PARIS",
  "status": "ASSET_RECOVERED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Geofence-Safe-Zone'**: No alerts are triggered if the item is left in a "Verified-Safe-Zone" (e.g., the traveler's locked hotel room), unless the traveler is "Checking-Out."
- **Rule 2: Checkout-Inventory-Sweep**: At the moment of "Hotel-Checkout" (detected via bill-payment or key-return), the agent MUST perform a full sweep of all tagged assets to ensure nothing is left in the room.
- **Rule 3: Multi-Device-Broadcasting**: Separation alerts are pushed simultaneously to the traveler's Watch, Phone, and (if applicable) a travel companion's device (FLW-003).

## 5. Success Metrics (Security)

- **Asset-Recovery-Time**: Time between separation detection and asset re-possession.
- **Critical-Loss-Prevention**: Number of high-value items (Passports/Wallets) saved from abandonment.
- **False-Positive-Ratio**: % of alerts triggered when the item was actually safe (target: <5%).
