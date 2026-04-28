# Travel Fraud Detection & Prevention — Investigation & Response

> Research document for fraud investigation workflows, incident response, prevention measures, and fraud analytics.

---

## Key Questions

1. **How do we investigate suspected fraud?**
2. **What's the incident response process for confirmed fraud?**
3. **How do we recover losses from fraud?**
4. **What prevention measures reduce future fraud?**
5. **What reporting and compliance is required for fraud incidents?**

---

## Research Areas

### Fraud Investigation Workflow

```typescript
interface FraudInvestigation {
  caseId: string;
  type: FraudType;
  status: InvestigationStatus;
  assignedTo: string;
  bookingId?: string;
  customerId?: string;
  agentId?: string;
  timeline: InvestigationTimeline;
  evidence: Evidence[];
  actions: InvestigationAction[];
  resolution: InvestigationResolution;
}

type InvestigationStatus =
  | 'detected'                        // Fraud signal detected
  | 'triaged'                         // Prioritized for investigation
  | 'investigating'                   // Active investigation
  | 'evidence_collected'             // Evidence gathered
  | 'decision_pending'               // Waiting for decision
  | 'resolved'                       // Investigation complete
  | 'escalated';                     // Escalated to management/legal

// Investigation workflow:
//
// Step 1: Detection & Triage (0-4 hours)
// - Fraud signal triggered (automated or manual report)
// - System auto-gathers initial data:
//   - Booking details, customer profile, payment info
//   - IP logs, device fingerprint, communication history
//   - Previous fraud flags on customer/agent/card
// - Triage decision:
//   - Low priority: Queue for batch review
//   - Medium priority: Investigate within 24 hours
//   - High priority: Immediate investigation
//   - Critical: Block transaction, investigate immediately
//
// Step 2: Investigation (4-48 hours)
// - Review booking and payment details
// - Cross-reference with fraud databases
// - Contact customer for verification (if needed)
// - Contact payment gateway for transaction details
// - Review agent actions (if internal fraud suspected)
// - Document all findings
//
// Step 3: Decision
// - Confirmed fraud: Proceed to response actions
// - Suspicious but unconfirmed: Enhanced monitoring
// - False positive: Close case, update detection rules
// - Insufficient evidence: Monitor, keep case open (30-day expiry)
//
// Step 4: Response (immediate for confirmed)
// - See response actions below
//
// Step 5: Post-investigation
// - Update fraud detection rules (if new pattern discovered)
// - Add customer/agent to watchlist (if confirmed)
// - Report to authorities (if required)
// - Document learnings for team training

interface Evidence {
  type: EvidenceType;
  source: string;
  data: string;
  collectedAt: Date;
  collectedBy: string;
}

type EvidenceType =
  | 'booking_record'
  | 'payment_record'
  | 'communication_log'
  | 'ip_device_data'
  | 'identity_document'
  | 'agent_action_log'
  | 'supplier_record'
  | 'external_database';

// Evidence collection (automated):
// - Booking: Full booking details, timestamps, agent actions
// - Payment: Transaction ID, amount, card BIN, AVS result, 3DS status
// - Communication: WhatsApp messages, emails, call recordings
// - Technical: IP address, device fingerprint, browser, screen resolution
// - Identity: Uploaded documents, verification results, selfie photos
// - Agent log: Actions taken on booking, modifications, cancellations
```

### Incident Response

```typescript
interface IncidentResponse {
  caseId: string;
  fraudType: FraudType;
  severity: 'low' | 'medium' | 'high' | 'critical';
  actions: ResponseAction[];
  recovery: RecoveryAction[];
  communication: CommunicationAction[];
  timeline: ResponseTimeline;
}

interface ResponseAction {
  action: string;
  executedAt?: Date;
  executedBy?: string;
  status: 'pending' | 'executed' | 'failed';
}

// Response actions by severity:
//
// LOW (minor fraud, < ₹5,000 loss):
// - Flag customer for enhanced monitoring
// - Update fraud detection rules
// - Document case
// - No recovery action (cost exceeds potential recovery)
//
// MEDIUM (₹5,000-50,000 loss):
// - Flag customer and block future high-risk bookings
// - Attempt chargeback representment (if card payment)
// - Request customer to explain discrepancy
// - Update fraud detection rules
// - Report to payment gateway
//
// HIGH (₹50,000-5,00,000 loss):
// - Block customer account
// - Initiate chargeback representment with full evidence
// - Notify payment gateway fraud team
// - Request police complaint filing (Section 420 IPC)
// - Engage recovery agency (if viable)
// - Full audit of related bookings
// - Notify agency owner/management
//
// CRITICAL (> ₹5,00,000 or organized fraud):
// - All HIGH actions plus:
// - File FIR with cyber crime cell
// - Engage legal counsel
// - Report to CERT-In (if cyber crime component)
// - Notify insurance (if covered under professional indemnity)
// - Media/PR management (if public-facing incident)
// - Board notification (if company)

interface RecoveryAction {
  method: RecoveryMethod;
  amount: Money;
  probability: number;                // 0-1 chance of success
  timeline: string;
  status: RecoveryStatus;
}

type RecoveryMethod =
  | 'chargeback_representment'         // Fight the chargeback
  | 'payment_recovery'                // Demand payment from fraudster
  | 'insurance_claim'                 // Claim on fraud insurance
  | 'supplier_recovery'               // Recover from supplier (if complicit)
  | 'agent_recovery'                  // Recover from agent (if internal fraud)
  | 'write_off';                      // Accept loss

// Recovery probability by method:
// Chargeback representment: 30-50% success rate
// Payment recovery: 5-15% (fraudsters rarely pay)
// Insurance claim: 80-90% (if policy covers fraud)
// Supplier recovery: 20-40% (if supplier was negligent)
// Agent recovery: 60-80% (legal action threat effective)
// Write-off: 100% (loss accepted)
```

### Fraud Prevention Measures

```typescript
interface FraudPrevention {
  policies: FraudPolicy[];
  training: FraudTraining[];
  monitoring: ContinuousMonitoring;
  reporting: FraudReporting;
}

interface FraudPolicy {
  policy: string;
  category: 'customer' | 'agent' | 'supplier' | 'platform';
  enforcement: 'automatic' | 'manual';
}

// Fraud prevention policies:
//
// Customer-facing:
// - Mandatory OTP for all payments (RBI mandate)
// - Booking value limits for new customers (₹1L initial, increases with history)
// - Enhanced verification for international bookings
// - Cooling period: 24 hours between account creation and first high-value booking
// - Payment method restrictions: No third-party wallet for high-value bookings
// - Maximum 3 active bookings for new customers
//
// Agent-facing:
// - No self-bookings (agent can't book for themselves at commission rates)
// - Family booking requires manager approval
// - Commission only on completed trips (not cancellations)
// - Random audit of agent bookings (5% monthly)
// - No supplier payments without matching booking
// - Agent access to customer data logged and audited
//
// Supplier-facing:
// - Supplier verification before first payment
// - No advance payments to new suppliers > ₹10,000
// - Bank account verification (penny drop) before first payment
// - GSTIN verification before processing invoices
// - Regular supplier statement reconciliation
//
// Platform-level:
// - Role-based access control (no agent can approve their own payments)
// - Dual approval for payments > ₹25,000
// - Automated daily reconciliation
// - Audit trail for all financial transactions
// - Regular penetration testing (quarterly)
// - Employee background verification

interface ContinuousMonitoring {
  realTime: RealTimeMonitor[];
  daily: DailyCheck[];
  weekly: WeeklyReview[];
  monthly: MonthlyAudit[];
}

// Continuous monitoring dashboard:
// ┌──────────────────────────────────────────┐
// │  Fraud Monitoring Dashboard               │
// │                                          │
// │  Today:                                   │
// │  Bookings: 45 | Flagged: 3 (6.7%)       │
// │  Payments: ₹18.5L | Blocked: ₹2.1L      │
// │                                          │
// │  Active Alerts:                           │
// │  🔴 Card on fraud watchlist used          │
// │     Booking #TRV-45789, ₹1.8L            │
// │     Action: Blocked, awaiting review      │
// │                                          │
// │  🟡 Suspicious booking pattern            │
// │     3 bookings from same IP, diff cards   │
// │     Action: Enhanced verification required│
// │                                          │
// │  🟢 Minor velocity trigger                │
// │     2 payment attempts, same card         │
// │     Action: Auto-approved (2nd attempt)   │
// │                                          │
// │  Monthly Stats:                           │
// │  Fraud rate: 0.3% (target: <0.5%)        │
// │  Chargeback rate: 0.1% (target: <0.5%)   │
// │  False positive rate: 8% (target: <10%)  │
// │  Loss prevention: ₹4.2L saved this month  │
// │                                          │
// │  [View Cases] [Export Report]             │
// └──────────────────────────────────────────┘
```

---

## Open Problems

1. **Recovery cost vs. recovery amount** — Pursuing ₹5,000 fraud costs more in staff time than the fraud loss. Need clear thresholds for when to investigate vs. write off.

2. **Internal fraud detection** — Agents have legitimate access to booking and payment systems. Detecting abuse of legitimate access is harder than detecting external fraud.

3. **Cross-platform fraud** — Same fraudster may target multiple travel agencies. No industry-wide fraud database in India (unlike banking's negative list).

4. **Legal enforcement** — Filing FIR for cyber fraud is slow in India. Investigations take months. Recovery probability is low.

5. **Customer experience vs. security** — Every fraud prevention measure adds friction. The 3% of fraudsters cause 97% of genuine customers to go through additional verification.

---

## Next Steps

- [ ] Build fraud investigation workflow with case management
- [ ] Create incident response playbook with severity-based actions
- [ ] Design continuous fraud monitoring dashboard
- [ ] Build fraud analytics with detection rule management
- [ ] Study fraud management platforms (Sardine, Unit21, Featurespace, Feedzai)
