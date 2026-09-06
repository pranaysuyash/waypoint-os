# Consolidated Build Queue — Waypoint OS

**Date**: 2026-04-22
**Status**: Authoritative single source of truth for execution.

---

## Current Wave: Wave 15 — Financial State Persistence & Sourcing

| Item | Description | Status | Priority |
|------|-------------|--------|----------|
| P3-A | **Vendor/Cost/Sourcing Tracking** (Gap #01) | Ready | P0 |
| P3-B | **Financial State Persistence** (Gap #04) | Ready | P0 |
| P3-C | **Indian Tax Compliance (TCS/GST)** (Gap #15) | Planned | P1 |

---

## Completed (Recent)

- [x] **Extraction Truth & Statutory Compliance (2026-08-31 Register Closures)**:
  - **[NEW-01 & NEW-02 & F-21] Intake Extraction Truth & Epistemic Honesty** (`src/intake/extractors.py`): Resolved companion party parsing ("me and 3 friends" ➔ 4 pax), per-person budget recognition ("5k each", "3500 pp"), and calibrated `epistemic_status=EpistemicStatus.ASSUMED` on defaulted budget slots.
  - **[F-04] Customer Payment Authorization Mandate Ledger** (`src/financial/payment_mandates.py`): Immutable consent artifacts, cryptographic SHA-256 agreement digests, max authorization caps, and charge lifecycle tracking (`ACTIVE`, `CONSUMED`, `REVOKED`). **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
  - **[F-05] Data Privacy Retention & Erasure SLA Enforcement Engine** (`src/security/retention_enforcer.py`): Statutory retention sweepers (Passport MRZ 30d, Payment Token 120d, Logs 180d, Tax Invoice 7yr) and GDPR Art 17 cryptographic `ErasureCertificate` issuer. **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
- [x] **P1 Findings Hardening (2026-08-31 Register Closures)**:
  - **[F-01] Price Lock Optimistic Concurrency & Idempotency Guard** (`spine_api/routers/price_lock.py`): Re-lock version conflict detection (`409 Conflict`) and replay idempotency caching.
  - **[F-02] Cryptographic Proposal Capability Tokens** (`spine_api/routers/public_proposals.py`): HMAC-SHA256 signatures, TTL expiration enforcement, and explicit token revocation. *(Hardened 2026-09-02: required signing key, demo-token allowlist, agency-scoped v2 tokens, durable revocations — see PT-01…PT-06 in FINDINGS_REGISTER_2026-08-31.md Part 4c.)*
  - **[F-14] Perishable Deadlines Sentinel** (`src/monitoring/perishable_sentinel.py`): Unified monitor for Visa appointments, flight quote TTLs, CFAR 14-day insurance waiver windows, and supplier balance deadlines. **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
  - **[F-07] Agent DLQ Inspector & Poisoned Job Replay** (`src/agents/dlq_inspector.py`): Dead-letter queue inspection, secret/PII redaction, and counterfactual payload replay. **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
- [x] **Operations & Logistics Intelligence Suite (Area #17 Final Tail)**:
  - **Group Rooming List & Occupancy Engine** (`src/logistics/rooming_list.py`): Single supplement calculations, room type & bedding allocations, family/couple roommate pairing.
  - **Fleet & Vehicle Allocation Engine** (`src/logistics/fleet_allocation.py`): Passenger, luggage, and child-seat capacity physics with multi-vehicle split recommendations.
  - **Timed Entry & Admission Window Scheduler** (`src/logistics/timed_entry.py`): Transit buffer audits against strict gate cutoffs (Louvre, Colosseum, Universal Express).
  - **Hub Flight Connection & MCT Risk Scorer** (`src/logistics/connection_risk.py`): Terminal changes, IATA MCT violations, and separate PNR self-transfer penalties.
  - **Traveler Accessibility & Medical Logistics** (`src/logistics/accessibility.py`): Airline SSR directives (WCHR, WCHS, WCHC, MEDA, BLND, DEAF) and hotel step-free audits.
  - **Logistics REST Router** (`spine_api/routers/logistics.py`): Complete API suite on `/api/v1/logistics/*`.
- [x] **Industry Expansion & Blind Spot Closure (Area #17)** *(truthfulness amendment 2026-09-02: the four engines below are completed **simulated/shadow capability** — each has zero production callers and test-only coverage; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)*:
  - **Corporate Travel Policy Engine** (`src/corporate/policy_engine.py`): Seniority tiers (Executive, Senior Mgmt, Standard), flight duration cabin rules, city-tier per-diem hotel caps, and multi-level approval chains (Manager -> Director -> Finance VP). **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
  - **Visa Application Workflow & Document Verification** (`src/documents/visa_workflow.py`): Stage lifecycle, milestone timeline generation (D-45 prep, D-30 appointment, D-15 submission), passport validity checks, and embassy turnaround delay risk scoring. **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
  - **Pre-Departure Automated Briefing Cadence** (`src/briefing/pre_departure_cadence.py`): D-7 logistics & prep briefing, D-3 72-hour weather & web check-in brief, and D-1 live flight gate & 24/7 SOS Concierge emergency packet. **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
  - **Accounting System Export Bridge** (`src/accounting/export_bridge.py`): Tally ERP 9 / Tally Prime XML sales voucher exporter and Intuit QuickBooks Online REST v3 JSON invoice exporter. **Completed (simulated — engine has zero production callers, test-only; see GEMINI_WAVE_MODULE_AUDIT_2026-09-01 §1)**
- [x] **Wave 15 / Phase 3**: Financial Depth & Tax Compliance:
  - **Indian Tax Compliance Engine** (`src/fees/tax_compliance.py`): Statutory Section 206C(1G) TCS (5% / 20% LRS thresholds & non-PAN penalty) and GST (5% Tour Package vs 18% Service Fee with CGST/SGST/IGST splits).
  - **Sourcing Cost Ledger** (`SourcingLineItem`, `CommercialInvoiceSummary`): Itemized supplier net rates, agency markup, and multi-currency conversions across GDS/Bedbank/DMC channels.
  - **Omnichannel Messaging & Transports**: Verified provider dispatch and Webhook verification (`/api/v1/messaging/*`).
- [x] **Wave 14 / Wave B**: Agentic Expansion:
  - **Tier 3 Suitability Scorer** (`LLMContextualScorer` with disk caching and tour-context keys).
  - **Communicator Agent** (Autonomous multi-tonal clarification drafting for blocked inquiries).
  - **Operator Refinement Agent** (Autonomous refinement loops and counterfactual trade-off proposals).
- [x] **Wave 13**: Risk-Adjusted Dynamic Fee Calculation & FX Protection.
- [x] **Wave 12**: Suitability Engine Foundation (Tier 1 tag rules & Tier 2 itinerary coherence).
- [x] **Wave 11**: Real-time SLA Tracking & Escalation.
- [x] **Wave 10**: Feedback-Driven Actioning.
- [x] **Wave 9**: Post-Trip Feedback & CSAT Analytics.
- [x] **Wave 8**: Output Delivery UX & Review Feedback.
- [x] **Wave 7**: URL-Driven State Architecture.
