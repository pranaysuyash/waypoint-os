# Supplier Relationship & Contract Intelligence — Master Index

> Exploration of supplier rate management, negotiation intelligence, performance scoring, and contract lifecycle management for Indian travel agencies.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Rate Management](SUPPLIER_01_RATE_MANAGEMENT.md) | Contracted/net/dynamic rates, seasonal tiers, rate comparison, parity monitoring, markup calculator, GST/TCS considerations |
| 02 | [Negotiation Intelligence](SUPPLIER_02_NEGOTIATION.md) | Volume leverage, win-win framework, negotiation playbook, tracker, alternative suppliers, relationship-based negotiation, festival-season advance booking |
| 03 | [Performance Scoring](SUPPLIER_03_PERFORMANCE.md) | Multi-dimensional scoring, dashboard by category, SLA tracking, gold/silver/bronze tiering, supplier rotation, review aggregation |
| 04 | [Contract Lifecycle](SUPPLIER_04_CONTRACT_LIFECYCLE.md) | Template system, e-signature integration, term extraction, compliance verification, GST clauses, TDS, MSME payment timeline, stamp duty |

---

## Key Themes

- **Rates are the foundation of profitability** — Every rupee saved on supplier rates flows directly to margin. Systematic rate management, historical tracking, and parity monitoring prevent margin leakage. The markup calculator ensures we never sell below breakeven while staying competitive.

- **Negotiation is data-driven, not adversarial** — The best supplier relationships are win-win. Volume data, market intelligence, and timing give us leverage. But in India, relationships come first — the negotiation framework must respect cultural norms while still driving better commercial outcomes.

- **Performance is measured, not assumed** — Subjective impressions of supplier quality are unreliable. A structured scoring framework across six dimensions (service quality, responsiveness, issue resolution, price competitiveness, reliability, compliance) creates objective, comparable metrics. Tiering has real consequences: gold suppliers get priority; underperformers get rotated out.

- **Contracts are living documents** — A signed contract is not the end; it is the beginning. Key terms need continuous monitoring: Are rates being charged correctly? Is GST invoiced properly? Are payments within MSME timelines? Is the supplier honoring allotments? Compliance is continuous, not a one-time check.

- **India-specific compliance is non-negotiable** — GST clause verification, TDS deduction at correct sections, MSME 45-day payment timelines, and state-specific stamp duty requirements are legal obligations. Non-compliance carries financial penalties (interest on delayed MSME payments, ITC loss from GST non-filing, TDS penalties). The system must automate these checks.

## Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js + React | Supplier dashboards, rate comparison tables, negotiation tracker UI |
| State Management | Zustand | Rate cache, negotiation state, performance scores |
| Backend API | Next.js API Routes | Rate queries, contract CRUD, compliance checks |
| Database | Supabase (PostgreSQL) | Supplier rates, contracts, performance scores, SLA records |
| Document Storage | Supabase Storage | Contract PDFs, signed documents, rate cards |
| OCR / Extraction | Tesseract.js / Cloud OCR | Contract digitization, rate card parsing |
| E-Signature | Zoho Sign / eMudhra API | Indian DSC and Aadhaar eSign support |
| Rate Monitoring | Custom + RateGain API | Rate parity checks, OTA rate comparison |
| Notifications | In-app + WhatsApp Business API | Rate change alerts, contract expiry reminders |
| Analytics | Supabase + custom dashboards | Performance trends, rate history, compliance reports |
| Review Aggregation | Google Places API + TripAdvisor API | External review collection and sentiment analysis |
| Scheduling | Vercel Cron / pg_cron | Periodic rate checks, compliance scans, SLA monitoring |
| Compliance Engine | Custom rules engine | GST verification, TDS tracking, MSME timeline enforcement |

## Cross-References

### Internal Series

| Series | Relationship |
|--------|-------------|
| **Supplier Integration** (`SUPPLIER_INTEGRATION_*`) | Technical integration with supplier APIs for live rate feeds, booking confirmations, and inventory sync. Rate management depends on real-time integration. |
| **Supplier Settlement** (`SUPPLIER_SETTLE_*`) | Invoice processing, payment execution, and reconciliation. Contract terms (payment terms, TDS, GST) flow into settlement workflows. |
| **Vendor Management** (`VENDOR_*`) | Supplier onboarding, qualification, and relationship management. Negotiation intelligence builds on vendor profiles. Performance scoring extends vendor assessment. |
| **Accommodation Catalog** (`ACCOMMODATION_CATALOG_*`) | Property data, room types, and amenities. Contracted rates and allotments link to catalog entries. |
| **Pricing Engine** (`PRICING_*`) | Dynamic pricing, margin management, and price comparison. Rate management feeds into the pricing engine's markup calculator. |
| **Commission Tracking** (`COMMISSION_*`) | Commission calculation and tracking. Commission-based rates from contracts drive commission workflows. |
| **Finance & Accounting** (`FINANCE_*`) | Journal entries, profit centers, and treasury. TDS deductions, GST reconciliation, and payment compliance link to financial accounting. |
| **Regulatory & Licensing** (`REGULATORY_*`) | IATA compliance, government reporting. GST clause verification and TDS returns tie to regulatory compliance. |
| **Reporting** (`REPORTING_*`) | GST reports, IATA reports, business reports. Contract compliance and performance data feed into reporting dashboards. |
| **Analytics & BI** (`ANALYTICS_*`) | Data warehouse, dashboards, and predictive analytics. Rate trends, performance scores, and negotiation outcomes are analytics inputs. |
| **Risk Management** (`RISK_*`) | Supplier safety, destination intelligence. Underperforming suppliers and contract breaches are risk signals. |
| **Contract Management** (`CONTRACT_*`) | General contract templates, e-signatures, and renewals. This series is specialized for travel supplier contracts. |

### Key Integration Flows

```
                        +---------------------------+
                        |   Supplier Rate Card      |
                        |   (Contracted Rates)      |
                        +-----------+---------------+
                                    |
                                    v
+------------------+    +---------------------------+    +------------------+
|   Supplier       |    |   Rate Management         |    |   Pricing        |
|   Integration    |--->|   (SUPPLIER_01)           |--->|   Engine         |
|   (Live Rates)   |    +---------------------------+    |   (PRICING_*)    |
+------------------+                |                     +------------------+
                                    |
                            +-------+-------+
                            |               |
                            v               v
                  +------------------+  +------------------+
                  |   Rate Parity    |  |   Markup Calc    |
                  |   Monitor        |  |   & Breakeven    |
                  +------------------+  +------------------+
                            |
                            v
                  +---------------------------+
                  |   Negotiation Tracker      |
                  |   (SUPPLIER_02)            |
                  +---------------------------+
                            |
                +-----------+-----------+
                |                       |
                v                       v
      +------------------+    +------------------+
      |   Contract       |    |   Performance    |
      |   Lifecycle      |    |   Scoring        |
      |   (SUPPLIER_04)  |    |   (SUPPLIER_03)  |
      +--------+---------+    +--------+---------+
               |                       |
               v                       v
      +------------------+    +------------------+
      |   Compliance     |    |   Supplier       |
      |   Verification   |    |   Tiering &      |
      |   (GST/TDS/MSME) |    |   Rotation       |
      +--------+---------+    +------------------+
               |
               v
      +---------------------------+
      |   Supplier Settlement     |
      |   (SUPPLIER_SETTLE_*)     |
      +---------------------------+
```

---

## Open Questions for the Series

1. **Build vs. buy for rate parity monitoring?** — Tools like RateGain and AxisRoom exist for Indian market rate monitoring. Is it better to integrate an existing tool or build custom monitoring?

2. **Performance scoring data freshness** — How frequently should performance scores be recalculated? Real-time is ideal but computationally expensive. Daily? Weekly? Different frequencies for different dimensions?

3. **Contract digitization approach** — For existing physical contracts, is it worth digitizing historical contracts or only new contracts going forward? What is the ROI on back-digitization?

4. **MSME compliance automation depth** — How deeply should we integrate with the Udyam portal for real-time MSME verification? Is periodic manual checking sufficient?

5. **E-signature provider selection** — Zoho Sign is cost-effective and popular in India. DocuSign is more established globally. eMudhra is the DSC authority. Which provider (or combination) offers the best balance of cost, compliance, and supplier adoption?

---

*This series is part of the Travel Agency Agent research documentation. Each document is a living artifact — update as implementation decisions are made and new information emerges.*
