# Persona Profile: Tariq Al-Mansoor — High-End Visa & Expedition Concierge

**Identifier**: `P6-EXPEDITION-01`\
**Role**: Director of Document Compliance & Visa Concierge at *Vanguard Polar & Remote Expeditions*\
**Operational Scale**: Coordinates multi-border international expeditions (Antarctica via Ushuaia, Patagonia traverse, Silk Road overland) for 200+ high-net-worth clients annually.\
**Primary Tooling Need**: ICAO Doc 9303 MRZ parsing with Modulo-10 checksum validation, passport 6-month validity compliance, automated visa appointment milestone scheduling, and GDS/airline e-ticket cross-reconciliation.

---

## 1. Professional Background & Operational Context

Tariq handles expeditions where a single document discrepancy, typo in a passport number, or unnoticed 5-month expiry date leads to denied boarding at JFK or deportation at Chilean immigration. His core operational challenges include:

1. **OCR & Transcription Errors**: Client photo uploads of passport identity pages often introduce OCR noise (substituting `0` for `O`, `1` for `I`, or missing check digits).
2. **Passport Validity Buffers**: Many countries (including Argentina, Chile, and Schengen states) strictly enforce the **6-Month Validity Rule** beyond the planned departure date.
3. **Multi-Document Discrepancies**: Ensuring names and dates match 100% across ICAO TD3 passports, 13-digit airline e-tickets (e.g. Delta 006), Amadeus GDS PNRs, and local expedition hotel vouchers.

---

## 2. Core Jobs-To-Be-Done (JTBD)

1. **Deterministic MRZ Checksum Verification**: Execute 7-3-1 Modulo-10 checksum algorithms across passport numbers, birth dates, expiration dates, and composite check digits to catch 100% of OCR errors before filing visa applications.
2. **Automated Visa Timeline Milestones**: Calculate consular processing lead times (e.g., 45 days for Chilean Antarctic permits) and auto-schedule client reminders.
3. **Cross-Document E-Ticket Synchronization**: Match 13-digit e-ticket coupons with GDS record locators and hotel confirmation codes to ensure seamless voucher validation.
