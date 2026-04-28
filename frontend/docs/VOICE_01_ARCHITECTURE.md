# Voice & Conversational AI — Platform Architecture

> Research document for voice platform architecture, telephony integration, IVR design, and call management.

---

## Key Questions

1. **What's the architecture for voice-based travel interactions?**
2. **How do we integrate with telephony providers in India?**
3. **What's the IVR (Interactive Voice Response) design for a travel agency?**
4. **How do we handle inbound and outbound call management?**
5. **What are the regulatory requirements for telephony in India?**

---

## Research Areas

### Voice Platform Architecture

```typescript
interface VoicePlatform {
  telephony: TelephonyIntegration;
  ivr: IVRSystem;
  routing: CallRouting;
  recording: CallRecording;
  analytics: VoiceAnalytics;
}

interface TelephonyIntegration {
  provider: TelephonyProvider;
  numbers: BusinessNumber[];
  sip: SIPConfig;
  capabilities: TelephonyCapability[];
}

type TelephonyProvider =
  | 'exotel'                          // Popular in India, strong API
  | 'knowlarity'                      // Enterprise CPaaS, good IVR
  | 'twilio'                          // Global, developer-friendly
  | 'ameyo'                           // Contact center, India-focused
  | 'kookoo';                         // Budget-friendly, IVR-focused

// India telephony requirements:
// 1. DoT (Department of Telecommunications) registration
// 2. TRAI (Telecom Regulatory Authority of India) compliance
// 3. DND (Do Not Disturb) registry check before outbound calls
// 4. Recording disclosure: Must inform caller that call is recorded
// 5. Data localization: Call recordings stored in India
// 6. Number format: +91 (India country code), 10-digit mobile
// 7. Business numbers: Landline (011-XXXX-XXXX), Toll-free (1800-XXX-XXXX),
//    Mobile virtual (not available in India — use landline routing)
//
// Recommended: Exotel or Knowlarity for India-specific compliance
// - Handles TRAI compliance, DND checks, and recording consent
// - API-first, integrates with web platforms
// - Call recording stored in India data centers
// - Per-minute pricing (₹0.50-1.50/min depending on provider)

interface BusinessNumber {
  number: string;                     // +91-11-XXXX-XXXX or 1800-XXX-XXXX
  type: 'landline' | 'toll_free' | 'mobile';
  purpose: string;                    // "Sales", "Support", "Emergency"
  assignedTo: string[];               // Agent IDs
  availability: AvailabilitySchedule;
}

// Number strategy:
// Sales: 1 toll-free number (1800) for inbound inquiries
// Support: 1 landline number for post-booking support
// Emergency: 1 dedicated number for during-trip emergencies
// WhatsApp Business: Linked to one number for WhatsApp API
//
// Cost estimate (India):
// Toll-free (1800): ₹3,000-5,000/month + ₹1-2/min incoming
// Landline virtual: ₹500-1,000/month + ₹0.50-1/min incoming
// Outbound calling: ₹0.50-1.50/min
// Call recording storage: ₹500/month (10,000 minutes)
// Total: ₹5,000-10,000/month for a small agency

interface TelephonyCapability {
  capability: string;
  enabled: boolean;
}

// Telephony capabilities needed:
// - Inbound call routing (customer calls → route to available agent)
// - Outbound calling (agent calls customer from platform)
// - Call recording (all calls recorded for quality and compliance)
// - Call transfer (agent transfers to another agent or supervisor)
// - Conference calling (agent + customer + supplier, 3-way)
// - Voicemail (unanswered calls → voicemail → notification)
// - SMS (send booking confirmations via SMS)
// - Click-to-call (agent clicks phone number in Workbench → call initiated)
// - Whisper coaching (supervisor speaks to agent without customer hearing)
// - Call barging (supervisor joins call for escalation)
```

### IVR System Design

```typescript
interface IVRSystem {
  flows: IVRFlow[];
  menus: IVRMenu[];
  responses: IVRResponse[];
  fallback: IVRFallback;
}

interface IVRFlow {
  flowId: string;
  name: string;
  trigger: IVRTrigger;
  steps: IVRStep[];
  language: IVRLanguage[];
}

// IVR flow for travel agency:
//
// Customer calls → "Welcome to {Agency Name}"
// → Language selection: "Press 1 for English, 2 for Hindi"
// → Main menu:
//   "Press 1 for New Trip Inquiry"
//   "Press 2 for Existing Booking"
//   "Press 3 for Support / Changes"
//   "Press 4 for Emergency (During Trip)"
//   "Press 5 to speak with an agent"
//
// Flow 1: New Trip Inquiry
//   "Please tell us your destination. You can say 'Kerala', 'Goa', 'Singapore'..."
//   → [Voice recognition or keypad input]
//   → "How many travelers?" → [Voice: "2 adults and 1 child"]
//   → "When are you planning to travel? Say the month, like 'December'"
//   → [Voice recognition for month]
//   → "Thank you! Connecting you to a travel specialist for {destination}."
//   → [Route to agent with trip type = destination]
//   → [Agent sees pre-filled inquiry on screen]
//
// Flow 2: Existing Booking
//   "Please enter your booking reference number, followed by #"
//   → [Keypad input: 12345#]
//   → "Booking for {Customer Name}, {Destination}, {Date}. Is this correct?"
//   → "Press 1 for Yes, 2 for No"
//   → If yes: "Press 1 for Itinerary Details, 2 for Payment Status,
//              3 for Changes, 4 for Cancellation, 5 to speak with agent"
//   → Itinerary details: "Your trip includes..." [reads itinerary summary]
//   → Payment status: "Total ₹45,000. Paid ₹30,000. Balance ₹15,000 due by {date}."
//
// Flow 3: Emergency
//   → Immediate priority routing to emergency agent
//   → If no agent available: forward to emergency mobile number
//   → Record message: "Please state your emergency. Our team is being alerted."
//   → Send WhatsApp + SMS alert to on-call agent with recording
//   → Log emergency in system for follow-up

interface IVRLanguage {
  language: string;                   // "en-IN", "hi-IN", "ta-IN"
  voice: string;                      // TTS voice ID
  sttModel: string;                   // Speech-to-text model
}

// Language support:
// Primary: English (en-IN), Hindi (hi-IN)
// Secondary (phase 2): Tamil (ta-IN), Bengali (bn-IN), Kannada (kn-IN)
// TTS (Text-to-Speech): Google Cloud TTS or Amazon Polly
// STT (Speech-to-Text): Google Speech-to-Text or Azure Speech
//
// India language considerations:
// - Hindi + English covers ~70% of Indian callers
// - Code-switching (Hinglish) is common — STT must handle mixed language
// - Accent variation: Indian English STT needs India-specific model
// - Names: Indian names often misrecognized — need name entity training
```

### Call Routing & Management

```typescript
interface CallRouting {
  strategy: RoutingStrategy;
  queues: CallQueue[];
  skills: SkillBasedRouting;
  overflow: OverflowConfig;
}

type RoutingStrategy =
  | 'round_robin'                     // Distribute equally
  | 'least_busy'                      // Route to agent with fewest active calls
  | 'skill_based'                     // Route based on inquiry type
  | 'customer_dedicated'              // Route to customer's dedicated agent
  | 'priority';                       // Priority customers get routed first

// Skill-based routing matrix:
// Domestic flights → Agent with flight booking skill
// International packages → Agent with international experience
// Visa inquiries → Agent with visa processing knowledge
// Corporate travel → Agent with corporate account experience
// Honeymoon packages → Agent with honeymoon specialization
// Emergency → On-call emergency agent (24/7)
//
// Customer-based routing:
// VIP customer (3+ bookings) → Dedicated agent or senior agent
// Repeat customer → Agent who handled their last trip
// New customer → Any available agent
// Complaint caller → Supervisor or senior agent

interface CallQueue {
  queueId: string;
  name: string;                       // "Sales", "Support", "Emergency"
  maxWaitTime: number;                // Seconds before overflow
  musicOnHold: string;
  positionMessage: string;            // "You are caller number {n}"
  callbackOption: boolean;            // Offer callback instead of waiting
}

// Queue management:
// Max wait time: 120 seconds (Sales), 300 seconds (Support)
// Position message every 30 seconds: "You are caller number 3. Expected wait: 4 minutes."
// Callback option: "Press 1 to receive a callback instead of waiting. We'll call you back in approximately {time}."
// Overflow: After max wait → route to voicemail → send WhatsApp to on-call agent
//
// Queue metrics:
// Average wait time (target: <60 seconds)
// Abandonment rate (target: <10%)
// Service level: % of calls answered within X seconds
// Average handle time (target: 5-8 minutes for inquiry, 3-5 for support)

interface OverflowConfig {
  afterHours: OverflowAction;
  allBusy: OverflowAction;
  noAnswer: OverflowAction;
}

type OverflowAction =
  | { type: 'voicemail'; message: string }
  | { type: 'callback'; collectNumber: boolean }
  | { type: 'forward'; number: string }
  | { type: 'whatsapp'; sendTemplate: string }
  | { type: 'sms'; message: string };

// After-hours strategy:
// Business hours (9 AM - 8 PM IST): Full IVR + agent routing
// Extended hours (8 PM - 10 PM): IVR only + callback option
// Night (10 PM - 9 AM): Emergency only, all others → voicemail + WhatsApp
// Emergency: 24/7, routes to on-call agent's mobile
```

### Voice Analytics

```typescript
interface VoiceAnalytics {
  callMetrics: CallMetrics;
  agentPerformance: VoiceAgentPerformance[];
  customerSentiment: CallSentiment[];
  qualityMonitoring: QualityScore[];
}

interface CallMetrics {
  totalCalls: number;
  inbound: number;
  outbound: number;
  missed: number;
  avgDuration: string;
  avgWaitTime: string;
  abandonRate: number;
  peakHours: PeakHour[];
  callVolumeByDay: DailyVolume[];
}

// Call analytics dashboard:
// ┌──────────────────────────────────────────┐
// │  Voice Analytics — This Week              │
// │                                          │
// │  Total Calls: 245                        │
// │  Answered: 218 (89%)                     │
// │  Missed: 27 (11%)                        │
// │  Avg Wait: 45 seconds                    │
// │  Avg Duration: 6.2 minutes               │
// │                                          │
// │  Peak Hours: 10-11 AM, 3-4 PM           │
// │                                          │
// │  By Type:                                │
// │  Inquiries: 120 (55%)                    │
// │  Support: 68 (31%)                       │
// │  Changes: 20 (9%)                        │
// │  Emergency: 10 (5%)                      │
// │                                          │
// │  [Listen to Calls] [Export Report]       │
// └──────────────────────────────────────────┘
```

---

## Open Problems

1. **Voice recognition accuracy** — Indian accents, code-switching (Hinglish), background noise, and diverse names make speech recognition challenging. Need India-specific STT models.

2. **DND compliance** — Outbound calls must check TRAI's DND registry. Penalties for calling DND-registered numbers. Need real-time DND check before every outbound call.

3. **Call quality** — VoIP call quality varies across Indian networks. Poor audio affects both customer experience and speech recognition accuracy.

4. **Cost vs. coverage** — Toll-free numbers are expensive. Local landline numbers limit accessibility. Mobile virtual numbers aren't available in India. Need cost-effective number strategy.

5. **Agent resistance** — Agents may resist call recording and monitoring. Need to balance quality assurance with agent privacy and trust.

---

## Next Steps

- [ ] Design voice platform architecture with Exotel/Knowlarity integration
- [ ] Build IVR system with multi-language support (English + Hindi)
- [ ] Create skill-based call routing with queue management
- [ ] Design voice analytics dashboard with call metrics
- [ ] Study voice platforms (Twilio, Exotel, Knowlarity, Amazon Connect)
