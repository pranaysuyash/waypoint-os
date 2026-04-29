# Destination Event & Festival Intelligence — Package Design

> Research document for festival-specific package creation, event inventory management, agent event toolkit, and event marketing automation.

---

## Key Questions

1. **How do agents create event-specific packages efficiently?**
2. **What event inventory management challenges exist?**
3. **How do we automate event-driven marketing?**
4. **What post-event opportunities exist?**

---

## Research Areas

### Event Package Creation Toolkit

```typescript
interface EventPackageBuilder {
  // Start from event template
  createFromEvent(event_id: string): EventTravelPackage;

  // Smart pricing based on event demand
  calculatePricing(base_cost: Money, event: DestinationEvent): EventPricing;

  // Inventory pre-booking
  preBookInventory(hotel_ids: string[], flight_routes: string[], event_tickets: number): Promise<InventoryHold>;

  // Marketing materials
  generateMarketing(package_id: string): EventMarketingMaterials;
}

interface EventPricing {
  base_cost: Money;
  event_premium: Money;
  early_bird_price: Money;
  standard_price: Money;
  last_minute_price: Money;
  commission_amount: Money;
  margin: Money;
  margin_pct: number;
}

// ── Package builder workflow ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Package Builder — Step by Step                 │
// │                                                       │
// │  1. Select Event                                      │
// │     [Search events... ] or [Calendar pick]            │
// │     → Diwali 2026 (Oct 20)                           │
// │     → Demand: HIGH | Price surge: +25%               │
// │                                                       │
// │  2. Choose Destinations                               │
// │     Recommended: Goa, Kerala, Rajasthan, Singapore   │
// │     → Selected: Goa (3N) + Kerala (4N)              │
// │                                                       │
// │  3. Select Components                                 │
// │     Flights: Mumbai → Goa → Kochi → Mumbai           │
// │     Hotels: Goa (beach resort) + Kerala (houseboat)  │
// │     Activities: Diwali celebration, beach, backwaters│
// │                                                       │
// │  4. Pricing                                           │
// │     Base cost: ₹48,000                               │
// │     Event premium: +₹12,000 (Diwali peak)            │
// │     Package price: ₹60,000 per person                │
// │     Early bird (Aug): ₹51,000 (-15%)                 │
// │     Last minute (Oct): ₹72,000 (+20%)                │
// │     Agent margin: ₹9,000 (15%)                       │
// │                                                       │
// │  5. Inventory                                         │
// │     Goa hotel: 20 rooms held (release: Sep 15)       │
// │     Flights: Group fare locked (30 seats)            │
// │     Kerala houseboat: 5 boats reserved               │
// │                                                       │
// │  6. Marketing                                         │
// │     Auto-generated: WhatsApp flyer, email template,  │
// │     social media posts, landing page                 │
// │     [Preview] [Edit] [Send to leads]                 │
// └─────────────────────────────────────────────────────┘
```

### Event Inventory Management

```typescript
interface EventInventoryManager {
  // Pre-booking for events
  holdInventory(event_id: string, holds: {
    hotel_id: string;
    room_count: number;
    hold_until: string;                 // release date
    deposit_paid: Money;
  }[]): Promise<InventoryHoldResult>;

  // Monitor inventory levels
  getInventoryStatus(event_id: string): EventInventoryStatus;
}

interface EventInventoryStatus {
  event_id: string;
  destination: string;

  hotels: {
    hotel_id: string;
    hotel_name: string;
    total_rooms: number;
    held_by_agency: number;
    sold: number;
    available: number;
    release_date: string;
    days_until_release: number;
    release_warning: boolean;
  }[];

  flights: {
    route: string;
    total_seats: number;
    held: number;
    sold: number;
    available: number;
    fare_locked: boolean;
  }[];

  event_tickets: {
    type: string;
    total: number;
    held: number;
    sold: number;
    available: number;
  };
}

// ── Event inventory dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Inventory — Diwali Goa Packages                 │
// │  Release deadline: Sep 15 (18 days away)              │
// │                                                       │
// │  Hotels:                                              │
// │  Taj Village     | 20 held | 14 sold | 6 left  ⚠️   │
// │  Novotel Goa     | 15 held |  8 sold | 7 left       │
// │  Holiday Inn     | 10 held |  3 sold | 7 left       │
// │                                                       │
// │  Flights:                                             │
// │  BOM→GOI (Oct 18) | 30 held | 22 sold | 8 left      │
// │  GOI→BOM (Oct 22) | 30 held | 22 sold | 8 left      │
// │                                                       │
// │  Actions:                                             │
// │  ⚠️ Taj Village: 6 rooms unsold, release in 18 days  │
// │     → Send reminder to 12 warm leads                 │
// │     → Offer 10% discount on remaining rooms          │
// │     → Or release 3 rooms to reduce exposure          │
// │                                                       │
// │  Total inventory value: ₹18.5L                       │
// │  Sold: ₹12.8L (69%) | At risk: ₹5.7L (31%)          │
// │  Deposit paid: ₹3.2L | Forfeit risk: ₹1.8L          │
// └─────────────────────────────────────────────────────┘
```

### Event Marketing Automation

```typescript
// ── Event marketing triggers ──
// ┌─────────────────────────────────────────────────────┐
// │  Automated Event Marketing Triggers                   │
// │                                                       │
// │  Trigger                          | Action            │
// │  ─────────────────────────────────────────────────── │
// │  Event 12 weeks away              | Send "early bird"│
// │                                    | to past customers│
// │                                    | for same destination│
// │                                                       │
// │  Event 8 weeks away               | Push to warm     │
// │                                    | leads + social   │
// │                                    | media campaign   │
// │                                                       │
// │  Inventory > 50% sold             | "Selling fast!"  │
// │                                    | urgency campaign │
// │                                                       │
// │  Inventory > 80% sold             | "Almost gone!"   │
// │                                    | final push       │
// │                                                       │
// │  Inventory release in 2 weeks     | Discount unsold  │
// │                                    | inventory        │
// │                                                       │
// │  Event 2 weeks away               | "Last minute"    │
// │                                    | deals at premium │
// │                                                       │
// │  Event completed                  | Send feedback    │
// │                                    | + next year waitlist│
// │                                                       │
// │  Same event next year announced   | Auto-notify      │
// │                                    | previous bookers │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Inventory risk** — Holding hotel rooms and flight seats requires deposits. Unsold inventory is a direct financial loss. Need conservative hold strategies with release options.

2. **Package pricing complexity** — Event packages bundle multiple components with different markup levels. Pricing must account for event premium, commission, and competitive positioning simultaneously.

3. **Multi-event trips** — Some trips span multiple events (e.g., Diwali in Goa + Christmas in Kerala). Package design must handle overlapping event calendars.

4. **Cancellation cascade** — If an event is cancelled (COVID, weather), all linked packages need cascading cancellations, refunds, and customer communication.

---

## Next Steps

- [ ] Build event package creation toolkit with templates
- [ ] Create event inventory management with hold/release tracking
- [ ] Implement event marketing automation triggers
- [ ] Design event cancellation handling workflow
