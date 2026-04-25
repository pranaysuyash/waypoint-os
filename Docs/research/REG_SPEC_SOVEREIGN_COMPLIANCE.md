# Regulatory Spec: Sovereign Regulatory Compliance (REG-001)

**Status**: Research/Draft
**Area**: Legal Autonomy & Multi-Jurisdictional Compliance

---

## 1. The Problem: "The Legal Vacuum"
When a flight from NYC to London is diverted to Gander (Canada), the legal framework changes mid-air. Does US DOT apply? Canadian CTA? EC261? If the agent applies the "Wrong Law," it may miss compensation deadlines or violate the traveler's rights.

## 2. The Solution: 'Jurisdictional-Law-Injection' (JLI)

The JLI protocol allows the agent to dynamically "Switch" its legal reasoning core based on GPS/PNR context.

### Regulatory Layers:

1.  **Point-of-Origin Law**: (e.g., US DOT for flights departing the US).
2.  **Carrier-Nationality Law**: (e.g., EC261 for EU carriers).
3.  **Active-Jurisdiction Law**: (e.g., Canadian CTA for diversions into Canada).
4.  **Destination Law**: (e.g., UK261 for flights arriving in the UK).

## 3. Data Schema: `Jurisdictional_Context_Packet`

```json
{
  "incident_id": "REG-INC-1100",
  "active_coordinates": [48.9500, -54.5800],
  "inferred_jurisdiction": "CANADA_CTA",
  "applicable_statutes": [
    {
      "name": "APPR",
      "region": "CANADA",
      "re-booking_requirement": "NEXT_AVAILABLE_9_HOURS",
      "cash_compensation_threshold": "3_HOURS_DELAY"
    }
  ],
  "conflict_resolution": "MAXIMIZE_TRAVELER_BENEFIT",
  "priority_law": "EC261_PREVAILS_OVER_CTA"
}
```

## 4. Key Logic Rules

- **Rule 1: Most-Favorable-Clause**: If multiple laws apply (e.g., EC261 and Canada APPR), the agent MUST autonomously select the one that offers the **highest compensation** and **fastest re-booking** for the traveler.
- **Rule 2: Instant-Claim-Filing**: The moment a delay hits a "Compensation Trigger" (e.g., 3 hours), the agent auto-generates the legal claim form, signs it via 'Evidence Vault' PGP keys, and submits it to the airline API.
- **Rule 3: Settlement-Negotiation-Cap**: The agent can autonomously "Accept" a travel voucher settlement ONLY if it is >150% of the cash-value required by law. Otherwise, it must escalate to "Manual Review."

## 5. Success Metrics (Compliance)

- **Claim Capture Rate**: % of legally valid compensation claims successfully identified and filed (Target: 100%).
- **Settlement Yield**: Average increase in compensation value by leveraging "Most-Favorable" jurisdictional arbitrage.
- **Regulatory Error Rate**: Number of claims rejected due to "Wrong-Jurisdiction" logic (Target: 0).
