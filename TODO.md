# Waypoint OS — Actionable Todos

**Generated**: 2026-04-30
**Priority**: P0 = customer conversations first (per Ayse advisory call)

---

## P0: Must Do (Next 14 Days) — Customer Discovery

- [ ] **Send 50 LinkedIn connection requests to travel agency owners** (7-10 days, not 10-20)
- [ ] Lead list tracked in Google Sheet: https://docs.google.com/spreadsheets/d/1voQUxncEqXPF36wrr7fdDkKj5YETh2Cv0X-mKJZZs-0/edit?gid=0
- [ ] Target: small outbound leisure agencies in India, custom itineraries, WhatsApp-heavy
- [ ] DM the ones who accept — "15-min chat? No pitch, learning the workflow."
- [ ] Run 7-10 calls minimum
- [ ] Track TWO tracks per call: inquiry intake pain + follow-up/lead leakage pain
- [ ] Add commercial questions: inquiry volume, booking value, response time sensitivity
- [ ] Capture exact words they use (this becomes your positioning)
- [ ] After 10 calls: decide based on clear pattern (6+ same pain) or pause

## P1: After Customer Discovery

### Product / Launch

- [ ] Decide: waitlist vs live signups for initial launch
- [ ] Update landing page CTA from "Book a demo" to appropriate phase
- [ ] Set up Stripe billing integration (monthly + annual)
- [ ] Implement 14-day trial gating
- [ ] Build pricing page with current plan structure

### Content / SEO

- [ ] Create Cloudflare R2 bucket `waypoint-blog` and configure rclone
- [ ] Create `tools/build-blog.py` — converts markdown → JSON → uploads to R2
- [ ] Create blog lib + blog listing page + individual post page in frontend
- [ ] Convert first 3 Tier 1 docs to blog posts (pick from: pricing research, competitive analysis, market overview)
- [ ] Add blog section to homepage between trust section and CTA band
- [ ] Set up meta tags + Open Graph on all pages
- [ ] Submit sitemap to Google Search Console

### Sales / Outreach

- [ ] Create simple CRM spreadsheet (name, agency, stage, next action, dates)
- [ ] Identify first 3 Facebook travel agent groups to join
- [ ] Join groups, spend 2 weeks answering questions (no pitching yet)
- [ ] Post first value-first content in FB group
- [ ] Start LinkedIn: update profile with Waypoint OS context
- [ ] LinkedIn: send 10 connection requests/week to travel agency owners
- [ ] LinkedIn: post 1 insight post/week (industry research-based)
- [ ] Write first 3 LinkedIn DM templates (connection note, welcome DM, follow-up)

---

## P1: Important (Next 60 Days)

### Product

- [ ] Build 1 add-on module (flight tracking recommended — most requested)
- [ ] Annual billing option with 20% discount
- [ ] Customer onboarding flow (guided setup → first inquiry processed)

### Content

- [ ] Write and publish 5 more blog posts (convert Tier 1 docs)
- [ ] Weekly posting cadence established
- [ ] Create free itinerary checker as wedge (already exists, promote it more)

### Sales

- [ ] Get first 5 paying customers
- [ ] Monthly check-in email sequence for active users
- [ ] Start referral conversation with first happy customer
- [ ] Qualify and reach out to first host agency

### Side Project Sustainability

- [ ] Set up 10-15 hrs/week schedule (see SIDE_PROJECT_PLAYBOOK.md)
- [ ] Keep 6 months of fixed costs (₹36K) in bank before spending on growth
- [ ] Automation: billing, reporting, email sequences

---

## P2: Future (60+ Days)

### Product

- [ ] Additional add-on modules (price intelligence, traveler portal)
- [ ] Usage-based seat pack pricing finalized
- [ ] API access for larger agencies

### Content

- [ ] Convert 50+ docs to blog posts
- [ ] Tag/category system on blog
- [ ] RSS feed for blog
- [ ] Monitor Google Search Console for keyword performance

### Growth

- [ ] Affiliate program (manual, after 50 customers)
- [ ] Host agency partnership program
- [ ] Paid acquisition (after 50 paying customers, LTV/CAC confirmed)
- [ ] Evaluate: keep side project, go full-time, or sell

---

## References

| Resource | What It Covers |
|----------|---------------|
| `Docs/SIDE_PROJECT_PLAYBOOK.md` | Side project schedule, milestones, go full-time signals |
| `Docs/CONTENT_ARCHITECTURE.md` | R2 JSON dump setup, build script, frontend pages |
| `Docs/CONTENT_SEO_STRATEGY.md` | Keyword targets, promotion channels, publishing cadence |
| `Docs/SALES_MARKETING_FIT.md` | FB group outreach, founder sales flow, ICP |
| `Docs/SAAS_PLAYBOOK.md` | Objection scripts, conversation flows, weekly cadence |
| `Docs/REVENUE_FIRST_GROWTH_APPLICATION.md` | Customer-funded dev, annual billing, cash reserves |
| `Docs/PRICING_REVENUE_AUDIT_2026-04-29.md` | Full pricing audit |
| `tools/financial_model_v7.py` | Side project financial model |

## Tools Created

| Tool | Purpose |
|------|---------|
| `tools/financial_model_v1.py` through `v7.py` | Financial models (v7 = current side project version) |

## Model Versions

| Version | File | Best For |
|---------|------|----------|
| v7 | `financial_model_v7.py` | **Current** — side project mode |
| v6 | `financial_model_v6.py` | Startup mode with PLG + retention feedback |
| v1-5 | `financial_model_v*.py` | Archived baselines |
