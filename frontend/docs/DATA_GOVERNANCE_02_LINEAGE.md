# DATA_GOVERNANCE_02: Data Lineage Deep Dive

> Data lineage tracking, impact analysis, and provenance

---

## Table of Contents

1. [Overview](#overview)
2. [Lineage Metadata Model](#lineage-metadata-model)
3. [Source-to-Target Mapping](#source-to-target-mapping)
4. [Column-Level Lineage](#column-level-lineage)
5. [Impact Analysis](#impact-analysis)
6. [Data Provenance](#data-provenance)
7. [Lineage Visualization](#lineage-visualization)
8. [Automated Capture](#automated-capture)
9. [Cross-System Lineage](#cross-system-lineage)
10. [API Specification](#api-specification)
11. [Testing Scenarios](#testing-scenarios)
12. [Metrics & Monitoring](#metrics--monitoring)

---

## Overview

Data lineage tracks the flow of data from origin to destination, including all transformations and intermediate steps. This enables impact analysis, debugging, compliance, and trust in data.

### Why Lineage Matters

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Flow Example                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Customer Email ──▶ Intake ──▶ Packet ──▶ Booking ──▶ Quote │
│                     │         │          │         │        │
│                     ▼         ▼          ▼         ▼        │
│                  Extract   Validate   Transform  Output     │
│                     │         │          │         │        │
│                     ▼         ▼          ▼         ▼        │
│                  Raw NLP   Cleaned    Enriched  Final PDF  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Questions lineage answers:
- Where did this email address come from?
- What transformations were applied?
- If we change this field, what breaks?
- Who accessed this data and when?
- Is this data GDPR-compliant?
```

### Lineage Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Technical** | System-to-system data flow | Impact analysis, debugging |
| **Business** | Business term mapping | Glossary, stewardship |
| **Column-Level** | Field-by-field tracking | Precision impact analysis |
| **Provenance** | Origin and custody | Compliance, audit |

---

## Lineage Metadata Model

### Core Entities

```typescript
// data-lineage/model/entities.ts

export interface LineageNode {
  id: string;
  name: string;
  type: NodeType;
  system: string;
  schema?: string;
  attributes: Record<string, any>;
  metadata: {
    created: Date;
    modified: Date;
    owner: string;
    description?: string;
    tags: string[];
  };
}

export enum NodeType {
  // Sources
  SOURCE_TABLE = 'source_table',
  SOURCE_VIEW = 'source_view',
  SOURCE_FILE = 'source_file',
  SOURCE_API = 'source_api',
  SOURCE_MESSAGE = 'source_message',

  // Processing
  TRANSFORMATION = 'transformation',
  VALIDATION = 'validation',
  ENRICHMENT = 'enrichment',
  AGGREGATION = 'aggregation',
  FILTER = 'filter',

  // Storage
  TABLE = 'table',
  VIEW = 'view',
  MATERIALIZED_VIEW = 'materialized_view',
  CACHE = 'cache',

  // Output
  REPORT = 'report',
  EXPORT = 'export',
  API_ENDPOINT = 'api_endpoint',
  NOTIFICATION = 'notification'
}

export interface LineageEdge {
  id: string;
  from: string; // Node ID
  to: string;   // Node ID
  type: EdgeType;
  fields?: FieldMapping[];
  transformation?: string;
  condition?: string;
  metadata: {
    created: Date;
    createdBy: string;
    description?: string;
  };
}

export enum EdgeType {
  DATA_FLOW = 'data_flow',           // Direct data copy
  TRANSFORM = 'transform',            // Data transformation
  AGGREGATE = 'aggregate',            // Data aggregation
  FILTER = 'filter',                  // Data filtering
  JOIN = 'join',                      // Data joining
  UNION = 'union',                    // Data combination
  LOOKUP = 'lookup',                  // Reference lookup
  VALIDATE = 'validate',              // Validation step
  DEPENDENCY = 'dependency'           // Dependency relationship
}

export interface FieldMapping {
  source: string;
  target: string;
  transformation?: string;
}

export interface LineageGraph {
  id: string;
  name: string;
  domain: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
  metadata: {
    version: number;
    created: Date;
    modified: Date;
    lastAnalyzed: Date;
  };
}
```

### Column-Level Lineage

```typescript
// data-lineage/model/column-lineage.ts

export interface ColumnLineage {
  columnId: string;
  name: string;
  lineageChain: LineageStep[];
  sources: ColumnSource[];
  transformations: Transformation[];
  destinations: ColumnDestination[];
}

export interface LineageStep {
  stepId: string;
  nodeId: string;
  nodeName: string;
  inputFields: string[];
  outputField: string;
  transformation: string;
  timestamp: Date;
}

export interface ColumnSource {
  source: string;
  field: string;
  sourceType: 'column' | 'literal' | 'computed' | 'external';
  confidence: number;
}

export interface ColumnDestination {
  destination: string;
  field: string;
  downstreamSteps: string[];
}

export interface Transformation {
  id: string;
  type: TransformationType;
  expression: string;
  description: string;
  inputs: string[];
  outputs: string[];
}

export enum TransformationType {
  DIRECT_COPY = 'direct_copy',
  CONCATENATION = 'concatenation',
  CALCCULATION = 'calculation',
  CONDITIONAL = 'conditional',
  LOOKUP = 'lookup',
  AGGREGATION = 'aggregation',
  DATE_FORMAT = 'date_format',
  STRING_MANIPULATION = 'string_manipulation',
  TYPE_CONVERSION = 'type_conversion',
  CUSTOM = 'custom'
}
```

---

## Source-to-Target Mapping

### Mapping Configuration

```typescript
// data-lineage/mapping/configuration.ts

export interface SourceToTargetMapping {
  id: string;
  name: string;
  source: DataSource;
  target: DataTarget;
  mappings: FieldMapping[];
  transformations: Transformation[];
  businessRules: BusinessRule[];
  schedule?: MappingSchedule;
  metadata: MappingMetadata;
}

export interface DataSource {
  system: string;
  type: 'database' | 'file' | 'api' | 'message_queue';
  connection: ConnectionConfig;
  schema: string;
  table: string;
  query?: string;
}

export interface DataTarget {
  system: string;
  type: 'database' | 'file' | 'api' | 'data_warehouse';
  connection: ConnectionConfig;
  schema: string;
  table: string;
  loadType: 'full' | 'incremental' | 'cdc';
}

export interface ConnectionConfig {
  type: string;
  host?: string;
  port?: number;
  database?: string;
  credentials?: string;
  params?: Record<string, any>;
}

export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  condition: string;
  action: string;
  priority: number;
}

export interface MappingSchedule {
  type: 'cron' | 'event' | 'continuous';
  expression?: string;
  eventSource?: string;
}

export interface MappingMetadata {
  created: Date;
  modified: Date;
  owner: string;
  steward: string;
  version: number;
  tags: string[];
  compliance: ComplianceInfo;
}

export interface ComplianceInfo {
  classification: string;
  retention: string;
  privacy: boolean;
  gdprRelevant: boolean;
}

// Example mapping configuration
export const customerInquiryMapping: SourceToTargetMapping = {
  id: 'MAP_CUST_INQ_001',
  name: 'Customer Inquiry to Packet',
  source: {
    system: 'communication_hub',
    type: 'message_queue',
    connection: {
      type: 'sqs',
      region: 'us-east-1'
    },
    schema: 'raw',
    table: 'customer_inquiries'
  },
  target: {
    system: 'workspace',
    type: 'database',
    connection: {
      type: 'postgresql',
      host: 'db.internal',
      port: 5432,
      database: 'travel_agency'
    },
    schema: 'public',
    table: 'packets',
    loadType: 'incremental'
  },
  mappings: [
    { source: 'from_address', target: 'customer_email' },
    { source: 'subject', target: 'inquiry_subject' },
    { source: 'body', target: 'inquiry_text' },
    { source: 'received_at', target: 'created_at' }
  ],
  transformations: [
    {
      id: 'TRANS_001',
      type: TransformationType.STRING_MANIPULATION,
      expression: 'TRIM(UPPER(source.email))',
      description: 'Normalize email to uppercase and trim',
      inputs: ['source.email'],
      outputs: ['target.customer_email']
    },
    {
      id: 'TRANS_002',
      type: TransformationType.CONCATENATION,
      expression: 'CONCAT(source.subject, " - ", LEFT(source.body, 50))',
      description: 'Create summary from subject and body preview',
      inputs: ['source.subject', 'source.body'],
      outputs: ['target.summary']
    }
  ],
  businessRules: [
    {
      id: 'BR_001',
      name: 'Dedupe Inquiries',
      description: 'Skip if same email received within 1 hour',
      condition: 'NOT EXISTS(SELECT 1 FROM packets WHERE customer_email = source.email AND created_at > NOW() - INTERVAL "1 hour")',
      action: 'SKIP',
      priority: 1
    },
    {
      id: 'BR_002',
      name: 'Classify Inquiry Type',
      description: 'Set inquiry type based on keywords',
      condition: 'CONTAINS(LOWER(source.subject), "quote") OR CONTAINS(LOWER(source.body), "quote")',
      action: 'SET target.inquiry_type = "quote_request"',
      priority: 2
    }
  ],
  schedule: {
    type: 'event',
    eventSource: 'sqs://customer-inquiries-queue'
  },
  metadata: {
    created: new Date('2026-01-01'),
    modified: new Date('2026-04-01'),
    owner: 'data-engineering',
    steward: 'customer-operations',
    version: 3,
    tags: ['customer', 'inquiry', 'ingestion'],
    compliance: {
      classification: 'internal',
      retention: '7_years',
      privacy: true,
      gdprRelevant: true
    }
  }
};
```

---

## Column-Level Lineage

### Column Lineage Service

```typescript
// data-lineage/service/column-lineage.ts

export class ColumnLineageService {
  private lineageGraph: LineageGraph;
  private columnIndex: Map<string, ColumnLineage> = new Map();

  constructor(graph: LineageGraph) {
    this.lineageGraph = graph;
    this.buildColumnIndex();
  }

  async getColumnLineage(
    tableName: string,
    columnName: string
  ): Promise<ColumnLineage> {
    const columnId = `${tableName}.${columnName}`;
    const cached = this.columnIndex.get(columnId);

    if (cached) {
      return cached;
    }

    return this.traceLineage(tableName, columnName);
  }

  private async traceLineage(
    tableName: string,
    columnName: string
  ): Promise<ColumnLineage> {
    const chain: LineageStep[] = [];
    const sources: ColumnSource[] = [];
    const transformations: Transformation[] = [];
    const destinations: ColumnDestination[] = [];

    // Trace backwards to find sources
    await this.traceBackwards(tableName, columnName, chain, sources, transformations);

    // Trace forwards to find destinations
    await this.traceForwards(tableName, columnName, destinations);

    return {
      columnId: `${tableName}.${columnName}`,
      name: columnName,
      lineageChain: chain,
      sources,
      transformations,
      destinations
    };
  }

  private async traceBackwards(
    tableName: string,
    columnName: string,
    chain: LineageStep[],
    sources: ColumnSource[],
    transformations: Transformation[]
  ): Promise<void> {
    const currentNode = this.findNode(tableName);
    if (!currentNode) return;

    // Find edges that point to this column
    const incomingEdges = this.lineageGraph.edges.filter(
      e => e.to === currentNode.id && e.fields?.some(f => f.target === columnName)
    );

    for (const edge of incomingEdges) {
      const sourceNode = this.lineageGraph.nodes.find(n => n.id === edge.from);
      if (!sourceNode) continue;

      for (const mapping of edge.fields || []) {
        if (mapping.target === columnName) {
          // Add to chain
          chain.push({
            stepId: edge.id,
            nodeId: sourceNode.id,
            nodeName: sourceNode.name,
            inputFields: [mapping.source],
            outputField: mapping.target,
            transformation: mapping.transformation || edge.transformation || 'DIRECT_COPY',
            timestamp: edge.metadata.created
          });

          // Record transformation
          if (mapping.transformation) {
            transformations.push({
              id: edge.id,
              type: this.inferTransformationType(mapping.transformation),
              expression: mapping.transformation,
              description: `Transform ${mapping.source} to ${mapping.target}`,
              inputs: [mapping.source],
              outputs: [mapping.target]
            });
          }

          // Check if source is a leaf (actual source)
          if (this.isSourceNode(sourceNode)) {
            sources.push({
              source: sourceNode.name,
              field: mapping.source,
              sourceType: 'column',
              confidence: 1.0
            });
          } else {
            // Continue tracing back
            await this.traceBackwards(
              sourceNode.name,
              mapping.source,
              chain,
              sources,
              transformations
            );
          }
        }
      }
    }
  }

  private async traceForwards(
    tableName: string,
    columnName: string,
    destinations: ColumnDestination[]
  ): Promise<void> {
    const currentNode = this.findNode(tableName);
    if (!currentNode) return;

    // Find edges that originate from this column
    const outgoingEdges = this.lineageGraph.edges.filter(
      e => e.from === currentNode.id && e.fields?.some(f => f.source === columnName)
    );

    for (const edge of outgoingEdges) {
      const targetNode = this.lineageGraph.nodes.find(n => n.id === edge.to);
      if (!targetNode) continue;

      for (const mapping of edge.fields || []) {
        if (mapping.source === columnName) {
          destinations.push({
            destination: targetNode.name,
            field: mapping.target,
            downstreamSteps: [edge.id]
          });

          // Continue tracing forward
          await this.traceForwards(targetNode.name, mapping.target, destinations);
        }
      }
    }
  }

  private findNode(tableName: string): LineageNode | undefined {
    return this.lineageGraph.nodes.find(n => n.name === tableName);
  }

  private isSourceNode(node: LineageNode): boolean {
    return node.type.startsWith('source_');
  }

  private inferTransformationType(expression: string): TransformationType {
    const upperExpr = expression.toUpperCase();

    if (upperExpr.includes('CONCAT') || upperExpr.includes('||')) {
      return TransformationType.CONCATENATION;
    }
    if (upperExpr.includes('CASE WHEN') || upperExpr.includes('IF(')) {
      return TransformationType.CONDITIONAL;
    }
    if (upperExpr.includes('SUM(') || upperExpr.includes('COUNT(') || upperExpr.includes('AVG(')) {
      return TransformationType.AGGREGATION;
    }
    if (upperExpr.includes('JOIN') || upperExpr.includes('LOOKUP')) {
      return TransformationType.LOOKUP;
    }
    if (upperExpr.includes('TO_DATE') || upperExpr.includes('DATE_FORMAT')) {
      return TransformationType.DATE_FORMAT;
    }
    if (upperExpr.includes('CAST(') || upperExpr.includes('CONVERT(')) {
      return TransformationType.TYPE_CONVERSION;
    }
    if (upperExpr.includes('TRIM') || upperExpr.includes('UPPER') || upperExpr.includes('LOWER')) {
      return TransformationType.STRING_MANIPULATION;
    }
    if (upperExpr.match(/[\+\-\*\/]/)) {
      return TransformationType.CALCCULATION;
    }

    return TransformationType.CUSTOM;
  }

  private buildColumnIndex(): void {
    // Build index of all columns for quick lookup
    for (const node of this.lineageGraph.nodes) {
      if (node.attributes.columns) {
        for (const column of node.attributes.columns) {
          this.columnIndex.set(`${node.name}.${column}`, {
            columnId: `${node.name}.${column}`,
            name: column,
            lineageChain: [],
            sources: [],
            transformations: [],
            destinations: []
          });
        }
      }
    }
  }
}
```

---

## Impact Analysis

### Impact Analysis Service

```typescript
// data-lineage/service/impact-analysis.ts

export interface ImpactAnalysisRequest {
  nodeType: 'table' | 'column' | 'transformation';
  nodeId: string;
  changeType: 'add' | 'modify' | 'delete';
  changes: ChangeDescription[];
}

export interface ChangeDescription {
  field: string;
  changeType: 'add' | 'modify' | 'delete' | 'rename';
  oldValue?: any;
  newValue?: any;
}

export interface ImpactAnalysisResult {
  nodeId: string;
  changeType: string;
  impacts: Impact[];
  summary: ImpactSummary;
  recommendations: string[];
}

export interface Impact {
  targetId: string;
  targetName: string;
  targetType: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  impact: string;
  downstreamSteps: string[];
  affectedFields: string[];
  estimatedEffort: 'low' | 'medium' | 'high';
}

export interface ImpactSummary {
  totalImpacts: number;
  criticalImpacts: number;
  highImpacts: number;
  mediumImpacts: number;
  lowImpacts: number;
  affectedSystems: string[];
  affectedTeams: string[];
}

export class ImpactAnalysisService {
  private graph: LineageGraph;

  constructor(graph: LineageGraph) {
    this.graph = graph;
  }

  async analyzeImpact(request: ImpactAnalysisRequest): Promise<ImpactAnalysisResult> {
    const impacts: Impact[] = [];

    // Find all downstream nodes
    const downstreamNodes = this.findDownstreamNodes(request.nodeId);

    // Analyze impact on each downstream node
    for (const node of downstreamNodes) {
      const nodeImpacts = await this.analyzeNodeImpact(node, request);
      impacts.push(...nodeImpacts);
    }

    return {
      nodeId: request.nodeId,
      changeType: request.changeType,
      impacts: impacts.sort((a, b) => this.severityScore(b.severity) - this.severityScore(a.severity)),
      summary: this.summarizeImpacts(impacts),
      recommendations: this.generateRecommendations(request, impacts)
    };
  }

  private findDownstreamNodes(nodeId: string): LineageNode[] {
    const visited = new Set<string>();
    const downstream: LineageNode[] = [];

    const traverse = (currentId: string) => {
      if (visited.has(currentId)) return;
      visited.add(currentId);

      const outgoingEdges = this.graph.edges.filter(e => e.from === currentId);
      for (const edge of outgoingEdges) {
        const targetNode = this.graph.nodes.find(n => n.id === edge.to);
        if (targetNode) {
          downstream.push(targetNode);
          traverse(targetNode.id);
        }
      }
    };

    traverse(nodeId);
    return downstream;
  }

  private async analyzeNodeImpact(
    node: LineageNode,
    request: ImpactAnalysisRequest
  ): Promise<Impact[]> {
    const impacts: Impact[] = [];
    const incomingEdge = this.graph.edges.find(e => e.to === node.id);

    for (const change of request.changes) {
      const severity = this.calculateSeverity(node, change, request.changeType);
      const affectedFields = this.getAffectedFields(node, change);

      impacts.push({
        targetId: node.id,
        targetName: node.name,
        targetType: node.type,
        severity,
        impact: this.describeImpact(node, change),
        downstreamSteps: this.getDownstreamPath(node.id),
        affectedFields,
        estimatedEffort: this.estimateEffort(severity, node)
      });
    }

    return impacts;
  }

  private calculateSeverity(
    node: LineageNode,
    change: ChangeDescription,
    changeType: string
  ): 'critical' | 'high' | 'medium' | 'low' {
    // Critical impacts
    if (node.type === NodeType.REPORT && changeType === 'delete') {
      return 'critical';
    }
    if (node.type === NodeType.API_ENDPOINT && changeType === 'delete') {
      return 'critical';
    }

    // High impacts
    if (node.type === NodeType.MATERIALIZED_VIEW) {
      return 'high';
    }
    if (node.type === NodeType.TABLE && change.changeType === 'delete') {
      return 'high';
    }

    // Medium impacts
    if (node.type === NodeType.TRANSFORMATION) {
      return 'medium';
    }

    return 'low';
  }

  private getAffectedFields(node: LineageNode, change: ChangeDescription): string[] {
    const incomingEdge = this.graph.edges.find(e => e.to === node.id);
    if (!incomingEdge || !incomingEdge.fields) return [];

    return incomingEdge.fields
      .filter(f => f.source === change.field || f.target === change.field)
      .map(f => f.target);
  }

  private describeImpact(node: LineageNode, change: ChangeDescription): string {
    switch (change.changeType) {
      case 'delete':
        return `${node.name} will lose access to ${change.field}. Downstream processes may fail.`;
      case 'modify':
        return `${node.name} will receive modified ${change.field}. Data types or values may change.`;
      case 'rename':
        return `${node.name} field mapping needs update from ${change.oldValue} to ${change.newValue}.`;
      case 'add':
        return `${node.name} can optionally use new field ${change.field}.`;
      default:
        return `Change to ${change.field} affects ${node.name}.`;
    }
  }

  private getDownstreamPath(nodeId: string): string[] {
    const path: string[] = [];
    let currentId = nodeId;

    while (currentId) {
      path.push(currentId);
      const nextEdge = this.graph.edges.find(e => e.from === currentId);
      currentId = nextEdge?.to || '';
    }

    return path;
  }

  private estimateEffort(
    severity: string,
    node: LineageNode
  ): 'low' | 'medium' | 'high' {
    if (severity === 'critical') return 'high';
    if (severity === 'high') return 'medium';
    return 'low';
  }

  private summarizeImpacts(impacts: Impact[]): ImpactSummary {
    const affectedSystems = new Set<string>();
    const affectedTeams = new Set<string>();

    for (const impact of impacts) {
      const node = this.graph.nodes.find(n => n.id === impact.targetId);
      if (node) {
        affectedSystems.add(node.system);
        affectedTeams.add(node.metadata.owner);
      }
    }

    return {
      totalImpacts: impacts.length,
      criticalImpacts: impacts.filter(i => i.severity === 'critical').length,
      highImpacts: impacts.filter(i => i.severity === 'high').length,
      mediumImpacts: impacts.filter(i => i.severity === 'medium').length,
      lowImpacts: impacts.filter(i => i.severity === 'low').length,
      affectedSystems: Array.from(affectedSystems),
      affectedTeams: Array.from(affectedTeams)
    };
  }

  private generateRecommendations(
    request: ImpactAnalysisRequest,
    impacts: Impact[]
  ): string[] {
    const recommendations: string[] = [];

    if (request.changeType === 'delete') {
      recommendations.push('Consider deprecating the field instead of deleting to allow graceful migration.');
    }

    const criticalImpacts = impacts.filter(i => i.severity === 'critical');
    if (criticalImpacts.length > 0) {
      recommendations.push(`Create rollback plan before proceeding. ${criticalImpacts.length} critical dependencies found.`);
    }

    const highImpacts = impacts.filter(i => i.severity === 'high');
    if (highImpacts.length > 5) {
      recommendations.push('High number of impacts. Consider breaking change into multiple phases.');
    }

    recommendations.push('Notify all affected teams before deploying change.');
    recommendations.push('Update data quality monitoring for affected fields.');

    return recommendations;
  }

  private severityScore(severity: string): number {
    const scores = { critical: 4, high: 3, medium: 2, low: 1 };
    return scores[severity] || 0;
  }
}
```

---

## Data Provenance

### Provenance Tracking

```typescript
// data-lineage/provenance/tracker.ts

export interface ProvenanceRecord {
  id: string;
  entityId: string;
  entityType: string;
  origin: DataOrigin;
  custodyChain: CustodyTransfer[];
  transformations: TransformationRecord[];
  accessHistory: AccessRecord[];
  compliance: ProvenanceCompliance;
  metadata: ProvenanceMetadata;
}

export interface DataOrigin {
  source: string;
  sourceType: 'customer' | 'employee' | 'system' | 'third_party' | 'public';
  sourceId?: string;
  timestamp: Date;
  method: 'api' | 'web' | 'email' | 'import' | 'integration';
  ipAddress?: string;
  userAgent?: string;
  consent: boolean;
  consentTimestamp?: Date;
}

export interface CustodyTransfer {
  from: string;
  to: string;
  timestamp: Date;
  reason: string;
  method: string;
  approvedBy: string;
}

export interface TransformationRecord {
  id: string;
  timestamp: Date;
  transformation: string;
  inputHash?: string;
  outputHash?: string;
  performedBy: string;
  system: string;
}

export interface AccessRecord {
  timestamp: Date;
  accessedBy: string;
  accessMethod: string;
  purpose: string;
  duration?: number;
}

export interface ProvenanceCompliance {
  dataClassification: string;
  retentionStart: Date;
  retentionEnd?: Date;
  gdprRelevant: boolean;
  consentTracked: boolean;
  dataMinimized: boolean;
  purposeLimitation: string;
}

export interface ProvenanceMetadata {
  created: Date;
  modified: Date;
  version: number;
  verified: boolean;
  lastVerified: Date;
  hash: string;
}

export class DataProvenanceService {
  private records: Map<string, ProvenanceRecord> = new Map();

  async trackOrigin(
    entityId: string,
    entityType: string,
    origin: DataOrigin
  ): Promise<void> {
    const record: ProvenanceRecord = {
      id: `PROV_${entityId}_${Date.now()}`,
      entityId,
      entityType,
      origin,
      custodyChain: [],
      transformations: [],
      accessHistory: [],
      compliance: {
        dataClassification: 'internal',
        retentionStart: new Date(),
        gdprRelevant: entityType === 'customer',
        consentTracked: origin.consent,
        dataMinimized: false,
        purposeLimitation: 'service_delivery'
      },
      metadata: {
        created: new Date(),
        modified: new Date(),
        version: 1,
        verified: false,
        lastVerified: new Date(),
        hash: this.calculateHash(origin)
      }
    };

    this.records.set(entityId, record);
  }

  async recordCustodyTransfer(
    entityId: string,
    from: string,
    to: string,
    reason: string,
    approvedBy: string
  ): Promise<void> {
    const record = this.records.get(entityId);
    if (!record) throw new Error(`Provenance record not found: ${entityId}`);

    record.custodyChain.push({
      from,
      to,
      timestamp: new Date(),
      reason,
      method: 'transfer',
      approvedBy
    });

    record.metadata.version++;
    record.metadata.modified = new Date();
  }

  async recordTransformation(
    entityId: string,
    transformation: string,
    performedBy: string,
    system: string
  ): Promise<void> {
    const record = this.records.get(entityId);
    if (!record) throw new Error(`Provenance record not found: ${entityId}`);

    record.transformations.push({
      id: `TRANS_${Date.now()}`,
      timestamp: new Date(),
      transformation,
      performedBy,
      system
    });

    record.metadata.version++;
    record.metadata.modified = new Date();
  }

  async recordAccess(
    entityId: string,
    accessedBy: string,
    accessMethod: string,
    purpose: string
  ): Promise<void> {
    const record = this.records.get(entityId);
    if (!record) throw new Error(`Provenance record not found: ${entityId}`);

    record.accessHistory.push({
      timestamp: new Date(),
      accessedBy,
      accessMethod,
      purpose
    });

    record.metadata.modified = new Date();
  }

  async getProvenance(entityId: string): Promise<ProvenanceRecord | undefined> {
    return this.records.get(entityId);
  }

  async verifyProvenance(entityId: string): Promise<boolean> {
    const record = this.records.get(entityId);
    if (!record) return false;

    // Verify custody chain integrity
    for (const transfer of record.custodyChain) {
      if (!this.verifyTransfer(transfer)) {
        return false;
      }
    }

    // Verify transformations
    for (const transform of record.transformations) {
      if (!this.verifyTransformation(transform)) {
        return false;
      }
    }

    record.metadata.verified = true;
    record.metadata.lastVerified = new Date();

    return true;
  }

  private calculateHash(data: any): string {
    const crypto = require('crypto');
    return crypto
      .createHash('sha256')
      .update(JSON.stringify(data))
      .digest('hex');
  }

  private verifyTransfer(transfer: CustodyTransfer): boolean {
    // Verify transfer was authorized and logged
    return transfer.approvedBy !== undefined;
  }

  private verifyTransformation(transform: TransformationRecord): boolean {
    // Verify transformation was logged and traceable
    return transform.performedBy !== undefined && transform.system !== undefined;
  }
}
```

---

## Lineage Visualization

### Graph Visualization

```typescript
// data-lineage/visualization/graph.ts

export interface LineageVisualization {
  nodes: VisualNode[];
  edges: VisualEdge[];
  layout: LayoutConfig;
  legend: LegendItem[];
}

export interface VisualNode {
  id: string;
  label: string;
  type: NodeType;
  position: { x: number; y: number };
  size: number;
  color: string;
  icon?: string;
  metadata: {
    system: string;
    owner: string;
    lastModified: Date;
  };
}

export interface VisualEdge {
  id: string;
  from: string;
  to: string;
  type: EdgeType;
  label?: string;
  style: EdgeStyle;
  animated?: boolean;
}

export type EdgeStyle = 'solid' | 'dashed' | 'dotted';

export interface LayoutConfig {
  type: 'hierarchical' | 'force' | 'circular' | 'grid';
  direction: 'TB' | 'BT' | 'LR' | 'RL'; // Top-Bottom, Bottom-Top, Left-Right, Right-Left
  levelSpacing: number;
  nodeSpacing: number;
}

export interface LegendItem {
  type: string;
  label: string;
  color: string;
}

export class LineageVisualizationService {
  private nodeColors: Record<NodeType, string> = {
    [NodeType.SOURCE_TABLE]: '#4CAF50',
    [NodeType.SOURCE_VIEW]: '#81C784',
    [NodeType.SOURCE_FILE]: '#AED581',
    [NodeType.SOURCE_API]: '#C5E1A5',
    [NodeType.SOURCE_MESSAGE]: '#DCEDC8',
    [NodeType.TRANSFORMATION]: '#FF9800',
    [NodeType.VALIDATION]: '#FFB74D',
    [NodeType.ENRICHMENT]: '#FFCC80',
    [NodeType.TABLE]: '#2196F3',
    [NodeType.VIEW]: '#64B5F6',
    [NodeType.MATERIALIZED_VIEW]: '#42A5F5',
    [NodeType.CACHE]: '#90CAF9',
    [NodeType.REPORT]: '#9C27B0',
    [NodeType.EXPORT]: '#BA68C8',
    [NodeType.API_ENDPOINT]: '#AB47BC',
    [NodeType.NOTIFICATION]: '#CE93D8'
  };

  visualize(
    graph: LineageGraph,
    focusNode?: string
  ): LineageVisualization {
    const nodes = this.createVisualNodes(graph, focusNode);
    const edges = this.createVisualEdges(graph, focusNode);

    return {
      nodes,
      edges,
      layout: {
        type: 'hierarchical',
        direction: 'LR',
        levelSpacing: 100,
        nodeSpacing: 50
      },
      legend: this.createLegend()
    };
  }

  private createVisualNodes(
    graph: LineageGraph,
    focusNode?: string
  ): VisualNode[] {
    const nodes: VisualNode[] = [];

    for (const node of graph.nodes) {
      // If focus node specified, only include related nodes
      if (focusNode && !this.isRelatedTo(graph, node.id, focusNode)) {
        continue;
      }

      nodes.push({
        id: node.id,
        label: node.name,
        type: node.type,
        position: { x: 0, y: 0 }, // Will be calculated by layout engine
        size: this.calculateNodeSize(node, focusNode),
        color: this.nodeColors[node.type] || '#9E9E9E',
        icon: this.getNodeIcon(node.type),
        metadata: {
          system: node.system,
          owner: node.metadata.owner,
          lastModified: node.metadata.modified
        }
      });
    }

    return nodes;
  }

  private createVisualEdges(
    graph: LineageGraph,
    focusNode?: string
  ): VisualEdge[] {
    const edges: VisualEdge[] = [];

    for (const edge of graph.edges) {
      // If focus node specified, only include related edges
      if (focusNode && edge.from !== focusNode && edge.to !== focusNode) {
        // Check if edge is on path to/from focus node
        if (!this.isRelatedTo(graph, edge.from, focusNode) &&
            !this.isRelatedTo(graph, edge.to, focusNode)) {
          continue;
        }
      }

      edges.push({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        type: edge.type,
        label: edge.fields?.map(f => `${f.source} → ${f.target}`).join(', '),
        style: this.getEdgeStyle(edge.type),
        animated: edge.type === EdgeType.DATA_FLOW
      });
    }

    return edges;
  }

  private isRelatedTo(graph: LineageGraph, nodeId: string, focusNodeId: string): boolean {
    if (nodeId === focusNodeId) return true;

    // Check if upstream
    const visited = new Set<string>();
    const queue = [focusNodeId];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current === nodeId) return true;
      if (visited.has(current)) continue;
      visited.add(current);

      const incomingEdges = graph.edges.filter(e => e.to === current);
      for (const edge of incomingEdges) {
        queue.push(edge.from);
      }
    }

    // Check if downstream
    visited.clear();
    queue.push(focusNodeId);

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current === nodeId) return true;
      if (visited.has(current)) continue;
      visited.add(current);

      const outgoingEdges = graph.edges.filter(e => e.from === current);
      for (const edge of outgoingEdges) {
        queue.push(edge.to);
      }
    }

    return false;
  }

  private calculateNodeSize(node: LineageNode, focusNode?: string): number {
    const baseSize = 40;
    const focusBonus = focusNode === node.id ? 20 : 0;
    return baseSize + focusBonus;
  }

  private getNodeIcon(type: NodeType): string {
    const icons: Record<NodeType, string> = {
      [NodeType.SOURCE_TABLE]: 'table',
      [NodeType.SOURCE_VIEW]: 'eye',
      [NodeType.SOURCE_FILE]: 'file',
      [NodeType.SOURCE_API]: 'cloud',
      [NodeType.SOURCE_MESSAGE]: 'message',
      [NodeType.TRANSFORMATION]: 'transform',
      [NodeType.VALIDATION]: 'check-circle',
      [NodeType.ENRICHMENT]: 'plus-circle',
      [NodeType.TABLE]: 'database',
      [NodeType.VIEW]: 'eye',
      [NodeType.MATERIALIZED_VIEW]: 'star',
      [NodeType.CACHE]: 'bolt',
      [NodeType.REPORT]: 'file-text',
      [NodeType.EXPORT]: 'download',
      [NodeType.API_ENDPOINT]: 'api',
      [NodeType.NOTIFICATION]: 'bell'
    };

    return icons[type] || 'circle';
  }

  private getEdgeStyle(type: EdgeType): EdgeStyle {
    switch (type) {
      case EdgeType.DATA_FLOW:
        return 'solid';
      case EdgeType.TRANSFORM:
        return 'solid';
      case EdgeType.VALIDATE:
        return 'dashed';
      case EdgeType.DEPENDENCY:
        return 'dotted';
      default:
        return 'solid';
    }
  }

  private createLegend(): LegendItem[] {
    return [
      { type: 'source', label: 'Data Sources', color: this.nodeColors[NodeType.SOURCE_TABLE] },
      { type: 'transform', label: 'Transformations', color: this.nodeColors[NodeType.TRANSFORMATION] },
      { type: 'storage', label: 'Data Storage', color: this.nodeColors[NodeType.TABLE] },
      { type: 'output', label: 'Data Output', color: this.nodeColors[NodeType.REPORT] }
    ];
  }
}
```

---

## Automated Capture

### Automatic Lineage Capture

```typescript
// data-lineage/capture/automatic.ts

export class LineageCaptureService {
  private graph: LineageGraph;
  private parsers: Map<string, QueryParser> = new Map();

  constructor() {
    this.graph = {
      id: 'main_lineage_graph',
      name: 'Travel Agency Data Lineage',
      domain: 'travel_agency',
      nodes: [],
      edges: [],
      metadata: {
        version: 1,
        created: new Date(),
        modified: new Date(),
        lastAnalyzed: new Date()
      }
    };

    this.registerParsers();
  }

  async captureFromQuery(
    query: string,
    sourceSystem: string
  ): Promise<void> {
    const parser = this.getParser(sourceSystem);
    const parsed = parser.parse(query);

    // Add or update source nodes
    for (const source of parsed.sources) {
      await this.ensureNode(source, NodeType.SOURCE_TABLE, sourceSystem);
    }

    // Add or update target node
    const targetNode = await this.ensureNode(
      parsed.target,
      NodeType.TABLE,
      sourceSystem
    );

    // Add edges for column mappings
    for (const mapping of parsed.columnMappings) {
      await this.ensureEdge(
        mapping.source,
        parsed.target,
        EdgeType.TRANSFORM,
        mapping
      );
    }

    this.graph.metadata.lastAnalyzed = new Date();
  }

  async captureFromTransformation(
    transformationId: string,
    config: TransformationConfig
  ): Promise<void> {
    // Add transformation node
    const transformNode: LineageNode = {
      id: transformationId,
      name: config.name,
      type: NodeType.TRANSFORMATION,
      system: config.system,
      attributes: {
        type: config.type,
        description: config.description
      },
      metadata: {
        created: new Date(),
        modified: new Date(),
        owner: config.owner,
        tags: config.tags || []
      }
    };

    this.upsertNode(transformNode);

    // Connect sources to transformation
    for (const source of config.sources) {
      await this.ensureEdge(
        source,
        transformationId,
        EdgeType.TRANSFORM
      );
    }

    // Connect transformation to targets
    for (const target of config.targets) {
      await this.ensureEdge(
        transformationId,
        target,
        EdgeType.TRANSFORM
      );
    }
  }

  async captureFromAPICall(
    endpoint: string,
    request: APIRequest,
    response: APIResponse
  ): Promise<void> {
    const nodeId = `api_${endpoint.replace(/\//g, '_')}`;

    // Add API node if not exists
    await this.ensureNode(
      nodeId,
      NodeType.API_ENDPOINT,
      'api'
    );

    // Track data flow from request fields to response fields
    for (const [responseField, source] of Object.entries(response.fieldMappings)) {
      await this.ensureEdge(
        source.nodeId,
        nodeId,
        EdgeType.TRANSFORM,
        { source: source.field, target: responseField }
      );
    }
  }

  private async ensureNode(
    name: string,
    type: NodeType,
    system: string,
    attributes?: Record<string, any>
  ): Promise<LineageNode> {
    let node = this.graph.nodes.find(n => n.name === name && n.system === system);

    if (!node) {
      node = {
        id: `node_${name}_${system}_${Date.now()}`,
        name,
        type,
        system,
        attributes: attributes || {},
        metadata: {
          created: new Date(),
          modified: new Date(),
          owner: 'system',
          tags: []
        }
      };

      this.graph.nodes.push(node);
    }

    return node;
  }

  private async ensureEdge(
    fromName: string,
    toName: string,
    type: EdgeType,
    fieldMapping?: FieldMapping
  ): Promise<void> {
    const fromNode = this.graph.nodes.find(n => n.name === fromName);
    const toNode = this.graph.nodes.find(n => n.name === toName);

    if (!fromNode || !toNode) {
      throw new Error(`Cannot create edge: nodes not found`);
    }

    let edge = this.graph.edges.find(e => e.from === fromNode.id && e.to === toNode.id);

    if (!edge) {
      edge = {
        id: `edge_${fromNode.id}_${toNode.id}_${Date.now()}`,
        from: fromNode.id,
        to: toNode.id,
        type,
        fields: fieldMapping ? [fieldMapping] : undefined,
        metadata: {
          created: new Date(),
          createdBy: 'system'
        }
      };

      this.graph.edges.push(edge);
    } else if (fieldMapping) {
      edge.fields = edge.fields || [];
      if (!edge.fields.some(f => f.source === fieldMapping.source && f.target === fieldMapping.target)) {
        edge.fields.push(fieldMapping);
      }
    }
  }

  private upsertNode(node: LineageNode): void {
    const existing = this.graph.nodes.find(n => n.id === node.id);
    if (existing) {
      Object.assign(existing, node);
    } else {
      this.graph.nodes.push(node);
    }
  }

  private registerParsers(): void {
    this.parsers.set('postgresql', new PostgreSQLParser());
    this.parsers.set('mysql', new MySQLParser());
    this.parsers.set('spark', new SparkParser());
  }

  private getParser(system: string): QueryParser {
    return this.parsers.get(system) || new GenericParser();
  }

  getGraph(): LineageGraph {
    return this.graph;
  }
}

export interface TransformationConfig {
  name: string;
  type: string;
  system: string;
  sources: string[];
  targets: string[];
  owner: string;
  description?: string;
  tags?: string[];
}

export interface APIRequest {
  endpoint: string;
  fields: Record<string, any>;
}

export interface APIResponse {
  fieldMappings: Record<string, { nodeId: string; field: string }>;
}

// Query Parser Interface
interface QueryParser {
  parse(query: string): ParsedQuery;
}

interface ParsedQuery {
  sources: string[];
  target: string;
  columnMappings: FieldMapping[];
  type: 'select' | 'insert' | 'update' | 'delete' | 'create';
}

class PostgreSQLParser implements QueryParser {
  parse(query: string): ParsedQuery {
    // Parse SQL query for lineage
    // Simplified implementation
    return {
      sources: this.extractSources(query),
      target: this.extractTarget(query),
      columnMappings: this.extractMappings(query),
      type: this.getQueryType(query)
    };
  }

  private extractSources(query: string): string[] {
    const fromMatch = query.match(/FROM\s+([^\s,]+)/gi);
    const joinMatch = query.match(/JOIN\s+([^\s,]+)/gi);

    const sources: string[] = [];

    if (fromMatch) {
      sources.push(...fromMatch.map(m => m.replace(/FROM\s+/i, '')));
    }

    if (joinMatch) {
      sources.push(...joinMatch.map(m => m.replace(/JOIN\s+/i, '')));
    }

    return [...new Set(sources)];
  }

  private extractTarget(query: string): string {
    const insertMatch = query.match(/INSERT\s+INTO\s+([^\s(]+)/i);
    const createMatch = query.match(/CREATE\s+TABLE\s+([^\s(]+)/i);
    const updateMatch = query.match(/UPDATE\s+([^\s,]+)/i);

    return insertMatch?.[1] || createMatch?.[1] || updateMatch?.[1] || '';
  }

  private extractMappings(query: string): FieldMapping[] {
    // Extract column mappings from SELECT clause
    const selectMatch = query.match(/SELECT\s+(.*?)\s+FROM/i);
    if (!selectMatch) return [];

    const selectClause = selectMatch[1];
    const mappings: FieldMapping[] = [];

    // Simple parsing for "column" or "table.column" or "alias"
    const columns = selectClause.split(',').map(c => c.trim());

    for (const column of columns) {
      const parts = column.split(/\s+AS\s+/i);
      const source = parts[0].trim();
      const target = parts[1]?.trim() || source.split('.').pop() || source;

      mappings.push({ source, target });
    }

    return mappings;
  }

  private getQueryType(query: string): ParsedQuery['type'] {
    if (query.trim().toUpperCase().startsWith('SELECT')) return 'select';
    if (query.trim().toUpperCase().startsWith('INSERT')) return 'insert';
    if (query.trim().toUpperCase().startsWith('UPDATE')) return 'update';
    if (query.trim().toUpperCase().startsWith('DELETE')) return 'delete';
    if (query.trim().toUpperCase().startsWith('CREATE')) return 'create';
    return 'select';
  }
}

class GenericParser implements QueryParser {
  parse(query: string): ParsedQuery {
    return {
      sources: [],
      target: '',
      columnMappings: [],
      type: 'select'
    };
  }
}

class MySQLParser extends PostgreSQLParser {}
class SparkParser extends PostgreSQLParser {}
```

---

## Cross-System Lineage

### Cross-System Tracking

```typescript
// data-lineage/cross-system/tracker.ts

export interface CrossSystemLineage {
  id: string;
  source: SystemEndpoint;
  destination: SystemEndpoint;
  pathway: DataPathway[];
  transformations: CrossSystemTransformation[];
  handoffs: HandoffPoint[];
  metadata: CrossSystemMetadata;
}

export interface SystemEndpoint {
  system: string;
  systemType: 'database' | 'api' | 'message_queue' | 'file' | 'data_warehouse';
  endpoint: string;
  schema?: string;
  table?: string;
}

export interface DataPathway {
  id: string;
  type: 'sync' | 'async' | 'batch';
  protocol: string;
  frequency?: string;
  reliability: 'at_least_once' | 'at_most_once' | 'exactly_once';
}

export interface CrossSystemTransformation {
  id: string;
  location: 'source' | 'intermediate' | 'destination';
  transformation: string;
  system: string;
}

export interface HandoffPoint {
  id: string;
  from: string;
  to: string;
  mechanism: 'api_call' | 'message_queue' | 'file_transfer' | 'database_link';
  format: string;
  encryption: boolean;
}

export interface CrossSystemMetadata {
  created: Date;
  modified: Date;
  owner: string;
  sla: SLAInfo;
  compliance: ComplianceInfo;
}

export interface SLAInfo {
  latency: string;
  throughput: string;
  availability: string;
}

export class CrossSystemLineageService {
  private crossSystemPaths: Map<string, CrossSystemLineage> = new Map();

  async trackDataFlow(
    source: SystemEndpoint,
    destination: SystemEndpoint,
    pathway: DataPathway
  ): Promise<void> {
    const pathId = this.generatePathId(source, destination);

    const lineage: CrossSystemLineage = {
      id: pathId,
      source,
      destination,
      pathway: [pathway],
      transformations: [],
      handoffs: [],
      metadata: {
        created: new Date(),
        modified: new Date(),
        owner: 'data-architecture',
        sla: {
          latency: '< 5s',
          throughput: '1000 req/s',
          availability: '99.9%'
        },
        compliance: {
          classification: 'internal',
          retention: '7_years',
          privacy: false,
          gdprRelevant: false
        }
      }
    };

    this.crossSystemPaths.set(pathId, lineage);
  }

  async addHandoff(
    pathId: string,
    from: string,
    to: string,
    mechanism: HandoffPoint['mechanism'],
    format: string
  ): Promise<void> {
    const lineage = this.crossSystemPaths.get(pathId);
    if (!lineage) throw new Error(`Path not found: ${pathId}`);

    lineage.handoffs.push({
      id: `handoff_${Date.now()}`,
      from,
      to,
      mechanism,
      format,
      encryption: true
    });

    lineage.metadata.modified = new Date();
  }

  async getCrossSystemImpact(
    system: string,
    changeType: 'modify' | 'deprecate' | 'decommission'
  ): Promise<CrossSystemImpact> {
    const affectedPaths = Array.from(this.crossSystemPaths.values()).filter(
      p => p.source.system === system || p.destination.system === system
    );

    const upstreamSystems = new Set<string>();
    const downstreamSystems = new Set<string>();

    for (const path of affectedPaths) {
      if (path.destination.system === system) {
        upstreamSystems.add(path.source.system);
      }
      if (path.source.system === system) {
        downstreamSystems.add(path.destination.system);
      }
    }

    return {
      system,
      changeType,
      affectedPaths: affectedPaths.length,
      upstreamSystems: Array.from(upstreamSystems),
      downstreamSystems: Array.from(downstreamSystems),
      recommendedActions: this.generateActionRecommendations(
        system,
        changeType,
        upstreamSystems,
        downstreamSystems
      )
    };
  }

  private generatePathId(source: SystemEndpoint, destination: SystemEndpoint): string {
    return `${source.system}_to_${destination.system}`.replace(/\s+/g, '_');
  }

  private generateActionRecommendations(
    system: string,
    changeType: string,
    upstreamSystems: Set<string>,
    downstreamSystems: Set<string>
  ): string[] {
    const recommendations: string[] = [];

    if (changeType === 'decommission') {
      recommendations.push(`Establish data migration plan for ${downstreamSystems.size} downstream systems.`);
      recommendations.push(`Notify ${upstreamSystems.size} upstream systems of endpoint changes.`);
    }

    if (changeType === 'modify') {
      recommendations.push('Coordinate API versioning with all dependent systems.');
      recommendations.push('Run integration tests with all connected systems.');
    }

    recommendations.push('Update cross-system SLAs if latency/throughput changes.');
    recommendations.push('Review data retention policies across affected systems.');

    return recommendations;
  }
}

export interface CrossSystemImpact {
  system: string;
  changeType: string;
  affectedPaths: number;
  upstreamSystems: string[];
  downstreamSystems: string[];
  recommendedActions: string[];
}
```

---

## API Specification

### Data Lineage API

```typescript
// api/data-lineage/routes.ts

import { z } from 'zod';

// Schemas
const LineageNodeSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  system: z.string(),
  metadata: z.object({
    created: z.date(),
    modified: z.date(),
    owner: z.string()
  })
});

const LineageEdgeSchema = z.object({
  id: z.string(),
  from: z.string(),
  to: z.string(),
  type: z.string(),
  fields: z.array(z.object({
    source: z.string(),
    target: z.string()
  }))
});

const LineageGraphSchema = z.object({
  id: z.string(),
  name: z.string(),
  nodes: z.array(LineageNodeSchema),
  edges: z.array(LineageEdgeSchema)
});

const ColumnLineageSchema = z.object({
  columnId: z.string(),
  name: z.string(),
  sources: z.array(z.object({
    source: z.string(),
    field: z.string(),
    confidence: z.number()
  })),
  transformations: z.array(z.object({
    type: z.string(),
    expression: z.string(),
    inputs: z.array(z.string()),
    outputs: z.array(z.string())
  }))
});

const ImpactAnalysisRequestSchema = z.object({
  nodeType: z.enum(['table', 'column', 'transformation']),
  nodeId: z.string(),
  changeType: z.enum(['add', 'modify', 'delete']),
  changes: z.array(z.object({
    field: z.string(),
    changeType: z.enum(['add', 'modify', 'delete', 'rename']),
    oldValue: z.any().optional(),
    newValue: z.any().optional()
  }))
});

const ImpactAnalysisResultSchema = z.object({
  nodeId: z.string(),
  changeType: z.string(),
  impacts: z.array(z.object({
    targetId: z.string(),
    targetName: z.string(),
    severity: z.enum(['critical', 'high', 'medium', 'low']),
    impact: z.string(),
    affectedFields: z.array(z.string())
  })),
  summary: z.object({
    totalImpacts: z.number(),
    criticalImpacts: z.number(),
    affectedSystems: z.array(z.string())
  }),
  recommendations: z.array(z.string())
});

// Routes
export const dataLineageRoutes = {
  // Graph Management
  'GET /api/lineage/graph': {
    summary: 'Get full lineage graph',
    query: z.object({
      domain: z.string().optional(),
      system: z.string().optional()
    }),
    response: LineageGraphSchema
  },

  'GET /api/lineage/graph/:nodeId': {
    summary: 'Get lineage for specific node',
    params: z.object({
      nodeId: z.string()
    }),
    query: z.object({
      direction: z.enum(['upstream', 'downstream', 'both']),
      depth: z.number().default(3)
    }),
    response: LineageGraphSchema
  },

  // Column Lineage
  'GET /api/lineage/column/:table/:column': {
    summary: 'Get column lineage',
    params: z.object({
      table: z.string(),
      column: z.string()
    }),
    response: ColumnLineageSchema
  },

  'POST /api/lineage/column/trace': {
    summary: 'Trace lineage for multiple columns',
    request: z.object({
      columns: z.array(z.object({
        table: z.string(),
        column: z.string()
      }))
    }),
    response: z.array(ColumnLineageSchema)
  },

  // Impact Analysis
  'POST /api/lineage/impact': {
    summary: 'Analyze impact of proposed change',
    request: ImpactAnalysisRequestSchema,
    response: ImpactAnalysisResultSchema
  },

  'GET /api/lineage/impact/:nodeId': {
    summary: 'Get downstream dependencies',
    params: z.object({
      nodeId: z.string()
    }),
    response: z.object({
      nodeId: z.string(),
      downstream: z.array(z.object({
        id: z.string(),
        name: z.string(),
        type: z.string(),
        distance: z.number()
      }))
    })
  },

  // Source-to-Target Mappings
  'GET /api/lineage/mappings': {
    summary: 'List all source-to-target mappings',
    query: z.object({
      sourceSystem: z.string().optional(),
      targetSystem: z.string().optional(),
      active: z.boolean().optional()
    }),
    response: z.array(z.object({
      id: z.string(),
      name: z.string(),
      source: z.object({
        system: z.string(),
        table: z.string()
      }),
      target: z.object({
        system: z.string(),
        table: z.string()
      })
    }))
  },

  'GET /api/lineage/mappings/:mappingId': {
    summary: 'Get mapping details',
    params: z.object({
      mappingId: z.string()
    }),
    response: z.any() // SourceToTargetMapping
  },

  // Provenance
  'GET /api/lineage/provenance/:entityType/:entityId': {
    summary: 'Get data provenance',
    params: z.object({
      entityType: z.string(),
      entityId: z.string()
    }),
    response: z.object({
      id: z.string(),
      origin: z.object({
        source: z.string(),
        timestamp: z.date(),
        consent: z.boolean()
      }),
      custodyChain: z.array(z.object({
        from: z.string(),
        to: z.string(),
        timestamp: z.date()
      })),
      transformations: z.array(z.object({
        transformation: z.string(),
        timestamp: z.date()
      }))
    })
  },

  // Visualization
  'GET /api/lineage/visualize/:nodeId': {
    summary: 'Get lineage visualization data',
    params: z.object({
      nodeId: z.string()
    }),
    query: z.object({
      depth: z.number().default(2),
      direction: z.enum(['upstream', 'downstream', 'both'])
    }),
    response: z.object({
      nodes: z.array(z.object({
        id: z.string(),
        label: z.string(),
        type: z.string(),
        position: z.object({
          x: z.number(),
          y: z.number()
        }),
        color: z.string()
      })),
      edges: z.array(z.object({
        id: z.string(),
        from: z.string(),
        to: z.string(),
        label: z.string().optional()
      }))
    })
  },

  // Cross-System
  'GET /api/lineage/cross-system': {
    summary: 'List cross-system data flows',
    query: z.object({
      sourceSystem: z.string().optional(),
      targetSystem: z.string().optional()
    }),
    response: z.array(z.object({
      id: z.string(),
      source: z.object({
        system: z.string(),
        systemType: z.string()
      }),
      destination: z.object({
        system: z.string(),
        systemType: z.string()
      }),
      pathway: z.array(z.object({
        type: z.string(),
        protocol: z.string()
      }))
    }))
  },

  'POST /api/lineage/cross-system/impact': {
    summary: 'Analyze cross-system impact',
    request: z.object({
      system: z.string(),
      changeType: z.enum(['modify', 'deprecate', 'decommission'])
    }),
    response: z.object({
      system: z.string(),
      affectedPaths: z.number(),
      upstreamSystems: z.array(z.string()),
      downstreamSystems: z.array(z.string()),
      recommendedActions: z.array(z.string())
    })
  }
};
```

---

## Testing Scenarios

### Data Lineage Tests

```typescript
// tests/data-lineage/scenarios.ts

interface TestScenario {
  name: string;
  description: string;
  test: () => Promise<void>;
}

export const dataLineageTests: TestScenario[] = [
  {
    name: 'Column Lineage Tracing',
    description: 'Trace column from source to destination',
    test: async () => {
      const service = new ColumnLineageService(mockGraph);
      const lineage = await service.getColumnLineage('bookings', 'customer_email');

      expect(lineage.sources.length).toBeGreaterThan(0);
      expect(lineage.sources[0].source).toBe('customer_inquiries');
    }
  },

  {
    name: 'Impact Analysis - Column Delete',
    description: 'Analyze impact of deleting a column',
    test: async () => {
      const service = new ImpactAnalysisService(mockGraph);
      const result = await service.analyzeImpact({
        nodeType: 'column',
        nodeId: 'bookings.customer_email',
        changeType: 'delete',
        changes: [{ field: 'customer_email', changeType: 'delete' }]
      });

      expect(result.impacts.length).toBeGreaterThan(0);
      expect(result.summary.criticalImpacts).toBe(0);
    }
  },

  {
    name: 'Provenance Tracking',
    description: 'Track data origin and custody',
    test: async () => {
      const service = new DataProvenanceService();
      await service.trackOrigin('booking-123', 'booking', {
        source: 'customer@example.com',
        sourceType: 'customer',
        timestamp: new Date(),
        method: 'email',
        consent: true
      });

      const provenance = await service.getProvenance('booking-123');
      expect(provenance).toBeDefined();
      expect(provenance!.origin.source).toBe('customer@example.com');
    }
  },

  {
    name: 'Cross-System Impact',
    description: 'Analyze cross-system dependencies',
    test: async () => {
      const service = new CrossSystemLineageService();
      const impact = await service.getCrossSystemImpact('workspace', 'modify');

      expect(impact.downstreamSystems).toBeDefined();
      expect(impact.recommendedActions).toBeDefined();
    }
  }
];
```

---

## Metrics & Monitoring

### Data Lineage KPIs

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| **Lineage Coverage** | % of tables with documented lineage | 100% | < 95% |
| **Column Coverage** | % of columns with column-level lineage | > 80% | < 70% |
| **Graph Freshness** | Time since last lineage update | < 24 hours | > 48 hours |
| **Impact Analysis Accuracy** | % of predicted impacts that occur | > 90% | < 85% |
| **Provenance Completeness** | % of entities with origin tracked | 100% | < 95% |

### Dashboard Queries

```promql
# Lineage coverage percentage
(sum(lineage_nodes) by (system) > 0) / sum(tables) by (system) * 100

# Cross-system data flows
sum(cross_system_flows) by (source_system, target_system)

# Impact analysis requests
rate(lineage_impact_analysis_requests_total[5m])

# Lineage graph size
lineage_graph_nodes{domain="travel_agency"}
lineage_graph_edges{domain="travel_agency"}
```

---

**Document Version:** 1.0

**Last Updated:** 2026-04-26

**Related Documents:**
- [DATA_GOVERNANCE_MASTER_INDEX.md](./DATA_GOVERNANCE_MASTER_INDEX.md)
- [DATA_GOVERNANCE_01_QUALITY.md](./DATA_GOVERNANCE_01_QUALITY.md)
- [DATA_GOVERNANCE_03_CATALOG.md](./DATA_GOVERNANCE_03_CATALOG.md) - Next document
