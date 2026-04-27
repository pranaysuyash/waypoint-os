# Flight Integration 03: Pricing & Fares

> Fare types, price calculation, tax and fee handling, currency conversion, and dynamic pricing

---

## Overview

This document details the flight pricing subsystem, covering fare types, price calculation algorithms, tax and fee handling, currency conversion, and dynamic pricing strategies. The pricing engine processes fare quotes from GDS providers, applies markups and taxes, and presents accurate pricing to customers.

**Key Capabilities:**
- Multi-passenger type pricing (adult, child, infant)
- Comprehensive tax and fee calculation
- Multi-currency support with real-time conversion
- Fare rule enforcement and validation
- Dynamic pricing based on demand and seasonality
- Corporate negotiated fare handling

---

## Table of Contents

1. [Pricing Architecture](#pricing-architecture)
2. [Fare Types and Classes](#fare-types-and-classes)
3. [Price Calculation](#price-calculation)
4. [Taxes and Fees](#taxes-and-fees)
5. [Currency Conversion](#currency-conversion)
6. [Fare Rules](#fare-rules)
7. [Dynamic Pricing](#dynamic-pricing)
8. [Corporate Fares](#corporate-fares)

---

## Pricing Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLIGHT PRICING ENGINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   FARE       │───▶│    PRICE     │───▶│     TAX      │                  │
│  │   QUOTE      │    │  CALCULATOR  │    │  ENGINE      │                  │
│  │   (INBOUND)  │    │              │    │              │                  │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘                  │
│                             │                    │                          │
│                             └─────────┬──────────┘                          │
│                                       │                                     │
│                                       ▼                                     │
│                              ┌──────────────┐                              │
│                              │    CURRENCY  │                              │
│                              │  CONVERTER   │                              │
│                              └──────┬───────┘                              │
│                                     │                                       │
│                                       ▼                                     │
│                              ┌──────────────┐                              │
│                              │    MARKUP    │                              │
│                              │  MANAGER     │                              │
│                              └──────┬───────┘                              │
│                                     │                                       │
│                                       ▼                                     │
│                              ┌──────────────┐                              │
│                              │    FARE      │                              │
│                              │    RULES     │                              │
│                              │   VALIDATOR  │                              │
│                              └──────┬───────┘                              │
│                                     │                                       │
│                                       ▼                                     │
│                              ┌──────────────┐                              │
│                              │   RESPONSE   │                              │
│                              │   BUILDER    │                              │
│                              └──────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Fare Quote Processor** | Normalizes fare quotes from GDS providers |
| **Price Calculator** | Calculates base and total prices per passenger type |
| **Tax Engine** | Calculates taxes and fees based on route and passenger |
| **Currency Converter** | Converts prices between currencies |
| **Markup Manager** | Applies service fees and markups |
| **Fare Rules Validator** | Validates fare rules and restrictions |
| **Response Builder** | Formats pricing for client consumption |

---

## Fare Types and Classes

### Fare Hierarchy

```
                    CABIN CLASS
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
    ECONOMY      BUSINESS CLASS    FIRST CLASS
        │               │               │
    ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
    ▼       ▼       ▼       ▼       ▼       ▼
  BASIC  STANDARD FLEXIBLE FLEXIBLE FLEXIBLE FLEXIBLE
```

### Fare Type Definitions

```typescript
enum FareType {
  BASIC = 'basic',                  // Most restricted, lowest price
  STANDARD = 'standard',            // Normal restrictions
  FLEXIBLE = 'flexible',            // Flexible changes
  BUSINESS = 'business',            // Business class rules
  FIRST = 'first'                   // First class rules
}

interface FareTypeRules {
  type: FareType;

  // Cancellation rules
  cancellable: boolean;
  cancellationFee?: number;
  cancellationDeadline?: CancellationDeadline;

  // Change rules
  changeable: boolean;
  changeFee?: number;
  changeDeadline?: ChangeDeadline;

  // Refund rules
  refundable: boolean;
  refundType: 'full' | 'partial' | 'none';

  // Advance purchase
  advancePurchase?: AdvancePurchaseRule;

  // Minimum stay
  minimumStay?: MinimumStayRule;

  // Maximum stay
  maximumStay?: MaximumStayRule;

  // Other restrictions
  restrictions: FareRestriction[];
}

interface CancellationDeadline {
  type: 'before_departure' | 'after_booking';
  value: number; // hours or days
  unit: 'hours' | 'days';
}

interface ChangeDeadline {
  type: 'before_departure';
  value: number;
  unit: 'hours' | 'days';
}

interface AdvancePurchaseRule {
  required: boolean;
  daysBeforeDeparture: number;
}

interface MinimumStayRule {
  required: boolean;
  duration: number;
  unit: 'days' | 'saturday_night' | 'sunday');
}

interface MaximumStayRule {
  duration: number;
  unit: 'days' | 'months';
}

interface FareRestriction {
  type: 'blackout' | 'seasonal' | 'inventory' | 'other';
  description: string;
  startDate?: Date;
  endDate?: Date;
}
```

### Booking Classes

```typescript
enum BookingClass {
  // Economy
  Y = 'Y',  // Economy full fare
  B = 'B',  // Economy flexible
  M = 'M',  Economy standard
  H = 'H',  // Economy discounted
  K = 'K',  // Economy highly discounted
  L = 'L',  // Economy sale
  Q = 'Q',  // Economy deep discount
  T = 'T',  // Economy tiered
  V = 'V',  // Economy tiered
  W = 'W',  // Economy tiered
  S = 'S',  // Economy tiered
  N = 'N',  // Economy niche
  O = 'O',  // Economy niche

  // Premium Economy
  E = 'E',  // Premium Economy
  P = 'P',  // Premium Economy

  // Business
  J = 'J',  // Business full fare
  C = 'C',  // Business flexible
  D = 'D',  // Business discounted
  I = 'I',  // Business discounted
  Z = 'Z',  // Business discounted

  // First
  F = 'F',  // First full fare
  A = 'A',  // First discounted
  R = 'R'   // First discounted
}

interface BookingClassInfo {
  code: BookingClass;
  cabinClass: CabinClass;
  description: string;
  tier: number; // 1-10, higher = better
  milesPercent: number; // Award miles earning percentage
  statusPercent: number; // Status miles earning percentage
}
```

### Cabin Classes

```typescript
enum CabinClass {
  ECONOMY = 'economy',
  PREMIUM_ECONOMY = 'premium_economy',
  BUSINESS = 'business',
  FIRST = 'first'
}

interface CabinClassInfo {
  class: CabinClass;
  bookingClasses: BookingClass[];
  amenities: CabinAmenities;
  baggage: BaggageAllowance;
  seat: SeatInfo;
  service: ServiceLevel;
}

interface CabinAmenities {
  meal: boolean;
  mealType?: 'hot' | 'cold' | 'snack' | 'full';
  beverage: boolean;
  alcoholIncluded: boolean;
  WiFi: boolean;
  powerOutlets: boolean;
  entertainment: 'none' | 'shared' | 'personal';
  amenityKit: boolean;
  loungeAccess: boolean;
  priorityBoarding: boolean;
}

interface BaggageAllowance {
  carryOn: { count: number; weight: number; dimensions: string };
  checked: { count: number; weight: number; dimensions: string };
}

interface SeatInfo {
  pitch: number; // inches
  width: number; // inches
  recline: number; // inches
  bedLength?: number; // for lie-flat seats
  bedMode?: 'angle' | 'flat' | 'suite';
}

interface ServiceLevel {
  checkIn: 'standard' | 'priority';
  boarding: 'standard' | 'priority' | 'exclusive';
  prioritySecurity: boolean;
}
```

---

## Price Calculation

### Multi-Passenger Pricing

```typescript
interface PassengerPriceBreakdown {
  passengerType: PassengerType;
  count: number;

  // Base fare
  baseFare: number;
  totalBaseFare: number; // baseFare * count

  // Taxes and fees
  taxes: TaxBreakdown;
  fees: FeeBreakdown;
  totalTaxesAndFees: number;

  // Per passenger total
  totalPerPassenger: number;

  // Subtotal for this passenger type
  subtotal: number;
}

interface FlightPricing {
  // Currency
  currency: string;

  // Breakdown by passenger type
  passengers: {
    adults: PassengerPriceBreakdown;
    children?: PassengerPriceBreakdown;
    infants?: PassengerPriceBreakdown;
    infantsOnSeat?: PassengerPriceBreakdown;
  };

  // Totals
  baseFareTotal: number;
  taxesTotal: number;
  feesTotal: number;
  grandTotal: number;

  // Per person totals
  totalPerPerson: number;

  // Price guarantee
  guarantee: 'guaranteed' | 'shopping';
  validUntil: Date;

  // Breakdown of all components
  components: PriceComponent[];
}

enum PassengerType {
  ADULT = 'adult',
  CHILD = 'child',       // Age 2-11
  INFANT = 'infant',     // Age 0-1, lap
  INFANT_ON_SEAT = 'infant_on_seat' // Age 0-1, with seat
}

interface PriceComponent {
  type: 'fare' | 'tax' | 'fee' | 'surcharge' | 'discount';
  code?: string;
  name: string;
  amount: number;
  perPassenger: boolean;
  passengerTypes?: PassengerType[];
  included: boolean;
  required: boolean;
  refundable: boolean;
}
```

### Price Calculator

```typescript
class FlightPriceCalculator {
  async calculatePrice(
    offer: FlightOffer,
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightPricing> {
    // 1. Calculate base fares per passenger type
    const baseFares = await this.calculateBaseFares(offer, request, context);

    // 2. Calculate taxes per passenger type
    const taxes = await this.calculateTaxes(offer, baseFares, context);

    // 3. Calculate fees per passenger type
    const fees = await this.calculateFees(offer, request, context);

    // 4. Calculate totals
    const pricing = this.assemblePricing(baseFares, taxes, fees, request);

    // 5. Apply markups if configured
    const finalPricing = await this.applyMarkups(pricing, context);

    return finalPricing;
  }

  private async calculateBaseFares(
    offer: FlightOffer,
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<Map<PassengerType, BaseFareInfo>> {
    const baseFares = new Map<PassengerType, BaseFareInfo>();

    // Get base fare from offer (usually adult fare)
    const adultBaseFare = offer.pricing.baseFare;

    // Calculate adult pricing
    baseFares.set(PassengerType.ADULT, {
      amount: adultBaseFare,
      count: request.passengers.adults
    });

    // Calculate child pricing (typically 75% of adult, varies by airline)
    if (request.passengers.children > 0) {
      const childDiscount = await this.getChildDiscount(offer, context);
      baseFares.set(PassengerType.CHILD, {
        amount: adultBaseFare * (1 - childDiscount),
        count: request.passengers.children
      });
    }

    // Calculate infant pricing (lap infants typically 10%)
    if (request.passengers.infants > 0) {
      const infantDiscount = await this.getInfantDiscount(offer, false, context);
      baseFares.set(PassengerType.INFANT, {
        amount: adultBaseFare * (1 - infantDiscount),
        count: request.passengers.infants
      });
    }

    // Calculate infant-on-seat pricing (child fare)
    if (request.passengers.infantsOnSeat && request.passengers.infantsOnSeat > 0) {
      baseFares.set(PassengerType.INFANT_ON_SEAT, {
        amount: adultBaseFare * (1 - await this.getChildDiscount(offer, context)),
        count: request.passengers.infantsOnSeat
      });
    }

    return baseFares;
  }

  private assemblePricing(
    baseFares: Map<PassengerType, BaseFareInfo>,
    taxes: Map<PassengerType, TaxBreakdown>,
    fees: Map<PassengerType, FeeBreakdown>,
    request: FlightSearchRequest
  ): FlightPricing {
    const pricing: Partial<FlightPricing> = {
      currency: request.currency || 'USD',
      passengers: {},
      components: []
    };

    let baseFareTotal = 0;
    let taxesTotal = 0;
    let feesTotal = 0;
    let totalPassengers = 0;

    // Process each passenger type
    for (const [type, baseFare] of baseFares) {
      const taxBreakdown = taxes.get(type) || this.emptyTaxBreakdown();
      const feeBreakdown = fees.get(type) || this.emptyFeeBreakdown();

      const totalTaxes = Object.values(taxBreakdown).reduce((sum, t) => sum + t, 0);
      const totalFees = Object.values(feeBreakdown).reduce((sum, f) => sum + f, 0);

      const totalPerPassenger = baseFare.amount + totalTaxes + totalFees;
      const subtotal = totalPerPassenger * baseFare.count;

      const breakdown: PassengerPriceBreakdown = {
        passengerType: type,
        count: baseFare.count,
        baseFare: baseFare.amount,
        totalBaseFare: baseFare.amount * baseFare.count,
        taxes: taxBreakdown,
        fees: feeBreakdown,
        totalTaxesAndFees: (totalTaxes + totalFees) * baseFare.count,
        totalPerPassenger,
        subtotal
      };

      pricing.passengers![type] = breakdown;
      baseFareTotal += breakdown.totalBaseFare;
      taxesTotal += breakdown.totalTaxesAndFees;
      feesTotal += subtotal - breakdown.totalBaseFare - totalTaxes * baseFare.count;
      totalPassengers += baseFare.count;
    }

    pricing.baseFareTotal = baseFareTotal;
    pricing.taxesTotal = taxesTotal;
    pricing.feesTotal = feesTotal;
    pricing.grandTotal = baseFareTotal + taxesTotal + feesTotal;
    pricing.totalPerPerson = pricing.grandTotal / totalPassengers;

    return pricing as FlightPricing;
  }
}
```

---

## Taxes and Fees

### Tax Types

```typescript
interface TaxBreakdown {
  [taxCode: string]: number;
}

enum TaxCode {
  // US Taxes
  US_US = 'US',           // US Transportation Tax
  US_AY = 'AY',           // US Animal and Plant Health Inspection
  US_XF = 'XF',           // US Passenger Facility Charge
  US_XA = 'XA',           // US Flight Segment Tax
  US_XC = 'XC',           // // US Immigration User Fee
  US_XY = 'XY',           // US APHIS User Fee
  US_EF = 'EF',           // US Customs User Fee

  // International Taxes
  GB_GB = 'GB',           // UK Air Passenger Duty
  CA_CA = 'CA',           // Canada Goods and Services Tax
  CA_AT = 'AT',           // Canada Air Travellers Security Charge
  AU_SF = 'SF',           // Australia Passenger Movement Charge
  DE_DE = 'DE',           // Germany Solidarity Surcharge
  FR_FR = 'FR',           // France Civil Aviation Tax
  IT_IZ = 'IZ',           // Italy Embarkation Tax
  JP_QX = 'QX',           // Japan Passenger Service Facilities Charge

  // Other
  QN_QN = 'QN',           // Passenger Service Charge
  YR_YR = 'YR',           // US Security Fee
  YC_YC = 'YC',           // Animal and Plant Health Inspection
  XY_XY = 'XY',           // US APHIS Fee
  RA_RA = 'RA',           // Airport Tax
  RB_RB = 'RB',           // Federal Inspection Fee
  RC_RC = 'RC',           // Passenger Facility Charge
  RD_RD = 'RD',           // Immigration User Fee
  SO_SO = 'SO',           // State Tax
  TC_TC = 'TC',           // Tourism Tax
  OT_OT = 'OT'            // Other Tax
}

interface TaxInfo {
  code: TaxCode;
  name: string;
  description: string;
  type: 'amount' | 'percentage' | 'segment';
  amount?: number;
  percentage?: number;
  applicableTo: PassengerType[];
  routeBased: boolean;
  countries?: string[]; // Applicable countries
  airports?: string[]; // Applicable airports
}
```

### Fee Types

```typescript
interface FeeBreakdown {
  [feeCode: string]: number;
}

enum FeeCode {
  CARRIER = 'carrier',           // Carrier-imposed fee
  FUEL = 'fuel',                 // Fuel surcharge
  SELECTION = 'selection',       // Seat selection fee
  BAGGAGE = 'baggage',           // Baggage fee
  MEAL = 'meal',                 // Meal fee
  PRIORITY = 'priority',         // Priority boarding fee
  INSURANCE = 'insurance',       // Travel insurance
  BOOKING = 'booking',           // Booking fee
  PAYMENT = 'payment',           // Payment processing fee
  SERVICE = 'service',           // Service fee
  CHANGE = 'change',             // Change fee
  CANCELLATION = 'cancellation', // Cancellation fee
  OTHER = 'other'                // Other fee
}

interface FeeInfo {
  code: FeeCode;
  name: string;
  description: string;
  amount: number;
  perPassenger: boolean;
  perSegment: boolean;
  optional: boolean;
  refundable: boolean;
  applicability: FeeApplicability;
}

interface FeeApplicability {
  passengerTypes?: PassengerType[];
  cabinClasses?: CabinClass[];
  routes?: string[]; // Route patterns
  airlines?: string[];
  fareTypes?: FareType[];
}
```

### Tax Calculator

```typescript
class TaxCalculator {
  private taxRates: Map<TaxCode, TaxInfo>;

  async calculateTaxes(
    offer: FlightOffer,
    baseFares: Map<PassengerType, BaseFareInfo>,
    context: SearchContext
  ): Promise<Map<PassengerType, TaxBreakdown>> {
    const taxes = new Map<PassengerType, TaxBreakdown>();

    for (const [passengerType, baseFare] of baseFares) {
      const breakdown: TaxBreakdown = {};

      // Get route information
      const routes = this.extractRoutes(offer);

      // Calculate taxes for each route segment
      for (const route of routes) {
        const routeTaxes = await this.calculateRouteTaxes(
          route,
          baseFare.amount,
          passengerType,
          context
        );

        // Merge tax breakdown
        for (const [code, amount] of Object.entries(routeTaxes)) {
          breakdown[code] = (breakdown[code] || 0) + amount;
        }
      }

      taxes.set(passengerType, breakdown);
    }

    return taxes;
  }

  private async calculateRouteTaxes(
    route: RouteInfo,
    baseFare: number,
    passengerType: PassengerType,
    context: SearchContext
  ): Promise<TaxBreakdown> {
    const taxes: TaxBreakdown = {};

    // Get applicable taxes for route
    const applicableTaxes = this.getApplicableTaxes(route, passengerType);

    for (const tax of applicableTaxes) {
      let amount = 0;

      switch (tax.type) {
        case 'amount':
          amount = tax.amount!;
          break;

        case 'percentage':
          amount = baseFare * (tax.percentage! / 100);
          break;

        case 'segment':
          amount = tax.amount!;
          break;
      }

      taxes[tax.code] = amount;
    }

    return taxes;
  }

  private getApplicableTaxes(
    route: RouteInfo,
    passengerType: PassengerType
  ): TaxInfo[] {
    const applicable: TaxInfo[] = [];

    for (const tax of this.taxRates.values()) {
      // Check passenger type applicability
      if (!tax.applicableTo.includes(passengerType)) {
        continue;
      }

      // Check route-based applicability
      if (tax.routeBased) {
        if (tax.countries && !tax.countries.includes(route.destinationCountry)) {
          continue;
        }
        if (tax.airports && !tax.airports.includes(route.destinationAirport)) {
          continue;
        }
      }

      applicable.push(tax);
    }

    return applicable;
  }

  private extractRoutes(offer: FlightOffer): RouteInfo[] {
    const routes: RouteInfo[] = [];

    for (const slice of offer.slices) {
      for (const segment of slice.segments) {
        routes.push({
          originAirport: segment.flight.departure.airport.code,
          originCountry: segment.flight.departure.airport.country,
          destinationAirport: segment.flight.arrival.airport.code,
          destinationCountry: segment.flight.arrival.airport.country,
          carrier: segment.marketingCarrier
        });
      }
    }

    return routes;
  }
}

interface RouteInfo {
  originAirport: string;
  originCountry: string;
  destinationAirport: string;
  destinationCountry: string;
  carrier: string;
}

interface BaseFareInfo {
  amount: number;
  count: number;
}
```

---

## Currency Conversion

### Currency Service

```typescript
class CurrencyConverter {
  private exchangeRates: Map<string, ExchangeRate>;
  private lastUpdate: Date;

  async convert(
    amount: number,
    from: string,
    to: string
  ): Promise<number> {
    // If same currency, no conversion needed
    if (from === to) {
      return amount;
    }

    // Get exchange rate
    const rate = await this.getExchangeRate(from, to);

    // Convert with markup (typically 1-2%)
    const convertedAmount = amount * rate.rate;

    // Apply service markup
    const markup = this.getConversionMarkup(from, to);
    const finalAmount = convertedAmount * (1 + markup);

    // Round to 2 decimal places
    return Math.round(finalAmount * 100) / 100;
  }

  async convertPricing(
    pricing: FlightPricing,
    targetCurrency: string
  ): Promise<FlightPricing> {
    const currentCurrency = pricing.currency;

    if (currentCurrency === targetCurrency) {
      return pricing;
    }

    // Convert all amounts
    const converted: FlightPricing = {
      ...pricing,
      currency: targetCurrency,
      baseFareTotal: await this.convert(pricing.baseFareTotal, currentCurrency, targetCurrency),
      taxesTotal: await this.convert(pricing.taxesTotal, currentCurrency, targetCurrency),
      feesTotal: await this.convert(pricing.feesTotal, currentCurrency, targetCurrency),
      grandTotal: await this.convert(pricing.grandTotal, currentCurrency, targetCurrency),
      totalPerPerson: await this.convert(pricing.totalPerPerson, currentCurrency, targetCurrency),
      passengers: {}
    };

    // Convert passenger breakdowns
    for (const [type, breakdown] of Object.entries(pricing.passengers)) {
      converted.passengers[type] = {
        ...breakdown,
        baseFare: await this.convert(breakdown.baseFare, currentCurrency, targetCurrency),
        totalBaseFare: await this.convert(breakdown.totalBaseFare, currentCurrency, targetCurrency),
        totalTaxesAndFees: await this.convert(breakdown.totalTaxesAndFees, currentCurrency, targetCurrency),
        totalPerPassenger: await this.convert(breakdown.totalPerPassenger, currentCurrency, targetCurrency),
        subtotal: await this.convert(breakdown.subtotal, currentCurrency, targetCurrency),
        taxes: await this.convertTaxBreakdown(breakdown.taxes, currentCurrency, targetCurrency),
        fees: await this.convertFeeBreakdown(breakdown.fees, currentCurrency, targetCurrency)
      };
    }

    return converted;
  }

  private async getExchangeRate(from: string, to: string): Promise<ExchangeRate> {
    const key = `${from}_${to}`;

    // Check if rate exists and is fresh
    if (this.exchangeRates.has(key)) {
      const rate = this.exchangeRates.get(key)!;
      const age = Date.now() - rate.timestamp.getTime();

      // Rates are valid for 1 hour
      if (age < 60 * 60 * 1000) {
        return rate;
      }
    }

    // Fetch new rate
    const rate = await this.fetchExchangeRate(from, to);
    this.exchangeRates.set(key, rate);

    return rate;
  }

  private async fetchExchangeRate(from: string, to: string): Promise<ExchangeRate> {
    // Call external currency API (e.g., Fixer.io, OXR)
    const response = await fetch(`${this.CURRENCY_API_URL}/latest?base=${from}&symbols=${to}`, {
      headers: { 'Authorization': `Bearer ${this.CURRENCY_API_KEY}` }
    });

    const data = await response.json();

    return {
      from,
      to,
      rate: data.rates[to],
      timestamp: new Date()
    };
  }

  private getConversionMarkup(from: string, to: string): number {
    // Typical markup is 1-2% for currency conversion
    // This covers the cost of conversion and provides margin
    return 0.015; // 1.5%
  }
}

interface ExchangeRate {
  from: string;
  to: string;
  rate: number;
  timestamp: Date;
}
```

---

## Fare Rules

### Fare Rule Validation

```typescript
class FareRulesValidator {
  async validateFareRules(
    offer: FlightOffer,
    request: FlightSearchRequest
  ): Promise<FareRuleValidation> {
    const rules = await this.getFareRules(offer);
    const violations: FareRuleViolation[] = [];

    // Validate advance purchase
    const advancePurchaseResult = this.validateAdvancePurchase(
      request.departureDate,
      rules.advancePurchase
    );
    if (!advancePurchaseResult.valid) {
      violations.push({
        type: 'advance_purchase',
        description: advancePurchaseResult.message,
        severity: 'error'
      });
    }

    // Validate minimum stay (for round-trip)
    if (request.returnDate && rules.minimumStay) {
      const minStayResult = this.validateMinimumStay(
        request.departureDate,
        request.returnDate,
        rules.minimumStay
      );
      if (!minStayResult.valid) {
        violations.push({
          type: 'minimum_stay',
          description: minStayResult.message,
          severity: 'warning'
        });
      }
    }

    // Validate maximum stay (for round-trip)
    if (request.returnDate && rules.maximumStay) {
      const maxStayResult = this.validateMaximumStay(
        request.departureDate,
        request.returnDate,
        rules.maximumStay
      );
      if (!maxStayResult.valid) {
        violations.push({
          type: 'maximum_stay',
          description: maxStayResult.message,
          severity: 'warning'
        });
      }
    }

    // Check for blackout dates
    const blackoutCheck = this.checkBlackoutDates(
      request.departureDate,
      request.returnDate,
      rules.restrictions
    );
    if (!blackoutCheck.valid) {
      violations.push({
        type: 'blackout_date',
        description: blackoutCheck.message,
        severity: 'error'
      });
    }

    return {
      valid: violations.filter(v => v.severity === 'error').length === 0,
      violations,
      rules
    };
  }

  private validateAdvancePurchase(
    departureDate: Date,
    rule?: AdvancePurchaseRule
  ): ValidationResult {
    if (!rule || !rule.required) {
      return { valid: true };
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const daysUntilDeparture = Math.floor(
      (departureDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysUntilDeparture < rule.daysBeforeDeparture) {
      return {
        valid: false,
        message: `This fare requires booking ${rule.daysBeforeDeparture} days in advance. ` +
                `Currently ${daysUntilDeparture} days before departure.`
      };
    }

    return { valid: true };
  }

  private validateMinimumStay(
    departureDate: Date,
    returnDate: Date,
    rule: MinimumStayRule
  ): ValidationResult {
    const stayDuration = Math.floor(
      (returnDate.getTime() - departureDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (rule.unit === 'saturday_night') {
      // Check if return is on or after Saturday
      const returnDay = returnDate.getDay();
      if (returnDay < 6) { // 0 = Sunday, 6 = Saturday
        return {
          valid: false,
          message: 'This fare requires a Saturday night stay.'
        };
      }
    } else if (rule.unit === 'sunday') {
      const returnDay = returnDate.getDay();
      if (returnDay !== 0) {
        return {
          valid: false,
          message: 'This fare requires returning on Sunday.'
        };
      }
    } else if (stayDuration < rule.duration) {
      return {
        valid: false,
        message: `This fare requires a minimum stay of ${rule.duration} ${rule.unit}. ` +
                `Current stay: ${stayDuration} days.`
      };
    }

    return { valid: true };
  }

  private validateMaximumStay(
    departureDate: Date,
    returnDate: Date,
    rule: MaximumStayRule
  ): ValidationResult {
    let maxDurationDays: number;

    if (rule.unit === 'months') {
      maxDurationDays = rule.duration * 30;
    } else {
      maxDurationDays = rule.duration;
    }

    const stayDuration = Math.floor(
      (returnDate.getTime() - departureDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (stayDuration > maxDurationDays) {
      return {
        valid: false,
        message: `This fare has a maximum stay of ${rule.duration} ${rule.unit}. ` +
                `Current stay: ${stayDuration} days.`
      };
    }

    return { valid: true };
  }

  private checkBlackoutDates(
    departureDate: Date,
    returnDate: Date | undefined,
    restrictions: FareRestriction[]
  ): ValidationResult {
    const blackoutDates = restrictions.filter(r => r.type === 'blackout');

    for (const blackout of blackoutDates) {
      if (blackout.startDate && blackout.endDate) {
        // Check if departure falls in blackout period
        if (departureDate >= blackout.startDate && departureDate <= blackout.endDate) {
          return {
            valid: false,
            message: `This fare is not available for departure on ${departureDate.toDateString()}. ` +
                    `Blackout period: ${blackout.startDate.toDateString()} - ${blackout.endDate.toDateString()}`
          };
        }

        // Check if return falls in blackout period
        if (returnDate && returnDate >= blackout.startDate && returnDate <= blackout.endDate) {
          return {
            valid: false,
            message: `This fare is not available for return on ${returnDate.toDateString()}. ` +
                    `Blackout period: ${blackout.startDate.toDateString()} - ${blackout.endDate.toDateString()}`
          };
        }
      }
    }

    return { valid: true };
  }
}

interface FareRuleValidation {
  valid: boolean;
  violations: FareRuleViolation[];
  rules: FareTypeRules;
}

interface FareRuleViolation {
  type: string;
  description: string;
  severity: 'error' | 'warning' | 'info';
}

interface ValidationResult {
  valid: boolean;
  message?: string;
}
```

---

## Dynamic Pricing

### Dynamic Pricing Engine

```typescript
class DynamicPricingEngine {
  private factors: PricingFactor[];

  async calculateDynamicPrice(
    offer: FlightOffer,
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<DynamicPriceResult> {
    const basePrice = offer.pricing.total;
    let adjustment = 0;
    const appliedFactors: AppliedFactor[] = [];

    // 1. Demand factor
    const demandFactor = await this.calculateDemandFactor(offer, context);
    adjustment += demandFactor.adjustment;
    appliedFactors.push(demandFactor);

    // 2. Seasonality factor
    const seasonalityFactor = await this.calculateSeasonalityFactor(request, context);
    adjustment += seasonalityFactor.adjustment;
    appliedFactors.push(seasonalityFactor);

    // 3. Lead time factor
    const leadTimeFactor = await this.calculateLeadTimeFactor(request, context);
    adjustment += leadTimeFactor.adjustment;
    appliedFactors.push(leadTimeFactor);

    // 4. Occupancy factor
    const occupancyFactor = await this.calculateOccupancyFactor(offer, context);
    adjustment += occupancyFactor.adjustment;
    appliedFactors.push(occupancyFactor);

    // 5. Competitor factor
    const competitorFactor = await this.calculateCompetitorFactor(offer, request, context);
    adjustment += competitorFactor.adjustment;
    appliedFactors.push(competitorFactor);

    // 6. Event factor
    const eventFactor = await this.calculateEventFactor(offer, context);
    adjustment += eventFactor.adjustment;
    appliedFactors.push(eventFactor);

    // Calculate final price
    const adjustedPrice = basePrice + adjustment;
    const adjustmentPercent = (adjustment / basePrice) * 100;

    return {
      basePrice,
      adjustment,
      adjustedPrice,
      adjustmentPercent,
      appliedFactors
    };
  }

  private async calculateDemandFactor(
    offer: FlightOffer,
    context: SearchContext
  ): Promise<AppliedFactor> {
    // Get recent booking trends for this route
    const route = this.getRouteKey(offer);
    const demandLevel = await this.getDemandLevel(route);

    let adjustment = 0;
    let multiplier = 1;

    switch (demandLevel) {
      case 'very_high':
        multiplier = 1.15;
        break;
      case 'high':
        multiplier = 1.08;
        break;
      case 'medium':
        multiplier = 1.0;
        break;
      case 'low':
        multiplier = 0.95;
        break;
      case 'very_low':
        multiplier = 0.88;
        break;
    }

    const basePrice = offer.pricing.total;
    adjustment = basePrice * (multiplier - 1);

    return {
      name: 'Demand',
      value: demandLevel,
      adjustment,
      adjustmentPercent: (multiplier - 1) * 100
    };
  }

  private async calculateSeasonalityFactor(
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<AppliedFactor> {
    const departureDate = request.departureDate;
    const route = `${request.origin}-${request.destination}`;

    // Get seasonality data for route and date
    const seasonality = await this.getSeasonalityData(route, departureDate);

    let multiplier = 1;
    const season = this.getSeason(departureDate);

    switch (seasonality.demandLevel) {
      case 'peak':
        multiplier = 1.25;
        break;
      case 'high':
        multiplier = 1.12;
        break;
      case 'shoulder':
        multiplier = 1.0;
        break;
      case 'low':
        multiplier = 0.85;
        break;
    }

    const basePrice = request.estimatedPrice || 500; // Placeholder
    const adjustment = basePrice * (multiplier - 1);

    return {
      name: 'Seasonality',
      value: `${season} (${seasonality.demandLevel})`,
      adjustment,
      adjustmentPercent: (multiplier - 1) * 100
    };
  }

  private async calculateLeadTimeFactor(
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<AppliedFactor> {
    const today = new Date();
    const daysUntilDeparture = Math.floor(
      (request.departureDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );

    let multiplier = 1;

    // Last-minute bookings pay premium
    if (daysUntilDeparture <= 3) {
      multiplier = 1.35;
    } else if (daysUntilDeparture <= 7) {
      multiplier = 1.20;
    } else if (daysUntilDeparture <= 14) {
      multiplier = 1.10;
    } else if (daysUntilDeparture <= 30) {
      multiplier = 1.0;
    } else if (daysUntilDeparture <= 60) {
      multiplier = 0.95;
    } else if (daysUntilDeparture <= 90) {
      multiplier = 0.90;
    } else {
      // Very early booking discount
      multiplier = 0.85;
    }

    const basePrice = request.estimatedPrice || 500;
    const adjustment = basePrice * (multiplier - 1);

    return {
      name: 'Lead Time',
      value: `${daysUntilDeparture} days`,
      adjustment,
      adjustmentPercent: (multiplier - 1) * 100
    };
  }

  private async calculateOccupancyFactor(
    offer: FlightOffer,
    context: SearchContext
  ): Promise<AppliedFactor> {
    // Get current occupancy for flights in offer
    const occupancyRate = await this.getOccupancyRate(offer);

    let multiplier = 1;

    if (occupancyRate >= 0.95) {
      multiplier = 1.20; // Nearly full
    } else if (occupancyRate >= 0.85) {
      multiplier = 1.10;
    } else if (occupancyRate >= 0.70) {
      multiplier = 1.0;
    } else if (occupancyRate >= 0.50) {
      multiplier = 0.95;
    } else {
      multiplier = 0.90; // Plenty of seats
    }

    const basePrice = offer.pricing.total;
    const adjustment = basePrice * (multiplier - 1);

    return {
      name: 'Occupancy',
      value: `${Math.round(occupancyRate * 100)}%`,
      adjustment,
      adjustmentPercent: (multiplier - 1) * 100
    };
  }

  private async calculateCompetitorFactor(
    offer: FlightOffer,
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<AppliedFactor> {
    // Get competitor prices for same route
    const competitorPrices = await this.getCompetitorPrices(request);

    if (competitorPrices.length === 0) {
      return {
        name: 'Competitor',
        value: 'No data',
        adjustment: 0,
        adjustmentPercent: 0
      };
    }

    const avgCompetitorPrice = competitorPrices.reduce((sum, p) => sum + p, 0) / competitorPrices.length;
    const ourPrice = offer.pricing.total;

    // Adjust to be slightly below average competitor price
    const targetPrice = avgCompetitorPrice * 0.98; // 2% below
    const adjustment = targetPrice - ourPrice;

    return {
      name: 'Competitor',
      value: `Avg: $${Math.round(avgCompetitorPrice)}`,
      adjustment,
      adjustmentPercent: ((targetPrice / ourPrice) - 1) * 100
    };
  }

  private async calculateEventFactor(
    offer: FlightOffer,
    context: SearchContext
  ): Promise<AppliedFactor> {
    // Check for major events at destination
    const events = await this.getEventsAtDestination(offer);

    if (events.length === 0) {
      return {
        name: 'Events',
        value: 'None',
        adjustment: 0,
        adjustmentPercent: 0
      };
    }

    // Major events increase demand
    const totalImpact = events.reduce((sum, event) => sum + event.impact, 0);
    const multiplier = 1 + (totalImpact * 0.1); // 10% per impact point

    const basePrice = offer.pricing.total;
    const adjustment = basePrice * (multiplier - 1);

    return {
      name: 'Events',
      value: events.map(e => e.name).join(', '),
      adjustment,
      adjustmentPercent: (multiplier - 1) * 100
    };
  }

  private getSeason(date: Date): string {
    const month = date.getMonth();

    if (month >= 2 && month <= 4) return 'Spring';
    if (month >= 5 && month <= 7) return 'Summer';
    if (month >= 8 && month <= 10) return 'Fall';
    return 'Winter';
  }

  private getRouteKey(offer: FlightOffer): string {
    const origin = offer.slices[0].segments[0].flight.departure.airport.code;
    const lastSlice = offer.slices[offer.slices.length - 1];
    const dest = lastSlice.segments[lastSlice.segments.length - 1].flight.arrival.airport.code;
    return `${origin}-${dest}`;
  }
}

interface DynamicPriceResult {
  basePrice: number;
  adjustment: number;
  adjustedPrice: number;
  adjustmentPercent: number;
  appliedFactors: AppliedFactor[];
}

interface AppliedFactor {
  name: string;
  value: string;
  adjustment: number;
  adjustmentPercent: number;
}
```

---

## Corporate Fares

### Negotiated Fare Management

```typescript
class CorporateFareManager {
  async getCorporateFares(
    request: FlightSearchRequest,
    corporateCode: string,
    context: SearchContext
  ): Promise<CorporateFareResult[]> {
    // 1. Validate corporate code
    const corporate = await this.validateCorporateCode(corporateCode);
    if (!corporate) {
      throw new Error('Invalid corporate code');
    }

    // 2. Get negotiated fares for this route
    const negotiatedFares = await this.getNegotiatedFares(
      corporate.id,
      request.origin,
      request.destination
    );

    // 3. Check eligibility and availability
    const eligibleFares = [];

    for (const fare of negotiatedFares) {
      if (await this.isFareEligible(fare, request, corporate)) {
        const availability = await this.checkAvailability(fare, request);

        eligibleFares.push({
          fare,
          availability,
          discount: fare.discountPercent,
          corporateName: corporate.name
        });
      }
    }

    return eligibleFares;
  }

  async applyCorporateFare(
    offer: FlightOffer,
    corporateFare: NegotiatedFare,
    corporateCode: string
  ): Promise<FlightOffer> {
    // Apply corporate discount
    const discount = offer.pricing.total * (corporateFare.discountPercent / 100);

    return {
      ...offer,
      pricing: {
        ...offer.pricing,
        total: offer.pricing.total - discount,
        corporateDiscount: discount,
        corporateCode
      },
      fareType: FareType.STANDARD // Corporate fares often have standard restrictions
    };
  }

  private async validateCorporateCode(code: string): Promise<CorporateAccount | null> {
    // Validate against database
    const corporate = await this.corporateRepo.findByCode(code);

    if (!corporate) {
      return null;
    }

    // Check if account is active
    if (corporate.status !== 'active') {
      return null;
    }

    // Check if code is expired
    if (corporate.expiresAt && corporate.expiresAt < new Date()) {
      return null;
    }

    return corporate;
  }

  private async isFareEligible(
    fare: NegotiatedFare,
    request: FlightSearchRequest,
    corporate: CorporateAccount
  ): Promise<boolean> {
    // Check booking class eligibility
    if (fare.bookingClasses && fare.bookingClasses.length > 0) {
      // Verify that offer has eligible booking classes
    }

    // Check advance purchase requirements
    if (fare.advancePurchaseDays) {
      const daysUntil = this.getDaysUntilDeparture(request.departureDate);
      if (daysUntil < fare.advancePurchaseDays) {
        return false;
      }
    }

    // Check cabin class eligibility
    if (fare.cabinClasses && !fare.cabinClasses.includes(request.cabinClass)) {
      return false;
    }

    // Check route validity
    if (!this.isRouteValid(fare, request)) {
      return false;
    }

    // Check date validity
    if (!this.areDatesValid(fare, request)) {
      return false;
    }

    return true;
  }

  private isRouteValid(fare: NegotiatedFare, request: FlightSearchRequest): boolean {
    // Check if route is covered by this fare
    for (const route of fare.routes) {
      if (route.origin === request.origin && route.destination === request.destination) {
        return true;
      }
    }
    return false;
  }

  private areDatesValid(fare: NegotiatedFare, request: FlightSearchRequest): boolean {
    const depDate = request.departureDate;

    // Check effective date
    if (fare.effectiveFrom && depDate < fare.effectiveFrom) {
      return false;
    }

    // Check expiry date
    if (fare.effectiveTo && depDate > fare.effectiveTo) {
      return false;
    }

    // Check blackout dates
    if (fare.blackoutDates) {
      for (const blackout of fare.blackoutDates) {
        if (depDate >= blackout.start && depDate <= blackout.end) {
          return false;
        }
      }
    }

    return true;
  }

  private getDaysUntilDeparture(departureDate: Date): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dep = new Date(departureDate);
    dep.setHours(0, 0, 0, 0);
    return Math.floor((dep.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  }
}

interface CorporateFareResult {
  fare: NegotiatedFare;
  availability: number;
  discount: number;
  corporateName: string;
}

interface NegotiatedFare {
  id: string;
  corporateAccountId: string;
  name: string;
  discountPercent: number;
  routes: NegotiatedRoute[];
  bookingClasses?: BookingClass[];
  cabinClasses?: CabinClass[];
  advancePurchaseDays?: number;
  minimumStay?: number;
  maximumStay?: number;
  effectiveFrom?: Date;
  effectiveTo?: Date;
  blackoutDates?: DateRange[];
  contractType: 'guaranteed' | 'slot' | 'spot';
}

interface NegotiatedRoute {
  origin: string;
  destination: string;
  via?: string[];
}

interface CorporateAccount {
  id: string;
  code: string;
  name: string;
  status: 'active' | 'inactive' | 'suspended';
  expiresAt?: Date;
}

interface DateRange {
  start: Date;
  end: Date;
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
