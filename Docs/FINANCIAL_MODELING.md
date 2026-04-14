# Financial Modeling

**Date**: 2026-04-14
**Purpose**: Is this a viable business? What are the numbers?

---

## The Solo Builder Financial Reality

> "A profitable business with $10K MRR is better than a funded startup burning $100K/month."

Your goal: Profitability on minimal revenue.

---

## Unit Economics

### Per-Customer Math

| Tier | Price | Monthly cost to serve | Gross margin |
|------|-------|----------------------|--------------|
| **Solo** | ₹999 | ~₹100 (hosting + API) | 90% |
| **Small** | ₹3,999 | ~₹200 | 95% |
| **Medium** | ₹9,999 | ~₹500 | 95% |

**Costs per customer**:
- Hosting/database: ~₹50-100/month (amortized)
- OpenAI API: ~₹50-400/month depending on usage
- Support: ~₹50-100/month (your time amortized)
- **Total**: ₹150-600/month

**Key insight**: High gross margin → you can afford customer acquisition.

---

### Break-Even Analysis

**Fixed costs** (monthly):
- Your time: ₹0 (you're not paying yourself yet)
- Hosting: ₹500
- Domain/email: ₹200
- Tools (Clerk, Sentry): ₹0 (free tiers)
- **Total**: ~₹700/month

**Break-even customers**:
- Solo tier: 1 customer covers costs
- In reality: You need 5-10 active customers to cover time value

---

## Revenue Scenarios

### Scenario A: Conservative (Slow Growth)

```
Month 1:  0 customers, ₹0 MRR
Month 3:  3 customers, ₹3,000 MRR (3 Solo)
Month 6:  8 customers, ₹12,000 MRR (5 Solo, 3 Small)
Month 12: 20 customers, ₹40,000 MRR (mix)
```

**At month 12**: ₹40,000/month = ₹4.8L/year. Not full-time income, but good side income.

---

### Scenario B: Moderate (Healthy Growth)

```
Month 1:  0 customers, ₹0 MRR
Month 3:  5 customers, ₹8,000 MRR
Month 6:  15 customers, ₹35,000 MRR
Month 12: 40 customers, ₹120,000 MRR
```

**At month 12**: ₹1.2L/month = ₹14.4L/year. Comfortable full-time income in India.

---

### Scenario C: Optimistic (Strong PMF)

```
Month 1:  0 customers, ₹0 MRR
Month 3:  10 customers, ₹20,000 MRR
Month 6:  30 customers, ₹90,000 MRR
Month 12: 100 customers, ₹350,000 MRR
```

**At month 12**: ₹3.5L/month = ₹42L/year. Serious business.

---

## Customer Acquisition Cost (CAC)

### Organic Channels (Low CAC)

| Channel | Estimated CAC | Why |
|----------|---------------|-----|
| Facebook groups | ₹0 (time only) | Your time = money, but no direct spend |
| Referrals | ₹0 | Best source |
| SEO/content | ₹500-2,000 | Amortized over many customers |
| Host agency partnerships | ₹500 | Revenue split, but warm leads |

### Paid Channels (Higher CAC)

| Channel | Estimated CAC | Comment |
|----------|---------------|---------|
| Facebook ads | ₹1,000-3,000 | Test after product-market fit |
| Google ads | ₹2,000-5,000 | Expensive for B2B |
| LinkedIn ads | ₹3,000-7,000 | High quality but expensive |

**Rule**: Don't spend on ads until LTV > 3× CAC.

---

## Customer Lifetime Value (LTV)

### Formula

```
LTV = (ARPU × Gross Margin) / Churn Rate

ARPU = Average Revenue Per User
```

### Example Calculation

If:
- ARPU = ₹2,000/month
- Gross margin = 90%
- Churn = 10%/month (high)

```
LTV = (2,000 × 0.9) / 0.1 = ₹18,000
```

If:
- ARPU = ₹2,000/month
- Gross margin = 90%
- Churn = 5%/month (healthy)

```
LTV = (2,000 × 0.9) / 0.05 = ₹36,000
```

**Key insight**: Reducing churn dramatically increases LTV.

---

## LTV:CAC Ratio

| Ratio | Interpretation |
|-------|----------------|
| < 1× | You're losing money |
| 1-2× | Barely sustainable |
| 2-3× | Healthy |
| > 3× | Excellent |

**Target**: LTV:CAC > 3× before scaling acquisition.

---

## Runway Calculations

### Your Situation

**Monthly burn** (expenses):
- Hosting/tools: ₹700
- Personal expenses: ₹30,000 (example)
- **Total**: ₹30,700/month

**Savings runway**:
- If you have ₹3L savings: ~10 months runway
- If you have ₹6L savings: ~20 months runway

**Revenue needed to break even personally**:
- At ₹999/month: Need ~31 customers
- At ₹3,999/month: Need ~8 customers

**Your "freedom number"**: 8-10 Medium-tier customers = full-time income.

---

## Profitability Timeline

### Conservative Path

```
Month 1-3:  Building, no revenue
Month 4-6:  First paying customers, negative cash flow
Month 7-12: Growing, approaching break-even
Month 13+:  Profitable
```

### Key Milestones

| Milestone | Metric | Meaning |
|-----------|--------|---------|
| **First dollar** | First paying customer | Validation |
| **Ramens profitable** | Covers hosting costs | Can keep going indefinitely |
| **Personal break-even** | Covers your expenses | Full-time option |
| **Hiring threshold** | ₹50K+ MRR | Can afford help |

---

## Pricing Sensitivity

### What if you're wrong about pricing?

**Too high** (e.g., no one buys at ₹999):
- Lower to ₹699 for early adopters
- Or: Offer 6 months for price of 12

**Too low** (e.g., selling too fast):
- Raise for new customers (grandfather early ones)
- Add higher tier with more features

**Pricing is not fixed** — iterate based on data.

---

## Cash Flow Management

### The Solo Builder Trap

> "Revenue looks great, but cash is tight."

**Why**: Invoices, annual vs monthly billing, API costs in advance.

**Best practices**:
- Charge upfront (annual or quarterly)
- Offer discount for annual: 12 months for 10
- Monitor API costs weekly (they can surprise you)

### Simple Cash Flow Forecast

```
Month | Starting Cash | Revenue | Expenses | Ending Cash
------|--------------|---------|-----------|-------------
  1   |    ₹100,000   |    ₹0   |  ₹30,000  |   ₹70,000
  2   |     ₹70,000   |  ₹5,000 |  ₹30,000  |   ₹45,000
  3   |     ₹45,000   | ₹15,000 |  ₹32,000  |   ₹28,000
  4   |     ₹28,000   | ₹30,000 |  ₹35,000  |   ₹23,000
  5   |     ₹23,000   | ₹50,000 |  ₹35,000  |   ₹38,000
  6   |     ₹38,000   | ₹70,000 |  ₹38,000  |   ₹70,000
```

**Danger zone**: Months 3-4 where cash is lowest.

**Solution**: Keep 6 months expenses in savings.

---

## Three-Year Projection (Rough)

```
Year 1: Build, validate, 20-30 customers, ₹2-4L revenue
Year 2: Scale, 50-100 customers, ₹8-15L revenue, maybe hire 1 person
Year 3: Growth, 200-300 customers, ₹25-40L revenue, small team
```

**These are scenarios, not targets.** Actual will differ.

---

## Key Metrics to Track Weekly

| Metric | Formula | Target |
|--------|---------|--------|
| **MRR** | Sum of subscription revenue | Growing |
| **ARR** | MRR × 12 | Growing |
| **ARPU** | MRR / customers | ₹1,500+ |
| **Churn %** | Lost customers / total | < 10% |
| **CAC** | Marketing spend / new customers | < ₹2,000 |
| **LTV** | ARPU × customer lifetime | > ₹15,000 |
| **LTV:CAC** | LTV / CAC | > 3× |

---

## The "Freedom Number" Calculator

Your personal run rate = ₹X/month (your expenses)

```
Freedom customers = X / Average revenue per customer
```

Example:
- Your expenses: ₹40,000/month
- Average revenue: ₹2,000/customer
- Freedom customers: 40,000 / 2,000 = 20 customers

**With 20 customers at ₹2,000 each, you're free.**

---

## Summary

**Unit economics**: High margin (90%+) → viable business

**Break-even**: 5-10 customers covers costs, 20-30 = full-time income

**CAC target**: < ₹2,000 (organic channels)

**LTV target**: > ₹15,000 (low churn is key)

**Freedom number**: ~20 customers at mid-tier pricing

**Philosophy**: Profitability > growth. You don't need massive scale to make this work.

---

## Next Steps

- [ ] Build simple spreadsheet with these formulas
- [ ] Calculate your personal freedom number
- [ ] Set up MRR/churn tracking
- [ ] Review monthly, adjust if needed
