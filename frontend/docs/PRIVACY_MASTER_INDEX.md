# Data Privacy & Consent Management — Master Index

> Comprehensive research on consent lifecycle, data subject rights, privacy-by-design, and breach response under India's DPDP Act and global regulations.

---

## Series Overview

This series explores how Waypoint OS handles personal data responsibly — from collecting informed consent at every touchpoint to fulfilling data subject rights, embedding privacy into system architecture, and responding to data breaches. India's DPDP Act (2023) is the primary regulatory framework, with GDPR alignment for international travelers.

**Target Audience:** Backend engineers, DPOs, legal/compliance, product managers

**Regulatory Framework:** DPDP Act 2023 (India), GDPR (EU), cross-border transfer rules

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [PRIVACY_01_CONSENT.md](PRIVACY_01_CONSENT.md) | Consent collection, lifecycle, withdrawal, DPDP Act requirements |
| 2 | [PRIVACY_02_DATA_RIGHTS.md](PRIVACY_02_DATA_RIGHTS.md) | Data access, correction, erasure, portability rights and automation |
| 3 | [PRIVACY_03_PRIVACY_BY_DESIGN.md](PRIVACY_03_PRIVACY_BY_DESIGN.md) | Privacy architecture, data classification, anonymization, PIA process |
| 4 | [PRIVACY_04_BREACH.md](PRIVACY_04_BREACH.md) | Breach detection, notification, containment, investigation, remediation |

---

## Key Themes

### 1. DPDP Act Compliance
India's Digital Personal Data Protection Act (2023) is the primary framework. Key obligations: explicit consent, purpose limitation, data subject rights, 72-hour breach notification, cross-border transfer restrictions. Penalties up to ₹250 crore per instance.

### 2. Privacy as Product Feature
Privacy controls aren't just legal checkboxes — they're product features that build trust. Granular consent management, easy data export, and transparent data practices differentiate the platform.

### 3. Data Classification Drives Protection
Not all data needs the same protection. A four-level classification system (Public → Internal → Confidential → Restricted) ensures proportionate security controls without over-engineering.

### 4. Anonymization Enables Analytics
Analytics and AI don't need raw personal data. Pseudonymization, aggregation, and differential privacy techniques enable insights while protecting individual privacy.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Security Architecture (SECURITY_*) | Encryption, access control, audit logging |
| Data Governance (DATA_GOVERNANCE_*) | Data quality, lineage, catalog |
| Multi-tenancy (MULTI_TENANCY_*) | Tenant-specific privacy controls |
| User Accounts (USER_ACCOUNTS_*) | Account data management and rights |
| Customer Identity (IDENTITY_*) | KYC data handling and government ID processing |
| Payment Processing (PAYMENT_*) | PCI-DSS compliance, financial data protection |
| Vendor Management (VENDOR_*) | Data processor agreements and audits |

---

## DPDP Act Compliance Checklist

- [ ] Appoint Data Protection Officer (DPO)
- [ ] Publish privacy policy in English and Hindi
- [ ] Implement consent management with granular controls
- [ ] Build data subject rights portal (access, correction, erasure, portability)
- [ ] Data classification and inventory complete
- [ ] Data Protection Impact Assessment for high-risk processing
- [ ] Breach notification process (72-hour to Board, prompt to individuals)
- [ ] Data processor agreements with all third parties
- [ ] Cross-border transfer assessment (whitelist countries)
- [ ] Annual privacy audit by independent auditor
- [ ] Employee privacy training program
- [ ] Children's data protection (verifiable parental consent)

---

**Created:** 2026-04-28
