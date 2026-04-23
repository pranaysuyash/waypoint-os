# Domain Knowledge: IATA Standards & Accreditation (Global)

**Category**: Regulatory & Compliance  
**Focus**: IATA accreditation, ticketing authority, and BSP (Billing and Settlement Plan).

---

## 1. What is IATA?

The **International Air Transport Association (IATA)** is the trade association for the world’s airlines. For a travel agency, IATA accreditation is the "Gold Standard" that allows direct ticketing with airlines.

### Types of Accreditation
- **Full IATA Accreditation**: Allows the agency to issue tickets directly on behalf of IATA member airlines. Requires strict financial bonding and certified staff.
- **TIDS (Travel Industry Designator Service)**: For agencies that don't issue tickets but want to be recognized by suppliers (hotels, car rentals) for commissions.
- **GoLite (Non-Cash)**: A newer, lighter accreditation for agencies that pay for tickets via IATA EasyPay or credit card (no cash-based BSP).

---

## 2. The BSP (Billing and Settlement Plan)

The **BSP** is the system used to settle payments between agencies and airlines globally.

### How it Works
- **The Cycle**: Agencies report their sales daily/weekly. IATA aggregates all sales for all airlines and pulls a single payment from the agency's bank account.
- **Risk**: If the payment fails (Short Remittance), the agency's ticketing authority is suspended globally within hours.
- **SOP**: The Treasury Team (P2) must ensure the BSP bank account is fully funded 48 hours before the settlement date.

---

## 3. Global Ticketing Standards

### The "IATA Number"
- Every accredited agency has a unique 8-digit IATA number. This number is embedded in every PNR and TST.
- **Operational SOP**: Never share your IATA number with unvetted third parties, as it can be used for "Fraudulent Ticketing."

### PCI-DSS Compliance
- **Requirement**: Agencies handling credit card data (Global) must comply with the Payment Card Industry Data Security Standard.
- **System Action**: Using "Tokenization" for all credit card storage in the `AuditStore`.

---

## 4. Operational Best Practices
- **Bonding**: Regularly review the agency's "Financial Bond" requirements as IATA often updates these based on global risk levels.
- **Staff Training**: Ensure at least two agents (P3) are "IATA Certified" to maintain accreditation status.
- **ADM Management**: Monitor the "Post-Billing Dispute" (PBD) portal for any airline-issued fines.
