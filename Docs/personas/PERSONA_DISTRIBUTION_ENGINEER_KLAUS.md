# Persona Profile: Klaus Weber — Principal Airline Protocol & GDS Distribution Engineer

**Identifier**: `P14-DISTRIB-01`\
**Role**: Head of Distribution Engineering & GDS/NDC Interoperability at *Global Transit Systems Ltd*\
**Operational Scale**: Architects flight distribution pipelines across legacy EDIFACT GDS (Amadeus 1A, Sabre 1S, Travelport 1G) and modern IATA NDC 21.3 direct airline connections (British Airways, Lufthansa Group, Singapore Airlines).\
**Primary Tooling Need**: Cryptic EDIFACT PNR terminal parsers, IATA NDC 21.3 XML `AirShoppingRQ` / `OrderCreateRQ` schema validation engines, and ATPCO Cat 16 / Cat 35 Net Remit ADM shield audit algorithms.

---

## 1. Professional Background & Operational Context

Klaus bridges the multi-decade architectural divide between 1970s teletype EDIFACT commands and modern JSON/XML NDC direct-connect APIs:

1. **Cryptic EDIFACT Ingestion**: Transforming unformatted legacy terminal dumps (`RP/NYC1A0982/NYC1A0982 AA/SU 30AUG26/0842Z 6XY7ZQ`) into structured, typed JSON entities.
2. **NDC 21.3 Direct Connects**: Bypassing legacy GDS distribution surcharges ($12 to $25 per segment) by connecting directly to airline NDC endpoints while bundling rich ancillaries (fast-track security, lounge passes).
3. **Agency Debit Memo (ADM) Protection**: Auditing Category 35 net remit markups and Category 16 change/cancellation penalty rules to ensure agencies never receive punitive debit memos from IATA BSP.
