# On-Demand Travel Support — Real-Time Agent Availability

> Research document for on-demand travel support, real-time agent availability, instant support channels, live chat, emergency hotline, and always-on customer assistance for the Waypoint OS platform.

---

## Key Questions

1. **How do we provide real-time support to active travelers?**
2. **What channels deliver instant assistance?**
3. **How does on-demand support scale without 24/7 staffing?**
4. **What's the balance between automated and human support?**

---

## Research Areas

### On-Demand Support Architecture

```typescript
interface OnDemandSupport {
  // Real-time travel assistance for active and prospective customers
  support_channels: {
    LIVE_CHAT: {
      description: "Instant chat with available agent via companion app or website";
      availability: "8 AM - 10 PM IST daily (extended hours during peak season)";
      response_time: "<30 seconds to connect; <2 minutes for first meaningful response";
      capabilities: ["Answer trip questions", "Modify itinerary", "Book add-on services", "Handle complaints", "Emergency assistance"];
      escalation: "If no agent available within 60 seconds → AI bot handles initial triage → queues for next agent";
    };

    WHATSAPP_INSTANT: {
      description: "WhatsApp message with guaranteed quick response";
      sla: "During business hours: <15 minutes; After hours: <2 hours; Emergency: <5 minutes";
      mechanism: "Auto-acknowledge immediately → route to available agent based on expertise and load";
      features: {
        quick_actions: ["My itinerary", "Change activity", "Emergency help", "Payment status", "Talk to my agent"];
        photo_support: "Customer sends photo of issue (wrong room, damaged item) → agent can see and respond";
        location_share: "Customer shares location → agent provides nearest hospital/ATM/restaurant";
      };
    };

    EMERGENCY_HOTLINE: {
      description: "24/7 phone number for travel emergencies";
      scope: "Safety concerns, medical emergencies, lost passport, stranded travelers ONLY";
      staffed: "Rotating on-call agent + escalation to owner for critical issues";
      response: "Answer within 3 rings; never voicemail during emergency";
      not_for: "Booking inquiries, status checks, general questions — redirect to WhatsApp";
    };

    AI_INSTANT_ASSIST: {
      description: "AI-powered instant answers when agents are unavailable";
      capabilities: {
        faq_answers: "90% accurate for common questions (weather, check-in time, visa status, payment balance)";
        itinerary_info: "Full itinerary access with instant response to 'what's next?' queries";
        emergency_guidance: "Pre-programmed emergency response (nearest hospital, embassy, police)",
        translation: "Common phrases in local language for immediate use",
      };
      handoff: "If AI detects frustration or complexity → immediate transfer to human agent";
      availability: "24/7 — fills the gap when human agents are offline";
    };
  };

  // ── On-demand support — customer view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  💬 Support · Sharma Family · Singapore Day 3              │
  // │                                                       │
  // │  How can we help?                                     │
  // │                                                       │
  // │  [📋 My Itinerary]  [🔄 Change Activity]                    │
  // │  [💰 Payment]       [🆘 Emergency]                          │
  // │  [💬 Chat with Agent] [🤖 Quick Answer]                     │
  // │                                                       │
  // │  Recent:                                              │
  // │  Agent: Today's weather is partly cloudy, 30°C            │
  // │  You: What time is Sentosa Express?                       │
  // │  Agent: Sentosa Express runs every 5-8 min from           │
  // │         VivoCity station. Your entry ticket is             │
  // │         in the Documents section. Have fun! 🌴             │
  // │                                                       │
  // │  Agent available: Priya · Last reply: 3 min ago           │
  // │  [Type message...                                         │
  // └─────────────────────────────────────────────────────────┘
}
```

### Agent Availability & Routing

```typescript
interface AgentAvailabilityRouting {
  // Managing agent availability for on-demand support
  scheduling: {
    BUSINESS_HOURS: {
      hours: "8 AM - 10 PM IST, 7 days a week";
      coverage: "All agents share support duty on rotation";
      load_balancing: "Incoming support requests distributed by agent availability and expertise";
    };

    AFTER_HOURS: {
      hours: "10 PM - 8 AM IST";
      coverage: "1 on-call agent for emergencies; AI handles non-urgent queries";
      escalation: "On-call agent responds within 30 minutes; owner escalation for critical";
      compensation: "On-call agent receives additional compensation (₹500-1,000/night on duty)";
    };

    PEAK_SEASON: {
      coverage: "Extended hours (7 AM - 11 PM); additional on-call agents";
      staffing: "Temporary support staff or overtime for permanent agents";
    };
  };

  routing_rules: {
    PRIORITY_ROUTING: {
      emergency: "Routes to on-call agent immediately regardless of other queues";
      active_trip: "Customer currently traveling → priority over pre-trip inquiries";
      repeat_customer: "Customer who booked 3+ times → priority routing";
      complaint: "Customer with open complaint → routed to same agent handling the complaint";
    };

    EXPERTISE_MATCHING: {
      rules: [
        "Visa question → visa specialist agent",
        "Accessible travel → agent trained in accessible travel",
        "Corporate trip → corporate travel manager",
        "Language preference → Hindi/English/regional language matching",
      ];
    };

    CONTINUITY: {
      rule: "Returning customer → same agent who handled before (when available)";
      benefit: "Customer doesn't re-explain their situation; agent has full context";
    };
  };
}
```

### Support Metrics

```typescript
interface SupportMetrics {
  metrics: {
    RESPONSE_TIME: {
      target: "<30 seconds for live chat; <15 min for WhatsApp; <5 min for emergency";
      measurement: "Time from customer message to first meaningful agent response";
    };

    RESOLUTION_TIME: {
      target: "80% of issues resolved in first interaction (first-contact resolution)";
      measurement: "Time from support request to confirmed resolution";
    };

    CUSTOMER_SATISFACTION: {
      target: "4.5+/5 post-interaction rating";
      measurement: "Survey after each support interaction";
    };

    CHANNEL_DISTRIBUTION: {
      targets: {
        whatsapp: "60% of support interactions (primary channel)",
        live_chat: "20% (companion app users)",
        phone: "15% (emergencies and complex issues)",
        ai_bot: "5% (after-hours and simple queries resolved without human)",
      };
    };

    AGENT_UTILIZATION: {
      target: "70-80% utilization during shift (not idle, not overwhelmed)";
      measurement: "Time spent on active support vs. available-for-support";
    };
  };
}
```

---

## Open Problems

1. **24/7 staffing cost** — True 24/7 coverage requires 3-4 shifts of agents, which is expensive for small agencies. AI-assisted after-hours support with emergency-only human escalation is the practical solution.

2. **Agent burnout** — Support duty (especially on-call) is demanding. Rotating on-call fairly and compensating adequately prevents burnout and resentment.

3. **Multi-timezone challenges** — A customer in Singapore (IST +2:30) calling at 10 PM local time is calling at 7:30 PM IST. Support hours must account for destination time zones, not just IST.

4. **AI vs. human handoff** — A poorly executed handoff from AI to human ("I can't help, transferring you...") is frustrating. The human must receive full context so the customer doesn't repeat themselves.

5. **Quality vs. speed** — Pressure to respond quickly can lead to rushed, inaccurate responses. Agent training should emphasize "correct in 2 minutes" over "fast but wrong in 30 seconds."

---

## Next Steps

- [ ] Build multi-channel support hub with live chat, WhatsApp, and emergency hotline
- [ ] Create agent availability scheduling with rotation and on-call management
- [ ] Implement AI instant-assist for after-hours and overflow support
- [ ] Design support routing with priority, expertise, and continuity rules
- [ ] Build support analytics dashboard with response and resolution tracking
