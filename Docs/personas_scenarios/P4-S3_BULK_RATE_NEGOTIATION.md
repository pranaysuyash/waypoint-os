# Scenario P4-S3: Bulk Rate Negotiation Support

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P1 (High — revenue leverage missing)

---

## Scenario Description**

Vikram is preparing for a contract renewal with Taj Hotels. His company spends ~₹80L/year at Taj properties (Mumbai, Delhi, Bangalore). He needs to negotiate:
- Current rate: ₹8,500/night (standard room, includes breakfast)
- Ask: ₹7,000/night (15% discount) based on volume (200 room-nights/year)
- Justification: "Competitor IHG offers ₹6,500. Match or lose the account."

The system should analyze: "200 room-nights, ₹80L annual spend. Leverage: HIGH. Recommended ask: ₹6,800 (20% discount)."

---

## Input (Spend Analysis Request)**

```json
{
  "company_id": "techcorp-001",
  "vendor": "Taj Hotels",
  "annual_spend": 8000000,
  "room_nights": 200,
  "current_avg_rate": 8500,
  "competitor_rate": 6500,
  "contract_renewal_date": "2026-06-30",
  "negotiation_leverage": null,
  "recommended_ask": null
}
```

---

## Expected System Behavior**

1. **Spend Analysis** (`src/analytics/spend_analysis.py` — to be built) processes: 200 nights × ₹8,500 = ₹80L confirmed.
2. **Leverage Calculation:** `spend > ₹50L` → leverage `HIGH`. Competitor rate ₹6.5K → ask `₹6,800` (20% off current).
3. **Negotiation Brief:** Generate PDF: "Taj Renewal 2026 — Annual Spend ₹80L, Ask ₹6.8K (save ₹34L/year)."
4. **Threat Analysis:** "IHG offers ₹6.5K. If Taj doesn't match, switch 60% of volume = ₹48L lost revenue for Taj."
5. **Output to Vikram:** "📊 NEGOTIATION BRIEF: Ask ₹6.8K (20% off). Leverage: HIGH (₹80L spend). Threat: IHG at ₹6.5K."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Spend analytics** | ❌ Not implemented | No `src/analytics/` directory |
| **Vendor performance tracking** | ❌ Not implemented | No vendor scoring |
| **Negotiation brief generator** | ❌ Not implemented | No PDF generation for contracts |
| **Leverage calculator** | ❌ Not implemented | No spend-based scoring |

---

## Success Criteria**

- [ ] System analyzes annual spend: ₹80L confirmed
- [ ] Leverage score: HIGH (spend > ₹50L)
- [ ] Recommended ask: ₹6,800 (20% off) with justification
- [ ] Threat analysis: IHG at ₹6.5K, 60% volume at risk
- [ ] Negotiation brief PDF generated with charts and savings

---

## Failure Mode (If System Doesn't Help)**

Vikram walks into the Taj renewal meeting with a handwritten note: "Please give us 15% discount." Taj asks: "Why? What's your volume? What's the market rate?" Vikram stumbles. Taj offers 5% discount. Vikram loses ₹10L in negotiating power.

---

## Notes**

- This is a "nice-to-have" for mid-size companies but CRITICAL for ₹5Cr+ annual spend companies.
- The `vendor_contracts[]` array needs to be added to the canonical packet.
- Negotiation brief should include market benchmarks (scraped or manual entry).
- **Related files to create:** `src/analytics/spend_analysis.py`, `src/negotiation/brief_generator.py`, `frontend/components/NegotiationDashboard.tsx`
