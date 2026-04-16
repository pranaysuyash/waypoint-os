# Discovery Gap Analysis: Seasonality/Dynamic Pricing

**Date**: 2026-04-16
**Gap Register**: #14 (P2 — pricing accuracy)
**Scope**: Seasonal rate awareness, peak pricing, quote accuracy improvements. NOT: payment processing, financial state tracking (#04).

---

## 1. Executive Summary

The system has deterministic budget feasibility tables (`BUDGET_FEASIBILITY_TABLE` and `BUDGET_BUCKET_RANGES` in `decision.py`) with per-destination cost estimates — all marked `maturity: "heuristic"` and derived from general knowledge, not real-time data. There is no seasonality model, no date-aware pricing, no peak/off-peak awareness, and no dynamic pricing from supplier APIs. A Goa trip quoted in December (peak) uses the same budget estimates as one in August (off-peak).

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L75-76 | Seasonal pricing variation (3x in peak), hotel rate fluctuations | Docs/ |
| `15_MISSING_CONCEPTS.md` L90-93 | Missing Concept #6: `travel_dates` affects feasibility and budget; peak/off-peak matters | notebooks/ |
| `FROZEN_SPINE_STATUS.md` L111 | "Seasonal pricing adjustments" listed as needed capability | Docs/ |
| `decision.py` L370-683 | `BUDGET_FEASIBILITY_TABLE` (25+ destinations) and `BUDGET_BUCKET_RANGES` (20+ destinations) — all heuristic, no seasonal variation | src/ |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `decision.py` L370-399 | `BUDGET_FEASIBILITY_TABLE`: per-destination cost estimates, all `maturity: "heuristic"` | **Working but static** — no date awareness |
| `decision.py` L402-683 | `BUDGET_BUCKET_RANGES`: per-destination cost breakdown (flights, stay, food, etc.) | **Working but static** — no seasonal variation |
| `extractors.py` L222-276 | Date extraction with month awareness | **Working** — extracts dates but doesn't use them for pricing |

### What's NOT Implemented

- No seasonality model (peak/off-peak dates per destination)
- No date-aware budget adjustment (December Goa != August Goa)
- No supplier rate feeds
- No dynamic pricing from APIs
- No fare class awareness (refundable vs. non-refundable)
- No booking window impact on pricing (book 3 months ahead vs. 3 days)

---

## 3. Phase-In Recommendations

### Phase 1: Seasonal Multipliers (P2, ~1-2 days, blocked by #02 for persistence)

1. Add `peak_dates` dictionary per destination (e.g., Goa: Dec-Jan peak, Jun-Sep off-peak)
2. Add `season_multiplier` function: given destination + month → multiplier (0.7 to 1.5)
3. Apply multiplier to budget feasibility estimates
4. Show agent: "December Goa: ×1.4 peak season multiplier applied"

**Acceptance**: Agent quoting a Goa trip in December sees "Peak season: budget estimates ×1.4" and adjusted numbers.

### Phase 2: Booking Window Awareness (P3, ~1-2 days)

1. Add booking window impact: "book 60+ days ahead → estimate ×0.85, book <7 days → estimate ×1.2"
2. Add fare class impact: refundable vs. non-refundable price difference per route
3. Wire date extraction results to budget calculation

**Acceptance**: System adjusts estimates based on booking window and extracts travel dates to compute seasonality.

### Phase 3: Supplier Rate Integration (P3+, blocked by #01)

1. Connect to 1-2 supplier APIs for live hotel pricing
2. Use live rates as baseline, heuristic tables as fallback
3. Track rate accuracy over time (heuristic vs. actual)

**Acceptance**: System shows both "estimated ₹35,000" and "live rate ₹38,500" for hotel in Goa in December.

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Seasonality data source | (a) Manual per-destination table, (b) OTA API, (c) Historical booking data | **(a) Manual table** for MVP — covers top 20 destinations with typical peak/off-peak periods |
| Pricing refresh frequency | (a) Static tables updated quarterly, (b) Daily API refresh, (c) Real-time | **(a) Quarterly updates** for MVP |

**Out of Scope**: Real-time supplier pricing API integration (Phase 3+), ML-based demand prediction, fare alert monitoring, price matching against OTAs.