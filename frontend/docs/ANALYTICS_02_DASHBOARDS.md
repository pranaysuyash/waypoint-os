# Analytics — Dashboards & Visualization

> Research document for operational and executive dashboards, KPIs, and data visualization.

---

## Key Questions

1. **What dashboards does each role need (agent, team lead, operations, finance, executive)?**
2. **What are the critical KPIs for a travel agency?**
3. **How do we build dashboards that drive action, not just display data?**
4. **What's the right visualization tool — custom React components, or BI platform (Metabase, Looker)?**
5. **How do we handle dashboard performance with large datasets?**

---

## Research Areas

### Dashboard-by-Role Matrix

| Role | Dashboard | Key Metrics | Refresh |
|------|-----------|-------------|---------|
| Agent | Personal productivity | Trips handled, conversion rate, revenue, CSAT | Real-time |
| Team Lead | Team performance | Team bookings, pipeline, SLA compliance | Hourly |
| Operations | Operational health | Active trips, alerts, issues, supplier performance | Real-time |
| Finance | Financial health | Revenue, margins, receivables, payables | Daily |
| Executive | Business overview | Revenue, growth, market share, profitability | Daily/Weekly |
| Sales | Sales pipeline | Leads, conversion, deals in progress | Real-time |
| Marketing | Campaign performance | CAC, channel ROI, engagement | Daily |

### KPI Framework

```typescript
interface KPI {
  kpiId: string;
  name: string;
  category: KPICategory;
  formula: string;
  unit: string;
  target: number;
  frequency: 'real_time' | 'hourly' | 'daily' | 'weekly' | 'monthly';
  owner: string;
  visualization: VisualizationType;
  alerts: KPIAlert[];
}

type KPICategory =
  | 'revenue'           // Total revenue, revenue per trip, margin
  | 'volume'            // Bookings, trips, travelers
  | 'conversion'        // Lead → booking, quote → booking
  | 'efficiency'        // Time to quote, time to book, spine run time
  | 'quality'           // CSAT, complaint rate, error rate
  | 'customer'          // NPS, retention rate, lifetime value
  | 'supplier'          // Supplier performance, SLA compliance
  | 'financial'         // Cash flow, receivables aging, cost per booking;

type VisualizationType =
  | 'line_chart'        // Trends over time
  | 'bar_chart'         // Comparisons
  | 'donut_chart'       // Composition
  | 'funnel'            // Conversion funnel
  | 'heatmap'           // Activity density
  | 'scorecard'         // Single metric with trend
  | 'table'             // Detailed data
  | 'map'               // Geographic distribution
  | 'sparkline';        // Inline mini-chart

interface KPIAlert {
  condition: 'above' | 'below' | 'outside_range';
  threshold: number;
  severity: 'info' | 'warning' | 'critical';
  recipients: string[];
}
```

### Dashboard Components

```typescript
interface Dashboard {
  dashboardId: string;
  name: string;
  role: string;
  layout: DashboardLayout;
  filters: DashboardFilter[];
  autoRefresh: number;          // Seconds
  exportFormats: ('pdf' | 'csv' | 'excel')[];
}

interface DashboardLayout {
  rows: DashboardRow[];
}

interface DashboardRow {
  columns: DashboardColumn[];
}

interface DashboardColumn {
  width: number;                // 1-12 grid
  widget: DashboardWidget;
}

interface DashboardWidget {
  type: 'kpi_scorecard' | 'chart' | 'table' | 'list' | 'funnel';
  dataSource: string;
  config: Record<string, unknown>;
  drillDown?: string;           // Link to detailed view
}
```

---

## Open Problems

1. **Dashboard sprawl** — Easy to create too many dashboards that nobody uses. Need a curated set per role, not unlimited customization.

2. **Real-time vs. performance** — Real-time dashboards with complex aggregations are expensive. Need caching and pre-aggregation strategy.

3. **Actionable insights** — Dashboards should highlight "what to do" not just "what happened." Anomaly detection and recommendations need to be built in.

4. **Mobile dashboard experience** — Executives want to check metrics on mobile. Complex charts don't work on small screens.

5. **Data democratization** — Non-technical users need to create custom reports. Self-service BI requires careful UX design.

---

## Next Steps

- [ ] Research BI tools for embedded dashboards (Metabase, Apache Superset, Recharts)
- [ ] Define KPI library with targets and alert thresholds
- [ ] Design dashboard wireframes for each role
- [ ] Study dashboard performance optimization (pre-aggregation, caching)
- [ ] Create dashboard requirements document with priority ranking
