# Integration Spec: Protocol-Adapter Layer (IN-001)

**Status**: Research/Draft
**Area**: External System Connectivity & API Standardization

---

## 1. The Problem: "The Heterogeneous Mess"
The agency must talk to GDS (legacy), Slack (Chat), WhatsApp (Chat), Stripe (Finance), and Flight-Trackers (Data). Each has a different schema, making it difficult for agents to reason consistently across all channels.

## 2. The Solution: The 'Unified-Agent-Interface' (UAI)

The UAI is a middleware layer that translates all external "Dialects" into a single, agent-native "Language."

### Adapter Types:

1.  **Channel Adapters (Slack/WhatsApp)**:
    *   **Input**: `Slack_Message` or `WhatsApp_Media`.
    *   **UAI Translation**: `Unified_Message_Object` { `sender`, `text`, `intent`, `media_url` }.

2.  **Legacy Adapters (GDS)**:
    *   **Input**: `PNR_EDIFACT_STRING`.
    *   **UAI Translation**: `CanonicalPacket` { `pnr`, `itinerary`, `segments`, `pax_count` }.

3.  **Financial Adapters (Banking)**:
    *   **Input**: `Stripe_Charge` or `Swift_Transfer`.
    *   **UAI Translation**: `Transaction_Event` { `amount`, `currency`, `project_id`, `status` }.

## 3. Data Schema: `Unified_Action_Payload`

When an agent wants to "Do Something," it sends a UAI command, and the adapter handles the implementation details.

```json
{
  "action": "NOTIFY_TRAVELER",
  "priority": "HIGH",
  "channels": ["SLACK", "WHATSAPP"],
  "content": {
    "text": "Your flight is delayed. Alternative booked.",
    "cta": "Check itinerary"
  },
  "metadata": { "trace_id": "T-998" }
}
```

## 4. Key Logic Rules

- **Rule 1: Schema Integrity**: No agent can access a raw external API. They MUST go through the UAI.
- **Rule 2: Retry & Exponential Backoff**: The Adapter Layer (not the agent) handles HTTP 429s and connection timeouts.
- **Rule 3: Auditable-Trace**: Every UAI action is logged to the `AuditStore` with a `Source_System` tag.

## 5. Success Metrics (Integration)

- **Integration Speed**: Time taken to add a new external system (e.g., "Add Telegram support") reduced to < 1 day.
- **Schema Variance**: Zero instances of agents failing due to "Unexpected API Response Structure."
- **Reliability**: 99.9% success rate for UAI-to-Channel delivery.
