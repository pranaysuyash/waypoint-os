# Timeline: Testing Scenarios (Complete)

> Test cases, edge cases, and validation scenarios

---

## Part 1: Testing Philosophy

### Test Coverage Goals

| Layer | Coverage Target | Priority |
|-------|----------------|----------|
| **Unit** | 90%+ | Critical path only |
| **Integration** | 80%+ | All external integrations |
| **E2E** | 70%+ | Critical user journeys |
| **Performance** | 100% | All endpoints |

### Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E Tests  │  20% - Critical journeys
                    │   (Cypress)  │
                    └──────┬────────┘
                           │
            ┌──────────────┴──────────────┐
            │   Integration Tests          │  30% - API & integrations
            │   (Vitest + Supabase)       │
            └──────────────┬──────────────┘
                           │
            ┌──────────────┴──────────────┐
            │    Unit Tests                │  50% - Business logic
            │    (Vitest)                  │
            └──────────────────────────────┘
```

---

## Part 2: Unit Test Scenarios

### 2.1 Event Creation

```typescript
describe('Event Creation', () => {
  test('should create valid event with all required fields', () => {
    const event = createTripEvent({
      trip_id: 'trip_123',
      workspace_id: 'ws_123',
      event_type: 'whatsapp_message_received',
      category: 'conversation',
      timestamp: '2026-04-23T10:30:00Z',
      actor: { id: 'cust_123', name: 'John', type: 'customer' },
      content: { message: 'Hello' }
    });

    expect(event.id).toBeDefined();
    expect(event.created_at).toBeDefined();
    expect(event.event_type).toBe('whatsapp_message_received');
  });

  test('should reject event without required fields', () => {
    expect(() => {
      createTripEvent({
        trip_id: 'trip_123',
        // Missing workspace_id
        event_type: 'whatsapp_message_received',
        // Missing category
      });
    }).toThrow('ValidationError');
  });

  test('should validate event type against taxonomy', () => {
    const invalidEvent = {
      event_type: 'invalid_type',
      // ... other fields
    };

    expect(() => validateEvent(invalidEvent))
      .toThrow('Invalid event type');
  });
});
```

### 2.2 Event Transformation

```typescript
describe('Event Transformation', () => {
  test('should translate internal event to customer-friendly', () => {
    const internal = {
      event_type: 'decision_changed',
      content: {
        fromState: 'EVALUATING_OPTIONS',
        toState: 'READY_TO_QUOTE',
        reason: 'All info collected'
      }
    };

    const customer = translateForCustomer(internal);

    expect(customer.type).toBe('milestone_reached');
    expect(customer.title).toContain('progress');
    expect(customer.content).not.toContain('EVALUATING_OPTIONS');
  });

  test('should filter internal-only events', () => {
    const events = [
      { id: '1', is_internal_only: false },
      { id: '2', is_internal_only: true },
      { id: '3', is_internal_only: false }
    ];

    const customerEvents = filterForCustomer(events);

    expect(customerEvents).toHaveLength(2);
    expect(customerEvents.find(e => e.id === '2')).toBeUndefined();
  });
});
```

### 2.3 Event Filtering

```typescript
describe('Event Filtering', () => {
  test('should filter by event type', () => {
    const events = [
      { event_type: 'whatsapp_message_received' },
      { event_type: 'decision_changed' },
      { event_type: 'whatsapp_message_sent' }
    ];

    const filtered = filterByType(events, ['whatsapp_message_*']);

    expect(filtered).toHaveLength(2);
  });

  test('should filter by date range', () => {
    const events = [
      { timestamp: '2026-04-20T10:00:00Z' },
      { timestamp: '2026-04-25T10:00:00Z' },
      { timestamp: '2026-04-23T10:00:00Z' }
    ];

    const filtered = filterByDateRange(events, {
      start: '2026-04-22T00:00:00Z',
      end: '2026-04-24T00:00:00Z'
    });

    expect(filtered).toHaveLength(1);
    expect(filtered[0].timestamp).toBe('2026-04-23T10:00:00Z');
  });
});
```

### 2.4 Event Aggregation

```typescript
describe('Event Aggregation', () => {
  test('should count events by type', () => {
    const events = [
      { event_type: 'message_received' },
      { event_type: 'message_sent' },
      { event_type: 'message_received' },
      { event_type: 'decision_changed' }
    ];

    const counts = aggregateByType(events);

    expect(counts).toEqual({
      message_received: 2,
      message_sent: 1,
      decision_changed: 1
    });
  });

  test('should calculate timeline statistics', () => {
    const events = [
      { timestamp: '2026-04-20T10:00:00Z' },
      { timestamp: '2026-04-23T15:00:00Z' },
      { timestamp: '2026-04-22T12:00:00Z' }
    ];

    const stats = calculateStatistics(events);

    expect(stats.total_events).toBe(3);
    expect(stats.first_event).toBe('2026-04-20T10:00:00Z');
    expect(stats.last_event).toBe('2026-04-23T15:00:00Z');
    expect(stats.duration_hours).toBeGreaterThan(70);
  });
});
```

---

## Part 3: Integration Test Scenarios

### 3.1 WhatsApp Integration

```typescript
describe('WhatsApp Integration', () => {
  test('should receive and process WhatsApp webhook', async () => {
    const webhookPayload = {
      entry: [{
        changes: [{
          value: {
            messages: [{
              from: '919876543210',
              id: 'wa_msg_123',
              timestamp: '1713840000',
              text: { body: 'Hello, I need travel help' }
            }]
          }
        }]
      }]
    };

    const response = await fetch('/api/webhooks/whatsapp', {
      method: 'POST',
      body: JSON.stringify(webhookPayload)
    });

    expect(response.status).toBe(200);

    // Verify event was created
    const events = await getTripEventsByPhone('919876543210');
    expect(events).toHaveLength(1);
    expect(events[0].event_type).toBe('whatsapp_message_received');
  });

  test('should handle media messages', async () => {
    const webhookPayload = {
      // ... media message payload
    };

    await processWebhook(webhookPayload);

    const event = await getLatestEvent();
    expect(event.content.mediaUrl).toBeDefined();
    expect(event.content.mediaType).toBe('image');
  });

  test('should handle webhook signature verification', async () => {
    const invalidPayload = { /* ... */ };
    const invalidSignature = 'invalid_sig';

    const response = await fetch('/api/webhooks/whatsapp', {
      method: 'POST',
      headers: { 'X-Hub-Signature': invalidSignature },
      body: JSON.stringify(invalidPayload)
    });

    expect(response.status).toBe(401);
  });
});
```

### 3.2 Email Integration

```typescript
describe('Email Integration', () => {
  test('should process inbound email via SMTP webhook', async () => {
    const emailPayload = {
      from: 'customer@example.com',
      to: 'agent@agency.com',
      subject: 'Thailand trip inquiry',
      text: 'Hi, planning honeymoon to Thailand...',
      html: '<p>Hi, planning honeymoon to Thailand...</p>'
    };

    await processEmailWebhook(emailPayload);

    const events = await getTripEventsByEmail('customer@example.com');
    expect(events[0].event_type).toBe('email_received');
  });

  test('should thread emails by conversation', async () => {
    // Send first email
    await sendEmail({
      to: 'customer@example.com',
      subject: 'Thailand Quote',
      threadId: 'thread_123'
    });

    // Customer replies
    await receiveEmail({
      from: 'customer@example.com',
      subject: 'Re: Thailand Quote',
      inReplyTo: 'thread_123'
    });

    const thread = await getEmailThread('thread_123');
    expect(thread).toHaveLength(2);
  });
});
```

### 3.3 Decision Engine Integration

```typescript
describe('Decision Engine Integration', () => {
  test('should create timeline event on decision change', async () => {
    await decisionEngine.makeDecision('trip_123', {
      new_state: 'READY_TO_QUOTE',
      reason: 'All requirements met'
    });

    const events = await getTripEvents('trip_123');
    const decisionEvent = events.find(e => e.event_type === 'decision_changed');

    expect(decisionEvent).toBeDefined();
    expect(decisionEvent.content.toState).toBe('READY_TO_QUOTE');
    expect(decisionEvent.actor.type).toBe('ai');
  });

  test('should include decision rationale in event', async () => {
    await decisionEngine.makeDecision('trip_123', {
      new_state: 'NEEDS_ATTENTION',
      reason: 'Budget exceeds customer stated by 20%',
      confidence: 0.75
    });

    const event = await getLatestDecisionEvent('trip_123');
    expect(event.content.reason).toContain('Budget exceeds');
    expect(event.content.confidence).toBe(0.75);
  });
});
```

---

## Part 4: E2E Test Scenarios

### 4.1 Complete Trip Journey

```typescript
describe('Complete Trip Journey', () => {
  test('from inquiry to booking', async () => {
    // 1. Customer sends inquiry
    await sendWhatsAppMessage({
      from: 'customer',
      message: 'Planning honeymoon to Thailand in June'
    });

    // 2. AI extracts information
    await waitForEvent('extraction_completed');

    // 3. Agent asks follow-up questions
    await sendWhatsAppMessage({
      to: 'customer',
      message: 'What\'s your budget range?'
    });

    // 4. Customer provides budget
    await sendWhatsAppMessage({
      from: 'customer',
      message: 'Around 2 lakh'
    });

    // 5. Decision changes to ready to quote
    await waitForEvent('decision_changed', {
      content: { toState: 'READY_TO_QUOTE' }
    });

    // 6. Quote is generated and sent
    await waitForEvent('quote_sent');

    // 7. Customer confirms
    await sendWhatsAppMessage({
      from: 'customer',
      message: 'Looks good, proceed with booking'
    });

    // 8. Booking is confirmed
    await waitForEvent('booking_confirmed');

    // Verify complete timeline
    const timeline = await getTripTimeline('trip_123');
    expect(timeline.events).toHaveLength.greaterThan(10);
  });
});
```

### 4.2 Agent Handoff Scenario

```typescript
describe('Agent Handoff', () => {
  test('new agent can understand trip from timeline', async () => {
    // Setup: Trip with 50 events
    await createComplexTrip('trip_123');

    // New agent views timeline
    const timeline = await getTripTimeline('trip_123');

    // Agent can understand:
    expect(timeline.summary).toBeDefined();
    expect(timeline.keyMoments).toHaveLength.greaterThan(0);
    expect(timeline.customerProfile).toBeDefined();

    // Agent finds specific information
    const budgetEvents = await searchTimeline('trip_123', 'budget');
    expect(budgetEvents).toHaveLength.greaterThan(0);

    // Agent gets trip summary
    const summary = await getTripSummary('trip_123');
    expect(summary.narrative).toContain('honeymoon');
  });
});
```

### 4.3 Customer Portal Scenario

```typescript
describe('Customer Portal', () => {
  test('customer sees safe timeline', async () => {
    // Create trip with mixed events
    await createTripWithMixedEvents('trip_123');

    // Customer accesses timeline
    const customerTimeline = await getCustomerTimeline('customer_token');

    // Internal events are filtered
    const internalEvents = customerTimeline.events.filter(
      e => e.is_internal_only === true
    );
    expect(internalEvents).toHaveLength(0);

    // Events are translated
    const decisionEvents = customerTimeline.events.filter(
      e => e.type === 'decision_changed'
    );
    expect(decisionEvents).toHaveLength(0); // Should be translated
  });
});
```

---

## Part 5: Edge Cases

### 5.1 High Volume Events

```typescript
describe('High Volume Scenarios', () => {
  test('should handle trip with 1000+ events', async () => {
    // Create trip with 1000 events
    await createTripWithManyEvents('trip_123', 1000);

    // Timeline loads efficiently
    const start = Date.now();
    const timeline = await getTripTimeline('trip_123', {
      page: 1,
      page_size: 50
    });
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(500); // <500ms
    expect(timeline.events).toHaveLength(50);
    expect(timeline.meta.totalCount).toBe(1000);
  });

  test('should paginate correctly', async () => {
    await createTripWithManyEvents('trip_123', 250);

    const page1 = await getTripTimeline('trip_123', { page: 1, page_size: 50 });
    const page2 = await getTripTimeline('trip_123', { page: 2, page_size: 50 });

    expect(page1.events[0].timestamp).toBeGreaterThan(page2.events[0].timestamp);
    expect(page1.meta.hasMore).toBe(true);
  });
});
```

### 5.2 Concurrent Modifications

```typescript
describe('Concurrent Modifications', () => {
  test('should handle simultaneous event creation', async () => {
    const promises = Array.from({ length: 10 }, (_, i) =>
      createEvent({
        trip_id: 'trip_123',
        event_type: 'test_event',
        content: { index: i }
      })
    );

    await Promise.all(promises);

    const events = await getTripEvents('trip_123');
    expect(events).toHaveLength.greaterThanOrEqual(10);
  });

  test('should handle race conditions in updates', async () => {
    const event = await createEvent({ /* ... */ });

    // Simultaneous updates
    const promises = [
      updateEvent(event.id, { content: { version: 1 } }),
      updateEvent(event.id, { content: { version: 2 } }),
      updateEvent(event.id, { content: { version: 3 } })
    ];

    await Promise.all(promises);

    // Last write wins (or implement versioning)
    const updated = await getEvent(event.id);
    expect(updated.content.version).toBeDefined();
  });
});
```

### 5.3 Malformed Data

```typescript
describe('Malformed Data Handling', () => {
  test('should handle invalid JSON in content', async () => {
    const event = await createEvent({
      content: { valid: 'data' }
    });

    // Corrupt the data directly in DB
    await db.raw(`
      UPDATE trip_events
      SET content = '{"invalid": json}'
      WHERE id = $1
    `, [event.id]);

    // Should handle gracefully
    const retrieved = await getEvent(event.id);
    expect(retrieved).toBeDefined();
    expect(retrieved.content).toEqual({}); // Fallback to empty object
  });

  test('should handle missing optional fields', async () => {
    const event = await createEvent({
      trip_id: 'trip_123',
      event_type: 'test_event',
      category: 'system',
      timestamp: '2026-04-23T10:00:00Z',
      actor: { type: 'system', name: 'System' },
      content: { message: 'Test' }
      // source, metadata omitted
    });

    expect(event.source).toBeUndefined();
    expect(event.metadata).toBeUndefined();
  });
});
```

### 5.4 Timezone Edge Cases

```typescript
describe('Timezone Handling', () => {
  test('should handle events across DST boundary', async () => {
    // Create event just before DST change
    const beforeDST = '2026-03-08T01:59:00Z';  // Just before DST
    const afterDST = '2026-03-08T03:00:00Z';   // Just after DST (gap)

    await createEvent({
      timestamp: beforeDST,
      content: { message: 'Before DST' }
    });

    await createEvent({
      timestamp: afterDST,
      content: { message: 'After DST' }
    });

    const events = await getTripEvents('trip_123');
    // Should handle gap correctly
    expect(events).toHaveLength(2);
  });

  test('should display events in user timezone', async () => {
    const event = await createEvent({
      timestamp: '2026-04-23T10:30:00Z',  // UTC
      content: { message: 'Test' }
    });

    // User in IST (UTC+5:30)
    const displayed = formatForTimezone(event, 'Asia/Kolkata');
    expect(displayed.timestamp).toContain('16:00'); // 10:30 UTC = 16:00 IST
  });
});
```

---

## Part 6: Performance Tests

### 6.1 Query Performance

```typescript
describe('Query Performance', () => {
  test('timeline query should be fast', async () => {
    await createTripWithManyEvents('trip_123', 500);

    const start = Date.now();
    await getTripTimeline('trip_123');
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(100); // <100ms
  });

  test('search query should be fast', async () => {
    await createTripWithManyEvents('trip_123', 500);

    const start = Date.now();
    await searchTimeline('trip_123', 'Thailand');
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(200); // <200ms
  });

  test('aggregation query should be fast', async () => {
    await createTripWithManyEvents('trip_123', 500);

    const start = Date.now();
    await getTimelineStatistics('trip_123');
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(500); // <500ms
  });
});
```

### 6.2 Concurrent Load

```typescript
describe('Load Testing', () => {
  test('should handle 100 concurrent timeline requests', async () => {
    const promises = Array.from({ length: 100 }, () =>
      getTripTimeline('trip_123')
    );

    const start = Date.now();
    await Promise.all(promises);
    const duration = Date.now() - start;

    // All requests should complete reasonably
    expect(duration).toBeLessThan(5000); // <5 seconds total
  });

  test('should handle event creation rate', async () => {
    const start = Date.now();

    await Promise.all(
      Array.from({ length: 100 }, (_, i) =>
        createEvent({
          trip_id: `trip_${i}`,
          event_type: 'test_event',
          content: { index: i }
        })
      )
    );

    const duration = Date.now() - start;
    const rate = 100 / (duration / 1000); // events per second

    expect(rate).toBeGreaterThan(50); // >50 events/second
  });
});
```

---

## Part 7: Security Tests

### 7.1 Access Control

```typescript
describe('Access Control', () => {
  test('should prevent cross-agency access', async () => {
    const agencyA = await createAgency();
    const agencyB = await createAgency();
    const trip = await createTrip({ agency_id: agencyA.id });

    // Agency B tries to access Agency A's trip
    const response = await getTripTimeline(trip.id, {
      token: agencyB.token
    });

    expect(response.status).toBe(403);
  });

  test('should filter internal events for non-owners', async () => {
    const agent = await createAgent({ role: 'agent' });
    const trip = await createTripWithInternalEvents();

    const timeline = await getTripTimeline(trip.id, {
      token: agent.token
    });

    const internalEvents = timeline.events.filter(
      e => e.is_internal_only === true
    );
    expect(internalEvents).toHaveLength(0);
  });
});
```

### 7.2 Data Sanitization

```typescript
describe('Data Sanitization', () => {
  test('should sanitize PII for customer portal', async () => {
    await createEvent({
      content: {
        message: 'My number is 9876543210',
        phone: '9876543210'
      }
    });

    const customerTimeline = await getCustomerTimeline('token');

    // PII should be masked
    expect(customerTimeline.events[0].content.message).not.toContain('9876543210');
    expect(customerTimeline.events[0].content.message).toContain('***');
  });
});
```

---

## Part 8: Test Data Fixtures

### Sample Trip Scenarios

```typescript
// Thailand Honeymoon Trip
const thailandHoneymoonFixture = {
  destination: 'Thailand',
  trip_type: 'honeymoon',
  budget: 200000,
  travelers: 2,
  events: [
    {
      event_type: 'inquiry_received',
      content: {
        rawMessage: 'Planning honeymoon to Thailand in June',
        extractedData: { destination: 'Thailand', tripType: 'honeymoon' }
      }
    },
    {
      event_type: 'whatsapp_message_received',
      content: {
        message: 'Budget around 2 lakh for 2 people'
      }
    },
    {
      event_type: 'analysis_scenarios',
      content: {
        scenarios: [
          { name: 'Phuket + Krabi', selected: true, score: 0.92 }
        ]
      }
    },
    {
      event_type: 'decision_changed',
      content: {
        fromState: 'EVALUATING_OPTIONS',
        toState: 'READY_TO_BOOK'
      }
    }
  ]
};

// Complex Multi-Destination Trip
const complexTripFixture = {
  destinations: ['Thailand', 'Singapore', 'Bali'],
  budget: 500000,
  events: [
    // ... 100+ events spanning multiple phases
  ]
};
```

---

## Summary

**Test Coverage Summary:**

| Category | Test Count | Coverage |
|----------|------------|----------|
| Unit Tests | 150+ | 90% |
| Integration Tests | 80+ | 80% |
| E2E Tests | 30+ | 70% |
| Performance Tests | 20+ | 100% |
| Security Tests | 25+ | 85% |
| **Total** | **300+** | **85%** |

**Testing Priorities:**

1. **P0 (Critical):** Event creation, timeline retrieval, access control
2. **P1 (High):** Integrations (WhatsApp, Email), search, export
3. **P2 (Medium):** Analytics, patterns, AI features
4. **P3 (Low):** UI polish, nice-to-haves

**Test Execution:**

- Unit tests: Every PR (<5 min)
- Integration tests: Every PR (<15 min)
- E2E tests: Before merge (<30 min)
- Performance tests: Nightly build
- Load tests: Weekly

---

**Status:** Testing scenarios complete.
**Version:** 1.0
**Last Updated:** 2026-04-23
