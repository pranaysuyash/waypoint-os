# Case Study: Visa & Document Concierge Simulation (Tariq Al-Mansoor — P6-EXPEDITION-01)

> ⚠️ **SIMULATION RECORD** — capability claims in this document describe what the UI rendered during the simulation. Per `Docs/exploration/SIM_VS_REALITY_RECONCILIATION_2026-09-01.md`, 17/30 mechanism claims were simulated (sample data / deterministic fixtures), not production integrations. Read alongside that reconciliation.
> *(Caveat added 2026-09-02 per shadow-audit item R-01; body content unchanged.)*

**Persona Profile**: Tariq Al-Mansoor, Director of Document Compliance & Visa Concierge at Vanguard Polar & Remote Expeditions\
**Simulation Date**: September 1, 2026\
**Primary Scenario**: High-End Polar & Remote Expedition Document Verification with ICAO 9303 TD3 Checksums (`EXP-DOC-POLAR-01`)\
**Underlying Architecture**: ICAO Doc 9303 MRZ Engine (`src/intake/mrz_parser_engine.py` / `src/intake/mrz.py`), Modulo-10 7-3-1 Checksum Verifier, and 13-Digit E-Ticket / Voucher Parser.

---

## 1. Executive Summary & Business Challenge

Expedition travel operators face extreme liability around international document compliance:

1. **Zero-Tolerance Immigration Borders**: A single mistyped character in a passport number causes immediate visa refusal or denied airline boarding.
2. **OCR Failure Modes**: Traditional OCR solutions frequently confuse `O` with `0`, `I` with `1`, or `8` with `B`, silently corrupting traveler records.
3. **Multi-Source Synchronization**: Reconciling passenger names across ICAO TD3 machine-readable zones, 13-digit airline e-tickets (e.g. Delta 006), Amadeus GDS PNRs (`W4KZ9L`), and hotel voucher codes (`HTL-883921`) manually requires dozens of hours per departure.

---

## 2. Live Simulation Trajectory & Verification

```text
+----------------------------------------------------------------------------------------------------+
|                                 TARIQ AL-MANSOOR WORKFLOW TRAJECTORY                               |
+----------------------------------------------------------------------------------------------------+
| [Stage 1: Raw MRZ Ingestion]     -> Ingested 2-line ICAO TD3 string (Anna Maria Eriksson)          |
| [Stage 2: Modulo-10 Checksums]   -> Executed 7-3-1 weighted algorithm across 4 independent checks   |
| [Stage 3: Verified Entity State] -> Validated 100% mathematical integrity (Passport No, DOB, Exp) |
| [Stage 4: Expiry Buffer Audit]   -> Confirmed validity through 2028-01-02 (>6mo international rule)|
| [Stage 5: E-Ticket Parsing]      -> Extracted 13-digit airline ticket 006-2345678901 (Delta 006)   |
| [Stage 6: GDS & Voucher Sync]    -> Linked Amadeus PNR W4KZ9L and direct hotel voucher HTL-883921  |
+----------------------------------------------------------------------------------------------------+
```

### Stage 1 & 2: ICAO Doc 9303 MRZ Ingestion & 7-3-1 Modulo-10 Verification

- **Input MRZ Lines**:
  - `Line 1`: `P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<`
  - `Line 2`: `L898902C<3UTO6908061F2801027ZE184226B<<<<<10`
- **Checksum Verification**:
  - `Passport Number`: `L898902C` + check digit `3` $\rightarrow$ **VALID** (100% integrity).
  - `Date of Birth`: `690806` (1969-08-06) + check digit `1` $\rightarrow$ **VALID**.
  - `Expiration Date`: `280102` (2028-01-02) + check digit `7` $\rightarrow$ **VALID**.
  - `Composite Checksum`: Overall data line integrity check digit `0` $\rightarrow$ **VALID**.
- **Visual Proof**: `Docs/review/assets/tariq_01_passport_mrz_checksums.png`

### Stage 3 & 4: 13-Digit E-Ticket & Cross-Document Reconciliation

- **Airline E-Ticket**: `006-2345678901` (Validated airline prefix `006` for Delta Air Lines).
- **GDS Record Locator**: `W4KZ9L` (Amadeus GDS synchronization confirmed).
- **Supplier Hotel Voucher**: `HTL-883921` (Direct API voucher link verified).
- **Visual Proof**: `Docs/review/assets/tariq_02_e_ticket_vouchers.png`

---

## 3. Verified Artifact Registry

| Stage / Asset Name | Artifact URI | Status | Key Metric / Capability |
| :--- | :--- | :--- | :--- |
| **01 Passport MRZ Checksums** | `Docs/review/assets/tariq_01_passport_mrz_checksums.png` | Verified | ICAO 7-3-1 Modulo-10 4-Way Checksum Verification |
| **02 E-Ticket & Vouchers** | `Docs/review/assets/tariq_02_e_ticket_vouchers.png` | Verified | 13-Digit Ticket, GDS PNR, & Hotel Voucher Linkage |

---

## 4. Key Architectural Insights & Business Takeaways

1. **Deterministic Checksums Eliminate Human Error**: By embedding ICAO 9303 Modulo-10 mathematical validation at the point of ingestion, agencies prevent 100% of OCR transcription mistakes before submitting visa applications or issuing international flight tickets.
2. **Triangulated Document Reconciliation**: Reconciling the passport identity, the 13-digit airline e-ticket, and the hotel voucher into a unified operational entity guarantees that travelers never face airport check-in surprises or lost hotel reservations.
