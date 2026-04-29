# AI_COPILOT_03: Customer-Facing AI Features

> Research document for AI-powered customer-facing features: chatbot, search, recommendations, and in-trip assistance

---

## Document Overview

**Series:** Travel AI Copilot
**Document:** 3 of 4
**Focus:** Customer-Facing AI Features
**Last Updated:** 2026-04-28
**Status:** Research Phase

---

## Table of Contents

1. [Key Questions](#key-questions)
2. [Research Areas](#research-areas)
3. [TypeScript Data Models](#typescript-data-models)
4. [Practical Examples](#practical-examples)
5. [India-Specific Considerations](#india-specific-considerations)
6. [Open Problems](#open-problems)
7. [Next Steps](#next-steps)

---

## Key Questions

1. **Human handoff threshold:** When should the AI chatbot escalate to a human agent? Too early wastes agent time; too late frustrates customers. What signals indicate handoff necessity?
2. **Expectation management:** How to prevent customers from trusting AI-generated itineraries as finalized bookings? What disclaimers are effective without eroding trust?
3. **Search accuracy for Indian destinations:** How to handle queries like "hill station near Delhi under 10k" where "near" is subjective and "10k" means INR 10,000?
4. **Recommendation diversity:** How to avoid the "filter bubble" effect where the AI only recommends popular destinations, missing hidden gems that might better match customer preferences?
5. **In-trip AI reliability:** What happens when the AI gives a wrong local recommendation during a live trip? Liability, trust, and recovery considerations.
6. **Language support depth:** Full conversational AI in Hindi, Tamil, Bengali is much harder than English. What is the minimum viable language support?
7. **Personalization cold start:** New customers have no history. How to give good recommendations without prior data?
8. **Offline in-trip AI:** Travelers often have poor connectivity. What AI features must work offline?

---

## Research Areas

### 1. AI Chatbot for Trip Inquiries

Pre-agent qualification, FAQ handling, and intelligent routing for customer inquiries.

**Chatbot Architecture Tiers:**

| Tier | Capability | Handoff Trigger |
|------|-----------|-----------------|
| **Tier 0: FAQ Bot** | Pattern-matched answers to common questions (visa requirements, cancellation policy, payment methods) | Any question not in FAQ database |
| **Tier 1: Qualification Bot** | Conversational gathering of trip requirements (destination, dates, budget, travelers) | Customer ready for quote, complex request, negative sentiment |
| **Tier 2: Search Bot** | Natural language trip search ("beach holiday under 50k for 2") | Customer wants specific availability check, customization |
| **Tier 3: Advisory Bot** | Destination comparison, travel tips, itinerary suggestions | Customer ready to book, pricing discussion, complex multi-city |
| **Human Agent** | Full service, negotiation, complex itineraries | Customer requests, or bot confidence drops below threshold |

**Conversation Design Principles:**
- Lead with questions, not suggestions (understand before recommending)
- Always show progress ("Got it! I now know your destination, dates, and budget. Just need traveler details.")
- Never promise specific prices or availability (use ranges: "typically INR 40-60k for...")
- Transparent about being AI ("I'm an AI assistant. Let me connect you with a travel expert for the best deals.")

**Qualification Flow:**

```
Customer: "I want to plan a trip"
    ↓
Bot: "I'd love to help! Where are you thinking of traveling?"
    ↓
Customer: "Somewhere with beaches, not too crowded"
    ↓
Bot: "Great taste! When are you planning to travel?"
    ↓
Customer: "December end"
    ↓
Bot: "How many travelers?"
    ↓
Customer: "Just me and my wife"
    ↓
Bot: "What's your approximate budget per person?"
    ↓
Customer: "Around 40k"
    ↓
Bot: "Based on what you've shared, here are some options:
      1. Gokarna, Karnataka — Quiet beaches, great for couples
      2. Varkala, Kerala — Cliff-side beaches, ayurvedic spas
      3. Havelock Island, Andaman — Pristine, adventurous
      Want me to connect you with a travel expert who can
      create a personalized plan?"
    ↓
[Handoff to agent with full qualification context]
```

---

### 2. Intelligent Trip Search

Natural language search that understands travel intent, not just keyword matching.

**Search Query Understanding:**

| Query Type | Example | Extraction Needs |
|-----------|---------|-----------------|
| Destination-focused | "Goa trip packages" | destination, intent |
| Budget-focused | "Beach holiday under 50k" | trip_type, budget_max |
| Activity-focused | "Scuba diving trip in India" | activity, country |
| Season-focused | "Best places to visit in July monsoon" | month, weather_preference |
| Group-focused | "Family vacation with kids activities" | group_type, amenity_needs |
| Emotion-focused | "Relaxing getaway from Mumbai" | origin, mood, distance |
| Comparison | "Goa vs Kerala for honeymoon" | destinations, trip_type, comparison |
| Specific need | "Pet-friendly resorts near Pune" | amenity, location, proximity |

**Search Result Ranking Factors:**

| Factor | Weight | Signal Source |
|--------|--------|--------------|
| Relevance to query | 30% | NLP matching, semantic similarity |
| Customer preference match | 20% | Past searches, bookings, stated preferences |
| Availability | 15% | Real-time inventory check |
| Price fit | 15% | Budget signals from query or profile |
| Seasonality | 10% | Weather, crowd levels, events |
| Popularity/social proof | 10% | Booking frequency, ratings, reviews |

**India-Specific Search Challenges:**
- "Near Mumbai" could mean Lonavala (1hr), Matheran (2hr), or even Goa (flight, 1hr)
- Budget expressions: "cheap", "budget", "affordable", "value for money" all mean different things
- "Good for couples" vs. "honeymoon destination" — different intent despite similarity
- Seasonal ambiguity: "winter" in India means different months for different regions

---

### 3. Personalized Destination Recommendations

Recommendations based on past trips, stated preferences, budget, traveler profile, and seasonal factors.

**Recommendation Dimensions:**

```
┌─────────────────────────────────────────────────────────┐
│              RECOMMENDATION ENGINE                        │
│                                                          │
│  Customer Profile ──┐                                    │
│                     │                                    │
│  Trip History ──────┼──► [Scoring Engine] ──► Ranked    │
│                     │     per destination     Results   │
│  Season/Weather ────┤                                    │
│                     │                                    │
│  Budget Signals ────┤                                    │
│                     │                                    │
│  Social Signals ────┘ (trending, friend activity)        │
│                                                          │
│  ──── Filtering Layer ────                               │
│  × Visa difficulty | × Safety concerns | × Budget range  │
│  × Customer exclusions | × Availability constraints      │
│                                                          │
│  ──── Diversity Injection ────                           │
│  + Surprise factor (20% of results are "unexpected")     │
│  + Seasonal picks (time-sensitive opportunities)         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Recommendation Types:**

| Type | Trigger | Example |
|------|---------|---------|
| **Similar destinations** | Customer viewed or searched a destination | "Liked Goa? Try Gokarna for a quieter experience" |
| **Repeat-enhanced** | Customer booked similar trip before | "You enjoyed Kerala last December. How about Coorg this year?" |
| **Seasonal opportunity** | Optimal travel window for a destination | "Cherry blossoms in Shillong peak in November. Book now!" |
| **Budget-optimized** | Customer's budget can unlock a great deal | "Flight prices to Bali just dropped 30% for your dates" |
| **Social proof** | Popular among similar travelers | "4 of our families with kids loved this Jaipur itinerary" |
| **Complementary** | Based on past trip, suggest natural progression | "After Rajasthan, our customers often explore Gujarat" |

---

### 4. Travel Companion AI (In-Trip Assistance)

AI assistant available during the trip for local recommendations, language translation, and real-time support.

**In-Trip Capabilities:**

| Capability | Description | Connectivity Required |
|-----------|-------------|----------------------|
| **Local recommendations** | Restaurants, attractions, shopping near current location | Medium (cached + live) |
| **Language translation** | Real-time translation for common phrases | Low (cached phrases work offline) |
| **Itinerary management** | "What's next today?", time alerts, transport directions | Low (cached itinerary) |
| **Emergency assistance** | Nearby hospitals, police, embassy contacts | High (live data preferred) |
| **Weather alerts** | Rain warnings, heat advisories, storm alerts | Medium (push notifications) |
| **Currency conversion** | Real-time forex rates for international trips | Medium (cached + periodic update) |
| **Local customs** | "Is tipping expected?", "What should I wear at the temple?" | Low (pre-cached content) |
| **Food recommendations** | Vegetarian-friendly restaurants, local specialties | Medium (cached + search) |

**Offline Capability Design:**
- Pre-trip cache: Key phrases, emergency contacts, itinerary, venue details, cached maps
- Graceful degradation: Show "updated info available, connect to refresh" banner
- Critical always-on: Emergency contacts, itinerary, hotel address, embassy info

---

## TypeScript Data Models

```typescript
// ─── Chatbot Session ────────────────────────────────────────────────

interface ChatbotSession {
  id: string;
  customerId?: string;       // anonymous sessions allowed for pre-login
  anonymousId?: string;

  // State
  status: 'active' | 'paused' | 'completed' | 'handed_off';
  currentTier: 0 | 1 | 2 | 3;
  messages: ChatbotMessage[];

  // Qualification state
  qualification: TripQualification;
  qualificationProgress: number; // 0-1

  // Context
  detectedIntent: CustomerIntent;
  detectedSentiment: CustomerSentiment;
  conversationTopics: string[];

  // Handoff
  handoffTrigger?: HandoffTrigger;
  handoffAgentId?: string;
  handoffContext?: HandoffContext;

  // Metadata
  channel: 'web' | 'whatsapp' | 'mobile_app' | 'instagram' | 'facebook';
  language: string;
  startedAt: Date;
  completedAt?: Date;
  durationSeconds?: number;
}

interface ChatbotMessage {
  id: string;
  role: 'customer' | 'bot' | 'system' | 'agent';
  content: string;
  contentType: 'text' | 'carousel' | 'quick_replies' | 'card' | 'location' | 'image';
  quickReplies?: QuickReply[];
  cards?: ChatCard[];
  metadata?: {
    suggestions?: string[];
    confidence?: number;
    modelUsed?: string;
    processingTimeMs?: number;
  };
  timestamp: Date;
}

interface QuickReply {
  id: string;
  text: string;
  action?: 'select_destination' | 'set_budget' | 'confirm_travelers' | 'request_handoff';
  payload?: Record<string, unknown>;
}

interface ChatCard {
  id: string;
  title: string;
  subtitle: string;
  imageUrl?: string;
  actions: CardAction[];
}

interface CardAction {
  label: string;
  action: 'view_details' | 'select' | 'compare' | 'book' | 'share';
  targetId: string;
}

interface TripQualification {
  destination?: QualificationField<string>;
  dates?: QualificationField<DateRange>;
  travelers?: QualificationField<TravelerInfo>;
  budget?: QualificationField<BudgetRange>;
  tripType?: QualificationField<TripType>;
  specialPreferences?: QualificationField<string[]>;
  originCity?: QualificationField<string>;
}

interface QualificationField<T> {
  value: T;
  confidence: number;
  source: 'customer_stated' | 'inferred' | 'default';
  extractedFrom: string; // message ID
}

interface TravelerInfo {
  adults: number;
  children: number;
  childAges?: number[];
  seniors: number;
  relationships?: string[]; // "couple", "family", "friends"
}

interface BudgetRange {
  min: number;
  max: number;
  currency: 'INR' | 'USD' | 'EUR';
  type: 'per_person' | 'total';
  confidence: number;
}

type TripType =
  | 'beach' | 'hill_station' | 'adventure' | 'pilgrimage'
  | 'honeymoon' | 'family_vacation' | 'weekend_getaway'
  | 'corporate' | 'backpacking' | 'luxury' | 'cultural'
  | 'wildlife' | 'wellness';

interface CustomerIntent {
  primary: 'explore' | 'plan' | 'book' | 'modify' | 'support' | 'complaint' | 'information';
  secondary?: string;
  urgency: 'browsing' | 'interested' | 'ready_to_book' | 'urgent';
}

interface CustomerSentiment {
  overall: 'positive' | 'neutral' | 'negative';
  engagement: 'high' | 'medium' | 'low';
  frustrationRisk: number; // 0-1
}

interface HandoffTrigger {
  type: 'customer_request' | 'low_confidence' | 'complex_inquiry'
      | 'negative_sentiment' | 'booking_intent' | 'complaint'
      | 'tier_limit_reached' | 'vip_customer';
  confidence: number;
  reason: string;
  suggestedPriority: 'low' | 'normal' | 'high' | 'urgent';
}

interface HandoffContext {
  sessionId: string;
  qualificationSummary: string;
  suggestedActions: string[];
  relevantTripOptions?: SearchResult[];
  customerHistory?: CustomerHistory;
  sentimentNotes?: string;
}

// ─── Natural Language Search ────────────────────────────────────────

interface NaturalLanguageSearch {
  id: string;
  customerId?: string;
  anonymousId?: string;

  // Input
  rawQuery: string;
  detectedLanguage: string;
  parsedQuery: ParsedSearchQuery;

  // Execution
  searchStrategy: SearchStrategy;
  filters: SearchFilter[];
  boostFactors: BoostFactor[];

  // Results
  results: SearchResult[];
  resultCount: number;
  hasMore: boolean;

  // Interaction
  customerActions: CustomerSearchAction[];
  convertedToBooking: boolean;
  convertedToTrip: boolean;

  // Metadata
  searchLatencyMs: number;
  modelUsed: string;
  timestamp: Date;
}

interface ParsedSearchQuery {
  // Extracted entities
  destinations?: string[];
  tripTypes?: TripType[];
  activities?: string[];
  budgetRange?: BudgetRange;
  dateRange?: DateRange;
  travelerCount?: number;
  travelerComposition?: string;
  originCity?: string;
  amenities?: string[];
  moodOrTheme?: string; // "romantic", "adventurous", "peaceful"

  // Query classification
  queryType: 'destination_focused' | 'budget_focused' | 'activity_focused'
           | 'season_focused' | 'group_focused' | 'comparison' | 'general';
  intent: 'browse' | 'specific_search' | 'comparison' | 'inspiration';
  ambiguity: string[]; // parts of the query that are unclear
}

interface SearchStrategy {
  primary: 'semantic' | 'keyword' | 'structured' | 'hybrid';
  fallback: SearchStrategy[];
  reranking: 'relevance' | 'popularity' | 'price_asc' | 'price_desc' | 'rating' | 'seasonal';
}

interface SearchFilter {
  field: string;
  operator: 'eq' | 'gte' | 'lte' | 'in' | 'contains' | 'near';
  value: unknown;
  applied: boolean;
  source: 'extracted' | 'customer_set' | 'system_default';
}

interface BoostFactor {
  field: string;
  direction: 'up' | 'down';
  weight: number;
  reason: string;
}

interface SearchResult {
  id: string;
  type: 'destination' | 'trip_package' | 'hotel' | 'activity' | 'itinerary_template';
  title: string;
  description: string;
  imageUrl?: string;

  // Match info
  matchScore: number;
  matchReasons: string[];
  highlightedFields: { field: string; highlight: string }[];

  // Pricing
  priceFrom?: { amount: number; currency: string; perWhat: string };

  // Quick actions
  actions: ('view_details' | 'book' | 'customize' | 'compare' | 'save' | 'share')[];
}

interface CustomerSearchAction {
  action: 'view' | 'click' | 'compare' | 'save' | 'share' | 'book' | 'refine' | 'abandon';
  targetId: string;
  targetType: string;
  timestamp: Date;
}

// ─── Recommendation Engine ──────────────────────────────────────────

interface RecommendationEngine {
  id: string;
  customerId?: string;
  anonymousId?: string;

  // Context
  context: RecommendationContext;
  strategy: RecommendationStrategy;

  // Results
  recommendations: DestinationRecommendation[];
  explanation: RecommendationExplanation;

  // Feedback
  customerInteractions: RecommendationInteraction[];

  timestamp: Date;
}

interface RecommendationContext {
  customerId?: string;
  currentSearch?: string;
  currentTripId?: string;
  pageLocation: 'home' | 'search_results' | 'trip_builder' | 'post_booking' | 'email';
  season: string;
  device: 'mobile' | 'desktop' | 'tablet';
  timeOfDay: 'morning' | 'afternoon' | 'evening' | 'night';
}

interface RecommendationStrategy {
  primary: 'collaborative_filtering' | 'content_based' | 'popularity' | 'hybrid';
  fallback: string[];
  diversityInjection: number; // 0-0.5, fraction of "surprise" recommendations
  freshnessBias: number; // weight towards recently added content
  personalizationLevel: 'none' | 'light' | 'moderate' | 'heavy';
}

interface DestinationRecommendation {
  id: string;
  destinationId: string;
  name: string;
  country: string;
  imageUrl?: string;

  // Why this was recommended
  recommendationType: 'similar' | 'repeat_enhanced' | 'seasonal' | 'budget_optimized'
                      | 'social_proof' | 'complementary' | 'trending' | 'surprise';
  matchReasons: string[];
  matchScore: number;

  // Details
  estimatedBudget: BudgetRange;
  bestSeason: string[];
  tripTypes: TripType[];
  highlights: string[];

  // Social proof
  bookingCount?: number;
  averageRating?: number;
  reviewSnippet?: string;
}

interface RecommendationExplanation {
  summary: string;          // "Based on your Kerala trip + your love for beaches"
  factors: {
    factor: string;
    weight: number;
    description: string;
  }[];
  alternativesConsidered: number;
}

interface RecommendationInteraction {
  recommendationId: string;
  action: 'viewed' | 'clicked' | 'saved' | 'dismissed' | 'shared' | 'booked';
  dwellTimeMs?: number;
  timestamp: Date;
}

// ─── Travel Assistant (In-Trip) ─────────────────────────────────────

interface TravelAssistant {
  id: string;
  tripId: string;
  customerId: string;

  // Trip context
  tripDetails: TripSummary;
  currentDay: number;
  currentLocation?: GeoLocation;
  offlineCacheStatus: OfflineCacheStatus;

  // Capabilities
  capabilities: TravelAssistantCapability[];
  activeAssistance: ActiveAssistance[];

  // Interaction history
  interactions: TravelAssistantInteraction[];

  // Emergency
  emergencyContacts: EmergencyContact[];
  emergencyModeActive: boolean;

  // Metadata
  language: string;
  connectivityStatus: 'online' | 'degraded' | 'offline';
  lastSyncAt: Date;
  createdAt: Date;
}

interface TripSummary {
  tripId: string;
  destination: string;
  dates: DateRange;
  hotel: { name: string; address: string; phone: string; coordinates: GeoLocation };
  itinerary: ItineraryDay[];
  agentContact: { name: string; phone: string; email: string };
  emergencyNumber: string;
}

interface ItineraryDay {
  day: number;
  date: Date;
  activities: ItineraryActivity[];
  notes: string;
}

interface ItineraryActivity {
  id: string;
  name: string;
  time: string;
  location: string;
  duration: string;
  notes: string;
  bookingRef?: string;
}

interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

interface OfflineCacheStatus {
  lastUpdated: Date;
  cachedItems: CacheItem[];
  totalCacheSize: string;
  pendingSyncs: number;
}

interface CacheItem {
  type: 'itinerary' | 'emergency_contacts' | 'phrase_book' | 'venue_details' | 'map_tiles';
  size: string;
  expiresAt: Date;
}

interface TravelAssistantCapability {
  type: 'local_recommendations' | 'translation' | 'itinerary' | 'emergency'
      | 'weather' | 'currency' | 'customs' | 'food' | 'transport';
  available: boolean;
  offlineSupported: boolean;
  lastUpdated: Date;
}

interface ActiveAssistance {
  type: 'weather_alert' | 'next_activity_reminder' | 'transport_direction'
       | 'restaurant_suggestion' | 'language_phrase' | 'customs_tip';
  content: string;
  urgency: 'info' | 'reminder' | 'alert' | 'urgent';
  expiresAt?: Date;
  actionUrl?: string;
}

interface TravelAssistantInteraction {
  id: string;
  type: 'question' | 'recommendation_request' | 'translation' | 'emergency' | 'feedback';
  input: string;
  response: string;
  language: string;
  wasOffline: boolean;
  timestamp: Date;
}

interface EmergencyContact {
  type: 'police' | 'ambulance' | 'fire' | 'embassy' | 'hospital' | 'agent' | 'insurance';
  name: string;
  phone: string;
  address?: string;
  distance?: string;
  notes?: string;
}

// ─── Supporting Types ───────────────────────────────────────────────

interface DateRange {
  start: Date;
  end: Date;
}

interface CustomerHistory {
  previousTrips: number;
  previousDestinations: string[];
  averageSpend: number;
  preferredTripTypes: TripType[];
  loyaltyTier: string;
}
```

---

## Practical Examples

### Example 1: Natural Language Search

```
Customer types: "Find me a beach holiday under 50,000 for 2 in December"
    ↓
Parsed query:
  tripType: beach
  budget: INR 50,000 (total, for 2)
  travelers: 2
  date: December 2026
    ↓
Results:
  ┌──────────────────────────────────────────────────────────┐
  │ 1. Gokarna, Karnataka                    ★ 4.5 (2.1k)   │
  │    Beach + spirituality, quiet alternative to Goa         │
  │    Est. INR 35,000-45,000 for 2 (4 nights)               │
  │    December: Perfect weather, low crowds                   │
  │    [View] [Customize] [Compare]                           │
  │                                                           │
  │ 2. Varkala, Kerala                       ★ 4.6 (1.8k)   │
  │    Cliff-side beaches, ayurvedic wellness                  │
  │    Est. INR 40,000-48,000 for 2 (4 nights)               │
  │    December: Great weather, peak season deals              │
  │    [View] [Customize] [Compare]                           │
  │                                                           │
  │ 3. Diu, Gujarat                          ★ 4.2 (890)     │
  │    Portuguese heritage + pristine beaches                  │
  │    Est. INR 28,000-38,000 for 2 (4 nights)               │
  │    December: Ideal weather, alcohol permitted              │
  │    [View] [Customize] [Compare]                           │
  │                                                           │
  │ 4. Pondicherry                            ★ 4.3 (1.5k)   │
  │    French colonial charm + beach + food                    │
  │    Est. INR 30,000-42,000 for 2 (4 nights)               │
  │    December: Pleasant, great for walking tours             │
  │    [View] [Customize] [Compare]                           │
  │                                                           │
  │ 💡 Note: Goa would be INR 55,000+ in December (peak).     │
  │    These alternatives offer similar vibes within budget.   │
  └──────────────────────────────────────────────────────────┘
```

### Example 2: Recommendation Engine Output

```
Customer: Priya Sharma
  History: Kerala trip (Dec 2024), Rajasthan trip (Oct 2023)
  Preferences: Cultural experiences, vegetarian food, mid-range budget
  Profile: Couple, 30s, Mumbai-based

Personalized recommendations for April 2026:

  ┌──────────────────────────────────────────────────────────┐
  │ RECOMMENDED FOR YOU                                       │
  │                                                           │
  │ Based on your love for cultural trips + Kerala experience │
  │                                                           │
  │ 1. Hampi, Karnataka                       [Cultural]     │
  │    Why: You enjoyed historical Rajasthan. Hampi is a      │
  │    UNESCO site with stunning temples and boulder-strewn   │
  │    landscapes. Great in April (not too hot yet).          │
  │    Est. INR 25,000-35,000 (3 nights, couple)             │
  │                                                           │
  │ 2. Coorg + Mysore combo                   [Nature + Culture] │
  │    Why: Natural extension of your Kerala trip. Coffee     │
  │    plantations + Mysore Palace + local cuisine.           │
  │    Est. INR 30,000-40,000 (4 nights, couple)             │
  │                                                           │
  │ 3. Surprise Pick: Orchha, MP              [Heritage]      │
  │    Why: Hidden gem with Bundela-era palaces. Very few     │
  │    tourists, authentic experiences. Perfect for history    │
  │    lovers who've done the usual circuit.                  │
  │    Est. INR 20,000-28,000 (3 nights, couple)             │
  └──────────────────────────────────────────────────────────┘
```

### Example 3: In-Trip Travel Companion

```
Day 2 of Kerala trip, customer opens companion app:

  ┌──────────────────────────────────────────────────────────┐
  │ YOUR TRIP - Day 2 of 5                                   │
  │ Alleppey Houseboat Day                                    │
  │                                                           │
  │ TODAY'S PLAN                                              │
  │ 09:00 - Board houseboat at Alleppey jetty                 │
  │ 11:00 - Backwater cruising through village canals         │
  │ 13:00 - Traditional Kerala lunch on houseboat             │
  │ 15:00 - Visit Kumarakom Bird Sanctuary                   │
  │ 17:00 - Sunset at Vembanad Lake                          │
  │ 19:30 - Dinner on houseboat                               │
  │                                                           │
  │ 🌤️ Weather: 28°C, partly cloudy. Light rain possible     │
  │    in afternoon. Carry umbrella.                          │
  │                                                           │
  │ 💡 LOCAL TIP: The bird sanctuary is best early morning,   │
  │    but afternoon visits still rewarding. Wear comfortable │
  │    walking shoes.                                         │
  │                                                           │
  │ 🗣️ USEFUL PHRASES (Malayalam):                            │
  │    "Hello" → "Namaskaram"                                 │
  │    "Thank you" → "Nanni"                                  │
  │    "How much?" → "Ethra?"                                 │
  │    "Vegetarian food" → "Vegetarian aaharam"               │
  │                                                           │
  │ 🍽️ NEARBY (within 2km):                                   │
  │    1. Mother's Kitchen ★4.7 - Veg-friendly, local cuisine │
  │    2. Halais Restaurant ★4.5 - Famous for seafood         │
  │    3. Indian Coffee House ★4.3 - Budget, classic Kerala   │
  │                                                           │
  │ 🆘 EMERGENCY: Dial 112 | Nearest hospital: 3.2km         │
  │    Your agent: Ravi (98765-43210)                         │
  └──────────────────────────────────────────────────────────┘
```

---

## India-Specific Considerations

### 1. Language Support Strategy

| Priority | Language | Use Case | Complexity |
|----------|----------|----------|------------|
| P0 | English | Primary interface, most urban customers | Baseline |
| P0 | Hindi | Largest user base, WhatsApp conversations | Medium |
| P1 | Hinglish | Most common actual usage pattern | Hard (code-mixing) |
| P1 | Tamil | South India market, Chennai base | Medium |
| P2 | Bengali | Kolkata and East India | Medium |
| P2 | Marathi | Maharashtra market | Medium |
| P2 | Telugu | Hyderabad and Andhra/Telangana | Medium |
| P3 | Kannada, Malayalam, Gujarati | Regional expansion | Higher effort |

### 2. Payment and Pricing UX

- Always show prices in INR by default (with currency toggle)
- Handle EMI-related queries ("Can I pay in installments?")
- GST-inclusive vs. exclusive pricing transparency
- UPI payment integration context (Google Pay, PhonePe, Paytm references in chat)

### 3. Cultural and Regional Sensitivity

- Pilgrimage recommendations must respect religious calendars (Ramadan, Navratri, etc.)
- Food recommendations must account for vegetarian majority, Jain dietary restrictions, halal requirements
- Destination recommendations should not assume alcohol consumption
- Family-oriented recommendations should account for joint family travel patterns

### 4. Connectivity and Device Constraints

- Many Indian travelers on budget Android devices with limited storage
- 2G/3G connectivity in remote destinations (hill stations, rural areas)
- WhatsApp-first approach: most customer interactions happen on WhatsApp
- Low data usage mode for in-trip companion

---

## Open Problems

### P1: Conversational Intent Accuracy in Hinglish

**Problem:** Hinglish input is linguistically ambiguous. "Mujhe Goa jana hai" could be browsing, planning, or booking intent.
**Research Needed:**
- Hinglish intent classification training data collection
- Multi-turn intent refinement (don't classify on first message, ask clarifying question)
- Intent confidence calibration for code-mixed input

### P2: Recommendation Fairness and Bias

**Problem:** Recommendation engine may over-index on popular destinations (Goa, Manali) and under-represent lesser-known but better-matching options.
**Research Needed:**
- Diversity injection algorithms for recommendation results
- Long-tail destination boosting for niche interests
- A/B testing framework for measuring recommendation diversity vs. conversion

### P3: Handoff Quality

**Problem:** When chatbot hands off to human agent, the agent needs full context. Summaries can miss nuances from a 20-message conversation.
**Research Needed:**
- Conversation summarization quality for handoff context
- Structured qualification data extraction from free-form chat
- Agent-facing UI for quickly reviewing bot conversation history

### P4: In-Trip Reliability

**Problem:** Wrong restaurant recommendation during a trip erodes trust faster than pre-trip errors.
**Research Needed:**
- Recommendation quality scoring based on real-time feedback
- Fallback to agency-curated content when AI confidence is low
- Graceful error recovery ("I'm not sure about this one, let me check with your agent")

### P5: Anonymous vs. Known User Personalization

**Problem:** Pre-login, the system has no customer history. Post-login, it has rich data. How to bridge this gap?
**Research Needed:**
- Anonymous session qualification that persists after login
- Progressive personalization that improves with each interaction
- Cookie/device fingerprinting for anonymous returning visitors (with privacy compliance)

---

## Next Steps

### Immediate (Week 1-2)
1. Map customer journey touchpoints where AI can add value (pre-search, search, booking, in-trip, post-trip)
2. Audit existing customer FAQ to build Tier 0 chatbot knowledge base
3. Study [KAYAK Explore](https://www.kayak.com/explore) for natural language travel search UX
4. Review [Duolingo AI](https://www.duolingo.com) for conversational language learning patterns

### Short-Term (Month 1-2)
1. Prototype natural language trip search (English only, top 20 destinations)
2. Build chatbot Tier 0 (FAQ) and Tier 1 (qualification) for WhatsApp
3. Design recommendation engine data model and scoring algorithm
4. Study [Hopper](https://www.hopper.com) for AI-driven price prediction and recommendation UX

### Medium-Term (Month 2-4)
1. Add Hinglish support to search and chatbot
2. Implement recommendation engine with collaborative filtering
3. Build in-trip companion MVP (itinerary + emergency + basic recommendations)
4. Study [Tripadvisor AI](https://www.tripadvisor.com) for recommendation and review integration

### Platforms to Study

| Platform | What to Learn | Priority |
|----------|--------------|----------|
| KAYAK Explore | Natural language travel search, result presentation | High |
| Hopper | Price prediction, personalized push notifications | High |
| Tripadvisor | Review integration, recommendation diversity | High |
| Duolingo Max | Conversational AI with progressive difficulty | Medium |
| Replika | Long-term conversational AI companion patterns | Medium |
| Wanderlog | Trip planning collaboration, itinerary sharing | Medium |
| Culture Trip | Editorial + AI recommendations blend | Low |
| Rome2Rio | Multi-modal transport search and comparison | Low |

---

## Cross-References

| Related Document | Relevance |
|-----------------|-----------|
| [AI_COPILOT_01_AGENT_ASSIST](./AI_COPILOT_01_AGENT_ASSIST.md) | Chatbot handoff connects to agent assist |
| [AI_COPILOT_02_AUTO_FILL](./AI_COPILOT_02_AUTO_FILL.md) | Chatbot qualification feeds auto-fill pipeline |
| [AI_COPILOT_04_ETHICS](./AI_COPILOT_04_ETHICS.md) | Bias prevention in customer-facing recommendations |
| [AIML_01 LLM Integration](./AIML_01_LLM_INTEGRATION_PATTERNS.md) | LLM architecture for chatbot and search |
| [AIML_02 Decision Intelligence](./AIML_02_DECISION_INTELLIGENCE.md) | Recommendation engine core architecture |
| [AIML_03 NLP Patterns](./AIML_03_NLP_PATTERNS.md) | NLP pipeline for search query understanding |
| [RECOMMENDATIONS_ENGINE_01](./RECOMMENDATIONS_ENGINE_01_ARCHITECTURE.md) | Recommendation system architecture |
| [DESTINATION_01](./DESTINATION_01_CONTENT_MANAGEMENT.md) | Destination content for search results |
| [CUSTOMER_PORTAL_01](./CUSTOMER_PORTAL_01_DASHBOARD.md) | Customer portal where chatbot lives |
| [OFFLINE_01_STRATEGY](./OFFLINE_01_STRATEGY.md) | Offline strategy for in-trip companion |
