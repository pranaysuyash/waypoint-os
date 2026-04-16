# Master Gap Register — Waypoint OS

**Date**: 2026-04-16
**Purpose**: Single source of truth for ALL documented gaps across all areas. Each gap will be linked to a dedicated deep-dive analysis as it's completed.
**Method**: Consolidated from INDUSTRY_PROCESS_GAP_ANALYSIS, PERSONA_PROCESS_GAP_ANALYSIS, COVERAGE_MATRIX, CODEBASE_ANALYSIS, test gap analyses, and systemic area audit.
**Preceded By**: Scattered fragments across 5+ docs — this consolidates them.

---

## What This Is

A **register**, not an analysis. Each row links to (or will link to) a dedicated discovery gap analysis that provides:
- Evidence inventory (what's documented vs. what's coded)
- Gap taxonomy (structural, computation, integration, decision-state)
- Dependency graph
- Data model specifications
- Phase-in recommendations
- Key decisions required

---

## Register: 17 Gap Areas

| # | Area | Deep-Dive Doc | Doc Status | Priority | Blocks | Blocked By |
|---|------|--------------|------------|----------|--------|------------|
| 01 | Vendor/Cost/Sourcing/Margin Tracking | [DISCOVERY_GAP_ANALYSIS](VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md) | **Complete** | P0 | All commercial features, sourcing logic, supplier risk flags | Nothing (foundational) |
| 02 | Data Persistence & State Architecture | [DISCOVERY_GAP](DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md) | **Complete** | P0 | Everything — system forgets between runs | Nothing (foundational) |
| 03 | Communication & Channel Architecture | [DISCOVERY_GAP](DISCOVERY_GAP_COMMUNICATION_CHANNELS_2026-04-16.md) | **Complete** | P0 | All output delivery, proposal sending, client interaction | #02 (needs persistence for message state) |
| 04 | Financial State Tracking | [DISCOVERY_GAP](DISCOVERY_GAP_FINANCIAL_STATE_2026-04-16.md) | **Complete** | P0 | Quote/collected/pending/confirmed state tracking — NO payment gateway, NO reconciliation, NO commission settlement. Agencies collect money wherever they want; system just records the state. | #02 (needs DB), #01 (needs cost ledger) |
| 05 | Cancellation/Refund Policy Engine | [DISCOVERY_GAP](DISCOVERY_GAP_CANCELLATION_REFUND_2026-04-16.md) | **Complete** | P1 | Cancellation workflow, refund state tracking, policy lookup | #04 (needs financial state), #01 (needs supplier policies) |
| 06 | Customer Lifecycle & Cross-Trip Memory | [DISCOVERY_GAP](DISCOVERY_GAP_CUSTOMER_LIFECYCLE_2026-04-16.md) | **Complete** | P1 | Repeat detection, retention, conversion tracking | #02 (needs customer entity/persistence) |
| 07 | LLM/AI Integration Architecture | [DISCOVERY_GAP](DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md) | **Complete** | P1 | All "AI" features — extraction, question gen, proposal gen | Nothing (parallel track to #02) |
| 08 | Auth/Identity & Multi-Agent | [DISCOVERY_GAP](DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md) | **Complete** | P1 | Roles, permissions, team ops, traveler portal | #02 (needs user DB) |
| 09 | In-Trip Ops & Emergency Protocol | [DISCOVERY_GAP](DISCOVERY_GAP_IN_TRIP_OPS_EMERGENCY_2026-04-16.md) | **Complete** | P2 | Active-trip monitoring, crisis handling, rebooking | #02 (needs trip state persistence), #03 (needs alert delivery) |
| 10 | Document/Visa Management | [DISCOVERY_GAP](DISCOVERY_GAP_DOCUMENT_VISA_MANAGEMENT_2026-04-16.md) | **Complete** | P1 | Visa database, document checklists, timeline risk | #02 (needs document storage), #08 (needs upload auth) |
| 11 | Post-Trip/Feedback/Learning Loops | [DISCOVERY_GAP](DISCOVERY_GAP_POST_TRIP_FEEDBACK_LOOPS_2026-04-16.md) | **Complete** | P2 | Supplier scoring from reviews, retention loops | #06 (needs customer memory), #01 (needs supplier entity) |
| 12 | Analytics/Reporting Pipeline | [DISCOVERY_GAP](DISCOVERY_GAP_ANALYTICS_REPORTING_2026-04-16.md) | **Complete** | P2 | Owner dashboards, conversion metrics, KPI tracking | #02 (needs event storage), #06 (needs lifecycle data) |
| 13 | Audit Trail/Action Logging | [DISCOVERY_GAP](DISCOVERY_GAP_AUDIT_TRAIL_ACTION_LOGGING_2026-04-16.md) | **Complete** | P1 | Change tracking, accountability, compliance | #02 (needs event store) |
| 14 | Seasonality/Dynamic Pricing | [DISCOVERY_GAP](DISCOVERY_GAP_SEASONALITY_DYNAMIC_PRICING_2026-04-16.md) | **Complete** | P2 | Seasonal rate awareness, peak pricing, quote accuracy | #01 (needs supplier cost data) |
| 15 | Insurance/TCS/GST Compliance | [DISCOVERY_GAP](DISCOVERY_GAP_INSURANCE_TCS_GST_2026-04-16.md) | **Complete** | P2 | Indian tax compliance, mandatory insurance, claims | #04 (needs payment/invoicing layer) |
| 16 | Configuration Management | [DISCOVERY_GAP](DISCOVERY_GAP_CONFIGURATION_MANAGEMENT_2026-04-16.md) | **Complete** | P2 | Per-agency settings, margin policies, feature flags | #02 (needs config storage) |
| 17 | Industry Blind Spots (20 items) | [DISCOVERY_GAP](DISCOVERY_GAP_INDUSTRY_BLIND_SPOTS_2026-04-16.md) | **Complete** | P2-P3 | PNR tracking, rooming lists, forex, accounting integration, etc. | Multiple — see section below |

---

## Current Deep-Dive Completion Status

| # | Area | Status |
|---|------|--------|
| 01 | Vendor/Cost/Sourcing/Margin | ✅ Complete — `VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md` |
| 02 | Data Persistence | ✅ Complete — `DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md` |
| 03 | Communication/Channels | ✅ Complete — `DISCOVERY_GAP_COMMUNICATION_CHANNELS_2026-04-16.md` |
| 04 | Financial State Tracking | ✅ Complete — `DISCOVERY_GAP_FINANCIAL_STATE_2026-04-16.md` |
| 05 | Cancellation/Refund | ✅ Complete — `DISCOVERY_GAP_CANCELLATION_REFUND_2026-04-16.md` |
| 06 | Customer Lifecycle | ✅ Complete — `DISCOVERY_GAP_CUSTOMER_LIFECYCLE_2026-04-16.md` |
| 07 | LLM/AI Integration | ✅ Complete — `DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md` |
| 08 | Auth/Identity & Multi-Agent | ✅ Complete — `DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` |
| 09 | In-Trip/Emergency | ✅ Complete — `DISCOVERY_GAP_IN_TRIP_OPS_EMERGENCY_2026-04-16.md` |
| 10 | Document/Visa | ✅ Complete — `DISCOVERY_GAP_DOCUMENT_VISA_MANAGEMENT_2026-04-16.md` |
| 11 | Post-Trip/Feedback | ✅ Complete — `DISCOVERY_GAP_POST_TRIP_FEEDBACK_LOOPS_2026-04-16.md` |
| 12 | Analytics/Reporting | ✅ Complete — `DISCOVERY_GAP_ANALYTICS_REPORTING_2026-04-16.md` |
| 13 | Audit Trail | ✅ Complete — `DISCOVERY_GAP_AUDIT_TRAIL_ACTION_LOGGING_2026-04-16.md` |
| 14 | Seasonality | ✅ Complete — `DISCOVERY_GAP_SEASONALITY_DYNAMIC_PRICING_2026-04-16.md` |
| 15 | Insurance/TCS/GST | ✅ Complete — `DISCOVERY_GAP_INSURANCE_TCS_GST_2026-04-16.md` |
| 16 | Configuration | ✅ Complete — `DISCOVERY_GAP_CONFIGURATION_MANAGEMENT_2026-04-16.md` |
| 17 | Industry Blind Spots | ✅ Complete — `DISCOVERY_GAP_INDUSTRY_BLIND_SPOTS_2026-04-16.md` |

---

## Where Existing Fragments Live (Do NOT Delete)

These docs contain partial gap information that the deep-dives will consolidate:

| Existing Doc | Covers | Gap Register Area(s) |
|-------------|--------|---------------------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS_2026-04-16.md` | 23 financial ops, supplier ops, visa, comms, crisis, 15 dealbreaker processes, 20 undocumented items | #01, #04, #05, #09, #10, #15, #17 |
| `PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md` | Per-persona gaps (P1: solo agent, P2: owner, P3: junior, S1/S2: traveler), team ops, infrastructure, LLM, testing | #02, #03, #06, #07, #08, #12, #13 |
| `COVERAGE_MATRIX_2026-04-15.md` | Risk, persona, scenario, lifecycle, market coverage matrices with build-control columns | All areas (sparse) |
| `TEST_GAP_ANALYSIS.md` | 30 scenario test gaps, P0-P2 prioritized | #01, #05, #10, #14 |
| `CODEBASE_ANALYSIS_2026-04-12.md` | Planned modules, data strategy gaps, architecture gaps | #02, #07, #13 |
| `VENDOR_COST_TRACKING_GAP_ANALYSIS_2026-04-16.md` | Initial discussion capture (superseded by discovery analysis) | #01 |
| `VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md` | Full deep-dive with evidence, dependency graph, data models, phase-in | #01 |
| `15_MISSING_CONCEPTS.md` | 15 missing NB concepts with priority assignments | #01, #06, #10, #14 |
| `SCENARIO_COVERAGE_GAPS.md` | 30 scenario → NB coverage matrix | #01, #05, #06, #10 |
| `FROZEN_SPINE_STATUS.md` | Spine module status including stub signals | #01, #05, #14 |
| `ROLLING_CONTEXT_SYNTHESIS.md` | Cross-part synthesis | Cross-cutting |

---

## Dependency Graph (Simplified)

```
FOUNDATIONAL (must exist first)
├── #02 Data Persistence ──────────── blocks EVERYTHING
├── #01 Vendor/Cost/Sourcing ──────── blocks all commercial features
└── #07 LLM/AI Integration ────────── blocks extraction quality, generation

CORE FEATURES (blocked by foundational)
├── #08 Auth/Identity ─────────────── blocked by #02
├── #03 Communication/Channels ─────── blocked by #02
├── #04 Financial State Tracking ──────── blocked by #02, #01
├── #06 Customer Lifecycle ──────────── blocked by #02
├── #10 Document/Visa ───────────────── blocked by #02
└── #13 Audit Trail ─────────────────── blocked by #02

DERIVATIVE FEATURES (blocked by core)
├── #05 Cancellation/Refund ──────────── blocked by #04, #01
├── #09 In-Trip/Emergency ────────────── blocked by #02, #03
├── #11 Post-Trip/Feedback ────────────── blocked by #06, #01
├── #12 Analytics/Reporting ────────────── blocked by #02, #06
├── #14 Seasonality ─────────────────────── blocked by #01
├── #15 Insurance/TCS/GST ──────────────── blocked by #04
└── #16 Configuration ────────────────────── blocked by #02

INDUSTRY EXPANSION (long tail)
└── #17 Industry Blind Spots (20 items) ──── blocked by multiple
```

---

## Area #17: Industry Blind Spots (Not Documented Anywhere Else)

From `INDUSTRY_PROCESS_GAP_ANALYSIS_2026-04-16.md` section 11 — "What the Docs Don't Cover At All":

| # | Process | Why It Matters | Status |
|---|---------|---------------|--------|
| 1 | Component-level trip costing | Each component (flight, hotel, transfer, activity) sourced separately with different margin rules | Not modeled |
| 2 | Supplier contract/rate management | Contracted rates, allotments, release dates | Not modeled |
| 3 | PNR/booking reference tracking | Per-supplier confirmation numbers | Not modeled |
| 4 | Ticketing deadlines | Airline fare hold expiry, "will this price hold until client confirms?" | Not modeled |
| 5 | TCS/GST tax compliance | Indian tax requirements on overseas packages | Not modeled |
| 6 | LRS/FEMA foreign exchange compliance | Individual remittance limits, record keeping | Not modeled |
| 7 | Visa application process management | Not just requirement lookup — the actual submission workflow | Not modeled |
| 8 | Pre-departure communication cadence | D-7, D-3, D-1 automated briefings | Not modeled |
| 9 | During-trip monitoring | Flight status, check-in confirmation | Not modeled |
| 10 | Supplier feedback from client reviews | Closing the quality loop | Not modeled |
| 11 | Rooming list management | For groups — who is in which room | Not modeled |
| 12 | Transfer vehicle type mapping | By party size — sedan/Innova/Tempo/Coach | Not modeled |
| 13 | Activity/excursion slot booking | Time-sensitive pre-booking (Universal Studios timed entry) | Not modeled |
| 14 | Forex card arrangement | Multi-currency loading, rates, delivery | Not modeled |
| 15 | Corporate travel policy compliance | For B2B bookings — approval workflows, spend limits | Not modeled |
| 16 | Medical/accessibility requirement planning | Elderly/disabled travelers — wheelchair, hospital proximity | Not modeled |
| 17 | Destination seasonality intelligence | Best-time-to-visit matrix, weather patterns | Not modeled |
| 18 | Connection risk scoring | Layover time + terminal change + immigration risk | Not modeled |
| 19 | Accounting system integration | Tally/QuickBooks export | Not modeled |
| 20 | Payment gateway integration | Razorpay/PayU payment links | Not modeled |

Items 1-4 overlap with existing gap areas (#01, #04, #14). Items 5-6 overlap with #15. Items 7-9 overlap with #10, #09. The rest are genuinely undocumented anywhere.

---

## Naming Convention for Deep-Dive Docs

Each deep-dive follows the pattern:
```
Docs/DISCOVERY_GAP_{AREA}_2026-04-16.md
```

Example: `DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md`

Each deep-dive MUST include:
1. Executive Summary
2. Evidence Inventory (doc intent vs. code reality)
3. Gap Taxonomy (structural, computation, integration, decision-state)
4. Dependency Graph
5. Data Model Specifications
6. Phase-In Recommendations
7. Key Decisions Required
8. Risks

---

*This register is the control document. Deep-dive analyses are linked from column 3. When a deep-dive is completed, update the link and status.*