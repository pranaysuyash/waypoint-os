# Accessibility & Assistive Technology — Voice Control & Speech Navigation

> Research document for voice command navigation, speech-driven workflows, hands-free operation, and voice accessibility.

---

## Key Questions

1. **How do we support voice control for platform navigation?**
2. **What voice commands are needed for core workflows?**
3. **How do we enable hands-free trip building?**
4. **What's the voice interaction model for accessibility?**
5. **How do we handle voice commands with noisy environments?**

---

## Research Areas

### Voice Command System

```typescript
interface VoiceControlSystem {
  commands: VoiceCommand[];
  grammar: VoiceGrammar;
  feedback: VoiceFeedback;
  modes: VoiceInteractionMode[];
}

interface VoiceCommand {
  command: string;                    // "Show my inbox"
  alternatives: string[];             // ["Open inbox", "Go to inbox"]
  action: string;                     // Route action
  category: CommandCategory;
  confirmation: boolean;              // Requires "yes" confirmation
}

type CommandCategory =
  | 'navigation'                      // Moving between pages/sections
  | 'action'                          // Performing an action
  | 'query'                           // Asking for information
  | 'editing'                         // Modifying content
  | 'control';                        // UI control (zoom, scroll, etc.)

// Voice command library:
//
// NAVIGATION:
// "Go to [inbox/workbench/settings/analytics]"
// "Show trip [number/name]"
// "Open panel [intake/trip/output]"
// "Next/previous trip"
// "Go back"
// "Show [destination] trips"
//
// ACTION:
// "Create new trip"
// "Send message to [customer name]"
// "Book this trip"
// "Cancel booking [reference]"
// "Assign to [agent name]"
// "Mark as [priority/status]"
// "Send quote"
//
// QUERY:
// "What's the status of trip [number]?"
// "Show [customer name] bookings"
// "What's the price for [destination]?"
// "When is [customer name] traveling?"
// "How many pending trips?"
// "What's my schedule today?"
//
// EDITING:
// "Add [hotel/flight/transfer] to trip"
// "Change date to [date]"
// "Update price to [amount]"
// "Remove [component] from trip"
// "Set [traveler count] travelers"
//
// CONTROL:
// "Scroll down/up"
// "Zoom in/out"
// "Show keyboard shortcuts"
// "Read page"
// "Stop listening"

interface VoiceGrammar {
  language: string;                   // "en-IN"
  entities: VoiceEntity[];
  contextFreeGrammar: string;
}

// Voice entity recognition for travel:
// Destinations: "Kerala", "Goa", "Singapore", "Thailand", "Dubai"
// Customer names: "Rajesh Sharma", "Priya Mehta"
// Agent names: "Arun", "Priya"
// Dates: "December 15th", "next week", "tomorrow"
// Amounts: "fifty thousand", "1.5 lakh"
// Trip types: "honeymoon", "family", "adventure", "pilgrimage"
// Components: "hotel", "flight", "transfer", "activity"
//
// Natural language command examples:
// "Show me all honeymoon trips to Kerala in December"
//   → Filter: type=honeymoon, destination=Kerala, month=December
//
// "Assign the Singapore trip to Priya"
//   → Find unassigned Singapore trip → Assign to agent Priya
//
// "What's Rajesh Sharma's latest booking?"
//   → Search customer → Show most recent trip
//
// "Add a 5-star hotel in Kochi for 3 nights"
//   → Open trip builder → Add hotel component → Set Kochi, 3 nights, luxury
```

### Hands-Free Trip Building

```typescript
interface VoiceTripBuilder {
  state: VoiceTripState;
  workflow: VoiceTripWorkflow;
  confirmation: VoiceConfirmation;
}

interface VoiceTripState {
  tripId: string;
  currentStep: TripBuildingStep;
  collectedInfo: Partial<TripInfo>;
  pendingConfirmation: string[];
}

type TripBuildingStep =
  | 'destination'
  | 'dates'
  | 'travelers'
  | 'budget'
  | 'preferences'
  | 'hotel'
  | 'flight'
  | 'activities'
  | 'review'
  | 'confirm';

// Voice-driven trip building flow:
//
// Agent: "I'm ready to create a new trip. Where would you like to go?"
// Customer: "Kerala, Alleppey and Munnar"
// Agent: "Kerala, beautiful choice. When are you planning to travel?"
// Customer: "Second week of December"
// Agent: "How many nights?"
// Customer: "Five nights"
// Agent: "And how many travelers?"
// Customer: "Two adults"
//
// System auto-populates:
// - Destination: Kerala (Alleppey, Munnar)
// - Dates: December 8-13, 2026 (approximate)
// - Duration: 5 nights
// - Travelers: 2 adults
//
// System auto-searches and presents:
// Agent: "I found a great option. 5 nights in Kerala, visiting
//         Alleppey and Munnar. Houseboat stay in Alleppey,
//         hill resort in Munnar. Starting from ₹27,500 per person.
//         Would you like me to add flights from Delhi?"
// Customer: "Yes, from Delhi"
//
// [System adds flight component]
// Agent: "I've added Delhi to Kochi flights. Total trip is now
//         ₹55,000 for two. Should I send you the detailed itinerary?"
// Customer: "Yes, send it on WhatsApp"
// Agent: "Done! I've sent the itinerary to your WhatsApp.
//         The trip is saved as draft. Shall I hold the booking
//         until you confirm?"

interface VoiceConfirmation {
  type: ConfirmationType;
  message: string;
  required: boolean;
}

type ConfirmationType =
  | 'destructive'                     // Cancel, delete, send
  | 'financial'                       // Payment, booking confirm
  | 'modification';                   // Change dates, swap hotel

// Confirmation requirements:
// Destructive: "You said cancel trip TRV-45678. Confirm with yes or no."
// Financial: "Confirm booking for ₹55,000? Say yes to proceed."
// Modification: "Change hotel to Taj Malabar? Confirm yes or no."
//
// Safety: Never execute destructive/financial actions without explicit "yes"
// Timeout: If no response in 10 seconds, cancel the action
// Retry: "I didn't catch that. Please say yes or no."
```

### Voice Feedback System

```typescript
interface VoiceFeedback {
  responses: VoiceResponse[];
  pacing: VoicePacing;
  interruption: InterruptionHandling;
}

// Voice response design:
// - Confirm every recognized command: "Opening inbox"
// - State current context: "You're viewing 24 trips in Kerala"
// - Announce results: "Found 3 matching trips"
// - Error feedback: "I didn't understand. Try saying 'show inbox'"
// - Progress: "Searching for Kerala trips... Found 24 results"
//
// Response pacing:
// - Short responses: < 3 seconds ("Opening inbox")
// - Medium responses: 3-5 seconds (search results summary)
// - Long responses: Offer summary first, then option for details
//   "Trip Kerala has 5 components. Say 'read details' for full itinerary."
//
// Interruption handling:
// - Customer can interrupt: "Stop" or "Next" during long response
// - "Next" skips to next item in list
// - "Stop" stops reading and waits for new command
// - "Repeat" reads the last response again
// - "Slower" / "Faster" adjusts speech rate
//
// Accessibility considerations for voice:
// - Speech rate adjustable (0.5x to 2x)
// - Language selection (English, Hindi)
// - Voice gender selection (male/female TTS voice)
// - Audio cues for navigation (ding for new message, chime for confirmation)
// - Haptic feedback on mobile (vibration patterns for actions)
```

---

## Open Problems

1. **Accuracy in Indian accents** — Speech recognition accuracy drops significantly for Indian English accents, especially with background noise. Need India-accented voice models.

2. **Mixed language commands** — Agents commonly use Hinglish ("Kerala trip dikhao" = "show Kerala trips"). Voice command system must handle code-switching.

3. **Microphone quality** — Laptop microphones vary in quality. Background office noise (other agents talking) interferes with voice recognition.

4. **Privacy in shared workspace** — Voice commands in an open office mean other agents hear customer names and trip details. Need headset-only mode or push-to-talk.

5. **Learning curve** — Voice commands require memorization. New agents won't know the commands. Need discoverable voice UI (suggest commands contextually).

---

## Next Steps

- [ ] Build voice command recognition system with travel-specific grammar
- [ ] Create hands-free trip building workflow with voice-driven slot filling
- [ ] Design voice feedback system with adjustable pacing and interruption
- [ ] Implement push-to-talk mode for shared workspace privacy
- [ ] Study voice accessibility (Voice Control on macOS, Voice Access on Android, Dragon)
