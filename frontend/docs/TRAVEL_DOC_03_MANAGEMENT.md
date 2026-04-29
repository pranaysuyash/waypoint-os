# Travel Document Lifecycle — Storage, Versioning & Management

> Research document for document storage, version control, lifecycle management, expiry tracking, and compliance retention policies.

---

## Key Questions

1. **How do we store and organize documents across agencies and trips?**
2. **How do we version documents and track changes?**
3. **What lifecycle stages do travel documents go through?**
4. **What retention and deletion policies ensure compliance?**

---

## Research Areas

### Document Storage Architecture

```typescript
interface DocumentStore {
  // Storage path: /{agency_id}/{trip_id}/{document_type}/{version}/
  store(doc: GeneratedDocument): DocumentRef;
  retrieve(ref: DocumentRef): GeneratedDocument;
  list(filter: DocumentFilter): DocumentRef[];
  delete(ref: DocumentRef): void;
}

interface GeneratedDocument {
  id: string;
  type: TravelDocumentType;
  trip_id: string;
  booking_id: string | null;
  agency_id: string;

  // File
  filename: string;
  file_url: string;                    // cloud storage URL
  file_size_kb: number;
  page_count: number;
  content_hash: string;                // SHA-256 for integrity

  // Versioning
  version: number;
  previous_version_id: string | null;
  change_description: string | null;

  // Lifecycle
  status: DocumentLifecycleStatus;
  generated_at: string;
  expires_at: string | null;
  archived_at: string | null;
  deleted_at: string | null;

  // Access
  generated_by: string;                // agent or system
  access_log: DocumentAccessEntry[];

  // Delivery
  delivery_history: DocumentDelivery[];
}

type DocumentLifecycleStatus =
  | "DRAFT" | "FINAL" | "SENT" | "ACKNOWLEDGED"
  | "SUPERSEDED" | "ARCHIVED" | "EXPIRED" | "DELETED";

// ── Storage hierarchy ──
// ┌─────────────────────────────────────────────────────┐
// │  Agency A (tenant-isolated)                           │
// │  ├── Trip TP-101                                      │
// │  │   ├── itinerary/                                   │
// │  │   │   ├── v1.pdf (DRAFT, superseded)              │
// │  │   │   └── v2.pdf (FINAL, current)                 │
// │  │   ├── confirmation/                                │
// │  │   │   └── v1.pdf (SENT, acknowledged)             │
// │  │   ├── vouchers/                                    │
// │  │   │   ├── hotel_voucher.pdf                        │
// │  │   │   ├── activity_voucher_sentosa.pdf             │
// │  │   │   └── transfer_voucher.pdf                     │
// │  │   └── invoice/                                     │
// │  │       └── gst_invoice_001.pdf                      │
// │  └── Trip TP-102/...                                  │
// └─────────────────────────────────────────────────────┘
```

### Version Control & Diff Tracking

```typescript
interface DocumentVersion {
  document_id: string;
  version: number;
  created_at: string;
  created_by: string;
  change_type: "CREATED" | "UPDATED" | "CORRECTED" | "AMENDED";
  change_description: string;

  // Diff (for text-based content)
  diff_summary: string;                // "Added Day 5 activity, updated hotel name"
  changed_sections: string[];
}

// ── Version timeline ──
// ┌─────────────────────────────────────────────────────┐
// │  Itinerary for TP-101 — Version History              │
// │                                                       │
// │  v1  Apr 25 10:00  Draft (Agent: Ravi)              │
// │  v2  Apr 26 14:00  Updated (Agent: Ravi)            │
// │      Changes: Added Day 5 activities                │
// │      Changes: Updated hotel to 4★                  │
// │      Changes: Fixed restaurant reservation time     │
// │  v3  Apr 27 09:00  Customer approved                │
// │      Changes: Removed Day 3 museum (customer req)  │
// │      Status: SENT → customer via WhatsApp           │
// │                                                       │
// │  Current: v3 | Total changes: 5 sections modified   │
// └─────────────────────────────────────────────────────┘
```

### Expiry & Retention Management

```typescript
interface DocumentRetentionPolicy {
  document_type: TravelDocumentType;
  retention_period: string;            // "7_YEARS", "3_YEARS", "1_YEAR", "TRIP_PLUS_90_DAYS"
  auto_archive_after: string;          // "TRIP_END"
  auto_delete_after: string;           // retention_period from archive date
  legal_hold: boolean;                 // prevent deletion if under legal hold

  // India-specific compliance
  gst_retention: "8_YEARS";            // GST records must be kept 8 years
  tds_retention: "8_YEARS";            // TDS records 8 years
  invoice_retention: "8_YEARS";
  contract_retention: "5_YEARS_AFTER_EXPIRY";
  customer_data_retention: "AS_PER_CONSENT";
}

// ── Expiry tracking dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Document Expiry Alerts                               │
// │                                                       │
// │  Expiring in 7 days:                                  │
// │  ├── Hotel voucher (TP-101) — expires May 5         │
// │  └── Insurance certificate (TP-205) — expires May 3 │
// │                                                       │
// │  Expiring in 30 days:                                 │
// │  ├── Visa (TP-312) — expires May 28                 │
// │  └── Passport (Priya Sharma) — expires May 30       │
// │                                                       │
// │  Auto-archive scheduled:                              │
// │  ├── 15 completed trips → archive next Monday       │
// │  └── 200+ documents older than 3 years              │
// └─────────────────────────────────────────────────────┘
```

### Search & Retrieval

```typescript
interface DocumentSearch {
  query(text: string, filters: DocumentFilter): SearchResult;
}

interface DocumentFilter {
  agency_id: string;
  trip_id?: string;
  document_type?: TravelDocumentType[];
  status?: DocumentLifecycleStatus[];
  date_range?: DateRange;
  generated_by?: string;
  tags?: string[];
}

// Full-text search index:
// - Document metadata (type, trip, dates, customer)
// - Extracted text from PDF (OCR for scanned documents)
// - Content hash for deduplication
```

---

## Open Problems

1. **Storage cost at scale** — A single trip may generate 10+ documents across versions. With 1000+ trips/year, storage grows rapidly. Need tiered storage (hot/warm/cold).

2. **Content hash integrity** — Documents can be tampered with if storage is compromised. Need content hash verification for legal documents.

3. **Cross-tenant data leakage** — Strict tenant isolation at the storage level is critical. A misconfigured path could expose one agency's documents to another.

4. **Retention vs. legal hold** — Documents under legal investigation must be preserved even if retention period expires. Need legal hold flags that override auto-deletion.

---

## Next Steps

- [ ] Build cloud document storage with tenant isolation
- [ ] Implement version control with diff tracking
- [ ] Create retention policy engine with India-compliant defaults
- [ ] Build full-text search across document library
- [ ] Design tiered storage (hot/warm/cold) for cost optimization
