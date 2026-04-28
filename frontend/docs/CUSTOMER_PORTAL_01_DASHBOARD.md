# Customer Self-Service — Dashboard & Trip Overview

> Research document for the customer-facing portal dashboard, trip views, and navigation.

---

## Key Questions

1. **What does the customer need to see first when they log in?**
2. **How do we present trip status in a way that's immediately clear?**
3. **What self-service actions should be available without contacting an agent?**
4. **How do we handle customers with zero trips vs. active travelers?**
5. **What's the mobile-first vs. desktop experience difference?**

---

## Research Areas

### Dashboard Layout

```typescript
interface CustomerDashboard {
  customerId: string;
  // Sections
  upcomingTrips: TripSummary[];
  pastTrips: TripSummary[];
  draftTrips: TripSummary[];
  // Quick actions
  quickActions: QuickAction[];
  // Personalization
  recommendations: Recommendation[];
  // Notifications
  pendingNotifications: Notification[];
  documentsAwaitingAction: Document[];
}

interface TripSummary {
  tripId: string;
  destination: string;
  dates: DateRange;
  status: TripStatus;
  travelerCount: number;
  nextMilestone: string;           // "Flight in 3 days" / "Check-in tomorrow"
  coverImage: string;
  totalPaid: number;
  totalDue: number;
}

type QuickAction =
  | 'view_itinerary'
  | 'download_vouchers'
  | 'make_payment'
  | 'contact_agent'
  | 'request_modification'
  | 'submit_feedback'
  | 'upload_documents'
  | 'check_in';
```

### Trip Detail View

```typescript
interface CustomerTripDetail {
  tripId: string;
  overview: TripOverview;
  itinerary: CustomerItinerary;
  documents: CustomerDocument[];
  payments: PaymentSummary;
  travelers: TravelerInfo[];
  support: SupportAccess;
}

interface TripOverview {
  destination: string;
  dates: DateRange;
  status: TripStatus;
  progress: TripProgress;         // Visual progress indicator
  agent: AgentInfo;
  countdown: string;               // "12 days until departure"
}

interface TripProgress {
  stages: ProgressStage[];
  currentStage: number;
}

type ProgressStage =
  | 'inquiry'              // Trip requested
  | 'planning'             // Agent working on itinerary
  | 'quoted'               // Quote sent, awaiting approval
  | 'confirmed'            // Booking confirmed
  | 'documents_ready'      // Vouchers and tickets available
  | 'pre_departure'        // Final preparations
  | 'in_progress'          // Currently traveling
  | 'completed';           // Trip finished

interface CustomerItinerary {
  days: ItineraryDay[];
  totalSegments: number;
}

interface ItineraryDay {
  dayNumber: number;
  date: Date;
  summary: string;
  segments: SegmentSummary[];
}

interface SegmentSummary {
  type: 'flight' | 'hotel' | 'transfer' | 'activity' | 'free_time';
  title: string;
  time: string;
  status: 'confirmed' | 'pending' | 'cancelled';
  viewDetailsAction: string;
}
```

### Self-Service Actions

```typescript
interface SelfServiceCapability {
  action: string;
  requiresAgentApproval: boolean;
  availableFromStatus: TripStatus[];
  description: string;
}

// Self-service (no agent needed):
// - View itinerary and documents
// - Download vouchers and tickets
// - Update contact information
// - Submit traveler details (passport, dietary needs)
// - View payment history
// - Submit post-trip feedback
// - Contact support (chat/email/phone)

// Agent-assisted (request sent to agent):
// - Modify itinerary
// - Change dates
// - Add/remove travelers
// - Cancel booking
// - Request special arrangements
// - Upgrade service level
```

### Empty State & First-Time Experience

```typescript
interface EmptyStateStrategy {
  // No trips yet
  noTrips: {
    message: string;
    cta: 'start_exploring' | 'contact_agent' | 'browse_destinations';
    showRecommendations: boolean;
  };
  // Returning customer with past trips only
  pastTripsOnly: {
    message: string;               // "Ready for your next adventure?"
    showPastTripHighlights: boolean;
    suggestSimilar: boolean;
  };
}
```

---

## Open Problems

1. **Agent vs. self-service balance** — Too much self-service reduces agent value; too little frustrates customers who want quick answers.

2. **Real-time data freshness** — Customer sees a flight status that's 5 minutes stale. How real-time does the portal need to be?

3. **Complex itinerary display** — Multi-city, multi-week trips are hard to display clearly. Need progressive disclosure (day → segment → detail).

4. **Payment visibility** — How much financial detail to show (full breakdown vs. summary only). Cultural expectations vary.

5. **Multi-traveler access** — A family trip where multiple travelers need portal access. Who sees what? Who can take actions?

---

## Next Steps

- [ ] Design customer dashboard wireframes (mobile and desktop)
- [ ] Study customer portal patterns (Booking.com, Airbnb, Tripit)
- [ ] Map self-service vs. agent-assisted action boundary
- [ ] Design trip detail page with progressive disclosure
- [ ] Create empty state designs for new and returning customers
