# Analytics — Data Warehouse & ETL Architecture

> Research document for data infrastructure, ETL pipelines, and data modeling for analytics.

---

## Key Questions

1. **What data sources feed into analytics, and what's the ingestion strategy?**
2. **Should we use a data warehouse (BigQuery, Snowflake, Redshift) or a simpler OLAP approach?**
3. **What's the data model — star schema, data vault, or something else?**
4. **How do we handle real-time vs. batch analytics?**
5. **What's the cost model for analytics infrastructure at our expected scale?**

---

## Research Areas

### Data Sources

```typescript
interface DataSource {
  sourceId: string;
  name: string;
  type: 'operational_db' | 'event_stream' | 'external_api' | 'file_upload' | 'log';
  recordsPerDay: number;
  freshness: 'real_time' | 'near_real_time' | 'daily' | 'weekly';
  criticality: 'essential' | 'important' | 'nice_to_have';
}

// Key data sources:
// 1. Trip/booking database (PostgreSQL)
// 2. User activity events (frontend interactions)
// 3. Spine run results (processing pipeline)
// 4. Payment transactions
// 5. Supplier interactions (API calls, responses)
// 6. Customer communication logs
// 7. Travel alert feeds
// 8. Commission and financial records
```

### Analytics Data Model (Star Schema)

```typescript
// Fact tables
type FactTable =
  | 'fact_bookings'          // One row per booking event
  | 'fact_payments'          // One row per payment transaction
  | 'fact_commissions'       // One row per commission earned
  | 'fact_spine_runs'        // One row per processing run
  | 'fact_customer_interactions' // One row per interaction
  | 'fact_supplier_performance'  // One row per supplier KPI measurement
  | 'fact_notifications'     // One row per notification sent;

// Dimension tables
type DimensionTable =
  | 'dim_trips'
  | 'dim_customers'
  | 'dim_agents'
  | 'dim_suppliers'
  | 'dim_destinations'
  | 'dim_services'           // Hotels, flights, etc.
  | 'dim_time'
  | 'dim_products'           // Service types/packages
  | 'dim_channels';          // Booking/marketing channels
```

### ETL Strategy

```typescript
interface ETLPipeline {
  pipelineId: string;
  source: DataSource;
  target: string;
  schedule: 'streaming' | 'hourly' | 'daily';
  transformations: Transformation[];
  qualityChecks: QualityCheck[];
  alerting: AlertConfig;
}

type Transformation =
  | 'clean_nulls'
  | 'normalize_currency'
  | 'enrich_geography'
  | 'aggregate_daily'
  | 'deduplicate'
  | 'validate_referential';
```

---

## Open Problems

1. **Real-time vs. batch trade-off** — Operational dashboards need near-real-time data, but ETL is typically batch. CDC (Change Data Capture) can bridge this but adds complexity.

2. **Cost at scale** — BigQuery charges per query. With many dashboards refreshing frequently, costs can escalate. Need caching strategy.

3. **Data freshness SLA** — How fresh does data need to be for different use cases? Executive dashboards can be daily; operational dashboards need hourly.

4. **PII in analytics** — Customer data in the warehouse needs anonymization or access controls. GDPR/DPDP compliance for analytics.

5. **Schema evolution** — As the operational database changes, the analytics schema needs to evolve without breaking existing reports.

---

## Next Steps

- [ ] Evaluate data warehouse options (BigQuery, ClickHouse, DuckDB for smaller scale)
- [ ] Design initial star schema for bookings and payments
- [ ] Research CDC tools for real-time data sync (Debezium, Airbyte)
- [ ] Study cost optimization for cloud data warehouses
- [ ] Design data governance policies for analytics access
