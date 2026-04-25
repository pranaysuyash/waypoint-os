# Reporting Module — Technical Deep Dive

> Report engine, data warehouse, query builder, and performance optimization

---

## Document Overview

**Series:** Reporting Module | **Document:** 1 of 4 | **Focus:** Technical Architecture

**Related Documents:**
- [02: UX/UI Deep Dive](./REPORTING_02_UX_UI_DEEP_DIVE.md) — Report builder interface
- [03: Export Deep Dive](./REPORTING_03_EXPORT_DEEP_DIVE.md) — Export formats
- [04: Scheduling Deep Dive](./REPORTING_04_SCHEDULING_DEEP_DIVE.md) — Automated reports

---

## Table of Contents

1. [Report Engine Architecture](#1-report-engine-architecture)
2. [Data Warehouse Integration](#2-data-warehouse-integration)
3. [Query Builder System](#3-query-builder-system)
4. [Aggregation & Computation](#4-aggregation--computation)
5. [Caching Strategies](#5-caching-strategies)
6. [Performance Optimization](#6-performance-optimization)
7. [Security & Authorization](#7-security--authorization)

---

## 1. Report Engine Architecture

### 1.1 System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         REPORT ENGINE ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                          API LAYER                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Report CRUD  │  │ Query Exec   │  │ Export Mgmt  │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  └──────────────────────────────┬───────────────────────────────────────┘ │
│                                 │                                          │
│  ┌──────────────────────────────▼───────────────────────────────────────┐ │
│  │                         REPORT ENGINE                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Query Builder│  │ Validator    │  │ Optimizer    │               │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │ │
│  │         │                  │                  │                       │ │
│  │  ┌──────▼──────────────────▼──────────────────▼───────┐             │ │
│  │  │              Execution Engine                        │             │ │
│  │  │  - SQL generation                                  │             │ │
│  │  │  - Result aggregation                              │             │ │
│  │  │  - Format transformation                           │             │ │
│  │  └──────┬──────────────────────────────────────────────┘             │ │
│  └─────────┼──────────────────────────────────────────────────────────┘ │
│            │                                                           │
│  ┌─────────▼─────────────────────────────────────────────────────────┐ │
│  │                        DATA LAYER                                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │ │
│  │  │ Data Warehouse│ │ Cache Layer   │ │ Job Queue    │             │ │
│  │  │ (ClickHouse) │ │ (Redis)       │ │ (Bull/Redis) │             │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Report Definition Model

```typescript
// Report definition schema
interface ReportDefinition {
  // Core metadata
  id: string;
  name: string;
  description?: string;
  createdBy: string;
  createdAt: number;
  updatedAt: number;
  version: number;

  // Data source
  dataSource: DataSourceConfig;

  // Query configuration
  query: QueryConfiguration;

  // Visualization
  visualization?: VisualizationConfig;

  // Scheduling
  schedule?: ScheduleConfig;

  // Access control
  access: AccessControl;

  // Tags for organization
  tags: string[];
}

interface DataSourceConfig {
  type: 'warehouse' | 'database' | 'api' | 'file';
  connection: string; // Connection pool ID or API endpoint
  schema?: string;
  table?: string;
}

interface QueryConfiguration {
  // Fields to select
  fields: FieldConfig[];

  // Filters
  filters: FilterGroup;

  // Grouping
  groupBy?: string[];

  // Sorting
  orderBy?: SortConfig[];

  // Limits
  limit?: number;
  offset?: number;
}

interface FieldConfig {
  id: string;
  name: string;
  type: 'dimension' | 'measure';
  dataType: 'string' | 'number' | 'date' | 'boolean';
  expression?: string; // For computed fields
  aggregation?: 'sum' | 'count' | 'avg' | 'min' | 'max' | 'count_distinct';
  alias?: string;
}
```

### 1.3 Report Engine Implementation

```typescript
// Report engine core
class ReportEngine {
  private queryBuilder: QueryBuilder;
  private executor: QueryExecutor;
  private cache: ReportCache;
  private validator: ReportValidator;

  async executeReport(
    report: ReportDefinition,
    context: ExecutionContext
  ): Promise<ReportResult> {
    // Validate report definition
    const validation = await this.validator.validate(report);
    if (!validation.valid) {
      throw new ReportValidationError(validation.errors);
    }

    // Check authorization
    if (!this.canExecute(report, context.user)) {
      throw new UnauthorizedError('User not authorized for this report');
    }

    // Check cache
    const cacheKey = this.buildCacheKey(report, context);
    const cached = await this.cache.get(cacheKey);
    if (cached && !context.bypassCache) {
      return cached;
    }

    // Build query
    const query = await this.queryBuilder.build(report.query);

    // Execute query
    const data = await this.executor.execute(query, context);

    // Process results
    const result = await this.processResults(data, report);

    // Cache results
    await this.cache.set(cacheKey, result, this.calculateTTL(report));

    return result;
  }

  async executeReportById(
    reportId: string,
    context: ExecutionContext
  ): Promise<ReportResult> {
    const report = await this.loadReport(reportId);
    return this.executeReport(report, context);
  }

  private async processResults(
    data: QueryResult,
    report: ReportDefinition
  ): Promise<ReportResult> {
    // Apply post-processing
    const processed = await this.applyTransformations(data, report);

    // Format for output
    return {
      meta: {
        reportId: report.id,
        reportName: report.name,
        executedAt: Date.now(),
        rowCount: processed.rows.length,
        columnCount: processed.columns.length,
      },
      columns: processed.columns,
      rows: processed.rows,
      aggregations: processed.aggregations,
    };
  }

  private buildCacheKey(report: ReportDefinition, context: ExecutionContext): string {
    return crypto
      .createHash('sha256')
      .update(JSON.stringify({
        reportId: report.id,
        reportVersion: report.version,
        params: context.parameters,
        agencyId: context.agencyId,
      }))
      .digest('hex');
  }

  private calculateTTL(report: ReportDefinition): number {
    // TTL based on data freshness requirements
    const defaultTTL = 300000; // 5 minutes
    const shortTTL = 60000;    // 1 minute
    const longTTL = 3600000;   // 1 hour

    // Real-time data gets short TTL
    if (report.tags.includes('realtime')) {
      return shortTTL;
    }

    // Daily reports get long TTL
    if (report.tags.includes('daily')) {
      return longTTL;
    }

    return defaultTTL;
  }
}
```

---

## 2. Data Warehouse Integration

### 2.1 Warehouse Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         DATA WAREHOUSE LAYERS                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                      PRESENTATION LAYER                               │ │
│  │  - Materialized views for common queries                              │ │
│  │  - Aggregated tables (daily, weekly, monthly)                         │ │
│  │  - Star schema for fast joins                                         │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        INTEGRATION LAYER                              │ │
│  │  - Dimension tables (customer, trip, supplier, etc.)                  │ │
│  │  - Fact tables (bookings, payments, messages)                         │ │
│  │  - Slowly changing dimensions (SCD Type 2)                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                         STAGING LAYER                                 │ │
│  │  - Raw data ingestion                                                 │ │
│  │  - Data quality checks                                                │ │
│  │  - Transformation jobs                                                │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                          SOURCE SYSTEMS                               │ │
│  │  - PostgreSQL (transactional)                                         │ │
│  │  - MongoDB (documents)                                                │ │
│  │  - External APIs (suppliers)                                          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Schema Design

```sql
-- Dimension: Customer
CREATE TABLE dim_customer (
  customer_key BIGINT PRIMARY KEY,
  customer_id VARCHAR(36) UNIQUE,
  agency_id VARCHAR(36) NOT NULL,
  name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  city VARCHAR(100),
  state VARCHAR(100),
  country VARCHAR(100),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  is_active BOOLEAN,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,
  is_current BOOLEAN
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (customer_id, valid_from);

-- Dimension: Trip
CREATE TABLE dim_trip (
  trip_key BIGINT PRIMARY KEY,
  trip_id VARCHAR(36) UNIQUE,
  agency_id VARCHAR(36) NOT NULL,
  customer_key BIGINT,
  destination VARCHAR(255),
  travel_date DATE,
  status VARCHAR(50),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,
  is_current BOOLEAN
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(travel_date)
ORDER BY (trip_id, valid_from);

-- Fact: Bookings
CREATE TABLE fact_booking (
  booking_key BIGINT PRIMARY KEY,
  booking_id VARCHAR(36) UNIQUE,
  agency_id VARCHAR(36) NOT NULL,
  trip_key BIGINT,
  customer_key BIGINT,
  supplier_key BIGINT,
  booking_date DATE,
  travel_date DATE,
  amount DECIMAL(12, 2),
  commission DECIMAL(12, 2),
  margin DECIMAL(12, 2),
  status VARCHAR(50),
  created_at TIMESTAMP
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(booking_date)
ORDER BY (agency_id, booking_date, trip_key);

-- Fact: Payments
CREATE TABLE fact_payment (
  payment_key BIGINT PRIMARY KEY,
  payment_id VARCHAR(36) UNIQUE,
  agency_id VARCHAR(36) NOT NULL,
  booking_key BIGINT,
  customer_key BIGINT,
  payment_date DATE,
  amount DECIMAL(12, 2),
  payment_method VARCHAR(50),
  status VARCHAR(50),
  created_at TIMESTAMP
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(payment_date)
ORDER BY (agency_id, payment_date, booking_key);

-- Aggregated: Daily Summary
CREATE MATERIALIZED VIEW mv_daily_agency_summary
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (agency_id, date)
POPULATE
AS SELECT
  agency_id,
  toDate(booking_date) as date,
  count(*) as booking_count,
  sum(amount) as total_amount,
  sum(commission) as total_commission,
  sum(margin) as total_margin,
  countIf(status = 'confirmed') as confirmed_count,
  countIf(status = 'pending') as pending_count
FROM fact_booking
GROUP BY agency_id, toDate(booking_date);
```

### 2.3 Data Ingestion Pipeline

```typescript
// ETL Pipeline for warehouse updates
class WarehouseIngestionPipeline {
  private sources: DataSource[];
  private transformers: Map<string, DataTransformer>;
  private loader: WarehouseLoader;

  async ingest(sourceType: string, since?: Date): Promise<IngestionResult> {
    const source = this.sources.find(s => s.type === sourceType);
    if (!source) {
      throw new Error(`Unknown source: ${sourceType}`);
    }

    // Extract
    const rawData = await this.extract(source, since);

    // Transform
    const transformedData = await this.transform(sourceType, rawData);

    // Load
    const result = await this.load(sourceType, transformedData);

    return result;
  }

  private async extract(source: DataSource, since?: Date): Promise<RawData[]> {
    const extractor = this.getExtractor(source.type);

    return await extractor.extract({
      connection: source.connection,
      query: source.extractQuery,
      since,
    });
  }

  private async transform(
    sourceType: string,
    data: RawData[]
  ): Promise<TransformedData[]> {
    const transformer = this.transformers.get(sourceType);
    if (!transformer) {
      throw new Error(`No transformer for: ${sourceType}`);
    }

    // Apply transformations
    const results: TransformedData[] = [];

    for (const row of data) {
      // Data type conversion
      const typed = this.convertTypes(row);

      // Validate
      const validated = this.validate(typed);

      // Apply business logic
      const transformed = await transformer.transform(validated);

      results.push(transformed);
    }

    return results;
  }

  private async load(
    sourceType: string,
    data: TransformedData[]
  ): Promise<IngestionResult> {
    return await this.loader.load({
      sourceType,
      data,
      strategy: 'upsert', // Insert new, update existing
    });
  }
}

// Incremental sync scheduler
class WarehouseSyncScheduler {
  private pipeline: WarehouseIngestionPipeline;
  private schedule: Map<string, CronSchedule> = new Map();

  start(): void {
    // Set up schedules for each source
    this.schedule.set('bookings', { pattern: '*/5 * * * *', source: 'bookings' });
    this.schedule.set('payments', { pattern: '*/5 * * * *', source: 'payments' });
    this.schedule.set('customers', { pattern: '0 * * * *', source: 'customers' });

    // Start cron jobs
    for (const [source, config] of this.schedule) {
      cron.schedule(config.pattern, async () => {
        await this.syncSource(source);
      });
    }
  }

  private async syncSource(source: string): Promise<void> {
    const lastSync = await this.getLastSyncTime(source);
    const result = await this.pipeline.ingest(source, lastSync);

    // Update last sync time
    await this.updateLastSyncTime(source, new Date());

    // Log metrics
    logger.info(`Synced ${source}`, {
      recordsProcessed: result.processed,
      recordsInserted: result.inserted,
      recordsUpdated: result.updated,
      errors: result.errors,
    });
  }
}
```

---

## 3. Query Builder System

### 3.1 Query Builder Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          QUERY BUILDER                                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Input: QueryConfiguration                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  {                                                                    │ │
│  │    fields: [                                                          │ │
│  │      { name: 'customer.name', type: 'dimension' },                   │ │
│  │      { name: 'booking.amount', type: 'measure', aggregation: 'sum' } │ │
│  │    ],                                                                 │ │
│  │    filters: {                                                         │ │
│  │      and: [                                                           │ │
│  │        { field: 'booking_date', operator: 'gte', value: '2026-01-01' }│ │
│  │      ]                                                                │ │
│  │    },                                                                 │ │
│  │    groupBy: ['customer.name'],                                        │ │
│  │    orderBy: [{ field: 'sum_amount', direction: 'desc' }]             │ │
│  │  }                                                                    │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │                                         │
│                                 ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                       QUERY BUILDER ENGINE                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Field Parser │  │Filter Builder│  │Join Resolver │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  │         │                  │                  │                       │ │
│  │  ┌──────▼──────────────────▼──────────────────▼───────┐             │ │
│  │  │              SQL Generator                          │             │ │
│  │  └──────┬──────────────────────────────────────────────┘             │ │
│  └─────────┼──────────────────────────────────────────────────────────┘ │
│            │                                                           │
│            ▼                                                           │
│  Output: SQL Query                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  SELECT                                                              │ │
│  │    c.name as customer_name,                                          │ │
│  │    sum(b.amount) as sum_amount                                       │ │
│  │  FROM fact_booking b                                                  │ │
│  │  JOIN dim_customer c ON b.customer_key = c.customer_key              │ │
│  │  WHERE b.booking_date >= '2026-01-01'                                │ │
│  │  GROUP BY c.name                                                      │ │
│  │  ORDER BY sum_amount DESC                                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Query Builder Implementation

```typescript
// Query builder
class QueryBuilder {
  private schemaManager: SchemaManager;
  private sqlGenerator: SQLGenerator;

  async build(config: QueryConfiguration): Promise<ExecutableQuery> {
    // Parse and resolve fields
    const resolvedFields = await this.resolveFields(config.fields);

    // Build SELECT clause
    const selectClause = this.buildSelect(resolvedFields);

    // Build FROM clause with joins
    const fromClause = await this.buildFrom(resolvedFields);

    // Build WHERE clause from filters
    const whereClause = await this.buildWhere(config.filters);

    // Build GROUP BY clause
    const groupByClause = this.buildGroupBy(config.groupBy, resolvedFields);

    // Build ORDER BY clause
    const orderByClause = this.buildOrderBy(config.orderBy, resolvedFields);

    // Build LIMIT/OFFSET
    const limitClause = this.buildLimit(config.limit, config.offset);

    // Combine into full query
    const sql = this.combineClauses({
      select: selectClause,
      from: fromClause,
      where: whereClause,
      groupBy: groupByClause,
      orderBy: orderByClause,
      limit: limitClause,
    });

    return {
      sql,
      params: [],
      fields: resolvedFields,
    };
  }

  private async resolveFields(fields: FieldConfig[]): Promise<ResolvedField[]> {
    const resolved: ResolvedField[] = [];

    for (const field of fields) {
      // Parse field reference (e.g., 'customer.name' → table: customer, column: name)
      const parsed = this.parseFieldReference(field.name);

      // Resolve to actual table and column
      const schema = await this.schemaManager.getSchema(parsed.table);

      resolved.push({
        ...field,
        table: parsed.table,
        column: parsed.column,
        sqlExpression: this.buildFieldExpression(field, schema),
      });
    }

    return resolved;
  }

  private buildFieldExpression(field: FieldConfig, schema: TableSchema): string {
    if (field.expression) {
      return field.expression;
    }

    const columnRef = `${schema.tableName}.${schema.columnName}`;

    if (field.aggregation) {
      return `${field.aggregation}(${columnRef})`;
    }

    return columnRef;
  }

  private parseFieldReference(ref: string): ParsedField {
    const parts = ref.split('.');
    if (parts.length !== 2) {
      throw new Error(`Invalid field reference: ${ref}`);
    }
    return { table: parts[0], column: parts[1] };
  }

  private async buildWhere(filters: FilterGroup): Promise<string> {
    if (!filters || (!filters.and?.length && !filters.or?.length)) {
      return '';
    }

    const conditions: string[] = [];

    for (const filter of filters.and || []) {
      conditions.push(await this.buildFilterCondition(filter));
    }

    return `WHERE ${conditions.join(' AND ')}`;
  }

  private async buildFilterCondition(filter: Filter): Promise<string> {
    const field = this.parseFieldReference(filter.field);
    const schema = await this.schemaManager.getSchema(field.table);

    let operator: string;
    switch (filter.operator) {
      case 'eq': operator = '='; break;
      case 'ne': operator = '!='; break;
      case 'gt': operator = '>'; break;
      case 'gte': operator = '>='; break;
      case 'lt': operator = '<'; break;
      case 'lte': operator = '<='; break;
      case 'like': operator = 'LIKE'; break;
      case 'in': operator = 'IN'; break;
      case 'is_null': operator = 'IS NULL'; break;
      case 'is_not_null': operator = 'IS NOT NULL'; break;
      default: throw new Error(`Unknown operator: ${filter.operator}`);
    }

    const columnRef = `${schema.tableName}.${schema.columnName}`;

    if (filter.operator === 'in') {
      const values = filter.value.map((v: any) => this.formatValue(v));
      return `${columnRef} ${operator} (${values.join(', ')})`;
    }

    if (filter.operator === 'is_null' || filter.operator === 'is_not_null') {
      return `${columnRef} ${operator}`;
    }

    return `${columnRef} ${operator} ${this.formatValue(filter.value)}`;
  }

  private formatValue(value: any): string {
    if (typeof value === 'string') {
      return `'${value.replace(/'/g, "''")}'`;
    }
    if (value instanceof Date) {
      return `'${value.toISOString()}'`;
    }
    if (value === null) {
      return 'NULL';
    }
    return String(value);
  }
}
```

### 3.3 Schema Manager

```typescript
// Schema management for query building
interface TableSchema {
  table: string;          // Logical name
  tableName: string;      // Physical table name
  column: string;         // Logical column name
  columnName: string;     // Physical column name
  dataType: string;
  isDimension: boolean;
  relationships?: Relationship[];
}

interface Relationship {
  type: 'one_to_one' | 'one_to_many' | 'many_to_many';
  toTable: string;
  joinColumn: string;
  foreignKey: string;
}

class SchemaManager {
  private schemas: Map<string, TableSchema[]> = new Map();
  private relationships: Map<string, Relationship[]> = new Map();

  constructor() {
    this.initializeSchemas();
  }

  private initializeSchemas(): void {
    // Define dimension: customer
    this.addSchema('customer', {
      table: 'customer',
      tableName: 'dim_customer',
      column: 'name',
      columnName: 'name',
      dataType: 'String',
      isDimension: true,
    });
    // ... more customer fields

    // Define fact: booking
    this.addSchema('booking', {
      table: 'booking',
      tableName: 'fact_booking',
      column: 'amount',
      columnName: 'amount',
      dataType: 'Decimal',
      isDimension: false,
    });
    // ... more booking fields

    // Define relationships
    this.addRelationship('booking', {
      type: 'many_to_one',
      toTable: 'customer',
      joinColumn: 'customer_key',
      foreignKey: 'customer_key',
    });

    this.addRelationship('booking', {
      type: 'many_to_one',
      toTable: 'trip',
      joinColumn: 'trip_key',
      foreignKey: 'trip_key',
    });
  }

  addSchema(table: string, schema: TableSchema): void {
    if (!this.schemas.has(table)) {
      this.schemas.set(table, []);
    }
    this.schemas.get(table)!.push(schema);
  }

  addRelationship(fromTable: string, relationship: Relationship): void {
    if (!this.relationships.has(fromTable)) {
      this.relationships.set(fromTable, []);
    }
    this.relationships.get(fromTable)!.push(relationship);
  }

  async getSchema(table: string, column?: string): Promise<TableSchema> {
    const schemas = this.schemas.get(table);
    if (!schemas) {
      throw new Error(`Unknown table: ${table}`);
    }

    if (column) {
      const schema = schemas.find(s => s.column === column);
      if (!schema) {
        throw new Error(`Unknown column: ${table}.${column}`);
      }
      return schema;
    }

    return schemas[0];
  }

  async getRelationships(table: string): Promise<Relationship[]> {
    return this.relationships.get(table) || [];
  }

  async findJoinPath(fromTable: string, toTable: string): Promise<JoinPath[]> {
    // BFS to find shortest join path
    const queue: JoinNode[] = [{ table: fromTable, path: [] }];
    const visited = new Set<string>([fromTable]);

    while (queue.length > 0) {
      const { table, path } = queue.shift()!;

      if (table === toTable) {
        return path;
      }

      const relationships = await this.getRelationships(table);
      for (const rel of relationships) {
        if (!visited.has(rel.toTable)) {
          visited.add(rel.toTable);
          queue.push({
            table: rel.toTable,
            path: [...path, { from: table, to: rel.toTable, relationship: rel }],
          });
        }
      }
    }

    throw new Error(`No join path found from ${fromTable} to ${toTable}`);
  }
}
```

---

## 4. Aggregation & Computation

### 4.1 Aggregation Functions

```typescript
// Supported aggregations
type AggregationFunction =
  | 'sum'
  | 'count'
  | 'count_distinct'
  | 'avg'
  | 'min'
  | 'max'
  | 'median'
  | 'percentile'
  | 'stddev'
  | 'variance';

interface AggregationConfig {
  function: AggregationFunction;
  field: string;
  alias?: string;
  params?: any; // For percentile, etc.
}

// Aggregation engine
class AggregationEngine {
  // Map aggregation functions to SQL
  private sqlAggregations: Record<AggregationFunction, (field: string, params?: any) => string> = {
    sum: (field) => `sum(${field})`,
    count: (field) => `count(${field})`,
    count_distinct: (field) => `count(distinct ${field})`,
    avg: (field) => `avg(${field})`,
    min: (field) => `min(${field})`,
    max: (field) => `max(${field})`,
    median: (field) => `median(${field})`,
    percentile: (field, params) => `quantile(${field}, ${params?.percentile || 0.5})`,
    stddev: (field) => `stddev(${field})`,
    variance: (field) => `var(${field})`,
  };

  buildAggregation(config: AggregationConfig, fieldSchema: TableSchema): string {
    const fieldRef = `${fieldSchema.tableName}.${fieldSchema.columnName}`;
    const sqlFunc = this.sqlAggregations[config.function];

    if (!sqlFunc) {
      throw new Error(`Unknown aggregation: ${config.function}`);
    }

    const expression = sqlFunc(fieldRef, config.params);
    const alias = config.alias || `${config.function}_${config.field}`;

    return `${expression} as ${this.quoteIdentifier(alias)}`;
  }

  // Post-query aggregations (for computed metrics)
  async computeDerivedMetrics(
    data: QueryResult,
    metrics: DerivedMetric[]
  ): Promise<QueryResult> {
    const result = { ...data };

    for (const metric of metrics) {
      result.rows = await this.applyMetric(result, metric);
    }

    return result;
  }

  private async applyMetric(
    data: QueryResult,
    metric: DerivedMetric
  ): Promise<any[]> {
    // Apply formula to each row or aggregate
    switch (metric.type) {
      case 'row_formula':
        return data.rows.map(row => this.applyRowFormula(row, metric.expression));

      case 'running_total':
        return this.computeRunningTotal(data, metric);

      case 'moving_average':
        return this.computeMovingAverage(data, metric);

      case 'percent_of_total':
        return this.computePercentOfTotal(data, metric);

      case 'period_over_period':
        return this.computePeriodOverPeriod(data, metric);

      default:
        throw new Error(`Unknown metric type: ${metric.type}`);
    }
  }

  private computeRunningTotal(data: QueryResult, metric: DerivedMetric): any[] {
    let total = 0;
    const valueField = metric.expression.field;

    return data.rows.map(row => {
      total += row[valueField] || 0;
      return { ...row, [metric.alias]: total };
    });
  }

  private computeMovingAverage(data: QueryResult, metric: DeriveMetric): any[] {
    const window = metric.window || 3;
    const valueField = metric.expression.field;
    const result = [];

    for (let i = 0; i < data.rows.length; i++) {
      if (i < window - 1) {
        result.push({ ...data.rows[i], [metric.alias]: null });
        continue;
      }

      let sum = 0;
      for (let j = i - window + 1; j <= i; j++) {
        sum += data.rows[j][valueField] || 0;
      }
      result.push({ ...data.rows[i], [metric.alias]: sum / window });
    }

    return result;
  }
}
```

### 4.2 Time-Series Aggregation

```typescript
// Time-based grouping
interface TimeSeriesConfig {
  granularity: 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';
  timezone?: string;
  fillMissing?: boolean;
}

class TimeSeriesAggregator {
  buildTimeGroup(config: TimeSeriesConfig, dateField: string): string {
    const timezone = config.timezone || 'UTC';

    switch (config.granularity) {
      case 'minute':
        return `toStartOfMinute(toTimeZone(${dateField}, '${timezone}'))`;
      case 'hour':
        return `toStartOfHour(toTimeZone(${dateField}, '${timezone}'))`;
      case 'day':
        return `toDate(toTimeZone(${dateField}, '${timezone}'))`;
      case 'week':
        return `toMonday(toTimeZone(${dateField}, '${timezone}'))`;
      case 'month':
        return `toStartOfMonth(toTimeZone(${dateField}, '${timezone}'))`;
      case 'quarter':
        return `toStartOfQuarter(toTimeZone(${dateField}, '${timezone}'))`;
      case 'year':
        return `toStartOfYear(toTimeZone(${dateField}, '${timezone}'))`;
      default:
        throw new Error(`Unknown granularity: ${config.granularity}`);
    }
  }

  fillMissingPeriods(
    data: QueryResult,
    config: TimeSeriesConfig,
    startDate: Date,
    endDate: Date
  ): QueryResult {
    if (!config.fillMissing) {
      return data;
    }

    const periods = this.generatePeriods(startDate, endDate, config.granularity);
    const dataMap = new Map(data.rows.map(row => [row.period, row]));

    const filledRows = periods.map(period => ({
      period,
      ...dataMap.get(period) || this.createEmptyRow(data.columns),
    }));

    return { ...data, rows: filledRows };
  }

  private generatePeriods(
    startDate: Date,
    endDate: Date,
    granularity: string
  ): string[] {
    const periods: string[] = [];
    const current = new Date(startDate);

    while (current <= endDate) {
      periods.push(current.toISOString().split('T')[0]); // YYYY-MM-DD

      // Advance by granularity
      switch (granularity) {
        case 'day':
          current.setDate(current.getDate() + 1);
          break;
        case 'week':
          current.setDate(current.getDate() + 7);
          break;
        case 'month':
          current.setMonth(current.getMonth() + 1);
          break;
        case 'quarter':
          current.setMonth(current.getMonth() + 3);
          break;
        case 'year':
          current.setFullYear(current.getFullYear() + 1);
          break;
      }
    }

    return periods;
  }

  private createEmptyRow(columns: Column[]): any {
    const row: any = { period: null };
    columns.forEach(col => {
      if (col.type === 'number') {
        row[col.name] = 0;
      } else {
        row[col.name] = null;
      }
    });
    return row;
  }
}
```

---

## 5. Caching Strategies

### 5.1 Multi-Level Cache

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-LEVEL CACHE                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        L1: RESULT CACHE                               │ │
│  │  - Stores: Complete query results                                    │ │
│  │  - TTL: 1-60 minutes                                                 │ │
│  │  - Eviction: LRU                                                     │ │
│  │  - Storage: Redis                                                    │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │ Hit                                     │
│                                 ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        L2: AGGREGATION CACHE                          │ │
│  │  - Stores: Pre-computed aggregations (daily, weekly)                 │ │
│  │  - TTL: 1-24 hours                                                   │ │
│  │  - Eviction: Time-based                                              │ │
│  │  - Storage: Redis / Materialized Views                               │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │ Hit                                     │
│                                 ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        L3: RAW DATA                                  │ │
│  │  - Source: Data warehouse                                            │ │
│  │  - No caching                                                        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Cache Implementation

```typescript
// Report cache manager
class ReportCache {
  private redis: Redis;
  private localCache: LRUCache<string, CachedResult>;

  constructor() {
    this.redis = new Redis(process.env.REDIS_URL);
    this.localCache = new LRUCache({ max: 100, ttl: 30000 }); // 30s local cache
  }

  async get(key: string): Promise<QueryResult | null> {
    // Check local cache first
    const local = this.localCache.get(key);
    if (local) {
      return local.data;
    }

    // Check Redis
    const cached = await this.redis.get(`report:${key}`);
    if (cached) {
      const result = JSON.parse(cached) as CachedResult;
      // Populate local cache
      this.localCache.set(key, result);
      return result.data;
    }

    return null;
  }

  async set(key: string, data: QueryResult, ttl: number): Promise<void> {
    const cached: CachedResult = {
      data,
      cachedAt: Date.now(),
      ttl,
    };

    // Set in local cache
    this.localCache.set(key, cached);

    // Set in Redis
    await this.redis.setex(
      `report:${key}`,
      Math.ceil(ttl / 1000),
      JSON.stringify(cached)
    );
  }

  async invalidate(pattern?: string): Promise<void> {
    if (pattern) {
      // Invalidate matching keys
      const keys = await this.redis.keys(`report:${pattern}`);
      if (keys.length > 0) {
        await this.redis.del(...keys);
      }
    } else {
      // Clear local cache
      this.localCache.clear();
    }
  }

  // Cache warming for popular reports
  async warmCache(reportIds: string[]): Promise<void> {
    for (const reportId of reportIds) {
      const report = await this.loadReport(reportId);
      const key = this.buildCacheKey(report);

      // Check if cached
      const existing = await this.get(key);
      if (existing) {
        continue;
      }

      // Execute and cache
      const engine = new ReportEngine();
      const result = await engine.executeReportById(reportId, {
        bypassCache: true,
      });

      await this.set(key, result, this.calculateTTL(report));
    }
  }
}

// Cache invalidation on data changes
class CacheInvalidator {
  private cache: ReportCache;

  async onBookingCreated(booking: Booking): Promise<void> {
    // Invalidate all reports that depend on booking data
    await this.cache.invalidate('booking:*');
    await this.cache.invalidate('daily_summary:*');
  }

  async onBookingUpdated(booking: Booking): Promise<void> {
    await this.cache.invalidate('booking:*');
  }

  async onPaymentReceived(payment: Payment): Promise<void> {
    await this.cache.invalidate('payment:*');
    await this.cache.invalidate('revenue:*');
  }
}
```

---

## 6. Performance Optimization

### 6.1 Query Optimization

```typescript
// Query optimizer
class QueryOptimizer {
  private schemaManager: SchemaManager;

  async optimize(query: ExecutableQuery): Promise<ExecutableQuery> {
    let optimized = query;

    // Apply optimization rules
    optimized = await this.pushDownPredicates(optimized);
    optimized = await this.reorderJoins(optimized);
    optimized = await this.eliminateUnusedColumns(optimized);
    optimized = await this.applyIndexHints(optimized);
    optimized = await this.partitionPruning(optimized);

    return optimized;
  }

  // Push filters down to the earliest possible point
  private async pushDownPredicates(query: ExecutableQuery): Promise<ExecutableQuery> {
    // Move WHERE conditions before JOINs when possible
    // This reduces the amount of data for the join
    return query;
  }

  // Reorder joins based on table sizes
  private async reorderJoins(query: ExecutableQuery): Promise<ExecutableQuery> {
    // Join smaller tables first
    const tableStats = await this.getTableStatistics(query);
    // Reorder based on row counts
    return query;
  }

  // Remove unused columns from SELECT
  private async eliminateUnusedColumns(query: ExecutableQuery): Promise<ExecutableQuery> {
    // Keep only columns that are used in output, grouping, or sorting
    return query;
  }

  // Add index hints for better query plans
  private async applyIndexHints(query: ExecutableQuery): Promise<ExecutableQuery> {
    // Add hints like: SELECT /* +INDEX(booking_idx) */ ...
    return query;
  }

  // Skip irrelevant partitions
  private async partitionPruning(query: ExecutableQuery): Promise<ExecutableQuery> {
    // If querying last 30 days, only scan those partitions
    return query;
  }

  private async getTableStatistics(query: ExecutableQuery): Promise<TableStats[]> {
    // Get row counts, sizes for tables in query
    return [];
  }
}
```

### 6.2 Materialized Views

```typescript
// Materialized view manager
class MaterializedViewManager {
  private views: Map<string, MaterializedView> = new Map();

  async refresh(viewName: string): Promise<void> {
    const view = this.views.get(viewName);
    if (!view) {
      throw new Error(`Unknown view: ${viewName}`);
    }

    // Create new version
    const tempName = `${viewName}_temp_${Date.now()}`;
    await this.createView(tempName, view.query);

    // Swap atomically
    await this.swapView(viewName, tempName);

    // Update metadata
    view.lastRefreshed = Date.now();
  }

  async refreshAllIncremental(): Promise<void> {
    for (const [name, view] of this.views) {
      if (view.refreshStrategy === 'incremental') {
        await this.refreshIncremental(name);
      }
    }
  }

  private async refreshIncremental(viewName: string): Promise<void> {
    const view = this.views.get(viewName)!;
    const lastRefresh = new Date(view.lastRefreshed);

    // Insert new data
    await this.insertNewData(viewName, view.query, lastRefresh);

    view.lastRefreshed = Date.now();
  }

  // Common materialized views
  async initializeViews(): Promise<void> {
    // Daily agency summary
    this.addView('daily_agency_summary', {
      query: `
        SELECT
          agency_id,
          toDate(booking_date) as date,
          count(*) as booking_count,
          sum(amount) as total_amount,
          sum(commission) as total_commission
        FROM fact_booking
        WHERE booking_date >= today() - INTERVAL 90 DAY
        GROUP BY agency_id, toDate(booking_date)
      `,
      refreshInterval: 3600000, // 1 hour
      refreshStrategy: 'incremental',
    });

    // Customer lifetime value
    this.addView('customer_ltv', {
      query: `
        SELECT
          c.customer_id,
          c.agency_id,
          count(b.booking_key) as total_bookings,
          sum(b.amount) as total_spent,
          sum(b.commission) as total_commission,
          min(b.booking_date) as first_booking,
          max(b.booking_date) as last_booking
        FROM dim_customer c
        LEFT JOIN fact_booking b ON c.customer_key = b.customer_key
        GROUP BY c.customer_id, c.agency_id
      `,
      refreshInterval: 86400000, // 24 hours
      refreshStrategy: 'full',
    });
  }
}
```

---

## 7. Security & Authorization

### 7.1 Row-Level Security

```typescript
// Row-level security for multi-tenant reports
class RowLevelSecurity {
  async applyFilters(
    query: ExecutableQuery,
    user: User
  ): Promise<ExecutableQuery> {
    // Add agency_id filter for all queries
    query = this.addAgencyFilter(query, user.agencyId);

    // Apply role-based filters
    query = await this.applyRoleFilters(query, user);

    // Apply data access restrictions
    query = await this.applyDataRestrictions(query, user);

    return query;
  }

  private addAgencyFilter(query: ExecutableQuery, agencyId: string): ExecutableQuery {
    // Ensure all queries are scoped to the user's agency
    // This is critical for multi-tenant isolation
    return {
      ...query,
      sql: this.injectAgencyFilter(query.sql, agencyId),
    };
  }

  private async applyRoleFilters(query: ExecutableQuery, user: User): Promise<ExecutableQuery> {
    // Agents only see their assigned trips
    if (user.role === 'agent') {
      return this.addAgentFilter(query, user.id);
    }

    // Owners see everything in their agency
    if (user.role === 'owner') {
      return query;
    }

    // Staff may have limited access
    if (user.role === 'staff') {
      return this.applyStaffRestrictions(query, user);
    }

    return query;
  }

  private async applyDataRestrictions(
    query: ExecutableQuery,
    user: User
  ): Promise<ExecutableQuery> {
    // Remove sensitive columns if user doesn't have access
    if (!user.permissions.includes('view_financials')) {
      query = this.removeFinancialColumns(query);
    }

    if (!user.permissions.includes('view_customer_contacts')) {
      query = this.removeContactColumns(query);
    }

    return query;
  }

  private removeFinancialColumns(query: ExecutableQuery): ExecutableQuery {
    // Remove amount, commission, margin from SELECT
    return query;
  }

  private removeContactColumns(query: ExecutableQuery): ExecutableQuery {
    // Remove email, phone from SELECT
    return query;
  }
}
```

### 7.2 Resource Limits

```typescript
// Prevent resource exhaustion
class ResourceLimiter {
  private limits: Map<string, ResourceLimit> = new Map();

  constructor() {
    // Define limits per user tier
    this.limits.set('free', {
      maxQueryTime: 30000,      // 30 seconds
      maxRows: 10000,           // 10k rows
      maxConcurrent: 1,
      maxReportsPerDay: 10,
    });

    this.limits.set('pro', {
      maxQueryTime: 120000,     // 2 minutes
      maxRows: 100000,          // 100k rows
      maxConcurrent: 5,
      maxReportsPerDay: 100,
    });

    this.limits.set('enterprise', {
      maxQueryTime: 300000,     // 5 minutes
      maxRows: 1000000,         // 1M rows
      maxConcurrent: 20,
      maxReportsPerDay: -1,     // unlimited
    });
  }

  async checkLimits(user: User, report: ReportDefinition): Promise<void> {
    const limit = this.limits.get(user.tier) || this.limits.get('free')!;

    // Check concurrent query limit
    const concurrent = await this.getConcurrentQueryCount(user.id);
    if (concurrent >= limit.maxConcurrent) {
      throw new QuotaExceededError('Concurrent query limit reached');
    }

    // Check daily report limit
    if (limit.maxReportsPerDay > 0) {
      const todayReports = await this.getTodayReportCount(user.id);
      if (todayReports >= limit.maxReportsPerDay) {
        throw new QuotaExceededError('Daily report limit reached');
      }
    }

    // Estimate query complexity
    const estimatedRows = await this.estimateRowCount(report);
    if (estimatedRows > limit.maxRows) {
      throw new QuotaExceededError(`Query would return ${estimatedRows} rows, limit is ${limit.maxRows}`);
    }
  }

  private async estimateRowCount(report: ReportDefinition): Promise<number> {
    // Use table statistics to estimate
    // For now, use a heuristic
    return 1000;
  }
}
```

---

## Summary

The report engine provides a flexible, performant system for generating custom reports:

| Component | Purpose |
|-----------|---------|
| **Report Engine** | Orchestrates query execution, caching, post-processing |
| **Data Warehouse** | Columnar storage for fast aggregations |
| **Query Builder** | Transforms visual config to optimized SQL |
| **Aggregation** | Sum, count, avg, time-series, derived metrics |
| **Caching** | Multi-level (L1: results, L2: aggregations) |
| **Security** | Row-level security, column masking, resource limits |

**Key Takeaways:**
- Use columnar storage for analytics workloads
- Cache aggressively at multiple levels
- Optimize queries with predicate pushdown
- Apply row-level security for multi-tenant isolation
- Set resource limits to prevent exhaustion
- Use materialized views for common aggregations

---

**Related:** [02: UX/UI Deep Dive](./REPORTING_02_UX_UI_DEEP_DIVE.md) → Report builder interface and visualization
