# Customer Communication Preferences — Notification & Channel Management

> Research document for customer communication preference management, notification channels, frequency controls, quiet hours, opt-in/opt-out management, and personalized communication cadence for the Waypoint OS platform.

---

## Key Questions

1. **How do customers control how and when the agency communicates?**
2. **What notification channels are available and how are they managed?**
3. **How do we balance engagement with avoiding notification fatigue?**
4. **What regulatory requirements govern customer communications?**

---

## Research Areas

### Communication Preference Center

```typescript
interface CommunicationPreferences {
  // Customer-controlled communication settings
  preference_center: {
    CHANNEL_PREFERENCES: {
      description: "Customer chooses their preferred communication channels";
      channels: {
        WHATSAPP: {
          use_cases: ["Trip updates", "Payment reminders", "Quick questions", "Emergency alerts"];
          opt_out_possible: "Yes, except for booking-critical and emergency messages";
          customer_control: "Can disable marketing messages while keeping transactional";
        };

        EMAIL: {
          use_cases: ["Booking confirmations", "Itinerary PDFs", "Payment receipts", "Newsletters"];
          opt_out_possible: "Yes for newsletters and marketing; no for transactional";
          frequency: "Customer selects: All emails / Important only / None";
        };

        SMS: {
          use_cases: ["OTP/verification", "Emergency alerts", "Payment reminders"];
          opt_out_possible: "Yes, except for emergency alerts";
          cost_note: "SMS costs ₹0.5-2 per message; used sparingly";
        };

        PHONE_CALL: {
          use_cases: ["Pre-trip walkthrough", "Emergency contact", "Complex issues"];
          opt_out_possible: "Yes, agent will use WhatsApp instead";
          timing: "Customer specifies preferred call times";
        };

        APP_NOTIFICATION: {
          use_cases: ["Trip updates", "Checklist reminders", "Budget alerts", "Chat messages"];
          opt_out_possible: "Yes, but trip-critical alerts always shown";
          control: "Customer can disable non-critical app notifications";
        };
      };
    };

    FREQUENCY_PREFERENCES: {
      description: "How often the customer wants to hear from the agency";
      settings: {
        MARKETING: {
          options: ["Weekly deals", "Monthly digest", "Only when relevant to my trip", "Never"];
          default: "Only when relevant to my trip";
        };

        TRIP_UPDATES: {
          options: ["Every update", "Important updates only", "Weekly summary"];
          default: "Important updates only";
        };

        PAYMENT_REMINDERS: {
          options: ["All reminders", "Only overdue", "None (I'll track myself)"];
          default: "All reminders";
        };

        CHECKLIST_REMINDERS: {
          options: ["Daily until complete", "Every 3 days", "Weekly", "None"];
          default: "Every 3 days";
        };
      };
    };

    QUIET_HOURS: {
      description: "Times when non-emergency messages are not sent";
      settings: {
        do_not_disturb: "Customer sets DND window (default: 10 PM - 8 AM IST)";
        respect: "System queues messages during quiet hours and sends at next available time";
        exceptions: "Emergency alerts bypass quiet hours (traveler safety always takes priority)";
        timezone: "Automatically adjusted when customer is traveling abroad";
      };
    };

    CONTENT_PREFERENCES: {
      description: "What types of content the customer wants to receive";
      settings: {
        destination_tips: "Yes/No — destination guides, local tips, cultural info";
        deal_alerts: "Yes/No — flash deals, price drops, early bird offers";
        travel_inspiration: "Yes/No — new destinations, seasonal campaigns";
        post_trip_content: "Yes/No — trip journal, feedback requests, next trip suggestions";
      };
    };
  };

  // ── Communication preference center (customer view) ──
  // ┌─────────────────────────────────────────────────────┐
  // │  ⚙️ Communication Preferences                             │
  // │                                                       │
  // │  📱 Preferred Channel: WhatsApp ●  Email ○  Phone ○     │
  // │                                                       │
  // │  🔕 Quiet Hours: 10 PM - 8 AM                             │
  // │  (Emergency alerts bypass quiet hours)                 │
  // │                                                       │
  // │  Marketing Emails:                                    │
  // │  ○ Weekly deals                                        │
  // │  ● Only when relevant to my trip                        │
  // │  ○ Never                                               │
  // │                                                       │
  // │  Trip Updates:                                        │
  // │  ○ Every update                                        │
  // │  ● Important updates only                               │
  // │                                                       │
  // │  Payment Reminders: ● All reminders                      │
  // │  Checklist Reminders: ● Every 3 days                     │
  // │                                                       │
  // │  Content I want:                                      │
  // │  ☑ Destination tips    ☑ Deal alerts                     │
  // │  ☐ Travel inspiration  ☑ Post-trip content                │
  // │                                                       │
  // │  Language: English ●  Hindi ○  Regional ○                │
  // │                                                       │
  // │  [Save Preferences]                                       │
  // └─────────────────────────────────────────────────────┘
}
```

### Automated Notification Engine

```typescript
interface NotificationEngine {
  // Smart notification scheduling and delivery
  notification_types: {
    TRANSACTIONAL: {
      description: "Essential messages related to the booking (cannot be fully disabled)";
      examples: [
        "Booking confirmation",
        "Payment receipt",
        "Visa status update",
        "Flight schedule change",
        "Emergency alert",
      ];
      opt_out: "Cannot be disabled; customer can only change channel preference";
      timing: "Sent immediately regardless of quiet hours for critical items";
    };

    REMINDER: {
      description: "Time-based reminders for pending actions";
      examples: [
        "Payment due in 7 days",
        "Documents still needed: passport copy",
        "Travel insurance not purchased yet",
        "Check-in available for your flight",
        "Trip starts in 3 days — are you ready?",
      ];
      scheduling: "Sent during customer's preferred hours; respects quiet time";
      escalation: "If no action after 2 reminders → escalate to agent phone call";
    };

    MARKETING: {
      description: "Promotional and inspirational content";
      examples: [
        "Weekly deals: Singapore from ₹1.1L",
        "New destination launched: Japan",
        "Early bird offer: Book summer trips now",
        "Your trip anniversary — save 15% on next booking",
      ];
      opt_out: "Can be fully disabled; requires explicit opt-in for marketing";
      frequency: "Respects customer's frequency preference setting";
      targeting: "Only sends marketing relevant to customer's interests and past trips";
    };

    ENGAGEMENT: {
      description: "Content that maintains relationship between trips";
      examples: [
        "Travel tip: How to pack for Singapore in June",
        "Behind the scenes: Agent Priya's Singapore recommendations",
        "Customer spotlight: The Mehta family's trip photos",
        "Seasonal: Best destinations for Diwali break",
      ];
      purpose: "Keep agency top-of-mind without selling; provide value";
      frequency: "Max 2 per week for opted-in customers";
    };
  };

  smart_scheduling: {
    RULES: {
      never_duplicate: "Don't send the same message via WhatsApp AND email — use preferred channel only";
      batch_non_urgent: "Non-urgent messages batched and sent at preferred time (e.g., morning digest)";
      respect_timezone: "Customer in Singapore (IST +2:30) → adjust quiet hours accordingly";
      space_messages: "Minimum 4 hours between non-critical messages to same customer";
      limit_daily: "Max 3 non-critical messages per customer per day";
    };

    AI_OPTIMIZATION: {
      best_time: "Learn when each customer typically reads messages → send at that time";
      engagement_tracking: "Track open/read rates per channel per customer → optimize channel selection";
      content_relevance: "Only send marketing content matching customer's stated interests";
    };
  };
}
```

### Regulatory Compliance

```typescript
interface CommunicationCompliance {
  // Legal requirements for customer communications
  regulations: {
    DPDP_ACT_2023: {
      requirements: [
        "Consent required before sending marketing communications",
        "Clear and easy opt-out mechanism in every marketing message",
        "Honor opt-out within 48 hours",
        "Record consent with timestamp and method",
        "Customer can request all communication data held",
      ];
    };

    TRAI_DND: {
      description: "TRAI Do Not Disturb registry";
      requirements: [
        "Check DND registry before sending promotional SMS/calls",
        "Transactional messages exempt from DND",
        "WhatsApp marketing messages require opt-in (not covered by DND but by platform policy)",
      ];
    };

    WHATSAPP_POLICY: {
      requirements: [
        "24-hour messaging window for free-form messages after customer-initiated contact",
        "Pre-approved message templates for outbound messages outside 24-hour window",
        "Customer must initiate conversation or opt-in to receive WhatsApp business messages",
        "No spam or unsolicited messages — WhatsApp can ban business accounts",
      ];
    };

    UNSUBSCRIBE_MANAGEMENT: {
      mechanism: "'Reply STOP to unsubscribe' in every marketing message";
      processing: "Unsubscribe processed within 48 hours; added to suppression list";
      granular: "Customer can unsubscribe from marketing while keeping transactional messages";
      re_subscribe: "Customer can resubscribe via preference center or by messaging agent";
    };
  };
}
```

---

## Open Problems

1. **Preference vs. best practice** — Customers who disable all reminders then miss payment deadlines and blame the agency. Need a balance: critical items (payment, documents) should always notify, even if the customer has reduced frequency.

2. **Cross-channel coordination** — Sending a WhatsApp message AND an email AND an SMS for the same reminder is spam. The system must choose the best channel based on customer preference and past engagement.

3. **WhatsApp template approval** — WhatsApp Business API requires pre-approved message templates for outbound messages. Customizing messages per customer is limited by template flexibility. Transactional templates (booking confirmation) are pre-approved; marketing templates need review.

4. **Measuring notification effectiveness** — Did the payment reminder cause the payment, or would the customer have paid anyway? Attribution of notifications to actions requires tracking links and behavioral analysis.

5. **Generational preferences** — Younger customers prefer WhatsApp and app notifications; older customers prefer phone calls and email. Default preferences should be set based on customer demographics, then refined by behavior.

---

## Next Steps

- [ ] Build communication preference center for customer portal and companion app
- [ ] Create smart notification engine with channel selection and scheduling
- [ ] Implement quiet hours and frequency controls
- [ ] Design unsubscribe management with granular opt-out
- [ ] Build notification analytics with engagement and attribution tracking
