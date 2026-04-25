# DR Spec: Autonomous Legacy Fallback (DR-003)

**Status**: Research/Draft
**Area**: Interface Resilience & Protocol Fallback

---

## 1. The Problem: "The API Apocalypse"
Modern travel APIs (NDC, JSON wrappers) often sit on top of ancient Mainframe GDS systems. If the API layer (e.g., Amadeus JSON) fails, but the underlying GDS (Amadeus Cryptic) is still alive, the agency must be able to "Bypass" the middleman.

## 2. The Solution: 'Native-Bridge' (NB)

The NB allows the AI to autonomously switch from "API-Calls" to "Terminal-Commands" (Cryptic GDS) when it detects API-layer instability.

### Fallback Mechanisms:

1.  **Cryptic-Command Emulation**:
    *   **Action**: AI translates the booking intent into raw GDS commands (e.g., `SS LH400 Y1` for Sell Segment).
2.  **Web-Scraping Bridge**:
    *   **Action**: If GDS is also down, the AI falls back to "Headless Browser" tool-use to book directly on airline/hotel consumer websites.
3.  **Human-Protocol Generation**:
    *   **Action**: If all digital paths fail, the AI generates a "Manual-Instruction-Set" (e.g., "Call this specific number, reference this PNR, and provide this credit card").

## 3. Data Schema: `Fallback_Interface_Active`

```json
{
  "incident_id": "DR-NB-7788",
  "reason": "Amadeus NDC API returning 503 Gateway Timeout",
  "active_interface": "GDS_CRYPTIC_TERMINAL",
  "translation_log": [
    {
      "intent": "BOOK_SEGMENT_LHR_NYC",
      "command": "SS BA112 Y1 10MAY LHRJFK"
    },
    {
      "intent": "CONFIRM_PNR",
      "command": "ER"
    }
  ],
  "human_intervention_required": false
}
```

## 4. Key Logic Rules

- **Rule 1: Accuracy-Verification**: Before sending raw GDS commands, the AI must "Simulate" the command response to ensure it's not performing a destructive action (e.g., `XI` for Cancel All).
- **Rule 2: Automated 'Manual' Handover**: If the AI is forced to use the "Human-Protocol" (Phone/Fax), it auto-dials the number and uses "Text-to-Speech" to initiate the conversation for the human agent.
- **Rule 3: Post-Recovery Sync**: Once APIs are restored, the AI must autonomously "Re-Sync" any manual/GDS-native bookings back into the modern database layer.

## 5. Success Metrics (Fallback)

- **Survival Rate**: % of bookings successfully completed using Fallback interfaces when primary APIs were down.
- **Protocol Versatility**: Number of different interface types (API, GDS, Web, Phone) the AI can autonomously navigate.
- **Re-Sync Integrity**: Zero discrepancies between "Fallback-Bookings" and the final "Post-Recovery" database state.
