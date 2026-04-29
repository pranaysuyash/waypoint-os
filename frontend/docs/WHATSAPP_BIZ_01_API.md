# WhatsApp Business Platform — API & Architecture

> Research document for the WhatsApp Business API integration, message templates, conversation management, and the technical architecture for WhatsApp-first travel agency operations.

---

## Key Questions

1. **How does WhatsApp Business API work for travel agencies?**
2. **What message templates are needed?**
3. **How do conversations map to trips and customers?**
4. **What are the rate limits, costs, and constraints?**

---

## Research Areas

### WhatsApp Business API Architecture

```typescript
interface WhatsAppBusinessConfig {
  // WhatsApp Business Platform setup
  setup: {
    business_account_id: string;
    phone_number_id: string;
    whatsapp_business_api_key: string;
    webhook_url: string;
    webhook_verify_token: string;

    // Compliance
    business_display_name: string;       // "Waypoint Travel"
    business_category: "TRAVEL_SERVICES";
    business_description: string;
    country: "IN";

    // Quality rating
    quality_rating: "GREEN" | "YELLOW" | "RED";
    messaging_limit: string;             // "1K", "10K", "100K", "UNLIMITED"
  };

  // Message types
  message_types: {
    // Business-initiated (requires approved template)
    TEMPLATE_MESSAGE: {
      description: "Proactive messages to customers";
      requires_template_approval: true;
      cost_per_message: number;           // varies by country (~₹0.3-1.0 India)
      examples: [
        "Booking confirmation",
        "Trip reminder",
        "Itinerary update",
        "Daily briefing",
        "Payment reminder",
      ];
    };

    // User-initiated (customer messages first)
    CONVERSATION_MESSAGE: {
      description: "Reply within 24h customer service window";
      cost: "FREE within 24h window";
      window: "24 hours from last customer message";
      beyond_window: "Must use template message";
    };

    // Interactive messages
    INTERACTIVE: {
      types: ["QUICK_REPLY", "BUTTON", "LIST"];
      use_cases: [
        "Objection response options",
        "Package variant selection",
        "Check-in mood buttons",
        "Payment plan options",
      ];
    };

    // Rich media
    MEDIA: {
      types: ["IMAGE", "DOCUMENT", "VIDEO", "STICKER", "LOCATION", "CONTACT"];
      size_limits: {
        image: "5MB";
        document: "100MB";
        video: "16MB";
      };
    };
  };
}

// ── WhatsApp Business API overview ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Business Platform — Waypoint Travel           │
// │                                                       │
// │  Account Status: ✅ Active                              │
// │  Quality Rating: 🟢 GREEN                              │
// │  Messaging Limit: 10K conversations/day                │
// │                                                       │
// │  Message categories:                                  │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Type           │ Cost        │ Requires        │   │
// │  │                │             │ Approval        │   │
// │  │ ──────────────────────────────────────────────│   │
// │  │ Template (proactive)│₹0.3-1.0│ Yes (Meta)      │   │
// │  │ Conversation (reply)│ FREE   │ No (24h window) │   │
// │  │ Interactive buttons │ FREE   │ No (in convo)   │   │
// │  │ Rich media          │ FREE   │ No (in convo)   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Monthly usage:                                       │
// │  Template messages: 2,400 (₹1,200)                    │
// │  Conversation messages: 18,500 (FREE)                 │
// │  Total cost: ~₹1,200/month                            │
// │  vs. SMS equivalent: ~₹37,000/month                   │
// │  Savings: 97%                                         │
// │                                                       │
// │  [Template Manager] [Analytics] [Webhook Logs]          │
// └─────────────────────────────────────────────────────┘
```

### Message Template Library

```typescript
interface WhatsAppTemplateLibrary {
  templates: {
    // Trip lifecycle templates
    BOOKING_CONFIRMATION: {
      name: "trip_booking_confirmed";
      category: "MARKETING";
      language: "en";
      body: "Your {destination} trip is confirmed! 🎉\n\n📅 {dates}\n👥 {travelers} travelers\n💰 Total: ₹{amount}\n\nNext: We'll send your visa checklist shortly.\n\nTrack your trip: {trip_link}";
      parameters: ["destination", "dates", "travelers", "amount", "trip_link"];
      approval_status: "APPROVED";
    };

    PAYMENT_REMINDER: {
      name: "payment_reminder";
      category: "UTILITY";
      body: "Hi {name}, your {destination} trip balance payment of ₹{amount} is due by {due_date}.\n\nPay now: {payment_link}\n\nQuestions? Reply to this message.";
      parameters: ["name", "destination", "amount", "due_date", "payment_link"];
      approval_status: "APPROVED";
    };

    DOCUMENT_REMINDER: {
      name: "document_reminder";
      category: "UTILITY";
      body: "Hi {name}, your {document_type} for {destination} trip is still pending.\n\nPlease upload by {deadline} to avoid delays.\n\nUpload here: {upload_link}";
      parameters: ["name", "document_type", "destination", "deadline", "upload_link"];
      approval_status: "APPROVED";
    };

    DAILY_BRIEFING: {
      name: "daily_trip_briefing";
      category: "UTILITY";
      body: "☀️ Good morning, {name}!\n\nDay {day_number} in {city}\n🌤️ {weather}\n\nToday:\n{schedule}\n\n💡 Tip: {tip}";
      parameters: ["name", "day_number", "city", "weather", "schedule", "tip"];
      approval_status: "APPROVED";
    };

    DISRUPTION_ALERT: {
      name: "trip_disruption";
      category: "UTILITY";
      body: "⚠️ Trip Update — {destination}\n\n{what_happened}\n\nNew plan: {new_plan}\n\nYour agent {agent_name} is handling this. Questions? Reply here.";
      parameters: ["destination", "what_happened", "new_plan", "agent_name"];
      approval_status: "APPROVED";
    };

    MEMORY_BOOK_READY: {
      name: "memory_book_ready";
      category: "MARKETING";
      body: "📸 Your {destination} memory book is ready!\n\n{photo_count} photos · {pages} pages\n\n[Preview Image]\n\n📥 Download: {download_link}\n📖 Print version: {print_link}";
      parameters: ["destination", "photo_count", "pages", "download_link", "print_link"];
      approval_status: "APPROVED";
    };
  };
}

// ── Template management ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Template Manager                               │
// │                                                       │
// │  Approved: 18 · Pending: 1 · Rejected: 0              │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Template              │ Category │ Status │ Uses│   │
// │  │ ────────────────────────────────────────────  │   │
// │  │ booking_confirmed     │ MARKETING│ ✅     │ 342│   │
// │  │ payment_reminder      │ UTILITY  │ ✅     │ 218│   │
// │  │ document_reminder     │ UTILITY  │ ✅     │ 156│   │
// │  │ daily_briefing        │ UTILITY  │ ✅     │ 89 │   │
// │  │ disruption_alert      │ UTILITY  │ ✅     │ 12 │   │
// │  │ memory_book_ready     │ MARKETING│ ✅     │ 45 │   │
// │  │ review_request        │ MARKETING│ ✅     │ 67 │   │
// │  │ referral_request      │ MARKETING│ ⏳     │ —  │   │
// │  │ visa_update           │ UTILITY  │ ✅     │ 134│   │
// │  │ trip_countdown        │ MARKETING│ ✅     │ 89 │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [+ New Template] [Import] [Bulk Approve Request]      │
// └─────────────────────────────────────────────────────┘
```

### Conversation-Trip Mapping

```typescript
interface ConversationMapping {
  // Map WhatsApp conversations to trips and customers
  mapping: {
    whatsapp_phone: string;
    customer_id: string | null;           // matched via phone number
    active_trips: string[];               // trip IDs with this phone
    conversation_state: "NEW" | "QUALIFYING" | "PROPOSAL" | "BOOKING" | "ACTIVE_TRIP" | "POST_TRIP" | "IDLE";

    // Message routing
    assigned_agent: string | null;
    last_message_at: string;
    last_message_by: "CUSTOMER" | "AGENT" | "SYSTEM";
    unread_count: number;

    // 24h window tracking
    window_expires_at: string | null;
    window_expired: boolean;
  };
}

// ── Conversation management ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Conversations — Active (23)                    │
// │                                                       │
// │  🔴 Needs response (4):                               │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ +91-98XXX-XXXX → "Dubai trip kitna hoga?"      │   │
// │  │ Customer: New · State: QUALIFYING               │   │
// │  │ Window: 23h 15min remaining · Assigned: None    │   │
// │  │ [Assign Agent] [Auto-Reply]                      │   │
// │  │                                               │   │
// │  │ +91-97XXX-XXXX → Sharma family                  │   │
// │  │ Customer: TRV-1847 · Trips: WP-442 (active)     │   │
// │  │ State: ACTIVE_TRIP                              │   │
// │  │ "Universal Studios mein crowd bahut tha"         │   │
// │  │ Window: 22h 45min · Assigned: Priya ✅          │   │
// │  │ [Reply] [View Trip] [Send Update]               │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ✅ Responded (19):                                   │
// │  19 conversations handled within SLA                   │
// │                                                       │
// │  ⏰ Window expiring soon (2):                          │
// │  • +91-99XXX-XXXX — 1h 30min remaining                 │
// │  • +91-96XXX-XXXX — 45min remaining                    │
// │                                                       │
// │  [View All] [Auto-Distribute] [Analytics]               │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Template approval delays** — Meta's template approval can take 24-48 hours. Need a template library with pre-approved variants to avoid delays.

2. **24-hour window constraint** — After 24 hours without a customer message, businesses must use paid template messages. Need strategies to keep conversations alive naturally.

3. **Multi-trip conversations** — Customers with multiple trips (past and active) need clear context in each message about which trip is being discussed.

4. **Hinglish support** — Customer messages in Hinglish need NLP that handles both Hindi and English mixed naturally.

---

## Next Steps

- [ ] Build WhatsApp Business API integration with webhook handlers
- [ ] Create template library with pre-approved message templates
- [ ] Implement conversation-trip mapping with auto-routing
- [ ] Design 24-hour window management with proactive engagement
