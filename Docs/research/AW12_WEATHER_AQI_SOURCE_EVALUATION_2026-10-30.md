# AW1/AW2 — Weather, Climate & AQI Source Evaluation (2026-10-30)

Cluster #2 of the Destination Intelligence program (master list category AW, weather + AQI block, ~lines 2369-2385). READ-FIRST order followed. Context: Open-Meteo is already wired in `src/public_checker/live_checks.py` and OpenWeather in `spine_api/routers/pre_departure.py` — the gap this doc closes is the **formal evaluation**, not wiring. Sources verified 2026-10-30 from pricing/docs pages.

## Weather NOW/forecast

| Source | Free tier | Verdict |
|---|---|---|
| **Open-Meteo** | 10k calls/day, 600/min, no key, non-commercial (€29/mo Standard for commercial); 16-day hourly multi-model; ERA5 history **to 1940**; CC BY 4.0 | **A+ bulk + live.** One API covers forecast + historical + AQI + marine + geocoding. |
| **OpenWeather** | 60/min, 1M calls/mo free (5-day/3h, Air Pollution, Geocoding); ODbL + logo attribution | **B live backup.** Already wired. Weak for bulk (paid history £7/location). |
| **Visual Crossing** | 1,000 records/day free (**commercial OK**); 15-day hourly; 50+ yr history | **B+ bulk alternative** if a commercial license is needed without cost. |
| **Tomorrow.io** | ~500 calls/day (unverified — page 429'd) | C — not needed; Open-Meteo covers. |
| **WeatherAPI.com** | 100k/mo but only 3-day forecast | C — too short for trip-date gates. |
| **AccuWeather** | 50 calls/day trial | D — skip. |

## Historical / climate baselines ("best time to visit")

- **Open-Meteo Historical + Climate API** — **A+ primary** (ERA5 hourly 1940→, CMIP6 scenarios); already wired.
- ERA5/Copernicus CDS — B bulk archive (batch, heavier pipeline).
- NOAA NCEI / Meteostat — B station-level supplements.

## Air quality

| Source | Verdict |
|---|---|
| **Open-Meteo Air-Quality (CAMS-backed)** | **A default.** PM2.5/PM10/O3/NO2/SO2/CO, EU+US AQI, UV; 5-7 day hourly forecast; EU reanalysis 2013→, global 2022→; pollen (EU only, 6 taxa). |
| **OpenAQ** | **A− bulk** — v3 key, 60/min + 2,000/hr; full archive on AWS S3 (programmatic baselines without API limits). |
| **WAQI/AQICN** | **B live display only** — attribution mandatory + originating EPA; **no caching/redistribution clause** blocks baking into pages. |
| **IQAir** | C (community ~10k calls/mo, unverified — 429'd). |
| **CPCB India** | **B+ hybrid**: CAMS 45km under-resolves Delhi winter smog → WAQI station feed for India city truth. |

## Specialty

Marine/beach: **Open-Meteo Marine A** (Stormglass free tier now only 10 req/day). UV: free via Open-Meteo (A). Pollen: EU-only free (B). India monsoon: IMD publishes onset dates but **no free API** → proxy strategy (30 onset values/yr + Open-Meteo precip climatology).

## Recommended standardized stack

1. **Open-Meteo — everything bulk + most live** (single free non-commercial license covering all four needs; a full 500-city monthly rebuild ≈ 1,500 calls).
2. **OpenWeather — live fallback/secondary** (cross-validation; already wired).
3. **WAQI live AQI for India/CPCB truth + OpenAQ S3 for historical baselines** (avoids WAQI's no-cache clause).
Commercial migration path: Open-Meteo Standard (~€29/mo) or Visual Crossing free commercial tier.

## Per-master-list-item verdicts

- ✅ Weather API landscape evaluation — READY (this doc).
- ✅ Micro-climate resolution — READY (11km sufficient for city pages; venue-level = paid).
- ✅ Historical weather pattern database (10yr × 500 destinations) — READY (build plan: ERA5 via Open-Meteo, ~1,500 calls/month refresh).
- ✅ AQI sources evaluation — READY (IQAir rejected, WAQI constraints documented).
- ✅ Seasonal pollution patterns — READY (EU reanalysis + OpenAQ S3).
- ✅ Pollution-adjusted itineraries / 7-day AQI forecast / health advisories — READY for the data layer (CAMS 7-day hourly verified); itinerary logic stays 🔵 until product build.
- 🔵 Weather impact on trip satisfaction / weather-aware pricing / packing recs — open (needs our own booking data — Year-1 moat).
- 🔵 Indoor AQI / pollution-impact-on-booking — open (market research, not source evaluation).

## Product/tool ideas unlocked

1. **Trip-Date Suitability Gate**: dates + destination → 16-day forecast + CAMS AQI → green/yellow/red per activity type (marine for beach, precip+wind for hiking) + "suggest alternative dates" CTA.
2. **"Best Time to Visit" generator**: ERA5 normals → monthly heat/rain/AQI/pollen charts → 500×12 = 6,000 programmatic pages + "Best Destinations for [Month]" index.
3. **AQI health gate for respiratory travelers**: 7-day AQI forecast + traveler profile → indoor-alternative rerouting (asthmatic-traveler content prism).
Nontraditional: webcams as accuracy ground truth (Windy webcams — proprietary accuracy moat); flight-delay × weather correlation join (OpenSky + weather) as free-tool data product.

## Caveats + sources

Verify-marks update (2026-10-30 PM): tomorrow.io/weather-api reachable (HTTP 200) — free-tier figure (~500 calls/day) remains training-knowledge pending a console signup; iqair.com still 429 (bot-walled). Open-Meteo historical free-tier scope re-test advised before mass backfill (current wired calls succeed, so non-commercial access confirmed at today's volumes).
Sources: open-meteo.com/en/pricing · open-meteo.com/en/docs/air-quality-api · openweathermap.org/price · visualcrossing.com/weather-api · weatherapi.com/pricing.aspx · tomorrow.io/weather-api · aqicn.org/api · docs.openaq.org · stormglass.io/pricing · cds.climate.copernicus.eu · mausam.imd.gov.in
