# Accommodation Catalog 05: Booking Integration

> Reservations, confirmations, modifications, and cancellations

---

## Overview

This document details the booking integration subsystem for accommodations, covering the complete reservation lifecycle from creation and confirmation through modifications and cancellations. This subsystem connects the accommodation catalog to the booking engine and coordinates with external suppliers.

**Key Capabilities:**
- Reservation creation and confirmation
- Real-time availability holding
- Booking modification support
- Cancellation processing
- Supplier coordination
- Booking status tracking

---

## Table of Contents

1. [Reservation Flow](#reservation-flow)
2. [Availability Holding](#availability-holding)
3. [Booking Creation](#booking-creation)
4. [Booking Confirmation](#booking-confirmation)
5. [Modification Handling](#modification-handling)
6. [Cancellation Processing](#cancellation-processing)
7. [Supplier Coordination](#supplier-coordination)

---

## Reservation Flow

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ACCOMMODATION BOOKING FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CUSTOMER REQUEST                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   SEARCH    │───▶│   SELECT    │───▶│   REQUEST   │                    │
│  │  STAY DATES │    │  PROPERTY   │    │  TO BOOK    │                    │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                    │
│                                              │                             │
│  AVAILABILITY CHECK                          │                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────▼─────┐                    │
│  │ CHECK       │───▶│ HOLD        │───▶│ CONFIRM   │                    │
│  │ INVENTORY   │    │ AVAILABILITY│    │ BOOKING   │                    │
│  └─────────────┘    └──────┬──────┘    └─────┬─────┘                    │
│                            │                   │                          │
│                            │                   ▼                          │
│                            │            SUPPLIER BOOKING                 │
│                            │            ┌─────────────┐                   │
│                            │            │ CREATE     │                   │
│                            │            │ RESERVATION│                   │
│                            │            └──────┬──────┘                   │
│                            │                   │                          │
│                            │            ┌──────▼──────┐                   │
│                            │            │ GET CONFIRM │                   │
│                            │            │ & REFERENCE│                   │
│                            │            └──────┬──────┘                   │
│                            │                   │                          │
│                            ▼                   ▼                          │
│                     ┌─────────────────────────────┐                     │
│                     │      BOOKING CONFIRMED      │                     │
│                     │  - Send confirmation email  │                     │
│                     │  - Update inventory         │                     │
│                     │  - Trigger notifications    │                     │
│                     └─────────────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### State Machine

```typescript
type AccommodationBookingStatus =
  | 'pending'        // Initial state
  | 'holding'        // Availability held
  | 'confirming'     // Awaiting supplier confirmation
  | 'confirmed'      // Booking confirmed
  | 'modified'       // Booking modified
  | 'cancelled'      // Booking cancelled
  | 'rejected'       // Booking rejected
  | 'failed';        // Booking failed

interface AccommodationBooking {
  id: string;
  bookingId: string; // Parent booking ID
  propertyId: string;
  roomTypeId: string;
  ratePlanId: string;

  // Stay details
  checkIn: Date;
  checkOut: Date;
  nights: number;
  rooms: number;

  // Guest details
  guestDetails: GuestDetails;

  // Pricing
  pricing: AccommodationPricing;

  // Supplier info
  supplierId: string;
  supplierReference?: string;
  supplierStatus?: string;

  // Status
  status: AccommodationBookingStatus;

  // Timestamps
  createdAt: Date;
  confirmedAt?: Date;
  cancelledAt?: Date;
  modifiedAt?: Date;
}
```

---

## Availability Holding

### Hold Service

```typescript
export class AvailabilityHoldService {
  private readonly HOLD_TTL = 15 * 60; // 15 minutes

  async createHold(
    propertyId: string,
    roomTypeId: string,
    dates: DateRange,
    ratePlanId: string,
    quantity: number = 1
  ): Promise<HoldToken> {
    // Check availability first
    const available = await this.availabilityService.checkAvailability(
      propertyId,
      roomTypeId,
      dates,
      { adults: 2, children: 0 }
    );

    if (!available.available) {
      throw new ConflictError('No availability for requested dates');
    }

    // Generate hold token
    const token = this.generateToken();

    // Store hold in Redis
    const hold: AvailabilityHold = {
      id: crypto.randomUUID(),
      token,
      propertyId,
      roomTypeId,
      ratePlanId,
      dates,
      quantity,
      expiresAt: new Date(Date.now() + this.HOLD_TTL * 1000),
      createdAt: new Date(),
    };

    await this.redis.setex(
      `hold:${token}`,
      this.HOLD_TTL,
      JSON.stringify(hold)
    );

    // Temporarily reduce available inventory
    await this.temporarilyReduceAvailability(hold);

    return {
      token,
      expiresAt: hold.expiresAt,
    };
  }

  async getHold(token: string): Promise<AvailabilityHold | null> {
    const data = await this.redis.get(`hold:${token}`);

    if (!data) {
      return null;
    }

    return JSON.parse(data);
  }

  async extendHold(token: string, additionalMinutes: number): Promise<void> {
    const hold = await this.getHold(token);

    if (!hold) {
      throw new NotFoundError('Hold not found');
    }

    if (hold.expiresAt < new Date()) {
      throw new ValidationError('Hold has expired');
    }

    // Extend expiry
    hold.expiresAt = new Date(Date.now() + additionalMinutes * 60 * 1000);

    await this.redis.setex(
      `hold:${token}`,
      additionalMinutes * 60,
      JSON.stringify(hold)
    );
  }

  async releaseHold(token: string): Promise<void> {
    const hold = await this.getHold(token);

    if (!hold) {
      return; // Already expired or released
    }

    // Restore availability
    await this.restoreAvailability(hold);

    // Delete hold
    await this.redis.del(`hold:${token}`);
  }

  async consumeHold(token: string): Promise<AvailabilityHold> {
    const hold = await this.getHold(token);

    if (!hold) {
      throw new NotFoundError('Hold not found or expired');
    }

    // Delete hold (don't restore - consumed by booking)
    await this.redis.del(`hold:${token}`);

    return hold;
  }

  private async temporarilyReduceAvailability(hold: AvailabilityHold): Promise<void> {
    const dates = this.eachDate(hold.dates);

    for (const date of dates) {
      const key = `availability:${hold.propertyId}:${hold.roomTypeId}:${hold.ratePlanId}:${date.toISOString().split('T')[0]}`;

      await this.redis.decrby(key, hold.quantity);
    }
  }

  private async restoreAvailability(hold: AvailabilityHold): Promise<void> {
    const dates = this.eachDate(hold.dates);

    for (const date of dates) {
      const key = `availability:${hold.propertyId}:${hold.roomTypeId}:${hold.ratePlanId}:${date.toISOString().split('T')[0]}`;

      await this.redis.incrby(key, hold.quantity);
    }
  }

  private generateToken(): string {
    return crypto.randomBytes(16).toString('base64url');
  }

  private eachDate(range: DateRange): Date[] {
    const dates: Date[] = [];
    const current = new Date(range.start);

    while (current < range.end) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return dates;
  }
}
```

---

## Booking Creation

### Booking Service

```typescript
export class AccommodationBookingService {
  async createBooking(
    request: AccommodationBookingRequest
  ): Promise<AccommodationBooking> {
    // 1. Validate request
    await this.validateRequest(request);

    // 2. Consume hold (if provided)
    let hold: AvailabilityHold | null = null;
    if (request.holdToken) {
      hold = await this.holdService.consumeHold(request.holdToken);
    } else {
      // Create hold inline
      const holdToken = await this.holdService.createHold(
        request.propertyId,
        request.roomTypeId,
        { start: request.checkIn, end: request.checkOut },
        request.ratePlanId,
        request.rooms
      );
      hold = await this.holdService.consumeHold(holdToken.token);
    }

    // 3. Calculate pricing
    const pricing = await this.pricingService.calculatePrice({
      propertyId: request.propertyId,
      roomTypeId: request.roomTypeId,
      dates: { start: request.checkIn, end: request.checkOut },
      occupancy: { adults: request.adults, children: request.children },
      ratePlanCode: request.ratePlanId,
      promoCode: request.promoCode,
    });

    // 4. Create booking record
    const booking: AccommodationBooking = {
      id: crypto.randomUUID(),
      bookingId: request.bookingId,
      propertyId: request.propertyId,
      roomTypeId: request.roomTypeId,
      ratePlanId: request.ratePlanId,
      checkIn: request.checkIn,
      checkOut: request.checkOut,
      nights: this.countNights(request.checkIn, request.checkOut),
      rooms: request.rooms,
      guestDetails: request.guestDetails,
      pricing: pricing.prices[0].totalPrice,
      supplierId: (await this.getProperty(request.propertyId)).supplierId,
      status: 'pending',
      createdAt: new Date(),
    };

    await this.bookingRepository.create(booking);

    // 5. Confirm with supplier
    await this.confirmWithSupplier(booking);

    return booking;
  }

  private async confirmWithSupplier(
    booking: AccommodationBooking
  ): Promise<void> {
    try {
      // Update status
      await this.updateStatus(booking.id, 'confirming');

      // Get supplier adapter
      const property = await this.getProperty(booking.propertyId);
      const adapter = this.supplierAdapterFactory.getAdapter(property.supplierId);

      // Create supplier reservation
      const supplierBooking = await adapter.createReservation({
        propertyCode: property.supplierCode,
        roomTypeCode: (await this.getRoomType(booking.roomTypeId)).code,
        ratePlanCode: (await this.getRatePlan(booking.ratePlanId)).code,
        checkIn: booking.checkIn,
        checkOut: booking.checkOut,
        guests: {
          adults: booking.guestDetails.adults,
          children: booking.guestDetails.children,
        },
        guestName: `${booking.guestDetails.firstName} ${booking.guestDetails.lastName}`,
        guestEmail: booking.guestDetails.email,
        guestPhone: booking.guestDetails.phone,
        specialRequests: booking.guestDetails.specialRequests,
      });

      // Update booking with supplier reference
      await this.bookingRepository.update(booking.id, {
        supplierReference: supplierBooking.referenceNumber,
        supplierStatus: supplierBooking.status,
        status: 'confirmed',
        confirmedAt: new Date(),
      });

      // Trigger confirmation workflow
      await this.confirmationService.bookingConfirmed(booking);

    } catch (error) {
      // Handle failure
      await this.updateStatus(booking.id, 'failed');

      // Release hold if we had one
      // (Note: already consumed, but need to restore inventory)
      await this.restoreInventory(booking);

      throw new BookingError('Failed to confirm booking with supplier', error);
    }
  }

  private async validateRequest(request: AccommodationBookingRequest): Promise<void> {
    // Validate dates
    if (request.checkIn >= request.checkOut) {
      throw new ValidationError('Check-out must be after check-in');
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (request.checkIn < today) {
      throw new ValidationError('Check-in cannot be in the past');
    }

    // Validate occupancy
    const roomType = await this.roomTypeService.getRoomType(
      request.propertyId,
      request.roomTypeId
    );

    if (request.adults < roomType.occupancy.minAdults || 0) {
      throw new ValidationError(
        `Minimum ${roomType.occupancy.minAdults || 1} adults required`
      );
    }

    if (request.adults > roomType.occupancy.maxAdults) {
      throw new ValidationError(
        `Maximum ${roomType.occupancy.maxAdults} adults allowed`
      );
    }

    const totalGuests = request.adults + (request.children || 0);
    if (totalGuests > roomType.occupancy.maxTotal) {
      throw new ValidationError(
        `Maximum ${roomType.occupancy.maxTotal} guests allowed`
      );
    }

    // Validate rate plan
    const ratePlan = await this.ratePlanService.getRatePlan(
      request.propertyId,
      request.ratePlanId
    );

    if (ratePlan.status !== 'active') {
      throw new ValidationError('Rate plan is not available');
    }

    // Check if bookable
    if (ratePlan.constraints.bookableStart || ratePlan.constraints.bookableEnd) {
      const checkIn = request.checkIn;

      if (
        ratePlan.constraints.bookableStart &&
        checkIn < ratePlan.constraints.bookableStart
      ) {
        throw new ValidationError('Booking is before rate plan bookable period');
      }

      if (
        ratePlan.constraints.bookableEnd &&
        checkIn > ratePlan.constraints.bookableEnd
      ) {
        throw new ValidationError('Booking is after rate plan bookable period');
      }
    }
  }

  private async restoreInventory(booking: AccommodationBooking): Promise<void> {
    const dates = this.eachDate({ start: booking.checkIn, end: booking.checkOut });

    for (const date of dates) {
      await this.availabilityService.updateAvailability([
        {
          propertyId: booking.propertyId,
          roomTypeId: booking.roomTypeId,
          ratePlanId: booking.ratePlanId,
          date,
          delta: booking.rooms,
        },
      ]);
    }
  }

  private async updateStatus(
    bookingId: string,
    status: AccommodationBookingStatus
  ): Promise<void> {
    await this.bookingRepository.update(bookingId, { status });
  }

  private async getProperty(propertyId: string): Promise<Property> {
    return this.propertyService.getProperty(propertyId);
  }

  private async getRoomType(roomTypeId: string): Promise<RoomType> {
    return this.roomTypeRepository.findById(roomTypeId);
  }

  private async getRatePlan(ratePlanId: string): Promise<RatePlan> {
    return this.ratePlanRepository.findById(ratePlanId);
  }

  private countNights(checkIn: Date, checkOut: Date): number {
    return Math.ceil(
      (checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24)
    );
  }

  private eachDate(range: DateRange): Date[] {
    const dates: Date[] = [];
    const current = new Date(range.start);

    while (current < range.end) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return dates;
  }
}
```

---

## Booking Confirmation

### Confirmation Service

```typescript
export class BookingConfirmationService {
  async bookingConfirmed(booking: AccommodationBooking): Promise<void> {
    // 1. Update inventory
    await this.updateInventory(booking);

    // 2. Generate confirmation documents
    const documents = await this.generateDocuments(booking);

    // 3. Send notifications
    await this.sendConfirmations(booking, documents);

    // 4. Update search index availability
    await this.updateSearchIndex(booking);

    // 5. Trigger post-booking workflows
    await this.triggerPostBookingWorkflows(booking);
  }

  private async updateInventory(booking: AccommodationBooking): Promise<void> {
    const dates = this.eachDate({ start: booking.checkIn, end: booking.checkOut });

    const updates: AvailabilityUpdate[] = [];

    for (const date of dates) {
      updates.push({
        propertyId: booking.propertyId,
        roomTypeId: booking.roomTypeId,
        ratePlanId: booking.ratePlanId,
        date,
        delta: -booking.rooms, // Reduce available
      });
    }

    await this.availabilityService.updateAvailability(updates);
  }

  private async generateDocuments(
    booking: AccommodationBooking
  ): Promise<BookingDocuments> {
    const [property, roomType] = await Promise.all([
      this.propertyService.getProperty(booking.propertyId),
      this.roomTypeService.getRoomType(booking.propertyId, booking.roomTypeId),
    ]);

    return {
      voucher: await this.documentService.generateVoucher({
        booking,
        property,
        roomType,
      }),
      invoice: await this.documentService.generateInvoice({
        booking,
        property,
      }),
      itinerary: await this.documentService.generateItinerary({
        booking,
        property,
      }),
    };
  }

  private async sendConfirmations(
    booking: AccommodationBooking,
    documents: BookingDocuments
  ): Promise<void> {
    // Email confirmation
    await this.emailService.send({
      to: booking.guestDetails.email,
      template: 'booking_confirmed',
      data: {
        booking,
        documents,
        property: await this.getProperty(booking.propertyId),
      },
      attachments: [
        {
          filename: 'voucher.pdf',
          content: documents.voucher,
        },
        {
          filename: 'invoice.pdf',
          content: documents.invoice,
        },
      ],
    });

    // SMS confirmation
    if (booking.guestDetails.phone) {
      await this.smsService.send({
        to: booking.guestDetails.phone,
        template: 'booking_confirmed_sms',
        data: {
          bookingReference: booking.bookingId,
          propertyName: (await this.getProperty(booking.propertyId)).name.en,
          checkIn: booking.checkIn,
          checkOut: booking.checkOut,
        },
      });
    }

    // Agency notification
    await this.notificationService.send({
      type: 'booking_confirmed',
      channel: 'agency',
      data: {
        bookingId: booking.bookingId,
        propertyId: booking.propertyId,
        value: booking.pricing.total,
      },
    });
  }

  private async triggerPostBookingWorkflows(
    booking: AccommodationBooking
  ): Promise<void> {
    // Schedule check-in reminder
    await this.schedulerService.schedule({
      job: 'check_in_reminder',
      at: this.addDays(booking.checkIn, -2),
      data: { bookingId: booking.id },
    });

    // Schedule post-stay review request
    await this.schedulerService.schedule({
      job: 'review_request',
      at: this.addDays(booking.checkOut, 1),
      data: { bookingId: booking.id },
    });

    // Update user preferences based on booking
    await this.updateUserPreferences(booking);
  }

  private async updateUserPreferences(
    booking: AccommodationBooking
  ): Promise<void> {
    // Update property type preferences
    const property = await this.getProperty(booking.propertyId);
    const userId = booking.guestDetails.userId;

    if (userId) {
      await this.userPreferenceService.recordBooking(userId, {
        propertyType: property.type,
        amenities: property.amenities.map(a => a.id),
        location: property.location,
        priceRange: booking.pricing.total,
      });
    }
  }

  private addDays(date: Date, days: number): Date {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  }

  private async getProperty(propertyId: string): Promise<Property> {
    return this.propertyService.getProperty(propertyId);
  }

  private eachDate(range: DateRange): Date[] {
    const dates: Date[] = [];
    const current = new Date(range.start);

    while (current < range.end) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return dates;
  }
}
```

---

## Modification Handling

### Modification Service

```typescript
export class BookingModificationService {
  async modifyBooking(
    bookingId: string,
    modifications: BookingModifications
  ): Promise<AccommodationBooking> {
    const booking = await this.getBooking(bookingId);

    // 1. Validate modification request
    await this.validateModifications(booking, modifications);

    // 2. Calculate price difference
    const pricing = await this.calculateModifiedPrice(booking, modifications);

    // 3. Create new booking if dates changed
    if (modifications.checkIn || modifications.checkOut) {
      return await this.createNewBookingForDates(booking, modifications);
    }

    // 4. Modify existing booking
    const modified = await this.applyModifications(booking, modifications);

    // 5. Confirm with supplier
    await this.confirmModificationWithSupplier(modified);

    return modified;
  }

  private async validateModifications(
    booking: AccommodationBooking,
    modifications: BookingModifications
  ): Promise<void> {
    // Check if modification is allowed
    if (booking.status !== 'confirmed') {
      throw new ValidationError('Can only modify confirmed bookings');
    }

    // Check modification deadline
    const deadline = this.getModificationDeadline(booking);
    if (new Date() > deadline) {
      throw new ValidationError(
        'Modifications not allowed within deadline period'
      );
    }

    // Validate date changes
    if (modifications.checkIn || modifications.checkOut) {
      const newCheckIn = modifications.checkIn || booking.checkIn;
      const newCheckOut = modifications.checkOut || booking.checkOut;

      if (newCheckIn >= newCheckOut) {
        throw new ValidationError('Check-out must be after check-in');
      }

      const today = new Date();
      if (newCheckIn < today) {
        throw new ValidationError('Cannot modify to past dates');
      }

      // Check availability for new dates
      const available = await this.availabilityService.checkAvailability(
        booking.propertyId,
        booking.roomTypeId,
        { start: newCheckIn, end: newCheckOut },
        { adults: booking.guestDetails.adults, children: booking.guestDetails.children }
      );

      if (!available.available) {
        throw new ConflictError('No availability for requested dates');
      }
    }

    // Validate guest count changes
    if (
      modifications.adults ||
      modifications.children !== undefined
    ) {
      const roomType = await this.roomTypeService.getRoomType(
        booking.propertyId,
        booking.roomTypeId
      );

      const newAdults = modifications.adults || booking.guestDetails.adults;
      const newChildren = modifications.children !== undefined
        ? modifications.children
        : booking.guestDetails.children;

      if (newAdults > roomType.occupancy.maxAdults) {
        throw new ValidationError('Exceeds maximum adults');
      }

      const totalGuests = newAdults + (newChildren || 0);
      if (totalGuests > roomType.occupancy.maxTotal) {
        throw new ValidationError('Exceeds maximum occupancy');
      }
    }
  }

  private async calculateModifiedPrice(
    booking: AccommodationBooking,
    modifications: BookingModifications
  ): Promise<PriceDifference> {
    const originalPrice = booking.pricing.total;

    const newPrice = await this.pricingService.calculatePrice({
      propertyId: booking.propertyId,
      roomTypeId: booking.roomTypeId,
      ratePlanId: booking.ratePlanId,
      dates: {
        start: modifications.checkIn || booking.checkIn,
        end: modifications.checkOut || booking.checkOut,
      },
      occupancy: {
        adults: modifications.adults || booking.guestDetails.adults,
        children: modifications.children !== undefined
          ? modifications.children
          : booking.guestDetails.children,
      },
      promoCode: booking.promoCode,
    });

    return {
      original: originalPrice,
      new: newPrice.total,
      difference: newPrice.total - originalPrice,
      refundDue: newPrice.total < originalPrice,
      additionalPayment: newPrice.total > originalPrice,
    };
  }

  private async createNewBookingForDates(
    original: AccommodationBooking,
    modifications: BookingModifications
  ): Promise<AccommodationBooking> {
    // Cancel original booking
    await this.cancelBooking(original.id, 'modification', false);

    // Create new booking with new dates
    return await this.bookingService.createBooking({
      bookingId: original.bookingId,
      propertyId: original.propertyId,
      roomTypeId: original.roomTypeId,
      ratePlanId: original.ratePlanId,
      checkIn: modifications.checkIn || original.checkIn,
      checkOut: modifications.checkOut || original.checkOut,
      adults: modifications.adults || original.guestDetails.adults,
      children: modifications.children ?? original.guestDetails.children,
      rooms: original.rooms,
      guestDetails: original.guestDetails,
      promoCode: original.promoCode,
      modificationOf: original.id,
    });
  }

  private async applyModifications(
    booking: AccommodationBooking,
    modifications: BookingModifications
  ): Promise<AccommodationBooking> {
    const updates: Partial<AccommodationBooking> = {};

    if (modifications.guestDetails) {
      updates.guestDetails = {
        ...booking.guestDetails,
        ...modifications.guestDetails,
      };
    }

    if (modifications.specialRequests !== undefined) {
      updates.guestDetails = {
        ...updates.guestDetails || booking.guestDetails,
        specialRequests: modifications.specialRequests,
      };
    }

    const modified = await this.bookingRepository.update(booking.id, {
      ...updates,
      status: 'modified',
      modifiedAt: new Date(),
    });

    // Send modification confirmation
    await this.sendModificationConfirmation(modified);

    return modified;
  }

  private async confirmModificationWithSupplier(
    booking: AccommodationBooking
  ): Promise<void> {
    const property = await this.getProperty(booking.propertyId);
    const adapter = this.supplierAdapterFactory.getAdapter(property.supplierId);

    try {
      await adapter.modifyReservation({
        referenceNumber: booking.supplierReference,
        modifications: {
          guestName: booking.guestDetails.firstName && booking.guestDetails.lastName
            ? `${booking.guestDetails.firstName} ${booking.guestDetails.lastName}`
            : undefined,
          specialRequests: booking.guestDetails.specialRequests,
        },
      });
    } catch (error) {
      this.logger.error('Failed to confirm modification with supplier', {
        bookingId: booking.id,
        error,
      });
      // Non-fatal - continue with local modification
    }
  }

  private getModificationDeadline(booking: AccommodationBooking): Date {
    // Typically 48-72 hours before check-in
    const hoursBefore = 72;
    const deadline = new Date(booking.checkIn);
    deadline.setHours(deadlight.getHours() - hoursBefore);
    return deadline;
  }

  private async sendModificationConfirmation(
    booking: AccommodationBooking
  ): Promise<void> {
    await this.emailService.send({
      to: booking.guestDetails.email,
      template: 'booking_modified',
      data: {
        booking,
        property: await this.getProperty(booking.propertyId),
      },
    });
  }

  private async getBooking(bookingId: string): Promise<AccommodationBooking> {
    const booking = await this.bookingRepository.findById(bookingId);
    if (!booking) {
      throw new NotFoundError('Booking not found');
    }
    return booking;
  }

  private async getProperty(propertyId: string): Promise<Property> {
    return this.propertyService.getProperty(propertyId);
  }

  private async cancelBooking(
    bookingId: string,
    reason: string,
    supplierCancel: boolean
  ): Promise<void> {
    return this.cancellationService.cancelBooking(bookingId, reason, supplierCancel);
  }
}
```

---

## Cancellation Processing

### Cancellation Service

```typescript
export class BookingCancellationService {
  async cancelBooking(
    bookingId: string,
    reason: string = 'customer_request',
    supplierCancel: boolean = true
  ): Promise<CancellationResult> {
    const booking = await this.getBooking(bookingId);

    // 1. Check if cancellation is allowed
    await this.validateCancellation(booking);

    // 2. Calculate refund
    const refund = await this.calculateRefund(booking);

    // 3. Cancel with supplier
    if (supplierCancel) {
      await this.cancelWithSupplier(booking);
    }

    // 4. Update booking status
    await this.updateBookingStatus(bookingId, 'cancelled');

    // 5. Restore inventory
    await this.restoreInventory(booking);

    // 6. Process refund
    if (refund.amount > 0) {
      await this.processRefund(booking, refund);
    }

    // 7. Send notifications
    await this.sendCancellationNotice(booking, refund);

    return {
      bookingId,
      cancelledAt: new Date(),
      refund,
      reason,
    };
  }

  private async validateCancellation(
    booking: AccommodationBooking
  ): Promise<void> {
    // Check status
    if (booking.status === 'cancelled') {
      throw new ValidationError('Booking already cancelled');
    }

    if (booking.status === 'pending' || booking.status === 'holding') {
      // Can cancel without penalty
      return;
    }

    // Check cancellation policy
    const ratePlan = await this.ratePlanService.getRatePlan(
      booking.propertyId,
      booking.ratePlanId
    );

    const policy = ratePlan.constraints.cancellationPolicy;

    if (policy.type === 'non_refundable') {
      throw new ValidationError('Booking is non-refundable');
    }

    // Check deadline
    if (policy.deadline) {
      const now = new Date();
      const deadline = this.calculateDeadline(booking.checkIn, policy.deadline);

      if (now > deadline) {
        throw new ValidationError(
          'Past cancellation deadline - no refund available'
        );
      }
    }
  }

  private async calculateRefund(
    booking: AccommodationBooking
  ): Promise<RefundCalculation> {
    const ratePlan = await this.ratePlanService.getRatePlan(
      booking.propertyId,
      booking.ratePlanId
    );

    const policy = ratePlan.constraints.cancellationPolicy;
    const totalPaid = booking.pricing.total;

    // Calculate penalty
    let penalty = 0;

    if (policy.penalty) {
      switch (policy.penalty.type) {
        case 'fixed':
          penalty = policy.penalty.amount || 0;
          break;

        case 'percentage':
          penalty = (totalPaid * (policy.penalty.amount || 0)) / 100;
          break;

        case 'nights':
          const nightlyRate = totalPaid / booking.nights;
          penalty = nightlyRate * (policy.penalty.nights || 1);
          break;
      }
    }

    const refundAmount = Math.max(0, totalPaid - penalty);

    return {
      totalPaid,
      penalty,
      refundAmount,
      refundPercentage: totalPaid > 0 ? (refundAmount / totalPaid) * 100 : 0,
      currency: totalPaid.currency,
    };
  }

  private async cancelWithSupplier(
    booking: AccommodationBooking
  ): Promise<void> {
    const property = await this.getProperty(booking.propertyId);
    const adapter = this.supplierAdapterFactory.getAdapter(property.supplierId);

    try {
      await adapter.cancelReservation({
        referenceNumber: booking.supplierReference,
        reason: 'customer_request',
      });
    } catch (error) {
      this.logger.error('Failed to cancel with supplier', {
        bookingId: booking.id,
        supplierReference: booking.supplierReference,
        error,
      });
      // Continue with local cancellation
    }
  }

  private async updateBookingStatus(
    bookingId: string,
    status: 'cancelled'
  ): Promise<void> {
    await this.bookingRepository.update(bookingId, {
      status,
      cancelledAt: new Date(),
    });
  }

  private async restoreInventory(booking: AccommodationBooking): Promise<void> {
    const dates = this.eachDate({ start: booking.checkIn, end: booking.checkOut });

    const updates: AvailabilityUpdate[] = [];

    for (const date of dates) {
      updates.push({
        propertyId: booking.propertyId,
        roomTypeId: booking.roomTypeId,
        ratePlanId: booking.ratePlanId,
        date,
        delta: booking.rooms, // Restore
      });
    }

    await this.availabilityService.updateAvailability(updates);
  }

  private async processRefund(
    booking: AccommodationBooking,
    refund: RefundCalculation
  ): Promise<void> {
    if (booking.paymentId) {
      await this.paymentService.refund({
        paymentId: booking.paymentId,
        amount: refund.refundAmount,
        currency: refund.currency,
        reason: 'Booking cancellation',
      });
    }
  }

  private async sendCancellationNotice(
    booking: AccommodationBooking,
    refund: RefundCalculation
  ): Promise<void> {
    await this.emailService.send({
      to: booking.guestDetails.email,
      template: 'booking_cancelled',
      data: {
        booking,
        refund,
        property: await this.getProperty(booking.propertyId),
      },
    });

    // SMS notification
    if (booking.guestDetails.phone) {
      await this.smsService.send({
        to: booking.guestDetails.phone,
        template: 'booking_cancelled_sms',
        data: {
          bookingReference: booking.bookingId,
          refundAmount: refund.refundAmount,
        },
      });
    }
  }

  private calculateDeadline(
    checkIn: Date,
    deadline: { amount: number; unit: string; before: string }
  ): Date {
    const result = new Date(checkIn);

    switch (deadline.unit) {
      case 'hours':
        result.setHours(result.getHours() - deadline.amount);
        break;
      case 'days':
        result.setDate(result.getDate() - deadline.amount);
        break;
    }

    return result;
  }

  private async getBooking(bookingId: string): Promise<AccommodationBooking> {
    const booking = await this.bookingRepository.findById(bookingId);
    if (!booking) {
      throw new NotFoundError('Booking not found');
    }
    return booking;
  }

  private async getProperty(propertyId: string): Promise<Property> {
    return this.propertyService.getProperty(propertyId);
  }

  private eachDate(range: DateRange): Date[] {
    const dates: Date[] = [];
    const current = new Date(range.start);

    while (current < range.end) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return dates;
  }
}
```

---

## Supplier Coordination

### Webhook Handler

```typescript
export class SupplierWebhookHandler {
  async handleWebhook(
    supplierId: string,
    event: SupplierWebhookEvent
  ): Promise<void> {
    switch (event.type) {
      case 'booking.cancelled':
        await this.handleSupplierCancellation(event);
        break;

      case 'booking.modified':
        await this.handleSupplierModification(event);
        break;

      case 'availability.changed':
        await this.handleAvailabilityChange(event);
        break;

      case 'booking.failed':
        await this.handleBookingFailure(event);
        break;

      default:
        this.logger.warn(`Unknown event type: ${event.type}`);
    }
  }

  private async handleSupplierCancellation(
    event: SupplierWebhookEvent
  ): Promise<void> {
    const booking = await this.bookingRepository.findBySupplierReference(
      event.supplierId,
      event.data.referenceNumber
    );

    if (!booking || booking.status === 'cancelled') {
      return; // Already handled or not found
    }

    // Update booking status
    await this.bookingRepository.update(booking.id, {
      status: 'cancelled',
      cancelledAt: new Date(),
      cancellationReason: 'supplier_cancelled',
    });

    // Restore inventory
    await this.restoreInventoryForBooking(booking);

    // Process refund
    await this.refundService.processFullRefund(booking.paymentId);

    // Notify customer
    await this.notificationService.send({
      type: 'booking_cancelled_by_supplier',
      channel: 'email',
      recipients: [booking.guestDetails.email],
      data: {
        booking,
        reason: event.data.reason,
      },
    });

    // Notify agency
    await this.notificationService.send({
      type: 'booking_cancelled_by_supplier',
      channel: 'agency',
      data: {
        bookingId: booking.id,
        supplierId: event.supplierId,
        reason: event.data.reason,
      },
    });
  }

  private async handleBookingFailure(
    event: SupplierWebhookEvent
  ): Promise<void> {
    const booking = await this.bookingRepository.findBySupplierReference(
      event.supplierId,
      event.data.referenceNumber
    );

    if (!booking || booking.status === 'failed') {
      return;
    }

    // Update booking status
    await this.bookingRepository.update(booking.id, {
      status: 'failed',
      failedAt: new Date(),
      failureReason: event.data.reason,
    });

    // Release hold/restore inventory
    await this.restoreInventoryForBooking(booking);

    // Notify agency for follow-up
    await this.notificationService.send({
      type: 'booking_failed',
      channel: 'agency',
      priority: 'high',
      data: {
        bookingId: booking.id,
        supplierId: event.supplierId,
        reason: event.data.reason,
      },
    });
  }

  private async restoreInventoryForBooking(
    booking: AccommodationBooking
  ): Promise<void> {
    const dates = this.eachDate({ start: booking.checkIn, end: booking.checkOut });

    const updates: AvailabilityUpdate[] = [];

    for (const date of dates) {
      updates.push({
        propertyId: booking.propertyId,
        roomTypeId: booking.roomTypeId,
        ratePlanId: booking.ratePlanId,
        date,
        delta: booking.rooms,
      });
    }

    await this.availabilityService.updateAvailability(updates);
  }

  private eachDate(range: DateRange): Date[] {
    const dates: Date[] = [];
    const current = new Date(range.start);

    while (current < range.end) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return dates;
  }
}
```

---

## API Endpoints

### Booking Endpoints

```
POST   /accommodations/bookings
GET    /accommodations/bookings/:bookingId
PATCH  /accommodations/bookings/:bookingId
POST   /accommodations/bookings/:bookingId/cancel
POST   /accommodations/bookings/:bookingId/modify
GET    /accommodations/bookings/:bookingId/status
```

### Hold Endpoints

```
POST   /accommodations/holds
GET    /accommodations/holds/:token
PATCH  /accommodations/holds/:token/extend
DELETE /accommodations/holds/:token
```

### Availability Endpoints

```
POST   /accommodations/availability/check
POST   /accommodations/availability/sync
```

---

**Series Complete:** The Accommodation Catalog series (5 documents) is now complete. Next series: [Flight Integration](./FLIGHT_INTEGRATION_MASTER_INDEX.md)
