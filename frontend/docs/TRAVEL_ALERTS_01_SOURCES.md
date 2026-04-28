# Travel Alerts — Advisory Data Sources & Feeds

> Research document for identifying and integrating travel advisory data sources.

---

## Key Questions

1. **What are the authoritative sources for travel safety advisories by country?**
2. **What data formats do these sources provide (API, RSS, scraped)?**
3. **How current is the data, and what's the update frequency?**
4. **How do we normalize advisories from different sources into a unified format?**
5. **What's the cost structure for commercial travel intelligence feeds?**

---

## Research Areas

### Advisory Source Landscape

**Government advisories:**

| Source | Coverage | Format | Update Frequency |
|--------|----------|--------|-----------------|
| India MEA | Indian citizens abroad | Website | Event-driven |
| US State Department | Global (4 levels) | API + RSS | As needed |
| UK FCDO | Global | API | As needed |
| Australia DFAT | Global | RSS | As needed |
| Canada Travel | Global | RSS | As needed |
| EU Travel Advisory | EU citizens | API | As needed |

**Commercial travel intelligence:**

| Provider | Coverage | Strengths | Cost |
|----------|----------|-----------|------|
| International SOS | Global | Medical + security | Enterprise license |
| Riskline | Global | Country risk reports | Per-seat |
| Sitata | Global | Real-time alerts | API pricing |
| Travelstitch | Regional | Southeast Asia focus | Moderate |
| WorldAware (JETRO) | Global | Corporate travel risk | Enterprise |

**Event data feeds:**

| Source | Type | Coverage |
|--------|------|----------|
| GDACS | Natural disasters | Global |
| PDC (Pacific Disaster Center) | Hazards | Asia-Pacific |
| WHO | Health emergencies | Global |
| IATA NOTAMs | Aviation disruptions | Global |
| FlightAware | Flight disruptions | Global |

```typescript
interface AdvisorySource {
  sourceId: string;
  name: string;
  type: 'government' | 'commercial' | 'news' | 'crowdsourced';
  coverage: string[];
  reliability: number;          // 0-1
  latency: string;              // Time between event and alert
  format: SourceFormat;
  cost: 'free' | 'freemium' | 'paid';
  integration: IntegrationDetail;
}

type SourceFormat =
  | 'rest_api'
  | 'rss_atom'
  | 'webhook'
  | 'email_digest'
  | 'web_scraping'
  | 'csv_dump';
```

### Alert Data Model

```typescript
interface TravelAlert {
  alertId: string;
  sources: AlertSource[];
  type: AlertType;
  severity: AlertSeverity;
  geography: AffectedGeography;
  timeRange: AlertTimeRange;
  description: string;
  recommendations: string[];
  affectedBookings: string[];     // Auto-matched booking IDs
  status: AlertStatus;
}

type AlertType =
  | 'natural_disaster'    // Earthquake, flood, hurricane
  | 'political_unrest'    // Protests, civil disturbance
  | 'health_advisory'     // Disease outbreak, pandemic
  | 'security_threat'     // Terrorism, crime wave
  | 'transport_disruption' // Airport closure, strike
  | 'weather_severe'      // Storm, extreme heat, blizzard
  | 'regulatory_change'   // Visa changes, entry requirements
  | 'infrastructure'      // Power outage, telecom disruption
  | 'environmental'       // Air quality, water contamination
  | 'mass_event';         // Major event causing congestion

type AlertSeverity =
  | 'informational'       // Be aware
  | 'advisory'            // Exercise caution
  | 'warning'             // Reconsider travel
  | 'critical'            // Do not travel / evacuate;

interface AffectedGeography {
  type: 'country' | 'region' | 'city' | 'radius';
  identifiers: string[];        // ISO country codes, city names, etc.
  coordinates?: { lat: number; lng: number; radiusKm: number };
}
```

---

## Open Problems

1. **Source normalization** — Different sources use different severity scales, geography granularity, and terminology. Normalizing these into a unified format without losing nuance is challenging.

2. **Alert fatigue** — Too many low-severity alerts desensitize agents. Need smart filtering and aggregation (e.g., "3 low-level alerts about Thailand" → one digest).

3. **Verification lag** — Social media reports are fast but unreliable. Government advisories are authoritative but slow. How to balance speed and accuracy?

4. **Geo-fencing precision** — An airport closure in Bangkok shouldn't alert travelers heading to Phuket. Need precise geo-matching against trip itineraries.

5. **Historical advisory data** — For insurance and liability purposes, we may need to prove what advisories were active at booking time vs. travel time.

---

## Next Steps

- [ ] Evaluate free government advisory APIs (US State Dept, UK FCDO)
- [ ] Assess commercial travel intelligence providers for cost-value
- [ ] Design alert normalization and deduplication pipeline
- [ ] Study alert aggregation patterns to avoid alert fatigue
- [ ] Prototype geo-matching against trip itinerary data
