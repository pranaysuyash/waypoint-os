# Voice & Conversational AI — Voice-Driven Booking Flow

> Research document for voice-based trip inquiry, slot filling, booking confirmation, and voice-commerce for travel.

---

## Key Questions

1. **How do customers book trips through voice interaction?**
2. **What's the slot-filling model for collecting travel requirements?**
3. **How do we confirm bookings verbally with legal validity?**
4. **What's the voice UX for trip comparison and selection?**
5. **How do we handle payment authorization over the phone?**

---

## Research Areas

### Voice Booking Flow

```typescript
interface VoiceBookingFlow {
  callId: string;
  customer: VoiceCustomer;
  phase: BookingPhase;
  slots: BookingSlots;
  trips: VoiceTripOption[];
  selected: VoiceTripSelection;
  confirmation: VoiceConfirmation;
}

type BookingPhase =
  | 'greeting'                        // Welcome and identification
  | 'requirement_gathering'           // Collect trip requirements
  | 'search_and_present'              // Search and present options
  | 'selection'                       // Customer selects a trip
  | 'traveler_details'                // Collect traveler information
  | 'pricing_review'                  // Review final pricing
  | 'payment'                         // Payment processing
  | 'confirmation';                   // Booking confirmed

// Voice booking flow (3-8 minutes):
//
// Phase 1: Greeting (15 seconds)
// Agent: "Hello, thank you for calling {Agency}. I'm {Name}.
//         How can I help you plan your trip today?"
// Customer: "I want to plan a trip to Kerala"
//
// Phase 2: Requirement Gathering (1-2 minutes)
// Agent: "Kerala is a beautiful choice! Let me get some details.
//         When are you planning to travel?"
// Customer: "Second week of December"
// Agent: "And how many travelers?"
// Customer: "Just me and my wife, 2 adults"
// Agent: "How many nights would you like to stay?"
// Customer: "5 nights"
// Agent: "Any preference for the type of experience?
//         Backwaters, hills, beaches, or a mix?"
// Customer: "We want backwaters and some hills"
// Agent: "What's your budget per person?"
// Customer: "Around 25 to 30 thousand"
//
// Phase 3: Search & Present (30-60 seconds)
// [Agent searches in Workbench while customer waits]
// Agent: "I have a perfect option for you.
//         It's a 5-night Kerala Backwaters and Hills tour.
//         Day 1-2: Kochi sightseeing and stay
//         Day 3-4: Houseboat in Alleppey backwaters
//         Day 5: Munnar tea gardens
//         Day 6: Return from Kochi
//         Starting from ₹27,500 per person,
//         including flights, hotels, houseboat, and breakfast.
//         Would you like to hear more details or see other options?"
//
// Phase 4: Selection (30-60 seconds)
// Customer: "Tell me about the hotels"
// Agent: "In Kochi, you'll stay at the Trident — 5-star,
//         waterfront location. In Alleppey, a premium houseboat
//         with private deck and chef. In Munnar, the Tea County
//         resort with mountain views."
// Customer: "Sounds great. Can we do it starting December 10th?"
// Agent: "Let me check... Yes, December 10th is available!
//         Total for 2 adults: ₹55,000. Shall I book this?"
// Customer: "Yes, go ahead"
//
// Phase 5: Traveler Details (1-2 minutes)
// Agent: "I'll need some details. Your full name?"
// Customer: "Rajesh Sharma"
// Agent: "And your wife's name?"
// Customer: "Priya Sharma"
// Agent: "Your email for the booking confirmation?"
// Customer: "rajesh dot sharma at gmail dot com"
// Agent: "And your WhatsApp number?"
// Customer: "98765 43210"
// [Agent enters details in Workbench in real-time]
//
// Phase 6: Payment (1-2 minutes)
// Agent: "I can take your payment now. We accept UPI, cards,
//         and net banking. For this booking, I need ₹16,500
//         as advance — that's 30%. The balance is due
//         by November 25th."
// Customer: "I'll pay by UPI"
// Agent: "I'm sending a payment link to your WhatsApp.
//         You'll see it in just a moment... Sent!
//         You can complete the payment at your convenience.
//         Your booking is provisionally confirmed."
//
// Phase 7: Confirmation (30 seconds)
// Agent: "Your booking reference is TRV-45678.
//         I'm sending the confirmation with your itinerary
//         to your WhatsApp and email.
//         Is there anything else I can help with?"
// Customer: "No, that's all. Thank you!"
// Agent: "You're welcome! Have a wonderful trip to Kerala.
//         Goodbye!"

interface BookingSlots {
  destination?: string;
  dates?: TravelDates;
  travelers?: TravelerCount;
  duration?: TripDuration;
  budget?: BudgetRange;
  tripType?: string;
  preferences?: string[];
  accommodationLevel?: string;
}

// Slot filling strategy:
// Priority order (collect most impactful first):
// 1. Destination (determines what's available)
// 2. Dates (determines pricing and availability)
// 3. Traveler count (determines room configuration)
// 4. Duration (determines itinerary scope)
// 5. Budget (narrows options to relevant price range)
// 6. Preferences (refines itinerary)
//
// Missing slot handling:
// If destination missing: "Where would you like to travel?"
// If dates flexible: "We have great options year-round.
//                    Any specific time in mind, or should I
//                    suggest the best season?"
// If budget not mentioned: Don't ask directly.
//   Present 2-3 options at different price points instead.
//
// Proactive slot filling:
// If customer says "honeymoon in December":
//   → Auto-fill: trip_type = honeymoon, date = December
//   → Auto-suggest: duration = 5-7 nights (common for honeymoon)
//   → Ask: "How many nights?" (confirm duration)
//   → Don't ask: trip_type (already known)
```

### Voice Trip Comparison

```typescript
interface VoiceTripComparison {
  trips: VoiceTripOption[];
  comparisonScript: ComparisonScript;
  customerResponse: CustomerPreference;
}

interface VoiceTripOption {
  tripId: string;
  name: string;
  highlights: string[];               // 3-5 key selling points
  price: Money;
  pricePerPerson: Money;
  duration: string;                   // "5 nights, 6 days"
  destinations: string[];
  inclusions: string[];               // What's included (brief)
  exclusions?: string[];              // What's not included
}

// Voice comparison strategies:
// For 2 options: "I have two options for you.
//   Option A is ₹27,500 — backwaters and hills, 5-star hotels.
//   Option B is ₹22,000 — similar experience, 4-star hotels,
//   and includes a Kathakali show.
//   Which sounds more appealing?"
//
// For 3+ options: Present top 2 only (cognitive load limit)
//   "I found several options. The most popular one is..."
//   "If you'd like to explore more, I can share details via WhatsApp."
//
// Comparison by dimension:
// Price: "Option A is ₹5,000 more but includes all meals."
// Hotels: "Option A has 5-star hotels. Option B has 4-star."
// Activities: "Option B includes a Kathakali show, Option A doesn't."
// Seasonal: "December is peak season. January has the same weather
//            but ₹3,000 less per person."
//
// Decision support:
// Agent: "Based on what you've told me — honeymoon, backwaters,
//         25-30K budget — I'd recommend Option A. The houseboat
//         experience is perfect for couples, and the Trident
//         has a special honeymoon package with candlelight dinner."

interface ComparisonScript {
  opening: string;                    // "Here are your options..."
  optionPresentation: string[];       // Script for each option
  comparisonHighlight: string[];      // Key differences to mention
  recommendation: string;             // Agent's recommendation
  closing: string;                    // "Which option interests you?"
}
```

### Voice Payment Authorization

```typescript
interface VoicePayment {
  bookingId: string;
  amount: Money;
  method: VoicePaymentMethod;
  authorization: PaymentAuthorization;
  security: VoicePaymentSecurity;
}

type VoicePaymentMethod =
  | 'payment_link'                    // Send link via WhatsApp/SMS
  | 'upi_intent'                      // UPI app opens on customer's phone
  | 'card_on_file'                    // Previously saved card
  | 'bank_transfer';                  // NEFT/IMPS details shared

// Voice payment flow (PCI-DSS compliant):
//
// NEVER collect card numbers verbally over the phone.
// PCI-DSS Level 1 compliance requires secure payment channels.
//
// Recommended flow:
// 1. Agent initiates payment in Workbench
// 2. System sends payment link to customer's WhatsApp/SMS
// 3. Customer opens link → Secure payment page (Razorpay)
// 4. Customer completes payment (UPI, card, net banking)
// 5. Payment confirmation → Agent sees in Workbench
// 6. Booking confirmed
//
// Alternative: UPI Intent
// 1. Agent sends payment request with UPI deep link
// 2. Customer's UPI app opens with pre-filled amount
// 3. Customer authorizes with UPI PIN
// 4. Instant confirmation
//
// For repeat customers (saved payment):
// 1. Agent: "Would you like to use your saved card ending in 4242?"
// 2. Customer: "Yes"
// 3. Agent triggers payment → Customer gets OTP on phone
// 4. Customer shares OTP → Payment processed
// 5. Confirmation
//
// Security requirements:
// - Never store card numbers (tokenization only)
// - Never speak card numbers aloud
// - Payment page must be PCI-DSS compliant
// - OTP/3DS verification required for all card payments
// - UPI PIN never shared with agent
// - Payment confirmation via webhook (not verbal relay)

interface PaymentAuthorization {
  authorizedBy: string;               // Customer name
  method: string;
  timestamp: Date;
  ipAddress?: string;                 // For online payments
  recordingSegment?: string;          // Call recording timestamp for verbal consent
}

// Verbal consent recording:
// Agent: "I'm confirming your booking for Kerala trip,
//         reference TRV-45678, total ₹55,000 for 2 adults,
//         departing December 10th. Advance payment of ₹16,500.
//         Do you confirm this booking?"
// Customer: "Yes, I confirm"
// [Recording timestamp saved as proof of verbal consent]
// This is legally valid under Indian Contract Act for telephone bookings
```

---

## Open Problems

1. **Cognitive load** — Customers can't remember more than 2-3 trip options presented verbally. Need to supplement voice with WhatsApp/visual delivery.

2. **Payment compliance** — PCI-DSS prohibits collecting card details verbally. Must route all payments through secure digital channels, even during phone calls.

3. **Misunderstanding cost** — A misunderstood date ("December 10th" vs. "December 18th") can lead to wrong bookings. Need verbal confirmation of all critical details.

4. **Call duration** — Booking calls take 5-8 minutes. Customer may get impatient. Need to offer async alternatives ("I'll send options on WhatsApp, take your time").

5. **Agent skill requirement** — Voice booking requires skilled agents who can converse naturally while simultaneously operating the Workbench. Not all agents can do this.

---

## Next Steps

- [ ] Design voice booking flow with slot-filling model
- [ ] Build voice trip comparison and presentation scripts
- [ ] Create PCI-DSS compliant voice payment flow
- [ ] Design verbal consent recording for booking confirmation
- [ ] Study voice commerce platforms (Amazon Alexa for Hospitality, Google Business Messages)
