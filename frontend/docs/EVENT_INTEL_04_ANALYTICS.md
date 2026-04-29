# Destination Event & Festival Intelligence — Analytics

> Research document for event performance analytics, ROI tracking, demand forecasting accuracy, and event intelligence for agency strategy.

---

## Key Questions

1. **How do we measure event package performance?**
2. **How accurate are event-driven demand forecasts?**
3. **What event analytics inform agency strategy?**
4. **How does event intelligence integrate with CRM?**

---

## Research Areas

### Event Package Performance

```typescript
interface EventPackageAnalytics {
  event_id: string;
  package_id: string;

  // Sales metrics
  packages_sold: number;
  revenue: Money;
  avg_selling_price: Money;
  early_bird_pct: number;               // % sold at early bird rate
  last_minute_pct: number;

  // Profitability
  cost: Money;
  gross_margin: Money;
  margin_pct: number;
  inventory_forfeit_cost: Money;        // unsold rooms/flights lost
  net_margin: Money;

  // Customer metrics
  avg_group_size: number;
    repeat_customers_pct: number;         // booked same event last year
  new_customers_pct: number;
  customer_satisfaction: number;

  // Marketing metrics
  leads_generated: number;
  conversion_rate: number;
  cost_per_acquisition: Money;
  whatsapp_open_rate: number;
  email_click_rate: number;
}

// ── Event package performance dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Package Performance — 2026                      │
// │                                                       │
// │  Top Events by Revenue:                               │
// │  1. New Year Goa        — ₹42L | 95% sold | 18% marg│
// │  2. Diwali Kerala        — ₹28L | 82% sold | 22% marg│
// │  3. Dubai Shopping Fest  — ₹22L | 78% sold | 16% marg│
// │  4. Holi Rajasthan       — ₹15L | 70% sold | 20% marg│
// │  5. Singapore Xmas       — ₹18L | 65% sold | 14% marg│
// │                                                       │
// │  Inventory Risk:                                       │
// │  Total holds: ₹38L | Forfeited: ₹2.8L (7.4%)       │
// │  Worst: Holi Rajasthan — 30% unsold, ₹4.5L at risk  │
// │  Best: New Year Goa — 5% unsold, minimal risk       │
// │                                                       │
// │  Customer Insights:                                    │
// │  Repeat event bookers: 35%                            │
// │  New year bookers most loyal (42% rebook next year)  │
// │  Diwali packages attract most first-time customers   │
// │                                                       │
// │  Marketing ROI:                                        │
// │  WhatsApp campaigns: 3.2x ROI                         │
// │  Email campaigns: 1.8x ROI                            │
// │  Social media: 2.1x ROI                               │
// │  Best channel: WhatsApp for last-minute deals         │
// └─────────────────────────────────────────────────────┘
```

### Demand Forecast Accuracy

```typescript
// ── Forecast accuracy tracking ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Demand Forecast Accuracy — 2026                 │
// │                                                       │
// │  Event            | Predicted | Actual | Error        │
// │  ─────────────────────────────────────────────────── │
// │  Diwali (domestic)| +35% demand| +32% | -3% ✅       │
// │  New Year Goa     | +50% demand| +58% | +8% ⚠️      │
// │  Holi Rajasthan   | +25% demand| +18% | -7% ⚠️      │
// │  Dubai Shopping   | +20% demand| +22% | +2% ✅       │
// │  Christmas SG     | +30% demand| +28% | -2% ✅       │
// │                                                       │
// │  Lessons learned:                                     │
// │  • Under-predicted New Year (social media buzz)      │
// │  • Over-predicted Holi (competing with IPL finals)   │
// │  • Dubai and SG forecasts most accurate              │
// │                                                       │
// │  Model improvements:                                  │
// │  • Weight social media sentiment higher for Goa      │
// │  • Factor competing events into demand model         │
// │  • Add airline capacity data as input                │
// └─────────────────────────────────────────────────────┘
```

### Event Strategy Recommendations

```typescript
// ── Strategy recommendations from event analytics ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Strategy — 2027 Recommendations                 │
// │                                                       │
// │  Double Down:                                         │
// │  • New Year Goa: highest demand, best margins        │
// │    → Pre-book 50% more inventory by June 2026       │
// │    → Launch early bird in July (vs August)           │
// │                                                       │
// │  Grow:                                                │
// │  • Diwali packages: attracts new customers           │
// │    → Expand to Diwali Dubai + Diwali Singapore       │
// │    → Create "Diwali abroad" category                 │
// │                                                       │
// │  Optimize:                                            │
// │  • Holi Rajasthan: good margins but lower fill rate  │
// │    → Reduce held inventory by 20%                    │
// │    → Target niche: photography tours + Holi          │
// │                                                       │
// │  Explore:                                             │
// │  • IPL final travel packages (new opportunity)       │
// │  • Cherry blossom Japan (growing Indian interest)    │
// │  • Bali Nyepi (Day of Silence) — unique experience   │
// │                                                       │
// │  Exit:                                                │
// │  • Easter Goa — declining demand, low margins        │
// │    → Replace with spring break alternatives          │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Attribution** — A customer may see a WhatsApp message about Diwali packages, browse the website, then call to book. Which channel gets credit?

2. **Year-over-year comparison** — Event dates shift (Diwali moves 10-15 days each year). Comparing "Diwali 2025" with "Diwali 2026" requires date-normalized models.

3. **Competitive intelligence** — Competing agencies also book event inventory. Knowing their pricing and availability would help but is hard to obtain.

4. **Long-tail events** — Top 10 events drive 80% of revenue. But niche events (wine festivals, marathons, temple fairs) collectively matter. Tracking them all is expensive.

---

## Next Steps

- [ ] Build event package performance analytics
- [ ] Create demand forecast accuracy tracker
- [ ] Implement event strategy recommendation engine
- [ ] Design event CRM integration for customer targeting
