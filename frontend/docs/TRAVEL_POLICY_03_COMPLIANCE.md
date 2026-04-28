# Travel Policy & Duty of Care — Compliance Management

> Research document for policy violation detection, exception management, compliance reporting, and audit trail for corporate travel.

---

## Key Questions

1. **How do we detect policy violations in real-time and post-booking?**
2. **What exception management workflows balance flexibility with control?**
3. **How do we report compliance metrics to corporate clients?**
4. **What audit trail is needed for travel policy compliance?**
5. **How do we drive policy compliance without creating traveler frustration?**

---

## Research Areas

### Policy Violation Detection

```typescript
interface ViolationDetection {
  realTime: RealTimeDetection;
  postBooking: PostBookingDetection;
  expenseAudit: ExpenseAuditDetection;
  patterns: PatternDetection;
}

interface RealTimeDetection {
  triggers: RealTimeTrigger[];
  evaluation: RealTimeEvaluation;
  intervention: InterventionAction[];
}

// Real-time violation detection points:
//
// SEARCH PHASE:
// When traveler searches for flights/hotels:
// - Filter results to show policy-compliant options first
// - Flag non-compliant options with warning badge
// - Hard-block options that violate mandatory rules
// - Show policy rationale: "Economy class only for domestic flights under 4h"
//
// SELECTION PHASE:
// When traveler selects a flight/hotel:
// - Evaluate all applicable policy rules against selection
// - Calculate variance from policy (₹ over limit, star rating over, etc.)
// - If hard block: Show alternatives within policy, require exception request
// - If soft warning: Show warning with "Proceed anyway" option + justification
// - Log all evaluations for compliance reporting
//
// BOOKING PHASE:
// Before confirming booking:
// - Final policy check against all rules
// - Verify approval obtained for any exceptions
// - Check booking lead time requirements
// - Verify documentation requirements (visa, passport, insurance)
// - Confirm preferred supplier mandate compliance
// - Generate compliance certificate for the booking

interface PolicyViolation {
  id: string;
  bookingId: string;
  travelerId: string;
  companyId: string;
  ruleId: string;
  ruleName: string;
  severity: 'hard_violation' | 'soft_violation' | 'warning';
  category: PolicyCategory;
  details: string;                     // Human-readable description
  variance: {
    allowed: any;                      // What policy allows
    actual: any;                       // What was booked/spent
    difference: any;                   // The gap
  };
  status: ViolationStatus;
  exception?: ExceptionRef;
  detectedAt: Date;
  detectedBy: 'real_time' | 'post_booking' | 'expense_audit' | 'pattern_analysis';
}

type ViolationStatus =
  | 'detected'                         // Just detected, no action yet
  | 'exception_requested'              // Traveler requested exception
  | 'exception_approved'               // Exception granted
  | 'exception_rejected'               // Exception denied, booking cancelled
  | 'acknowledged'                     // Traveler acknowledged warning
  | 'escalated'                        // Escalated to manager/admin
  | 'resolved'                         // Resolved (booking modified or cancelled)
  | 'flagged_for_audit';               // Flagged for expense audit

// Common violation categories and frequencies:
// 1. Hotel rate over limit: 35% of all violations
//    "Booked ₹7,200/night hotel, policy max ₹5,000/night"
// 2. Flight class violation: 20%
//    "Booked business class for 2h domestic flight (economy only)"
// 3. Booking lead time: 15%
//    "Booked flight 3 days before travel (14-day policy minimum)"
// 4. Non-preferred supplier: 12%
//    "Booked independent hotel instead of preferred Taj/Marriott"
// 5. Meal expense overage: 10%
//    "₹3,200 meal expense, policy max ₹1,500/day"
// 6. Destination restriction: 5%
//    "Travel to high-risk destination without security approval"
// 7. Missing documentation: 3%
//    "International travel without uploaded insurance certificate"

// Post-booking violation detection:
// Run nightly compliance audit against all active bookings:
// 1. Price comparison: Was the booking within limits at time of booking?
// 2. Supplier check: Was a preferred supplier available when non-preferred was booked?
// 3. Duplicate bookings: Same traveler, same dates, different bookings
// 4. Unused bookings: Booked but no check-in / no-show without cancellation
// 5. Pattern anomalies: Traveler always books above policy, always uses non-preferred
//
// Expense audit detection:
// Run monthly audit against expense reports:
// 1. Receipt amount vs. booking amount (unexplained overages)
// 2. Personal expenses mixed with business expenses
// 3. Duplicate expense claims (same receipt, multiple trips)
// 4. Out-of-policy meal and entertainment expenses
// 5. Missing receipts for expenses above threshold (₹500)
// 6. Cash expenses without proper documentation
// 7. Currency conversion discrepancies
//
// Pattern detection:
// Machine learning model trained on historical violations:
// - Travelers with high violation rates (flag for policy refresher training)
// - Departments with consistently low compliance (targeted policy review)
// - Routes/destinations with frequent violations (policy may be unrealistic)
// - Time patterns (end-of-quarter rush = more violations)
// - Approver patterns (managers who approve 95%+ exceptions = rubber stamping)
```

### Compliance Reporting Dashboard

```typescript
interface ComplianceReporting {
  metrics: ComplianceMetrics;
  dashboards: ComplianceDashboard[];
  reports: ComplianceReport[];
  benchmarks: ComplianceBenchmark;
}

interface ComplianceMetrics {
  overall: OverallCompliance;
  byCategory: CategoryCompliance[];
  byDepartment: DepartmentCompliance[];
  byTraveler: TravelerCompliance[];
  trend: ComplianceTrend[];
}

interface OverallCompliance {
  totalBookings: number;
  compliantBookings: number;
  complianceRate: number;               // Percentage
  violationRate: number;
  exceptionRate: number;                // % of bookings with exceptions
  exceptionApprovalRate: number;
  costOfNonCompliance: number;          // ₹ extra spent on violations
  savingsFromCompliance: number;        // ₹ saved by following policy
}

// Compliance dashboard views:
//
// EXECUTIVE VIEW (for company CFO / travel admin):
// - Overall compliance rate (target: 85%+)
// - Month-over-month trend
// - Top 5 violation categories
// - Cost of non-compliance (₹)
// - Savings from preferred supplier program
// - Average booking lead time
// - Exception approval rate by department
//
// DEPARTMENT VIEW (for department managers):
// - Department compliance rate vs. company average
// - Department violation breakdown
// - Top violators in department
// - Exception requests pending approval
// - Department travel spend vs. budget
//
// TRAVELER VIEW (for individual travelers):
// - Personal compliance score
// - Recent violations and status
// - Policy reminders for upcoming trips
// - Preferred supplier options
// - Booking guidelines summary

// Compliance report types:
//
// Monthly Compliance Report:
// - Overall compliance rate with trend
// - Top violation categories with count and cost impact
// - Department rankings (best to worst compliance)
// - Preferred supplier utilization rate
// - Exception request volume and approval rates
// - Recommendations for policy improvement
//
// Quarterly Savings Report:
// - Total savings from preferred supplier program
// - Savings by supplier category (airline, hotel, car)
// - Lost savings from non-compliance (what could have been saved)
// - ROI on preferred supplier contracts
// - Recommendations for contract renegotiation
//
// Annual Travel Policy Review:
// - Year-over-year compliance trends
// - Policy effectiveness analysis
// - Traveler satisfaction with policy
// - Recommended policy changes for next year
// - Benchmark against industry standards
//
// Violation Audit Report:
// - Detailed list of all violations in period
// - Resolution status for each
// - Repeat offenders identified
// - Policy rules most frequently violated
// - Recommended enforcement actions

// Compliance benchmarks:
// Industry average compliance rates:
// Flights: 88% compliance (economy class rules)
// Hotels: 75% compliance (rate limits hardest to enforce)
// Car rental: 82% compliance
// Meals: 65% compliance (most violated category)
// Advance booking: 70% compliance
// Preferred suppliers: 80% compliance
//
// Target for Indian corporate travel:
// Overall: 85%+ compliance
// Flight: 90%+
// Hotel: 80%+
// Preferred supplier: 85%+
// Advance booking: 75%+
```

### Policy Optimization

```typescript
interface PolicyOptimization {
  analysis: PolicyAnalysis;
  recommendations: PolicyRecommendation[];
  simulation: PolicySimulation;
}

// Policy analysis questions:
// 1. Are any policy rules violated > 30% of the time?
//    → Rule may be unrealistic, consider updating
//
// 2. Are exception approval rates > 90% for any rule?
//    → Rule is too strict, consider relaxing
//
// 3. Are preferred supplier rates actually cheaper?
//    → Compare preferred vs. non-preferred booking costs
//    → If non-preferred is often cheaper, renegotiate or expand supplier list
//
// 4. What's the traveler satisfaction score?
//    → Survey travelers on policy experience
//    → Low satisfaction = policy is too restrictive or unclear
//
// 5. What's the ROI of the preferred supplier program?
//    → Total negotiated savings vs. program management cost
//    → Include: Administrative cost, compliance monitoring, traveler friction
//
// Policy simulation:
// Before changing a policy rule, simulate the impact:
// Input: "Increase hotel rate limit from ₹5,000 to ₹7,000/night"
// Simulation results:
//   - Compliance rate change: 75% → 92%
//   - Additional cost: ₹1.2 lakh/month across company
//   - Exception request reduction: 45% fewer exceptions
//   - Traveler satisfaction improvement: +15 points
//   - Recommended: Yes, cost increase justified by reduced admin overhead
//
// Common policy optimization recommendations:
// 1. Increase hotel rate limits in expensive cities (Mumbai, Bangalore)
// 2. Allow premium economy for flights > 4 hours (improves traveler comfort)
// 3. Reduce advance booking requirement from 14 to 7 days (more realistic)
// 4. Add more preferred hotels in underserved cities
// 5. Allow non-preferred suppliers when rate is > 20% cheaper
```

---

## Open Problems

1. **Enforcement vs. experience** — Aggressive policy enforcement (hard blocks) frustrates travelers and drives them to book outside the system. Soft enforcement (warnings, nudges) is better for adoption but may result in lower compliance.

2. **Policy data quality** — Compliance reporting is only as good as the underlying booking data. Incomplete expense reports, missing receipts, and manual entries create data quality issues that skew compliance metrics.

3. **Multi-policy complexity** — A single company may have different policies for domestic vs. international, by department, by seniority level, and by trip purpose. Ensuring the correct policy version is applied to each booking requires robust policy routing.

4. **Attribution of savings** — Measuring the financial impact of compliance (preferred supplier savings, avoided overages) requires comparing against counterfactual pricing that doesn't exist. Estimates are imperfect.

5. **Traveler education** — Most violations stem from travelers not understanding the policy, not willful non-compliance. Effective policy communication (just-in-time guidance, not lengthy PDFs) is essential.

---

## Next Steps

- [ ] Build real-time policy violation detection engine
- [ ] Create compliance reporting dashboard with executive and department views
- [ ] Design policy optimization simulation tool
- [ ] Implement traveler compliance scoring with nudging system
- [ ] Study compliance platforms (SAP Concur, Navan, TripActions, TravelPerk compliance modules)
