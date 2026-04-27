# Flight Integration 06: Operations

> Flight schedules, status tracking, disruption management, and rebooking automation

---

## Overview

This document details the flight operations subsystem, covering flight schedules, real-time status tracking, disruption handling, automated rebooking, and passenger notifications. The operations system monitors flights throughout their lifecycle, detects disruptions, and orchestrates appropriate responses to minimize passenger impact.

**Key Capabilities:**
- Flight schedule management
- Real-time flight status tracking
- Disruption detection and classification
- Automated rebooking workflows
- Multi-channel passenger notifications
- Duty of care compliance
- Operational analytics and reporting

---

## Table of Contents

1. [Operations Architecture](#operations-architecture)
2. [Flight Schedules](#flight-schedules)
3. [Status Tracking](#status-tracking)
4. [Disruption Management](#disruption-management)
5. [Rebooking Automation](#rebooking-automation)
6. [Notifications](#notifications)
7. [Duty of Care](#duty-of-care)
8. [Analytics and Reporting](#analytics-and-reporting)

---

## Operations Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLIGHT OPERATIONS SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   SCHEDULE   │───▶│   STATUS     │───▶│    EVENT     │                  │
│  │   MANAGER    │    │   TRACKER    │    │    STREAM    │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                          │
│         └───────────────────┼───────────────────┘                          │
│                             │                                              │
│                             ▼                                              │
│                     ┌──────────────┐                                      │
│                     │  DISRUPTION  │                                      │
│                     │  DETECTOR    │                                      │
│                     └──────┬───────┘                                      │
│                            │                                              │
│              ┌─────────────┼─────────────┐                               │
│              │                           │                                │
│         ┌────▼────┐               ┌─────▼─────┐                          │
│         │  IMPACT  │               │REBOOKING  │                          │
│         │ ANALYZER│               │  ENGINE   │                          │
│         └────┬────┘               └─────┬─────┘                          │
│              │                           │                                │
│              └───────────┬───────────────┘                                │
│                          │                                                │
│                          ▼                                                │
│                   ┌──────────────┐                                       │
│                   │  DECISION    │                                       │
│                   │  ENGINE      │                                       │
│                   └──────┬───────┘                                       │
│                          │                                                │
│     ┌────────────────────┼────────────────────┐                          │
│     │                    │                     │                          │
│ ┌───▼────┐         ┌─────▼─────┐        ┌─────▼─────┐                     │
│ │NOTIFY   │         │ REBOOK    │        │ COMPEN-   │                     │
│ │PASSEN-  │         │ PASSENGERS│        │ SATE      │                     │
│ │GERS    │         │           │        │           │                     │
│ └─────────┘         └───────────┘        └───────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Schedule Manager** | Maintains flight schedules and timetables |
| **Status Tracker** | Monitors real-time flight status |
| **Event Stream** | Processes status updates from multiple sources |
| **Disruption Detector** | Identifies and classifies disruptions |
| **Impact Analyzer** | Assesses disruption severity and affected passengers |
| **Rebooking Engine** | Generates rebooking options |
| **Decision Engine** | Determines appropriate response actions |
| **Notification Service** | Sends multi-channel notifications |
| **Compensation Manager** | Handles compensation and duty of care |

---

## Flight Schedules

### Schedule Management

```typescript
interface FlightSchedule {
  // Identification
  id: string;
  flightNumber: string;
  airlineCode: string;

  // Route
  origin: string;
  destination: string;
  route: RouteInfo;

  // Timing
  departureTime: string;        // Scheduled departure time (HH:mm)
  arrivalTime: string;          // Scheduled arrival time (HH:mm)
  durationMinutes: number;
  timezone: string;

  // Frequency
  frequency: FlightFrequency;
  effectivePeriod: DateRange;
  operationalDays: DayOfWeek[];

  // Aircraft
  equipment: AircraftInfo;
  equipmentVariation?: string;  // Equipment changes

  // Operational notes
  notes: ScheduleNote[];

  // Status
  status: ScheduleStatus;
}

interface FlightFrequency {
  type: 'daily' | 'weekly' | 'custom';
  daysOfWeek?: DayOfWeek[];
  dates?: Date[];              // For custom/irregular schedules
  exceptions?: ScheduleException[];
}

interface ScheduleException {
  date: Date;
  type: 'cancelled' | 'added' | 'time_change';
  newDepartureTime?: string;
  newArrivalTime?: string;
  reason?: string;
}

enum ScheduleStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SEASONAL = 'seasonal',
  CHARTER = 'charter',
  DISCONTINUED = 'discontinued'
}

enum DayOfWeek {
  MONDAY = 'monday',
  TUESDAY = 'tuesday',
  WEDNESDAY = 'wednesday',
  THURSDAY = 'thursday',
  FRIDAY = 'friday',
  SATURDAY = 'saturday',
  SUNDAY = 'sunday'
}

class ScheduleManager {
  async getFlightSchedule(
    flightNumber: string,
    airlineCode: string,
    date: Date
  ): Promise<FlightSchedule | null> {
    // Check cache first
    const cached = await this.cache.get(`${airlineCode}${flightNumber}:${date.toISOString()}`);
    if (cached) return cached;

    // Get from database
    const schedule = await this.db.flightSchedule.findFirst({
      where: {
        flightNumber,
        airlineCode,
        effectivePeriod: {
          start: { lte: date },
          end: { gte: date }
        },
        operationalDays: {
          has: this.getDayOfWeek(date)
        }
      }
    });

    if (schedule) {
      await this.cache.set(`${airlineCode}${flightNumber}:${date.toISOString()}`, schedule);
    }

    return schedule;
  }

  async getScheduledFlights(
    route: { origin: string; destination: string },
    date: Date
  ): Promise<FlightSchedule[]> {
    return await this.db.flightSchedule.findMany({
      where: {
        origin: route.origin,
        destination: route.destination,
        effectivePeriod: {
          start: { lte: date },
          end: { gte: date }
        },
        operationalDays: {
          has: this.getDayOfWeek(date)
        },
        status: ScheduleStatus.ACTIVE
      }
    });
  }

  async updateSchedule(
    flightNumber: string,
    airlineCode: string,
    update: ScheduleUpdate
  ): Promise<FlightSchedule> {
    // Get existing schedule
    const existing = await this.db.flightSchedule.findFirst({
      where: { flightNumber, airlineCode }
    });

    if (!existing) {
      throw new Error('Schedule not found');
    }

    // Apply update
    const updated = await this.db.flightSchedule.update({
      where: { id: existing.id },
      data: update
    });

    // Invalidate cache
    await this.invalidateCache(updated);

    return updated;
  }

  private getDayOfWeek(date: Date): DayOfWeek {
    const days = [
      DayOfWeek.SUNDAY,
      DayOfWeek.MONDAY,
      DayOfWeek.TUESDAY,
      DayOfWeek.WEDNESDAY,
      DayOfWeek.THURSDAY,
      DayOfWeek.FRIDAY,
      DayOfWeek.SATURDAY
    ];
    return days[date.getDay()];
  }
}
```

---

## Status Tracking

### Real-Time Status Monitoring

```typescript
interface FlightStatus {
  // Identification
  flightId: string;
  flightNumber: string;
  airlineCode: string;
  departureDate: Date;

  // Current status
  status: FlightStatusValue;
  statusCode: string;

  // Timing
  scheduledDeparture: Date;
  scheduledArrival: Date;
  estimatedDeparture?: Date;
  estimatedArrival?: Date;
  actualDeparture?: Date;
  actualArrival?: Date;

  // Delays
  departureDelayMinutes?: number;
  arrivalDelayMinutes?: number;

  // Positions
  departureGate?: string;
  arrivalGate?: string;
  terminal?: string;
  baggageClaim?: string;

  // Aircraft
  aircraftRegistration?: string;
  aircraftType?: string;

  // Codeshare
  codeshares?: CodeshareStatus[];

  // Timestamp
  lastUpdate: Date;
  source: StatusSource;
}

enum FlightStatusValue {
  SCHEDULED = 'scheduled',
  CHECK_IN_OPEN = 'check_in_open',
  CHECK_IN_CLOSED = 'check_in_closed',
  GATE_CLOSED = 'gate_closed',
  GATE_OPEN = 'gate_open',
  BOARDING = 'boarding',
  DEPARTED = 'departed',
  AIRBORNE = 'airborne',
  EN_ROUTE = 'en_route',
  APPROACHING = 'approaching',
  LANDED = 'landed',
  ARRIVED = 'arrived',
  CANCELLED = 'cancelled',
  DIVERTED = 'diverted',
  DELAYED = 'delayed',
  RETURNING_TO_GATE = 'returning_to_gate'
}

enum StatusSource {
  GDS = 'gds',
  AIRLINE = 'airline',
  AIRPORT = 'airport',
  ADSB = 'adsb',           // Automatic Dependent Surveillance-Broadcast
  MANUAL = 'manual'
}

class StatusTracker {
  private statusProviders: Map<StatusSource, StatusProvider>;
  private eventBus: EventBus;

  async trackFlight(flightId: string): Promise<void> {
    // Subscribe to status updates for this flight
    for (const [source, provider] of this.statusProviders) {
      provider.subscribe(flightId, (update) => this.handleStatusUpdate(update));
    }

    // Fetch initial status
    const status = await this.fetchCurrentStatus(flightId);
    await this.storeStatus(status);
  }

  async handleStatusUpdate(update: StatusUpdate): Promise<void> {
    // Store status
    await this.storeStatus(update);

    // Detect status changes
    const previous = await this.getPreviousStatus(update.flightId);
    if (previous && previous.status !== update.status) {
      await this.handleStatusChange(previous, update);
    }

    // Publish to event bus
    await this.eventBus.publish('flight.status.updated', {
      flightId: update.flightId,
      status: update.status,
      timestamp: update.lastUpdate
    });
  }

  async handleStatusChange(
    previous: FlightStatus,
    current: FlightStatus
  ): Promise<void> {
    // Detect disruptions
    const disruption = await this.detectDisruption(previous, current);

    if (disruption) {
      await this.eventBus.publish('flight.disruption.detected', {
        flightId: current.flightId,
        disruption,
        previousStatus: previous.status,
        currentStatus: current.status
      });
    }

    // Send notifications for significant changes
    const significantChanges = this.getSignificantChanges(previous, current);

    for (const change of significantChanges) {
      await this.notifyStatusChange(current, change);
    }
  }

  private async detectDisruption(
    previous: FlightStatus,
    current: FlightStatus
  ): Promise<Disruption | null> {
    // Check for cancellation
    if (current.status === FlightStatusValue.CANCELLED) {
      return {
        type: DisruptionType.CANCELLATION,
        flightId: current.flightId,
        severity: DisruptionSeverity.HIGH,
        detectedAt: new Date(),
        details: {
          previousStatus: previous.status,
          reason: current.statusReason
        }
      };
    }

    // Check for diversion
    if (current.status === FlightStatusValue.DIVERTED) {
      return {
        type: DisruptionType.DIVERSION,
        flightId: current.flightId,
        severity: DisruptionSeverity.HIGH,
        detectedAt: new Date(),
        details: {
          previousStatus: previous.status,
          diversionAirport: current.diversionAirport
        }
      };
    }

    // Check for significant delay
    const delayMinutes = current.departureDelayMinutes || current.arrivalDelayMinutes || 0;
    if (delayMinutes >= 45) {
      return {
        type: DisruptionType.DELAY,
        flightId: current.flightId,
        severity: delayMinutes >= 120 ? DisruptionSeverity.HIGH : DisruptionSeverity.MEDIUM,
        detectedAt: new Date(),
        details: {
          delayMinutes,
          previousStatus: previous.status
        }
      };
    }

    return null;
  }

  private getSignificantChanges(
    previous: FlightStatus,
    current: FlightStatus
  ): StatusChange[] {
    const changes: StatusChange[] = [];

    // Boarding started
    if (previous.status !== FlightStatusValue.BOARDING &&
        current.status === FlightStatusValue.BOARDING) {
      changes.push({
        type: 'boarding_started',
        message: 'Boarding has started',
        urgency: 'normal'
      });
    }

    // Gate closing soon
    if (current.status === FlightStatusValue.BOARDING &&
        current.estimatedDeparture) {
      const minutesUntilDeparture = (current.estimatedDeparture.getTime() - Date.now()) / (1000 * 60);
      if (minutesUntilDeparture <= 15 && minutesUntilDeparture > 10) {
        changes.push({
          type: 'gate_closing_soon',
          message: 'Gate is closing soon',
          urgency: 'high'
        });
      }
    }

    // Flight delayed
    if ((current.departureDelayMinutes || 0) > 0 &&
        (previous.departureDelayMinutes || 0) === 0) {
      changes.push({
        type: 'flight_delayed',
        message: `Flight delayed by ${current.departureDelayMinutes} minutes`,
        urgency: (current.departureDelayMinutes || 0) > 60 ? 'high' : 'normal'
      });
    }

    return changes;
  }

  private async notifyStatusChange(
    status: FlightStatus,
    change: StatusChange
  ): Promise<void> {
    // Get affected passengers
    const passengers = await this.getAffectedPassengers(status.flightId);

    // Send notifications
    for (const passenger of passengers) {
      await this.notificationService.send({
        recipient: passenger,
        type: change.type,
        message: change.message,
        urgency: change.urgency,
        data: {
          flightNumber: status.flightNumber,
          airline: status.airlineCode,
          status: status.status,
          estimatedDeparture: status.estimatedDeparture,
          estimatedArrival: status.estimatedArrival,
          gate: status.departureGate
        }
      });
    }
  }
}

interface StatusUpdate extends FlightStatus {}

interface StatusChange {
  type: string;
  message: string;
  urgency: 'low' | 'normal' | 'high' | 'urgent';
}
```

---

## Disruption Management

### Disruption Detection

```typescript
interface Disruption {
  id: string;
  type: DisruptionType;
  flightId: string;
  severity: DisruptionSeverity;
  detectedAt: Date;

  // Details
  details: DisruptionDetails;

  // Impact
  affectedPassengers: number;
  affectedBookings: string[];

  // Resolution
  status: DisruptionStatus;
  resolution?: DisruptionResolution;

  // Communication
  communicationStatus: CommunicationStatus;
  lastCommunicationAt?: Date;
}

enum DisruptionType {
  CANCELLATION = 'cancellation',
  DELAY = 'delay',
  DIVERSION = 'diversion',
  AIRCRAFT_CHANGE = 'aircraft_change',
  SCHEDULE_CHANGE = 'schedule_change',
  CREW_ISSUE = 'crew_issue',
  WEATHER = 'weather',
  STRIKE = 'strike',
  SECURITY = 'security'
}

enum DisruptionSeverity {
  LOW = 'low',         // Minor delays, minimal impact
  MEDIUM = 'medium',   // Significant delays, some impact
  HIGH = 'high',       // Major disruptions, high impact
  CRITICAL = 'critical' // Severe disruptions, widespread impact
}

enum DisruptionStatus {
  DETECTED = 'detected',
  ASSESSING = 'assessing',
  RESOLVING = 'resolving',
  RESOLVED = 'resolved',
  CLOSED = 'closed'
}

enum CommunicationStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed'
}

class DisruptionManager {
  async handleDisruption(disruption: Disruption): Promise<void> {
    // 1. Assess impact
    const impact = await this.assessImpact(disruption);

    // 2. Determine response strategy
    const strategy = await this.determineStrategy(disruption, impact);

    // 3. Execute response
    await this.executeResponse(disruption, strategy);

    // 4. Monitor resolution
    await this.monitorResolution(disruption);
  }

  async assessImpact(disruption: Disruption): Promise<DisruptionImpact> {
    // Get affected passengers
    const passengers = await this.getAffectedPassengers(disruption.flightId);

    // Get connecting passengers
    const connectingPassengers = await this.getConnectingPassengers(disruption.flightId);

    // Calculate impact metrics
    const totalAffected = passengers.length + connectingPassengers.length;

    // Check for VIP passengers
    const vipPassengers = passengers.filter(p => p.isVIP);

    // Check for duty of care requirements
    const overnightRequired = await this.requiresOvernightStay(disruption);
    const mealRequired = await this.requiresMeal(disruption);

    return {
      totalPassengers: totalAffected,
      directPassengers: passengers.length,
      connectingPassengers: connectingPassengers.length,
      vipCount: vipPassengers.length,
      overnightRequired,
      mealRequired,
      estimatedCost: await this.estimateImpactCost(disruption, totalAffected)
    };
  }

  async determineStrategy(
    disruption: Disruption,
    impact: DisruptionImpact
  ): Promise<ResponseStrategy> {
    const strategy: ResponseStrategy = {
      actions: [],
      priority: this.calculatePriority(disruption, impact)
    };

    // Always notify passengers
    strategy.actions.push({
      type: 'notify_passengers',
      urgency: disruption.severity === DisruptionSeverity.CRITICAL ? 'urgent' : 'high',
      timing: 'immediate'
    });

    // Based on disruption type
    switch (disruption.type) {
      case DisruptionType.CANCELLATION:
        strategy.actions.push(
          { type: 'rebook_all', timing: 'immediate' },
          { type: 'offer_refund', timing: 'immediate' },
          { type: 'compensation', timing: 'deferred' }
        );
        break;

      case DisruptionType.DELAY:
        if (disruption.details.delayMinutes >= 120) {
          strategy.actions.push(
            { type: 'offer_rebooking', timing: 'optional' },
            { type: 'compensation', timing: 'deferred' }
          );
        }
        if (impact.overnightRequired) {
          strategy.actions.push(
            { type: 'provide_accommodation', timing: 'immediate' },
            { type: 'provide_meals', timing: 'immediate' }
          );
        }
        break;

      case DisruptionType.DIVERSION:
        strategy.actions.push(
          { type: 'arrange_transport', timing: 'immediate' },
          { type: 'rebook_to_destination', timing: 'immediate' }
        );
        break;
    }

    // VIP handling
    if (impact.vipCount > 0) {
      strategy.actions.push({
        type: 'vip_assistance',
        timing: 'immediate'
      });
    }

    return strategy;
  }

  private calculatePriority(
    disruption: Disruption,
    impact: DisruptionImpact
  ): 'low' | 'medium' | 'high' | 'critical' {
    if (disruption.severity === DisruptionSeverity.CRITICAL) return 'critical';
    if (impact.vipCount > 0) return 'high';
    if (impact.overnightRequired) return 'high';
    if (impact.totalPassengers > 100) return 'high';

    switch (disruption.severity) {
      case DisruptionSeverity.HIGH: return 'high';
      case DisruptionSeverity.MEDIUM: return 'medium';
      default: return 'low';
    }
  }
}

interface DisruptionDetails {
  delayMinutes?: number;
  reason?: string;
  diversionAirport?: string;
  newSchedule?: Date;
  [key: string]: any;
}

interface DisruptionImpact {
  totalPassengers: number;
  directPassengers: number;
  connectingPassengers: number;
  vipCount: number;
  overnightRequired: boolean;
  mealRequired: boolean;
  estimatedCost: number;
}

interface ResponseStrategy {
  priority: 'low' | 'medium' | 'high' | 'critical';
  actions: ResponseAction[];
}

interface ResponseAction {
  type: string;
  timing: 'immediate' | 'deferred' | 'optional';
  urgency?: 'low' | 'normal' | 'high' | 'urgent';
}
```

---

## Rebooking Automation

### Rebooking Engine

```typescript
class RebookingEngine {
  async findRebookingOptions(
    originalTicket: Ticket,
    disruption: Disruption
  ): Promise<RebookingOption[]> {
    const options: RebookingOption[] = [];

    // 1. Get same airline options
    const sameAirlineOptions = await this.findSameAirlineOptions(originalTicket, disruption);
    options.push(...sameAirlineOptions);

    // 2. Get partner airline options
    const partnerOptions = await this.findPartnerAirlineOptions(originalTicket, disruption);
    options.push(...partnerOptions);

    // 3. Get alternative options (different airlines)
    const alternativeOptions = await this.findAlternativeOptions(originalTicket, disruption);
    options.push(...alternativeOptions);

    // 4. Score and rank options
    const scored = await this.scoreOptions(originalTicket, options);

    // 5. Sort by score
    scored.sort((a, b) => b.score - a.score);

    // Return top options
    return scored.slice(0, 10).map(s => s.option);
  }

  async autoRebook(
    ticket: Ticket,
    disruption: Disruption,
    preferences?: RebookingPreferences
  ): Promise<RebookingResult> {
    // 1. Find rebooking options
    const options = await this.findRebookingOptions(ticket, disruption);

    if (options.length === 0) {
      return {
        success: false,
        reason: 'No rebooking options available'
      };
    }

    // 2. Select best option
    const selected = await this.selectBestOption(options, ticket, preferences);

    // 3. Create new booking
    const newBooking = await this.createRebookedBooking(selected, ticket);

    // 4. Reissue ticket
    const newTicket = await this.reissueTicket(newBooking, ticket);

    // 5. Cancel old ticket
    await this.cancelOriginalTicket(ticket);

    // 6. Send confirmation
    await this.sendRebookingConfirmation(newTicket, ticket, selected);

    return {
      success: true,
      originalTicket: ticket.ticketNumber,
      newTicket: newTicket.ticketNumber,
      option: selected
    };
  }

  private async findSameAirlineOptions(
    ticket: Ticket,
    disruption: Disruption
  ): Promise<RebookingOption[]> {
    const options: RebookingOption[] = [];

    // Get remaining itinerary
    const remainingSegments = this.getRemainingSegments(ticket);

    for (const segment of remainingSegments) {
      // Search for same airline flights
      const searchResult = await this.searchService.search({
        origin: segment.origin,
        destination: segment.destination,
        departureDate: disruption.details.newSchedule || segment.departureDate,
        passengers: { adults: 1 },
        cabinClass: this.getCabinClassFromBooking(segment.bookingClass),
        providers: [segment.airline],
        directOnly: false
      });

      // Convert to rebooking options
      for (const offer of searchResult.offers) {
        options.push({
          type: 'same_airline',
          airline: segment.airline,
          flights: offer.slices,
          departureTime: offer.slices[0].segments[0].flight.departure.time,
          arrivalTime: offer.slices[offer.slices.length - 1].segments.slice(-1)[0].flight.arrival.time,
          price: 0, // No additional cost for rebooking
          currency: ticket.pricing.currency,
          seatsAvailable: offer.seatsAvailable,
          guarantee: 'guaranteed'
        });
      }
    }

    return options;
  }

  private async findPartnerAirlineOptions(
    ticket: Ticket,
    disruption: Disruption
  ): Promise<RebookingOption[]> {
    // Similar to same airline but includes partner airlines
    const partners = await this.getPartnerAirlines(ticket.flights[0].airline);

    // Implementation similar to findSameAirlineOptions
    return [];
  }

  private async findAlternativeOptions(
    ticket: Ticket,
    disruption: Disruption
  ): Promise<RebookingOption[]> {
    // Search all airlines for alternative routing
    const options: RebookingOption[] = [];

    const remainingSegments = this.getRemainingSegments(ticket);

    for (const segment of remainingSegments) {
      const searchResult = await this.searchService.search({
        origin: segment.origin,
        destination: segment.destination,
        departureDate: disruption.details.newSchedule || segment.departureDate,
        passengers: { adults: 1 },
        cabinClass: this.getCabinClassFromBooking(segment.bookingClass),
        directOnly: false
      });

      for (const offer of searchResult.offers) {
        options.push({
          type: 'alternative',
          airline: offer.slices[0].segments[0].marketingCarrier,
          flights: offer.slices,
          departureTime: offer.slices[0].segments[0].flight.departure.time,
          arrivalTime: offer.slices[offer.slices.length - 1].segments.slice(-1)[0].flight.arrival.time,
          price: 0,
          currency: ticket.pricing.currency,
          seatsAvailable: offer.seatsAvailable,
          guarantee: 'guaranteed'
        });
      }
    }

    return options;
  }

  private async scoreOptions(
    ticket: Ticket,
    options: RebookingOption[]
  ): Promise<ScoredOption[]> {
    const scored: ScoredOption[] = [];

    for (const option of options) {
      let score = 0;

      // Prefer same airline
      if (option.type === 'same_airline') {
        score += 30;
      }

      // Prefer minimal delay
      const originalDeparture = this.getOriginalDepartureTime(ticket);
      const delayMinutes = (option.departureTime.getTime() - originalDeparture.getTime()) / (1000 * 60);

      if (delayMinutes < 60) {
        score += 25;
      } else if (delayMinutes < 120) {
        score += 15;
      } else if (delayMinutes < 240) {
        score += 5;
      }

      // Prefer direct flights
      const stops = option.flights.reduce((sum, slice) => sum + slice.stops, 0);
      if (stops === 0) {
        score += 20;
      } else if (stops === 1) {
        score += 10;
      }

      // Prefer similar cabin class
      const originalCabin = this.getOriginalCabinClass(ticket);
      if (this.isCabinClassSimilar(option, originalCabin)) {
        score += 15;
      }

      // Prefer guaranteed availability
      if (option.guarantee === 'guaranteed') {
        score += 10;
      }

      scored.push({ option, score });
    }

    return scored;
  }

  private getRemainingSegments(ticket: Ticket): TicketedFlight[] {
    // Return segments that haven't been flown yet
    return ticket.flights.filter(f => f.couponStatus !== CouponStatus.FLOWN);
  }

  private getOriginalDepartureTime(ticket: Ticket): Date {
    const nextSegment = ticket.flights.find(f => f.couponStatus !== CouponStatus.FLOWN);
    return nextSegment ? nextSegment.departureDate : ticket.flights[0].departureDate;
  }

  private getOriginalCabinClass(ticket: Ticket): CabinClass {
    // Determine cabin class from first remaining segment
    const nextSegment = ticket.flights.find(f => f.couponStatus !== CouponStatus.FLOWN);
    return this.getCabinClassFromBooking(nextSegment?.class || BookingClass.Y);
  }

  private getCabinClassFromBooking(bookingClass: BookingClass): CabinClass {
    // Map booking class to cabin class
    const first = ['F', 'A', 'R'];
    const business = ['J', 'C', 'D', 'I', 'Z'];
    const premiumEconomy = ['E', 'P'];

    if (first.includes(bookingClass)) return CabinClass.FIRST;
    if (business.includes(bookingClass)) return CabinClass.BUSINESS;
    if (premiumEconomy.includes(bookingClass)) return CabinClass.PREMIUM_ECONOMY;
    return CabinClass.ECONOMY;
  }

  private isCabinClassSimilar(option: RebookingOption, original: CabinClass): boolean {
    // Check if option offers similar or better cabin class
    const optionCabin = option.flights[0].segments[0].cabinClass;
    const hierarchy = [
      CabinClass.ECONOMY,
      CabinClass.PREMIUM_ECONOMY,
      CabinClass.BUSINESS,
      CabinClass.FIRST
    ];

    const originalIndex = hierarchy.indexOf(original);
    const optionIndex = hierarchy.indexOf(optionCabin);

    return optionIndex >= originalIndex;
  }
}

interface RebookingOption {
  type: 'same_airline' | 'partner' | 'alternative';
  airline: string;
  flights: FlightSlice[];
  departureTime: Date;
  arrivalTime: Date;
  price: number;
  currency: string;
  seatsAvailable: number;
  guarantee: 'guaranteed' | 'shopping';
}

interface ScoredOption {
  option: RebookingOption;
  score: number;
}

interface RebookingResult {
  success: boolean;
  originalTicket?: string;
  newTicket?: string;
  option?: RebookingOption;
  reason?: string;
}

interface RebookingPreferences {
  prioritizeTime?: boolean;
  prioritizeDirect?: boolean;
  acceptLowerCabin?: boolean;
  maxDelay?: number; // minutes
}
```

---

## Notifications

### Multi-Channel Notification Service

```typescript
class NotificationService {
  private channels: Map<NotificationChannel, NotificationChannel>;

  async send(request: NotificationRequest): Promise<void> {
    // Determine recipient's preferred channels
    const preferences = await this.getRecipientPreferences(request.recipient);

    // Determine urgency
    const urgency = request.urgency || 'normal';

    // Send to appropriate channels based on urgency and preferences
    const channelsToSend = this.selectChannels(preferences, urgency);

    // Send notifications
    const results = await Promise.allSettled(
      channelsToSend.map(channel =>
        this.channels.get(channel)?.send(request)
      )
    );

    // Log results
    await this.logNotificationResults(request, results);
  }

  async sendBulk(requests: NotificationRequest[]): Promise<void> {
    // Group by channel for efficient sending
    const grouped = new Map<NotificationChannel, NotificationRequest[]>();

    for (const req of requests) {
      const preferences = await this.getRecipientPreferences(req.recipient);
      const channels = this.selectChannels(preferences, req.urgency || 'normal');

      for (const channel of channels) {
        if (!grouped.has(channel)) {
          grouped.set(channel, []);
        }
        grouped.get(channel)!.push(req);
      }
    }

    // Send bulk notifications
    for (const [channel, channelRequests] of grouped) {
      await this.channels.get(channel)?.sendBulk(channelRequests);
    }
  }

  private selectChannels(
    preferences: NotificationPreferences,
    urgency: Urgency
  ): NotificationChannel[] {
    const channels: NotificationChannel[] = [];

    switch (urgency) {
      case 'urgent':
        // Use all available channels for urgent notifications
        channels.push(NotificationChannel.SMS);
        channels.push(NotificationChannel.EMAIL);
        channels.push(NotificationChannel.PUSH);
        if (preferences.phone) {
          channels.push(NotificationChannel.VOICE);
        }
        break;

      case 'high':
        channels.push(NotificationChannel.SMS);
        channels.push(NotificationChannel.EMAIL);
        channels.push(NotificationChannel.PUSH);
        break;

      case 'normal':
        // Use preferred channels
        if (preferences.email) {
          channels.push(NotificationChannel.EMAIL);
        }
        if (preferences.push) {
          channels.push(NotificationChannel.PUSH);
        }
        if (preferences.sms && preferences.smsForNormal) {
          channels.push(NotificationChannel.SMS);
        }
        break;

      case 'low':
        // Email only for low urgency
        if (preferences.email) {
          channels.push(NotificationChannel.EMAIL);
        }
        break;
    }

    return channels;
  }
}

enum NotificationChannel {
  EMAIL = 'email',
  SMS = 'sms',
  PUSH = 'push',
  VOICE = 'voice',
  WHATSAPP = 'whatsapp',
  IN_APP = 'in_app'
}

enum Urgency {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

interface NotificationRequest {
  recipient: PassengerInfo;
  type: string;
  message: string;
  urgency: Urgency;
  data?: Record<string, any>;
  template?: string;
  language?: string;
}

interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  push: boolean;
  voice: boolean;
  whatsapp: boolean;
  smsForNormal: boolean;
  language: string;
}
```

### Notification Templates

```typescript
class NotificationTemplates {
  getFlightDelayedTemplate(
    flight: FlightStatus,
    delayMinutes: number
  ): NotificationTemplate {
    return {
      subject: `Flight ${flight.flightNumber} Delayed`,
      body: `Your flight ${flight.flightNumber} from ${flight.origin} to ${flight.destination} ` +
             `has been delayed by ${delayMinutes} minutes. ` +
             `New departure time: ${this.formatTime(flight.estimatedDeparture)}. ` +
             `We apologize for the inconvenience.`,
      variables: {
        flightNumber: flight.flightNumber,
        origin: flight.origin,
        destination: flight.destination,
        delayMinutes,
        newDepartureTime: this.formatTime(flight.estimatedDeparture),
        gate: flight.departureGate
      }
    };
  }

  getFlightCancelledTemplate(
    flight: FlightStatus
  ): NotificationTemplate {
    return {
      subject: `Flight ${flight.flightNumber} Cancelled`,
      body: `We regret to inform you that flight ${flight.flightNumber} from ${flight.origin} ` +
             `to ${flight.destination} has been cancelled. ` +
             `Our team is working on rebooking options for you. ` +
             `You will receive another notification with your new flight details shortly.`,
      variables: {
        flightNumber: flight.flightNumber,
        origin: flight.origin,
        destination: flight.destination,
        reason: flight.cancellationReason
      }
    };
  }

  getRebookedTemplate(
    originalFlight: FlightStatus,
    newFlight: RebookingOption
  ): NotificationTemplate {
    return {
      subject: `Your Flight Has Been Rebooked`,
      body: `Due to a disruption with your original flight, we have rebooked you on a new flight. ` +
             `\n\nNew Flight Details:\n` +
             `Flight: ${newFlight.airline} ${newFlight.flights[0].segments[0].flightNumber}\n` +
             `Departure: ${this.formatDateTime(newFlight.departureTime)}\n` +
             `Arrival: ${this.formatDateTime(newFlight.arrivalTime)}\n` +
             `\nIf this new flight does not work for you, please contact us.`,
      variables: {
        originalFlightNumber: originalFlight.flightNumber,
        newFlightNumber: newFlight.flights[0].segments[0].flightNumber,
        newAirline: newFlight.airline,
        newDepartureTime: this.formatDateTime(newFlight.departureTime),
        newArrivalTime: this.formatDateTime(newFlight.arrivalTime)
      }
    };
  }
}

interface NotificationTemplate {
  subject: string;
  body: string;
  variables: Record<string, any>;
}
```

---

## Duty of Care

### Duty of Care Management

```typescript
class DutyOfCareManager {
  async assessDutyOfCare(
    disruption: Disruption,
    passengers: PassengerInfo[]
  ): Promise<DutyOfCareRequirements[]> {
    const requirements: DutyOfCareRequirements[] = [];

    for (const passenger of passengers) {
      const requirement: DutyOfCareRequirements = {
        passengerId: passenger.id,
        disruptionId: disruption.id,
        meals: [],
        accommodation: null,
        transportation: null,
        communication: []
      };

      // Assess meal requirements
      const delayHours = (disruption.details.delayMinutes || 0) / 60;
      if (delayHours >= 2) {
        requirement.meals.push({
          type: 'snack',
          providedAt: new Date(),
          cost: 15
        });
      }
      if (delayHours >= 4) {
        requirement.meals.push({
          type: 'meal',
          providedAt: new Date(),
          cost: 25
        });
      }

      // Assess accommodation requirements
      if (await this.requiresOvernightAccommodation(disruption, passenger)) {
        requirement.accommodation = {
          type: 'hotel',
          category: this.getHotelCategory(passenger),
          checkIn: new Date(),
          checkOut: new Date(Date.now() + 24 * 60 * 60 * 1000),
          costEstimate: 150
        };
      }

      // Assess transportation requirements
      if (requirement.accommodation) {
        requirement.transportation = {
          type: 'airport_transfer',
          from: 'airport',
          to: 'hotel',
          costEstimate: 30
        };
      }

      // Assess communication requirements
      if (passenger.language !== 'en' && passenger.language) {
        requirement.communication.push({
          type: 'translation',
          language: passenger.language,
          method: 'phone'
        });
      }

      requirements.push(requirement);
    }

    return requirements;
  }

  async provideDutyOfCare(
    requirements: DutyOfCareRequirements[]
  ): Promise<void> {
    for (const req of requirements) {
      // Arrange meals
      for (const meal of req.meals) {
        await this.arrangeMeal(req.passengerId, meal);
      }

      // Arrange accommodation
      if (req.accommodation) {
        await this.arrangeAccommodation(req.passengerId, req.accommodation);
      }

      // Arrange transportation
      if (req.transportation) {
        await this.arrangeTransportation(req.passengerId, req.transportation);
      }

      // Arrange communication assistance
      for (const comm of req.communication) {
        await this.arrangeCommunication(req.passengerId, comm);
      }
    }
  }

  private async requiresOvernightAccommodation(
    disruption: Disruption,
    passenger: PassengerInfo
  ): Promise<boolean> {
    // Check if delay extends overnight
    if (disruption.type === DisruptionType.CANCELLATION) {
      return true;
    }

    const delayHours = (disruption.details.delayMinutes || 0) / 60;
    const currentHour = new Date().getHours();

    // If delayed past 10 PM and more than 4 hours
    if (currentHour >= 22 && delayHours > 4) {
      return true;
    }

    // If delay results in arrival after midnight
    const originalArrival = await this.getOriginalArrivalTime(disruption.flightId);
    const newArrival = this.calculateNewArrivalTime(originalArrival, disruption.details.delayMinutes || 0);

    if (newArrival.getDate() > originalArrival.getDate()) {
      return true;
    }

    return false;
  }

  private getHotelCategory(passenger: PassengerInfo): 'economy' | 'business' | 'first' {
    // Determine hotel category based on passenger's ticket class
    // VIP passengers get higher category
    if (passenger.isVIP) {
      return 'business';
    }

    return 'economy';
  }
}

interface DutyOfCareRequirements {
  passengerId: string;
  disruptionId: string;
  meals: MealProvision[];
  accommodation: AccommodationProvision | null;
  transportation: TransportationProvision | null;
  communication: CommunicationProvision[];
}

interface MealProvision {
  type: 'snack' | 'meal';
  providedAt: Date;
  cost: number;
}

interface AccommodationProvision {
  type: 'hotel';
  category: 'economy' | 'business' | 'first';
  checkIn: Date;
  checkOut: Date;
  costEstimate: number;
}

interface TransportationProvision {
  type: 'airport_transfer' | 'taxi' | 'rental_car';
  from: string;
  to: string;
  costEstimate: number;
}

interface CommunicationProvision {
  type: 'translation' | 'assistance';
  language: string;
  method: 'phone' | 'in_person';
}
```

---

## Analytics and Reporting

### Operations Analytics

```typescript
class OperationsAnalytics {
  async generateDisruptionReport(
    startDate: Date,
    endDate: Date
  ): Promise<DisruptionReport> {
    // Get disruptions in period
    const disruptions = await this.getDisruptions(startDate, endDate);

    // Calculate metrics
    const totalDisruptions = disruptions.length;
    const byType = this.groupByType(disruptions);
    const bySeverity = this.groupBySeverity(disruptions);
    const byCause = this.groupByCause(disruptions);

    // Calculate impact metrics
    const totalAffectedPassengers = disruptions.reduce(
      (sum, d) => sum + d.affectedPassengers,
      0
    );

    const totalCost = disruptions.reduce(
      (sum, d) => sum + (d.resolution?.cost || 0),
      0
    );

    // Calculate resolution metrics
    const avgResolutionTime = this.calculateAverageResolutionTime(disruptions);
    const resolutionRate = disruptions.filter(d => d.status === DisruptionStatus.RESOLVED).length / totalDisruptions;

    return {
      period: { start: startDate, end: endDate },
      totalDisruptions,
      byType,
      bySeverity,
      byCause,
      totalAffectedPassengers,
      totalCost,
      avgResolutionTime,
      resolutionRate,
      topDisruptedRoutes: await this.getTopDisruptedRoutes(startDate, endDate)
    };
  }

  async generateOnTimePerformanceReport(
    startDate: Date,
    endDate: Date
  ): Promise<OnTimePerformanceReport> {
    // Get flights in period
    const flights = await this.getFlights(startDate, endDate);

    // Calculate OTP metrics
    const onTimeFlights = flights.filter(f =>
      (f.departureDelayMinutes || 0) <= 15
    ).length;

    const otpRate = (onTimeFlights / flights.length) * 100;

    // By airline
    const byAirline = await this.calculateOTPByAirline(startDate, endDate);

    // By route
    const byRoute = await this.calculateOTPByRoute(startDate, endDate);

    // By time of day
    const byTimeOfDay = await this.calculateOTPByTimeOfDay(startDate, endDate);

    return {
      period: { start: startDate, end: endDate },
      totalFlights: flights.length,
      onTimeFlights,
      otpRate,
      byAirline,
      byRoute,
      byTimeOfDay
    };
  }

  async generateRebookingReport(
    startDate: Date,
    endDate: Date
  ): Promise<RebookingReport> {
    const rebookings = await this.getRebookings(startDate, endDate);

    return {
      period: { start: startDate, end: endDate },
      totalRebookings: rebookings.length,
      byReason: this.groupRebookingsByReason(rebookings),
      byAirline: this.groupRebookingsByAirline(rebookings),
      avgTimeToRebook: this.calculateAvgTimeToRebook(rebookings),
      passengerSatisfaction: await this.calculatePassengerSatisfaction(rebookings)
    };
  }
}

interface DisruptionReport {
  period: DateRange;
  totalDisruptions: number;
  byType: Map<DisruptionType, number>;
  bySeverity: Map<DisruptionSeverity, number>;
  byCause: Map<string, number>;
  totalAffectedPassengers: number;
  totalCost: number;
  avgResolutionTime: number;
  resolutionRate: number;
  topDisruptedRoutes: RouteDisruptionInfo[];
}

interface OnTimePerformanceReport {
  period: DateRange;
  totalFlights: number;
  onTimeFlights: number;
  otpRate: number;
  byAirline: Map<string, number>;
  byRoute: Map<string, number>;
  byTimeOfDay: Map<string, number>;
}

interface RebookingReport {
  period: DateRange;
  totalRebookings: number;
  byReason: Map<string, number>;
  byAirline: Map<string, number>;
  avgTimeToRebook: number;
  passengerSatisfaction: number;
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
