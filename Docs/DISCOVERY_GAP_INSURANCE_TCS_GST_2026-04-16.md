# Discovery Gap Analysis: Insurance/TCS/GST Compliance

**Date**: 2026-04-16
**Gap Register**: #15 (P2 — Indian regulatory compliance)
**Scope**: TCS (Tax Collected at Source) on overseas packages, GST compliance, mandatory travel insurance, LRS/FEMA forex compliance. NOT: payment processing (#04), general financial state.

---

## 1. Executive Summary

Indian travel agencies handling overseas packages must comply with TCS (5% on packages >₹7L, 0.5% below), GST (18% on service component), mandatory travel insurance for Schengen/visa-required countries, and LRS/FEMA reporting for forex. **None of this is modeled, computed, or tracked.** The system has a `visa_insurance` budget bucket (heuristic cost estimates) but no compliance engine, no tax calculation, and no regulatory reporting.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L28-30 | TCS: 5% on packages >₹7 lakh, 0.5% below — "No TCS computation, no tracking, no reporting" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L37-39 | GST: 18% on service component, input tax credit — "No GST computation" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L44 | PAN card collection for transactions >₹50K — "No document compliance" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L108 | Mandatory insurance for visa countries — "No insurance rules engine" | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L131, L133 | LRS/FEMA reporting, forex compliance — "Not modeled" | Docs/ |
| `MASTER_GAP_REGISTER` L131-133 | TCS/GST, LRS/FEMA — all "Not modeled" | Docs/ |
| `decision.py` L53, L918, L956-963 | `visa_insurance` budget bucket — heuristic cost estimate per destination | src/ |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `decision.py` L53, L918 | `visa_insurance` as budget bucket with heuristic costs per destination | **Heuristic estimate** — no compliance logic |
| `decision.py` L956-963 | Domestic trip skips visa_insurance; flags visa_fee_omission for multi-destination | **Working** — basic awareness |

### What's NOT Implemented

- No TCS calculation (5%/0.5% based on package amount)
- No GST computation (18% on service component)
- No TCS/GST reporting
- No PAN card collection threshold
- No mandatory insurance rules engine
- No LRS/FEMA reporting
- No forex compliance tracking
- No e-invoice generation

---

## 3. Phase-In Recommendations

### Phase 1: TCS + GST Calculation (P2, ~2-3 days, blocked by #04)

1. Create `ComplianceCalc` dataclass: TCS rate, GST rate, taxable amount, total compliance cost
2. Compute TCS: package >₹7L → 5%, else 0.5%. GST: 18% on service component.
3. Add compliance breakdown to quote output (separate from trip cost)
4. Store compliance amounts in financial state (#04)

**Acceptance**: Quote shows: "Trip cost: ₹2.8L. TCS (0.5%): ₹14,000. GST (18% on service ₹45,000): ₹8,100. Total: ₹3.02L."

### Phase 2: Insurance Rules + PAN (P2, ~2 days)

1. Add insurance requirement check per destination (Schengen = mandatory, minimum €30K)
2. Add PAN card collection reminder for transactions >₹50K
3. Wire insurance compliance to document checklist (#10)

**Acceptance**: System flags: "Schengen visa requires mandatory travel insurance (minimum €30K coverage). PAN card required for package >₹50,000."

### Phase 3: LRS/FEMA + Reporting (P3, ~2-3 days)

1. Add LRS declaration reminder for overseas remittance >$250K
2. Add FEMA compliance tracking for forex transactions
3. Add quarterly compliance report generation

**Acceptance**: Agent gets reminded: "LRS declaration required for this ₹4.5L overseas package."

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Compliance data source | (a) Hardcoded Indian tax rules, (b) Configurable rules per jurisdiction, (c) Third-party tax API | **(a) Hardcoded Indian rules for MVP** — only serving Indian agencies |
| Invoice generation | (a) Manual, (b) PDF generation, (c) E-invoice API | **(a) Manual for MVP** — agent generates invoices externally |

**Out of Scope**: Multi-jurisdiction tax compliance, automated tax filing, bank integration for TCS collection, GST return filing, accounting system integration (Tally/QuickBooks).