# Conversation History & Activity Log

> Research document for conversation history browsing, activity logs, and audit trails.

---

## Current State

No dedicated history or log page exists. Past interactions are stored as flat fields on trip objects with no browsable interface, no filtering, and no replay capability.

---

## Key Questions

1. **What's the primary use case for history — reviewing past trips, auditing agent actions, or training?**
2. **How do we organize history — by trip, by customer, by agent, by date, or all of these?**
3. **What activity types need logging (messages, edits, system actions, spine runs)?**
4. **How long should history be retained?**
5. **What search and filtering capabilities are essential?**
6. **How do we display spine run results in context of the conversation that triggered them?**

---

## Research Areas

### History Views

```typescript
type HistoryViewType =
  | 'by_trip'            // All activity for a specific trip
  | 'by_customer'        // All interactions with a customer
  | 'by_agent'           // All actions by an agent
  | 'by_date'            // Timeline view of all activity
  | 'by_status'          // Trips filtered by status
  | 'by_type'            // Filter by activity type
  | 'search_results';    // Free-text search results

interface HistoryPage {
  viewType: HistoryViewType;
  filters: HistoryFilter[];
  sort: HistorySort;
  pagination: PaginationState;
  results: HistoryEntry[];
  aggregations: HistoryAggregations;
}

interface HistoryFilter {
  field: string;
  operator: 'equals' | 'contains' | 'range' | 'in';
  value: string | number | string[];
}

interface HistorySort {
  field: string;
  direction: 'asc' | 'desc';
}
```

### Activity Log Model

```typescript
interface ActivityLogEntry {
  entryId: string;
  tripId: string;
  timestamp: Date;
  actor: ActorInfo;
  action: ActivityAction;
  category: ActivityCategory;
  details: Record<string, unknown>;
  relatedEntries: string[];        // IDs of related log entries
  undoable: boolean;
}

interface ActorInfo {
  type: 'agent' | 'customer' | 'system' | 'assistant';
  id: string;
  name: string;
}

type ActivityCategory =
  | 'message'           // Sent, received, edited, deleted
  | 'trip'              // Created, updated, status changed
  | 'spine_run'         // Initiated, completed, failed
  | 'booking'           // Booked, modified, cancelled
  | 'document'          // Generated, sent, downloaded
  | 'note'              // Internal note added
  | 'system'            // System event (alert, error)
  | 'integration'       // External API call
  | 'approval'          // Approval action
  | 'assignment';       // Trip assignment change

type ActivityAction =
  | 'created'
  | 'updated'
  | 'deleted'
  | 'sent'
  | 'received'
  | 'edited'
  | 'status_changed'
  | 'assigned'
  | 'commented'
  | 'approved'
  | 'rejected'
  | 'escalated'
  | 'resolved';
```

### Trip Timeline View

**A unified chronological view of everything that happened on a trip:**

```typescript
interface TripTimeline {
  tripId: string;
  events: TimelineEvent[];
}

interface TimelineEvent {
  id: string;
  timestamp: Date;
  type: TimelineEventType;
  actor: ActorInfo;
  title: string;
  summary: string;
  expandable: boolean;
  detail?: TimelineEventDetail;
}

type TimelineEventType =
  | 'customer_message'   // Customer sent a message
  | 'agent_message'      // Agent sent a response
  | 'agent_note'         // Agent added internal note
  | 'spine_run_started'  // Processing initiated
  | 'spine_run_completed' // Processing finished
  | 'spine_run_failed'   // Processing failed
  | 'itinerary_generated' // Itinerary created
  | 'quote_generated'    // Quote created
  | 'booking_made'       // Component booked
  | 'booking_modified'   // Booking changed
  | 'booking_cancelled'  // Booking cancelled
  | 'document_sent'      // Document sent to customer
  | 'payment_received'   // Payment received
  | 'status_change'      // Trip status changed
  | 'assignment_change'  // Agent assignment changed
  | 'alert_received'     // Travel alert received
  | 'customer_feedback'  // Customer feedback received
  | 'edit_made'          // Message or data edited
  | 'system_event';      // System notification
```

### Search & Filtering

```typescript
interface HistorySearch {
  query?: string;                  // Full-text search
  filters: {
    dateRange?: DateRange;
    tripStatus?: TripStatus[];
    agents?: string[];
    customers?: string[];
    destinations?: string[];
    activityTypes?: ActivityCategory[];
    hasSpineRuns?: boolean;
    hasBookings?: boolean;
  };
  sortBy: 'date' | 'relevance' | 'trip_value';
  sortOrder: 'asc' | 'desc';
}
```

**Research needed:**
- What search engine works best for this use case (PostgreSQL full-text, Meilisearch, Typesense)?
- How to index message content + structured data together?
- What's the right pagination approach for infinite scroll vs. page-based?

---

## Open Problems

1. **Log volume management** — A single trip generates 20-50 log entries. At 1,000 trips, that's 50K entries. How to keep the log browsable without overwhelming?

2. **Spine run context** — When viewing a spine run in the timeline, how much detail to show inline vs. requiring a click-through? The run output can be large.

3. **Cross-trip patterns** — "Show me all trips where the customer asked for a change after itinerary generation" requires cross-trip querying that's hard with per-trip timelines.

4. **Privacy in activity logs** — Internal notes and agent actions may be sensitive. Who can see what in the activity log?

5. **Real-time log updates** — Should the history page update in real-time as new activities occur, or only on refresh?

---

## Next Steps

- [ ] Research activity log UI patterns (Linear, Notion, GitHub activity)
- [ ] Design trip timeline component with expandable events
- [ ] Study search indexing options for message + structured data
- [ ] Create wireframes for history browsing views
- [ ] Map all activity types that need logging from current system
- [ ] Design log retention and archival strategy
