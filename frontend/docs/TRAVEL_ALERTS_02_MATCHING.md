# Travel Alerts — Trip-Alert Matching Engine

> Research document for matching travel alerts to active trips and bookings.

---

## Key Questions

1. **How do we efficiently match alerts to the right trips without scanning every booking?**
2. **What's the matching granularity — destination city, hotel, airport, route segment?**
3. **How do we handle alerts that affect connecting flights but not the final destination?**
4. **What's the time window for matching (alerts about next 24h vs. next 30 days)?**
5. **How do we prioritize which affected trips get attention first?**

---

## Research Areas

### Matching Architecture

```typescript
interface TripAlertMatcher {
  // Index trips for fast geo-temporal lookup
  indexTrips(trips: Trip[]): void;
  // Match incoming alert against indexed trips
  matchAlert(alert: TravelAlert): AffectedTrip[];
  // Score the impact level for each trip
  scoreImpact(trip: Trip, alert: TravelAlert): ImpactScore;
}

interface Trip {
  tripId: string;
  travelers: Traveler[];
  segments: TripSegment[];
  dates: DateRange;
  status: TripStatus;
}

interface TripSegment {
  segmentId: string;
  type: 'flight' | 'hotel' | 'transfer' | 'activity' | 'cruise' | 'rail';
  location: GeoLocation;
  dates: DateRange;
  bookingRef: string;
  supplierId: string;
}

interface AffectedTrip {
  tripId: string;
  matchedSegments: MatchedSegment[];
  overallImpact: ImpactLevel;
  priority: number;
  recommendedActions: RecommendedAction[];
}

interface MatchedSegment {
  segmentId: string;
  alertId: string;
  matchType: MatchType;
  impactLevel: ImpactLevel;
}

type MatchType =
  | 'direct_location'     // Segment is in affected area
  | 'transit_through'     // Segment transits through affected area
  | 'origin_destination'  // Segment starts or ends in affected area
  | 'supplier_affected'   // Supplier (airline, hotel) is affected
  | 'route_affected';     // Travel route passes through affected area

type ImpactLevel = 'minimal' | 'moderate' | 'significant' | 'severe' | 'critical';
```

### Matching Strategies

**Spatial matching:**
- Point-in-polygon (segment location within alert geography)
- Route intersection (flight path or road route crosses alert zone)
- Proximity (segment within X km of alert zone)

**Temporal matching:**
- Alert time range overlaps with segment dates
- Alert is "ongoing" and segment is in the future
- Alert has a forecast window (e.g., storm expected in 48h)

**Priority scoring:**

```typescript
interface ImpactScore {
  safety: number;      // Risk to traveler safety (0-10)
  disruption: number;  // Likelihood of travel disruption (0-10)
  proximity: number;   // How close the trip is to the event (0-10)
  urgency: number;     // How soon the trip is (0-10)
  composite: number;   // Weighted combination
}

// Priority factors:
// - Trip departing in <48h gets higher urgency
// - "Do not travel" advisory gets max safety score
// - Direct location match gets higher proximity than route match
// - Travelers already in destination get highest priority
```

---

## Open Problems

1. **Near-miss detection** — A flight connecting through an affected airport but not stopping there. Should this be flagged? What about flights overflying a conflict zone?

2. **Multi-segment cascading** — A cancelled flight in Segment 2 disrupts Segment 3 (connecting flight) and Segment 4 (hotel check-in). How to model cascading impacts?

3. **Performance at scale** — With 10,000+ active trips and 100+ daily alerts, brute-force matching is O(n*m). Need efficient spatial indexing.

4. **False positive management** — Over-alerting causes agents to ignore warnings. Need high precision on critical alerts, broader recall on informational ones.

5. **Historical matching** — "Was this trip affected by any alerts?" requires retroactive matching against historical alert data.

---

## Next Steps

- [ ] Research spatial indexing approaches for geo-temporal matching (PostGIS, GeoHash, H3)
- [ ] Design matching pipeline with configurable rules per alert type
- [ ] Prototype priority scoring model
- [ ] Study cascade impact modeling for multi-segment trips
- [ ] Benchmark matching performance with realistic trip volumes
