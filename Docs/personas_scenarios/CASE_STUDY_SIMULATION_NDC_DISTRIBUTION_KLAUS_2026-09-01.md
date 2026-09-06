# Case Study: NDC 21.3 vs EDIFACT Teletype Message Validation Simulation (Klaus Weber — P14-DISTRIB-01)

**Persona Profile**: Klaus Weber, Head of Distribution Engineering at Global Transit Systems Ltd\
**Simulation Date**: September 1, 2026\
**Primary Scenario**: Bi-Directional EDIFACT Terminal Parsing & IATA NDC 21.3 Order Lifecycle Execution (`EXP-DISTRIB-NDC-01`)\
**Underlying Architecture**: GDS Protocol Engine (`DistributionPanel.tsx`), Amadeus/Sabre EDIFACT Cryptic Parser, IATA NDC 21.3 Gateway, and ATPCO Cat 16/35 ADM Shield.

---

## 1. Executive Summary & Business Challenge

Airlines are rapidly deprecating legacy EDIFACT GDS distribution and penalizing agencies with surcharges, while NDC APIs remain notoriously fragmented and difficult to parse:

1. **Cryptic Terminal Entanglement**: Agency veterans still use green-screen cryptic entries (`6XY7ZQ`, `HK2`, `SSR VGML`), which break modern CRM and accounting systems.
2. **NDC Integration Friction**: Connecting to XML-based IATA NDC 21.3 feeds requires custom schema translation, dynamic offer generation, and ancillary bundling.
3. **Cat 35 ADM Penalties**: Miscalculating private net remit fares triggers severe airline debit memos (ADMs) via ARC/BSP.

---

## 2. Live Simulation Trajectory & Verification

```text
+----------------------------------------------------------------------------------------------------+
|                                  KLAUS WEBER WORKFLOW TRAJECTORY                                   |
+----------------------------------------------------------------------------------------------------+
| [Stage 1: Cryptic Ingestion]       -> Ingested: RP/NYC1A0982/NYC1A0982 ... 6XY7ZQ BA 178 J 15OCT   |
| [Stage 2: Deterministic Parsing]   -> Extracted: Record Locator: 6XY7ZQ | BA 178 Club World HK2    |
| [Stage 3: ADM Shield Verification] -> Verified: Compliant · Zero ADM Risk                          |
| [Stage 4: NDC 21.3 Direct Connect] -> Queried: LHR -> JFK (Business / Club World)                  |
| [Stage 5: Order Confirmation]      -> Generated: ORD-NDC-BA-99A841 ($4,850.00 Guaranteed Direct)   |
|                                       - Bundled: Group 1 Boarding, Fast Track Security, Lounge     |
+----------------------------------------------------------------------------------------------------+
```

### Stage 1 & 2: Legacy EDIFACT Cryptic Terminal Parser

- **Raw Terminal Dump**:

  ```text
  RP/NYC1A0982/NYC1A0982            AA/SU 30AUG26/0842Z   6XY7ZQ
  1.MORGAN/ALEX MR  2.MORGAN/TAYLOR MS
  1  BA 178 J 15OCT LHRJFK HK2  1140 1425  *1A/E*
  SSR VGML BA HK1/S1
  OSI BA VIP REPEAT TRAVELER
  TK TL15SEP/NYC1A0982
  ```

- **Parsed Output**:
  - `Record Locator`: `6XY7ZQ`
  - `Passengers`: `MORGAN/ALEX MR`, `MORGAN/TAYLOR MS`
  - `Flight`: `BA 178 · J (Club World) · LHR -> JFK (15OCT 11:40 - 15OCT 14:25) · HK (Confirmed)`
  - `Compliance`: `Compliant · Zero ADM Risk`
- **Visual Proof**: `Docs/review/assets/klaus_01_edifact_translation.png`

### Stage 3 & 4: IATA NDC 21.3 Direct Connect & Ancillary Bundling

- **Route**: `LHR` to `JFK` (Business / Club World).
- **NDC Order Reference**: `ORD-NDC-BA-99A841` `[CONFIRMED (Direct Carrier Direct Connect)]`.
- **Guaranteed Direct Price**: $\$4,850.00$ (Eliminates $\$36.00$ GDS surcharge).
- **Bundled Ancillaries**: Priority Boarding Group 1, Fast Track Security, Galleries Club Lounge Access.
- **Visual Proof**: `Docs/review/assets/klaus_02_ndc_xml_validation.png`

---

## 3. Verified Artifact Registry

| Stage / Asset Name | Artifact URI | Status | Key Metric / Capability |
| :--- | :--- | :--- | :--- |
| **01 EDIFACT Parser** | `Docs/review/assets/klaus_01_edifact_translation.png` | Verified | Cryptic Terminal Ingestion & ADM Shield |
| **02 NDC 21.3 Gateway** | `Docs/review/assets/klaus_02_ndc_xml_validation.png` | Verified | Direct Carrier Connection & Ancillary Bundling |

---

## 4. Key Architectural Insights & Business Takeaways

1. **Bi-Directional Schema Bridging**: Native support for both legacy EDIFACT and modern NDC 21.3 XML allows agencies to transition to modern direct connects without forcing re-training of veteran agents.
2. **Zero-ADM Margin Safety**: Automated validation of ticketing time limits (`TK TL`) and fare basis categories guarantees zero debit memo penalties from IATA BSP clearing houses.
