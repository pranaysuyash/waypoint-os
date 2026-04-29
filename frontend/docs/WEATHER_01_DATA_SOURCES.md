# Travel Weather Intelligence — Data Sources & Aggregation

> Research document for weather data sources, API integration, data granularity, India meteorological integration, and caching strategies.

---

## Key Questions

1. **What weather data sources are available and reliable?**
2. **How do we integrate IMD data for Indian destinations?**
3. **What data granularity do different travel use cases need?**
4. **How do we cache and refresh weather data efficiently?**

---

## Research Areas

### Weather Data Architecture

```typescript
interface WeatherDataSource {
  provider: WeatherProvider;
  api_endpoint: string;
  api_key: string;
  rate_limits: RateLimit;
  pricing: WeatherPricing;
  coverage: "GLOBAL" | "INDIA_ONLY" | "REGIONAL";
  granularity: WeatherGranularity[];
  reliability_score: number;           // 0-1
}

type WeatherProvider =
  | "OPENWEATHERMAP" | "WEATHERAPI" | "ACCUWEATHER"
  | "WEATHERBIT" | "VISUAL_CROSSING" | "TOMORROW_IO"
  | "IMD"                              // India Meteorological Department
  | "MAPMYINDIA_WEATHER";              // India-specific

type WeatherGranularity =
  | "CURRENT"            // real-time conditions
  | "HOURLY_FORECAST"    // next 48-120 hours
  | "DAILY_FORECAST"     // next 7-16 days
  | "MONTHLY_OUTLOOK"    // next 3-6 months
  | "HISTORICAL"         // past years data
  | "CLIMATE_NORMS";     // 30-year averages

// ── Provider comparison ──
// ┌─────────────────────────────────────────────────────┐
// │  Provider        | Free Tier  | Forecast | India    │
// │  ─────────────────────────────────────────────────── │
// │  OpenWeatherMap  | 60/min     | 5d hourly| ✅       │
// │  WeatherAPI      | 14.3M/mo   | 14d daily| ✅       │
// │  AccuWeather     | 50/day     | 5d hourly| ✅       │
// │  Tomorrow.io     | 25/day     | 15d daily| ✅       │
// │  IMD             | Govt API   | 7d daily | ★ Best   │
// │  Visual Crossing | 1000/d     | 15d daily| ✅       │
// └─────────────────────────────────────────────────────┘
```

### Weather Data Model

```typescript
interface WeatherData {
  location: GeoLocation;
  destination_name: string;
  fetched_at: string;
  source: WeatherProvider;

  current: CurrentWeather | null;
  forecast: DailyForecast[] | null;
  alerts: WeatherAlert[] | null;
  historical: HistoricalWeather[] | null;
  climate_norms: ClimateNorms | null;
}

interface CurrentWeather {
  temperature_c: number;
  feels_like_c: number;
  humidity_percentage: number;
  wind_speed_kmh: number;
  wind_direction: string;
  precipitation_mm: number;
  visibility_km: number;
  uv_index: number;
  condition: WeatherCondition;
  icon: string;
  description: string;
}

type WeatherCondition =
  | "CLEAR" | "PARTLY_CLOUDY" | "CLOUDY" | "OVERCAST"
  | "LIGHT_RAIN" | "RAIN" | "HEAVY_RAIN" | "THUNDERSTORM"
  | "DRIZZLE" | "SNOW" | "FOG" | "MIST" | "HAZE"
  | "DUST" | "TORNADO" | "TROPICAL_STORM" | "HAIL";

interface DailyForecast {
  date: string;
  temp_max_c: number;
  temp_min_c: number;
  temp_feels_like_max_c: number;
  temp_feels_like_min_c: number;
  humidity_percentage: number;
  precipitation_probability: number;    // 0-100%
  precipitation_mm: number;
  wind_max_kmh: number;
  uv_index: number;
  condition: WeatherCondition;
  sunrise: string;
  sunset: string;

  // Travel-specific scoring
  outdoor_activity_score: number;       // 0-100
  sightseeing_score: number;
  beach_score: number;
  adventure_score: number;
}

interface WeatherAlert {
  severity: "MINOR" | "MODERATE" | "SEVERE" | "EXTREME";
  type: "HEAT_WAVE" | "COLD_WAVE" | "HEAVY_RAIN" | "CYCLONE"
    | "THUNDERSTORM" | "FOG" | "DUST_STORM" | "FLOOD";
  headline: string;
  description: string;
  effective_from: string;
  effective_until: string;
  affected_areas: string[];
}
```

### India-Specific: IMD Integration

```typescript
// ── IMD (India Meteorological Department) Integration ──
// ┌─────────────────────────────────────────────────────┐
// │  IMD provides:                                        │
// │  - City-level forecasts (300+ cities)                 │
// │  - District-level warnings                            │
// │  - Cyclone tracking (Bay of Bengal, Arabian Sea)     │
// │  - Monsoon progress tracking                         │
// │  - Heat wave warnings                                │
// │  - Cold wave warnings                                │
// │  - Rainfall maps                                      │
// │  - Agricultural weather (relevant for rural tourism) │
// │                                                       │
// │  Data format: JSON / XML / HTML                       │
// │  Update frequency: Every 3 hours                     │
// │  Monsoon special: Daily monsoon progress reports     │
// │                                                       │
// │  Key URLs:                                            │
// │  - mausam.imd.gov.in (public portal)                 │
// │  - API endpoint for programmatic access              │
// │                                                       │
// │  Priority alerts for Indian destinations:            │
// │  - Heat wave: >45°C plains, >40°C coastal            │
// │  - Cyclone: Bay of Bengal tracking                   │
// │  - Monsoon: Kerala onset, withdrawal dates           │
// │  - Fog: Delhi/North India winter (Dec-Jan)           │
// └─────────────────────────────────────────────────────┘
```

### Caching & Refresh Strategy

```typescript
interface WeatherCacheStrategy {
  // Current weather: refresh every 30 minutes
  current: { ttl_minutes: 30 };

  // Hourly forecast: refresh every 2 hours
  hourly: { ttl_minutes: 120 };

  // Daily forecast: refresh every 6 hours
  daily: { ttl_minutes: 360 };

  // Historical data: cache indefinitely (doesn't change)
  historical: { ttl_minutes: null };    // never expires

  // Climate norms: cache for 30 days
  climate: { ttl_minutes: 43200 };

  // Active trip destinations: pre-fetch, shorter TTL
  active_trips: { ttl_minutes: 15 };    // more frequent for active trips
}

// ── Caching architecture ──
// ┌─────────────────────────────────────────────────────┐
// │  Request → Check Redis Cache                           │
// │     ├── Hit → Return cached data                      │
// │     └── Miss → Fetch from API                         │
// │              ├── Store in Redis (with TTL)            │
// │              └── Return to caller                     │
// │                                                       │
// │  Pre-fetching:                                        │
// │  - All active trip destinations: every 15 min        │
// │  - Popular destinations: every 30 min                │
// │  - Search destinations: on-demand + cache            │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Forecast accuracy beyond 7 days** — Weather forecasts beyond 7 days are unreliable. Monthly outlooks for trip planning (30+ days out) need climate norms, not forecasts.

2. **Micro-climate coverage** — Tourist destinations often have micro-climates (hill stations, coastal areas) not captured by city-level weather data.

3. **IMD API reliability** — Government APIs may have downtime or rate limits. Need fallback to commercial providers.

4. **Real-time alert latency** — Cyclone and severe weather alerts need near-real-time delivery. 30-minute cache delays are unacceptable for emergencies.

---

## Next Steps

- [ ] Integrate primary weather API (WeatherAPI or OpenWeatherMap)
- [ ] Add IMD integration for Indian destination accuracy
- [ ] Build weather data caching layer with active-trip pre-fetching
- [ ] Create weather alert subscription system
- [ ] Design micro-climate data enrichment for tourist destinations
