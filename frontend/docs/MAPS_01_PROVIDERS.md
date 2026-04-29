# Travel Maps & Navigation — Provider Integration

> Research document for map provider comparison, India-specific providers, pricing models, feature comparison, and integration strategies.

---

## Key Questions

1. **Which map providers best serve the travel domain?**
2. **What India-specific map providers are available?**
3. **How do we handle map API costs at scale?**
4. **What caching strategies reduce map API costs?**

---

## Research Areas

### Provider Comparison

```typescript
// ── Map provider comparison for travel ──
// ┌─────────────────────────────────────────────────────────────┐
// │  Feature          | Google Maps | Mapbox | OSM    | MapMyIndia│
// │  ─────────────────────────────────────────────────────────── │
// │  Geocoding        | ★★★★★     | ★★★★  | ★★★   | ★★★★★ IN │
// │  Routing          | ★★★★★     | ★★★★  | ★★★   | ★★★★    │
// │  POI data         | ★★★★★     | ★★★   | ★★★   | ★★★★ IN │
// │  Street view      | ★★★★★     | ★★     | ★      | ★★★ IN  │
// │  3D buildings     | ★★★★      | ★★★★★ | ★★     | ★★      │
// │  India coverage   | ★★★★      | ★★★   | ★★★   | ★★★★★   │
// │  Offline support  | ★★★       | ★★★★★ | ★★★★★ | ★★      │
// │  Custom styling   | ★★★★      | ★★★★★ | ★★★   | ★★      │
// │  Free tier        | $200/mo   | 50K/mo | Free  | Limited  │
// │  Price/load       | $7/1K     | $5/1K  | Free  | ₹2/call │
// │  ─────────────────────────────────────────────────────────── │
// │  Recommended: Mapbox for custom UI + Google fallback       │
// │  India: MapMyIndia for domestic, Google for international  │
// └─────────────────────────────────────────────────────────────┘

interface MapProviderConfig {
  provider: "GOOGLE" | "MAPBOX" | "OSM" | "MAPMYINDIA" | "HERE";
  api_key: string;
  features: MapFeature[];
  fallback_provider: string | null;
  rate_limits: RateLimit;
  pricing: MapPricing;
}

type MapFeature =
  | "GEOCODING" | "REVERSE_GEOCODING" | "ROUTING" | "DIRECTIONS"
  | "POI_SEARCH" | "AUTOCOMPLETE" | "STATIC_MAP" | "STREET_VIEW"
  | "TRAFFIC" | "DISTANCE_MATRIX" | "ELEVATION" | "TIMEZONE"
  | "OFFLINE_TILES" | "3D_TERRAIN" | "SATELLITE";
```

### Integration Architecture

```typescript
interface MapService {
  geocode(address: string): Promise<GeoLocation[]>;
  reverseGeocode(location: GeoLocation): Promise<Address>;
  route(waypoints: GeoLocation[], mode: TransportMode): Promise<Route>;
  searchPOI(query: string, location: GeoLocation, radius_km: number): Promise<POI[]>;
  staticMap(center: GeoLocation, markers: Marker[]): Promise<string>; // URL
  autocomplete(input: string, bounds: GeoBounds): Promise<PlaceSuggestion[]>;
}

// ── Provider routing strategy ──
// ┌─────────────────────────────────────────────────────┐
// │  Request → Check origin (India vs International)      │
// │     ├── India → MapMyIndia (primary)                 │
// │     │         → Google Maps (fallback)               │
// │     └── International → Mapbox (primary)             │
// │                        → Google Maps (fallback)      │
// │                                                       │
// │  Caching:                                             │
// │  - Geocoding results: cache 30 days                  │
// │  - Static map tiles: cache 7 days                    │
// │  - Route results: cache 1 hour                       │
// │  - POI data: cache 24 hours                          │
// └─────────────────────────────────────────────────────┘
```

### India-Specific: MapMyIndia Integration

```typescript
// ── MapMyIndia capabilities ──
// ┌─────────────────────────────────────────────────────┐
// │  Strengths:                                           │
// │  - Best Indian road data (village-level coverage)     │
// │  - Hindi + regional language support                  │
// │  - Toll plaza and checkpoint data                     │
// │  - Real-time traffic for major Indian cities          │
// │  - Indian address format (sector, colony, landmark)   │
// │  - Temple, mosque, gurudwara POI data                 │
// │  - Railway station and bus stand data                 │
// │                                                       │
// │  Weaknesses:                                          │
// │  - Limited international coverage                     │
// │  - No street view                                     │
// │  - Smaller developer ecosystem                        │
// │  - API documentation less comprehensive               │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Cost at scale** — Map API calls for 1000+ trips with geocoding, routing, and static maps can cost ₹50K+/month. Need aggressive caching and tile pre-rendering.

2. **Address format variation** — Indian addresses don't follow Western formats (landmark-based, no postal codes in rural areas). Geocoding accuracy varies significantly.

3. **Offline tile licensing** — Most commercial providers restrict offline tile caching. For traveler offline maps, need OSM-based solution.

4. **Provider lock-in** — Switching map providers requires UI and API changes. Need abstraction layer to allow provider switching.

---

## Next Steps

- [ ] Implement map service abstraction layer with provider routing
- [ ] Integrate Mapbox for primary map rendering
- [ ] Add MapMyIndia for Indian destination accuracy
- [ ] Build aggressive caching layer for geocoding and static maps
- [ ] Design provider fallback strategy for high availability
