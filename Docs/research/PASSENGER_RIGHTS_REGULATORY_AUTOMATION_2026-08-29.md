# Research & Exploration: Automated Passenger Rights & Regulatory Claim Filing under EU261 / US DOT

**Persona:** `Travel Entitlements Graph & Passenger Rights Architect`  
**System:** Waypoint OS (`pranaysuyash/travel_agency_agent`)  
**Date:** August 29, 2026  
**Status:** Canonical Specialist Exploration  

---

## 1. Regulatory Context & Entitlement Tiers

Under European Regulation (EC) No 261/2004 and the UK Air Passenger Rights framework, airlines are legally bound to pay statutory compensation for arrivals delayed $\ge 3$ hours unless extraordinary circumstances (e.g. weather, air traffic control) are proven.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            STATUTORY COMPENSATION TIERS (EU261)                             │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│ Tier 1: Flights <= 1,500 km   │ Tier 2: Flights 1,500-3,500 km│ Tier 3: Flights > 3,500 km  │
│   - Compensation: €250        │   - Compensation: €400        │   - Compensation: €600      │
│   - Delay Threshold: >= 3h    │   - Delay Threshold: >= 3h    │   - Delay Threshold: >= 4h  │
└───────────────────────────────┴───────────────────────────────┴─────────────────────────────┘
```

### 1.1 Extraordinary Circumstances Legal Precedents
* **CJEU Case C-549/07 (*Wallentin-Hermann*)**: Technical aircraft defects resulting from premature part failures are inherent in airline operations and **do NOT constitute extraordinary circumstances**.
* **CJEU Case C-195/17 (*Krzüsemann*)**: "Wildcat strikes" by airline staff following restructuring announcements are within the airline's control and **do NOT exempt compensation**.

### 1.2 Automated Radar Telemetry Ingestion
By integrating real-time ADS-B flight tracking touchdown timestamps, Waypoint OS can auto-generate ready-to-sign legal claim PDFs the instant a flight arrives $\ge 180\text{ minutes}$ behind schedule.
