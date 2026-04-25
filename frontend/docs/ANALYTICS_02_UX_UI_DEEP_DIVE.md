# Analytics Dashboard 02: UX/UI Deep Dive

> Complete guide to analytics dashboard design, chart selection, and user experience

---

## Document Overview

**Series:** Analytics Dashboard Deep Dive (Document 2 of 4)
**Focus:** UX/UI — Dashboard layout, chart selection, interactions, responsive design
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Dashboard Layout Architecture](#dashboard-layout-architecture)
3. [Chart Selection Guidelines](#chart-selection-guidelines)
4. [Interactive Features](#interactive-features)
5. [Responsive Design](#responsive-design)
6. [Loading and Empty States](#loading-and-empty-states)
7. [Accessibility](#accessibility)
8. [Implementation Reference](#implementation-reference)

---

## Executive Summary

The Analytics Dashboard UX focuses on clarity, efficiency, and interactivity. Role-based dashboards surface relevant KPIs immediately, with drill-down capabilities for detailed analysis. Interactive filtering, real-time updates, and responsive design ensure accessibility across devices.

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Progressive Disclosure** | Show summary first, details on demand |
| **Visual Hierarchy** | Most important metrics prominent |
| **Consistent Patterns** | Familiar interactions across all views |
| **Performance First** | Fast loading, optimistic updates |
| **Mobile Responsive** | Core metrics accessible on any device |

---

## Dashboard Layout Architecture

### Layout Grid System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD LAYOUT GRID                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HEADER (Fixed, 60px)                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  [Logo]  Analytics    │  Time Range ▼  │  Export  │  Refresh   ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TABS (Fixed, 48px)                                                 │   │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                         │   │
│  │  │Overview│Revenue│Bookings│Customers│Agents│Settings│            │   │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FILTER BAR (Fixed, 48px)                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ 📅 Last 30 days ▼  │  🏢 All Teams ▼  │  👤 All Agents ▼  │  ✅ ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  KPI CARDS ROW (Auto, 140px)                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐│   │
│  │  │ Total Revenue │  │ Bookings     │  │ Customers    │  │ Margin    ││   │
│  │  │ ₹12.5L       │  │ 156          │  │ 89           │  │ 8.5%      ││   │
│  │  │ ↑ 12%        │  │ ↑ 8%         │  │ ↑ 15%        │  │ → 0%      ││   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────┬───────────────┐│
│  │  MAIN CHART AREA (Flexible, 2:1 ratio)                │  SIDE PANEL   ││
│  │                                                       │  (Fixed 320px)││
│  │  ┌───────────────────────────────────────────────────┐ │              ││
│  │  │  Revenue Trend (Line Chart)                       │ │  ┌───────────┐││
│  │  │  ┌─────────────────────────────────────────────┐  │ │  │ Top       │││
│  │  │  │    ₹12.5L                                    │  │ │  │ Customers │││
│  │  │  │  ──╮                                    ╭───│  │ │  │           │││
│  │  │  │     ╲                                  ╱    │  │ │  │ 1. ABC... │││
│  │  │  │      ╲                                ╱     │  │ │  │ 2. XYZ... │││
│  │  │  │       ╲                              ╱      │  │ │  │ 3. DEF... │││
│  │  │  │        ╲                            ╱       │  │ │  │           │││
│  │  │  └─────────────────────────────────────────────┘  │ │  └───────────┘││
│  │  │  Jan  Feb  Mar  Apr  May  Jun                   │ │              ││
│  │  └───────────────────────────────────────────────────┘ │              ││
│  │                                                       │  ┌───────────┐││
│  │  ┌───────────────────────────────────────────────────┐ │  │ Recent    │││
│  │  │  Bookings by Destination (Bar Chart)              │ │  │ Activity  │││
│  │  │  ┌─────────────────────────────────────────────┐  │ │  │           │││
│  │  │  │ Goa ████████████████████ 45                 │  │ │  │ • New...  │││
│  │  │  │ Kerala ██████████████ 38                    │  │ │  │ • Quote...│││
│  │  │  │ Rajasthan ██████████ 32                     │  │ │  │ • Book... │││
│  │  │  │ Himachal ███████ 24                         │  │ │  │           │││
│  │  │  └─────────────────────────────────────────────┘  │ │  └───────────┘││
│  │  └───────────────────────────────────────────────────┘ │              ││
│  │                                                       │              ││
│  └───────────────────────────────────────────────────────┴───────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
AnalyticsDashboard
│
├── DashboardHeader
│   ├── DashboardTitle
│   ├── TimeRangeSelector
│   ├── ExportButton
│   └── RefreshButton (with live indicator)
│
├── DashboardTabs
│   ├── OverviewTab
│   ├── RevenueTab
│   ├── BookingsTab
│   ├── CustomersTab
│   ├── AgentsTab
│   └── SettingsTab
│
├── FilterBar
│   ├── DateRangePicker
│   ├── TeamFilter
│   ├── AgentFilter
│   └── ClearFiltersButton
│
├── KPIGrid
│   ├── KPICard
│   │   ├── KPIValue
│   │   ├── KPIChange
│   │   ├── KPITrend
│   │   └── KPIDrillDown
│   │
├── ChartGrid
│   ├── LineChartCard
│   │   ├── ChartHeader
│   │   ├── ChartCanvas
│   │   ├── ChartLegend
│   │   ├── ChartTooltip
│   │   └── ChartActions
│   │       ├── ZoomButton
│   │       ├── DownloadButton
│   │       └── ExpandButton
│   │
│   ├── BarChartCard
│   ├── PieChartCard
│   ├── FunnelChartCard
│   └── HeatmapCard
│
├── SidePanel
│   ├── LeaderboardCard
│   ├── ActivityFeedCard
│   └── AlertsCard
│
└── DashboardFooter
    ├── LastUpdatedTime
    ├── DataFreshnessIndicator
    └── FeedbackLink
```

### Role-Based Dashboard Variants

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ROLE-BASED DASHBOARD LAYOUTS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OWNER / ADMIN DASHBOARD                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Focus: Business health, revenue, team performance                   │   │
│  │                                                                      │   │
│  │  KPIs: Revenue, Margin, Bookings, Customers, Active Agents           │   │
│  │  Charts: Revenue trend, Booking funnel, Agent leaderboard            │   │
│  │  Side Panel: Agency-wide activity, Revenue alerts                    │   │
│  │                                                                      │   │
│  │  Drill-down: Agency → Team → Agent → Individual bookings            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SENIOR AGENT DASHBOARD                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Focus: Team performance, operational metrics                       │   │
│  │                                                                      │   │
│  │  KPIs: Team bookings, Team revenue, Avg response time, Satisfaction  │   │
│  │  Charts: Team daily performance, Agent comparison, Status breakdown  │   │
│  │  Side Panel: Team activity, Escalations, Pending items              │   │
│  │                                                                      │   │
│  │  Drill-down: Team → Agent → Trip → Booking details                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AGENT DASHBOARD                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Focus: Personal performance, assigned tasks                        │   │
│  │                                                                      │   │
│  │  KPIs: My bookings, My revenue, Completion rate, Avg response time  │   │
│  │  Charts: Personal trend, Task status, Customer responses            │   │
│  │  Side Panel: My tasks, Unread messages, Reminders                   │   │
│  │                                                                      │   │
│  │  Drill-down: My trips → Individual trip details                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  READONLY DASHBOARD                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Focus: View-only access to permitted metrics                       │   │
│  │                                                                      │   │
│  │  KPIs: Limited to permitted categories (e.g., revenue only)         │   │
│  │  Charts: View-only, no drill-down                                   │   │
│  │  Side Panel: None (simplified view)                                 │   │
│  │                                                                      │   │
│  │  Actions: Export only (no modifications)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Chart Selection Guidelines

### Chart Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHART SELECTION TREE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  What do you want to show?                                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  TIME SERIES → How does a value change over time?                   │   │
│  │     │                                                               │   │
│  │     ├─ One metric, simple trend → LINE CHART                        │   │
│  │     │   Example: Revenue over months                                │   │
│  │     │                                                               │   │
│  │     ├─ Multiple metrics, same scale → MULTI-LINE CHART              │   │
│  │     │   Example: Revenue vs Cost over months                         │   │
│  │     │                                                               │   │
│  │     ├─ Multiple metrics, different scales → DUAL-AXIS LINE          │   │
│  │     │   Example: Revenue (₹) vs Margin (%)                          │   │
│  │     │                                                               │   │
│  │     └─ Part-to-whole over time → STACKED AREA                       │   │
│  │         Example: Booking sources over months                         │   │
│  │                                                                      │   │
│  ├───────────────────────────────────────────────────────────────────    │
│  │                                                                      │   │
│  │  COMPARISON → How do values compare across categories?              │   │
│  │     │                                                               │   │
│  │     ├─ Few categories (<8) → VERTICAL BAR CHART                     │   │
│  │     │   Example: Bookings by destination (top 5)                    │   │
│  │     │                                                               │   │
│  │     ├─ Many categories (>8) → HORIZONTAL BAR CHART                  │   │
│  │     │   Example: Bookings by all destinations                      │   │
│  │     │                                                               │   │
│  │     ├─ Two metrics per category → GROUPED BAR CHART                 │   │
│  │     │   Example: Revenue vs Target by team                          │   │
│  │     │                                                               │   │
│  │     └─ Part-to-whole → STACKED BAR                                  │   │
│  │         Example: Booking status by month                             │   │
│  │                                                                      │   │
│  ├───────────────────────────────────────────────────────────────────    │
│  │                                                                      │   │
│  │  PROPORTION → How is a whole divided?                               │   │
│  │     │                                                               │   │
│  │     ├─ Few parts (<5) → PIE CHART                                   │   │
│  │     │   Example: Booking status distribution                         │   │
│  │     │                                                               │   │
│  │     ├─ Many parts (5+) → DONUT CHART                                │   │
│  │     │   Example: Bookings by destination                             │   │
│  │     │                                                               │   │
│  │     └─ Hierarchical → SUNBURST / TREEMAP                            │   │
│  │         Example: Destination → State → City                          │   │
│  │                                                                      │   │
│  ├───────────────────────────────────────────────────────────────────    │
│  │                                                                      │   │
│  │  DISTRIBUTION → How are values distributed?                         │   │
│  │     │                                                               │   │
│  │     ├─ Continuous variable → HISTOGRAM                              │   │
│  │     │   Example: Booking value distribution                          │   │
│  │     │                                                               │   │
│  │     └─ Outliers needed → BOX PLOT                                   │   │
│  │         Example: Agent response times                                │   │
│  │                                                                      │   │
│  ├───────────────────────────────────────────────────────────────────    │
│  │                                                                      │   │
│  │  CORRELATION → How are two variables related?                       │   │
│  │     │                                                               │   │
│  │     ├─ Many data points → SCATTER PLOT                              │   │
│  │     │   Example: Response time vs Customer satisfaction              │   │
│  │     │                                                               │   │
│  │     └─ Heat needed → HEATMAP                                        │   │
│  │         Example: Bookings by day × hour                              │   │
│  │                                                                      │   │
│  └───────────────────────────────────────────────────────────────────    │
│                                                                      │   │
│  FUNNEL → Sequential conversion? → FUNNEL CHART                         │
│     Example: Inquiry → Quote → Booking → Payment                       │
│                                                                      │   │
│  RANKING → Ordered list? → LEADERBOARD / TABLE                         │
│     Example: Top 10 agents by revenue                                  │
│                                                                      │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Chart Library

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHART TYPE REFERENCE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LINE CHART                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Use: Trends over time                                              │   │
│  │  Data: Time series (continuous)                                     │   │
│  │  Max Series: 5                                                      │   │
│  │  Max Points: 100 per series                                         │   │
│  │                                                                      │   │
│  │  Variants:                                                           │   │
│  │  - Simple line: Single metric                                       │   │
│  │  - Multi-line: Multiple comparable metrics                          │   │
│  │  - Area: Filled area under line                                     │   │
│  │  - Stacked: Multiple part-to-whole metrics                          │   │
│  │  - Smooth: Bezier curves (use sparingly)                            │   │
│  │                                                                      │   │
│  │  Features: Hover tooltip, Zoom, Annotate                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BAR CHART                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Use: Comparisons across categories                                 │   │
│  │  Data: Categorical × Numerical                                      │   │
│  │  Max Categories: 12 (vertical), 20 (horizontal)                     │   │
│  │                                                                      │   │
│  │  Variants:                                                           │   │
│  │  - Vertical: Standard comparison                                    │   │
│  │  - Horizontal: Long labels                                          │   │
│  │  - Grouped: Side-by-side comparison                                 │   │
│  │  - Stacked: Part-to-whole within category                           │   │
│  │                                                                      │   │
│  │  Features: Sort, Filter, Drill-down                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PIE / DONUT CHART                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Use: Part-to-whole proportions                                     │   │
│  │  Data: Categorical × Numerical (percentages)                        │   │
│  │  Max Slices: 8 (group others)                                       │   │
│  │                                                                      │   │
│  │  Variants:                                                           │   │
│  │  - Pie: Classic pie chart                                           │   │
│  │  - Donut: Pie with center hole (show total)                        │   │
│  │  - Semi-donut: Half circle (progress style)                         │   │
│  │                                                                      │   │
│  │  Features: Click slice to filter, Label on hover                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FUNNEL CHART                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Use: Sequential conversion tracking                                │   │
│  │  Data: Steps with counts                                            │   │
│  │  Max Steps: 8                                                       │   │
│  │                                                                      │   │
│  │  Features:                                                           │   │
│  │  - Show conversion rate between steps                               │   │
│  │  - Show overall conversion rate                                     │   │
│  │  - Highlight drop-off points                                        │   │
│  │                                                                      │   │
│  │  Example: Inquiry (100%) → Quote (75%) → Booking (50%) → Payment (45%)│  │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLE / LEADERBOARD                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Use: Detailed data, rankings                                      │   │
│  │  Data: Multi-column                                                │   │
│  │  Max Rows: 50 (with pagination)                                    │   │
│  │                                                                      │   │
│  │  Features:                                                           │   │
│  │  - Sort by any column                                              │   │
│  │  - Column filtering                                                 │   │
│  │  - Row actions (view, drill-down)                                  │   │
│  │  - Sparklines in cells                                             │   │
│  │                                                                      │   │
│  │  Visual: Badge ranks (1, 2, 3), trend indicators (↑ → ↓)           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HEATMAP                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Use: Two-dimensional patterns                                     │   │
│  │  Data: X category × Y category × Value                             │   │
│  │                                                                      │   │
│  │  Example: Bookings by Day of Week × Hour                           │   │
│  │                                                                      │   │
│  │  Features: Color scale legend, Click cell to filter                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Color Palette for Charts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHART COLOR PALETTE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMARY COLORS (Sequential data, positive)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Blue    #3B82F6  (Primary data, revenue)                           │   │
│  │  Indigo  #6366F1  (Secondary data)                                  │   │
│  │  Violet  #8B5CF6  (Tertiary data)                                   │   │
│  │  Purple  #A855F7  (Quaternary data)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CATEGORICAL COLORS (Distinct categories)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Blue    #3B82F6  (Category 1)                                      │   │
│  │  Green   #10B981  (Category 2, positive)                            │   │
│  │  Yellow  #F59E0B  (Category 3)                                      │   │
│  │  Orange  #F97316  (Category 4)                                      │   │
│  │  Red     #EF4444  (Category 5, negative)                            │   │
│  │  Pink    #EC4899  (Category 6)                                      │   │
│  │  Teal    #14B8A6  (Category 7)                                      │   │
│  │  Gray    #6B7280  (Other / Uncategorized)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SEMANTIC COLORS (Meaning-based)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Success Green  #10B981  (Positive growth, completed)               │   │
│  │  Warning Amber  #F59E0B  (Caution, pending)                         │   │
│  │  Error Red     #EF4444  (Negative, declined, cancelled)             │   │
│  │  Info Blue      #3B82F6  (Neutral, informational)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NEUTRAL COLORS (Backgrounds, borders)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gray 50  #F9FAFB  (Background)                                     │   │
│  │  Gray 100 #F3F4F6  (Card background)                                │   │
│  │  Gray 200 #E5E7EB  (Border)                                         │   │
│  │  Gray 400 #9CA3AF  (Text secondary)                                 │   │
│  │  Gray 600 #4B5563  (Text primary)                                   │   │
│  │  Gray 900 #111827  (Text heading)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HEATMAP COLORS (Low to High)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Level 1: #EBF5FF  (Very low)                                       │   │
│  │  Level 2: #BFDBFE  (Low)                                            │   │
│  │  Level 3: #60A5FA  (Medium)                                         │   │
│  │  Level 4: #2563EB  (High)                                           │   │
│  │  Level 5: #1E3A8A  (Very high)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interactive Features

### Filtering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FILTERING SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GLOBAL FILTERS (Apply to all widgets)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │   │
│  │  │ Time Range      │  │ Team            │  │ Agent           │      │   │
│  │  │ ───────────────│  │ ───────────────│  │ ───────────────│      │   │
│  │  │ Last 30 days ▼ │  │ All Teams ▼    │  │ All Agents ▼   │      │   │
│  │  │                 │  │                 │  │                 │      │   │
│  │  │ Presets:        │  │ ☐ Team A       │  │ ☐ Agent A       │      │   │
│  │  │ • Today         │  │ ☐ Team B       │  │ ☐ Agent B       │      │   │
│  │  │ • This week     │  │ ☐ Team C       │  │ ☐ Agent C       │      │   │
│  │  │ • This month    │  │                 │  │                 │      │   │
│  │  │ • Custom        │  │                 │  │                 │      │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │   │
│  │                                                                  │   │
│  │  [Clear All Filters]                                    [Apply] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WIDGET-LEVEL FILTERS (Apply to specific widget)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Revenue Chart                                      [Filter ⚙]     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  ─────────                                                      ││   │
│  │  │    ╭───╮                                                       ││   │
│  │  │  ──╯   ╰────────────                                          ││   │
│  │  │                                                                ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                  │   │
│  │  Click [Filter ⚙] to show:                                       │   │
│  │  • Booking status (Confirmed, Pending, Cancelled)                │   │
│  │  • Destination type (Domestic, International)                    │   │
│  │  • Payment status (Paid, Pending, Overdue)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INTERACTIVE FILTERING                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Click bar in chart → Filter other widgets by that category        │   │
│  │  Example: Click "Goa" bar → All widgets show Goa data only         │   │
│  │                                                                      │   │
│  │  Active filters shown as chips:                                     │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │   │
│  │  │ Last 30 ✕   │ │ Team A ✕    │ │ Goa ✕       │                   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Drill-Down

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DRILL-DOWN FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEVEL 1: AGENCY OVERVIEW                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Total Revenue: ₹12.5L                           [Click to drill down]│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  ───╮                                                         ││   │
│  │  │     ╲                                                        ││   │
│  │  │      ╲                                                       ││   │
│  │  │       ╲                                                      ││   │
│  │  │        ╲                                                     ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │ Click                                 │
│                                    ▼                                       │
│  LEVEL 2: BY TEAM                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Revenue by Team                                      [Back ▲]      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ Team A ████████████████████ ₹5.2L                              ││   │
│  │  │ Team B ██████████████ ₹3.8L                                    ││   │
│  │  │ Team C ████████████ ₹3.5L                                      ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │ Click Team A                         │
│                                    ▼                                       │
│  LEVEL 3: BY AGENT (Team A)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Revenue by Agent - Team A                           [Back ▲]      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ Agent A-1 ████████████████ ₹2.1L                               ││   │
│  │  │ Agent A-2 ██████████ ₹1.5L                                     ││   │
│  │  │ Agent A-3 ████████ ₹1.6L                                       ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │ Click Agent A-1                       │
│                                    ▼                                       │
│  LEVEL 4: BOOKING DETAILS                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Bookings by Agent A-1                                [Back ▲]      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ Booking ID    │ Customer    │ Destination │ Revenue  │ Actions ││   │
│  │  │ ──────────────┼─────────────┼─────────────┼──────────┼─────────││   │
│  │  │ BK-001        │ ABC Corp    │ Goa         │ ₹45,000  │ View    ││   │
│  │  │ BK-002        │ XYZ Ltd     │ Kerala      │ ₹38,000  │ View    ││   │
│  │  │ BK-003        │ DEF Inc     │ Rajasthan   │ ₹52,000  │ View    ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Updates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REAL-TIME UPDATE UX                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LIVE INDICATOR                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ● Live  Updating every 5 seconds                        [Pause]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  UPDATE ANIMATION                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  When new data arrives:                                              │   │
│  │                                                                      │   │
│  │  1. Flash affected values (100ms fade in/out)                       │   │
│  │                                                                      │   │
│  │     2. Number animate (count up/down over 500ms)                    │   │
│  │     ₹12,45,000 → ₹12,50,000                                         │   │
│  │                                                                      │   │
│  │  3. Chart update (smooth transition)                                │   │
│  │     ┌─────────────────────────────────────────────────────────────┐│   │
│  │     │  OLD DATA POINTS fade out                                    ││   │
│  │     │  NEW DATA POINTS fade in                                     ││   │
│  │     │  Line draws to new position                                  ││   │
│  │     └─────────────────────────────────────────────────────────────┘│   │
│  │                                                                      │   │
│  │  4. Show toast notification for significant changes                │   │
│  │     ┌─────────────────────────────────────────────────────────────┐│   │
│  │     │  ✓ New booking: ₹45,000 from ABC Travels                    ││   │
│  │     │                                           [Dismiss]         ││   │
│  │     └─────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  UPDATE CONTROL                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User can:                                                          │   │
│  │  • Pause live updates                                               │   │
│  │  • Set refresh rate (5s, 30s, 1m, 5m, Manual)                       │   │
│  │  • See "Last updated" timestamp                                     │   │
│  │  • Force refresh with Refresh button                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Responsive Design

### Breakpoint Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RESPONSIVE BREAKPOINTS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DESKTOP (1280px+)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Full layout: Side panel visible, all charts in grid                 │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────┬─────────────────────────┐  │   │
│  │  │  Main content (flex-1)                │  Side panel (320px)    │  │   │
│  │  │  ┌────────────────────────────────┐  │  ┌───────────────────┐│  │   │
│  │  │  │ KPIs (4 columns)               │  │  │ Leaderboard       ││  │   │
│  │  │  ├────────────────────────────────┤  │  │ Activity          ││  │   │
│  │  │  │ Charts (2:1 grid)               │  │  │ Alerts            ││  │   │
│  │  │  │  ┌────────────┬────────────┐   │  │  │                   ││  │   │
│  │  │  │  │ Chart 1    │ Chart 2    │   │  │  │                   ││  │   │
│  │  │  │  ├────────────┴────────────┤   │  │  │                   ││  │   │
│  │  │  │  │ Chart 3 (full width)      │   │  │  │                   ││  │   │
│  │  │  │  └────────────────────────────┘   │  │  │                   ││  │   │
│  │  │  └────────────────────────────────┘  │  └───────────────────┘│  │   │
│  │  └──────────────────────────────────────┴─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLET (768px - 1279px)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Side panel collapsible, charts stack vertically                   │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ KPIs (2 columns, wrap to 2 rows)                                ││   │
│  │  ├─────────────────────────────────────────────────────────────────┤│   │
│  │  │ Charts (single column, full width)                              ││   │
│  │  │  ┌────────────────────────────────────────────────────────────┐││   │
│  │  │  │ Chart 1 (full width)                                       │││   │
│  │  │  ├────────────────────────────────────────────────────────────┤││   │
│  │  │  │ Chart 2 (full width)                                       │││   │
│  │  │  ├────────────────────────────────────────────────────────────┤││   │
│  │  │  │ Chart 3 (full width)                                       │││   │
│  │  │  └────────────────────────────────────────────────────────────┘││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                      │   │
│  │  [Show Side Panel] toggle in header                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MOBILE (320px - 767px)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Simplified view, essential KPIs only                               │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ KPIs (1 column, horizontal scroll)                              ││   │
│  │  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               ││   │
│  │  │  │ Revenue │  │Booking │  │Customer│  │ Margin │ →            ││   │
│  │  │  │ ₹12.5L  │  │  156   │  │   89   │  │  8.5%  │               ││   │
│  │  │  └────────┘  └────────┘  └────────┘  └────────┘               ││   │
│  │  ├─────────────────────────────────────────────────────────────────┤│   │
│  │  │ Primary Chart (full viewport width)                             ││   │
│  │  │  ┌────────────────────────────────────────────────────────────┐││   │
│  │  │  │                                                            │││   │
│  │  │  │  Revenue Trend (simplified, fewer points)                  │││   │
│  │  │  │                                                            │││   │
│  │  │  └────────────────────────────────────────────────────────────┘││   │
│  │  ├─────────────────────────────────────────────────────────────────┤│   │
│  │  │ Quick Actions                                                  ││   │
│  │  │  [View Details] [Export] [Refresh]                             ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                      │   │
│  │  Side panel: Bottom sheet / modal                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Touch Interactions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOUCH INTERACTION PATTERNS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SWIPE                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Swipe horizontally between dashboard tabs                        │   │
│  │  • Swipe vertically on long charts                                  │   │
│  │  • Swipe left on KPI card to see details                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PINCH & ZOOM                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Pinch to zoom in/out on time range                               │   │
│  │  • Double-tap to reset zoom                                         │   │
│  │  • Pan when zoomed in                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TAP                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Tap chart element to see details                                 │   │
│  │  • Tap legend item to show/hide series                              │   │
│  │  • Tap KPI card to drill down                                       │   │
│  │  • Long-press for context menu                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Loading and Empty States

### Loading States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LOADING STATE PATTERNS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INITIAL LOAD (Full page)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Analytics                                                      ││   │
│  │  ├─────────────────────────────────────────────────────────────────┤│   │
│  │  │  ● Overview  Revenue  Bookings  Customers  Agents               ││   │
│  │  ├─────────────────────────────────────────────────────────────────┤│   │
│  │  │                                                                  ││   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      ││   │
│  │  │  │ ░░░░░░░░ │  │ ░░░░░░░░ │  │ ░░░░░░░░ │  │ ░░░░░░░░ │      ││   │
│  │  │  │ ░░░░░░░░ │  │ ░░░░░░░░ │  │ ░░░░░░░░ │  │ ░░░░░░░░ │      ││   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      ││   │
│  │  │                                                                  ││   │
│  │  │  ┌────────────────────────────────────────────────────────────┐││   │
│  │  │  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │││   │
│  │  │  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │││   │
│  │  │  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │││   │
│  │  │  └────────────────────────────────────────────────────────────┘││   │
│  │  │                                                                  ││   │
│  │  │  Loading your analytics data...                                   ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INCREMENTAL LOAD (Widget refresh)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Revenue Chart                                              ↻       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ││   │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ││   │
│  │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ││   │
│  │  │  Refreshing...                                                  ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OPTIMISTIC UPDATE (New data arriving)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Total Revenue                                              ✓ New   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  ₹12,50,000                                      +5,000 today    ││   │
│  │  │  ↑ 12% vs last period                                           ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Empty States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EMPTY STATE PATTERNS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NO DATA YET (New agency, no events)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │                                                                  ││   │
│  │  │                      📊                                         ││   │
│  │  │                                                                  ││   │
│  │  │              No analytics data yet                              ││   │
│  │  │                                                                  ││   │
│  │  │         Start creating bookings to see your analytics           ││   │
│  │  │                                                                  ││   │
│  │  │                   [Create Booking]                               ││   │
│  │  │                                                                  ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NO RESULTS (Filter returns nothing)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Revenue Chart (Last 30 days)                         [Clear Filters]│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │                                                                  ││   │
│  │  │                       🔍                                        ││   │
│  │  │                                                                  ││   │
│  │  │            No data matches your filters                          ││   │
│  │  │                                                                  ││   │
│  │  │         Try adjusting your date range or filters                ││   │
│  │  │                                                                  ││   │
│  │  │              [Clear All Filters]                                 ││   │
│  │  │                                                                  ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NO ACCESS (Permission denied)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │                                                                  ││   │
│  │  │                      🔒                                         ││   │
│  │  │                                                                  ││   │
│  │  │         You don't have access to this analytics                 ││   │
│  │  │                                                                  ││   │
│  │  │      Contact your admin to request access                       ││   │
│  │  │                                                                  ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Accessibility

### A11y Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ACCESSIBILITY CHECKLIST                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COLOR CONTRAST                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ All text meets WCAG AA (4.5:1 for normal, 3:1 for large)       │   │
│  │  ✅ Chart colors distinguishable by color + pattern/shape           │   │
│  │  ✅ Semantic colors (green/red) paired with icons/labels            │   │
│  │  ✅ Focus states visible on all interactive elements               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  KEYBOARD NAVIGATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ All charts focusable with Tab                                    │   │
│  │  ✅ Arrow keys navigate chart data points                            │   │
│  │  ✅ Enter/Space drills down on focused element                       │   │
│  │  ✅ Escape closes modals/side panels                                 │   │
│  │  ✅ Skip links for main content                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCREEN READER                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ Chart data available in table format                            │   │
│  │  ✅ aria-labels on all charts and KPIs                              │   │
│  │  ✅ Live updates announced with aria-live                           │   │
│  │  ✅ Chart trends described in text ("increased by 12%")             │   │
│  │  ✅ Data table export available                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MAGNIFICATION / ZOOM                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ Layout doesn't break at 200% zoom                               │   │
│  │  ✅ Charts scale without losing data                                │   │
│  │  ✅ Text remains readable at all zoom levels                        │   │
│  │  ✅ No horizontal scroll on body                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Reference

### React Components

```typescript
// components/analytics/DashboardLayout.tsx
import { useQuery } from '@tanstack/react-query';
import { KPICard } from './KPICard';
import { ChartCard } from './ChartCard';
import { FilterBar } from './FilterBar';
import { SidePanel } from './SidePanel';

export function DashboardLayout() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => fetch('/api/analytics/dashboard').then(r => r.json()),
    refetchInterval: 30000, // Refresh every 30s
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="analytics-dashboard">
      <DashboardHeader />
      <DashboardTabs />

      <FilterBar />

      <div className="kpi-grid grid grid-cols-4 gap-4">
        <KPICard
          title="Total Revenue"
          value={metrics.revenue.total}
          change={metrics.revenue.change}
          trend={metrics.revenue.trend}
          format="currency"
        />
        <KPICard
          title="Bookings"
          value={metrics.bookings.total}
          change={metrics.bookings.change}
          format="number"
        />
        <KPICard
          title="Customers"
          value={metrics.customers.total}
          change={metrics.customers.change}
          format="number"
        />
        <KPICard
          title="Margin"
          value={metrics.margin.percent}
          change={metrics.margin.change}
          format="percent"
        />
      </div>

      <div className="content-grid grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="charts-area lg:col-span-2 space-y-6">
          <ChartCard
            title="Revenue Trend"
            type="line"
            data={metrics.revenue.trend}
            actions={['zoom', 'download', 'expand']}
            onDrillDown={handleRevenueDrillDown}
          />
          <ChartCard
            title="Bookings by Destination"
            type="bar"
            data={metrics.bookings.byDestination}
            actions={['filter', 'download']}
          />
        </div>

        <SidePanel>
          <Leaderboard data={metrics.agents.leaderboard} />
          <ActivityFeed events={metrics.recentActivity} />
        </SidePanel>
      </div>
    </div>
  );
}

// components/analytics/KPICard.tsx
interface KPICardProps {
  title: string;
  value: number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  format?: 'currency' | 'number' | 'percent';
  onClick?: () => void;
}

export function KPICard({
  title,
  value,
  change,
  trend,
  format = 'number',
  onClick,
}: KPICardProps) {
  const formatValue = (val: number) => {
    switch (format) {
      case 'currency':
        return `₹${(val / 100000).toFixed(1)}L`;
      case 'percent':
        return `${val.toFixed(1)}%`;
      default:
        return val.toLocaleString();
    }
  };

  const trendIcon = {
    up: '↑',
    down: '↓',
    neutral: '→',
  }[trend || 'neutral'];

  const trendColor = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500',
  }[trend || 'neutral'];

  return (
    <button
      onClick={onClick}
      className="kpi-card p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
    >
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <p className="text-2xl font-bold mt-2">{formatValue(value)}</p>
      {change !== undefined && (
        <p className={`text-sm mt-1 ${trendColor}`}>
          {trendIcon} {Math.abs(change)}% vs last period
        </p>
      )}
    </button>
  );
}

// components/analytics/ChartCard.tsx
import { LineChart, BarChart } from '@/components/charts';

interface ChartCardProps {
  title: string;
  type: 'line' | 'bar' | 'pie' | 'funnel';
  data: any[];
  actions?: string[];
  onDrillDown?: (data: any) => void;
}

export function ChartCard({ title, type, data, actions, onDrillDown }: ChartCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="chart-card bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold">{title}</h3>
        <ChartActions actions={actions} onExpand={() => setIsExpanded(true)} />
      </div>

      {type === 'line' && <LineChart data={data} onDataPointClick={onDrillDown} />}
      {type === 'bar' && <BarChart data={data} onBarClick={onDrillDown} />}

      {isExpanded && (
        <ChartModal title={title} type={type} data={data} onClose={() => setIsExpanded(false)} />
      )}
    </div>
  );
}
```

### Chart Library Integration

```typescript
// components/charts/LineChart.tsx
import { Line } from 'react-chartjs-2';
import { ChartOptions } from 'chart.js';

interface LineChartProps {
  data: { date: string; value: number }[];
  onDataPointClick?: (point: any) => void;
}

export function LineChart({ data, onDataPointClick }: LineChartProps) {
  const chartData = {
    labels: data.map(d => d.date),
    datasets: [{
      label: 'Revenue',
      data: data.map(d => d.value),
      borderColor: '#3B82F6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.4,
    }],
  };

  const options: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1F2937',
        padding: 12,
        titleFont: { size: 13 },
        bodyFont: { size: 12 },
        callbacks: {
          label: (context) => `₹${context.parsed.y.toLocaleString()}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { maxTicksLimit: 6 },
      },
      y: {
        beginAtZero: true,
        grid: { color: '#E5E7EB' },
        ticks: {
          callback: (value) => `₹${(value / 1000).toFixed(0)}K`,
        },
      },
    },
    onClick: (event, elements) => {
      if (elements.length > 0 && onDataPointClick) {
        const index = elements[0].index;
        onDataPointClick(data[index]);
      }
    },
  };

  return (
    <div className="chart-container h-64">
      <Line data={chartData} options={options} />
    </div>
  );
}
```

---

## Summary

The Analytics Dashboard UX/UI provides:

- **Clear Layout**: Grid-based layout with KPIs, charts, and side panel
- **Smart Charts**: Appropriate chart selection for each data type
- **Rich Interactions**: Filtering, drill-down, real-time updates
- **Responsive Design**: Optimized for desktop, tablet, and mobile
- **Accessible**: WCAG AA compliant, keyboard navigation, screen reader support

This completes the UX/UI Deep Dive. The next document covers Metrics definitions.

---

**Related Documents:**
- [Technical Deep Dive](./ANALYTICS_01_TECHNICAL_DEEP_DIVE.md) — Data architecture
- [Metrics Deep Dive](./ANALYTICS_03_METRICS_DEEP_DIVE.md) — KPI definitions
- [Real-Time Deep Dive](./ANALYTICS_04_REALTIME_DEEP_DIVE.md) — Streaming and alerts

**Master Index:** [Analytics Dashboard Deep Dive Master Index](./ANALYTICS_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
