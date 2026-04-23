# Area Deep Dive: Travel Technology & Distribution

**Domain**: Technical Infrastructure  
**Focus**: NDC, GDS, API fragmentation, and content parity.

---

## 1. The GDS vs. NDC Conflict

The travel industry is currently in a massive transition from legacy GDS (Global Distribution Systems) to NDC (New Distribution Capability).

### Legacy GDS (Amadeus, Sabre, Travelport)
- **Mechanics**: Aggregates hundreds of airlines into a single "Green Screen" or XML feed.
- **Risk**: Airlines are pulling their "Best Prices" and "Ancillaries" (bags, seats) out of GDS to avoid high fees.
- **System Action**: Identifying when a GDS quote is "Sub-optimal" compared to a direct airline source.

### NDC (New Distribution Capability)
- **Logic**: A modern XML-based standard that allows airlines to offer personalized bundles (e.g., "Corporate Fare with Wi-Fi").
- **System Action**: Consuming NDC feeds to provide "Content Parity" for the traveler.

---

## 2. API Fragmentation & Scrapers

### The "LCC" Gap
- **Problem**: Low-Cost Carriers (Ryanair, IndiGo, Southwest) often refuse to participate in GDS/NDC.
- **System Action**: Using specialized "Scrapers" or Direct-to-Web aggregators (e.g., Travelfusion) to fetch these fares.

### Aggregator Conflict Resolution
- **Logic**: If three different APIs return three different prices for the same flight, which one do we trust?
- **System Action**: Applying "Truth Rules" (e.g., "Always trust the API with the lowest cached age").

---

## 3. Synchronization & PNR Integrity

### Passive Segments
- **Requirement**: If a booking is made outside the GDS (e.g., on an airline website), it must be "synced" back as a "Passive Segment" so the agency can track it.
- **System Action**: Creating passive PNRs for all non-GDS bookings in Phase 2 (Fulfillment).

### Queue Management
- **Logic**: GDS communicates changes (cancellations, schedule shifts) via "Queues".
- **System Action**: Monitoring "Queue 0" (Schedule changes) every 15 minutes and triggering NB02 "Disruption Recovery" if a change is detected.

---

## 4. Proposed Scenarios for this Domain

| Scenario ID | Title | Persona | Category |
|-------------|-------|---------|----------|
| TECH-001 | GDS vs NDC Price Discrepancy | P1 | Comparison |
| TECH-002 | LCC Scraper Time-out Recovery | S1 | Fulfillment |
| TECH-003 | Passive Segment Sync Failure | P3 | Operations |
| TECH-004 | Queue 0 Schedule Change Alert | S1 | Disruption |
| TECH-005 | API "Fare Expired" during Payment | S1 | Fulfillment |
| TECH-006 | Duplicate PNR Detection | P2 | Risk |
