# Template & Quick-Start System — Quick-Start Flows

> Research document for rapid trip creation workflows, one-click bookings, and express workflows.

---

## Key Questions

1. **How do we reduce trip creation from 30 minutes to 5 minutes?**
2. **What's the express booking flow for repeat customers?**
3. **How do we handle quick-start for different inquiry channels?**
4. **What's the minimum viable trip data needed to generate a quote?**
5. **How do quick-start flows maintain quality?**

---

## Research Areas

### Quick-Start Models

```typescript
type QuickStartType =
  | 'template_to_trip'               // Start from template, customize
  | 'clone_trip'                     // Copy a past successful trip
  | 'express_quote'                  // Minimal data → instant estimate
  | 'package_booking'                // Book a fixed package directly
  | 'channel_trigger'                // WhatsApp/email inquiry → trip draft
  | 'ai_suggestion'                  // AI builds itinerary from description;

interface QuickStartConfig {
  type: QuickStartType;
  estimatedTime: string;             // "2 minutes", "5 minutes"
  requiredFields: string[];
  optionalFields: string[];
  steps: QuickStartStep[];
  qualityChecks: QualityCheck[];
}

// Quick-start flow: Template to Trip
// 1. Select template (30 seconds)
// 2. Enter dates and travelers (1 minute)
// 3. Select hotel tier (30 seconds)
// 4. Review auto-generated itinerary (1 minute)
// 5. Customize activities (1 minute)
// 6. Review pricing (30 seconds)
// Total: ~5 minutes (vs. 30+ minutes from scratch)
```

### Express Quote Flow

```typescript
interface ExpressQuote {
  quoteId: string;
  destination: string;
  travelDates: DateRange;
  travelers: TravelerSummary;
  budget: BudgetRange;
  generatedAt: Date;
  expiresAt: Date;
  components: QuoteComponent[];
  totalPrice: PriceBreakdown;
  confidence: number;                // How accurate is this estimate
  assumptions: string[];             // What we assumed
}

interface TravelerSummary {
  adults: number;
  children: number;
  ages?: number[];                   // For activity pricing
  specialNeeds?: string[];
}

interface QuoteComponent {
  type: string;
  name: string;
  estimatedPrice: PriceRange;
  note: string;
  isEstimated: boolean;              // True if price is approximate
}

// Express quote flow:
// Customer: "We want to go to Singapore for 5 nights, 2 adults 1 child, around ₹1.5L"
// System:
// 1. Match to "Singapore Family" template
// 2. Look up current flight prices (Delhi → Singapore)
// 3. Look up hotel prices for dates (3-star family hotel)
// 4. Add standard activities pricing
// 5. Calculate total: ₹1,20,000 - ₹1,80,000 range
// 6. Present quote in 30 seconds
// 7. "This is an estimate. Actual price may vary by ±10%."
// 8. Agent can refine or customer can approve for detailed itinerary

// Express quote assumptions:
// - Standard hotel category (unless budget specifies luxury)
// - Economy flights (unless budget allows premium)
// - Shared transfers (unless group size justifies private)
// - Popular activities (unless customer specifies interests)
```

### Clone Trip Flow

```typescript
interface TripClone {
  sourceTripId: string;
  newTripId: string;
  clonedComponents: string[];
  updatedComponents: string[];
  newPricing: boolean;
}

// Clone trip flow:
// 1. Agent selects past trip to clone
// 2. System identifies reusable vs. date-specific components
// 3. Agent enters new dates
// 4. System updates:
//    - Flight prices (new dates)
//    - Hotel availability (new dates)
//    - Activity availability (new dates)
//    - Seasonal pricing adjustments
// 5. Agent reviews changes and confirms
// 6. New trip created with updated pricing

// What gets cloned:
// Reusable: Activities, itinerary structure, meal plans, notes, preferences
// Updated: Flights, hotels, transfers (new dates/prices)
// Cleared: Payments, confirmations, traveler details (new trip)

// Clone variants:
// Exact clone: Same itinerary, different dates
// Similar clone: Same destination, adjust activities
// Upsell clone: Same trip, upgrade hotel/activities
// Downsell clone: Same trip, budget-friendly alternatives
```

### Channel-Triggered Quick-Start

```typescript
interface ChannelTrigger {
  channel: 'whatsapp' | 'email' | 'phone' | 'web_form' | 'walk_in';
  rawData: string;
  extractedData: ExtractedTripData;
  suggestedTemplate: string;
  confidence: number;
  agentAction: AgentAction;
}

interface ExtractedTripData {
  destination?: string;
  dates?: DateRange;
  travelers?: TravelerSummary;
  budget?: BudgetRange;
  interests?: string[];
  specialRequests?: string[];
  customerName?: string;
  customerPhone?: string;
  customerEmail?: string;
  extractionConfidence: number;       // How confident is the extraction
}

// Channel-triggered flows:
//
// WhatsApp: "Hi, we're planning a trip to Bali in June for our anniversary. Just the two of us, budget around 2 lakhs."
// → Extract: destination=Bali, month=June, travelers=2, occasion=anniversary, budget=₹2L
// → Suggest: "Bali Honeymoon/Anniversary" template
// → Auto-create trip draft with extracted data pre-filled
// → Agent reviews and customizes
//
// Email: Forward of hotel booking confirmation from customer
// → Extract: hotel name, dates, location
// → Suggest: Build trip around confirmed hotel
// → Auto-create trip with hotel component filled
// → Agent adds flights, transfers, activities
//
// Phone: Agent takes notes during call
// → Agent enters quick notes in natural language
// → System extracts structured data
// → Suggests template or starts from scratch
// → Agent refines in workbench
```

---

## Open Problems

1. **Quote accuracy** — Express quotes are estimates. If the actual price is 30% higher, customer feels bait-and-switch. Need ±10% accuracy target with clear disclaimers.

2. **Quality vs. speed** — Quick-start may skip important steps (accessibility needs, dietary requirements, visa checks). Need mandatory quality gates even in express mode.

3. **Channel data quality** — WhatsApp messages are informal ("bali trip june, 2 ppl"). Email forwards may be in Hindi. Need robust extraction across formats and languages.

4. **Template mismatch** — Customer wants "something like Bali but cheaper" or "like last year but different hotel." Template matching isn't always straightforward.

5. **Agent skill gap** — Quick-start is great for experienced agents who know what to customize. New agents may not know what they're skipping.

---

## Next Steps

- [ ] Design express quote generation pipeline
- [ ] Build trip clone workflow with date-aware price updates
- [ ] Create channel-triggered quick-start for WhatsApp and email
- [ ] Design quality gates for quick-start flows
- [ ] Study quick-start UX (TravelTriangle, MakeMyTrip, Expedia packages)
