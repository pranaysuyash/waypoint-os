# Fin Spec: Chargeback Defense Automation (FIN-REAL-001)

**Status**: Research/Draft
**Area**: Financial Risk & Fraud Prevention

---

## 1. The Problem: "Friendly Fraud"
Travelers sometimes dispute legitimate charges (e.g., non-refundable cancellations) with their bank, claiming they "didn't authorize" the transaction or the "service wasn't as described." The agency loses the revenue and pays a dispute fee. Manual defense is time-consuming and often fails due to missing evidence.

## 2. The Solution: 'Evidence-Packet-Protocol' (EPP)

The EPP autonomously assembles a "Court-Ready" packet of evidence the moment a transaction is initiated.

### Financial Actions:

1.  **Transaction-Context-Snapshot**:
    *   **Action**: Capturing the exact UI state, terms-and-conditions presented, and "Traveler-Check-Box" approval at the time of purchase.
2.  **Intent-Verification-Audit-Trail**:
    *   **Action**: Linking the transaction to previous communication (Emails, WhatsApp) where the traveler explicitly requested the booking.
3.  **Automated-Representment**:
    *   **Action**: If a dispute is received, the agent autonomously "Uploads" the evidence packet to the payment gateway (Stripe, Adyen) within 24 hours.

## 3. Data Schema: `Evidence_Packet`

```json
{
  "packet_id": "EP-99221",
  "transaction_id": "TX-88112",
  "traveler_approval_hash": "0xAB88...FF11",
  "ip_address": "192.168.1.1",
  "device_fingerprint": "BROWSER_CHROME_OSX_15",
  "communication_links": ["MSG_ID_44", "EMAIL_ID_88"],
  "terms_agreed_version": "TC_2026_04_A"
}
```

## 4. Key Logic Rules

- **Rule 1: Proactive-Warning**: If the agent detects a traveler has a history of high-dispute behavior (via external risk scores), it MUST require "3D-Secure" or "Wire-Transfer" for any non-refundable bookings.
- **Rule 2: Automated-Engagement**: Upon receiving a dispute, the agent autonomously messages the traveler: "We noticed a dispute on transaction X. Was this an error? If not, we have provided the following evidence to your bank..." (This often results in the traveler withdrawing the dispute).
- **Rule 3: Ledger-Symmetry**: Every evidence packet must be mirrored in the `Evidence Vault` (LEGAL-001).

## 5. Success Metrics (Financial)

- **Chargeback-Win-Rate**: % of disputes resolved in the agency's favor.
- **Manual-Labor-Reduction**: Hours saved per month on manual dispute defense.
- **Dispute-Ratio**: Maintaining a dispute ratio < 0.1% to avoid high-risk merchant categorization.
