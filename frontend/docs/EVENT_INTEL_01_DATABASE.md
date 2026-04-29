# Destination Event & Festival Intelligence — Event Database

> Research document for destination event databases, festival calendars, sports events, concerts, cultural events, and their impact on travel demand and pricing.

---

## Key Questions

1. **What events drive travel demand at each destination?**
2. **How do we build and maintain an event database?**
3. **What India-specific festivals and events affect travel patterns?**
4. **How do events correlate with pricing and availability?**

---

## Research Areas

### Destination Event Database

```typescript
interface DestinationEvent {
  id: string;
  name: string;
  destination: string;
  country: string;

  // Event details
  type: "FESTIVAL" | "SPORTS" | "CONCERT" | "CULTURAL" | "CONFERENCE" | "HOLIDAY" | "SEASONAL" | "RELIGIOUS" | "NATURE" | "EXPO";
  category: string;                     // "Music", "Cricket", "Diwali", "Cherry Blossom"
  description: string;

  // Timing
  start_date: string;
  end_date: string;
  recurrence: "ANNUAL" | "BIANNUAL" | "ONE_TIME" | "IRREGULAR";
  fixed_date: boolean;                  // fixed calendar date vs movable (lunar)
  next_occurrence: string;              // for annual events

  // Impact metrics
  attendance: number | null;
  tourist_influx_multiplier: number;    // 1.5 = 50% more tourists than normal
  hotel_demand_multiplier: number;      // 2.0 = hotels fill 2x normal
  price_impact: "LOW" | "MODERATE" | "HIGH" | "EXTREME";
  avg_price_increase_pct: number;       // how much prices go up

  // Travel implications
  booking_advice: {
    book_how_far_ahead_weeks: number;   // how early to book
    availability_warning: string;       // "Hotels sell out 3 months before"
    best_for: string[];                 // ["families", "couples", "solo"]
    avoid_for: string[];                // ["budget travelers", "quiet seekers"]
  };

  // Sources
  sources: string[];
  last_verified: string;
}

// ── India event calendar (sample) ──
// ┌─────────────────────────────────────────────────────┐
// │  India Festival & Event Impact Calendar               │
// │                                                       │
// │  Month    | Event              | Impact | Price ↑    │
// │  ─────────────────────────────────────────────────── │
// │  January  | Republic Day       | MOD    | +15%       │
// │           | Pongal/Makar Sankr.| MOD    | +10% (South)│
// │           | Jaipur Lit Fest     | LOW    | +20% (Jai) │
// │  February | Taj Mahotsav       | LOW    | +15% (Agra)│
// │           | Goa Carnival        | HIGH   | +35% (Goa) │
// │  March    | Holi               | HIGH   | +25%       │
// │           | IPL Cricket starts  | HIGH   | +40% (host)│
// │  April    | Baisakhi           | MOD    | +15% (Pun) │
// │           | Easter             | MOD    | +20% (Goa) │
// │  May      | Ramadan (Eid)      | MOD    | +15%       │
// │           | Summer holidays     | EXTREME│ +50%       │
// │  June     | Rath Yatra (Puri)   | HIGH   | +30% (Puri)│
// │           | International Yoga  │ LOW    | +10% (Rish)│
// │  July     | Hemis Festival      | MOD    | +20% (Lad)│
// │           | Monsoon tourism     | LOW    | -15% (off) │
// │  August   | Independence Day    | LOW    | +5%        │
// │           | Onam               | HIGH   | +30% (Ker) │
// │           | Raksha Bandhan      | MOD    | +10%       │
// │  September| Ganesh Chaturthi   | HIGH   | +25% (Mum) │
// │           | Navratri begins     | MOD    | +15% (Guj) │
// │  October  | Dussehra            | HIGH   | +25%       │
// │           | Durga Puja          | HIGH   | +35% (Kol) │
// │           | Marwar Festival     | LOW    | +15% (Jod) │
// │  November | Diwali             | EXTREME│ +45%       │
// │           | Pushkar Camel Fair  | HIGH   | +30% (Push)│
// │           | Guru Purab         | MOD    | +10% (Pun) │
// │  December | Christmas           | HIGH   | +30% (Goa) │
// │           | New Year's Eve      | EXTREME│ +60% (Goa) │
// │           | Rann Utsav         | MOD    | +20% (Kutch)│
// └─────────────────────────────────────────────────────┘
```

### International Event Intelligence

```typescript
// ── International events affecting Indian outbound travel ──
// ┌─────────────────────────────────────────────────────┐
// │  Top International Events for Indian Travelers         │
// │                                                       │
// │  Event              | Dest.   | When    | Impact      │
// │  ─────────────────────────────────────────────────── │
// │  Dubai Shopping Fest| Dubai   | Jan-Feb | HIGH (+30%) │
// │  Chinese New Year   | Singapore| Jan-Feb| HIGH (+25%) │
// │  Cherry Blossom     | Japan   | Mar-Apr | MOD (+20%) │
// │  Songkran          | Thailand| Apr     | HIGH (+25%) │
// │  Ramadan            | Dubai   | Varies  | LOW (-10%) │
// │  Summer Olympics    | Various | Jul-Aug | EXTREME     │
// │  Wimbledon          | London  | Jun-Jul | MOD (+15%) │
// │  Edinburgh Fringe   | Scotland| Aug     | MOD (+15%) │
// │  Oktoberfest        | Munich  | Sep-Oct | HIGH (+30%)│
// │  Hajj Season       | Mecca   | Varies  | EXTREME     │
// │  Black Friday Sales | Dubai/US| Nov     | MOD (+15%) │
// │  Christmas Markets  | Europe  | Dec     | HIGH (+25%)│
// │  New Year Fireworks | Various | Dec 31  | EXTREME    │
// │                                                       │
// │  Booking lead times for events:                      │
// │  • Music concerts: 2-4 weeks                        │
// │  • Sports events: 4-8 weeks                         │
// │  • Festivals: 8-12 weeks                            │
// │  • New Year/Christmas: 16+ weeks                    │
// │  • Hajj: 6+ months (visa lottery)                   │
// └─────────────────────────────────────────────────────┘
```

### Event-Driven Pricing Impact

```typescript
interface EventPricingImpact {
  event_id: string;
  destination: string;

  // Hotel pricing
  hotels: {
    normal_avg_rate: Money;             // non-event period
    event_avg_rate: Money;              // during event
    premium_pct: number;                // price increase
    sellout_date: string | null;        // when hotels typically sell out
    last_room_available_weeks: number;  // how early last rooms go
  };

  // Flight pricing
  flights: {
    normal_avg_fare: Money;
    event_avg_fare: Money;
    premium_pct: number;
    sellout_date: string | null;
  };

  // Activities
  activities: {
    availability_impact: string;
    premium_pct: number;
    advance_booking_required: boolean;
  };
}

// ── Pricing impact example ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Pricing Impact: Diwali 2026                    │
// │                                                       │
// │  Goa (top domestic destination):                       │
// │  Hotels: ₹4,500/night → ₹8,500/night (+89%)         │
// │  Flights (Mumbai→Goa): ₹5,500 → ₹12,000 (+118%)   │
// │  Hotels sell out: 8 weeks before                     │
// │  Last flights fill: 4 weeks before                   │
// │                                                       │
// │  Singapore (top international):                        │
// │  Hotels: ₹8,000/night → ₹12,000/night (+50%)        │
// │  Flights (Delhi→SIN): ₹22,000 → ₹38,000 (+73%)    │
// │  Hotels sell out: 6 weeks before                     │
// │                                                       │
// │  Recommendation for agents:                           │
// │  • Quote Diwali trips by August (3 months ahead)     │
// │  • Lock hotel rates early, flights can wait till Sep │
// │  • Offer "book now, pay later" for early birds       │
// │  • Consider alternative: Sri Lanka (less price surge)│
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Event data accuracy** — Festival dates shift (lunar calendars). Event cancellations happen. Need multiple data sources and verification.

2. **Correlation vs causation** — Price increases during events may be coincidental (peak season overlap). Need to separate event-driven demand from seasonal demand.

3. **Hyper-local events** — A local marathon or temple festival may not be in global event databases but significantly affects local hotel availability.

4. **Event sentiment** — Some events (political summits, protests) negatively affect tourism. Event database must track both positive and negative demand impacts.

---

## Next Steps

- [ ] Build destination event database with India festival calendar
- [ ] Create event-pricing correlation engine
- [ ] Implement event-driven booking recommendation system
- [ ] Design event-aware trip planning suggestions
