# Output Panel 15: Complete Metrics Definitions

> Comprehensive KPIs, metrics calculations, and dashboard definitions for the Output Panel system

---

## Part 1: Metrics Overview

### 1.1 Metrics Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         METRICS HIERARCHY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              ┌─────────────┐                                │
│                              │  BUSINESS   │                                │
│                              │   OUTCOMES  │                                │
│                              └──────┬──────┘                                │
│                                     │                                       │
│                    ┌──────────────────┼──────────────────┐                  │
│                    ▼                  ▼                  ▼                  │
│           ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│           │ CONVERSION  │    │  EFFICIENCY │    │   QUALITY   │            │
│           │             │    │             │    │             │            │
│           │ Quote →     │    │ Generation  │    │ Error Rate  │            │
│           │ Booking     │    │ Time        │    │ NPS         │            │
│           │ Rate        │    │ Agent Time  │    │ Revisions   │            │
│           └──────┬──────┘    └──────┬──────┘    └──────┬──────┘            │
│                  │                  │                  │                   │
│                  └──────────────────┼──────────────────┘                   │
│                                     ▼                                       │
│                          ┌─────────────────────┐                          │
│                          │  OPERATIONAL METRICS │                          │
│                          │                     │                          │
│                          │ • Volume             │                          │
│                          │ • Delivery Rates     │                          │
│                          │ • Engagement        │                          │
│                          │ • Technical Health  │                          │
│                          └─────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Metric Categories

| Category | Purpose | Stakeholders |
|----------|---------|--------------|
| **Conversion** | Measure funnel effectiveness | Management, Sales |
| **Efficiency** | Track operational speed | Operations, Agents |
| **Quality** | Monitor output accuracy | Quality, Compliance |
| **Engagement** | Gauge customer interaction | Marketing, Product |
| **Technical** | System health monitoring | Engineering, DevOps |
| **Financial** | Revenue and cost impact | Finance, Management |

---

## Part 2: Conversion Metrics

### 2.1 Funnel Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONVERSION FUNNEL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INQUIRY ──► QUOTE SENT ──► QUOTE VIEWED ──► BOOKING ──► REVENUE           │
│                                                                             │
│    │           │              │              │            │                │
│    │           │              │              │            │                │
│    ▼           ▼              ▼              ▼            ▼                │
│  1000        850            640            128        ₹12,80,000         │
│  (100%)      (85%)          (75%)          (20%)       (₹1L avg)         │
│                                                                             │
│  Drop-off:    Drop-off:      Drop-off:     Conversion:  AOV:             │
│  15%          25%            80%            12.8%       ₹1,00,000        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Metric Definitions

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Quote Send Rate** | Quotes Sent / Inquiries × 100 | % of inquiries getting quotes | ≥90% |
| **Quote View Rate** | Quotes Viewed / Quotes Sent × 100 | % of quotes opened by customers | ≥70% |
| **Quote Engagement Rate** | (Viewed + Clicked) / Sent × 100 | % of quotes with any engagement | ≥75% |
| **Quote-to-Booking Conversion** | Bookings / Quotes Sent × 100 | % of quotes converting to bookings | ≥15% |
| **View-to-Booking Conversion** | Bookings / Quotes Viewed × 100 | % of viewed quotes converting | ≥20% |
| **Time-to-First-View** | Avg time from send to first view | Engagement speed | <2 hours |
| **Quote Response Time** | Avg time from inquiry to quote sent | Agent responsiveness | <4 hours |

### 2.2 Conversion Benchmarking

```typescript
interface ConversionBenchmarks {
  industry: {
    quoteSendRate: number;      // 85-95%
    quoteViewRate: number;      // 60-75%
    conversionRate: number;     // 10-20%
  };

  topPerformers: {
    quoteSendRate: number;      // ≥98%
    quoteViewRate: number;      // ≥85%
    conversionRate: number;     // ≥25%
  };

  byDestinationType: {
    domestic: {
      quoteViewRate: number;    // 75-80%
      conversionRate: number;   // 18-25%
    };
    international: {
      quoteViewRate: number;    // 65-75%
      conversionRate: number;   // 12-18%
    };
    honeymoon: {
      quoteViewRate: number;    // 85-90%
      conversionRate: number;   // 22-30%;
    };
  };
}
```

---

## Part 3: Efficiency Metrics

### 3.1 Generation Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Avg Generation Time** | Sum of gen times / Count | Time to generate bundle | <5 seconds |
| **P95 Generation Time** | 95th percentile of gen times | Worst-case performance | <10 seconds |
| **P99 Generation Time** | 99th percentile of gen times | Extreme cases | <15 seconds |
| **Failed Generation Rate** | Failures / Total attempts × 100 | % of failed generations | <0.5% |
| **Retry Rate** | Retries / Total attempts × 100 | % of generations requiring retry | <2% |
| **Queue Depth** | Current pending generations | System load | <100 |

### 3.2 Agent Efficiency Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Time Per Quote** | Sum of quote creation time / Quotes | Agent time to create quote | <5 minutes |
| **Quotes Per Agent Per Day** | Total quotes / Active agents | Daily agent productivity | ≥15 |
| **Revision Rate** | Revised quotes / Total quotes × 100 | % requiring revisions | <15% |
| **Auto-Acceptance Rate** | Auto-accepted quotes / Total quotes × 100 | % accepted without changes | ≥80% |
| **Template Usage** | Template-based / Total × 100 | % using templates vs manual | ≥90% |

### 3.3 Delivery Efficiency Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Delivery Success Rate** | Successful deliveries / Total attempts × 100 | % of successful deliveries | ≥98% |
| **First Delivery Success** | First attempt success / Total × 100 | % without retries | ≥95% |
| **Avg Delivery Time** | Sum of delivery times / Count | Time to successful delivery | <30 seconds |
| **Channel Success Rate** | By channel (WhatsApp, Email, Portal) | Per-channel reliability | ≥95% each |

---

## Part 4: Quality Metrics

### 4.1 Accuracy Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Data Completeness Score** | Complete fields / Required fields × 100 | % of required fields filled | 100% |
| **Pricing Accuracy Rate** | Correct prices / Total prices checked × 100 | % of accurate prices | 99.9% |
| **Validation Pass Rate** | Passed validations / Total validations × 100 | % passing quality checks | ≥95% |
| **Error Detection Rate** | Errors caught / Total errors × 100 | % of errors caught before delivery | ≥99% |
| **Return/Revision Rate** | Returned quotes / Total quotes × 100 | % returned for corrections | <5% |

### 4.2 Customer Satisfaction Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Quote NPS** | (Promoters - Detractors) × 100 | Customer satisfaction score | ≥50 |
| **Quote CSAT** | Avg satisfaction rating (1-5) | Average customer rating | ≥4.2 |
| **Complaint Rate** | Complaints / Quotes sent × 1000 | Per 1000 quotes | <5 |
| **Referral Rate** | Referrals / Total customers × 100 | % of customers referring | ≥15% |

### 4.3 Content Quality Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Template Consistency** | Template usage / Total × 100 | % using approved templates | ≥95% |
| **Brand Compliance** | Compliant / Total checked × 100 | % meeting brand guidelines | 100% |
| **Grammar/Spelling Score** | Error-free / Total checked × 100 | % without errors | ≥99% |
| **PDF Quality Score** | Passed quality checks / Total × 100 | % passing PDF quality checks | ≥99% |

---

## Part 5: Engagement Metrics

### 5.1 View Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Open Rate** | Opened / Sent × 100 | % of quotes opened | ≥70% |
| **Unique Views** | Unique viewers / Sent | Distinct viewers per quote | ≥1.5× |
| **View Duration** | Avg time spent viewing | Engagement depth | ≥60 seconds |
| **Scroll Depth** | Avg % of page scrolled | Content engagement | ≥80% |
| **Reopen Rate** | Reopened / Opened × 100 | % viewed multiple times | ≥30% |

### 5.2 Interaction Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Click-Through Rate** | Clicked / Viewed × 100 | % clicking any link | ≥25% |
| **Attachment Download Rate** | Downloads / Viewed × 100 | % downloading PDF | ≥60% |
| **Share Rate** | Shared / Viewed × 100 | % shared with others | ≥10% |
| **Reply Rate** | Replied / Sent × 100 | % prompting response | ≥40% |

### 5.3 Channel Engagement Comparison

| Channel | Open Rate | Click Rate | Reply Rate | Best For |
|---------|-----------|------------|------------|----------|
| **WhatsApp** | 95%+ | 35%+ | 50%+ | Quick questions, urgency |
| **Email** | 60-75% | 20-30% | 25-35% | Detailed info, attachments |
| **Portal** | 80%+ | 40%+ | 15-20% | Self-service, families |

---

## Part 6: Technical Metrics

### 6.1 System Health Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **API Uptime** | (Total time - Downtime) / Total × 100 | Service availability | ≥99.9% |
| **API Response Time (P50)** | Median response time | Typical response | <200ms |
| **API Response Time (P95)** | 95th percentile response | Slow but acceptable | <500ms |
| **API Response Time (P99)** | 99th percentile response | Worst case | <1000ms |
| **Error Rate** | Errors / Total requests × 100 | % of failed requests | <0.1% |

### 6.2 Infrastructure Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **CPU Utilization** | Avg CPU usage | Server load | <70% |
| **Memory Utilization** | Avg memory usage | Memory pressure | <80% |
| **Disk Utilization** | Storage used / Total × 100 | Storage capacity | <85% |
| **Database Query Time** | Avg query execution time | DB performance | <100ms |
| **Cache Hit Rate** | Cache hits / Total reads × 100 | Cache effectiveness | ≥90% |

### 6.3 Integration Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **WhatsApp Success Rate** | Successful / Sent × 100 | WhatsApp API reliability | ≥98% |
| **Email Success Rate** | Successful / Sent × 100 | Email service reliability | ≥99% |
| **PDF Gen Success Rate** | Successful / Attempted × 100 | PDF generation reliability | ≥99.9% |
| **Storage Success Rate** | Successful / Attempted × 100 | Storage write reliability | ≥99.9% |

---

## Part 7: Financial Metrics

### 7.1 Revenue Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Revenue Per Quote** | Total revenue / Quotes sent | Average value per quote | ≥₹1,00,000 |
| **Revenue Per Booking** | Total revenue / Bookings | Average booking value | ≥₹5,00,000 |
| **Conversion Revenue** | Revenue from converted quotes / Total quotes | Revenue efficiency | ≥₹15,000 per quote |
| **Monthly Recurring Revenue** | MRR from subscription contracts | Predictable revenue | Track growth |

### 7.2 Cost Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Cost Per Quote** | Total costs / Quotes sent | Cost to generate quote | <₹50 |
| **Cost Per Booking** | Total costs / Bookings | Cost per conversion | <₹500 |
| **Delivery Cost Per Quote** | Delivery costs / Quotes sent | WhatsApp/Email costs | <₹5 |
| **PDF Storage Cost** | Storage costs / PDFs stored | S3/storage cost | <₹0.01 per PDF |

### 7.3 ROI Metrics

| Metric | Formula | Description | Target |
|--------|---------|-------------|--------|
| **Quote ROI** | (Revenue - Cost) / Cost × 100 | Return on quote investment | ≥500% |
| **Automation ROI** | (Manual cost - Automated cost) / Automated cost | Automation value | ≥300% |
| **Agent Time Savings** | (Manual time - Automated time) / Manual time × 100 | Time efficiency | ≥80% |
| **Annual Savings** | Monthly savings × 12 | Yearly impact | Track |

---

## Part 8: Dashboard Definitions

### 8.1 Executive Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXECUTIVE DASHBOARD                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │   TODAY'S       │  │   THIS WEEK     │  │   THIS MONTH    │           │
│  │   SUMMARY       │  │   SUMMARY       │  │   SUMMARY       │           │
│  │  ─────────────  │  │  ─────────────  │  │  ─────────────  │           │
│  │  Quotes: 156   │  │  Quotes: 1,245  │  │  Quotes: 5,432  │           │
│  │  Bookings: 18  │  │  Bookings: 187   │  │  Bookings: 823  │           │
│  │  Revenue: ₹18L │  │  Revenue: ₹1.8Cr │  │  Revenue: ₹7.8Cr│           │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CONVERSION FUNNEL                                                   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Inquiries (100%)  ████████████████████████████████████  5,432      │   │
│  │  Quotes Sent  (91%) ██████████████████████████████████   4,943      │   │
│  │  Viewed       (72%) ███████████████████████████           3,911      │   │
│  │  Booked       (15%) ██████                                 823       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CONVERSION TREND (Last 30 Days)                                    │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  25% │                                                               │   │
│  │  20% │    ╱╲╱╲    ╱─╲                                              │   │
│  │  15% │  ╱───╲╱──╲╱    ╱─╲    ╱╲                                    │   │
│  │  10% │╱────────────────────╲╱──╲╱─╲╱──╲    ╱╲                      │   │
│  │   5% │                                          ╲╱                  │   │
│  │   0% └────────────────────────────────────────────────────────       │   │
│  │      1  4  7 10 13 16 19 22 25 28                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │  TOP DESTINATIONS           │  │  TOP PERFORMING AGENTS             │ │
│  │  ───────────────────────────  │  │  ────────────────────────────────  │ │
│  │  1. Dubai        234 quotes │  │  1. Agent A    45 quotes, 12 book  │ │
│  │  2. Thailand     189 quotes │  │  2. Agent B    42 quotes, 11 book  │ │
│  │  3. Singapore   156 quotes │  │  3. Agent C    38 quotes,  9 book  │ │
│  │  4. Maldives     98 quotes │  │  4. Agent D    35 quotes,  8 book  │ │
│  │  5. Bali         87 quotes │  │  5. Agent E    33 quotes,  8 book  │ │
│  └─────────────────────────────┘  └─────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Operations Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OPERATIONS DASHBOARD                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SYSTEM HEALTH                                                       │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │ API        │  │ WhatsApp   │  │ Email      │  │ PDF Gen    │    │   │
│  │  │ 99.95%     │  │ 98.2%      │  │ 99.8%      │  │ 99.9%      │    │   │
│  │  │ UP         │  │ OPERATIONAL │  │ OPERATIONAL │  │ OPERATIONAL │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GENERATION PERFORMANCE (Last 24 Hours)                             │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Average: 3.2s  │  P95: 6.8s  │  P99: 9.2s  │  Failed: 0.1%      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DELIVERY PERFORMANCE                                                │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Channel      │ Sent │ Delivered │ Failed │ Rate  │ Avg Time        │   │
│  │  ──────────────┼──────┼───────────┼────────┼───────┼─────────        │   │
│  │  WhatsApp     │ 2,345│ 2,298     │ 47     │ 98.0% │ 28s             │   │
│  │  Email        │ 1,890│ 1,882     │ 8      │ 99.6% │ 45s             │   │
│  │  Portal       │   N/A│ 5,432     │ 0      │ 100%  │ N/A             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUEUE STATUS                                                        │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Current Queue Depth: 23                                             │   │
│  │  Avg Wait Time: 0.8s                                                │   │
│  │  Workers Active: 5/8                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ERROR SUMMARY (Last 24 Hours)                                       │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Template Not Found: 2                                              │   │
│  │  Data Incomplete: 12                                                │   │
│  │  WhatsApp API Error: 47                                             │   │
│  │  PDF Generation Failed: 1                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Quality Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        QUALITY DASHBOARD                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUALITY SCORES                                                       │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ DATA        │  │ PRICING     │  │ CONTENT     │  │ OVERALL     │  │   │
│  │  │ COMPLETENESS│  │ ACCURACY    │  │ QUALITY     │  │ SCORE       │  │   │
│  │  │             │  │             │  │             │  │             │  │   │
│  │  │     99.2%   │  │     99.95%  │  │     98.7%   │  │     99.3%   │  │   │
│  │  │   ████████  │  │   ████████  │  │   ████████  │  │   ████████  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CUSTOMER SATISFACTION                                                │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  NPS Score: 58  │  CSAT: 4.3/5  │  Complaints: 3/1000            │   │
│  │                                                                       │   │
│  │  70 │   ╱╲                                                          │   │
│  │  50 │ ╱──╲╱─╲╱╲╱─╲  ╱──╲                                           │   │
│  │  30 │╱────────────────────────────╲                                │   │
│  │  10 │                    ╲───────────────╲                         │   │
│  │ -10 │                                         ╲                    │   │
│  │ -30 └───────────────────────────────────────────────────────       │   │
│  │     Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REVISION ANALYSIS                                                   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Total Revisions: 145 (12.3%)                                       │   │
│  │                                                                       │   │
│  │  Reason for Revision:                                                │   │
│  │  Price adjustment        42%  ████████████████████████             │   │
│  │  Hotel change            28%  ████████████████                      │   │
│  │  Date modification       18%  ██████████                            │   │
│  │  Activity changes        12%  ██████                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  VALIDATION FAILURES                                                  │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Missing passport       23  ████████████                            │   │
│  │  Invalid GSTIN          12  ██████                                  │   │
│  │  Price mismatch          8   ████                                    │   │
│  │  Template error         5   ██                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 9: Alert Definitions

### 9.1 Critical Alerts

| Alert | Condition | Action | Escalation |
|-------|-----------|--------|------------|
| **System Down** | API error rate >50% for 5 min | Page on-call | Immediate |
| **Queue Backup** | Queue depth >500 for 5 min | Scale up workers | 15 min |
| **Delivery Failure Spike** | Failure rate >10% for 10 min | Check service status | 30 min |
| **Generation Slowdown** | P95 >30s for 10 min | Check resources | 20 min |

### 9.2 Warning Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| **High Error Rate** | Error rate >1% for 15 min | Investigate logs |
| **Low Delivery Rate** | Delivery rate <95% for 1 hour | Check service status |
| **Template Issues** | Template errors >5/hour | Review recent changes |
| **Quality Drop** | Quality score <95% | Review validation rules |

### 9.3 Informational Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| **Daily Summary** | End of day | Email report |
| **Weekly Report** | End of week | Dashboard update |
| **Milestone Reached** | Target achieved | Notification |
| **New Template Created** | Template added | Log entry |

---

## Part 10: Metric Calculations

### 10.1 Conversion Rate Calculation

```typescript
function calculateConversionRate(
  bookings: number,
  quotes: number,
  window: 'day' | 'week' | 'month'
): ConversionMetrics {
  const rate = (bookings / quotes) * 100;

  return {
    rate,
    bookings,
    quotes,
    window,
    benchmark: getBenchmark('conversion', window),
    performance: rate >= getBenchmark('conversion', window) ? 'ABOVE' : 'BELOW'
  };
}

function getBenchmark(metric: string, window: string): number {
  const benchmarks = {
    conversion: { day: 12, week: 14, month: 15 },
    viewRate: { day: 65, week: 70, month: 72 }
  };
  return benchmarks[metric][window];
}
```

### 10.2 NPS Calculation

```typescript
function calculateNPS(responses: NPSResponse[]): NPSResult {
  const promoters = responses.filter(r => r.score >= 9).length;
  const detractors = responses.filter(r => r.score <= 6).length;
  const total = responses.length;

  const nps = ((promoters - detractors) / total) * 100;

  return {
    score: Math.round(nps),
    promoters: (promoters / total) * 100,
    passives: ((total - promoters - detractors) / total) * 100,
    detractors: (detractors / total) * 100,
    totalResponses: total,
    category: nps >= 50 ? 'EXCELLENT' : nps >= 0 ? 'GOOD' : 'POOR'
  };
}
```

### 10.3 ROI Calculation

```typescript
function calculateROI(metrics: FinancialMetrics): ROIResult {
  const { revenue, costs, baselineCosts } = metrics;

  const automationSavings = baselineCosts - costs;
  const netProfit = revenue - costs;
  const roi = (netProfit / costs) * 100;

  return {
    roi: Math.round(roi),
    netProfit,
    automationSavings,
    paybackPeriod: costs / (revenue / 30), // in days
    breakEvenPoint: costs / (revenue / revenue), // ratio
    monthlyROI: (revenue - costs) / costs * 100
  };
}
```

### 10.4 Quality Score Calculation

```typescript
function calculateQualityScore(metrics: QualityMetrics): QualityScore {
  const weights = {
    completeness: 0.3,
    accuracy: 0.4,
    content: 0.2,
    compliance: 0.1
  };

  const score =
    (metrics.completeness * weights.completeness) +
    (metrics.accuracy * weights.accuracy) +
    (metrics.content * weights.content) +
    (metrics.compliance * weights.compliance);

  return {
    overall: Math.round(score * 100) / 100,
    breakdown: {
      completeness: metrics.completeness,
      accuracy: metrics.accuracy,
      content: metrics.content,
      compliance: metrics.compliance
    },
    grade: score >= 99 ? 'A+' : score >= 95 ? 'A' : score >= 90 ? 'B' : 'C'
  };
}
```

---

## Part 11: Reporting Periods

### 11.1 Real-Time Metrics

| Metric | Update Frequency | Retention |
|--------|------------------|-----------|
| Queue depth | 5 seconds | 1 hour |
| API response time | 1 minute | 24 hours |
| Current generation rate | 1 minute | 7 days |
| Active users | 1 minute | 24 hours |

### 11.2 Operational Metrics

| Metric | Update Frequency | Retention |
|--------|------------------|-----------|
| Daily quote volume | End of day | 1 year |
| Daily conversion rate | End of day | 1 year |
| Delivery success rate | Hourly | 90 days |
| Error rates | Hourly | 180 days |

### 11.3 Business Metrics

| Metric | Update Frequency | Retention |
|--------|------------------|-----------|
| Monthly revenue | End of month | 7 years |
| Agent productivity | Weekly | 3 years |
| Customer NPS | Monthly | 5 years |
| Year-over-year growth | End of year | Indefinite |

---

## Part 12: Metric Targets by Tier

### 12.1 Starter Tier

| Metric | Target |
|--------|--------|
| Quotes per month | <500 |
| Generation time | <10 seconds |
| Delivery success rate | ≥95% |
| API uptime | ≥99% |
| Support response | <24 hours |

### 12.2 Professional Tier

| Metric | Target |
|--------|--------|
| Quotes per month | 500-5,000 |
| Generation time | <5 seconds |
| Delivery success rate | ≥98% |
| API uptime | ≥99.5% |
| Support response | <8 hours |

### 12.3 Enterprise Tier

| Metric | Target |
|--------|--------|
| Quotes per month | >5,000 |
| Generation time | <3 seconds |
| Delivery success rate | ≥99.5% |
| API uptime | ≥99.95% |
| Support response | <1 hour |
| Dedicated account manager | Yes |

---

## Summary

This document provides:

1. **Metrics Overview** — Hierarchy, categories, stakeholders
2. **Conversion Metrics** — Funnel metrics, benchmarks, by destination type
3. **Efficiency Metrics** — Generation, agent productivity, delivery efficiency
4. **Quality Metrics** — Accuracy, customer satisfaction, content quality
5. **Engagement Metrics** — View, interaction, channel comparison
6. **Technical Metrics** — System health, infrastructure, integrations
7. **Financial Metrics** — Revenue, cost, ROI calculations
8. **Dashboard Definitions** — Executive, operations, quality dashboards
9. **Alert Definitions** — Critical, warning, informational alerts
10. **Metric Calculations** — Conversion, NPS, ROI, quality score formulas
11. **Reporting Periods** — Real-time, operational, business metrics
12. **Targets by Tier** — Starter, professional, enterprise SLAs

**Series Completion:** This completes the 15-document Output Panel & Bundle Generation Deep Dive series.

---

**Document**: OUTPUT_15_METRICS_DEFINITIONS_COMPLETE.md
**Series**: Output Panel & Bundle Generation Deep Dive
**Status**: ✅ Complete
**Last Updated**: 2026-04-23
