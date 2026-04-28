# MICE Venues — Venue Sourcing & Management

> Research document for venue discovery, evaluation, and booking management for events.

---

## Key Questions

1. **What venue types exist in the MICE ecosystem, and how do their booking patterns differ?**
2. **How do we source venues across geographies with consistent data quality?**
3. **What's the minimum venue data needed for meaningful search and comparison?**
4. **How do we handle venue holds, provisional bookings, and booking confirmations?**
5. **What virtual/hybrid venue capabilities should we support?**

---

## Research Areas

### Venue Taxonomy

```typescript
type VenueType =
  | 'hotel_ballroom'       // Hotel meeting/ballroom space
  | 'convention_center'    // Standalone convention/exhibition center
  | 'business_hotel'       // Business hotel with meeting rooms
  | 'resort'               // Resort with event facilities
  | 'standalone_venue'     // Independent event venue
  | 'outdoor'              // Gardens, beaches, terraces
  | 'restaurant_private'   // Restaurant private dining/events
  | 'coworking_space'      // Flexible meeting spaces
  | 'heritage_property'    // Palaces, forts, heritage buildings
  | 'virtual'              // Virtual event platform
  | 'hybrid';              // Physical + virtual hybrid

interface VenueProfile {
  venueId: string;
  name: string;
  type: VenueType;
  location: VenueLocation;
  capacity: VenueCapacity;
  spaces: VenueSpace[];
  amenities: VenueAmenity[];
  policies: VenuePolicy;
  media: VenueMedia[];
  rating: number;
  reviewCount: number;
}

interface VenueSpace {
  spaceId: string;
  name: string;
  type: SpaceType;
  capacity: SpaceCapacity;      // Different configurations
  dimensions: { length: number; width: number; height: number };
  basePrice: number;
  hourlyRate?: number;
  fullDayRate: number;
  halfDayRate: number;
  setupStyles: SetupStyle[];
  avEquipment: string[];
  accessibility: string[];
  images: string[];
}

type SetupStyle =
  | 'theater'       // Rows of chairs facing front
  | 'classroom'     // Tables and chairs facing front
  | 'boardroom'     // Single large table
  | 'ushape'        // U-shaped table arrangement
  | 'hollow_square' // Square of tables with open center
  | 'banquet'       // Round tables for dining
  | 'cocktail'      // Standing reception
  | 'exhibition'    // Booth/grid layout
  | 'hybrid';       // Mixed physical-virtual setup

interface SpaceCapacity {
  theater: number;
  classroom: number;
  boardroom: number;
  banquet: number;
  cocktail: number;
}
```

### Venue Search & Discovery

**Search dimensions for MICE venues:**

| Dimension | Type | Example |
|-----------|------|---------|
| Location | City, area, landmark | "Near Bangalore airport" |
| Capacity | Minimum attendees | "200+ theater style" |
| Event type | Meeting, conference, wedding | "Corporate conference" |
| Date availability | Specific dates or ranges | "Dec 15-17, 2026" |
| Budget | Per-day or total | "Under ₹2L per day" |
| Setup style | Required configuration | "Theater + classroom breakout" |
| Amenities | Required features | "AV, WiFi, parking, outdoor space" |
| F&B capability | Required catering | "In-house, vegetarian options" |
| Accessibility | Required access features | "Wheelchair accessible, elevator" |

**Open questions:**
- Should we maintain our own venue database or integrate with venue marketplaces (VenueLook, Weddingz)?
- How do we handle venues that don't have digital presence?
- What's the search UX for MICE vs. leisure venue discovery?

### Booking Flow for Venues

**MICE venue booking differs significantly from hotel booking:**

```typescript
interface VenueBooking {
  bookingId: string;
  venueId: string;
  spaces: SpaceBooking[];
  eventType: MICEType;
  status: VenueBookingStatus;
  holds: VenueHold[];
  pricing: VenuePricing;
  addOns: VenueAddOn[];
}

type VenueBookingStatus =
  | 'inquiry'           // Initial inquiry sent
  | 'proposal_received' // Venue sent proposal
  | 'hold_placed'       // Space tentatively held
  | 'hold_confirmed'    // Hold confirmed with deposit
  | 'contract_signed'   // Contract executed
  | 'deposit_paid'      // First deposit received
  | 'confirmed'         // Fully confirmed
  | 'in_progress'       // Event happening
  | 'completed'         // Event finished
  | 'cancelled';

interface VenueHold {
  holdId: string;
  spaces: string[];
  dates: DateRange;
  holdType: 'soft' | 'hard';
  expiresAt: Date;
  depositRequired: number;
  depositPaid: boolean;
}
```

**Research needed:**
- What's the standard hold period for venues in India?
- How do soft holds convert to hard holds and then to confirmed bookings?
- What's the typical deposit structure (10% hold, 40% contract, 50% event)?

---

## Open Problems

1. **Venue data acquisition** — Unlike hotels (which have standardized data via GDS), venues have fragmented, inconsistent data. How to build and maintain a reliable venue database?

2. **Multi-space bookings** — A conference needs a ballroom for plenary + 5 breakout rooms + exhibition area + dining hall. How to model availability across all spaces simultaneously?

3. **Seasonal venue pricing** — Wedding season (Nov-Feb) vs. conference season (Mar-May) vs. off-season pricing. Venues may have 3-4x price variation.

4. **Provisional holds at scale** — A popular venue may receive 5 holds for the same date. How to manage priority queues without creating false scarcity?

5. **Virtual/hybrid venue modeling** — How to represent virtual event platforms as "venues" with their own capacity, features, and pricing?

---

## Next Steps

- [ ] Research venue data aggregators in India (VenueLook, BookEventZ, Weddingz)
- [ ] Study venue booking workflow patterns from event management platforms
- [ ] Design multi-space availability engine
- [ ] Investigate virtual venue platform APIs (Zoom Events, Hopin, Airmeet)
- [ ] Map venue pricing variation patterns across seasons
