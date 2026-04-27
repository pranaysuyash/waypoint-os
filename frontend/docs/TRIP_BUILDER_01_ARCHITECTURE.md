# Trip Builder 01: Architecture

> System design, data model, integration patterns, and service orchestration

---

## Overview

This document details the Trip Builder subsystem, which orchestrates multi-component trip planning across flights, accommodations, ground transportation, activities, and services. The system manages the complete trip lifecycle from initial planning through booking and post-trip management.

**Key Capabilities:**
- Multi-component trip planning
- Real-time pricing and availability
- Collaborative trip design
- Automated itinerary validation
- Cross-component booking orchestration
- Trip modification and cancellation

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Domain Model](#domain-model)
3. [Service Integration](#service-integration)
4. [State Management](#state-management)
5. [Workflow Orchestration](#workflow-orchestration)
6. [Database Schema](#database-schema)

---

## System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TRIP BUILDER SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   CLIENT     │───▶│   TRIP       │───▶│   STATE      │                  │
│  │   REQUESTS   │    │   SERVICE    │    │   MANAGER    │                  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘                  │
│                             │                                                  │
│                             ▼                                                  │
│                     ┌──────────────┐                                         │
│                     │  COMPONENT   │                                         │
│                     │  ORCHESTRATOR│                                         │
│                     └──────┬───────┘                                         │
│                            │                                                │
│          ┌─────────────────┼─────────────────┐                             │
│          │                 │                 │                              │
│     ┌────▼────┐      ┌────▼────┐      ┌────▼────┐                          │
│     │ FLIGHT  │      │ HOTEL   │      │  CAR    │                          │
│     │ SERVICE │      │ SERVICE │      │ SERVICE │                          │
│     └────┬────┘      └────┬────┘      └────┬────┘                          │
│          │                 │                 │                               │
│          └─────────────────┼─────────────────┘                               │
│                            │                                                │
│                            ▼                                                │
│                     ┌──────────────┐                                       │
│                     │  PRICING     │                                       │
│                     │  AGGREGATOR  │                                       │
│                     └──────┬───────┘                                       │
│                            │                                                │
│                            ▼                                                │
│                     ┌──────────────┐                                       │
│                     │ VALIDATION   │                                       │
│                     │ ENGINE       │                                       │
│                     └──────┬───────┘                                       │
│                            │                                                │
│     ┌──────────────────────┼──────────────────────┐                        │
│     │                      │                      │                         │
│ ┌───▼────┐          ┌─────▼─────┐          ┌─────▼─────┐                    │
│ │BOOKING │          │COLLABORA- │          │ NOTIFICA- │                    │
│ │ENGINE  │          │TION       │          │ TION     │                    │
│ └────────┘          └───────────┘          └───────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **Trip Service** | Trip CRUD, lifecycle management | Node.js/TypeScript |
| **Component Orchestrator** | Coordinates multi-component operations | TypeScript |
| **Flight Service** | Flight search and booking | Python |
| **Hotel Service** | Accommodation search and booking | Node.js |
| **Car Service** | Car rental integration | Node.js |
| **Pricing Aggregator** | Multi-component pricing | Python |
| **Validation Engine** | Timing and logistics validation | TypeScript |
| **Booking Engine** | Cross-component booking orchestration | Node.js |
| **Collaboration Service** | Shared planning, approvals | Node.js |
| **Notification Service** | Multi-channel notifications | Node.js |

---

## Domain Model

### Core Entities

```typescript
interface Trip {
  // Identification
  id: string;
  name: string;
  slug: string;
  description?: string;
  image?: string;

  // Status
  status: TripStatus;
  phase: TripPhase;

  // Travelers
  primaryTravelerId: string;
  travelers: TripTraveler[];

  // Planning details
  purpose: TripPurpose;
  tripType: TripType;
  flexibility: TripFlexibility;

  // Dates
  startDate: Date;
  endDate: Date;
  duration: number; // days

  // Budget
  budget?: TripBudget;

  // Components
  components: TripComponent[];

  // Timeline
  timeline: TripTimeline;

  // Collaboration
  collaboration?: TripCollaboration;

  // Bookings
  bookings: TripBooking[];

  // Metadata
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;

  // Settings
  settings: TripSettings;

  // Tags and categories
  tags: string[];
  category?: TripCategory;
}

enum TripStatus {
  DRAFT = 'draft',                   // Initial planning
  PLANNING = 'planning',             // Active planning
  PRICING = 'pricing',               // Gathering prices
  PENDING_APPROVAL = 'pending_approval', // Awaiting approval
  APPROVED = 'approved',             // Approved, ready to book
  BOOKING = 'booking',               // Booking in progress
  BOOKED = 'booked',                 // All components booked
  CONFIRMED = 'confirmed',           // Supplier confirmations received
  MODIFIED = 'modified',             // Post-booking modification
  CANCELLED = 'cancelled',           // Trip cancelled
  COMPLETED = 'completed',           // Trip completed
  ARCHIVED = 'archived'              // Trip archived
}

enum TripPhase {
  PLANNING = 'planning',
  BOOKING = 'booking',
  PRE_TRAVEL = 'pre_travel',
  IN_TRAVEL = 'in_travel',
  POST_TRAVEL = 'post_travel'
}

enum TripPurpose {
  LEISURE = 'leisure',
  BUSINESS = 'business',
  BLEISURE = 'bleisure',             // Business + leisure
  FAMILY = 'family',
  ROMANTIC = 'romantic',
  SOLO = 'solo',
  GROUP = 'group',
  ADVENTURE = 'adventure',
  WELLNESS = 'wellness',
  EDUCATION = 'education',
  EVENT = 'event'                    // Wedding, conference, etc.
}

enum TripType {
  ONE_WAY = 'one_way',
  ROUND_TRIP = 'round_trip',
  MULTI_CITY = 'multi_city',
  CIRCULAR = 'circular'              // Returns to origin via different route
}

interface TripFlexibility {
  datesFlexible: boolean;
  dateRange?: DateRange;
  destinationsFlexible: boolean;
  alternativeAirports: boolean;
  budgetFlexible: boolean;
  budgetVariance?: number;           // Percentage
}
```

### Trip Component

```typescript
interface TripComponent {
  // Identification
  id: string;
  tripId: string;

  // Component type
  type: ComponentType;
  category: ComponentCategory;

  // Status
  status: ComponentStatus;
  bookingStatus: BookingStatus;

  // Product details
  productId?: string;
  supplierId: string;
  supplierCode: string;

  // Timing
  startDate: Date;
  endDate: Date;
  duration?: number; // minutes or days

  // Location
  origin?: Location;
  destination: Location;

  // Pricing
  pricing: ComponentPricing;

  // Offer details (if not yet booked)
  offer?: ComponentOffer;

  // Booking details (if booked)
  booking?: ComponentBooking;

  // Dependencies
  dependsOn?: string[]; // Component IDs this depends on
  requiredFor?: string[]; // Component IDs that depend on this

  // Validation
  validation?: ComponentValidation;

  // Metadata
  position: number; // Order in itinerary
  notes?: string;
  tags: string[];
}

enum ComponentType {
  // Transport
  FLIGHT = 'flight',
  TRAIN = 'train',
  BUS = 'bus',
  FERRY = 'ferry',
  CAR_RENTAL = 'car_rental',
  TRANSFER = 'transfer',
  RIDESHARE = 'rideshare',

  // Accommodation
  ACCOMMODATION = 'accommodation',
  CAMPGROUND = 'campground',

  // Activities
  ACTIVITY = 'activity',
  TOUR = 'tour',
  EXPERIENCE = 'experience',
  TICKET = 'ticket', // Museum, attraction tickets

  // Services
  INSURANCE = 'insurance',
  VISA = 'visa',
  VACCINATION = 'vaccination',
  SIM_CARD = 'sim_card',

  // Dining
  RESTAURANT = 'restaurant',
  FOOD_TOUR = 'food_tour'
}

enum ComponentCategory {
  TRANSPORT = 'transport',
  ACCOMMODATION = 'accommodation',
  ACTIVITY = 'activity',
  SERVICE = 'service',
  DINING = 'dining'
}

enum ComponentStatus {
  PROPOSED = 'proposed',             // Suggested but not selected
  SELECTED = 'selected',             // Selected by user
  PRICED = 'priced',                 // Price obtained
  VALIDATED = 'validated',           // Timing/logistics validated
  PENDING_BOOKING = 'pending_booking',
  BOOKING = 'booking',
  BOOKED = 'booked',
  CONFIRMED = 'confirmed',
  CANCELLED = 'cancelled',
  FAILED = 'failed'
}

enum BookingStatus {
  NOT_BOOKED = 'not_booked',
  PENDING = 'pending',
  PROCESSING = 'processing',
  CONFIRMED = 'confirmed',
  MODIFIED = 'modified',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}
```

### Component Pricing

```typescript
interface ComponentPricing {
  // Currency
  currency: string;

  // Breakdown
  basePrice: number;
  taxes: number;
  fees: number;
  total: number;

  // Per person pricing
  perPerson?: number;

  // Price type
  priceType: PriceType;
  guaranteed: boolean;

  // Validity
  validUntil: Date;
  quotedAt: Date;

  // Price history
  previousPrices?: PriceHistoryEntry[];

  // Discounts
  appliedDiscounts?: Discount[];
}

enum PriceType {
  ESTIMATE = 'estimate',             // Approximate price
  QUOTE = 'quote',                   // Firm quote from supplier
  GUARANTEED = 'guaranteed',         // Price is guaranteed
  BOOKED = 'booked'                  // Final booked price
}

interface PriceHistoryEntry {
  price: number;
  timestamp: Date;
  source: string;
}

interface Discount {
  type: 'percentage' | 'fixed' | 'promo';
  amount: number;
  code?: string;
  description: string;
}
```

### Trip Budget

```typescript
interface TripBudget {
  // Currency
  currency: string;

  // Total budget
  total: number;
  remaining: number;

  // Breakdown by category
  allocation: BudgetAllocation;

  // Tracking
  spent: number;
  committed: number;                 // Booked but not yet paid

  // Alerts
  alertThreshold: number;            // Percentage
  alertsEnabled: boolean;

  // Target prices
  targetPrices?: Map<string, number>; // Component type -> target price
}

interface BudgetAllocation {
  transport: number;
  accommodation: number;
  activities: number;
  dining: number;
  services: number;
  contingency: number;               // Buffer for unexpected costs
}
```

### Trip Timeline

```typescript
interface TripTimeline {
  // Events
  events: TimelineEvent[];

  // Day summaries
  days: DaySummary[];

  // Transfers
  transfers: TransferInfo[];
}

interface TimelineEvent {
  id: string;
  componentId: string;

  // Timing
  startDateTime: Date;
  endDateTime: Date;
  duration: number;

  // Location
  location: Location;

  // Type
  type: EventType;
  category: ComponentCategory;

  // Display
  title: string;
  description?: string;
  icon?: string;
  color?: string;

  // Status
  status: EventStatus;

  // Notifications
  reminderOffset?: number;           // Minutes before event
  notified: boolean;
}

enum EventType {
  CHECK_IN_OPEN = 'check_in_open',
  DEPARTURE = 'departure',
  ARRIVAL = 'arrival',
  CHECK_IN = 'check_in',
  CHECK_OUT = 'check_out',
  ACTIVITY_START = 'activity_start',
  ACTIVITY_END = 'activity_end',
  MEAL = 'meal',
  TRANSFER = 'transfer',
  REST = 'rest'
}

enum EventStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  MISSED = 'missed',
  CANCELLED = 'cancelled'
}

interface DaySummary {
  dayNumber: number;
  date: Date;
  location: Location;

  // Components
  components: string[]; // Component IDs

  // Summary
  activities: number;
  meals: number;
  transfers: number;

  // Highlights
  highlights?: string[];

  // Weather
  weatherForecast?: WeatherInfo;
}

interface TransferInfo {
  fromComponentId: string;
  toComponentId: string;

  // Transfer details
  type: TransferType;
  duration: number;
  distance?: number;

  // Pricing
  price?: number;
  currency?: string;

  // Booking
  booked: boolean;
  bookingId?: string;
}

enum TransferType {
  WALKING = 'walking',
  TAXI = 'taxi',
  PRIVATE_TRANSFER = 'private_transfer',
  RENTAL_CAR = 'rental_car',
  PUBLIC_TRANSPORT = 'public_transport',
  INCLUDED = 'included' // Part of another component
}
```

### Trip Collaboration

```typescript
interface TripCollaboration {
  // Members
  members: TripMember[];

  // Sharing
  shareCode: string;
  shareLink: string;
  shareExpiresAt?: Date;

  // Permissions
  permissions: PermissionSettings;

  // Activity
  lastActivity: Date;
  activityLog: ActivityEntry[];

  // Approval workflow
  approvalWorkflow?: ApprovalWorkflow;

  // Comments
  comments: Comment[];

  // Votes
  votes: Vote[];
}

interface TripMember {
  userId: string;
  role: MemberRole;
  permissions: MemberPermission[];

  // Status
  status: MemberStatus;
  joinedAt: Date;
  lastViewedAt?: Date;

  // Preferences
  preferences?: MemberPreferences;
}

enum MemberRole {
  OWNER = 'owner',                   // Full control
  EDITOR = 'editor',                 // Can edit components
  VIEWER = 'viewer',                 // Read-only
  APPROVER = 'approver'              // Can approve/reject
}

enum MemberStatus {
  ACTIVE = 'active',
  PENDING = 'pending',
  DECLINED = 'declined',
  REMOVED = 'removed'
}

interface ApprovalWorkflow {
  enabled: boolean;
  required: boolean;

  // Approvers
  approvers: string[]; // User IDs

  // Status
  status: ApprovalStatus;
  requiredApprovals: number;
  receivedApprovals: number;

  // Responses
  responses: ApprovalResponse[];

  // Deadline
  deadline?: Date;
}

enum ApprovalStatus {
  NOT_REQUIRED = 'not_required',
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled'
}

interface ApprovalResponse {
  userId: string;
  decision: 'approve' | 'reject' | 'abstain';
  comment?: string;
  respondedAt: Date;
}
```

---

## Service Integration

### Component Service Interface

```typescript
interface ComponentService {
  // Search
  search(request: SearchRequest): Promise<ComponentOffer[]>;

  // Pricing
  getPrice(offerId: string): Promise<ComponentPricing>;

  // Availability
  checkAvailability(offerId: string, dates: DateRange): Promise<AvailabilityInfo>;

  // Booking
  book(offer: ComponentOffer, travelers: TravelerInfo[]): Promise<ComponentBooking>;

  // Confirmation
  confirm(bookingId: string): Promise<ConfirmationDetails>;

  // Modification
  modify(bookingId: string, changes: ComponentChanges): Promise<ComponentBooking>;

  // Cancellation
  cancel(bookingId: string, reason: string): Promise<CancellationResult>;
}

interface ComponentOffer {
  id: string;
  type: ComponentType;
  supplier: string;

  // Product details
  product: ComponentProduct;

  // Pricing
  pricing: ComponentPricing;

  // Availability
  availability: AvailabilityInfo;

  // Validity
  validFrom: Date;
  validUntil: Date;
}

interface ComponentProduct {
  id: string;
  name: string;
  description?: string;

  // Location
  location: Location;

  // Images
  images: MediaItem[];

  // Attributes
  attributes: Map<string, any>;

  // Ratings
  rating?: number;
  reviewCount?: number;
}

interface ComponentBooking {
  id: string;
  confirmationCode: string;
  componentId: string;

  // Status
  status: BookingStatus;

  // Details
  travelers: TravelerInfo[];
  dates: DateRange;

  // Pricing
  pricing: ComponentPricing;

  // Supplier
  supplier: SupplierReference;

  // Documents
  documents: Document[];

  // Timeline
  bookedAt: Date;
  confirmedAt?: Date;
  cancelledAt?: Date;
}
```

### Service Registry

```typescript
class ServiceRegistry {
  private services: Map<ComponentType, ComponentService>;

  register(type: ComponentType, service: ComponentService): void {
    this.services.set(type, service);
  }

  get(type: ComponentType): ComponentService | undefined {
    return this.services.get(type);
  }

  async search(
    type: ComponentType,
    request: SearchRequest
  ): Promise<ComponentOffer[]> {
    const service = this.get(type);
    if (!service) {
      throw new Error(`No service registered for type: ${type}`);
    }
    return await service.search(request);
  }

  async book(
    type: ComponentType,
    offer: ComponentOffer,
    travelers: TravelerInfo[]
  ): Promise<ComponentBooking> {
    const service = this.get(type);
    if (!service) {
      throw new Error(`No service registered for type: ${type}`);
    }
    return await service.book(offer, travelers);
  }
}
```

---

## State Management

### Trip State Machine

```typescript
class TripStateMachine {
  private transitions: Map<TripStatus, TripStatus[]>;

  constructor() {
    this.transitions = new Map([
      [TripStatus.DRAFT, [TripStatus.PLANNING, TripStatus.CANCELLED]],
      [TripStatus.PLANNING, [TripStatus.PRICING, TripStatus.PENDING_APPROVAL, TripStatus.CANCELLED]],
      [TripStatus.PRICING, [TripStatus.PLANNING, TripStatus.PENDING_APPROVAL, TripStatus.APPROVED]],
      [TripStatus.PENDING_APPROVAL, [TripStatus.PLANNING, TripStatus.APPROVED, TripStatus.CANCELLED]],
      [TripStatus.APPROVED, [TripStatus.BOOKING, TripStatus.PLANNING]],
      [TripStatus.BOOKING, [TripStatus.BOOKED, TripStatus.APPROVED]],
      [TripStatus.BOOKED, [TripStatus.CONFIRMED, TripStatus.MODIFIED]],
      [TripStatus.CONFIRMED, [TripStatus.MODIFIED, TripStatus.COMPLETED]],
      [TripStatus.MODIFIED, [TripStatus.CONFIRMED, TripStatus.CANCELLED]],
      [TripStatus.COMPLETED, [TripStatus.ARCHIVED]],
      [TripStatus.CANCELLED, [TripStatus.ARCHIVED]]
    ]);
  }

  canTransition(from: TripStatus, to: TripStatus): boolean {
    const allowed = this.transitions.get(from);
    return allowed ? allowed.includes(to) : false;
  }

  transition(trip: Trip, newStatus: TripStatus): Trip {
    if (!this.canTransition(trip.status, newStatus)) {
      throw new InvalidStateTransitionError(trip.status, newStatus);
    }

    return {
      ...trip,
      status: newStatus,
      updatedAt: new Date()
    };
  }
}

class InvalidStateTransitionError extends Error {
  constructor(from: TripStatus, to: TripStatus) {
    super(`Invalid state transition: ${from} -> ${to}`);
    this.name = 'InvalidStateTransitionError';
  }
}
```

### Optimistic Locking

```typescript
interface TripVersion {
  id: string;
  tripId: string;
  version: number;
  data: any;
  createdBy: string;
  createdAt: Date;
}

class VersionManager {
  async saveVersion(trip: Trip, userId: string): Promise<TripVersion> {
    const currentVersion = await this.getCurrentVersion(trip.id);

    const version: TripVersion = {
      id: this.generateId(),
      tripId: trip.id,
      version: (currentVersion?.version || 0) + 1,
      data: trip,
      createdBy: userId,
      createdAt: new Date()
    };

    await this.db.tripVersion.create({ data: version });

    return version;
  }

  async getVersion(tripId: string, version: number): Promise<Trip | null> {
    const versionRecord = await this.db.tripVersion.findFirst({
      where: { tripId, version }
    });

    return versionRecord ? versionRecord.data as Trip : null;
  }

  async getVersionHistory(tripId: string): Promise<TripVersion[]> {
    return await this.db.tripVersion.findMany({
      where: { tripId },
      orderBy: { version: 'desc' },
      take: 50
    });
  }
}
```

---

## Workflow Orchestration

### Trip Planning Workflow

```typescript
class TripPlanningWorkflow {
  async startPlanning(request: CreateTripRequest): Promise<Trip> {
    // 1. Create trip in draft state
    const trip = await this.createTrip(request);

    // 2. Add initial components
    for (const componentRequest of request.components) {
      await this.addComponent(trip.id, componentRequest);
    }

    // 3. Generate initial timeline
    await this.generateTimeline(trip.id);

    // 4. Calculate initial pricing
    await this.updatePricing(trip.id);

    // 5. Validate itinerary
    const validation = await this.validateTrip(trip.id);

    // 6. Transition to planning state
    return await this.transitionTo(trip.id, TripStatus.PLANNING);
  }

  async addComponent(
    tripId: string,
    request: AddComponentRequest
  ): Promise<TripComponent> {
    // 1. Search for component
    const offers = await this.serviceRegistry.search(request.type, request.search);

    // 2. Select best offer
    const selected = await this.selectOffer(offers, request.preferences);

    // 3. Create component
    const component: TripComponent = {
      id: this.generateId(),
      tripId,
      type: request.type,
      category: this.getCategory(request.type),
      status: ComponentStatus.SELECTED,
      bookingStatus: BookingStatus.NOT_BOOKED,
      productId: selected.product.id,
      supplierId: selected.supplier,
      supplierCode: selected.supplierCode,
      startDate: request.startDate,
      endDate: request.endDate,
      destination: selected.product.location,
      pricing: selected.pricing,
      offer: selected,
      position: await this.getNextPosition(tripId),
      tags: []
    };

    // 4. Validate component
    const validation = await this.validateComponent(component, tripId);

    // 5. Save component
    await this.db.tripComponent.create({ data: component });

    // 6. Update timeline
    await this.updateTimeline(tripId);

    // 7. Update pricing
    await this.updatePricing(tripId);

    return component;
  }

  async removeComponent(tripId: string, componentId: string): Promise<void> {
    // 1. Check if component can be removed
    const component = await this.getComponent(componentId);

    if (component.bookingStatus === BookingStatus.CONFIRMED) {
      throw new Error('Cannot remove confirmed component');
    }

    // 2. Check for dependencies
    const dependents = await this.getDependentComponents(componentId);
    if (dependents.length > 0) {
      throw new Error(`Cannot remove component with ${dependents.length} dependencies`);
    }

    // 3. Remove component
    await this.db.tripComponent.delete({
      where: { id: componentId }
    });

    // 4. Update timeline
    await this.updateTimeline(tripId);

    // 5. Update pricing
    await this.updatePricing(tripId);
  }

  async updatePricing(tripId: string): Promise<TripPricing> {
    // 1. Get all components
    const components = await this.getComponents(tripId);

    // 2. Get fresh pricing for each component
    const priced = await Promise.all(
      components.map(async (component) => {
        if (component.offer) {
          const freshPrice = await this.serviceRegistry
            .get(component.type)
            ?.getPrice(component.offer.id);

          return {
            ...component,
            pricing: freshPrice || component.pricing
          };
        }
        return component;
      })
    );

    // 3. Calculate totals
    const pricing = this.calculateTotalPricing(priced);

    // 4. Update trip pricing
    await this.db.trip.update({
      where: { id: tripId },
      data: { pricing }
    });

    return pricing;
  }

  private calculateTotalPricing(components: TripComponent[]): TripPricing {
    let total = 0;
    const breakdown = new Map<ComponentCategory, number>();

    for (const component of components) {
      total += component.pricing.total;

      const category = component.category;
      breakdown.set(category, (breakdown.get(category) || 0) + component.pricing.total);
    }

    return {
      total,
      currency: components[0]?.pricing.currency || 'USD',
      breakdown
    };
  }
}
```

### Booking Workflow

```typescript
class TripBookingWorkflow {
  async startBooking(tripId: string): Promise<BookingResult> {
    // 1. Validate trip is ready for booking
    const trip = await this.getTrip(tripId);

    if (trip.status !== TripStatus.APPROVED) {
      throw new Error('Trip must be approved before booking');
    }

    // 2. Transition to booking state
    await this.transitionTo(tripId, TripStatus.BOOKING);

    // 3. Sort components by dependencies
    const components = await this.getComponentsSorted(tripId);

    // 4. Book components in order
    const bookings: ComponentBooking[] = [];
    const failures: BookingFailure[] = [];

    for (const component of components) {
      try {
        const booking = await this.bookComponent(component, trip);
        bookings.push(booking);
      } catch (error) {
        failures.push({
          componentId: component.id,
          error: error.message
        });

        // Rollback previous bookings
        await this.rollbackBookings(bookings);
        throw new BookingFailedError('Booking failed, rolled back', failures);
      }
    }

    // 5. Transition to booked state
    await this.transitionTo(tripId, TripStatus.BOOKED);

    return {
      success: true,
      tripId,
      bookings,
      confirmationCodes: bookings.map(b => b.confirmationCode)
    };
  }

  private async bookComponent(
    component: TripComponent,
    trip: Trip
  ): Promise<ComponentBooking> {
    const service = this.serviceRegistry.get(component.type);

    if (!service) {
      throw new Error(`No service for component type: ${component.type}`);
    }

    // Get travelers for this component
    const travelers = await this.getTravelersForComponent(component, trip);

    // Book the component
    const booking = await service.book(component.offer!, travelers);

    // Update component with booking info
    await this.db.tripComponent.update({
      where: { id: component.id },
      data: {
        bookingStatus: BookingStatus.CONFIRMED,
        booking,
        status: ComponentStatus.BOOKED
      }
    });

    return booking;
  }

  private async rollbackBookings(bookings: ComponentBooking[]): Promise<void> {
    for (const booking of bookings) {
      try {
        const service = this.serviceRegistry.get(
          this.getComponentTypeFromBooking(booking)
        );

        await service?.cancel(booking.id, 'Rollback due to failed booking');
      } catch (error) {
        console.error(`Failed to cancel booking ${booking.id}:`, error);
      }
    }
  }
}
```

---

## Database Schema

### Trip Table

```sql
CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,

  status VARCHAR(50) NOT NULL DEFAULT 'draft',
  phase VARCHAR(50) NOT NULL DEFAULT 'planning',

  primary_traveler_id UUID NOT NULL REFERENCES users(id),
  purpose VARCHAR(50),
  trip_type VARCHAR(50),

  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  end_date TIMESTAMP WITH TIME ZONE NOT NULL,
  duration INTEGER NOT NULL,

  budget_total DECIMAL(10, 2),
  budget_currency CHAR(3) DEFAULT 'USD',
  budget_remaining DECIMAL(10, 2),

  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE,

  settings JSONB,
  tags TEXT[]
);

CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_user ON trips(primary_traveler_id);
CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
```

### Trip Components Table

```sql
CREATE TABLE trip_components (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,

  type VARCHAR(50) NOT NULL,
  category VARCHAR(50) NOT NULL,

  status VARCHAR(50) NOT NULL DEFAULT 'proposed',
  booking_status VARCHAR(50) NOT NULL DEFAULT 'not_booked',

  product_id VARCHAR(255),
  supplier_id VARCHAR(255) NOT NULL,
  supplier_code VARCHAR(255) NOT NULL,

  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  end_date TIMESTAMP WITH TIME ZONE NOT NULL,

  destination_latitude DECIMAL(9, 6),
  destination_longitude DECIMAL(9, 6),
  destination_name VARCHAR(255),

  pricing_total DECIMAL(10, 2),
  pricing_currency CHAR(3),
  pricing_data JSONB,

  offer_data JSONB,
  booking_data JSONB,

  position INTEGER NOT NULL,
  notes TEXT,
  tags TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trip_components_trip ON trip_components(trip_id);
CREATE INDEX idx_trip_components_type ON trip_components(type);
CREATE INDEX idx_trip_components_dates ON trip_components(start_date, end_date);
```

### Trip Members Table

```sql
CREATE TABLE trip_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id),

  role VARCHAR(50) NOT NULL DEFAULT 'viewer',
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  permissions JSONB,

  joined_at TIMESTAMP WITH TIME ZONE,
  last_viewed_at TIMESTAMP WITH TIME ZONE,

  preferences JSONB,

  UNIQUE(trip_id, user_id)
);

CREATE INDEX idx_trip_members_trip ON trip_members(trip_id);
CREATE INDEX idx_trip_members_user ON trip_members(user_id);
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
