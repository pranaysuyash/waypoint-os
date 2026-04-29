# Travel Maps & Navigation — Itinerary Visualization

> Research document for interactive trip maps, route visualization, timeline sliders, and map embedding in documents.

---

## Key Questions

1. **How do we visualize multi-day itineraries on interactive maps?**
2. **What markers and overlays enhance trip understanding?**
3. **How do we create timeline-based map exploration?**
4. **How do we embed maps in PDFs and WhatsApp shares?**

---

## Research Areas

### Interactive Itinerary Map

```typescript
interface ItineraryMap {
  trip_id: string;
  center: GeoLocation;
  zoom: number;

  // Markers
  markers: MapMarker[];
  // Route lines
  routes: MapRoute[];
  // Overlays
  overlays: MapOverlay[];

  // Interaction
  selected_day: number | null;          // null = show all days
  timeline_mode: boolean;
}

interface MapMarker {
  id: string;
  type: "HOTEL" | "RESTAURANT" | "ATTRACTION" | "AIRPORT" | "STATION" | "ACTIVITY" | "MEETING_POINT";
  location: GeoLocation;
  day: number;
  order_in_day: number;
  label: string;
  icon: string;
  color: string;                       // color-coded by day
  popup: MarkerPopup;
}

interface MarkerPopup {
  title: string;
  subtitle: string;                    // "Day 2, Activity 3"
  details: string;                     // "10:00 - 12:00"
  image_url: string | null;
  rating: number | null;
  booking_ref: string | null;
}

interface MapRoute {
  from: GeoLocation;
  to: GeoLocation;
  day: number;
  transport_mode: TransportMode;
  color: string;
  dashed: boolean;                     // dashed for flights
  duration_minutes: number;
  distance_km: number;
}

// ── Itinerary map visualization ──
// ┌─────────────────────────────────────────────────────┐
// │  ┌─ Map ──────────────────────────────────────┐     │
// │  │                                              │     │
// │  │   ✈️ DEL ─ ─ ─ ─ ─ ─ ─ ─ ─ ✈️ SIN        │     │
// │  │    (Day 1, flight arc)                       │     │
// │  │                                              │     │
// │  │          🏨 Marina Bay Sands (Day 1-3)       │     │
// │  │          │                                   │     │
// │  │          ├── 🌳 Gardens by the Bay           │     │
// │  │          │        (Day 1, 16:00)             │     │
// │  │          │                                   │     │
// │  │          ├── 🎡 Sentosa (Day 2, full day)    │     │
// │  │          │                                   │     │
// │  │          └── 🛍️ Orchard Road (Day 2, PM)    │     │
// │  │                                              │     │
// │  │          🏨 Hotel 81 (Day 4-5)               │     │
// │  │          │                                   │     │
// │  │          └── 🦁 Zoo (Day 4, AM)             │     │
// │  │                                              │     │
// │  │   ✈️ SIN ─ ─ ─ ─ ─ ─ ─ ─ ─ ✈️ DEL        │     │
// │  │    (Day 5, return flight)                    │     │
// │  └──────────────────────────────────────────────┘     │
// │                                                       │
// │  [Day 1] [Day 2] [Day 3] [Day 4] [Day 5] [All]      │
// │  ◄──────── Timeline slider ────────►                  │
// └─────────────────────────────────────────────────────┘
```

### Map Embedding in Documents

```typescript
interface StaticMapGenerator {
  generateTripMap(trip_id: string): Promise<string>; // URL to static map image
  generateDayMap(trip_id: string, day: number): Promise<string>;
}

// ── Static map for PDF embedding ──
// ┌─────────────────────────────────────────────────────┐
// │  PDF Itinerary: embedded static map                   │
// │                                                       │
// │  ┌─ Day 2: Sentosa ──────────────────────────┐      │
// │  │ [Static map showing:                       │      │
// │  │  Hotel → Sentosa (ferry route)             │      │
// │  │  Sentosa: Universal Studios, Beach,        │      │
// │  │           S.E.A. Aquarium marked           │      │
// │  │  Return: Sentosa → Hotel (cable car)       │      │
// │  │ ]                                         │      │
// │  └────────────────────────────────────────────┘      │
// │                                                       │
// │  Transport: Hotel → Sentosa ferry (15 min)           │
// │  Activities: Universal Studios (10:00-14:00)        │
// │  Lunch: Todai Restaurant (14:00-15:00)              │
// │  Beach: Palawan Beach (15:30-17:00)                 │
// │  Return: Cable car (17:30)                           │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Multi-city route visualization** — Trips spanning distant cities (Delhi → Singapore → Bali) make the map either too zoomed out or require split views.

2. **Real-time traffic overlay** — Showing current traffic on route lines helps but adds API cost. Need to limit to active trips only.

3. **Map accessibility** — Map visualizations are inherently visual. Need text-based alternatives for screen readers and accessibility compliance.

---

## Next Steps

- [ ] Build interactive itinerary map with day-by-day filtering
- [ ] Create static map generator for PDF embedding
- [ ] Implement timeline slider for progressive route display
- [ ] Design WhatsApp shareable map preview images
