# Agency Operations Command Center — Master Index

> Operations dashboard, alert system, workflow monitoring, and operational reporting for Indian travel agencies

---

## Series Overview

**Focus:** Real-time operations command center for agency management
**Status:** Research complete
**Last Updated:** 2026-04-28

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 01 | [Dashboard](./OPS_CENTER_01_DASHBOARD.md) | Real-time agency health overview, role-based views, customizable widgets, India-specific metrics | Research |
| 02 | [Alerts](./OPS_CENTER_02_ALERTS.md) | Alert categories, severity, routing, escalation, fatigue prevention, multi-channel notification, resolution workflow | Research |
| 03 | [Workflow Monitor](./OPS_CENTER_03_WORKFLOW_MONITOR.md) | Pipeline velocity, time-in-stage, stuck trip detection, SLA monitoring, process mining, bottleneck visualization | Research |
| 04 | [Reporting](./OPS_CENTER_04_REPORTING.md) | Operational reports, KPI tracking, trend analysis, automated generation, India regulatory reporting | Research |

---

**Total:** 4 research documents

---

## Key Themes

### 1. Role-Based Operations
Every surface in the command center adapts to the viewer's role: agent (personal productivity), team lead (team pipeline), manager (department health), owner (agency P&L). Widgets, reports, and alerts all filter and prioritize by role.

### 2. India-Specific Compliance
Indian travel agencies face a complex regulatory landscape. The command center tracks GST collections (CGST/SGST/IGST), TCS deposits, TDS filings, IATA BSP settlements, PF/ESI contributions, and state tourism board requirements with automated deadline alerts.

### 3. Alert Discipline
Alert fatigue is a real risk. The system employs deduplication, rate limiting, aggregation for low-severity alerts, smart throttling, and clear escalation paths to ensure every alert is actionable and critical issues are never missed.

### 4. Data-Driven Pipeline Management
Pipeline velocity, time-in-stage metrics, and process mining transform anecdotal "things feel slow" into measurable, actionable data. Bottleneck detection identifies root causes and suggests interventions.

### 5. Automated Reporting at Scale
From daily flash reports on WhatsApp to quarterly regulatory filings, the reporting engine generates, formats, and distributes reports across channels with versioned templates and role-based customization.

---

## Technology Stack

| Layer | Technology Options | Notes |
|-------|--------------------|-------|
| **Real-time updates** | WebSocket (Socket.io / Pusher / AWS API Gateway) | Dashboard live feeds, alert push |
| **Dashboard grid** | react-grid-layout, muuri | Customizable widget layout with drag-and-drop |
| **Charts & visualization** | Recharts, D3.js, Plotly.js | Funnel charts, heatmaps, Sankey diagrams |
| **Alert routing** | Custom rules engine or PagerDuty / Opsgenie | Escalation policies, on-call rotation |
| **Report generation** | Puppeteer (PDF), ExcelJS (Excel), WeasyPrint (PDF) | Template-based rendering pipeline |
| **Report scheduling** | Bull/BullMQ (job queue), node-cron | Cron-based scheduling with retry logic |
| **Notification channels** | MSG91/Gupshup (SMS/WhatsApp), SendGrid (email), FCM (push) | India-optimized delivery |
| **Data warehouse** | BigQuery, ClickHouse, or DuckDB | Pre-aggregated metrics for dashboard widgets |
| **Process mining** | pm4py (Python), custom event analysis | Workflow discovery from trip events |
| **Regulatory integration** | GSTN API, IATA BSP, EPFO portal | Automated data pull for compliance reports |
| **Mobile dashboard** | PWA or React Native | Responsive single-column layout with tab navigation |
| **Caching** | Redis, React Query | Widget data caching, stale-while-revalidate |

---

## Cross-References to Related Series

| Series | Relevance | Key Overlaps |
|--------|-----------|--------------|
| [Analytics & BI](./ANALYTICS_BI_MASTER_INDEX.md) | Data warehouse and KPI definitions feed into dashboard widgets and reports | KPI framework, data model, star schema |
| [Analytics — Dashboards](./ANALYTICS_02_DASHBOARDS.md) | Dashboard visualization patterns and KPI-by-role matrix | Role-based views, widget types, visualization library choices |
| [Workflow Automation](./WORKFLOW_AUTOMATION_MASTER_INDEX.md) | Workflow rules engine and monitoring infrastructure | SLA configuration, process metrics, stage definitions |
| [Workflow — Monitoring](./WORKFLOW_04_MONITORING.md) | Workflow metrics, SLA tracking, bottleneck detection | Stage metrics, process alerts, incident response |
| [Finance & Accounting](./FINANCE_MASTER_INDEX.md) | Chart of accounts, journal entries, financial reporting | GST/TCS/TDS accounting, P&L generation, reconciliation |
| [Finance — Reporting](./FINANCE_04_REPORTING.md) | Financial report generation and distribution | P&L statements, margin analysis, cost center reporting |
| [Notification & Messaging](./NOTIFICATION_MESSAGING_MASTER_INDEX.md) | Multi-channel notification infrastructure | Channel capabilities, delivery reliability, cost per channel, WhatsApp templates |
| [Notification — Channels](./NOTIFICATION_01_CHANNELS.md) | Channel architecture and India-specific regulatory requirements | DND compliance, TRAI DLT, WhatsApp Business API |
| [Emergency Assistance](./EMERGENCY_MASTER_INDEX.md) | Crisis alerting and emergency response | Emergency severity handling, escalation to owner, traveler safety alerts |
| [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) | Payment gateway status monitoring and reconciliation | Gateway health checks, payment failure alerts, settlement tracking |
| [Commission](./COMMISSION_MASTER_INDEX.md) | Commission tracking and agent performance | Agent revenue widgets, commission-based KPIs |
| [Regulatory & Compliance](./REGULATORY_MASTER_INDEX.md) | IATA, licensing, and regulatory compliance | IATA BSP reporting, agency license status |
| [Multi-Tenancy](./MULTI_TENANCY_PATTERNS_MASTER_INDEX.md) | Branch-level data isolation and reporting | Branch comparison reports, multi-branch consolidation |
| [Mobile App](./MOBILE_APP_DEEP_DIVE_MASTER_INDEX.md) | Mobile dashboard design and push notifications | Mobile widget layout, haptic alerts, offline dashboard |
| [Error Handling](./ERROR_HANDLING_MASTER_INDEX.md) | System error detection and incident response | System alert categories, error rate monitoring, incident workflow |

---

## Series Architecture

```
                        OPS CENTER MASTER INDEX
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
   ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
   │  01 DASHBOARD│      │  02 ALERTS  │      │ 03 WORKFLOW │
   │  Real-time   │      │  Detection  │      │  Monitor    │
   │  agency      │◄────►│  routing    │◄────►│  Pipeline   │
   │  health      │      │  escalation │      │  velocity   │
   │  widgets     │      │  fatigue    │      │  bottlenecks│
   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                        ┌──────▼──────┐
                        │ 04 REPORTING│
                        │  KPI trends │
                        │  Regulatory │
                        │  Automated  │
                        └─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
          ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
          │  Analytics │  │  Finance  │  │ Compliance│
          │  Data WH   │  │  GST/TCS  │  │  IATA     │
          │  KPIs      │  │  P&L      │  │  PF/ESI   │
          └───────────┘  └───────────┘  └───────────┘
```

---

**Last Updated:** 2026-04-28
