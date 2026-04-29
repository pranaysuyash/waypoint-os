# Travel Compliance Automation — Master Index

> Research on document/visa compliance, financial tax compliance (GST/TCS/TDS), data privacy (DPDP Act), and audit trail/reporting for the Waypoint OS platform.

---

## Series Overview

This series covers compliance automation for Indian travel agencies — from document verification and visa compliance to GST/TCS/TDS financial compliance, India DPDP Act data privacy, and regulatory reporting. The goal is to make compliance automatic and invisible so agents focus on selling, not filing.

**Target Audience:** Product managers, backend engineers, legal/compliance officers

**Key Insight:** Compliance is not a feature — it's a constraint on every feature. Every trip touches document compliance (passports, visas), financial compliance (GST, TCS, TDS), and data privacy (DPDP Act). Automating these checks prevents costly violations and frees agents from manual compliance work.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [COMPLIANCE_AUTO_01_DOCUMENTATION.md](COMPLIANCE_AUTO_01_DOCUMENTATION.md) | Travel document compliance engine, visa rules, document collection workflow, regulatory change monitoring |
| 2 | [COMPLIANCE_AUTO_02_FINANCIAL.md](COMPLIANCE_AUTO_02_FINANCIAL.md) | GST invoice generation, TCS on foreign packages, TDS on international payments, GST filing dashboard |
| 3 | [COMPLIANCE_AUTO_03_DATA_PRIVACY.md](COMPLIANCE_AUTO_03_DATA_PRIVACY.md) | India DPDP Act compliance, consent management, data subject rights automation, vendor DPA tracking |
| 4 | [COMPLIANCE_AUTO_04_REPORTING.md](COMPLIANCE_AUTO_04_REPORTING.md) | Compliance audit trail, pre-trip compliance gates, regulatory reporting engine, compliance dashboard |

---

## Key Themes

### 1. Compliance as Automation, Not Checklist
Manual compliance checking is error-prone and slow. Every check that can be automated (passport expiry, visa requirements, TCS calculation) should be. Agents should only handle exceptions.

### 2. India-Specific Tax Complexity
Indian travel agencies face a unique combination of GST, TCS (on foreign packages), and TDS (on international payments). Each has different rates, thresholds, filing deadlines, and forms. The system must handle all three correctly.

### 3. Privacy by Design
The DPDP Act requires explicit consent, purpose limitation, and data subject rights. These aren't add-ons — they must be designed into every data collection and sharing flow from the start.

### 4. Pre-Trip Compliance Gate
No trip should depart without passing automated compliance checks. Documents collected? TCS paid? Insurance active? Consents obtained? The gate catches issues before they become problems.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Financial Dashboard (FIN_DASH_*) | Tax projections, GST/TCS revenue tracking |
| Health Intelligence (HEALTH_INTEL_*) | Vaccination compliance for destinations |
| Customer CRM (CRM_*) | Customer data subject to DPDP consent |
| Travel Photography (TRAVEL_MEM_*) | Photo consent, privacy controls |
| Draft System (DRAFT_SYS_*) | Draft-era audit trail for compliance |
| Sales Playbook (SALES_PLAYBOOK_*) | TCS disclosure during quotation |

---

## Implementation Phases

| Phase | Scope | Impact |
|-------|-------|--------|
| 1 | GST invoice generator + TCS calculator + document checklist | Financial compliance automated |
| 2 | Consent management + document collection workflow | Privacy compliance operational |
| 3 | Pre-trip compliance gate + audit trail | No non-compliant trips depart |
| 4 | Regulatory reporting + compliance dashboard | Filing automation + proactive monitoring |

---

**Created:** 2026-04-29
