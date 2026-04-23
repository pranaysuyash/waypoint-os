# Timeline: Event Taxonomy (Complete)

> Every event type, data schema, and relationship definition

---

## Part 1: Taxonomy Overview

### Category System

```typescript
enum EventCategory {
  ORIGIN = 'origin',           // Trip beginning
  ANALYSIS = 'analysis',       // AI/ML processing
  DECISION = 'decision',       // State changes, approvals
  CONVERSATION = 'conversation', // Messages, calls
  ACTION = 'action',           // Manual updates, edits
  REVIEW = 'review',           // Owner/manager reviews
  SYSTEM = 'system'            // Automated events
}
```

### Event Type Hierarchy

```
TripEvent (Abstract)
├── Origin Events
│   ├── inquiry_received
│   ├── referral_received
│   └── repeat_booking
├── Analysis Events
│   ├── extraction_completed
│   ├── extraction_confidence_update
│   ├── analysis_scenarios
│   ├── analysis_recommendation
│   └── pattern_detected
├── Decision Events
│   ├── decision_changed
│   ├── decision_confidence_update
│   ├── blocker_identified
│   ├── blocker_resolved
│   └── state_transition
├── Conversation Events
│   ├── whatsapp_message_sent
│   ├── whatsapp_message_received
│   ├── whatsapp_message_delivered
│   ├── email_sent
│   ├── email_received
│   ├── email_opened
│   ├── phone_call_started
│   ├── phone_call_ended
│   └── voicemail_left
├── Action Events
│   ├── field_updated
│   ├── field_bulk_updated
│   ├── document_uploaded
│   ├── document_deleted
│   ├── tag_added
│   └── fields_restored
├── Review Events
│   ├── owner_review_requested
│   ├── owner_review_completed
│   ├── manager_override
│   └── quality_check
└── System Events
    ├── trip_assigned
    ├── trip_unassigned
    ├── sla_alert
    ├── deadline_reminder
    ├── system_error
    └── data_sync_completed
```

---

## Part 2: Origin Events

### 2.1 inquiry_received

**When:** Customer first contacts agency

**Schema:**

```typescript
interface InquiryReceivedEvent extends TripEvent {
  eventType: 'inquiry_received';
  category: 'origin';

  content: {
    // Raw inquiry
    rawMessage: string;

    // Channel details
    channel: 'whatsapp' | 'email' | 'web' | 'phone' | 'referral';

    // Extracted data (if available)
    extractedData?: {
      destination?: string;
      tripType?: string;
      budget?: number;
      dates?: {
        departure?: string;
        return?: string;
        flexibility?: string;
      };
      partySize?: number;
      travelers?: TravelerProfile[];
    };

    // Confidence scores
    confidence?: {
      destination: number;
      budget: number;
      dates: number;
      overall: number;
    };

    // Source metadata
    source?: {
      campaign?: string;
      referrer?: string;
      landingPage?: string;
    };
  };
}
```

**Example:**

```json
{
  "id": "evt_inquiry_abc123",
  "eventType": "inquiry_received",
  "category": "origin",
  "timestamp": "2026-04-20T11:00:00Z",
  "actor": {
    "type": "customer",
    "id": "cust_456",
    "name": "John Doe"
  },
  "source": {
    "channel": "whatsapp",
    "messageId": "wa_msg_789"
  },
  "content": {
    "rawMessage": "Hi, planning honeymoon to Thailand in June. 2 people, budget around 2L",
    "channel": "whatsapp",
    "extractedData": {
      "destination": "Thailand",
      "tripType": "honeymoon",
      "budget": 200000,
      "dates": {
        "departure": "2026-06-01",
        "flexibility": "±7 days"
      },
      "partySize": 2
    },
    "confidence": {
      "destination": 0.95,
      "budget": 0.90,
      "dates": 0.60,
      "overall": 0.82
    }
  }
}
```

### 2.2 referral_received

**When:** Existing customer refers new customer

**Schema:**

```typescript
interface ReferralReceivedEvent extends TripEvent {
  eventType: 'referral_received';
  category: 'origin';

  content: {
    referrerCustomerId: string;
    referrerName: string;
    referredCustomerId?: string;
    referredName?: string;
    relationship: string;
    message?: string;
    incentive?: {
      type: string;
      value: number;
      description: string;
    };
  };
}
```

### 2.3 repeat_booking

**When:** Existing customer books again

**Schema:**

```typescript
interface RepeatBookingEvent extends TripEvent {
  eventType: 'repeat_booking';
  category: 'origin';

  content: {
    previousTrips: string[];  // Trip IDs
    customerSince: string;
    totalBookings: number;
    lifetimeValue: number;
    loyaltyStatus: string;
  };
}
```

---

## Part 3: Analysis Events

### 3.1 extraction_completed

**When:** AI extracts data from inquiry

**Schema:**

```typescript
interface ExtractionCompletedEvent extends TripEvent {
  eventType: 'extraction_completed';
  category: 'analysis';

  content: {
    rawMessage: string;
    extractedFields: {
      destination: string;
      tripType: string;
      budget: number;
      dates: DateRange;
      travelers: TravelerProfile[];
      preferences?: string[];
      requirements?: string[];
    };
    confidenceScores: {
      [field: string]: number;
    };
    missingFields: string[];
    ambiguousFields: {
      field: string;
      detectedValues: string[];
      confidence: number;
    }[];
    modelVersion: string;
    processingTimeMs: number;
  };
}
```

### 3.2 analysis_scenarios

**When:** AI evaluates destination/trip scenarios

**Schema:**

```typescript
interface AnalysisScenariosEvent extends TripEvent {
  eventType: 'analysis_scenarios';
  category: 'analysis';

  content: {
    scenarios: Scenario[];
    selectedScenarioId: string;
    rationale: string;
    comparisonFactors: string[];
    constraints: {
      budget: number;
      dates: DateRange;
      preferences: string[];
    };
    evidence: Evidence[];
    modelVersion: string;
  };
}

interface Scenario {
  id: string;
  name: string;
  description: string;
  destination: string;
  duration: number;
  budget: {
    estimated: number;
    range: { min: number; max: number };
  };
  fit: 'excellent' | 'good' | 'fair' | 'poor';
  pros: string[];
  cons: string[];
  score: number;
  selected: boolean;
  components?: {
    flights?: FlightInfo;
    hotels?: HotelInfo[];
    activities?: ActivityInfo[];
  };
}
```

**Example:**

```json
{
  "eventType": "analysis_scenarios",
  "content": {
    "scenarios": [
      {
        "id": "s1",
        "name": "Phuket + Krabi",
        "destination": "Thailand",
        "duration": 7,
        "budget": { "estimated": 220000, "range": { "min": 180000, "max": 250000 } },
        "fit": "excellent",
        "pros": ["Best beaches", "Good weather in June", "Direct flights"],
        "cons": ["Can be crowded", "Touristy areas"],
        "score": 0.92,
        "selected": true
      },
      {
        "id": "s2",
        "name": "Bangkok + Pattaya",
        "budget": { "estimated": 150000, "range": { "min": 120000, "max": 180000 } },
        "fit": "good",
        "pros": ["Budget-friendly", "More activities"],
        "cons": ["Less romantic", "Busy city"],
        "score": 0.75,
        "selected": false
      }
    ],
    "selectedScenarioId": "s1",
    "rationale": "Phuket+Krabi offers best balance of romantic beaches and budget fit. June weather optimal for Andaman coast."
  }
}
```

### 3.3 pattern_detected

**When:** AI detects pattern across trips

**Schema:**

```typescript
interface PatternDetectedEvent extends TripEvent {
  eventType: 'pattern_detected';
  category: 'analysis';

  content: {
    patternType: 'destination' | 'budget' | 'timing' | 'issue' | 'success';
    patternName: string;
    description: string;
    confidence: number;
    supportingTrips: string[];  // Trip IDs
    anomaly?: boolean;
    recommendation?: string;
    metadata: {
      sampleSize: number;
      patternStrength: number;
      firstSeen: string;
    };
  };
}
```

---

## Part 4: Decision Events

### 4.1 decision_changed

**When:** Trip decision state changes

**Schema:**

```typescript
interface DecisionChangedEvent extends TripEvent {
  eventType: 'decision_changed';
  category: 'decision';

  content: {
    fromState: string;
    toState: string;
    reason: string;
    confidence: number;
    triggers: string[];
    blockers?: Blocker[];
    requirements?: string[];
    actorType: 'ai' | 'agent' | 'owner' | 'system';
  };
}

enum DecisionState {
  INQUIRY_RECEIVED = 'INQUIRY_RECEIVED',
  GATHERING_INFO = 'GATHERING_INFO',
  EVALUATING_OPTIONS = 'EVALUATING_OPTIONS',
  READY_TO_QUOTE = 'READY_TO_QUOTE',
  QUOTE_PRESENTED = 'QUOTE_PRESENTED',
  AWAITING_CONFIRMATION = 'AWAITING_CONFIRMATION',
  READY_TO_BOOK = 'READY_TO_BOOK',
  BOOKING_IN_PROGRESS = 'BOOKING_IN_PROGRESS',
  BOOKED = 'BOOKED',
  CANCELLED = 'CANCELLED',
  NEEDS_ATTENTION = 'NEEDS_ATTENTION',
  NEEDS_OWNER_APPROVAL = 'NEEDS_OWNER_APPROVAL'
}
```

**Example:**

```json
{
  "eventType": "decision_changed",
  "content": {
    "fromState": "EVALUATING_OPTIONS",
    "toState": "READY_TO_QUOTE",
    "reason": "All required information collected. Destination, budget, and dates confirmed.",
    "confidence": 0.95,
    "triggers": [
      "field_updated: departure_date",
      "field_updated: budget_confirmed"
    ]
  }
}
```

### 4.2 blocker_identified

**When:** Something blocks progress

**Schema:**

```typescript
interface BlockerIdentifiedEvent extends TripEvent {
  eventType: 'blocker_identified';
  category: 'decision';

  content: {
    blocker: {
      id: string;
      type: 'budget' | 'dates' | 'destination' | 'requirements' | 'supplier' | 'customer' | 'other';
      severity: 'low' | 'medium' | 'high' | 'critical';
      description: string;
      resolution?: string;
      estimatedResolutionTime?: string;
    };
    impact: string;
    suggestedActions: string[];
  };
}
```

### 4.3 blocker_resolved

**When:** Blocker is cleared

**Schema:**

```typescript
interface BlockerResolvedEvent extends TripEvent {
  eventType: 'blocker_resolved';
  category: 'decision';

  content: {
    blockerId: string;
    resolution: string;
    resolvedBy: string;
    resolvedAt: string;
    timeToResolve: number;  // minutes
    stateTransition: {
      from: string;
      to: string;
    };
  };
}
```

---

## Part 5: Conversation Events

### 5.1 whatsapp_message_sent

**Schema:**

```typescript
interface WhatsAppMessageSentEvent extends TripEvent {
  eventType: 'whatsapp_message_sent';
  category: 'conversation';

  content: {
    messageId: string;
    message: string;
    direction: 'outbound';
    templateUsed?: string;
    media?: {
      type: 'image' | 'video' | 'document' | 'audio' | 'location' | 'contact';
      url: string;
      caption?: string;
    };
    metadata: {
      toNumber: string;
      fromNumber: string;
      sentAt: string;
      deliveredAt?: string;
      readAt?: string;
    };
  };
}
```

### 5.2 whatsapp_message_received

**Schema:**

```typescript
interface WhatsAppMessageReceivedEvent extends TripEvent {
  eventType: 'whatsapp_message_received';
  category: 'conversation';

  content: {
    messageId: string;
    message: string;
    direction: 'inbound';
    media?: {
      type: 'image' | 'video' | 'document' | 'audio' | 'location' | 'contact';
      url: string;
      caption?: string;
    };
    metadata: {
      fromNumber: string;
      toNumber: string;
      receivedAt: string;
    };
  };
}
```

### 5.3 email_sent

**Schema:**

```typescript
interface EmailSentEvent extends TripEvent {
  eventType: 'email_sent';
  category: 'conversation';

  content: {
    emailId: string;
    subject: string;
    body: string;
    bodyHtml?: string;
    direction: 'outbound';
    to: EmailAddress[];
    cc?: EmailAddress[];
    bcc?: EmailAddress[];
    attachments?: Attachment[];
    metadata: {
      messageId: string;
      threadId: string;
      sentAt: string;
      deliveryStatus?: 'sent' | 'delivered' | 'bounced' | 'failed';
      openedAt?: string;
      clickedAt?: string;
    };
  };
}
```

### 5.4 email_received

**Schema:**

```typescript
interface EmailReceivedEvent extends TripEvent {
  eventType: 'email_received';
  category: 'conversation';

  content: {
    emailId: string;
    subject: string;
    body: string;
    bodyHtml?: string;
    direction: 'inbound';
    from: EmailAddress;
    to: EmailAddress[];
    cc?: EmailAddress[];
    attachments?: Attachment[];
    metadata: {
      messageId: string;
      threadId: string;
      receivedAt: string;
      inReplyTo?: string;
    };
  };
}
```

### 5.5 phone_call_started

**Schema:**

```typescript
interface PhoneCallStartedEvent extends TripEvent {
  eventType: 'phone_call_started';
  category: 'conversation';

  content: {
    callId: string;
    direction: 'inbound' | 'outbound';
    fromNumber: string;
    toNumber: string;
    startedAt: string;
    recordingEnabled: boolean;
  };
}
```

### 5.6 phone_call_ended

**Schema:**

```typescript
interface PhoneCallEndedEvent extends TripEvent {
  eventType: 'phone_call_ended';
  category: 'conversation';

  content: {
    callId: string;
    direction: 'inbound' | 'outbound';
    duration: number;  // seconds
    endedAt: string;
    status: 'completed' | 'no_answer' | 'busy' | 'failed';
    recordingUrl?: string;
    transcript?: string;
    summary?: string;
    sentiment?: 'positive' | 'neutral' | 'negative';
  };
}
```

---

## Part 6: Action Events

### 6.1 field_updated

**Schema:**

```typescript
interface FieldUpdatedEvent extends TripEvent {
  eventType: 'field_updated';
  category: 'action';

  content: {
    field: string;
    oldValue: any;
    newValue: any;
    reason?: string;
    relatedFields?: string[];
    bulkUpdate?: boolean;
  };
}
```

**Example:**

```json
{
  "eventType": "field_updated",
  "content": {
    "field": "destination",
    "oldValue": "Thailand",
    "newValue": "Thailand - Phuket + Krabi",
    "reason": "Customer specified exact destinations"
  }
}
```

### 6.2 field_bulk_updated

**Schema:**

```typescript
interface FieldBulkUpdatedEvent extends TripEvent {
  eventType: 'field_bulk_updated';
  category: 'action';

  content: {
    fields: {
      field: string;
      oldValue: any;
      newValue: any;
    }[];
    reason: string;
    source: 'import' | 'api' | 'bulk_edit' | 'template';
    recordCount: number;
  };
}
```

### 6.3 document_uploaded

**Schema:**

```typescript
interface DocumentUploadedEvent extends TripEvent {
  eventType: 'document_uploaded';
  category: 'action';

  content: {
    documentId: string;
    documentType: 'quote' | 'invoice' | 'itinerary' | 'ticket' | 'voucher' | 'passport' | 'visa' | 'other';
    fileName: string;
    fileSize: number;
    mimeType: string;
    url: string;
    uploadedBy: string;
    description?: string;
    tags?: string[];
    version?: number;
  };
}
```

---

## Part 7: Review Events

### 7.1 owner_review_requested

**Schema:**

```typescript
interface OwnerReviewRequestedEvent extends TripEvent {
  eventType: 'owner_review_requested';
  category: 'review';

  content: {
    reviewType: 'budget_exceed' | 'high_value' | 'complex_trip' | 'customer_issue' | 'other';
    reason: string;
    urgency: 'low' | 'medium' | 'high';
    requestedBy: string;
    context: {
      currentBudget?: number;
      customerBudget?: number;
      overage?: number;
      tripComplexity?: string;
    };
  };
}
```

### 7.2 owner_review_completed

**Schema:**

```typescript
interface OwnerReviewCompletedEvent extends TripEvent {
  eventType: 'owner_review_completed';
  category: 'review';

  content: {
    decision: 'approved' | 'rejected' | 'modified' | 'escalated';
    reason: string;
    notes?: string;
    approvedBy: string;
    approvedAt: string;
    conditions?: string[];
    modifications?: {
      field: string;
      previousValue: any;
      newValue: any;
    }[];
  };
}
```

---

## Part 8: System Events

### 8.1 trip_assigned

**Schema:**

```typescript
interface TripAssignedEvent extends TripEvent {
  eventType: 'trip_assigned';
  category: 'system';

  content: {
    assignedTo: string;
    assignedToName: string;
    assignedBy: string;
    assignmentType: 'manual' | 'auto' | 'round_robin' | 'workload_balance';
    previousAssignee?: string;
    reason?: string;
  };
}
```

### 8.2 sla_alert

**Schema:**

```typescript
interface SLAAlertEvent extends TripEvent {
  eventType: 'sla_alert';
  category: 'system';

  content: {
    slaType: 'response_time' | 'quote_time' | 'resolution_time';
    threshold: number;  // minutes/hours
    elapsed: number;
    remaining: number;  // negative = overdue
    severity: 'warning' | 'critical';
    actionRequired: string;
  };
}
```

### 8.3 deadline_reminder

**Schema:**

```typescript
interface DeadlineReminderEvent extends TripEvent {
  eventType: 'deadline_reminder';
  category: 'system';

  content: {
    deadlineType: 'quote_expiry' | 'payment_due' | 'booking_deadline' | 'document_submission';
    deadline: string;
    timeRemaining: string;
    affectedParty: 'agent' | 'customer' | 'supplier';
    action: string;
    urgency: 'low' | 'medium' | 'high';
  };
}
```

---

## Part 9: Event Relationships

### Parent-Child Relationships

```typescript
interface EventRelationships {
  parentEventId?: string;      // This event responds to
  relatedEventIds?: string[];  // Related context
  triggeredEvents?: string[];  // Events this caused
}
```

**Examples:**

```
Parent: inquiry_received
  ├─ Child: extraction_completed (triggered by)
  ├─ Child: analysis_scenarios (triggered by)
  └─ Child: decision_changed (result of)

Parent: whatsapp_message_received
  ├─ Child: field_updated (customer provided info)
  ├─ Child: extraction_completed (new data to extract)
  └─ Child: decision_changed (state changed)
```

### Event Chains

```typescript
interface EventChain {
  chainId: string;
  triggerEvent: string;
  events: string[];
  chainType: 'conversation' | 'workflow' | 'investigation' | 'resolution';
}
```

---

## Part 10: Event Metadata

### Standard Metadata

```typescript
interface EventMetadata {
  // Display control
  isInternalOnly: boolean;     // Don't show customer
  isHighlighted: boolean;      // Important event
  isPinned: boolean;           // Always show at top

  // Organization
  tags?: string[];             // For filtering/grouping
  category?: string;           // Custom category

  // AI enrichment
  aiSummary?: string;
  aiSentiment?: SentimentAnalysis;
  aiUrgency?: UrgencyAnalysis;
  aiEntities?: EntityExtraction;

  // Technical
  sourceVersion?: string;      // API version
  ingestionTime?: string;      // When we received it
  processedTime?: string;      // When we processed it

  // Audit
  ipAddress?: string;
  userAgent?: string;
  requestId?: string;
}
```

---

## Summary

**Complete Event Count:** 40+ event types across 7 categories

**Usage Guide:**

| Use Case | Recommended Events |
|----------|-------------------|
| **Trip Story** | inquiry_received, extraction_completed, analysis_scenarios, decision_changed, whatsapp_message_* |
| **Handoff** | All events with AI summaries |
| **Dispute Resolution** | All conversation events, decision_changed, field_updated |
| **Performance Review** | trip_assigned, owner_review_*, sla_alert |
| **Compliance** | All events with timestamps, actors, content |

**Extensibility:**
- Custom event types via `eventType: "custom_*"`
- Custom categories via `category: "custom"`
- Flexible content schema via JSONB

---

**Status:** Event taxonomy complete and versioned.
**Version:** 1.0
**Last Updated:** 2026-04-23
