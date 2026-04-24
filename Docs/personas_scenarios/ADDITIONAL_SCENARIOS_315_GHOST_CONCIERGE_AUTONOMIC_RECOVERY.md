# Additional Scenario 315: Ghost Concierge Autonomic Recovery

**Scenario**: A low-risk flight delay is detected, and the Ghost Concierge autonomically reschedules ground transport and notifies the hotel without agent intervention.

---

## Situation

- A traveler is mid-air on a flight to Singapore.
- The system detects a 45-minute delay via the flight tracking API.
- The "Autonomic Permission" rules allow Ghost Concierge to handle delays < 60 mins for "Business" travelers.

## What the system should do

- **Detect & Log**: Record the delay event in `AuditStore`.
- **Autonomic Action**: Pings the pre-booked transport provider via API to adjust the pickup time.
- **Silent Notification**: Sends a WhatsApp message to the traveler (formatted via `whatsapp_formatter.py`): "Welcome to Singapore! We noticed your flight was slightly delayed. Your driver is already aware and is waiting for you at the revised time."
- **Confirmation**: Logs a `GhostWorkflow` entry with status `completed` and `autonomic_level: 2`.

## Why this matters

- High-leverage operational efficiency: The agent doesn't need to manually check flight statuses for minor delays.
- Traveler Experience: Proactive resolution reduces arrival anxiety.

## Success criteria

- No manual agent clicks required for the reschedule.
- Traveler receives the update before landing.
- The `GhostWorkflow` record is correctly persisted for the Agency Owner to audit.
