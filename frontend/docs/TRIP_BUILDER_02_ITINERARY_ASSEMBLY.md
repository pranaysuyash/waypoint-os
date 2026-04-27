# Trip Builder 02: Itinerary Assembly

> Multi-component trip planning, component selection algorithms, timing validation, and route optimization

---

## Overview

This document details the itinerary assembly subsystem, covering multi-component trip planning, component selection algorithms, timing and logistics validation, route optimization, and alternative suggestions. The assembly engine orchestrates the combination of flights, accommodations, transfers, and activities into coherent, validated itineraries.

**Key Capabilities:**
- Multi-component itinerary assembly
- Automatic timing validation
- Route optimization
- Transfer calculation
- Constraint satisfaction
- Alternative generation
- Conflict detection and resolution

---

## Table of Contents

1. [Assembly Architecture](#assembly-architecture)
2. [Component Selection](#component-selection)
3. [Timing Validation](#timing-validation)
4. [Transfer Management](#transfer-management)
5. [Route Optimization](#route-optimization)
6. [Constraint Handling](#constraint-handling)
7. [Alternative Generation](#alternative-generation)

---

## Assembly Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ITINERARY ASSEMBLY ENGINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  TRIP       │───▶│  COMPONENT   │───▶│  SELECTION   │                  │
│  │  REQUEST    │    │  FINDER      │    │  RANKER      │                  │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘                  │
│                             │                    │                          │
│                             └─────────┬──────────┘                          │
│                                       │                                     │
│                                       ▼                                     │
│                              ┌──────────────┐                             │
│                              │  ASSEMBLY    │                             │
│                              │  ENGINE      │                             │
│                              └──────┬───────┘                             │
│                                       │                                     │
│          ┌────────────────────────────┼────────────────────────────┐      │
│          │                            │                            │       │
│     ┌────▼────┐                  ┌─────▼─────┐              ┌─────▼─────┐    │
│     │TIMING   │                  │ TRANSFER  │              │ ROUTE     │    │
│     │VALIDATOR│                  │ CALCULATOR│              │OPTIMIZER  │    │
│     └────┬────┘                  └─────┬─────┘              └─────┬─────┘    │
│          │                            │                            │           │
│          └────────────────────────────┼────────────────────────────┘       │
│                                       │                                    │
│                                       ▼                                    │
│                              ┌──────────────┐                             │
│                              │  CONSTRAINT  │                             │
│                              │  SOLVER      │                             │
│                              └──────┬───────┘                             │
│                                       │                                    │
│                                       ▼                                    │
│                              ┌──────────────┐                             │
│                              │  ITINERARY   │                             │
│                              │  BUILDER     │                             │
│                              └──────┬───────┘                             │
│                                       │                                    │
│                                       ▼                                    │
│                              ┌──────────────┐                             │
│                              │  TIMELINE    │                             │
│                              │  GENERATOR   │                             │
│                              └──────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Component Finder** | Searches for available components across suppliers |
| **Selection Ranker** | Scores and ranks component options |
| **Assembly Engine** | Combines components into coherent itineraries |
| **Timing Validator** | Validates timing between components |
| **Transfer Calculator** | Calculates transfer times and logistics |
| **Route Optimizer** | Optimizes multi-component routing |
| **Constraint Solver** | Satisfies user constraints and preferences |
| **Itinerary Builder** | Constructs final itinerary structure |
| **Timeline Generator** | Generates visual timeline representation |

---

## Component Selection

### Search and Selection

```typescript
class ComponentFinder {
  private services: Map<ComponentType, ComponentService>;

  async findComponents(
    request: ComponentSearchRequest
  ): Promise<ComponentOption[]> {
    const options: ComponentOption[] = [];

    // Search each component type
    for (const type of request.types) {
      const typeOptions = await this.searchComponentType(type, request);
      options.push(...typeOptions);
    }

    return options;
  }

  private async searchComponentType(
    type: ComponentType,
    request: ComponentSearchRequest
  ): Promise<ComponentOption[]> {
    const service = this.services.get(type);

    if (!service) {
      return [];
    }

    // Build search request for this type
    const searchRequest = this.buildSearchRequest(type, request);

    // Search for options
    const offers = await service.search(searchRequest);

    // Convert to component options
    return offers.map(offer => ({
      id: this.generateId(),
      type,
      offer,
      pricing: offer.pricing,
      availability: offer.availability,
      score: 0 // Will be calculated by ranker
    }));
  }

  private buildSearchRequest(
    type: ComponentType,
    request: ComponentSearchRequest
  ): SearchRequest {
    const base = {
      origin: request.origin,
      destination: request.destination,
      startDate: request.startDate,
      endDate: request.endDate,
      passengers: request.passengers,
      currency: request.currency
    };

    switch (type) {
      case ComponentType.FLIGHT:
        return {
          ...base,
          cabinClass: request.preferences?.flightCabinClass,
          directOnly: request.preferences?.directFlights,
          maxStops: request.preferences?.maxStops
        } as FlightSearchRequest;

      case ComponentType.ACCOMMODATION:
        return {
          ...base,
          roomType: request.preferences?.roomType,
          amenities: request.preferences?.amenities
        } as AccommodationSearchRequest;

      case ComponentType.CAR_RENTAL:
        return {
          ...base,
          vehicleType: request.preferences?.vehicleType,
          transmission: request.preferences?.transmission
        } as CarRentalSearchRequest;

      default:
        return base;
    }
  }
}

interface ComponentSearchRequest {
  types: ComponentType[];
  origin: Location;
  destination: Location;
  startDate: Date;
  endDate: Date;
  passengers: PassengerCount;
  currency: string;
  preferences?: TripPreferences;
}

interface ComponentOption {
  id: string;
  type: ComponentType;
  offer: ComponentOffer;
  pricing: ComponentPricing;
  availability: AvailabilityInfo;
  score: number;
}
```

### Selection Ranking

```typescript
class SelectionRanker {
  async rankOptions(
    options: ComponentOption[],
    context: RankingContext
  ): Promise<ComponentOption[]> {
    // Score each option
    const scored = await Promise.all(
      options.map(option => this.scoreOption(option, context))
    );

    // Sort by score
    scored.sort((a, b) => b.score - a.score);

    return scored;
  }

  private async scoreOption(
    option: ComponentOption,
    context: RankingContext
  ): Promise<ComponentOption> {
    let score = 0;

    // Price score (lower is better, but invert for ranking)
    const priceScore = this.calculatePriceScore(option, context);
    score += priceScore * context.weights.price;

    // Quality score
    const qualityScore = await this.calculateQualityScore(option, context);
    score += qualityScore * context.weights.quality;

    // Location score
    const locationScore = this.calculateLocationScore(option, context);
    score += locationScore * context.weights.location;

    // Timing score
    const timingScore = this.calculateTimingScore(option, context);
    score += timingScore * context.weights.timing;

    // Availability score
    const availabilityScore = this.calculateAvailabilityScore(option);
    score += availabilityScore * context.weights.availability;

    // Preference match score
    const preferenceScore = this.calculatePreferenceScore(option, context);
    score += preferenceScore * context.weights.preferences;

    return {
      ...option,
      score: Math.max(0, Math.min(100, score))
    };
  }

  private calculatePriceScore(
    option: ComponentOption,
    context: RankingContext
  ): number {
    const budget = context.budget;
    if (!budget) return 50; // Neutral score if no budget

    const price = option.pricing.total;
    const allocation = this.getAllocationForType(option.type, budget);

    if (price <= allocation) {
      // Within budget - higher score for lower price
      return 50 + (1 - price / allocation) * 50;
    } else {
      // Over budget - penalize
      const overage = (price - allocation) / allocation;
      return Math.max(0, 50 - overage * 100);
    }
  }

  private async calculateQualityScore(
    option: ComponentOption,
    context: RankingContext
  ): Promise<number> {
    const product = option.offer.product;

    // Rating score
    let ratingScore = 50;
    if (product.rating) {
      ratingScore = product.rating * 20; // 5 stars = 100
    }

    // Review count confidence
    if (product.reviewCount && product.reviewCount < 10) {
      ratingScore *= 0.7; // Reduce confidence for low review counts
    }

    return ratingScore;
  }

  private calculateLocationScore(
    option: ComponentOption,
    context: RankingContext
  ): number {
    const productLocation = option.offer.product.location;
    const preferences = context.preferences;

    // Proximity to desired location
    if (preferences?.location) {
      const distance = this.calculateDistance(
        preferences.location,
        productLocation
      );

      if (distance < 1) return 100; // Within 1km
      if (distance < 5) return 80;  // Within 5km
      if (distance < 10) return 60; // Within 10km
      return 40; // Far
    }

    return 50; // Neutral
  }

  private calculateTimingScore(
    option: ComponentOption,
    context: RankingContext
  ): number {
    // Check if timing aligns with preferences
    const preferences = context.preferences;

    if (preferences?.preferredTimes) {
      const startTime = option.offer.startDate;
      const hour = startTime.getHours();

      // Morning preference
      if (preferences.preferredTimes.includes('morning') && hour >= 6 && hour < 12) {
        return 80;
      }

      // Afternoon preference
      if (preferences.preferredTimes.includes('afternoon') && hour >= 12 && hour < 18) {
        return 80;
      }

      // Evening preference
      if (preferences.preferredTimes.includes('evening') && hour >= 18 && hour < 22) {
        return 80;
      }
    }

    return 50; // Neutral
  }

  private calculateAvailabilityScore(option: ComponentOption): number {
    const availability = option.availability;

    if (availability.status === 'available') {
      // Higher score for more availability
      return Math.min(100, 50 + availability.seatsAvailable * 5);
    }

    if (availability.status === 'limited') {
      return 30;
    }

    return 0; // Not available
  }

  private calculatePreferenceScore(
    option: ComponentOption,
    context: RankingContext
  ): number {
    const preferences = context.preferences;
    let score = 0;

    // Check amenity preferences
    if (preferences?.amenities && option.offer.product.attributes) {
      const matchCount = preferences.amenities.filter(amenity =>
        option.offer.product.attributes.has(amenity)
      ).length;

      score += (matchCount / preferences.amenities.length) * 30;
    }

    // Check airline/hotel brand preferences
    if (preferences?.preferredSuppliers?.includes(option.offer.supplier)) {
      score += 20;
    }

    return score;
  }

  private calculateDistance(loc1: Location, loc2: Location): number {
    const R = 6371; // Earth's radius in km
    const dLat = this.toRad(loc2.latitude - loc1.latitude);
    const dLon = this.toRad(loc2.longitude - loc1.longitude);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(loc1.latitude)) *
      Math.cos(this.toRad(loc2.latitude)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  private toRad(degrees: number): number {
    return degrees * (Math.PI / 180);
  }

  private getAllocationForType(type: ComponentType, budget: TripBudget): number {
    const allocations = {
      [ComponentType.FLIGHT]: budget.allocation.transport,
      [ComponentType.ACCOMMODATION]: budget.allocation.accommodation,
      [ComponentType.CAR_RENTAL]: budget.allocation.transport,
      [ComponentType.ACTIVITY]: budget.allocation.activities
    };

    return allocations[type] || 0;
  }
}

interface RankingContext {
  budget?: TripBudget;
  preferences?: TripPreferences;
  weights: RankingWeights;
  travelers: PassengerCount;
}

interface RankingWeights {
  price: number;
  quality: number;
  location: number;
  timing: number;
  availability: number;
  preferences: number;
}

interface TripPreferences {
  location?: Location;
  preferredTimes?: ('morning' | 'afternoon' | 'evening')[];
  amenities?: string[];
  preferredSuppliers?: string[];
  flightCabinClass?: CabinClass;
  roomType?: string;
  directFlights?: boolean;
  maxStops?: number;
  vehicleType?: string;
}
```

---

## Timing Validation

### Validation Engine

```typescript
class TimingValidator {
  async validateItinerary(
    components: TripComponent[]
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Sort components by start date
    const sorted = [...components].sort((a, b) =>
      a.startDate.getTime() - b.startDate.getTime()
    );

    // Validate timing between consecutive components
    for (let i = 0; i < sorted.length - 1; i++) {
      const current = sorted[i];
      const next = sorted[i + 1];

      const validation = await this.validateTimingBetween(current, next);

      errors.push(...validation.errors);
      warnings.push(...validation.warnings);
    }

    // Validate overall trip duration
    const durationValidation = this.validateOverallDuration(sorted);
    errors.push(...durationValidation.errors);
    warnings.push(...durationValidation.warnings);

    // Validate component-specific timing
    for (const component of sorted) {
      const componentValidation = await this.validateComponentTiming(component);
      errors.push(...componentValidation.errors);
      warnings.push(...componentValidation.warnings);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  private async validateTimingBetween(
    current: TripComponent,
    next: TripComponent
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Calculate gap between components
    const currentEnd = current.endDate;
    const nextStart = next.startDate;
    const gapMinutes = (nextStart.getTime() - currentEnd.getTime()) / (1000 * 60);

    // Determine minimum required gap based on component types
    const minGap = this.getMinimumGap(current.type, next.type);

    if (gapMinutes < minGap) {
      errors.push({
        type: 'insufficient_time',
        message: `Insufficient time between ${current.type} and ${next.type}. ` +
                `Required: ${minGap} minutes, Available: ${gapMinutes} minutes`,
        componentId: next.id,
        severity: 'error'
      });
    }

    // Check for excessively long gaps
    const maxGap = this.getMaximumGap(current.type, next.type);
    if (maxGap && gapMinutes > maxGap) {
      warnings.push({
        type: 'excessive_gap',
        message: `Long gap (${Math.round(gapMinutes / 60)} hours) between ${current.type} and ${next.type}`,
        componentId: next.id,
        severity: 'warning'
      });
    }

    // Validate location changes
    if (this.requiresTransfer(current, next)) {
      const transferTime = await this.calculateTransferTime(current, next);

      if (gapMinutes < transferTime.minimum) {
        errors.push({
          type: 'insufficient_transfer_time',
          message: `Insufficient transfer time. Need at least ${transferTime.minimum} minutes for transfer`,
          componentId: next.id,
          severity: 'error'
        });
      }
    }

    return { valid: errors.length === 0, errors, warnings };
  }

  private getMinimumGap(from: ComponentType, to: ComponentType): number {
    // Minimum time between components in minutes
    const gaps: Record<ComponentType, Record<ComponentType, number>> = {
      [ComponentType.FLIGHT]: {
        [ComponentType.FLIGHT]: 90, // Domestic connection
        [ComponentType.ACCOMMODATION]: 60,
        [ComponentType.CAR_RENTAL]: 45,
        [ComponentType.ACTIVITY]: 120,
        [ComponentType.TRANSFER]: 30
      },
      [ComponentType.ACCOMMODATION]: {
        [ComponentType.FLIGHT]: 60,
        [ComponentType.ACCOMMODATION]: 0,
        [ComponentType.CAR_RENTAL]: 30,
        [ComponentType.ACTIVITY]: 30,
        [ComponentType.TRANSFER]: 15
      },
      [ComponentType.CAR_RENTAL]: {
        [ComponentType.FLIGHT]: 90,
        [ComponentType.ACCOMMODATION]: 30,
        [ComponentType.CAR_RENTAL]: 0,
        [ComponentType.ACTIVITY]: 30,
        [ComponentType.TRANSFER]: 15
      },
      [ComponentType.ACTIVITY]: {
        [ComponentType.FLIGHT]: 120,
        [ComponentType.ACCOMMODATION]: 30,
        [ComponentType.CAR_RENTAL]: 30,
        [ComponentType.ACTIVITY]: 30,
        [ComponentType.TRANSFER]: 15
      },
      [ComponentType.TRANSFER]: {
        [ComponentType.FLIGHT]: 60,
        [ComponentType.ACCOMMODATION]: 30,
        [ComponentType.CAR_RENTAL]: 15,
        [ComponentType.ACTIVITY]: 30,
        [ComponentType.TRANSFER]: 0
      }
    };

    return gaps[from]?.[to] || 60;
  }

  private getMaximumGap(from: ComponentType, to: ComponentType): number | null {
    // Maximum reasonable gap in minutes (null = no limit)
    if (from === ComponentType.ACCOMMODATION && to === ComponentType.ACCOMMODATION) {
      return null; // Multiple nights in a row is fine
    }

    if (from === ComponentType.FLIGHT && to === ComponentType.FLIGHT) {
      return 6 * 60; // Don't want more than 6 hours between flights
    }

    return 4 * 60; // 4 hours default max gap
  }

  private requiresTransfer(current: TripComponent, next: TripComponent): boolean {
    // Check if locations are different
    if (!current.destination || !next.destination) {
      return false;
    }

    const distance = this.calculateDistance(current.destination, next.destination);
    return distance > 0.5; // More than 500m requires transfer
  }

  private async calculateTransferTime(
    current: TripComponent,
    next: TripComponent
  ): Promise<{ minimum: number; recommended: number }> {
    const distance = this.calculateDistance(current.destination, next.destination);
    const transferType = this.determineTransferType(current, next, distance);

    switch (transferType) {
      case 'walking':
        return {
          minimum: Math.ceil(distance / 5 * 60), // 5km/h walking speed
          recommended: Math.ceil(distance / 4 * 60)
        };

      case 'taxi':
        return {
          minimum: Math.ceil(distance / 30 * 60) + 10, // 30km/h + 10min buffer
          recommended: Math.ceil(distance / 30 * 60) + 20
        };

      case 'public_transport':
        return {
          minimum: Math.ceil(distance / 20 * 60) + 15, // 20km/h + wait time
          recommended: Math.ceil(distance / 20 * 60) + 30
        };

      case 'flight_connection':
        return {
          minimum: 90, // 90 minutes minimum for domestic connections
          recommended: 120
        };

      default:
        return { minimum: 60, recommended: 90 };
    }
  }

  private determineTransferType(
    current: TripComponent,
    next: TripComponent,
    distance: number
  ): TransferType {
    // Flight to flight = connection
    if (current.type === ComponentType.FLIGHT && next.type === ComponentType.FLIGHT) {
      return 'flight_connection';
    }

    // Short distance = walking
    if (distance < 1) {
      return 'walking';
    }

    // Medium distance = taxi
    if (distance < 10) {
      return 'taxi';
    }

    // Long distance = public transport or taxi
    return 'taxi';
  }

  private validateOverallDuration(
    components: TripComponent[]
  ): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    const first = components[0];
    const last = components[components.length - 1];

    const totalDuration = (last.endDate.getTime() - first.startDate.getTime()) / (1000 * 60 * 60 * 24);
    const totalDays = Math.ceil(totalDuration);

    // Check for unreasonably long trips
    if (totalDays > 30) {
      warnings.push({
        type: 'long_trip',
        message: `Trip duration is ${totalDays} days. Consider splitting into multiple trips.`,
        severity: 'warning'
      });
    }

    // Check for very short trips with many components
    if (totalDays < 3 && components.length > 5) {
      warnings.push({
        type: 'packed_itinerary',
        message: `Many components packed into ${totalDays} days. Consider extending stay.`,
        severity: 'warning'
      });
    }

    return { valid: errors.length === 0, errors, warnings };
  }

  private async validateComponentTiming(
    component: TripComponent
  ): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Validate duration is reasonable for component type
    const durationHours = (component.endDate.getTime() - component.startDate.getTime()) / (1000 * 60 * 60);

    switch (component.type) {
      case ComponentType.FLIGHT:
        if (durationHours > 15) {
          warnings.push({
            type: 'long_flight',
            message: `Flight duration is ${durationHours} hours. Consider layover options.`,
            componentId: component.id,
            severity: 'warning'
          });
        }
        break;

      case ComponentType.ACCOMMODATION:
        const nights = Math.round(durationHours / 24);
        if (nights < 1) {
          errors.push({
            type: 'invalid_stay',
            message: `Accommodation duration is less than 1 night.`,
            componentId: component.id,
            severity: 'error'
          });
        }
        break;

      case ComponentType.CAR_RENTAL:
        if (durationHours < 4) {
          warnings.push({
            type: 'short_rental',
            message: `Car rental duration is ${durationHours} hours. Minimum may apply.`,
            componentId: component.id,
            severity: 'warning'
          });
        }
        break;
    }

    return { valid: errors.length === 0, errors, warnings };
  }
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

interface ValidationError {
  type: string;
  message: string;
  componentId?: string;
  severity: 'error';
}

interface ValidationWarning {
  type: string;
  message: string;
  componentId?: string;
  severity: 'warning';
}

type TransferType = 'walking' | 'taxi' | 'public_transport' | 'flight_connection';
```

---

## Transfer Management

### Transfer Calculator

```typescript
class TransferCalculator {
  async calculateTransfers(
    components: TripComponent[]
  ): Promise<TransferInfo[]> {
    const transfers: TransferInfo[] = [];

    // Sort components by time
    const sorted = [...components].sort((a, b) =>
      a.startDate.getTime() - b.startDate.getTime()
    );

    // Calculate transfer between each consecutive pair
    for (let i = 0; i < sorted.length - 1; i++) {
      const current = sorted[i];
      const next = sorted[i + 1];

      if (this.requiresTransfer(current, next)) {
        const transfer = await this.calculateTransfer(current, next);
        transfers.push(transfer);
      }
    }

    return transfers;
  }

  private async calculateTransfer(
    from: TripComponent,
    to: TripComponent
  ): Promise<TransferInfo> {
    const distance = this.calculateDistance(from.destination, to.destination);
    const duration = this.estimateTransferDuration(distance, from, to);
    const options = await this.getTransferOptions(from, to, distance);

    return {
      fromComponentId: from.id,
      toComponentId: to.id,
      type: this.getBestTransferType(options),
      distance,
      duration,
      options,
      recommendedOption: this.selectRecommendedOption(options),
      price: this.estimatePrice(options),
      currency: 'USD',
      booked: false
    };
  }

  private async getTransferOptions(
    from: TripComponent,
    to: TripComponent,
    distance: number
  ): Promise<TransferOption[]> {
    const options: TransferOption[] = [];

    // Walking option (if reasonable)
    if (distance < 2) {
      options.push({
        type: 'walking',
        duration: Math.ceil(distance / 5 * 60), // 5km/h
        price: 0,
        available: true,
        description: `${Math.round(distance * 10) / 10} km walk`
      });
    }

    // Taxi option
    options.push({
      type: 'taxi',
      duration: Math.ceil(distance / 30 * 60) + 5, // 30km/h + 5min buffer
      price: this.estimateTaxiPrice(distance),
      available: true,
      description: `Taxi or rideshare`
    });

    // Public transport option (if available)
    const publicTransport = await this.checkPublicTransport(from, to);
    if (publicTransport) {
      options.push({
        type: 'public_transport',
        duration: publicTransport.duration,
        price: publicTransport.price,
        available: true,
        description: publicTransport.description
      });
    }

    // Private transfer option
    options.push({
      type: 'private_transfer',
      duration: Math.ceil(distance / 40 * 60) + 10,
      price: this.estimatePrivateTransferPrice(distance),
      available: true,
      description: `Pre-booked private transfer`
    });

    return options;
  }

  private selectRecommendedOption(options: TransferOption[]): TransferOption {
    // Prefer walking if available and reasonable
    const walking = options.find(o => o.type === 'walking');
    if (walking && walking.duration < 20) {
      return walking;
    }

    // Prefer public transport if significantly cheaper
    const publicTransport = options.find(o => o.type === 'public_transport');
    const taxi = options.find(o => o.type === 'taxi');

    if (publicTransport && taxi && publicTransport.price < taxi.price * 0.5) {
      return publicTransport;
    }

    // Default to taxi
    return taxi || options[0];
  }

  private estimateTaxiPrice(distance: number): number {
    // Base fare + distance charge
    const baseFare = 3.0;
    const perKm = 2.0;
    return baseFare + (distance * perKm);
  }

  private estimatePrivateTransferPrice(distance: number): number {
    // Private transfers are more expensive but fixed price
    const baseFare = 15.0;
    const perKm = 2.5;
    return Math.max(baseFare, baseFare + (distance * perKm));
  }

  private async checkPublicTransport(
    from: TripComponent,
    to: TripComponent
  ): Promise<PublicTransportOption | null> {
    // Check if public transport is available between locations
    // This would integrate with local transit APIs

    // For now, return null (no data available)
    return null;
  }
}

interface TransferInfo {
  fromComponentId: string;
  toComponentId: string;
  type: TransferType;
  distance: number; // km
  duration: number; // minutes
  options: TransferOption[];
  recommendedOption: TransferOption;
  price: number;
  currency: string;
  booked: boolean;
}

interface TransferOption {
  type: 'walking' | 'taxi' | 'public_transport' | 'private_transfer';
  duration: number; // minutes
  price: number;
  available: boolean;
  description: string;
}

interface PublicTransportOption {
  duration: number;
  price: number;
  description: string;
}
```

---

## Route Optimization

### Route Optimizer

```typescript
class RouteOptimizer {
  async optimizeItinerary(
    components: TripComponent[],
    constraints: OptimizationConstraints
  ): Promise<TripComponent[]> {
    // Create optimization model
    const model = this.createOptimizationModel(components, constraints);

    // Solve optimization
    const solution = await this.solveOptimization(model);

    // Apply solution to components
    return this.applySolution(components, solution);
  }

  private createOptimizationModel(
    components: TripComponent[],
    constraints: OptimizationConstraints
  ): OptimizationModel {
    // Define decision variables
    const variables = components.map((c, i) => ({
      component: c,
      index: i,
      startTime: this.getStartTimeWindow(c, constraints),
      endTime: this.getEndTimeWindow(c, constraints),
      position: this.getPositionOptions(c, components.length)
    }));

    // Define objective function
    const objective = this.buildObjective(variables, constraints);

    // Define constraints
    const constraintList = this.buildConstraints(variables, constraints);

    return { variables, objective, constraints: constraintList };
  }

  private buildObjective(
    variables: OptimizationVariable[],
    constraints: OptimizationConstraints
  ): OptimizationObjective {
    // Minimize: total cost, total travel time, gaps between activities
    const minimize: string[] = [];

    if (constraints.minimizeCost) {
      minimize.push('total_cost');
    }

    if (constraints.minimizeTravelTime) {
      minimize.push('total_travel_time');
    }

    if (constraints.minimizeGaps) {
      minimize.push('total_gap_time');
    }

    // Maximize: activity time, satisfaction
    const maximize: string[] = [];

    if (constraints.maximizeActivityTime) {
      maximize.push('total_activity_time');
    }

    if (constraints.maximizeSatisfaction) {
      maximize.push('total_satisfaction');
    }

    return { minimize, maximize };
  }

  private buildConstraints(
    variables: OptimizationVariable[],
    constraints: OptimizationConstraints
  ): OptimizationConstraint[] {
    const constraintList: OptimizationConstraint[] = [];

    // Each component must be assigned exactly one position
    constraintList.push({
      type: 'assignment',
      description: 'Each component assigned to one position'
    });

    // No two components at same position
    constraintList.push({
      type: 'unique_position',
      description: 'Unique position for each component'
    });

    // Timing constraints between components
    constraintList.push({
      type: 'timing',
      description: 'Valid timing between consecutive components',
      minGap: constraints.minGapMinutes || 30
    });

    // Location constraints (if fixed start/end)
    if (constraints.fixedOrigin) {
      constraintList.push({
        type: 'fixed_start',
        description: 'First component must start at origin',
        location: constraints.fixedOrigin
      });
    }

    if (constraints.fixedDestination) {
      constraintList.push({
        type: 'fixed_end',
        description: 'Last component must end at destination',
        location: constraints.fixedDestination
      });
    }

    // Time window constraints
    if (constraints.timeWindows) {
      for (const window of constraints.timeWindows) {
        constraintList.push({
          type: 'time_window',
          componentId: window.componentId,
          start: window.start,
          end: window.end
        });
      }
    }

    return constraintList;
  }

  private async solveOptimization(
    model: OptimizationModel
  ): Promise<OptimizationSolution> {
    // Use constraint programming or genetic algorithm
    // For simplicity, using greedy approach here

    const solution: OptimizationSolution = {
      componentOrder: [],
      timings: new Map(),
      objectiveValue: 0
    };

    // Sort components by constraints
    const sorted = this.greedySort(model.variables, model.constraints);

    // Calculate optimal timings
    let currentTime = sorted[0].startTime.earliest;

    for (const variable of sorted) {
      solution.componentOrder.push(variable.component.id);

      // Set start time (respect time windows)
      const start = Math.max(currentTime, variable.startTime.earliest);
      const duration = (variable.component.endDate.getTime() -
                       variable.component.startDate.getTime()) / (1000 * 60);

      solution.timings.set(variable.component.id, {
        start: new Date(start),
        end: new Date(start + duration * 60 * 1000)
      });

      // Update current time
      currentTime = start + duration + this.getMinGapAfter(variable, model.constraints);
    }

    return solution;
  }

  private greedySort(
    variables: OptimizationVariable[],
    constraints: OptimizationConstraint[]
  ): OptimizationVariable[] {
    // Sort by earliest start time, then by duration
    return [...variables].sort((a, b) => {
      // Fixed position components first
      const aFixed = this.hasFixedPosition(a, constraints);
      const bFixed = this.hasFixedPosition(b, constraints);

      if (aFixed && !bFixed) return -1;
      if (!aFixed && bFixed) return 1;

      // Then by earliest start
      if (a.startTime.earliest < b.startTime.earliest) return -1;
      if (a.startTime.earliest > b.startTime.earliest) return 1;

      // Then by shortest duration first
      const aDuration = a.component.endDate.getTime() - a.component.startDate.getTime();
      const bDuration = b.component.endDate.getTime() - b.component.startDate.getTime();

      return aDuration - bDuration;
    });
  }

  private applySolution(
    components: TripComponent[],
    solution: OptimizationSolution
  ): TripComponent[] {
    const componentMap = new Map(components.map(c => [c.id, c]));
    const optimized: TripComponent[] = [];

    for (const id of solution.componentOrder) {
      const component = componentMap.get(id)!;
      const timing = solution.timings.get(id)!;

      optimized.push({
        ...component,
        startDate: timing.start,
        endDate: timing.end
      });
    }

    return optimized;
  }
}

interface OptimizationConstraints {
  minimizeCost?: boolean;
  minimizeTravelTime?: boolean;
  minimizeGaps?: boolean;
  maximizeActivityTime?: boolean;
  maximizeSatisfaction?: boolean;
  minGapMinutes?: number;
  fixedOrigin?: Location;
  fixedDestination?: Location;
  timeWindows?: TimeWindow[];
}

interface OptimizationModel {
  variables: OptimizationVariable[];
  objective: OptimizationObjective;
  constraints: OptimizationConstraint[];
}

interface OptimizationVariable {
  component: TripComponent;
  index: number;
  startTime: TimeRange;
  endTime: TimeRange;
  position: number[];
}

interface OptimizationObjective {
  minimize: string[];
  maximize: string[];
}

interface OptimizationConstraint {
  type: string;
  description: string;
  [key: string]: any;
}

interface OptimizationSolution {
  componentOrder: string[];
  timings: Map<string, TimeRange>;
  objectiveValue: number;
}

interface TimeRange {
  earliest: number; // timestamp
  latest: number; // timestamp
}

interface TimeWindow {
  componentId: string;
  start: Date;
  end: Date;
}
```

---

## Constraint Handling

### Constraint Solver

```typescript
class ConstraintSolver {
  async solveConstraints(
    components: TripComponent[],
    constraints: TripConstraints
  ): Promise<SolutionResult> {
    const solutions: SolutionResult[] = [];

    // Try different strategies
    const strategies = this.getSolutionStrategies(constraints);

    for (const strategy of strategies) {
      const result = await this.tryStrategy(components, constraints, strategy);

      if (result.satisfied) {
        solutions.push(result);
      }
    }

    // Return best solution
    if (solutions.length === 0) {
      return {
        satisfied: false,
        violations: this.getViolations(components, constraints)
      };
    }

    // Rank solutions and return best
    solutions.sort((a, b) => b.score - a.score);
    return solutions[0];
  }

  private async tryStrategy(
    components: TripComponent[],
    constraints: TripConstraints,
    strategy: SolutionStrategy
  ): Promise<SolutionResult> {
    // Apply strategy
    let modified = [...components];

    switch (strategy) {
      case 'shift_timing':
        modified = this.shiftTimings(components, constraints);
        break;

      case 'swap_components':
        modified = this.swapComponents(components, constraints);
        break;

      case 'remove_component':
        modified = this.removeProblematicComponents(components, constraints);
        break;

      case 'add_buffer':
        modified = this.addBuffers(components, constraints);
        break;
    }

    // Check if constraints are satisfied
    const satisfied = await this.checkConstraints(modified, constraints);

    if (satisfied) {
      // Calculate solution score
      const score = this.calculateSolutionScore(modified, constraints);

      return {
        satisfied: true,
        components: modified,
        score,
        strategy
      };
    }

    return {
      satisfied: false,
      violations: await this.getViolations(modified, constraints)
    };
  }

  private shiftTimings(
    components: TripComponent[],
    constraints: TripConstraints
  ): TripComponent[] {
    // Shift component timings to satisfy constraints
    const modified: TripComponent[] = [];
    let currentTime = constraints.startTime?.getTime() || components[0].startDate.getTime();

    for (const component of components) {
      const duration = component.endDate.getTime() - component.startDate.getTime();

      modified.push({
        ...component,
        startDate: new Date(currentTime),
        endDate: new Date(currentTime + duration)
      });

      currentTime += duration + constraints.minGapMinutes * 60 * 1000;
    }

    return modified;
  }

  private swapComponents(
    components: TripComponent[],
    constraints: TripConstraints
  ): TripComponent[] {
    // Find components that can be swapped to improve constraints
    // This is a simplified version - real implementation would use more sophisticated swapping

    return [...components]; // Placeholder
  }

  private removeProblematicComponents(
    components: TripComponent[],
    constraints: TripConstraints
  ): TripComponent[] {
    // Remove components that cause constraint violations
    // This is a last resort strategy

    return [...components]; // Placeholder
  }

  private addBuffers(
    components: TripComponent[],
    constraints: TripConstraints
  ): TripComponent[] {
    // Add time buffers between components
    const modified: TripComponent[] = [];
    let currentTime = components[0].startDate.getTime();

    for (let i = 0; i < components.length; i++) {
      const component = components[i];
      const duration = component.endDate.getTime() - component.startDate.getTime();

      modified.push({
        ...component,
        startDate: new Date(currentTime),
        endDate: new Date(currentTime + duration)
      });

      currentTime += duration;

      // Add buffer (except after last component)
      if (i < components.length - 1) {
        const buffer = this.getRequiredBuffer(component, components[i + 1]);
        currentTime += buffer * 60 * 1000;
      }
    }

    return modified;
  }

  private getRequiredBuffer(current: TripComponent, next: TripComponent): number {
    // Calculate required buffer time based on component types
    const baseBuffer = 30; // 30 minutes default

    // Add buffer for uncertainty
    if (current.type === ComponentType.FLIGHT) {
      return baseBuffer + 30; // Flights are unpredictable
    }

    return baseBuffer;
  }
}

interface TripConstraints {
  startTime?: Date;
  endTime?: Date;
  minGapMinutes?: number;
  maxDuration?: number; // days
  mustInclude?: string[]; // component IDs
  mustExclude?: string[]; // component IDs
  fixedOrder?: boolean;
  budget?: TripBudget;
}

interface SolutionResult {
  satisfied: boolean;
  components?: TripComponent[];
  score?: number;
  strategy?: SolutionStrategy;
  violations?: ConstraintViolation[];
}

interface ConstraintViolation {
  type: string;
  componentId?: string;
  description: string;
  severity: 'error' | 'warning';
}

type SolutionStrategy = 'shift_timing' | 'swap_components' | 'remove_component' | 'add_buffer';
```

---

## Alternative Generation

### Alternative Generator

```typescript
class AlternativeGenerator {
  async generateAlternatives(
    trip: Trip,
    count: number = 3
  ): Promise<TripAlternative[]> {
    const alternatives: TripAlternative[] = [];

    // Generate different types of alternatives
    const strategies = [
      'cheaper',
      'better_quality',
      'different_timing',
      'different_route',
      'shorter_duration'
    ];

    for (const strategy of strategies) {
      if (alternatives.length >= count) break;

      const alternative = await this.generateAlternative(trip, strategy);

      if (alternative) {
        alternatives.push(alternative);
      }
    }

    // Score and rank alternatives
    for (const alt of alternatives) {
      alt.score = await this.scoreAlternative(alt, trip);
    }

    alternatives.sort((a, b) => b.score - a.score);

    return alternatives.slice(0, count);
  }

  private async generateAlternative(
    trip: Trip,
    strategy: AlternativeStrategy
  ): Promise<TripAlternative | null> {
    switch (strategy) {
      case 'cheaper':
        return await this.generateCheaperAlternative(trip);

      case 'better_quality':
        return await this.generateBetterQualityAlternative(trip);

      case 'different_timing':
        return await this.generateDifferentTimingAlternative(trip);

      case 'different_route':
        return await this.generateDifferentRouteAlternative(trip);

      case 'shorter_duration':
        return await this.generateShorterDurationAlternative(trip);

      default:
        return null;
    }
  }

  private async generateCheaperAlternative(trip: Trip): Promise<TripAlternative | null> {
    // Find cheaper options for each component
    const alternativeComponents: TripComponent[] = [];

    for (const component of trip.components) {
      const cheaperOptions = await this.findCheaperOptions(component);

      if (cheaperOptions.length > 0) {
        alternativeComponents.push({
          ...component,
          offer: cheaperOptions[0],
          pricing: cheaperOptions[0].pricing
        });
      } else {
        alternativeComponents.push(component);
      }
    }

    const savings = this.calculateSavings(trip.components, alternativeComponents);

    return {
      type: 'cheaper',
      name: 'Budget Option',
      description: `Save ${savings.amount} ${savings.currency} with alternative choices`,
      components: alternativeComponents,
      pricing: this.calculateTotalPricing(alternativeComponents),
      highlights: [
        `Saves ${savings.amount} ${savings.currency}`,
        'Similar itinerary, lower cost'
      ],
      tradeoffs: [
        'May have different amenities',
        'Possible timing changes'
      ]
    };
  }

  private async generateBetterQualityAlternative(trip: Trip): Promise<TripAlternative | null> {
    // Find higher quality options for each component
    const alternativeComponents: TripComponent[] = [];

    for (const component of trip.components) {
      const betterOptions = await this.findBetterQualityOptions(component);

      if (betterOptions.length > 0) {
        alternativeComponents.push({
          ...component,
          offer: betterOptions[0],
          pricing: betterOptions[0].pricing
        });
      } else {
        alternativeComponents.push(component);
      }
    }

    const premium = this.calculatePremium(trip.components, alternativeComponents);

    return {
      type: 'better_quality',
      name: 'Premium Option',
      description: `Upgrade experience for ${premium.amount} ${premium.currency} more`,
      components: alternativeComponents,
      pricing: this.calculateTotalPricing(alternativeComponents),
      highlights: [
        'Higher-rated accommodations',
        'Better flight times',
        'Premium amenities'
      ],
      tradeoffs: [
        `Costs ${premium.amount} ${premium.currency} more`
      ]
    };
  }

  private async generateDifferentTimingAlternative(trip: Trip): Promise<TripAlternative | null> {
    // Shift trip by a day or two
    const offsetDays = 1;
    const alternativeComponents: TripComponent[] = [];

    for (const component of trip.components) {
      const newStart = new Date(component.startDate.getTime() + offsetDays * 24 * 60 * 60 * 1000);
      const newEnd = new Date(component.endDate.getTime() + offsetDays * 24 * 60 * 60 * 1000);

      // Search for options on new dates
      const newOptions = await this.searchOptionsForDates(
        component.type,
        component.destination,
        newStart,
        newEnd
      );

      if (newOptions.length > 0) {
        alternativeComponents.push({
          ...component,
          startDate: newStart,
          endDate: newEnd,
          offer: newOptions[0],
          pricing: newOptions[0].pricing
        });
      } else {
        // No options available for alternative dates
        return null;
      }
    }

    return {
      type: 'different_timing',
      name: `${offsetDays} Day${offsetDays > 1 ? 's' : ''} Later`,
      description: `Same itinerary, ${offsetDays} day${offsetDays > 1 ? 's' : ''} later`,
      components: alternativeComponents,
      pricing: this.calculateTotalPricing(alternativeComponents),
      highlights: [
        'Different departure date',
        'Similar experience'
      ],
      tradeoffs: [
        'Different dates may affect pricing',
        'May impact availability'
      ]
    };
  }

  private async scoreAlternative(
    alternative: TripAlternative,
    original: Trip
  ): Promise<number> {
    let score = 50;

    // Price comparison
    const priceDiff = alternative.pricing.total - original.pricing.total;
    if (priceDiff < 0) {
      score += Math.min(20, Math.abs(priceDiff) / 100); // Up to 20 points for savings
    }

    // Quality improvement
    const qualityImprovement = await this.calculateQualityImprovement(
      alternative.components,
      original.components
    );
    score += qualityImprovement * 10;

    // Timing similarity (closer to original is better)
    const timingSimilarity = this.calculateTimingSimilarity(
      alternative.components,
      original.components
    );
    score += timingSimilarity * 10;

    return Math.max(0, Math.min(100, score));
  }
}

interface TripAlternative {
  type: string;
  name: string;
  description: string;
  components: TripComponent[];
  pricing: TripPricing;
  highlights: string[];
  tradeoffs: string[];
  score?: number;
}

type AlternativeStrategy = 'cheaper' | 'better_quality' | 'different_timing' | 'different_route' | 'shorter_duration';
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
