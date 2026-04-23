# Timeline: Legal & Compliance Deep Dive

> Regulations, privacy, audits, and legal protections for Timeline data

---

## Part 1: Legal Framework Overview

### The Compliance Challenge

Timeline stores sensitive customer communications, financial decisions, and agency records. This creates legal responsibilities:

**Key Regulatory Areas:**

| Area | Applicable Laws | Timeline Impact |
|------|-----------------|-----------------|
| **Data Privacy** | PDPA, IT Rules 2011 | Customer consent, data minimization |
| **Consumer Protection** | Consumer Protection Act 2019 | Record of commitments, terms |
| **Financial Records** | GST Act, Income Tax | Transaction records, invoicing |
| **Communication** | IT Act, Telecom Rules | Message retention, consent |
| **Employment** | Labor laws | Agent performance records |

---

## Part 2: Data Privacy & Protection

### 2.1 Personal Data Protection

**Applicable Regulations:**
- **Personal Data Protection Bill (PDPB)** - India's upcoming GDPR-like law
- **Information Technology Act, 2000** - Section 43A (data negligence)
- **IT (Reasonable Security Practices and Procedures) Rules, 2011**

**Timeline Data Classification:**

```typescript
enum DataSensitivity {
  PUBLIC = 'public',           // Non-sensitive: Destination names, general info
  INTERNAL = 'internal',       // Agency internal: Agent notes, decisions
  CONFIDENTIAL = 'confidential', // Customer business: Budget, preferences
  SENSITIVE = 'sensitive',     // Personally identifiable: Phone, email, address
  RESTRICTED = 'restricted'    // Highly sensitive: Payment details, passports
}

interface DataClassification {
  field: string;
  sensitivity: DataSensitivity;
  retention_period: string;    // How long to keep
  access_level: string;        // Who can access
  encryption_required: boolean;
}
```

**Field-Level Classification:**

| Field | Sensitivity | Retention | Access |
|-------|-------------|-----------|--------|
| Customer name | SENSITIVE | 7 years | All agents |
| Phone number | SENSITIVE | 7 years | All agents |
| Email address | SENSITIVE | 7 years | All agents |
| Address | SENSITIVE | 7 years | All agents |
| Budget | CONFIDENTIAL | 7 years | All agents |
| Payment details | RESTRICTED | 7 years | Owner + finance |
| Passport details | RESTRICTED | 7 years | Owner + booking team |
| Travel dates | CONFIDENTIAL | 7 years | All agents |
| Preferences | CONFIDENTIAL | 3 years | All agents |
| Agent notes | INTERNAL | 3 years | All agents |
| System logs | INTERNAL | 6 months | Tech team |

### 2.2 Consent Management

**Timeline must capture and respect customer consent:**

```typescript
interface ConsentRecord {
  id: string;
  customer_id: string;
  consent_type: 'communication' | 'data_processing' | 'data_sharing' | 'recording';
  granted: boolean;
  granted_at: string;
  revoked_at?: string;
  channel: 'whatsapp' | 'email' | 'web' | 'phone';
  consent_text: string;        // What customer agreed to
  ip_address?: string;
  user_agent?: string;
}

interface TripEvent {
  // ... existing fields
  consent_verified?: boolean;   // Was consent verified for this event?
  consent_id?: string;          // Link to consent record
}
```

**Consent Capture Points:**

1. **First Inquiry:** Auto-reply with consent request
2. **WhatsApp Opt-in:** Explicit checkbox before adding
3. **Email Communication:** Unsubscribe link + consent footer
4. **Phone Calls:** "This call may be recorded for quality purposes"
5. **Data Sharing:** Explicit consent before sharing with suppliers

**Implementation:**

```python
class ConsentManager:
    """Manage customer consent for timeline data"""

    async def verify_consent(
        self,
        customer_id: str,
        consent_type: ConsentType,
        channel: str
    ) -> bool:
        """Verify if customer has given consent"""

        # Check for active consent
        consent = await db.query("""
            SELECT * FROM consent_records
            WHERE customer_id = $1
              AND consent_type = $2
              AND channel = $3
              AND granted = true
              AND (revoked_at IS NULL OR revoked_at > NOW())
            ORDER BY granted_at DESC
            LIMIT 1
        """, customer_id, consent_type, channel)

        return bool(consent)

    async def record_consent(
        self,
        customer_id: str,
        consent_type: ConsentType,
        granted: boolean,
        channel: str,
        metadata: dict
    ) -> ConsentRecord:
        """Record consent/grant event"""

        # Create consent record
        consent = await db.insert('consent_records', {
            'id': generate_id(),
            'customer_id': customer_id,
            'consent_type': consent_type,
            'granted': granted,
            'granted_at': datetime.now(),
            'channel': channel,
            'consent_text': metadata.get('consent_text'),
            'ip_address': metadata.get('ip_address'),
            'user_agent': metadata.get('user_agent')
        })

        # Also create timeline event for audit trail
        await create_timeline_event(
            event_type='consent_recorded',
            category=EventCategory.SYSTEM,
            content={
                'consent_type': consent_type,
                'granted': granted,
                'channel': channel
            }
        )

        return consent
```

### 2.3 Right to Erasure (Right to be Forgotten)

**Customer can request deletion of their data:**

```python
class DataErasureService:
    """Handle customer data deletion requests"""

    async def process_erasure_request(
        self,
        customer_id: str,
        requestor: str,
        reason: str
    ) -> ErasureReport:
        """Process customer data deletion request"""

        # 1. Verify requestor is authorized
        await self._verify_requestor(requestor, customer_id)

        # 2. Create erasure request record (for audit)
        request_id = await db.insert('erasure_requests', {
            'id': generate_id(),
            'customer_id': customer_id,
            'requested_by': requestor,
            'reason': reason,
            'status': 'processing',
            'requested_at': datetime.now()
        })

        # 3. Identify all data to delete
        data_inventory = await self._inventory_customer_data(customer_id)

        # 4. Delete/anonymize data
        deletion_report = await self._delete_customer_data(customer_id, data_inventory)

        # 5. Keep legal hold for required period (anonymized)
        await self._create_legal_hold(request_id, deletion_report)

        # 6. Update request status
        await db.update('erasure_requests', request_id, {
            'status': 'completed',
            'completed_at': datetime.now(),
            'deletion_report': deletion_report
        })

        return deletion_report

    async def _delete_customer_data(
        self,
        customer_id: str,
        inventory: DataInventory
    ) -> DeletionReport:
        """Delete customer data from all systems"""

        report = DeletionReport()

        # Timeline events - ANONYMIZE (keep for legal requirements)
        timeline_events = await db.query("""
            SELECT * FROM trip_events
            WHERE customer_id = $1
        """, customer_id)

        for event in timeline_events:
            # Anonymize PII
            event.content = anonymize_pii(event.content)
            event.actor = anonymize_actor(event.actor)

            # Mark as anonymized
            event.anonymized = True
            event.anonymized_at = datetime.now()

            await db.update('trip_events', event.id, event)

        report.timeline_events_anonymized = len(timeline_events)

        # Workspace data - DELETE
        await db.execute("""
            DELETE FROM workspaces
            WHERE customer_id = $1
        """, customer_id)

        report.workspaces_deleted = await db.rowcount()

        # Communication history - ANONYMIZE
        await self._anonymize_communications(customer_id)

        # ... other data types

        return report
```

---

## Part 3: Consumer Protection Compliance

### 3.1 Record of Commitments

**Consumer Protection Act 2019 requires:**
- Clear record of what was promised
- Terms and conditions communicated
- No misleading representations
- Proof of customer acceptance

**Timeline as Legal Evidence:**

```typescript
interface CommitmentRecord {
  id: string;
  trip_id: string;
  commitment_type: 'price' | 'service' | 'timeline' | 'cancellation' | 'terms';
  agency_commitment: string;     // What agency promised
  customer_acceptance: string;   // How customer accepted
  evidence: {
    event_id: string;            // Timeline event with proof
    message_content: string;      // Exact message
    timestamp: string;
    channel: string;
  };
  terms_communicated: string[];  // What terms were shared
  restrictions: string[];        // Any limitations noted
}
```

**Automatic Commitment Tracking:**

```python
class CommitmentTracker:
    """Track agency commitments for legal protection"""

    async def extract_commitments(
        self,
        trip_id: str
    ) -> List[CommitmentRecord]:
        """Extract all commitments from timeline"""

        events = await get_trip_events(trip_id)
        commitments = []

        for event in events:
            # Outbound messages may contain commitments
            if event.event_type in ['whatsapp_message_sent', 'email_sent']:
                extracted = await self._extract_commitments_from_message(event)
                commitments.extend(extracted)

            # Decision events may represent commitments
            if event.event_type == 'decision_changed':
                if event.content.toState == 'READY_TO_BOOK':
                    # Price commitment
                    commitments.append(self._create_price_commitment(event))

        return commitments

    async def _extract_commitments_from_message(
        self,
        event: TripEvent
    ) -> List[CommitmentRecord]:
        """Extract commitments from agent messages"""

        message = event.content.get('message', '')
        commitments = []

        # Use NLP to identify commitment language
        # "I will", "we'll include", "confirmed", "promised"
        commitment_patterns = {
            'price': r'(?:price|cost|rate|charge|₹)\s*(?:of|:)?\s*₹?\s*[\d,]+',
            'service': r'(?:include|provide|arrange|book)\s+(?:flight|hotel|transfer|tour)',
            'timeline': r'(?:by|before|on)\s+(?:\w+\s+){0,3}\d+(?:st|nd|rd|th)?',
            'cancellation': r'(?:cancel|refund|change)\s+policy'
        }

        for commitment_type, pattern in commitment_patterns.items():
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                commitments.append(CommitmentRecord(
                    id=generate_id(),
                    trip_id=event.trip_id,
                    commitment_type=commitment_type,
                    agency_commitment=match.group(0),
                    customer_acceptance='Sent via ' + event.source.channel,
                    evidence={
                        'event_id': event.id,
                        'message_content': message,
                        'timestamp': event.timestamp,
                        'channel': event.source.channel
                    }
                ))

        return commitments
```

### 3.2 Terms Communication Tracking

**Must track what terms were communicated and when:**

```typescript
interface TermsCommunication {
  id: string;
  trip_id: string;
  terms_type: 'cancellation_policy' | 'payment_terms' | 'refund_policy' | 'general_terms';
  communicated_at: string;
  communicated_via: string;
  acknowledged_by_customer: boolean;
  acknowledged_at?: string;
  content_shared: string;        // What was actually shared
  version: string;               // Terms version number
}
```

**Implementation:**

```python
class TermsTracker:
    """Track terms communication for compliance"""

    async def record_terms_communication(
        self,
        trip_id: str,
        terms_type: TermsType,
        content: str,
        channel: str
    ):
        """Record that terms were communicated"""

        # Create timeline event
        await create_timeline_event(
            trip_id=trip_id,
            event_type='terms_communicated',
            category=EventCategory.SYSTEM,
            content={
                'terms_type': terms_type,
                'content_shared': content,
                'channel': channel,
                'version': await self._get_current_terms_version(terms_type)
            }
        )

    async def verify_terms_acknowledgment(
        self,
        trip_id: str
    ) -> AcknowledgmentStatus:
        """Verify if customer acknowledged required terms"""

        required_terms = [
            'cancellation_policy',
            'payment_terms',
            'refund_policy'
        ]

        status = AcknowledgmentStatus()

        for terms_type in required_terms:
            # Check if terms were communicated
            communicated = await db.query("""
                SELECT * FROM trip_events
                WHERE trip_id = $1
                  AND event_type = 'terms_communicated'
                  AND content->>'terms_type' = $2
                ORDER BY timestamp DESC
                LIMIT 1
            """, trip_id, terms_type)

            if not communicated:
                status.missing.append(terms_type)
                continue

            # Check if customer acknowledged
            # (e.g., replied "OK", "Understood", "Accepted")
            acknowledgment = await db.query("""
                SELECT * FROM trip_events
                WHERE trip_id = $1
                  AND event_type = 'whatsapp_message_received'
                  AND timestamp > $2
                  AND content->>'message' ~* '(ok|understood|accepted|agreed|noted)'
                LIMIT 1
            """, trip_id, communicated[0].timestamp)

            status.communicated[terms_type] = communicated[0].timestamp
            status.acknowledged[terms_type] = bool(acknowledgment)

        return status
```

---

## Part 4: Financial Compliance

### 4.1 GST Compliance

**Timeline must support GST audit requirements:**

```typescript
interface GSTRecord {
  trip_id: string;
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  gst_amount: number;
  gst_rate: number;
  customer_gst_number?: string;
  place_of_supply: string;
  supply_type: ' interstate' | 'intrastate';
  timeline_event_id: string;    // Link to timeline for audit trail
}

interface TripEvent {
  // ... existing fields
  gst_reference?: string;       // Link to GST record
  invoice_generated?: boolean;
}
```

**GST Audit Trail:**

```python
class GSTAuditTrail:
    """Create GST-compliant audit trail"""

    async def generate_gst_audit_report(
        self,
        period_start: date,
        period_end: date
    ) -> GSTAuditReport:
        """Generate GST audit report from timeline data"""

        # Get all invoice events in period
        invoice_events = await db.query("""
            SELECT * FROM trip_events
            WHERE event_type = 'invoice_generated'
              AND timestamp BETWEEN $1 AND $2
            ORDER BY timestamp
        """, period_start, period_end)

        # Build report
        report = GSTAuditReport(
            period_start=period_start,
            period_end=period_end,
            invoices=[]
        )

        for event in invoice_events:
            # Get complete trip context
            trip_events = await get_trip_events(event.trip_id)

            invoice = GSTInvoiceRecord(
                invoice_number=event.content.invoice_number,
                invoice_date=event.timestamp,
                invoice_amount=event.content.amount,
                gst_amount=event.content.gst_amount,
                gst_rate=event.content.gst_rate,
                customer_gst_number=event.content.customer_gst,
                place_of_supply=event.content.place_of_supply,
                # Timeline proof
                inquiry_received=self._find_event(trip_events, 'inquiry_received'),
                quote_sent=self._find_event(trip_events, 'quote_sent'),
                customer_acceptance=self._find_event(trip_events, 'customer_confirmed'),
                payment_received=self._find_event(trip_events, 'payment_received'),
                service_delivered=self._find_event(trip_events, 'booking_confirmed')
            )

            report.invoices.append(invoice)

        return report
```

### 4.2 TCS (Tax Collected at Source) Compliance

**For foreign remittances, track TCS:**

```typescript
interface TCSRecord {
  trip_id: strring;
  remittance_amount: number;
  tcs_amount: number;
  tcs_rate: number;
  pan_card: string;
  remittance_date: string;
  purpose_code: string;         // RBI purpose code
  timeline_event_id: string;
}
```

### 4.3 Transaction Records

**Timeline must track all financial transactions:**

```typescript
interface TransactionEvent extends TripEvent {
  eventType: 'payment_received' |
              'payment_refunded' |
              'invoice_generated' |
              'supplier_payment' |
              'commission_received';

  content: {
    transaction_type: string;
    amount: number;
    currency: string;
    payment_method: string;
    reference_number: string;
    gst_details?: {
        amount: number;
        rate: number;
        gst_number: string;
    };
    related_invoice?: string;
  };
}
```

---

## Part 5: Data Retention Policy

### 5.1 Retention Schedule

**Legal requirements + business needs:**

| Data Type | Retention Period | Legal Basis | Disposition |
|-----------|------------------|-------------|-------------|
| **Inquiry records** | 7 years | GST, Income Tax | Anonymize after 7 years |
| **Customer communications** | 7 years | Consumer Protection, Legal disputes | Anonymize after 7 years |
| **Financial transactions** | 7 years | GST Act | Anonymize after 7 years |
| **AI analysis data** | 2 years | Business value | Delete after 2 years |
| **Agent performance data** | 3 years | Labor laws | Anonymize after 3 years |
| **System logs** | 6 months | Security | Delete after 6 months |
| **Draft/unsent content** | 30 days | Privacy | Delete after 30 days |
| **Customer preferences** | 3 years | Business value | Delete after 3 years |
| **Supplier contracts** | 7 years after contract end | Contract law | Archive separately |

### 5.2 Retention Implementation

```python
class RetentionManager:
    """Manage data retention according to policy"""

    async def process_retention(self):
        """Daily job to process data retention"""

        policies = await self._get_retention_policies()

        for policy in policies:
            if policy.disposition == 'delete':
                await self._delete_expired_data(policy)
            elif policy.disposition == 'anonymize':
                await self._anonymize_expired_data(policy)
            elif policy.disposition == 'archive':
                await self._archive_expired_data(policy)

    async def _anonymize_expired_data(self, policy: RetentionPolicy):
        """Anonymize data that has exceeded retention period"""

        cutoff_date = datetime.now() - timedelta(days=policy.retention_days)

        # Get expired events
        expired_events = await db.query("""
            SELECT * FROM trip_events
            WHERE event_type = $1
              AND timestamp < $2
              AND anonymized = false
        """, policy.event_type, cutoff_date)

        for event in expired_events:
            # Anonymize PII
            event.content = self._anonymize_content(event.content)
            event.actor = self._anonymize_actor(event.actor)

            # Mark as anonymized
            event.anonymized = True
            event.anonymized_at = datetime.now()
            event.anonymization_reason = policy.reason

            await db.update('trip_events', event.id, event)

        # Create retention audit log
        await db.insert('retention_log', {
            'policy_id': policy.id,
            'records_processed': len(expired_events),
            'processed_at': datetime.now()
        })

    def _anonymize_content(self, content: dict) -> dict:
        """Anonymize PII in content"""

        # Fields to anonymize
        pii_fields = [
            'name', 'email', 'phone', 'mobile',
            'address', 'passport', 'pan', 'aadhar',
            'account_number', 'ifsc_code'
        ]

        anonymized = content.copy()

        for field in pii_fields:
            if field in anonymized:
                # Replace with placeholder
                anonymized[field] = f"[REDACTED_{field.upper()}]"

        # Anonymize free text
        if 'message' in anonymized:
            anonymized['message'] = self._anonymize_text(
                anonymized['message']
            )

        return anonymized

    def _anonymize_text(self, text: str) -> str:
        """Anonymize PII in free text"""

        # Use NER to find and replace PII
        entities = self.ner_model.extract_entities(text)

        anonymized = text
        for entity in entities:
            if entity.type in ['PERSON', 'PHONE', 'EMAIL', 'ADDRESS']:
                anonymized = anonymized.replace(
                    entity.text,
                    f"[REDACTED_{entity.type}]"
                )

        return anonymized
```

---

## Part 6: Audit Capabilities

### 6.1 Audit Log

**All access to timeline data must be logged:**

```typescript
interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: {
    id: string;
    type: 'agent' | 'owner' | 'system' | 'api';
    name: string;
  };
  action: string;               // 'viewed', 'exported', 'searched', 'filtered'
  resource_type: 'trip' | 'event' | 'customer';
  resource_id: string;
  ip_address?: string;
  user_agent?: string;
  result: 'success' | 'denied' | 'error';
  error_message?: string;
}
```

**Implementation:**

```python
class AuditLogger:
    """Log all timeline access for audit"""

    async def log_access(
        self,
        actor: Actor,
        action: str,
        resource_type: str,
        resource_id: str,
        result: str,
        request: Request
    ):
        """Log access to timeline data"""

        await db.insert('audit_log', {
            'id': generate_id(),
            'timestamp': datetime.now(),
            'actor': {
                'id': actor.id,
                'type': actor.type,
                'name': actor.name
            },
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': request.client.host if request else None,
            'user_agent': request.headers.get('user-agent') if request else None,
            'result': result
        })

# Middleware to automatically log all timeline API access
@app.middleware("http")
async def audit_timeline_access(request: Request, call_next):
    """Audit all timeline API access"""

    if request.url.path.startswith('/api/timeline'):
        # Process request
        response = await call_next(request)

        # Log access
        await audit_logger.log_access(
            actor=get_current_actor(request),
            action='viewed',
            resource_type='timeline',
            resource_id=request.path_params.get('trip_id'),
            result='success' if response.status_code < 400 else 'error',
            request=request
        )

        return response

    return await call_next(request)
```

### 6.2 Audit Report Generation

**Generate audit reports for compliance:**

```python
class AuditReportGenerator:
    """Generate compliance audit reports"""

    async def generate_access_report(
        self,
        start_date: date,
        end_date: date,
        filters: AuditFilters
    ) -> AccessReport:
        """Generate access audit report"""

        # Query audit log
        access_logs = await db.query("""
            SELECT * FROM audit_log
            WHERE timestamp BETWEEN $1 AND $2
              AND actor->>'type' = ANY($3)
            ORDER BY timestamp
        """, start_date, end_date, filters.actor_types)

        # Build report
        report = AccessReport(
            period_start=start_date,
            period_end=end_date,
            total_access_events=len(access_logs),
            by_actor=self._group_by_actor(access_logs),
            by_action=self._group_by_action(access_logs),
            by_resource=self._group_by_resource(access_logs),
            denied_access=self._count_denied(access_logs),
            unusual_patterns=self._detect_patterns(access_logs)
        )

        return report
```

---

## Part 7: Data Security

### 7.1 Encryption Requirements

**IT Rules 2011 Reasonable Security Practices:**

```typescript
interface EncryptionPolicy {
  field: string;
  at_rest: boolean;            // Database encryption
  in_transit: boolean;         // TLS/SSL
  algorithm: string;
  key_rotation: string;        // How often to rotate keys
}

const ENCRYPTION_POLICY: EncryptionPolicy[] = [
  {
    field: 'customer.phone',
    at_rest: true,
    in_transit: true,
    algorithm: 'AES-256-GCM',
    key_rotation: '90 days'
  },
  {
    field: 'customer.email',
    at_rest: true,
    in_transit: true,
    algorithm: 'AES-256-GCM',
    key_rotation: '90 days'
  },
  {
    field: 'payment.details',
    at_rest: true,
    in_transit: true,
    algorithm: 'AES-256-GCM',
    key_rotation: '30 days'
  }
];
```

### 7.2 Access Control

**Role-based access control:**

```python
class TimelineAccessControl:
    """Control access to timeline data"""

    async def check_access(
        self,
        actor: Actor,
        trip_id: str,
        action: str
    ) -> AccessDecision:
        """Check if actor can access trip timeline"""

        # Get trip workspace
        workspace = await get_workspace(trip_id)
        agency_id = workspace.agency_id

        # Check if actor belongs to agency
        if actor.agency_id != agency_id:
            return AccessDecision(
                allowed=False,
                reason="Actor does not belong to this agency"
            )

        # Check role permissions
        permissions = await self._get_role_permissions(actor.role)

        if action not in permissions.actions:
            return AccessDecision(
                allowed=False,
                reason=f"Role {actor.role} cannot perform {action}"
            )

        # Check internal-only events
        if action == 'view':
            internal_events = await db.query("""
                SELECT COUNT(*) FROM trip_events
                WHERE trip_id = $1
                  AND is_internal_only = true
            """, trip_id)

            if internal_events > 0 and not permissions.can_view_internal:
                # Filter out internal events
                return AccessDecision(
                    allowed=True,
                    filters={'is_internal_only': False}
                )

        return AccessDecision(allowed=True)

    async def _get_role_permissions(self, role: str) -> RolePermissions:
        """Get permissions for role"""

        role_permissions = {
            'owner': RolePermissions(
                actions=['view', 'export', 'delete', 'search'],
                can_view_internal=True,
                can_view_all_trips=True
            ),
            'agent': RolePermissions(
                actions=['view', 'search'],
                can_view_internal=False,
                can_view_all_trips=False  # Only assigned trips
            ),
            'manager': RolePermissions(
                actions=['view', 'export', 'search'],
                can_view_internal=True,
                can_view_all_trips=True
            ),
            'support': RolePermissions(
                actions=['view'],
                can_view_internal=True,
                can_view_all_trips=True
            )
        }

        return role_permissions.get(role, RolePermissions())
```

---

## Part 8: Legal Protection Features

### 8.1 Evidence Export

**Generate court-admissible evidence packages:**

```python
class EvidenceExporter:
    """Export timeline data for legal purposes"""

    async def export_evidence_package(
        self,
        trip_id: str,
        purpose: str,
        requesting_party: str
    ) -> EvidencePackage:
        """Generate complete evidence package"""

        # Get all trip events
        events = await get_trip_events(trip_id)

        # Generate hash chain for integrity
        hash_chain = self._generate_hash_chain(events)

        # Create evidence package
        package = EvidencePackage(
            package_id=generate_id(),
            trip_id=trip_id,
            generated_at=datetime.now(),
            generated_by=get_current_actor(),
            purpose=purpose,
            requesting_party=requesting_party,
            integrity_hash=hash_chain.root_hash,
            contents={
                'timeline_events': events,
                'hash_chain': hash_chain,
                'certificate_of_authenticity': self._generate_certificate(hash_chain)
            }
        )

        # Digitally sign package
        package.signature = self._sign_package(package)

        return package

    def _generate_hash_chain(self, events: List[TripEvent]) -> HashChain:
        """Generate cryptographic hash chain"""

        hashes = []
        previous_hash = None

        for event in sorted(events, key=lambda e: e.timestamp):
            # Hash event content
            event_hash = hashlib.sha256(
                json.dumps(event.dict(), sort_keys=True).encode()
            ).hexdigest()

            # Chain with previous hash
            if previous_hash:
                combined = f"{event_hash}{previous_hash}"
                chained_hash = hashlib.sha256(combined.encode()).hexdigest()
            else:
                chained_hash = event_hash

            hashes.append({
                'event_id': event.id,
                'event_hash': event_hash,
                'chained_hash': chained_hash,
                'previous_hash': previous_hash,
                'timestamp': event.timestamp
            })

            previous_hash = chained_hash

        return HashChain(
            hashes=hashes,
            root_hash=previous_hash
        )

    def _generate_certificate(self, hash_chain: HashChain) -> str:
        """Generate certificate of authenticity"""

        return f"""
        CERTIFICATE OF AUTHENTICITY

        This evidence package was generated on {datetime.now()}.

        Package Integrity:
        - Total Events: {len(hash_chain.hashes)}
        - Root Hash: {hash_chain.root_hash}

        Verification:
        Any modification to this package will result in a different root hash.
        To verify, re-compute the hash chain and compare root hashes.

        Generated by: Travel Agency Agent System
        System Version: {get_system_version()}
        """
```

### 8.2 Dispute Resolution Support

**Timeline features for dispute handling:**

```typescript
interface DisputeResolutionKit {
  trip_id: string;
  dispute_topic: string;
  evidence: {
    commitments: CommitmentRecord[];
    communications: TripEvent[];
    timeline_proof: string;      // Hash-verified proof
    customer_acknowledgments: AcknowledgmentRecord[];
  };
  summary: string;
  recommended_actions: string[];
}
```

---

## Part 9: Compliance Checklist

### Phase 1 Implementation Checklist

**Data Privacy:**
- [ ] Data classification framework implemented
- [ ] Consent capture at all touchpoints
- [ ] Consent verification before timeline creation
- [ ] Right to erasure process documented
- [ ] Data retention policy configured

**Consumer Protection:**
- [ ] Commitment tracking enabled
- [ ] Terms communication tracking
- [ ] Acknowledgment verification
- [ ] Evidence export functionality

**Financial Compliance:**
- [ ] GST audit trail generation
- [ ] TCS tracking for foreign remittances
- [ ] Invoice-timeline linkage
- [ ] Transaction event types defined

**Security:**
- [ ] Role-based access control
- [ ] Audit logging for all access
- [ ] Encryption at rest and in transit
- [ ] Key rotation schedule

---

## Summary

**Legal compliance is not optional for Timeline — it's foundational.**

**Key requirements:**

1. **Data Privacy:** PDPA compliance, consent management, right to erasure
2. **Consumer Protection:** Record of commitments, terms communication
3. **Financial Compliance:** GST audit trail, TCS tracking
4. **Data Retention:** 7-year retention for legal compliance
5. **Audit Capabilities:** Complete access logging
6. **Security:** Encryption, access control, audit trails

**Timeline as Legal Asset:**
- Evidence in disputes
- GST audit support
- Consumer protection compliance
- Contract enforcement support

**Implementation principle:** Privacy by design, compliance by default.

---

**Status:** Legal/compliance framework complete. Ready for legal review.

**Next:** Customer experience deep dive (TIMELINE_07)
