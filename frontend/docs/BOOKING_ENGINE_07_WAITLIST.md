# Booking Engine — Waitlist System

> Waitlist management, notifications, and automatic conversion

**Series:** Booking Engine | **Document:** 7 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Waitlist Configuration](#waitlist-configuration)
3. [Waitlist Enrollment](#waitlist-enrollment)
4. [Availability Monitoring](#availability-monitoring)
5. [Waitlist Notification](#waitlist-notification)
6. [Conversion Flow](#conversion-flow)
7. [Waitlist Prioritization](#waitlist-prioritization)
8. [Expiration & Cleanup](#expiration--cleanup)

---

## Overview

The waitlist system captures demand when inventory is unavailable and automatically converts waitlisted customers to bookings when availability opens up. This maximizes revenue capture and improves customer experience.

### Waitlist Types

| Type | Description | Conversion Window |
|------|-------------|-------------------|
| **Sold Out** | Product fully booked | First available slot |
| **Dates Request** | Specific dates unavailable | Requested dates only |
| **Flexible** | Customer flexible on dates | Best available option |
| **Price Alert** | Waiting for lower price | Price threshold met |
| **Upgrade Waitlist** | Waiting for upgrade availability | Upgrade opens |

### Waitlist Benefits

- **Revenue Recovery**: Capture demand that would otherwise be lost
- **Customer Retention**: Keep customers engaged rather than losing them
- **Demand Intelligence**: Understand true demand beyond current inventory
- **Dynamic Pricing**: Inform pricing decisions based on waitlist depth

---

## Waitlist Configuration

### Configuration Model

```typescript
// ============================================================================
// WAITLIST CONFIGURATION
// ============================================================================

interface WaitlistConfig {
  // Global settings
  enabled: boolean;
  maxQueueSize: number;
  defaultExpiry: number; // hours

  // Product-specific overrides
  productOverrides: Map<string, ProductWaitlistConfig>;

  // Notification settings
  notifications: {
    enabled: boolean;
    channels: ('email' | 'sms' | 'push')[];
    responseWindow: number; // hours to respond
    reminderCount: number;
  };

  // Conversion settings
  conversion: {
    autoConvert: boolean;
    paymentRequired: boolean;
    holdDuration: number; // minutes to hold inventory
  };

  // Prioritization
  prioritization: {
    enabled: boolean;
    factors: PriorityFactor[];
  };
}

interface ProductWaitlistConfig {
  productId: string;
  enabled: boolean;
  maxQueueSize: number;
  allowMultipleEntries: boolean;
  flexibleDatesEnabled: boolean;
  flexibleDateRange: number; // days
}

type PriorityFactor =
  | 'customer_tier'
  | 'wait_duration'
  | 'booking_value'
  | 'loyalty_status'
  | 'first_come_first_served';

const DEFAULT_WAITLIST_CONFIG: WaitlistConfig = {
  enabled: true,
  maxQueueSize: 1000,
  defaultExpiry: 168, // 7 days

  productOverrides: new Map(),

  notifications: {
    enabled: true,
    channels: ['email', 'sms', 'push'],
    responseWindow: 24, // 24 hours to respond
    reminderCount: 2,
  },

  conversion: {
    autoConvert: false, // Require customer confirmation
    paymentRequired: true,
    holdDuration: 60, // 60 minutes to complete booking
  },

  prioritization: {
    enabled: true,
    factors: ['customer_tier', 'wait_duration', 'booking_value'],
  },
};

class WaitlistConfigService {
  private config: WaitlistConfig;

  constructor() {
    this.config = DEFAULT_WAITLIST_CONFIG;
  }

  async getConfig(productId?: string): Promise<WaitlistConfig | ProductWaitlistConfig> {
    if (productId) {
      const override = this.config.productOverrides.get(productId);
      if (override) {
        return override;
      }
    }
    return this.config;
  }

  async isWaitlistEnabled(productId: string): Promise<boolean> {
    const config = await this.getConfig(productId);
    return config.enabled;
  }

  async getMaxQueueSize(productId: string): Promise<number> {
    const config = await this.getConfig(productId);
    return config.maxQueueSize;
  }
}
```

---

## Waitlist Enrollment

### Adding to Waitlist

```typescript
// ============================================================================
// WAITLIST ENROLLMENT
// ============================================================================

interface WaitlistEntry {
  id: string;
  customerId: string;
  productId: string;
  supplierId: string;

  // Request details
  requestedDates: DateRange;
  flexibleDates: boolean;
  flexibleRange?: number; // days
  quantity: number;

  // Budget
  maxPrice?: number;
  currency: string;

  // Preferences
  preferences: {
    roomType?: string;
    cabinClass?: string;
    mealPlan?: string;
    [key: string]: unknown;
  };

  // Status
  status: 'active' | 'notified' | 'converting' | 'converted' | 'expired' | 'cancelled';

  // Priority
  priority: number;
  priorityFactors: PriorityFactors;

  // Timestamps
  createdAt: Date;
  expiresAt: Date;
  notifiedAt?: Date;
  convertedAt?: Date;
}

interface PriorityFactors {
  customerTier: 'platinum' | 'gold' | 'silver' | 'standard';
  waitDuration: number; // hours
  bookingValue: number;
  loyaltyPoints: number;
}

interface WaitlistEnrollmentRequest {
  customerId: string;
  productId: string;
  requestedDates: DateRange;
  quantity: number;
  flexibleDates?: boolean;
  flexibleRange?: number;
  maxPrice?: number;
  preferences?: Record<string, unknown>;
}

interface WaitlistEnrollmentResponse {
  success: boolean;
  entryId: string;
  position?: number;
  estimatedWait?: string;
  alternatives?: AlternativeOption[];
}

class WaitlistEnrollment {
  private config: WaitlistConfigService;

  async enroll(
    request: WaitlistEnrollmentRequest
  ): Promise<WaitlistEnrollmentResponse> {
    // Check if waitlist is enabled for this product
    const enabled = await this.config.isWaitlistEnabled(request.productId);
    if (!enabled) {
      return {
        success: false,
        entryId: '',
        alternatives: await this.getAlternatives(request),
      };
    }

    // Check queue size
    const queueSize = await this.getQueueSize(request.productId);
    const maxSize = await this.config.getMaxQueueSize(request.productId);

    if (queueSize >= maxSize) {
      return {
        success: false,
        entryId: '',
        alternatives: await this.getAlternatives(request),
      };
    }

    // Check if customer already has an active entry
    const existing = await WaitlistEntry.findOne({
      customerId: request.customerId,
      productId: request.productId,
      status: { $in: ['active', 'notified'] },
    });

    if (existing) {
      return {
        success: false,
        entryId: existing.id,
        position: await this.getPosition(existing.id),
        estimatedWait: await this.estimateWait(existing),
      };
    }

    // Create waitlist entry
    const entry = await this.createEntry(request);

    // Calculate priority
    entry.priority = await this.calculatePriority(entry);

    await entry.save();

    const position = await this.getPosition(entry.id);
    const estimatedWait = await this.estimateWait(entry);

    // Send confirmation
    await this.sendEnrollmentConfirmation(entry, position);

    return {
      success: true,
      entryId: entry.id,
      position,
      estimatedWait,
    };
  }

  private async createEntry(
    request: WaitlistEnrollmentRequest
  ): Promise<WaitlistEntry> {
    const product = await ProductService.get(request.productId);
    const customer = await CustomerService.get(request.customerId);

    const entry: WaitlistEntry = {
      id: crypto.randomUUID(),
      customerId: request.customerId,
      productId: request.productId,
      supplierId: product.supplierId,
      requestedDates: request.requestedDates,
      flexibleDates: request.flexibleDates || false,
      flexibleRange: request.flexibleRange,
      quantity: request.quantity,
      maxPrice: request.maxPrice,
      currency: product.currency,
      preferences: request.preferences || {},
      status: 'active',
      priority: 0,
      priorityFactors: {
        customerTier: customer.tier,
        waitDuration: 0,
        bookingValue: await this.getEstimatedBookingValue(request),
        loyaltyPoints: customer.loyaltyPoints || 0,
      },
      createdAt: new Date(),
      expiresAt: addHours(new Date(), 168), // 7 days default
    };

    return await WaitlistEntry.create(entry);
  }

  private async calculatePriority(entry: WaitlistEntry): Promise<number> {
    const config = await this.config.getConfig();
    if (!config.prioritization.enabled) {
      return entry.createdAt.getTime(); // First come, first served
    }

    let score = 0;

    // Customer tier (0-100 points)
    const tierScores = { platinum: 100, gold: 75, silver: 50, standard: 25 };
    score += tierScores[entry.priorityFactors.customerTier] || 0;

    // Wait duration (0-50 points, maxes out at 30 days)
    const waitHours = entry.priorityFactors.waitDuration;
    score += Math.min(50, Math.floor(waitHours / 24) * 1.67);

    // Booking value (0-30 points)
    const value = entry.priorityFactors.bookingValue;
    score += Math.min(30, Math.floor(value / 100));

    // Loyalty points (0-20 points)
    const points = entry.priorityFactors.loyaltyPoints;
    score += Math.min(20, Math.floor(points / 1000));

    // Invert score (lower = higher priority for sorting)
    return 1000 - score;
  }

  private async getPosition(entryId: string): Promise<number> {
    const entry = await WaitlistEntry.findById(entryId);
    const count = await WaitlistEntry.countDocuments({
      productId: entry.productId,
      status: 'active',
      priority: { $lt: entry.priority },
    });
    return count + 1;
  }

  private async getQueueSize(productId: string): Promise<number> {
    return await WaitlistEntry.countDocuments({
      productId,
      status: { $in: ['active', 'notified', 'converting'] },
    });
  }

  private async estimateWait(entry: WaitlistEntry): Promise<string> {
    // Check recent cancellations for this product
    const recentCancellations = await this.getRecentCancellations(
      entry.productId,
      30 // days
    );

    const position = await this.getPosition(entry.id);

    if (recentCancellations === 0) {
      return 'Unknown';
    }

    const daysPerCancellation = 30 / recentCancellations;
    const estimatedDays = position * daysPerCancellation;

    if (estimatedDays < 1) {
      return 'Less than 1 day';
    } else if (estimatedDays < 7) {
      return `${Math.ceil(estimatedDays)} days`;
    } else if (estimatedDays < 30) {
      return `${Math.ceil(estimatedDays / 7)} weeks`;
    } else {
      return `${Math.ceil(estimatedDays / 30)}+ months`;
    }
  }

  private async getRecentCancellations(
    productId: string,
    days: number
  ): Promise<number> {
    const since = subDays(new Date(), days);

    return await BookingEvent.countDocuments({
      type: 'item.cancelled',
      'data.productId': productId,
      timestamp: { $gte: since },
    });
  }

  private async getEstimatedBookingValue(
    request: WaitlistEnrollmentRequest
  ): Promise<number> {
    const pricing = await PricingService.calculatePrice({
      productId: request.productId,
      dates: request.requestedDates,
      quantity: request.quantity,
    });

    return pricing.total;
  }

  private async getAlternatives(
    request: WaitlistEnrollmentRequest
  ): Promise<AlternativeOption[]> {
    const alternatives: AlternativeOption[] = [];

    // Check nearby dates
    if (request.flexibleDates !== false) {
      const range = request.flexibleRange || 3;

      for (let offset = -range; offset <= range; offset++) {
        if (offset === 0) continue;

        const altDates = {
          start: addDays(request.requestedDates.start, offset),
          end: addDays(request.requestedDates.end, offset),
        };

        const available = await InventoryService.checkAvailability({
          productId: request.productId,
          dates: altDates,
          quantity: request.quantity,
        });

        if (available.available) {
          const pricing = await PricingService.calculatePrice({
            productId: request.productId,
            dates: altDates,
            quantity: request.quantity,
          });

          if (!request.maxPrice || pricing.total <= request.maxPrice) {
            alternatives.push({
              type: 'date',
              description: offset > 0 ? `+${offset} days` : `${offset} days`,
              value: altDates,
              price: pricing.total,
            });
          }
        }
      }
    }

    // Check similar products
    const similarProducts = await ProductService.getSimilar(request.productId);
    for (const product of similarProducts) {
      const available = await InventoryService.checkAvailability({
        productId: product.id,
        dates: request.requestedDates,
        quantity: request.quantity,
      });

      if (available.available) {
        const pricing = await PricingService.calculatePrice({
          productId: product.id,
          dates: request.requestedDates,
          quantity: request.quantity,
        });

        if (!request.maxPrice || pricing.total <= request.maxPrice) {
          alternatives.push({
            type: 'product',
            description: product.name,
            value: { productId: product.id },
            price: pricing.total,
          });
        }
      }
    }

    return alternatives.slice(0, 5);
  }

  private async sendEnrollmentConfirmation(
    entry: WaitlistEntry,
    position: number
  ): Promise<void> {
    const customer = await CustomerService.get(entry.customerId);
    const product = await ProductService.get(entry.productId);

    await EmailService.send({
      to: customer.email,
      subject: `Waitlist Confirmation: ${product.name}`,
      template: 'waitlist-enrollment',
      data: {
        customerName: customer.firstName,
        productName: product.name,
        position,
        dates: entry.requestedDates,
        expiresAt: entry.expiresAt,
      },
    });
  }
}

interface AlternativeOption {
  type: 'date' | 'product';
  description: string;
  value: Record<string, unknown>;
  price: number;
}
```

---

## Availability Monitoring

### Monitoring for Openings

```typescript
// ============================================================================
// AVAILABILITY MONITORING
// ============================================================================

class AvailabilityMonitor {
  private scheduler: Scheduler;

  constructor() {
    this.scheduler = new Scheduler();
    this.startMonitoring();
  }

  private startMonitoring(): void {
    // Check every 5 minutes for high-demand products
    this.scheduler.schedule('*/5 * * * *', async () => {
      await this.checkHighDemandProducts();
    });

    // Check every 15 minutes for regular products
    this.scheduler.schedule('*/15 * * * *', async () => {
      await this.checkRegularProducts();
    });

    // Check immediately when cancellations occur
    this.subscribeToCancellations();
  }

  private async checkHighDemandProducts(): Promise<void> {
    const highDemandProducts = await this.getHighDemandProducts();

    for (const product of highDemandProducts) {
      await this.checkProductAvailability(product);
    }
  }

  private async checkRegularProducts(): Promise<void> {
    const productsWithWaitlist = await this.getProductsWithActiveWaitlist();

    for (const product of productsWithWaitlist) {
      await this.checkProductAvailability(product);
    }
  }

  private async checkProductAvailability(productId: string): Promise<void> {
    // Get active waitlist entries for this product
    const entries = await WaitlistEntry.find({
      productId,
      status: 'active',
    }).sort({ priority: 1 });

    if (entries.length === 0) {
      return;
    }

    // Check availability for each entry's requested dates
    for (const entry of entries) {
      const available = await InventoryService.checkAvailability({
        productId,
        dates: entry.requestedDates,
        quantity: entry.quantity,
      });

      if (available.available && this.meetsPriceCriteria(entry, available)) {
        await this.notifyWaitlistEntry(entry);
      }

      // Check flexible dates if enabled
      if (entry.flexibleDates && !available.available) {
        const flexibleAvailable = await this.checkFlexibleDates(entry);
        if (flexibleAvailable) {
          await this.notifyWaitlistEntry(entry, flexibleAvailable);
        }
      }
    }
  }

  private async checkFlexibleDates(
    entry: WaitlistEntry
  ): Promise<FlexibleAvailability | null> {
    const range = entry.flexibleRange || 3;

    for (let offset = -range; offset <= range; offset++) {
      if (offset === 0) continue;

      const altDates = {
        start: addDays(entry.requestedDates.start, offset),
        end: addDays(entry.requestedDates.end, offset),
      };

      const available = await InventoryService.checkAvailability({
        productId: entry.productId,
        dates: altDates,
        quantity: entry.quantity,
      });

      if (available.available && this.meetsPriceCriteria(entry, available)) {
        return {
          dates: altDates,
          price: available.price,
        };
      }
    }

    return null;
  }

  private meetsPriceCriteria(
    entry: WaitlistEntry,
    available: AvailabilityResponse
  ): boolean {
    if (!entry.maxPrice) {
      return true;
    }

    const price = available.dates[0]?.pricing?.baseRate || 0;
    return price <= entry.maxPrice;
  }

  private async notifyWaitlistEntry(
    entry: WaitlistEntry,
    flexible?: FlexibleAvailability
  ): Promise<void> {
    // Update entry status
    entry.status = 'notified';
    entry.notifiedAt = new Date();
    await entry.save();

    // Send notification
    await this.sendAvailabilityNotification(entry, flexible);

    // Schedule expiration (response window)
    const config = await new WaitlistConfigService().getConfig();
    const responseWindow = config.notifications.responseWindow;

    await Agenda.schedule('waitlist-expire', addHours(new Date(), responseWindow), {
      entryId: entry.id,
    });
  }

  private async sendAvailabilityNotification(
    entry: WaitlistEntry,
    flexible?: FlexibleAvailability
  ): Promise<void> {
    const customer = await CustomerService.get(entry.customerId);
    const product = await ProductService.get(entry.productId);
    const config = await new WaitlistConfigService().getConfig();

    const holdToken = crypto.randomUUID();

    // Generate hold token link
    const holdUrl = `${process.env.APP_URL}/waitlist/claim?token=${holdToken}`;

    // Store hold token
    await Redis.setex(
      `waitlist:hold:${holdToken}`,
      3600, // 1 hour
      JSON.stringify({
        entryId: entry.id,
        productId: entry.productId,
        dates: flexible?.dates || entry.requestedDates,
        quantity: entry.quantity,
      })
    );

    // Send email
    if (config.notifications.channels.includes('email')) {
      await EmailService.send({
        to: customer.email,
        subject: `Good news! ${product.name} is now available`,
        template: 'waitlist-available',
        data: {
          customerName: customer.firstName,
          productName: product.name,
          dates: flexible?.dates || entry.requestedDates,
          price: flexible?.price,
          holdUrl,
          responseWindow: config.notifications.responseWindow,
        },
      });
    }

    // Send SMS
    if (config.notifications.channels.includes('sms') && customer.phone) {
      await SMSService.send({
        to: customer.phone,
        message: `Good news! ${product.name} is now available for your dates. Click to claim: ${holdUrl}`,
      });
    }

    // Send push
    if (config.notifications.channels.includes('push') && customer.deviceTokens) {
      await PushService.send({
        tokens: customer.deviceTokens,
        notification: {
          title: 'Availability Alert! 🎉',
          body: `${product.name} is now available for your requested dates.`,
        },
        data: {
          type: 'waitlist_available',
          entryId: entry.id,
          holdUrl,
        },
      });
    }

    // Schedule reminders
    for (let i = 1; i <= config.notifications.reminderCount; i++) {
      const reminderTime = addHours(new Date(), (config.notifications.responseWindow * i) / (config.notifications.reminderCount + 1));
      await Agenda.schedule('waitlist-reminder', reminderTime, {
        entryId: entry.id,
        holdUrl,
        reminderNumber: i,
      });
    }
  }

  private subscribeToCancellations(): void {
    // Listen for cancellation events
    EventSubscriber.on('booking.item_cancelled', async (event) => {
      const productId = event.data.productId;
      const dates = event.data.dates;

      // Check if waitlist exists for this product/dates
      await this.checkProductAvailability(productId);
    });
  }

  private async getHighDemandProducts(): Promise<string[]> {
    // Get products with high waitlist count
    const products = await WaitlistEntry.aggregate([
      { $match: { status: 'active' } },
      { $group: { _id: '$productId', count: { $sum: 1 } } },
      { $match: { count: { $gte: 10 } } },
      { $project: { productId: '$_id', _id: 0 } },
    ]);

    return products.map(p => p.productId);
  }

  private async getProductsWithActiveWaitlist(): Promise<string[]> {
    const products = await WaitlistEntry.distinct('productId', {
      status: 'active',
    });

    return products;
  }
}

interface FlexibleAvailability {
  dates: DateRange;
  price: number;
}
```

---

## Waitlist Notification

### Notification Templates

```typescript
// ============================================================================
// NOTIFICATION TEMPLATES
// ============================================================================

const WAITLIST_TEMPLATES = {
  enrollment: {
    subject: 'You\'re on the waitlist for {{productName}}',
    body: `
      <h1>Waitlist Confirmation</h1>

      <p>Hi {{customerName}},</p>

      <p>You've been added to the waitlist for <strong>{{productName}}</strong>.</p>

      <h2>Your Details</h2>
      <ul>
        <li>Dates: {{dates.start}} - {{dates.end}}</li>
        <li>Position: #{{position}}</li>
        <li>Expires: {{expiresAt}}</li>
      </ul>

      <p>We'll notify you as soon as availability opens up.</p>

      <p>In the meantime, you can check your waitlist status in your account.</p>
    `,
  },

  available: {
    subject: 'Good news! {{productName}} is now available',
    body: `
      <h1>Availability Opened! 🎉</h1>

      <p>Hi {{customerName}},</p>

      <p>Great news! <strong>{{productName}}</strong> is now available for your requested dates.</p>

      <h2>Your Trip</h2>
      <ul>
        <li>Dates: {{dates.start}} - {{dates.end}}</li>
        <li>Price: {{price}}</li>
      </ul>

      <p>You have <strong>{{responseWindow}} hours</strong> to claim this availability.</p>

      <p><a href="{{holdUrl}}" class="button">Claim Your Spot</a></p>

      <p>Don't miss out - this offer expires automatically.</p>
    `,
  },

  reminder: {
    subject: 'Reminder: {{productName}} is waiting for you',
    body: `
      <h1>Last Chance!</h1>

      <p>Hi {{customerName}},</p>

      <p>This is a reminder that <strong>{{productName}}</strong> is still available for your waitlist request.</p>

      <p><a href="{{holdUrl}}" class="button">Claim Now</a></p>

      <p>This offer expires soon.</p>
    `,
  },

  expired: {
    subject: 'Your waitlist offer has expired',
    body: `
      <h1>Offer Expired</h1>

      <p>Hi {{customerName}},</p>

      <p>Your waitlist offer for <strong>{{productName}}</strong> has expired.</p>

      <p>You're still on the waitlist for future availability. We'll notify you again when something opens up.</p>

      <p>Would you like to remain on the waitlist?</p>
    `,
  },

  converted: {
    subject: 'Booking Confirmed! 🎉',
    body: `
      <h1>Booking Confirmed</h1>

      <p>Hi {{customerName}},</p>

      <p>Congratulations! Your waitlist offer has been successfully converted to a booking.</p>

      <h2>Your Booking</h2>
      <ul>
        <li>Reference: {{bookingReference}}</li>
        <li>Dates: {{dates.start}} - {{dates.end}}</li>
        <li>Total: {{total}}</li>
      </ul>

      <p><a href="{{viewBookingUrl}}" class="button">View Your Booking</a></p>
    `,
  },
};
```

---

## Conversion Flow

### Converting Waitlist to Booking

```typescript
// ============================================================================
// CONVERSION FLOW
// ============================================================================

interface WaitlistConversionRequest {
  entryId: string;
  holdToken: string;
  accept: boolean;
  paymentMethod?: PaymentMethod;
}

interface WaitlistConversionResult {
  success: boolean;
  booking?: Booking;
  reason?: string;
}

class WaitlistConverter {
  private config: WaitlistConfigService;

  async convert(
    request: WaitlistConversionRequest
  ): Promise<WaitlistConversionResult> {
    // Validate hold token
    const holdData = await this.validateHoldToken(request.holdToken);
    if (!holdData) {
      return {
        success: false,
        reason: 'Invalid or expired hold token',
      };
    }

    // Get entry
    const entry = await WaitlistEntry.findById(request.entryId);
    if (!entry || entry.status !== 'notified') {
      return {
        success: false,
        reason: 'Invalid waitlist entry',
      };
    }

    if (!request.accept) {
      // Declined - remove from waitlist
      await this.removeEntry(entry, 'declined');
      return { success: false, reason: 'Declined by customer' };
    }

    // Update status
    entry.status = 'converting';
    await entry.save();

    try {
      // Create hold on inventory
      const hold = await this.createInventoryHold(entry, holdData);

      // Create booking
      const booking = await this.createBooking(entry, hold, request.paymentMethod);

      // Process payment
      const config = await this.config.getConfig();
      if (config.conversion.paymentRequired) {
        await this.processPayment(booking, request.paymentMethod);
      }

      // Confirm booking
      await this.confirmBooking(booking);

      // Update entry
      entry.status = 'converted';
      entry.convertedAt = new Date();
      await entry.save();

      // Send confirmation
      await this.sendConversionConfirmation(entry, booking);

      return {
        success: true,
        booking,
      };

    } catch (error) {
      // Revert status
      entry.status = 'notified';
      await entry.save();

      return {
        success: false,
        reason: error.message,
      };
    }
  }

  private async validateHoldToken(
    token: string
  ): Promise<WaitlistHoldData | null> {
    const data = await Redis.get(`waitlist:hold:${token}`);
    if (!data) {
      return null;
    }

    return JSON.parse(data);
  }

  private async createInventoryHold(
    entry: WaitlistEntry,
    holdData: WaitlistHoldData
  ): Promise<InventoryHold> {
    const config = await this.config.getConfig();
    const holdDuration = config.conversion.holdDuration;

    return await new HoldManager().createHold({
      bookingId: null, // Will be set after booking created
      bookingItemId: null,
      supplierId: entry.supplierId,
      productId: entry.productId,
      dates: holdData.dates,
      quantity: entry.quantity,
      ttl: holdDuration * 60, // Convert to seconds
    });
  }

  private async createBooking(
    entry: WaitlistEntry,
    hold: InventoryHold,
    paymentMethod?: PaymentMethod
  ): Promise<Booking> {
    const customer = await CustomerService.get(entry.customerId);

    const booking = await Booking.create({
      status: 'pending',
      state: 'reserving',
      customerId: entry.customerId,
      customerInfo: {
        primary: {
          title: customer.title,
          firstName: customer.firstName,
          lastName: customer.lastName,
          email: customer.email,
          phone: customer.phone,
        },
        travelers: [], // To be provided
      },
      items: [{
        id: crypto.randomUUID(),
        type: 'accommodation', // Determine from product
        supplierId: entry.supplierId,
        productId: entry.productId,
        dates: hold.dates,
        pricing: {
          baseRate: 0,
          taxes: 0,
          fees: 0,
          discount: 0,
          total: 0,
          currency: entry.currency,
        },
        status: 'pending',
      }],
      pricing: {
        subtotal: 0,
        taxes: 0,
        fees: 0,
        discount: 0,
        total: 0,
        currency: entry.currency,
      },
      paymentStatus: 'pending',
      metadata: {
        source: 'waitlist',
        waitlistEntryId: entry.id,
      },
    });

    // Update hold with booking ID
    hold.bookingId = booking.id;
    await hold.save();

    return booking;
  }

  private async processPayment(
    booking: Booking,
    paymentMethod?: PaymentMethod
  ): Promise<void> {
    if (!paymentMethod) {
      throw new PaymentMethodRequiredError();
    }

    const payment = await PaymentService.charge({
      paymentMethodId: paymentMethod.id,
      amount: booking.pricing.total,
      currency: booking.pricing.currency,
      bookingId: booking.id,
      description: `Waitlist conversion for booking ${booking.id}`,
    });

    await BookingPayment.create({
      bookingId: booking.id,
      paymentId: payment.id,
      amount: payment.amount,
      currency: payment.currency,
      status: 'captured',
    });

    booking.paymentStatus = 'paid';
    await booking.save();
  }

  private async confirmBooking(booking: Booking): Promise<void> {
    const result = await new ConfirmationOrchestrator().confirmBooking(booking.id);

    if (!result.success) {
      throw new ConfirmationFailedError();
    }
  }

  private async sendConversionConfirmation(
    entry: WaitlistEntry,
    booking: Booking
  ): Promise<void> {
    const customer = await CustomerService.get(entry.customerId);
    const product = await ProductService.get(entry.productId);

    await EmailService.send({
      to: customer.email,
      subject: `Booking Confirmed! ${product.name}`,
      template: 'waitlist-converted',
      data: {
        customerName: customer.firstName,
        productName: product.name,
        bookingReference: booking.reference,
        dates: entry.requestedDates,
        total: booking.pricing.total,
        viewBookingUrl: `${process.env.APP_URL}/bookings/${booking.id}`,
      },
    });
  }

  private async removeEntry(
    entry: WaitlistEntry,
    reason: string
  ): Promise<void> {
    entry.status = 'cancelled';
    await entry.save();

    await WaitlistEvent.create({
      entryId: entry.id,
      type: 'entry_removed',
      reason,
      timestamp: new Date(),
    });
  }
}

interface WaitlistHoldData {
  entryId: string;
  productId: string;
  dates: DateRange;
  quantity: number;
}
```

---

## Waitlist Prioritization

### Priority Scoring

```typescript
// ============================================================================
// PRIORITY SCORING
// ============================================================================

interface PriorityScore {
  total: number;
  breakdown: {
    customerTier: number;
    waitDuration: number;
    bookingValue: number;
    loyaltyPoints: number;
    flexibility: number;
  };
}

class PriorityScorer {
  async scoreEntry(entry: WaitlistEntry): Promise<PriorityScore> {
    const config = await new WaitlistConfigService().getConfig();

    const breakdown = {
      customerTier: this.scoreCustomerTier(entry.priorityFactors.customerTier),
      waitDuration: this.scoreWaitDuration(entry.priorityFactors.waitDuration),
      bookingValue: this.scoreBookingValue(entry.priorityFactors.bookingValue),
      loyaltyPoints: this.scoreLoyaltyPoints(entry.priorityFactors.loyaltyPoints),
      flexibility: this.scoreFlexibility(entry),
    };

    const total = Object.values(breakdown).reduce((sum, score) => sum + score, 0);

    return { total, breakdown };
  }

  private scoreCustomerTier(tier: string): number {
    const scores = {
      platinum: 100,
      gold: 75,
      silver: 50,
      standard: 25,
    };
    return scores[tier] || 0;
  }

  private scoreWaitDuration(hours: number): number {
    // Max 50 points, caps at 30 days (720 hours)
    return Math.min(50, Math.floor(hours / 14.4));
  }

  private scoreBookingValue(value: number): number {
    // Max 30 points for high-value bookings
    return Math.min(30, Math.floor(value / 100));
  }

  private scoreLoyaltyPoints(points: number): number {
    // Max 20 points for loyalty
    return Math.min(20, Math.floor(points / 1000));
  }

  private scoreFlexibility(entry: WaitlistEntry): number {
    // Bonus for flexible customers
    if (!entry.flexibleDates) {
      return 0;
    }

    let score = 10; // Base score for being flexible

    // Additional points for wider flexibility
    if (entry.flexibleRange && entry.flexibleRange > 3) {
      score += 5;
    }

    if (entry.maxPrice) {
      score += 5; // Willing to pay more for alternatives
    }

    return Math.min(20, score);
  }

  // Recalculate all scores (run periodically)
  async recalculateScores(): Promise<void> {
    const entries = await WaitlistEntry.find({
      status: 'active',
    });

    for (const entry of entries) {
      // Update wait duration
      entry.priorityFactors.waitDuration = differenceInHours(
        new Date(),
        entry.createdAt
      );

      // Recalculate priority
      entry.priority = await this.calculatePriority(entry);
      await entry.save();
    }
  }

  private async calculatePriority(entry: WaitlistEntry): Promise<number> {
    const score = await this.scoreEntry(entry);
    // Invert for sorting (lower = higher priority)
    return 1000 - score.total;
  }
}
```

---

## Expiration & Cleanup

### Waitlist Maintenance

```typescript
// ============================================================================
// EXPIRATION & CLEANUP
// ============================================================================

class WaitlistMaintenance {
  async processExpirations(): Promise<void> {
    // Find expired entries
    const expired = await WaitlistEntry.find({
      status: { $in: ['notified', 'converting'] },
      expiresAt: { $lt: new Date() },
    });

    for (const entry of expired) {
      await this.expireEntry(entry);
    }
  }

  private async expireEntry(entry: WaitlistEntry): Promise<void> {
    // Check if entry was converting (had accepted but didn't complete)
    if (entry.status === 'converting') {
      // May have been a payment failure - give another chance
      await this.offerSecondChance(entry);
    } else {
      // Regular expiration - remove from waitlist
      entry.status = 'expired';
      await entry.save();

      // Send expiration notice
      await this.sendExpirationNotice(entry);

      // Release any holds
      await this.releaseHolds(entry);
    }
  }

  private async offerSecondChance(entry: WaitlistEntry): Promise<void> {
    // Extend expiration by 1 hour
    entry.expiresAt = addHours(new Date(), 1);
    entry.status = 'notified';
    await entry.save();

    // Send reminder
    await this.sendSecondChanceNotice(entry);
  }

  private async sendExpirationNotice(entry: WaitlistEntry): Promise<void> {
    const customer = await CustomerService.get(entry.customerId);
    const product = await ProductService.get(entry.productId);

    await EmailService.send({
      to: customer.email,
      subject: 'Your waitlist offer has expired',
      template: 'waitlist-expired',
      data: {
        customerName: customer.firstName,
        productName: product.name,
      },
    });
  }

  private async sendSecondChanceNotice(entry: WaitlistEntry): Promise<void> {
    const customer = await CustomerService.get(entry.customerId);
    const product = await ProductService.get(entry.productId);

    await EmailService.send({
      to: customer.email,
      subject: 'Last chance: Complete your booking',
      template: 'waitlist-second-chance',
      data: {
        customerName: customer.firstName,
        productName: product.name,
        holdUrl: `${process.env.APP_URL}/waitlist/claim?token=${entry.id}`,
      },
    });
  }

  private async releaseHolds(entry: WaitlistEntry): Promise<void> {
    const holds = await InventoryHold.find({
      bookingId: entry.id, // Waitlist entries use entry ID as temp booking ID
      status: 'active',
    });

    for (const hold of holds) {
      await new HoldManager().releaseHold(hold.id, 'waitlist_expired');
    }
  }

  // Cleanup old entries (run daily)
  async cleanupOldEntries(): Promise<void> {
    const ninetyDaysAgo = subDays(new Date(), 90);

    // Archive old entries
    const oldEntries = await WaitlistEntry.find({
      status: { $in: ['expired', 'cancelled', 'converted'] },
      createdAt: { $lt: ninetyDaysAgo },
    });

    for (const entry of oldEntries) {
      await WaitlistArchive.create(entry.toJSON());
      await WaitlistEntry.deleteOne({ _id: entry._id });
    }

    logger.info(`Archived ${oldEntries.length} old waitlist entries`);
  }

  // Recalculate priorities (hourly)
  async updatePriorities(): Promise<void> {
    await new PriorityScorer().recalculateScores();
  }

  // Check for stale entries (not notified but very old)
  async checkStaleEntries(): Promise<void> {
    const thirtyDaysAgo = subDays(new Date(), 30);

    const staleEntries = await WaitlistEntry.find({
      status: 'active',
      notifiedAt: { $exists: false },
      createdAt: { $lt: thirtyDaysAgo },
    });

    for (const entry of staleEntries) {
      // Send status update
      await this.sendStatusUpdate(entry);
    }
  }

  private async sendStatusUpdate(entry: WaitlistEntry): Promise<void> {
    const customer = await CustomerService.get(entry.customerId);
    const product = await ProductService.get(entry.productId);
    const position = await new WaitlistEnrollment()['getPosition'](entry.id);

    await EmailService.send({
      to: customer.email,
      subject: `Waitlist Update: ${product.name}`,
      template: 'waitlist-status',
      data: {
        customerName: customer.firstName,
        productName: product.name,
        position,
        daysWaiting: differenceInDays(new Date(), entry.createdAt),
      },
    });
  }
}
```

---

**Next:** [State Machine](./BOOKING_ENGINE_08_STATE_MACHINE.md) — Complete booking lifecycle and state transitions
