# Timeline: API Specification (Complete)

> All endpoints, contracts, and integration points

---

## Part 1: API Overview

### Base URL

```
Production:  https://api.agency.app/timeline/v1
Staging:     https://api-staging.agency.app/timeline/v1
Development: http://localhost:8000/timeline/v1
```

### Authentication

```http
Authorization: Bearer {jwt_token}

# JWT claims:
{
  "sub": "user_id",
  "agency_id": "agency_id",
  "role": "agent|owner|admin",
  "exp": 1234567890
}
```

### Response Format

```typescript
interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    page?: number;
    pageSize?: number;
    totalCount?: number;
    hasMore?: boolean;
  };
}
```

---

## Part 2: Event Endpoints

### 2.1 Create Event

```http
POST /timeline/v1/events
```

**Request:**

```typescript
interface CreateEventRequest {
  trip_id: string;
  workspace_id: string;
  event_type: EventType;
  category: EventCategory;
  timestamp: string;  // ISO 8601
  actor: Actor;
  source?: EventSource;
  content: Record<string, any>;
  metadata?: EventMetadata;
  parent_event_id?: string;
  related_event_ids?: string[];
}
```

**Response:**

```typescript
interface CreateEventResponse {
  event: TripEvent;
}
```

**Example:**

```bash
curl -X POST https://api.agency.app/timeline/v1/events \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": "trip_abc123",
    "workspace_id": "ws_def456",
    "event_type": "whatsapp_message_received",
    "category": "conversation",
    "timestamp": "2026-04-23T10:30:00Z",
    "actor": {
      "id": "cust_789",
      "name": "John Doe",
      "type": "customer"
    },
    "source": {
      "channel": "whatsapp",
      "messageId": "wa_msg_xyz"
    },
    "content": {
      "message": "Can you also include Phi Phi islands?",
      "direction": "inbound"
    }
  }'
```

### 2.2 Get Event

```http
GET /timeline/v1/events/{event_id}
```

**Response:**

```typescript
interface GetEventResponse {
  event: TripEvent;
}
```

### 2.3 Update Event

```http
PATCH /timeline/v1/events/{event_id}
```

**Request:**

```typescript
interface UpdateEventRequest {
  content?: Record<string, any>;
  metadata?: EventMetadata;
}
```

**Note:** Only content and metadata can be updated. Immutable fields: id, trip_id, event_type, timestamp, actor.

### 2.4 Delete Event

```http
DELETE /timeline/v1/events/{event_id}
```

**Note:** Soft delete. Event marked as deleted but retained for audit.

---

## Part 3: Timeline Query Endpoints

### 3.1 Get Trip Timeline

```http
GET /timeline/v1/trips/{trip_id}/events
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_type` | string[] | all | Filter by event types |
| `category` | string[] | all | Filter by categories |
| `start_date` | string | none | ISO 8601 start |
| `end_date` | string | none | ISO 8601 end |
| `actor_type` | string[] | all | Filter by actor types |
| `include_internal` | boolean | false | Include internal events |
| `page` | number | 1 | Page number |
| `page_size` | number | 50 | Items per page (max 200) |

**Response:**

```typescript
interface GetTripTimelineResponse {
  events: TripEvent[];
  meta: {
    page: number;
    pageSize: number;
    totalCount: number;
    hasMore: boolean;
  };
}
```

**Example:**

```bash
curl "https://api.agency.app/timeline/v1/trips/trip_abc123/events?category=conversation&include_internal=false&page=1&page_size=20" \
  -H "Authorization: Bearer {token}"
```

### 3.2 Search Events

```http
GET /timeline/v1/trips/{trip_id}/events/search
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `event_type` | string[] | No | Filter by types |
| `category` | string[] | No | Filter by categories |
| `fuzzy` | boolean | false | Fuzzy matching |

**Response:**

```typescript
interface SearchEventsResponse {
  events: TripEvent[];
  highlights?: {
    event_id: string;
    field: string;
    text: string;
  }[];
  meta: {
    totalCount: number;
    searchTimeMs: number;
  };
}
```

### 3.3 Get Timeline Statistics

```http
GET /timeline/v1/trips/{trip_id}/statistics
```

**Response:**

```typescript
interface TimelineStatisticsResponse {
  statistics: {
    totalEvents: number;
    eventsByType: Record<string, number>;
    eventsByCategory: Record<string, number>;
    eventsByActor: Record<string, number>;
    firstEvent: string;
    lastEvent: string;
    duration: string;
    dailyActivity: {
      date: string;
      count: number;
    }[];
  };
}
```

---

## Part 4: Stream Endpoints

### 4.1 Subscribe to Timeline Updates

```http
GET /timeline/v1/trips/{trip_id}/stream
```

**Protocol:** WebSocket

**Connection:**

```javascript
const ws = new WebSocket(
  'wss://api.agency.app/timeline/v1/trips/trip_abc123/stream?token={jwt_token}'
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'event_created':
      console.log('New event:', message.event);
      break;
    case 'event_updated':
      console.log('Updated event:', message.event);
      break;
    case 'heartbeat':
      // Keep-alive
      break;
  }
};
```

**Message Types:**

```typescript
type StreamMessage =
  | { type: 'event_created'; event: TripEvent }
  | { type: 'event_updated'; event: TripEvent }
  | { type: 'heartbeat'; timestamp: string }
  | { type: 'error'; error: string };
```

### 4.2 Subscribe to Multiple Trips

```http
POST /timeline/v1/stream/subscribe
```

**Request (WebSocket):**

```javascript
const ws = new WebSocket(
  'wss://api.agency.app/timeline/v1/stream?token={jwt_token}'
);

// Subscribe to trips
ws.send(JSON.stringify({
  action: 'subscribe',
  trip_ids: ['trip_abc123', 'trip_def456', 'trip_ghi789']
}));

// Unsubscribe
ws.send(JSON.stringify({
  action: 'unsubscribe',
  trip_ids: ['trip_abc123']
}));
```

---

## Part 5: Export Endpoints

### 5.1 Export Timeline as PDF

```http
POST /timeline/v1/trips/{trip_id}/export/pdf
```

**Request:**

```typescript
interface ExportPDFRequest {
  include_internal?: boolean;
  include_summary?: boolean;
  date_range?: {
    start: string;
    end: string;
  };
  filters?: {
    event_types?: string[];
    categories?: string[];
  };
  template?: 'default' | 'legal' | 'customer';
}
```

**Response:**

```typescript
interface ExportPDFResponse {
  export_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  download_url?: string;
  expires_at?: string;
}
```

### 5.2 Get Export Status

```http
GET /timeline/v1/exports/{export_id}
```

**Response:**

```typescript
interface GetExportStatusResponse {
  export_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;  // 0-100
  download_url?: string;
  expires_at?: string;
  error?: string;
}
```

### 5.3 Export Timeline as JSON

```http
POST /timeline/v1/trips/{trip_id}/export/json
```

**Response:**

```typescript
interface ExportJSONResponse {
  trip_id: string;
  events: TripEvent[];
  exported_at: string;
  event_count: number;
}
```

---

## Part 6: Analytics Endpoints

### 6.1 Get Trip Summary

```http
GET /timeline/v1/trips/{trip_id}/summary
```

**Response:**

```typescript
interface TripSummaryResponse {
  summary: {
    narrative: string;
    keyMoments: {
      event_id: string;
      timestamp: string;
      description: string;
    }[];
    status: {
      current_state: string;
      progress: number;
      blockers: string[];
    };
    customerProfile: {
      communicationStyle: string;
      sentimentTrend: 'improving' | 'stable' | 'declining';
      engagementLevel: 'high' | 'medium' | 'low';
    };
  };
}
```

### 6.2 Get Similar Trips

```http
GET /timeline/v1/trips/{trip_id}/similar
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 5 | Max results |
| `min_similarity` | number | 0.5 | Minimum similarity score |

**Response:**

```typescript
interface SimilarTripsResponse {
  similar_trips: {
    trip_id: string;
    similarity_score: number;
    reasons: string[];
    summary: string;
  }[];
}
```

### 6.3 Get Patterns

```http
GET /timeline/v1/patterns
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `destination` | string | No | Filter by destination |
| `trip_type` | string | No | Filter by trip type |
| `min_occurrences` | number | No | Minimum pattern frequency |

**Response:**

```typescript
interface GetPatternsResponse {
  patterns: {
    pattern_id: string;
    name: string;
    description: string;
    matching_trips: number;
    confidence: number;
    common_attributes: Record<string, any>;
  }[];
}
```

---

## Part 7: Webhook Endpoints

### 7.1 Register Webhook

```http
POST /timeline/v1/webhooks
```

**Request:**

```typescript
interface RegisterWebhookRequest {
  url: string;
  events: string[];  // Event types to subscribe to
  secret?: string;   // HMAC secret
  filters?: {
    trip_ids?: string[];
    agencies?: string[];
  };
}
```

**Response:**

```typescript
interface RegisterWebhookResponse {
  webhook: {
    id: string;
    url: string;
    events: string[];
    secret: string;  // Only returned on creation
    created_at: string;
  };
}
```

### 7.2 List Webhooks

```http
GET /timeline/v1/webhooks
```

**Response:**

```typescript
interface ListWebhooksResponse {
  webhooks: {
    id: string;
    url: string;
    events: string[];
    active: boolean;
    created_at: string;
    last_triggered_at?: string;
  }[];
}
```

### 7.3 Delete Webhook

```http
DELETE /timeline/v1/webhooks/{webhook_id}
```

### 7.4 Webhook Payload

When an event occurs, your webhook URL receives:

```typescript
interface WebhookPayload {
  webhook_id: string;
  event_id: string;
  event_type: string;
  trip_id: string;
  timestamp: string;
  data: {
    event: TripEvent;
  };
  signature: string;  // HMAC SHA256
}
```

**Verify Signature:**

```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(JSON.stringify(payload));
  const expected = hmac.digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

---

## Part 8: Customer-Facing Endpoints

### 8.1 Get Customer Timeline

```http
GET /timeline/v1/customer/{token}/events
```

**Note:** Uses customer token, not JWT. Automatically filters internal events.

**Response:**

```typescript
interface CustomerTimelineResponse {
  events: CustomerTimelineEvent[];
  trip: {
    id: string;
    destination: string;
    dates: string;
    status: string;
  };
}
```

### 8.2 Get Customer Actions

```http
GET /timeline/v1/customer/{token}/actions
```

**Response:**

```typescript
interface CustomerActionsResponse {
  pending_actions: {
    id: string;
    title: string;
    description: string;
    priority: 'low' | 'medium' | 'high';
    deadline: string;
    action: any;
  }[];
}
```

---

## Part 9: Batch Operations

### 9.1 Batch Create Events

```http
POST /timeline/v1/events/batch
```

**Request:**

```typescript
interface BatchCreateEventsRequest {
  events: CreateEventRequest[];
}
```

**Response:**

```typescript
interface BatchCreateEventsResponse {
  created: string[];  // Event IDs
  failed: {
    index: number;
    error: string;
  }[];
}
```

### 9.2 Batch Update Events

```http
PATCH /timeline/v1/events/batch
```

**Request:**

```typescript
interface BatchUpdateEventsRequest {
  updates: {
    event_id: string;
    content?: Record<string, any>;
    metadata?: EventMetadata;
  }[];
}
```

---

## Part 10: Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `DUPLICATE_EVENT` | 409 | Event already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

**Error Response Format:**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "event_type",
      "issue": "Invalid event type"
    }
  }
}
```

---

## Part 11: Rate Limiting

| Tier | Limit | Window |
|------|-------|--------|
| **Free** | 100 requests/hour | Hour |
| **Pro** | 1,000 requests/hour | Hour |
| **Enterprise** | 10,000 requests/hour | Hour |

**Rate Limit Headers:**

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1713840000
```

---

## Part 12: SDK Examples

### JavaScript/TypeScript

```typescript
import { TimelineClient } from '@agency/timeline-sdk';

const client = new TimelineClient({
  apiKey: process.env.AGENCY_API_KEY,
  baseURL: 'https://api.agency.app/timeline/v1'
});

// Get timeline
const timeline = await client.trips.getEvents('trip_abc123', {
  category: ['conversation'],
  includeInternal: false
});

// Create event
const event = await client.events.create({
  trip_id: 'trip_abc123',
  event_type: 'whatsapp_message_received',
  category: 'conversation',
  // ... rest of event data
});

// Subscribe to updates
const stream = await client.trips.stream('trip_abc123');
stream.on('event_created', (event) => {
  console.log('New event:', event);
});
```

### Python

```python
from agency_timeline import TimelineClient

client = TimelineClient(
    api_key="your-api-key",
    base_url="https://api.agency.app/timeline/v1"
)

# Get timeline
timeline = client.trips.get_events(
    trip_id="trip_abc123",
    category=["conversation"],
    include_internal=False
)

# Create event
event = client.events.create(
    trip_id="trip_abc123",
    event_type="whatsapp_message_received",
    category="conversation",
    # ... rest of event data
)

# Subscribe to updates
def on_event(event):
    print(f"New event: {event}")

stream = client.trips.stream("trip_abc123", callback=on_event)
```

---

## Summary

**API Endpoints Summary:**

| Category | Endpoints | Purpose |
|----------|-----------|---------|
| **Events** | 5 | CRUD operations |
| **Timeline** | 3 | Query and search |
| **Stream** | 2 | Real-time updates |
| **Export** | 3 | PDF/JSON export |
| **Analytics** | 3 | Insights and patterns |
| **Webhooks** | 4 | Event notifications |
| **Customer** | 2 | Customer-facing |
| **Batch** | 2 | Bulk operations |

**Total: 24 endpoints**

**Version:** 1.0
**Last Updated:** 2026-04-23
**Compatibility:** Backward compatible within 1.x series
