# Audit & Compliance — Data Lineage & Provenance

> Research document for tracking data flow, transformation, and provenance across the platform.

---

## Key Questions

1. **What data flows through the system, and what transformations occur?**
2. **How do we trace a piece of data from origin to current state?**
3. **What data lineage requirements exist for regulatory compliance?**
4. **How do we visualize data flows for debugging and compliance?**
5. **How do we track which data came from which supplier or customer?**

---

## Research Areas

### Data Lineage Model

```typescript
interface DataLineage {
  // A record of where data came from and how it was transformed
  lineageId: string;
  entityId: string;
  entityType: string;
  currentData: Record<string, unknown>;
  provenance: DataProvenance[];
  transformations: DataTransformation[];
}

interface DataProvenance {
  source: DataSource;
  fetchedAt: Date;
  rawData: Record<string, unknown>;
  confidence: number;
}

type DataSource =
  | { type: 'customer_input'; field: string; form: string }
  | { type: 'supplier_api'; supplier: string; endpoint: string }
  | { type: 'spine_extraction'; runId: string }
  | { type: 'agent_input'; agentId: string }
  | { type: 'system_generated'; algorithm: string }
  | { type: 'third_party'; provider: string }
  | { type: 'manual_import'; importedBy: string };

interface DataTransformation {
  step: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  transformation: string;
  performedAt: Date;
  performedBy: string;            // Service or agent
}
```

### Example: Customer Itinerary Data Lineage

```
Customer email (raw text)
  → Spine extraction (run_abc123)
    → Extracted: destination = "Singapore", dates = "Jun 15-20", budget = "₹80K"
      → Agent correction: budget changed to "₹1L"
        → Spine pricing: hotels fetched from supplier_api(marriott)
          → Spine pricing: hotels fetched from supplier_api(hilton)
            → Agent selects: Marriott + Singapore Airlines + transfer
              → Booking confirmation: trip finalized
```

### Provenance Queries

```typescript
interface LineageQuery {
  // "Where did this data come from?"
  entityType: string;
  entityId: string;
  field?: string;                 // Specific field, or all fields
  depth: number;                  // How many steps back
}

interface LineageResult {
  field: string;
  currentValue: unknown;
  provenanceChain: ProvenanceStep[];
}

interface ProvenanceStep {
  step: number;
  source: DataSource;
  value: unknown;
  transformation?: string;
  timestamp: Date;
}
```

---

## Open Problems

1. **Lineage storage overhead** — Storing full provenance for every data point is expensive. Need selective lineage tracking (critical fields only).

2. **Cross-system lineage** — Data flows from frontend → spine API → database → document generation. Tracking across system boundaries requires correlation IDs.

3. **Spine run lineage** — Spine processes extract and transform customer input through multiple stages. Each stage produces intermediate data that should be traceable.

4. **Data freshness vs. lineage** — When supplier data is updated, the lineage of the old data matters for historical accuracy. Need time-travel queries.

5. **Lineage for ML models** — If we use ML for recommendations or pricing, the training data lineage matters for model explainability and bias detection.

---

## Next Steps

- [ ] Design lineage tracking for spine run pipeline
- [ ] Map critical data flows that require provenance tracking
- [ ] Study data lineage tools (Apache Atlas, DataHub, OpenLineage)
- [ ] Design lineage query API for compliance team
- [ ] Implement correlation ID propagation across services
