# Con Spec: Cultural-Nuance-Engine (CON-REAL-003)

**Status**: Research/Draft
**Area**: Cultural Intelligence & Executive Support

---

## 1. The Problem: "The Generic Advice Gap"
Generic travel advice ("Don't tip in Japan," "Cover your shoulders in Italy") is common knowledge for frequent travelers. However, "High-Stakes" interactions (B2B negotiations, ultra-luxury social events) require much deeper, non-obvious cultural nuance that generic LLMs or guidebooks miss. Misunderstanding a specific business hierarchy or gift-giving protocol can derail a million-dollar deal.

## 2. The Solution: 'Hyper-Contextual-Etiquette-Protocol' (HCEP)

The HCEP allows the agent to act as a "Virtual-Cultural-Chief-of-Staff."

### Intelligence Actions:

1.  **Vertical-Specific-Etiquette**:
    *   **Action**: Providing guidance specific to the *industry* of the interaction (e.g., "The etiquette for meeting a Venture Capitalist in Riyadh is different from meeting a Government Official").
2.  **Relationship-Vault-Integration**:
    *   **Action**: Cross-referencing the traveler's 'Relationship-Vault' (ITIN-002) to provide guidance on the specific *individual* being met (e.g., "This specific contact in Tokyo is modernized and prefers Western-style handshakes, but appreciates X specific formality").
3.  **Real-Time Nuance-Pings**:
    *   **Action**: Sending "Just-in-Time" alerts before an interaction. E.g., "You are entering the restaurant now. Remember: The senior-most person sits furthest from the door."
4.  **Gift-Sourcing-Optimization**:
    *   **Action**: Autonomously sourcing culturally "Perfect" gifts (and identifying "Forbidden" ones) based on the recipient's background and the occasion.

## 3. Data Schema: `Cultural_Nuance_Brief`

```json
{
  "brief_id": "HCEP-88221",
  "traveler_id": "GUID_9911",
  "interaction_type": "HIGH_STAKES_NEGOTIATION",
  "region": "SOUTH_KOREA",
  "industry_context": "SEMICONDUCTOR_TECH",
  "key_protocols": [
    {"topic": "HIERARCHY", "guidance": "Always address the Chairman as 'Hoeyang-nim' before any first name usage."},
    {"topic": "GIFTING", "guidance": "High-end fruit is acceptable; avoid red ink on cards."}
  ],
  "just_in_time_alert_scheduled": "2026-11-12T08:50:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Non-Obvious' Rule**: The agent MUST NOT prioritize generic advice that can be found in a top-10 list. It MUST prioritize "Insider" or "Executive" level nuance.
- **Rule 2: The 'Stereotype-Filter'**: The agent MUST autonomously audit its guidance to ensure it is based on current socio-economic reality rather than outdated or offensive stereotypes.
- **Rule 3: Language-Bridge-Nuance**: The agent provides guidance on specific "Honorifics" or "Power-Words" in the local language that convey respect without requiring the traveler to be fluent.

## 5. Success Metrics (Nuance)

- **Interaction-Confidence-Score**: Traveler-reported confidence level before/after receiving the brief.
- **Relationship-Yield**: % of "Successful-Outcome" reports for high-stakes business meetings.
- **Cultural-Gaffe-Avoidance**: 0 reported incidents of cultural offense during agent-led trips.
