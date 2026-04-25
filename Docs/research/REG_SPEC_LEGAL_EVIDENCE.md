# Reg Spec: Post-Incident Legal-Packet (REG-REAL-004)

**Status**: Research/Draft
**Area**: Legal Protection & Incident Documentation

---

## 1. The Problem: "The Evidentiary Decay"
When a serious incident occurs during travel (personal injury, theft, assault, major contract breach), the "Evidence" begins to decay immediately. Security footage is overwritten, vendor communication logs are deleted, and traveler memories fade. Victims often struggle to gather the structured data needed for insurance claims or legal action months later.

## 2. The Solution: 'Legal-Evidence-Protocol' (LEP)

The LEP allows the agent to act as a "First-Responder-Archivist" for legal integrity.

### Preservation Actions:

1.  **Immediate Log-Freeze**:
    *   **Action**: At the moment an incident is flagged, the agent autonomously "Freezes" all internal logs related to the PNR, including every API call to the airline, hotel, and transport provider.
2.  **Vendor-Evidence-Request**:
    *   **Action**: Autonomously issuing a formal "Letter-of-Preservation" to the vendor (e.g., hotel) requesting they preserve CCTV footage or staff logs related to the incident time-window.
3.  **Proof-of-Presence-Verification**:
    *   **Action**: Consolidating GPS telemetry (APP-008), boarding pass scans, and digital keys into a "Certified-Timeline" that proves the traveler's exact location at the time of the incident.
4.  **Legal-Discovery-Packet-Assembly**:
    *   **Action**: Packaging all communications, receipts, and preserved data into a structured, timestamped PDF/ZIP file ready for a lawyer or insurance adjuster.

## 3. Data Schema: `Legal_Discovery_Audit`

```json
{
  "incident_id": "LEP-88221",
  "traveler_id": "GUID_9911",
  "incident_type": "PERSONAL_INJURY_FACILITY",
  "timestamp_utc": "2026-11-12T14:00:00Z",
  "location_context": "HOTEL_LOBBY_MARRIOTT",
  "evidence_frozen": ["API_LOGS", "CHAT_HISTORY", "PNR_DATA"],
  "preservation_notices_sent": [
    {"target": "MARRIOTT_INTL", "status": "DELIVERED"}
  ],
  "timeline_integrity_hash": "sha256:778899..."
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Conflict' Protocol**: The agent MUST NOT provide legal advice. It is strictly an "Evidence-Collector."
- **Rule 2: The 'Immutability-Hash'**: Every evidence packet generated MUST be cryptographically hashed to ensure it has not been tampered with after the incident.
- **Rule 3: Privacy-Gating**: Access to the Legal-Packet MUST require multi-factor authentication (MFA) and explicit traveler authorization, even for the traveler's own employer.

## 5. Success Metrics (Protection)

- **Evidence-Completeness-Score**: % of critical data points preserved within 60 minutes of incident flagging.
- **Legal-Acceptance-Rate**: % of packets successfully used in insurance or legal settlements.
- **Audit-Integrity**: 0% failures in the timeline integrity hash.
