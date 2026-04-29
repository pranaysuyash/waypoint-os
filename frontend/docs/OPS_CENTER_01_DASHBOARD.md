# Agency Operations Command Center — Dashboard

> Research document for the real-time operations command dashboard: agency health overview, customizable widgets, role-based views, and India-specific metrics.

---

## Key Questions

1. **What real-time metrics define "agency health" at a glance?**
2. **How do we build a customizable dashboard widget system that supports role-based views (agent, team lead, manager, owner)?**
3. **What India-specific operational metrics need dedicated widgets (GST collections, TCS pending, payment gateway status)?**
4. **How do we design a mobile-friendly operations dashboard that remains useful on small screens?**
5. **What data freshness requirements exist for different widget types — which need WebSockets, which can poll?**

---

## Research Areas

### Dashboard Data Model

```typescript
interface OpsDashboard {
  dashboardId: string;
  name: string;
  ownerId: string;                        // User or role
  role: DashboardRole;
  layout: DashboardLayout;
  widgets: OpsWidget[];
  filters: DashboardFilter[];
  refreshPolicy: RefreshPolicy;
  lastRefreshed: Date;
  isLive: boolean;                        // Real-time WebSocket feed
}

type DashboardRole =
  | 'agent'            // Personal trips, tasks, revenue
  | 'team_lead'        // Team pipeline, agent load, SLA
  | 'manager'          // Department health, revenue, escalations
  | 'owner';           // Full agency P&L, compliance, strategic

interface DashboardLayout {
  columns: 1 | 2 | 3 | 4;
  breakpoints: {
    mobile: 1;         // Single column
    tablet: 2;
    desktop: 3 | 4;
  };
  rows: LayoutRow[];
}

interface LayoutRow {
  id: string;
  height: 'auto' | 'fixed';
  widgets: WidgetPlacement[];
}

interface WidgetPlacement {
  widgetId: string;
  colSpan: number;     // 1-4
  rowSpan: number;     // 1-3
  order: number;
}

interface DashboardFilter {
  type: 'date_range' | 'agent' | 'team' | 'destination' | 'service_type' | 'branch';
  defaultValue: string;
  affectsWidgets: string[];              // Widget IDs that respond to this filter
}

interface RefreshPolicy {
  mode: 'websocket' | 'poll' | 'manual';
  pollIntervalMs?: number;               // 5000 for critical, 30000 for standard
  staleAfterMs: number;                  // Show "stale data" indicator after this
}
```

### Core Widget Types

```typescript
type OpsWidgetType =
  // Pipeline widgets
  | 'trip_pipeline'             // Funnel: intake → quoting → booking → confirmed → traveling → completed
  | 'stage_distribution'        // Bar chart: trips per stage
  | 'revenue_ticker'            // Real-time revenue today/week/month
  | 'agent_workload'            // Heatmap or bar: trips per agent
  | 'pending_approvals'         // List: items awaiting sign-off
  | 'alerts_escalations'        // List: active alerts with severity

  // Financial widgets
  | 'gst_collections'           // CGST/SGST/IGST collected this period
  | 'tcs_pending'               // TCS collected but not yet deposited
  | 'payment_gateway_status'    // Live status: Razorpay/PayU/Bank gateways
  | 'receivables_aging'         // Table: outstanding by aging bucket

  // Performance widgets
  | 'sla_compliance'            // Gauge: % trips within SLA
  | 'response_time'             // Chart: avg time to first response
  | 'conversion_rate'           // Funnel: leads → quotes → bookings

  // Custom widgets
  | 'custom_kpi'                // User-defined KPI with formula
  | 'embedded_report'           // Link to a saved report
  | 'external_url';             // IFrame for 3rd-party tool

interface OpsWidget {
  widgetId: string;
  type: OpsWidgetType;
  title: string;
  config: Record<string, unknown>;
  dataSource: WidgetDataSource;
  interactions: WidgetInteraction[];
  alertRules: WidgetAlertRule[];
}

interface WidgetDataSource {
  type: 'api_endpoint' | 'websocket_channel' | 'query' | 'composite';
  endpoint?: string;
  channel?: string;
  query?: string;
  refreshOn?: ('filter_change' | 'data_change' | 'interval')[];
}

interface WidgetInteraction {
  action: 'drill_down' | 'filter' | 'navigate' | 'export';
  target: string;                         // Widget ID, page route, or API
  params?: Record<string, string>;
}

interface WidgetAlertRule {
  condition: string;                      // e.g., "value > threshold"
  threshold: number;
  severity: 'info' | 'warning' | 'critical';
  notification: boolean;
}
```

### Agency Health Scorecard Widget

```typescript
interface AgencyHealthScorecard {
  timestamp: Date;

  // Pipeline health
  tripsInPipeline: number;
  tripsToday: number;
  tripsThisWeek: number;
  tripsThisMonth: number;
  pipelineTrend: TrendDirection;          // up / down / flat

  // Revenue
  revenueToday: Money;
  revenueThisWeek: Money;
  revenueThisMonth: Money;
  revenueTarget: Money;
  revenuePercentOfTarget: number;         // 0-100

  // Agent workload
  activeAgents: number;
  avgTripsPerAgent: number;
  maxTripsPerAgent: number;               // Highlight if one agent is overloaded
  agentUtilizationPercent: number;

  // Approvals
  pendingApprovals: number;
  oldestPendingApproval: Date;
  approvalsOverdue: number;

  // Alerts
  activeAlerts: number;
  criticalAlerts: number;
  unacknowledgedAlerts: number;
}

type TrendDirection = 'up' | 'down' | 'flat';

interface Money {
  amount: number;
  currency: string;                       // 'INR' default
}
```

### Role-Based Dashboard Views

```typescript
interface RoleDashboardTemplate {
  role: DashboardRole;
  defaultWidgets: DefaultWidgetConfig[];
  availableWidgets: OpsWidgetType[];
  layout: DashboardLayout;
  readOnlyWidgets: string[];              // Widgets this role cannot remove
}

// ┌─────────────────────────────────────────────────────────────────────┐
// │  AGENT VIEW — Personal productivity focus                          │
// ├───────────────────────┬───────────────────────┬─────────────────────┤
// │  My Trips Pipeline    │  Revenue Ticker        │  Tasks Today        │
// │  (5 in intake,        │  Today: ₹1.2L          │  3 follow-ups       │
// │   2 quoting,          │  Week: ₹8.5L           │  2 docs pending     │
// │   8 confirmed)        │  Target: 72%           │  1 approval needed  │
// ├───────────────────────┴───────────────────────┴─────────────────────┤
// │  My Alerts               │  Response Time        │  CSAT Score       │
// │  ⚠ Booking #4213...     │  Avg: 12 min          │  4.6 / 5.0        │
// │  ✅ Payment received     │  Target: 15 min       │  ↑ 0.2 this week  │
// └─────────────────────────────────────────────────────────────────────┘

// ┌─────────────────────────────────────────────────────────────────────┐
// │  TEAM LEAD VIEW — Team pipeline and SLA focus                      │
// ├───────────────────────┬───────────────────────┬─────────────────────┤
// │  Team Pipeline Funnel │  Agent Workload        │  SLA Compliance     │
// │  45 total trips       │  Ravi: 12 trips █████  │  94% within SLA     │
// │  ████████████████████ │  Priya: 8 trips  ████  │  3 at risk          │
// │  Intake→Quote→Book    │  Amit: 14 trips ██████ │  1 breached         │
// ├───────────────────────┼───────────────────────┼─────────────────────┤
// │  Pending Approvals    │  Revenue This Week     │  Team Alerts        │
// │  5 awaiting review    │  ₹24.5L (target ₹30L) │  2 critical         │
// │  Oldest: 3h ago       │  ↑ 12% vs last week   │  7 warnings         │
// └───────────────────────┴───────────────────────┴─────────────────────┘

// ┌─────────────────────────────────────────────────────────────────────┐
// │  MANAGER VIEW — Department health and revenue focus                │
// ├───────────────────────┬───────────────────────┬─────────────────────┤
// │  Revenue Dashboard    │  Trip Pipeline         │  Escalations        │
// │  Today: ₹5.2L         │  120 active trips      │  3 open             │
// │  This week: ₹38L      │  18 in intake          │  1 overdue          │
// │  This month: ₹1.2Cr   │  35 in quoting         │  5 resolved today   │
// ├───────────────────────┼───────────────────────┼─────────────────────┤
// │  GST Collections      │  Payment Gateway       │  Conversion Rate    │
// │  CGST: ₹4.2L          │  Razorpay: ✅ UP       │  Lead→Quote: 68%   │
// │  SGST: ₹4.2L          │  PayU: ✅ UP            │  Quote→Book: 42%   │
// │  IGST: ₹2.1L          │  ICICI Bank: ⚠ SLOW    │  Overall: 29%      │
// ├───────────────────────┼───────────────────────┼─────────────────────┤
// │  TCS Pending          │  Agent Performance     │  Compliance Status  │
// │  ₹8.5L due by 7th    │  Top: Priya (₹6.2L)    │  GST: ✅ Filed      │
// │  Next deposit: 5 days │  Avg: ₹3.8L/agent      │  TDS: ✅ Filed      │
// │  3 trips uncollected  │  Lowest: Amit (₹1.1L)  │  IATA: ⚠ Pending   │
// └───────────────────────┴───────────────────────┴─────────────────────┘

// ┌─────────────────────────────────────────────────────────────────────┐
// │  OWNER VIEW — Full agency P&L and strategic metrics                │
// ├───────────────────────┬───────────────────────┬─────────────────────┤
// │  Agency P&L Summary   │  Branch Performance    │  Compliance        │
// │  Revenue: ₹4.2Cr      │  Mumbai: ₹1.8Cr (43%) │  GST: ✅ Current    │
// │  COGS: ₹3.1Cr         │  Delhi: ₹1.2Cr (29%)   │  TCS: ⚠ 2 pending  │
// │  Gross Margin: 26%    │  Bangalore: ₹0.7Cr(17%)│  IATA: ✅ Renewed   │
// │  EBITDA: ₹0.6Cr       │  Chennai: ₹0.5Cr (11%) │  PF/ESI: ✅ Filed  │
// ├───────────────────────┼───────────────────────┼─────────────────────┤
// │  Strategic KPIs       │  Cash Flow             │  Risk Dashboard     │
// │  NPS: 72              │  Inflow: ₹85L/month    │  FX exposure: $42K  │
// │  Repeat Rate: 38%     │  Outflow: ₹72L/month   │  Supplier risk: Low │
// │  Market Share: 4.2%   │  Net: +₹13L            │  Regulatory: Clear  │
// │  YoY Growth: 22%      │  Cash Reserve: 2.1mo   │  Cyber: ✅ Audited  │
// └───────────────────────┴───────────────────────┴─────────────────────┘
```

### India-Specific Metrics Widgets

```typescript
interface IndiaMetricsWidget {
  // GST Collections
  gst: {
    period: 'current_month' | 'last_month' | 'quarter';
    cgst: Money;
    sgst: Money;
    igst: Money;
    cess: Money;
    totalCollected: Money;
    inputTaxCredit: Money;
    netPayable: Money;
    filingStatus: 'not_started' | 'in_progress' | 'filed' | 'verified';
    filingDeadline: Date;
    gstr1Status: FilingStatus;              // Outward supplies
    gstr3bStatus: FilingStatus;             // Summary return
  };

  // TCS (Tax Collected at Source)
  tcs: {
    collectedThisMonth: Money;
    pendingDeposit: Money;
    nextDepositDate: Date;                  // 7th of next month
    certificateIssued: number;
    certificatePending: number;
    overdueDeposits: OverdueDeposit[];
  };

  // Payment Gateway Health
  paymentGateways: PaymentGatewayStatus[];
}

interface FilingStatus {
  return_type: string;
  period: string;                          // "2026-04"
  status: 'pending' | 'prepared' | 'filed' | 'acknowledged';
  filedDate?: Date;
  dueDate: Date;
  amount?: Money;
}

interface OverdueDeposit {
  tripId: string;
  customerName: string;
  amount: Money;
  collectionDate: Date;
  daysOverdue: number;
}

interface PaymentGatewayStatus {
  provider: 'razorpay' | 'payu' | 'billdesk' | 'icici_bank' | 'hdfc_bank' | 'phonepe' | 'googlepay';
  status: 'operational' | 'degraded' | 'down';
  latencyMs: number;
  successRate: number;                     // Last 1 hour
  lastTransaction: Date;
  uptime24h: number;                       // Percentage
  activeMerchants: string[];               // Merchant IDs linked to agency
}
```

### Customizable Widget System

```typescript
interface WidgetRegistry {
  // Built-in widgets
  builtIn: BuiltInWidgetDefinition[];
  // Custom widgets created by agency
  custom: CustomWidgetDefinition[];
  // Marketplace widgets (future)
  marketplace: MarketplaceWidget[];
}

interface BuiltInWidgetDefinition {
  type: OpsWidgetType;
  name: string;
  description: string;
  category: 'pipeline' | 'financial' | 'performance' | 'compliance' | 'team' | 'customer';
  configSchema: Record<string, ConfigField>;   // JSON Schema for config
  minSize: { colSpan: number; rowSpan: number };
  defaultSize: { colSpan: number; rowSpan: number };
  requiredPermissions: string[];
  dataFreshness: 'real_time' | 'near_real_time' | 'hourly' | 'daily';
}

interface ConfigField {
  type: 'string' | 'number' | 'boolean' | 'select' | 'multi_select' | 'date_range';
  label: string;
  required: boolean;
  defaultValue?: unknown;
  options?: { label: string; value: string }[];
}

interface CustomWidgetDefinition {
  widgetId: string;
  name: string;
  query: string;                          // SQL-like or API query
  visualization: VisualizationType;
  createdBy: string;
  sharedWith: 'self' | 'team' | 'agency';
}
```

### Mobile Dashboard Design

```typescript
interface MobileDashboardLayout {
  // Mobile: single column, priority-ordered widgets
  // Only show top-N most critical widgets
  // Swipeable between "Overview" / "Alerts" / "My Tasks" tabs

  tabs: MobileTab[];
  compactWidgets: CompactWidget[];
  pullToRefresh: boolean;
  hapticAlerts: boolean;                  // Vibrate on critical alert
}

interface MobileTab {
  id: string;
  label: string;
  icon: string;
  widgets: string[];                      // Widget IDs to show on this tab
  maxWidgets: number;                     // Limit for performance
}

// Mobile layout (single column, scroll):
//
// ┌──────────────────────┐
// │  Overview | Alerts | Me │  ← Tab bar
// ├──────────────────────┤
// │  Agency Health       │
// │  ██████████ 94% OK   │
// │  3 critical alerts   │
// ├──────────────────────┤
// │  Revenue Today       │
// │  ₹5.2L ↑ 12%        │
// ├──────────────────────┤
// │  My Trips (8)        │
// │  ⚠ 2 need attention  │
// ├──────────────────────┤
// │  Alerts (3)          │
// │  🔴 Payment declined │
// │  🟡 GST filing due   │
// │  🔵 New booking #428 │
// ├──────────────────────┤
// │  Quick Actions       │
// │  [+Trip] [Search]    │
// └──────────────────────┘
```

### Real-Time Data Architecture

```typescript
interface DashboardDataFeed {
  // WebSocket channels for real-time updates
  channels: {
    'dashboard:agency_health': {
      event: 'health_update';
      payload: AgencyHealthScorecard;
      frequency: 'on_change';            // Push when any metric changes
    };
    'dashboard:revenue': {
      event: 'revenue_tick';
      payload: { revenueToday: Money; newBooking: boolean };
      frequency: 'on_change';
    };
    'dashboard:pipeline': {
      event: 'stage_change';
      payload: { tripId: string; fromStage: string; toStage: string };
      frequency: 'on_change';
    };
    'dashboard:alerts': {
      event: 'new_alert' | 'alert_updated' | 'alert_resolved';
      payload: Alert;
      frequency: 'on_change';
    };
    'dashboard:gateway_status': {
      event: 'gateway_health';
      payload: PaymentGatewayStatus[];
      frequency: 30000;                  // Poll every 30s
    };
  };
}

// Fallback strategy:
// 1. Try WebSocket connection
// 2. If disconnected, fall back to polling (5s for critical, 30s for standard)
// 3. Show connection status indicator
// 4. Queue offline changes and replay on reconnect
```

---

## Open Problems

1. **Widget performance budget** — A dashboard with 10+ widgets all pulling real-time data can overwhelm the browser. Need a performance budget per widget and smart data aggregation on the server side (one WebSocket message updating multiple widgets).

2. **Role-based data isolation** — An agent should only see their own revenue data, while a manager sees the team's. The data layer must enforce row-level security, not just UI filtering.

3. **India-specific data sources** — GST filing status, payment gateway health, and TCS deposit tracking require integrations with government portals (GSTN) and payment aggregators. These APIs may not be real-time.

4. **Custom widget security** — If users can create custom widgets with arbitrary queries, we need SQL injection prevention, query timeout limits, and resource quotas.

5. **Offline dashboard** — Field agents traveling with clients may have poor connectivity. Should the dashboard cache last-known state and clearly indicate stale data?

6. **Widget discoverability** — With 20+ widget types, users may not know what is available. Need a curated "getting started" template and a widget marketplace with descriptions.

---

## Next Steps

- [ ] Wireframe the four role-based dashboard views with a designer
- [ ] Define the widget registry schema and built-in widget catalog
- [ ] Research WebSocket infrastructure (Socket.io, Pusher, AWS API Gateway)
- [ ] Prototype the Agency Health Scorecard widget with mock data
- [ ] Investigate GSTN API availability for automated filing status checks
- [ ] Research payment gateway status APIs (Razorpay, PayU health endpoints)
- [ ] Design mobile dashboard tab structure and touch interactions
- [ ] Evaluate dashboard grid libraries (react-grid-layout, muuri)
