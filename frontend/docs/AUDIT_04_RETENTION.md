# Audit & Compliance — Data Retention & Lifecycle

> Research document for data retention policies, deletion workflows, and lifecycle management.

---

## Key Questions

1. **What are the legal retention requirements per data type and jurisdiction?**
2. **How do we implement right-to-erasure (GDPR/DPDP) while maintaining audit trails?**
3. **What's the data lifecycle — when does data move from hot to cold to deleted?**
4. **How do we handle data that's referenced across multiple systems?**
5. **What's the deletion verification process?**

---

## Research Areas

### Retention Policy Matrix

```typescript
interface RetentionPolicy {
  dataType: string;
  jurisdiction: string;
  regulation: string;
  minRetention: string;
  maxRetention: string;
  autoDelete: boolean;
  archiveAfter: string;
  exceptions: string[];
}

// Retention by data type:
// Financial records: 7 years (IT Act, Companies Act)
// Tax invoices: 7 years (GST law)
// Contracts: 7 years after termination
// Customer PII: Until consent withdrawn + 30 days (DPDP)
// Booking data: Trip completion + 90 days (operational)
// Payment records: 7 years (RBI)
// Insurance records: Policy term + 5 years (IRDAI)
// Audit logs: 7 years (compliance)
// Webhook logs: 90 days
// Session data: 30 days
// Marketing data: Until consent withdrawn
// Employee data: 7 years after separation
// Supplier data: Contract term + 2 years
```

### Data Lifecycle Management

```typescript
interface DataLifecycle {
  dataType: string;
  stages: LifecycleStage[];
  currentStage: string;
  timestamps: Record<string, Date>;
}

type LifecycleStage =
  | 'active'              // Currently in use
  | 'archived'            // Moved to cold storage
  | 'anonymized'          // PII stripped, statistical data retained
  | 'pending_deletion'    // Scheduled for deletion
  | 'deleted';            // Permanently removed

interface DataLifecycleManager {
  // Evaluate all data and apply retention policies
  runRetentionSweep(): Promise<RetentionSweepResult>;
  // Anonymize PII while retaining statistical value
  anonymize(dataType: string, entityId: string): Promise<void>;
  // Delete data and verify deletion across all systems
  deleteWithVerification(dataType: string, entityId: string): Promise<DeletionResult>;
}
```

### Right to Erasure Workflow

```typescript
interface ErasureRequest {
  requestId: string;
  customerId: string;
  requestDate: Date;
  verificationStatus: 'pending' | 'verified' | 'rejected';
  scope: 'full' | 'partial';
  exclusions: ErasureExclusion[];
  status: 'received' | 'processing' | 'completed' | 'partially_completed';
  completionDeadline: Date;         // 30 days from request
  affectedSystems: ErasureTarget[];
}

interface ErasureExclusion {
  dataType: string;
  reason: string;
  regulation: string;              // Legal basis for retaining
  retentionUntil: Date;
}

interface ErasureTarget {
  system: string;
  dataType: string;
  recordCount: number;
  deletionStatus: 'pending' | 'completed' | 'failed' | 'excluded';
  deletedAt?: Date;
  verificationMethod: string;
}

// Common exclusions:
// - Active bookings can't be erased until completed
// - Financial records must be retained for 7 years
// - Tax invoices can't be deleted
// - Active insurance policies must be retained
// - Audit log entries anonymized but not deleted
```

---

## Open Problems

1. **Cascading deletion** — Deleting a customer record requires finding and handling all references across bookings, payments, communications, documents, and audit logs.

2. **Right to erasure vs. audit trail** — Deleting customer data from audit logs breaks the tamper-proof chain. Need anonymization (replace name with hash) instead of deletion.

3. **Backup data** — Data deleted from production may exist in backups. How to handle erasure across backup systems? Full backup rotation + selective deletion.

4. **Multi-system consistency** — Customer data exists in the app database, CRM, email system, document storage, and analytics warehouse. Erasure must cover all.

5. **Verification** — How to prove data was actually deleted? Need cryptographic proof or third-party verification.

---

## Next Steps

- [ ] Map all data types to retention requirements by jurisdiction
- [ ] Design data lifecycle management system
- [ ] Create right-to-erasure workflow with system-by-system checklist
- [ ] Study data anonymization techniques (k-anonymity, differential privacy)
- [ ] Design deletion verification and audit trail
