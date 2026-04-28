# Travel Policy & Duty of Care — Analytics

> Research document for travel policy effectiveness measurement, cost savings analysis, traveler satisfaction metrics, and benchmarking.

---

## Key Questions

1. **How do we measure travel policy effectiveness beyond compliance rate?**
2. **What cost savings methodologies apply to corporate travel programs?**
3. **How do we benchmark travel program performance against industry standards?**
4. **What traveler satisfaction metrics matter for policy design?**
5. **How do predictive analytics improve travel program management?**

---

## Research Areas

### Policy Effectiveness Metrics

```typescript
interface PolicyEffectiveness {
  compliance: ComplianceMetrics;
  financial: FinancialMetrics;
  operational: OperationalMetrics;
  traveler: TravelerMetrics;
  composite: ProgramHealthScore;
}

interface ComplianceMetrics {
  overallRate: number;                 // % of bookings fully compliant
  byCategory: Record<PolicyCategory, number>;
  bySeverity: Record<PolicySeverity, number>;
  trend: MonthlyTrend[];
  topViolations: ViolationRanking[];
}

// Compliance metrics deep dive:
// Overall compliance rate: 82.3% (target: 85%)
//   Flights: 88.5% (above target)
//   Hotels: 74.2% (below target — room rate limits too strict?)
//   Transport: 81.7% (on target)
//   Meals: 62.4% (well below — policy unclear or unrealistic?)
//   Advance booking: 71.3% (below — shorten lead time requirement?)
//
// Violation trend (6 months):
// Jan: 85.1%, Feb: 83.7%, Mar: 81.2%, Apr: 82.9%, May: 80.5%, Jun: 78.8%
// Trend: Declining → investigate cause (new employees? policy change? seasonality?)
//
// Top 5 violations this quarter:
// 1. Hotel rate over limit: 127 incidents, avg ₹2,300 over limit
// 2. Late booking (<14 day lead time): 89 incidents
// 3. Non-preferred hotel: 67 incidents
// 4. Meal expense over daily limit: 54 incidents
// 5. Flight class upgrade: 31 incidents

interface FinancialMetrics {
  totalSpend: SpendBreakdown;
  savings: SavingsAnalysis;
  costOfNonCompliance: CostOfNonCompliance;
  roi: ProgramROI;
}

interface SpendBreakdown {
  total: number;                       // ₹ total travel spend
  flights: number;                     // ₹ on flights
  hotels: number;                      // ₹ on hotels
  transport: number;                   // ₹ on ground transport
  meals: number;                       // ₹ on meals and entertainment
  insurance: number;                   // ₹ on travel insurance
  visa: number;                        // ₹ on visa processing
  other: number;                       // ₹ miscellaneous
  perTraveler: number;                 // ₹ average per traveler
  perTrip: number;                     // ₹ average per trip
  perNight: number;                    // ₹ average per night
}

// Spend analysis example (quarterly):
// Total travel spend: ₹1.24 crore
//   Flights: ₹52.3 lakh (42%)
//   Hotels: ₹39.7 lakh (32%)
//   Transport: ₹12.4 lakh (10%)
//   Meals: ₹9.3 lakh (7.5%)
//   Insurance: ₹6.2 lakh (5%)
//   Visa: ₹2.5 lakh (2%)
//   Other: ₹1.6 lakh (1.5%)
//
// Per traveler: ₹1.85 lakh/quarter (avg 3.2 trips)
// Per trip: ₹57,800
// Per night: ₹8,200

interface SavingsAnalysis {
  preferredSupplier: PreferredSavings;
  complianceSavings: number;           // ₹ saved by compliant bookings
  negotiatedRates: number;             // ₹ saved vs. public rates
  advanceBookingSavings: number;       // ₹ saved by booking early
  totalSavings: number;
  savingsRate: number;                 // % saved vs. unmanaged travel
}

// Savings breakdown:
// Preferred supplier discounts: ₹18.4 lakh (airlines ₹9.2L, hotels ₹6.8L, car ₹2.4L)
// Early booking savings: ₹4.7 lakh (14-day advance vs. last-minute)
// Policy-compliant choices: ₹3.2 lakh (economy vs. business, 3-star vs. 5-star)
// Negotiated corporate rates: ₹8.9 lakh (vs. public rate)
// Total savings: ₹35.2 lakh (28.4% of spend)
// ROI: 7.2x return on travel management cost

interface CostOfNonCompliance {
  totalOverage: number;                // ₹ spent over policy limits
  nonPreferredPremium: number;         // ₹ extra for non-preferred suppliers
  lateBookingPremium: number;          // ₹ extra for last-minute bookings
  exceptionProcessingCost: number;     // ₹ admin cost for exceptions
  total: number;                       // ₹ total cost of non-compliance
}

// Cost of non-compliance:
// Hotel rate overages: ₹2.9 lakh (127 incidents × avg ₹2,300)
// Non-preferred hotels: ₹4.2 lakh (67 incidents × avg ₹6,300 premium)
// Late booking premium: ₹5.7 lakh (89 incidents × avg ₹6,400 premium)
// Meal overages: ₹0.9 lakh
// Exception processing: ₹1.8 lakh (admin time @ ₹500/hour)
// Total non-compliance cost: ₹15.5 lakh (12.5% of spend)
//
// Insight: If we could reduce hotel violations alone to <10%,
//          we'd save ₹7.1 lakh/quarter = ₹28.4 lakh/year

// Program health score (composite metric):
// Score: 0-100
// Components:
//   Compliance rate: 40% weight (target: 85%)
//   Cost savings rate: 25% weight (target: 25% of spend)
//   Traveler satisfaction: 20% weight (target: 4.0/5.0)
//   Approval speed: 10% weight (target: <8 hours)
//   Duty of care score: 5% weight (target: 100% insured + tracked)
//
// Current score: 76/100
//   Compliance: 82.3% × 40 = 32.9 points
//   Savings: 28.4% × 25 = 25.0 points
//   Satisfaction: 3.6/5.0 × 20 = 14.4 points
//   Approval: 6.2h (good) × 10 = 9.0 points
//   Duty of care: 95% × 5 = 4.8 points
```

### Traveler Satisfaction Analytics

```typescript
interface TravelerAnalytics {
  satisfaction: SatisfactionMetrics;
  behavior: TravelerBehavior;
  feedback: FeedbackAnalysis;
  personas: TravelerPersona[];
}

interface SatisfactionMetrics {
  nps: number;                         // Net Promoter Score
  overallSatisfaction: number;         // 1-5 scale
  policySatisfaction: number;          // 1-5 scale
  bookingExperience: number;           // 1-5 scale
  supportExperience: number;           // 1-5 scale
  surveyResponses: number;             // Count
}

// Traveler satisfaction survey (post-trip):
// 1. Overall trip experience: ⭐⭐⭐⭐ (4/5)
// 2. Booking process ease: ⭐⭐⭐⭐ (4/5)
// 3. Policy clarity: ⭐⭐⭐ (3/5) — opportunity for improvement
// 4. Travel policy fairness: ⭐⭐⭐ (3/5)
// 5. Support quality: ⭐⭐⭐⭐⭐ (4.5/5)
// 6. Would you recommend our travel program? NPS: +32
// 7. Open feedback: "Hotel rate limit too low for Mumbai/Bangalore"
//
// Satisfaction by policy area:
// Flight policy: 4.2/5 (generally satisfied)
// Hotel policy: 2.8/5 (biggest pain point — rate limits too strict for metros)
// Meal policy: 3.1/5 (adequate but tight for client entertainment)
// Transport policy: 3.8/5 (reasonable)
// Advance booking: 3.0/5 (14 days feels excessive for domestic)
// Preferred suppliers: 3.5/5 (good options but limited in some cities)
//
// Top traveler complaints:
// 1. "₹5,000 hotel limit doesn't work in Mumbai" (mentioned 42 times)
// 2. "14-day advance booking is unrealistic for urgent client meetings" (38 times)
// 3. "Preferred hotel list doesn't cover Tier 2 cities" (29 times)
// 4. "Meal limit doesn't cover business dinners with clients" (24 times)
// 5. "Approval process takes too long for urgent travel" (21 times)

interface TravelerBehavior {
  bookingPatterns: BookingPattern[];
  policyInteraction: PolicyInteraction[];
  complianceHistory: TravelerComplianceScore[];
}

// Traveler behavior insights:
// Booking lead time distribution:
//   >14 days: 35% (compliant)
//   7-14 days: 28% (soft violation)
//   3-7 days: 22% (violation)
//   <3 days: 15% (severe violation — often urgent business needs)
//
// Preferred supplier acceptance:
//   Accept first recommendation: 62%
//   Browse alternatives: 28%
//   Request non-preferred: 10%
//
// Peak booking times:
//   Monday 9-11 AM: Highest booking volume (planning for the week)
//   Friday 4-6 PM: Second peak (planning for next week)
//   Quarter-end: 40% increase in booking volume
//
// Traveler persona analysis:
// 1. "Policy Follower" (45%): Books within policy, minimal exceptions
//    → Keep informed, don't over-communicate
// 2. "Flexibility Seeker" (30%): Occasionally over policy, reasonable exceptions
//    → Provide clear exception process, quick approval
// 3. "Policy Challenger" (15%): Frequently over policy, many exceptions
//    → Needs policy refresher, personalized guidance
// 4. "Last-Minute Larry" (10%): Always books late, usually urgent business
//    → Pre-approve certain routes/hotels to speed up booking
```

### Predictive Analytics

```typescript
interface PredictiveAnalytics {
  demandForecast: DemandForecast;
  costForecast: CostForecast;
  compliancePrediction: CompliancePrediction;
  riskForecast: RiskForecast;
}

interface DemandForecast {
  period: string;                      // "Q3 2026"
  totalTrips: number;
  byDestination: DestinationDemand[];
  byDepartment: DepartmentDemand[];
  confidence: number;
}

// Demand forecasting:
// Historical patterns + business calendar:
// Q1 (Jan-Mar): High (new year travel, budget spending)
// Q2 (Apr-Jun): Moderate (summer travel begins for families)
// Q3 (Jul-Sep): Low (monsoon, but international demand picks up)
// Q4 (Oct-Dec): Highest (festivals, year-end, holiday travel)
//
// Forecast for Q3 2026:
// Total trips: 185 (vs. 168 in Q3 2025, +10% growth)
// Top destinations: Mumbai (32), Bangalore (28), Delhi (25), Singapore (15)
// New trend: Increased Pune trips (+25%) — new office opening
// Budget requirement: ₹1.38 crore (₹1.24 crore × 1.10 growth)
//
// Cost forecast:
// Airfare trend: +8% YoY (fuel costs, capacity constraints)
// Hotel trend: +5% YoY (inflation, demand growth)
// Recommendation: Lock in annual rates with preferred hotels now
//
// Compliance prediction:
// If policy unchanged, compliance rate will drop to ~75% by Q4
// Reason: Hotel rate limits too low for 2026 prices
// Recommendation: Increase hotel limits by 15% for metro cities
//
// Risk forecast:
// Monsoon season (Jun-Sep): Flight disruption risk high for coastal cities
// Recommendation: Flexible ticket options for monsoon-period travel
// Diwali period (Oct): Hotel availability crunch in Rajasthan/Gujarat
// Recommendation: Book Diwali-period travel 2+ months ahead

// Benchmarking:
interface TravelBenchmark {
  company: CompanyMetrics;
  industry: IndustryMetrics;
  bestInClass: BestInClassMetrics;
  percentile: number;                  // Company's percentile ranking
}

// Industry benchmarks (Indian corporate travel):
// Average spend per employee: ₹1.8-2.5 lakh/year
// Average trips per employee: 6-8/year
// Compliance rate: 75-85%
// Preferred supplier utilization: 70-80%
// Average booking lead time: 10-12 days
// Exception rate: 15-25%
// NPS for travel program: +20 to +40
//
// Our company vs. benchmarks:
// Spend per employee: ₹2.1 lakh (52nd percentile)
// Compliance: 82.3% (58th percentile)
// Preferred supplier: 80% (65th percentile)
// Booking lead time: 11.2 days (55th percentile)
// NPS: +32 (60th percentile)
// → Room for improvement in compliance and booking lead time
```

---

## Open Problems

1. **Attribution complexity** — Savings from compliance, preferred suppliers, and advance booking overlap. A single booking may benefit from all three, making isolated attribution difficult.

2. **Survey fatigue** — Post-trip satisfaction surveys get declining response rates over time. Finding the right balance between data collection and traveler burden is key.

3. **Benchmarking data availability** — Indian corporate travel benchmarking data is limited compared to US/EU markets. Most benchmarks come from global TMCs and may not reflect Indian market conditions.

4. **Predictive accuracy** — Travel demand is influenced by unpredictable factors (new client wins, market downturns, pandemic waves). Forecasting models need wide confidence intervals.

5. **Actionability gap** — Analytics produce insights ("hotel compliance is low in Mumbai") but turning insights into action ("increase Mumbai hotel rate limits by ₹2,000") requires policy change workflows.

---

## Next Steps

- [ ] Build travel program analytics dashboard with composite health score
- [ ] Create traveler satisfaction measurement system with NPS tracking
- [ ] Design predictive demand and cost forecasting models
- [ ] Implement benchmarking framework against industry standards
- [ ] Study travel analytics platforms (Advito, CWT Solutions, Egencia Analytics)
