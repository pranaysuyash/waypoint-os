# Knowledge Base & Internal Wiki — Supplier Knowledge

> Research document for supplier-specific knowledge, relationship intelligence, and booking procedures.

---

## Key Questions

1. **What supplier knowledge do agents need during booking?**
2. **How do we capture and share institutional supplier knowledge?**
3. **What's the supplier procedure library?**
4. **How do we track supplier performance knowledge?**
5. **How do agents access supplier info during trip building?**

---

## Research Areas

### Supplier Knowledge Base

```typescript
interface SupplierKnowledge {
  supplierId: string;
  supplierName: string;
  type: SupplierType;
  profile: SupplierProfile;
  bookingProcedures: BookingProcedure[];
  specialNotes: SupplierNote[];
  performanceHistory: PerformanceSummary;
  agentTips: AgentTip[];
}

type SupplierType =
  | 'hotel_chain' | 'hotel_independent' | 'resort'
  | 'airline' | 'gds'
  | 'tour_operator' | 'activity_provider'
  | 'transfer_company' | 'car_rental'
  | 'insurance_provider' | 'visa_service'
  | 'forex_provider' | 'sim_provider'
  | 'restaurant' | 'event_venue';

interface SupplierProfile {
  contactInfo: ContactInfo;
  apiDetails: APIDetails;
  paymentTerms: string;
  cancellationPolicy: string;
  commissionRate: string;
  preferredBookingChannel: string;
  accountManager: string;
  supportHours: string;
  responseTime: string;              // Average response time
}

interface BookingProcedure {
  procedureId: string;
  procedureType: 'new_booking' | 'modification' | 'cancellation' | 'group_booking';
  steps: ProcedureStep[];
  requiredDocuments: string[];
  typicalProcessingTime: string;
  commonIssues: string[];
  workarounds: string[];
}

// Example: Taj Hotels booking procedure
// New Booking:
//   1. Check availability on Taj Connect portal (or call central reservations)
//   2. For corporate rate, apply corporate ID: TAJ-CORP-XXXXX
//   3. Guarantee with credit card (no charge until check-in)
//   4. Receive confirmation number via email within 2 hours
//   5. For suite bookings, request upgrade at check-in (mention repeat guest)
//
// Common Issues:
//   - Overbooking during peak season → Book 90 days in advance
//   - Rate discrepancy → Call account manager directly
//   - Early check-in → Request 24 hours before, not guaranteed
//
// Agent Tips:
//   - "The Taj Club rooms are worth the upgrade — includes lounge access and evening cocktails"
//   - "For Taj Lake Palace Udaipur, book 6 months in advance for winter dates"
//   - "Corporate rate available for 10+ room nights, ask for RFP process"
```

### Agent Tips & Tribal Knowledge

```typescript
interface AgentTip {
  tipId: string;
  supplierId: string;
  author: string;
  category: TipCategory;
  content: string;
  verified: boolean;
  verifiedBy?: string;
  upvotes: number;
  downvotes: number;
  createdAt: Date;
}

type TipCategory =
  | 'booking_hack'                   // Tips to get better rates/availability
  | 'customer_experience'            // Tips to enhance customer experience
  | 'money_saving'                   // Cost optimization tips
  | 'time_saving'                    // Efficiency tips
  | 'avoid_problem'                  // Common pitfalls to avoid
  | 'upsell'                         // Upselling opportunities
  | 'hidden_gem';                    // Lesser-known features/benefits

// Tribal knowledge examples:
// "At Marriott Mumbai, ask for the sea-facing room. Same price, much better view."
// "For Indigo flights, web check-in opens 48 hours before. Set a reminder."
// "Singapore Airlines allows free stopover in Singapore. Use it as a selling point."
// "The breakfast buffet at ITC Grand Chola is the best in Chennai. Mention it to foodie customers."
// "Booking Amadeus through the agency console gives 2% better commission than online."
// "For visa to Thailand, VFS Global in Mumbai is faster than Delhi. Plan accordingly."

// Tip verification:
// 1. Agent submits tip
// 2. Other agents upvote/downvote
// 3. Tips with 5+ upvotes and < 2 downvotes → "Community Verified"
// 4. Tips verified by team lead → "Expert Verified"
// 5. Tips with 3+ downvotes → Flagged for review
// 6. Tips older than 12 months → Flagged for re-verification
```

### Supplier Performance Knowledge

```typescript
interface SupplierPerformanceSummary {
  supplierId: string;
  overallRating: number;
  ratings: SupplierRating[];
  incidentHistory: IncidentRecord[];
  trendAnalysis: TrendData;
}

interface SupplierRating {
  category: string;
  score: number;
  trend: 'improving' | 'stable' | 'declining';
}

// Performance categories:
// - Reliability: Do they honor bookings? (% of confirmed bookings not cancelled by supplier)
// - Response time: How fast do they respond to requests?
// - Quality: Customer satisfaction with the supplier
// - Pricing: Are their rates competitive?
// - Support: How well do they handle issues?
// - Payment: Do they process commissions on time?

// Supplier knowledge in workbench:
// When agent selects a hotel for a trip:
// → Show supplier card with:
//   "Taj Hotels | ★★★★☆ Reliability | ★★★★★ Quality
//    Avg response time: 2 hours | Commission: 10%
//    Trend: Stable | Last issue: 3 months ago
//    Agent tips: 12 tips (3 verified) [View Tips]
//    [Booking Procedure] [Contact Account Manager]"
```

---

## Open Problems

1. **Tip accuracy decay** — "Ask for sea-facing room" may not apply after renovation. Tips need expiry dates and re-verification.

2. **Supplier sensitivity** — Tips about getting better rates may not be information the supplier wants shared publicly. Need internal-only classification.

3. **Competitive supplier intel** — "Marriott gives 12% commission vs. Taj at 10%" — sharing this across agents is useful but sensitive.

4. **Knowledge capture from departing agents** — When an experienced agent leaves, their supplier knowledge goes with them. Need systematic capture, not just voluntary sharing.

5. **Supplier-specific training** — Each supplier has different booking systems, procedures, and quirks. Training agents on every supplier is impractical.

---

## Next Steps

- [ ] Design supplier knowledge base structure
- [ ] Build agent tip submission and verification system
- [ ] Create supplier booking procedure library
- [ ] Design supplier knowledge card for workbench integration
- [ ] Study supplier knowledge management (travel agent forums, TBO Holidays, Hotelbeds knowledge)
