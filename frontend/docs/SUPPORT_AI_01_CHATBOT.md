# Customer Support AI — Chatbot & Self-Service Engine

> Research document for AI-powered customer support, chatbot architecture, FAQ automation, intelligent ticket routing, self-service resolution, and support analytics for the Waypoint OS platform.

---

## Key Questions

1. **How do we build an AI chatbot for travel customer support?**
2. **What customer queries can be automated vs. need human agents?**
3. **How does intelligent ticket routing work?**
4. **What self-service capabilities reduce agent workload?**

---

## Research Areas

### Support Chatbot Architecture

```typescript
interface SupportChatbot {
  // AI-powered customer support chatbot
  architecture: {
    INTENT_CLASSIFICATION: {
      description: "Classify customer message into intent categories";
      model: "Fine-tuned classifier (BERT/DistilBERT) or LLM-based intent extraction";
      intent_categories: {
        BOOKING_STATUS: {
          examples: ["Where is my booking confirmation?", "Is my hotel booked?", "Show my itinerary"];
          automation: "95% automated — query system → return status";
          escalation: "If booking not found → route to agent with context";
        };

        ITINERARY_CHANGE: {
          examples: ["Can I change my dates?", "I want to add one more day", "Change my hotel"];
          automation: "40% automated (simple date changes within policy) → 60% agent-assisted";
          pre_processing: "Check change policy → show options → if complex, hand off with summary";
        };

        PAYMENT_QUERY: {
          examples: ["How much do I still owe?", "Did you receive my payment?", "Send me payment link"];
          automation: "85% automated — query payment system → return balance/link";
          escalation: "Payment dispute → agent with payment history attached";
        };

        VISA_STATUS: {
          examples: ["What's my visa status?", "Do I need a visa for Thailand?", "Track my visa application"];
          automation: "70% automated — requirement check + status lookup";
        };

        TRIP_QUESTION: {
          examples: ["What's the weather in Singapore in June?", "Do I need an adapter?", "Is tap water safe?"];
          automation: "90% automated — answer from destination knowledge base";
        };

        COMPLAINT: {
          examples: ["The hotel was terrible", "My flight was cancelled and no one told me", "I want a refund"];
          automation: "10% — acknowledge + collect details → route to agent with priority";
          handling: "AI detects complaint sentiment → immediate priority flag + empathetic acknowledgment";
        };

        EMERGENCY: {
          examples: ["I lost my passport", "I need medical help", "There's a natural disaster"];
          automation: "0% — detect emergency → immediate human agent + emergency protocol";
          detection: "Keywords + urgency scoring → bypass all queues";
        };

        GENERAL_INQUIRY: {
          examples: ["What destinations do you cover?", "How much does a Singapore trip cost?", "Do you do group bookings?"];
          automation: "80% automated — answer from FAQ/knowledge base";
        };
      };
    };

    CONVERSATION_FLOW: {
      description: "How chatbot handles multi-turn conversations";
      flow: {
        greeting: "Hi {name}! I'm your travel assistant. How can I help today?";
        intent_detection: "Classify first message → route to appropriate handler";
        context_maintenance: "Remember conversation context across turns (trip ID, customer ID)";
        escalation_trigger: "If 3+ failed attempts or customer types 'agent' → hand off to human";
        handoff_protocol: {
          message: "Let me connect you with {agent_name} who can help with this.";
          context_transfer: "Full conversation history + detected intent + customer profile + trip details";
          seamless: "Agent picks up without customer repeating anything";
        };
      };
    };
  };

  // ── Chatbot conversation example ──
  // ┌─────────────────────────────────────────────────────┐
  // │  🤖 Travel Assistant · WhatsApp                          │
  // │                                                       │
  // │  Customer: Hi, when is my Singapore trip?             │
  // │                                                       │
  // │  🤖 Hi Mr. Sharma! Your Singapore trip is Jun 15-20.     │
  // │  Here's a quick summary:                                  │
  // │  ✈️ Flight: IndiGo 6E-37 · Jun 15, 8:15 AM              │
  // │  🏨 Hotel: Grand Mercure · 5 nights                       │
  // │  💰 Balance: ₹42,000 (due Jun 1)                         │
  // │                                                       │
  // │  What would you like to know more about?              │
  // │  [Itinerary] [Payment] [Documents] [Weather]              │
  // │                                                       │
  // │  Customer: weather                                    │
  // │                                                       │
  // │  🤖 Singapore in June:                                    │
  // │  🌡️ 26-32°C · Humidity: 80-85%                            │
  // │  🌧️ Rain expected: Brief afternoon showers common         │
  // │  👕 Pack: Light cotton clothes + umbrella                 │
  // │  ☀️ UV: High — bring sunscreen (SPF 50+)                 │
  // │                                                       │
  // │  Need anything else?                                  │
  // │  [View Full Itinerary] [Pay Balance] [Talk to Agent]      │
  // └─────────────────────────────────────────────────────┘
}

### Self-Service Capabilities

```typescript
interface SelfServiceCapabilities {
  // Customer self-service without agent involvement
  capabilities: {
    ITINERARY_ACCESS: {
      description: "View full itinerary with all confirmations, vouchers, tickets";
      access: "WhatsApp link or app — authenticated by phone number";
      content: ["Day-by-day schedule", "Hotel vouchers with QR codes", "Flight e-tickets", "Activity confirmations", "Transfer details with driver contact"];
      automation: "100% self-service";
    };

    PAYMENT_MANAGEMENT: {
      description: "View balance, make payments, download invoices";
      capabilities: {
        view_balance: "Show outstanding amount and due date";
        make_payment: "Payment link via Razorpay/PhonePe (UPI, card, net banking)";
        download_invoice: "PDF invoice with GST details";
        payment_history: "All payments made with dates and amounts";
        emi_options: "Show EMI availability for qualifying amounts";
      };
      automation: "90% self-service (only disputes need agent)";
    };

    DOCUMENT_UPLOAD: {
      description: "Upload passport, visa documents, ID proofs";
      mechanism: "WhatsApp photo/document → OCR extraction → verify → store encrypted";
      use_case: "Visa document submission, identity verification, insurance claims";
      automation: "70% automated (OCR + validation) → 30% manual review";
    };

    TRIP_MODIFICATION_REQUEST: {
      description: "Request changes to confirmed bookings";
      flow: {
        step_1: "Customer selects what to change (dates, hotel, activities)";
        step_2: "System checks modification policy and availability";
        step_3: "Show options with price impact (if any)";
        step_4: "Customer confirms → system processes or routes to agent";
      };
      automation: "30% (simple changes like activity swap) → 70% agent-assisted";
    };

    FEEDBACK_SUBMISSION: {
      description: "Rate trip, leave review, report issues";
      mechanism: "Post-trip WhatsApp survey (3 questions) or detailed feedback form";
      automation: "100% self-service";
      routing: "NPS < 7 → auto-route to retention team; complaint → agent priority queue";
    };
  };

  // Self-service metrics
  self_service_metrics: {
    target_resolution_rate: "70% of customer queries resolved without agent";
    current_channels: {
      whatsapp_bot: "60% of queries start here → 45% resolved by bot";
      app_portal: "25% self-service via app → 80% resolved without agent";
      phone_call: "15% call directly → 90% need agent involvement";
    };
    resolution_by_type: {
      booking_status: "95% automated";
      payment: "85% automated";
      trip_questions: "90% automated";
      itinerary_changes: "30% automated";
      complaints: "10% automated";
      emergencies: "0% automated (always human)";
    };
  };
}

// ── Self-service portal ──
// ┌─────────────────────────────────────────────────────┐
// │  Self-Service — Sharma Family · Singapore Trip             │
// │                                                       │
// │  What would you like to do?                           │
// │                                                       │
// │  📋 View Itinerary (with all vouchers & tickets)          │
// │  💰 Make Payment · Balance: ₹42,000 due Jun 1             │
// │  📄 Upload Documents (passport, visa photos)               │
// │  🔄 Request Change (dates, hotel, activities)              │
// │  📊 Trip Budget Tracker (₹68K of ₹1.2L spent)             │
// │  ⭐ Leave Feedback · Download Invoice                     │
// │  📞 Contact Agent (Priya · Last chat: 2h ago)             │
// │                                                       │
// │  Quick answers:                                       │
// │  ❓ Do I need a visa for Singapore? → Yes, e-visa         │
// │  ❓ What time is my flight? → IndiGo 6E-37, 8:15 AM       │
// │  ❓ Hotel check-in time? → 3:00 PM                          │
// │                                                       │
// │  💬 Chat with Assistant                                    │
// └─────────────────────────────────────────────────────┘
```

### Intelligent Ticket Routing & Support Analytics

```typescript
interface TicketRoutingAndAnalytics {
  // Smart routing and support performance tracking
  ticket_routing: {
    CLASSIFICATION: {
      automatic: "AI classifies incoming message into category + urgency + sentiment";
      categories: ["booking_status", "payment", "modification", "complaint", "emergency", "general"];
      urgency_levels: {
        CRITICAL: "Emergency, safety, medical → immediate human response";
        HIGH: "Active trip issue, payment dispute → respond within 30 min";
        MEDIUM: "Pre-trip question, document request → respond within 2 hours";
        LOW: "General inquiry, feedback → respond within 4 hours";
      };
      sentiment: {
        positive: "Smooth query → bot handles or low-priority agent";
        neutral: "Standard query → route by category";
        negative: "Frustrated customer → priority agent with empathy guidance";
        angry: "Escalation risk → senior agent + owner notification";
      };
    };

    ROUTING_RULES: {
      specialist_matching: "Visa queries → visa specialist; luxury trips → senior agent; corporate → corporate manager";
      load_balancing: "Distribute tickets across agents based on current load (not just round-robin)";
      language_matching: "Hindi query → Hindi-speaking agent; regional language → appropriate agent";
      customer_history: "Repeat caller → same agent who handled before (continuity)";
    };
  };

  support_analytics: {
    AGENT_PERFORMANCE: {
      metrics: {
        avg_response_time: "Time from customer message to first agent response";
        avg_resolution_time: "Time from ticket creation to resolution";
        first_contact_resolution: "Tickets resolved in single interaction (target: 70%+)";
        customer_satisfaction: "Post-interaction rating (target: 4.5+/5)";
        escalation_rate: "Tickets escalated to senior/owner (target: <10%)";
      };
    };

    BOT_PERFORMANCE: {
      metrics: {
        intent_accuracy: "Correct intent classification rate (target: 90%+)";
        self_service_rate: "Queries resolved without human (target: 70%)";
        handoff_rate: "Conversations handed to agent (target: <30%)";
        false_positive_automation: "Bot answers incorrectly but confidently (target: <2%)";
      };
    };

    VOLUME_PATTERNS: {
      peak_hours: "9-11 AM and 7-9 PM (before/after business hours)";
      peak_days: "Monday (weekend follow-ups), day after holidays";
      seasonal: "Oct-Feb: 3x volume (peak travel season)";
      trip_day_spikes: "Day 1 of trips (check-in issues) and last day (checkout questions)";
    };
  };
}
```

---

## Open Problems

1. **Bot hallucination risk** — AI chatbots may confidently give wrong answers (e.g., incorrect visa requirements, wrong hotel check-in time). Need grounding in verified knowledge base with confidence scoring and fallback to human for uncertain answers.

2. **Escalation detection** — Recognizing when a customer is frustrated (despite polite words) requires sentiment analysis beyond keyword matching. False negatives (missed frustration) damage relationships; false positives (unnecessary agent escalation) waste resources.

3. **Multi-language support** — Indian customers may mix Hindi and English in the same message. "Mera payment ho gaya but confirmation nahi aaya" requires bilingual understanding. Current models handle this imperfectly.

4. **Self-service adoption** — Customers who are used to calling their agent may resist self-service. Need to make the bot experience so good that customers prefer it over waiting for a human.

---

## Next Steps

- [ ] Build intent classification model for travel support queries
- [ ] Design chatbot conversation flows with escalation triggers
- [ ] Create self-service portal with payment and itinerary access
- [ ] Implement intelligent ticket routing with load balancing
