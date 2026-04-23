# Timeline: Integration Deep Dive

> Every possible connection: data sources, APIs, third-party services, and internal systems

---

## Part 1: Integration Architecture Overview

### The Integration Challenge

Timeline is only as valuable as the data it captures. A manual timeline is a toy — an automated timeline is a strategic asset.

**Integration Philosophy:**
- **Push over pull:** Systems push events to Timeline when they happen
- **Async everywhere:** No blocking calls, all integration via queues
- **Idempotent:** Retry-safe, duplicate detection built-in
- **Schema-flexible:** JSONB content accommodates any source
- **Graceful degradation:** Timeline works even if source is down

---

## Part 2: Data Source Taxonomy

### 2.1 Internal Systems

| System | Events | Priority | Complexity |
|--------|--------|----------|------------|
| **Intake Pipeline** | Inquiry received, extraction results | P0 | Low |
| **Decision Engine** | Decisions, state changes, confidence | P0 | Low |
| **Workspace/Fields** | Field edits, manual updates | P0 | Medium |
| **Output Generator** | Bundles created, quotes sent | P0 | Low |
| **Safety Systems** | Risk flags, compliance checks | P1 | Medium |
| **User Management** | Agent assignments, role changes | P1 | Low |
| **Notification System** | Alerts sent, reminders | P2 | Low |

### 2.2 External Communication Channels

| Channel | Events | Priority | Complexity |
|---------|--------|----------|------------|
| **WhatsApp Business API** | Messages (in/out), status updates | P0 | High |
| **Email (SMTP/IMAP)** | Emails (in/out), delivery status | P0 | Medium |
| **Phone System** | Call logs, transcripts, recordings | P1 | High |
| **Web Chat** | Chat sessions, transcripts | P2 | Medium |
| **SMS Gateway** | SMS sent/delivered | P2 | Low |

### 2.3 Third-Party Services

| Service | Events | Priority | Complexity |
|---------|--------|----------|------------|
| **Supplier APIs** | Price checks, availability, bookings | P1 | High |
| **Payment Gateway** | Transactions, refunds, status | P1 | Medium |
| **CRM Systems** | Contact sync, external references | P2 | High |
| **Analytics Tools** | Tracking events, conversions | P2 | Low |
| **Calendar Systems** | Meeting schedules, reminders | P2 | Medium |

---

## Part 3: Integration Patterns

### Pattern 1: Event Publisher (Internal Systems)

**Use Case:** Any internal system that generates trip events

```python
# Internal system publishes event
class EventPublisher:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def publish_event(self, event: TripEvent):
        """Publish event to timeline via message queue"""
        await self.event_bus.publish(
            topic="timeline.events",
            message={
                "event_id": event.id,
                "trip_id": event.trip_id,
                "workspace_id": event.workspace_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "content": event.content,
                "metadata": event.metadata
            }
        )
```

**Advantages:**
- Decoupled: Systems don't know about Timeline directly
- Reliable: Queue handles failures and retries
- Scalable: Async processing

**Implementation Order:**
1. Decision Engine (highest value, lowest effort)
2. Intake Pipeline
3. Output Generator
4. Workspace/Field edits

---

### Pattern 2: Webhook Consumer (External APIs)

**Use Case:** External systems that send webhooks

```python
# Webhook endpoint for external events
@app.post("/api/webhooks/timeline")
async def timeline_webhook(request: WebhookRequest):
    """Receive events from external systems"""

    # Verify webhook signature
    if not verify_signature(request):
        raise HTTPException(401, "Invalid signature")

    # Validate and transform to TripEvent
    trip_event = transform_webhook_to_event(request)

    # Queue for processing (don't block webhook response)
    await event_queue.enqueue(trip_event)

    return {"status": "accepted", "event_id": trip_event.id}
```

**External Systems with Webhooks:**
- Payment Gateway (transaction events)
- Supplier APIs (booking confirmations)
- CRM Systems (contact updates)
- Calendar Systems (meeting events)

---

### Pattern 3: Polling Consumer (No Webhook Available)

**Use Case:** Systems without webhook support

```python
# Periodic polling for new data
class PollingConsumer:
    def __init__(self, source: DataSource, interval: int):
        self.source = source
        self.interval = interval  # seconds

    async def poll(self):
        """Poll source for new events"""
        last_checkpoint = self.get_last_checkpoint()

        new_events = await self.source.fetch_events(since=last_checkpoint)

        for event in new_events:
            await event_queue.enqueue(event)

        await self.update_checkpoint(new_events[-1].timestamp if new_events else last_checkpoint)
```

**Systems Requiring Polling:**
- Email (IMAP polling for new emails)
- Legacy CRM systems
- Phone systems without webhooks
- Supplier booking status checks

**Polling Strategy:**
- Real-time sources: 1-5 minutes
- Batch sources: 15-60 minutes
- Static sources: 1-24 hours

---

### Pattern 4: Stream Processor (Real-time Data)

**Use Case:** High-volume real-time data streams

```python
# Process streaming events
class StreamProcessor:
    def __init__(self, stream: EventStream):
        self.stream = stream

    async def process_stream(self):
        """Continuously process streaming events"""
        async for event in self.stream:
            # Filter relevant events
            if self.is_relevant(event):
                # Batch insert for efficiency
                await self.batch_insert([event])

            # Acknowledge stream position
            await event.ack()
```

**Streaming Sources:**
- WebSocket connections (live chat)
- Server-Sent Events (SSE)
- Kafka/Kinesis streams (for enterprise)

---

## Part 4: System-Specific Integrations

### 4.1 WhatsApp Business API Integration

**Why Critical:** Primary customer communication channel

**Event Types Captured:**
```typescript
interface WhatsAppEvent extends TripEvent {
  eventType: 'whatsapp_message_sent' |
              'whatsapp_message_received' |
              'whatsapp_message_delivered' |
              'whatsapp_message_read' |
              'whatsapp_media_shared';

  content: {
    messageId: string;
    direction: 'inbound' | 'outbound';
    message: string;
    mediaType?: 'image' | 'video' | 'document' | 'audio' | 'location';
    mediaUrl?: string;
    metadata: {
      fromNumber: string;
      toNumber: string;
      timestamp: string;
      status: 'sent' | 'delivered' | 'read' | 'failed';
    };
  };
}
```

**Integration Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    WhatsApp Integration                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Webhook Receiver (FastAPI endpoint)                          │
│     └─ POST /api/webhooks/whatsapp                              │
│        └─ Verify signature, validate payload                    │
│                                                                   │
│  2. Message Transformer                                          │
│     └─ Convert WhatsApp format → TripEvent                      │
│     └─ Link to workspace via phone number lookup               │
│                                                                   │
│  3. Event Queue (Redis/RedisMQ)                                  │
│     └─ Async processing, retry logic                            │
│                                                                   │
│  4. Timeline Ingestion Service                                   │
│     └─ Batch insert to TripEvents table                        │
│     └─ Trigger real-time update via WebSocket                  │
│                                                                   │
│  5. Storage Service                                              │
│     └─ Download and store media files                          │
│     └─ Generate thumbnails for timeline display                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**WhatsApp Webhook Handler:**

```python
@app.post("/api/webhooks/whatsapp")
async def whatsapp_webhook(payload: WhatsAppWebhookPayload):
    """Handle WhatsApp webhook"""

    # Verify webhook signature
    if not verify_whatsapp_signature(payload):
        logger.warning("Invalid WhatsApp webhook signature")
        return {"status": "error"}

    # Process each message
    events = []
    for entry in payload.entry:
        for change in entry.changes:
            for message in change.value.messages:

                # Find workspace by customer phone
                workspace = await find_workspace_by_phone(message.from_)
                if not workspace:
                    logger.info(f"No workspace found for {message.from_}")
                    continue

                # Create timeline event
                event = TripEvent(
                    trip_id=workspace.trip_id,
                    workspace_id=workspace.id,
                    eventType='whatsapp_message_received',
                    category=EventCategory.CONVERSATION,
                    timestamp=datetime.fromtimestamp(int(message.timestamp)),
                    actor={
                        'id': message.from_,
                        'name': workspace.customer_name,
                        'type': 'customer'
                    },
                    source={
                        'channel': 'whatsapp',
                        'messageId': message.id
                    },
                    content={
                        'direction': 'inbound',
                        'message': message.text.body if message.text else None,
                        'mediaType': get_media_type(message),
                        'mediaUrl': get_media_url(message)
                    }
                )
                events.append(event)

    # Queue for batch processing
    await event_queue.enqueue_many(events)

    return {"status": "accepted", "event_count": len(events)}
```

**Message Retrieval (Historical Sync):**

```python
async def sync_historical_whatsapp(
    workspace_id: str,
    since: datetime,
    limit: int = 100
):
    """Sync historical WhatsApp messages for a workspace"""

    workspace = await get_workspace(workspace_id)

    # Fetch messages from WhatsApp API
    messages = await whatsapp_client.get_messages(
        phone_number=workspace.customer_phone,
        since=since,
        limit=limit
    )

    # Convert to timeline events
    events = [convert_whatsapp_to_event(msg, workspace) for msg in messages]

    # Batch insert
    await insert_timeline_events(events)

    return len(events)
```

---

### 4.2 Email Integration

**Why Important:** Formal communications, quotes, confirmations

**Event Types Captured:**
```typescript
interface EmailEvent extends TripEvent {
  eventType: 'email_sent' |
              'email_received' |
              'email_delivered' |
              'email_opened' |
              'email_link_clicked';

  content: {
    emailId: string;
    subject: string;
    body: string;  // HTML + plain text
    direction: 'inbound' | 'outbound';
    from: EmailAddress;
    to: EmailAddress[];
    cc?: EmailAddress[];
    attachments?: Attachment[];
    metadata: {
      messageId: string;
      threadId: string;
      deliveredAt?: string;
      openedAt?: string;
    };
  };
}
```

**Integration Options:**

| Option | Complexity | Real-time | Cost |
|--------|------------|-----------|------|
| **SMTP Parse + Webhook** (SendGrid/Mailgun) | Low | Yes | Paid |
| **IMAP IDLE** (Push notification) | Medium | Near real-time | Free |
| **IMAP Polling** | Low | Delayed (5-15 min) | Free |

**Recommended:** SMTP provider (SendGrid/Mailgun) for outbound, IMAP IDLE for inbound

**IMAP IDLE Integration:**

```python
class EmailIMAPMonitor:
    """Monitor email inbox via IMAP IDLE for push notifications"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.imap_client = imaplib.IMAP4_SSL(config.imap_server)

    async def start_monitoring(self):
        """Start IDLE monitoring"""

        # Login and select inbox
        self.imap_client.login(config.username, config.password)
        self.imap_client.select('INBOX')

        while True:
            # Check for new emails
            self.imap_client.idle()
            while True:
                # Wait for IDLE response
                response = self.imap_client.idle_check(timeout=29)

                if response:
                    # New emails arrived
                    await self.process_new_emails()

                    # Re-enter IDLE
                    self.imap_client.idle_done()
                    break

    async def process_new_emails(self):
        """Process new emails and create timeline events"""

        # Search for unseen emails
        status, messages = self.imap_client.search(None, 'UNSEEN')

        for msg_id in messages[0].split():
            # Fetch email
            status, data = self.imap_client.fetch(msg_id, '(RFC822)')

            # Parse email
            email = parse_email(data[0])

            # Find workspace by sender email
            workspace = await find_workspace_by_email(email.from_address)

            if workspace:
                # Create timeline event
                event = create_email_timeline_event(email, workspace)
                await event_queue.enqueue(event)

            # Mark as read
            self.imap_client.store(msg_id, '+FLAGS', '\\Seen')
```

**Email Threading:**
- Group emails by `threadId` (References + In-Reply-To headers)
- Display as conversation thread in Timeline
- Show email chain expanded/collapsed

---

### 4.3 Phone System Integration

**Why Valuable:** Verbal commitments, urgent conversations

**Event Types Captured:**
```typescript
interface PhoneEvent extends TripEvent {
  eventType: 'call_started' |
              'call_ended' |
              'call_missed' |
              'voicemail_left' |
              'call_transcript_available';

  content: {
    callId: string;
    direction: 'inbound' | 'outbound';
    duration?: number;  // seconds
    recordingUrl?: string;
    transcript?: string;
    sentiment?: 'positive' | 'neutral' | 'negative';
    summary?: string;  // AI-generated
    metadata: {
      fromNumber: string;
      toNumber: string;
      startTime: string;
      endTime: string;
      answerStatus: 'answered' | 'no_answer' | 'busy' | 'failed';
    };
  };
}
```

**Integration Options:**

| Provider | Webhook | Recording | Transcription | Cost |
|----------|---------|-----------|---------------|------|
| **Twilio** | Yes | Yes | Yes (via AI) | Paid |
| **Exotel** | Yes | Yes | No | Paid |
| **MyOperator** | Yes | Yes | No | Paid |
| **Plivo** | Yes | Yes | No | Paid |

**Twilio Webhook Handler:**

```python
@app.post("/api/webhooks/twilio/call_events")
async def twilio_call_webhook(request: Request):
    """Handle Twilio call event webhooks"""

    form_data = await request.form()

    # Extract call data
    call_sid = form_data.get('CallSid')
    call_status = form_data.get('CallStatus')
    direction = form_data.get('Direction')
    from_number = form_data.get('From')
    to_number = form_data.get('To')
    duration = form_data.get('CallDuration')

    # Find workspace by phone number
    workspace = await find_workspace_by_phone(from_number)
    if not workspace:
        return {"status": "ok"}  # Acknowledge webhook

    # Map Twilio status to our event types
    event_type_map = {
        'ringing': 'call_started',
        'completed': 'call_ended',
        'no-answer': 'call_missed',
        'voicemail': 'voicemail_left'
    }

    event_type = event_type_map.get(call_status, 'call_ended')

    # Create timeline event
    event = TripEvent(
        trip_id=workspace.trip_id,
        workspace_id=workspace.id,
        eventType=event_type,
        category=EventCategory.CONVERSATION,
        timestamp=datetime.now(),
        actor={
            'id': from_number,
            'name': workspace.customer_name,
            'type': 'customer' if direction == 'inbound' else 'agent'
        },
        source={
            'channel': 'phone',
            'callId': call_sid
        },
        content={
            'direction': direction.lower(),
            'duration': int(duration) if duration else None,
            'recordingUrl': form_data.get('RecordingUrl'),
            'metadata': {
                'fromNumber': from_number,
                'toNumber': to_number,
                'startTime': form_data.get('StartTime'),
                'endTime': form_data.get('EndTime'),
                'answerStatus': call_status
            }
        }
    )

    await event_queue.enqueue(event)

    return Response(status_code=200)  # Twilio expects 200
```

**AI Transcription Integration:**

```python
async def transcribe_call_recording(recording_url: str, event_id: str):
    """Transcribe call recording using AI"""

    # Download recording
    audio_file = await download_audio(recording_url)

    # Transcribe using speech-to-text
    transcript = await speech_to_text.transcribe(audio_file)

    # Generate summary using LLM
    summary = await llm.summarize(
        text=transcript,
        context="Call between travel agent and customer about trip booking"
    )

    # Update timeline event
    await update_timeline_event(
        event_id=event_id,
        updates={
            'content.transcript': transcript,
            'content.summary': summary,
            'content.aiSummary': summary
        }
    )
```

---

### 4.4 Decision Engine Integration

**Why Critical:** Core intelligence, decision rationale

**Event Types Captured:**
```typescript
interface DecisionEvent extends TripEvent {
  eventType: 'decision_changed' |
              'decision_confidence_update' |
              'decision_blocker_added' |
              'decision_blocker_resolved' |
              'decision_scenario_evaluated';

  content: {
    fromState?: string;
    toState: string;
    confidence: number;
    reason: string;
    triggers?: string[];
    blockers?: Blocker[];
    scenarios?: Scenario[];
    evidence?: Evidence[];
  };
}
```

**Integration: Direct Method Call**

```python
class DecisionEngine:
    """Decision engine that publishes timeline events"""

    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher

    async def make_decision(
        self,
        workspace_id: str,
        trip_context: TripContext
    ) -> Decision:
        """Make decision and publish to timeline"""

        # Previous state
        old_state = trip_context.current_state

        # Run decision logic
        decision = await self._evaluate(trip_context)

        # Publish state change event
        await self.event_publisher.publish_event(
            TripEvent(
                workspace_id=workspace_id,
                trip_id=trip_context.trip_id,
                eventType='decision_changed',
                category=EventCategory.DECISION,
                timestamp=datetime.now(),
                actor={'type': 'ai', 'name': 'Decision Engine'},
                content={
                    'fromState': old_state,
                    'toState': decision.state,
                    'confidence': decision.confidence,
                    'reason': decision.rationale,
                    'triggers': decision.triggers,
                    'blockers': decision.blockers
                }
            )
        )

        return decision
```

---

### 4.5 Workspace/Field Edit Integration

**Why Important:** Track all manual changes to trip data

**Event Types Captured:**
```typescript
interface FieldEditEvent extends TripEvent {
  eventType: 'field_updated' |
              'field_bulk_updated' |
              'fields_restored';

  content: {
    field: string;
    oldValue: any;
    newValue: any;
    reason?: string;
    relatedFields?: string[];  // For bulk updates
  };
}
```

**Integration: ORM/ODM Hooks**

```python
class WorkspaceChangeListener:
    """Listen for workspace changes and create timeline events"""

    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher

    async def on_field_change(
        self,
        workspace_id: str,
        field: str,
        old_value: any,
        new_value: any,
        actor_id: str,
        actor_name: str
    ):
        """Handle field change event"""

        # Skip if no actual change
        if old_value == new_value:
            return

        # Skip certain fields (internal metadata)
        if field in INTERNAL_FIELDS:
            return

        # Publish timeline event
        await self.event_publisher.publish_event(
            TripEvent(
                workspace_id=workspace_id,
                eventType='field_updated',
                category=EventCategory.ACTION,
                timestamp=datetime.now(),
                actor={
                    'id': actor_id,
                    'name': actor_name,
                    'type': 'agent'
                },
                content={
                    'field': field,
                    'oldValue': old_value,
                    'newValue': new_value
                }
            )
        )

# Register with ORM
@event.listens_for(Workspace, 'after_update')
def on_workspace_update(mapper, connection, target):
    """SQLAlchemy event listener"""

    # Get changed fields
    state = inspect(target)
    changes = state.attrs

    for attr in changes:
        if attr.history.has_changes():
            # Fire timeline event
            asyncio.create_task(
                change_listener.on_field_change(
                    workspace_id=target.id,
                    field=attr.key,
                    old_value=attr.history.deleted[0] if attr.history.deleted else None,
                    new_value=attr.history.added[0] if attr.history.added else None,
                    actor_id=target.updated_by,
                    actor_name=target.updated_by_name
                )
            )
```

---

### 4.6 Intake Pipeline Integration

**Why Critical:** Trip origin story

**Event Types Captured:**
```typescript
interface IntakeEvent extends TripEvent {
  eventType: 'inquiry_received' |
              'extraction_completed' |
              'extraction_confidence_update' |
              'data_validated';

  content: {
    rawMessage: string;
    channel: 'whatsapp' | 'email' | 'web' | 'phone';
    extractedData: Record<string, any>;
    confidence: Record<string, number>;
    missingFields: string[];
  };
}
```

**Integration: Pipeline Events**

```python
class IntakePipeline:
    """Intake pipeline that publishes timeline events"""

    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher

    async def process_inquiry(
        self,
        raw_message: str,
        channel: str,
        source_metadata: dict
    ) -> ProcessedInquiry:
        """Process incoming inquiry"""

        # Publish inquiry received event
        await self.event_publisher.publish_event(
            TripEvent(
                eventType='inquiry_received',
                category=EventCategory.ORIGIN,
                timestamp=datetime.now(),
                actor={'type': 'customer', 'name': 'Unknown'},
                source={'channel': channel},
                content={
                    'rawMessage': raw_message,
                    'channel': channel
                }
            )
        )

        # Extract data
        extraction = await self.extractor.extract(raw_message)

        # Publish extraction completed event
        await self.event_publisher.publish_event(
            TripEvent(
                eventType='extraction_completed',
                category=EventCategory.ANALYSIS,
                timestamp=datetime.now(),
                actor={'type': 'ai', 'name': 'Extraction Engine'},
                content={
                    'rawMessage': raw_message,
                    'extractedData': extraction.data,
                    'confidence': extraction.confidence_scores,
                    'missingFields': extraction.missing_fields
                }
            )
        )

        return extraction
```

---

## Part 5: Integration Phasing

### Phase 1: Core Internal (Weeks 1-4)

**Goal:** Capture all internally-generated events

| Integration | Effort | Value | Priority |
|-------------|--------|-------|----------|
| Decision Engine | 2 days | High | P0 |
| Intake Pipeline | 2 days | High | P0 |
| Workspace Field Edits | 3 days | High | P0 |
| Output Generator | 1 day | Medium | P1 |

**Deliverable:** Timeline shows all internal decision and action history

---

### Phase 2: WhatsApp (Weeks 5-8)

**Goal:** Capture primary customer communication

| Task | Effort |
|------|--------|
| Webhook endpoint setup | 1 day |
| Message transformation | 2 days |
| Workspace linking logic | 2 days |
| Media download/storage | 3 days |
| Real-time WebSocket push | 2 days |
| Testing & edge cases | 3 days |

**Deliverable:** Timeline shows complete WhatsApp conversation history

---

### Phase 3: Email (Weeks 9-12)

**Goal:** Capture formal communications

| Task | Effort |
|------|--------|
| SMTP webhook setup | 1 day |
| IMAP IDLE monitoring | 3 days |
| Email parsing | 2 days |
| Threading logic | 2 days |
| Attachment handling | 2 days |
| Testing | 2 days |

**Deliverable:** Timeline shows all email communications

---

### Phase 4: Phone (Weeks 13-16)

**Goal:** Capture verbal conversations

| Task | Effort |
|------|--------|
| Twilio/Exotel integration | 2 days |
| Call event mapping | 2 days |
| Recording storage | 2 days |
| Transcription (optional) | 5 days |
| Testing | 2 days |

**Deliverable:** Timeline shows call log with recordings

---

### Phase 5: External Services (Weeks 17-20)

**Goal:** Capture supplier and payment events

| Integration | Effort |
|-------------|--------|
| Payment gateway | 2 days |
| Supplier APIs | 5 days |
| CRM sync | 3 days |

**Deliverable:** Timeline shows complete transaction history

---

## Part 6: Integration Security

### 6.1 Webhook Verification

**All incoming webhooks must be verified:**

```python
def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    provider: str
) -> bool:
    """Verify webhook signature"""

    if provider == 'whatsapp':
        # WhatsApp X-Hub-Signature
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f'sha256={expected}', signature)

    elif provider == 'twilio':
        # Twilio expects URL-encoded signature
        return twilio.request_validator.validate(
            url=request.url,
            payload=payload,
            signature=signature
        )

    elif provider == 'sendgrid':
        # Sendgrid signature verification
        # ... implementation

    return False
```

### 6.2 Rate Limiting

**Protect webhook endpoints from abuse:**

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/webhooks/whatsapp")
@limiter.limit("60/minute")  # Per IP
async def whatsapp_webhook(request: Request):
    # ... webhook handler
```

### 6.3 Data Sanitization

**Sanitize data before storage:**

```python
def sanitize_event_content(content: dict) -> dict:
    """Sanitize event content before storage"""

    # Remove sensitive fields
    sensitive_fields = ['password', 'cvv', 'pin', 'otp']

    for field in sensitive_fields:
        if field in content:
            content[field] = '***REDACTED***'

    # Sanitize HTML
    if 'html' in content:
        content['html'] = bleach.clean(
            content['html'],
            tags=[],
            strip=True
        )

    return content
```

---

## Part 7: Error Handling & Recovery

### 7.1 Retry Strategy

```python
class EventRetryPolicy:
    """Retry policy for failed event processing"""

    # Retry with exponential backoff
    max_retries = 5
    base_delay = 1  # seconds
    max_delay = 300  # 5 minutes

    def get_delay(self, attempt: int) -> int:
        """Calculate delay for retry attempt"""
        return min(
            self.base_delay * (2 ** attempt),
            self.max_delay
        )

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error is retryable"""
        if attempt >= self.max_retries:
            return False

        # Retry on transient errors
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            DatabaseError,
            APIError  # 5xx errors
        )

        return isinstance(error, retryable_errors)
```

### 7.2 Dead Letter Queue

```python
class DeadLetterQueue:
    """Store events that failed permanently"""

    async def enqueue_failed_event(
        self,
        event: TripEvent,
        error: Exception,
        attempt: int
    ):
        """Store failed event for manual inspection"""

        await dead_letter_db.insert({
            'event_id': event.id,
            'event_data': event.dict(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'failed_at': datetime.now(),
            'attempt': attempt,
            'status': 'pending_review'
        })

    async def retry_failed_event(self, event_id: str):
        """Retry processing failed event"""
        # ... implementation
```

### 7.3 Duplicate Detection

```python
async def is_duplicate_event(event: TripEvent) -> bool:
    """Check if event is duplicate"""

    # Check by event ID if provided
    if event.id:
        existing = await db.query(
            "SELECT 1 FROM trip_events WHERE id = $1",
            event.id
        )
        return bool(existing)

    # Check by natural key
    existing = await db.query("""
        SELECT 1 FROM trip_events
        WHERE trip_id = $1
          AND event_type = $2
          AND timestamp = $3
          AND content->>'messageId' = $4
    """, event.trip_id, event.event_type, event.timestamp,
        event.content.get('messageId'))

    return bool(existing)
```

---

## Part 8: Performance Considerations

### 8.1 Batch Insertion

**Never insert events one-by-one:**

```python
async def batch_insert_events(events: List[TripEvent]):
    """Batch insert events for efficiency"""

    # Group by 100
    for batch in chunks(events, 100):
        await db.execute_many(
            """INSERT INTO trip_events
               (id, trip_id, workspace_id, event_type, category,
                timestamp, actor, source, content, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            *[event.values() for event in batch]
        )
```

### 8.2 Async Processing

**All integration processing should be async:**

```python
# Don't block webhook response
@app.post("/api/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    # Quick validation
    event = validate_webhook(request)

    # Queue for processing (non-blocking)
    await event_queue.enqueue(event)

    # Immediate response
    return {"status": "accepted"}

# Background worker processes queue
async def event_processor_worker():
    while True:
        batch = await event_queue.dequeue_batch(100)
        await batch_insert_events(batch)
```

---

## Part 9: Monitoring & Observability

### 9.1 Integration Health Dashboard

**Metrics to track:**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Event ingestion rate | Events/second | < 1/sec for 5 min |
| Processing latency | Time to insert | > 5 seconds for 5% |
| Webhook success rate | Successful webhooks | < 95% |
| Queue depth | Pending events | > 10000 |
| Dead letter count | Failed events | > 100/hour |

### 9.2 Integration Logging

```python
import structlog

logger = structlog.get_logger()

await logger.info(
    "event_ingested",
    source="whatsapp",
    event_type="message_received",
    trip_id=event.trip_id,
    workspace_id=event.workspace_id,
    event_id=event.id
)
```

---

## Summary

**Timeline integration is a phased, systematic approach:**

1. **Phase 1 (Internal):** 2 weeks, captures 60% of value
2. **Phase 2 (WhatsApp):** 4 weeks, captures 30% more value
3. **Phase 3-5 (External):** 8 weeks, completes the picture

**Key principles:**
- Async everywhere (never block)
- Batch operations (efficiency)
- Idempotent (retry-safe)
- Graceful degradation (works even if source is down)

**Success metrics:**
- 95%+ event capture rate
- <5 second processing latency
- 99.9% webhook uptime

---

**Status:** Integration architecture complete. Ready for implementation.

**Next:** AI/ML deep dive (TIMELINE_05)
