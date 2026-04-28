# Data Import, Export & Migration — Data Migration

> Research document for system migrations, legacy data conversion, and cross-platform data transfer.

---

## Key Questions

1. **How do we migrate agencies from legacy systems (Tally, Excel, CRM)?**
2. **What's the migration workflow from evaluation to go-live?**
3. **How do we handle data schema differences between systems?**
4. **What's the rollback plan if migration goes wrong?**
5. **How do we validate migration accuracy?**

---

## Research Areas

### Migration Model

```typescript
interface DataMigration {
  migrationId: string;
  agencyId: string;
  sourceSystem: SourceSystem;
  targetSystem: 'platform';
  status: MigrationStatus;
  phases: MigrationPhase[];
  startedAt: Date;
  completedAt?: Date;
  migrationManager: string;
  rollbackPlan: RollbackPlan;
}

type SourceSystem =
  | { type: 'tally'; version: string }
  | { type: 'excel'; description: string }
  | { type: 'custom_crm'; name: string }
  | { type: 'travelomatrix'; version?: string }
  | { type: 'salestrack'; version?: string }
  | { type: 'manual'; description: string }
  | { type: 'competitor'; name: string }
  | { type: 'generic'; description: string };

type MigrationStatus =
  | 'planning'                       // Scoping and mapping
  | 'data_extraction'                // Extracting from source
  | 'transformation'                 // Converting to target schema
  | 'validation'                     // Verifying data quality
  | 'review'                         // Agency reviews migrated data
  | 'go_live'                        // Switch to new system
  | 'post_migration'                 // Monitoring and fixes
  | 'completed'
  | 'rolled_back';
```

### Migration Phases

```typescript
interface MigrationPhase {
  phaseId: string;
  name: string;
  order: number;
  status: PhaseStatus;
  dataEntities: MigrationEntity[];
  validation: MigrationValidation[];
}

type MigrationEntity =
  | 'agency_profile'                 // Agency settings and branding
  | 'agent_accounts'                 // Agent logins and permissions
  | 'customer_master'                // Customer directory
  | 'traveler_profiles'              // Traveler details, passport info
  | 'supplier_master'                // Supplier directory
  | 'contract_records'               // Supplier contracts
  | 'price_lists'                    // Supplier pricing
  | 'booking_history'                // Historical bookings
  | 'payment_records'                // Payment history
  | 'invoice_records'                // Invoice history
  | 'commission_records'             // Agent commission history
  | 'document_templates'             // Custom templates
  | 'communication_history'          // Past emails/messages
  | 'financial_balances'             // Opening balances
  | 'audit_history';                 // Historical audit trail

// Migration order (dependencies):
// Phase 1: Agency Profile → Agency settings, branding, team structure
// Phase 2: Master Data → Customers, Travelers, Suppliers, Agents
// Phase 3: Reference Data → Price lists, Contracts, Templates
// Phase 4: Transaction History → Bookings, Payments, Invoices
// Phase 5: Financial Balances → Opening balances, Outstanding amounts
// Phase 6: Communication History → Emails, messages (optional)
// Phase 7: Audit History → Compliance records (optional)

// Migration timeline estimate:
// Phase 1: 1 day
// Phase 2: 2-3 days (depends on customer/supplier count)
// Phase 3: 1-2 days
// Phase 4: 3-5 days (largest volume, most complex)
// Phase 5: 1 day (needs careful reconciliation)
// Phase 6: 1-2 days (optional, lower priority)
// Phase 7: 1 day (optional)
// Total: 10-16 business days for a medium-sized agency
```

### Schema Transformation

```typescript
interface SchemaMapping {
  sourceField: string;
  targetField: string;
  transformation?: TransformRule;
  defaultValue?: unknown;
  validation: TransformValidation;
}

// Common transformation challenges:
//
// 1. Customer name splitting:
//    Source: "Mr. Rajesh Kumar Sharma" (single field)
//    Target: { title: "Mr", firstName: "Rajesh", middleName: "Kumar", lastName: "Sharma" }
//    Transform: Name parsing with Indian name conventions
//
// 2. Phone number normalization:
//    Source: "+91-98765-43210", "9876543210", "09876543210"
//    Target: "+919876543210" (E.164 format)
//    Transform: Strip formatting, add country code
//
// 3. Address structuring:
//    Source: "123, MG Road, Koramangala, Bangalore - 560034"
//    Target: { street: "123, MG Road", area: "Koramangala", city: "Bangalore", pincode: "560034" }
//    Transform: Address parsing (complex, may need manual review)
//
// 4. Date format conversion:
//    Source: "15/04/2026" (DD/MM/YYYY) or "2026-04-15" (ISO)
//    Target: "2026-04-15T00:00:00+05:30" (ISO 8601 with timezone)
//    Transform: Date parsing with format detection
//
// 5. Currency amounts:
//    Source: "₹1,25,000.00" (Indian formatting with commas)
//    Target: 125000.00 (numeric)
//    Transform: Parse Indian number formatting (lakhs/crores commas)
//
// 6. Booking status mapping:
//    Source: {"CNF", "PND", "CXD", "MOD", "TKT"}
//    Target: {"confirmed", "pending", "cancelled", "modified", "ticketed"}
//    Transform: Enum mapping with unknown handling

// Schema version tracking:
interface SchemaVersion {
  sourceSystem: string;
  sourceVersion: string;
  mappingVersion: number;
  lastUpdated: Date;
  testedAgainstSourceSample: boolean;
}
```

### Migration Validation

```typescript
interface MigrationValidation {
  validationType: MigrationValidationType;
  threshold: number;
  actual: number;
  passed: boolean;
}

type MigrationValidationType =
  | 'row_count_match'                // Source row count ≈ Target row count (±1%)
  | 'financial_balance_match'        // Opening balances match to the penny
  | 'customer_count_match'           // Customer count matches
  | 'no_null_required_fields'        // No null values in required fields
  | 'date_range_preserved'           // Oldest/newest dates match
  | 'referential_integrity'          // All foreign keys resolve
  | 'unique_constraint_check'        // No duplicate emails, phones, booking IDs
  | 'sample_verification';           // Manual spot-check of 50 random records

// Go-live checklist:
// [ ] All migration phases completed
// [ ] Row counts match within tolerance
// [ ] Financial balances reconciled
// [ ] Sample of 50 records manually verified
// [ ] Agency admin signs off on data accuracy
// [ ] Agent accounts created and tested
// [ ] Old system set to read-only (not deleted)
// [ ] Parallel run period defined (1-2 weeks)
// [ ] Support escalation path established
// [ ] Rollback plan reviewed and tested

interface RollbackPlan {
  rollbackTrigger: string;           // What triggers rollback
  maxRollbackTime: string;           // How long before rollback is impossible
  rollbackSteps: string[];
  dataRecoveryPlan: string;
  communicationPlan: string;
}
```

---

## Open Problems

1. **Legacy data quality** — Agencies have been using Excel for years. Data is incomplete, inconsistent, and sometimes wrong. Migration can't fix underlying data quality issues.

2. **Parallel run complexity** — Running old and new systems simultaneously during transition. Bookings happen in both systems. Need reconciliation.

3. **Historical data volume** — 10 years of booking history across millions of rows. Full migration takes weeks. What data is essential vs. nice-to-have?

4. **Custom fields** — Every agency has custom data (special tags, notes, categories) that don't map to standard fields. Need extensible custom fields.

5. **User resistance** — Agents resist change. Migration is as much a people problem as a technical one. Need change management strategy.

---

## Next Steps

- [ ] Design migration framework with phase-based approach
- [ ] Build schema transformation engine for common source systems
- [ ] Create migration validation and reconciliation toolkit
- [ ] Design go-live checklist and rollback procedures
- [ ] Study data migration best practices (Salesforce migration, ERP migration)
