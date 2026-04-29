# Reporting & Analytics — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, need metrics that drive decisions  
**Approach:** Independent analysis — skip vanity metrics, focus on actionable  

---

## 1. The Core Principle: Vanity Metrics Don't Pay Bills**

### Your Reality (Solo Dev)

| What You Care About | What You DON'T Care About |
|-------------------|--------------------------|
| ✅ Revenue this month | ❌ Page views (you're B2B) |
| ✅ Conversion rate (enquiry → booking) | ❌ Session duration |
| ✅ Top vendors (by booking value) | ❌ User growth (it's just you) |
| ✅ Overdue EMI count | ❌ Daily active users |
| ✅ Customer repeat rate | ❌ Churn rate (vanity) |
| ✅ Commission earned this month | ❌ API response times |

**My insight:**  
As solo dev, you need **3 reports**: Revenue, Conversion, Vendor Performance.  
Everything else is **nice-to-have**, build it when bored.

---

## 2. My Lean Report Model (3 Core Reports)**

### Report 1: Revenue Dashboard (Monthly)**

```json
{
  "report_type": "REVENUE_MONTHLY",
  "period": "2026-04",
  
  // Money in
  "total_revenue": "number (float)",  // All bookings finalized
  "revenue_by_currency": { "INR": 1200000, "USD": 5000 },
  "revenue_by_trip_type": { "leisure": 800000, "corporate": 400000 },
  
  // Money out
  "vendor_payouts": "number (float)",  // What you paid vendors
  "commission_earned": "number (float)",  // Your actual profit
  "commission_rate_actual": "number (0.0-100.0)",  // commission % realized
  
  // Trends
  "vs_last_month": "number (float)",  // +12% or -5%
  "vs_same_month_last_year": "number (float)",
  
  // By customer type
  "revenue_by_customer_segment": {
    "VIP": 500000,
    "STANDARD": 600000,
    "CORPORATE": 100000
  }
}
```

**My insight:**  
`commission_earned` is YOUR salary. Track it **weekly**, not monthly.  
`vs_last_month` → if negative 2 months in a row → alarm bells.

---

### Report 2: Conversion Funnel**

```json
{
  "report_type": "CONVERSION_FUNNEL",
  "period": "2026-04",
  
  // Stages (count + value)
  "enquiries_received": { "count": 45, "value": 0 },
  "quotes_sent": { "count": 38, "value": 0 },  // Draft → sent
  "bookings_confirmed": { "count": 22, "value": 1200000 },
  "bookings_cancelled": { "count": 3, "value": 180000 },
  
  // Conversion rates
  "enquiry_to_quote_rate": "number (0.0-1.0)",  // 38/45 = 84%
  "quote_to_booking_rate": "number (0.0-1.0)",  // 22/38 = 58%
  "overall_conversion": "number (0.0-1.0)",  // 22/45 = 49%
  
  // Leakage analysis
  "leakage_points": [
    { "stage": "quote → booking", "lost": 16, "reason": "price_too_high" },
    { "stage": "enquiry → quote", "lost": 7, "reason": "customer_ghosted" }
  ],
  
  // By acquisition source
  "conversion_by_source": {
    "repeat_customer": { "enquiries": 15, "bookings": 12, "rate": 0.80 },
    "inbound_organic": { "enquiries": 20, "bookings": 8, "rate": 0.40 },
    "referral": { "enquiries": 10, "bookings": 7, "rate": 0.70 }
  }
}
```

**My insight:**  
`repeat_customer` conversion = 80% → focus on retention, not just acquisition.  
`inbound_organic` = 40% → SEO is working, but need better follow-up.

---

### Report 3: Vendor Scorecard (Top 10)**

```json
{
  "report_type": "VENDOR_SCORECARD",
  "period": "2026-04",
  "top_vendors": [
    {
      "vendor_id": "vnd-001",
      "company_name": "Breeze Bali Resort",
      "vendor_tier": "PREFERRED",
      "bookings_with_them": 8,
      "total_value": 450000,
      "commission_earned": 45000,
      "average_rating": 4.5,
      "complaint_count": 0,
      "response_time_hours_avg": 2.5,
      "ontime_confirmation_rate": 1.0  // 8/8 on time
    },
    {
      "vendor_id": "vnd-002",
      "company_name": "Phuket Paradise",
      "vendor_tier": "CONTRACTED",
      "bookings_with_them": 5,
      "total_value": 280000,
      "commission_earned": 28000,
      "average_rating": 3.8,  // Lower!
      "complaint_count": 2,  // Issues!
      "response_time_hours_avg": 6.0,  // Slower
      "ontime_confirmation_rate": 0.8  // 4/5 on time
    }
  ],
  
  // Actionable insights
  "recommendations": [
    "Negotiate higher commission with Breeze Bali (top performer)",
    "Warning: Phuket Paradise — 2 complaints, slow response. Review contract."
  ]
}
```

**My insight:**  
`ontime_confirmation_rate` → if <0.8, customer will complain.  
`complaint_count > 0` → add to watchlist, stricter vetting for next booking.

---

## 3. Customer Insights (Who to Focus On)**

### Repeat Customer Analysis**

```json
{
  "report_type": "CUSTOMER_INSIGHTS",
  "period": "2026-04",
  
  "total_customers": 45,
  "new_customers": 30,
  "repeat_customers": 15,
  "repeat_rate": "number (0.0-1.0)",  // 15/45 = 33%
  
  // Lifetime value segments
  "customer_segments": {
    "VIP": { "count": 3, "total_spend": 600000, "avg_per_customer": 200000 },
    "HIGH_VALUE": { "count": 8, "total_spend": 800000, "avg_per_customer": 100000 },
    "STANDARD": { "count": 34, "total_spend": 400000, "avg_per_customer": 11765 }
  },
  
  // At-risk customers (need attention)
  "at_risk_customers": [
    {
      "customer_id": "cust-042",
      "name": "Ravi Kumar",
      "last_booking": "2025-12-15",  // 4+ months ago
      "total_past_spend": 150000,
      "status": "AT_RISK",
      "action": "Send personal WhatsApp: 'Missed you, special offer for Bali?'"
    }
  ],
  
  // Referral sources (what's working?)
  "acquisition_effectiveness": {
    "referral": { "enquiries": 10, "conversion_rate": 0.70, "cost_per_acquisition": 0 },  // Free!
    "inbound_organic": { "enquiries": 20, "conversion_rate": 0.40, "cost_per_acquisition": 500 },  // SEO cost
    "paid_search": { "enquiries": 15, "conversion_rate": 0.30, "cost_per_acquisition": 1200 }  // Google Ads
  }
}
```

**My insight:**  
`referral` = 70% conversion, ₹0 CPA → **double down** on referral program.  
`paid_search` = 30% conversion, ₹1200 CPA → maybe cut budget, improve landing page.

---

## 4. Agent Performance (YOU = Only Agent)**

### Solo Dev Version (Simple Metrics)**

```json
{
  "report_type": "AGENT_PERFORMANCE",
  "agent_id": "you",
  "period": "2026-04",
  
  // Workload
  "enquiries_handled": 45,
  "bookings_created": 22,
  "conversion_rate": 0.49,  // 22/45
  "average_response_time_hours": 3.2,  // You're fast!
  
  // Value
  "total_booking_value": 1200000,
  "commission_earned": 120000,  // Your salary
  "average_booking_value": 54545,
  
  // Quality
  "customer_satisfaction_avg": 4.7,  // Out of 5
  "complaints_received": 1,  // Only 1!
  "complaints_resolved": 1,
  
  // Time tracking
  "total_hours_worked": 160,  // ~8h/day, 20 days
  "revenue_per_hour": 7500,  // 1200000 / 160
  "enquiries_per_hour": 0.28  // 45 / 160
}
```

**My insight:**  
`revenue_per_hour = ₹7500` → if you want ₹1.5L/month, need 20 enquiries/month.  
`complaints_received = 1` → great quality, keep doing what you're doing.

---

## 5. Analytics API (Simple Endpoints)**

### What You'll Actually Use**

```python
# /api/analytics/revenue?period=2026-04
@app.get("/api/analytics/revenue")
async def get_revenue_report(period: str):
    return db.get_revenue_report(period)

# /api/analytics/conversion?period=2026-04
@app.get("/api/analytics/conversion")
async def get_conversion_funnel(period: str):
    return db.get_conversion_funnel(period)

# /api/analytics/vendors?period=2026-04&limit=10
@app.get("/api/analytics/vendors")
async def get_vendor_scorecard(period: str, limit: int = 10):
    return db.get_vendor_scorecard(period, limit)

# /api/analytics/customers?period=2026-04
@app.get("/api/analytics/customers")
async def get_customer_insights(period: str):
    return db.get_customer_insights(period)
```

**My insight:**  
4 endpoints only. Don't build a "full analytics platform".  
Frontend calls these 4, renders charts. Done.

---

## 6. Export for Accountant (Excel/PDF)**

### What You Need for Tax Filing**

```json
{
  "export_type": "TAX_FILING",
  "period": "2026-04",
  "format": "EXCEL | PDF",
  
  // Revenue
  "total_revenue_inr": 1200000,
  "total_revenue_usd": 5000,
  "gst_payable": 180000,  // 18% GST
  "tds_deducted": 12000,  // Section 194J/194C
  
  // Invoices (for CA)
  "invoice_list": [
    {
      "invoice_number": "INV-2026-0042",
      "date": "2026-04-15",
      "customer_name": "Ravi Kumar",
      "amount": 60000,
      "gst": 10800,
      "total": 70800
    }
  ],
  
  // Vendor payouts (for reconciliation)
  "vendor_payouts": [
    {
      "vendor_name": "Breeze Bali Resort",
      "booking_ref": "BK-001",
      "gross_amount": 50000,
      "commission_kept": 5000,
      "amount_paid_to_vendor": 45000
    }
  ]
}
```

**My insight:**  
CA (accountant) wants **Excel, not dashboards**.  
Build one `/api/export/tax-filing?period=2026-04` → generates Excel.

---

## 7. Current State vs Analytics Model**

| Concept | Current Schema | My Lean Model |
|---------|---------------|-------------------|
| Revenue tracking | None | `REVENUE_MONTHLY` report |
| Conversion funnel | None | `CONVERSION_FUNNEL` with leakage points |
| Vendor scorecard | None | `VENDOR_SCORECARD` top 10 |
| Customer insights | None | `CUSTOMER_INSIGHTS` with at-risk |
| Agent performance | None | `AGENT_PERFORMANCE` (YOU only) |
| Export | None | Excel/PDF for tax filing |

---

## 8. Decisions Needed (Simple Answers)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Build analytics UI? | Full dashboard / 3 charts | **3 charts** — revenue, conversion, vendors |
| Real-time vs batch? | Real-time / Daily cron | **Daily cron** — you check once/day |
| Export format? | Excel / PDF / Both | **Excel** — CA wants it |
| Vendor scorecard depth? | Top 10 / Full list | **Top 10** — Pareto principle |
| At-risk alerts? | Yes / No | **YES** — "Ravi hasn't booked in 4 months" |

---

## 9. Next Discussion: Audit & Compliance**

Now that we know **WHAT metrics matter**, we need to discuss: **HOW to stay legal?**

Key questions for next discussion:
1. **GDPR/PII** — customers can ask "delete my data", how to handle?
2. **Consent logs** — customer agreed to "store my passport"?
3. **Data retention** — how long to keep enquiry data? (7 years for tax?)
4. **Audit logs** — who changed what? (for disputes)
5. **Encryption** — PII (passport numbers) must be encrypted at rest
6. **Solo dev reality** — what's the MINIMUM to stay legal?
7. **WhatsApp data** — is it PII? (phone number, messages)

---

**Next file:** `Docs/discussions/audit_and_compliance_2026-04-29.md`
