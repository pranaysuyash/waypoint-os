# Area Deep Dive: Risk, Compliance, and Policy

**Domain**: Risk & Governance  
**Focus**: Regulatory alignment, traveler safety, and data integrity.

---

## 1. Regulatory & Document Compliance

The system must act as a "Compliance Sentinel" ensuring all legal and regulatory bars are met before a trip proceeds.

### Visa & Entry Requirements
- **Dynamic Policy Checks**: Rules for transit visas, e-visas, and sticker visas change frequently.
- **Hard Blockers**: Passport validity < 6 months, insufficient blank pages, or criminal record restrictions.
- **System Action**: Cross-reference traveler nationality with destination/transit country rules in NB02.

### Financial Compliance (LRS/TCS/GST)
- **LRS Tracking**: Monitoring the $250k annual limit for Indian residents.
- **Tax Collection**: Automating the 5-20% TCS (Tax Collected at Source) calculation based on spend thresholds.
- **GST Invoicing**: Ensuring correct GST categories (5% for flights, 18% for service fees) are applied to invoices.

### Data Privacy (GDPR/DPDP)
- **PII Redaction**: Redacting sensitive data (Passport numbers) in logs unless strictly necessary.
- **Consent Logs**: Maintaining an audit trail of when and why a traveler shared their data.
- **Data Retention**: Automating the deletion of identity documents 30 days post-trip.

---

## 2. Crisis & Emergency Management

When a crisis occurs, the system shifts from "Planner" to "Emergency Responder".

### The "Crisis Protocol"
- **Trigger**: Natural disaster, political unrest, or pandemic-level event in a destination.
- **Action**: 
    1. Identify all travelers currently in the affected zone.
    2. Identify all travelers departing for that zone in the next 14 days.
    3. Generate a "Status Dashboard" for the Agency Owner (P2).
    4. Draft "Urgent Safety Briefs" for affected travelers.

### Medical Emergencies
- **Protocol**: If a traveler reports a medical issue, the system must immediately identify the nearest "International Standard" hospital and coordinate with the insurance provider.

---

## 3. Supplier & Corporate Policy Compliance

### Supplier Vetting
- **Criteria**: Checking if a supplier is on any blacklists or has a high failure rate in the `AuditStore`.
- **System Action**: Flagging low-confidence suppliers in NB02 before the quote is sent.

### Corporate Travel Policy
- **Enforcement**: Ensuring corporate bookings stay within budget limits and use approved airlines/hotels.
- **Approval Workflows**: Automating the "Wait for Manager Approval" loop before booking execution.

---

## 4. Proposed Scenarios for this Domain

| Scenario ID | Title | Persona | Category |
|-------------|-------|---------|----------|
| RISK-001 | Last-Minute Transit Visa Change | P3 | Regulatory |
| RISK-002 | TCS Threshold Breach Detection | P2 | Financial |
| RISK-003 | Political Unrest - Evacuation Plan | S1 | Emergency |
| RISK-004 | PII Leak Prevention in Handoff | P1 | Privacy |
| RISK-005 | Corporate Budget Violation Flagging | P3 | Compliance |
| RISK-006 | Biosecurity Ban - Mid-Trip Rerouting | S1 | Crisis |
