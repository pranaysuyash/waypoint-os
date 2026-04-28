# Flw Spec: Agentic 'Itinerary-Versioning' Control System (FLW-REAL-033)

**Status**: Research/Draft
**Area**: Itinerary Change Management, Audit Trail Integrity & Rollback Architecture

---

## 1. The Problem: "The Itinerary-Mutation-Blindspot"
Complex itineraries evolve through dozens of revisions — flights change, hotels upgrade, activities swap, dates shift. Most agencies track itinerary versions informally: a chain of emails, a manually named document ("itinerary_FINAL_v3_ACTUAL.pdf"). When a dispute arises ("you changed our flights without telling us"), neither the agency nor the traveler has a clean, timestamped record of who changed what and when. This "Mutation-Blindspot" creates legal exposure, trust erosion, and costly dispute resolution.

## 2. The Solution: 'Version-Control-Protocol' (VCP)

The VCP acts as the "Itinerary-Git-System."

### Versioning Actions:

1.  **Immutable-Change-Ledger**:
    *   **Action**: Every change to an itinerary — regardless of source (AI, human agent, vendor, traveler request) — is recorded as an immutable "Change-Event" with: timestamp, change author, change category (Flight/Hotel/Activity/Date/Price/Notes), old value, new value, and change rationale.
2.  **Semantic-Diff-Generation**:
    *   **Action**: When a new version is produced, the agent generates a human-readable "Semantic-Diff" — a plain-English summary of what changed (e.g., "Flight LHR→DXB on Day 1 changed from BA107 at 09:15 to EK004 at 11:30 due to BA schedule change — no cost impact, arrival time 45 minutes later").
3.  **Traveler-Change-Notification**:
    *   **Action**: All changes above a "Materiality-Threshold" (configurable by agency: e.g., >30 minute schedule change, >$200 cost change, activity substitution) MUST trigger an immediate Semantic-Diff notification to the traveler — requiring explicit acknowledgment before the change is confirmed.
4.  **One-Click-Rollback**:
    *   **Action**: Any itinerary can be rolled back to any prior version with a single action — useful when a vendor-initiated change makes the itinerary worse and the agency needs to revert to the prior arrangement immediately.

## 3. Data Schema: `Itinerary_Version_Event`

```json
{
  "event_id": "VCP-88221",
  "itinerary_id": "JAPAN-CIRCUIT-2026",
  "version_number": 7,
  "change_author": "AGENT_PRIYA",
  "change_category": "FLIGHT",
  "change_rationale": "BA schedule change — force majeure",
  "old_value": "BA107 LHR-DXB 09:15",
  "new_value": "EK004 LHR-DXB 11:30",
  "cost_delta_usd": 0,
  "materiality_threshold_exceeded": true,
  "traveler_acknowledgment_required": true,
  "traveler_acknowledged_at": "2026-04-27T14:32:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Immutability-Guarantee'**: Change-Events MUST be write-once and cryptographically signed. No retroactive alteration of the change history is permitted under any circumstance.
- **Rule 2: The 'Materiality-Acknowledgment' Gate**: Changes exceeding the Materiality-Threshold MUST receive explicit traveler acknowledgment before being confirmed. Silence does not constitute consent.
- **Rule 3: The 'Author-Attribution' Standard**: Every change must have a clearly identified author (AI agent, specific human agent name, or "Vendor-Initiated"). Unattributed changes are not permitted.

## 5. Success Metrics (Versioning)

- **Dispute-Attribution-Speed**: Average time to produce a complete, verified change timeline when a dispute is raised.
- **Traveler-Acknowledgment-Compliance-Rate**: % of material changes that receive explicit traveler acknowledgment before confirmation.
- **Rollback-Exercise-Rate**: % of itinerary versions where a rollback was exercised and the reason it was needed.
