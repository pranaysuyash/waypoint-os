# Financial Model Versions — Discussion Log

This document tracks the evolution of the financial model, what changed, and why.

## Version History

| Version | File | ARPU | Key Assumptions | Created | 
|---------|------|------|-----------------|---------|
| v1 | `tools/financial_model_v1.py` | ₹3,500 | Original baseline. 3% churn, ₹21K fixed, ₹500 var, 83 USD. Not actual pricing. | Apr 29 |
| v2 | `tools/financial_model_v2.py` | ₹3,099 | Corrected: 70% Solo/20% Core/10% mix, 4.3% churn (weighted), ₹30K fixed + ₹1L one-time, 93 USD. Still used older LLM cost estimates. | Apr 29 |
| v3 | `tools/financial_model_v3.py` | Interactive scenarios | Rewritten as what-if explorer. $20 base plan (₹1,860), lower LLM costs (₹150/cust), ₹15K fixed, 4 scenario comparison, formula explanations. | Apr 30 |
| v6 | `tools/financial_model_v6.py` | PLG + retention + churn feedback | Added churn-reduction feedback loop: ₹200/cust/mo retention spend → 40% lower churn. LTV jumps 67%. | Apr 30 |

**Current recommended**: `tools/financial_model_v6.py` — most complete version.

## v6 Change: Retention → Churn Feedback Loop

Added `RETENTION_CHURN_REDUCTION = 0.4` — the ₹200/cust/mo retention investment reduces churn by 40%.

This models reality: onboarding calls, check-ins, and support prevent customers from leaving. Without this feedback, v5 showed retention as pure cost. v6 shows it as a profit multiplier.

**Impact**: LTV jumps 67%, Y3 ARR jumps 32%, 36mo profit up 18%. The ₹200/cust/mo pays for itself ~5x over.

## v5 Change: Customer Retention Cost

Added ₹200/customer/month for customer success activities (onboarding calls, check-ins, training, churn prevention).

Impact on v4 numbers:
- Variable cost went from ₹400 to ₹600/cust/mo
- 36mo costs increased by ₹24.9L ($2,680)
- 36mo profit decreased by ₹24.9L (5% reduction)
- LTV dropped proportionally (Scenario A: ₹29,200 → ₹25,200)

**Tradeoff not yet modeled**: The ₹200/cust/mo retention investment SHOULD reduce churn. Currently churn rates stay the same. In reality, if this investment drops churn from 5% to 3%, it pays for itself many times over. Future model versions could add a churn-reduction factor tied to retention spend.

## PLG Discussion (Apr 30)

Applied the `plg-patterns` skill to Waypoint OS:

### Key PLG Patterns That Fit

1. **Team-based gating** — Your base plan (1 owner + 3 free seats) naturally triggers upgrades when agencies need more seats.
2. **Free tier with limits** — Let agencies process 5-10 inquiries free before hitting a paywall.
3. **Activation metric**: First inquiry processed end-to-end. Target 40%+ of trials within 48 hrs.
4. **Expansion revenue triggers**: Seat packs, add-ons (flight tracking, price intel), usage thresholds.

### Viral Loop Potential

- Most realistic: Host agency partnerships. One host = 50-500 agents.
- Collaborative: Trip sharing between agencies ("partner agency can view this").
- Referral: Offer 1 month free for both sides.

### What v4 Shows

| Growth Mode | Y3 ARR (at ₹4,500 ARPU) |
|-------------|------------------------|
| Founder-Led (no PLG) | ₹54.5L ($58,645) |
| Organic PLG | ₹41L ($44,129) — slower Y1, compounds later |
| Host Agency Powered | ₹1.26Cr ($135,870) |
| Full PLG + Viral + Partners | ₹2.55Cr ($274,645) |

The Founder-Led and Organic PLG look close in Y1, but PLG compounds in Y2-Y3.
Host agency partnerships are the highest-leverage growth channel.

### What v4 Also Shows

| Strategy | Y3 ARR |
|----------|--------|
| Full PLG + $20 base only | ₹69.6L ($74,880) |
| Full PLG + $20 base + seat packs | ₹1.37Cr ($147,097) |
| Full PLG + base + seats + add-ons | ₹2.55Cr ($274,645) |
| Full PLG + full stack | ₹4.13Cr ($443,677) |

Upgrading customers from base to seats + add-ons multiplies ARR by 5x.

## Key Discussion Points

### LLM Costs (Apr 30)

**Old assumption**: ₹300/customer/month for LLM API.
**Reality**: New models cost $4-14/million tokens. At ~2,000-3,000 tokens per inquiry processing, and ~50-100 inquiries per customer per month:
- Cost per inquiry: ~$0.025 (₹2.30)
- Cost per customer per month: ~₹115-230
- Current estimate: **₹150/customer/month** (conservative)

### Pricing Structure (User's actual plan)

| Component | Price | Notes |
|-----------|-------|-------|
| Base plan | ~$20/mo (₹1,860) | 1 owner + 3 free seats |
| Seat packs | Extra | +5 seats at additional cost |
| Add-on modules | Extra | Flight tracking, price intelligence, etc. (later) |

Not the ₹999/₹6,000/₹12,000 tiers from earlier docs. Those were draft thinking that has since evolved.

### CAC (Customer Acquisition Cost)

CAC = Total spend on sales & marketing ÷ number of new customers.

Examples:
- Facebook group organic: ~₹500-1,500/customer
- WhatsApp communities: ~₹500-1,000/customer
- LinkedIn content: ~₹3,000-5,000/customer
- Referral: ~₹500-1,000/customer
- Host agency partnership: ~₹5,000-15,000/customer

LTV/CAC > 3x is healthy. v3 model estimates CAC based on churn rate (lower churn channels cost more).

### Breakeven

With ₹15K/mo fixed costs and ₹400/customer variable:
- At ₹1,860 ARPU: ~10 customers to breakeven
- At ₹3,000 ARPU: ~5-6 customers
- At ₹4,500 ARPU: ~3-4 customers
- At ₹6,000 ARPU: ~2-3 customers

One-time cost: ~₹1,00,000 ($1,075) for deployment, legal, branding.

## Revenue-First Growth Applied (Apr 30)

Loaded `bootstrapping-indie/revenue-first-growth` and applied to Waypoint OS.

### Key Takeaways

1. **Customer-funded development** — Don't build features on spec. Find 3 agencies who want flight tracking, have them commit to ₹2,000/mo add-on, build it with guaranteed revenue. Zero risk.

2. **Annual billing** — 20% discount for annual prepay. 50 annual customers = ₹8.9L upfront cash. Target 30%+ adoption.

3. **Seasonality matters** — Travel agencies are busiest Jan-Feb (peak booking) and Jul-Aug (trip execution). Sell in Jan-Feb. Support in Jul-Aug. Build in Sep-Oct.

4. **Cash reserves** — Keep 6 months of fixed costs (₹90K) in the bank before spending on growth. Profit from month 3 doesn't mean spend every rupee.

5. **Anti-patterns** — Don't grow into unprofitability. Don't underprice add-ons. Don't burn out trying to grow fast.

Full document: `Docs/REVENUE_FIRST_GROWTH_APPLICATION.md`

## Fundraising Assessment (Apr 30)

Loaded `fundraising-by-type/pre-seed-seed` and applied to Waypoint OS.

**Key decision**: Bootstrap first. Business works without funding (breakeven month 3). Raise only for acceleration (hiring, host agency partnerships, paid ads).

**If raising: pre-seed round**
- Amount: $50-250K via SAFE at $3-5M cap
- 2-5% dilution
- Key gap: solo founder (investors prefer teams)

**Pre-fundraising checklist**:
- [ ] 10-20 paying customers
- [ ] 40%+ activation rate
- [ ] 1 host agency letter of intent
- [ ] Confirmed unit economics (LTV/CAC > 3x)
- [ ] Monthly investor updates started (3 months before)

Full document: `Docs/FUNDRAISING_ASSESSMENT.md`

## Side Project Context (Apr 30)

Not planning to raise. Running Waypoint OS as a side project.

**Key changes to the model**:
- Lower fixed costs: ₹5-8K/mo (not ₹15K) — free tiers, minimal tools
- Lower one-time: ₹50K (not ₹1L)
- Slower growth: 2-4 customers/mo side project pace (not 5-10)
- No hiring. Automate everything. Stay solo.

**Year 2 target**: 40-60 customers, ₹74K-1.1L/mo MRR — meaningful side income.
**Breakeven**: 5-7 customers. ₹50K investment total.
**Go full-time signal**: ₹1.5L+/mo MRR + growing 15%+/mo without active outreach.

Full document: `Docs/SIDE_PROJECT_PLAYBOOK.md`

## v7: Side Project Mode (Apr 30)

Created `tools/financial_model_v7.py` with side-project specific numbers.

**Key changes from v6**:
- Fixed costs: ₹6K/mo (was ₹15K)
- One-time: ₹50K (was ₹1L)
- New growth modes: casual/steady/focused/focused+host
- Higher churn (less time for support)
- Growth modes named after effort levels

**Reality check**: Casual and steady effort (< 8 hrs/wk) don't overcome churn. Focused (10-15 hrs/wk) works: 37 customers, ₹17.8L ARR, ₹22.8L profit by year 3.

Full doc: `Docs/SIDE_PROJECT_PLAYBOOK.md`

## How to Use

Run `python3 tools/financial_model_v7.py` for side project mode, or `v6.py` for the full PLG version.
Edit the SCENARIOS, PRICING_SCENARIOS, and GROWTH_MODES at the top of those files to test different assumptions.

## Skills Applied — Full List

| # | Skill | Document |
|---|-------|----------|
| 1 | `pricing-packaging` | `PRICING_REVENUE_AUDIT_2026-04-29.md` |
| 2 | `plg-patterns` | Built into financial model v4-v7 |
| 3 | `saas-metrics-benchmarks` | Financial model (unit economics) |
| 4 | `saas-business-model` | Retention investment (v5-v7) |
| 5 | `revenue-first-growth` | `REVENUE_FIRST_GROWTH_APPLICATION.md` |
| 6 | `pre-seed-seed` | `FUNDRAISING_ASSESSMENT.md` (archived — not raising) |
| 7 | `sales-marketing-fit` | `SALES_MARKETING_FIT.md` |
| 8 | `saas-playbooks` | `SAAS_PLAYBOOK.md` |
| 9 | Content/SEO Strategy | `CONTENT_SEO_STRATEGY.md` |

## Content & SEO Strategy (Apr 30)

Loaded the content/SEO approach — not from a single skill but synthesized across `sales-marketing-fit`, `landing-page-copy`, and existing project knowledge.

**Key insight**: The 14 Docs already written ARE your content. Each one can become 2-3 blog posts.

**Landing page**: Missing a blog/content section. Proposed to add a `/blog` route + "Latest from the blog" section on homepage between trust section and CTA band. No CMS needed — just a data file for a side project.

**Waitlist strategy**: Three-phase launch (content/waitlist → free tool wedge → full product). Current CTA "Book a demo" is wrong for a $20 product — should be "Start free trial" or "Join the waitlist" depending on phase.

**SEO**: Target long-tail keywords with low competition. Publish 2 cornerstone posts in week 1, then 1-2 posts/month.

**Affiliate**: Premature. Launch manually at 50 customers, automated at 200+.

Full document: `Docs/CONTENT_SEO_STRATEGY.md`
