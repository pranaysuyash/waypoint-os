# Customer Journey Orchestration — Touchpoint Design & Channel Strategy

> Research document for designing optimal touchpoints, channel selection, message timing, and experience consistency across the customer journey.

---

## Key Questions

1. **How do we design optimal touchpoints for each journey stage?**
2. **What channel strategy maximizes engagement for Indian travelers?**
3. **How do we ensure message consistency across channels?**
4. **What timing and frequency prevents annoyance while maintaining engagement?**
5. **How do we measure touchpoint effectiveness?**

---

## Research Areas

### Touchpoint Design System

```typescript
interface TouchpointDesign {
  library: TouchpointLibrary[];
  templates: TouchpointTemplate[];
  personalization: TouchpointPersonalization;
  scheduling: TouchpointScheduler;
}

interface TouchpointLibrary {
  stage: JourneyStageType;
  touchpoints: Touchpoint[];
}

interface Touchpoint {
  id: string;
  name: string;                        // "Pre-trip weather update"
  stage: JourneyStageType;
  trigger: TouchpointTrigger;
  channel: Channel;
  content: TouchpointContent;
  timing: TouchpointTiming;
  metrics: TouchpointMetric[];
}

// Touchpoint catalog by stage:
//
// AWARENESS (5 touchpoints):
// ─────────────────────────────────────────
// T1: Social media post — destination inspiration
//     Channel: Instagram, Facebook
//     Frequency: 3-5x per week
//     Goal: Drive inquiry
//
// T2: SEO landing page — "Best time to visit Kerala"
//     Channel: Website
//     Frequency: Always available
//     Goal: Capture search traffic
//
// T3: WhatsApp catalog — destination packages
//     Channel: WhatsApp Business
//     Frequency: On request
//     Goal: Share options quickly
//
// T4: Referral program — "Share with friends"
//     Channel: WhatsApp (forwarded)
//     Frequency: Post-trip
//     Goal: Word of mouth
//
// T5: Festival campaign — "Diwali getaway ideas"
//     Channel: WhatsApp, Email, Social
//     Frequency: Seasonal
//     Goal: Timely inspiration

// CONSIDERATION (8 touchpoints):
// ─────────────────────────────────────────
// T1: Welcome message — "Hi! I'm [agent], how can I help?"
//     Channel: WhatsApp
//     Timing: <2 min after inquiry
//     Goal: First response, build trust
//
// T2: Destination guide — "Here's everything about Kerala"
//     Channel: WhatsApp (PDF + images)
//     Timing: Within 1 hour of inquiry
//     Goal: Demonstrate expertise
//
// T3: Personalized recommendation — "Based on your preferences..."
//     Channel: WhatsApp
//     Timing: 4-8 hours after inquiry
//     Goal: Show personalization
//
// T4: Price comparison — "Why book with us vs OTA"
//     Channel: WhatsApp
//     Timing: When customer mentions OTA comparison
//     Goal: Differentiate value
//
// T5: Follow-up — "Any questions about the itinerary?"
//     Channel: WhatsApp
//     Timing: 24 hours after last message (if no response)
//     Goal: Keep conversation going
//
// T6: Customization offer — "Want to add a houseboat?"
//     Channel: WhatsApp
//     Timing: During itinerary discussion
//     Goal: Upsell and personalize
//
// T7: Social proof — "Here's what Rajesh said about his trip"
//     Channel: WhatsApp (screenshot/review)
//     Timing: When customer hesitates
//     Goal: Build confidence
//
// T8: Urgency trigger — "Only 2 rooms left at this price"
//     Channel: WhatsApp
//     Timing: When real availability constraint exists
//     Goal: Encourage booking decision

// BOOKING (6 touchpoints):
// ─────────────────────────────────────────
// T1: Detailed quote — Full price breakdown
//     Channel: WhatsApp + Email (PDF)
//     Timing: After customer confirms interest
//     Goal: Transparent pricing
//
// T2: Booking confirmation — "Your trip is confirmed!"
//     Channel: WhatsApp + Email
//     Timing: Immediately after booking
//     Goal: Reassurance and excitement
//
// T3: Payment link — Easy UPI/card payment
//     Channel: WhatsApp
//     Timing: With booking confirmation
//     Goal: Frictionless payment
//
// T4: Payment receipt — "Payment received ₹X"
//     Channel: WhatsApp + Email
//     Timing: Immediately after payment
//     Goal: Confirmation and trust
//
// T5: Itinerary delivery — "Here's your complete itinerary"
//     Channel: Email (PDF) + WhatsApp (summary)
//     Timing: 1-2 days after full payment
//     Goal: Trip feels real
//
// T6: Add-on suggestions — "Want to add travel insurance?"
//     Channel: WhatsApp
//     Timing: After booking, before travel
//     Goal: Upsell services

// PREPARATION (7 touchpoints):
// ─────────────────────────────────────────
// T1: Welcome to your trip — WhatsApp group creation
//     Channel: WhatsApp
//     Timing: 7 days before departure
//     Goal: Communication channel established
//
// T2: Document checklist — Visa, passport, insurance
//     Channel: WhatsApp (checklist image)
//     Timing: 7 days before departure
//     Goal: Ensure readiness
//
// T3: Weather update — "Expect 28°C in Kochi"
//     Channel: WhatsApp
//     Timing: 3 days before departure
//     Goal: Packing preparation
//
// T4: Hotel & driver contacts — "Your driver: Rahul, +91-..."
//     Channel: WhatsApp
//     Timing: 1 day before departure
//     Goal: Last-mile readiness
//
// T5: Excitement message — "Your Kerala adventure starts tomorrow!"
//     Channel: WhatsApp
//     Timing: Evening before departure
//     Goal: Build excitement
//
// T6: Day-of reminder — "Flight at 8 AM, reach airport by 6"
//     Channel: WhatsApp
//     Timing: Morning of departure (4 hours before)
//     Goal: Practical reminder
//
// T7: WhatsApp group intro — Agent + ground handler + customer
//     Channel: WhatsApp group
//     Timing: 1 day before departure
//     Goal: Support team introduced

// TRAVEL (6 touchpoints):
// ─────────────────────────────────────────
// T1: Arrival check-in — "How was your flight?"
//     Channel: WhatsApp
//     Timing: 2 hours after landing
//     Goal: Show care
//
// T2: Daily plan — "Today: Munnar hill station tour"
//     Channel: WhatsApp
//     Timing: Morning (8 AM local time)
//     Goal: Keep customer informed
//
// T3: Mid-trip check — "How's everything going?"
//     Channel: WhatsApp
//     Timing: Day 3 of 5-day trip
//     Goal: Proactive issue detection
//
// T4: Issue resolution — "We've fixed the AC issue"
//     Channel: WhatsApp
//     Timing: As needed (response <30 min)
//     Goal: Rapid problem solving
//
// T5: Farewell message — "Hope you enjoyed Kerala!"
//     Channel: WhatsApp
//     Timing: Last evening of trip
//     Goal: Positive close
//
// T6: Return journey check — "Safe flight home!"
//     Channel: WhatsApp
//     Timing: Day of return flight
//     Goal: Complete the loop

// POST-TRIP (5 touchpoints):
// ─────────────────────────────────────────
// T1: Welcome back — "Welcome home! How was your trip?"
//     Channel: WhatsApp
//     Timing: Day after return
//     Goal: Show care while memory is fresh
//
// T2: Feedback survey — 3-question WhatsApp survey
//     Channel: WhatsApp
//     Timing: 2 days after return
//     Goal: Collect feedback
//
// T3: Review request — "Would you recommend us?"
//     Channel: WhatsApp (Google review link)
//     Timing: If feedback > 4 stars
//     Goal: Social proof
//
// T4: Photo share — "Share your best trip photos!"
//     Channel: WhatsApp
//     Timing: 3-5 days after return
//     Goal: Engagement + user-generated content
//
// T5: Referral offer — "Share ₹2000 off with friends"
//     Channel: WhatsApp
//     Timing: 1 week after return (if satisfied)
//     Goal: Word of mouth acquisition
```

### Channel Strategy

```typescript
interface ChannelStrategy {
  channels: ChannelConfig[];
  routing: ChannelRouting;
  consistency: CrossChannelConsistency;
  preferences: ChannelPreferences;
}

// Channel effectiveness matrix for Indian travel customers:
// ─────────────────────────────────────────
// Channel      | Open Rate | Response | Best For              | Cost
// ──────────────────────────────────────────────────────────────────
// WhatsApp     | 95%       | 80%      | Everything (default)  | ₹0.5-2/msg
// SMS          | 90%       | 25%      | Confirmations, OTP    | ₹0.1-0.3/msg
// Email        | 25%       | 5%       | Documents, itineraries| ₹0.01/msg
// Phone call   | 70%       | 90%      | Complex discussions   | ₹1-3/min
// Push notif   | 40%       | 10%      | In-app reminders      | Free
// In-app       | 60%       | 15%      | Dashboard alerts      | Free
// ─────────────────────────────────────────
//
// Channel selection rules:
// 1. DEFAULT: WhatsApp (highest engagement in India)
// 2. DOCUMENTS: Email (PDF attachments, better printing)
// 3. URGENT: Phone call (SOS, payment overdue, flight change)
// 4. CONFIRMATION: SMS (payment receipt, booking confirmation)
// 5. IN-APP: Push notification (when app is open)
//
// Channel escalation:
// WhatsApp (no response in 2h) → Phone call (if urgent)
// Email (no open in 24h) → WhatsApp summary
// In-app (not seen in 4h) → Push notification

// Message frequency caps:
// ─────────────────────────────────────────
// Stage         | Max per day | Max per week
// ─────────────────────────────────────────
// Awareness     | 1           | 3
// Consideration | 3           | 10
// Booking       | 5           | 15
// Preparation   | 2           | 7
// Traveling     | 3           | 15 (daily check-ins)
// Post-trip     | 1           | 3
// Dormant       | 1           | 2 (win-back only)
// ─────────────────────────────────────────
//
// Frequency rules:
// - Never send >3 messages without customer response
// - If customer hasn't responded to 2 messages → Pause 24h
// - Marketing messages capped at 2 per week
// - Transactional messages (booking, payment) excluded from caps
// - WhatsApp Business API has per-customer daily limits (varies by tier)

// Cross-channel consistency:
// ┌─────────────────────────────────────────┐
// │  Message Consistency Check               │
// │                                            │
// │  Trip: Kerala December (TRV-45678)        │
// │                                            │
// │  WhatsApp: "Your trip is confirmed!"      │
// │  Email:    "Booking Confirmation"          │
// │  SMS:      "Trip TRV-45678 confirmed"     │
// │  In-app:   "Kerala trip confirmed"        │
// │                                            │
// │  ✅ All channels convey same status        │
// │  ✅ Timing: WhatsApp → Email → SMS (staggered)│
// │  ✅ Each adds value (WhatsApp=excitement, │
// │     Email=details, SMS=quick reference)   │
// │                                            │
// │  ❌ Avoid: Sending identical message on    │
// │     all channels simultaneously            │
// └─────────────────────────────────────────────┘
```

### Touchpoint Analytics

```typescript
interface TouchpointAnalytics {
  metrics: TouchpointMetric[];
  effectiveness: TouchpointEffectiveness;
  optimization: TouchpointOptimization;
}

// Touchpoint effectiveness tracking:
// ┌─────────────────────────────────────────┐
// │  Touchpoint Performance — Last 30 Days    │
// │                                            │
// │  Top Performers:                           │
// │  1. Welcome message — 92% response rate   │
// │  2. Booking confirmation — 88% open rate  │
// │  3. Daily travel plan — 85% read rate     │
// │                                            │
// │  Needs Improvement:                        │
// │  1. Feedback survey — 35% completion       │
// │  2. Review request — 12% click-through    │
// │  3. Referral offer — 5% share rate         │
// │                                            │
// │  Journey Impact:                           │
// │  Customers with 5+ touchpoints: 82% satisfaction│
// │  Customers with <3 touchpoints: 58% satisfaction│
// │                                            │
// │  Channel Comparison:                       │
// │  WhatsApp: 85% read, 65% response          │
// │  Email: 28% open, 8% click                 │
// │  SMS: 92% delivered, 18% response          │
// │                                            │
// │  Optimization Suggestions:                 │
// │  • Feedback survey: Shorten to 1 question  │
// │  • Review request: Add incentive (₹500 off)│
// │  • Referral: Make sharing one-tap          │
// └─────────────────────────────────────────────┘
```

---

## Open Problems

1. **WhatsApp template approval** — WhatsApp Business API requires pre-approved message templates. Custom personalized messages hit rate limits. Balancing template rigidity with personalization is a constant challenge.

2. **Optimal frequency** — Too few touchpoints feel like abandonment; too many feel like spam. The right frequency varies by customer segment, journey stage, and individual preference. A/B testing is needed but risks annoying real customers.

3. **Channel attribution** — When a customer books after receiving WhatsApp, email, and SMS, which channel gets credit? Multi-touch attribution models are complex and often misleading.

4. **Cultural tone sensitivity** — The same message can feel warm to one customer and intrusive to another. Indian communication norms vary widely by region, age, and social class. Tone adaptation is hard to automate.

5. **Message fatigue during travel** — Daily check-ins are valuable but can feel overbearing. Some travelers want to be left alone. Reading customer preference for communication frequency during travel is difficult.

---

## Next Steps

- [ ] Build touchpoint library with per-stage templates and triggers
- [ ] Create channel strategy engine with frequency caps and escalation rules
- [ ] Implement cross-channel consistency checker for message coherence
- [ ] Design touchpoint analytics with effectiveness scoring and optimization
- [ ] Study journey orchestration (Braze, MoEngage, WebEngage, CleverTap)
