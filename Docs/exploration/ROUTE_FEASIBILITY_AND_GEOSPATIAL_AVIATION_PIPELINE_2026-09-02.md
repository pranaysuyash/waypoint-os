# Deep Dive: Route Feasibility, Hop Validation & External Data Architecture

**Category:** Logistics, Aviation, Geospatial Intelligence & Agent Connectivity\
**Status:** Canonical Specialist Exploration & Architectural Design\
**Date:** 2026-09-02\
**Doctrines Applied:** `OPERATING_DOCTRINE.md` 8.0, `EXPLORATION_DOCTRINE.md` 1.1, `ARCHITECTURE_DOCTRINE.md` 1.1, `DOCUMENTATION_DOCTRINE.md` 1.1\

---

## 0. Executive Summary & Problem Scope

When an autonomous AI agent in **Waypoint OS** generates or reviews a multi-city travel itinerary, proposing a sequence of flights, rail legs, ferry hops, and ground transfers is only a draft hypothesis.

In real-world travel agency operations, an unverified route can result in catastrophic failures:

1. **Illegal / High-Risk Flight Connections:** 45-minute transfers between non-connected terminals at mega-hubs (e.g., Heathrow T2 to T5 or Paris CDG 2E to 2G) leading to guaranteed misconnects.
2. **Self-Transfer & Separate PNR Traps:** Uncoordinated low-cost carrier hops where travelers must clear border control, wait for luggage carousels, and re-check bags in under 90 minutes.
3. **Immigration & Transit Visa Incompatibilities:** Double-Schengen transit hops, Canadian Transit Without Visa (TWOV) rule violations, or US transit requirements.
4. **Geographical Zigzagging & Logistical Hallucinations:** Itineraries backtracking thousands of miles or proposing land transfers between locations separated by unnavigable terrain.
5. **Private Aviation Operational Violations:** Routing a heavy jet into a high-altitude mountain airstrip with insufficient runway length or missing customs clearance (eAPIS/FBO).
6. **Commercial Airline Fare & PNR Rule Violations:** Open-jaw segments missing surface leg flags (`//`) triggering automated cancellations, or illicit hidden-city routing causing carrier Agency Debit Memos (ADMs).

To solve this, Waypoint OS implements a **6-Layer Route Feasibility Verification Matrix** powered by a **4-Tier Data Sourcing Pipeline** that spans local offline deterministic engines, open geospatial services, commercial aviation GDS/NDC aggregators, and regulatory feeds.

---

## 1. The 6-Layer Route Feasibility Verification Matrix

Every route or itinerary proposed by or fed to the agents must pass through 6 rigorous layers of validation before it is deemed feasible:

```text
+-----------------------------------------------------------------------------+
| 1. GEOMETRIC & GEOSPATIAL SANITY LAYER                                      |
|    - Great-circle geodesic distance & directional ordering (anti-zigzagging) |
|    - Physical ground/maritime transit feasibility & drive-time limits       |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 2. FLIGHT & HUB TRANSIT (MCT) MECHANICS LAYER                               |
|    - IATA Minimum Connection Time (MCT) per airport & terminal pair         |
|    - Terminal transit penalties, security re-screening, customs clearance   |
|    - Separate PNR / Self-transfer baggage re-check model (60-90m penalty)   |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 3. CHRONOLOGY, TIMEZONE & CIRCADIAN LAYER                                   |
|    - UTC vs local timestamp math, International Date Line crossings         |
|    - Circadian fatigue gating, red-eye recovery buffers, cruise cutoffs     |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 4. COMMERCIAL, AIRLINE & PNR POLICY LAYER                                   |
|    - Interline ticketing agreements & baggage through-check validity        |
|    - Open-jaw surface segment markers (//) preventing no-show auto-cancels  |
|    - Skiplagging / ADM fraud detection, Cabotage legal compliance          |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 5. PRIVATE AVIATION & CHARTER RUNWAY LAYER                                  |
|    - Runway length vs aircraft takeoff/landing requirements (hot & high)    |
|    - Range curves under payload/headwinds, FBO slots, eAPIS filings         |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 6. REAL-TIME OPERATIONAL & DISRUPTION LAYER                                 |
|    - Historical on-time performance (OTP) & delay probability modeling     |
|    - Weather disruption forecasts, active NOTAMs, airspace closures         |
+-----------------------------------------------------------------------------+
```

---

### Layer 1: Geometric & Geospatial Feasibility

- **Geodesic Vector Analysis:** Calculates Great-Circle (Haversine / Vincenty) distances between all origin, waypoint, and destination coordinates.
- **Backtracking & Convex Hull Ordering:** Evaluates whether a multi-stop itinerary forms a clean topological polygon or wastes traveler time in retrograde hops (e.g. `Rome -> Venice -> Florence -> Milan` vs `Rome -> Florence -> Venice -> Milan`).
- **Ground & Maritime Feasibility:** Distinguishes whether two locations can be connected via high-speed rail, road, or ferry, or strictly require scheduled commercial/charter aviation (e.g. island hopping in Greece vs Scottish Highlands).

### Layer 2: Flight & Hub Transit (MCT) Mechanics Layer

- **IATA Minimum Connection Time (MCT):** Evaluates connection layovers against airport-specific standards (`HUB_MCT_CATALOG` in `src/logistics/connection_risk.py`).
- **Terminal Pair Penalties:** Quantifies inter-terminal transit friction:
  - Same terminal: standard 45-60 minutes.
  - Terminal change (e.g., LHR T2 to T5, CDG 2E to 2G, JFK T4 to T8): adds 30-45 minutes.
  - Inter-airport change (e.g., Tokyo HND to NRT, New York JFK to EWR): adds 180-240 minutes.
- **Self-Transfer / Separate PNR Penalty:** When legs are on un-interlined tickets, the system adds a mandatory 60-90 minute buffer for baggage reclaim, landside transit, and counter check-in.
- **Immigration / Border Reclearance:** Adds automated penalties (+30 to +45 mins) whenever international-to-domestic or non-Schengen to Schengen hops occur.

### Layer 3: Chronology, Timezone & Circadian Layer

- **Date Line & Timezone Offset Reconciliation:** Prevents chronology inversion bugs when crossing the International Date Line (e.g., flying Tokyo `NRT` -> San Francisco `SFO` arriving "before" departure in local time).
- **Red-Eye & Circadian Gating:** Prohibits scheduling demanding morning activities or tight tight connections immediately following overnight long-haul flights across >= 5 timezones without buffer rest periods.
- **Event & Departure Hard Buffers:** Enforces mandatory safety buffers prior to unyielding logistics (e.g., requiring arrival at least 4 hours before cruise embarkation or private yacht charter departures).

### Layer 4: Commercial, Airline & PNR Policy Layer

- **Baggage Interlining & Codeshare Rules:** Validates whether operating carrier A and marketing carrier B have an active IATA interline agreement permitting baggage to be checked through to final destination.
- **Open-Jaw Surface Integrity (`//`):** Ensures that ground transport legs between arrival city A and departure city B are properly codified in the PNR to avoid airline computer systems canceling the return flight for "passenger no-show".
- **Anti-Skiplagging Guardrail:** Flags hidden-city ticketing attempts to protect the agency from airline Agency Debit Memos (ADMs) and protect the traveler from loyalty status revocation.
- **Cabotage Compliance:** Prevents routing domestic legs on foreign flag carriers where prohibited by international aviation law (e.g., booking British Airways for `JFK -> LAX`).

### Layer 5: Private Aviation & Charter Runway Layer

- **Runway Length & Density Altitude:** Cross-references aircraft model specifications (`FLEET_CATALOG` in `src/charter/aviation_engine.py`) against target airport runway dimensions (`AIRPORT_RUNWAY_DATABASE`):
  - E.g., Aspen Pitkin County (`KASE`): High altitude requires specialized climb gradient and reduced payload limits.
- **Empty-Leg Positioning Feasibility:** Matches traveler dates with live repositioning legs (`SAMPLE_EMPTY_LEGS`), checking FBO operating hours and eAPIS passenger manifest submission deadlines (minimum 60-minute pre-departure filing).

### Layer 6: Real-Time Operational & Disruption Layer

- **Historical On-Time Performance (OTP):** Checks historical delay distributions for specific flight numbers and hub slots (e.g., evening departures out of Newark `EWR` or Chicago `ORD` having higher ground-delay program risk).
- **Dynamic Weather Forecasting:** Ingests live weather alerts (e.g. Open-Meteo precipitation/wind data via `OpenMeteoWeatherTool`) to flag connections during tropical storms or snow squalls.
- **Airspace Closures & Geopolitical Safety:** Ingests travel advisories (via `StateDeptTravelAdvisoryTool`) and NOTAM feeds to avoid active conflict zones and restricted air corridors.

---

## 2. Multi-Tier Data Sourcing Architecture

To execute these checks without incurring unsustainable API latency or cloud costs, Waypoint OS employs a **4-Tier Data Sourcing Architecture**:

```text
+-----------------------------------------------------------------------------+
| TIER 0: EMBEDDED OFFLINE / IN-MEMORY DETERMINISTIC ENGINES (0ms, 100% Free) |
| - GeoNames 590k Cities (data/cities5000.txt, intake/geography.py)          |
| - Global Airport Database & Runway Specs (charter/aviation_engine.py)       |
| - IATA Hub MCT & Terminal Change Directory (logistics/connection_risk.py)   |
| - Geodesic Vector & Haversine Distance Calculators                          |
+-----------------------------------------------------------------------------+
                                      | (fallback / initial prune)
                                      v
+-----------------------------------------------------------------------------+
| TIER 1: OPEN GEOSPATIAL & GROUND MOBILITY ENGINES (<50ms, Free / Low Cost) |
| - Open-Meteo Geocoding & Weather Forecasts (Keyless, open_meteo)            |
| - OSRM (Open Source Routing Machine) / Valhalla for road/rail distance      |
| - OpenStreetMap Overpass API for local POIs, stations, and ferry terminals  |
+-----------------------------------------------------------------------------+
                                      | (scheduled commercial availability)
                                      v
+-----------------------------------------------------------------------------+
| TIER 2: AVIATION GDS / NDC & LIVE INVENTORY ENGINES (Cached, Rate-Limited)  |
| - Amadeus Self-Service / Enterprise API (Flight Offers, Hub MCT, Schedules) |
| - Sabre REST / SOAP APIs (GDS availability, PNR surface segment rules)      |
| - Duffel / Kiwi Tequila APIs (Virtual interlining, baggage re-check rules)   |
| - Cirium / FlightAware APIs (Live flight status, historical OTP, delays)    |
+-----------------------------------------------------------------------------+
                                      | (regulatory & passenger safety)
                                      v
+-----------------------------------------------------------------------------+
| TIER 3: REGULATORY, VISA & SAFETY ADVISORY FEEDS (High TTL Caching)         |
| - U.S. State Dept & UK FCDO Travel Advisories (travel.state.gov)            |
| - IATA Timatic API (Visa, passport validity, and transit visa requirements) |
| - FAA & Eurocontrol NOTAM / Airspace restriction feeds                      |
+-----------------------------------------------------------------------------+
```

---

## 3. Tool Contracts & Sandboxing Architecture

All external data access in Waypoint OS is mediated by **Strict Tool Contracts** (`src/agents/tool_contracts.py` and `src/agents/live_tools.py`) adhering to three core principles:

1. **Normalized `ToolResult` Outputs:**
   AI agents never consume raw provider JSON payloads. Every tool adapter normalizes data into a strictly typed `ToolResult` containing `confidence`, `freshness`, `raw_reference`, and explicit `mode` (`mock` | `live`).

2. **Hierarchical `CONNECTIVITY_TIER` Support:**
   - `MOCK` (Tier 0/1): Fast, deterministic in-repo data for CI/CD, regression testing, and local offline development.
   - `SANDBOX` (Tier 2): Verified test credentials connecting to supplier development sandboxes (e.g. Amadeus Test Environment).
   - `LIVE` (Tier 3): Production credentials with rate limiting, token buckets, and cryptographic secret management.

3. **Freshness Policies & TTL Caching:**
   - Static Geospatial / Runway data: Permanent / 30-day cache.
   - IATA MCT Standards: 7-day cache.
   - Travel Advisories & Visa Rules: 6-hour to 24-hour cache.
   - Flight Schedules & Fares: 15-minute to 30-minute cache.
   - Live Flight Status & Weather: 5-minute to 15-minute cache.

---

## 4. Summary of Verification Execution Flow

When an agent plans or refines an itinerary:

1. **Intake & Extraction:** The agent extracts cities, airports, and dates via `intake/geography.py`.
2. **Topology Pruning (Tier 0):** Fast in-memory distance and hub checks eliminate geometrically impossible combinations (e.g. 30-minute connections or reverse backtracking).
3. **Logistics & Connection Scoring (Tier 0/1):** `ConnectionRiskScorer` evaluates MCT, terminal changes, and self-transfer baggage penalties.
4. **Live Validation (Tier 2/3):** If live connectivity is enabled, the agent calls normalized adapters for live schedule verification, baggage interlining, and travel safety alerts.
5. **Human Operator Sign-Off:** If any leg is categorized as `HIGH_MISCONNECT_RISK`, `ILLEGAL_MCT_VIOLATION`, or `ELEVATED_SAFETY_RISK`, the engine surfaces a high-visibility warning to the travel agent operator before proposal presentation.
