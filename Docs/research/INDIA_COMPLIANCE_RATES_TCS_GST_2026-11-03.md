# India Compliance Rates — TCS + GST current-law research (2026-11-03)

**Purpose:** source-backed rate data for the jurisdiction-aware compliance layer
(TRV-DP-06 / R2-C build, owner lift of the pilot-onboarding trigger, 2026-11-03).
**Method:** TinyFish Search+Fetch (built-in WebSearch quota-blocked until
2026-11-06, per standing directive). Claims below are labeled by truth taxonomy
(OPERATING_DOCTRINE §2): tier-4 external evidence (fetched live pages), with
staleness falsifiers.

## CRITICAL CORRECTION vs TRV-DP-06 / COUNCIL_OPEN_ITEM_ADJUDICATION_2026-10-30

The adjudication record describes TCS as "5%/20% over ₹7L, PAN-gated" — that is
the **FY2024-25 (post-Budget-2024) rule and is STALE**. Current law (two
independent specialist sources + official Income Tax Dept snippet):

### TCS — Overseas Tour Programme Package (the travel-agency case)

| Window | Rate on tour-package amount | Basis |
|---|---|---|
| ≥2025-04-01 (Budget 2025) | 5% up to ₹10 lakh; 20% above ₹10L / without PAN | Budget 2025 threshold change |
| ≥2026-04-01 (Budget 2026, **current**) | **2% flat, from the first rupee** (no threshold) | IT Act 2025 s.394(1) Table Sl. No. 8.D(a)&(b); BookMyForex: "flat 2% TCS from the first rupee" |

Related rows (not the agency's collection duty, needed for traveler-facing
explanation): LRS education/medical >₹10L → 2%; LRS other purposes >₹10L → 20%.
History: Oct-2023 20% over ₹7L → Budget 2025 ₹10L threshold → Budget 2026 flat 2%.

**Sources (fetched 2026-11-03):**
- https://blog.tdsman.com/2026/09/tcs-on-foreign-remittances-and-overseas-tour-packages-section-3941-206c1g/ (2026-09-10; rate table incl. IT Act 2025 section renumbering)
- https://www.bookmyforex.com/blog/new-tcs-on-foreign-travel-what-you-need-to-know/ (Budget 2026 explainer; timeline 20%→₹10L threshold→flat 2%)
- https://www.incometaxindia.gov.in/documents/20117/42998/Tax-Collection-at-Source-TCS_2026-01-19_06-07-07_032f98_en.pdf (official dept PDF; snippet via Search)

### GST 2.0 — travel services (effective 2025-09-22, GST Council 56th meeting)

| Service | Rate | Condition |
|---|---|---|
| Hotel rooms ≤ ₹7,500/night | **5% (without ITC)** | basis moved from "declared tariff" to **transaction value** from 2025 |
| Hotel rooms > ₹7,500/night | **18% (with ITC)** | unchanged |
| Economy/premium-economy air travel | 5% | unchanged |
| Business-class air travel | 12% | unchanged |
| Restaurants (incl. in hotels) | 5% without ITC | GST 2.0 simplification |

**Sources (fetched 2026-11-03):**
- https://gstcouncil.gov.in/sites/default/files/2025-09/faq_0.pdf (official FAQ; found via Search; PDF fetch not machine-parsed — cited by URL)
- https://blog.axisrooms.com/hotel-gst/ (fetched; 5% w/o ITC ≤₹7,500 from 22 Sept 2025, transaction-value basis)
- https://www.bajajfinserv.in/all-about-gst-on-hotel-rooms + https://www.hdfcergo.com/blogs/travel-insurance/gst-cuts-on-budget-hotels-economy-flights-in-2025 (corroborating, via Search snippets)

## Compliance-layer design implications (Verified → Proposed)

1. **Effective-dated matrix is mandatory, not optional** — rates changed in
   Apr-2024, Oct-2023, Apr-2025, Sep-2025, Apr-2026. A static table would
   already be wrong once (proven above).
2. **The adjudication's own rate claim needed correction** — reinforces
   doctrine §0 (live truth) for regulatory data: the matrix rows must carry
   `source_url` + `effective_from` + `as_of_checked`.
3. Calc is **display/estimate-only** (calc-only boundary per adjudication R2-C:
   no money movement, no filing duty assumed); PAN-gating becomes a
   configuration flag default-conservative.
4. **Falsifiers:** next GST Council meeting or Union Budget alters any row
   (budget cycle ≈ Feb, effective ≈ Apr 1); a compliance review disputes the
   flat-2% interpretation; official CBIC notification contradicts the
   specialist summaries. Re-verify matrix on any budget/GST-council event.

**Unverified/Unknown:** exact PAN-absent handling for tour packages under the
2% regime (sources silent; encode as config flag, default = PAN-required
conservative note, never fabricate); agency GSTIN/ITC posture is
agency-config, not rate data.
