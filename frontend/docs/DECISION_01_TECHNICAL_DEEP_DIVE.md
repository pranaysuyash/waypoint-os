# Decision Engine 01: Technical Deep Dive

> Architecture, state machine, confidence scoring, and decision orchestration

---

## Part 1: System Overview

### 1.1 What is the Decision Engine?

The Decision Engine is the AI-powered brain of the Travel Agency Agent workspace. It continuously analyzes trip data, evaluates state, and makes intelligent recommendations to guide agents through the customer journey from inquiry to booking.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DECISION ENGINE ROLE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  INPUTS                                                             │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Trip data (dates, destination, pax, budget)                        │   │
│  │  • Customer interactions (messages, calls)                           │   │
│  │  • Booking status (flights, hotels, activities)                      │   │
│  │  • Agent actions (edits, approvals, communications)                  │   │
│  │  • External signals (price changes, availability)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DECISION ENGINE CORE                                               │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│   │
│  │  │   STATE     │  │  SCORING    │  │ RULE ENGINE │  │   ML       ││   │
│  │  │  MANAGER    │  │  ENGINE     │  │             │  │  MODELS    ││   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│   │
│  │         │                 │                 │                 │       │   │
│  │         └─────────────────┼─────────────────┼─────────────────┘       │   │
│  │                           ▼                 ▼                           │   │
│  │                    ┌─────────────────────────────┐                    │   │
│  │                    │      DECISION ORCHESTRATOR   │                    │   │
│  │                    └─────────────────────────────┘                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OUTPUTS                                                            │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Trip state classification                                        │   │
│  │  • Recommended actions (priority-ranked)                            │   │
│  │  • Confidence scores for each decision                               │   │
│  │  • Risk flags and blockers                                           │   │
│  │  • Next-step guidance                                                │   │
│  │  • Automation opportunities                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DECISION ENGINE ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: DATA INGESTION                                             │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Trip Store (PostgreSQL)                                           │   │
│  │  • Event Stream (Kafka)                                              │   │
│  │  • Real-time Updates (WebSocket)                                     │   │
│  │  • External APIs (Pricing, Availability)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2: STATE MANAGEMENT                                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • State Machine (Current State → Next State)                        │   │
│  │  • Transition Rules (When can we move?)                              │   │
│  │  • State History (Audit trail)                                       │   │
│  │  • State Persistence (Database)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3: SCORING & CONFIDENCE                                       │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Completeness Score (How much data do we have?)                   │   │
│  │  • Confidence Score (How certain are we?)                            │   │
│  │  • Urgency Score (How time-sensitive is this?)                       │   │
│  │  • Risk Score (What could go wrong?)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: DECISION LOGIC                                              │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Rule Engine (If-then-else, deterministic)                         │   │
│  │  • ML Models (Classification, regression, ranking)                    │   │
│  │  • Heuristics (Expert knowledge encoded)                              │   │
│  │  • Ensemble (Combine multiple approaches)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 5: ACTION GENERATION                                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Recommendations (What should happen next?)                        │   │
│  │  • Prioritization (What's most important?)                           │   │
│  │  • Blocking Issues (What must be resolved?)                          │   │
│  │  • Automation Candidates (What can we auto-do?)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 6: OUTPUT & NOTIFICATION                                      │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Decision Panel (UI)                                               │   │
│  │  • Push Notifications                                               │   │
│  │  • Webhooks                                                          │   │
│  │  • Audit Log                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: State Machine

### 2.1 Trip States

The Decision Engine maintains a state machine that represents where each trip is in its lifecycle.

```typescript
/**
 * Complete Trip State Machine
 * States represent the journey from initial inquiry to completed travel
 */
enum TripState {
  // Discovery Phase
  INQUIRY_RECEIVED = 'INQUIRY_RECEIVED',
  DATA_EXTRACTION = 'DATA_EXTRACTION',
  REQUIREMENTS_GATHERING = 'REQUIREMENTS_GATHERING',
  
  // Quoting Phase
  QUOTE_PREPARATION = 'QUOTE_PREPARATION',
  QUOTE_SENT = 'QUOTE_SENT',
  QUOTE_VIEWED = 'QUOTE_VIEWED',
  QUOTE_REVISION = 'QUOTE_REVISION',
  
  // Decision Phase
  AWAITING_DECISION = 'AWAITING_DECISION',
  PRICE_NEGOTIATION = 'PRICE_NEGOTIATION',
  
  // Booking Phase
  BOOKING_INITIATED = 'BOOKING_INITIATED',
  BOOKING_IN_PROGRESS = 'BOOKING_IN_PROGRESS',
  BOOKING_PENDING_CONFIRMATION = 'BOOKING_PENDING_CONFIRMATION',
  
  // Confirmation Phase
  BOOKING_CONFIRMED = 'BOOKING_CONFIRMED',
  DOCUMENTS_GENERATED = 'DOCUMENTS_GENERATED',
  DOCUMENTS_DELIVERED = 'DOCUMENTS_DELIVERED',
  
  // Pre-Travel Phase
  PRE_TRAVEL_CHECKLIST = 'PRE_TRAVEL_CHECKLIST',
  VISA_PROCESSING = 'VISA_PROCESSING',
  INSURANCE_ISSUED = 'INSURANCE_ISSUED',
  
  // Travel Phase
  TRIP_ACTIVE = 'TRIP_ACTIVE',
  
  // Post-Travel Phase
  TRIP_COMPLETED = 'TRIP_COMPLETED',
  FEEDREW_REQUESTED = 'FEEDBACK_REQUESTED',
  FEEDBACK_RECEIVED = 'FEEDBACK_RECEIVED',
  
  // Exception States
  ON_HOLD = 'ON_HOLD',
  CANCELLED = 'CANCELLED',
  REJECTED = 'REJECTED',
  STALE = 'STALE',
  
  // Terminal States
  CLOSED = 'CLOSED',
  ARCHIVED = 'ARCHIVED'
}

/**
 * State Categories for grouping
 */
enum StateCategory {
  DISCOVERY = 'DISCOVERY',           // Learning about customer needs
  QUOTING = 'QUOTING',               // Preparing and sending quotes
  DECISION = 'DECISION',             // Customer deciding
  BOOKING = 'BOOKING',               // Securing reservations
  CONFIRMATION = 'CONFIRMATION',     // Finalizing and documenting
  PRE_TRAVEL = 'PRE_TRAVEL',         // Preparing for travel
  ACTIVE = 'ACTIVE',                 // Trip is happening
  POST_TRAVEL = 'POST_TRAVEL',       // After trip completion
  EXCEPTION = 'EXCEPTION',           // Something unusual
  TERMINAL = 'TERMINAL'              // Journey complete
}
```

### 2.2 State Transition Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE TRANSITION DIAGRAM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌──────────────┐                                                        │
│    │ INQUIRY      │                                                        │
│    │ RECEIVED     │                                                        │
│    └──────┬───────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│    ┌──────────────┐                                                        │
│    │ DATA         │                                                        │
│    │ EXTRACTION   │ ◄────┐ (more info needed)                             │
│    └──────┬───────┘      │                                               │
│           │               │                                               │
│           ▼               │                                               │
│    ┌──────────────┐      │                                               │
│    │ REQUIREMENTS  │──────┘                                               │
│    │ GATHERING    │                                                        │
│    └──────┬───────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│    ┌──────────────┐                                                        │
│    │ QUOTE        │                                                        │
│    │ PREPARATION  │                                                        │
│    └──────┬───────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│    ┌──────────────┐                                                        │
│    │ QUOTE SENT   │                                                        │
│    └──────┬───────┘                                                        │
│           │                                                                 │
│           ├──────────────────────────────────────────────┐                  │
│           ▼                                              ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ QUOTE        │ (customer viewed)              │ AWAITING     │          │
│    │ VIEWED       │───────────────────────────────▶│ DECISION     │          │
│    └──────┬───────┘                              └──────┬───────┘          │
│           │                                             │                  │
│           ▼                                             ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ QUOTE        │ (revision requested)          │ BOOKING      │          │
│    │ REVISION     │◄───────────────────────────────│ INITIATED    │          │
│    └──────┬───────┘                              └──────┬───────┘          │
│           │                                             │                  │
│           │ (accept)                                    │                  │
│           └─────────────────────────────────────────────┘                  │
│                                                          │                  │
│                                                          ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ BOOKING      │◄───────────────────────────────│ BOOKING      │          │
│    │ IN PROGRESS  │ (supplier confirmation)        │ PENDING      │          │
│    └──────┬───────┘                              └──────┬───────┘          │
│           │                                             │                  │
│           ▼                                             ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ BOOKING      │───────────────────────────────▶│ BOOKING      │          │
│    │ CONFIRMED    │                              │ CONFIRMED    │          │
│    └──────┬───────┘                              └──────┬───────┘          │
│           │                                             │                  │
│           ▼                                             ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ DOCUMENTS    │───────────────────────────────▶│ DOCUMENTS    │          │
│    │ GENERATED   │                              │ DELIVERED    │          │
│    └──────┬───────┘                              └──────┬───────┘          │
│           │                                             │                  │
│           ▼                                             ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ PRE-TRAVEL   │───────────────────────────────▶│ TRIP ACTIVE  │          │
│    │ CHECKLIST    │                              └──────┬───────┘          │
│    └──────┬───────┘                                     │                  │
│           │                                             │                  │
│           ▼                                             ▼                  │
│    ┌──────────────┐                              ┌──────────────┐          │
│    │ VISA         │ (optional)                    │ TRIP         │          │
│    │ PROCESSING   │                              │ COMPLETED    │          │
│    └──────────────┘                              └──────┬───────┘          │
│                                                           │                  │
│                                                           ▼                  │
│                                                    ┌──────────────┐          │
│                                                    │ FEEDBACK     │          │
│                                                    │ RECEIVED     │          │
│                                                    └──────┬───────┘          │
│                                                           │                  │
│                                                           ▼                  │
│                                                    ┌──────────────┐          │
│                                                    │ CLOSED       │          │
│                                                    │ / ARCHIVED    │          │
│                                                    └──────────────┘          │
│                                                                             │
│  Exception Transitions (from any active state):                             │
│  ────────────────────────────────────────────────────────────────────────  │
│  → ON_HOLD (customer paused, agent action needed)                           │
│  → STALE (no activity for 30 days)                                         │
│  → CANCELLED (customer cancellation)                                       │
│  → REJECTED (quote declined, no further interest)                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 State Transition Rules

```typescript
/**
 * Rules governing when state transitions can occur
 */
interface TransitionRule {
  from: TripState | TripState[];
  to: TripState;
  condition: TransitionCondition;
  requiredFields: string[];
  autoTransition: boolean;  // Can system do it automatically?
}

const transitionRules: TransitionRule[] = [
  {
    from: TripState.INQUIRY_RECEIVED,
    to: TripState.DATA_EXTRACTION,
    condition: {
      type: 'AUTOMATIC',
      trigger: 'ingestion_complete'
    },
    requiredFields: ['inquiry_source', 'initial_message'],
    autoTransition: true
  },
  {
    from: TripState.DATA_EXTRACTION,
    to: TripState.REQUIREMENTS_GATHERING,
    condition: {
      type: 'SCORE_BASED',
      threshold: 0.7,
      score: 'completeness'
    },
    requiredFields: ['destination', 'dates', 'pax'],
    autoTransition: true
  },
  {
    from: TripState.REQUIREMENTS_GATHERING,
    to: TripState.QUOTE_PREPARATION,
    condition: {
      type: 'SCORE_BASED',
      threshold: 0.85,
      score: 'completeness'
    },
    requiredFields: ['destination', 'dates', 'pax', 'budget', 'preferences'],
    autoTransition: true
  },
  {
    from: TripState.QUOTE_PREPARATION,
    to: TripState.QUOTE_SENT,
    condition: {
      type: 'MANUAL',
      trigger: 'agent_send_quote'
    },
    requiredFields: ['quote_content'],
    autoTransition: false
  },
  {
    from: TripState.QUOTE_SENT,
    to: TripState.QUOTE_VIEWED,
    condition: {
      type: 'EVENT',
      trigger: 'quote_opened'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.QUOTE_VIEWED,
    to: TripState.AWAITING_DECISION,
    condition: {
      type: 'TIME_BASED',
      delay: 30000  // 30 seconds after view
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.AWAITING_DECISION,
    to: TripState.BOOKING_INITIATED,
    condition: {
      type: 'MANUAL',
      trigger: 'booking_confirmed'
    },
    requiredFields: ['customer_approval', 'payment_received'],
    autoTransition: false
  },
  {
    from: [TripState.QUOTE_SENT, TripState.QUOTE_VIEWED, TripState.AWAITING_DECISION],
    to: TripState.QUOTE_REVISION,
    condition: {
      type: 'MANUAL',
      trigger: 'revision_requested'
    },
    requiredFields: ['revision_details'],
    autoTransition: false
  },
  {
    from: TripState.AWAITING_DECISION,
    to: TripState.REJECTED,
    condition: {
      type: 'TIME_BASED',
      delay: 2592000000,  // 30 days
      unless: 'customer_responded'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.BOOKING_INITIATED,
    to: TripState.BOOKING_IN_PROGRESS,
    condition: {
      type: 'AUTOMATIC',
      trigger: 'supplier_bookings_started'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.BOOKING_IN_PROGRESS,
    to: TripState.BOOKING_PENDING_CONFIRMATION,
    condition: {
      type: 'ALL_BOOKINGS_SUBMITTED'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.BOOKING_PENDING_CONFIRMATION,
    to: TripState.BOOKING_CONFIRMED,
    condition: {
      type: 'ALL_CONFIRMATIONS_RECEIVED'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.BOOKING_CONFIRMED,
    to: TripState.DOCUMENTS_GENERATED,
    condition: {
      type: 'AUTOMATIC',
      trigger: 'documents_ready'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.DOCUMENTS_GENERATED,
    to: TripState.DOCUMENTS_DELIVERED,
    condition: {
      type: 'ALL_DELIVERIES_SUCCESSFUL'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.DOCUMENTS_DELIVERED,
    to: TripState.PRE_TRAVEL_CHECKLIST,
    condition: {
      type: 'TIME_BASED',
      trigger: 'X_days_before_travel',
      days: 30
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.PRE_TRAVEL_CHECKLIST,
    to: TripState.VISA_PROCESSING,
    condition: {
      type: 'CONDITIONAL',
      check: 'visa_required'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.PRE_TRAVEL_CHECKLIST,
    to: TripState.TRIP_ACTIVE,
    condition: {
      type: 'TIME_BASED',
      trigger: 'travel_date_arrived'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.TRIP_ACTIVE,
    to: TripState.TRIP_COMPLETED,
    condition: {
      type: 'TIME_BASED',
      trigger: 'return_date_passed'
    },
    requiredFields: [],
    autoTransition: true
  },
  {
    from: TripState.TRIP_COMPLETED,
    to: TripState.FEEDBACK_REQUESTED,
    condition: {
      type: 'AUTOMATIC',
      trigger: 'post_trip_elapsed',
      delay: 86400000  // 24 hours
    },
    requiredFields: [],
    autoTransition: true
  }
];
```

---

## Part 3: Scoring System

### 3.1 Completeness Score

Measures how much required information we have for a trip.

```typescript
/**
 * Completeness Score Calculation
 * Range: 0-100, where 100 means all required data is present
 */
interface CompletenessScore {
  overall: number;           // 0-100
  breakdown: {
    essential: number;       // Critical path items (dates, destination, pax)
    preferences: number;     // Customer preferences
    logistics: number;       // Contact details, pickup info
    financial: number;       // Budget, payment info
  };
  missing: {
    critical: string[];      // Must-have items missing
    recommended: string[];   // Should-have items missing
    optional: string[];      // Nice-to-have items missing
  };
}

const completenessWeights = {
  essential: 0.40,      // 40% - Core trip details
  preferences: 0.25,    // 25% - What customer wants
  logistics: 0.20,      // 20% - How to reach/coordinate
  financial: 0.15       // 15% - Budget and payment
};

const requiredFields = {
  essential: [
    'destination', 'destination_country',
    'travel_date_from', 'travel_date_to',
    'pax_adults', 'pax_children', 'pax_infants'
  ],
  preferences: [
    'trip_type', 'budget_range',
    'accommodation_preference', 'meal_preference'
  ],
  logistics: [
    'customer_name', 'customer_email', 'customer_phone',
    'origin_city', 'pickup_location'
  ],
  financial: [
    'budget_estimate', 'payment_method_preference'
  ]
};

function calculateCompleteness(tripData: TripData): CompletenessScore {
  const scores = {
    essential: calculateFieldCompleteness(tripData, requiredFields.essential),
    preferences: calculateFieldCompleteness(tripData, requiredFields.preferences),
    logistics: calculateFieldCompleteness(tripData, requiredFields.logistics),
    financial: calculateFieldCompleteness(tripData, requiredFields.financial)
  };

  const overall = 
    scores.essential * completenessWeights.essential +
    scores.preferences * completenessWeights.preferences +
    scores.logistics * completenessWeights.logistics +
    scores.financial * completenessWeights.financial;

  const missing = identifyMissingFields(tripData);

  return {
    overall: Math.round(overall),
    breakdown: scores,
    missing
  };
}
```

### 3.2 Confidence Score

Measures how certain the Decision Engine is about its recommendations.

```typescript
/**
 * Confidence Score Calculation
 * Range: 0-100, where 100 means highly certain
 */
interface ConfidenceScore {
  overall: number;           // 0-100
  breakdown: {
    dataQuality: number;     // Based on completeness and accuracy
    historicalMatch: number;  // How similar past trips performed
    modelAgreement: number;   // Do different models agree?
    timing: number;           // Is this a good time to decide?
  };
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
}

function calculateConfidence(
  tripData: TripData,
  historicalData: HistoricalTrip[],
  modelOutputs: ModelOutput[]
): ConfidenceScore {
  // Data Quality: Based on completeness score
  const dataQuality = calculateCompleteness(tripData).overall;

  // Historical Match: How many similar trips were successful?
  const similarTrips = findSimilarTrips(tripData, historicalData, 10);
  const historicalMatch = similarTrips.length > 0
    ? (similarTrips.filter(t => t.converted).length / similarTrips.length) * 100
    : 50; // Neutral if no similar trips

  // Model Agreement: Do ML models agree with rule-based decisions?
  const modelAgreement = calculateModelConsensus(modelOutputs);

  // Timing: Is this an optimal time for customer to make decisions?
  const timing = calculateTimingScore(tripData);

  const overall = (
    dataQuality * 0.30 +
    historicalMatch * 0.25 +
    modelAgreement * 0.25 +
    timing * 0.20
  );

  let level: ConfidenceScore['level'];
  if (overall >= 90) level = 'VERY_HIGH';
  else if (overall >= 70) level = 'HIGH';
  else if (overall >= 50) level = 'MEDIUM';
  else level = 'LOW';

  return {
    overall: Math.round(overall),
    breakdown: {
      dataQuality,
      historicalMatch,
      modelAgreement,
      timing
    },
    level
  };
}
```

### 3.3 Urgency Score

Measures how time-sensitive this trip is.

```typescript
/**
 * Urgency Score Calculation
 * Range: 0-100, where 100 means immediate action required
 */
interface UrgencyScore {
  overall: number;           // 0-100
  factors: {
    daysUntilTravel: number; // Closer = more urgent
    leadTimeStatus: string;   // 'CRITICAL', 'SHORT', 'NORMAL', 'LONG'
    bookingWindow: string;    // Is now a good time to book?
    seasonality: number;      // Peak season = more urgent
  };
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

function calculateUrgency(tripData: TripData): UrgencyScore {
  const daysUntilTravel = daysBetween(new Date(), tripData.travelDateFrom);
  
  let leadTimeStatus: string;
  let leadTimeScore: number;
  
  if (daysUntilTravel < 7) {
    leadTimeStatus = 'CRITICAL';
    leadTimeScore = 100;
  } else if (daysUntilTravel < 14) {
    leadTimeStatus = 'SHORT';
    leadTimeScore = 80;
  } else if (daysUntilTravel < 30) {
    leadTimeStatus = 'NORMAL';
    leadTimeScore = 50;
  } else {
    leadTimeStatus = 'LONG';
    leadTimeScore = 20;
  }

  // Booking window: Are we in optimal booking period?
  const optimalDaysBefore = getOptimalBookingDays(tripData.destination_type);
  const daysFromOptimal = Math.abs(daysUntilTravel - optimalDaysBefore);
  const bookingWindowScore = Math.max(0, 100 - (daysFromOptimal * 2));

  // Seasonality: Peak season = higher urgency
  const seasonality = isPeakSeason(tripData.destination, tripData.travelDateFrom) ? 80 : 40;

  const overall = (
    leadTimeScore * 0.50 +
    bookingWindowScore * 0.30 +
    seasonality * 0.20
  );

  let level: UrgencyScore['level'];
  if (overall >= 80) level = 'CRITICAL';
  else if (overall >= 60) level = 'HIGH';
  else if (overall >= 40) level = 'MEDIUM';
  else level = 'LOW';

  return {
    overall: Math.round(overall),
    factors: {
      daysUntilTravel,
      leadTimeStatus,
      bookingWindow: daysFromOptimal < 7 ? 'OPTIMAL' : daysFromOptimal < 21 ? 'GOOD' : 'SUBOPTIMAL',
      seasonality
    },
    level
  };
}
```

### 3.4 Risk Score

Measures potential issues that could block conversion.

```typescript
/**
 * Risk Score Calculation
 * Range: 0-100, where 100 means high risk
 */
interface RiskScore {
  overall: number;           // 0-100
  breakdown: {
    budget: number;          // Budget vs. market prices
    availability: number;    // Supply constraints
    complexity: number;      # Trip complexity
    season: number;          // Seasonal challenges
    customer: number;        // Customer behavior patterns
  };
  flags: RiskFlag[];
}

interface RiskFlag {
  type: 'BUDGET' | 'AVAILABILITY' | 'VISA' | 'SEASON' | 'COMPLEXITY';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  suggestion?: string;
}

function calculateRisk(tripData: TripData, marketData: MarketData): RiskScore {
  const flags: RiskFlag[] = [];

  // Budget Risk
  const budgetRisk = calculateBudgetRisk(tripData, marketData);
  if (budgetRisk > 50) {
    flags.push({
      type: 'BUDGET',
      severity: budgetRisk > 80 ? 'CRITICAL' : 'HIGH',
      message: `Budget may be insufficient for ${tripData.destination}`,
      suggestion: 'Consider adjusting travel dates or exploring alternatives'
    });
  }

  // Availability Risk
  const availabilityRisk = calculateAvailabilityRisk(tripData, marketData);
  if (availabilityRisk > 50) {
    flags.push({
      type: 'AVAILABILITY',
      severity: availabilityRisk > 80 ? 'CRITICAL' : 'HIGH',
      message: 'Limited availability for selected dates',
      suggestion: 'Consider flexible dates or nearby alternatives'
    });
  }

  // Visa Risk
  const visaRisk = calculateVisaRisk(tripData);
  if (visaRisk > 0) {
    flags.push({
      type: 'VISA',
      severity: visaRisk > 70 ? 'HIGH' : 'MEDIUM',
      message: 'Visa required with processing time needed',
      suggestion: 'Initiate visa process immediately'
    });
  }

  // Season Risk
  const seasonRisk = isPeakSeason(tripData.destination, tripData.travelDateFrom) ? 70 : 30;
  if (seasonRisk > 50) {
    flags.push({
      type: 'SEASON',
      severity: 'MEDIUM',
      message: 'Peak season travel - expect higher prices',
      suggestion: 'Book immediately to secure best rates'
    });
  }

  // Complexity Risk
  const complexityRisk = calculateComplexityRisk(tripData);
  if (complexityRisk > 60) {
    flags.push({
      type: 'COMPLEXITY',
      severity: 'MEDIUM',
      message: 'Complex trip with multiple moving parts',
      suggestion: 'Allow extra time for planning and confirmations'
    });
  }

  // Customer Risk (based on past behavior)
  const customerRisk = await calculateCustomerRisk(tripData.customer_id);
  if (customerRisk > 60) {
    flags.push({
      type: 'COMPLEXITY',
      severity: customerRisk > 80 ? 'HIGH' : 'MEDIUM',
      message: 'Customer has history of cancellations',
      suggestion: 'Consider flexible booking options'
    });
  }

  const overall = Math.max(
    budgetRisk * 0.30,
    availabilityRisk * 0.25,
    visaRisk * 0.20,
    seasonRisk * 0.10,
    complexityRisk * 0.10,
    customerRisk * 0.05
  );

  return {
    overall: Math.round(overall),
    breakdown: {
      budget: budgetRisk,
      availability: availabilityRisk,
      complexity: complexityRisk,
      season: seasonRisk,
      customer: customerRisk
    },
    flags
  };
}
```

---

## Part 4: Decision Logic

### 4.1 Rule Engine

Deterministic rules that always produce the same output for given inputs.

```typescript
/**
 * Rule Engine Structure
 */
interface Rule {
  id: string;
  name: string;
  priority: number;        // Higher = evaluated first
  condition: RuleCondition;
  action: RuleAction;
  category: 'STATE' | 'RECOMMENDATION' | 'ALERT' | 'AUTOMATION';
}

interface RuleCondition {
  type: 'FIELD' | 'SCORE' | 'TIME' | 'EVENT' | 'COMPOSITE';
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'matches';
  field?: string;
  threshold?: number;
  value?: any;
  rules?: RuleCondition[];  // For COMPOSITE type
}

interface RuleAction {
  type: 'SET_STATE' | 'ADD_RECOMMENDATION' | 'SEND_ALERT' | 'TRIGGER_AUTOMATION';
  target?: string;
  value?: any;
}

/**
 * Example Rules
 */
const decisionRules: Rule[] = [
  // STATE RULES
  {
    id: 'auto-quote-ready',
    name: 'Move to quote preparation when data is complete',
    priority: 100,
    category: 'STATE',
    condition: {
      type: 'SCORE',
      field: 'completeness',
      operator: 'gte',
      threshold: 85
    },
    action: {
      type: 'SET_STATE',
      value: 'QUOTE_PREPARATION'
    }
  },
  {
    id: 'detect-stale-inquiry',
    name: 'Mark inquiry as stale if no activity for 7 days',
    priority: 90,
    category: 'STATE',
    condition: {
      type: 'TIME',
      field: 'last_activity',
      operator: 'gte',
      threshold: 604800000  // 7 days in ms
    },
    action: {
      type: 'SET_STATE',
      value: 'STALE'
    }
  },
  {
    id: 'detect-urgent-travel',
    name: 'Flag urgent travel when <14 days',
    priority: 95,
    category: 'ALERT',
    condition: {
      type: 'SCORE',
      field: 'urgency',
      operator: 'gte',
      threshold: 80
    },
    action: {
      type: 'SEND_ALERT',
      value: {
        level: 'HIGH',
        message: 'Urgent travel date - immediate attention needed'
      }
    }
  },
  // RECOMMENDATION RULES
  {
    id: 'suggest-early-book',
    name: 'Suggest booking now when prices are favorable',
    priority: 70,
    category: 'RECOMMENDATION',
    condition: {
      type: 'COMPOSITE',
      rules: [
        { type: 'FIELD', field: 'state', operator: 'eq', value: 'QUOTE_VIEWED' },
        { type: 'FIELD', field: 'price_trend', operator: 'eq', value: 'RISING' }
      ],
      logic: 'AND'
    },
    action: {
      type: 'ADD_RECOMMENDATION',
      value: {
        priority: 'HIGH',
        title: 'Book Now to Lock in Prices',
        description: 'Prices are trending upward. Secure current rates by booking today.',
        action: 'INITIATE_BOOKING'
      }
    }
  },
  {
    id: 'suggest-follow-up',
    name: 'Suggest follow-up after quote sent',
    priority: 60,
    category: 'RECOMMENDATION',
    condition: {
      type: 'TIME',
      field: 'quote_sent_at',
      operator: 'gte',
      threshold: 86400000  // 24 hours
    },
    action: {
      type: 'ADD_RECOMMENDATION',
      value: {
        priority: 'MEDIUM',
        title: 'Follow Up on Quote',
        description: 'Customer has not responded to quote. Consider a follow-up message.',
        action: 'SEND_FOLLOW_UP'
      }
    }
  },
  // AUTOMATION RULES
  {
    id: 'auto-send-reminder',
    name: 'Automatically send reminder if quote not viewed',
    priority: 50,
    category: 'AUTOMATION',
    condition: {
      type: 'COMPOSITE',
      rules: [
        { type: 'FIELD', field: 'state', operator: 'eq', value: 'QUOTE_SENT' },
        { type: 'TIME', field: 'quote_sent_at', operator: 'gte', threshold: 172800000 }, // 48 hours
        { type: 'FIELD', field: 'quote_viewed', operator: 'eq', value: false }
      ],
      logic: 'AND'
    },
    action: {
      type: 'TRIGGER_AUTOMATION',
      value: 'SEND_QUOTE_REMINDER'
    }
  },
  {
    id: 'auto-visa-alert',
    name: 'Alert about visa processing time',
    priority: 85,
    category: 'ALERT',
    condition: {
      type: 'FIELD',
      field: 'visa_required',
      operator: 'eq',
      value: true
    },
    action: {
      type: 'SEND_ALERT',
      value: {
        level: 'HIGH',
        message: 'Visa required - start process immediately',
        target: 'AGENT'
      }
    }
  }
];

/**
 * Rule Engine Evaluator
 */
class RuleEngine {
  private rules: Rule[];

  constructor(rules: Rule[]) {
    // Sort by priority (highest first)
    this.rules = rules.sort((a, b) => b.priority - a.priority);
  }

  evaluate(tripContext: TripContext): DecisionResult {
    const actions: Action[] = [];
    const matchedRules: string[] = [];

    for (const rule of this.rules) {
      if (this.evaluateCondition(rule.condition, tripContext)) {
        actions.push(rule.action);
        matchedRules.push(rule.id);

        // Stop evaluating lower priority rules if this was a state change
        if (rule.category === 'STATE' && rule.action.type === 'SET_STATE') {
          break;
        }
      }
    }

    return {
      actions,
      matchedRules,
      timestamp: new Date()
    };
  }

  private evaluateCondition(condition: RuleCondition, context: TripContext): boolean {
    switch (condition.type) {
      case 'FIELD':
        return this.evaluateFieldCondition(condition, context);
      case 'SCORE':
        return this.evaluateScoreCondition(condition, context);
      case 'TIME':
        return this.evaluateTimeCondition(condition, context);
      case 'EVENT':
        return this.evaluateEventCondition(condition, context);
      case 'COMPOSITE':
        return this.evaluateCompositeCondition(condition, context);
      default:
        return false;
    }
  }

  private evaluateFieldCondition(condition: RuleCondition, context: TripContext): boolean {
    const fieldValue = this.getNestedValue(context, condition.field!);
    return this.compare(fieldValue, condition.operator, condition.value);
  }

  private evaluateScoreCondition(condition: RuleCondition, context: TripContext): boolean {
    const scoreValue = context.scores[condition.field!]?.overall || 0;
    return this.compare(scoreValue, condition.operator, condition.threshold!);
  }

  private evaluateTimeCondition(condition: RuleCondition, context: TripContext): boolean {
    const fieldValue = this.getNestedValue(context, condition.field!);
    if (!fieldValue) return false;
    
    const elapsed = Date.now() - new Date(fieldValue).getTime();
    return this.compare(elapsed, condition.operator, condition.threshold!);
  }

  private evaluateCompositeCondition(condition: RuleCondition, context: TripContext): boolean {
    if (!condition.rules || condition.rules.length === 0) return true;
    
    const results = condition.rules.map(rule => this.evaluateCondition(rule, context));
    
    // Default to AND logic
    const logic = (condition as any).logic || 'AND';
    
    return logic === 'AND'
      ? results.every(r => r)
      : results.some(r => r);
  }

  private compare(actual: any, operator: string, expected: any): boolean {
    switch (operator) {
      case 'eq': return actual === expected;
      case 'ne': return actual !== expected;
      case 'gt': return actual > expected;
      case 'gte': return actual >= expected;
      case 'lt': return actual < expected;
      case 'lte': return actual <= expected;
      case 'contains': return Array.isArray(actual) ? actual.includes(expected) : false;
      case 'matches': return new RegExp(expected).test(actual);
      default: return false;
    }
  }

  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }
}
```

### 4.2 ML Models

Machine learning models for pattern recognition and prediction.

```typescript
/**
 * ML Model Types for Decision Engine
 */
interface MLModel {
  name: string;
  type: 'CLASSIFICATION' | 'REGRESSION' | 'RANKING' | 'CLUSTERING';
  input: ModelInput;
  output: ModelOutput;
  confidence: number;
}

/**
 * Conversion Probability Model
 * Predicts likelihood of quote converting to booking
 */
class ConversionProbabilityModel {
  async predict(tripContext: TripContext): Promise<number> {
    const features = {
      // Customer features
      customer_history_score: tripContext.customer.history_score,
      previous_bookings: tripContext.customer.previous_bookings,
      loyalty_tier: tripContext.customer.loyalty_tier,
      
      // Trip features
      destination_type: tripContext.trip.destination_type,  // domestic/international
      duration_days: tripContext.trip.duration_days,
      advance_days: tripContext.trip.advance_days,
      pax_count: tripContext.trip.pax_count,
      
      // Quote features
      price_vs_budget: tripContext.quote.price / tripContext.trip.budget,
      price_competitiveness: tripContext.quote.competitiveness_score,
      response_time_hours: tripContext.quote.response_time_hours,
      
      // Engagement features
      quote_viewed: tripContext.engagement.quote_viewed ? 1 : 0,
      views_count: tripContext.engagement.views_count,
      last_view_hours_ago: tripContext.engagement.last_view_hours_ago,
      clicks_count: tripContext.engagement.clicks_count,
      
      // Market features
      season_demand: tripContext.market.demand_score,
      price_trend: tripContext.market.price_trend,  // rising/stable/falling
      availability_score: tripContext.market.availability_score
    };

    // Call ML service
    const prediction = await this.model.predict(features);
    return prediction.probability;
  }
}

/**
 * Churn Risk Model
 * Predicts likelihood of customer disengaging
 */
class ChurnRiskModel {
  async predict(tripContext: TripContext): Promise<number> {
    const features = {
      // Time since last activity
      last_activity_hours: tripContext.engagement.last_activity_hours,
      
      // Communication patterns
      messages_sent: tripContext.engagement.messages_sent,
      messages_received: tripContext.engagement.messages_received,
      response_rate: tripContext.engagement.response_rate,
      
      // Comparison behavior
      competitor_quotes: tripContext.engagement.competitor_quotes_requested,
      
      // Quote interactions
      quote_views: tripContext.engagement.views_count,
      time_to_first_view: tripContext.engagement.time_to_first_view_hours,
      
      // Customer profile
      new_customer: tripContext.customer.is_new ? 1 : 0,
      budget_variance: Math.abs(tripContext.quote.price - tripContext.trip.budget) / tripContext.trip.budget
    };

    const prediction = await this.model.predict(features);
    return prediction.probability;
  }
}

/**
 // Next Best Action Model
 * Recommends the most effective action to take
 */
class NextBestActionModel {
  async predict(tripContext: TripContext): Promise<ActionRecommendation[]> {
    const actions = [
      { action: 'SEND_FOLLOW_UP', expected_impact: 0 },
      { action: 'OFFER_DISCOUNT', expected_impact: 0 },
      { action: 'SEND_ALTERNATIVES', expected_impact: 0 },
      { action: 'CALL_CUSTOMER', expected_impact: 0 },
      { action: 'WAIT', expected_impact: 0 }
    ];

    for (const action of actions) {
      const features = {
        action_type: action.action,
        customer_state: tripContext.state,
        days_since_quote: tripContext.engagement.days_since_quote,
        quote_viewed: tripContext.engagement.quote_viewed ? 1 : 0,
        price_sensitivity: tripContext.customer.price_sensitivity,
        urgency: tripContext.scores.urgency.overall
      };

      action.expected_impact = await this.model.predict(features);
    }

    // Sort by expected impact
    return actions
      .sort((a, b) => b.expected_impact - a.expected_impact)
      .slice(0, 3)
      .map(a => ({
        action: a.action,
        confidence: a.expected_impact,
        reason: this.getReasonForAction(a.action, tripContext)
      }));
  }
}
```

### 4.3 Ensemble Decision Making

Combining rules and ML for robust decisions.

```typescript
/**
 * Ensemble Decision Engine
 * Combines rule-based and ML-based approaches
 */
class EnsembleDecisionEngine {
  private ruleEngine: RuleEngine;
  private mlModels: {
    conversion: ConversionProbabilityModel;
    churn: ChurnRiskModel;
    nextAction: NextBestActionModel;
  };

  async decide(tripContext: TripContext): Promise<DecisionOutput> {
    // Get rule-based decisions
    const ruleResult = this.ruleEngine.evaluate(tripContext);

    // Get ML predictions
    const mlPredictions = await Promise.all([
      this.mlModels.conversion.predict(tripContext),
      this.mlModels.churn.predict(tripContext),
      this.mlModels.nextAction.predict(tripContext)
    ]);

    const [conversionProb, churnProb, recommendedActions] = mlPredictions;

    // Combine into unified decision
    return {
      state: this.determineState(ruleResult, tripContext),
      recommendations: this.generateRecommendations(
        ruleResult.actions,
        recommendedActions,
        tripContext
      ),
      alerts: this.generateAlerts(ruleResult.actions, churnProb, tripContext),
      confidence: this.calculateOverallConfidence(ruleResult, mlPredictions),
      scores: tripContext.scores,
      metadata: {
        rulesMatched: ruleResult.matchedRules,
        conversionProbability: conversionProb,
        churnRisk: churnProb
      }
    };
  }

  private determineState(ruleResult: DecisionResult, context: TripContext): TripState {
    // If rules explicitly set a state, use that
    const stateAction = ruleResult.actions.find(a => a.type === 'SET_STATE');
    if (stateAction) {
      return stateAction.value as TripState;
    }

    // Otherwise, use current state from context
    return context.state;
  }

  private generateRecommendations(
    ruleActions: Action[],
    mlActions: ActionRecommendation[],
    context: TripContext
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Add ML-recommended actions
    for (const mlAction of mlActions) {
      recommendations.push({
        id: `ml-${mlAction.action.toLowerCase()}`,
        priority: this.mapConfidenceToPriority(mlAction.confidence),
        title: this.formatActionTitle(mlAction.action),
        description: mlAction.reason,
        action: mlAction.action,
        confidence: mlAction.confidence,
        source: 'ML'
      });
    }

    // Add rule-based recommendations
    for (const ruleAction of ruleActions) {
      if (ruleAction.type === 'ADD_RECOMMENDATION') {
        recommendations.push({
          id: `rule-${ruleAction.value.action.toLowerCase()}`,
          priority: ruleAction.value.priority,
          title: ruleAction.value.title,
          description: ruleAction.value.description,
          action: ruleAction.value.action,
          confidence: 95,  // Rules are high confidence
          source: 'RULE'
        });
      }
    }

    // Sort by priority and confidence
    return recommendations
      .sort((a, b) => {
        const priorityOrder = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
        if (priorityDiff !== 0) return priorityDiff;
        return b.confidence - a.confidence;
      })
      .slice(0, 5);  // Top 5 recommendations
  }

  private generateAlerts(
    ruleActions: Action[],
    churnProb: number,
    context: TripContext
  ): Alert[] {
    const alerts: Alert[] = [];

    // Add rule-based alerts
    for (const ruleAction of ruleActions) {
      if (ruleAction.type === 'SEND_ALERT') {
        alerts.push({
          level: ruleAction.value.level,
          message: ruleAction.value.message,
          target: ruleAction.value.target || 'AGENT',
          source: 'RULE'
        });
      }
    }

    // Add ML-based alerts
    if (churnProb > 0.7) {
      alerts.push({
        level: 'HIGH',
        message: `High churn risk detected (${Math.round(churnProb * 100)}% probability)`,
        target: 'AGENT',
        source: 'ML',
        suggestion: 'Consider proactive follow-up or special offer'
      });
    }

    // Add risk-based alerts
    if (context.scores.risk.overall > 70) {
      alerts.push({
        level: 'MEDIUM',
        message: 'Multiple risk factors detected',
        target: 'AGENT',
        source: 'SYSTEM',
        details: context.scores.risk.flags
      });
    }

    return alerts;
  }

  private calculateOverallConfidence(
    ruleResult: DecisionResult,
    mlPredictions: number[]
  ): number {
    // Weight different sources
    const ruleConfidence = ruleResult.matchedRules.length > 0 ? 90 : 50;
    const mlConfidence = mlPredictions[0] * 100;  // Conversion probability

    return (ruleConfidence * 0.4 + mlConfidence * 0.6);
  }

  private mapConfidenceToPriority(confidence: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (confidence >= 80) return 'CRITICAL';
    if (confidence >= 60) return 'HIGH';
    if (confidence >= 40) return 'MEDIUM';
    return 'LOW';
  }

  private formatActionTitle(action: string): string {
    const titles = {
      'SEND_FOLLOW_UP': 'Send Follow-Up Message',
      'OFFER_DISCOUNT': 'Offer Special Discount',
      'SEND_ALTERNATIVES': 'Present Alternative Options',
      'CALL_CUSTOMER': 'Call Customer',
      'WAIT': 'Wait for Customer Response'
    };
    return titles[action] || action;
  }

  private getReasonForAction(action: string, context: TripContext): string {
    // Generate contextual reason based on trip state and data
    const reasons = {
      'SEND_FOLLOW_UP': `Customer hasn't responded in ${context.engagement.days_since_quote} days`,
      'OFFER_DISCOUNT': 'Price is above budget, discount may increase conversion',
      'SEND_ALTERNATIVES': 'Current options have limited availability',
      'CALL_CUSTOMER': 'High-value customer, personal touch recommended',
      'WAIT': 'Customer recently viewed, give time to consider'
    };
    return reasons[action] || 'Recommended based on trip analysis';
  }
}
```

---

## Part 5: Decision Output Structure

### 5.1 Complete Decision Output

```typescript
/**
 * Complete Decision Engine Output
 */
interface DecisionOutput {
  // Current state determination
  state: TripState;
  previousState: TripState;
  stateTransition: {
    transition: string;
    reason: string;
    timestamp: Date;
  };

  // Recommendations (priority-ranked)
  recommendations: Recommendation[];

  // Alerts and warnings
  alerts: Alert[];

  // Scores
  scores: {
    completeness: CompletenessScore;
    confidence: ConfidenceScore;
    urgency: UrgencyScore;
    risk: RiskScore;
  };

  // Confidence in overall decision
  confidence: number;

  // Metadata
  metadata: {
    decisionId: string;
    timestamp: Date;
    processingTime: number;  // milliseconds
    rulesMatched: string[];
    modelPredictions: {
      conversion: number;
      churn: number;
    };
  };
}

interface Recommendation {
  id: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  description: string;
  action: string;
  confidence: number;
  source: 'RULE' | 'ML' | 'HYBRID';
  estimatedImpact?: {
    conversion: number;  // Expected conversion lift
    revenue: number;     // Expected revenue impact
  };
}

interface Alert {
  level: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  target: 'AGENT' | 'CUSTOMER' | 'SYSTEM';
  source: string;
  suggestion?: string;
  details?: any;
}
```

### 5.2 Decision Panel API Response

```typescript
/**
 * API Response Format for Decision Panel
 */
interface DecisionPanelResponse {
  success: true;
  data: {
    trip: {
      id: string;
      reference: string;
      state: TripState;
      stateLabel: string;
      stateColor: string;  // For UI theming
    };

    scores: {
      completeness: {
        overall: number;
        label: string;
        color: string;
        missing: {
          critical: string[];
          recommended: string[];
        };
      };
      confidence: {
        overall: number;
        label: string;
        color: string;
      };
      urgency: {
        overall: number;
        label: string;
        color: string;
        daysUntilTravel?: number;
      };
      risk: {
        overall: number;
        label: string;
        color: string;
        flags: Alert[];
      };
    };

    recommendations: Array<{
      id: string;
      priority: string;
      priorityOrder: number;
      title: string;
      description: string;
      action: string;
      actionLabel: string;
      confidence: number;
      source: string;
      icon?: string;
      estimatedImpact?: string;
    }>;

    alerts: Array<{
      id: string;
      level: string;
      icon: string;
      message: string;
      target: string;
      dismissible: boolean;
      actions?: Array<{
        label: string;
        action: string;
      }>;
    }>;

    timeline: {
      currentState: {
        state: string;
        since: Date;
        duration: string;
      };
      previousStates: Array<{
        state: string;
        from: Date;
        to: Date;
        duration: string;
      }>;
      nextStates: Array<{
        state: string;
        likelihood: number;
        blocking?: string[];
      }>;
    };

    automation: {
      available: Array<{
        id: string;
        name: string;
        description: string;
        triggered: boolean;
        triggerReason?: string;
      }>;
      recentlyTriggered: Array<{
        id: string;
        name: string;
        triggeredAt: Date;
        result: string;
      }>;
    };
  };
}
```

---

## Part 6: Implementation Architecture

### 6.1 Service Structure

```
src/decision-engine/
├── core/
│   ├── DecisionEngine.ts          # Main orchestrator
│   ├── StateMachine.ts             # State management
│   ├── RuleEngine.ts              # Rule evaluation
│   └── EnsembleEngine.ts          # ML + Rule combination
├── models/
│   ├── ConversionModel.ts         # Conversion prediction
│   ├── ChurnModel.ts              # Churn prediction
│   └── NextActionModel.ts         # Action recommendation
├── scorers/
│   ├── CompletenessScorer.ts      # Data completeness
│   ├── ConfidenceScorer.ts        # Decision confidence
│   ├── UrgencyScorer.ts           # Time sensitivity
│   └── RiskScorer.ts              # Risk assessment
├── rules/
│   ├── index.ts                   # Rule definitions
│   ├── stateRules.ts              # State transition rules
│   ├── recommendationRules.ts     # Recommendation rules
│   └── alertRules.ts              # Alert rules
├── types/
│   ├── state.ts                   # State types
│   ├── decision.ts                # Decision types
│   └── scores.ts                  # Score types
└── api/
    ├── routes.ts                  # Express routes
    └── controller.ts              # Request handlers
```

### 6.2 Database Schema

```sql
-- Trip State History
CREATE TABLE trip_state_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id),
  from_state VARCHAR(50),
  to_state VARCHAR(50) NOT NULL,
  transition_reason TEXT,
  automatic BOOLEAN DEFAULT false,
  triggered_by UUID REFERENCES users(id),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_trip_state_history_trip (trip_id, created_at DESC)
);

-- Decision Log
CREATE TABLE decision_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id),
  decision_id VARCHAR(100) UNIQUE NOT NULL,
  state VARCHAR(50) NOT NULL,
  recommendations JSONB,
  alerts JSONB,
  scores JSONB,
  confidence DECIMAL(5,2),
  rules_matched TEXT[],
  model_predictions JSONB,
  processing_time INTEGER,  -- milliseconds
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_decision_log_trip (trip_id, created_at DESC),
  INDEX idx_decision_log_decision (decision_id)
);

-- Automation Events
CREATE TABLE automation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id),
  automation_id VARCHAR(100) NOT NULL,
  trigger_rule VARCHAR(100),
  triggered_at TIMESTAMP DEFAULT NOW(),
  executed_at TIMESTAMP,
  status VARCHAR(50),
  result JSONB,
  error TEXT,
  INDEX idx_automation_events_trip (trip_id, triggered_at DESC)
);
```

---

## Summary

This document covers the technical foundation of the Decision Engine:

1. **System Overview** — Role, architecture layers, input/output flow
2. **State Machine** — 25+ trip states, transition matrix, rules
3. **Scoring System** — Completeness, confidence, urgency, risk scores
4. **Decision Logic** — Rule engine, ML models, ensemble approach
5. **Output Structure** — Decision panel API response format
6. **Implementation** — Service structure, database schema

**Next Document**: DECISION_02_UX_UI_DEEP_DIVE.md — Decision panel visualization and state indicators

---

**Document**: DECISION_01_TECHNICAL_DEEP_DIVE.md
**Series**: Decision Engine & Strategy System Deep Dive
**Status**: ✅ Complete
**Last Updated**: 2026-04-23
