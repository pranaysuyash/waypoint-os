# PII Detection & Data Classification — Master Index

> Research on automated PII detection, named entity recognition, ML-based classification, field-level encryption, data retention, and compliance automation for the Waypoint OS platform.

---

## Series Overview

This series covers PII detection and data classification as a core infrastructure capability — from regex and NER-based detection to field-level encryption, key management, automated data retention, and DPDP Act compliance automation. PII protection isn't optional; it's a legal requirement under India's Digital Personal Data Protection Act (2023) and a trust differentiator for agencies handling passport numbers, Aadhaar, and payment data.

**Target Audience:** Platform engineers, security architects, compliance teams

**Key Insight:** Standard PII detection tools (AWS Comprehend, Google DLP) miss Indian-specific formats — Aadhaar numbers (12 digits), PAN cards (10 alphanumeric), and Indian passport numbers (1 letter + 7 digits + 1 letter). Building custom recognizers on top of open-source Presidio, combined with travel-specific context rules (distinguishing travel dates from DOBs, prices from account numbers), achieves 95%+ detection accuracy with <5ms latency.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [PII_DETECT_01_ENGINE.md](PII_DETECT_01_ENGINE.md) | Multi-layer PII detection (regex, NER, context engine), data classification tiers (Tier 0-4), domain-specific vision models (MedGemma-class for document processing), document verification, and inverse usage (PII redaction from documents) |
| 2 | [PII_DETECT_02_STORAGE.md](PII_DETECT_02_STORAGE.md) | Field-level encryption (AES-256-GCM), envelope encryption, searchable encryption (HMAC blind indexes), key management hierarchy, automated retention policies, crypto-shredding, DPDP Act compliance automation, PCI-DSS compliance |

---

## Key Themes

### 1. Travel-Domain PII Is Different
Travel platforms handle unique PII types (passport numbers, visa details, travel documents) that standard DLP tools don't recognize. Plus, travel conversations are full of dates, numbers, and names that trigger false positives. A travel-specific detection engine is essential.

### 2. Tiered Protection Over Blanket Encryption
Not all data needs the same protection. Tier 0 (public destination info) needs none; Tier 4 (Aadhaar, passport) needs encryption, searchability restrictions, and automatic purging. Tiered classification avoids over-engineering while ensuring compliance.

### 3. Vision Models as Double-Edged Swords
The same document understanding models that extract passport data (MedGemma-class approach) can also REDACT PII from documents — producing sanitized copies for demos, training, and compliance exports. The "opposite usage" is as valuable as the primary one.

### 4. Compliance Through Automation
Manual PII compliance doesn't scale. Automated classification at ingestion, encryption at rest, scheduled purging, and rights request handling ensure continuous compliance without relying on human discipline.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Data Governance (DATA_GOVERNANCE_*) | Data quality and catalog with PII classification |
| Privacy & Consent (PRIVACY_*) | Consent management feeding PII access control |
| Identity & KYC (IDENTITY_*) | Document processing pipeline |
| Fraud Detection (FRAUD_*) | Document forgery detection |
| Security Architecture (SECURITY_*) | Encryption and key management |
| AI/ML Patterns (AIML_*) | ML model governance for PII detection models |
| ML Training Data (ML_DATA_*) | Training data pipeline with PII sanitization |
| Compliance Automation (COMPLIANCE_AUTO_*) | DPDP Act compliance reporting |

---

**Created:** 2026-04-30
