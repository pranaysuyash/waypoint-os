# Fin Spec: Agentic 'Cross-Border-Taxation' Intelligence (FIN-REAL-034)

**Status**: Research/Draft
**Area**: Multi-Jurisdiction Tax Compliance, Tourist Levy Management & VAT Recovery Optimization

---

## 1. The Problem: "The Tax-Complexity-Blindspot"
International travel generates a labyrinth of overlapping tax obligations that most agencies navigate manually and inconsistently. Tourist levies change without warning (Bali introduced a $10/entry levy in 2024). VAT is recoverable in many EU countries but only with the right documentation. Digital service taxes create nexus exposure for agencies in unexpected jurisdictions. Without "Tax-Nexus-Intelligence," agencies are either over-paying taxes (crushing margins) or under-collecting them (creating compliance liabilities).

## 2. The Solution: 'Tax-Nexus-Protocol' (TNP)

The TNP acts as the "Global-Tax-Compliance-Engine."

### Tax Intelligence Actions:

1.  **Destination-Tax-Profile-Generation**:
    *   **Action**: For every destination in a booking, generating a real-time "Destination-Tax-Profile": applicable tourist levies, city taxes, VAT rates on accommodation and tours, digital service taxes, and any recent legislative changes affecting the booking period.
2.  **VAT-Recovery-Opportunity-Detection**:
    *   **Action**: Identifying EU and UK bookings where the agency or traveler is VAT-registered and can claim input tax recovery on accommodation, qualifying professional services, and ground transport — and generating the required documentation package at booking.
3.  **Agency-Nexus-Risk-Monitoring**:
    *   **Action**: Tracking the agency's booking volume by jurisdiction to identify when it crosses "Economic-Nexus-Thresholds" that could create unexpected tax registration obligations in foreign markets — alerting the owner before the threshold is breached.
4.  **Traveler-Tax-Obligation-Briefing**:
    *   **Action**: Briefing travelers on all personal tax obligations they must discharge at the destination (e.g., Bali tourist levy payable on arrival, French city tax per person per night) — with exact amounts, payment mechanisms, and required documentation.

## 3. Data Schema: `Tax_Nexus_Profile`

```json
{
  "profile_id": "TNP-88221",
  "booking_id": "BALI-EUROPE-CIRCUIT-2026",
  "destinations_analyzed": ["BALI", "PARIS", "AMSTERDAM"],
  "tourist_levies_total_usd": 127,
  "vat_recovery_opportunity_usd": 840,
  "agency_nexus_risk_flags": 0,
  "documentation_packages_generated": 2,
  "traveler_tax_brief_delivered": true,
  "legislative_change_alerts": 1
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Real-Time-Rate' Requirement**: Tourist levy rates MUST be fetched from authoritative government sources at booking time — not from a static internal database that may be stale. Rates that changed within the past 90 days MUST trigger a "Recent-Change" flag.
- **Rule 2: Tax-Opinion-Boundary**: The agent MUST present tax information as "Guidance-Based-on-Published-Law" — it MUST NOT provide formal tax opinions or advice. Complex nexus situations MUST be escalated to a qualified tax professional.
- **Rule 3: Documentation-Integrity**: All VAT recovery documentation packages MUST include the specific invoice format requirements of the target jurisdiction. Incorrectly formatted invoices cannot be recovered.

## 5. Success Metrics (Tax)

- **VAT-Recovery-Yield**: Total VAT successfully recovered per year across all eligible bookings.
- **Compliance-Incident-Rate**: % of bookings where a tax compliance issue (under-collection, wrong rate, missed levy) is discovered post-booking.
- **Nexus-Breach-Prevention-Rate**: % of approaching nexus thresholds identified and addressed before breach.
