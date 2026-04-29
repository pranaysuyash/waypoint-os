# WhatsApp Business Platform — Agent Toolkit & Workflows

> Research document for the agent WhatsApp toolkit, message templates, quick replies, agent handoff, and the unified inbox for managing all WhatsApp conversations.

---

## Key Questions

1. **What tools do agents need to manage WhatsApp conversations?**
2. **How do quick replies and templates speed up responses?**
3. **How does agent handoff work for complex conversations?**
4. **What does the unified WhatsApp inbox look like?**

---

## Research Areas

### Unified WhatsApp Inbox

```typescript
interface UnifiedWhatsAppInbox {
  // Single inbox for all WhatsApp conversations
  inbox: {
    // Conversation list
    conversations: {
      phone: string;
      customer_name: string | null;
      customer_id: string | null;
      trip_ids: string[];

      // Status
      status: "UNREAD" | "NEEDS_REPLY" | "WAITING_CUSTOMER" | "RESOLVED";
      priority: "URGENT" | "HIGH" | "NORMAL" | "LOW";
      assigned_agent: string | null;

      // Context
      last_message: string;
      last_message_time: string;
      last_message_by: "CUSTOMER" | "AGENT" | "SYSTEM";
      window_expires: string | null;

      // Quick tags
      tags: string[];                     // ["hot_lead", "payment_pending", "complaint"]
    }[];

    // Filters
    filters: {
      status: string;
      assigned_to: string;
      priority: string;
      tags: string[];
      trip_id: string;
      window_status: "ACTIVE" | "EXPIRING_SOON" | "EXPIRED";
    };
  };
}

// ── Unified WhatsApp inbox ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Inbox · 23 conversations                      │
// │                                                       │
// │  Filter: [All ▼] [Mine ▼] [Priority ▼] [Tag ▼]        │
// │                                                       │
// │  🔴 UNREAD (4)                                        │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ +91-98XXX-XXXX · New lead · 5 min ago          │   │
// │  │ "Singapore trip chahiye" · Priority: HIGH       │   │
// │  │ [Assign to Me] [Auto-Reply]                      │   │
// │  │                                               │   │
// │  │ +91-97XXX-XXXX · Sharma (WP-442) · 12 min ago  │   │
// │  │ "Universal mein crowd tha" · Priority: HIGH     │   │
// │  │ Trip: Active (Day 3) · Assigned: Priya          │   │
// │  │ [Open Conversation]                              │   │
// │  │                                               │   │
// │  │ +91-96XXX-XXXX · Gupta (WP-448) · 30 min ago   │   │
// │  │ "Payment done!" · Priority: NORMAL              │   │
// │  │ Trip: Confirmed · Assigned: Rahul               │   │
// │  │ [Open Conversation]                              │   │
// │  │                                               │   │
// │  │ +91-95XXX-XXXX · Unknown · 45 min ago           │   │
// │  │ "Dubai honeymoon package price?" · Priority: NORM│  │
// │  │ [Assign to Me] [Quick Match CRM]                 │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ⏰ WINDOW EXPIRING (2)                               │
// │  • +91-94XXX-XXXX — 45min remaining                   │
// │  • +91-93XXX-XXXX — 1h 20min remaining                │
// │                                                       │
// │  ✅ RESOLVED (17)                                     │
// │  17 conversations handled today                        │
// │                                                       │
// │  [Auto-Distribute] [Bulk Actions] [Analytics]           │
// └─────────────────────────────────────────────────────┘
```

### Quick Reply & Template System

```typescript
interface AgentQuickReplies {
  // Categorized quick replies for agents
  categories: {
    GREETING: {
      replies: [
        { shortcut: "/hi"; text: "Hi {name}! 👋 How can I help you today?"; language: "EN" },
        { shortcut: "/namaste"; text: "Namaste {name} ji! 🙏 Kaise madad karun?"; language: "HI" },
      ];
    };

    QUALIFYING: {
      replies: [
        { shortcut: "/budget"; text: "Budget kitna rakha hai aur dates fix hain ya flexible?" },
        { shortcut: "/travelers"; text: "Kitne log travel karenge? Adults aur kids count?" },
        { shortcut: "/destinations"; text: "Kahan jana hai? Koi specific destination ya explore karna hai?" },
      ];
    };

    PRICING: {
      replies: [
        { shortcut: "/quote"; text: "Yeh raha aapka personalized quote. 2 options hain — [attach proposal image]" },
        { shortcut: "/discount"; text: "Main {amount} tak discount de sakti hoon agar aaj confirm karte hain. Kya booking karein?" },
        { shortcut: "/emi"; text: "EMI option available hai! 3 installments mein pay karein. Details: [payment plan]" },
      ];
    };

    DOCUMENTS: {
      replies: [
        { shortcut: "/docsneeded"; text: "Your {destination} trip ke liye yeh documents chahiye:\n\n✅ Passport copy\n✅ 2 photos\n✅ Bank statement (3 months)\n✅ {additional_docs}\n\nUpload link: {link}" },
        { shortcut: "/visastatus"; text: "Visa status check kar rahi hoon... [auto-populated status]" },
      ];
    };

    TRIP_SUPPORT: {
      replies: [
        { shortcut: "/weather"; text: "Aaj {city} mein {weather} hai. Temperature: {temp}°C. {advice}" },
        { shortcut: "/directions"; text: "{venue} ka address: {address}\n\nGoogle Maps: {map_link}\nPickup time: {time}" },
        { shortcut: "/emergency"; text: "Emergency contacts for {destination}:\n🚑 Ambulance: {emergency}\n🚔 Police: {police}\n🏨 Hotel: {hotel_phone}\n💬 Agent: {agent_phone}" },
      ];
    };

    CLOSING: {
      replies: [
        { shortcut: "/booked"; text: "🎉 Booking confirmed! Payment received. Itinerary bhejungi shortly. Koi sawal ho toh yehi message karein!" },
        { shortcut: "/followup"; text: "Theek hai {name}, main {time} tak follow-up karungi. Tab tak koi sawal ho toh message karein!" },
        { shortcut: "/thanks"; text: "Thank you {name}! Aapki trip kal se start ho rahi hai. Packing tip: {tip}. Safe travels! ✈️" },
      ];
    };
  };
}

// ─- Quick reply toolbar ──
// ┌─────────────────────────────────────────────────────┐
// │  Conversation: Sharma (+91-97XXX-XXXX)                  │
// │  Trip: WP-442 Singapore · Day 3/5                       │
// │                                                       │
// │  [12:45 PM] Sharma: "Universal Studios mein crowd        │
// │             bahut tha, kuch rides nahi kar paye"         │
// │                                                       │
// │  ┌─ AI Suggested Replies ─────────────────────────┐  │
// │  │ 1. "Sorry to hear! Main alternative arrange     │  │
// │  │     kar rahi hoon. Night Safari VIP tickets      │  │
// │  │     available hain — kids ko bahut pasand        │  │
// │  │     aayengi!"                                    │  │
// │  │                                                 │  │
// │  │ 2. "Oh no! Kal main VIP access arrange kar      │  │
// │  │     sakti hoon Universal ke liye. Ya phir        │  │
// │  │     Adventure Cove try karein?"                  │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  Quick Replies:                                       │
// │  [/weather] [/directions] [/emergency] [/docsneeded]    │
// │  [/quote] [/booked] [/thanks] [+ More]                 │
// │                                                       │
// │  Type message...                              [Send]    │
// └─────────────────────────────────────────────────────┘
```

### Agent Handoff Protocol

```typescript
interface ConversationHandoff {
  // Transfer conversation between agents
  handoff_types: {
    EXPERTISE_TRANSFER: {
      trigger: "Customer asks about destination agent doesn't handle";
      protocol: [
        "Agent A: 'Let me connect you with our {destination} specialist'",
        "Transfer conversation with context summary",
        "Agent B receives: customer profile + trip context + conversation history",
        "Agent B: 'Hi {name}, I'm {agent}, your {destination} specialist!'",
      ];
      context_transferred: ["Customer profile", "Conversation history", "Active trip details", "Open issues"];
    };

    SHIFT_TRANSFER: {
      trigger: "Agent's shift ends, conversation still active";
      protocol: [
        "Auto-detect shift end in 30 minutes for open conversations",
        "Agent creates handoff note",
        "Incoming agent sees note + full context",
        "If customer messages during transfer, auto-reply holds window",
      ];
    };

    ESCALATION_TRANSFER: {
      trigger: "Issue exceeds agent's authority (e.g., major complaint)";
      protocol: [
        "Agent escalates with reason",
        "Manager notified immediately",
        "Conversation stays in same thread",
        "Customer sees: 'I'm connecting you with my manager for the best resolution'",
      ];
    };
  };
}

// ── Conversation handoff ──
// ┌─────────────────────────────────────────────────────┐
// │  Conversation Handoff — Sharma (+91-97XXX-XXXX)         │
// │                                                       │
// │  From: Priya (Morning shift)                            │
// │  To: Rahul (Evening shift)                              │
// │                                                       │
// │  Context:                                              │
// │  • Customer: Rajesh Sharma (TRV-1847)                   │
// │  • Trip: WP-442 Singapore · Day 3 of 5                  │
// │  • Mood: Neutral (disappointed about Universal)          │
// │  • Open issue: Switched to Night Safari, went well       │
// │  • Tomorrow: Gardens by the Bay + Orchid Garden          │
// │  • Payment: Fully paid                                  │
// │  • Special: Kids vegetarian, early flight Day 5          │
// │                                                       │
// │  Agent note: "Sharmas are lovely customers. Day 3 had   │
// │  a hiccup (Universal overcrowded) but resolved well.     │
// │  Send 8 PM check-in. Wake-up call Day 5 at 4 AM."       │
// │                                                       │
// │  [Accept Handoff] [View Full History] [Add Note]         │
// └─────────────────────────────────────────────────────┘
```

### WhatsApp Agent Performance

```typescript
interface WhatsAppAgentMetrics {
  agent_id: string;
  period: string;

  metrics: {
    conversations_handled: number;
    avg_first_response_time_minutes: number;
    avg_resolution_time_minutes: number;
    customer_satisfaction_avg: number;
    conversion_rate: number;              // for sales conversations
    template_usage_rate: number;          // % using templates vs free-text
    quick_reply_usage_rate: number;
    escalation_rate: number;
  };
}

// ── WhatsApp agent performance ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Agent Performance — April 2026                 │
// │                                                       │
// │  Agent    │ Convs │ Avg Resp │ CSAT │ Conv │ Escal │
// │  ─────────────────────────────────────────────────── │
// │  Rahul    │   68  │  8 min   │ 4.7  │ 52%  │  3%   │
// │  Priya    │   72  │ 12 min   │ 4.5  │ 45%  │  5%   │
// │  Amit     │   45  │ 18 min   │ 4.1  │ 35%  │  8%   │
// │  Neha     │   52  │ 14 min   │ 4.3  │ 42%  │  4%   │
// │  ─────────────────────────────────────────────────── │
// │  Team avg │  237  │ 13 min   │ 4.4  │ 44%  │  5%   │
// │                                                       │
// │  Best practices from Rahul (top performer):           │
// │  • Uses quick replies 60% of the time                 │
// │  • Responds within 5 min for active trips              │
// │  • Sends visual proposals within 2 hours               │
// │  • Follows up on unresponsive leads within 24h         │
// │                                                       │
// │  Coaching for Amit (improvement needed):              │
// │  • Response time 38% slower than team avg              │
// │  • Escalation rate 60% above team avg                  │
// │  • Recommend: Practice objection handling quick replies│
// │                                                       │
// │  [Full Report] [Coaching Plan] [Leaderboard]            │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Quick reply overuse** — Agents relying too heavily on templates can sound robotic. Need balance: templates for structure, personalization for connection.

2. **Multi-language conversations** — Same customer may send Hinglish messages. Quick replies need both English and Hindi variants.

3. **Conversation context across sessions** — New agents picking up a conversation need full history without scrolling through hundreds of messages. Need AI-generated conversation summaries.

4. **Template vs. free-text tracking** — Need to track when agents deviate from templates (often for good reason) to improve template quality.

---

## Next Steps

- [ ] Build unified WhatsApp inbox with conversation management
- [ ] Create quick reply system with AI-suggested responses
- [ ] Implement agent handoff protocol with context transfer
- [ ] Design WhatsApp agent performance dashboard with coaching
