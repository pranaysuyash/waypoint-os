# Audit & Compliance — Audit Trail Architecture

> Research document for building immutable, comprehensive audit trails for travel operations.

---

## Key Questions

1. **What actions must be audited (regulatory requirement vs. operational need)?**
2. **How do we build an immutable audit log that can't be tampered with?**
3. **What's the right granularity — field-level changes or entity-level events?**
4. **How do we make audit data queryable without impacting operational performance?**
5. **What's the retention policy for audit records?**

---

## Research Areas

### Audit Event Model

```typescript
interface AuditEvent {
  eventId: string;
  timestamp: Date;
  // Who
  actor: AuditActor;
  // What
  action: AuditAction;
  entity: AuditEntity;
  // Where
  source: AuditSource;
  // Result
  outcome: 'success' | 'failure' | 'denied';
  // Details
  changes?: AuditChange[];
  metadata: Record<string, unknown>;
}

interface AuditActor {
  type: 'user' | 'system' | 'api_key' | 'cron_job';
  id: string;
  name: string;
  role: string;
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
}

interface AuditEntity {
  type: 'trip' | 'booking' | 'customer' | 'payment' | 'commission' | 'contract' | 'supplier' | 'agent' | 'document';
  id: string;
  name?: string;
}

type AuditAction =
  | 'create' | 'read' | 'update' | 'delete'
  | 'login' | 'logout' | 'login_failed'
  | 'approve' | 'reject' | 'escalate'
  | 'export' | 'download' | 'print'
  | 'assign' | 'reassign'
  | 'cancel' | 'refund'
  | 'sign' | 'verify'
  | 'permission_change' | 'role_change';

interface AuditSource {
  application: string;            // 'workbench', 'spine_api', 'admin'
  environment: string;
  region: string;
}

interface AuditChange {
  field: string;
  oldValue: unknown;
  newValue: unknown;
}
```

### Immutability Guarantees

```typescript
interface AuditStore {
  // Append-only — events can never be modified or deleted
  writePolicy: 'append_only';
  // Cryptographic chaining (hash chain)
  chaining: {
    enabled: boolean;
    algorithm: 'sha256';
    // Each event includes hash of previous event
    // Detects any tampering in the chain
  };
  // Separate storage from operational database
  storage: 'dedicated_database' | 'object_storage' | 'ledger_service';
  // Access control — read-only for all except audit service
  accessControl: 'write_once_read_many';
}
```

### Mandatory Audit Events (Regulatory)

```typescript
type MandatoryAuditEvent =
  // Financial (tax law, 7-year retention)
  | 'payment_received'
  | 'payment_refunded'
  | 'commission_earned'
  | 'commission_paid'
  | 'invoice_generated'
  // Data privacy (GDPR, DPDP)
  | 'personal_data_accessed'
  | 'personal_data_modified'
  | 'personal_data_exported'
  | 'personal_data_deleted'
  | 'consent_given'
  | 'consent_withdrawn'
  // Security
  | 'login_success'
  | 'login_failure'
  | 'password_change'
  | 'permission_change'
  | 'data_export'
  // Contractual
  | 'contract_signed'
  | 'contract_amended'
  | 'contract_terminated';
```

---

## Open Problems

1. **Volume management** — Every field change is an audit event. A complex booking modification generates 20+ events. At scale, this is millions of events per month.

2. **Query performance** — Auditors need to query historical events ("show all modifications to booking X between dates Y and Z"). Append-only stores aren't optimized for reads.

3. **PII in audit logs** — Audit events may contain personal data (old/new values include customer names). This creates a tension between audit completeness and data privacy (right to erasure).

4. **Cross-service correlation** — A single user action may trigger events in multiple services (booking service, payment service, notification service). Correlating these into a single user action view requires a correlation ID.

5. **Audit log integrity verification** — How to periodically verify the hash chain is intact without reading the entire log.

---

## Next Steps

- [ ] Design audit event schema for current system entities
- [ ] Evaluate audit log storage options (dedicated table, event store, cloud ledger)
- [ ] Implement hash chaining for tamper detection
- [ ] Design audit query interface for compliance team
- [ ] Map mandatory audit events per regulatory requirement
