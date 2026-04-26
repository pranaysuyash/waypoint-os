# DATA_GOVERNANCE_03: Data Catalog Deep Dive

> Data catalog, metadata management, discovery, and business glossary

---

## Table of Contents

1. [Overview](#overview)
2. [Catalog Schema](#catalog-schema)
3. [Metadata Management](#metadata-management)
4. [Data Dictionary](#data-dictionary)
5. [Business Glossary](#business-glossary)
6. [Data Discovery](#data-discovery)
7. [Tagging & Classification](#tagging--classification)
8. [Data Ownership](#data-ownership)
9. [Search & Navigation](#search--navigation)
10. [Catalog Integration](#catalog-integration)
11. [API Specification](#api-specification)
12. [Testing Scenarios](#testing-scenarios)
13. [Metrics & Monitoring](#metrics--monitoring)

---

## Overview

A data catalog is a organized inventory of data assets that enables data discovery, understanding, and trust. This document covers the catalog schema, metadata management, business glossary, and search capabilities.

### The Data Catalog Challenge

```
┌─────────────────────────────────────────────────────────────┐
│                  Before Data Catalog                        │
├─────────────────────────────────────────────────────────────┤
│  "Where do we store customer emails?"                       │
│  "What does the 'status' field mean in bookings?"           │
│  "Who owns the inventory data?"                             │
│  "Is this data GDPR-relevant?"                              │
│  "What tables have PII?"                                    │
│  ↓                                                           │
│  "Ask around," "check the wiki," "look in the code"         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   After Data Catalog                        │
├─────────────────────────────────────────────────────────────┤
│  Search: "customer email"                                   │
│  Result: customers.email (verified, PII, GDPR)              │
│  Owner: customer-ops@travel-agency.com                      │
│  Lineage: intake → packet → booking → quote                 │
│  Quality Score: 98.5                                        │
│  Tags: contact, primary, verified                           │
└─────────────────────────────────────────────────────────────┘
```

### Catalog Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Catalog                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Assets    │  │  Glossary   │  │   Search    │        │
│  │             │  │             │  │             │        │
│  │ - Tables    │  │ - Terms     │  │ - Full-text │        │
│  │ - Columns   │  │ - Definitions│ │ - Filters   │        │
│  │ - Views     │  │ - Synonyms  │  │ - Facets    │        │
│  │ - Files     │  │ - Acronyms  │  │ - Similar   │        │
│  │ - APIs      │  │ - Abbreviations│ │            │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                           │                                 │
│                           ▼                                 │
│                  ┌───────────────┐                         │
│                  │  Metadata     │                         │
│                  │  Registry     │                         │
│                  └───────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Catalog Schema

### Core Data Model

```typescript
// data-catalog/model/entities.ts

export interface DataAsset {
  id: string;
  name: string;
  qualifiedName: string; // system.schema.table
  type: AssetType;
  description: string;
  owner: string;
  steward: string;
  domain: string;
  system: string;
  attributes: AssetAttributes;
  tags: Tag[];
  classifications: Classification[];
  properties: Record<string, any>;
  metadata: AssetMetadata;
}

export enum AssetType {
  TABLE = 'table',
  VIEW = 'view',
  MATERIALIZED_VIEW = 'materialized_view',
  COLUMN = 'column',
  FILE = 'file',
  API_ENDPOINT = 'api_endpoint',
  MESSAGE_QUEUE = 'message_queue',
  PIPELINE = 'pipeline',
  REPORT = 'report',
  DASHBOARD = 'dashboard'
}

export interface AssetAttributes {
  forType: AssetType;
  schema?: string;
  table?: string;
  column?: ColumnAttributes;
  file?: FileAttributes;
  api?: APIAttributes;
}

export interface ColumnAttributes {
  dataType: string;
  nullable: boolean;
  defaultValue?: any;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  references?: string;
  maxLength?: number;
  enumValues?: any[];
}

export interface FileAttributes {
  format: string;
  size: number;
  encoding: string;
  delimiter?: string;
  headerRow: boolean;
}

export interface APIAttributes {
  method: string;
  endpoint: string;
  authentication: string;
  rateLimit: string;
  version: string;
}

export interface Tag {
  name: string;
  category: string;
  description: string;
  color?: string;
  count?: number;
}

export interface Classification {
  name: string;
  type: 'sensitivity' | 'retention' | 'privacy' | 'domain';
  level: string;
  description: string;
}

export interface AssetMetadata {
  created: Date;
  modified: Date;
  createdBy: string;
  modifiedBy: string;
  version: number;
  verified: boolean;
  verifiedAt?: Date;
  verifiedBy?: string;
  source: 'manual' | 'extracted' | 'imported';
  lastAnalyzed: Date;
  qualityScore?: number;
}

// Catalog entry for a table
export interface TableCatalogEntry extends DataAsset {
  type: AssetType.TABLE;
  attributes: {
    forType: AssetType.TABLE;
    schema: string;
    table: string;
  };
  columns: ColumnCatalogEntry[];
  row_count: number;
  size_bytes: number;
  location: string;
}

// Catalog entry for a column
export interface ColumnCatalogEntry {
  id: string;
  name: string;
  table: string;
  description: string;
  dataType: string;
  nullable: boolean;
  defaultValue?: any;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  references?: string;
  tags: Tag[];
  classifications: Classification[];
  quality: ColumnQualityInfo;
}

export interface ColumnQualityInfo {
  completeness: number; // 0-100
  uniqueness: number; // 0-100
  validity: number; // 0-100
  lastAssessed: Date;
}
```

### Catalog Registry

```typescript
// data-catalog/registry/service.ts

export class DataCatalogRegistry {
  private assets: Map<string, DataAsset> = new Map();
  private index: CatalogIndex;

  constructor() {
    this.index = {
      byName: new Map(),
      byType: new Map(),
      byOwner: new Map(),
      byDomain: new Map(),
      byTag: new Map(),
      byClassification: new Map()
    };
  }

  async registerAsset(asset: DataAsset): Promise<void> {
    // Validate asset
    this.validateAsset(asset);

    // Check for duplicates
    const existing = this.assets.get(asset.qualifiedName);
    if (existing) {
      await this.updateAsset(asset.qualifiedName, asset);
    } else {
      // Add to registry
      this.assets.set(asset.qualifiedName, asset);

      // Update indexes
      this.index.byName.set(asset.name, asset.qualifiedName);
      this.index.byType.set(asset.type, [...(this.index.byType.get(asset.type) || []), asset.qualifiedName]);
      this.index.byOwner.set(asset.owner, [...(this.index.byOwner.get(asset.owner) || []), asset.qualifiedName]);
      this.index.byDomain.set(asset.domain, [...(this.index.byDomain.get(asset.domain) || []), asset.qualifiedName]);

      for (const tag of asset.tags) {
        this.index.byTag.set(tag.name, [...(this.index.byTag.get(tag.name) || []), asset.qualifiedName]);
      }

      for (const classification of asset.classifications) {
        this.index.byClassification.set(classification.name, [...(this.index.byClassification.get(classification.name) || []), asset.qualifiedName]);
      }
    }
  }

  async updateAsset(qualifiedName: string, updates: Partial<DataAsset>): Promise<void> {
    const asset = this.assets.get(qualifiedName);
    if (!asset) throw new Error(`Asset not found: ${qualifiedName}`);

    Object.assign(asset, updates);
    asset.metadata.modified = new Date();
    asset.metadata.version++;
  }

  async getAsset(qualifiedName: string): Promise<DataAsset | undefined> {
    return this.assets.get(qualifiedName);
  }

  async searchAssets(query: CatalogQuery): Promise<DataAsset[]> {
    let results = Array.from(this.assets.values());

    // Filter by type
    if (query.types && query.types.length > 0) {
      results = results.filter(a => query.types!.includes(a.type));
    }

    // Filter by domain
    if (query.domain) {
      results = results.filter(a => a.domain === query.domain);
    }

    // Filter by owner
    if (query.owner) {
      results = results.filter(a => a.owner === query.owner);
    }

    // Filter by tags
    if (query.tags && query.tags.length > 0) {
      results = results.filter(a =>
        query.tags!.some(t => a.tags.some(at => at.name === t))
      );
    }

    // Filter by classification
    if (query.classifications && query.classifications.length > 0) {
      results = results.filter(a =>
        query.classifications!.some(c =>
          a.classifications.some(ac => ac.name === c)
        )
      );
    }

    // Text search
    if (query.search) {
      const searchLower = query.search.toLowerCase();
      results = results.filter(a =>
        a.name.toLowerCase().includes(searchLower) ||
        a.description.toLowerCase().includes(searchLower) ||
        a.qualifiedName.toLowerCase().includes(searchLower)
      );
    }

    // Pagination
    const offset = query.offset || 0;
    const limit = query.limit || 50;

    return results.slice(offset, offset + limit);
  }

  private validateAsset(asset: DataAsset): void {
    if (!asset.name) throw new Error('Asset name is required');
    if (!asset.qualifiedName) throw new Error('Asset qualifiedName is required');
    if (!asset.type) throw new Error('Asset type is required');
    if (!asset.owner) throw new Error('Asset owner is required');
  }

  async deleteAsset(qualifiedName: string): Promise<void> {
    const asset = this.assets.get(qualifiedName);
    if (!asset) return;

    // Remove from indexes
    this.index.byName.delete(asset.name);
    this.index.byType.set(asset.type, (this.index.byType.get(asset.type) || []).filter(n => n !== qualifiedName));
    this.index.byOwner.set(asset.owner, (this.index.byOwner.get(asset.owner) || []).filter(n => n !== qualifiedName));
    this.index.byDomain.set(asset.domain, (this.index.byDomain.get(asset.domain) || []).filter(n => n !== qualifiedName));

    for (const tag of asset.tags) {
      this.index.byTag.set(tag.name, (this.index.byTag.get(tag.name) || []).filter(n => n !== qualifiedName));
    }

    for (const classification of asset.classifications) {
      this.index.byClassification.set(classification.name, (this.index.byClassification.get(classification.name) || []).filter(n => n !== qualifiedName));
    }

    this.assets.delete(qualifiedName);
  }

  getStats(): CatalogStats {
    return {
      totalAssets: this.assets.size,
      byType: this.getAssetCountsByType(),
      byDomain: this.getAssetCountsByDomain(),
      byOwner: this.getAssetCountsByOwner(),
      topTags: this.getTopTags(10),
      verifiedCount: Array.from(this.assets.values()).filter(a => a.metadata.verified).length
    };
  }

  private getAssetCountsByType(): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const asset of this.assets.values()) {
      counts[asset.type] = (counts[asset.type] || 0) + 1;
    }
    return counts;
  }

  private getAssetCountsByDomain(): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const asset of this.assets.values()) {
      counts[asset.domain] = (counts[asset.domain] || 0) + 1;
    }
    return counts;
  }

  private getAssetCountsByOwner(): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const asset of this.assets.values()) {
      counts[asset.owner] = (counts[asset.owner] || 0) + 1;
    }
    return counts;
  }

  private getTopTags(limit: number): Array<{ tag: string; count: number }> {
    const tagCounts: Record<string, number> = {};
    for (const asset of this.assets.values()) {
      for (const tag of asset.tags) {
        tagCounts[tag.name] = (tagCounts[tag.name] || 0) + 1;
      }
    }
    return Object.entries(tagCounts)
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }
}

export interface CatalogQuery {
  search?: string;
  types?: AssetType[];
  domain?: string;
  owner?: string;
  tags?: string[];
  classifications?: string[];
  offset?: number;
  limit?: number;
}

export interface CatalogIndex {
  byName: Map<string, string>;
  byType: Map<AssetType, string[]>;
  byOwner: Map<string, string[]>;
  byDomain: Map<string, string[]>;
  byTag: Map<string, string[]>;
  byClassification: Map<string, string[]>;
}

export interface CatalogStats {
  totalAssets: number;
  byType: Record<string, number>;
  byDomain: Record<string, number>;
  byOwner: Record<string, number>;
  topTags: Array<{ tag: string; count: number }>;
  verifiedCount: number;
}
```

---

## Metadata Management

### Metadata Extraction

```typescript
// data-catalog/metadata/extraction.ts

export class MetadataExtractor {
  async extractFromDatabase(
    connection: DatabaseConnection,
    schema?: string
  ): Promise<DataAsset[]> {
    const assets: DataAsset[] = [];

    // Extract tables
    const tables = await this.listTables(connection, schema);
    for (const table of tables) {
      const tableAsset = await this.extractTableMetadata(connection, table);
      assets.push(tableAsset);
    }

    return assets;
  }

  async extractTableMetadata(
    connection: DatabaseConnection,
    table: string
  ): Promise<DataAsset> {
    const columns = await this.listColumns(connection, table);
    const stats = await this.getTableStats(connection, table);

    return {
      id: `table_${table}_${Date.now()}`,
      name: table,
      qualifiedName: `${connection.database}.${connection.schema || 'public'}.${table}`,
      type: AssetType.TABLE,
      description: '', // Will be enriched later
      owner: this.inferOwner(table),
      steward: '',
      domain: this.inferDomain(table),
      system: connection.system,
      attributes: {
        forType: AssetType.TABLE,
        schema: connection.schema || 'public',
        table
      },
      tags: this.inferTags(table, columns),
      classifications: this.inferClassifications(table, columns),
      properties: {
        row_count: stats.rowCount,
        size_bytes: stats.sizeBytes
      },
      metadata: {
        created: new Date(),
        modified: new Date(),
        createdBy: 'system',
        modifiedBy: 'system',
        version: 1,
        verified: false,
        source: 'extracted',
        lastAnalyzed: new Date()
      }
    };
  }

  async extractFromFile(
    filePath: string
  ): Promise<DataAsset> {
    const stats = await this.getFileStats(filePath);
    const schema = await this.inferFileSchema(filePath);

    return {
      id: `file_${filePath}_${Date.now()}`,
      name: filePath.split('/').pop() || filePath,
      qualifiedName: `file://${filePath}`,
      type: AssetType.FILE,
      description: '',
      owner: this.inferFileOwner(filePath),
      steward: '',
      domain: this.inferDomain(filePath),
      system: 'filesystem',
      attributes: {
        forType: AssetType.FILE,
        file: {
          format: stats.format,
          size: stats.size,
          encoding: stats.encoding,
          delimiter: stats.delimiter,
          headerRow: stats.headerRow
        }
      },
      tags: [],
      classifications: this.inferFileClassifications(filePath),
      properties: {
        columns: schema
      },
      metadata: {
        created: new Date(),
        modified: stats.modified,
        createdBy: 'system',
        modifiedBy: 'system',
        version: 1,
        verified: false,
        source: 'extracted',
        lastAnalyzed: new Date()
      }
    };
  }

  async extractFromAPI(
    openApiSpec: any
  ): Promise<DataAsset[]> {
    const assets: DataAsset[] = [];

    for (const path in openApiSpec.paths) {
      for (const method in openApiSpec.paths[path]) {
        const endpoint = openApiSpec.paths[path][method];

        assets.push({
          id: `api_${method}_${path}_${Date.now()}`,
          name: `${method.toUpperCase()} ${path}`,
          qualifiedName: `api://${openApiSpec.info.title}${path}`,
          type: AssetType.API_ENDPOINT,
          description: endpoint.summary || endpoint.description || '',
          owner: this.inferAPIOwner(openApiSpec, path),
          steward: '',
          domain: this.inferAPIDomain(openApiSpec, path),
          system: openApiSpec.info.title,
          attributes: {
            forType: AssetType.API_ENDPOINT,
            api: {
              method: method.toUpperCase(),
              endpoint: path,
              authentication: this.extractAuthType(endpoint),
              rateLimit: this.extractRateLimit(endpoint),
              version: openApiSpec.info.version
            }
          },
          tags: this.extractAPITags(endpoint),
          classifications: [],
          properties: {
            requestBody: endpoint.requestBody,
            responses: endpoint.responses,
            parameters: endpoint.parameters
          },
          metadata: {
            created: new Date(),
            modified: new Date(),
            createdBy: 'system',
            modifiedBy: 'system',
            version: 1,
            verified: false,
            source: 'extracted',
            lastAnalyzed: new Date()
          }
        });
      }
    }

    return assets;
  }

  private async listTables(
    connection: DatabaseConnection,
    schema?: string
  ): Promise<string[]> {
    // Database-specific implementation
    return [];
  }

  private async listColumns(
    connection: DatabaseConnection,
    table: string
  ): Promise<ColumnCatalogEntry[]> {
    // Database-specific implementation
    return [];
  }

  private async getTableStats(
    connection: DatabaseConnection,
    table: string
  ): Promise<{ rowCount: number; sizeBytes: number }> {
    // Database-specific implementation
    return { rowCount: 0, sizeBytes: 0 };
  }

  private async getFileStats(filePath: string): Promise<any> {
    return {
      format: 'csv',
      size: 0,
      encoding: 'utf-8',
      delimiter: ',',
      headerRow: true,
      modified: new Date()
    };
  }

  private async inferFileSchema(filePath: string): Promise<any[]> {
    return [];
  }

  private inferOwner(name: string): string {
    // Infer owner from naming convention or config
    const ownershipRules: Record<string, string> = {
      customer: 'customer-ops@travel-agency.com',
      booking: 'booking-team@travel-agency.com',
      inventory: 'inventory-team@travel-agency.com',
      payment: 'finance-team@travel-agency.com',
      report: 'analytics-team@travel-agency.com'
    };

    for (const [key, owner] of Object.entries(ownershipRules)) {
      if (name.toLowerCase().includes(key)) {
        return owner;
      }
    }

    return 'data-team@travel-agency.com';
  }

  private inferFileOwner(filePath: string): string {
    return this.inferOwner(filePath);
  }

  private inferDomain(name: string): string {
    const domainRules: Record<string, string> = {
      customer: 'customer',
      booking: 'booking',
      trip: 'booking',
      inventory: 'inventory',
      supplier: 'inventory',
      price: 'inventory',
      payment: 'finance',
      invoice: 'finance',
      report: 'analytics',
      metric: 'analytics',
      log: 'operations'
    };

    for (const [key, domain] of Object.entries(domainRules)) {
      if (name.toLowerCase().includes(key)) {
        return domain;
      }
    }

    return 'general';
  }

  private inferAPIDomain(spec: any, path: string): string {
    return this.inferDomain(path);
  }

  private inferAPIOwner(spec: any, path: string): string {
    return this.inferOwner(path);
  }

  private inferTags(name: string, columns: ColumnCatalogEntry[]): Tag[] {
    const tags: Tag[] = [];

    // Infer tags from column names
    for (const col of columns) {
      if (col.name.includes('email') || col.name.includes('phone')) {
        tags.push({ name: 'contact', category: 'data_type', description: 'Contact information' });
      }
      if (col.name.includes('price') || col.name.includes('amount') || col.name.includes('cost')) {
        tags.push({ name: 'financial', category: 'sensitivity', description: 'Financial data' });
      }
      if (col.name.includes('name') || col.name.includes('address')) {
        tags.push({ name: 'personal', category: 'sensitivity', description: 'Personal information' });
      }
    }

    return [...new Set(tags)];
  }

  private inferClassifications(name: string, columns: ColumnCatalogEntry[]): Classification[] {
    const classifications: Classification[] = [];

    // Check for PII columns
    const piiColumns = columns.filter(c =>
      c.name.toLowerCase().includes('email') ||
      c.name.toLowerCase().includes('phone') ||
      c.name.toLowerCase().includes('ssn') ||
      c.name.toLowerCase().includes('passport') ||
      c.name.toLowerCase().includes('dob') ||
      c.name.toLowerCase().includes('name')
    );

    if (piiColumns.length > 0) {
      classifications.push({
        name: 'PII',
        type: 'privacy',
        level: 'medium',
        description: 'Contains personally identifiable information'
      });
    }

    // Check for financial data
    const financialColumns = columns.filter(c =>
      c.name.toLowerCase().includes('price') ||
      c.name.toLowerCase().includes('amount') ||
      c.name.toLowerCase().includes('cost') ||
      c.name.toLowerCase().includes('payment')
    );

    if (financialColumns.length > 0) {
      classifications.push({
        name: 'FINANCIAL',
        type: 'sensitivity',
        level: 'high',
        description: 'Contains financial data'
      });
    }

    return classifications;
  }

  private inferFileClassifications(filePath: string): Classification[] {
    return [];
  }

  private extractAuthType(endpoint: any): string {
    return 'bearer';
  }

  private extractRateLimit(endpoint: any): string {
    return '1000/hour';
  }

  private extractAPITags(endpoint: any): Tag[] {
    return (endpoint.tags || []).map((t: string) => ({
      name: t,
      category: 'api',
      description: t
    }));
  }
}

export interface DatabaseConnection {
  system: string;
  host: string;
  port: number;
  database: string;
  schema?: string;
  credentials: string;
}
```

### Metadata Enrichment

```typescript
// data-catalog/metadata/enrichment.ts

export class MetadataEnricher {
  private glossary: BusinessGlossary;
  private lineage: LineageGraph;

  constructor(glossary: BusinessGlossary, lineage: LineageGraph) {
    this.glossary = glossary;
    this.lineage = lineage;
  }

  async enrichAsset(asset: DataAsset): Promise<DataAsset> {
    let enriched = { ...asset };

    // Enrich with glossary terms
    enriched = await this.enrichWithGlossary(enriched);

    // Enrich with lineage info
    enriched = await this.enrichWithLineage(enriched);

    // Enrich with quality scores
    enriched = await this.enrichWithQuality(enriched);

    // Enrich with usage stats
    enriched = await this.enrichWithUsage(enriched);

    // Enrich with relationships
    enriched = await this.enrichWithRelationships(enriched);

    return enriched;
  }

  private async enrichWithGlossary(asset: DataAsset): Promise<DataAsset> {
    const terms = await this.glossary.findRelatedTerms(asset.name, asset.description);

    // Add relevant tags from glossary
    const newTags = terms
      .filter(t => t.relevance > 0.7)
      .map(t => ({
        name: t.name,
        category: 'glossary',
        description: t.definition
      }));

    asset.tags = [...asset.tags, ...newTags];

    // Update description if more detailed one exists in glossary
    const primaryTerm = terms.find(t => t.relevance > 0.9);
    if (primaryTerm && primaryTerm.definition.length > asset.description.length) {
      asset.description = primaryTerm.definition;
    }

    return asset;
  }

  private async enrichWithLineage(asset: DataAsset): Promise<DataAsset> {
    // Find upstream and downstream assets
    const upstream = this.lineage.edges.filter(e => e.to === asset.id);
    const downstream = this.lineage.edges.filter(e => e.from === asset.id);

    asset.properties = {
      ...asset.properties,
      upstreamCount: upstream.length,
      downstreamCount: downstream.length,
      upstreamSources: upstream.map(e => e.from),
      downstreamTargets: downstream.map(e => e.to)
    };

    return asset;
  }

  private async enrichWithQuality(asset: DataAsset): Promise<DataAsset> {
    // Get quality score from quality monitoring service
    const qualityScore = await this.getQualityScore(asset.qualifiedName);

    if (qualityScore !== undefined) {
      asset.metadata.qualityScore = qualityScore;
    }

    return asset;
  }

  private async enrichWithUsage(asset: DataAsset): Promise<DataAsset> {
    // Get usage statistics
    const usage = await this.getUsageStats(asset.qualifiedName);

    asset.properties = {
      ...asset.properties,
      usage: {
        queryCount: usage.queryCount,
        lastAccessed: usage.lastAccessed,
        topUsers: usage.topUsers
      }
    };

    return asset;
  }

  private async enrichWithRelationships(asset: DataAsset): Promise<DataAsset> {
    if (asset.type === AssetType.TABLE) {
      // Find related tables through foreign keys
      const relationships = await this.findTableRelationships(asset);

      asset.properties = {
        ...asset.properties,
        relationships
      };
    }

    return asset;
  }

  private async getQualityScore(qualifiedName: string): Promise<number | undefined> {
    // Query quality monitoring service
    return undefined;
  }

  private async getUsageStats(qualifiedName: string): Promise<any> {
    return {
      queryCount: 0,
      lastAccessed: new Date(),
      topUsers: []
    };
  }

  private async findTableRelationships(asset: DataAsset): Promise<any[]> {
    return [];
  }
}
```

---

## Data Dictionary

### Data Dictionary Service

```typescript
// data-catalog/dictionary/service.ts

export interface DataDictionary {
  tables: DictionaryTable[];
  columns: DictionaryColumn[];
  relationships: Relationship[];
  enums: EnumDefinition[];
}

export interface DictionaryTable {
  name: string;
  qualifiedName: string;
  description: string;
  owner: string;
  domain: string;
  rowCount: number;
  columns: string[];
  tags: string[];
  classifications: string[];
}

export interface DictionaryColumn {
  name: string;
  table: string;
  qualifiedName: string;
  dataType: string;
  nullable: boolean;
  defaultValue?: any;
  description: string;
  businessName: string;
  businessDefinition: string;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  references?: string;
  enumValues?: any[];
  sampleValues: any[];
  qualityScore: number;
}

export interface Relationship {
  fromTable: string;
  fromColumn: string;
  toTable: string;
  toColumn: string;
  type: 'one_to_one' | 'one_to_many' | 'many_to_many';
  description: string;
}

export interface EnumDefinition {
  name: string;
  description: string;
  values: EnumValue[];
}

export interface EnumValue {
  value: string;
  label: string;
  description: string;
  isActive: boolean;
}

export class DataDictionaryService {
  private dictionary: DataDictionary;

  constructor() {
    this.dictionary = {
      tables: [],
      columns: [],
      relationships: [],
      enums: []
    };
  }

  async buildDictionary(assets: DataAsset[]): Promise<DataDictionary> {
    const tables: DictionaryTable[] = [];
    const columns: DictionaryColumn[] = [];
    const relationships: Relationship[] = [];

    for (const asset of assets) {
      if (asset.type === AssetType.TABLE) {
        const dictTable = this.toDictionaryTable(asset);
        tables.push(dictTable);

        if (asset.properties.columns) {
          for (const col of asset.properties.columns) {
            columns.push(this.toDictionaryColumn(asset, col));
          }
        }

        // Extract relationships from foreign keys
        const tableRelationships = this.extractRelationships(asset);
        relationships.push(...tableRelationships);
      }
    }

    this.dictionary = {
      tables,
      columns,
      relationships,
      enums: await this.buildEnums(columns)
    };

    return this.dictionary;
  }

  async getTableDefinition(tableName: string): Promise<DictionaryTable | undefined> {
    return this.dictionary.tables.find(t => t.name === tableName);
  }

  async getColumnDefinition(columnName: string, tableName?: string): Promise<DictionaryColumn | undefined> {
    if (tableName) {
      return this.dictionary.columns.find(c => c.name === columnName && c.table === tableName);
    }
    return this.dictionary.columns.find(c => c.name === columnName);
  }

  async getRelationships(tableName: string): Promise<Relationship[]> {
    return this.dictionary.relationships.filter(
      r => r.fromTable === tableName || r.toTable === tableName
    );
  }

  async searchDictionary(query: string): Promise<DictionarySearchResult> {
    const searchLower = query.toLowerCase();

    const matchingTables = this.dictionary.tables.filter(t =>
      t.name.toLowerCase().includes(searchLower) ||
      t.description.toLowerCase().includes(searchLower)
    );

    const matchingColumns = this.dictionary.columns.filter(c =>
      c.name.toLowerCase().includes(searchLower) ||
      c.businessName.toLowerCase().includes(searchLower) ||
      c.businessDefinition.toLowerCase().includes(searchLower)
    );

    return {
      query,
      tables: matchingTables,
      columns: matchingColumns,
      totalMatches: matchingTables.length + matchingColumns.length
    };
  }

  private toDictionaryTable(asset: DataAsset): DictionaryTable {
    return {
      name: asset.name,
      qualifiedName: asset.qualifiedName,
      description: asset.description,
      owner: asset.owner,
      domain: asset.domain,
      rowCount: asset.properties.row_count || 0,
      columns: asset.properties.columns?.map((c: any) => c.name) || [],
      tags: asset.tags.map(t => t.name),
      classifications: asset.classifications.map(c => c.name)
    };
  }

  private toDictionaryColumn(asset: DataAsset, col: any): DictionaryColumn {
    return {
      name: col.name,
      table: asset.name,
      qualifiedName: `${asset.qualifiedName}.${col.name}`,
      dataType: col.dataType,
      nullable: col.nullable,
      defaultValue: col.defaultValue,
      description: col.description || '',
      businessName: this.toBusinessName(col.name),
      businessDefinition: col.description || this.generateBusinessDefinition(col),
      isPrimaryKey: col.isPrimaryKey || false,
      isForeignKey: col.isForeignKey || false,
      references: col.references,
      enumValues: col.enumValues,
      sampleValues: col.sampleValues || [],
      qualityScore: col.quality?.overallScore || 100
    };
  }

  private toBusinessName(columnName: string): string {
    // Convert snake_case to Title Case
    return columnName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  private generateBusinessDefinition(col: any): string {
    if (col.name.includes('id')) {
      return 'Unique identifier for the record';
    }
    if (col.name.includes('name')) {
      return 'Name of the entity';
    }
    if (col.name.includes('email')) {
      return 'Email address for communication';
    }
    if (col.name.includes('created_at') || col.name.includes('createdAt')) {
      return 'Timestamp when the record was created';
    }
    if (col.name.includes('updated_at') || col.name.includes('updatedAt')) {
      return 'Timestamp when the record was last updated';
    }
    return `The ${this.toBusinessName(col.name)} field`;
  }

  private extractRelationships(asset: DataAsset): Relationship[] {
    const relationships: Relationship[] = [];

    if (asset.properties.columns) {
      for (const col of asset.properties.columns) {
        if (col.isForeignKey && col.references) {
          const [refTable, refColumn] = col.references.split('.');
          relationships.push({
            fromTable: asset.name,
            fromColumn: col.name,
            toTable: refTable,
            toColumn: refColumn || 'id',
            type: 'many_to_one',
            description: `Reference to ${refTable}`
          });
        }
      }
    }

    return relationships;
  }

  private async buildEnums(columns: DictionaryColumn[]): Promise<EnumDefinition[]> {
    const enumMap = new Map<string, EnumDefinition>();

    for (const col of columns) {
      if (col.enumValues && col.enumValues.length > 0) {
        const enumName = `${col.table}_${col.name}`.toUpperCase();
        if (!enumMap.has(enumName)) {
          enumMap.set(enumName, {
            name: enumName,
            description: `Possible values for ${col.businessName}`,
            values: col.enumValues.map((v: any) => ({
              value: v,
              label: this.toBusinessName(v.toString()),
              description: '',
              isActive: true
            }))
          });
        }
      }
    }

    return Array.from(enumMap.values());
  }
}

export interface DictionarySearchResult {
  query: string;
  tables: DictionaryTable[];
  columns: DictionaryColumn[];
  totalMatches: number;
}
```

---

## Business Glossary

### Glossary Model

```typescript
// data-catalog/glossary/model.ts

export interface BusinessGlossary {
  terms: GlossaryTerm[];
  categories: GlossaryCategory[];
  acronyms: AcronymDefinition[];
  abbreviations: AbbreviationDefinition[];
}

export interface GlossaryTerm {
  id: string;
  name: string;
  displayName: string;
  definition: string;
  extendedDefinition?: string;
  examples: string[];
  synonyms: string[];
  relatedTerms: string[];
  category: string;
  domain: string;
  steward: string;
  status: 'draft' | 'approved' | 'deprecated';
  sources: TermSource[];
  tags: string[];
  metadata: TermMetadata;
}

export interface GlossaryCategory {
  id: string;
  name: string;
  description: string;
  parentCategory?: string;
  terms: string[];
}

export interface AcronymDefinition {
  acronym: string;
  fullName: string;
  definition: string;
  context: string;
}

export interface AbbreviationDefinition {
  abbreviation: string;
  fullName: string;
  definition: string;
}

export interface TermSource {
  name: string;
  url?: string;
  type: 'document' | 'policy' | 'system' | 'external';
}

export interface TermMetadata {
  created: Date;
  modified: Date;
  createdBy: string;
  modifiedBy: string;
  version: number;
  lastReviewed: Date;
}

// Sample business terms
export const travelAgencyGlossaryTerms: GlossaryTerm[] = [
  {
    id: 'GT_CUSTOMER',
    name: 'customer',
    displayName: 'Customer',
    definition: 'An individual or organization that has expressed interest in or purchased travel services from the agency.',
    extendedDefinition: 'Customers may be at various stages: prospects (inquiring), leads (qualified), or active (have booked). A customer record includes contact information, preferences, and travel history.',
    examples: [
      'A person sending an email inquiry about a Bali trip',
      'A repeat customer who has booked 3 family vacations'
    ],
    synonyms: ['client', 'traveler', 'guest', 'prospect'],
    relatedTerms: ['booking', 'inquiry', 'lead'],
    category: 'Parties',
    domain: 'Customer',
    steward: 'customer-ops@travel-agency.com',
    status: 'approved',
    sources: [
      { name: 'Customer Management Policy', type: 'policy' }
    ],
    tags: ['core', 'party'],
    metadata: {
      created: new Date('2026-01-01'),
      modified: new Date('2026-03-15'),
      createdBy: 'data-team',
      modifiedBy: 'customer-ops',
      version: 2,
      lastReviewed: new Date('2026-03-01')
    }
  },
  {
    id: 'GT_BOOKING',
    name: 'booking',
    displayName: 'Booking',
    definition: 'A confirmed reservation for travel services, including flights, accommodations, and activities.',
    extendedDefinition: 'A booking represents a commitment between a customer and the agency. It becomes confirmed after initial payment or deposit. Bookings progress through stages: inquiry → quote → booking → confirmed → traveled.',
    examples: [
      'A confirmed 7-day Bali package for 2 adults',
      'A flight-only booking for Delhi to Mumbai'
    ],
    synonyms: ['reservation', 'itinerary_booking'],
    relatedTerms: ['customer', 'quote', 'invoice', 'trip'],
    category: 'Transactions',
    domain: 'Booking',
    steward: 'booking-team@travel-agency.com',
    status: 'approved',
    sources: [
      { name: 'Booking Process Documentation', type: 'document' }
    ],
    tags: ['core', 'transaction'],
    metadata: {
      created: new Date('2026-01-01'),
      modified: new Date('2026-02-10'),
      createdBy: 'data-team',
      modifiedBy: 'booking-team',
      version: 1,
      lastReviewed: new Date('2026-02-01')
    }
  },
  {
    id: 'GT_QUOTE',
    name: 'quote',
    displayName: 'Quote',
    definition: 'A formal price offer presented to a customer for proposed travel services.',
    extendedDefinition: 'Quotes are generated after understanding customer requirements and include detailed pricing for flights, hotels, transfers, and activities. Quotes are valid for a specified period (typically 3-7 days) and may change based on availability.',
    examples: [
      'A ₹1,50,000 quote for 5-day Thailand trip',
      'A revised quote after upgrading hotel category'
    ],
    synonyms: ['proposal', 'price_quote', 'estimate'],
    relatedTerms: ['inquiry', 'booking', 'invoice'],
    category: 'Transactions',
    domain: 'Booking',
    steward: 'booking-team@travel-agency.com',
    status: 'approved',
    sources: [],
    tags: ['core', 'commercial'],
    metadata: {
      created: new Date('2026-01-01'),
      modified: new Date('2026-01-15'),
      createdBy: 'data-team',
      modifiedBy: 'booking-team',
      version: 1,
      lastReviewed: new Date('2026-01-10')
    }
  },
  {
    id: 'GT_PACKET',
    name: 'packet',
    displayName: 'Packet',
    definition: 'A structured representation of a customer inquiry containing extracted travel requirements and preferences.',
    extendedDefinition: 'Packets are created from unstructured customer communications (emails, messages). They contain structured data like destination, travel dates, number of travelers, budget, and special requirements. Packets are the primary input for quote generation.',
    examples: [
      'A packet extracted from an email about a honeymoon trip to Maldives',
      'A packet from a WhatsApp message about family vacation'
    ],
    synonyms: ['inquiry_packet', 'structured_inquiry'],
    relatedTerms: ['inquiry', 'quote', 'extraction'],
    category: 'Data',
    domain: 'Intake',
    steward: 'data-team@travel-agency.com',
    status: 'approved',
    sources: [
      { name: 'Intake System Documentation', type: 'document' }
    ],
    tags: ['core', 'internal'],
    metadata: {
      created: new Date('2026-01-01'),
      modified: new Date('2026-04-01'),
      createdBy: 'data-team',
      modifiedBy: 'data-team',
      version: 3,
      lastReviewed: new Date('2026-04-01')
    }
  },
  {
    id: 'GT_SUPPLIER',
    name: 'supplier',
    displayName: 'Supplier',
    definition: 'External entities that provide travel services sold by the agency.',
    extendedDefinition: 'Suppliers include airlines, hotels, tour operators, transport services, and activity providers. Each supplier has specific rates, commission structures, and booking requirements.',
    examples: [
      'IndiGo (airline)',
      'Marriott (hotel chain)',
      'SOTC (tour operator)'
    ],
    synonyms: ['vendor', 'provider', 'service_provider'],
    relatedTerms: ['inventory', 'commission', 'booking'],
    category: 'Parties',
    domain: 'Inventory',
    steward: 'inventory-team@travel-agency.com',
    status: 'approved',
    sources: [],
    tags: ['core', 'party'],
    metadata: {
      created: new Date('2026-01-01'),
      modified: new Date('2026-02-20'),
      createdBy: 'data-team',
      modifiedBy: 'inventory-team',
      version: 1,
      lastReviewed: new Date('2026-02-15')
    }
  }
];

export const travelAgencyAcronyms: AcronymDefinition[] = [
  {
    acronym: 'PII',
    fullName: 'Personally Identifiable Information',
    definition: 'Information that can be used to identify an individual',
    context: 'Data privacy and security'
  },
  {
    acronym: 'GDPR',
    fullName: 'General Data Protection Regulation',
    definition: 'EU regulation on data protection and privacy',
    context: 'Compliance'
  },
  {
    acronym: 'PNR',
    fullName: 'Passenger Name Record',
    definition: 'Record in airline reservation system containing passenger itinerary',
    context: 'Airline bookings'
  },
  {
    acronym: 'FIT',
    fullName: 'Free Independent Traveler',
    definition: 'Individual traveler not part of a group tour',
    context: 'Customer type'
  },
  {
    acronym: 'GIT',
    fullName: 'Group Inclusive Tour',
    definition: 'Group travel package with fixed itinerary',
    context: 'Product type'
  },
  {
    acronym: 'MICE',
    fullName: 'Meetings, Incentives, Conferences, and Exhibitions',
    definition: 'Business travel segment',
    context: 'Market segment'
  },
  {
    acronym: 'B2B',
    fullName: 'Business to Business',
    definition: 'Transactions between businesses',
    context: 'Sales channel'
  },
  {
    acronym: 'B2C',
    fullName: 'Business to Consumer',
    definition: 'Direct sales to individual customers',
    context: 'Sales channel'
  }
];
```

### Glossary Service

```typescript
// data-catalog/glossary/service.ts

export class BusinessGlossaryService {
  private terms: Map<string, GlossaryTerm> = new Map();
  private acronyms: Map<string, AcronymDefinition> = new Map();
  private abbreviations: Map<string, AbbreviationDefinition> = new Map();
  private categoryIndex: Map<string, string[]> = new Map();

  constructor() {
    this.initializeGlossary();
  }

  private initializeGlossary(): void {
    for (const term of travelAgencyGlossaryTerms) {
      this.terms.set(term.name, term);
      this.terms.set(term.displayName, term);
      for (const synonym of term.synonyms) {
        this.terms.set(synonym, term);
      }

      // Index by category
      if (!this.categoryIndex.has(term.category)) {
        this.categoryIndex.set(term.category, []);
      }
      this.categoryIndex.get(term.category)!.push(term.name);
    }

    for (const acronym of travelAgencyAcronyms) {
      this.acronyms.set(acronym.acronym, acronym);
    }
  }

  async getTerm(termName: string): Promise<GlossaryTerm | undefined> {
    return this.terms.get(termName);
  }

  async searchTerms(query: string): Promise<GlossaryTerm[]> {
    const searchLower = query.toLowerCase();
    const results: GlossaryTerm[] = [];

    for (const [name, term] of this.terms) {
      if (name.toLowerCase().includes(searchLower) ||
          term.displayName.toLowerCase().includes(searchLower) ||
          term.definition.toLowerCase().includes(searchLower) ||
          term.synonyms.some(s => s.toLowerCase().includes(searchLower))) {
        if (!results.includes(term)) {
          results.push(term);
        }
      }
    }

    return results;
  }

  async findRelatedTerms(termName: string, maxResults = 5): Promise<Array<{ term: GlossaryTerm; relevance: number }>> {
    const term = await this.getTerm(termName);
    if (!term) return [];

    const related: Array<{ term: GlossaryTerm; relevance: number }> = [];

    // Direct related terms
    for (const relatedName of term.relatedTerms) {
      const relatedTerm = await this.getTerm(relatedName);
      if (relatedTerm) {
        related.push({ term: relatedTerm, relevance: 1.0 });
      }
    }

    // Find terms in same domain
    for (const [name, t] of this.terms) {
      if (t.domain === term.domain && t.name !== term.name && !term.relatedTerms.includes(t.name)) {
        related.push({ term: t, relevance: 0.7 });
      }
    }

    // Find terms with similar tags
    for (const [name, t] of this.terms) {
      if (t.name === term.name) continue;
      const commonTags = t.tags.filter(tag => term.tags.includes(tag));
      if (commonTags.length > 0) {
        const relevance = commonTags.length / Math.max(term.tags.length, t.tags.length);
        if (!related.find(r => r.term.name === t.name)) {
          related.push({ term: t, relevance });
        }
      }
    }

    return related
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, maxResults);
  }

  async getAcronym(acronym: string): Promise<AcronymDefinition | undefined> {
    return this.acronyms.get(acronym.toUpperCase());
  }

  async getTermsByCategory(category: string): Promise<GlossaryTerm[]> {
    const termNames = this.categoryIndex.get(category) || [];
    const terms: GlossaryTerm[] = [];

    for (const name of termNames) {
      const term = await this.getTerm(name);
      if (term) {
        terms.push(term);
      }
    }

    return terms;
  }

  async getTermsByDomain(domain: string): Promise<GlossaryTerm[]> {
    const terms: GlossaryTerm[] = [];

    for (const term of this.terms.values()) {
      if (term.domain === domain && !terms.includes(term)) {
        terms.push(term);
      }
    }

    return terms;
  }

  async addTerm(term: GlossaryTerm): Promise<void> {
    this.terms.set(term.name, term);
    this.terms.set(term.displayName, term);
  }

  async updateTerm(termName: string, updates: Partial<GlossaryTerm>): Promise<void> {
    const term = this.terms.get(termName);
    if (!term) throw new Error(`Term not found: ${termName}`);

    Object.assign(term, updates);
    term.metadata.modified = new Date();
    term.metadata.version++;
  }
}
```

---

## Data Discovery

### Search Service

```typescript
// data-catalog/discovery/search.ts

export interface SearchQuery {
  query: string;
  filters: SearchFilters;
  pagination: Pagination;
}

export interface SearchFilters {
  assetTypes?: AssetType[];
  domains?: string[];
  owners?: string[];
  tags?: string[];
  classifications?: string[];
  dateRange?: {
    from: Date;
    to: Date;
  };
  qualityScore?: {
    min: number;
    max: number;
  };
}

export interface Pagination {
  offset: number;
  limit: number;
}

export interface SearchResult {
  assets: SearchAssetResult[];
  total: number;
  facets: SearchFacets[];
  suggestions: string[];
  queryTime: number;
}

export interface SearchAssetResult {
  asset: DataAsset;
  relevance: number;
  highlights: string[];
}

export interface SearchFacets {
  name: string;
  values: FacetValue[];
}

export interface FacetValue {
  value: string;
  count: number;
}

export class DataCatalogSearchService {
  private registry: DataCatalogRegistry;
  private glossary: BusinessGlossaryService;

  constructor(registry: DataCatalogRegistry, glossary: BusinessGlossaryService) {
    this.registry = registry;
    this.glossary = glossary;
  }

  async search(query: SearchQuery): Promise<SearchResult> {
    const startTime = Date.now();

    // Tokenize and expand query
    const tokens = this.tokenizeQuery(query.query);
    const expandedTokens = await this.expandQuery(tokens);

    // Search assets
    const assets = await this.registry.searchAssets({
      search: query.query,
      types: query.filters.assetTypes,
      domain: query.filters.domains?.[0],
      owner: query.filters.owners?.[0],
      tags: query.filters.tags,
      classifications: query.filters.classifications,
      offset: query.pagination.offset,
      limit: query.pagination.limit
    });

    // Calculate relevance
    const results = await this.rankResults(assets, expandedTokens);

    // Extract facets
    const facets = await this.calculateFacets(query);

    // Generate suggestions
    const suggestions = await this.generateSuggestions(query.query);

    return {
      assets: results,
      total: results.length,
      facets,
      suggestions,
      queryTime: Date.now() - startTime
    };
  }

  private tokenizeQuery(query: string): string[] {
    return query.toLowerCase().split(/\s+/).filter(t => t.length > 0);
  }

  private async expandQuery(tokens: string[]): Promise<string[]> {
    const expanded = new Set(tokens);

    for (const token of tokens) {
      // Add synonyms from glossary
      const term = await this.glossary.getTerm(token);
      if (term) {
        for (const synonym of term.synonyms) {
          expanded.add(synonym.toLowerCase());
        }
      }

      // Add related terms
      const related = await this.glossary.findRelatedTerms(token, 3);
      for (const r of related) {
        if (r.relevance > 0.8) {
          expanded.add(r.term.name.toLowerCase());
        }
      }
    }

    return Array.from(expanded);
  }

  private async rankResults(
    assets: DataAsset[],
    queryTokens: string[]
  ): Promise<SearchAssetResult[]> {
    const results: SearchAssetResult[] = [];

    for (const asset of assets) {
      const relevance = this.calculateRelevance(asset, queryTokens);
      const highlights = this.extractHighlights(asset, queryTokens);

      results.push({
        asset,
        relevance,
        highlights
      });
    }

    return results.sort((a, b) => b.relevance - a.relevance);
  }

  private calculateRelevance(asset: DataAsset, tokens: string[]): number {
    let score = 0;

    const nameLower = asset.name.toLowerCase();
    const descLower = asset.description.toLowerCase();

    for (const token of tokens) {
      // Exact name match
      if (nameLower === token) score += 100;

      // Name contains token
      if (nameLower.includes(token)) score += 50;

      // Description contains token
      if (descLower.includes(token)) score += 10;

      // Tags match
      if (asset.tags.some(t => t.name.toLowerCase() === token)) score += 30;

      // Qualified name match
      if (asset.qualifiedName.toLowerCase().includes(token)) score += 20;
    }

    // Boost verified assets
    if (asset.metadata.verified) score += 10;

    // Boost by quality score
    if (asset.metadata.qualityScore) {
      score += asset.metadata.qualityScore / 10;
    }

    return score;
  }

  private extractHighlights(asset: DataAsset, tokens: string[]): string[] {
    const highlights: string[] = [];

    for (const token of tokens) {
      if (asset.name.toLowerCase().includes(token)) {
        highlights.push(this.highlightText(asset.name, token));
      }

      if (asset.description.toLowerCase().includes(token)) {
        highlights.push(this.highlightText(asset.description, token));
      }
    }

    return highlights;
  }

  private highlightText(text: string, token: string): string {
    const regex = new RegExp(`(${token})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  private async calculateFacets(query: SearchQuery): Promise<SearchFacets[]> {
    const facets: SearchFacets[] = [];

    // Domain facet
    const domainCounts = await this.getDomainCounts();
    facets.push({
      name: 'Domain',
      values: Object.entries(domainCounts).map(([value, count]) => ({ value, count: count as number }))
    });

    // Type facet
    const typeCounts = await this.getTypeCounts();
    facets.push({
      name: 'Type',
      values: Object.entries(typeCounts).map(([value, count]) => ({ value, count: count as number }))
    });

    // Tag facet
    const tagCounts = await this.getTagCounts();
    facets.push({
      name: 'Tags',
      values: tagCounts.slice(0, 10)
    });

    return facets;
  }

  private async generateSuggestions(query: string): Promise<string[]> {
    const suggestions: string[] = [];

    // Suggest similar asset names
    for (const asset of this.registry['assets'].values()) {
      if (asset.name.toLowerCase().startsWith(query.toLowerCase())) {
        suggestions.push(asset.name);
      }
    }

    // Suggest glossary terms
    const termResults = await this.glossary.searchTerms(query);
    for (const term of termResults) {
      suggestions.push(term.displayName);
    }

    return [...new Set(suggestions)].slice(0, 10);
  }

  private async getDomainCounts(): Promise<Record<string, number>> {
    return this.registry.getStats().byDomain;
  }

  private async getTypeCounts(): Promise<Record<string, number>> {
    return this.registry.getStats().byType;
  }

  private async getTagCounts(): Promise<Array<{ value: string; count: number }>> {
    return this.registry.getStats().topTags;
  }
}
```

---

## Tagging & Classification

### Tag Management

```typescript
// data-catalog/tags/service.ts

export interface TagDefinition {
  name: string;
  category: string;
  description: string;
  color: string;
  icon?: string;
  applicableTo: AssetType[];
  managed: boolean; // Managed tags require approval
  owner: string;
}

export interface TagRule {
  id: string;
  name: string;
  description: string;
  condition: TagCondition;
  autoTag: string[];
  removeTag: string[];
}

export interface TagCondition {
  field: string;
  operator: 'contains' | 'equals' | 'matches' | 'starts_with' | 'ends_with';
  value: any;
}

export class TagManagementService {
  private tagDefinitions: Map<string, TagDefinition> = new Map();
  private tagRules: TagRule[] = [];

  constructor() {
    this.initializeTagDefinitions();
    this.initializeTagRules();
  }

  private initializeTagDefinitions(): void {
    const definitions: TagDefinition[] = [
      {
        name: 'pii',
        category: 'sensitivity',
        description: 'Contains personally identifiable information',
        color: '#e74c3c',
        applicableTo: [AssetType.TABLE, AssetType.COLUMN],
        managed: false,
        owner: 'data-team'
      },
      {
        name: 'financial',
        category: 'sensitivity',
        description: 'Contains financial data',
        color: '#f39c12',
        applicableTo: [AssetType.TABLE, AssetType.COLUMN],
        managed: false,
        owner: 'finance-team'
      },
      {
        name: 'verified',
        category: 'quality',
        description: 'Data has been verified for accuracy',
        color: '#27ae60',
        applicableTo: [AssetType.TABLE, AssetType.COLUMN, AssetType.VIEW],
        managed: true,
        owner: 'data-team'
      },
      {
        name: 'gold_standard',
        category: 'quality',
        description: 'Meets highest quality standards',
        color: '#f1c40f',
        applicableTo: [AssetType.TABLE],
        managed: true,
        owner: 'data-team'
      },
      {
        name: 'public',
        category: 'access',
        description: 'Can be shared externally',
        color: '#3498db',
        applicableTo: [AssetType.TABLE, AssetType.REPORT, AssetType.DASHBOARD],
        managed: true,
        owner: 'data-team'
      },
      {
        name: 'internal',
        category: 'access',
        description: 'Internal use only',
        color: '#9b59b6',
        applicableTo: AssetType.TABLE,
        managed: false,
        owner: 'data-team'
      },
      {
        name: 'restricted',
        category: 'access',
        description: 'Restricted access required',
        color: '#e74c3c',
        applicableTo: [AssetType.TABLE, AssetType.COLUMN],
        managed: true,
        owner: 'security-team'
      },
      {
        name: 'customer_data',
        category: 'domain',
        description: 'Customer-related data',
        color: '#1abc9c',
        applicableTo: [AssetType.TABLE, AssetType.COLUMN],
        managed: false,
        owner: 'customer-ops'
      },
      {
        name: 'operational',
        category: 'domain',
        description: 'Operational/transactional data',
        color: '#95a5a6',
        applicableTo: [AssetType.TABLE],
        managed: false,
        owner: 'ops-team'
      },
      {
        name: 'analytical',
        category: 'domain',
        description: 'Analytics/reporting data',
        color: '#16a085',
        applicableTo: [AssetType.TABLE, AssetType.DASHBOARD],
        managed: false,
        owner: 'analytics-team'
      }
    ];

    for (const def of definitions) {
      this.tagDefinitions.set(def.name, def);
    }
  }

  private initializeTagRules(): void {
    this.tagRules = [
      {
        id: 'rule_pii_email',
        name: 'Auto-tag PII email columns',
        description: 'Automatically tag columns containing email as PII',
        condition: { field: 'name', operator: 'contains', value: 'email' },
        autoTag: ['pii', 'customer_data'],
        removeTag: []
      },
      {
        id: 'rule_pii_phone',
        name: 'Auto-tag PII phone columns',
        description: 'Automatically tag columns containing phone as PII',
        condition: { field: 'name', operator: 'contains', value: 'phone' },
        autoTag: ['pii', 'customer_data'],
        removeTag: []
      },
      {
        id: 'rule_financial',
        name: 'Auto-tag financial columns',
        description: 'Automatically tag financial columns',
        condition: {
          field: 'name',
          operator: 'matches',
          value: /(price|amount|cost|payment|invoice|fee|commission)/i
        },
        autoTag: ['financial'],
        removeTag: []
      },
      {
        id: 'rule_verified',
        name: 'Auto-verify high quality assets',
        description: 'Auto-tag assets with quality score > 95 as verified',
        condition: { field: 'qualityScore', operator: 'greater_than', value: 95 },
        autoTag: ['verified'],
        removeTag: []
      }
    ];
  }

  async applyTagRules(asset: DataAsset): Promise<DataAsset> {
    for (const rule of this.tagRules) {
      if (this.evaluateCondition(asset, rule.condition)) {
        // Add auto tags
        for (const tagName of rule.autoTag) {
          const tagDef = this.tagDefinitions.get(tagName);
          if (tagDef && !asset.tags.some(t => t.name === tagName)) {
            asset.tags.push({
              name: tagName,
              category: tagDef.category,
              description: tagDef.description,
              color: tagDef.color
            });
          }
        }

        // Remove tags
        for (const tagName of rule.removeTag) {
          asset.tags = asset.tags.filter(t => t.name !== tagName);
        }
      }
    }

    return asset;
  }

  private evaluateCondition(asset: DataAsset, condition: TagCondition): boolean {
    const fieldValue = this.getFieldValue(asset, condition.field);

    switch (condition.operator) {
      case 'contains':
        return typeof fieldValue === 'string' && fieldValue.includes(condition.value);
      case 'equals':
        return fieldValue === condition.value;
      case 'matches':
        return typeof fieldValue === 'string' && new RegExp(condition.value, 'i').test(fieldValue);
      case 'starts_with':
        return typeof fieldValue === 'string' && fieldValue.startsWith(condition.value);
      case 'ends_with':
        return typeof fieldValue === 'string' && fieldValue.endsWith(condition.value);
      case 'greater_than':
        return typeof fieldValue === 'number' && fieldValue > condition.value;
      case 'less_than':
        return typeof fieldValue === 'number' && fieldValue < condition.value;
      default:
        return false;
    }
  }

  private getFieldValue(asset: DataAsset, field: string): any {
    if (field === 'name') return asset.name;
    if (field === 'description') return asset.description;
    if (field === 'domain') return asset.domain;
    if (field === 'owner') return asset.owner;
    if (field === 'type') return asset.type;
    if (field === 'qualityScore') return asset.metadata.qualityScore;
    return null;
  }

  async addTag(
    assetQualifiedName: string,
    tagName: string,
    userId: string
  ): Promise<void> {
    const tagDef = this.tagDefinitions.get(tagName);
    if (!tagDef) {
      throw new Error(`Tag not defined: ${tagName}`);
    }

    if (tagDef.managed) {
      // Require approval for managed tags
      await this.requestTagApproval(assetQualifiedName, tagName, userId);
    } else {
      // Apply tag directly
      // Implementation depends on registry
    }
  }

  private async requestTagApproval(
    assetQualifiedName: string,
    tagName: string,
    userId: string
  ): Promise<void> {
    // Create approval request
    console.log(`Tag approval requested: ${tagName} for ${assetQualifiedName} by ${userId}`);
  }

  getTagDefinition(tagName: string): TagDefinition | undefined {
    return this.tagDefinitions.get(tagName);
  }

  getAllTagDefinitions(): TagDefinition[] {
    return Array.from(this.tagDefinitions.values());
  }
}
```

---

## Data Ownership

### Ownership Assignment

```typescript
// data-catalog/ownership/service.ts

export interface OwnershipAssignment {
  assetQualifiedName: string;
  owner: string;
  steward: string;
  technicalOwner?: string;
  businessOwner?: string;
  assignedAt: Date;
  assignedBy: string;
  reason: string;
}

export interface OwnershipPolicy {
  pattern: string;
  owner: string;
  steward: string;
  domain: string;
  autoAssign: boolean;
}

export class DataOwnershipService {
  private assignments: Map<string, OwnershipAssignment> = new Map();
  private policies: OwnershipPolicy[] = [];

  constructor() {
    this.initializePolicies();
  }

  private initializePolicies(): void {
    this.policies = [
      {
        pattern: '*customer*',
        owner: 'customer-ops@travel-agency.com',
        steward: 'customer-ops-lead@travel-agency.com',
        domain: 'customer',
        autoAssign: true
      },
      {
        pattern: '*booking*',
        owner: 'booking-team@travel-agency.com',
        steward: 'booking-lead@travel-agency.com',
        domain: 'booking',
        autoAssign: true
      },
      {
        pattern: '*payment*',
        owner: 'finance-team@travel-agency.com',
        steward: 'finance-lead@travel-agency.com',
        domain: 'finance',
        autoAssign: true
      },
      {
        pattern: '*inventory*',
        owner: 'inventory-team@travel-agency.com',
        steward: 'inventory-lead@travel-agency.com',
        domain: 'inventory',
        autoAssign: true
      },
      {
        pattern: '*report*',
        owner: 'analytics-team@travel-agency.com',
        steward: 'analytics-lead@travel-agency.com',
        domain: 'analytics',
        autoAssign: true
      }
    ];
  }

  async assignOwnership(
    assetQualifiedName: string,
    owner: string,
    steward: string,
    assignedBy: string,
    reason: string
  ): Promise<OwnershipAssignment> {
    const assignment: OwnershipAssignment = {
      assetQualifiedName,
      owner,
      steward,
      assignedAt: new Date(),
      assignedBy,
      reason
    };

    this.assignments.set(assetQualifiedName, assignment);

    return assignment;
  }

  async autoAssignOwnership(assetName: string): Promise<OwnershipAssignment | null> {
    const policy = this.findMatchingPolicy(assetName);

    if (policy && policy.autoAssign) {
      return await this.assignOwnership(
        assetName,
        policy.owner,
        policy.steward,
        'system',
        `Auto-assigned based on policy: ${policy.pattern}`
      );
    }

    return null;
  }

  private findMatchingPolicy(assetName: string): OwnershipPolicy | null {
    const nameLower = assetName.toLowerCase();

    for (const policy of this.policies) {
      const pattern = policy.pattern.replace(/\*/g, '.*');
      const regex = new RegExp(pattern, 'i');
      if (regex.test(nameLower)) {
        return policy;
      }
    }

    return null;
  }

  async getOwnership(assetQualifiedName: string): Promise<OwnershipAssignment | undefined> {
    return this.assignments.get(assetQualifiedName);
  }

  async getOwnerAssets(owner: string): Promise<string[]> {
    const assets: string[] = [];

    for (const [asset, assignment] of this.assignments) {
      if (assignment.owner === owner || assignment.steward === owner) {
        assets.push(asset);
      }
    }

    return assets;
  }
}
```

---

## Search & Navigation

### Navigation Service

```typescript
// data-catalog/navigation/service.ts

export interface NavigationPath {
  id: string;
  name: string;
  type: 'domain' | 'system' | 'category';
  path: string[];
  itemCount: number;
}

export interface RelatedAssets {
  upstream: DataAsset[];
  downstream: DataAsset[];
  related: DataAsset[];
  similar: DataAsset[];
}

export class NavigationService {
  private registry: DataCatalogRegistry;
  private lineage: LineageGraph;

  constructor(registry: DataCatalogRegistry, lineage: LineageGraph) {
    this.registry = registry;
    this.lineage = lineage;
  }

  async getNavigationPaths(): Promise<NavigationPath[]> {
    const paths: NavigationPath[] = [];

    // Domain-based paths
    const domains = Object.keys(this.registry.getStats().byDomain);
    for (const domain of domains) {
      paths.push({
        id: `domain_${domain}`,
        name: this.capitalize(domain),
        type: 'domain',
        path: [domain],
        itemCount: this.registry.getStats().byDomain[domain]
      });
    }

    // System-based paths
    const systems = await this.getSystems();
    for (const system of systems) {
      paths.push({
        id: `system_${system}`,
        name: this.capitalize(system),
        type: 'system',
        path: ['systems', system],
        itemCount: await this.getSystemAssetCount(system)
      });
    }

    return paths;
  }

  async getRelatedAssets(assetQualifiedName: string): Promise<RelatedAssets> {
    const asset = await this.registry.getAsset(assetQualifiedName);
    if (!asset) {
      return { upstream: [], downstream: [], related: [], similar: [] };
    }

    // Upstream from lineage
    const upstream = await this.getUpstreamAssets(asset.id);

    // Downstream from lineage
    const downstream = await this.getDownstreamAssets(asset.id);

    // Related by domain/tags
    const related = await this.getRelatedByMetadata(asset);

    // Similar by name/description
    const similar = await this.getSimilarAssets(asset);

    return {
      upstream: upstream.filter(a => a !== undefined) as DataAsset[],
      downstream: downstream.filter(a => a !== undefined) as DataAsset[],
      related,
      similar
    };
  }

  private async getUpstreamAssets(nodeId: string): Promise<DataAsset[]> {
    const edges = this.lineage.edges.filter(e => e.to === nodeId);
    const assets: DataAsset[] = [];

    for (const edge of edges) {
      const node = this.lineage.nodes.find(n => n.id === edge.from);
      if (node) {
        const asset = await this.registry.getAsset(node.name);
        if (asset) assets.push(asset);
      }
    }

    return assets;
  }

  private async getDownstreamAssets(nodeId: string): Promise<DataAsset[]> {
    const edges = this.lineage.edges.filter(e => e.from === nodeId);
    const assets: DataAsset[] = [];

    for (const edge of edges) {
      const node = this.lineage.nodes.find(n => n.id === edge.to);
      if (node) {
        const asset = await this.registry.getAsset(node.name);
        if (asset) assets.push(asset);
      }
    }

    return assets;
  }

  private async getRelatedByMetadata(asset: DataAsset): Promise<DataAsset[]> {
    const results = await this.registry.searchAssets({
      domain: asset.domain,
      limit: 10
    });

    return results.filter(a => a.qualifiedName !== asset.qualifiedName);
  }

  private async getSimilarAssets(asset: DataAsset): Promise<DataAsset[]> {
    const results = await this.registry.searchAssets({
      search: asset.name.split('_')[0], // Use first part of name
      limit: 5
    });

    return results.filter(a => a.qualifiedName !== asset.qualifiedName);
  }

  private async getSystems(): Promise<string[]> {
    const systems = new Set<string>();
    const assets = await this.registry.searchAssets({ limit: 1000 });

    for (const asset of assets) {
      systems.add(asset.system);
    }

    return Array.from(systems);
  }

  private async getSystemAssetCount(system: string): Promise<number> {
    // Count assets for system
    return 0;
  }

  private capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}
```

---

## Catalog Integration

### BI Tool Integration

```typescript
// data-catalog/integration/bi.ts

export interface BIIntegration {
  tool: 'tableau' | 'looker' | 'powerbi' | 'metabase';
  syncAssets: () => Promise<void>;
  importAssets: () => Promise<DataAsset[]>;
  exportAssets: (assets: DataAsset[]) => Promise<void>;
}

export class TableauIntegration implements BIIntegration {
  tool = 'tableau' as const;

  constructor(private tableauAPI: any) {}

  async syncAssets(): Promise<void> {
    // Fetch workbooks and datasources from Tableau
    const workbooks = await this.fetchWorkbooks();

    for (const workbook of workbooks) {
      // Register as catalog asset
      // Implementation depends on Tableau API
    }
  }

  async importAssets(): Promise<DataAsset[]> {
    return [];
  }

  async exportAssets(assets: DataAsset[]): Promise<void> {
    // Push catalog metadata to Tableau
  }

  private async fetchWorkbooks(): Promise<any[]> {
    return [];
  }
}

export class LookerIntegration implements BIIntegration {
  tool = 'looker' as const;

  constructor(private lookerAPI: any) {}

  async syncAssets(): Promise<void> {
    // Fetch Looks, Dashboards, and Explores from Looker
  }

  async importAssets(): Promise<DataAsset[]> {
    return [];
  }

  async exportAssets(assets: DataAsset[]): Promise<void> {
    // Push catalog metadata to Looker
  }
}
```

---

## API Specification

### Data Catalog API

```typescript
// api/data-catalog/routes.ts

import { z } from 'zod';

// Schemas
const DataAssetSchema = z.object({
  id: z.string(),
  name: z.string(),
  qualifiedName: z.string(),
  type: z.string(),
  description: z.string(),
  owner: z.string(),
  domain: z.string(),
  tags: z.array(z.object({
    name: z.string(),
    category: z.string(),
    description: z.string()
  })),
  classifications: z.array(z.object({
    name: z.string(),
    type: z.string(),
    level: z.string()
  })),
  metadata: z.object({
    created: z.date(),
    modified: z.date(),
    verified: z.boolean(),
    qualityScore: z.number().optional()
  })
});

const GlossaryTermSchema = z.object({
  id: z.string(),
  name: z.string(),
  displayName: z.string(),
  definition: z.string(),
  category: z.string(),
  domain: z.string(),
  status: z.enum(['draft', 'approved', 'deprecated'])
});

const SearchQuerySchema = z.object({
  query: z.string(),
  filters: z.object({
    assetTypes: z.array(z.string()).optional(),
    domains: z.array(z.string()).optional(),
    owners: z.array(z.string()).optional(),
    tags: z.array(z.string()).optional()
  }),
  pagination: z.object({
    offset: z.number().default(0),
    limit: z.number().default(20)
  })
});

// Routes
export const dataCatalogRoutes = {
  // Assets
  'GET /api/catalog/assets': {
    summary: 'List catalog assets',
    query: SearchQuerySchema,
    response: z.object({
      assets: z.array(DataAssetSchema),
      total: z.number(),
      facets: z.array(z.object({
        name: z.string(),
        values: z.array(z.object({
          value: z.string(),
          count: z.number()
        }))
      }))
    })
  },

  'GET /api/catalog/assets/:qualifiedName': {
    summary: 'Get asset details',
    params: z.object({
      qualifiedName: z.string()
    }),
    response: DataAssetSchema
  },

  'POST /api/catalog/assets': {
    summary: 'Register new asset',
    request: DataAssetSchema.partial(),
    response: DataAssetSchema
  },

  'PUT /api/catalog/assets/:qualifiedName': {
    summary: 'Update asset',
    params: z.object({
      qualifiedName: z.string()
    }),
    request: DataAssetSchema.partial(),
    response: DataAssetSchema
  },

  'DELETE /api/catalog/assets/:qualifiedName': {
    summary: 'Delete asset',
    params: z.object({
      qualifiedName: z.string()
    }),
    response: z.object({ success: z.boolean() })
  },

  // Tags
  'POST /api/catalog/assets/:qualifiedName/tags': {
    summary: 'Add tag to asset',
    params: z.object({
      qualifiedName: z.string()
    }),
    request: z.object({
      tag: z.string(),
      userId: z.string()
    }),
    response: DataAssetSchema
  },

  'DELETE /api/catalog/assets/:qualifiedName/tags/:tag': {
    summary: 'Remove tag from asset',
    params: z.object({
      qualifiedName: z.string(),
      tag: z.string()
    }),
    response: z.object({ success: z.boolean() })
  },

  'GET /api/catalog/tags': {
    summary: 'List all tags',
    response: z.array(z.object({
      name: z.string(),
      category: z.string(),
      description: z.string(),
      color: z.string(),
      count: z.number()
    }))
  },

  // Glossary
  'GET /api/catalog/glossary': {
    summary: 'List glossary terms',
    query: z.object({
      category: z.string().optional(),
      domain: z.string().optional(),
      search: z.string().optional()
    }),
    response: z.array(GlossaryTermSchema)
  },

  'GET /api/catalog/glossary/:termId': {
    summary: 'Get glossary term',
    params: z.object({
      termId: z.string()
    }),
    response: GlossaryTermSchema
  },

  'POST /api/catalog/glossary': {
    summary: 'Create glossary term',
    request: GlossaryTermSchema.partial(),
    response: GlossaryTermSchema
  },

  // Data Dictionary
  'GET /api/catalog/dictionary/tables/:tableName': {
    summary: 'Get table definition',
    params: z.object({
      tableName: z.string()
    }),
    response: z.object({
      name: z.string(),
      description: z.string(),
      owner: z.string(),
      columns: z.array(z.object({
        name: z.string(),
        dataType: z.string(),
        nullable: z.boolean(),
        description: z.string()
      }))
    })
  },

  'GET /api/catalog/dictionary/columns/:columnName': {
    summary: 'Get column definition',
    params: z.object({
      columnName: z.string()
    }),
    response: z.object({
      name: z.string(),
      table: z.string(),
      dataType: z.string(),
      businessName: z.string(),
      businessDefinition: z.string()
    })
  },

  // Search
  'POST /api/catalog/search': {
    summary: 'Search catalog',
    request: SearchQuerySchema,
    response: z.object({
      assets: z.array(z.object({
        asset: DataAssetSchema,
        relevance: z.number(),
        highlights: z.array(z.string())
      })),
      total: z.number(),
      suggestions: z.array(z.string())
    })
  },

  // Navigation
  'GET /api/catalog/navigation': {
    summary: 'Get navigation paths',
    response: z.array(z.object({
      id: z.string(),
      name: z.string(),
      type: z.string(),
      path: z.array(z.string()),
      itemCount: z.number()
    }))
  },

  'GET /api/catalog/assets/:qualifiedName/related': {
    summary: 'Get related assets',
    params: z.object({
      qualifiedName: z.string()
    }),
    response: z.object({
      upstream: z.array(DataAssetSchema),
      downstream: z.array(DataAssetSchema),
      related: z.array(DataAssetSchema),
      similar: z.array(DataAssetSchema)
    })
  },

  // Ownership
  'POST /api/catalog/assets/:qualifiedName/ownership': {
    summary: 'Assign ownership',
    params: z.object({
      qualifiedName: z.string()
    }),
    request: z.object({
      owner: z.string(),
      steward: z.string(),
      reason: z.string()
    }),
    response: z.object({
      assetQualifiedName: z.string(),
      owner: z.string(),
      steward: z.string(),
      assignedAt: z.date()
    })
  },

  // Metadata extraction
  'POST /api/catalog/extract/database': {
    summary: 'Extract metadata from database',
    request: z.object({
      connection: z.object({
        system: z.string(),
        host: z.string(),
        port: z.number(),
        database: z.string(),
        schema: z.string().optional()
      })
    }),
    response: z.object({
      extracted: z.number(),
      registered: z.number(),
      failed: z.number()
    })
  },

  'POST /api/catalog/extract/file': {
    summary: 'Extract metadata from file',
    request: z.object({
      filePath: z.string()
    }),
    response: DataAssetSchema
  },

  // Statistics
  'GET /api/catalog/stats': {
    summary: 'Get catalog statistics',
    response: z.object({
      totalAssets: z.number(),
      byType: z.record(z.number()),
      byDomain: z.record(z.number()),
      topTags: z.array(z.object({
        tag: z.string(),
        count: z.number()
      })),
      verifiedCount: z.number(),
      qualityAvgScore: z.number()
    })
  }
};
```

---

## Testing Scenarios

### Data Catalog Tests

```typescript
// tests/data-catalog/scenarios.ts

interface TestScenario {
  name: string;
  description: string;
  test: () => Promise<void>;
}

export const dataCatalogTests: TestScenario[] = [
  {
    name: 'Asset Registration',
    description: 'Verify assets can be registered and retrieved',
    test: async () => {
      const registry = new DataCatalogRegistry();
      const asset: DataAsset = {
        id: 'test_asset',
        name: 'test_table',
        qualifiedName: 'public.test_table',
        type: AssetType.TABLE,
        description: 'Test table',
        owner: 'test@example.com',
        steward: '',
        domain: 'test',
        system: 'test_db',
        attributes: { forType: AssetType.TABLE, schema: 'public', table: 'test_table' },
        tags: [],
        classifications: [],
        properties: {},
        metadata: {
          created: new Date(),
          modified: new Date(),
          createdBy: 'test',
          modifiedBy: 'test',
          version: 1,
          verified: false,
          source: 'manual',
          lastAnalyzed: new Date()
        }
      };

      await registry.registerAsset(asset);
      const retrieved = await registry.getAsset('public.test_table');

      expect(retrieved).toBeDefined();
      expect(retrieved!.name).toBe('test_table');
    }
  },

  {
    name: 'Tag Auto-Assignment',
    description: 'Verify tags are auto-assigned based on rules',
    test: async () => {
      const service = new TagManagementService();
      const asset: DataAsset = {
        id: 'test',
        name: 'customer_email',
        qualifiedName: 'public.customer_email',
        type: AssetType.COLUMN,
        description: 'Customer email address',
        owner: 'test@example.com',
        steward: '',
        domain: 'customer',
        system: 'test',
        attributes: { forType: AssetType.COLUMN, column: undefined },
        tags: [],
        classifications: [],
        properties: {},
        metadata: {
          created: new Date(),
          modified: new Date(),
          createdBy: 'test',
          modifiedBy: 'test',
          version: 1,
          verified: false,
          source: 'manual',
          lastAnalyzed: new Date()
        }
      };

      const tagged = await service.applyTagRules(asset);

      expect(tagged.tags.some(t => t.name === 'pii')).toBe(true);
      expect(tagged.tags.some(t => t.name === 'customer_data')).toBe(true);
    }
  },

  {
    name: 'Glossary Search',
    description: 'Verify glossary terms can be searched',
    test: async () => {
      const service = new BusinessGlossaryService();
      const results = await service.searchTerms('booking');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name).toBe('booking');
    }
  },

  {
    name: 'Ownership Assignment',
    description: 'Verify ownership can be assigned',
    test: async () => {
      const service = new DataOwnershipService();
      const assignment = await service.assignOwnership(
        'public.customers',
        'customer-ops@example.com',
        'customer-ops-lead@example.com',
        'admin',
        'Initial assignment'
      );

      expect(assignment.owner).toBe('customer-ops@example.com');
      expect(assignment.steward).toBe('customer-ops-lead@example.com');
    }
  }
];
```

---

## Metrics & Monitoring

### Data Catalog KPIs

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| **Catalog Coverage** | % of database tables cataloged | 100% | < 95% |
| **Description Coverage** | % of assets with descriptions | > 80% | < 70% |
| **Owner Assignment** | % of assets with assigned owner | 100% | < 95% |
| **Verification Rate** | % of assets verified | > 50% | < 30% |
| **Tag Coverage** | % of assets with tags | > 90% | < 80% |
| **Glossary Coverage** | % of terms linked to assets | > 70% | < 50% |
| **Search Success Rate** | % of searches with results | > 90% | < 80% |

### Dashboard Queries

```promql
# Catalog coverage
sum(catalog_assets) by (system) / sum(database_tables) by (system) * 100

# Description coverage
sum(catalog_assets{has_description="true"}) / sum(catalog_assets) * 100

# Search queries
rate(catalog_search_queries_total[5m])
rate(catalog_search_results_total[5m])

# Tag usage
catalog_tags_count{tag=~".*"} > 10
```

---

**Document Version:** 1.0

**Last Updated:** 2026-04-26

**Related Documents:**
- [DATA_GOVERNANCE_MASTER_INDEX.md](./DATA_GOVERNANCE_MASTER_INDEX.md)
- [DATA_GOVERNANCE_01_QUALITY.md](./DATA_GOVERNANCE_01_QUALITY.md)
- [DATA_GOVERNANCE_02_LINEAGE.md](./DATA_GOVERNANCE_02_LINEAGE.md)
- [DATA_GOVERNANCE_04_COMPLIANCE.md](./DATA_GOVERNANCE_04_COMPLIANCE.md) - Next document
