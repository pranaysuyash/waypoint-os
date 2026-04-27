# Accommodation Catalog 03: Inventory & Pricing

> Room types, availability tracking, rate plans, and pricing structures

---

## Overview

This document details the inventory and pricing subsystem for accommodations, covering room type management, real-time availability tracking, flexible rate plan structures, and dynamic pricing strategies. This subsystem connects properties to the booking engine, ensuring accurate inventory and pricing for reservations.

**Key Capabilities:**
- Room type catalog management
- Real-time availability tracking
- Flexible rate plan structures
- Dynamic pricing strategies
- Seasonal and promotional pricing
- Multi-occupancy pricing

---

## Table of Contents

1. [Room Type Management](#room-type-management)
2. [Availability Tracking](#availability-tracking)
3. [Rate Plan Management](#rate-plan-management)
4. [Pricing Engine](#pricing-engine)
5. [Dynamic Pricing](#dynamic-pricing)
6. [Promotions](#promotions)

---

## Room Type Management

### Room Type CRUD

```typescript
export class RoomTypeService {
  async createRoomType(
    propertyId: string,
    data: Omit<RoomType, 'id' | 'propertyId' | 'createdAt' | 'updatedAt'>
  ): Promise<RoomType> {
    // Validate property exists
    const property = await this.propertyService.getProperty(propertyId);

    // Validate room type data
    await this.validateRoomType(data);

    // Check for duplicate code
    const existing = await this.roomTypeRepository.findByCode(
      propertyId,
      data.code
    );

    if (existing) {
      throw new ConflictError('Room type code already exists');
    }

    // Create room type
    const roomType = await this.roomTypeRepository.create({
      ...data,
      propertyId,
      status: 'active',
    });

    // Index for search
    await this.searchService.indexRoomType(roomType);

    return roomType;
  }

  async updateRoomType(
    propertyId: string,
    roomTypeId: string,
    updates: Partial<RoomType>
  ): Promise<RoomType> {
    const roomType = await this.getRoomType(propertyId, roomTypeId);

    // Validate updates
    if (updates.occupancy) {
      this.validateOccupancy(updates.occupancy);
    }

    // Apply updates
    const updated = await this.roomTypeRepository.update(roomTypeId, {
      ...updates,
      updatedAt: new Date(),
    });

    // Re-index
    await this.searchService.reindexRoomType(roomTypeId);

    return updated;
  }

  async deleteRoomType(
    propertyId: string,
    roomTypeId: string
  ): Promise<void> {
    const roomType = await this.getRoomType(propertyId, roomTypeId);

    // Check for active bookings
    const hasBookings = await this.bookingService.hasActiveBookingsForRoomType(
      roomTypeId
    );

    if (hasBookings) {
      throw new ConflictError(
        'Cannot delete room type with active bookings'
      );
    }

    // Delete
    await this.roomTypeRepository.delete(roomTypeId);

    // Remove from search index
    await this.searchService.deleteRoomType(roomTypeId);
  }

  async getRoomType(
    propertyId: string,
    roomTypeId: string
  ): Promise<RoomType> {
    const roomType = await this.roomTypeRepository.findById(roomTypeId);

    if (!roomType || roomType.propertyId !== propertyId) {
      throw new NotFoundError('Room type not found');
    }

    return roomType;
  }

  async listRoomTypes(
    propertyId: string,
    options: ListOptions = {}
  ): Promise<RoomType[]> {
    const query = this.roomTypeRepository
      .query()
      .where('propertyId', propertyId)
      .where('status', '!=', 'deleted');

    if (options.activeOnly) {
      query.where('status', 'active');
    }

    return query.orderBy('name', 'asc').getMany();
  }

  private async validateRoomType(data: Partial<RoomType>): Promise<void> {
    // Required fields
    if (!data.code || !data.name) {
      throw new ValidationError('Code and name are required');
    }

    // Valid type
    if (data.type && !this.isValidRoomType(data.type)) {
      throw new ValidationError('Invalid room type');
    }

    // Occupancy limits
    if (data.occupancy) {
      this.validateOccupancy(data.occupancy);
    }

    // Bed configurations
    if (data.bedConfiguration) {
      for (const bed of data.bedConfiguration) {
        if (!bed.type || bed.count < 1) {
          throw new ValidationError('Invalid bed configuration');
        }
      }
    }
  }

  private validateOccupancy(occupancy: OccupancyLimits): void {
    if (occupancy.maxAdults < 1) {
      throw new ValidationError('Max adults must be at least 1');
    }

    if (occupancy.maxChildren < 0) {
      throw new ValidationError('Max children cannot be negative');
    }

    if (occupancy.maxTotal < occupancy.maxAdults) {
      throw new ValidationError('Max total must be at least max adults');
    }

    if (occupancy.minAdults !== undefined && occupancy.minAdults < 1) {
      throw new ValidationError('Min adults must be at least 1');
    }

    if (
      occupancy.minAdults !== undefined &&
      occupancy.minAdults > occupancy.maxAdults
    ) {
      throw new ValidationError('Min adults cannot exceed max adults');
    }
  }

  private isValidRoomType(type: string): boolean {
    const valid = [
      'single', 'double', 'twin', 'suite', 'studio', 'apartment',
      'family', 'accessible', 'penthouse', 'villa'
    ];
    return valid.includes(type);
  }
}
```

### Bed Configuration Builder

```typescript
export class BedConfigurationService {
  calculateCapacity(config: BedConfiguration[]): OccupancyLimits {
    let maxAdults = 0;
    let maxChildren = 0;

    for (const bed of config) {
      const capacity = this.getBedCapacity(bed.type, bed.size);
      maxAdults += capacity.adults;
      maxChildren += capacity.children;
    }

    return {
      maxAdults,
      maxChildren,
      maxTotal: maxAdults + maxChildren,
    };
  }

  private getBedCapacity(
    type: BedType,
    size?: BedSize
  ): { adults: number; children: number } {
    const capacities: Record<BedType, { adults: number; children: number }> = {
      single: { adults: 1, children: 0 },
      double: { adults: 2, children: 0 },
      queen: { adults: 2, children: 1 },
      king: { adults: 2, children: 1 },
      bunk: { adults: 1, children: 1 },
      sofa_bed: { adults: 1, children: 1 },
      cot: { adults: 0, children: 1 },
    };

    return capacities[type] || { adults: 1, children: 0 };
  }

  formatDescription(config: BedConfiguration[]): string {
    const grouped = this.groupByType(config);

    return Object.entries(grouped)
      .map(([type, beds]) => {
        const count = beds.reduce((sum, b) => sum + b.count, 0);
        return `${count} ${this.pluralize(type, count)}`;
      })
      .join(', ');
  }

  private groupByType(
    config: BedConfiguration[]
  ): Record<BedType, BedConfiguration[]> {
    return config.reduce((acc, bed) => {
      if (!acc[bed.type]) {
        acc[bed.type] = [];
      }
      acc[bed.type].push(bed);
      return acc;
    }, {} as Record<BedType, BedConfiguration[]>);
  }

  private pluralize(type: BedType, count: number): string {
    if (count === 1) {
      return type.replace(/_/g, ' ');
    }
    return `${type.replace(/_/g, ' ')}s`;
  }
}
```

---

## Availability Tracking

### Real-Time Availability

```typescript
export class AvailabilityService {
  async getAvailability(
    propertyId: string,
    roomTypeId: string,
    dates: DateRange,
    ratePlanId?: string
  ): Promise<Availability[]> {
    const cacheKey = this.cacheKey(propertyId, roomTypeId, dates, ratePlanId);

    // Check cache
    const cached = await this.redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Query database
    const availability = await this.availabilityRepository.find({
      propertyId,
      roomTypeId,
      date: { $gte: dates.start, $lte: dates.end },
      ...(ratePlanId && { ratePlanId }),
    });

    // Cache result
    await this.redis.setex(
      cacheKey,
      this.CACHE_TTL,
      JSON.stringify(availability)
    );

    return availability;
  }

  async updateAvailability(
    updates: AvailabilityUpdate[]
  ): Promise<void> {
    // Batch update
    await this.availabilityRepository.bulkUpsert(updates);

    // Invalidate cache
    for (const update of updates) {
      const pattern = `availability:${update.propertyId}:${update.roomTypeId}:*`;
      await this.redis.delPattern(pattern);
    }

    // Notify subscribers
    await this.notifyAvailabilityChange(updates);
  }

  async checkAvailability(
    propertyId: string,
    roomTypeId: string,
    dates: DateRange,
    occupancy: Occupancy
  ): Promise<AvailabilityStatus> {
    const roomType = await this.roomTypeService.getRoomType(propertyId, roomTypeId);

    // Check occupancy limits
    if (occupancy.adults > roomType.occupancy.maxAdults) {
      return {
        available: false,
        reason: 'exceeds_max_occupancy',
      };
    }

    if (
      occupancy.children > roomType.occupancy.maxChildren ||
      occupancy.adults + occupancy.children > roomType.occupancy.maxTotal
    ) {
      return {
        available: false,
        reason: 'exceeds_max_occupancy',
      };
    }

    // Check availability for each date
    const availability = await this.getAvailability(
      propertyId,
      roomTypeId,
      dates
    );

    for (const record of availability) {
      if (record.available <= 0 || record.status === 'sold_out') {
        return {
          available: false,
          reason: 'no_inventory',
          date: record.date,
        };
      }
    }

    // Check minimum stay constraints
    const nights = this.countNights(dates);
    const ratePlans = await this.ratePlanService.findByRoomType(roomTypeId);

    for (const ratePlan of ratePlans) {
      if (ratePlan.active) {
        if (
          ratePlan.availability.minStay &&
          nights < ratePlan.availability.minStay
        ) {
          return {
            available: false,
            reason: 'below_minimum_stay',
            minStay: ratePlan.availability.minStay,
          };
        }

        if (
          ratePlan.availability.maxStay &&
          nights > ratePlan.availability.maxStay
        ) {
          return {
            available: false,
            reason: 'above_maximum_stay',
            maxStay: ratePlan.availability.maxStay,
          };
        }
      }
    }

    return { available: true };
  }

  async syncFromSupplier(
    propertyId: string,
    supplierPropertyCode: string,
    dateRange: DateRange
  ): Promise<void> {
    const property = await this.propertyService.getProperty(propertyId);

    // Fetch from supplier
    const adapter = this.supplierAdapterFactory.getAdapter(property.supplierId);
    const roomTypes = await this.roomTypeService.listRoomTypes(propertyId);

    for (const roomType of roomTypes) {
      const availability = await adapter.fetchAvailability(
        supplierPropertyCode,
        dateRange,
        { adults: 2 }
      );

      // Map and update
      const updates = availability
        .filter(a => a.roomTypeCode === roomType.code)
        .map(a => ({
          propertyId,
          roomTypeId: roomType.id,
          ratePlanId: a.ratePlanCode,
          date: a.date,
          available: a.available,
          total: a.total || a.available,
          price: a.price,
          status: a.available > 0 ? 'available' : 'sold_out',
        }));

      await this.updateAvailability(updates);
    }
  }

  private cacheKey(
    propertyId: string,
    roomTypeId: string,
    dates: DateRange,
    ratePlanId?: string
  ): string {
    const datesStr = `${dates.start.toISOString().split('T')[0]}_${dates.end.toISOString().split('T')[0]}`;
    return `availability:${propertyId}:${roomTypeId}:${ratePlanId || 'all'}:${datesStr}`;
  }

  private readonly CACHE_TTL = 300; // 5 minutes

  private async notifyAvailabilityChange(updates: AvailabilityUpdate[]): Promise<void> {
    // Publish to message queue for real-time updates
    await this.messageBus.publish('availability.changed', { updates });
  }
}
```

### Availability Forecast

```typescript
export class AvailabilityForecastService {
  async forecast(
    propertyId: string,
    roomTypeId: string,
    horizon: number = 90 // days
  ): Promise<AvailabilityForecast> {
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + horizon);

    const [availability, bookings, seasonality] = await Promise.all([
      this.availabilityService.getAvailability(
        propertyId,
        roomTypeId,
        { start: new Date(), end: endDate }
      ),
      this.bookingRepository.getPendingBookings(propertyId, roomTypeId),
      this.seasonalityService.getSeasonality(propertyId, roomTypeId),
    ]);

    const forecast: DailyForecast[] = [];
    const roomType = await this.roomTypeService.getRoomType(propertyId, roomTypeId);
    const totalRooms = await this.getTotalRooms(propertyId, roomTypeId);

    for (let i = 0; i < horizon; i++) {
      const date = this.addDays(new Date(), i);

      const availRecord = availability.find(a =>
        a.date.toISOString() === date.toISOString()
      );

      const pendingBookings = bookings
        .filter(b => this.isDateInRange(date, b.checkIn, b.checkOut))
        .reduce((sum, b) => sum + b.rooms, 0);

      const seasonalityFactor = this.getSeasonalityFactor(date, seasonality);

      const available = availRecord?.available ?? totalRooms;
      const utilization = (totalRooms - available) / totalRooms;
      const forecastedDemand = this.forecastDemand(
        utilization,
        seasonalityFactor,
        pendingBookings
      );

      forecast.push({
        date,
        available,
        total: totalRooms,
        utilization,
        forecastedDemand,
        seasonality: seasonalityFactor,
        confidence: this.calculateConfidence(date, i),
      });
    }

    return {
      propertyId,
      roomTypeId,
      horizon,
      forecast,
      generatedAt: new Date(),
    };
  }

  private forecastDemand(
    currentUtilization: number,
    seasonalityFactor: number,
    pendingBookings: number
  ): number {
    // Simple forecast based on utilization and seasonality
    const baseDemand = currentUtilization * seasonalityFactor;
    const bookingPressure = pendingBookings * 0.1;

    return Math.min(1, baseDemand + bookingPressure);
  }

  private calculateConfidence(date: Date, daysOut: number): number {
    // Confidence decreases with time
    return Math.max(0.5, 1 - (daysOut / 365) * 0.5);
  }
}
```

---

## Rate Plan Management

### Rate Plan CRUD

```typescript
export class RatePlanService {
  async createRatePlan(
    propertyId: string,
    roomTypeId: string,
    data: Omit<RatePlan, 'id' | 'propertyId' | 'roomTypeId' | 'createdAt' | 'updatedAt'>
  ): Promise<RatePlan> {
    // Validate room type
    const roomType = await this.roomTypeService.getRoomType(propertyId, roomTypeId);

    // Check for duplicate code
    const existing = await this.ratePlanRepository.findByCode(
      propertyId,
      data.code
    );

    if (existing) {
      throw new ConflictError('Rate plan code already exists');
    }

    // Validate rate plan
    await this.validateRatePlan(data);

    // Create
    const ratePlan = await this.ratePlanRepository.create({
      ...data,
      propertyId,
      roomTypeId,
      status: 'active',
    });

    // Index
    await this.searchService.indexRatePlan(ratePlan);

    return ratePlan;
  }

  async updateRatePlan(
    propertyId: string,
    ratePlanId: string,
    updates: Partial<RatePlan>
  ): Promise<RatePlan> {
    const ratePlan = await this.getRatePlan(propertyId, ratePlanId);

    // Validate updates
    if (updates.pricing || updates.constraints || updates.availability) {
      await this.validateRatePlan({
        ...ratePlan,
        ...updates,
      });
    }

    // Apply updates
    const updated = await this.ratePlanRepository.update(ratePlanId, {
      ...updates,
      updatedAt: new Date(),
    });

    // Clear pricing cache
    await this.pricingCache.invalidate(propertyId, ratePlanId);

    return updated;
  }

  async getRatePlan(
    propertyId: string,
    ratePlanId: string
  ): Promise<RatePlan> {
    const ratePlan = await this.ratePlanRepository.findById(ratePlanId);

    if (!ratePlan || ratePlan.propertyId !== propertyId) {
      throw new NotFoundError('Rate plan not found');
    }

    return ratePlan;
  }

  async listRatePlans(
    propertyId: string,
    roomTypeId: string,
    options: ListOptions = {}
  ): Promise<RatePlan[]> {
    const query = this.ratePlanRepository
      .query()
      .where('propertyId', propertyId)
      .where('roomTypeId', roomTypeId);

    if (options.activeOnly) {
      query.where('status', 'active');
    }

    if (options.bookable?.start && options.bookable?.end) {
      query.where('constraints.bookableStart', '<=', options.bookable.start)
        .where('constraints.bookableEnd', '>=', options.bookable.end);
    }

    return query.getMany();
  }

  private async validateRatePlan(data: Partial<RatePlan>): Promise<void> {
    // Pricing validation
    if (data.pricing?.type === 'static') {
      if (!data.pricing.baseRate?.amount) {
        throw new ValidationError('Base rate required for static pricing');
      }
    }

    // Availability constraints
    if (data.availability) {
      if (
        data.availability.minStay &&
        data.availability.maxStay &&
        data.availability.minStay > data.availability.maxStay
      ) {
        throw new ValidationError('Min stay cannot exceed max stay');
      }

      if (
        data.availability.availableDays &&
        data.availability.availableDays.length === 0
      ) {
        throw new ValidationError('At least one available day required');
      }
    }

    // Cancellation policy validation
    if (data.constraints?.cancellationPolicy) {
      this.validateCancellationPolicy(data.constraints.cancellationPolicy);
    }
  }

  private validateCancellationPolicy(policy: CancellationPolicy): void {
    if (policy.deadline) {
      if (policy.deadline.amount <= 0) {
        throw new ValidationError('Deadline amount must be positive');
      }

      if (
        policy.deadline.unit !== 'hours' &&
        policy.deadline.unit !== 'days'
      ) {
        throw new ValidationError('Invalid deadline unit');
      }
    }

    if (policy.penalty) {
      if (
        policy.penalty.type === 'nights' &&
        (!policy.penalty.nights || policy.penalty.nights < 1)
      ) {
        throw new ValidationError('Penalty nights must be at least 1');
      }

      if (
        (policy.penalty.type === 'percentage' || policy.penalty.type === 'fixed') &&
        (!policy.penalty.amount || policy.penalty.amount <= 0)
      ) {
        throw new ValidationError('Penalty amount must be positive');
      }
    }
  }
}
```

### Rate Plan Inheritance

```typescript
export class RatePlanHierarchyService {
  async createDerivedRatePlan(
    parentRatePlanId: string,
    overrides: Partial<RatePlan>
  ): Promise<RatePlan> {
    const parent = await this.ratePlanRepository.findById(parentRatePlanId);

    if (!parent) {
      throw new NotFoundError('Parent rate plan not found');
    }

    // Create derived rate plan
    const derived: Omit<RatePlan, 'id' | 'createdAt' | 'updatedAt'> = {
      propertyId: parent.propertyId,
      roomTypeId: parent.roomTypeId,
      code: overrides.code || `${parent.code}_derived`,
      name: overrides.name || { ...parent.name },
      description: overrides.description || parent.description,

      // Inherit from parent, override with provided values
      pricing: { ...parent.pricing, ...overrides.pricing },
      availability: { ...parent.availability, ...overrides.availability },
      constraints: { ...parent.constraints, ...overrides.constraints },
      promotions: overrides.promotions || parent.promotions,

      status: 'active',
    };

    return await this.ratePlanRepository.create(derived);
  }

  async syncDerivedRatePlans(parentRatePlanId: string): Promise<void> {
    const derived = await this.ratePlanRepository.findByParent(parentPlanId);

    for (const ratePlan of derived) {
      // Re-apply inheritance
      await this.applyInheritance(ratePlan);
    }
  }

  private async applyInheritance(ratePlan: RatePlan): Promise<void> {
    const parent = await this.ratePlanRepository.findById(ratePlan.parentId);

    if (!parent) return;

    // Merge parent values
    const merged: Partial<RatePlan> = {
      pricing: this.deepMerge(parent.pricing, ratePlan.pricing),
      availability: this.deepMerge(parent.availability, ratePlan.availability),
      constraints: this.deepMerge(parent.constraints, ratePlan.constraints),
    };

    await this.ratePlanRepository.update(ratePlan.id, merged);
  }

  private deepMerge<T>(parent: T, child: Partial<T>): T {
    const result = { ...parent };

    for (const key in child) {
      if (typeof child[key] === 'object' && !Array.isArray(child[key])) {
        result[key] = { ...parent[key], ...child[key] };
      } else if (child[key] !== undefined) {
        result[key] = child[key];
      }
    }

    return result;
  }
}
```

---

## Pricing Engine

### Price Calculation

```typescript
export class AccommodationPricingEngine {
  async calculatePrice(
    request: PricingRequest
  ): Promise<PricingResult> {
    const {
      propertyId,
      roomTypeId,
      dates,
      occupancy,
      ratePlanCode,
      promoCode,
    } = request;

    // 1. Get applicable rate plans
    let ratePlans = await this.ratePlanService.listRatePlans(
      propertyId,
      roomTypeId,
      { activeOnly: true, bookable: dates }
    );

    if (ratePlanCode) {
      ratePlans = ratePlans.filter(rp => rp.code === ratePlanCode);
    }

    if (ratePlans.length === 0) {
      throw new NotFoundError('No applicable rate plans found');
    }

    // 2. Get availability
    const availability = await this.availabilityService.getAvailability(
      propertyId,
      roomTypeId,
      dates
    );

    // 3. Calculate base price for each rate plan
    const prices = await Promise.all(
      ratePlans.map(async ratePlan => {
        const basePrice = await this.calculateBasePrice(
          ratePlan,
          availability,
          dates
        );

        const totalPrice = await this.applyPricingRules(
          basePrice,
          ratePlan,
          request
        );

        return {
          ratePlanId: ratePlan.id,
          ratePlanCode: ratePlan.code,
          ratePlanName: ratePlanName.name,
          basePrice,
          totalPrice,
        };
      })
    );

    // 4. Apply promotions
    let finalPrices = prices;
    if (promoCode) {
      finalPrices = await this.applyPromoCode(prices, promoCode, request);
    }

    // 5. Sort by total price
    finalPrices.sort((a, b) => a.totalPrice.total - b.totalPrice.total);

    return {
      propertyId,
      roomTypeId,
      dates,
      prices: finalPrices,
      currency: finalPrices[0].totalPrice.currency,
    };
  }

  private async calculateBasePrice(
    ratePlan: RatePlan,
    availability: Availability[],
    dates: DateRange
  ): Promise<DailyPrice[]> {
    const dailyPrices: DailyPrice[] = [];
    const nights = this.eachDate(dates);

    for (const date of nights) {
      const avail = availability.find(
        a => a.date.toISOString() === date.toISOString()
      );

      let amount = 0;

      if (ratePlan.pricing.type === 'static') {
        amount = ratePlan.pricing.baseRate.amount;
      } else if (ratePlan.pricing.type === 'dynamic') {
        amount = avail?.price?.amount ?? ratePlan.pricing.baseRate.amount;
      }

      dailyPrices.push({
        date,
        amount,
        currency: ratePlan.pricing.baseRate.currency,
      });
    }

    return dailyPrices;
  }

  private async applyPricingRules(
    basePrice: DailyPrice[],
    ratePlan: RatePlan,
    request: PricingRequest
  ): Promise<TotalPrice> {
    let total = 0;
    const taxes: Tax[] = [];
    const fees: Fee[] = [];

    // 1. Calculate room total
    for (const day of basePrice) {
      total += day.amount;
    }

    // 2. Add occupancy-based adjustment
    const occupancyAdjustment = this.calculateOccupancyAdjustment(
      request.occupancy,
      ratePlan
    );
    total += occupancyAdjustment;

    // 3. Add length-of-stay adjustment
    const losAdjustment = this.calculateLOSAdjustment(
      basePrice.length,
      ratePlan
    );
    total += losAdjustment;

    // 4. Calculate taxes
    if (ratePlan.pricing.tax) {
      const taxAmount = this.calculateTax(total, ratePlan.pricing.tax);
      taxes.push({
        name: 'Tax',
        amount: taxAmount,
        currency: basePrice[0].currency,
        inclusive: ratePlan.pricing.tax.inclusive,
      });

      if (!ratePlan.pricing.tax.inclusive) {
        total += taxAmount;
      }
    }

    // 5. Add fees
    if (ratePlan.pricing.fees) {
      for (const fee of ratePlan.pricing.fees) {
        const feeAmount = this.calculateFee(total, basePrice.length, fee);
        fees.push({
          name: fee.name.en,
          amount: feeAmount,
          currency: basePrice[0].currency,
          type: fee.type,
          mandatory: fee.mandatory,
          payableAt: fee.payableAt,
        });

        if (fee.mandatory) {
          total += feeAmount;
        }
      }
    }

    return {
      roomTotal: basePrice.reduce((sum, d) => sum + d.amount, 0),
      adjustments: occupancyAdjustment + losAdjustment,
      taxes: taxes.reduce((sum, t) => sum + (t.inclusive ? 0 : t.amount), 0),
      fees: fees.filter(f => f.mandatory).reduce((sum, f) => sum + f.amount, 0),
      total,
      currency: basePrice[0].currency,
      breakdown: {
        daily: basePrice,
        taxes,
        fees,
      },
    };
  }

  private calculateOccupancyAdjustment(
    occupancy: Occupancy,
    ratePlan: RatePlan
  ): number {
    // Extra person charges
    const roomType = ratePlan; // Would need to fetch full room type
    const baseOccupancy = 2; // Standard occupancy

    if (occupancy.adults > baseOccupancy) {
      const extraAdults = occupancy.adults - baseOccupancy;
      return extraAdults * 20; // $20 per extra adult
    }

    if (occupancy.children > 0) {
      return occupancy.children * 10; // $10 per child
    }

    return 0;
  }

  private calculateLOSAdjustment(nights: number, ratePlan: RatePlan): number {
    // Length-of-stay discounts
    if (nights >= 7) {
      return -50; // $50 off for week+ stays
    } else if (nights >= 4) {
      return -20; // $20 off for 4+ nights
    } else if (nights === 1) {
      return 15; // $15 premium for single night
    }

    return 0;
  }

  private calculateTax(total: number, tax: TaxInfo): number {
    if (tax.percentage) {
      return (total * tax.percentage) / 100;
    }
    return tax.amount;
  }

  private calculateFee(
    total: number,
    nights: number,
    fee: FeeInfo
  ): number {
    switch (fee.type) {
      case 'fixed':
        return fee.amount.amount;
      case 'percentage':
        return (total * fee.amount.amount) / 100;
      case 'per_night':
        return fee.amount.amount * nights;
      case 'per_stay':
        return fee.amount.amount;
    }
  }

  private async applyPromoCode(
    prices: RatePlanPrice[],
    promoCode: string,
    request: PricingRequest
  ): Promise<RatePlanPrice[]> {
    const promo = await this.promotionService.validateCode(promoCode);

    if (!promo || !promo.applicableTo(request)) {
      return prices;
    }

    return prices.map(price => {
      const discount = this.calculatePromoDiscount(
        price.totalPrice.total,
        promo
      );

      return {
        ...price,
        totalPrice: {
          ...price.totalPrice,
          total: price.totalPrice.total - discount,
          discounts: [
            ...(price.totalPrice.discounts || []),
            {
              name: promo.name,
              amount: discount,
              type: promo.discount.type,
            },
          ],
        },
      };
    });
  }

  private calculatePromoDiscount(total: number, promo: Promotion): number {
    switch (promo.discount.type) {
      case 'percentage':
        return (total * promo.discount.amount) / 100;
      case 'fixed':
        return Math.min(promo.discount.amount, total);
      case 'nights_free':
        // Would need to calculate nightly rate
        return total * 0.1; // Simplified
    }
  }
}
```

---

## Dynamic Pricing

### Dynamic Pricing Engine

```typescript
export class DynamicPricingService {
  async calculateDynamicPrice(
    propertyId: string,
    roomTypeId: string,
    dates: DateRange,
    context: PricingContext
  ): Promise<DynamicPriceResult> {
    const [basePrice, factors] = await Promise.all([
      this.getBasePrice(propertyId, roomTypeId, dates),
      this.getPricingFactors(propertyId, roomTypeId, context),
    ]);

    let multiplier = 1;

    // Apply each factor
    for (const factor of factors) {
      multiplier *= this.applyFactor(factor, context);
    }

    // Calculate final price
    const finalPrice = basePrice * multiplier;

    return {
      basePrice,
      multiplier,
      finalPrice,
      factors,
      currency: context.currency,
    };
  }

  private async getPricingFactors(
    propertyId: string,
    roomTypeId: string,
    context: PricingContext
  ): Promise<PricingFactor[]> {
    const factors: PricingFactor[] = [];

    // 1. Demand factor
    const demand = await this.getDemandFactor(propertyId, roomTypeId, context);
    factors.push(demand);

    // 2. Seasonality factor
    const seasonality = await this.getSeasonalityFactor(propertyId, context);
    factors.push(seasonality);

    // 3. Lead time factor
    const leadTime = this.getLeadTimeFactor(context);
    factors.push(leadTime);

    // 4. Occupancy factor
    const occupancy = await this.getOccupancyFactor(propertyId, roomTypeId);
    factors.push(occupancy);

    // 5. Competitor pricing factor
    const competitor = await this.getCompetitorFactor(propertyId, context);
    factors.push(competitor);

    // 6. Event pricing factor
    const events = await this.getEventFactor(propertyId, context);
    factors.push(events);

    return factors;
  }

  private async getDemandFactor(
    propertyId: string,
    roomTypeId: string,
    context: PricingContext
  ): Promise<PricingFactor> {
    // Get recent booking rate
    const recentBookings = await this.bookingRepository.getRecentBookings(
      propertyId,
      roomTypeId,
      7 // days
    );

    const totalRooms = await this.getTotalRooms(propertyId, roomTypeId);
    const bookingRate = recentBookings / totalRooms;

    let multiplier = 1;
    if (bookingRate > 0.8) multiplier = 1.2; // High demand
    else if (bookingRate > 0.6) multiplier = 1.1;
    else if (bookingRate < 0.3) multiplier = 0.9; // Low demand

    return {
      name: 'demand',
      value: bookingRate,
      multiplier,
      weight: 0.3,
    };
  }

  private async getSeasonalityFactor(
    propertyId: string,
    context: PricingContext
  ): Promise<PricingFactor> {
    const seasonality = await this.seasonalityService.getFactor(
      propertyId,
      context.dates.start
    );

    return {
      name: 'seasonality',
      value: seasonality.factor,
      multiplier: seasonality.factor,
      weight: 0.2,
    };
  }

  private getLeadTimeFactor(context: PricingContext): PricingFactor {
    const daysUntilCheckIn = this.daysBetween(
      new Date(),
      context.dates.start
    );

    let multiplier = 1;
    if (daysUntilCheckIn <= 3) multiplier = 1.15; // Last minute premium
    else if (daysUntilCheckIn <= 7) multiplier = 1.1;
    else if (daysUntilCheckIn >= 30) multiplier = 0.95; // Early bird discount
    else if (daysUntilCheckIn >= 60) multiplier = 0.9;

    return {
      name: 'lead_time',
      value: daysUntilCheckIn,
      multiplier,
      weight: 0.15,
    };
  }

  private async getOccupancyFactor(
    propertyId: string,
    roomTypeId: string
  ): Promise<PricingFactor> {
    const occupancy = await this.availabilityService.getCurrentOccupancy(
      propertyId,
      roomTypeId
    );

    let multiplier = 1;
    if (occupancy > 0.9) multiplier = 1.25; // Nearly full
    else if (occupancy > 0.7) multiplier = 1.15;
    else if (occupancy < 0.3) multiplier = 0.85; // Plenty available

    return {
      name: 'occupancy',
      value: occupancy,
      multiplier,
      weight: 0.25,
    };
  }

  private applyFactor(factor: PricingFactor, context: PricingContext): number {
    // Apply weighted factor
    return 1 + (factor.multiplier - 1) * factor.weight;
  }
}
```

---

## Promotions

### Promotion Management

```typescript
export class PromotionService {
  async createPromotion(
    data: Omit<Promotion, 'id' | 'createdAt' | 'updatedAt'>
  ): Promise<Promotion> {
    // Validate promotion
    await this.validatePromotion(data);

    // Check for duplicate code
    if (data.code) {
      const existing = await this.promotionRepository.findByCode(data.code);
      if (existing) {
        throw new ConflictError('Promotion code already exists');
      }
    }

    return await this.promotionRepository.create(data);
  }

  async validateCode(
    code: string,
    context?: ValidationContext
  ): Promise<Promotion | null> {
    const promo = await this.promotionRepository.findByCode(code);

    if (!promo) {
      return null;
    }

    // Check if active
    const now = new Date();
    if (promo.startsAt && now < promo.startsAt) {
      return null;
    }

    if (promo.endsAt && now > promo.endsAt) {
      return null;
    }

    // Check usage limits
    if (promo.maxUses && promo.usedCount >= promo.maxUses) {
      return null;
    }

    // Check context-specific conditions
    if (context && !promo.applicableTo(context)) {
      return null;
    }

    return promo;
  }

  async applyPromotion(
    price: number,
    promotion: Promotion
  ): number {
    switch (promotion.discount.type) {
      case 'percentage':
        return (price * promotion.discount.amount) / 100;

      case 'fixed':
        return Math.min(promotion.discount.amount, price);

      case 'nights_free':
        // Requires calculation based on nightly rate
        // Simplified: 10% off
        return price * 0.1;
    }
  }

  private async validatePromotion(data: Partial<Promotion>): Promise<void> {
    // Discount validation
    if (!data.discount) {
      throw new ValidationError('Discount details required');
    }

    if (
      data.discount.type === 'percentage' &&
      (data.discount.amount <= 0 || data.discount.amount > 100)
    ) {
      throw new ValidationError('Percentage discount must be between 0-100');
    }

    if (data.discount.type === 'fixed' && data.discount.amount <= 0) {
      throw new ValidationError('Fixed discount must be positive');
    }

    // Date validation
    if (data.startsAt && data.endsAt && data.startsAt > data.endsAt) {
      throw new ValidationError('End date must be after start date');
    }

    // Conditions validation
    if (data.conditions?.minStay && data.conditions.minStay < 1) {
      throw new ValidationError('Minimum stay must be at least 1 night');
    }
  }
}
```

---

## API Endpoints

### Room Type Endpoints

```
GET    /accommodations/properties/:propertyId/room-types
POST   /accommodations/properties/:propertyId/room-types
GET    /accommodations/room-types/:roomTypeId
PATCH  /accommodations/room-types/:roomTypeId
DELETE /accommodations/room-types/:roomTypeId
```

### Availability Endpoints

```
POST   /accommodations/availability/check
GET    /accommodations/properties/:propertyId/availability
GET    /accommodations/room-types/:roomTypeId/availability
POST   /accommodations/room-types/:roomTypeId/availability/sync
```

### Rate Plan Endpoints

```
GET    /accommodations/properties/:propertyId/rate-plans
POST   /accommodations/properties/:propertyId/rate-plans
GET    /accommodations/rate-plans/:ratePlanId
PATCH  /accommodations/rate-plans/:ratePlanId
DELETE /accommodations/rate-plans/:ratePlanId
```

### Pricing Endpoints

```
POST   /accommodations/pricing/calculate
POST   /accommodations/pricing/dynamic
POST   /accommodations/promotions/validate
```

---

**Next:** [Search & Discovery](./ACCOMMODATION_CATALOG_04_SEARCH.md) — Filtering, sorting, and recommendations
