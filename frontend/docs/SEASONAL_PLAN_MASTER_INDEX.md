# Seasonal Campaign Planner — Master Index

> Canonical planning system for turning India-specific seasonality into profitable execution across pricing, campaigns, forecasting, and capacity.

## 0) Positioning

Seasonality is not a marketing sidebar for travel agencies—it is the primary operating system for demand management.

- **Business value:** improves booking capture, protects margin, reduces inventory risk, and stabilizes cash flow.
- **Operator value:** gives owners and campaign owners one canonical planning map for what to launch, when to launch, and how much risk to accept.
- **Exploration value:** adds a dedicated roadmap for season-shaping experiments (channel timing, offer stack, messaging vectors, and scenario planning).

## 1) Series Overview

The series defines a full seasonal planning product loop:

1. Calendar model (`SEASONAL_PLAN_01_CALENDAR.md`)
2. Strategy playbooks and campaign orchestration (`SEASONAL_PLAN_02_STRATEGY_PLAYBOOK.md`)
3. Contract-first campaign artifacts (`SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md`)
4. Integration runbook (`SEASONAL_PLAN_04_EXECUTION_AND_INTEGRATION.md`)

**Target audience:** marketing managers, revenue planners, owners, ops leads, and product owners.

**Success signal:** when every active seasonal campaign has:
- a linked data contract,
- budget and margin guardrails,
- channel assignment with rationale,
- owner + runbook + exit criteria,
- post-campaign evidence feed.

**Pre-launch constraint:** no backward compatibility shim is required; canonical structures can be clean and opinionated.

## 2) Documents

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [SEASONAL_PLAN_01_CALENDAR.md](./SEASONAL_PLAN_01_CALENDAR.md) | India travel season model, demand windows, booking pace, and destination-level planning baseline | ✅ Complete |
| 2 | [SEASONAL_PLAN_02_STRATEGY_PLAYBOOK.md](./SEASONAL_PLAN_02_STRATEGY_PLAYBOOK.md) | Campaign archetypes, pre/post season checklists, risk playbooks, and operating play sequences | ✅ Complete |
| 3 | [SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md](./SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md) | Canonical TypeScript contracts, campaign objects, margins, budget envelopes, and KPI definitions | ✅ Complete |
| 4 | [SEASONAL_PLAN_04_EXECUTION_AND_INTEGRATION.md](./SEASONAL_PLAN_04_EXECUTION_AND_INTEGRATION.md) | Integration protocol with pricing/revenue/campaign/ops systems and release sequencing | ✅ Complete |

## 3) Strategic Assumptions (Canonical, High-Level)

1. **Pre-plan before peak:**
   The majority of peak-season demand is won before the season starts; planning and creative must begin 6–14 weeks before booking windows.

2. **Shoulder-first growth:**
   Peak demand is profitable but fragile; value capture improves by activating off-peak and shoulder demand through curated campaigns.

3. **Monsoon is strategic, not emergency mode:**
   July/August demand exists if messaging is aligned to experiences with proven weather resilience and clear alternatives.

4. **No duplicate campaign rails:**
   Marketing execution should route through one canonical planner and downstream campaign engine(s); deprecated parallel rails are tracked as debt, not kept alive.

## 4) Cross-Reference Map

| Related Series | Connection |
|----------------|------------|
| Content Marketing (CONTENT_MKTG_*) | Seasonal narratives and campaign assets |
| Email Marketing (EMAIL_MKTG_*) | Sequence design and campaign delivery |
| WhatsApp Business (WHATSAPP_BIZ_*) | Primary high-intent distribution layer |
| Pricing Engine (PRICING_ENGINE_MASTER_INDEX.md) | Seasonality multipliers and margin guardrails |
| Revenue Architecture (REVENUE_ARCH_MASTER_INDEX.md) | Margin and demand mix tracking |
| Deals/Promotions (DEALS_PROMO_01_ENGINE.md) | Seasonal promotions and leverage controls |
| Marketing Automation (MARKETING_AUTOMATION_MASTER_INDEX.md) | Campaign state machine and scheduling |
| Forecasting & Finance (FIN_DASH_03_FORECASTING.md) | Cash-flow, lead-time, and scenario overlays |
| Destination Seasonal Intelligence (DESTINATION_02_SEASONAL_INTELLIGENCE.md) | Destination scoring and event/calendar signals |
| Owner Planning (OWNER_CMD_02_PLANNING.md) | Strategic review and growth decisions |

## 5) Delivery Status and Completion Gates

| Gate | Criteria | Current State |
|------|----------|---------------|
| G0 — Canonical seasonal model | Single seasonal calendar with season taxonomy and booking windows | Complete |
| G1 — Campaign pattern library | Templates for early-bird, last-minute, destination spotlight, monsoon capture | Complete |
| G2 — Contract-first controls | Shared campaign contract + KPI definitions + margin guardrails | Complete |
| G3 — Integration wiring | Explicit runbook + channel ownership + dependencies | Complete |
| G4 — Experiment map | Long-term exploration plan for continuous optimization | Complete |

## 6) Long-Term Exploration Additions

- Explore and harden dynamic campaign scheduling optimizer using confidence-weighted seasonal models.
- Explore and harden cross-channel budget rebalancing with conversion-per-cash-spend controls.
- Explore and harden micro-seasonality windows for top destinations with high monthly variance.
- Explore and harden weather-sensitive fallback playbooks for disruption windows.

## 7) Created

**Created:** 2026-04-30
**Last Updated:** 2026-06-01
