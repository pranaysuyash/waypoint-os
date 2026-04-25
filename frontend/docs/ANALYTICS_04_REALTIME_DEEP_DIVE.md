# Analytics Dashboard 04: Real-Time Deep Dive

> Complete guide to real-time streaming, live monitoring, and alerting

---

## Document Overview

**Series:** Analytics Dashboard Deep Dive (Document 4 of 4)
**Focus:** Real-Time — Streaming updates, live monitoring, alerting, anomaly detection
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Real-Time Architecture](#real-time-architecture)
3. [Streaming Data Flow](#streaming-data-flow)
4. [Live Dashboard Updates](#live-dashboard-updates)
5. [Alert System](#alert-system)
6. [Anomaly Detection](#anomaly-detection)
7. [Performance Monitoring](#performance-monitoring)
8. [Implementation Reference](#implementation-reference)

---

## Executive Summary

Real-time analytics enables agencies to respond quickly to opportunities and issues. The system uses WebSocket streaming for live dashboard updates, a configurable alert engine for proactive notifications, and anomaly detection for identifying unusual patterns automatically.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Live Updates** | Dashboard metrics update within seconds of new events |
| **Configurable Alerts** | Threshold-based notifications via multiple channels |
| **Anomaly Detection** | ML-based identification of unusual patterns |
| **Performance Monitoring** | System health and query performance tracking |

---

## Real-Time Architecture

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REAL-TIME DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. EVENT OCCURS                                                            │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  User action → Service → Database                                   │ │
│     │  Example: Agent confirms booking                                     │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  2. CHANGE DATA CAPTURE                                                    │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  PostgreSQL WAL → Debezium → Kafka                                 │ │
│     │  Topic: analytics.events                                            │ │
│     │  Latency: <100ms                                                    │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  3. REAL-TIME PROCESSOR                                                    │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  Event Processor Service                                            │ │
│     │  - Consumes from Kafka                                             │ │
│     │  - Updates ClickHouse                                               │ │
│     │  - Evaluates alerts                                                │ │
│     │  - Publishes to Redis pub/sub                                      │ │
│     │  Latency: <500ms                                                    │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  4. WEBSOCKET BROADCAST                                                    │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  WebSocket Server                                                   │ │
│     │  - Subscribes to Redis pub/sub                                     │ │
│     │  - Broadcasts to connected clients                                 │ │
│     │  Latency: <100ms                                                    │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  5. CLIENT UPDATE                                                         │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  Browser Dashboard                                                  │ │
│     │  - Receives WebSocket message                                      │ │
│     │  - Optimistic UI update                                             │ │
│     │  - Animates value changes                                          │ │
│     │  End-to-end latency: <1 second                                      │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REAL-TIME COMPONENTS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EVENT PROCESSOR (Node.js / BullMQ)                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  class RealTimeProcessor {                                      ││   │
│  │  │    async process(event) {                                      ││   │
│  │  │      // 1. Validate event                                       ││   │
│  │  │      // 2. Update ClickHouse (async)                            ││   │
│  │  │      // 3. Evaluate alerts                                      ││   │
│  │  │      // 4. Publish to Redis                                     ││   │
│  │  │    }                                                           ││   │
│  │  │  }                                                             ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ALERT ENGINE (Rules-based + ML)                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - Threshold rules (e.g., revenue < target)                    ││   │
│  │  │  - Rate of change rules (e.g., bookings drop >20%)             ││   │
│  │  │  - Anomaly detection (e.g., unusual pattern)                   ││   │
│  │  │  - Composite conditions (AND/OR logic)                          ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  NOTIFICATION SERVICE                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Channels:                                                      ││   │
│  │  │  - In-app (WebSocket)                                          ││   │
│  │  │  - Email (digest for non-urgent)                                ││   │
│  │  │  - WhatsApp (critical alerts)                                   ││   │
│  │  │  - Slack (team notifications)                                   ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WEBSOCKET GATEWAY                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - Connection management                                        ││   │
│  │  │  - Authentication (JWT)                                         ││   │
│  │  │  - Subscription registry                                        ││   │
│  │  │  - Broadcast optimization                                      ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CLIENT SDK                                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - Automatic reconnection                                       ││   │
│  │  │  - Subscription management                                      ││   │
│  │  │  - Optimistic updates                                           ││   │
│  │  │  - Fallback to polling                                           ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Streaming Data Flow

### Event Types for Streaming

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STREAMABLE EVENT TYPES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HIGH PRIORITY (Stream immediately)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • booking.confirmed        → Update revenue, bookings              │   │
│  │  • booking.cancelled        → Update cancellations                  │   │
│  │  • payment.completed        → Update revenue, payment metrics        │   │
│  │  • trip.status_changed      → Update trip status counts             │   │
│  │  • message.sent             → Update communication metrics          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MEDIUM PRIORITY (Batch every 10 seconds)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • customer.created         → Update customer counts               │   │
│  │  • document.generated       → Update document metrics              │   │
│  │  • quote.generated          → Update quote metrics                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOW PRIORITY (Batch every minute)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • agent.login              → Update agent activity                │   │
│  │  • view.dashboard           → Update usage analytics               │   │
│  │  • export.download          → Update export metrics                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Payload Format

```typescript
// Real-time event payload
interface RealtimeEvent {
  // Event identification
  id: string;
  type: string;              // e.g., 'booking.confirmed'
  category: string;          // 'high', 'medium', 'low'

  // Agency context
  agencyId: string;

  // Event data
  data: {
    // Previous value (for comparison)
    previous?: {
      revenue?: number;
      bookings?: number;
      // ... other metric values
    };

    // New value
    current: {
      revenue?: number;
      bookings?: number;
      // ... other metric values
    };

    // Change
    delta?: {
      revenue?: number;
      bookings?: number;
      // ... other metric changes
    };
  };

  // Timestamps
  timestamp: Date;
  processedAt: Date;

  // Affected widgets (for targeted updates)
  affectedWidgets: string[];    // e.g., ['revenue-card', 'revenue-chart']
}
```

---

## Live Dashboard Updates

### Update Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UPDATE STRATEGIES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OPTIMISTIC UI                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Update UI immediately with new data                             │   │
│  │  2. Show "updating..." indicator                                     │   │
│  │  3. Confirm with server response                                    │   │
│  │  4. Revert on error (rare)                                          │   │
│  │                                                                      │   │
│  │  Benefit: Instant feedback, perceived performance                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INCREMENTAL UPDATES                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For counter-type metrics:                                          │   │
│  │  - Animate from old value to new value                             │   │
│  │  - Show +N/-N indicator                                             │   │
│  │  - Flash background color briefly                                   │   │
│  │                                                                      │   │
│  │  Example: 156 → 157 with +1 badge                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHART UPDATES                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For charts:                                                        │   │
│  │  - Add new data point (no full refresh)                            │   │
│  │  - Smooth line transition                                           │   │
│  │  - Auto-scroll if viewing latest                                    │   │
│  │                                                                      │   │
│  │  Performance: O(1) update vs O(n) full refresh                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Update Throttling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UPDATE THROTTLING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THROTTLE RULES                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Metric Type          │ Update Frequency │ Rationale                │   │
│  │  ────────────────────┼─────────────────┼──────────────────────      │   │
│  │  Counters (bookings)  │ Immediate       │ User expects instant     │   │
│  │  Revenue              │ Immediate       │ Critical metric          │   │
│  │  Averages             │ Every 10s        │ Avoid jitter             │   │
│  │  Percentages          │ Every 10s        │ Avoid jitter             │   │
│  │  Historical charts    │ Every 30s        │ Less urgency             │   │
│  │  Leaderboards         │ Every 60s        │ Position changes rare    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEBOUNCING                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For rapid events (e.g., multiple bookings in quick succession):    │   │
│  │                                                                      │   │
│  │  - Collect events for 2 seconds                                      │   │
│  │  - Send single batch update                                          │   │
│  │  - Show "N new bookings" message                                      │   │
│  │                                                                      │   │
│  │  Reduces UI thrashing, improves perceived smoothness                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Alert System

### Alert Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ALERT TYPE TAXONOMY                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THRESHOLD ALERTS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger when metric crosses threshold                               │   │
│  │                                                                      │   │
│  │  Examples:                                                           │   │
│  │  • Revenue < 80% of target                                          │   │
│  │  • Cancellation rate > 10%                                          │   │
│  │  • Response time > 1 hour                                           │   │
│  │  • Stalled trips > 5%                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TREND ALERTS                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger when metric shows unusual trend                             │   │
│  │                                                                      │   │
│  │  Examples:                                                           │   │
│  │  • Bookings down >20% vs same period last week                      │   │
│  │  • Revenue declining for 3 consecutive days                         │   │
│  │  • Margin % dropping below target                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ANOMALY ALERTS                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger when ML model detects anomaly                               │   │
│  │                                                                      │   │
│  │  Examples:                                                           │   │
│  │  • Unusual spike in cancellations                                    │   │
│  │  • Sudden drop in inquiry conversion                                │   │
│  │  • Abnormal booking pattern (e.g., all from one agent)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  COMPOSITE ALERTS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger when multiple conditions met                               │   │
│  │                                                                      │   │
│  │  Examples:                                                           │   │
│  │  • Revenue < target AND bookings < target (critical)                │   │
│  │  │  High cancellations AND low CSAT (investigate)                  │   │
│  │  • No bookings for 24h AND peak season (urgent)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Alert Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ALERT CONFIGURATION UI                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CREATE ALERT                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Alert Name                   [Daily Revenue Target]               │   │
│  │                                                                      │   │
│  │  Metric Type                 ▼ Revenue                            │   │
│  │                            Bookings                               │   │
│  │                            Cancellations                          │   │
│  │                            Response Time                          │   │
│  │                                                                      │   │
│  │  Condition                  ○ Above threshold                     │   │
│  │                             ● Below threshold                     │   │
│  │                             ○ Rate of change                      │   │
│  │                             ○ Anomaly detected                    │   │
│  │                                                                      │   │
│  │  Threshold                  [₹1,00,000]                          │   │
│  │  Time Period                 ▼ Daily                              │   │
│  │                            Weekly                                 │   │
│  │                            Monthly                                 │   │
│  │                                                                      │   │
│  │  Severity                   ▼ Warning                             │   │
│  │                            Info                                   │   │
│  │                            Critical                               │   │
│  │                                                                      │   │
│  │  Notify                    ☑ Email                                │   │
│  │                            ☑ WhatsApp                             │   │
│  │                            ☐ Slack                                │   │
│  │                            ☐ In-app only                          │   │
│  │                                                                      │   │
│  │  Quiet Hours                ☑ Enable (10 PM - 8 AM)               │   │
│  │                                                                      │   │
│  │                           [Cancel]  [Save Alert]                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Alert Escalation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALERT ESCALATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEVEL 1: INFO (In-app notification only)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger: Minor deviation from trend                                 │   │
│  │  Example: Bookings slightly below target                             │   │
│  │  Action: Show in notification center, no push                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │ Not resolved in 2 hours               │
│                                    ▼                                       │
│  LEVEL 2: WARNING (Email + In-app)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger: Clear threshold breach                                     │   │
│  │  Example: Revenue 20% below target                                  │   │
│  │  Action: Send email to owner/admin, highlight in dashboard           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │ Not resolved in 4 hours               │
│                                    ▼                                       │
│  LEVEL 3: CRITICAL (WhatsApp + Email + In-app)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Trigger: Severe deviation or critical threshold                     │   │
│  │  Example: Zero bookings in 24h, system error                        │   │
│  │  Action: WhatsApp message to owner, email to team, loud alert       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AUTO-RESOLVE                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  When condition returns to normal:                                  │   │
│  │  - Mark alert as resolved                                           │   │
│  │  - Send "resolved" notification                                     │   │
│  │  - Log resolution time                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Anomaly Detection

### Detection Methods

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ANOMALY DETECTION METHODS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATISTICAL METHODS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Z-Score Analysis                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Z = (current_value - mean) / standard_deviation                ││   │
│  │  │                                                                  ││   │
│  │  │  Trigger alert if: |Z| > 3 (3-sigma rule)                       ││   │
│  │  │                                                                  ││   │
│  │  │  Use: Detecting outliers in booking values, response times      ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                      │   │
│  │  Moving Average                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Compare current value to 7-day moving average                  ││   │
│  │  │                                                                  ││   │
│  │  │  Trigger alert if: deviation > 2 standard deviations            ││   │
│  │  │                                                                  ││   │
│  │  │  Use: Trend detection, seasonality-adjusted alerts              ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ML-BASED METHODS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Isolation Forest                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Unsupervised learning for anomaly detection                    ││   │
│  │  │                                                                  ││   │
│  │  │  Use: Multivariate anomalies (e.g., high cancellations +        ││   │
│  │  │       low CSAT together)                                        ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                      │   │
│  │  Prophet (Time Series Forecasting)                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Facebook's Prophet model for forecasting                        ││   │
│  │  │                                                                  ││   │
│  │  │  Compares actual vs predicted, flags significant deviations    ││   │
│  │  │                                                                  ││   │
│  │  │  Use: Revenue forecasting, booking trend prediction             ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Anomaly Scenarios

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANOMALY SCENARIOS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SUDDEN SPIKE                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Scenario: Cancellations suddenly increase 300%                     │   │
│  │  Detection: Z-score > 5 for cancellation rate                        │   │
│  │  Alert: "Unusual cancellation activity detected"                     │   │
│  │  Action: Check for system error, supplier issue                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SUDDEN DROP                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Scenario: Bookings drop to zero for 4 hours                        │   │
│  │  Detection: Moving average deviation > 3 sigma                      │   │
│  │  Alert: "No new bookings in 4 hours (unusual)"                       │   │
│  │  Action: Check booking system, notification issues                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PATTERN CHANGE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Scenario: Response time gradually increasing over days             │   │
│  │  Detection: Linear regression trend with significant slope           │   │
│  │  Alert: "Response time trending upward (investigate)"                │   │
│  │  Action: Check agent workload, system performance                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CORRELATION ANOMALY                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Scenario: High bookings but low revenue (unusual)                  │   │
│  │  Detection: Multivariate anomaly detection                          │   │
│  │  Alert: "High booking volume with low revenue (check margins)"        │   │
│  │  Action: Verify booking values, check for discounts                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Performance Monitoring

### System Health Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SYSTEM HEALTH METRICS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PIPELINE LATENCY                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Event → Dashboard latency                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Target: <1 second (p95)                                       ││   │
│  │  │  Current: 850ms (p95) ✅                                       ││   │
│  │  │                                                                  ││   │
│  │  │  Breakdown:                                                      ││   │
│  │  │  • CDC capture: 50ms                                            ││   │
│  │  │  • Kafka publish: 30ms                                          ││   │
│  │  │  • Event processing: 200ms                                      ││   │
│  │  │  • ClickHouse update: 150ms                                     ││   │
│  │  │  • WebSocket broadcast: 100ms                                   ││   │
│  │  │  • Client render: 50ms                                          ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  QUERY PERFORMANCE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Dashboard query response times                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Query Type              │ p50    │ p95    │ p99    │ Target    ││   │
│  │  │  ───────────────────────┼────────┼────────┼────────┼───────────││   │
│  │  │  KPI cards               │ 45ms   │ 120ms  │ 280ms  │ <200ms    ││   │
│  │  │  Revenue chart           │ 180ms  │ 450ms  │ 920ms  │ <500ms    ││   │
│  │  │  Leaderboard            │ 220ms  │ 580ms  │ 1.1s   │ <600ms    ││   │
│  │  │  Funnel analysis         │ 320ms  │ 780ms  │ 1.4s   │ <800ms    ││   │
│  │  │  Agent drill-down       │ 150ms  │ 390ms  │ 720ms  │ <500ms    ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CACHE PERFORMANCE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Cache Hit Rate: 82% (Target: >75%) ✅                          ││   │
│  │  │  Cache Miss Rate: 18%                                           ││   │
│  │  │  Avg Cache Response: 8ms                                        ││   │
│  │  │  Avg DB Response (cache miss): 420ms                            ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WEBSOCKET METRICS                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Active connections: 47                                         ││   │
│  │  │  Messages/sec: 12                                               ││   │
│  │  │  Avg message size: 2.4KB                                        ││   │
│  │  │  Reconnection rate: 2%                                          ││   │
│  │  │  Error rate: 0.1%                                               ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Health Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HEALTH DASHBOARD (Admin Only)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PIPELINE STATUS                                           │ Healthy │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  ● CDC Running          │ 50 events/sec  │ Latency: 50ms       ││   │
│  │  │  ● Kafka Healthy        │ Lag: 0 msgs    │                      ││   │
│  │  │  ● Processor Running    │ 0 queued       │ CPU: 35%             ││   │
│  │  │  ● ClickHouse Healthy   │ QPS: 245       │ Disk: 45%            ││   │
│  │  │  ● Redis Healthy        │ Mem: 62%       │ Conn: 120            ││   │
│  │  │  ● WebSocket Running    │ 47 clients     │ Messages: 12/s       ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUERY PERFORMANCE (Last Hour)                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │                                                                  ││   │
│  │  │  Avg Response Time ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ││   │
│  │  │  Target (500ms)    ━━━━━━━━━━━━━                                ││   │
│  │  │                                                                  ││   │
│  │  │  ┌────────────────────────────────────────────────────────────┐ ││   │
│  │  │  │ P99: 920ms  │ P95: 450ms  │ P50: 180ms  │ Target: 500ms    │ ││   │
│  │  │  └────────────────────────────────────────────────────────────┘ ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ALERTS (Last 24 Hours)                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Triggered: 23    Resolved: 18    Active: 5                     ││   │
│  │  │                                                                  ││   │
│  │  │  Active Alerts:                                                  ││   │
│  │  │  • Revenue below target (Warning) - 2h ago                      ││   │
│  │  │  • Query latency high (Info) - 30m ago                          ││   │
│  │  │  • Agent Kavita response time (Warning) - 4h ago                ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Reference

### Real-Time Event Processor

```typescript
// services/realtime-processor.service.ts
import { Kafka, Consumer } from 'kafkajs';
import { Redis } from 'ioredis';
import { ClickHouseClient } from '@clickhouse/client';

export class RealTimeEventProcessor {
  private kafka: Kafka;
  private consumer: Consumer;
  private redis: Redis;
  private clickhouse: ClickHouseClient;
  private alertService: AlertService;

  async start() {
    await this.consumer.connect();
    await this.consumer.subscribe({ topic: 'analytics.events' });

    await this.consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        const event = JSON.parse(message.value.toString());

        // Process event
        await this.processEvent(event);
      },
    });
  }

  private async processEvent(event: any) {
    const startTime = Date.now();

    try {
      // 1. Validate event
      const validated = this.validateEvent(event);

      // 2. Update ClickHouse (async, don't wait)
      this.updateClickHouse(validated).catch(err => {
        console.error('ClickHouse update failed:', err);
      });

      // 3. Check for alerts
      const alerts = await this.checkAlerts(validated);

      // 4. Publish to Redis for WebSocket broadcast
      await this.publishUpdate(validated);

      // 5. Send alerts if triggered
      for (const alert of alerts) {
        await this.alertService.sendAlert(alert);
      }

      // 6. Log processing time
      const processingTime = Date.now() - startTime;
      this.recordMetric('event_processing_time', processingTime);
    } catch (error) {
      console.error('Event processing failed:', error);
      this.recordMetric('event_processing_errors', 1);
    }
  }

  private async checkAlerts(event: any): Promise<Alert[]> {
    const alerts: Alert[] = [];

    // Get applicable alert rules for this agency
    const rules = await this.getAlertRules(event.agencyId);

    for (const rule of rules) {
      const shouldTrigger = await this.evaluateRule(rule, event);

      if (shouldTrigger) {
        alerts.push({
          ruleId: rule.id,
          agencyId: event.agencyId,
          severity: rule.severity,
          message: this.formatAlertMessage(rule, event),
          data: event,
        });
      }
    }

    return alerts;
  }

  private async evaluateRule(rule: AlertRule, event: any): Promise<boolean> {
    switch (rule.type) {
      case 'threshold':
        return this.evaluateThreshold(rule, event);
      case 'trend':
        return this.evaluateTrend(rule, event);
      case 'anomaly':
        return this.evaluateAnomaly(rule, event);
      default:
        return false;
    }
  }

  private async evaluateThreshold(rule: AlertRule, event: any): Promise<boolean> {
    // Get current metric value
    const query = this.buildQuery(rule.metric, rule.timeWindow);
    const result = await this.clickhouse.query({ query });
    const currentValue = result.data[0]?.value;

    if (!currentValue) return false;

    // Evaluate condition
    switch (rule.condition) {
      case 'above':
        return currentValue > rule.threshold;
      case 'below':
        return currentValue < rule.threshold;
      case 'equals':
        return currentValue === rule.threshold;
      default:
        return false;
    }
  }

  private async publishUpdate(event: any) {
    const payload = {
      type: event.event_type,
      agencyId: event.agency_id,
      data: event.data,
      timestamp: new Date(),
    };

    // Publish to agency-specific channel
    await this.redis.publish(
      `analytics:${event.agency_id}`,
      JSON.stringify(payload)
    );

    // Also publish to global channel for system-wide updates
    await this.redis.publish(
      'analytics:all',
      JSON.stringify(payload)
    );
  }

  private recordMetric(name: string, value: number) {
    // Send to metrics system (e.g., Prometheus, DataDog)
    // Implementation depends on metrics backend
  }
}
```

### WebSocket Client

```typescript
// hooks/useRealtimeAnalytics.ts
import { useEffect, useState } from 'react';

export function useRealtimeAnalytics(agencyId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(
      `wss://api.example.com/analytics/stream?token=${getAuthToken()}`
    );

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);

      // Subscribe to agency updates
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels: [
          `analytics:${agencyId}:revenue`,
          `analytics:${agencyId}:bookings`,
          `analytics:${agencyId}:customers`,
        ],
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'update':
          // Update metrics with new data
          setMetrics(prev => this.mergeMetrics(prev, message.data));
          break;
        case 'alert':
          // Handle alert
          showAlertNotification(message.data);
          break;
        case 'connected':
          console.log('Subscribed to channels:', message.data.channels);
          break;
      }
    };

    ws.onerror = (event) => {
      setError('Connection error');
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Attempt reconnection after delay
      setTimeout(() => {
        // Reconnection logic would go here
      }, 5000);
    };

    return () => {
      ws.close();
    };
  }, [agencyId]);

  const mergeMetrics = (
    prev: DashboardMetrics | null,
    update: any
  ): DashboardMetrics => {
    if (!prev) return update;

    // Merge update into previous metrics
    return {
      ...prev,
      ...update,
      // For counters, add the delta
      revenue: {
        ...prev.revenue,
        ...(update.revenue?.total && {
          total: prev.revenue.total + (update.revenue.delta || 0),
        }),
      },
      bookings: {
        ...prev.bookings,
        ...(update.bookings?.total && {
          total: prev.bookings.total + (update.bookings.delta || 0),
        }),
      },
    };
  };

  return { isConnected, metrics, error };
}
```

---

## Summary

The Real-Time Analytics system provides:

- **Sub-Second Updates**: End-to-end latency under 1 second
- **Configurable Alerts**: Threshold, trend, and anomaly-based notifications
- **Multi-Channel Notifications**: In-app, email, WhatsApp, Slack
- **Anomaly Detection**: ML-powered unusual pattern detection
- **Performance Monitoring**: System health and query performance tracking
- **Smart Throttling**: Debouncing and batching for smooth UX

This completes the Real-Time Deep Dive and the entire Analytics Dashboard series.

---

**Related Documents:**
- [Technical Deep Dive](./ANALYTICS_01_TECHNICAL_DEEP_DIVE.md) — Data architecture
- [UX/UI Deep Dive](./ANALYTICS_02_UX_UI_DEEP_DIVE.md) — Dashboard design
- [Metrics Deep Dive](./ANALYTICS_03_METRICS_DEEP_DIVE.md) — KPI definitions

**Master Index:** [Analytics Dashboard Deep Dive Master Index](./ANALYTICS_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
