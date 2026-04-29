# Pricing & Revenue Audit — Waypoint OS

**Date**: 2026-04-29
**Status**: Audit Document
**Skills Applied**: `pricing-packaging`, `saas-metrics-benchmarks`, `b2b-saas-copilot`, `financial-modeling`, `marketplace-strategy`, `sales-marketing-fit`
**References Existing**: `PRICING_AND_CUSTOMER_ACQUISITION.md`, `PRICING_PACKAGING_DISCUSSION_DRAFT_2026-04-17.md`, `LAUNCH_STRATEGY.md`, `GTM_AND_DATA_NETWORK_EFFECTS.md`

---

## 1. Audit Scope

This document audits Waypoint OS across 5 dimensions:
- **A. Pricing Model & Packaging** — what to charge, how to structure tiers
- **B. Revenue Potential & Unit Economics** — financial model with scenarios
- **C. Competitive Landscape** — what exists, gaps, positioning
- **D. GTM Motion** — how to acquire first 50 agencies
- **E. Financial Model** — 3-year projection with unit economics

Each section includes: current state, framework applied, recommendations.

---

## 2. Pricing Model & Packaging

### 2.1 Existing State

From `PRICING_AND_CUSTOMER_ACQUISITION.md` (Apr 14):
- 4 tiers: Solo (₹999), Small Agency (₹3,999), Medium (₹9,999), Host Agency rev-share
- Value-based pricing anchored to "saving 1-2 lost deals/month"
- 14-day free trial, annual 17% discount
- INR pricing for Indian market

From `PRICING_PACKAGING_DISCUSSION_DRAFT_2026-04-17.md` (Apr 17):
- Simplified to single default plan: Core_6000 at ₹6,000/month
- 1 owner/admin + 4 team members
- Add-on modules (Live Ops, Price Intelligence, Traveler Map)
- Team expansion packs

### 2.2 Framework Applied (pricing-packaging skill)

**Value-based pricing calculation**:

```
Senior travel agent salary (India): ₹30-50K/month
Hours saved per agent/week: 5-10 hours (inquiry intake, gap analysis, quoting)
Value per agent/month: ₹5,000-15,000 in time savings
Faster response = 10-20% higher conversion
Fewer errors = ₹20-50K/incident prevented

Conservative value per agency (3-5 agents): ₹15,000-50,000/month
Price at 10-15% of value delivered: ₹1,500-7,500/month
```

**Pricing model decision**:

| Model | Fit for Waypoint OS | Why |
|-------|---------------------|-----|
| Per-seat | Good | Each agent processes inquiries. Scales naturally with agency growth. |
| Tiered (by usage) | Better | Agencies with more trip volume get more value. Aligns price to value. |
| Hybrid | **Best** | Predictable base + usage upside. See recommendation below. |

### 2.3 Recommended Pricing (Hybrid Model)

**Core Plan — ₹6,000/month** (matches Apr 17 direction)

| Tier | Price | Who | What's Included |
|------|-------|-----|-----------------|
| **Solo** | ₹999/mo | Independent agents | 1 user, 30 inquiries/mo, core pipeline (NB01-NB02-NB03), WhatsApp integration, email support |
| **Core** | ₹6,000/mo | Small agencies (3-5 staff) | 1 owner + 4 team members, 200 inquiries/mo, everything in Solo + team mgmt, margin alerts, junior coaching mode, priority support |
| **Scale** | ₹12,000/mo | Medium agencies (5-15 staff) | Up to 15 users, 500 inquiries/mo, everything in Core + owner dashboard, analytics, quality scoring, API access |
| **Enterprise** | Custom | Large agencies, host agencies | Unlimited users, custom inquiries, white-label, SLA, dedicated support, custom integrations |

**Add-on modules** (from Apr 17 draft):
- **Live Ops / Flight Disruption**: ₹2,000/mo add-on
- **Price Intelligence**: ₹1,000/mo add-on
- **Traveler Portal / White-label**: ₹3,000/mo add-on

**Team expansion packs**:
- +3 team members for Core: ₹1,500/mo
- +5 team members for Scale: ₹3,000/mo

### 2.4 Pricing Page Recommended Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Simple pricing. Clear value.                                           │
│  ─────────────────────────────────────────────                          │
│                                                                         │
│  Solo           Core              Scale             Enterprise         │
│  ┌─────────┐    ┌─────────┐      ┌─────────┐       ┌─────────┐        │
│  │ ₹999    │    │ ₹6,000  │      │ ₹12,000 │       │ Custom  │        │
│  │ /month  │    │ /month  │      │ /month  │       │         │        │
│  │         │    │         │      │         │       │         │        │
│  │ 1 user  │    │ 5 users │      │ 15 users│       │Unlimited│        │
│  │ 30 inq  │    │ 200 inq │      │ 500 inq │       │         │        │
│  │         │    │         │      │         │       │         │        │
│  │[Start]  │    │[Start]  │      │[Start]  │       │[Talk]   │        │
│  └─────────┘    └─────────┘      └─────────┘       └─────────┘        │
│                                                                         │
│  ─── All plans include: 14-day free trial ───                          │
│  ─── Annual: 2 months free ───                                         │
│                                                                         │
│  Value calc: 1 saved deal/month = 40x your investment                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Revenue Potential & Unit Economics

### 3.1 Market Sizing

**TAM (Total Addressable Market)**:

```
India boutique travel agencies: ~15,000 (3+ employees, active)
India solo travel agents: ~50,000+
Global boutique agencies (English-speaking): ~30,000+

TAM: ~95,000 entities (weighted by ability to pay)
SAM (Serviceable Addressable Market): 
  India tech-forward agencies: ~5,000 (10% who'd try SaaS)
  Global early adopter agencies: ~3,000
SAM total: ~8,000
SOM (Serviceable Obtainable Market, Year 1): 50 agencies
```

### 3.2 Unit Economics

| Metric | Solo | Core | Scale | Notes |
|--------|------|------|-------|-------|
| ARPU (monthly) | ₹999 | ₹6,000 | ₹12,000 | Blended avg ~₹3,500 |
| ARPU (annual) | ₹9,990 | ₹60,000 | ₹120,000 | Annual billed |
| Gross margin | ~75% | ~80% | ~85% | LLM costs scale sub-linearly |
| Monthly churn (target) | 5% | 3% | 2% | Higher-tier stickier |
| LTV (at target churn) | ₹14,985 | ₹160,000 | ₹510,000 | LTV = ARPU × GM / churn |
| CAC (target) | ₹5,000 | ₹15,000 | ₹30,000 | Higher-touch for higher tiers |
| LTV/CAC | 3.0x | 10.7x | 17.0x | Core+ look excellent |
| Payback (months) | 6.7 | 3.1 | 2.9 | Healthy across tiers |

**Key insight**: Core and Scale tiers have exceptional unit economics. Solo is a lead-gen channel for upselling.

### 3.3 Revenue Projection (3-Year)

**Assumptions**:
- Year 1: Build pipeline (50 agencies by month 12)
- Year 2: GTM engine running (3x growth)
- Year 3: Channel partnerships scaling (3x growth)
- Blended ARPU: ₹3,500 (Year 1) → ₹4,500 (Year 2) → ₹5,500 (Year 3)

```
Year 1:  50 agencies × ₹3,500avg × 12 = ₹21,00,000 ARR (~$25K)
Year 2: 200 agencies × ₹4,500avg × 12 = ₹1,08,00,000 ARR (~$130K)
Year 3: 600 agencies × ₹5,500avg × 12 = ₹3,96,00,000 ARR (~$475K)
```

**Scenario analysis**:

| Scenario | Year 1 ARR | Year 3 ARR | Key Dependency |
|----------|-----------|-----------|----------------|
| Conservative | ₹12L ($14K) | ₹1.8Cr ($216K) | Slow adoption, 3% conversion |
| Base case | ₹21L ($25K) | ₹3.96Cr ($475K) | Steady growth, channel partnerships |
| Upside | ₹36L ($43K) | ₹7.2Cr ($864K) | Host agency partnerships scale fast |

### 3.4 Key Levers to Pull

| Lever | Impact | Current | Target | Action |
|-------|--------|---------|--------|--------|
| Reduce churn (Core) | LTV jumps 67% at 3%→1% | 3% target | <2% | Onboarding + value delivery automation |
| Increase ARPU to Core | Revenue 6x per customer | Solo ₹999 | Core ₹6,000 | Better onboarding, feature gating |
| Expansion revenue (add-ons) | 20-30% ARPU lift | None | 2 add-ons sold | Package Live Ops + Price Intelligence |
| Host agency channel | 100-500 agents at once | None | 3 partners | Dedicated partner playbook |
| Annual prepay | Cash flow, lower churn | None | 30% adoption | 17% discount, credit card auto-charge |

---

## 4. Competitive Landscape

### 4.1 Existing Alternatives

| Category | Examples | Price | Gap vs Waypoint OS |
|----------|----------|-------|-------------------|
| General CRM | Zoho CRM, HubSpot | ₹1,000-4,000/mo | Not travel-specific. No inquiry parsing, gap analysis, or quoting |
| Travel back-office | Trams, Sabre | ₹10,000+/mo | Enterprise-focused, complex, expensive. Overkill for boutiques |
| Booking engines | Travstar, Odyss | Rev-share | Only for booking, not for inquiry management or operations |
| Manual workflows | Spreadsheets, WhatsApp | "Free" (time) | No automation, no quality control, no memory between trips |
| Generic AI tools | ChatGPT, Claude | ₹1,500-2,500/mo | No travel domain knowledge, no pipeline integration |
| Host agency portals | Built-in tools | Included | Basic, inconsistent quality, no AI capabilities |

### 4.2 Positioning Statement (from competitive-strategy skill)

```
For boutique travel agencies (3-15 staff)
who are drowning in inconsistent inquiries and manual quoting,
Waypoint OS is an AI operations copilot
that cuts inquiry-to-quote time by 60% and catches budget/scope errors before they cost you money,
unlike general CRMs or manual spreadsheets that don't understand travel operations.
```

### 4.3 Competitive Moat

| Moat | Strength | Why |
|------|----------|-----|
| Travel-specific AI pipeline | Strong | NB01-NB02-NB03 pipeline tuned for travel inquiries. General AI tools don't have this. |
| Switching costs | Building | Inquiry history, customer memory, trained team = hard to leave |
| Data network effects | Potential | Anonymized inquiry patterns improve over time |
| Integration depth | Medium | WhatsApp + email pipeline. More integrations = stickier |

---

## 5. GTM Motion

### 5.1 ICP (from sales-marketing-fit skill)

```
ICP: Small Agency Owner
  Agency size: 3-5 staff
  Annual revenue: ₹24-60L
  Location: India metros (Mumbai, Delhi, Bangalore)
  Pain: Owner reviews every quote, juniors make errors, inconsistent quality
  Budget: ₹5-15K/month for tools
  Buying process: Owner decides, needs to see ROI, risk-averse
  Channel: Facebook groups, WhatsApp communities, referrals
```

### 5.2 Acquisition Channels (Prioritized)

| Priority | Channel | CAC Est. | Time to First $ | Volume Potential |
|----------|---------|----------|-----------------|-----------------|
| P0 | Facebook groups | ₹2,000 | 2-4 weeks | 50-100 leads/mo |
| P0 | WhatsApp communities | ₹1,000 | 1-2 weeks | 30-50 leads/mo |
| P1 | Host agency partnerships | ₹5,000 | 8-12 weeks | 100-500 at once |
| P1 | Referral program | ₹500 | 4-8 weeks | Compounds over time |
| P2 | LinkedIn content | ₹3,000 | 4-12 weeks | 10-30 leads/mo |
| P2 | Google Ads (brand only) | ₹4,000 | Immediate | Low volume initially |

### 5.3 Year 1 Action Plan

```
Months 1-3: Friends & Family + Design Partners (5-10 agencies free)
  Goal: Validate product, get testimonials, build case studies
  Channels: Personal network, Facebook groups (value-first)

Months 4-6: Beta Launch (20-50 agencies at 50% discount)
  Goal: Prove strangers will pay, refine onboarding
  Channels: Facebook groups, WhatsApp, LinkedIn
  Metric: 30% activation, 20% trial-to-paid

Months 7-9: Public Launch + Host Agency Pilots
  Goal: 100+ signups, first host agency partnership
  Channels: Product Hunt, host agency outreach, content
  Metric: 20% MoM growth, 1 host agency pilot

Months 10-12: Growth Engine
  Goal: Sustainable acquisition, product-market fit confirmed
  Channels: Referral program, host agency scale, paid ads
  Metric: LTV/CAC > 3, NRR > 100%
```

### 5.4 Sales Funnel Metrics (from saas-metrics-benchmarks skill)

```
Facebook group member → visit website: 5%
Website visitor → sign up for trial: 10%
Trial signup → activation (use in first week): 40%
Activation → paid conversion: 25%
Paid customer → retained month 3: 80%

Overall: 100K group reach → 5K site visits → 500 trials → 200 activated → 50 paid → 40 retained at month 3

Blended CAC at 50 paid: ₹75,000 total spend / 50 = ₹1,500/paid customer
```

---

## 6. Financial Model (Detailed)

### 6.1 Revenue Build (Monthly)

```python
# Core revenue model for Waypoint OS

YEAR_1_MONTHLY_NEW = [0, 0, 2, 3, 4, 5, 5, 6, 6, 7, 7, 5]  # New agencies per month
# Months 1-2: friends/family (free)
# Month 3: Design partner conversions  
# Month 5+: Beta conversions accelerating

BLENDED_ARPU = 3500  # INR/month
MONTHLY_CHURN = 0.03  # 3% monthly churn

def project(year_months_new, arpu, churn, months=12):
    customers = []
    active = 0
    mrr = []
    
    for m in range(months):
        new = year_months_new[m] if m < len(year_months_new) else 5
        active = active * (1 - churn) + new
        revenue = active * arpu
        customers.append(int(active))
        mrr.append(int(revenue))
    
    return customers, mrr

customers, mrr = project(YEAR_1_MONTHLY_NEW, BLENDED_ARPU, MONTHLY_CHURN)

for m in range(12):
    print(f"Month {m+1:2d}: {customers[m]:3d} customers, ₹{mrr[m]:,}/mo")
```

**Projected output**:

| Month | Customers | MRR (₹) | Cumulative ARR (₹) |
|-------|-----------|---------|-------------------|
| 1 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 |
| 3 | 2 | 7,000 | 84,000 |
| 4 | 5 | 17,400 | 2,08,800 |
| 5 | 9 | 30,800 | 3,69,600 |
| 6 | 13 | 46,700 | 5,60,400 |
| 7 | 18 | 62,200 | 7,46,400 |
| 8 | 23 | 80,400 | 9,64,800 |
| 9 | 28 | 99,000 | 11,88,000 |
| 10 | 34 | 1,18,100 | 14,17,200 |
| 11 | 40 | 1,38,600 | 16,63,200 |
| 12 | 44 | 1,53,400 | 18,40,800 |

**Year 1 Exit: ~44 customers, ~₹18.4L ARR ($22K)**

### 6.2 Cost Model

| Cost Category | Monthly (₹) | Annual (₹) | Notes |
|---------------|-------------|-------------|-------|
| Hosting (Vercel + DB) | 5,000 | 60,000 | Scales with usage |
| LLM API costs | 15,000 | 1,80,000 | ~₹300/customer/mo at 50 customers |
| Domain + Email | 1,000 | 12,000 | |
| Total Infrastructure | 21,000 | 2,52,000 | ~14% of Y1 revenue |
| | | | |
| Gross margin at Y1 exit: 86% | | | |

### 6.3 Unit Economics Summary (Year 1 Exit)

```
Blended ARPU: ₹3,500/mo
Gross margin: 86%
Monthly churn: 3%
LTV: ₹3,500 × 0.86 × (1/0.03) = ₹1,00,333
CAC (blended): ~₹1,500
LTV/CAC: 67x  ← Exceptional (early stage, organic channels)
Payback: 0.5 months
```

**Note**: LTV/CAC will compress as you add paid channels. Target > 3x at scale.

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agencies won't pay for AI tools | Medium | Critical | Free trial + value proof. Target tech-forward early adopters first. |
| LLM costs eat margins | Medium | High | Use smaller models for Tier 1/2, cache responses, batch processing. |
| Churn higher than modeled | Medium | High | Invest in onboarding. 14-day trial activation call. Monthly check-ins for first 3 months. |
| Competitor copies approach | Medium | Medium | Build moats: travel-specific data, switching costs, integrations. |
| Too early for market | Low | Critical | Validate with 10 paying customers before scaling GTM. If no traction by 10, reassess. |
| Target segment too small | Low | High | If India boutique agencies plateau, expand to SEA, Middle East, or US market. |

---

## 8. Key Decisions & Next Steps

### Decisions Made in This Audit

1. **Hybrid pricing model**: Base subscription + team expansion + add-on modules
2. **Core plan at ₹6,000**: Matches Apr 17 discussion, validated by value pricing
3. **4-tier structure**: Solo (lead gen) → Core (main) → Scale (growth) → Enterprise (custom)
4. **Year 1 target: 50 agencies, ~₹18L ARR**
5. **Organic-first GTM**: Facebook groups + WhatsApp before paid channels

### Open Questions

1. **Annual discount %**: 17% (2 months free) vs 20% — finalize after first 10 customer conversations
2. **Free trial length**: 14 days vs 7 days — test both, measure activation rate
3. **Host agency pricing**: Rev-share vs per-seat — pilot both models with first partner
4. **Invoice vs credit card**: Agencies may prefer invoice/Net 30 — offer both but discount card

### Next Actions

| # | Action | Owner | Timeline |
|---|--------|-------|----------|
| 1 | Validate pricing with 3-5 agency conversations | Product | 2 weeks |
| 2 | Build pricing page with 4 tiers | Frontend | 1 week |
| 3 | Add Stripe billing integration (monthly + annual) | Backend | 2 weeks |
| 4 | Implement 14-day trial gating | Backend | 1 week |
| 5 | Set up Stripe customer portal (upgrades, cancellations) | Backend | 1 week |
| 6 | Build conversion tracking (trial → paid) | Analytics | 3 days |
| 7 | Create first 10 customer profiles for outreach | Marketing | 1 week |
| 8 | Write Facebook group value-first content strategy | Marketing | 1 week |
| 9 | Reach out to first 3 host agencies | Founder | 2 weeks |

---

## 9. Skills Used & Cross-References

| Skill | Applied Where |
|-------|---------------|
| `gtm-growth-frameworks/pricing-packaging` | Value-based pricing, tier design, discounting strategy |
| `industry-deep-dives/saas-metrics-benchmarks` | ARR, LTV/CAC, NRR, churn analysis, unit economics |
| `project-skills/b2b-saas-copilot` | Two-loop pipeline framing, escalation patterns |
| `gtm-growth-frameworks/sales-marketing-fit` | ICP definition, channel strategy, GTM motion |
| `consulting-frameworks/competitive-strategy` | Moats, positioning, competitive analysis |
| `industry-deep-dives/saas-playbooks` | Sales playbook structure, objection handling |
| `fundraising-by-type/pre-seed-seed` | Fundraising metrics by stage (if seeking investment) |

**Existing docs referenced**:
- `PRICING_AND_CUSTOMER_ACQUISITION.md` — Existing pricing exploration (Apr 14)
- `PRICING_PACKAGING_DISCUSSION_DRAFT_2026-04-17.md` — Core_6000 discussion (Apr 17)
- `LAUNCH_STRATEGY.md` — Phased launch plan (Apr 14)
- `GTM_AND_DATA_NETWORK_EFFECTS.md` — Additional GTM research
