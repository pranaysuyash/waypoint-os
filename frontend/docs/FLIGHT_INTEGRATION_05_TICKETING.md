# Flight Integration 05: Ticketing

> Ticket generation, issuance, modifications, refunds, and exchanges

---

## Overview

This document details the flight ticketing subsystem, covering ticket generation, issuance, modifications, refunds, and exchanges. The ticketing system manages the complete lifecycle of flight tickets from initial issuance through final settlement, integrating with GDS providers and airline systems to ensure proper ticket handling.

**Key Capabilities:**
- E-ticket generation and issuance
- PNR management and synchronization
- Ticket modifications and reissues
- Refund processing
- Ticket exchanges
- Ticket status tracking
- Settlement and reconciliation

---

## Table of Contents

1. [Ticketing Architecture](#ticketing-architecture)
2. [Ticket Data Model](#ticket-data-model)
3. [Ticket Issuance](#ticket-issuance)
4. [PNR Management](#pnr-management)
5. [Ticket Modifications](#ticket-modifications)
6. [Refunds and Exchanges](#refunds-and-exchanges)
7. [Settlement and Reconciliation](#settlement-and-reconciliation)

---

## Ticketing Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLIGHT TICKETING SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   BOOKING    │───▶│   TICKET     │───▶│    PNR       │                  │
│  │   CONFIRMED  │    │   SERVICE    │    │   MANAGER    │                  │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘                  │
│                             │                    │                          │
│                             ▼                    │                          │
│                     ┌──────────────┐            │                          │
│                     │  TICKET      │            │                          │
│                     │  GENERATOR   │            │                          │
│                     └──────┬───────┘            │                          │
│                            │                    │                          │
│          ┌─────────────────┼─────────────────┴─────────────────┐          │
│          │                 │                                  │           │
│     ┌────▼────┐      ┌────▼────┐                      ┌──────▼──────┐    │
│     │  GDS     │      │   NDC   │                      │  AIRLINE    │    │
│     │TICKETING │      │ TICKET  │                      │  DIRECT    │    │
│     └────┬────┘      └────┬────┘                      └──────┬──────┘    │
│          │                 │                                  │           │
│          └─────────────────┼──────────────────────────────────┘           │
│                            ▼                                              │
│                     ┌──────────────┐                                     │
│                     │  TICKET      │                                     │
│                     │  VALIDATOR   │                                     │
│                     └──────┬───────┘                                     │
│                            │                                              │
│                            ▼                                              │
│                     ┌──────────────┐                                     │
│                     │  TICKET      │                                     │
│                     │  STORAGE     │                                     │
│                     └──────┬───────┘                                     │
│                            │                                              │
│     ┌──────────────────────┼──────────────────────┐                      │
│     │                      │                      │                       │
│ ┌───▼────┐          ┌─────▼─────┐         ┌─────▼─────┐                 │
│ │MODIFY   │          │  REFUND   │         │  EXCHANGE  │                 │
│ │HANDLER  │          │  HANDLER  │         │  HANDLER   │                 │
│ └─────────┘          └───────────┘         └────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Ticket Service** | Orchestrates ticketing operations |
| **Ticket Generator** | Generates ticket numbers and formats |
| **PNR Manager** | Manages PNR lifecycle and synchronization |
| **GDS/NDC Adapters** | Interface with external ticketing systems |
| **Ticket Validator** | Validates ticket data and format |
| **Ticket Storage** | Persists ticket records |
| **Modify Handler** | Processes ticket modifications |
| **Refund Handler** | Processes refund requests |
| **Exchange Handler** | Processes ticket exchanges |

---

## Ticket Data Model

### Ticket Structure

```typescript
interface Ticket {
  // Identification
  ticketNumber: string;         // Full 13-digit ticket number
  numericCode: string;          // Airline numeric code (3 digits)
  formCode: string;             // Form code (1 digit)
  serialNumber: string;         // Serial number (10 digits)

  // PNR reference
  pnr: PNRReference;

  // Flight information
  flights: TicketedFlight[];

  // Passenger information
  passenger: TicketedPassenger;

  // Pricing
  pricing: TicketPricing;

  // Payment
  payment: TicketPayment;

  // Status
  status: TicketStatus;

  // Dates
  issuedAt: Date;
  validFrom: Date;
  validUntil?: Date;

  // Issuance
  issuingOffice: string;        // IATA code of issuing office
  issuingAgent: string;         // Agent ID
  ticketStock: string;          // Ticket stock control number

  // Restrictions
  endorsements: string;
  restrictions: TicketRestriction[];

  // Metadata
  metadata: TicketMetadata;
}

interface PNRReference {
  recordLocator: string;        // 6-character PNR code
  airlineCode: string;          // Airline code
  creationDate: Date;
}

interface TicketedFlight {
  // Flight identification
  airline: string;
  flightNumber: string;
  class: BookingClass;

  // Route
  origin: string;
  destination: string;

  // Dates
  departureDate: Date;
  departureTime: string;        // HH:mm

  // Status
  status: FlightStatus;

  // Coupon information
  couponNumber: number;
  couponStatus: CouponStatus;
}

interface TicketedPassenger {
  // Name
  lastName: string;
  firstName: string;
  title?: string;

  // Identification
  dateOfBirth?: Date;
  passport?: PassportInfo;
  idDocument?: IDDocumentInfo;

  // Loyalty
  frequentFlyer?: FrequentFlyerInfo;
}

interface TicketPricing {
  // Currency
  currency: string;

  // Fare details
  baseFare: number;
  taxes: number;
  fees: number;
  total: number;

  // Payment breakdown
  fareComponents: FareComponent[];
  taxBreakdown: TaxBreakdown;
  feeBreakdown: FeeBreakdown;

  // Equivalent fare (for currency conversion)
  equivalentFare?: {
    amount: number;
    currency: string;
    rate: number;
  };
}

interface TicketPayment {
  // Payment method
  method: PaymentMethod;
  cardLastFour?: string;

  // Authorization
  authorizationCode?: string;
  transactionId?: string;

  // Amount
  amount: number;
  currency: string;
}

enum TicketStatus {
  OPEN = 'open',                    // Ticket issued and valid
  CHECKED_IN = 'checked_in',        // Passenger checked in
  FLOWN = 'flown',                  // Flight completed
  REFUNDED = 'refunded',            // Ticket refunded
  EXCHANGED = 'exchanged',          // Ticket exchanged
  VOIDED = 'voided',                // Ticket voided
  SUSPENDED = 'suspended',          // Ticket temporarily suspended
  INVALID = 'invalid'               // Ticket invalid
}

enum FlightStatus {
  CONFIRMED = 'confirmed',
  WAITLISTED = 'waitlisted',
  STANDBY = 'standby',
  CANCELLED = 'cancelled',
  FLOWN = 'flown'
}

enum CouponStatus {
  OK = 'ok',                       // Valid for travel
  REROUTED = 'rerouted',           // Flight changed
  FLOWN = 'flown',                 // Segment flown
  REFUNDED = 'refunded',           // Segment refunded
  EXCHANGED = 'exchanged',         // Segment exchanged
  VOIDED = 'voided'                // Segment voided
}
```

### Ticket Number Format

```
Ticket Number Structure (13 digits):
┌─────────┬─────────┬──────────────────┐
│  AIRLINE│   FORM  │    SERIAL        │
│  NUMERIC│   CODE  │    NUMBER        │
│  (3)    │   (1)   │    (9)           │
└─────────┴─────────┴──────────────────┘

Example: 001-1-1234567890
│    │  │
│    │  └─ Serial Number (unique per ticket)
│    └──── Form Code (always 1 for e-tickets)
└───────── Airline Numeric Code (IATA assigned)
```

---

## Ticket Issuance

### Ticket Generation Service

```typescript
class TicketGenerationService {
  private ticketStockManager: TicketStockManager;

  async issueTicket(
    request: TicketIssuanceRequest,
    context: IssuanceContext
  ): Promise<Ticket> {
    // 1. Validate request
    await this.validateRequest(request, context);

    // 2. Get booking details
    const booking = await this.getBooking(request.bookingId);

    // 3. Generate ticket number
    const ticketNumber = await this.generateTicketNumber(booking.airline);

    // 4. Create ticket record
    const ticket = await this.createTicket({
      ticketNumber,
      booking,
      request,
      context
    });

    // 5. Send to GDS/NDC for issuance
    const issued = await this.issueWithProvider(ticket, context);

    // 6. Update ticket status
    ticket.status = TicketStatus.OPEN;
    ticket.issuedAt = new Date();
    ticket.validFrom = new Date();

    // 7. Store ticket
    await this.storeTicket(ticket);

    // 8. Update PNR
    await this.updatePNR(ticket.pnr, ticket);

    // 9. Send confirmation
    await this.sendConfirmation(ticket);

    return ticket;
  }

  async issueMultipleTickets(
    request: MultiTicketIssuanceRequest,
    context: IssuanceContext
  ): Promise<Ticket[]> {
    const tickets: Ticket[] = [];

    // Get booking
    const booking = await this.getBooking(request.bookingId);

    // Issue ticket for each passenger
    for (const passenger of booking.passengers) {
      const ticketRequest: TicketIssuanceRequest = {
        ...request,
        passengerId: passenger.id
      };

      const ticket = await this.issueTicket(ticketRequest, context);
      tickets.push(ticket);
    }

    return tickets;
  }

  private async generateTicketNumber(airlineCode: string): Promise<string> {
    // Get airline numeric code
    const numericCode = await this.getAirlineNumericCode(airlineCode);

    // Get ticket stock
    const stock = await this.ticketStockManager.getNextStock(numericCode);

    // Generate ticket number
    // Format: XXX-F-SSSSSSSSS
    // XXX = Airline numeric code
    // F = Form code (1 for e-ticket)
    // SSSSSSSSS = Serial number (padded with zeros)
    const serialNumber = stock.serialNumber.toString().padStart(9, '0');

    return `${numericCode}1${serialNumber}`;
  }

  private async createTicket(data: CreateTicketData): Promise<Ticket> {
    const { ticketNumber, booking, request, context } = data;

    // Build coupon information for each flight
    const flights: TicketedFlight[] = [];
    let couponNumber = 1;

    for (const slice of booking.slices) {
      for (const segment of slice.segments) {
        flights.push({
          airline: segment.marketingCarrier,
          flightNumber: segment.flight.flightNumber,
          class: segment.bookingClass,
          origin: segment.flight.departure.airport.code,
          destination: segment.flight.arrival.airport.code,
          departureDate: segment.flight.departure.time,
          departureTime: segment.flight.departure.time.toTimeString().slice(0, 5),
          status: FlightStatus.CONFIRMED,
          couponNumber: couponNumber++,
          couponStatus: CouponStatus.OK
        });
      }
    }

    // Get passenger info
    const passenger = booking.passengers.find(p => p.id === request.passengerId);

    return {
      ticketNumber,
      numericCode: ticketNumber.substring(0, 3),
      formCode: ticketNumber[3],
      serialNumber: ticketNumber.substring(4),

      pnr: {
        recordLocator: booking.pnr,
        airlineCode: booking.airline,
        creationDate: booking.createdAt
      },

      flights,

      passenger: {
        lastName: passenger.lastName,
        firstName: passenger.firstName,
        title: passenger.title,
        dateOfBirth: passenger.dateOfBirth,
        passport: passenger.passport,
        idDocument: passenger.idDocument,
        frequentFlyer: passenger.frequentFlyer
      },

      pricing: booking.pricing,

      payment: {
        method: booking.paymentMethod,
        cardLastFour: booking.cardLastFour,
        authorizationCode: booking.authorizationCode,
        transactionId: booking.transactionId,
        amount: booking.pricing.total,
        currency: booking.pricing.currency
      },

      status: TicketStatus.OPEN,
      issuedAt: new Date(),
      validFrom: new Date(),
      validUntil: booking.returnDate
        ? new Date(booking.returnDate.getTime() + 365 * 24 * 60 * 60 * 1000)
        : undefined,

      issuingOffice: context.officeCode,
      issuingAgent: context.agentId,
      ticketStock: '', // Will be filled by ticket stock manager

      endorsements: booking.fareRules.endorsements || '',
      restrictions: booking.fareRules.restrictions || [],

      metadata: {
        bookingId: booking.id,
        offerId: booking.offerId,
        source: booking.source,
        createdAt: new Date()
      }
    };
  }

  private async issueWithProvider(
    ticket: Ticket,
    context: IssuanceContext
  ): Promise<Ticket> {
    // Determine provider (GDS, NDC, or direct)
    const provider = await this.determineProvider(ticket);

    // Issue ticket through provider
    const result = await provider.issueTicket({
      ticketNumber: ticket.ticketNumber,
      pnr: ticket.pnr.recordLocator,
      flights: ticket.flights,
      passenger: ticket.passenger,
      pricing: ticket.pricing
    });

    // Update ticket with provider response
    ticket.ticketStock = result.ticketStock;

    return ticket;
  }
}

interface TicketIssuanceRequest {
  bookingId: string;
  passengerId: string;
  formOfPayment: PaymentMethod;
}

interface MultiTicketIssuanceRequest {
  bookingId: string;
  formOfPayment: PaymentMethod;
}

interface CreateTicketData {
  ticketNumber: string;
  booking: Booking;
  request: TicketIssuanceRequest;
  context: IssuanceContext;
}

interface IssuanceContext {
  officeCode: string;
  agentId: string;
  timestamp: Date;
}

interface TicketMetadata {
  bookingId: string;
  offerId: string;
  source: string;
  createdAt: Date;
}
```

### Ticket Stock Management

```typescript
class TicketStockManager {
  async getNextStock(airlineNumericCode: string): Promise<TicketStock> {
    // Get current stock for this airline
    const stock = await this.getCurrentStock(airlineNumericCode);

    // Check if stock is available
    if (stock.remaining <= stock.threshold) {
      // Request new stock from airline
      await this.requestNewStock(airlineNumericCode);
    }

    // Increment serial number
    const serialNumber = stock.lastSerialNumber + 1;

    // Update stock
    await this.updateStock(airlineNumericCode, {
      lastSerialNumber: serialNumber,
      remaining: stock.remaining - 1
    });

    return {
      airlineNumericCode,
      serialNumber,
      stockNumber: stock.stockNumber
    };
  }

  private async getCurrentStock(airlineNumericCode: string): Promise<TicketStockInfo> {
    // Get from database or cache
    return this.db.ticketStock.findUnique({
      where: { airlineNumericCode }
    });
  }

  private async requestNewStock(airlineNumericCode: string): Promise<void> {
    // Contact airline to request new ticket stock
    // This is typically done through GDS or direct integration
  }
}

interface TicketStock {
  airlineNumericCode: string;
  serialNumber: number;
  stockNumber: string;
}

interface TicketStockInfo {
  airlineNumericCode: string;
  stockNumber: string;
  rangeStart: number;
  rangeEnd: number;
  lastSerialNumber: number;
  remaining: number;
  threshold: number;
}
```

---

## PNR Management

### PNR Service

```typescript
class PNRManager {
  async createPNR(
    booking: Booking,
    context: BookingContext
  ): Promise<PNRReference> {
    // 1. Build PNR data
    const pnrData = this.buildPNRData(booking);

    // 2. Send to GDS/NDC
    const provider = await this.getProvider(booking.airline);
    const pnrResult = await provider.createPNR(pnrData);

    // 3. Store PNR reference
    const pnr: PNRReference = {
      recordLocator: pnrResult.recordLocator,
      airlineCode: booking.airline,
      creationDate: new Date()
    };

    await this.storePNR(pnr, booking.id);

    return pnr;
  }

  async retrievePNR(
    recordLocator: string,
    airlineCode: string
  ): Promise<PNR> {
    // Check cache first
    const cached = await this.getFromCache(recordLocator, airlineCode);
    if (cached) {
      return cached;
    }

    // Retrieve from provider
    const provider = await this.getProvider(airlineCode);
    const pnr = await provider.retrievePNR(recordLocator);

    // Cache the result
    await this.cachePNR(pnr);

    return pnr;
  }

  async updatePNR(
    recordLocator: string,
    updates: PNRUpdate
  ): Promise<PNR> {
    // Get current PNR
    const current = await this.retrievePNR(
      recordLocator,
      updates.airlineCode
    );

    // Apply updates
    const updated = { ...current, ...updates };

    // Send to provider
    const provider = await this.getProvider(updates.airlineCode);
    const result = await provider.updatePNR(recordLocator, updates);

    // Invalidate cache
    await this.invalidateCache(recordLocator, updates.airlineCode);

    return result;
  }

  async splitPNR(
    recordLocator: string,
    airlineCode: string,
    passengers: string[]
  ): Promise<PNRReference> {
    // Retrieve original PNR
    const original = await this.retrievePNR(recordLocator, airlineCode);

    // Create new PNR with selected passengers
    const provider = await this.getProvider(airlineCode);
    const newPNR = await provider.splitPNR(recordLocator, passengers);

    return {
      recordLocator: newPNR.recordLocator,
      airlineCode,
      creationDate: new Date()
    };
  }

  async cancelPNR(
    recordLocator: string,
    airlineCode: string
  ): Promise<void> {
    const provider = await this.getProvider(airlineCode);
    await provider.cancelPNR(recordLocator);

    // Update local records
    await this.markPNRCancelled(recordLocator, airlineCode);
  }

  private buildPNRData(booking: Booking): PNRData {
    return {
      // Passenger names
      passengers: booking.passengers.map(p => ({
        lastName: p.lastName,
        firstName: p.firstName,
        title: p.title,
        type: this.getPassengerType(p)
      })),

      // Flights
      segments: booking.slices.flatMap(slice =>
        slice.segments.map(seg => ({
          airline: seg.marketingCarrier,
          flightNumber: seg.flight.flightNumber,
          class: seg.bookingClass,
          origin: seg.flight.departure.airport.code,
          destination: seg.flight.arrival.airport.code,
          date: seg.flight.departure.time,
          status: 'confirmed'
        }))
      },

      // Contact information
      contact: {
        email: booking.contactEmail,
        phone: booking.contactPhone
      },

      // Ticketing
      ticketing: {
        arrangement: booking.ticketingArrangement,
        deadline: booking.ticketingTimeLimit
      },

      // Pricing
      pricing: {
        fareType: booking.fareType,
        baseFare: booking.pricing.baseFare,
        taxes: booking.pricing.taxes,
        total: booking.pricing.total,
        currency: booking.pricing.currency
      },

      // Remarks
      remarks: booking.remarks || []
    };
  }
}

interface PNR {
  recordLocator: string;
  airlineCode: string;
  creationDate: Date;

  // PNR elements
  passengers: PNRPassenger[];
  segments: PNRSegment[];
  contact: PNRContact;
  ticketing: PNRTicketing;
  pricing: PPRPricing;
  remarks: string[];

  // Status
  status: PNRStatus;
}

interface PNRData {
  passengers: PNRPassenger[];
  segments: PNRSegment[];
  contact: PNRContact;
  ticketing: PNRTicketing;
  pricing: PPRPricing;
  remarks: string[];
}

interface PNRPassenger {
  lastName: string;
  firstName: string;
  title?: string;
  type: 'adult' | 'child' | 'infant';
}

interface PNRSegment {
  airline: string;
  flightNumber: string;
  class: BookingClass;
  origin: string;
  destination: string;
  date: Date;
  status: 'confirmed' | 'waitlisted' | 'standby';
}

interface PNRContact {
  email: string;
  phone: string;
}

interface PNRTicketing {
  arrangement: 'ticketing' | 'non-ticketing';
  deadline: Date;
}

interface PPRPricing {
  fareType: FareType;
  baseFare: number;
  taxes: number;
  total: number;
  currency: string;
}

enum PNRStatus {
  ACTIVE = 'active',
  CANCELLED = 'cancelled',
  FLOWN = 'flown',
  PARTIALLY_FLOWN = 'partially_flown'
}
```

---

## Ticket Modifications

### Modification Service

```typescript
class TicketModificationService {
  async modifyTicket(
    request: TicketModificationRequest,
    context: ModificationContext
  ): Promise<Ticket> {
    // 1. Validate modification request
    await this.validateModification(request, context);

    // 2. Get current ticket
    const ticket = await this.getTicket(request.ticketNumber);

    // 3. Check if modification is allowed
    const canModify = await this.canModify(ticket, request);

    if (!canModify.allowed) {
      throw new ModificationNotAllowedError(canModify.reason);
    }

    // 4. Calculate any fees
    const fees = await this.calculateModificationFees(ticket, request);

    // 5. Process payment if required
    if (fees.total > 0) {
      await this.processPayment(ticket, fees, context);
    }

    // 6. Apply modification
    const modified = await this.applyModification(ticket, request, context);

    // 7. Reissue ticket if necessary
    let reissued: Ticket;
    if (this.requiresReissue(ticket, request)) {
      reissued = await this.reissueTicket(modified, request);
    } else {
      reissued = modified;
    }

    // 8. Update PNR
    await this.updatePNRForModification(reissued, request);

    // 9. Send notification
    await this.sendModificationNotification(reissued, request);

    return reissued;
  }

  async changeFlight(
    ticketNumber: string,
    newFlight: FlightChangeRequest,
    context: ModificationContext
  ): Promise<Ticket> {
    const ticket = await this.getTicket(ticketNumber);

    // 1. Check fare rules for changes
    const fareRules = await this.getFareRules(ticket);
    if (!fareRules.changeable) {
      throw new ModificationNotAllowedError('This fare does not allow changes');
    }

    // 2. Find alternative flights
    const alternatives = await this.findAlternativeFlights(ticket, newFlight);

    // 3. Select best alternative
    const selected = await this.selectFlight(alternatives, newFlight);

    // 4. Calculate price difference
    const priceDiff = await this.calculatePriceDifference(ticket, selected);

    // 5. Process payment or refund
    if (priceDiff > 0) {
      await this.processAdditionalPayment(ticket, priceDiff, context);
    } else if (priceDiff < 0) {
      await this.processRefund(ticket, Math.abs(priceDiff), context);
    }

    // 6. Reissue ticket
    return await this.reissueWithNewFlight(ticket, selected);
  }

  private async canModify(
    ticket: Ticket,
    request: TicketModificationRequest
  ): Promise<{ allowed: boolean; reason?: string }> {
    // Check ticket status
    if (ticket.status !== TicketStatus.OPEN) {
      return { allowed: false, reason: `Ticket is ${ticket.status}` };
    }

    // Check fare rules
    const fareRules = await this.getFareRules(ticket);
    if (!fareRules.changeable) {
      return { allowed: false, reason: 'Fare does not allow changes' };
    }

    // Check time restrictions
    const now = new Date();
    const firstFlight = ticket.flights[0];
    const hoursUntilDeparture = (firstFlight.departureDate.getTime() - now.getTime()) / (1000 * 60 * 60);

    if (hoursUntilDeparture < fareRules.changeDeadlineHours) {
      return { allowed: false, reason: 'Changes not allowed within deadline' };
    }

    // Check if any segments are flown
    const hasFlownSegments = ticket.flights.some(f => f.couponStatus === CouponStatus.FLOWN);
    if (hasFlownSegments) {
      return { allowed: false, reason: 'Cannot modify partially used ticket' };
    }

    return { allowed: true };
  }

  private async calculateModificationFees(
    ticket: Ticket,
    request: TicketModificationRequest
  ): Promise<ModificationFees> {
    const fareRules = await this.getFareRules(ticket);
    const fees: ModificationFees = {
      changeFee: 0,
      fareDifference: 0,
      taxAdjustment: 0,
      total: 0
    };

    // Change fee
    if (fareRules.changeFee) {
      fees.changeFee = fareRules.changeFee;
    }

    // Fare difference (if changing flights)
    if (request.type === 'flight_change') {
      const newFlight = await this.getFlight(request.newFlightId);
      const oldFare = ticket.pricing.baseFare;
      const newFare = newFlight.fare;

      fees.fareDifference = newFare - oldFare;

      // Tax adjustment
      const oldTaxes = ticket.pricing.taxes;
      const newTaxes = await this.calculateTaxes(newFlight);
      fees.taxAdjustment = newTaxes - oldTaxes;
    }

    fees.total = fees.changeFee + fees.fareDifference + fees.taxAdjustment;

    return fees;
  }

  private async reissueTicket(
    ticket: Ticket,
    request: TicketModificationRequest
  ): Promise<Ticket> {
    // Generate new ticket number
    const newTicketNumber = await this.generateReissueTicketNumber(ticket);

    // Create new ticket record
    const reissued: Ticket = {
      ...ticket,
      ticketNumber: newTicketNumber,
      numericCode: newTicketNumber.substring(0, 3),
      formCode: newTicketNumber[3],
      serialNumber: newTicketNumber.substring(4),

      status: TicketStatus.OPEN,

      // Update pricing if changed
      pricing: request.newPricing || ticket.pricing,

      // Update flights if changed
      flights: request.newFlights || ticket.flights,

      // Add reissue notation
      endorsements: `${ticket.endorsements} REISSUED FROM ${ticket.ticketNumber}`,

      metadata: {
        ...ticket.metadata,
        reissuedFrom: ticket.ticketNumber,
        reissuedAt: new Date(),
        reissueReason: request.type
      }
    };

    // Store reissued ticket
    await this.storeTicket(reissued);

    // Mark old ticket as exchanged
    await this.updateTicketStatus(ticket.ticketNumber, TicketStatus.EXCHANGED);

    return reissued;
  }

  private async generateReissueTicketNumber(originalTicket: Ticket): Promise<string> {
    // Reissue tickets typically use same stock but new serial number
    return await this.ticketGenerator.generate(originalTicket.numericCode);
  }

  private requiresReissue(ticket: Ticket, request: TicketModificationRequest): boolean {
    // Flight changes always require reissue
    if (request.type === 'flight_change') {
      return true;
    }

    // Name changes require reissue
    if (request.type === 'name_change') {
      return true;
    }

    // Some fare changes may require reissue
    if (request.type === 'fare_upgrade') {
      return true;
    }

    return false;
  }
}

interface TicketModificationRequest {
  type: 'flight_change' | 'name_change' | 'fare_upgrade' | 'other';
  ticketNumber: string;
  newFlightId?: string;
  newName?: PassengerName;
  newPricing?: TicketPricing;
  newFlights?: TicketedFlight[];
  reason: string;
}

interface ModificationFees {
  changeFee: number;
  fareDifference: number;
  taxAdjustment: number;
  total: number;
}
```

---

## Refunds and Exchanges

### Refund Service

```typescript
class RefundService {
  async processRefund(
    request: RefundRequest,
    context: RefundContext
  ): Promise<RefundResult> {
    // 1. Get ticket
    const ticket = await this.getTicket(request.ticketNumber);

    // 2. Validate refund eligibility
    const eligibility = await this.checkRefundEligibility(ticket, request);

    if (!eligibility.eligible) {
      throw new RefundNotEligibleError(eligibility.reason);
    }

    // 3. Calculate refund amount
    const refund = await this.calculateRefund(ticket, request);

    // 4. Process refund with payment provider
    const refundResult = await this.processRefundPayment(ticket, refund, context);

    // 5. Update ticket status
    await this.updateTicketStatus(ticket.ticketNumber, TicketStatus.REFUNDED);

    // 6. Cancel PNR if full refund
    if (refund.type === 'full') {
      await this.pnrManager.cancelPNR(
        ticket.pnr.recordLocator,
        ticket.pnr.airlineCode
      );
    }

    // 7. Send refund confirmation
    await this.sendRefundConfirmation(ticket, refund);

    return {
      success: true,
      ticketNumber: ticket.ticketNumber,
      refundAmount: refund.amount,
      refundType: refund.type,
      refundId: refundResult.refundId,
      processedAt: new Date()
    };
  }

  async processVoid(
    ticketNumber: string,
    context: RefundContext
  ): Promise<RefundResult> {
    const ticket = await this.getTicket(ticketNumber);

    // Voids can only be done within 24 hours of issuance
    const hoursSinceIssuance = (Date.now() - ticket.issuedAt.getTime()) / (1000 * 60 * 60);

    if (hoursSinceIssuance > 24) {
      throw new RefundNotEligibleError('Void period has expired (24 hours)');
    }

    // Process full refund
    const refundAmount = ticket.pricing.total;

    await this.processRefundPayment(ticket, {
      amount: refundAmount,
      type: 'full',
      currency: ticket.pricing.currency
    }, context);

    // Update ticket status
    await this.updateTicketStatus(ticketNumber, TicketStatus.VOIDED);

    // Cancel PNR
    await this.pnrManager.cancelPNR(
      ticket.pnr.recordLocator,
      ticket.pnr.airlineCode
    );

    return {
      success: true,
      ticketNumber,
      refundAmount,
      refundType: 'full',
      refundId: context.transactionId,
      processedAt: new Date()
    };
  }

  private async checkRefundEligibility(
    ticket: Ticket,
    request: RefundRequest
  ): Promise<RefundEligibility> {
    // Check ticket status
    if (ticket.status === TicketStatus.REFUNDED ||
        ticket.status === TicketStatus.VOIDED) {
      return { eligible: false, reason: 'Ticket already refunded/voided' };
    }

    // Check if any segments are flown
    const hasFlownSegments = ticket.flights.some(f => f.couponStatus === CouponStatus.FLOWN);
    if (hasFlownSegments) {
      return { eligible: false, reason: 'Partially used tickets cannot be refunded' };
    }

    // Check fare rules
    const fareRules = await this.getFareRules(ticket);
    if (!fareRules.refundable) {
      return { eligible: false, reason: 'Fare is non-refundable' };
    }

    // Check time restrictions
    const now = new Date();
    const firstFlight = ticket.flights[0];
    const hoursUntilDeparture = (firstFlight.departureDate.getTime() - now.getTime()) / (1000 * 60 * 60);

    if (hoursUntilDeparture < fareRules.refundDeadlineHours) {
      return { eligible: false, reason: 'Refund deadline has passed' };
    }

    return { eligible: true };
  }

  private async calculateRefund(
    ticket: Ticket,
    request: RefundRequest
  ): Promise<RefundCalculation> {
    const fareRules = await this.getFareRules(ticket);
    const totalPaid = ticket.pricing.total;

    let refundableAmount = totalPaid;
    let type: 'full' | 'partial' = 'full';

    // Apply cancellation fee if applicable
    if (fareRules.cancellationFee) {
      refundableAmount -= fareRules.cancellationFee;
      type = 'partial';
    }

    // Apply percentage-based refund if applicable
    if (fareRules.refundType === 'partial' && fareRules.refundPercent) {
      refundableAmount = totalPaid * (fareRules.refundPercent / 100);
      type = 'partial';
    }

    // Calculate service fee (our fee, not airline fee)
    const serviceFee = this.calculateServiceFee(ticket, refundableAmount);
    refundableAmount -= serviceFee;

    return {
      amount: Math.max(0, refundableAmount),
      currency: ticket.pricing.currency,
      type,
      breakdown: {
        originalAmount: totalPaid,
        cancellationFee: fareRules.cancellationFee || 0,
        serviceFee,
        refundableAmount
      }
    };
  }

  private calculateServiceFee(ticket: Ticket, refundableAmount: number): number {
    // Service fee is typically a percentage or fixed amount
    const percentage = 0.05; // 5%
    const minFee = 25;
    const maxFee = 100;

    const fee = refundableAmount * percentage;
    return Math.max(minFee, Math.min(maxFee, fee));
  }
}

interface RefundRequest {
  ticketNumber: string;
  reason: string;
}

interface RefundCalculation {
  amount: number;
  currency: string;
  type: 'full' | 'partial';
  breakdown: {
    originalAmount: number;
    cancellationFee: number;
    serviceFee: number;
    refundableAmount: number;
  };
}

interface RefundResult {
  success: boolean;
  ticketNumber: string;
  refundAmount: number;
  refundType: 'full' | 'partial';
  refundId: string;
  processedAt: Date;
}

interface RefundEligibility {
  eligible: boolean;
  reason?: string;
}
```

### Exchange Service

```typescript
class ExchangeService {
  async processExchange(
    request: ExchangeRequest,
    context: ExchangeContext
  ): Promise<ExchangeResult> {
    // 1. Get original ticket
    const originalTicket = await this.getTicket(request.ticketNumber);

    // 2. Validate exchange eligibility
    const eligibility = await this.checkExchangeEligibility(originalTicket, request);

    if (!eligibility.eligible) {
      throw new ExchangeNotEligibleError(eligibility.reason);
    }

    // 3. Find new flights
    const newFlights = await this.findNewFlights(originalTicket, request);

    // 4. Calculate price difference
    const priceDiff = await this.calculatePriceDifference(
      originalTicket,
      newFlights,
      request
    );

    // 5. Process additional payment or refund
    if (priceDiff > 0) {
      await this.processAdditionalPayment(originalTicket, priceDiff, context);
    } else if (priceDiff < 0) {
      await this.processRefund(originalTicket, Math.abs(priceDiff), context);
    }

    // 6. Apply exchange fee
    const exchangeFee = await this.calculateExchangeFee(originalTicket, request);
    if (exchangeFee > 0) {
      await this.processExchangeFee(originalTicket, exchangeFee, context);
    }

    // 7. Reissue ticket with new flights
    const newTicket = await this.reissueTicket(originalTicket, {
      type: 'exchange',
      newFlights,
      newPricing: await this.calculateNewPricing(originalTicket, newFlights),
      reason: request.reason
    });

    // 8. Update PNR
    await this.updatePNRForExchange(newTicket, originalTicket);

    // 9. Send exchange confirmation
    await this.sendExchangeConfirmation(newTicket, originalTicket);

    return {
      success: true,
      originalTicketNumber: originalTicket.ticketNumber,
      newTicketNumber: newTicket.ticketNumber,
      priceDifference: priceDiff,
      exchangeFee,
      totalPaid: priceDiff + exchangeFee,
      totalRefunded: priceDiff < 0 ? Math.abs(priceDiff) - exchangeFee : 0
    };
  }

  private async calculateExchangeFee(
    ticket: Ticket,
    request: ExchangeRequest
  ): Promise<number> {
    const fareRules = await this.getFareRules(ticket);

    // Use fare rules exchange fee if specified
    if (fareRules.exchangeFee) {
      return fareRules.exchangeFee;
    }

    // Default exchange fee structure
    const hoursUntilDeparture = this.getHoursUntilDeparture(ticket);

    if (hoursUntilDeparture > 30 * 24) { // More than 30 days
      return 50;
    } else if (hoursUntilDeparture > 7 * 24) { // 7-30 days
      return 100;
    } else { // Less than 7 days
      return 200;
    }
  }

  private getHoursUntilDeparture(ticket: Ticket): number {
    const now = new Date();
    const firstFlight = ticket.flights[0];
    return (firstFlight.departureDate.getTime() - now.getTime()) / (1000 * 60 * 60);
  }
}

interface ExchangeRequest {
  ticketNumber: string;
  newOrigin?: string;
  newDestination?: string;
  newDate?: Date;
  reason: string;
}

interface ExchangeResult {
  success: boolean;
  originalTicketNumber: string;
  newTicketNumber: string;
  priceDifference: number;
  exchangeFee: number;
  totalPaid: number;
  totalRefunded: number;
}
```

---

## Settlement and Reconciliation

### Settlement Service

```typescript
class SettlementService {
  async settleTicket(
    ticket: Ticket,
    context: SettlementContext
  ): Promise<SettlementResult> {
    // 1. Determine settlement type (BSP, ARC, or direct)
    const settlementType = await this.determineSettlementType(ticket);

    // 2. Calculate settlement amounts
    const settlement = await this.calculateSettlement(ticket, settlementType);

    // 3. Create settlement record
    const record = await this.createSettlementRecord({
      ticket,
      settlement,
      type: settlementType,
      context
    });

    // 4. Submit to settlement system
    const submitted = await this.submitSettlement(record, settlementType);

    // 5. Update ticket with settlement info
    await this.updateTicketSettlement(ticket.ticketNumber, submitted);

    return submitted;
  }

  async reconcileTickets(
    request: ReconciliationRequest
  ): Promise<ReconciliationResult> {
    // 1. Get tickets to reconcile
    const tickets = await this.getTicketsForReconciliation(request);

    // 2. Group by settlement type
    const grouped = this.groupBySettlementType(tickets);

    // 3. Reconcile with settlement system
    const results: ReconciliationItem[] = [];

    for (const [type, typeTickets] of grouped.entries()) {
      const reconciliation = await this.reconcileWithSystem(typeTickets, type);
      results.push(...reconciliation.items);
    }

    // 4. Generate report
    return {
      totalTickets: tickets.length,
      reconciled: results.filter(r => r.status === 'matched').length,
      unmatched: results.filter(r => r.status === 'unmatched').length,
      items: results,
      processedAt: new Date()
    };
  }

  private async calculateSettlement(
    ticket: Ticket,
    type: SettlementType
  ): Promise<TicketSettlement> {
    const baseFare = ticket.pricing.baseFare;
    const taxes = ticket.pricing.taxes;
    const total = ticket.pricing.total;

    // Calculate commission (if applicable)
    const commissionRate = await this.getCommissionRate(ticket);
    const commission = baseFare * commissionRate;

    // Calculate net amount due to airline
    const netAmount = total - commission;

    return {
      grossAmount: total,
      baseFare,
      taxes,
      commissionRate,
      commission,
      netAmount,
      currency: ticket.pricing.currency
    };
  }

  private async getCommissionRate(ticket: Ticket): Promise<number> {
    // Get commission rate for airline/route
    // Default is typically 0% (no commission) or 1-5% for some markets
    return 0; // Most airlines pay 0% commission now
  }
}

interface TicketSettlement {
  grossAmount: number;
  baseFare: number;
  taxes: number;
  commissionRate: number;
  commission: number;
  netAmount: number;
  currency: string;
}

interface SettlementResult {
  settlementId: string;
  ticketNumber: string;
  settlementType: SettlementType;
  amount: number;
  currency: string;
  settledAt: Date;
}

interface ReconciliationResult {
  totalTickets: number;
  reconciled: number;
  unmatched: number;
  items: ReconciliationItem[];
  processedAt: Date;
}

interface ReconciliationItem {
  ticketNumber: string;
  status: 'matched' | 'unmatched' | 'discrepancy';
  expectedAmount?: number;
  actualAmount?: number;
  difference?: number;
}

enum SettlementType {
  BSP = 'bsp',           // Billing and Settlement Plan
  ARC = 'arc',           // Airlines Reporting Corporation
  DIRECT = 'direct'      // Direct with airline
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
