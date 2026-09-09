# Passport/Identity PII Flow Audit — Exploration (VE-05)

**Date**: 2026-09-09
**Status**: EXPLORE (static flow audit, Tier 1; no runtime probes)
**Source**: Random document audit seed 20260909 → `Docs/research/ID_SPEC_IDENTITY_VAULT.md` (aspirational ZK/Sovereign-Identity spec, Status: Research/Draft) raised the near-term question: **how does passport/identity PII actually flow through the product today?** This doc maps the real flow; the ZK vault remains future exploration.
**Register refs**: VE-05; related: A4 booking_confirmation encryption (open), VD-02/VE-02.

---

## 1. PII surfaces found (Tier 1 evidence, 2026-09-09)

| Surface | What it holds | Protection today | Evidence |
|---|---|---|---|
| Packet facts (extraction) | `passport_status`, `visa_status` — **status enums only, no numbers** | n/a (no raw PII) | `src/intake/extractors.py:2197+` (`_extract_passport_visa`) |
| MRZ engine | Parses ICAO 9303 machine-readable zones (name, doc number, DOB, expiry) from passport scans | Checksum/validation only — **no storage path wired into intake** | `src/intake/mrz.py`, `src/intake/mrz_parser_engine.py` |
| Visa radar requests | `passport_country`, `passport_expiry_date` per check | **Stateless** — no persistence, no logging (analytics logger has zero passport hits) | `spine_api/services/visa_radar.py`, `spine_api/routers/visa_radar.py` |
| Trip persistence | PII keys incl. `passport`, `passport_number`, `full_name`, phone/email/medical | **Recursive PII encryption** on write (`_encrypt_pii`) keyed on a PII field-name allowlist | `spine_api/persistence.py:735-755` |
| BookingDocument (SQL) | Uploaded passport/visa/ticket scans per trip+agency | Agency-scoped rows, cascade-delete, explicitly "NOT trusted execution data, never inlined into trip hydration" | `spine_api/models/tenant.py:241-260` |
| Traveler profile blob | `{"full_name", "passport_number", ...}` | Column-level model (see tenant.py:311) | `spine_api/models/tenant.py:311` |
| PII masker | Export boundary sanitizer | Masks passport numbers (`L8****C3` pattern) before public-zone export | `src/services/pii_masker.py` |
| Hash-PII allowlist | `dob`, `passport_number`, `filename`, `sha256`, … | Keyed-hash allowlist for safe referencing | `spine_api/models/tenant.py:623` |

## 2. Flow assessment

**Strengths (real, verified statically):**
- Layered posture exists: encryption at rest (persistence), masking at export (pii_masker), hash-allowlist for referencing, agency scoping on document uploads, and MRZ checksum integrity.
- The intake pipeline deliberately extracts **status, not identity**: `passport_status: {status: valid}` — the visa/passport fact schema was designed to avoid carrying document numbers through the decision path. Good instinct, matches the ID-vault spec's least-privilege intent.

**Gaps / open questions (none exploited, all static-tier):**
1. **Encryption key management** — `_encrypt_pii` exists, but where do keys live, are they rotated, and is the ciphertext format versioned? (Unverified — needs a focused pass; same family as the A4 booking_confirmation encryption task.)
2. **visa_radar `/{trip_id}/requirements`** reads `passport_country`/`passport_expiry_date` from the trip packet — confirm this crosses the PII-encryption boundary correctly on read (encrypted values must not leak into API responses unmasked or fail-decryption silently).
3. **MRZ engine is wired to nothing in intake** — it can parse full passport identity from a scan, but no current path feeds it. Before anyone wires it (a natural "convenience" feature), the ID-vault question becomes live: parsed MRZ data is exactly the "PII-hemorrhage" the spec warns about. **Recommendation: gate MRZ wiring on a PII design decision, not on convenience.**
4. **Traveler profile blob (`tenant.py:311`)** — raw `passport_number` in a JSON blob: confirm it goes through `_encrypt_pii` on write (the persistence allowlist covers `passport_number`, but SQL-model-level writes may bypass the file-store path's encryptor — needs verification if/when traveler profiles gain write paths).

## 3. Relationship to ID_SPEC_IDENTITY_VAULT.md

The ZK vault / sovereign-identity spec is far-future (ZK attribute proving, vendor adoption metrics). The **near-term defensible position** is what mostly already exists: status-not-identity intake, encryption at rest, masking at export. The honest gap list above is the actual security backlog; the ZK spec should stay Research/Draft until a customer/market forces attribute-proving (per the pre-launch filter).

## 4. Recommended next work (when this lane activates)

1. Verify encryption-key lifecycle + add rotation runbook (ties into A4).
2. Runtime-verify the visa-radar trip-requirements read path across the encryption boundary (Tier 3/4 check).
3. Decision-gate MRZ engine wiring on a PII design note (banner the engine as intentionally-unwired meanwhile — it joins the DRIFT-2026-09-06 unwired-engines inventory).

**Falsifier**: if runtime verification shows `_encrypt_pii` already covers SQL writes via a shared session hook, gaps 1-2 shrink to key-lifecycle only.
