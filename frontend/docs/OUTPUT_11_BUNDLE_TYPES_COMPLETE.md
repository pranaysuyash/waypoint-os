# Output Panel 11: Complete Bundle Types Taxonomy

> Comprehensive specification of all document types, their structure, variants, and use cases

---

## Part 1: Bundle Type Overview

### 1.1 What is a Bundle?

A **bundle** is a structured collection of travel documents generated for a specific trip. Each bundle type serves a distinct purpose in the customer journey and has unique formatting, content, and delivery requirements.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BUNDLE TYPE ECOSYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  QUOTE   │───▶│ITINERARY │───▶│ VOUCHER  │───▶│ INVOICE  │             │
│  │          │    │          │    │          │    │          │             │
│  │ - Prices │    │ - Schedule│    │ - Booking│    │ - Payment│             │
│  │ - Options│    │ - Details │    │ - Confirm│    │ - Amount │             │
│  │ - Valid  │    │ - Contacts│    │ - Vendors│    │ - Due    │             │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│       │               │               │               │                   │
│       ▼               ▼               ▼               ▼                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │   PRE    │    │  TICKET  │    │  VISA    │    │  INSUR   │             │
│  │  BOOKING │    │  ETS     │    │  DOCS    │    │  CERTS   │             │
│  │          │    │          │    │          │    │          │             │
│  │ - Tentative│    │ - Flight │    │ - Embassy│    │ - Policy │             │
│  │ - Hold    │    │ - Seat   │    │ - Status │    │ - Coverage│             │
│  │ - Expire  │    │ - Board  │    │ - Stamps │    │ - Claims │             │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Bundle Classification Matrix

| Category | Bundle Types | Purpose | Audience | Timing |
|----------|-------------|---------|----------|--------|
| **Pre-Booking** | Quote, Pre-Booking | Provide pricing, hold options | Customer | Before commitment |
| **Post-Booking** | Itinerary, Voucher, Ticket | Confirm details, enable travel | Customer + Vendors | After confirmation |
| **Financial** | Invoice, Receipt, Tax Invoice | Document payments, enable compliance | Customer + Accounts | Throughout lifecycle |
| **Supplementary** | Visa Docs, Insurance Certs, Travel Alerts | Support travel requirements | Customer | As needed |
| **Internal** | Booking Sheet, Commission Sheet, Vendor PO | Internal operations | Staff/Partners | Operational |

---

## Part 2: Core Bundle Types

### 2.1 Quote Bundle

**Purpose**: Provide pricing and options for customer consideration before booking

**When Generated**: 
- Customer makes initial inquiry
- Customer requests modification to existing quote
- Agent proactively sends promotional quote

**Validity**: Typically 7-30 days from generation date

**Content Structure**:

```typescript
interface QuoteBundle {
  // Metadata
  quoteNumber: string;           // e.g., "QT-2024-001234"
  validFrom: Date;
  validUntil: Date;
  generatedAt: Date;
  generatedBy: string;           // Agent name/ID

  // Customer Information
  customer: {
    name: string;
    email: string;
    phone: string;
    reference?: string;          // Customer reference number
  };

  // Trip Overview
  trip: {
    type: 'international' | 'domestic' | 'honeymoon' | 'family' | 'business' | 'group';
    destination: string;
    duration: number;            // Nights
    travelDateRange: {
      from: Date;
      to: Date;
      flexible: boolean;
    };
    pax: {
      adults: number;
      children: number;
      infants: number;
    };
  };

  // Pricing Summary (Critical)
  pricing: {
    currency: string;            // INR, USD, EUR, etc.
    baseCost: number;
    taxes: number;
    fees: number;
    total: number;
    breakdown: PricingBreakdown[];
    priceIncludes: string[];     // "Breakfast", "Airport transfers", etc.
    priceExcludes: string[];     // "Visa fees", "Personal expenses", etc.
  };

  // Quote Options (If multiple variants provided)
  options?: QuoteOption[];

  // Terms and Conditions
  terms: {
    validityNote: string;
    cancellationPolicy: string;
    paymentSchedule: string[];
    modificationPolicy: string;
  };

  // Branding
  agency: {
    name: string;
    logo: string;
    contact: {
      phone: string;
      email: string;
      website: string;
      address: string;
    };
  };
}

interface QuoteOption {
  optionId: string;
  name: string;                  // "Budget Option", "Premium Option"
  description: string;
  highlights: string[];
  pricing: PricingBreakdown;
  differentiators: string[];     // What makes this option different
}

interface PricingBreakdown {
  category: string;              // "Flights", "Hotels", "Transfers", etc.
  items: {
    description: string;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }[];
}
```

**Quote Variants**:

| Variant | Use Case | Key Differences |
|---------|----------|-----------------|
| **Standard Quote** | Regular inquiry | Full pricing, single option |
| **Comparative Quote** | Multiple options | Side-by-side comparison |
| **Promotional Quote** | Special offers | Highlighted discounts, urgency |
| **Group Quote** | Group travel | Per-person vs total pricing, group terms |
| **Corporate Quote** | Business travel | Company billing, GST details, policy codes |

**Quote Display Template**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QUOTE                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  [AGENCY LOGO]                    Quote #: QT-2024-001234             │  │
│  │  ABC Travels Pvt Ltd              Valid Until: 15 Dec 2024            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  QUOTE FOR                                       Date: 08 Dec 2024     │  │
│  │  Mr. Rajesh Kumar                                                       │  │
│  │  rajesh.k@email.com                                                     │  │
│  │  +91 98765 43210                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TRIP OVERVIEW                                                          │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  Destination:  Dubai, UAE                                              │  │
│  │  Duration:     5 Nights / 6 Days                                        │  │
│  │  Travel Dates: 20 Jan 2025 - 25 Jan 2025                               │  │
│  │  Travelers:    2 Adults, 1 Child (8 years)                             │  │
│  │  Trip Type:    Family Vacation                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PRICE BREAKDOWN                                                        │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  ✈️  FLIGHTS                                                   │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Delhi → Dubai (IndiGo 6E 1475)                     ₹18,500   │   │  │
│  │  │  Dubai → Delhi (IndiGo 6E 1476)                     ₹18,500   │   │  │
│  │  │                                                         ─────   │   │  │
│  │  │  Subtotal: Flights                                 ₹37,000   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🏨  ACCOMMODATION                                              │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Atlantis The Royal (5 nights)                     ₹85,000   │   │  │
│  │  │  Room Type: Deluxe Room, King Bed                            │   │  │
│  │  │  Board Basis: Breakfast + Dinner                             │   │  │
│  │  │                                                         ─────   │   │  │
│  │  │  Subtotal: Accommodation                           ₹85,000   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🚗  TRANSFERS                                                  │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Airport ↔ Hotel (Private SUV)                      ₹6,000   │   │  │
│  │  │                                                         ─────   │   │  │
│  │  │  Subtotal: Transfers                                 ₹6,000   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🎫  ACTIVITIES                                                 │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Dubai Frame + Garden Glow Tour                    ₹4,500   │   │  │
│  │  │  Desert Safari with BBQ Dinner                       ₹6,000   │   │  │
│  │  │  Burj Khalifa 124th Floor                            ₹3,000   │   │  │
│  │  │                                                         ─────   │   │  │
│  │  │  Subtotal: Activities                               ₹13,500   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ──────────────────────────────────────────────────────────────────────│  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  💰  TAXES & FEES                                               │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  GST (18%)                                              ₹12,690   │   │  │
│  │  │  Payment Processing Fee                                ₹500   │   │  │
│  │  │                                                         ─────   │   │  │
│  │  │  Subtotal: Taxes & Fees                             ₹13,190   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                   │   │  │
│  │  │                        GRAND TOTAL                     ₹1,54,690   │   │  │
│  │  │                        Per Person (3)                 ₹51,563   │   │  │
│  │  │                                                                   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PRICE INCLUDES                                                         │  │
│  │  ✈️  Return economy class flights                                      │  │
│  │  🏨  5 nights accommodation at Atlantis The Royal                       │  │
│  │  🍽️  Breakfast + Dinner as specified                                   │  │
│  │  🚗  All airport transfers in private SUV                               │  │
│  │  🎫  All sightseeing as mentioned                                      │  │
│  │  📋  Visa assistance                                                    │  │
│  │                                                                         │  │
│  │  PRICE EXCLUDES                                                         │  │
│  │  🛂  Visa charges (approx. ₹5,000 per person)                           │  │
│  │  💉  Travel insurance (mandatory)                                       │  │
│  │  🍕  Meals not specified in itinerary                                   │  │
│  │  🛍️  Personal expenses, tips, laundry                                   │  │
│  │  📸  Camera fees at monuments                                          │  │
│  │  🎢  Any activities not mentioned in inclusions                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TERMS & CONDITIONS                                                      │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  • This quote is valid until 15 December 2024                          │  │
│  │  • Prices are subject to availability at the time of booking           │  │
│  │  • Flight prices may change until ticketed                              │  │
│  │  • 25% advance payment required to confirm booking                     │  │
│  │  • Balance payment due 15 days before travel                            │  │
│  │  • Cancellation charges apply as per policy below                      │  │
│  │                                                                         │  │
│  │  CANCELLATION POLICY                                                    │  │
│  │  ────────────────────────────────────────────────────────────────────  │  │
│  │  • Before 30 days: Full refund minus ₹2,000 per person                 │  │
│  │  • 29-15 days: 50% refund                                              │  │
│  │  • 14-8 days: 25% refund                                               │  │
│  │  • 7-0 days: No refund                                                 │  │
│  │  • No show: No refund                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  CONTACT US                                                             │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  📞  +91 11 2345 6789          📧  bookings@abctravels.com             │  │
│  │  🌐  www.abctravels.com        📍  123, Connaught Place, New Delhi     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Pre-Booking Bundle

**Purpose**: Hold tentative bookings while customer makes decision

**When Generated**:
- Customer requests hold on option
- Agent initiates booking process awaiting confirmation

**Validity**: Typically 24-72 hours

**Key Features**:
- Reservation/PNR numbers from vendors
- Hold expiration time
- Payment deadline
- "Not yet confirmed" disclaimers

**Content Structure**:

```typescript
interface PreBookingBundle {
  // Inherits from QuoteBundle, adds:

  status: 'HOLD' | 'PENDING_CONFIRMATION' | 'AWAITING_PAYMENT';

  holds: {
    category: 'FLIGHT' | 'HOTEL' | 'TRANSFER' | 'ACTIVITY';
    vendor: string;
    referenceNumber: string;     // PNR, confirmation number
    holdExpiry: Date;            // When hold expires
    status: 'HELD' | 'CONFIRMED' | 'RELEASED';
    notes?: string;
  }[];

  actionRequired: {
    type: 'PAYMENT' | 'DOCUMENT' | 'APPROVAL';
    description: string;
    deadline: Date;
  }[];

  warnings: string[];            // "Hotel hold expires in 18 hours"
}
```

**Pre-Booking Display Features**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️  PRE-BOOKING CONFIRMATION                                      │
│  ─────────────────────────────────────────────────────────────────  │
│  Your booking is ON HOLD but NOT CONFIRMED                         │
│                                                                     │
│  ⏰  TIME SENSITIVE                                                │
│  Hold expires: 10 Dec 2024, 6:00 PM (18 hours from now)            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  🎯  ACTION REQUIRED                                         │   │
│  │  ───────────────────────────────────────────────────────────  │   │
│  │  Pay ₹38,673 (25% advance) to confirm this booking          │   │
│  │  Payment link: https://pay.abctravels.com/QT-2024-001234    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  📋  HELD RESERVATIONS                                        │   │
│  │  ───────────────────────────────────────────────────────────  │   │
│  │  ✈️  IndiGo 6E 1475/76: PNR ABC123 (held until 11 Dec)      │   │
│  │  🏨  Atlantis The Royal: CONF12345 (held until 10 Dec, 6PM)  │   │
│  │  🚗  Private Transfer: Confirmed                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Itinerary Bundle

**Purpose**: Detailed travel plan for confirmed bookings

**When Generated**: After booking confirmation, before travel

**Delivery**: Primary customer-facing document

**Content Structure**:

```typescript
interface ItineraryBundle {
  // Metadata
  itineraryNumber: string;
  bookingReference: string;
  bookingDate: Date;
  generatedAt: Date;

  // Customer Information
  customer: {
    name: string;
    email: string;
    phone: string;
    emergencyContact?: {
      name: string;
      relationship: string;
      phone: string;
    };
  };

  // Trip Overview
  trip: {
    name: string;
    destination: string;
    type: string;
    duration: number;
    travelDates: {
      from: Date;
      to: Date;
    };
    pax: PaxDetails;
  };

  // Detailed Itinerary (Day by Day)
  days: ItineraryDay[];

  // Summary Table
  summary: {
    flights: FlightSummary[];
    hotels: HotelSummary[];
    transfers: TransferSummary[];
    activities: ActivitySummary[];
  };

  // Important Information
  importantInfo: {
    visaRequirements?: VisaInfo;
    insurance?: InsuranceInfo;
    weather?: WeatherInfo;
    currency?: CurrencyInfo;
    language?: string[];
    emergencyContacts: EmergencyContact[];
    packingTips?: string[];
  };

  // Vendor Contact Information
  vendorContacts: {
    category: string;
    name: string;
    phone: string;
    email?: string;
    address?: string;
  }[];
}

interface ItineraryDay {
  dayNumber: number;
  date: Date;
  title: string;
  description?: string;
  timeline: {
    time: string;               // "09:00", "14:30", "TBD"
    activity: string;
    type: 'FLIGHT' | 'TRANSFER' | 'HOTEL' | 'ACTIVITY' | 'MEAL' | 'FREE_TIME';
    details?: string;
    location?: string;
    duration?: string;          // "2 hours", "Overnight"
    status?: 'CONFIRMED' | 'TENTATIVE' | 'OPTIONAL';
    bookingReference?: string;
  }[];
  meals?: {
    breakfast?: string;
    lunch?: string;
    dinner?: string;
  };
  notes?: string[];
}
```

**Itinerary Display Template**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRAVEL ITINERARY                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  [AGENCY LOGO]                    Booking Ref: ABCT-2024-1234         │  │
│  │  ABC Travels Pvt Ltd              Booking Date: 12 Dec 2024            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TRAVELERS                                                               │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  1. Mr. Rajesh Kumar (Adult)                                            │  │
│  │     Passport: A1234567 | Exp: 15 Mar 2029                               │  │
│  │  2. Mrs. Priya Sharma (Adult)                                           │  │
│  │     Passport: B7654321 | Exp: 22 Aug 2028                               │  │
│  │  3. Master Aarav Kumar (Child, 8 yrs)                                   │  │
│  │     Passport: C9876543 | Exp: 03 Feb 2030                               │  │
│  │                                                                         │  │
│  │  Emergency Contact: Mr. Suresh Kumar (+91 99887 76655) - Father         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TRIP SUMMARY                                                           │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  Destination: Dubai, UAE     Dates: 20-25 Jan 2025     Duration: 5N/6D │  │
│  │  Flights: 2 segments         Hotels: 1 property        Activities: 4   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  DETAILED ITINERARY                                                     │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  DAY 1 - Monday, 20 January 2025                                │   │  │
│  │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │  │
│  │  │                                                                  │   │  │
│  │  │  ✈️  Departure from Delhi                                       │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 06:00                                                     │   │  │
│  │  │  Flight: IndiGo 6E 1475 | Economy | PNR: ABC123                 │   │  │
│  │  │  Terminal: T3, Indira Gandhi International Airport              │   │  │
│  │  │  Reporting: 03:00 (3 hours before departure)                    │   │  │
│  │  │  Duration: 3h 30m                                                │   │  │
│  │  │  Meals: Breakfast on board                                       │   │  │
│  │  │                                                                  │   │  │
│  │  │  ✈️  Arrival in Dubai                                           │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 08:00 (Local time, GMT+4)                                │   │  │
│  │  │  Terminal: T1, Dubai International Airport                      │   │  │
│  │  │                                                                  │   │  │
│  │  │  🚗  Transfer to Hotel                                          │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 08:30 - 09:30                                            │   │  │
│  │  │  Type: Private SUV (Chauffeur: Mohammed)                       │   │  │
│  │  │  Driver Contact: +971 50 123 4567                               │   │  │
│  │  │                                                                  │   │  │
│  │  │  🏨  Hotel Check-in                                             │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 09:30                                                    │   │  │
│  │  │  Hotel: Atlantis The Royal                                     │   │  │
│  │  │  Address: Palm Jumeirah, Dubai                                 │   │  │
│  │  │  Booking Ref: CONF12345                                        │   │  │
│  │  │  Room: Deluxe Room, King Bed, City View                        │   │  │
│  │  │  Board Basis: Breakfast + Dinner                               │   │  │
│  │  │                                                                  │   │  │
│  │  │  🍽️  Meals                                                     │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Breakfast: On flight                                          │   │  │
│  │  │  Lunch: At leisure (explore hotel)                              │   │  │
│  │  │  Dinner: At hotel (included)                                    │   │  │
│  │  │                                                                  │   │  │
│  │  │  📝  Notes                                                      │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  • Rest after journey, explore hotel facilities                 │   │  │
│  │  │  • Dubai Aquarium & Underwater Zoo is in the hotel             │   │  │
│  │  │                                                                  │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  DAY 2 - Tuesday, 21 January 2025                               │   │  │
│  │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │  │
│  │  │                                                                  │   │  │
│  │  │  🍽️  Breakfast at Hotel                                        │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 07:00 - 10:00 | Location: Kaleidoscope Restaurant        │   │  │
│  │  │                                                                  │   │  │
│  │  │  🎫  Morning Activity: Dubai Frame + Garden Glow               │   │  │
│  │  ────────────────────────────────────────────────────────────       │  │
│  │  Time: 09:00 - 13:00                                               │  │
│  │  Pickup: 08:30 from hotel lobby                                    │  │
│  │  Ticket Ref: ACT/DF/2024/12345                                     │  │
│  │  Includes: Guide, entrance fees, transfers                         │  │
│  │  Notes: Wear comfortable shoes                                      │  │
│  │                                                                  │   │  │
│  │  🍽️  Lunch: At leisure (Zabeel Park area)                         │   │  │
│  │                                                                  │   │  │
│  │  🏨  Rest at Hotel                                                │   │  │
│  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  Time: 14:00 - 16:00                                              │   │  │
│  │                                                                  │   │  │
│  │  🎫  Evening Activity: Dubai Mall & Aquarium                       │   │  │
│  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  Time: 16:30 - 20:00                                              │   │  │
│  │  Pickup: 16:15 from hotel lobby                                    │   │  │
│  │  Notes: Dubai Aquarium is in the mall                              │  │
│  │                                                                  │   │  │
│  │  🍽️  Dinner: At hotel (included)                                  │   │  │
│  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  DAY 3 - Wednesday, 22 January 2025                             │   │  │
│  │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │  │
│  │  │                                                                  │   │  │
│  │  │  🍽️  Breakfast at Hotel                                        │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 07:00 - 10:00                                            │   │  │
│  │  │                                                                  │   │  │
│  │  │  🏨  Hotel Checkout & Transfer to Desert                        │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 14:00                                                    │   │  │
│  │  │  Luggage stored at hotel                                        │   │  │
│  │  │                                                                  │   │  │
│  │  │  🎫  Evening Activity: Desert Safari with BBQ Dinner            │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 15:30 - 21:30                                            │   │  │
│  │  │  Pickup: 15:15 from hotel lobby                                  │   │  │
│  │  │  Ticket Ref: ACT/DS/2024/67890                                  │   │  │
│  │  │  Includes: Dune bashing, camel ride, BBQ dinner, shows          │   │  │
│  │  │  Notes: Wear comfortable clothes, sunscreen essential            │   │  │
│  │  │                                                                  │   │  │
│  │  │  🏨  Return to Hotel                                            │   │  │
│  │  │  ────────────────────────────────────────────────────────────   │   │  │
│  │  │  Time: 21:30                                                    │   │  │
│  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  [... DAY 4, DAY 5, DAY 6 similar format ...]                          │  │
│  │                                                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  BOOKING SUMMARY TABLE                                                 │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  ✈️  FLIGHTS                                                   │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Route   Flight    Date       Time   Class   PNR       Status  │   │  │
│  │  │  ─────── ───────── ────────── ────── ──────  ────────  ──────  │   │  │
│  │  │  DEL-DXB 6E 1475   20 Jan     06:00  Economy  ABC123   Confirmed│   │  │
│  │  │  DXB-DEL 6E 1476   25 Jan     22:00  Economy  ABC123   Confirmed│   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🏨  HOTELS                                                    │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Hotel              Check-in  Check-out  Room   Ref        Status│   │  │
│  │  │  ────────────────── ────────  ──────────  ─────  ────────── ──────│   │  │
│  │  │  Atlantis The Royal 20 Jan    25 Jan      Deluxe CONF12345 Confirmed│   │  │
│  │  │                     14:00     11:00       King                │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🚗  TRANSFERS                                                 │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Route                      Date     Time   Vehicle   Status  │   │  │
│  │  │  ────────────────────────── ──────── ────── ────────── ───────  │   │  │
│  │  │  Airport → Hotel            20 Jan   08:30  Private SUV Confirmed│   │  │
│  │  │  Hotel → Airport            25 Jan   19:00  Private SUV Confirmed│   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🎫  ACTIVITIES                                                │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Activity                   Date     Time     Ref        Status│   │  │
│  │  │  ─────────────────────────── ──────── ──────── ────────── ──────│   │  │
│  │  │  Dubai Frame + Garden Glow  21 Jan   09:00    ACT/DF/.. Confirmed│   │  │
│  │  │  Desert Safari              22 Jan   15:30    ACT/DS/.. Confirmed│   │  │
│  │  │  Burj Khalifa 124th Floor   23 Jan   16:00    ACT/BK/.. Confirmed│   │  │
│  │  │  Marina Dhow Cruise         24 Jan   19:30    ACT/DC/.. Confirmed│   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  IMPORTANT INFORMATION                                                  │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🛂  VISA REQUIREMENTS                                         │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Indian citizens require a visa for UAE. Your visa has been     │   │  │
│  │  │  applied for. Status: PENDING                                    │   │  │
│  │  │  Application Ref: VISA-2024-7890                                 │   │  │
│  │  │  Expected: 3-5 working days                                      │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  💉  TRAVEL INSURANCE                                          │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Policy: ICICI Lombard Travel Insurance                         │   │  │
│  │  │  Policy No: TLI/2024/123456                                     │   │  │
│  │  │  Coverage: Medical, trip delay, lost baggage                    │   │  │
│  │  │  Validity: 20 Jan 2025 - 25 Jan 2025                             │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🌡️  WEATHER                                                   │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Jan in Dubai: Pleasant, 20-25°C during day, 12-18°C night      │   │  │
│  │  │  Pack: Light cottons for day, light jacket for evenings         │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  💵  CURRENCY                                                  │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Local Currency: UAE Dirham (AED)                               │   │  │
│  │  │  Exchange Rate (approx): ₹1 = AED 0.045                         │   │  │
│  │  │  Cards widely accepted; carry some cash for small vendors       │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  📞  EMERGENCY CONTACTS                                        │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  ABC Travels 24/7:    +91 11 2345 6789                          │   │  │
│  │  │  UAE Emergency:        999                                      │   │  │
│  │  │  Indian Embassy:       +971 4 396 6222                          │   │  │
│  │  │  Hotel: Atlantis       +971 4 426 2000                          │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  🎒  PACKING TIPS                                              │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  • Valid passport (6+ months validity remaining)               │   │  │
│  │  │  • Visa approval printout                                       │   │  │
│  │  │  • Travel insurance policy document                             │   │  │
│  │  │  • Comfortable walking shoes                                    │   │  │
│  │  │  • Sunscreen, sunglasses, hat                                   │   │  │
│  │  │  • Light cotton clothing, modest for religious sites            │   │  │
│  │  │  • Universal travel adapter                                     │   │  │
│  │  │  • Any personal medications                                     │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  VENDOR CONTACTS                                                        │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  Transfer Company: Desert Adventures Tourism                   │   │  │
│  │  │  Phone: +971 4 123 4567   Email: info@desertadventures.ae        │   │  │
│  │  │                                                                   │   │  │
│  │  │  Activity Operator: Arabian Adventures                          │   │  │
│  │  │  Phone: +971 4 123 4567   Email: bookings@arabian-adventures.com  │   │  │
│  │  │                                                                   │   │  │
│  │  │  Hotel: Atlantis The Royal, Palm Jumeirah                       │   │  │
│  │  │  Phone: +971 4 426 2000   Email: reservations@atlantis.com       │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  CONTACT US                                                             │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  📞  24/7 Support:     +91 11 2345 6789                               │  │
│  │  📧  Email:            support@abctravels.com                          │  │
│  │  🌐  Website:          www.abctravels.com                              │  │
│  │  💬  WhatsApp:         wa.me/9198765432100                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Voucher Bundle

**Purpose**: Proof of booking for vendors (hotels, tours, transfers)

**When Generated**: After booking confirmation

**Delivery**: To customer (for presenting to vendors) AND to vendors

**Content Structure**:

```typescript
interface VoucherBundle {
  voucherNumber: string;
  bookingReference: string;
  type: 'HOTEL' | 'TRANSFER' | 'ACTIVITY' | 'COMBINED';

  // Customer Details
  customer: {
    name: string;
    email: string;
    phone: string;
  };

  // Voucher Details
  vouchers: {
    type: string;
    voucherNumber: string;
    supplier: string;
    service: string;
    date: Date;
    time?: string;
    location?: string;
    pax: PaxDetails;
    inclusions: string[];
    exclusions?: string[];
    importantNotes?: string[];
    cancellationPolicy: string;
  }[];

  // Payment Status
  paymentStatus: 'FULLY_PAID' | 'PARTIALLY_PAID' | 'PENDING';

  // Barcode/QR Code
  verificationCode: string;
}
```

**Voucher Display Template**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE VOUCHER                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  [AGENCY LOGO]                    Voucher: VC-2024-001234             │  │
│  │  ABC Travels Pvt Ltd              Booking: ABCT-2024-1234             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  GUEST DETAILS                                                          │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  Guest Name: Mr. Rajesh Kumar + 2                                     │  │
│  │  Contact: +91 98765 43210                                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  VOUCHER 1: ACCOMMODATION                                                │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  Hotel:           Atlantis The Royal                            │   │  │
│  │  │  Address:         Palm Jumeirah, Dubai, UAE                      │   │  │
│  │  │  Phone:           +971 4 426 2000                                │   │  │
│  │  │                                                                  │   │  │
│  │  │  Check-in:        Monday, 20 January 2025, 14:00                 │   │  │
│  │  │  Check-out:       Saturday, 25 January 2025, 11:00               │   │  │
│  │  │  Nights:          5                                              │   │  │
│  │  │                                                                  │   │  │
│  │  │  Room Type:       Deluxe Room, King Bed, City View               │   │  │
│  │  │  Board Basis:     Breakfast + Dinner                             │   │  │
│  │  │  Guests:          2 Adults, 1 Child (8 yrs)                      │   │  │
│  │  │                                                                  │   │  │
│  │  │  Confirmation No:  CONF12345                                     │   │  │
│  │  │  Booked Through:  ABC Travels Pvt Ltd                            │   │  │
│  │  │  Payment Status:   ✅ FULLY PAID                                  │   │  │
│  │  │                                                                  │   │  │
│  │  │  INCLUSIONS                                                      │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  • Accommodation in Deluxe Room (King Bed)                      │   │  │
│  │  │  • Daily breakfast at Kaleidoscope Restaurant                   │   │  │
│  │  │  • Daily dinner (set menu)                                      │   │  │
│  │  │  • Access to Aquaventure Waterpark (2 tickets per room)         │   │  │
│  │  │  • Access to Lost Chambers Aquarium                             │   │  │
│  │  │  • Complimentary WiFi in room                                   │   │  │
│  │  │                                                                  │   │  │
│  │  │  IMPORTANT NOTES                                                 │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  • Present this voucher and valid ID at check-in                │   │  │
│  │  │  • Early check-in/late check-out subject to availability        │   │  │
│  │  │  • Credit card required for incidentals at check-in             │   │  │
│  │  │  • Cancellation policy: 48 hours notice for full refund          │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  ████████████████████████████████████████████████████████████   │   │  │
│  │  │  ██████ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ ██████   │   │  │
│  │  │  ██████  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███╗   ██╗    ██████   │   │  │
│  │  │  ██████  ████╗  ██║██╔════╝██║  ██║██║   ██║████╗  ██║    ██████   │   │  │
│  │  │  ██████  ██╔██╗ ██║███████╗███████║██║   ██║██╔██╗ ██║    ██████   │   │  │
│  │  │  ██████  ██║╚██╗██║╚════██║██╔══██║██║   ██║██║╚██╗██║    ██████   │   │  │
│  │  │  ██████  ██║ ╚████║███████║██║  ██║╚██████╔╝██║ ╚████║    ██████   │   │  │
│  │  │  ██████  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝    ██████   │   │  │
│  │  │  ██████ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ██████   │   │  │
│  │  │  ████████████████████████████████████████████████████████████   │   │  │
│  │  │                                                                  │   │  │
│  │  │  VC-2024-001234-HOTEL | atlantis.com/bookings/VC-2024-001234   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  VOUCHER 2: TRANSFERS                                                    │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  [Similar format for transfer vouchers]                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  VOUCHER 3: ACTIVITIES                                                  │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  [Similar format for activity vouchers]                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.5 Invoice Bundle

**Purpose**: Formal payment documentation for accounting and tax purposes

**When Generated**:
- After each payment received
- Final invoice after full payment

**Content Structure**:

```typescript
interface InvoiceBundle {
  invoiceNumber: string;
  invoiceType: 'PROFORMA' | 'TAX_INVOICE' | 'COMMERCIAL';
  invoiceDate: Date;
  dueDate?: Date;

  // Billing Information
  billTo: {
    name: string;
    address: string;
    gstin?: string;              // GST Number for tax invoices
    pan?: string;                // PAN Number
    phone: string;
    email: string;
  };

  // Shipping/Delivery Information (if different)
  shipTo?: {
    name: string;
    address: string;
  };

  // Trip Reference
  tripReference: {
    bookingNumber: string;
    itineraryNumber: string;
    destination: string;
    travelDates: string;
  };

  // Invoice Items
  items: {
    srNo: number;
    description: string;
    sacCode?: string;            // SAC code for GST
    quantity: number;
    unit: string;                // "per person", "per night", etc.
    unitPrice: number;
    taxableValue: number;
    taxRate?: number;            // GST percentage
    taxAmount?: number;
    total: number;
  }[];

  // Tax Summary
  taxSummary: {
    cgst?: { rate: number; amount: number };
    sgst?: { rate: number; amount: number };
    igst?: { rate: number; amount: number };
    totalTax: number;
  };

  // Payment Summary
  paymentSummary: {
    totalInvoiceValue: number;
    amountPaid: number;
    amountDue: number;
    paymentStatus: 'PAID' | 'PARTIAL' | 'PENDING';
  };

  // Payment Details (for pending/partial)
  paymentDetails?: {
    bankName: string;
    accountNumber: string;
    accountName: string;
    ifscCode: string;
    branch: string;
    upiId?: string;
    paymentLink?: string;
  };

  // Terms
  terms: string[];

  // Authorized Signatory
  authorizedSignatory: {
    name: string;
    designation: string;
  };

  // Agency GST Details
  agency: {
    name: string;
    address: string;
    gstin: string;
    pan: string;
  };
}
```

**Invoice Display Template**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TAX INVOICE                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  [AGENCY LOGO]                         ┌───────────────────────────┐  │  │
│  │  ABC Travels Private Limited            │ TAX INVOICE               │  │  │
│  │  (A Unit of ABC Enterprises)            │ ─────────────────────────  │  │  │
│  │                                         │ Invoice No: INV-2024-0456 │  │  │
│  │  123, Connaught Place                   │ Date: 15 Dec 2024         │  │  │
│  │  New Delhi - 110001                     │ Due Date: 20 Dec 2024     │  │  │
│  │  Delhi, India                           └───────────────────────────┘  │  │
│  │                                                                         │  │
│  │  GSTIN: 07ABCDE1234F1Z5   PAN: ABCDE1234F                              │  │
│  │  Phone: +91 11 2345 6789   Email: accounts@abctravels.com               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────┬─────────────────────────────────┐│
│  │  BILL TO                              │ SHIP TO (if different)          ││
│  │  ───────────────────────────────────  │ ─────────────────────────────  ││
│  │                                       │                                 ││
│  │  Mr. Rajesh Kumar                     │                                 ││
│  │  B-123, Sector 45                     │                                 ││
│  │  Gurgaon - 122003                     │                                 ││
│  │  Haryana                              │                                 ││
│  │                                       │                                 ││
│  │  GSTIN: N/A                           │                                 ││
│  │  PAN: ABCDE1234F                      │                                 ││
│  │  Phone: +91 98765 43210               │                                 ││
│  │  Email: rajesh.k@email.com            │                                 ││
│  └───────────────────────────────────────┴─────────────────────────────────┘│
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TRIP REFERENCE                                                         │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  Booking: ABCT-2024-1234    Destination: Dubai, UAE    Dates: 20-25 Jan │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  INVOICE DETAILS                                                        │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌──────┬────────────────────────────┬──────────┬──────────┬──────────┐ │  │
│  │  │  #   │ Description                │   Qty    │  Unit    │   Rate   │ │  │
│  │  ├──────┼────────────────────────────┼──────────┼──────────┼──────────┤ │  │
│  │  │      │                            │          │          │  (₹)     │ │  │
│  │  ├──────┼────────────────────────────┼──────────┼──────────┼──────────┤ │  │
│  │  │  1   │ Flight Tickets             │    3     │ per pax  │ 12,333   │ │  │
│  │  │      │ Delhi ↔ Dubai (Return)     │          │          │          │ │  │
│  │  │      │ SAC: 9964                  │          │          │          │ │  │
│  │  ├──────┼────────────────────────────┼──────────┼──────────┼──────────┤ │  │
│  │  │  2   │ Hotel Accommodation        │    1     │ per room │ 85,000   │ │  │
│  │  │      │ Atlantis The Royal         │          │          │          │ │  │
│  │  │      │ 5 Nights, Deluxe Room      │          │          │          │ │  │
│  │  │      │ SAC: 9963                  │          │          │          │ │  │
│  │  ├──────┼────────────────────────────┼──────────┼──────────┼──────────┤ │  │
│  │  │  3   │ Airport Transfers          │    2     │ each way │  3,000   │ │  │
│  │  │      │ Private SUV                │          │          │          │ │  │
│  │  │      │ SAC: 9965                  │          │          │          │ │  │
│  │  ├──────┼────────────────────────────┼──────────┼──────────┼──────────┤ │  │
│  │  │  4   │ Sightseeing Activities     │    1     │ package  │ 13,500   │ │  │
│  │  │      │ Dubai Frame, Desert Safari,│          │          │          │ │  │
│  │  │      │ Burj Khalifa, Dhow Cruise  │          │          │          │ │  │
│  │  │      │ SAC: 9964                  │          │          │          │ │  │
│  │  ├──────┼────────────────────────────┼──────────┼──────────┼──────────┤ │  │
│  │  │      │                            │          │          │          │ │  │
│  │  │      │    SUBTOTAL                │          │          │ 1,16,833 │ │  │
│  │  ├──────┴────────────────────────────┴──────────┴──────────┴──────────┤ │  │
│  │  │                                                                       │ │  │
│  │  │  TAX SUMMARY                                                          │ │  │
│  │  │  ─────────────────────────────────────────────────────────────────  │ │  │
│  │  │  CGST (9% on ₹1,16,833):                                             ₹10,515              │ │  │
│  │  │  SGST (9% on ₹1,16,833):                                             ₹10,515              │ │  │
│  │  │  ─────────────────────────────────────────────────────────────────  │ │  │
│  │  │                                                                       │ │  │
│  │  │    GRAND TOTAL                                                      ₹1,37,863             │ │  │
│  │  └─────────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PAYMENT SUMMARY                                                        │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  Total Invoice Value:                                        ₹1,37,863 │  │
│  │  Amount Received (Advance):                                  ₹  38,673 │  │
│  │  Balance Payable:                                           ₹  99,190 │  │
│  │                                                                         │  │
│  │  Payment Status: ⚠️ PARTIAL PAYMENT - Balance due by 20 Dec 2024        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PAYMENT DETAILS                                                        │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  BANK TRANSFER                                                  │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  Bank:         HDFC Bank                                         │   │  │
│  │  │  Account No:   50100234567890                                    │   │  │
│  │  │  Account Name: ABC Travels Private Limited                       │   │  │
│  │  │  IFSC Code:    HDFC0001234                                       │   │  │
│  │  │  Branch:       Connaught Place, New Delhi                        │   │  │
│  │  │  Type:         Current Account                                   │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  UPI PAYMENT                                                    │   │  │
│  │  │  ─────────────────────────────────────────────────────────────  │   │  │
│  │  │  UPI ID:       abctravels@hdfc                                   │   │  │
│  │  │  Payment Link:  https://pay.abctravels.com/INV-2024-0456         │   │  │
│  │  │  Scan QR:      [QR Code]                                         │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TERMS & CONDITIONS                                                      │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  1. Payment is due within 5 days of invoice date                       │  │
│  │  2. Goods and Services Tax (GST) is applicable as per government norms │  │
│  │  3. Subject to Delhi jurisdiction only                                 │  │
│  │  4. Booking confirmation subject to realization of payment             │  │
│  │  5. Cancellation policy as per attached terms                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  BANK DETAILS (for NEFT/RTGS)                                          │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  Beneficiary Name: ABC Travels Private Limited                          │  │
│  │  Bank: HDFC Bank, A-45, Connaught Place, New Delhi - 110001            │  │
│  │  Account Number: 50100234567890                                          │  │
│  │  Account Type: Current Account                                          │  │
│  │  IFSC Code: HDFC0001234                                                 │  │
│  │  SWIFT Code: HDFCINBB                                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       ┌───┐ │
│  │  For ABC Travels Private Limited                                    │   │ │ │
│  │                                                                       │ 🔲│ │ │
│  │  Authorized Signatory                                                 │   │ │ │ │
│  │                                                                       │   │ │ │
│  │  [Signature]                                                         └───┘ │ │
│  │                                                                             │  │
│  │  This is a computer-generated invoice. No signature required.              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  AGENCY GST DETAILS                                                     │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  Legal Name: ABC Travels Private Limited                                │  │
│  │  Trade Name: ABC Travels                                                │  │
│  │  GSTIN: 07ABCDE1234F1Z5                                                  │  │
│  │  Constitution: Private Limited Company                                   │  │
│  │  Address: 123, Connaught Place, New Delhi - 110001, Delhi, India        │  │
│  │  State: Delhi (07)                                                       │  │
│  │  PAN: ABCDE1234F                                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Supplementary Bundle Types

### 3.1 Ticket E-Tickets Bundle

**Purpose**: Electronic tickets for flights, trains, buses

**Content Structure**:

```typescript
interface TicketBundle {
  ticketType: 'FLIGHT' | 'TRAIN' | 'BUS';
  ticketNumber: string;
  pnr: string;

  passenger: {
    name: string;
    type: 'ADULT' | 'CHILD' | 'INFANT';
    dob: Date;
    passport?: string;
  };

  flight?: {
    airline: string;
    flightNumber: string;
    from: { code: string; city: string; terminal: string };
    to: { code: string; city: string; terminal: string };
    date: Date;
    departure: string;
    arrival: string;
    duration: string;
    aircraft: string;
    class: 'ECONOMY' | 'BUSINESS' | 'FIRST';
    seat?: string;
    meal: string;
    baggage: { cabin: string; checkIn: string };
  };

  fare: {
    basis: string;
    class: string;
    currency: string;
    totalFare: number;
    breakdown: {
      baseFare: number;
      taxes: number;
      fees: number;
      surcharges: number;
    }[];
  };

  status: 'CONFIRMED' | 'WAITLISTED' | 'RAC' | 'CANCELLED';

  barcode: string;
}
```

---

### 3.2 Visa Documentation Bundle

**Purpose**: Visa application support documents

**Content Structure**:

```typescript
interface VisaDocsBundle {
  visaType: string;                // "Tourist", "Business", etc.
  destination: string;
  purpose: string;

  applicant: {
    name: string;
    passportNumber: string;
    nationality: string;
    dob: Date;
    occupation: string;
  };

  application: {
    applicationNumber: string;
    submittedDate: Date;
    status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'UNDER_PROCESS';
    expectedDecision?: Date;
  };

  documents: {
    type: string;
    provided: boolean;
    notes?: string;
  }[];

  embassy?: {
    name: string;
    address: string;
    phone: string;
    email: string;
    website: string;
  };

  importantNotes: string[];
}
```

---

### 3.3 Insurance Certificate Bundle

**Purpose**: Travel insurance policy document

**Content Structure**:

```typescript
interface InsuranceCertBundle {
  policyNumber: string;
  policyType: string;
  insurer: {
    name: string;
    logo: string;
    contact: { phone: string; email: string };
  };

  insured: {
    name: string;
    address: string;
    phone: string;
    email: string;
  };

  policy: {
    startDate: Date;
    endDate: Date;
    destination: string;
    duration: number;
    sumInsured: number;
    currency: string;
  };

  coverage: {
    category: string;
    covered: boolean;
    limit?: number;
    deductible?: number;
  }[];

  claims: {
    process: string[];
    documents: string[];
    contact: { phone: string; email: string };
  };

  exclusions: string[];
}
```

---

### 3.4 Travel Alert Bundle

**Purpose**: Real-time travel advisories and updates

**Content Structure**:

```typescript
interface TravelAlertBundle {
  alertId: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  category: 'WEATHER' | 'POLITICAL' | 'HEALTH' | 'TRANSPORT' | 'SECURITY';

  title: string;
  message: string;
  issuedAt: Date;
  validUntil?: Date;

  affectedRegions: {
    country: string;
    cities?: string[];
  };

  impact: {
    type: string;
    description: string;
    recommendedAction: string;
  }[];

  sources: {
    name: string;
    url: string;
  }[];
}
```

---

## Part 4: Internal Bundle Types

### 4.1 Booking Sheet Bundle

**Purpose**: Internal document for supplier booking

**Content**: Simplified version of itinerary with only supplier-relevant details

### 4.2 Commission Sheet Bundle

**Purpose**: Track commissions from suppliers

**Content Structure**:

```typescript
interface CommissionSheetBundle {
  bookingNumber: string;
  period: { from: Date; to: Date };

  commissions: {
    supplier: string;
    service: string;
    bookingValue: number;
    commissionRate: number;
    commissionAmount: number;
    status: 'EARNED' | 'PENDING' | 'RECEIVED';
    receivedDate?: Date;
  }[];

  summary: {
    totalCommission: number;
    received: number;
    pending: number;
  };
}
```

### 4.3 Vendor PO Bundle

**Purpose**: Purchase order sent to suppliers

**Content Structure**:

```typescript
interface VendorPOBundle {
  poNumber: string;
  poDate: Date;
  vendor: {
    name: string;
    contact: string;
    email: string;
  };

  bookingReference: string;
  customerName: string;

  items: {
    description: string;
    quantity: number;
    rate: number;
    amount: number;
  }[];

  totalAmount: number;
  paymentTerms: string;
  deliveryTerms: string;
}
```

---

## Part 5: Bundle Type Selector Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUNDLE TYPE SELECTION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TRIP STATUS                                                          │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                       │   │
│  │  ┌─────────┐    ┌────────────┐    ┌────────────────┐                 │   │
│  │  │ INQUIRY │───▶│ QUOTING    │───▶│ QUOTE SENT     │                 │   │
│  │  └────┬────┘    └─────┬──────┘    └────────┬───────┘                 │   │
│  │       │               │                     │                         │   │
│  │       ▼               ▼                     ▼                         │   │
│  │   Generate Quote    Generate Quote      Awaiting Decision           │   │
│  │   (Quote Bundle)    (Quote Bundle)      (Timer: 48h)                 │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CUSTOMER ACCEPTS                                                     │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │  Decision: HOLD or CONFIRM?                                  │    │   │
│  │  │                                                               │    │   │
│  │  │  HOLD → Generate Pre-Booking Bundle                          │    │   │
│  │  │  CONFIRM → Collect payment → Generate Confirmations          │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                    ┌──────────────┴───────────────┐                         │
│                    ▼                              ▼                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────┐   │
│  │  PRE-BOOKING PATH           │    │  CONFIRMATION PATH               │   │
│  │  ───────────────────────────│    │  ───────────────────────────────  │   │
│  │                             │    │                                  │   │
│  │  1. Create holds            │    │  1. Receive payment              │   │
│  │  2. Generate Pre-Booking    │    │  2. Confirm with suppliers       │   │
│  │  3. Send to customer        │    │  3. Generate Itinerary           │   │
│  │  4. Wait for decision       │    │  4. Generate Vouchers            │   │
│  │  5. If confirmed → Join     │    │  5. Generate Invoice             │   │
│  │     confirmation path       │    │  6. Generate E-Tickets           │   │
│  │                             │    │  7. Send all documents           │   │
│  └─────────────────────────────┘    └─────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  POST-BOOKING (As needed)                                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                       │   │
│  │  Visa Docs → Insurance Cert → Travel Alerts → Updates                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Bundle Type Matrix

### 6.1 Complete Reference Table

| Bundle Type | Primary Audience | Delivery Method | Generation Trigger | Template | Validity |
|-------------|------------------|-----------------|-------------------|----------|----------|
| **Quote** | Customer | Email, WhatsApp, Portal | Inquiry received | Quote | 7-30 days |
| **Pre-Booking** | Customer | Email, WhatsApp | Hold created | Pre-Booking | 24-72 hours |
| **Itinerary** | Customer | Email, WhatsApp, Portal | Booking confirmed | Itinerary | Until travel |
| **Voucher** | Customer + Vendor | Email, WhatsApp | Booking confirmed | Voucher | Travel dates |
| **Invoice** | Customer + Accounts | Email, Portal | Payment received/dues | Invoice | Per payment |
| **E-Ticket** | Customer | Email, App | Ticket issued | Ticket | Flight date |
| **Visa Docs** | Customer | Email, Portal | Visa applied | Visa Docs | Visa duration |
| **Insurance** | Customer | Email, Portal | Policy purchased | Insurance | Trip dates |
| **Booking Sheet** | Vendor | Email, Portal | Supplier booking | Internal | N/A |
| **Commission Sheet** | Accounts | Portal | Month-end | Internal | Period |
| **Vendor PO** | Vendor | Email | Supplier booking | PO | Per PO |
| **Travel Alert** | Customer | WhatsApp, Email | Event occurs | Alert | Event duration |

### 6.2 Template Assignment Matrix

| Bundle Type | Base Template | Trip Type Variants | Customization Level |
|-------------|---------------|-------------------|---------------------|
| Quote | `quote-base.hbs` | International, Domestic, Honeymoon | High (pricing, terms) |
| Pre-Booking | `prebooking-base.hbs` | Same as quote | Medium (hold details) |
| Itinerary | `itinerary-base.hbs` | All trip types | Very High (daily schedule) |
| Voucher | `voucher-base.hbs` | Hotel, Transfer, Activity | Low (vendor format) |
| Invoice | `invoice-base.hbs` | Proforma, Tax, Commercial | Medium (tax details) |
| E-Ticket | `ticket-base.hbs` | Flight, Train, Bus | Low (carrier format) |
| Visa Docs | `visa-base.hbs` | By destination | High (country specific) |
| Insurance | `insurance-base.hbs` | By insurer | Medium (policy details) |
| Booking Sheet | `booking-sheet.hbs` | By supplier | Low (supplier format) |
| Commission Sheet | `commission-sheet.hbs` | N/A | Low (standard) |

---

## Part 7: Bundle Content Requirements

### 7.1 Mandatory Content by Bundle Type

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   MANDATORY CONTENT REQUIREMENTS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ALL BUNDLES (Common Requirements)                                   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ✓ Agency logo and branding                                          │   │
│  │  ✓ Bundle reference number                                           │   │
│  │  ✓ Generation date                                                   │   │
│  │  ✓ Customer name and contact                                         │   │
│  │  ✓ Trip destination and dates                                        │   │
│  │  ✓ Agency contact information                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUOTE (Additional)                                                 │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ✓ Valid from and until dates                                       │   │
│  │  ✓ Complete price breakdown                                        │   │
│  │  ✓ Price inclusions                                                 │   │
│  │  ✓ Price exclusions                                                 │   │
│  │  ✓ Payment schedule                                                 │   │
│  │  ✓ Cancellation policy                                              │   │
│  │  ✓ Terms and conditions                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ITINERARY (Additional)                                             │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ✓ Day-by-day schedule                                              │   │
│  │  ✓ Timings for each activity                                       │   │
│  │  ✓ Booking reference numbers                                       │   │
│  │  ✓ Vendor contact information                                      │   │
│  │  ✓ Important information (visa, insurance, etc.)                   │   │
│  │  ✓ Emergency contacts                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  VOUCHER (Additional)                                              │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ✓ Supplier confirmation number                                    │   │
│  │  ✓ Service details (dates, times, locations)                       │   │
│  │  ✓ Inclusions and exclusions                                       │   │
│  │  ✓ Cancellation policy                                             │   │
│  │  ✓ QR code or barcode for verification                             │   │
│  │  ✓ Payment status                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  INVOICE (Additional)                                              │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  ✓ Invoice number and date                                         │   │
│  │  ✓ Bill to details (with GSTIN if applicable)                      │   │
│  │  ✓ Itemized breakdown with SAC codes                               │   │
│  │  ✓ Tax breakdown (CGST/SGST/IGST)                                  │   │
│  │  ✓ Total amount and payment status                                 │   │
│  │  ✓ Payment details (bank account, UPI)                             │   │
│  │  ✓ Terms and conditions                                            │   │
│  │  ✓ Agency GST details                                              │   │
│  │  ✓ Authorized signatory space                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Conditional Content Matrix

| Condition | Required Content | Bundle Types Affected |
|-----------|-----------------|----------------------|
| International trip | Passport details, visa information, embassy contacts | Quote, Itinerary, Visa Docs |
| Flight included | E-ticket, baggage allowance, meal details | Itinerary, Voucher, Ticket |
| Hotel included | Check-in/out times, room type, board basis | Itinerary, Voucher |
| Activities included | Tickets, timing, meeting points | Itinerary, Voucher |
| GST-registered customer | GSTIN, SAC codes, tax breakdown | Invoice |
| Corporate booking | Company billing, GST invoice, policy codes | Quote, Invoice |
| Group booking | Per-person pricing, group terms, leader details | Quote, Itinerary |
| Child/Infant passengers | Age proof requirements, special pricing | Quote, Itinerary, Ticket |
| Travel insurance | Policy document, coverage details, claims process | Insurance Cert |
| Visa required | Visa documents, embassy info, requirements | Visa Docs |

---

## Part 8: Bundle Delivery Configuration

### 8.1 Delivery Method by Bundle Type

| Bundle Type | Primary Delivery | Secondary Delivery | Customer Notification |
|-------------|-----------------|-------------------|----------------------|
| Quote | Email | WhatsApp | Yes |
| Pre-Booking | WhatsApp | Email | Urgent |
| Itinerary | WhatsApp | Email, Portal | Yes |
| Voucher | Email | Portal | Yes |
| Invoice | Email | Portal | Yes |
| E-Ticket | Email | App | Yes |
| Visa Docs | Email | Portal | Yes |
| Insurance | Email | Portal | Yes |
| Travel Alert | WhatsApp | Email | Urgent |
| Booking Sheet | Email (vendor) | Portal API | No |
| Commission Sheet | Portal (internal) | - | No |

### 8.2 Delivery Priority Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DELIVERY PRIORITY MATRIX                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔴  URGENT (Immediate delivery required)                            │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Pre-Booking (hold expiry imminent)                               │   │
│  │  • Travel Alerts (critical events)                                  │   │
│  │  • Payment Reminders (due within 24h)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🟡  HIGH (Same day delivery)                                        │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Itinerary (after booking confirmation)                           │   │
│  │  • Vouchers (after booking confirmation)                            │   │
│  │  • E-Tickets (after issuance)                                       │   │
│  │  • Invoices (after payment received)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🟢  NORMAL (Within 24 hours)                                        │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Quotes (initial inquiry)                                         │   │
│  │  • Visa Documentation                                              │   │
│  │  • Insurance Certificates                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔵  LOW (On-demand)                                                │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Commission Sheets (month-end)                                    │   │
│  │  • Booking Sheets (supplier sync)                                   │   │
│  │  • Historical Documents (portal access)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 9: Bundle Lifecycle

### 9.1 State Transitions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUNDLE LIFECYCLE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐      ┌──────────────┐      ┌─────────────┐               │
│  │   CREATED   │─────▶│    SENT      │─────▶│   DELIVERED │               │
│  │             │      │              │      │             │               │
│  │ - Generated │      │ - Queued     │      │ - Received  │               │
│  │ - Not sent  │      │ - Transmitting│     │ - Confirmed  │               │
│  └──────┬──────┘      └──────┬───────┘      └──────┬──────┘               │
│         │                     │                      │                     │
│         ▼                     ▼                      ▼                     │
│  ┌─────────────┐      ┌──────────────┐      ┌─────────────┐               │
│  │   FAILED    │      │   BOUNCED    │      │    VIEWED   │               │
│  │             │      │              │      │             │               │
│  │ - Error     │      │ - Invalid    │      │ - Opened    │               │
│  │ - Retry     │      │ - Returned   │      │ - Tracked   │               │
│  └─────────────┘      └──────────────┘      └──────┬──────┘               │
│                                                      │                     │
│                                                      ▼                     │
│                                              ┌─────────────┐               │
│                                              │   EXPIRED   │               │
│                                              │             │               │
│                                              │ - Validity  │               │
│                                              │   passed    │               │
│                                              └─────────────┘               │
│                                                                             │
│  Special States:                                                            │
│  ┌─────────────┐      ┌──────────────┐      ┌─────────────┐               │
│  │  CANCELLED  │      │   REVISED    │      │  ARCHIVED   │               │
│  │             │      │              │      │             │               │
│  │ - Trip      │      │ - New version│      │ - Historical│               │
│  │   cancelled │      │ - Superseded │      │ - Backup    │               │
│  └─────────────┘      └──────────────┘      └─────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Version Control

When a bundle is revised:
1. Original bundle remains accessible
2. New bundle gets new reference number
3. Version link established
4. Superseded flag set on old version

---

## Part 10: Implementation Checklist

### 10.1 Core Bundle Types

- [ ] Quote Bundle
  - [ ] Standard Quote template
  - [ ] Comparative Quote template
  - [ ] Group Quote template
  - [ ] Corporate Quote template
  - [ ] Promotional Quote template

- [ ] Pre-Booking Bundle
  - [ ] Hold status display
  - [ ] Expiry countdown
  - [ ] Action required alerts

- [ ] Itinerary Bundle
  - [ ] Day-by-day layout
  - [ ] Summary tables
  - [ ] Important info section
  - [ ] Emergency contacts

- [ ] Voucher Bundle
  - [ ] Hotel voucher
  - [ ] Transfer voucher
  - [ ] Activity voucher
  - [ ] QR code generation

- [ ] Invoice Bundle
  - [ ] Proforma invoice
  - [ ] Tax invoice
  - [ ] GST compliance
  - [ ] Payment details

### 10.2 Supplementary Bundle Types

- [ ] E-Ticket Bundle
- [ ] Visa Documentation Bundle
- [ ] Insurance Certificate Bundle
- [ ] Travel Alert Bundle

### 10.3 Internal Bundle Types

- [ ] Booking Sheet Bundle
- [ ] Commission Sheet Bundle
- [ ] Vendor PO Bundle

---

## Summary

This document provides a complete taxonomy of all bundle types in the Output Panel system:

1. **Core Bundles**: Quote, Pre-Booking, Itinerary, Voucher, Invoice
2. **Supplementary Bundles**: E-Tickets, Visa Docs, Insurance, Travel Alerts
3. **Internal Bundles**: Booking Sheets, Commission Sheets, Vendor POs

Each bundle type has:
- Defined purpose and use case
- Content structure specification
- Template requirements
- Delivery configuration
- Lifecycle management

**Next Document**: OUTPUT_12_TEMPLATE_REFERENCE_COMPLETE.md — Complete template syntax, helpers, and component reference

---

**Document**: OUTPUT_11_BUNDLE_TYPES_COMPLETE.md
**Series**: Output Panel & Bundle Generation Deep Dive
**Status**: ✅ Complete
**Last Updated**: 2026-04-23
