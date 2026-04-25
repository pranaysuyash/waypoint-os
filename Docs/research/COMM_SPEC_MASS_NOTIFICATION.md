# Comm Spec: Intelligent Mass-Notification (CO-001)

**Status**: Research/Draft
**Area**: Disruption Alerting & Multi-Channel Sync

---

## 1. The Problem: "Notification Fatigue vs. Silence"
During a mass disruption (e.g., a hub closure), travelers are either bombarded with redundant alerts or receive nothing until it's too late. We need a **Modality-Aware** notification engine.

## 2. The Solution: 'Urgency-Modality-Matrix' (UMM)

The UMM determines the communication channel based on the **Time-to-Impact** and **Traveler Priority**.

### Channel Selection Logic:

1.  **Critical (< 2 Hours to Impact)**:
    *   **Action**: `Voice_Call` (AI-driven) + `SMS` + `WhatsApp_Urgent`.
    *   **Goal**: Interrupt the traveler's current activity to ensure they don't go to the airport.

2.  **Urgent (2-6 Hours to Impact)**:
    *   **Action**: `WhatsApp` + `Slack` + `Push_Notification`.
    *   **Goal**: Ensure the traveler sees the update before they start their "Last-Mile" transit.

3.  **Informational (> 6 Hours to Impact)**:
    *   **Action**: `Email` + `In-App_Notification`.
    *   **Goal**: Provide full details for review at the traveler's convenience.

## 3. Data Schema: `Disruption_Alert_Payload`

```json
{
  "alert_id": "MSG-7788",
  "crisis_id": "HUB-LHR-CLOSE",
  "urgency": "CRITICAL",
  "content": {
    "headline": "ACTION REQUIRED: LHR Hub Closed",
    "body": "Your flight BA123 is cancelled. We are currently re-booking you. DO NOT proceed to the airport.",
    "next_step": "Await confirmation of new itinerary in 15 mins."
  },
  "distribution": {
    "sent_at": "2026-05-10T08:00:00Z",
    "channels_delivered": ["VOICE", "SMS", "WHATSAPP"],
    "ack_received": false
  }
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Dead-Man' Switch**: If the traveler doesn't "Acknowledge" a Critical alert within 10 minutes, the system auto-escalates to a human operator or the traveler's emergency contact.
- **Rule 2: Single-Source-of-Truth**: All channels MUST use the exact same `content_hash` to avoid conflicting information.
- **Rule 3: Modality Suppression**: If a traveler acknowledges on WhatsApp, do NOT send the automated Voice Call.

## 5. Success Metrics (Communications)

- **Alert Latency**: Time from disruption detection to first alert sent < 60 seconds.
- **Acknowledgment Rate**: % of travelers who confirm receipt of Critical alerts within 15 minutes.
- **Support Volume**: Reduction in "What's happening?" inbound queries during mass disruptions.
