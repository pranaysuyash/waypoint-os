# Reg Spec: Agentic 'Travel-Liability' Shield (REG-REAL-030)

**Status**: Research/Draft
**Area**: Agency Legal Liability & Risk Management

---

## 1. The Problem: "The Blanket-Waiver-Gap"
Many travel agencies use a single generic liability waiver for all trip activities. This "Blanket-Waiver" approach is legally fragile because: (1) the language often doesn't match the specific activity risks, (2) jurisdictional requirements differ significantly (e.g., California vs. UK vs. Thailand), and (3) travelers often sign waivers they don't understand, which courts may invalidate. Without "Agentic-Liability-Management," agencies are under-protected.

## 2. The Solution: 'Liability-Optimization-Protocol' (LOP)

The LOP acts as the "Legal-Risk-Minimizer."

### Shield Actions:

1.  **Activity-Risk-Profiling**:
    *   **Action**: Analyzing each itinerary and flagging "High-Risk-Activities" (e.g., scuba diving, mountain trekking, paragliding, safari wildlife encounters) that require specialized legal protection.
2.  **Jurisdiction-Specific-Waiver-Generation**:
    *   **Action**: Auto-generating or suggesting a "Jurisdiction-Specific-Waiver" for each flagged activity, using the correct legal language and risk disclosures required by local law.
3.  **Informed-Consent-Verification**:
    *   **Action**: Ensuring the traveler has reviewed and e-signed each applicable waiver. The agent tracks "Consent-Completion" status per traveler per activity.
4.  **Legal-Evidence-Package-Assembly**:
    *   **Action**: At trip completion, assembling a "Legal-Evidence-Package" containing all signed waivers, consent logs, and communication timestamps for the agency's liability records.

## 3. Data Schema: `Liability_Shield_Record`

```json
{
  "record_id": "LOP-88221",
  "itinerary_id": "SAFARI-KE-2026-01",
  "high_risk_activities": ["GAME_DRIVE_OPEN_VEHICLE", "WALKING_SAFARI"],
  "jurisdiction": "KENYA",
  "waivers_generated": 2,
  "consent_completion_status": "ALL_SIGNED",
  "evidence_package_status": "ASSEMBLED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Zero-Unsigned-Waiver' Gate**: The agent MUST block the final booking confirmation for any itinerary with flagged "High-Risk-Activities" until all applicable waivers have been signed.
- **Rule 2: Plain-Language-Mandate**: Generated waivers MUST include a "Plain-Language-Summary" alongside the legal text to ensure traveler comprehension and reduce the risk of courts invalidating "Uninformed" consent.
- **Rule 3: Attorney-Review-Escalation**: Any new waiver template or jurisdictional edge case MUST be flagged for attorney review before being deployed across the platform.

## 5. Success Metrics (Liability)

- **Waiver-Completion-Rate**: % of high-risk activities with fully executed and timestamped waivers.
- **Liability-Claim-Reduction**: % reduction in successful liability claims against agencies following the deployment of activity-specific waivers.
- **Legal-Evidence-Package-Utilization**: Number of evidence packages successfully assembled and used in dispute resolution.
