# Travel Maps & Navigation — Real-Time Navigation

> Research document for turn-by-turn navigation, walking directions, offline maps, location sharing, and emergency SOS features.

---

## Key Questions

1. **How do we provide navigation to travelers during trips?**
2. **What offline map support is needed for connectivity-poor destinations?**
3. **How do location sharing and SOS work?**
4. **What India-specific navigation challenges exist?**

---

## Research Areas

### Traveler Navigation

```typescript
interface TravelerNavigation {
  // Waypoint-based navigation for trip activities
  getNextDirection(current_location: GeoLocation, next_activity: ScheduledActivity): NavigationInstruction;
  getWalkingTourRoute(activities: ScheduledActivity[]): WalkingTourRoute;
}

interface NavigationInstruction {
  distance_to_next: string;             // "200m"
  direction: string;                    // "Turn right onto Orchard Road"
  eta_minutes: number;
  transport_mode: "WALK" | "DRIVE" | "TRANSIT";
  landmark: string | null;             // "Turn right at the Merlion statue"
}

interface WalkingTourRoute {
  waypoints: GeoLocation[];
  total_distance_km: number;
  total_duration_minutes: number;
  stops: {
    activity: string;
    location: GeoLocation;
    duration_minutes: number;
    walking_from_previous_minutes: number;
  }[];
}

// ── India-specific navigation challenges ──
// ┌─────────────────────────────────────────────────────┐
// │  Challenge              | Solution                   │
// │  ─────────────────────────────────────────────────── │
// │  Address by landmark    | "Near Jain Temple,        │
// │  (not street address)   |  Johari Bazaar, Jaipur"   │
// │                         | Use POI-based navigation   │
// │                                                       │
// │  Auto-rickshaw routing  | Three-wheeler accessible   │
// │                         | routes, not car-only       │
// │                                                       │
// │  Temple complexes       | Internal walking routes    │
// │  (large, no roads)      | within campus boundaries   │
// │                                                       │
// │  Market areas           | Pedestrian-only zone       │
// │  (narrow lanes)         | navigation                 │
// │                                                       │
// │  Hindi/local signage    | Navigation instructions    │
// │                         | in preferred language       │
// └─────────────────────────────────────────────────────┘
```

### Offline Map Support

```typescript
interface OfflineMapManager {
  downloadRegion(destination: string, bounds: GeoBounds): Promise<OfflineMapPack>;
  getOfflineStatus(destination: string): OfflineMapStatus;
  cleanupExpiredPacks(): void;
}

interface OfflineMapPack {
  destination: string;
  bounds: GeoBounds;
  size_mb: number;
  downloaded_at: string;
  expires_at: string;                  // auto-update after 30 days
  includes: string[];                  // "streets", "pois", "transit"
}

// ── Offline strategy ──
// ┌─────────────────────────────────────────────────────┐
// │  Pre-trip: Auto-download offline maps for            │
// │  all destinations when trip is confirmed             │
// │                                                       │
// │  Based on OSM tiles (no licensing restriction):     │
// │  - City-level detail (streets, POIs)                │
// │  - Surrounding area (50km radius)                   │
// │  - ~50-200MB per destination                        │
// │                                                       │
// │  Update: Refresh when WiFi available                 │
// │  Cleanup: Delete 7 days after trip ends              │
// └─────────────────────────────────────────────────────┘
```

### Location Sharing & SOS

```typescript
interface LocationSharing {
  trip_id: string;
  traveler_id: string;
  sharing_with: ("AGENT" | "GUIDE" | "FAMILY_MEMBER")[];
  mode: "CONTINUOUS" | "CHECK_IN" | "ON_DEMAND";
  frequency_minutes: number;
  active: boolean;
  started_at: string;
}

interface SOSSystem {
  triggerSOS(traveler_id: string, location: GeoLocation, trip_id: string): SOSResponse;
}

interface SOSResponse {
  sos_id: string;
  emergency_contacts_notified: string[];
  embassy_contact: string | null;
  nearest_hospital: { name: string; distance_km: number; phone: string } | null;
  police_contact: string;
  insurance_hotline: string | null;
  agent_notified: boolean;
  guide_notified: boolean;
}

// ── SOS flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Traveler taps SOS button in app                      │
// │       │                                               │
// │       ├── Immediate: Share GPS location              │
// │       ├── Notify: Assigned agent + guide             │
// │       ├── Show: Emergency contacts                   │
// │       │    ├── Local police: 100                     │
// │       │    ├── Embassy: +65-XXXX                    │
// │       │    ├── Insurance: 1800-XXX-XXXX              │
// │       │    └── Hospital: +65-XXXX (nearest)         │
// │       └── Log: Incident in trip record               │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Battery drain** — Continuous GPS tracking drains phone batteries quickly. Need adaptive tracking (frequent when moving, infrequent when stationary).

2. **Offline routing quality** — OSM-based offline routing may be less accurate than Google Maps in some regions. Need to set expectations.

3. **Privacy concerns** — Location sharing requires explicit consent and clear data retention policies. Family members tracking without consent is illegal.

---

## Next Steps

- [ ] Build traveler navigation with landmark-based directions
- [ ] Implement offline map download using OSM tiles
- [ ] Create location sharing with consent management
- [ ] Design SOS emergency system
- [ ] Build India-specific landmark-based routing
