# Data Import, Export & Migration — Import System

> Research document for bulk data import, CSV/Excel processing, validation pipelines, and error handling.

---

## Key Questions

1. **What data entities need bulk import capabilities?**
2. **How do we validate large imports without blocking the user?**
3. **What file formats should be supported?**
4. **How do we handle partial failures in large imports?**
5. **What's the import workflow from upload to completion?**

---

## Research Areas

### Import Model

```typescript
interface DataImport {
  importId: string;
  entityType: ImportEntityType;
  source: ImportSource;
  status: ImportStatus;
  totalRows: number;
  processedRows: number;
  succeededRows: number;
  failedRows: number;
  skippedRows: number;
  startedAt: Date;
  completedAt?: Date;
  initiatedBy: string;
  validationReport: ValidationReport;
  mapping: ColumnMapping[];
}

type ImportEntityType =
  | 'customers'                      // Customer profiles
  | 'travelers'                      // Traveler details
  | 'suppliers'                      // Supplier directory
  | 'bookings'                       // Historical bookings
  | 'payments'                       // Payment records
  | 'agents'                         // Agent accounts
  | 'hotels'                         // Hotel inventory
  | 'itineraries'                    // Trip itineraries
  | 'contracts'                      // Supplier contracts
  | 'price_lists'                    // Supplier pricing
  | 'commission_rates'               // Commission structures
  | 'travel_agents';                 // External agent network

type ImportSource =
  | { type: 'file'; fileName: string; format: FileFormat }
  | { type: 'clipboard'; pasteFormat: 'csv' | 'tsv' | 'json' }
  | { type: 'url'; url: string }
  | { type: 'api'; endpoint: string }
  | { type: 'integration'; provider: string };

type FileFormat =
  | 'csv'
  | 'xlsx'
  | 'xls'
  | 'json'
  | 'xml'
  | 'tsv';

type ImportStatus =
  | 'uploading'
  | 'validating'
  | 'mapping'
  | 'reviewing'
  | 'importing'
  | 'completed'
  | 'completed_with_errors'
  | 'failed';
```

### Column Mapping

```typescript
interface ColumnMapping {
  sourceColumn: string;              // Column header from file
  targetField: string;               // System field name
  transform?: TransformRule;
  defaultValue?: unknown;
  required: boolean;
  validation: FieldValidation[];
}

type TransformRule =
  | { type: 'rename'; pattern: string; replacement: string }
  | { type: 'date_format'; fromFormat: string; toFormat: string }
  | { type: 'phone_format'; countryCode: string }
  | { type: 'currency_convert'; from: string; to: string }
  | { type: 'enum_map'; mapping: Record<string, string> }
  | { type: 'split'; delimiter: string; targetFields: string[] }
  | { type: 'combine'; separator: string; sourceFields: string[] }
  | { type: 'trim' }
  | { type: 'lowercase' | 'uppercase' }
  | { type: 'regex_extract'; pattern: string; group: number }
  | { type: 'custom'; function: string };

// Column mapping examples:
// "Cust Name" → customer.name (trim, title case)
// "Phone" → customer.phone (format: +91 prefix, 10 digits)
// "DOB" → traveler.dateOfBirth (parse: DD/MM/YYYY → ISO 8601)
// "Amount" → payment.amount (currency: INR, parse number)
// "Status" → booking.status (enum_map: {"CNF": "confirmed", "PND": "pending"})

// Auto-mapping:
// System attempts to match column headers to known field names
// Fuzzy matching: "cust_name" matches "customer.name", "CustomerName"
// User reviews and corrects before import
// Mapping saved as template for future imports
```

### Validation Pipeline

```typescript
interface ValidationReport {
  totalRows: number;
  validRows: number;
  warningRows: number;
  errorRows: number;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  duplicates: DuplicateDetection[];
}

interface ValidationError {
  row: number;
  column: string;
  value: string;
  rule: string;
  message: string;
  severity: 'error' | 'warning';
  suggestion?: string;
}

// Validation rules applied per row:
// 1. Required fields — Missing required field = error
// 2. Type validation — "abc" in number field = error
// 3. Format validation — Invalid email, phone, date = error
// 4. Range validation — Negative price = error
// 5. Enum validation — Unknown status value = warning (with suggestion)
// 6. Length validation — Name too long = warning
// 7. Duplicate detection — Duplicate email/phone = warning
// 8. Referential integrity — Supplier ID doesn't exist = error
// 9. Business rules — End date before start date = error

interface DuplicateDetection {
  rowIndex: number;
  duplicateOfRow: number;
  matchFields: string[];
  action: 'skip' | 'update' | 'create_duplicate';
  resolved: boolean;
}

// Import workflow:
// 1. Upload file → Parse headers → Show preview (first 10 rows)
// 2. Auto-map columns → User reviews and corrects mapping
// 3. Run validation → Show validation report
// 4. User resolves errors (fix in UI, skip rows, or cancel)
// 5. Handle duplicates (skip, update existing, or create new)
// 6. Confirm import → Process in background
// 7. Show progress bar → Complete with summary
```

### Large File Handling

```typescript
interface LargeImportConfig {
  maxFileSize: string;               // "50MB"
  chunkSize: number;                 // Rows per processing chunk
  maxRows: number;                   // Maximum rows per import
  backgroundProcessing: boolean;
  estimatedTimePerRow: number;       // Ms
  progressTracking: boolean;
  resumeCapability: boolean;         // Resume interrupted import
}

// Strategies for large imports:
// 1. Streaming: Process file in chunks, don't load entire file into memory
// 2. Background jobs: Import runs as background task, not blocking UI
// 3. Progress tracking: Real-time progress bar with row counts
// 4. Resume: If interrupted (network, browser close), can resume from last checkpoint
// 5. Batch commit: Insert in batches of 100-500 rows, not one at a time
// 6. Rate limiting: Don't overwhelm the database (max 1000 inserts/second)
// 7. Disk-based: For very large files, use disk-based processing, not memory

// Import size guidelines:
// < 1,000 rows → Synchronous, progress bar in modal
// 1,000 - 10,000 rows → Background job, email notification on completion
// 10,000 - 100,000 rows → Background job, chunked processing, resume capability
// 100,000+ rows → Requires admin approval, scheduled for off-peak hours
```

---

## Open Problems

1. **Data quality from legacy systems** — Travel agencies migrating from Excel/pen-and-paper have messy, inconsistent data. Need aggressive cleaning and normalization.

2. **Character encoding** — Indian names in Hindi, destination names with special characters. UTF-8 handling across file formats (Excel is notorious for encoding issues).

3. **Duplicate resolution** — Same customer in 3 imports with slightly different names/phones. Fuzzy matching is error-prone at scale.

4. **Rollback** — Imported 10,000 rows, realized mapping was wrong. Need import rollback capability, which requires tracking every inserted row.

5. **Concurrent imports** — Two admins importing supplier lists simultaneously. Need locking or conflict resolution.

---

## Next Steps

- [ ] Design import pipeline with streaming and chunked processing
- [ ] Build column auto-mapping with fuzzy matching
- [ ] Create validation framework with configurable rules
- [ ] Design import template system for recurring imports
- [ ] Study import UX (Stripe, HubSpot, Salesforce data import)
