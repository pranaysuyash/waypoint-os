# Document Generation — Storage, Versioning & Management

> Research document for document lifecycle management, storage, retrieval, and archival.

---

## Key Questions

1. **Where should generated documents be stored (S3, GCS, database)?**
2. **How do we version documents and track which version was sent to whom?**
3. **What's the retrieval UX — how do agents and customers find past documents?**
4. **What are the retention and deletion policies per document type?**
5. **How do we handle regulatory requirements for document archival?**

---

## Research Areas

### Document Storage Architecture

```typescript
interface DocumentStorage {
  storageType: 'object_storage' | 'database' | 'hybrid';
  provider: string;              // S3, GCS, etc.
  pathTemplate: string;          // e.g., /{brandId}/{year}/{month}/{tripId}/{documentType}/
  retention: RetentionPolicy;
  encryption: EncryptionConfig;
  backup: BackupConfig;
  cdn: CDNConfig;
}

interface RetentionPolicy {
  documentType: DocumentType;
  retainFor: string;             // e.g., "7_years", "trip_plus_90_days", "indefinite"
  autoDelete: boolean;
  archiveAfter: string;          // Move to cold storage after
  legalHold: boolean;            // Freeze deletion if under legal hold
}

// Retention by type:
// Invoices: 7 years (tax law)
// Contracts: 7 years after termination
// Itineraries: Trip dates + 90 days
// Quotes: 1 year
// Vouchers: Trip dates + 30 days
// Insurance policies: Policy term + 5 years
// Internal reports: 3 years
```

### Document Versioning

```typescript
interface DocumentVersion {
  documentId: string;
  tripId: string;
  type: DocumentType;
  version: number;
  generatedAt: Date;
  generatedBy: string;
  templateId: string;
  templateVersion: number;
  dataSnapshot: string;          // Reference to data used for generation
  diff?: DocumentDiff;           // What changed from previous version
  deliveries: DeliveryRecord[];
  isCurrent: boolean;
}

interface DocumentDiff {
  fromVersion: number;
  toVersion: number;
  sections: SectionDiff[];
  summary: string;
}

interface SectionDiff {
  section: string;
  changeType: 'added' | 'removed' | 'modified';
  description: string;
}
```

### Document Retrieval

```typescript
interface DocumentSearch {
  // Find documents by various criteria
  filters: {
    tripId?: string;
    customerId?: string;
    documentType?: DocumentType[];
    dateRange?: DateRange;
    status?: string;
    sentTo?: string;
  };
  // Full-text search within documents
  query?: string;
  sort: 'date_desc' | 'date_asc' | 'type';
  pagination: PaginationState;
}

interface DocumentAccessLog {
  documentId: string;
  accessedBy: string;
  accessType: 'view' | 'download' | 'print' | 'email' | 'delete';
  accessedAt: Date;
  ipAddress: string;
  userAgent?: string;
}
```

### Document Management Dashboard

**Agent-facing document management:**

```typescript
interface DocumentDashboard {
  // Recent documents
  recentDocuments: DocumentSummary[];
  // Pending generation
  pendingGeneration: GenerationQueueItem[];
  // Delivery tracking
  deliveryStatus: {
    sent: number;
    delivered: number;
    opened: number;
    pending: number;
    failed: number;
  };
  // Quick actions
  actions: ('regenerate' | 'resend' | 'download' | 'print' | 'archive')[];
}
```

---

## Open Problems

1. **Storage cost optimization** — PDFs with images can be 5-10MB each. At 10,000 trips/year with 5 documents each, that's 250GB-500GB of documents. Need tiered storage (hot → warm → cold).

2. **Version proliferation** — Each trip change generates new documents. A trip with 5 modifications creates 5 versions of each document. Need to keep them organized.

3. **Data snapshot vs. regeneration** — Should we regenerate documents on demand from current data, or store the exact data snapshot used at generation time? Snapshots guarantee accuracy but use more storage.

4. **Cross-reference between documents and bookings** — A voucher references a booking. If the booking changes, how do we link the old voucher to the new booking state?

5. **GDPR/right-to-erasure** — Customer requests data deletion, but invoices must be retained for tax law. How to comply with both requirements?

---

## Next Steps

- [ ] Design document storage architecture with tiered retention
- [ ] Research object storage providers (S3, GCS) and lifecycle policies
- [ ] Create document versioning data model
- [ ] Design document management dashboard for agents
- [ ] Map retention requirements per document type by jurisdiction
- [ ] Design right-to-erasure workflow that respects retention obligations
