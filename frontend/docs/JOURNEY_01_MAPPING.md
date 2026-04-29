# Customer Journey Orchestration — Journey Mapping & Touchpoints

> Research document for end-to-end customer journey mapping, touchpoint identification, journey states, and experience orchestration across the travel lifecycle.

---

## Key Questions

1. **How do we map the complete customer journey from awareness to advocacy?**
2. **What touchpoints define the Indian travel customer experience?**
3. **How do journey states capture where each customer is in their lifecycle?**
4. **What journey orchestration engine coordinates cross-channel experiences?**
5. **How do we measure journey effectiveness and identify friction points?**

---

## Research Areas

### Customer Journey Map

```typescript
interface CustomerJourney {
  stages: JourneyStage[];
  touchpoints: Touchpoint[];
  transitions: JourneyTransition[];
  personas: JourneyPersonaMap[];
}

// Travel customer journey stages:
// ─────────────────────────────────────────
//
// ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
// │AWARENESS│──→│ CONSIDER │──→│  BOOK    │──→│ PREPARE  │──→│ TRAVEL   │──→│ POST-TRIP│
// │         │   │          │   │          │   │          │   │          │   │          │
// │Discover │   │Research  │   │Quote     │   │Documents │   │Experience│   │Review    │
// │Inspire  │   │Compare   │   │Customize │   │Packing   │   │Support   │   │Refer     │
// │Dream    │   │Consult   │   │Pay       │   │Excited   │   │Navigate  │   │Repeat    │
// └─────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
//
// Stage duration (typical India domestic):
// Awareness: Ongoing
// Consider: 1-4 weeks
// Book: 1-7 days
// Prepare: 2-30 days
// Travel: 3-14 days
// Post-trip: Ongoing

interface JourneyStage {
  id: string;
  name: string;
  description: string;
  entryConditions: string[];
  exitConditions: string[];
  touchpoints: Touchpoint[];
  emotions: EmotionMap;
  metrics: StageMetric[];
  avgDuration: string;
  dropOffPoints: string[];
}

// STAGE 1: AWARENESS
// How Indian travelers discover travel options:
// - Word of mouth (40% — highest in India)
// - Instagram/social media (25%)
// - Google search (15%)
// - WhatsApp forwards from friends/family (10%)
// - Travel agency storefront (5%)
// - TV/newspaper ads (3%)
// - OTT show destination inspiration (2%)
//
// Touchpoints:
// - Agency website / social media page
// - Friend's travel photos (WhatsApp/Instagram)
// - Google search "best places to visit in December"
// - Festival planning conversation (Diwali, summer vacation)
// - Travel expo / fair
// - YouTube travel vlog
//
// Customer emotions: Curious, dreaming, excited
// Agent opportunity: Be discoverable, share inspiring content

// STAGE 2: CONSIDERATION
// Research and comparison phase:
// Touchpoints:
// - WhatsApp inquiry to agent ("Kerala trip for 4 in December")
// - Agent sends destination guide / itinerary options
// - Customer compares with OTAs (MakeMyTrip, Goibibo)
// - Customer discusses with family/friends
// - Agent sends WhatsApp with photos and videos
// - Customer reads reviews online
// - Agent follows up with personalized recommendation
// - Customer asks for customization ("Can we add houseboat?")
//
// Key moments:
// 1. First agent contact → Response time critical (<15 min on WhatsApp)
// 2. First recommendation → Must be personalized, not generic
// 3. OTA comparison → Agent must demonstrate value over OTA
// 4. Family discussion → Agent may need to convince decision-maker
//
// Customer emotions: Interested, overwhelmed by options, price-conscious
// Drop-off risk: Slow response, generic recommendations, no differentiation
// Agent opportunity: Speed, personalization, expertise, trust

// STAGE 3: BOOKING
// From quote to confirmed booking:
// Touchpoints:
// - Agent sends detailed quote (WhatsApp + email)
// - Customer negotiates price
// - Agent adjusts itinerary and re-quotes
// - Customer confirms verbally ("Book kar do")
// - Agent sends booking confirmation
// - Payment collection (link, UPI, bank transfer)
// - Agent confirms hotel and flights
// - Itinerary shared with customer
// - Customer shares excitement with friends/family
//
// Key moments:
// 1. Price negotiation → Agent defends value, offers alternatives
// 2. Payment → Must be easy (UPI QR, payment link, EMI options)
// 3. Confirmation → Immediate WhatsApp confirmation with details
// 4. First document → Itinerary or voucher, feels real
//
// Customer emotions: Excited, anxious (is this the right choice?), price-sensitive
// Drop-off risk: Payment friction, no confirmation, better OTA deal
// Agent opportunity: Smooth payment, instant confirmation, reassurance

// STAGE 4: PREPARATION
// Pre-trip preparation and anticipation:
// Touchpoints:
// - Agent sends packing list and tips
// - Document reminders (visa, passport, insurance)
// - Weather update for destination
// - Hotel check-in details shared
// - Driver contact shared (day before)
// - WhatsApp group created (agent + customer + ground team)
// - Customer asks "Kitna cold hoga?" / "Kya pack karu?"
// - Agent sends destination guide / restaurant recommendations
// - Day-before departure reminder with all details
//
// Key moments:
// 1. Pre-trip anxiety → Agent provides reassurance and preparation tips
// 2. Document preparation → Agent verifies all documents ready
// 3. WhatsApp group → Direct line to agent during trip
//
// Customer emotions: Excited, nervous, anticipating, preparing
// Agent opportunity: Be the expert guide, reduce anxiety

// STAGE 5: TRAVEL
// During the trip:
// Touchpoints:
// - Day 1 check-in: "How was your flight?"
// - Daily morning: "Today's plan: [activity]. Enjoy!"
// - Mid-trip check: "How's everything going?"
// - Issue reported: "Hotel AC not working" → Agent resolves
// - Activity reminder: "Your backwater ride is at 10 AM"
// - Last day: "Hope you had a great trip! Check-out at 12 PM"
// - Airport drop: Driver contact and timing confirmed
//
// Key moments:
// 1. First-day check-in → Sets tone for rest of trip
// 2. Issue resolution → Make or break for satisfaction
// 3. Daily engagement → Shows agent cares, not just transactional
// 4. Last-day farewell → Positive close to the experience
//
// Customer emotions: Excited, experiencing, sometimes frustrated (issues)
// Agent opportunity: Proactive communication, fast issue resolution

// STAGE 6: POST-TRIP
// After the trip:
// Touchpoints:
// - Welcome back message (day after return)
// - Photo sharing request ("Share your best photos!")
// - Feedback survey (WhatsApp-based, short)
// - Review request (Google, Facebook, WhatsApp status)
// - Thank you message with referral offer
// - Follow-up for next trip suggestion (2-4 weeks later)
// - Festival/season offer ("Diwali getaway ideas!")
// - Anniversary/birthday greeting with travel offer
// - Repeat booking discussion
//
// Key moments:
// 1. Feedback collection → While experience is fresh
// 2. Review solicitation → Social proof for future customers
// 3. Referral request → Best time is when satisfaction is high
// 4. Next trip suggestion → Plant the seed while memory is warm
//
// Customer emotions: Satisfied, nostalgic, sharing experiences
// Agent opportunity: Convert satisfaction into loyalty and referrals
```

### Journey State Engine

```typescript
interface JourneyStateEngine {
  states: CustomerJourneyState[];
  transitions: StateTransition[];
  triggers: JourneyTrigger[];
  actions: JourneyAction[];
}

interface CustomerJourneyState {
  customerId: string;
  currentStage: JourneyStageType;
  currentTouchpoint: string;
  activeTrips: string[];               // Trip IDs
  lastInteraction: Date;
  lastChannel: 'whatsapp' | 'email' | 'phone' | 'in_person' | 'website';
  sentiment: 'positive' | 'neutral' | 'negative';
  riskFlags: string[];                 // ["slow_response", "price_shopping", "no_payment"]
  nextBestAction: string;              // AI-suggested next action
  journeyScore: number;                // 0-100, how engaged they are
}

type JourneyStageType =
  | 'awareness'
  | 'consideration'
  | 'booking'
  | 'preparation'
  | 'traveling'
  | 'post_trip'
  | 'dormant'                          // No activity for 90+ days
  | 'churned';                         // Explicitly left or went to competitor

// Journey state dashboard:
// ┌─────────────────────────────────────────┐
// │  Customer Journey Pipeline               │
// │                                            │
// │  Awareness      ●●●●● (5 new today)      │
// │  Consideration  ●●●●●●●●●● (10 active)  │
// │  Booking        ●●●●●●● (7 in progress)  │
// │  Preparation    ●●●●●● (6 upcoming trips)│
// │  Traveling      ●●●● (4 currently away)  │
// │  Post-trip      ●●●●●●●● (8 pending)    │
// │  Dormant        ●●●●●●●●●●●●●● (14)    │
// │                                            │
// │  Conversion: Consideration → Booking: 70% │
// │  Avg time to book: 4.2 days               │
// │  Avg trip value: ₹62,500                  │
// │                                            │
// │  ⚠️ Attention:                             │
// │  • 3 customers in consideration >7 days   │
// │  • 2 customers with negative sentiment    │
// │  • 14 dormant — win-back campaign?        │
// │                                            │
// │  [View Details] [Export Journey Report]    │
// └─────────────────────────────────────────────┘

interface StateTransition {
  from: JourneyStageType;
  to: JourneyStageType;
  trigger: string;                     // Event that causes transition
  autoTransition: boolean;             // Automatic or agent-triggered
  requiredActions: string[];           // Actions needed for transition
}

// Transition examples:
// awareness → consideration:
//   trigger: "customer_first_inquiry"
//   auto: true
//   actions: ["create_customer_profile", "assign_agent"]
//
// consideration → booking:
//   trigger: "quote_accepted" or "payment_initiated"
//   auto: true
//   actions: ["create_trip", "start_booking_workflow"]
//
// booking → preparation:
//   trigger: "trip_fully_confirmed"
//   auto: true
//   actions: ["send_preparation_pack", "create_whatsapp_group"]
//
// preparation → traveling:
//   trigger: "trip_start_date_reached"
//   auto: true
//   actions: ["send_departure_reminder", "activate_tracking"]
//
// traveling → post_trip:
//   trigger: "trip_end_date_reached"
//   auto: true
//   actions: ["send_feedback_request", "request_review"]
//
// post_trip → dormant:
//   trigger: "no_interaction_90_days"
//   auto: true
//   actions: ["trigger_win_back_campaign"]
//
// dormant → consideration:
//   trigger: "customer_re_engages"
//   auto: true
//   actions: ["welcome_back_message", "personalized_suggestion"]

interface JourneyTrigger {
  type: 'event' | 'time' | 'behavior' | 'manual';
  event?: string;
  timeCondition?: string;
  behaviorCondition?: string;
}

interface JourneyAction {
  type: 'send_message' | 'create_task' | 'assign_agent' | 'send_email'
      | 'create_trip' | 'update_profile' | 'trigger_campaign' | 'notify_agent';
  channel?: string;
  template?: string;
  delay?: number;                      // Seconds to wait before executing
}
```

### Journey Orchestration Engine

```typescript
interface JourneyOrchestration {
  rules: OrchestrationRule[];
  campaigns: JourneyCampaign[];
  automation: JourneyAutomation;
  analytics: JourneyAnalytics;
}

interface OrchestrationRule {
  id: string;
  name: string;                        // "Welcome New Inquiry"
  trigger: JourneyTrigger;
  conditions: string[];                // Additional conditions
  actions: JourneyAction[];
  priority: number;
  active: boolean;
}

// Orchestration rules examples:
//
// RULE: "Welcome New Inquiry"
// Trigger: customer_first_inquiry
// Conditions: stage = awareness
// Actions:
//   1. Send WhatsApp welcome message (instant)
//   2. Create customer profile (instant)
//   3. Assign to available agent (instant)
//   4. Send agent notification (instant)
//   5. If no response in 15 min → Escalate to team lead
//
// RULE: "Consideration Follow-up"
// Trigger: customer_in_consideration_48h
// Conditions: no_agent_response_in_24h = false
// Actions:
//   1. Send personalized destination content
//   2. Schedule agent follow-up reminder
//
// RULE: "Pre-trip Preparation Pack"
// Trigger: trip_confirmed + 7_days_before_travel
// Actions:
//   1. Send packing checklist
//   2. Send weather forecast
//   3. Share driver/hotel contacts
//   4. Create WhatsApp group
//
// RULE: "Trip Start Check-in"
// Trigger: trip_start_date + 6_hours
// Actions:
//   1. Send "How was your flight?" message
//   2. Create daily check-in schedule
//
// RULE: "Post-trip Engagement"
// Trigger: trip_end_date + 1_day
// Actions:
//   1. Send "Welcome back!" message
//   2. Request feedback (WhatsApp survey)
//   3. If feedback > 4 stars → Request Google review
//   4. Send referral offer
//
// RULE: "Win-back Dormant Customer"
// Trigger: customer_dormant_90_days
// Actions:
//   1. Send personalized "We miss you" message
//   2. Include special offer based on past trips
//   3. If no response in 7 days → Send festival-based suggestion
//   4. If no response in 30 days → Mark as churned

// Journey analytics:
interface JourneyAnalytics {
  // Stage conversion metrics:
  // ┌─────────────────────────────────────────┐
  // │  Journey Analytics — Last 90 Days         │
  // │                                            │
  // │  Funnel:                                   │
  // │  Awareness:       500 (100%)               │
  // │  Consideration:   320 (64%)  ← 36% drop   │
  // │  Booking:         224 (70% of considered)  │
  // │  Preparation:     218 (97% of booked)      │
  // │  Traveling:       210 (96% of prepared)    │
  // │  Post-trip:       198 (94% of traveled)    │
  // │                                            │
  // │  Overall conversion: 39.6% (awareness → travel)│
  // │                                            │
  // │  Friction points:                          │
  // │  1. Awareness → Consideration: 36% drop    │
  // │     Cause: Slow response (avg 45 min)     │
  // │  2. Consideration → Booking: 30% drop      │
  // │     Cause: Price comparison with OTAs      │
  // │  3. Post-trip → Repeat: Only 35% repeat    │
  // │     Cause: No follow-up campaign           │
  // │                                            │
  // │  Avg journey time: 18 days (inquiry → travel)│
  // │  Avg value per journey: ₹62,500           │
  // │  Customer journey LTV: ₹1,85,000          │
  // └─────────────────────────────────────────────┘
  //
  // Channel effectiveness at each stage:
  // Stage          | Best Channel    | Conversion
  // ──────────────────────────────────────────
  // Awareness      | WhatsApp (64%)  | Best
  // Consideration  | WhatsApp (58%)  | Best
  // Booking        | WhatsApp (42%)  | + Email for docs
  // Preparation    | WhatsApp (75%)  | Dominant
  // Traveling      | WhatsApp (80%)  | Dominant
  // Post-trip      | Email (45%)     | For longer content
}
```

---

## Open Problems

1. **Journey state accuracy** — Determining which stage a customer is in requires interpreting multiple signals (messages, actions, time). A customer might be in "consideration" but also browsing for a different trip. Multi-trip customers exist in multiple stages simultaneously.

2. **Orchestration rule conflicts** — Multiple rules may trigger simultaneously (e.g., "post-trip feedback" and "win-back campaign"). Priority-based execution and deduplication are needed to avoid spamming customers.

3. **WhatsApp rate limits** — India's WhatsApp-first approach runs into Meta's messaging rate limits. Business API has per-day limits per customer. Journey orchestration must batch non-urgent messages.

4. **Cross-channel journey continuity** — A customer may inquire on WhatsApp, get a quote via email, and call to book. Stitching these touchpoints into a coherent journey state requires identity resolution across channels.

5. **Dormant customer re-engagement** — Most dormant customers don't respond to automated win-back campaigns. The right re-engagement trigger is often external (festival, holiday, friend's trip) rather than timed.

---

## Next Steps

- [ ] Build journey state engine with stage transitions and trigger rules
- [ ] Create journey orchestration system with automated touchpoint management
- [ ] Design journey analytics dashboard with funnel metrics and friction detection
- [ ] Implement cross-channel journey stitching with identity resolution
- [ ] Study journey orchestration (Braze, Iterable, Customer.io, MoEngage, WebEngage)
