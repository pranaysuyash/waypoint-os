# Analytics Dashboard 03: Metrics Deep Dive

> Complete guide to KPI definitions, calculation logic, and business insights

---

## Document Overview

**Series:** Analytics Dashboard Deep Dive (Document 3 of 4)
**Focus:** Metrics — KPI definitions, calculation formulas, business insights
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Revenue Metrics](#revenue-metrics)
3. [Booking Metrics](#booking-metrics)
4. [Customer Metrics](#customer-metrics)
5. [Agent Performance Metrics](#agent-performance-metrics)
6. [Operational Metrics](#operational-metrics)
7. [Conversion Funnels](#conversion-funnels)
8. [Trend Analysis](#trend-analysis)
9. [Implementation Reference](#implementation-reference)

---

## Executive Summary

This document defines all key performance indicators (KPIs) tracked in the Analytics Dashboard. Each metric includes its definition, calculation formula, data source, business context, and insight interpretation.

### Metric Categories

| Category | Key Metrics | Primary Users |
|----------|-------------|---------------|
| **Revenue** | Gross Revenue, Net Revenue, Margin, Growth Rate | Owner, Admin |
| **Bookings** | Total, Confirmed, Cancelled, Average Value | All roles |
| **Customers** | New, Returning, Lifetime Value, Satisfaction | Owner, Admin |
| **Agent** | Productivity, Response Time, Completion Rate | Senior Agent, Admin |
| **Operational** | Response Time, Resolution Rate, Escalations | All roles |

---

## Revenue Metrics

### Gross Revenue

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GROSS REVENUE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Total value of all confirmed bookings before deductions                     │
│                                                                             │
│  FORMULA                                                                     │
│  Gross Revenue = SUM(booking.total_amount)                                   │
│                  WHERE booking.status = 'confirmed'                         │
│                  AND booking.created_at BETWEEN start_date AND end_date     │
│                                                                             │
│  DATA SOURCE                                                                 │
│  • Primary: bookings table                                                 │
│  • Analytics: mv_revenue_daily (ClickHouse)                                │
│                                                                             │
│  VISUALIZATION                                                               │
│  • Line chart: Trend over time                                              │
│  • Bar chart: Comparison by period (month/quarter)                          │
│  • Breakdown: By destination, by team, by agent                             │
│                                                                             │
│  INSIGHTS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Growth Trend                                                        │   │
│  │  • Positive growth → Business expanding                              │   │
│  │  • Flat/declining → Need investigation (seasonal? market changes?)    │   │
│  │                                                                      │   │
│  │  Seasonality                                                         │   │
│  │  • Peak: Oct-Mar (holiday season)                                    │   │
│  │  • Off-peak: Apr-Sep (focus on corporate/off-season promotions)      │   │
│  │                                                                      │   │
│  │  Benchmarks                                                          │   │
│  │  • Month-over-month growth: Target 10-15%                            │   │
│  │  • Year-over-year growth: Target 25-30%                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Net Revenue

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NET REVENUE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Gross revenue minus refunds, cancellations, and supplier commissions        │
│                                                                             │
│  FORMULA                                                                     │
│  Net Revenue = Gross Revenue                                                 │
│                - SUM(refund.amount)                                         │
│                - SUM(cancellation.penalty)                                  │
│                - SUM(supplier.commission)                                   │
│                                                                             │
│  DATA SOURCE                                                                 │
│  • Primary: bookings, refunds, cancellations tables                        │
│  • Analytics: mv_revenue_daily (ClickHouse)                                │
│                                                                             │
│  INSIGHTS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gap Analysis                                                        │   │
│  │  Gross vs Net gap indicates:                                         │   │
│  │  • High refunds → Quality issues                                     │   │
│  │  • High cancellations → Booking process issues                       │   │
│  │  • High commissions → Negotiate better rates                         │   │
│  │                                                                      │   │
│  │  Target Net/Gross Ratio: ≥90%                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Margin Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MARGIN METRICS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TOTAL MARGIN                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: SUM(booking.margin)                                        │   │
│  │                                                                      │   │
│  │  Insight: Actual profit earned from all bookings                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MARGIN PERCENTAGE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: (Total Margin / Gross Revenue) × 100                      │   │
│  │                                                                      │   │
│  │  Benchmark:                                                          │   │
│  │  • Domestic: 12-15%                                                  │   │
│  │  • International: 15-20%                                             │   │
│  │  • Corporate: 8-12%                                                  │   │
│  │                                                                      │   │
│  │  Action:                                                            │   │
│  │  • Below target → Review pricing, supplier costs                    │   │
│  │  • Above target → Opportunity to increase volume                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MARGIN BY DESTINATION                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Visual: Bar chart sorted by margin %                               │   │
│  │                                                                      │   │
│  │  Use: Identify high-margin destinations to prioritize               │   │
│  │                                                                      │   │
│  │  High margin destinations:                                           │   │
│  │  • Thailand, Malaysia, Singapore (18-22%)                            │   │
│  │  • Domestic tailor-made (15-18%)                                     │   │
│  │                                                                      │   │
│  │  Lower margin destinations:                                          │   │
│  │  • Dubai, Europe (10-12%, competitive)                               │   │
│  │  • Domestic packages (8-10%, price-sensitive)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Revenue Growth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REVENUE GROWTH                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MONTH-OVER-MONTH (MoM)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: ((Revenue_this_month - Revenue_last_month)                │   │
│  │            / Revenue_last_month) × 100                              │   │
│  │                                                                      │   │
│  │  Interpretation:                                                     │   │
│  │  • >15%: Excellent growth                                            │   │
│  │  • 5-15%: Healthy growth                                            │   │
│  │  • 0-5%: Stable                                                     │   │
│  │  • <0%: Declining (investigate)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  YEAR-OVER-YEAR (YoY)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: ((Revenue_this_year - Revenue_last_year)                 │   │
│  │            / Revenue_last_year) × 100                              │   │
│  │                                                                      │   │
│  │  Interpretation:                                                     │   │
│  │  • >30%: Outstanding                                                │   │
│  │  • 20-30%: Strong                                                   │   │
│  │  • 10-20%: Moderate                                                 │   │
│  │  • <10%: Below target                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  GROWTH RATE TREND                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Visual: Line chart showing growth rate over time                   │   │
│  │                                                                      │   │
│  │  Patterns to watch:                                                  │   │
│  │  • Accelerating growth → Scaling effectively                         │   │
│  │  • Decelerating growth → Market saturation or competition          │   │
│  │  • Volatile growth → Seasonal or inconsistent performance            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Booking Metrics

### Total Bookings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TOTAL BOOKINGS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Count of all bookings created in the period                                │
│                                                                             │
│  FORMULA                                                                     │
│  Total Bookings = COUNT(booking.id)                                          │
│                    WHERE booking.created_at BETWEEN start_date AND end_date │
│                                                                             │
│  BREAKDOWN BY STATUS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Status          │ Count   │ % of Total │ Trend                     │   │
│  │  ────────────────┼─────────┼────────────┼───────────────────        │   │
│  │  Confirmed       │ 124     │ 79.5%      │ ↑                         │   │
│  │  Pending         │ 22      │ 14.1%      │ →                         │   │
│  │  Cancelled       │ 8       │ 5.1%       │ ↓                         │   │
│  │  On Hold         │ 2       │ 1.3%       │ →                         │   │
│  │  TOTAL           │ 156     │ 100%       │ ↑ 8% vs last month         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CONVERSION RATE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Inquiry to Booking: (Bookings / Inquiries) × 100                   │   │
│  │  Target: 35-40%                                                      │   │
│  │                                                                      │   │
│  │  Quote to Booking: (Bookings / Quotes) × 100                        │   │
│  │  Target: 60-70%                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Average Booking Value (ABV)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AVERAGE BOOKING VALUE (ABV)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Average revenue per booking                                                 │
│                                                                             │
│  FORMULA                                                                     │
│  ABV = SUM(booking.total_amount) / COUNT(booking.id)                        │
│                                                                             │
│  SEGMENTED ABV                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Segment              │ ABV       │ vs Overall │ Trend                │   │
│  │  ─────────────────────┼───────────┼────────────┼────────────          │   │
│  │  International        │ ₹85,000   │ +32%       │ ↑                    │   │
│  │  Domestic             │ ₹42,000   │ -12%       │ →                    │   │
│  │  Corporate            │ ₹125,000  │ +78%       │ ↑                    │   │
│  │  Leisure (Individual) │ ₹35,000   │ -28%       │ ↓                    │   │
│  │  Leisure (Group)      │ ₹180,000  │ +120%      │ ↑                    │   │
│  │  OVERALL              │ ₹52,000   │ -          │ ↑ 5%                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INSIGHTS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Group bookings drive high ABV but lower volume                   │   │
│  │  • Focus on converting individual to group bookings                │   │
│  │  │  Corporate segment has high ABV + retention opportunity           │   │
│  │  • Rising ABV indicates up-selling success                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cancellation Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CANCELLATION ANALYSIS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CANCELLATION RATE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: (Cancelled Bookings / Total Bookings) × 100               │   │
│  │                                                                      │   │
│  │  Target: <5%                                                         │   │
│  │  Warning: 5-10%                                                      │   │
│  │  Critical: >10%                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CANCELLATION BY REASON                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Reason                 │ Count │ %      │ Revenue Impact           │   │
│  │  ───────────────────────┼───────┼───────┼─────────────────────      │   │
│  │  Customer cancelled     │ 5     │ 62.5%  │ ₹2,10,000                │   │
│  │  Payment not received   │ 2     │ 25.0%  │ ₹85,000                  │   │
│  │  Supplier unavailable   │ 1     │ 12.5%  │ ₹45,000                  │   │
│  │  TOTAL                  │ 8     │ 100%   │ ₹3,40,000                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CANCELLATION BY TIMING                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Time Before Departure  │ % of Cancellations │ Impact                 │   │
│  │  ───────────────────────┼────────────────────┼────────────            │   │
│  │  Within 24 hours        │ 15%                 │ High (refunds due)    │   │
│  │  1-7 days               │ 35%                 │ Medium                │   │
│  │  8-30 days              │ 30%                 │ Low                   │   │
│  │  30+ days               │ 20%                 │ Minimal               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACTIONS                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  High cancellation rate:                                            │   │
│  │  • Review quotation accuracy                                        │   │
│  │  • Improve payment collection process                               │   │
│  │  • Set clear cancellation policies                                   │   │
│  │  • Follow up on pending bookings                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Customer Metrics

### New vs Returning Customers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NEW VS RETURNING CUSTOMERS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITIONS                                                                 │
│  • New Customer: First booking in the system                                │
│  • Returning Customer: Has previous bookings                               │
│                                                                             │
│  DISTRIBUTION                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Customer Type    │ Count │ %      │ Revenue │ Avg Booking           │   │
│  │  ────────────────┼───────┼───────┼─────────┼────────────            │   │
│  │  New             │ 67    │ 75%   │ ₹28L    │ ₹42,000                │   │
│  │  Returning       │ 22    │ 25%   │ ₹35L    │ ₹1,59,000               │   │
│  │  TOTAL           │ 89    │ 100%  │ ₹63L    │ ₹71,000                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTOMER RETENTION RATE                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: (Returning Customers / Total Customers) × 100             │   │
│  │                                                                      │   │
│  │  Target: 30-40%                                                      │   │
│  │  Current: 25% → Opportunity to improve retention                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INSIGHTS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Returning customers spend 3.8x more per booking                   │   │
│  │  • Focus on retention programs for high-value customers             │   │
│  │  • Loyalty programs can increase retention rate                     │   │
│  │  • Email engagement correlates with repeat bookings                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Customer Lifetime Value (CLV)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOMER LIFETIME VALUE (CLV)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Total revenue expected from a customer over their relationship             │
│                                                                             │
│  FORMULA                                                                     │
│  CLV = Avg Annual Revenue per Customer × Customer Lifespan (years)          │
│                                                                             │
│  CLV SEGMENTS                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Segment           │ CLV      │ Count   │ % of Revenue │ Focus       │   │
│  │  ──────────────────┼──────────┼─────────┼──────────────┼─────────────│   │
│  │  High Value        │ >₹5L     │ 12      │ 38%          │ Retain      │   │
│  │  Medium Value      │ ₹2-5L    │ 34      │ 42%          │ Grow        │   │
│  │  Low Value         │ <₹2L     │ 43      │ 20%          │ Efficient   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CLV vs CAC (Customer Acquisition Cost)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Target CLV:CAC Ratio: 3:1                                          │   │
│  │  Current: 2.8:1 → Slightly below target                            │   │
│  │                                                                      │   │
│  │  Actions to improve:                                                │   │
│  │  • Increase retention (extends lifespan)                            │   │
│  │  • Up-sell/cross-sell (increases annual revenue)                   │   │
│  │  • Reduce acquisition cost (better marketing efficiency)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Customer Satisfaction (CSAT)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOMER SATISFACTION (CSAT)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA SOURCE                                                                 │
│  Post-trip feedback surveys (email, WhatsApp)                              │
│                                                                             │
│  CSAT SCORE                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: Average rating (1-5 scale)                                │   │
│  │                                                                      │   │
│  │  Target: 4.5+                                                       │   │
│  │  Current: 4.3                                                       │   │
│  │                                                                      │   │
│  │  Distribution:                                                       │   │
│  │  ⭐⭐⭐⭐⭐ (5): 58%                                                  │   │
│  │  ⭐⭐⭐⭐ (4): 28%                                                   │   │
│  │  ⭐⭐⭐ (3): 10%                                                     │   │
│  │  ⭐⭐ (2): 3%                                                       │   │
│  │  ⭐ (1): 1%                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CSAT BY DIMENSION                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Dimension       │ Score │ Trend │ Key Driver                      │   │
│  │  ───────────────┼───────┼───────┼────────────────────              │   │
│  │  Overall        │ 4.3   │ →     │ -                              │   │
│  │  Communication  │ 4.6   │ ↑     | WhatsApp responsiveness         │   │
│  │  Itinerary      │ 4.4   │ →     │ Hotel quality                  │   │
│  │  Value          │ 4.1   │ ↓     │ Perception of high cost         │   │
│  │  Support        │ 4.2   │ →     │ Trip modifications              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RESPONSE RATE                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Survey sent: 156                                                    │   │
│  │  Responses: 89 (57%)                                                 │   │
│  │  Target: 40%+                                                        │   │
│  │                                                                      │   │
│  │  Collection methods:                                                │   │
│  │  • WhatsApp: 65% response rate                                       │   │
│  │  • Email: 42% response rate                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Performance Metrics

### Agent Productivity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENT PRODUCTIVITY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BOOKINGS PER AGENT                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: COUNT(agent's bookings) / COUNT(unique agents)            │   │
│  │                                                                      │   │
│  │  Target: 15-20 bookings/month/agent                                 │   │
│  │                                                                      │   │
│  │  Leaderboard (This Month):                                           │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │ Rank │ Agent    │ Bookings │ Revenue  │ Margin │ CSAT  │ Trend │ │   │
│  │  │ ─────┼──────────┼──────────┼──────────┼────────┼───────┼───────│ │   │
│  │  │  1   │ Priya    │ 28       │ ₹11.2L   │ 9.8%   │ 4.6   │ ↑     │ │   │
│  │  │  2   │ Amit     │ 24       │ ₹9.8L    │ 10.2%  │ 4.4   │ →     │ │   │
│  │  │  3   │ Sneha    │ 22       │ ₹9.1L    │ 9.1%   │ 4.7   │ ↑     │ │   │
│  │  │  4   │ Rahul    │ 19       │ ₹7.8L    │ 8.9%   │ 4.2   │ ↓     │ │   │
│  │  │  5   │ Kavita   │ 17       │ ₹7.2L    │ 9.5%   │ 4.5   │ →     │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  REVENUE PER AGENT                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: SUM(agent's booking revenue)                              │   │
│  │                                                                      │   │
│  │  Target: ₹8-10L/month/agent                                         │   │
│  │  Top performer: 1.4x target                                          │   │
│  │  Bottom performer: 0.6x target → Needs coaching                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Response Time

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RESPONSE TIME                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Time between customer inquiry and first agent response                     │
│                                                                             │
│  FIRST RESPONSE TIME (FRT)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: AVG(first_response_time - inquiry_time)                  │   │
│  │                                                                      │   │
│  │  Target: <30 minutes (business hours)                               │   │
│  │                                                                      │   │
│  │  Current Performance:                                                │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │ Agent   │ Avg FRT  │ Target Status │ % Within Target          │ │   │
│  │  │ ────────┼──────────┼───────────────┼────────────────────────   │ │   │
│  │  │ Priya   │ 18 min   │ ✅ Excellent   │ 94%                      │ │   │
│  │  │ Amit    │ 25 min   │ ✅ Good        │ 88%                      │ │   │
│  │  │ Sneha   │ 22 min   │ ✅ Good        │ 91%                      │ │   │
│  │  │ Rahul   │ 38 min   │ ⚠️ Fair       │ 72%                      │ │   │
│  │  │ Kavita  │ 45 min   │ ❌ Poor       │ 65%                      │ │   │
│  │  │ AVERAGE │ 30 min   │ ✅ Target met  │ 82%                      │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RESPONSE TIME BY CHANNEL                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Channel   │ Avg Time │ Target │ Status                           │   │
│  │  ──────────┼──────────┼────────┼─────────────────────────          │   │
│  │  WhatsApp  │ 12 min   │ <15min │ ✅ Excellent                     │   │
│  │  Phone     │ 8 min    │ <10min │ ✅ Excellent                     │   │
│  │  Email     │ 2.5 hrs  │ <4hrs  │ ✅ Good                         │   │
│  │  Form      │ 4.2 hrs  │ <4hrs  │ ⚠️ Slightly over                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IMPACT ON CONVERSION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Response Time    │ Conversion Rate                                 │   │
│  │  ────────────────┼────────────────                                  │   │
│  │  <15 minutes      │ 72%                                             │   │
│  │  15-30 minutes    │ 58%                                             │   │
│  │  30-60 minutes    │ 41%                                             │   │
│  │  >60 minutes      │ 23%                                             │   │
│  │                                                                      │   │
│  │  Insight: Faster response = 3x higher conversion                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Completion Rate

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETION RATE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION                                                                  │
│  Percentage of assigned trips that reach "completed" status                 │
│                                                                             │
│  FORMULA                                                                     │
│  Completion Rate = (Completed Trips / Assigned Trips) × 100                  │
│                                                                             │
│  TARGETS                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Target: 85%+                                                        │   │
│  │  Current: 82% → Slightly below target                                │   │
│  │                                                                      │   │
│  │  Breakdown:                                                         │   │
│  │  • Completed: 82%                                                   │   │
│  │  • In Progress: 12%                                                │   │
│  │  • Cancelled: 4%                                                   │   │
│  │  • Stalled: 2%                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STALLED TRIPS (Requires attention)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Definition: No activity for 7+ days                               │   │
│  │                                                                      │   │
│  │  Common stall reasons:                                              │   │
│  │  • Awaiting customer response (45%)                                │   │
│  │  • Awaiting supplier confirmation (30%)                            │   │
│  │  • Payment pending (15%)                                            │   │
│  │  • Agent follow-up needed (10%)                                    │   │
│  │                                                                      │   │
│  │  Action: Automatic reminders at 3, 5, 7 days                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Operational Metrics

### Communication Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMMUNICATION METRICS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MESSAGES SENT                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Total: 2,847 messages                                               │   │
│  │                                                                      │   │
│  │  By Channel:                                                        │   │
│  │  • WhatsApp: 1,542 (54%)                                            │   │
│  │  • Email: 892 (31%)                                                 │   │
│  │  • SMS: 413 (15%)                                                   │   │
│  │                                                                      │   │
│  │  By Type:                                                           │   │
│  │  • Quotes: 524                                                      │   │
│  │  • Itineraries: 312                                                │   │
│  │  • Updates: 1,234                                                   │   │
│  │  • Reminders: 777                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ENGAGEMENT RATE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: (Messages opened / Messages delivered) × 100              │   │
│  │                                                                      │   │
│  │  WhatsApp: 94% (high engagement)                                    │   │
│  │  Email: 67% (moderate engagement)                                   │   │
│  │  SMS: 98% (highest engagement)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Escalations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             ESCALATIONS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ESCALATION RATE                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula: (Escalated Trips / Total Trips) × 100                     │   │
│  │                                                                      │   │
│  │  Target: <5%                                                         │   │
│  │  Current: 3.2% ✅                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ESCALATION REASONS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Reason                     │ Count │ %      │ Trend                 │   │
│  │  ───────────────────────────┼───────┼───────┼───────────────────     │   │
│  │  Complex itinerary          │ 8     │ 42%    │ →                     │   │
│  │  Customer issue             │ 5     │ 26%    │ ↓                     │   │
│  │  Supplier problem           │ 3     │ 16%    │ →                     │   │
│  │  Payment dispute            │ 2     │ 11%    │ →                     │   │
│  │  Other                      │ 1     │ 5%     │ -                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIME TO RESOLVE                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Average resolution time: 18 hours                                  │   │
│  │  Target: <24 hours                                                 │   │
│  │                                                                      │   │
│  │  Resolution SLA:                                                   │   │
│  │  • High priority: <4 hours (85% met)                               │   │
│  │  • Medium priority: <12 hours (78% met)                            │   │
│  │  • Low priority: <48 hours (92% met)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Conversion Funnels

### Booking Funnel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BOOKING FUNNEL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FUNNEL STAGES                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ 1. INQUIRY                            1,000 (100%)             │  │   │
│  │  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │   │
│  │  │                                                │ 75%           │  │   │
│  │  │                                                ▼               │  │   │
│  │  │ 2. QUOTE SENT                         750 (75%)               │  │   │
│  │  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━        │  │   │
│  │  │                                                   │ 67%       │  │   │
│  │  │                                                   ▼            │  │   │
│  │  │ 3. QUOTE OPENED                      500 (50%)               │  │   │
│  │  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                │  │   │
│  │  │                                                        │ 84%    │  │   │
│  │  │                                                        ▼        │  │   │
│  │  │ 4. NEGOTIATION/FOLLOW-UP              420 (42%)               │  │   │
│  │  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                       │  │   │
│  │  │                                                             │ 79% │  │   │
│  │  │                                                             ▼     │  │   │
│  │  │ 5. BOOKING INITIATED                  331 (33%)               │  │   │
│  │  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │  │   │
│  │  │                                                                  │  │   │
│  │  │ 6. BOOKING CONFIRMED                262 (26%) ✅                   │  │   │
│  │  │                                                                      │  │   │
│  │  │  Overall Conversion: 26% (Target: 30%)                            │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DROP-OFF ANALYSIS                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Biggest Drop-offs:                                                 │   │
│  │  1. Inquiry → Quote (25% drop)                                     │   │
│  │     • Reason: Unqualified leads, no response                        │   │
│  │     • Action: Better lead qualification                            │   │
│  │                                                                      │   │
│  │  2. Quote Sent → Opened (33% drop)                                │   │
│  │     • Reason: Email not opened, lost in inbox                      │   │
│  │     • Action: WhatsApp quotes, better subject lines                │   │
│  │                                                                      │   │
│  │  3. Booking Initiated → Confirmed (21% drop)                      │   │
│  │     • Reason: Payment issues, changed mind                         │   │
│  │     • Action: Faster payment collection, follow-up                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Payment Funnel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PAYMENT FUNNEL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. PAYMENT LINK SENT                  262 (100%)                   │   │
│  │     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━      │   │
│  │                                                  │ 78%              │   │
│  │                                                  ▼                  │   │
│  │  2. LINK CLICKED                       204 (78%)                    │   │
│  │     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                   │   │
│  │                                                          │ 91%       │   │
│  │                                                          ▼           │   │
│  │  3. PAYMENT ATTEMPTED                 186 (71%)                    │   │
│  │     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                       │   │
│  │                                                              │ 82%    │   │
│  │                                                              ▼        │   │
│  │  4. PAYMENT SUCCESS                   152 (58%) ✅                   │   │
│  │                                                                      │   │
│  │  Overall Conversion: 58%                                            │   │
│  │  Target: 70%                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PAYMENT FAILURES                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Failure Reason                   │ Count │ %      │ Resolution        │   │
│  │  ─────────────────────────────────┼───────┼───────┼──────────────     │   │
│  │  Insufficient funds              │ 12    │ 50%    │ Retry (60%)       │   │
│  │  Card declined                   │ 5     │ 21%    │ New card (40%)     │   │
│  │  Timeout                        │ 3     │ 13%    │ Retry (80%)       │   │
│  │  Technical error                 │ 2     │ 8%     │ Auto-retry         │   │
│  │  Customer cancelled              │ 2     │ 8%     │ -                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Trend Analysis

### Seasonal Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SEASONAL PATTERNS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REVENUE SEASONALITY                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Peak Season (Oct-Mar):                                             │   │
│  │  • Oct: Dussehra, Diwali bookings (domestic)                        │   │
│  │  • Nov-Dec: Year-end holidays (international)                       │   │
│  │  │  Jan: Republic Day, winter getaways                             │   │
│  │  • Feb-Mar: Summer vacation planning (early bookings)               │   │
│  │                                                                      │   │
│  │  Off-Peak (Apr-Sep):                                                │   │
│  │  • Apr-Jun: Summer holidays (domestic hill stations)                │   │
│  │  • Jul-Sep: Lean period, focus on monsoon getaways                 │   │
│  │                                                                      │   │
│  │  Strategy:                                                          │   │
│  │  • Peak: Focus on volume, margin optimization                        │   │
│  │  • Off-peak: Promotions, corporate segment focus                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BOOKING LEAD TIME                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Domestic: 14-21 days average                                       │   │
│  │  International: 30-45 days average                                   │   │
│  │  Group bookings: 60-90 days average                                  │   │
│  │                                                                      │   │
│  │  Insight: Earlier booking = higher conversion, better margin        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Reference

### Metrics Calculation Service

```typescript
// services/metrics-calculation.service.ts
import { ClickHouseClient } from '@clickhouse/client';

export class MetricsCalculationService {
  private clickhouse: ClickHouseClient;

  async getRevenueMetrics(input: {
    agencyId: string;
    startDate: Date;
    endDate: Date;
  }): Promise<RevenueMetrics> {
    const query = `
      SELECT
        SUM(total_amount) as gross_revenue,
        SUM(margin) as total_margin,
        SUM(total_amount - margin) as net_cost,
        COUNT(*) as booking_count,
        AVG(total_amount) as avg_booking_value
      FROM mv_revenue_daily
      WHERE agency_id = {agencyId:UUID}
        AND date >= {startDate:Date}
        AND date <= {endDate:Date}
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId: input.agencyId,
        startDate: input.startDate.toISOString().split('T')[0],
        endDate: input.endDate.toISOString().split('T')[0],
      },
    });

    const data = result.data[0];

    return {
      gross: data.gross_revenue,
      net: data.gross_revenue - data.total_margin,
      margin: data.total_margin,
      marginPercent: (data.total_margin / data.gross_revenue) * 100,
      bookingCount: data.booking_count,
      avgBookingValue: data.avg_booking_value,
    };
  }

  async getGrowthRate(input: {
    agencyId: string;
    currentPeriodStart: Date;
    currentPeriodEnd: Date;
    comparisonPeriodStart: Date;
    comparisonPeriodEnd: Date;
  }): Promise<GrowthRate> {
    const [current, comparison] = await Promise.all([
      this.getRevenueMetrics({
        agencyId: input.agencyId,
        startDate: input.currentPeriodStart,
        endDate: input.currentPeriodEnd,
      }),
      this.getRevenueMetrics({
        agencyId: input.agencyId,
        startDate: input.comparisonPeriodStart,
        endDate: input.comparisonPeriodEnd,
      }),
    ]);

    return {
      revenue: {
        current: current.gross,
        previous: comparison.gross,
        growth: ((current.gross - comparison.gross) / comparison.gross) * 100,
      },
      bookings: {
        current: current.bookingCount,
        previous: comparison.bookingCount,
        growth: ((current.bookingCount - comparison.bookingCount) / comparison.bookingCount) * 100,
      },
      avgBookingValue: {
        current: current.avgBookingValue,
        previous: comparison.avgBookingValue,
        growth: ((current.avgBookingValue - comparison.avgBookingValue) / comparison.avgBookingValue) * 100,
      },
    };
  }

  async getConversionFunnel(input: {
    agencyId: string;
    startDate: Date;
    endDate: Date;
  }): Promise<ConversionFunnel> {
    const query = `
      SELECT
        step,
        step_order,
        COUNT(DISTINCT trip_id) as count,
        COUNT(DISTINCT trip_id) * 100.0 /
          FIRST_VALUE(COUNT(DISTINCT trip_id)) OVER (ORDER BY step_order) as conversion_rate,
        LAG(COUNT(DISTINCT trip_id)) OVER (ORDER BY step_order) as prev_count,
        COUNT(DISTINCT trip_id) * 100.0 /
          LAG(COUNT(DISTINCT trip_id)) OVER (ORDER BY step_order) as step_conversion
      FROM mv_funnel_bookings
      WHERE agency_id = {agencyId:UUID}
        AND date >= {startDate:Date}
        AND date <= {endDate:Date}
      GROUP BY step, step_order
      ORDER BY step_order
    `;

    const result = await this.clickhouse.query({
      query,
      query_params: {
        agencyId: input.agencyId,
        startDate: input.startDate.toISOString().split('T')[0],
        endDate: input.endDate.toISOString().split('T')[0],
      },
    });

    return {
      steps: result.data,
      overallConversion: result.data[result.data.length - 1]?.conversion_rate || 0,
    };
  }
}
```

---

## Summary

The Analytics Dashboard metrics provide:

- **Revenue Metrics**: Gross/net revenue, margin, growth rate analysis
- **Booking Metrics**: Volume, value, cancellations, conversion tracking
- **Customer Metrics**: New/returning, CLV, satisfaction scores
- **Agent Metrics**: Productivity, response time, completion rates
- **Operational Metrics**: Communication, escalations, resolution times
- **Funnels**: Booking and payment conversion tracking
- **Trends**: Seasonal patterns, lead time analysis

This completes the Metrics Deep Dive. The next document covers Real-Time streaming and monitoring.

---

**Related Documents:**
- [Technical Deep Dive](./ANALYTICS_01_TECHNICAL_DEEP_DIVE.md) — Data architecture
- [UX/UI Deep Dive](./ANALYTICS_02_UX_UI_DEEP_DIVE.md) — Dashboard design
- [Real-Time Deep Dive](./ANALYTICS_04_REALTIME_DEEP_DIVE.md) — Streaming and alerts

**Master Index:** [Analytics Dashboard Deep Dive Master Index](./ANALYTICS_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
