# Travel Weather Intelligence — Weather-Aware Trip Planning

> Research document for best-time-to-visit engine, activity-weather matching, seasonal scoring, and packing list generation.

---

## Key Questions

1. **How do we determine the best time to visit a destination?**
2. **How do we match activities to weather conditions?**
3. **How do we generate weather-based packing lists?**
4. **What India-specific weather considerations affect planning?**

---

## Research Areas

### Best-Time-to-Visit Engine

```typescript
interface BestTimeEngine {
  getBestMonths(destination: string, preferences: WeatherPreferences): MonthScore[];
  getWeatherSummary(destination: string, month: number): WeatherSummary;
  compareDestinations(destinations: string[], dates: DateRange): DestinationWeatherComparison;
}

interface MonthScore {
  month: number;
  month_name: string;
  score: number;                       // 0-100
  avg_temp_c: { min: number; max: number };
  avg_rainfall_mm: number;
  rainy_days: number;
  sunshine_hours: number;
  humidity_percentage: number;
  highlights: string[];                // "Cherry blossom season", "Diwali"
  warnings: string[];                  // "Monsoon season", "Peak heat"
  crowd_level: "LOW" | "MODERATE" | "HIGH" | "PEAK";
  price_level: "BUDGET" | "MODERATE" | "HIGH" | "PEAK";
}

// ── Best time example: Singapore ──
// ┌─────────────────────────────────────────────────────┐
// │  Singapore — Monthly Weather Scores                    │
// │                                                       │
// │  Jan  ████████████████████████████████████░░ 78       │
// │  Feb  ██████████████████████████████████████ 82       │
// │  Mar  ████████████████████████████████████░░ 76       │
// │  Apr  ██████████████████████████████████░░░░ 70       │
// │  May  ████████████████████████████████░░░░░░ 65       │
// │  Jun  ██████████████████████████████████░░░░ 68       │
// │  Jul  ████████████████████████████████████░░ 74       │
// │  Aug  ██████████████████████████████████████ 80       │
// │  Sep  ██████████████████████████████████████ 82       │
// │  Oct  ██████████████████████████░░░░░░░░░░░░ 58       │
// │  Nov  ████████████████████░░░░░░░░░░░░░░░░░░ 48       │
// │  Dec  ██████████████████████░░░░░░░░░░░░░░░░ 52       │
// │                                                       │
// │  Best: Feb, Aug-Sep (dry, pleasant)                   │
// │  Worst: Nov-Dec (monsoon, heavy rain)                 │
// └─────────────────────────────────────────────────────┘
```

### Activity-Weather Matching

```typescript
interface ActivityWeatherMatcher {
  score(activity: string, weather: WeatherData): ActivityWeatherScore;
  suggestAlternatives(activity: string, weather: WeatherData): AlternativeActivity[];
}

interface ActivityWeatherScore {
  activity: string;
  feasible: boolean;
  score: number;                       // 0-100
  ideal_conditions: string;
  current_conditions: string;
  recommendations: string[];
}

// ── Activity weather rules ──
// ┌─────────────────────────────────────────────────────┐
// │  Activity         | Ideal Weather   | Avoid          │
// │  ─────────────────────────────────────────────────── │
// │  Beach            | 28-35°C, sunny  │ Rain, >38°C   │
// │  Hiking           | 15-25°C, clear  │ Rain, fog     │
// │  Wildlife safari  | 20-30°C, dry    │ Heavy rain    │
// │  City tour        | 20-30°C, any    │ >40°C, storm  │
// │  Photography      | Golden hour,    │ Overcast,     │
// │                   | partly cloudy   │ heavy rain    │
// │  Water sports     | 25-35°C, calm   │ Wind >30kmh  │
// │  Temple visit     | Any             │ Festival crowds│
// │  Shopping         | Any             │ Extreme heat  │
// │  Outdoor dining   | 20-30°C, clear  │ Rain, wind    │
// └─────────────────────────────────────────────────────┘
```

### Packing List Generator

```typescript
interface PackingListGenerator {
  generate(destination: string, dates: DateRange, activities: string[]): PackingList;
}

interface PackingList {
  destination: string;
  dates: DateRange;
  weather_summary: string;             // "Tropical, 28-34°C, occasional rain"

  categories: {
    clothing: PackingItem[];
    accessories: PackingItem[];
    electronics: PackingItem[];
    documents: PackingItem[];
    health: PackingItem[];
    miscellaneous: PackingItem[];
  };
}

interface PackingItem {
  name: string;
  quantity: number;
  reason: string;                      // "Monsoon season: expect rain"
  category: "ESSENTIAL" | "RECOMMENDED" | "OPTIONAL";
}

// ── Example: Singapore in November (monsoon) ──
// ┌─────────────────────────────────────────────────────┐
// │  Packing List: Singapore, Nov 10-15                   │
// │  Weather: 25-31°C, monsoon, heavy rain likely        │
// │                                                       │
// │  ESSENTIAL:                                           │
// │  ☂️ Umbrella / foldable raincoat (daily rain expected)│
// │  👟 Waterproof shoes (monsoon puddles)                │
// │  🧴 Sunscreen SPF 50 (UV still high in rain)        │
// │  💧 Water bottle (stay hydrated, 31°C)               │
// │  🔌 Universal adapter (Singapore Type G)             │
// │                                                       │
// │  CLOTHING:                                            │
// │  - Light cotton t-shirts × 6 (humid, 80%+)          │
// │  - Shorts / light trousers × 4                       │
// │  - Swimwear × 2 (hotel pool)                         │
// │  - Light rain jacket × 1                              │
// │  - Flip-flops + walking shoes                         │
// │                                                       │
// │  INDIA-SPECIFIC:                                      │
// │  - Copies of passport, visa, insurance               │
// │  - Indian SIM / int'l roaming plan                   │
// │  - INR → SGD conversion receipt (for customs)       │
// └─────────────────────────────────────────────────────┘
```

### India-Specific Weather Planning

```typescript
// ── India seasonal travel rules ──
// ┌─────────────────────────────────────────────────────┐
// │  Season     | Best For          | Avoid              │
// │  ─────────────────────────────────────────────────── │
// │  Winter     | Rajasthan, Goa,   | Ladakh,           │
// │  (Oct-Mar)  | Kerala, Tamil Nadu| hill stations     │
// │             |                   | (freezing)         │
// │  Summer     | Ladakh, hill      | Rajasthan,        │
// │  (Apr-Jun)  | stations,        | plains (45°C+)     │
// │             | Northeast India   |                    │
// │  Monsoon    | Ladakh, Rajasthan| Kerala, Goa       │
// │  (Jun-Sep)  | (desert rain is   | (heavy flooding)  │
// │             |  minimal)         |                    │
// │  Post-      | Everywhere        | N/A                │
// │  monsoon    | (best season)     |                    │
// │  (Sep-Nov)  |                   |                    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Climate change uncertainty** — Historical weather patterns are shifting. Monsoon dates are less predictable than 10 years ago. Need recent-year weighting.

2. **Indoor alternative suggestions** — When weather ruins outdoor plans, the system should proactively suggest indoor alternatives without the agent asking.

3. **Multi-destination weather variance** — A 10-day trip across 3 cities may have very different weather. Packing lists must cover the most demanding conditions.

4. **Customer weather tolerance** — Some customers don't mind rain (photographers love moody weather), others cancel at a drop. Need preference-based weather sensitivity.

---

## Next Steps

- [ ] Build best-time-to-visit engine with climate norms database
- [ ] Implement activity-weather matching rules engine
- [ ] Create packing list generator with weather-based recommendations
- [ ] Build India-specific seasonal travel calendar
- [ ] Design weather sensitivity preference in customer profiles
