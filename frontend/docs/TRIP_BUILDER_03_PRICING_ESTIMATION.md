# Trip Builder 03: Pricing Estimation

> Dynamic pricing, multi-component cost estimation, budget management, and currency handling

---

## Overview

This document details the pricing and estimation subsystem for multi-component trips, covering dynamic pricing updates, cost aggregation, budget tracking, currency conversion, and price optimization. The pricing engine provides real-time cost visibility throughout the trip planning process.

**Key Capabilities:**
- Multi-component pricing aggregation
- Dynamic price updates and monitoring
- Budget tracking and alerts
- Multi-currency support
- Price optimization recommendations
- What-if scenario analysis
- Historical price tracking

---

## Table of Contents

1. [Pricing Architecture](#pricing-architecture)
2. [Component Pricing](#component-pricing)
3. [Price Aggregation](#price-aggregation)
4. [Dynamic Pricing](#dynamic-pricing)
5. [Budget Management](#budget-management)
6. [Currency Handling](#currency-handling)
7. [Price Optimization](#price-optimization)

---

## Pricing Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRIP PRICING ENGINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  COMPONENT   │───▶│   PRICE      │───▶│   CURRENCY   │                  │
│  │  PRICERS     │    │   AGGREGATOR  │    │   CONVERTER  │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                              │
│                              ▼                                              │
│                      ┌──────────────┐                                     │
│                      │   BUDGET     │                                     │
│                      │   MANAGER    │                                     │
│                      └──────┬───────┘                                     │
│                             │                                             │
│          ┌────────────────────┼────────────────────┐                     │
│          │                    │                     │                      │
│     ┌────▼────┐         ┌─────▼─────┐        ┌─────▼─────┐                │
│     │ PRICE   │         │BUDGET    │        │OPTIMIZER │                │
│     │ MONITOR │         │ALERTS    │        │          │                │
│     └─────────┘         └───────────┘        └───────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Component Pricers** | Get real-time pricing from each supplier |
| **Price Aggregator** | Combine component prices into trip total |
| **Currency Converter** | Handle multi-currency conversions |
| **Budget Manager** | Track spending vs. budget |
| **Price Monitor** | Watch for price changes |
| **Budget Alerts** | Notify of budget issues |
| **Optimizer** | Suggest cost-saving alternatives |

---

## Component Pricing

### Pricing Service Interface

```typescript
class ComponentPricingService {
  private pricers: Map<ComponentType, ComponentPricer>;

  async getComponentPrice(
    component: TripComponent,
    context: PricingContext
  ): Promise<ComponentPricing> {
    const pricer = this.pricers.get(component.type);

    if (!pricer) {
      throw new Error(`No pricer for component type: ${component.type}`);
    }

    return await pricer.getPrice(component, context);
  }

  async getComponentPrices(
    components: TripComponent[],
    context: PricingContext
  ): Promise<Map<string, ComponentPricing>> {
    const prices = new Map<string, ComponentPricing>();

    // Price components in parallel
    const results = await Promise.allSettled(
      components.map(async (component) => {
        const price = await this.getComponentPrice(component, context);
        return { componentId: component.id, price };
      })
    );

    for (const result of results) {
      if (result.status === 'fulfilled') {
        prices.set(result.value.componentId, result.value.price);
      }
    }

    return prices;
  }

  async validatePrice(
    component: TripComponent,
    price: ComponentPricing,
    context: PricingContext
  ): Promise<PriceValidation> {
    // Check if price is still valid
    const pricer = this.pricers.get(component.type);

    if (!pricer) {
      return { valid: false, reason: 'No pricer available' };
    }

    // Re-fetch current price
    const currentPrice = await pricer.getPrice(component, context);

    // Check if price has changed significantly
    const priceDiff = Math.abs(currentPrice.total - price.total);
    const percentDiff = (priceDiff / price.total) * 100;

    if (percentDiff > 5) {
      return {
        valid: false,
        reason: 'Price has changed',
        previousPrice: price,
        currentPrice,
        percentChange: percentDiff
      };
    }

    // Check if price is still within validity period
    if (price.validUntil < new Date()) {
      return {
        valid: false,
        reason: 'Price quote expired',
        previousPrice: price,
        currentPrice
      };
    }

    return { valid: true };
  }
}

interface ComponentPricer {
  getPrice(component: TripComponent, context: PricingContext): Promise<ComponentPricing>;
  getPriceHistory(offerId: string, days: number): Promise<PriceHistoryEntry[]>;
  subscribeToPriceChanges(offerId: string, callback: PriceChangeCallback): void;
}

interface PricingContext {
  tripId: string;
  userId: string;
  currency: string;
  locale: string;
  market: string;
  corporateCode?: string;
  loyaltyPrograms?: LoyaltyAccount[];
}

interface PriceValidation {
  valid: boolean;
  reason?: string;
  previousPrice?: ComponentPricing;
  currentPrice?: ComponentPricing;
  percentChange?: number;
}
```

### Flight Pricer

```typescript
class FlightPricer implements ComponentPricer {
  async getPrice(
    component: TripComponent,
    context: PricingContext
  ): Promise<ComponentPricing> {
    // Get flight offer
    const offer = component.offer as FlightOffer;

    // Calculate price for all passengers
    const passengerTypes = this.getPassengerTypes(context.travelers);
    const prices = await this.calculatePassengerPrices(offer, passengerTypes);

    // Calculate total
    const total = Object.values(prices).reduce((sum, p) => sum + p.total, 0);

    return {
      currency: offer.pricing.currency,
      baseFare: prices.adults?.baseFare || 0 +
                prices.children?.baseFare || 0 +
                prices.infants?.baseFare || 0,
      taxes: prices.adults?.taxes || 0 +
             prices.children?.taxes || 0 +
             prices.infants?.taxes || 0,
      fees: prices.adults?.fees || 0 +
            prices.children?.fees || 0 +
            prices.infants?.fees || 0,
      total,
      perPassenger: this.calculatePerPassengerPrice(prices, context.travelers),
      breakdown: {
        byPassengerType: prices,
        bySegment: offer.pricing.breakdown
      },
      priceType: this.determinePriceType(offer),
      guaranteed: offer.guarantee === 'guaranteed',
      validUntil: new Date(Date.now() + 30 * 60 * 1000), // 30 minutes
      quotedAt: new Date()
    };
  }

  private async calculatePassengerPrices(
    offer: FlightOffer,
    passengerTypes: PassengerCount
  ): Promise<PassengerTypePrices> {
    const prices: PassengerTypePrices = {};

    // Adult pricing
    if (passengerTypes.adults > 0) {
      const adultPrice = await this.calculatePriceForType(
        offer,
        'adult',
        passengerTypes.adults
      );
      prices.adults = adultPrice;
    }

    // Child pricing
    if (passengerTypes.children > 0) {
      const childPrice = await this.calculatePriceForType(
        offer,
        'child',
        passengerTypes.children
      );
      prices.children = childPrice;
    }

    // Infant pricing
    if (passengerTypes.infants > 0) {
      const infantPrice = await this.calculatePriceForType(
        offer,
        'infant',
        passengerTypes.infants
      );
      prices.infants = infantPrice;
    }

    return prices;
  }

  private async calculatePriceForType(
    offer: FlightOffer,
    passengerType: 'adult' | 'child' | 'infant',
    count: number
  ): Promise<PassengerPrice> {
    let baseFare = offer.pricing.baseFare;
    let taxes = offer.pricing.taxes;
    let fees = offer.pricing.fees;

    // Apply discounts for children/infants
    if (passengerType === 'child') {
      const discount = await this.getChildDiscount(offer);
      baseFare *= (1 - discount);
    } else if (passengerType === 'infant') {
      const discount = await this.getInfantDiscount(offer);
      baseFare *= (1 - discount);
    }

    // Some taxes are per person, some are flat
    const perPersonTaxes = taxes / count; // Simplified
    const perPersonFees = fees / count;

    const total = baseFare + perPersonTaxes + perPersonFees;

    return {
      passengerType,
      count,
      baseFare,
      taxes: perPersonTaxes,
      fees: perPersonFees,
      total,
      totalForType: total * count
    };
  }

  private async getChildDiscount(offer: FlightOffer): Promise<number> {
    // Typically 25% off base fare for children
    return 0.25;
  }

  private async getInfantDiscount(offer: FlightOffer): Promise<number> {
    // Typically 90% off base fare for infants (lap children)
    return 0.90;
  }

  private determinePriceType(offer: FlightOffer): PriceType {
    if (offer.guarantee === 'guaranteed') {
      return PriceType.GUARANTEED;
    }
    if (offer.metadata?.isShopping) {
      return PriceType.ESTIMATE;
    }
    return PriceType.QUOTE;
  }
}

interface PassengerTypePrices {
  adults?: PassengerPrice;
  children?: PassengerPrice;
  infants?: PassengerPrice;
}

interface PassengerPrice {
  passengerType: 'adult' | 'child' | 'infant';
  count: number;
  baseFare: number;
  taxes: number;
  fees: number;
  total: number; // per passenger
  totalForType: number; // total for this passenger type
}
```

### Accommodation Pricer

```typescript
class AccommodationPricer implements ComponentPricer {
  async getPrice(
    component: TripComponent,
    context: PricingContext
  ): Promise<ComponentPricing> {
    const offer = component.offer as AccommodationOffer;
    const nights = this.calculateNights(component);

    // Calculate room price
    const roomRate = offer.pricing.nightlyRate;
    const baseFare = roomRate * nights;

    // Calculate taxes and fees
    const taxes = baseFare * offer.pricing.taxRate;
    const fees = offer.pricing.fees.total;

    // Calculate per person (if sharing)
    const perPerson = baseFare / context.travelers.adults;

    return {
      currency: offer.pricing.currency,
      baseFare,
      taxes,
      fees,
      total: baseFare + taxes + fees,
      perPerson,
      breakdown: {
        byNight: {
          nights,
          nightlyRate: roomRate,
          taxesPerNight: taxes / nights,
          feesPerNight: fees / nights
        },
        roomType: offer.roomType,
        boardBasis: offer.boardBasis
      },
      priceType: PriceType.QUOTE,
      guaranteed: offer.availability.guaranteed,
      validUntil: new Date(Date.now() + 60 * 60 * 1000), // 1 hour
      quotedAt: new Date()
    };
  }

  private calculateNights(component: TripComponent): number {
    const diffMs = component.endDate.getTime() - component.startDate.getTime();
    return Math.round(diffMs / (1000 * 60 * 60 * 24));
  }
}
```

---

## Price Aggregation

### Aggregation Service

```typescript
class PriceAggregator {
  async aggregateTripPrice(
    trip: Trip,
    context: PricingContext
  ): Promise<TripPricing> {
    // Get prices for all components
    const componentPrices = await this.pricingService.getComponentPrices(
      trip.components,
      context
    );

    // Calculate totals
    const totals = this.calculateTotals(componentPrices, trip.components);

    // Build breakdown
    const breakdown = this.buildBreakdown(componentPrices, trip.components);

    // Convert to trip currency if needed
    const finalPricing = context.currency === totals.currency
      ? totals
      : await this.currencyConverter.convertPricing(totals, context.currency);

    return {
      ...finalPricing,
      breakdown,
      componentCount: trip.components.length,
      estimated: this.isEstimated(trip.components),
      validUntil: this.getEarliestExpiry(trip.components)
    };
  }

  private calculateTotals(
    prices: Map<string, ComponentPricing>,
    components: TripComponent[]
  ): TripPricing {
    let total = 0;
    let baseFare = 0;
    let taxes = 0;
    let fees = 0;
    const currency = components[0]?.pricing.currency || 'USD';

    for (const component of components) {
      const price = prices.get(component.id);
      if (price) {
        total += price.total;
        baseFare += price.baseFare;
        taxes += price.taxes;
        fees += price.fees;
      }
    }

    return {
      total,
      baseFare,
      taxes,
      fees,
      currency,
      perPerson: total / 1, // Will be calculated based on traveler count
      breakdown: new Map()
    };
  }

  private buildBreakdown(
    prices: Map<string, ComponentPricing>,
    components: TripComponent[]
  ): PricingBreakdown {
    const breakdown: PricingBreakdown = {
      byComponent: [],
      byCategory: new Map(),
      byDate: new Map()
    };

    // By component
    for (const component of components) {
      const price = prices.get(component.id);
      if (price) {
        breakdown.byComponent.push({
          componentId: component.id,
          type: component.type,
          category: component.category,
          price: price.total,
          currency: price.currency
        });
      }
    }

    // By category
    for (const item of breakdown.byComponent) {
      const current = breakdown.byCategory.get(item.category) || 0;
      breakdown.byCategory.set(item.category, current + item.price);
    }

    // By date
    for (const component of components) {
      const price = prices.get(component.id);
      if (price) {
        const dateKey = this.getDateKey(component.startDate);
        const current = breakdown.byDate.get(dateKey) || 0;
        breakdown.byDate.set(dateKey, current + price.total);
      }
    }

    return breakdown;
  }

  private getDateKey(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  private isEstimated(components: TripComponent[]): boolean {
    return components.some(c =>
      c.pricing.priceType === PriceType.ESTIMATE ||
      !c.pricing.guaranteed
    );
  }

  private getEarliestExpiry(components: TripComponent[]): Date {
    const expiries = components
      .map(c => c.pricing.validUntil)
      .filter(d => d !== undefined) as Date[];

    return new Date(Math.min(...expiries.map(d => d.getTime())));
  }
}

interface TripPricing {
  total: number;
  baseFare: number;
  taxes: number;
  fees: number;
  currency: string;
  perPerson: number;
  breakdown: PricingBreakdown;
  componentCount: number;
  estimated: boolean;
  validUntil: Date;
}

interface PricingBreakdown {
  byComponent: ComponentPriceItem[];
  byCategory: Map<ComponentCategory, number>;
  byDate: Map<string, number>;
}

interface ComponentPriceItem {
  componentId: string;
  type: ComponentType;
  category: ComponentCategory;
  price: number;
  currency: string;
}
```

---

## Dynamic Pricing

### Price Monitoring Service

```typescript
class PriceMonitoringService {
  private subscriptions: Map<string, PriceSubscription>;
  private priceHistory: PriceHistoryStore;

  async subscribeToPriceChanges(
    tripId: string,
    callback: PriceChangeCallback
  ): Promise<void> {
    const trip = await this.getTrip(tripId);

    const subscription: PriceSubscription = {
      tripId,
      components: trip.components.map(c => c.id),
      callback,
      subscribedAt: new Date(),
      lastChecked: new Date()
    };

    this.subscriptions.set(tripId, subscription);

    // Start monitoring loop
    this.monitorPrices(tripId);
  }

  private async monitorPrices(tripId: string): Promise<void> {
    const subscription = this.subscriptions.get(tripId);
    if (!subscription) return;

    while (this.subscriptions.has(tripId)) {
      // Wait before checking again
      await this.sleep(5 * 60 * 1000); // 5 minutes

      // Check for price changes
      const changes = await this.checkPriceChanges(tripId);

      if (changes.length > 0) {
        // Notify callback
        await subscription.callback(changes);

        // Store in history
        for (const change of changes) {
          await this.priceHistory.record(change);
        }
      }

      subscription.lastChecked = new Date();
    }
  }

  private async checkPriceChanges(
    tripId: string
  ): Promise<PriceChange[]> {
    const changes: PriceChange[] = [];
    const trip = await this.getTrip(tripId);

    for (const component of trip.components) {
      // Validate current price
      const validation = await this.pricingService.validatePrice(
        component,
        component.pricing,
        this.createContext(trip)
      );

      if (!validation.valid && validation.currentPrice) {
        changes.push({
          componentId: component.id,
          type: component.type,
          previousPrice: component.pricing.total,
          newPrice: validation.currentPrice.total,
          changePercent: validation.percentChange!,
          changeAmount: validation.currentPrice.total - component.pricing.total,
          detectedAt: new Date()
        });

        // Update component pricing
        component.pricing = validation.currentPrice;
      }
    }

    return changes;
  }

  async getPriceHistory(
    componentId: string,
    days: number = 30
  ): Promise<PriceHistoryEntry[]> {
    const since = new Date();
    since.setDate(since.getDate() - days);

    return await this.priceHistory.getHistory(componentId, since);
  }

  async getPriceTrend(
    componentId: string
  ): Promise<PriceTrend> {
    const history = await this.getPriceHistory(componentId, 30);

    if (history.length < 2) {
      return {
        direction: 'unknown',
        percentChange: 0,
        min: history[0]?.price || 0,
        max: history[0]?.price || 0,
        average: history[0]?.price || 0
      };
    }

    const prices = history.map(h => h.price);
    const oldest = prices[0];
    const newest = prices[prices.length - 1];
    const percentChange = ((newest - oldest) / oldest) * 100;

    let direction: 'up' | 'down' | 'stable';
    if (Math.abs(percentChange) < 2) {
      direction = 'stable';
    } else {
      direction = percentChange > 0 ? 'up' : 'down';
    }

    return {
      direction,
      percentChange,
      min: Math.min(...prices),
      max: Math.max(...prices),
      average: prices.reduce((sum, p) => sum + p, 0) / prices.length
    };
  }
}

interface PriceSubscription {
  tripId: string;
  components: string[];
  callback: PriceChangeCallback;
  subscribedAt: Date;
  lastChecked: Date;
}

interface PriceChange {
  componentId: string;
  type: ComponentType;
  previousPrice: number;
  newPrice: number;
  changePercent: number;
  changeAmount: number;
  detectedAt: Date;
}

interface PriceTrend {
  direction: 'up' | 'down' | 'stable' | 'unknown';
  percentChange: number;
  min: number;
  max: number;
  average: number;
}
```

---

## Budget Management

### Budget Manager

```typescript
class BudgetManager {
  async trackBudget(tripId: string): Promise<BudgetStatus> {
    const trip = await this.getTrip(tripId);
    const pricing = await this.pricingAggregator.aggregateTripPrice(
      trip,
      this.createContext(trip)
    );

    const budget = trip.budget;

    if (!budget) {
      return {
        hasBudget: false,
        total: pricing.total,
        currency: pricing.currency
      };
    }

    // Convert to budget currency if needed
    const convertedPricing = budget.currency === pricing.currency
      ? pricing
      : await this.currencyConverter.convertPricing(pricing, budget.currency);

    const spent = this.calculateSpent(trip);
    const committed = this.calculateCommitted(trip);
    const remaining = budget.total - spent - committed;

    // Check budget status
    const percentUsed = ((spent + committed) / budget.total) * 100;
    const status = this.determineBudgetStatus(percentUsed, budget.alertThreshold);

    // Check category allocations
    const categoryStatus = await this.checkCategoryAllocations(trip, budget);

    return {
      hasBudget: true,
      total: budget.total,
      spent,
      committed,
      remaining,
      currency: budget.currency,
      percentUsed,
      status,
      alertsEnabled: budget.alertsEnabled,
      categoryStatus
    };
  }

  private determineBudgetStatus(
    percentUsed: number,
    alertThreshold: number
  ): BudgetStatusType {
    if (percentUsed >= 100) {
      return 'exceeded';
    }
    if (percentUsed >= alertThreshold) {
      return 'warning';
    }
    if (percentUsed >= 80) {
      return 'caution';
    }
    return 'healthy';
  }

  private async checkCategoryAllocations(
    trip: Trip,
    budget: TripBudget
  ): Promise<CategoryBudgetStatus[]> {
    const statuses: CategoryBudgetStatus[] = [];

    // Calculate spending by category
    const spendingByCategory = await this.calculateSpendingByCategory(trip);

    for (const [category, spent] of spendingByCategory) {
      const allocated = budget.allocation[category] || 0;
      const percentUsed = (spent / allocated) * 100;

      statuses.push({
        category,
        allocated,
        spent,
        remaining: allocated - spent,
        percentUsed,
        status: percentUsed >= 100 ? 'exceeded' : percentUsed >= 90 ? 'warning' : 'healthy'
      });
    }

    return statuses;
  }

  async checkBudgetAlerts(tripId: string): Promise<BudgetAlert[]> {
    const status = await this.trackBudget(tripId);
    const alerts: BudgetAlert[] = [];

    if (!status.hasBudget || !status.alertsEnabled) {
      return alerts;
    }

    // Overall budget alerts
    if (status.status === 'exceeded') {
      alerts.push({
        type: 'budget_exceeded',
        severity: 'critical',
        message: `Trip budget exceeded by ${Math.abs(status.remaining)} ${status.currency}`,
        amount: Math.abs(status.remaining),
        currency: status.currency
      });
    } else if (status.status === 'warning') {
      alerts.push({
        type: 'budget_warning',
        severity: 'warning',
        message: `Trip budget at ${status.percentUsed.toFixed(1)}% of total`,
        amount: status.total - status.remaining,
        currency: status.currency
      });
    }

    // Category alerts
    if (status.categoryStatus) {
      for (const cat of status.categoryStatus) {
        if (cat.status === 'exceeded') {
          alerts.push({
            type: 'category_exceeded',
            severity: 'warning',
            message: `${cat.category} budget exceeded by ${Math.abs(cat.remaining)} ${status.currency}`,
            category: cat.category,
            amount: Math.abs(cat.remaining),
            currency: status.currency
          });
        } else if (cat.status === 'warning') {
          alerts.push({
            type: 'category_warning',
            severity: 'info',
            message: `${cat.category} budget at ${cat.percentUsed.toFixed(1)}% of allocation`,
            category: cat.category,
            amount: cat.spent,
            currency: status.currency
          });
        }
      }
    }

    return alerts;
  }

  async whatIfAnalysis(
    tripId: string,
    changes: WhatIfChange[]
  ): Promise<WhatIfResult> {
    const trip = await this.getTrip(tripId);
    const originalPricing = await this.pricingAggregator.aggregateTripPrice(
      trip,
      this.createContext(trip)
    );

    // Apply changes to create modified trip
    const modifiedComponents = this.applyChanges(trip.components, changes);

    // Calculate new pricing
    const modifiedTrip = { ...trip, components: modifiedComponents };
    const newPricing = await this.pricingAggregator.aggregateTripPrice(
      modifiedTrip,
      this.createContext(modifiedTrip)
    );

    // Calculate differences
    const priceDiff = newPricing.total - originalPricing.total;

    return {
      originalTotal: originalPricing.total,
      newTotal: newPricing.total,
      difference: priceDiff,
      percentChange: (priceDiff / originalPricing.total) * 100,
      withinBudget: await this.checkWithinBudget(modifiedTrip, newPricing.total),
      breakdown: this.generateWhatIfBreakdown(changes, priceDiff)
    };
  }

  private applyChanges(
    components: TripComponent[],
    changes: WhatIfChange[]
  ): TripComponent[] {
    const modified = [...components];

    for (const change of changes) {
      switch (change.type) {
        case 'add_component':
          modified.push(change.component);
          break;

        case 'remove_component':
          return modified.filter(c => c.id !== change.componentId);

        case 'upgrade_component':
          const index = modified.findIndex(c => c.id === change.componentId);
          if (index >= 0 && change.upgradeOffer) {
            modified[index] = {
              ...modified[index],
              offer: change.upgradeOffer,
              pricing: change.upgradeOffer.pricing
            };
          }
          break;

        case 'change_dates':
          for (const comp of modified) {
            if (change.componentIds.includes(comp.id)) {
              const duration = comp.endDate.getTime() - comp.startDate.getTime();
              comp.startDate = change.newStartDate;
              comp.endDate = new Date(change.newStartDate.getTime() + duration);
            }
          }
          break;
      }
    }

    return modified;
  }
}

interface BudgetStatus {
  hasBudget: boolean;
  total?: number;
  spent?: number;
  committed?: number;
  remaining?: number;
  currency: string;
  percentUsed?: number;
  status?: BudgetStatusType;
  alertsEnabled?: boolean;
  categoryStatus?: CategoryBudgetStatus[];
}

interface CategoryBudgetStatus {
  category: ComponentCategory;
  allocated: number;
  spent: number;
  remaining: number;
  percentUsed: number;
  status: 'healthy' | 'warning' | 'exceeded';
}

interface BudgetAlert {
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  category?: ComponentCategory;
  amount: number;
  currency: string;
}

interface WhatIfResult {
  originalTotal: number;
  newTotal: number;
  difference: number;
  percentChange: number;
  withinBudget: boolean;
  breakdown: WhatIfBreakdownItem[];
}

type WhatIfChange =
  | { type: 'add_component'; component: TripComponent }
  | { type: 'remove_component'; componentId: string }
  | { type: 'upgrade_component'; componentId: string; upgradeOffer: ComponentOffer }
  | { type: 'change_dates'; componentIds: string[]; newStartDate: Date };
```

---

## Currency Handling

### Currency Converter

```typescript
class MultiCurrencyPricingConverter {
  private rates: Map<string, ExchangeRate>;
  private rateProvider: ExchangeRateProvider;

  async convertPricing(
    pricing: TripPricing,
    targetCurrency: string
  ): Promise<TripPricing> {
    if (pricing.currency === targetCurrency) {
      return pricing;
    }

    const rate = await this.getExchangeRate(pricing.currency, targetCurrency);

    return {
      ...pricing,
      currency: targetCurrency,
      total: pricing.total * rate.rate,
      baseFare: pricing.baseFare * rate.rate,
      taxes: pricing.taxes * rate.rate,
      fees: pricing.fees * rate.rate,
      perPerson: pricing.perPerson * rate.rate,
      breakdown: await this.convertBreakdown(pricing.breakdown, targetCurrency, rate)
    };
  }

  async convertTripPricing(
    trip: Trip,
    targetCurrency: string
  ): Promise<Trip> {
    // Convert all component prices
    const converted = await Promise.all(
      trip.components.map(async (component) => {
        if (component.pricing.currency === targetCurrency) {
          return component;
        }

        const rate = await this.getExchangeRate(
          component.pricing.currency,
          targetCurrency
        );

        return {
          ...component,
          pricing: {
            ...component.pricing,
            currency: targetCurrency,
            total: component.pricing.total * rate.rate,
            baseFare: component.pricing.baseFare * rate.rate,
            taxes: component.pricing.taxes * rate.rate,
            fees: component.pricing.fees * rate.rate,
            perPerson: component.pricing.perPerson * rate.rate
          }
        };
      })
    );

    return {
      ...trip,
      components: converted
    };
  }

  private async getExchangeRate(
    from: string,
    to: string
  ): Promise<ExchangeRate> {
    const key = `${from}_${to}`;

    // Check cache
    if (this.rates.has(key)) {
      const cached = this.rates.get(key)!;
      const age = (Date.now() - cached.timestamp.getTime()) / 1000;

      if (age < 3600) { // 1 hour cache
        return cached;
      }
    }

    // Fetch new rate
    const rate = await this.rateProvider.getRate(from, to);
    this.rates.set(key, rate);

    return rate;
  }
}

interface ExchangeRate {
  from: string;
  to: string;
  rate: number;
  timestamp: Date;
  provider: string;
}
```

---

## Price Optimization

### Optimization Engine

```typescript
class PriceOptimizer {
  async findOptimizations(
    trip: Trip,
    constraints: OptimizationConstraints
  ): Promise<PriceOptimization[]> {
    const optimizations: PriceOptimization[] = [];

    // Analyze each component for potential savings
    for (const component of trip.components) {
      const componentOptimizations = await this.optimizeComponent(
        component,
        trip,
        constraints
      );

      optimizations.push(...componentOptimizations);
    }

    // Look for package/bundle opportunities
    const bundleOptimizations = await this.findBundleSavings(trip);
    optimizations.push(...bundleOptimizations);

    // Score and rank optimizations
    for (const opt of optimizations) {
      opt.score = this.calculateOptimizationScore(opt, constraints);
    }

    optimizations.sort((a, b) => b.score - a.score);

    return optimizations.slice(0, 10);
  }

  private async optimizeComponent(
    component: TripComponent,
    trip: Trip,
    constraints: OptimizationConstraints
  ): Promise<PriceOptimization[]> {
    const optimizations: PriceOptimization[] = [];

    // Find cheaper alternatives
    const alternatives = await this.findCheaperAlternatives(component);

    for (const alternative of alternatives) {
      const savings = component.pricing.total - alternative.pricing.total;

      if (savings > 0) {
        // Check quality difference
        const qualityDiff = this.calculateQualityDifference(component, alternative);

        optimizations.push({
          type: 'component_alternative',
          componentId: component.id,
          currentOffer: component.offer,
          alternativeOffer: alternative.offer,
          savings,
          savingsPercent: (savings / component.pricing.total) * 100,
          qualityDifference: qualityDiff,
          tradeoffs: this.getTradeoffs(component, alternative),
          score: 0
        });
      }
    }

    // Check for timing-based savings
    const timingOptions = await this.findTimingSavings(component, trip);

    for (const option of timingOptions) {
      optimizations.push({
        type: 'timing_change',
        componentId: component.id,
        timingOption: option,
        savings: option.savings,
        savingsPercent: option.savingsPercent,
        tradeoffs: option.tradeoffs,
        score: 0
      });
    }

    return optimizations;
  }

  private async findBundleSavings(
    trip: Trip
  ): Promise<PriceOptimization[]> {
    const optimizations: PriceOptimization[] = [];

    // Check flight + hotel bundles
    const flightComponents = trip.components.filter(c => c.type === ComponentType.FLIGHT);
    const hotelComponents = trip.components.filter(c => c.type === ComponentType.ACCOMMODATION);

    if (flightComponents.length > 0 && hotelComponents.length > 0) {
      const bundleSavings = await this.checkFlightHotelBundle(
        flightComponents[0],
        hotelComponents[0]
      );

      if (bundleSavings.savings > 0) {
        optimizations.push({
          type: 'bundle',
          componentIds: [flightComponents[0].id, hotelComponents[0].id],
          bundleOffer: bundleSavings.bundle,
          savings: bundleSavings.savings,
          savingsPercent: bundleSavings.savingsPercent,
          tradeoffs: [],
          score: 0
        });
      }
    }

    return optimizations;
  }

  private calculateOptimizationScore(
    optimization: PriceOptimization,
    constraints: OptimizationConstraints
  ): number {
    let score = 0;

    // Savings score
    score += Math.min(50, optimization.savings / 10); // Max 50 points for savings

    // Penalize quality loss
    if (optimization.qualityDifference && optimization.qualityDifference < 0) {
      score -= Math.abs(optimization.qualityDifference) * 10;
    }

    // Bonus for significant savings percentage
    if (optimization.savingsPercent > 10) {
      score += 20;
    } else if (optimization.savingsPercent > 5) {
      score += 10;
    }

    // Penalty for tradeoffs
    score -= optimization.tradeoffs.length * 5;

    return Math.max(0, Math.min(100, score));
  }
}

interface PriceOptimization {
  type: string;
  componentId?: string;
  componentIds?: string[];
  currentOffer?: ComponentOffer;
  alternativeOffer?: ComponentOffer;
  bundleOffer?: BundleOffer;
  timingOption?: TimingOption;
  savings: number;
  savingsPercent: number;
  qualityDifference?: number;
  tradeoffs: string[];
  score: number;
}

interface OptimizationConstraints {
  maxQualityLoss?: number; // Maximum acceptable quality decrease (0-1)
  maxTimingChange?: number; // Maximum hours willing to shift
  requireSameLocation?: boolean;
  allowDifferentSupplier?: boolean;
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
