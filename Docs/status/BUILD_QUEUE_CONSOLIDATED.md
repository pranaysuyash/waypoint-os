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
