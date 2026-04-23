# Timeline Deep Dive 01: Technical Architecture

> Complete technical exploration: data models, scaling, performance, security

---

## Part 1: Data Model Design

### Core Tables

#### 1. trip_events (Main Events Table)
```sql
CREATE TABLE trip_events (
  -- Identity
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  workspace_id UUID NOT NULL REFERENCES workspaces(id),

  -- When
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',

  -- What
  event_type VARCHAR(100) NOT NULL,
  event_category VARCHAR(50) NOT NULL,
  title VARCHAR(500) NOT NULL,
  summary TEXT,

  -- Who
  actor_id UUID,
  actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('customer', 'agent', 'owner', 'ai', 'system')),
  actor_name VARCHAR(255) NOT NULL,

  -- Source (for conversations)
  source_channel VARCHAR(20),
  source_message_id VARCHAR(255),
  source_thread_id VARCHAR(255),

  -- Content (JSONB for flexibility)
  content JSONB NOT NULL DEFAULT '{}',

  -- Relationships
  parent_event_id UUID REFERENCES trip_events(id),
  related_event_ids UUID[] DEFAULT '{}',
  triggered_event_ids UUID[] DEFAULT '{}',

  -- Metadata
  is_internal_only BOOLEAN DEFAULT false,
  is_highlighted BOOLEAN DEFAULT false,
  tags VARCHAR(50)[] DEFAULT '{}',

  -- Audit
  ip_address INET,
  user_agent TEXT,

  -- Attachments
  attachment_count INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE,

  -- Indexes
  CONSTRAINT trip_events_trip_id_timestamp_idx
    CHECK (timestamp <= (NOW() + INTERVAL '1 day'))  -- Prevent future events
);

-- Critical Indexes
CREATE INDEX idx_trip_events_trip_timestamp
  ON trip_events(trip_id, timestamp DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_trip_events_workspace_timestamp
  ON trip_events(workspace_id, timestamp DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_trip_events_type_timestamp
  ON trip_events(event_type, timestamp DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_trip_events_actor_timestamp
  ON trip_events(actor_id, timestamp DESC)
  WHERE deleted_at IS NULL AND actor_id IS NOT NULL;

CREATE INDEX idx_trip_events_tags
  ON trip_events USING GIN(tags)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_trip_events_content_gin
  ON trip_events USING GIN(content)
  WHERE deleted_at IS NULL;

-- Partial index for internal-only filtering
CREATE INDEX idx_trip_events_internal_only
  ON trip_events(trip_id, timestamp DESC)
  WHERE is_internal_only = true AND deleted_at IS NULL;
```

#### 2. event_attachments (Supporting Table)
```sql
CREATE TABLE event_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL REFERENCES trip_events(id) ON DELETE CASCADE,

  -- File info
  filename VARCHAR(255) NOT NULL,
  file_type VARCHAR(100) NOT NULL,
  file_size_bytes INTEGER NOT NULL,
  storage_path TEXT NOT NULL,

  -- Metadata
  mime_type VARCHAR(100),
  checksum VARCHAR(64),

  -- Access
  is_public BOOLEAN DEFAULT false,
  access_url TEXT,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,

  CONSTRAINT event_attachments_file_size_check
    CHECK (file_size_bytes > 0 AND file_size_bytes < 100000000)  -- Max 100MB
);

CREATE INDEX idx_event_attachments_event_id
  ON event_attachments(event_id);
```

#### 3. event_groups (For Grouping Related Events)
```sql
CREATE TABLE event_groups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  workspace_id UUID NOT NULL REFERENCES workspaces(id),

  group_type VARCHAR(50) NOT NULL,  -- 'conversation', 'analysis_cycle', 'escalation'
  group_title VARCHAR(255) NOT NULL,

  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE,

  event_ids UUID[] NOT NULL DEFAULT '{}',
  summary TEXT,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  CONSTRAINT event_groups_end_time_check
    CHECK (end_time IS NULL OR end_time >= start_time)
);

CREATE INDEX idx_event_groups_trip_time
  ON event_groups(trip_id, start_time DESC);
```

---

## Part 2: Event Type Taxonomy (Complete)

### Event Types by Category

#### ORIGIN Category
```typescript
// Inquiry received
{
  event_type: 'inquiry_received',
  event_category: 'origin',
  content: {
    raw_message: string,
    channel: 'whatsapp' | 'email' | 'phone' | 'web' | 'referral',
    extracted_data: {
      destination?: string,
      trip_type?: string,
      budget?: number,
      currency?: string,
      party_size?: number,
      date_window?: string,
      preferences?: string[],
      urgency?: 'low' | 'medium' | 'high' | 'urgent',
    },
    confidence_scores: Record<string, number>,
    customer_info: {
      name?: string,
      phone?: string,
      email?: string,
      existing_customer?: boolean,
      previous_trips?: string[],
    },
    metadata: {
      source_campaign?: string,
      referrer?: string,
      utm_params?: Record<string, string>,
    }
  }
}
```

#### ANALYSIS Category
```typescript
// AI extraction
{
  event_type: 'analysis_extraction',
  event_category: 'analysis',
  content: {
    analysis_id: string,
    extraction_results: Record<string, {
      value: unknown,
      confidence: number,
      authority_level: string,
      evidence_refs: Array<{id: string, excerpt: string}>
    }>,
    ambiguities: Array<{
      field: string,
      ambiguity_type: string,
      raw_value: string,
      resolution?: string
    }>,
    unknowns: Array<{
      field: string,
      reason: string,
    }>,
    contradictions: Array<{
      field: string,
      values: unknown[],
      sources: string[],
    }>,
    model_version: string,
    processing_time_ms: number,
  }
}

// Scenario evaluation
{
  event_type: 'analysis_scenarios',
  event_category: 'analysis',
  content: {
    analysis_id: string,
    scenarios: Array<{
      id: string,
      name: string,
      description: string,
      budget_estimate: {low: number, high: number, currency: string},
      budget_fit: 'excellent' | 'good' | 'tight' | 'over',
      pros: string[],
      cons: string[],
      risk_flags: string[],
      confidence: number,
      selected: boolean,
      rejection_reason?: string,
    }>,
    comparison: {
      criteria: string[],
      scenario_scores: Record<string, number>,
      rationale: string,
    },
    model_version: string,
  }
}

// Decision analysis
{
  event_type: 'analysis_decision',
  event_category: 'analysis',
  content: {
    decision_state: string,
    confidence: {
      overall: number,
      data_quality: number,
      judgment_confidence: number,
      commercial_confidence: number,
    },
    rationale: {
      feasibility: string,
      hard_blockers: string[],
      soft_blockers: string[],
      contradictions: string[],
      risk_flags: string[],
    },
    followup_questions: Array<{
      field_name: string,
      question: string,
      priority: 'high' | 'medium' | 'low',
      suggested_values: unknown[],
    }>,
    branch_options: string[],
    budget_breakdown?: {
      verdict: string,
      currency: string,
      budget_stated: number,
      total_estimated_low: number,
      total_estimated_high: number,
      gap: number | null,
      buckets: Array<{
        bucket: string,
        low: number,
        high: number,
        covered: boolean,
      }>,
    },
    model_version: string,
  }
}
```

#### DECISION Category
```typescript
// Status changed
{
  event_type: 'status_changed',
  event_category: 'decision',
  content: {
    from_state: string,
    to_state: string,
    reason: string,
    confidence: number,
    triggers: string[],
    auto_applied: boolean,
  }
}

// Owner approval
{
  event_type: 'owner_approval',
  event_category: 'decision',
  content: {
    decision: 'approved' | 'rejected' | 'escalated' | 'returned',
    reason: string,
    notes?: string,
    conditions?: string[],
    overrides: string[],
    budget_authority?: {
      max_amount: number,
      currency: string,
    },
  }
}

// Owner rejection with escalation
{
  event_type: 'owner_escalation',
  event_category: 'decision',
  content: {
    escalation_reason: string,
    escalated_to: string,
    urgency: 'low' | 'medium' | 'high' | 'critical',
    deadline?: string,
    required_actions: string[],
  }
}
```

#### CONVERSATION Category
```typescript
// Message sent/received
{
  event_type: 'conversation_message',
  event_category: 'conversation',
  content: {
    direction: 'inbound' | 'outbound',
    message: string,
    channel: 'whatsapp' | 'email' | 'phone' | 'web',
    message_id: string,
    thread_id?: string,
    in_reply_to?: string,
    attachments: Array<{
      filename: string,
      type: string,
      url: string,
    }>,
    metadata: {
      delivered_at?: string,
      read_at?: string,
      failed_reason?: string,
    }
  }
}

// Follow-up sent
{
  event_type: 'followup_sent',
  event_category: 'conversation',
  content: {
    followup_type: 'automated' | 'manual',
    questions: Array<{
      field: string,
      question: string,
      priority: string,
    }>,
    channel: string,
    scheduled_for?: string,
    sent_at: string,
  }
}
```

#### ACTION Category
```typescript
// Field updated
{
  event_type: 'field_updated',
  event_category: 'action',
  content: {
    field: string,
    previous_value: unknown,
    new_value: unknown,
    reason?: string,
    update_source: 'manual' | 'api' | 'import' | 'ai_correction',
  }
}

// Trip created
{
  event_type: 'trip_created',
  event_category: 'action',
  content: {
    creation_source: 'manual' | 'whatsapp' | 'email' | 'api' | 'import',
    template_used?: string,
    initial_data: Record<string, unknown>,
  }
}

// Trip assigned
{
  event_type: 'trip_assigned',
  event_category: 'action',
  content: {
    from_agent_id?: string,
    to_agent_id: string,
    assignment_reason: string,
    assignment_type: 'manual' | 'auto' | 'escalation' | 'reassignment',
    notify_assignee: boolean,
  }
}

// Tags updated
{
  event_type: 'tags_updated',
  event_category: 'action',
  content: {
    tags_added: string[],
    tags_removed: string[],
    reason?: string,
  }
}
```

#### REVIEW Category
```typescript
// Review submitted
{
  event_type: 'review_submitted',
  event_category: 'review',
  content: {
    review_type: 'owner' | 'peer' | 'qa',
    reviewer_id: string,
    reviewer_name: string,
    review_decision: 'approved' | 'changes_requested' | 'rejected',
    findings: Array<{
      category: string,
      severity: 'info' | 'warning' | 'error',
      description: string,
      suggestion?: string,
    }>,
    notes?: string,
  }
}

// Review resolved
{
  event_type: 'review_resolved',
  event_category: 'review',
  content: {
    review_id: string,
    resolution: string,
    resolver_id: string,
    changes_made: string[],
  }
}
```

#### SYSTEM Category
```typescript
// SLA alert
{
  event_type: 'sla_alert',
  event_category: 'system',
  content: {
    sla_type: string,
    current_value: number,
    threshold: number,
    severity: 'warning' | 'critical',
    triggered_at: string,
    notification_sent_to: string[],
  }
}

// Auto-assignment
{
  event_type: 'auto_assignment',
  event_category: 'system',
  content: {
    assignment_logic: string,
    agent_id: string,
    reason: string,
    workload_snapshot: {
      agent: string,
      current_trips: number,
      capacity: number,
    },
  }
}

// System error
{
  event_type: 'system_error',
  event_category: 'system',
  content: {
    error_type: string,
    error_message: string,
    error_code?: string,
    stack_trace?: string,
    context: Record<string, unknown>,
    resolved: boolean,
    resolution?: string,
  }
}
```

---

## Part 3: Scaling Strategy

### Volume Projections

```
Assumptions:
- 1,000 trips per month (per agency)
- 50 events per trip (average)
- Event retention: 7 years

Calculations:
- Events per month: 50,000
- Events per year: 600,000
- Total events (7 years): 4.2 million
```

### Storage Strategy

#### Hot Data (0-90 days) - Fast Access
```
Storage: PostgreSQL with SSD
Indexing: Full
Access: Sub-second queries
Cost: High
Retention: 90 days
Size: ~150,000 events
```

#### Warm Data (90 days - 1 year) - Standard Access
```
Storage: PostgreSQL with standard disks
Indexing: Partial (trip_id, timestamp)
Access: < 1 second queries
Cost: Medium
Retention: 275 days
Size: ~450,000 events
```

#### Cold Data (1-7 years) - Archive
```
Storage: S3 / Glacier / Compressed SQL
Indexing: Minimal (trip_id only)
Access: < 5 seconds queries
Cost: Low
Retention: 6 years
Size: ~3.6 million events
```

### Partitioning Strategy

```sql
-- Partition by year (for 7-year retention)
CREATE TABLE trip_events (
  -- ... same schema ...
) PARTITION BY RANGE (timestamp);

-- Create partitions
CREATE TABLE trip_events_2026 PARTITION OF trip_events
  FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE trip_events_2027 PARTITION OF trip_events
  FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');

-- ... and so on

-- Archive old partitions
ALTER TABLE trip_events_2020 DETACH PARTITION trip_events_2020;
-- Move to cheaper storage, compress, etc.
```

### Caching Strategy

```
Cache Layer: Redis

What to cache:
- Recent timelines (last 50 events per trip)
- Aggregated summaries (event counts by type)
- Hot trips (frequently accessed)

TTL:
- Timeline cache: 5 minutes
- Summary cache: 15 minutes
- Hot trips: 1 hour

Cache keys:
- timeline:{trip_id}:sorted
- timeline:{trip_id}:summary
- timeline:{trip_id}:filtered:{filter_hash}
```

---

## Part 4: Query Patterns & Optimization

### Common Queries

#### 1. Get Timeline for a Trip (Paginated)
```sql
-- Optimized query with pagination
SELECT
  id,
  timestamp,
  timezone,
  event_type,
  event_category,
  title,
  summary,
  actor_type,
  actor_name,
  content,
  is_highlighted,
  tags
FROM trip_events
WHERE trip_id = $1
  AND deleted_at IS NULL
  AND ($2 IS NULL OR event_type = $2)  -- Optional filter by type
ORDER BY timestamp DESC
LIMIT $3 OFFSET $4;

-- Index used: idx_trip_events_trip_timestamp
```

#### 2. Get Related Events
```sql
-- Get events that are related to a given event
WITH RECURSIVE related_events AS (
  -- Start with the given event
  SELECT id, trip_id, timestamp, content, 1 as depth
  FROM trip_events
  WHERE id = $1

  UNION ALL

  -- Follow related_event_ids
  SELECT te.id, te.trip_id, te.timestamp, te.content, re.depth + 1
  FROM trip_events te
  JOIN related_events re ON te.id = ANY(re.related_event_ids)
  WHERE te.deleted_at IS NULL
    AND re.depth < 5  -- Max depth
)
SELECT * FROM related_events
ORDER BY timestamp ASC;

-- Index used: idx_trip_events_content_gin (for array operations)
```

#### 3. Timeline Summary (Aggregated)
```sql
-- Get summary counts by event type
SELECT
  event_type,
  event_category,
  COUNT(*) as count,
  MAX(timestamp) as last_occurrence,
  MIN(timestamp) as first_occurrence
FROM trip_events
WHERE trip_id = $1
  AND deleted_at IS NULL
GROUP BY event_type, event_category
ORDER BY last_occurrence DESC;

-- Index used: idx_trip_events_trip_timestamp (covers the GROUP BY)
```

#### 4. Search Across Timelines
```sql
-- Full-text search across event content
SELECT
  te.id,
  te.trip_id,
  te.timestamp,
  te.event_type,
  te.title,
  te.summary,
  ts_rank(te.content_tsv, query) as rank
FROM trip_events te,
     to_tsquery('english', $1) query,
     to_tsvector('english', 
       COALESCE(te.title, '') || ' ' ||
       COALESCE(te.summary, '') || ' ' ||
       COALESCE(te.content->>'message', '') || ' ' ||
       COALESCE(te.content->>'reason', '')
     ) content_tsv
WHERE te.content_tsv @@ query
  AND te.deleted_at IS NULL
  AND te.workspace_id = $2
  AND ($3 IS NULL OR te.event_type = $3)
ORDER BY rank DESC, te.timestamp DESC
LIMIT 50;

-- Requires: GIN index on content_tsv (full-text search)
```

#### 5. Time-in-Stage Analysis
```sql
-- Calculate time spent in each stage
WITH stage_transitions AS (
  SELECT
    trip_id,
    content->>'from_state' as from_stage,
    content->>'to_state' as to_stage,
    timestamp as transition_time,
    LAG(timestamp) OVER (PARTITION BY trip_id ORDER BY timestamp) as prev_timestamp
  FROM trip_events
  WHERE event_type = 'status_changed'
    AND deleted_at IS NULL
),
stage_durations AS (
  SELECT
    trip_id,
    to_stage as stage,
    transition_time - prev_timestamp as duration
  FROM stage_transitions
  WHERE prev_timestamp IS NOT NULL
)
SELECT
  stage,
  AVG(duration) as avg_duration,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY duration) as median_duration,
  percentile_cont(0.9) WITHIN GROUP (ORDER BY duration) as p90_duration,
  COUNT(*) as count
FROM stage_durations
GROUP BY stage
ORDER BY avg_duration DESC;
```

---

## Part 5: Real-Time Streaming

### WebSocket Architecture

```
Client → WebSocket Server → Message Queue → Workers → DB
  ↑                                                              ↓
  └───────────────────── Push Updates ←──────────────────────────┘
```

#### Event Streaming Protocol

```typescript
// Client subscribes to timeline updates
{
  action: 'subscribe',
  resource: 'timeline',
  trip_id: 'trip-123',
  filters: {
    event_types: ['conversation_message', 'status_changed'],
    since: '2026-04-23T00:00:00Z'
  }
}

// Server pushes new events
{
  type: 'timeline_event',
  data: {
    id: 'evt-456',
    trip_id: 'trip-123',
    timestamp: '2026-04-23T10:30:00Z',
    event_type: 'conversation_message',
    // ... full event data
  }
}

// Heartbeat
{
  type: 'ping',
  timestamp: '2026-04-23T10:35:00Z'
}
```

### Event Publishing

```python
# When an event is created
async def publish_event(event: TripEvent):
    # 1. Save to database
    await db.save_event(event)

    # 2. Publish to message queue
    await message_queue.publish(
        exchange='timeline',
        routing_key=f'timeline.{event.workspace_id}.{event.trip_id}',
        payload=event.to_json()
    )

    # 3. Invalidate cache
    await cache.delete(f'timeline:{event.trip_id}')

# WebSocket server subscribes to message queue
async def handle_websocket(websocket, trip_id):
    await websocket.subscribe(f'timeline.{workspace_id}.{trip_id}')

    async for message in websocket:
        if message.type == 'timeline_event':
            await websocket.send(message.payload)
```

---

## Part 6: Performance Benchmarks

### Target SLAs

| Metric | Target | How |
|--------|--------|-----|
| Timeline load (50 events) | < 200ms | Indexing, caching |
| Timeline load (500 events) | < 500ms | Pagination, lazy loading |
| Timeline search | < 1s | Full-text search, caching |
| Event creation | < 100ms | Async processing |
| Real-time push | < 500ms latency | WebSocket, message queue |

### Optimization Techniques

1. **Denormalized Summary Table**
```sql
CREATE TABLE trip_timeline_summary (
  trip_id UUID PRIMARY KEY,
  event_count INTEGER DEFAULT 0,
  last_event_at TIMESTAMP WITH TIME ZONE,
  last_event_type VARCHAR(100),
  event_counts_by_type JSONB DEFAULT '{}',
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger to update on event insert
CREATE OR REPLACE FUNCTION update_timeline_summary()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO trip_timeline_summary (trip_id, event_count, last_event_at, last_event_type)
  VALUES (NEW.trip_id, 1, NEW.timestamp, NEW.event_type)
  ON CONFLICT (trip_id) DO UPDATE SET
    event_count = trip_timeline_summary.event_count + 1,
    last_event_at = NEW.timestamp,
    last_event_type = NEW.event_type,
    updated_at = NOW();
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

2. **Materialized Views for Analytics**
```sql
CREATE MATERIALIZED VIEW timeline_metrics_by_day AS
SELECT
  DATE_TRUNC('day', timestamp) as event_date,
  event_type,
  COUNT(*) as event_count
FROM trip_events
WHERE deleted_at IS NULL
GROUP BY DATE_TRUNC('day', timestamp), event_type;

CREATE INDEX ON timeline_metrics_by_day(event_date, event_type);

-- Refresh strategy: cron job every hour
```

3. **Connection Pooling**
```python
# PgBouncer configuration
pool_mode = transaction
server_lifetime = 3600
server_idle_timeout = 600
max_client_conn = 10000
default_pool_size = 50
```

---

## Part 7: Security & Privacy

### Data Encryption

```
At Rest:
- Database encryption (AES-256)
- File storage encryption (S3 SSE-KMS)

In Transit:
- TLS 1.3 for all connections
- WebSocket over WSS

Application:
- Sensitive fields encrypted at application level
- Password hashing with bcrypt/scrypt
```

### Access Control Matrix

| Role | Can View | Can Create | Can Edit | Can Delete |
|------|----------|------------|----------|------------|
| **Owner** | All events | All types | All events | Own events |
| **Manager** | All events | All types | All events | No |
| **Agent** | Assigned trips | Message, field update | Own messages only | No |
| **External** | Assigned trips only | None | No | No |
| **Customer** | Customer-safe only | None | No | No |

### PII Redaction

```typescript
// Redact sensitive info for customer view
function redactForCustomer(event: TripEvent): TripEvent {
  const REDACTED = '[REDACTED]';

  return {
    ...event,
    content: {
      ...event.content,
      internal_notes: REDACTED,
      ai_confidence_below_threshold: REDACTED,
      risk_flags: event.content.risk_flags?.length > 0
        ? `[${event.content.risk_flags.length} items reviewed]`
        : [],
    },
    actor_name: event.actor_type === 'system'
      ? 'System'
      : event.actor_name,
    // Remove internal-only events entirely
    is_internal_only: event.is_internal_only
      ? true
      : event.is_internal_only,
  };
}
```

### Audit Logging

```sql
-- All timeline access is logged
CREATE TABLE timeline_access_log (
  id UUID PRIMARY KEY,
  trip_id UUID NOT NULL,
  user_id UUID NOT NULL,
  action VARCHAR(50) NOT NULL,  -- 'view', 'export', 'search'
  accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ip_address INET,
  user_agent TEXT,
  result VARCHAR(20),  -- 'success', 'partial', 'denied'
);
```

---

## Part 8: Monitoring & Observability

### Key Metrics

```
Timeline Performance:
- Timeline load time (p50, p95, p99)
- Event creation latency
- WebSocket push latency
- Cache hit rate

Data Quality:
- Events per trip (avg, min, max)
- Orphaned events (no trip_id)
- Event validation failures
- Missing parent_event_id references

Business:
- Timeline views per trip
- Most viewed event types
- Timeline exports per day
- Search queries per day
```

### Alerting Rules

```yaml
alerts:
  - name: TimelineLoadSlow
    condition: timeline_load_p95 > 1s
    severity: warning

  - name: EventCreationFailed
    condition: event_creation_error_rate > 0.01
    severity: critical

  - name: WebSocketBacklog
    condition: message_queue_backlog > 1000
    severity: warning

  - name: OrphanedEvents
    condition: orphaned_events_count > 100
    severity: warning
```

---

## Part 9: Disaster Recovery

### Backup Strategy

```
Real-time backup:
- WAL archiving to S3 every 5 minutes
- Streaming replication to standby

Daily backups:
- Full database backup to S3
- Encrypted with KMS
- Retention: 30 days

Point-in-time recovery:
- RTO: 1 hour
- RPO: 5 minutes
```

### Event Replay

```
If primary database fails:
1. Promote standby to primary
2. Replay WAL logs from last checkpoint
3. Verify data integrity
4. Resume operations

Maximum data loss: 5 minutes of events
```

---

**Status:** Technical deep dive complete
