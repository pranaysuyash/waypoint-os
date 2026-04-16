# Discovery Gap Analysis: Industry Blind Spots (20 Items)

**Date**: 2026-04-16
**Gap Register**: #17 (P2-P3 — documented nowhere else in the system)
**Scope**: Processes, regulations, and operational capabilities that Indian travel agencies handle daily but are completely absent from the system's documentation and code. These were identified in `INDUSTRY_PROCESS_GAP_ANALYSIS_2026-04-16.md` section 11 as "What the Docs Don't Cover At All."

---

## 1. Executive Summary

Section 11 of the industry gap analysis identified **20 industry processes** that are not mentioned or modeled anywhere in the codebase or documentation. These range from PNR tracking and rooming lists to forex cards and accounting integration. Some overlap with existing gap areas (#01, #04, #09, #10, #15), while others are genuinely undocumented capabilities that agencies need.

---

## 2. Complete Blind Spot Inventory

| # | Process | Why It Matters | Overlaps With | Recommended Phase-in |
|---|---------|---------------|---------------|---------------------|
| 1 | **Component-level trip costing** | Each component (flight, hotel, transfer, activity) sourced separately with different margin rules | #01 (vendor/cost) | Phase into #01 vendor data model |
| 2 | **Supplier contract/rate management** | Contracted rates, allotments, release dates, seasonal commitments | #01 (vendor/cost) | Phase into #01 vendor data model |
| 3 | **PNR/booking reference tracking** | Per-supplier confirmation numbers (airline PNR, hotel confirmation, activity voucher) | #01 (vendor/cost) | Phase into #01 as booking reference field |
| 4 | **Ticketing deadlines** | Airline fare hold expiry, "will this price hold until client confirms?" | #14 (seasonality) | Phase into #14 as deadline awareness |
| 5 | **TCS/GST tax compliance** | Indian tax requirements on overseas packages | #15 (insurance/tax) | Covered in #15 deep-dive |
| 6 | **LRS/FEMA foreign exchange compliance** | Individual remittance limits, record keeping | #15 (insurance/tax) | Covered in #15 deep-dive |
| 7 | **Visa application process management** | Not just requirement lookup — the actual submission workflow | #10 (document/visa) | Covered in #10 deep-dive |
| 8 | **Pre-departure communication cadence** | D-7, D-3, D-1 automated briefings | #09 (in-trip ops) | Covered in #09 Phase 2 |
| 9 | **During-trip monitoring** | Flight status, check-in confirmation | #09 (in-trip ops) | Covered in #09 Phase 3 |
| 10 | **Supplier feedback from client reviews** | Closing the quality loop | #11 (post-trip) | Covered in #11 Phase 2 |
| 11 | **Rooming list management** | For groups — who is in which room | **New blind spot** | P3 — add to trip entity as group management |
| 12 | **Transfer vehicle type mapping** | By party size — sedan/Innova/Tempo/Coach | #01 (vendor/cost) | Phase into #01 as vehicle type dimension |
| 13 | **Activity/excursion slot booking** | Time-sensitive pre-booking (Universal Studios timed entry) | #01 (vendor/cost) | Phase into #01 as booking urgency field |
| 14 | **Forex card arrangement** | Multi-currency loading, rates, delivery | **New blind spot** | P3 — add to financial state as forex component |
| 15 | **Corporate travel policy compliance** | For B2B — approval workflows, spend limits | **New blind spot** | P3 — add to #08 auth as corporate policy layer |
| 16 | **Medical/accessibility requirement planning** | Elderly/disabled travelers — wheelchair, hospital proximity | **New blind spot** | P2 — add to #10 as health requirements checklist |
| 17 | **Destination seasonality intelligence** | Best-time-to-visit matrix, weather patterns | #14 (seasonality) | Covered in #14 deep-dive |
| 18 | **Connection risk scoring** | Layover time + terminal change + immigration risk | **New blind spot** | P2 — add to decision engine as flight risk flag |
| 19 | **Accounting system integration** | Tally/QuickBooks export | **New blind spot** | P3 — CSV/PDF export, no API integration |
| 20 | **Payment gateway integration** | Razorpay/PayU payment links | #04 (financial state) | Explicitly out of scope per user direction |

---

## 3. Genuinely New Blind Spots (Not Covered by Other Gaps)

Items 11, 14, 15, 16, 18, and 19 are genuinely new blind spots not covered by any existing gap area:

### 3a. Rooming List Management (Item #11)

**What**: For group trips (families, corporate groups), the agency needs to assign travelers to rooms. This includes room types (single, double, triple, suite), sharing preferences, and special requests (adjacent rooms, ground floor).

**Why it matters**: Groups of 6-8 travelers need room allocation before hotel booking. The agency sends the rooming list to the hotel.

**Recommendation**: Add `RoomingList` to trip entity with per-traveler room assignment. Phase 3.

### 3b. Forex Card Arrangement (Item #14)

**What**: Indian travelers on overseas packages need forex cards (multi-currency prepaid cards). The agency arranges loading, rate locking, and delivery.

**Why it matters**: Agencies earn commission on forex cards (1-2% markup). It's a revenue stream and a customer convenience.

**Recommendation**: Add forex card as a component in `FinancialState`. Track as financial item. Phase 3.

### 3c. Corporate Travel Policy Compliance (Item #15)

**What**: B2B trips have corporate policy constraints: max hotel budget, approved airlines only, pre-approval requirements, spend limits per category.

**Why it matters**: Corporate travel is 20-30% of Indian agency revenue. The agency must enforce client policy.

**Recommendation**: Add corporate policy layer to #08 auth — policy rules per corporate client. Phase 3.

### 3d. Medical/Accessibility Requirement Planning (Item #16)

**What**: Elderly travelers need nearby hospitals, wheelchair accessibility, ground-floor rooms. Travelers with conditions need medical clearance, insurance with pre-existing conditions.

**Why it matters**: Safety-critical. A traveler with cardiac issues booked into a remote hill station without hospital access is a liability.

**Recommendation**: Add health requirements checklist to #10 document management. Flag destinations without adequate medical access. Phase 2.

### 3e. Connection Risk Scoring (Item #18)

**What**: Multi-segment flights have layover risk. Tight connections (45min domestic, 90min international), terminal changes, immigration lines, and re-check requirements create risk factors.

**Why it matters**: Missed connections are the #1 disruption risk for multi-city itineraries. Proactively flagging tight connections prevents problems.

**Recommendation**: Add `connection_risk` flag to decision engine. Score based on layover time, terminal change, and immigration requirements. Phase 2.

### 3f. Accounting System Integration (Item #19)

**What**: Agencies need to export financial data to Tally, QuickBooks, or Zoho Books for GST filing, P&L statements, and commission tracking.

**Why it matters**: Every agency uses accounting software. Manual double-entry is error-prone and time-consuming.

**Recommendation**: Add CSV/PDF export from financial state. No API integration (accounting systems vary). Phase 3.

---

## 4. Summary

Of 20 blind spots:
- **4 overlap fully** with existing gaps (#01, #04, #14, #15)
- **4 overlap partially** with existing gaps (#09, #10, #11, #14)
- **6 are genuinely new** blind spots (rooming lists, forex cards, corporate policy, medical/accessibility, connection risk, accounting)
- **1 is explicitly out of scope** per user direction (payment gateway)
- **1 is covered** by existing vendor data model (transfer vehicle types)

The 6 new blind spots should be folded into relevant existing gap areas during implementation rather than treated as standalone work items.