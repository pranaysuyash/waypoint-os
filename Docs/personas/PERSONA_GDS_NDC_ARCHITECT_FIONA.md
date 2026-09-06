# Persona Profile: Fiona Gallagher — Lead GDS & NDC Protocol Systems Architect

**Identifier**: `P10-GDS-01`\
**Role**: Director of Global Distribution & NDC Engineering at *Amadeus-Sabre Multi-Host Solutions*\
**Operational Scale**: Manages dual-host Global Distribution System (Amadeus 1A & Sabre 1S) connectivity, EDIFACT legacy teletype parsing, and IATA NDC 21.3 XML/JSON Offer & Order management across 10,000+ daily air queries.\
**Primary Tooling Need**: Dual-stack GDS sandbox execution, real-time fare basis decoding (`JFFLEX26`), inventory seat bucket monitoring, and instant zero-latency PNR / E-Ticket issuance.

---

## 1. Professional Background & Operational Context

Fiona bridges legacy airline distribution with modern direct-connect NDC protocols:

1. **Multi-GDS Redundancy**: When Amadeus experiences API rate limits or regional gateway timeouts, traffic automatically fails over to Sabre Dev Studio without agent interruption.
2. **Fare Basis Rule Parsing**: Commercial fare codes (e.g. `JFFLEX26`) dictate refundable status, change penalty waivers, and baggage allowances that must be presented accurately to corporate bookers.
3. **Instant PNR Creation**: Issuing live reservations requires bi-directional sync between GDS teletype queues and internal agency databases.
