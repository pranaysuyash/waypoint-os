# Travel Package Lifecycle 04: Operations Management

> Research document for package operations management, supplier coordination, voucher generation, departure preparation, on-tour monitoring, feedback collection, performance analytics, and package lifecycle management for Indian travel agencies.

---

## Document Overview

**Focus:** Post-booking operations that deliver the travel experience
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

1. **How do we coordinate with multiple suppliers (hotels, transport, activities, guides) for a single package departure?**
2. **What departure preparation checklist ensures nothing is missed before customers travel?**
3. **How do we generate and distribute travel vouchers, tickets, and itinerary documents?**
4. **What on-tour operations dashboard gives agents real-time visibility into active trips?**
5. **How do we collect structured customer feedback post-tour?**
6. **What package performance metrics (fill rate, profitability, repeat rate) drive business decisions?**
7. **When and how do we retire or archive underperforming packages?**

---

## Research Areas

### A. Supplier Coordination

```typescript
// Research-level model — not final

interface SupplierCoordination {
  departureId: string;
  packageId: string;

  // All supplier bookings for this departure
  supplierBookings: SupplierBooking[];

  // Coordination timeline
  milestones: CoordinationMilestone[];
  communications: SupplierCommunication[];

  // Overall status
  coordinationStatus: CoordinationStatus;
}

interface SupplierBooking {
  id: string;
  supplierType: SupplierType;
  supplierId: string;
  supplierName: string;

  // What's booked
  serviceType: string;                   // "Airport transfer", "Hotel stay"
  serviceDetails: string;                // "AC Innova, COK pickup, 2 vehicles"
  quantity: number;
  unitPrice: Money;
  totalPrice: Money;

  // Booking reference
  supplierConfirmationNumber?: string;
  supplierVoucherNumber?: string;
  bookingDate: Date;
  serviceDate: Date;

  // Status
  status: SupplierBookingStatus;
  lastConfirmedAt?: Date;
  reconfirmationRequired: boolean;
  reconfirmationDate?: Date;

  // Contact
  supplierContact: ContactInfo;
  emergencyContact?: ContactInfo;

  // Special instructions
  specialInstructions?: string;          // "Guest name: Sharma family, 4 pax"
  dietaryNotes?: string;                 // "Pure vegetarian, Jain meals for 2"
}

type SupplierType =
  | 'hotel'
  | 'transport_company'
  | 'airline'
  | 'activity_provider'
  | 'restaurant'
  | 'tour_guide'
  | 'insurance_provider'
  | 'visa_service'
  | 'forex_service'
  | 'sim_card_provider';

type SupplierBookingStatus =
  | 'requested'           // Sent to supplier, awaiting confirmation
  | 'confirmed'           // Supplier confirmed
  | 'waitlisted'          // Supplier put on waitlist
  | 'partially_confirmed' // Some parts confirmed, some pending
  | 'amended'             // Modified from original
  | 'cancelled'           // Cancelled
  | 'no_show'             // Customer didn't show
  | 'completed';          // Service delivered

type CoordinationStatus =
  | 'pending'             // Not started
  | 'in_progress'         // Coordinating with suppliers
  | 'all_confirmed'       // All suppliers confirmed
  | 'issues_pending'      // Some suppliers have issues
  | 'ready';              // All confirmed, documents generated

// Supplier coordination timeline:
//
// 60 days before departure:
//   - Send booking requests to all suppliers
//   - Hotels: rooming list + special requests
//   - Transport: vehicle type + route + pickup schedule
//   - Activities: group size + time slots
//   - Guide: language + itinerary + meeting points
//
// 30 days before departure:
//   - Reconfirm all bookings
//   - Collect confirmation numbers
//   - Resolve any waitlist issues
//   - Finalize meal plans (vegetarian/Jain count)
//
// 14 days before departure:
//   - Final reconfirmation with all suppliers
//   - Share guest details (names, contact numbers)
//   - Confirm pickup times and locations
//   - Verify special arrangements
//
// 7 days before departure:
//   - Generate all vouchers
//   - Share voucher copies with suppliers
//   - Final communication to travelers
//   - Emergency contacts distributed
//
// 1 day before departure:
//   - Last check on all suppliers
//   - Weather/disruption check
//   - Final briefing to tour leader (if group)
//
// Day of departure:
//   - Airport pickup tracking
//   - First hotel check-in verification
//   - Welcome call/message to travelers

interface CoordinationMilestone {
  milestone: string;
  dueDate: Date;
  status: 'pending' | 'completed' | 'overdue' | 'skipped';
  assignedTo: string;
  completedAt?: Date;
  notes?: string;
}

interface SupplierCommunication {
  id: string;
  supplierId: string;
  type: 'email' | 'whatsapp' | 'phone' | 'portal';
  direction: 'sent' | 'received';
  subject: string;
  content: string;
  timestamp: Date;
  attachments?: string[];
  requiresFollowUp: boolean;
  followUpDate?: Date;
}
```

### B. Voucher Generation

```typescript
interface VoucherGeneration {
  bookingId: string;
  departureId?: string;

  // All vouchers for this booking
  vouchers: TravelVoucher[];
  tickets: TravelTicket[];
  itinerary: ItineraryDocument;

  // Distribution
  deliveryMethod: VoucherDeliveryMethod;
  deliveryStatus: DeliveryStatus;
}

interface TravelVoucher {
  id: string;
  voucherNumber: string;                 // "VCH-2026-01234"
  type: VoucherType;
  bookingId: string;

  // Supplier info
  supplierId: string;
  supplierName: string;
  supplierAddress?: string;
  supplierContact: string;
  confirmationNumber: string;

  // Service details
  serviceDescription: string;
  serviceDate: Date;
  serviceEndDate?: Date;
  serviceLocation: string;
  paxCount: number;

  // Guest details
  leadGuestName: string;
  allGuestNames?: string[];

  // Inclusions
  includedItems: string[];
  specialNotes?: string;                 // "Includes breakfast", "AC vehicle"

  // Validity
  validFrom: Date;
  validTo: Date;
  termsAndConditions: string;

  // Status
  status: VoucherStatus;
  generatedAt: Date;
  deliveredAt?: Date;
  qrCode?: string;                       // QR code for verification
}

type VoucherType =
  | 'hotel'               // Hotel stay voucher
  | 'transfer'            // Airport/inter-city transfer
  | 'activity'            // Sightseeing/activity voucher
  | 'meal'                // Restaurant/meal voucher
  | 'guide'               // Tour guide service voucher
  | 'transport'           // Vehicle/coach voucher
  | 'insurance'           // Insurance certificate
  | 'package_summary';    // Comprehensive package voucher

type VoucherStatus =
  | 'draft'
  | 'generated'
  | 'delivered'
  | 'used'
  | 'expired'
  | 'cancelled';

type VoucherDeliveryMethod =
  | 'email_pdf'
  | 'whatsapp_pdf'
  | 'app_download'
  | 'physical_printout'
  | 'sms_link'
  | 'offline_sync';                      // Downloaded to device for offline access

// Voucher layout sketch:
//
// ┌─────────────────────────────────────────────────┐
│  [AGENCY LOGO]                                    │
│                                                   │
│  HOTEL VOUCHER                                    │
│  ─────────────────                                │
│  Voucher No: VCH-2026-01234                      │
│  Confirmation: HTL-CONF-78901                    │
│                                                   │
│  Hotel: Taj Malabar, Kochi                        │
│  Dates: Dec 15-17, 2026 (2 nights)               │
│  Room Type: Deluxe Sea View                      │
│  Guests: Rajesh Sharma, Priya Sharma              │
│  Meal Plan: Breakfast included                   │
│                                                   │
│  Special Requests:                                │
│  - Late checkout requested (Dec 17)              │
│  - Anniversary celebration (Dec 16)              │
│                                                   │
│  Included: Accommodation + Breakfast             │
│  Excluded: Mini bar, laundry, room service       │
│                                                   │
│  Contact: +91-484-2200 (Hotel Front Desk)        │
│  Emergency: +91-98765-43210 (Agency Helpline)    │
│                                                   │
│  [QR CODE]                                        │
│  Present this voucher at check-in                 │
│                                                   │
│  Terms: Non-refundable | Valid only for dates    │
│  shown | ID proof required at check-in           │
└─────────────────────────────────────────────────┘

interface TravelTicket {
  id: string;
  ticketType: 'flight' | 'train' | 'bus' | 'ferry';
  pnr: string;
  ticketNumber: string;
  // ... (same structure as defined in FLIGHT_INTEGRATION, RAIL series)
}

interface ItineraryDocument {
  id: string;
  bookingId: string;
  format: 'pdf' | 'html' | 'whatsapp_message' | 'app_view';

  // Content
  sections: ItinerarySection[];
  emergencyContacts: EmergencyContact[];
  packingChecklist?: string[];
  destinationTips?: string[];

  // Personalization
  travelerName: string;
  personalizedGreeting: string;
  weatherForecast?: WeatherForecast[];
}

interface ItinerarySection {
  dayNumber: number;
  date: Date;
  title: string;                         // "Day 1: Welcome to Kerala"
  theme?: string;                        // "Arrival & Relaxation"
  activities: ItineraryActivity[];
  accommodation?: AccommodationInfo;
  meals: MealInfo[];
  transport?: TransportInfo[];
  notes?: string;                        // "Keep your ID handy for monument entry"
}

interface EmergencyContact {
  purpose: string;                       // "Agency 24x7 Helpline", "Local Police"
  name: string;
  phone: string;
  email?: string;
  availableHours: string;                // "24x7", "9 AM - 6 PM IST"
}
```

### C. Departure Preparation Checklist

```typescript
interface DepartureChecklist {
  departureId: string;
  packageId: string;
  travelStartDate: Date;

  // Checklist items
  items: ChecklistItem[];

  // Overall readiness
  readinessScore: number;                // 0-100%
  readinessStatus: ReadinessStatus;
  blockers: string[];                    // Items preventing departure
}

interface ChecklistItem {
  id: string;
  category: ChecklistCategory;
  task: string;
  assignee: string;
  dueDate: Date;
  priority: 'critical' | 'important' | 'routine';
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  completedAt?: Date;
  notes?: string;
  dependencies?: string[];               // Other items that must be done first
}

type ChecklistCategory =
  | 'supplier_confirmation'  // All suppliers reconfirmed
  | 'document_generation'    // Vouchers, tickets, itinerary
  | 'payment_verification'   // All payments received
  | 'traveler_information'   // IDs, passport copies, visa, insurance
  | 'communication'          // Pre-departure briefing sent
  | 'logistics'              // Transport, pickup schedule
  | 'contingency'            // Weather check, backup plans
  | 'compliance'             // Insurance, waivers, declarations
  | 'ground_handling'        // Local coordinator, guide briefing
  | 'post_departure';        // On-tour monitoring setup

type ReadinessStatus =
  | 'not_started'
  | 'in_progress'
  | 'almost_ready'         // > 90% complete
  | 'ready'                // All critical items done
  | 'blocked';             // Critical items blocked

// Standard departure checklist (fixed-departure group tour):
//
// SUPPLIER CONFIRMATION (14 days before):
// [ ] All hotels reconfirmed with rooming list
// [ ] Transport company confirmed with vehicle details
// [ ] Activity providers confirmed with time slots
// [ ] Guide confirmed with itinerary and language
// [ ] Restaurant reservations confirmed (if meals external)
// [ ] Entry tickets/permissions arranged (monuments, parks)
//
// DOCUMENT GENERATION (10 days before):
// [ ] Hotel vouchers generated and shared with hotels
// [ ] Transfer vouchers generated
// [ ] Activity vouchers generated
// [ ] Flight tickets verified (if included)
// [ ] Comprehensive itinerary PDF generated
// [ ] All documents delivered to travelers
//
// PAYMENT VERIFICATION (7 days before):
// [ ] All traveler payments received
// [ ] Supplier advances paid
// [ ] Insurance premiums paid
// [ ] GST collected and invoice generated
// [ ] TCS collected (if overseas package)
//
// TRAVELER INFORMATION (7 days before):
// [ ] All passport copies collected (international)
// [ ] Visa documents verified
// [ ] Travel insurance certificates verified
// [ ] Medical fitness certificates (adventure/pilgrimage)
// [ ] Emergency contacts for each traveler
// [ ] Dietary requirements compiled
// [ ] Special needs/accommodations noted
//
// COMMUNICATION (5 days before):
// [ ] Pre-departure email/WhatsApp sent to all travelers
// [ ] Weather forecast shared
// [ ] Packing list shared
// [ ] Meeting point details confirmed
// [ ] Tour leader/agent contact shared
// [ ] App download link sent (if applicable)
//
// LOGISTICS (3 days before):
// [ ] Pickup schedule finalized with transport company
// [ ] Welcome kit prepared (SIM card, map, booklet)
// [ ] First aid kit stocked (for adventure/pilgrimage)
// [ ] Group WhatsApp group created
// [ ] Emergency protocol document prepared
//
// COMPLIANCE (3 days before):
// [ ] Liability waivers signed (adventure activities)
// [ ] Medical declarations collected
// [ ] Photography permissions arranged (restricted areas)
// [ ] Government registration completed (Amarnath, Char Dham)
//
// GROUND HANDLING (1 day before):
// [ ] Local coordinator briefed
// [ ] Hotel front desk informed of group arrival
// [ ] Welcome amenities arranged (flowers, fruit basket)
// [ ] Room allocation shared with hotel
```

### D. On-Tour Operations Dashboard

```typescript
interface OnTourDashboard {
  // Active trips currently in progress
  activeTrips: ActiveTrip[];

  // Upcoming departures (next 7 days)
  upcomingDepartures: UpcomingDeparture[];

  // Alerts requiring attention
  alerts: TourAlert[];
}

interface ActiveTrip {
  bookingId: string;
  packageId: string;
  departureId?: string;
  leadTraveler: string;
  contactNumber: string;

  // Trip progress
  currentDay: number;                    // Day 3 of 6
  totalDays: number;
  progressPercent: number;               // 50%
  currentLocation: string;               // "Munnar, Kerala"
  currentActivity: string;               // "Tea plantation visit"

  // Status
  status: TripStatus;
  lastCheckIn?: Date;
  nextActivity?: string;
  nextActivityTime?: Date;

  // Issues
  openIssues: number;
  resolvedIssues: number;
}

type TripStatus =
  | 'on_track'            // Everything going as planned
  | 'minor_issue'         // Small issue, not affecting experience
  | 'disruption'          // Significant disruption, needs attention
  | 'emergency';          // Emergency, needs immediate response

interface TourAlert {
  id: string;
  bookingId: string;
  severity: 'info' | 'warning' | 'urgent' | 'critical';
  category: AlertCategory;
  message: string;
  detectedAt: Date;
  status: 'new' | 'acknowledged' | 'in_progress' | 'resolved';
  assignedTo?: string;
  resolution?: string;
}

type AlertCategory =
  | 'flight_delay'         // Flight delayed, pickup time needs adjustment
  | 'flight_cancellation'  // Flight cancelled, rebooking needed
  | 'weather_disruption'   // Heavy rain, landslide warning, etc.
  | 'hotel_issue'          // Overbooking, room quality, maintenance
  | 'transport_issue'      // Vehicle breakdown, driver not available
  | 'activity_cancellation' // Activity provider cancelled
  | 'traveler_illness'     // Medical emergency
  | 'traveler_missing'     // Traveler not at meeting point
  | 'supplier_no_show'     // Guide/transport didn't show
  | 'document_issue'       // Missing voucher, wrong name on ticket
  | 'payment_issue'        // Final payment not received
  | 'safety_concern'       // Safety-related incident
  | 'covid_advisory'       // Health advisory for destination
  | 'natural_disaster'     // Earthquake, flood, etc.
  | 'political_unrest';    // Curfew, protest, bandh
```

**On-Tour Dashboard UI Sketch:**

```
+-------------------------------------------------------------------+
| ON-TOUR OPERATIONS DASHBOARD                    [Today: Dec 17]    |
+-------------------------------------------------------------------+
| Active Trips (5)  |  Upcoming (3)  |  Alerts (2)  |  Completed (12)|
+-------------------------------------------------------------------+
|                                                                    |
|  ACTIVE TRIPS                                                      |
|  +--------------------------------------------------------------+ |
|  | [●] Kerala Backwaters - Sharma Family                         | |
|  | Day 3 of 6 | Munnar | Tea plantation visit (in progress)     | |
|  | ████████████░░░░░░░░ 50% complete                             | |
|  | Last check-in: 2 hours ago | Next: Spice garden at 3 PM      | |
|  | [Contact Traveler] [View Itinerary] [Issue Report]            | |
|  +--------------------------------------------------------------+ |
|  | [●] Goa Beach - Corporate Group (25 pax)                      | |
|  | Day 2 of 3 | Baga Beach | Team building activity             | |
|  | ██████████░░░░░░░░░░ 67% complete                             | |
|  | [⚠] 1 vegetarian meal shortage reported                      | |
|  | [Contact Leader] [View Itinerary] [Resolve Issue]             | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  ALERTS                                                            |
|  +--------------------------------------------------------------+ |
|  | [URGENT] Flight delay: AI-456 (Goa group return)              | |
|  | Original: 4 PM | Now: 7:30 PM | Pickup needs rescheduling    | |
|  | [Acknowledge] [Reassign Pickup] [Notify Travelers]            | |
|  +--------------------------------------------------------------+ |
|  | [WARNING] Weather: Heavy rain expected Munnar tomorrow         | |
|  | Kerala Backwaters - Day 4 outdoor activities may be affected  | |
|  | [View Alternatives] [Contact Guide] [Notify Travelers]        | |
|  +--------------------------------------------------------------+ |
+-------------------------------------------------------------------+
```

### E. Ground Handling & Local Coordination

```typescript
interface GroundHandling {
  departureId: string;
  packageId: string;

  // Local team
  localCoordinator?: GroundHandler;
  tourLeader?: TourLeader;
  localGuides: LocalGuide[];

  // Ground logistics
  transportSchedule: TransportSchedule[];
  hotelCheckIns: HotelCheckIn[];
  activitySchedule: ActivitySchedule[];

  // Communication
  groupCommunicationChannel?: string;    // WhatsApp group link
  dailyBriefingSchedule: DailyBriefing[];
}

interface GroundHandler {
  name: string;
  company: string;
  phone: string;
  whatsapp: string;
  email: string;
  coverage: string;                      // "Kerala - Kochi to Trivandrum"
  languages: string[];
  available24x7: boolean;
}

interface TourLeader {
  name: string;
  phone: string;
  whatsapp: string;
  photo?: string;
  languages: string[];
  experience: string;                    // "5 years, 200+ tours"
  certifications?: string[];             // "First Aid", "Wildlife Guide"
}

interface LocalGuide {
  location: string;                      // "Kochi", "Munnar"
  name: string;
  phone: string;
  languages: string[];
  specialization?: string;               // "Spice plantation", "Ayurveda"
  assignedDays: number[];                // Day 1, Day 2
}

interface TransportSchedule {
  date: Date;
  pickupTime: string;
  pickupLocation: string;
  dropoffLocation: string;
  vehicleType: string;                   // "AC Innova", "Tempo Traveller"
  driverName: string;
  driverPhone: string;
  vehicleNumber: string;
  paxCount: number;
  luggageNotes?: string;
}

interface DailyBriefing {
  dayNumber: number;
  date: Date;
  briefingTime: string;                  // "8:00 AM at hotel lobby"
  agenda: string[];
  weatherForecast?: string;
  specialNotes?: string;
}
```

### F. Customer Feedback Collection

```typescript
interface FeedbackCollection {
  bookingId: string;
  packageId: string;

  // Survey configuration
  surveyType: FeedbackSurveyType;
  surveyTiming: SurveyTiming;
  deliveryMethod: VoucherDeliveryMethod;

  // Responses
  overallRating?: number;                // 1-5 stars
  categoryRatings?: CategoryRating[];
  openFeedback?: string;
  netPromoterScore?: number;             // 0-10
  wouldRecommend?: boolean;
  travelAgainWithAgency?: boolean;

  // Status
  surveySentAt?: Date;
  responseReceivedAt?: Date;
  reminderCount: number;
  incentivesOffered?: string;            // "₹500 off next booking"
}

type FeedbackSurveyType =
  | 'post_tour_comprehensive'  // Full survey after trip
  | 'post_tour_quick'          // Quick 3-question survey
  | 'post_activity'            // After specific activity
  | 'post_hotel'               // After hotel stay
  | 'nps_only';                // Just the NPS question

interface SurveyTiming {
  trigger: 'trip_completion' | 'last_activity' | 'custom';
  delayHours: number;                    // Send 24 hours after trip ends
  expiryDays: number;                    // Survey expires after 14 days
  reminderSchedule: number[];            // Remind at day 3, 7, 10
}

interface CategoryRating {
  category: FeedbackCategory;
  rating: number;                        // 1-5
  comment?: string;
}

type FeedbackCategory =
  | 'overall_experience'
  | 'itinerary_design'
  | 'hotel_quality'
  | 'food_quality'
  | 'transport_comfort'
  | 'guide_knowledge'
  | 'guide_behavior'
  | 'value_for_money'
  | 'booking_process'
  | 'communication'
  | 'responsiveness'
  | 'punctuality'
  | 'safety';

// India-specific feedback considerations:
//
// 1. LANGUAGE: Survey should be available in Hindi and English
//    (optionally in regional languages for pilgrimage/senior tours)
//
// 2. WHATSAPP-FIRST: Most Indian customers prefer WhatsApp surveys
//    over email. Send a WhatsApp message with a link to the survey.
//
// 3. INCENTIVE-DRIVEN: ₹500 off next booking for completing survey
//    significantly increases response rates in Indian market
//
// 4. GUIDE RATING: In Indian group tours, the guide/tour leader
//    makes or breaks the experience. Weighted heavily in scoring.
//
// 5. FOOD RATING: Dietary preferences (vegetarian, Jain, halal)
//    must be explicitly rated. Food complaints are common.
//
// 6. SENIOR ACCESSIBILITY: For pilgrimage tours, rate how well
//    the tour accommodated elderly travelers
```

### G. Package Performance Metrics

```typescript
interface PackagePerformanceMetrics {
  packageId: string;
  variantId?: string;
  period: DateRange;                     // Monthly, quarterly, annual

  // Sales metrics
  sales: PackageSalesMetrics;

  // Financial metrics
  financial: PackageFinancialMetrics;

  // Quality metrics
  quality: PackageQualityMetrics;

  // Operational metrics
  operational: PackageOperationalMetrics;

  // Customer metrics
  customer: PackageCustomerMetrics;

  // Lifecycle
  lifecycleStage: PackageLifecycleStage;
}

interface PackageSalesMetrics {
  totalBookings: number;
  totalPax: number;
  totalRevenue: Money;
  averageBookingValue: Money;

  // Funnel
  inquiries: number;
  quotationsSent: number;
  quotationToBookingRate: number;        // Conversion rate
  bookingToCompletionRate: number;       // How many actually traveled

  // Channel breakdown
  byChannel: Record<DistributionChannel, ChannelMetrics>;

  // Seasonal
  bookingsByMonth: Record<number, number>;
  revenueByMonth: Record<number, Money>;
}

interface ChannelMetrics {
  bookings: number;
  revenue: Money;
  averageValue: Money;
  conversionRate: number;
}

interface PackageFinancialMetrics {
  totalRevenue: Money;
  totalCost: Money;
  grossProfit: Money;
  grossMarginPercent: number;

  // Cost breakdown
  supplierCosts: Money;
  operationalCosts: Money;
  marketingCosts: Money;
  otaCommissions: Money;

  // Per booking
  revenuePerBooking: Money;
  profitPerBooking: Money;
  revenuePerPax: Money;
  profitPerPax: Money;

  // Trend
  marginTrend: 'improving' | 'stable' | 'declining';
  marginVsLastPeriod: number;            // +2% or -3%
}

interface PackageQualityMetrics {
  averageRating: number;                 // 1-5 stars
  ratingDistribution: Record<number, number>;
  netPromoterScore: number;              // -100 to +100
  complaintRate: number;                 // Complaints per 100 bookings
  commonComplaints: ComplaintCategory[];

  // Supplier quality
  hotelSatisfactionRate: number;
  guideSatisfactionRate: number;
  transportSatisfactionRate: number;
  foodSatisfactionRate: number;
}

interface PackageOperationalMetrics {
  // Departure metrics (fixed-departure)
  departuresScheduled: number;
  departuresCompleted: number;
  departuresCancelled: number;
  cancellationRate: number;              // % of departures cancelled
  fillRate: number;                      // Average seats filled per departure

  // Amendment metrics
  amendmentRate: number;                 // Amendments per booking
  commonAmendmentTypes: { type: AmendmentType; count: number }[];

  // Issue metrics
  onTourIssues: number;
  issuesPerTrip: number;
  averageResolutionTimeHours: number;

  // Operational cost
  coordinationHoursPerBooking: number;
}

interface PackageCustomerMetrics {
  repeatBookingRate: number;             // % who book again within 12 months
  referralRate: number;                  // % who refer others
  averageTravelerAge: number;
  topTravelerSegments: string[];
  loyaltyTierDistribution: Record<string, number>;
}

type PackageLifecycleStage =
  | 'new'                 // Recently created, gathering data
  | 'growing'             // Bookings increasing
  | 'mature'              // Stable performance
  | 'declining'           // Bookings/revenue declining
  | 'under_review'        // Being evaluated for changes
  | 'sunset';             // Being phased out

// Performance scorecard example:
//
// Kerala Backwaters Deluxe — Q4 2026 Performance
// ────────────────────────────────────────────────
// SALES:
//   Bookings: 47 (+15% vs Q3)
//   Revenue:  ₹19,74,000 (+12% vs Q3)
//   Conversion: 34% (inquiry → booking)
//   Avg. booking: ₹42,000
//
// FINANCIAL:
//   Gross margin: 32% (target: 30%) ✓
//   Profit/booking: ₹13,440
//   OTA commission: ₹2,96,100 (15% of OTA revenue)
//
// QUALITY:
//   Rating: 4.3/5 (target: 4.0) ✓
//   NPS: 62 (target: 50) ✓
//   Top complaint: "Houseboat quality varies" (8 reports)
//
// OPERATIONAL:
//   Fill rate: 87% (target: 85%) ✓
//   Cancellations: 2 departures (8%)
//   On-tour issues: 1.2 per trip
//   Amendment rate: 23%
//
// CUSTOMER:
//   Repeat rate: 18%
//   Referral rate: 12%
//   Avg. age: 34
//
// VERDICT: GROWING — Increase departures, standardize houseboat quality
```

### H. Package Retirement & Archival

```typescript
interface PackageRetirement {
  packageId: string;
  retirementReason: RetirementReason;
  retirementDate: Date;
  retiredBy: string;

  // Impact assessment
  impactAssessment: RetirementImpact;

  // Migration
  replacementPackageId?: string;
  migrationPlan?: MigrationPlan;

  // Status
  status: 'proposed' | 'approved' | 'in_progress' | 'completed';
}

type RetirementReason =
  | 'low_demand'           // Consistently low bookings
  | 'low_profitability'    // Margin below threshold
  | 'supplier_discontinued' // Key supplier no longer offers service
  | 'destination_unsafe'   // Safety/security concerns
  | 'regulatory_change'    // New regulations make package unviable
  | 'replaced_by_new'      // New version of package launched
  | 'seasonal_closure'     // Destination no longer accessible
  | 'quality_issues'       // Persistent quality complaints
  | 'strategic_decision';  // Agency business strategy change

interface RetirementImpact {
  // Active bookings
  activeBookings: number;                // Bookings with future travel dates
  activeBookingsRevenue: Money;

  // Historical
  lifetimeBookings: number;
  lifetimeRevenue: Money;
  lifetimePax: number;

  // Customer impact
  customersWithFutureBookings: number;
  refundLiability: Money;

  // Supplier impact
  suppliersToNotify: string[];
  contractTerminationRequired: string[];

  // Marketing
  marketingMaterialsToUpdate: string[];
  seoRedirectsNeeded: number;
}

interface MigrationPlan {
  // How to transition existing and prospective customers
  alternativePackageId: string;
  priceDifference: Money;                // +₹2,000 or -₹3,000
  automaticRedirect: boolean;            // URL redirect to new package
  customerCommunication: CommunicationPlan;
  bookingMigrationSteps: string[];
}

// Package lifecycle:
//
// CREATED ──► PUBLISHED ──► GROWING ──► MATURE ──► DECLINING ──► SUNSET ──► ARCHIVED
//                           │            │            │             │
//                           │            │            │             └── Keep data for
//                           │            │            │                 historical analysis
//                           │            │            │
//                           │            └──► REVISED (refresh itinerary, pricing)
//                           │                 └──► Back to GROWING
//                           │
//                           └──► CANCELLED (external factor)
//
// Retirement criteria:
//   - Bookings < 5 per season for 2 consecutive seasons
//   - Margin < 15% for 2 consecutive quarters
//   - Rating < 3.5 for 6+ months
//   - More than 20% departure cancellations
//   - Safety/regulatory concern identified
```

### I. Post-Tour Analytics & Reporting

```typescript
interface PostTourAnalytics {
  bookingId: string;
  packageId: string;
  departureId?: string;

  // Cost reconciliation
  costReconciliation: CostReconciliation;

  // Supplier performance
  supplierPerformance: SupplierPerformanceReview[];

  // Customer satisfaction
  customerSatisfaction?: FeedbackCollection;

  // Issues log
  issues: PostTourIssue[];

  // Learnings
  lessonsLearned: string[];
  recommendedChanges: RecommendedChange[];
}

interface CostReconciliation {
  // Budgeted vs. actual
  budgetedCost: Money;
  actualCost: Money;
  variance: Money;
  variancePercent: number;

  // Per-component variance
  componentVariances: ComponentVariance[];

  // Unplanned costs
  unplannedCosts: UnplannedCost[];
}

interface ComponentVariance {
  component: string;                     // "Accommodation", "Transport"
  budgeted: Money;
  actual: Money;
  variance: Money;
  reason?: string;                       // "Hotel upgraded due to overbooking"
}

interface UnplannedCost {
  description: string;                   // "Emergency vehicle replacement"
  amount: Money;
  reason: string;
  recoverable: boolean;                  // Can we claim insurance/supplier?
}

interface SupplierPerformanceReview {
  supplierId: string;
  supplierType: SupplierType;
  performanceRating: number;             // 1-5
  punctualityRating: number;
  qualityRating: number;
  communicationRating: number;
  issuesEncountered: string[];
  wouldUseAgain: boolean;
  notes: string;
}

interface RecommendedChange {
  area: string;                          // "Itinerary", "Hotel", "Activity"
  currentApproach: string;
  recommendedApproach: string;
  rationale: string;
  impact: 'cost_reduction' | 'quality_improvement' | 'customer_satisfaction' | 'operational_efficiency';
  estimatedSavings?: Money;
}
```

---

## Open Problems

1. **Real-time trip tracking** — How do we get real-time location/status updates without requiring travelers to actively check in? GPS tracking raises privacy concerns.

2. **Supplier reconfirmation reliability** — Indian suppliers (especially smaller hotels and transport companies) often don't respond to reconfirmation requests. How do we handle unconfirmed suppliers close to departure?

3. **Weather disruption protocols** — Monsoon season disruptions (landslides in hill stations, flooding in Kerala) are common but unpredictable. How do we build dynamic itinerary adjustment capability?

4. **Voucherless travel** — Many modern hotels and airlines are moving away from physical vouchers. How do we support both digital-first and traditional voucher-requiring suppliers?

5. **Feedback fatigue** — Indian customers are often reluctant to fill surveys. How do we achieve 40%+ response rates without excessive incentives?

6. **Guide performance management** — Tour guides are often freelance and work with multiple agencies. How do we maintain quality standards when guides are not agency employees?

7. **Multi-departure coordination** — During peak season, an agency may have 10+ departures running simultaneously. How do we scale operations without proportional headcount increase?

8. **Performance metric normalization** — A ₹20,000 domestic package and a ₹2,00,000 international package have very different economics. How do we normalize performance metrics across package types?

---

## Next Steps

1. **Departure checklist prototype** — Build a configurable checklist system that agents can customize per package type
2. **On-tour dashboard MVP** — Design the real-time operations dashboard with alert priority levels
3. **Voucher generation pipeline** — Research PDF generation libraries and WhatsApp document delivery APIs
4. **Supplier reconfirmation automation** — Build automated reconfirmation reminders via WhatsApp/email with escalation rules
5. **Feedback survey design** — Create survey templates for different package categories (honeymoon, pilgrimage, educational)
6. **Performance analytics dashboard** — Design the package performance scorecard view for agency managers
7. **Weather disruption playbook** — Document standard protocols for monsoon, landslide, and cyclone disruptions for top destinations
8. **Guide management system** — Design a freelance guide pool management system with rating and assignment workflow
9. **Cross-reference with Booking Lifecycle** — Ensure operational handoff points align with booking stages in PACKAGE_03_BOOKING.md
10. **Cross-reference with Package Catalog** — Ensure retirement workflows connect to catalog management in PACKAGE_01_CATALOG.md

---

**Status:** Research exploration, not implementation
**Last Updated:** 2026-04-28
