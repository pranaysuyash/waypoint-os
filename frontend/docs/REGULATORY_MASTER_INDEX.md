# Regulatory & Licensing — Master Index

> Exploration of travel agency licensing, IATA accreditation, GST/TCS compliance, and certificate lifecycle management.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Agency Licensing & Registration](REGULATORY_01_LICENSING.md) | Required licenses, government registration, compliance by agency type |
| 02 | [IATA Accreditation & BSP](REGULATORY_02_IATA.md) | IATA accreditation, BSP settlement, GDS integration, ticketing compliance |
| 03 | [GST/TCS Compliance & Filing](REGULATORY_03_COMPLIANCE.md) | GST rates, TCS on overseas tours, invoicing, automated filing |
| 04 | [Certificate Management & Renewals](REGULATORY_04_CERTIFICATES.md) | Certificate lifecycle, document vault, compliance dashboard, audit readiness |
| 05 | [FEMA Compliance & Forex Remittances](REGULATORY_05_FEMA.md) | LRS limits, overseas remittances, TCS on LRS, RBI reporting, forex card compliance |

---

## Key Themes

- **Compliance is non-negotiable** — Missing a GST filing or IATA renewal can result in penalties, suspension, or loss of accreditation. The platform must proactively manage compliance.
- **India-specific complexity** — GST rates vary by service type, TCS applies to overseas packages, and state-level licensing adds layers. Need deep India regulatory knowledge baked into the platform.
- **Automation reduces risk** — Auto-generated GST returns, renewal reminders, and compliance scoring reduce human error and ensure nothing falls through the cracks.
- **Small agency enablement** — Most Indian travel agencies are small (2-10 people). They can't afford dedicated compliance staff. The platform must serve as their compliance department.
- **Audit-ready by default** — Every transaction, invoice, and certificate should be organized and accessible. When audit season arrives, the agency is prepared, not scrambling.

## Integration Points

- **Booking Engine** — GST calculated per booking, TCS collected on overseas packages
- **Invoicing** — GST-compliant invoices with HSN codes, e-invoicing integration
- **Payment Processing** — TCS collected alongside package payments
- **Agency Settings** — License and registration details stored in agency profile
- **Analytics & BI** — Tax liability reports, filing status dashboards
- **Document Generation** — Compliance certificates, audit reports, filing confirmations
- **Notification System** — Renewal reminders, filing deadline alerts, compliance warnings
