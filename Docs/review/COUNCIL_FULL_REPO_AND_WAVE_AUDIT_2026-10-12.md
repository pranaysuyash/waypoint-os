# Waypoint OS — Council Full Repository & In-Flight Wave Audit (2026-10-12)

- **Audit Date**: `2026-10-12`
- **Orchestrator**: `$council-orchestrator` (`/Users/pranay/.agents/skills/council-orchestrator/SKILL.md` + `/Users/pranay/Projects/Council Orchestrator Skill.md`)
- **Active Doctrines**:
  - `OPERATING_DOCTRINE.md` (v8.2)
  - `REVIEW_DOCTRINE.md` (v1.2)
  - `ARCHITECTURE_DOCTRINE.md` (v1.1)
  - `SECURITY_PRIVACY_SAFETY_DOCTRINE.md` (v1.0)
  - `RELEASE_READINESS_DOCTRINE.md` (v1.0)
- **Canonical Persona Repository**:
  - **Resolved Path**: `/Users/pranay/Downloads/Understanding_Personas_24sep`
  - **Resolution Method**: `python3 ~/.agents/skills/council-orchestrator/scripts/resolve_persona_repo.py` (`confidence: high`, `canonical_rank: 7`, `st_birthtime: 1790235290.97338`)
  - **Source Fingerprint**: `fc9aef4328a8fd8ab815786de4b83d82334c91fa57972a6e94d123f99f83b64a` (`2,349` filesystem records / `2,318` DOCX candidates verified via `load_persona_index.py`)
- **Launch Target Rule**: Full-launch readiness (`NO-GO` until all P0/P1 blockers are closed with runtime proof; owner rule forbids MVP/pilot/design-partner scope-reduction framing).
- **Overall Launch Verdict**: **NO-GO** (`4 P0`, `12 P1`, `4 P2/P3 clusters` verified in live code).

---

## 1. Council Manifest & Expertise Coverage Matrix

### 1.1 Activated Council Roster (5 Personas across Lead + 4 Specialist/Counterposition Seats)

| Seat | Persona ID & Title | Canonical DOCX File | Paired Installed Skills | Owned Audit Dimensions |
| :--- | :--- | :--- | :--- | :--- |
| **Lead / Synthesis** | **`PER-0100`** — *Launch Readiness Director* | `0100_PER-0100_Launch_Readiness_Director_20250923_v1.docx` | `verification-before-completion` (`~/Projects/skills/`) | Go/No-Go gate ownership, cross-seat deduplication, falsifier arbitration, sequenced remediation plan |
| **Seat 1** | **`PER-0442`** — *Travel Operating Systems Architect* | `0442_PER-0442_Travel_Operating_Systems_Architect_20250923_v1.docx` | `state-audit`, `async-audit` (`~/Projects/skills/`) | State authority, `SQLTripStore` vs `FileTripStore`, `_run_async_blocking` loop safety (`FND-0321`), `refresh_or_reselect` (`FND-0310/0311`), `TripResponse` contract parity, multi-store split-brain |
| **Seat 2** | **`PER-0443`** — *Agentic Travel Systems Architect* | `0443_PER-0443_Agentic_Travel_Systems_Architect_20250923_v1.docx` | `agentic-eval-loop` (`~/Projects/skills/`) + `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md` | TypeSafe/Jev System One governance, intake extraction truthfulness (`FND-0308/0309/0314/0316/0318`), hybrid decision engine, Ghost Concierge & `irops_healer` (`ADR-008` rungs), DLQ/evals (`FND-0161/0165`) |
| **Seat 3** | **`PER-0362`** — *Security and Privacy Architect* | `0362_PER-0362_Security_and_Privacy_Architect_20250923_v1.docx` | `security-review` (`~/Projects/skills/`) | Privacy Guard bypass (`FND-0315/0320`), SQL PII encryption at rest, GDPR Art. 15/17/20 DSR (`T14`), capability tokens (`/a/[token]`, `/p/[token]`), statutory claims (`EU261`/`UK261`/`US_DOT`), TCS/GST, secret hygiene |
| **Seat 4 (Counterposition / Skeptic)** | **`PER-1098`** — *Travel Agency / TMC UX Designer* + **`PER-0468`** — *Missing-Workflow Red Team* | `1098_PER-1098_Travel_Agency_TMC_UX_Designer_20250923_v1.docx` + `0468_PER-0468_Missing-Workflow_Red_Team_20250923_v1.docx` | `bff-backend-reconciliation` (`~/.hermes/skills/backend-patterns/bff-backend-reconciliation/`) | BFF-to-backend route/schema parity, `PlanningStageGate` dead-ends (`FND-0317`, `U11`), `T1` Ask-Traveler E2E loop, CI/CD release hazards (`TRV-N05`), stale findings audit |

### 1.2 Rejected Candidate Personas & Skills (Smallest-Sufficient-Council Discipline)

- **`PER-0352` (*Principal Systems Architect*)**: Rejected — overlaps `PER-0442` on state/persistence and `PER-0100` on synthesis without adding travel-domain state invariants.
- **`PER-0338` (*Group & Bespoke Travel Operations Lead*)**: Rejected — narrower operational lens than `PER-1098` + `PER-0468` for auditing BFF contract parity and missing E2E loops.
- **`PER-20718` (*Database Reliability & Multi-Tenant RLS Engineer*)**: Rejected — PostgreSQL `FORCE RLS` and async session pooling are fully covered by `PER-0442` (`async-audit` + `state-audit`) and `PER-0362` (`security-review`).
- **`PER-880003` (*Disruption & IROPS Specialist*)**: Rejected — statutory claim rules (`EU261`/`UK261`/`US_DOT`) and `irops_healer` autonomy bounds are covered jointly by `PER-0362` and `PER-0443`.
- **`rendered-design-system-audit` / `persona-simulation`**: Rejected for this pass — this task is a code, contract, architecture, security, and release-readiness audit rather than a live browser visual-regression pass.

---

## 2. Live Verification Baseline

| Check | Command | Outcome | Evidence Tier |
| :--- | :--- | :--- | :--- |
| Findings Ledger Integrity | `.venv/bin/python scripts/findings.py validate` | **OK**: `617` events, `321` findings (`297` closed, `5` deferred, `19` open: `0 P0`, `0 P1`, `2 P2` [`FND-0315`, `FND-0317`], `17 P3`) | `Verified` (T1) |
| Python Linter (`ruff`) | `.venv/bin/ruff check src/ spine_api/ tests/ tools/` | **FAILED (exit 1)**: `F401 [*] json imported but unused` at [`tests/test_message_store_and_feed.py:8:8`](file:///Users/pranay/Projects/travel_agency_agent/tests/test_message_store_and_feed.py#L8) (refutes prior handoff claim of "ruff clean") | `Verified` (T1) |
| TypeScript Compiler (`tsc`) | `./node_modules/.bin/tsc --noEmit` (in `frontend/`) | **PASSED (exit 0)**: zero type errors | `Verified` (T1) |
| Wave Pytest Suite (15 files) | `.venv/bin/pytest -q` across 15 Sim #3 / T1..T15 test files | **125 passed, 5 errors**: [`tests/test_refresh_after_commit.py`](file:///Users/pranay/Projects/travel_agency_agent/tests/test_refresh_after_commit.py) (4) and [`tests/test_privacy_guard_http.py`](file:///Users/pranay/Projects/travel_agency_agent/tests/test_privacy_guard_http.py) (1) hit sandbox localhost `:5432` socket `PermissionError` in `tests/conftest.py:196` (`session_client`) | `Verified` (T2) |

---

## 3. Cross-Examination & Falsifier Resolution Table

Before synthesizing the issue register, the Lead (`PER-0100`) cross-examined every seat's claims against live code and resolved the open falsifiers from [`Docs/sims/SIM3_META_AUDIT_AND_PLAN_2026-10-05.md`](file:///Users/pranay/Projects/travel_agency_agent/Docs/sims/SIM3_META_AUDIT_AND_PLAN_2026-10-05.md) and [`Docs/planning/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md`](file:///Users/pranay/Projects/travel_agency_agent/Docs/planning/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md):

| Falsifier / Contested Claim | Prior Assumption / Seat Claim | Cross-Examined Ground Truth | Verdict |
| :--- | :--- | :--- | :--- |
| **`FND-0315` Falsifier** (`SIM3_META_AUDIT_AND_PLAN_2026-10-05.md:69, 214-215`): *Why does `/inbound/parse` fail-close with 422 on raw phone/email while `/run` accepts it?* | Prior doc hypothesized `/run` intentionally skips `customer_contact` scanning and encrypts `raw_input` at rest. | **Refuted (P0 Bug)**: [`src/security/privacy_guard.py:212-213`](file:///Users/pranay/Projects/travel_agency_agent/src/security/privacy_guard.py#L212-L213) checks `if isinstance(raw_input, dict) and "fixture_id" in raw_input: return True`. [`_build_processed_trip`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L2244) sets `trip["raw_input"] = spine_output.get("meta", {})`, and [`RunMeta`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/pipeline_execution_service.py#L669-L674) always contains `"fixture_id": None`. Every live `/run` trip is falsely exempted as a synthetic test fixture! | **Upgraded `FND-0315` from P2 to P0 (`AUD-01`)** |
| **SQL Encryption-at-Rest Claim** (`SIM3_META_AUDIT_AND_PLAN_2026-10-05.md:214`) | Assumed `SQLTripStore` encrypts `raw_input` and `customer_contact` at rest via Fernet. | **Refuted (P0 Bug)**: (1) Neither `.env` nor `.env.local` sets `ENCRYPTION_KEY`, so [`SQLTripStore._get_fernet()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L800-L831) returns `None` and stores 100% plaintext. (2) Even with `ENCRYPTION_KEY` set, [`_PII_FIELDS`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L763-L785) omits `"customer_contact"`, `"raw_note"`, `"owner_note"`, `"itinerary_text"`, `"agent_notes"`, `"answer"`, and never encrypts `trips.analytics["_extra"]` ([`persistence.py:994-1001`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L994-L1001)). | **Confirmed P0 (`AUD-02`)** |
| **`T14` GDPR Art. 17 Erasure "SHIPPED" Claim** (`LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md:53`) | Marked `SHIPPED (2026-10-01)` via `spine_api/routers/dsr.py` + `trip_dsr.py`. | **Refuted (P0 Bug)**: [`erase_trip_personal_data`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/trip_dsr.py#L203-L214) constructs dotted keys (`"packet.customer_name": "[REDACTED-BY-DSR]"`). Neither `FileTripStore` nor `SQLTripStore` expands dotted paths—it adds a literal top-level key `"packet.customer_name"` and leaves nested `trip["packet"]["customer_name"]` untouched! Also leaves PII in `extracted`, `traveler_bundle`, `internal_bundle`, `DraftStore`, `CustomerMemoryProfile`, and `data/messages/*.jsonl`. | **Confirmed P0 (`AUD-03`)** |
| **Seat 1 Claim on `TripResponse.from_dict()`** (`S1-F07`) | Seat 1 claimed `TripResponse.from_dict()` strips `passenger_claim`, `ghost_concierge`, and `traveler_answers`. | **Partially Refuted / Narrowed**: Direct check of [`spine_api/contract.py:1180-1188, 1264-1272`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/contract.py#L1180-L1272) confirmed `passenger_claim`, `ghost_concierge`, and `traveler_answers` **are** mapped on `TripResponse`. However, Seat 1's finding is **Confirmed** for `reassess` (attached at `server.py:2922` and stripped at `2949`!), `flight_status_updates` (accepted in `TripPatchRequest` at `contract.py:1318` and stripped on response), `decision`, `updated_at`, `traveler_asks`, `booking_data`, `analytics`, and `fees`. | **Narrowed & Confirmed P1 (`AUD-14`)** |
| **`T1` Ask-Traveler Loop "SHIPPED" Claim** (`LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md:40`) | Marked `SHIPPED` with `/a/[token]`, `public_asks.py`, and `followups.py`. | **Refuted (P1 Bug)**: `POST /api/public/asks/{token}/answers` writes `trip["traveler_answers"]`, which has **zero readers** in `src/` or `spine_api/` (never feeds `packet.facts` or clears `blocking_unknowns`). Furthermore, `POST /followups/{trip_id}/send` is unmapped in `frontend/src/lib/route-map.ts` and has zero frontend callers (`IntakePanel.tsx` only copies text). | **Confirmed P1 (`AUD-06`)** |
| **`FND-0309` Destination Carry-Forward Fix** (`src/intake/extractors.py:3458-3474`) | Landed in Sim #3 to preserve prior candidate destinations on reprocess. | **Falsified on Operator Override (P1 Bug)**: `_extract_from_freeform` extracts old `RAW_CUSTOMER_NOTE` (`"Bali"`) before `STRUCTURED_JSON` (`"Tokyo"`), putting `"Bali"` first, and sets `dest_status = "definite"` at line 3474 *before* merging `carried` at line 3549. Also, `trip_lifecycle_service.py:54-63` ignores cleared (`None`/`""`) fields on reassess. | **Confirmed P1 (`AUD-10`)** |

---

## 4. Deduplicated Findings Register (`AUD-01` .. `AUD-20`)

### 4.1 P0 Release & Legal Blockers

#### `AUD-01` [P0] — Live `/run` Trips Falsely Classified as Synthetic Fixtures, Completely Bypassing Privacy Guard (`FND-0315` Root Cause)
- **Seats**: Seat 3 (`SEC-01`) + Lead Cross-Exam
- **Truth Label & Evidence Tier**: `Verified` (T1 static + T2 runtime trace) — Sensitivity `S0`
- **Causal Chain**:
  1. **Producer**: [`_build_processed_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L2227-L2247) sets `trip_dict["raw_input"] = spine_output.get("meta", {})` at line `2244`. In [`pipeline_execution_service.py:669-674`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/pipeline_execution_service.py#L669-L674), `RunMeta` always initializes `fixture_id: Optional[str] = None`, so `spine_output["meta"]` is a `dict` containing `"fixture_id": None`.
  2. **Contract**: [`_is_known_fixture(trip_data)`](file:///Users/pranay/Projects/travel_agency_agent/src/security/privacy_guard.py#L204-L216) checks:
     ```python
     raw_input = trip_data.get("raw_input")
     if isinstance(raw_input, dict) and "fixture_id" in raw_input:
         return True
     ```
     Because `"fixture_id" in {"fixture_id": None, ...}` evaluates to `True`, `_is_known_fixture()` returns `True` for **every live `/run` trip**.
  3. **Consumer**: [`validate_trip_before_persistence()`](file:///Users/pranay/Projects/travel_agency_agent/src/security/privacy_guard.py#L140-L157) calls `is_fixture = _is_known_fixture(trip_data)` (`line 151`) and passes `allow_synthetic=is_fixture` (`line 156`), which immediately short-circuits [`scan_trip_for_real_pii()`](file:///Users/pranay/Projects/travel_agency_agent/src/security/privacy_guard.py#L118-L119) (`if allow_synthetic: return []`).
  4. **Failure Mechanism**: Neither Layer 1 (`customer_contact` email/phone) nor Layer 2 (high-risk SSN, passport, credit card, IBAN in `raw_input`/`notes`) ever runs on `/run` persistence! Meanwhile `/api/v1/inbound/parse` ([`inbound.py:293-305`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/inbound.py#L293-L305)) passes `{"raw_input": req.text, "customer_contact": ...}` where `raw_input` is a `str`, so `_is_known_fixture` is `False` and Layer 1 raises `422 PrivacyGuardError` on normal phone/email contacts (`FND-0320`).
- **Fix Direction**:
  1. Change [`src/security/privacy_guard.py:212-213`](file:///Users/pranay/Projects/travel_agency_agent/src/security/privacy_guard.py#L212-L213) to require a truthy string `bool(raw_input.get("fixture_id"))` that matches `_KNOWN_FIXTURE_PREFIXES` or `_SYNTHETIC_DOMAINS`.
  2. Align Layer 1 (`_CRITICAL_PII_PATTERNS` on `customer_contact`) with encryption-at-rest (`AUD-02`): if `customer_contact` is encrypted at rest via Fernet, allow standard business contact fields (email/phone) while keeping Layer 2 (`_HIGH_RISK_PATTERNS`: SSN, CC, IBAN, raw passport numbers) fail-closed across both `/run` and `/inbound/parse`.

#### `AUD-02` [P0] — Plaintext PII at Rest in `SQLTripStore` (Missing `ENCRYPTION_KEY`, Incomplete `_PII_FIELDS`, Unencrypted `analytics._extra`)
- **Seats**: Seat 3 (`SEC-02`) + Seat 1 (`S1-F06`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S0`
- **Causal Chain**:
  1. **Producer**: [`SQLTripStore._get_fernet()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L800-L831) reads `os.environ.get("ENCRYPTION_KEY")`. Neither `.env` nor `.env.local` sets `ENCRYPTION_KEY`; outside `production` mode it logs a warning once and returns `None`.
  2. **Contract**: [`SQLTripStore._PII_FIELDS`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L763-L785) lists keys to encrypt during recursive dict traversal, and [`_fold_extra_into_analytics()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L747-L761) packs unmapped top-level keys (`packet`, `customer_name`, `customer_contact`, `traveler_answers`, `traveler_asks`, `passenger_claim`, `ghost_concierge`, `agent_notes`) into `analytics["_extra"]`.
  3. **Consumer**: [`SQLTripStore.save_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L994-L1001) calls `self._encrypt_pii(...)` on `extracted`, `raw_input`, `traveler_bundle`, `internal_bundle`, `booking_data`, and `pending_booking_data`, **but never calls `self._encrypt_pii()` on `analytics` (`analytics_with_extra`)** (`line 1001`). Furthermore, `_PII_FIELDS` omits `"customer_contact"`, `"raw_note"`, `"owner_note"`, `"itinerary_text"`, `"agent_notes"`, `"customer_message"`, `"respondent_name"`, and `"answer"`.
  4. **Failure Mechanism**: Even if `ENCRYPTION_KEY` is configured in production, `customer_name`, `customer_contact`, `packet`, `traveler_answers`, `agent_notes`, and `raw_note` are persisted in **plaintext JSON** inside PostgreSQL `trips.analytics._extra` and `trips.extracted`.
- **Fix Direction**:
  1. Add all missing PII field names to `SQLTripStore._PII_FIELDS`.
  2. Pass `analytics_with_extra` through `self._encrypt_pii` on write (`persistence.py:1001, 1026, 1134`) and `self._decrypt_pii` on read (`persistence.py:926`).
  3. Require or auto-provision a development `ENCRYPTION_KEY` in `STEP1_ENV.sh` / `.env.example` so local/staging runs exercise the exact encrypted code path used in production.

#### `AUD-03` [P0] — GDPR Art. 17 Erasure (`POST /api/v1/dsr/trips/{trip_id}/erase`) Fails to Scrub PII Across `TripStore`, `DraftStore`, `MemoryStore`, and `MessageStore` (`T14` Falsified)
- **Seats**: Seat 3 (`SEC-03`) + Seat 1 (`S1-F10`, `S1-F13`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S0`
- **Causal Chain**:
  1. **Producer**: [`erase_trip_personal_data()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/trip_dsr.py#L172-L246) builds `updates` (`lines 195-213`) using dotted keys for nested packet fields:
     ```python
     for key in _PACKET_PII_KEYS:
         if key in packet and packet[key] not in (None, "", REDACTION_MARKER):
             updates[f"packet.{key}"] = REDACTION_MARKER
     ```
  2. **Contract**: [`FileTripStore.update_trip_for_agency`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L510-L534) runs `trip.update(updates)` (`line 529`), and [`SQLTripStore._fold_unmapped_updates`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L131-L160) writes unknown keys directly into `analytics["_extra"][key]`. Neither store splits dotted paths.
  3. **Consumer**: Calling `POST /api/v1/dsr/trips/{trip_id}/erase` writes literal key `"packet.customer_name": "[REDACTED-BY-DSR]"` while leaving `trip["packet"]["customer_name"]`, `trip["packet"]["customer_email"]`, `trip["packet"]["customer_phone"]`, and `trip["packet"]["raw_note"]` **completely intact**!
  4. **Additional Erasure Leaks**:
     - `trip_dsr.py` never scrubs `trip["extracted"]`, `trip["traveler_bundle"]`, `trip["internal_bundle"]`, `trip["booking_data"]`, `trip["pending_booking_data"]`, `trip["agent_notes"]`, `trip["traveler_asks"]`, `trip["traveler_answers"]`, or `trip["passenger_claim"]`.
     - [`_tombstone_trip_messages()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/dsr.py#L64-L103) only matches phone numbers from `packet.customer_phone` / `trip.customer_phone` (missing `customer_contact` and `extracted.customer_phone`), never matches messages by `row.get("trip_id") == trip_id`, leaves `from_party` / `to_party` phone numbers in plaintext on tombstoned JSONL lines (`lines 89-97`), and rewrites `data/messages/{agency_id}.jsonl` without acquiring `message_store._WRITE_LOCK`.
     - Neither `DraftStore` (`data/drafts/{trip_id}.json`) nor SQL `CustomerMemoryProfile` / `MemoryStore` / `GDPRMemoryEngine` is invoked during DSR erasure.
     - Subsequent `GET /api/v1/dsr/trips/{trip_id}/export` returns the unredacted `packet` and `extracted` PII alongside `"dsr_erased": true`.
- **Fix Direction**:
  1. Mutate a deep copy of `trip["packet"]`, `trip["extracted"]`, `trip["traveler_bundle"]`, `trip["internal_bundle"]`, `trip["booking_data"]`, `trip["pending_booking_data"]`, `trip["traveler_asks"]`, `trip["traveler_answers"]`, `trip["passenger_claim"]`, and `trip["agent_notes"]` in `erase_trip_personal_data()` and pass top-level keys to `update_trip_for_agency`.
  2. In `_tombstone_trip_messages()`, acquire `_WRITE_LOCK`, match by `row.get("trip_id") == trip_id` OR phone/email from `customer_contact`/`packet`/`extracted`, and redact `from_party`/`to_party`.
  3. Delete `DraftStore` drafts for `trip_id` and invoke `CustomerMemoryProfile` / `GDPRMemoryEngine` erasure when requested.

#### `AUD-04` [P0] — Unconditional Production Auto-Deploy on `master`/`main` Push While Launch Status Is `NO-GO` (`TRV-N05` / Blocker 8)
- **Seats**: Seat 4 (`S4-06`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: [`.github/workflows/deploy.yml:3-10`](file:///Users/pranay/Projects/travel_agency_agent/.github/workflows/deploy.yml#L3-L10) triggers on `workflow_run: workflows: ["CI"], types: [completed], branches: [master, main]`.
  2. **Contract**: [`Docs/LAUNCH_STATUS.md:1-15`](file:///Users/pranay/Projects/travel_agency_agent/Docs/LAUNCH_STATUS.md#L1-L15) declares `Overall Verdict: NO-GO`, and [`Docs/planning/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md:331`](file:///Users/pranay/Projects/travel_agency_agent/Docs/planning/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md#L331) tracks `TRV-N05` / Blocker 8 as `OPEN P1`.
  3. **Consumer**: [`.github/workflows/deploy.yml:27-42`](file:///Users/pranay/Projects/travel_agency_agent/.github/workflows/deploy.yml#L27-L42) executes `flyctl deploy --remote-only` with `FLY_API_TOKEN` whenever `github.event.workflow_run.conclusion == 'success'` with no `environment: production` manual approval gate and no check against `Docs/LAUNCH_STATUS.md`.
  4. **Failure Mechanism**: Pushing the current dirty tree to `master` after CI passes will automatically deploy unverified `NO-GO` code to Fly.io production.
- **Fix Direction**: Restrict `.github/workflows/deploy.yml` to `workflow_dispatch` (or require a GitHub `environment: production` manual approval gate + a CI step asserting `Overall Verdict: GO` in `Docs/LAUNCH_STATUS.md`).

---

### 4.2 P1 Functional, Security, & Architectural Blockers

#### `AUD-05` [P1] — Live Serving Spine Sends Unredacted Traveler PII to External TypeSafe/Jev API Without `llm_egress` or Cost Guard, and Mutates `os.environ` from `.env`
- **Seats**: Seat 2 (`FND-S2-001`) + Seat 3
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S0`
- **Causal Chain**:
  1. **Producer**: Despite the module docstring in [`src/llm/typesafe_client.py:17-19`](file:///Users/pranay/Projects/travel_agency_agent/src/llm/typesafe_client.py#L17-L19) claiming *"Benchmark lane only ... This client is not the serving path"*, [`run_spine_once()`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py#L285-L287) instantiates `IntakeAmbiguityClassifier()` on every live intake run (`enable_ambiguity_classifier: bool = True` by default at `line 172`), which constructs `TypesafeJevClient(model="jev-1.13.0")` ([`ambiguity_classifier.py:57, 189-203`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/ambiguity_classifier.py#L57)). Likewise, [`triage_customer_message()`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/live_triage.py#L93-L95) calls `TypesafeJevClient` on `POST /api/triage/message`.
  2. **Contract**: Global Agent Control Plane (`Jev/TypeSafe` rule) and [`spine_api/core/llm_egress.py:1-14`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/core/llm_egress.py#L1-L14) mandate that external LLM calls send **only redacted state** (`redact_pii` + `add_prompt_delimiters`) and enforce `LLMUsageGuard`.
  3. **Consumer**: [`ambiguity_classifier.py:189`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/ambiguity_classifier.py#L189) passes raw `note[:800]` and [`live_triage.py:128`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/live_triage.py#L128) passes raw `message[:1200]` directly into `TypesafeJevClient.decide()`, which `POST`s to `https://api.typesafe.ai/v1/systemone` ([`typesafe_client.py:29, 175-204`](file:///Users/pranay/Projects/travel_agency_agent/src/llm/typesafe_client.py#L175-L204)) with **zero PII redaction**, **zero prompt delimiters**, and **zero `LLMUsageGuard` accounting**. Furthermore, [`_resolve_api_key()`](file:///Users/pranay/Projects/travel_agency_agent/src/llm/typesafe_client.py#L46-L60) reads `.env`/`.env.local` from disk and calls `os.environ.setdefault(name, value)`, silently activating external network egress in tests and local runs whenever a key exists in `.env`.
- **Fix Direction**:
  1. Route all `TypesafeJevClient.decide()` inputs through `redact_pii()` and `add_prompt_delimiters()` (`spine_api/core/llm_egress.py`).
  2. Remove `.env` file-scanning and `os.environ.setdefault` mutation from `_resolve_api_key()`; require explicit env injection + an explicit `ENABLE_LIVE_JEV_SERVING=true` feature flag on the serving path.

#### `AUD-06` [P1] — `T1` Ask-Traveler Channel (`/a/[token]`) Is Disconnected at Both Ends (`traveler_answers` Has Zero Readers; `/followups/{trip_id}/send` Unmapped in BFF)
- **Seats**: Seat 4 (`S4-01`) + Seat 1 (`S1-F07`) + Seat 3 (`SEC-05`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Operator -> Traveler Break**: Backend implements `POST /followups/{trip_id}/send` ([`spine_api/routers/followups.py:326`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/followups.py#L326)) to mint `/a/{token}` and record outbound asks. However, [`frontend/src/lib/route-map.ts`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts) has **no mapping** for `/followups/{trip_id}/send`, and [`IntakePanel.tsx:1146-1158`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/IntakePanel.tsx#L1146-L1158) only copies text to the clipboard (`navigator.clipboard.writeText`). Additionally, [`frontend/src/app/(agency)/trips/[tripId]/followups/PageClient.tsx:51`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/trips/%5BtripId%5D/followups/PageClient.tsx#L51) fetches `/api/followups/dashboard`, which is also unmapped in `route-map.ts` and returns `404`.
  2. **Traveler -> Spine Break**: When a traveler submits answers on `/a/[token]`, [`POST /api/public/asks/{token}/answers`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/public_asks.py#L103-L160) appends `{question_id, answer, ...}` to `trip["traveler_answers"]`. Ripgrep across `src/` and `spine_api/` proves `traveler_answers` has **zero readers** in the intake, extraction, validation, or reassessment pipeline—answers never update `packet.facts`, never clear `blocking_unknowns`, and never trigger reassessment.
  3. **Operator Visibility Break**: `TripResponse` ([`spine_api/contract.py:1137-1308`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/contract.py#L1137-L1308)) includes `traveler_answers` (`line 1188`) but omits `traveler_asks`, and no workspace component (`IntakePanel.tsx`, `DecisionPanel.tsx`) renders `trip.traveler_answers`.
- **Fix Direction**:
  1. Map `POST /api/trips/[tripId]/followups/send` and `GET /api/followups/dashboard` in `frontend/src/lib/route-map.ts` and wire a "Send Ask Link" button in `IntakePanel.tsx`.
  2. Map `question_id` / slot answers in `submit_public_ask_answers` (or an operator "Apply & Reprocess Answers" action) into `structured_json` / `raw_note` and invoke `reassess_trip`, plus render `traveler_answers` and `traveler_asks` in `IntakePanel.tsx`.

#### `AUD-07` [P1] — Live Jev Message Triage (`POST /api/triage/message`) Returns 404 in BFF and Has Incompatible Response Schema
- **Seats**: Seat 4 (`S4-02`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: [`DecisionPanel.tsx:55-72`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/DecisionPanel.tsx#L55-L72) and [`IntakeTab.tsx:61-80`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/trip-workspace/tabs/IntakeTab.tsx#L61-L80) call `triageCustomerMessage()` -> `POST /api/triage/message` ([`api-client.ts:2046-2055`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/api-client.ts#L2046-L2055)).
  2. **Contract**: [`frontend/src/lib/route-map.ts`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts) has **no entry** for `/api/triage/message` (`resolveBackendRoute` returns `null` -> `404`), and `DecisionPanel.tsx:69` / `IntakeTab.tsx:76` swallow the error with `catch { // Triage is advisory }`.
  3. **Schema Mismatch**: Even if mapped in `route-map.ts`, [`MessageTriageResponse`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/message_triage.py#L32-L42) returns `{urgency, intent, requires_human_escalation, ...}` and omits `ok`, `latency_ms`, `sentiment`, `routing_recommendation`, and `advisory` required by frontend [`LiveMessageTriageResponse`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/api-client.ts#L2033-L2044) (`res.ok` at `DecisionPanel.tsx:64` is `undefined`, so `triageResult` is never set!).
- **Fix Direction**: Add `/api/triage/message` -> `/api/triage/message` to `frontend/src/lib/route-map.ts` and align `MessageTriageResponse` in `spine_api/routers/message_triage.py` with `LiveMessageTriageResponse`.

#### `AUD-08` [P1] — `FND-0321` Root Cause: 7 SQL Stores Share FastAPI's Main-Loop `AsyncEngine` Inside `_SYNC_ASYNC_BRIDGE`, Plus Unawaited Coroutine in `SQLRunCheckpointStore.list_metas`
- **Seats**: Seat 1 (`S1-F01`, `S1-F02`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: [`_run_async_blocking()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L220-L246) dispatches coroutines from sync callers onto a dedicated background thread running a persistent event loop (`_SYNC_ASYNC_BRIDGE.loop`). `SQLTripStore` avoids loop collisions by creating a loop-keyed `AsyncEngine` in [`tripstore_session_maker()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/core/database.py#L54-L90).
  2. **Contract**: An `asyncpg` connection pool bound to `spine_api.core.database.engine` (FastAPI's main uvloop) cannot be awaited on `_SYNC_ASYNC_BRIDGE.loop`.
  3. **Consumer**: Seven other SQL stores call `_run_async_blocking()` while using `AsyncSessionLocal` / `get_rls_session` bound to the global `engine`:
     - [`spine_api/run_ledger_sql.py:132-279`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/run_ledger_sql.py#L132-L279) (`SQLRunCheckpointStore`, `SQLDeadLetterQueue`)
     - [`src/orchestration/agent_lease.py:157-291`](file:///Users/pranay/Projects/travel_agency_agent/src/orchestration/agent_lease.py#L157-L291) (`SQLAgentLeaseStore`)
     - [`src/agents/idempotency.py:113-171`](file:///Users/pranay/Projects/travel_agency_agent/src/agents/idempotency.py#L113-L171) (`SQLIdempotencyStore`)
     - [`spine_api/services/proposal_token_store.py:140-260`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/proposal_token_store.py#L140-L260) (`SQLProposalTokenStore`)
     - [`spine_api/services/advisor_payout_store.py:216-247`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/advisor_payout_store.py#L216-L247)
     - [`spine_api/services/payment_mandate_service.py:196-306`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/payment_mandate_service.py#L196-L306)
     - [`spine_api/services/authority_approval_service.py:163-295`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/authority_approval_service.py#L163-L295)
     Furthermore, [`SQLTripStore`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L1217-L1225) calls `await emit_event_best_effort(...)` inside `_SYNC_ASYNC_BRIDGE`, which opens `AsyncSessionLocal()` ([`event_service.py:18, 91`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/event_service.py#L91)) on the global `engine`!
  4. **Unawaited Coroutine**: [`SQLRunCheckpointStore.list_metas()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/run_ledger_sql.py#L290-L303) executes `rows = session.scalars(query.limit(limit)).all()` (`line 300`) without `await`, raising `AttributeError: 'coroutine' object has no attribute 'all'`.
- **Fix Direction**:
  1. Make `get_rls_session()` and `event_service.py` resolve their session factory via loop-keyed `tripstore_session_maker()` whenever `asyncio.get_running_loop()` differs from the main loop (or unify all loop-keyed session creation in `spine_api/core/database.py`).
  2. Change `spine_api/run_ledger_sql.py:300` to `rows = (await session.scalars(query.limit(limit))).all()`.

#### `AUD-09` [P1] — Reprocessing a Trip (`save_processed_trip` -> `save_trip`) Destructively Overwrites Booking Columns & Wipes `analytics._extra` (`traveler_answers`, `passenger_claim`, `ghost_concierge`, etc.)
- **Seats**: Seat 1 (`S1-F03`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: [`reassess_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/trip_lifecycle_service.py#L101-L108) calls `save_processed_trip(..., preserve_trip_id=trip_id)`. [`_build_processed_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L2227-L2277) constructs a fresh `trip_dict` carrying over only `status_history` (`lines 2253-2263`).
  2. **Contract**: Reprocessing intake on an existing trip must preserve auxiliary operational state (`traveler_answers`, `traveler_asks`, `passenger_claim`, `ghost_concierge`, `flight_status_updates`, `booking_data`, `pending_booking_data`, `assigned_to_id`, `commission`, `booking_confirmation`, `journey_graph_nodes`).
  3. **Consumer**: [`SQLTripStore.save_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L1011-L1057) overwrites existing row columns (`booking_data = None`, `pending_booking_data = None`, `booking_data_source = None`, `assigned_to_id = None` at `lines 1030-1033`) and replaces `existing_trip.analytics` with `analytics_with_extra` built from the fresh `trip_dict` (`line 1026`), wiping all prior `analytics["_extra"]` keys! [`FileTripStore.save_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L469-L473) similarly preserves only `status_history` and overwrites the JSON file.
- **Fix Direction**: In `_build_processed_trip()` and `SQLTripStore.save_trip()` / `FileTripStore.save_trip()`, merge existing `analytics._extra` keys and preserve non-spine columns (`booking_data`, `pending_booking_data`, `booking_data_source`, `assigned_to_id`, `traveler_asks`, `traveler_answers`, `passenger_claim`, `ghost_concierge`, `flight_status_updates`) unless explicitly replaced.

#### `AUD-10` [P1] — `FND-0309` Destination Carry-Forward Inverts Operator Override Precedence, Locks `dest_status = "definite"`, and Ignores Cleared Fields on Reassess
- **Seats**: Seat 2 (`FND-S2-002`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: On reassessment, [`reassess_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/trip_lifecycle_service.py#L54-L99) passes both `[RAW_CUSTOMER_NOTE(original_raw)]` and `[STRUCTURED_JSON(merged_structured)]` into `run_spine_once()`.
  2. **Contract**: An operator's explicit `structured_json` edit (or clearing a field to `""`/`None`) must take precedence over the historical `raw_note`.
  3. **Consumer**:
     - [`trip_lifecycle_service.py:57-59`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/trip_lifecycle_service.py#L57-L59) filters `if v is not None and v != ""` when merging `req.structured_json` over `existing_structured`, making it **impossible for an operator to clear a previously extracted field**.
     - In [`extract_all()`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/extractors.py#L3458-L3555), `_extract_from_freeform(freeform_text)` (`line 3461`) runs on the original `RAW_CUSTOMER_NOTE` (`"Bali"`), and `_extract_from_structured` (`line 3470`) appends the new structured destination (`"Tokyo"`) *after* `"Bali"` (`candidates = ["Bali", "Tokyo"]`).
     - At `line 3474`, `dest_status = "definite" if len(candidates) == 1 else "candidates"` runs **before** the `FND-0309` carry-forward block (`lines 3544-3555`), so if `candidates` had 1 item and `carried` adds a 2nd item, `dest_status` stays `"definite"` while `len(candidates) == 2`—violating the `FND-0308` invariant!
- **Fix Direction**:
  1. Allow explicit `None` / `""` in `req.structured_json` to clear keys in `existing_structured` (`trip_lifecycle_service.py:54-63`).
  2. When `STRUCTURED_JSON` explicitly provides `destination` / `destinations`, treat it as an operator override (replacing rather than appending behind freeform/carried candidates), and recompute `dest_status` *after* any candidate list mutation (`extractors.py:3550`).

#### `AUD-11` [P1] — Public Proposal Acceptance (`POST /api/public/proposals/{token}/accept`) Fails With HTTP 409 Under PostgreSQL `FORCE RLS`, and `/a/{token}` Can Be Reused on `/p/{token}`
- **Seats**: Seat 3 (`SEC-04`, `SEC-05`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S0`
- **Causal Chain**:
  1. **RLS Break on Public Proposal Accept**: [`accept_public_proposal()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/public_proposals.py#L990) calls `TripStore.update_trip(trip_id, {...})` instead of `TripStore.update_trip_for_agency(trip_id, token_agency_id, {...})`. Because `/api/public/proposals/{token}/accept` is unauthenticated, `get_current_agency_id()` is `None`, so [`SQLTripStore.update_trip()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L1079-L1107) sets `app.current_agency_id = ''`, matches `0` rows under `FORCE ROW LEVEL SECURITY`, returns `None`, and raises `HTTPException(status_code=409, detail="Proposal state changed during acceptance; please retry.")` (`lines 1002-1006`). Similarly, `public_proposals.py:829` calls `get_trip_for_public_access(trip_id)` without `token_agency_id`.
  2. **Cross-Surface Token Reuse**: [`followups.py:347`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/followups.py#L347) mints Ask-Traveler tokens using `generate_signed_proposal_token(trip_id, agency_id=agency_id)`, and [`public_asks.py:41`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/public_asks.py#L41) validates them with `verify_proposal_token(token)`—with **no token purpose/scope claim**. A traveler given an intake clarification link (`/a/{token}`) can substitute the same token into `/p/{token}` (`GET /api/public/proposals/{token}` and `POST /api/public/proposals/{token}/accept`)!
- **Fix Direction**:
  1. Replace `TripStore.update_trip(trip_id, ...)` at `public_proposals.py:990` with `TripStore.update_trip_for_agency(trip_id, token_agency_id, ...)` and pass `agency_id=token_agency_id` at `line 829`.
  2. Add a signed `purpose` / `scope` claim (`"proposal"` vs `"ask"`) to token generation and verification so `/a/{token}` and `/p/{token}` tokens are cryptographically domain-separated.

#### `AUD-12` [P1] — Statutory Claims & `irops_healer` Defects: Hardcoded `distance_km=0.0`, GBP/USD-to-EUR Mislabeling, UK Carrier Misrouting, and Unmasked 16-Digit VCC PAN/CVV Persistence
- **Seats**: Seat 3 (`SEC-06`) + Seat 2 (`FND-S2-006`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S0`
- **Causal Chain**:
  1. **Hardcoded `distance_km=0.0` in Formal Claim Endpoint**: [`generate_formal_airline_claim()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/passenger_rights.py#L223-L231) hardcodes `distance_km = 0.0`, forcing every claim generated via `POST /api/v1/passenger-rights/trips/{trip_id}/generate-claim` into the lowest `<1500 km` tier (`€250` / `£220`), under-claiming long-haul disruptions (`€600` / `£520`).
  2. **Currency Erasure & False Conversion**: [`PassengerRightsAdvocate.assess_disruption_eligibility()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/passenger_rights_claims.py#L88-L126) discards `_currency` (`"GBP"` under `UK261`, `"USD"` under `US_DOT`) with `tier, amount, _currency = ...`, labels `statutory_compensation_eur: amount` (`line 116`), and multiplies `amount * 1.09` (`line 117`)—turning `£520` into `"520 EUR ($566.80 USD)"`.
  3. **Jurisdiction Misrouting (`UK261` vs `EU261`)**: In [`claim_framework.py:233-243`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/claim_framework.py#L233-L243), Rule 6 checks `if car in EU261_COUNTRIES or car == UNITED_KINGDOM: return "EU261", ...`—routing UK-licensed carriers (`BA`, `VS`) arriving in the EU from a third country to `EU261` instead of `UK261` (and missing UK carriers arriving in the UK from a third country). In addition, [`_country_text_hint()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/passenger_rights.py#L143-L154) omits `KNOWN_COUNTRIES`, so city/country text routes like `"New York to Tokyo"` on BA/LH resolve `dep=None, arr=None` and fall through to Rule 6 (`EU261`).
  4. **Unmasked 16-Digit VCC PAN & CVV Persisted via `ghost_concierge_monitor`**: [`process_disruption_Into_ghost_concierge()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/ghost_concierge_monitor.py#L225-L236) chains `IROPSAutoHealerEngine.execute_healing_protocol()` ([`src/orchestration/irops_healer.py:95-96, 143-159`](file:///Users/pranay/Projects/travel_agency_agent/src/orchestration/irops_healer.py#L95-L159)), which hardcodes `"EU261"` and calls `issue_supplier_vcc()`, generating a 16-digit `"4000..."` `card_number` and 3-digit `cvv` and persisting them into `trip["ghost_concierge"]["healer_plan"]` (returned on `GET /trips/{id}`) in violation of `ADR-008` Rung 3 and PCI-DSS hygiene.
- **Fix Direction**:
  1. Compute real great-circle distance (or extract from flight segment metadata) in `passenger_rights.py:223`, preserve `_currency` from `compute_tier_and_amount`, and fix Rule 6 in `claim_framework.py` + `_country_text_hint` in `passenger_rights.py`.
  2. Remove automatic `issue_supplier_vcc()` execution from `irops_healer.py` / `ghost_concierge_monitor.py` during draft generation (keep VCC issuance strictly behind an operator Rung 3 approval action and store only masked last-4 tokens).

#### `AUD-13` [P1] — Frontend `getRequiredPlanningFields()` Diverges from Backend `blocking_unknowns()` in Both Directions (`U11`)
- **Seats**: Seat 4 (`S4-04`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: Backend [`ValidationResult.blocking_unknowns()`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/validation.py#L64-L81) computes blocking unknowns dynamically from stage-aware `validation.errors` and `blocking_questions` (which at `shortlist`/`itinerary`/`booking_prep` include `origin_city`, `trip_purpose`, `passport_status`, `visa_status`, plus date contradictions; whereas at `planning` under TS-07 only `destination` and `date_window` are hard errors).
  2. **Contract**: Frontend `PlanningStageGate` and `IntakeChecklist` must reflect the exact blocking state of the backend spine.
  3. **Consumer**: [`getRequiredPlanningFields()`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/planning-status.ts#L54-L115) hardcodes 5 fields (`destination`, `dates`, `party`, `budget`, `origin`), checks `origin_city` **only** in `trip.validation?.warnings` (`lines 54-57`, missing `trip.validation?.errors` where `origin_city` lives at `shortlist+`!), and completely ignores `trip_purpose`, `passport_status`, and `visa_status`.
  4. **Failure Mechanism**:
     - *False Ready*: At `shortlist`/`booking_prep`, a trip missing `origin_city`, `passport_status`, or `visa_status` shows `"5/5 required details captured — Ready to build options"` in the UI while the backend blocks with `PROCEED_WITH_ASKS`.
     - *False Locked*: At `planning` stage (TS-07), a trip with `destination` + `dates` is `PROCEED` on the backend (`blocking_unknowns == []`), but `PlanningStageGate` locks the `strategy` and `decision` tabs because `budget` or `party` is only a soft warning!
- **Fix Direction**: Drive `getPlanningStatus()` in `frontend/src/lib/planning-status.ts` directly from backend `trip.validation?.errors` and `trip.decision?.follow_up_questions` (where `blocking === true`), falling back to local heuristics only when backend validation is absent.

#### `AUD-14` [P1] — `TripResponse.from_dict()` Silently Strips `reassess`, `decision`, `updated_at`, `flight_status_updates`, `traveler_asks`, `booking_data`, `analytics`, and `fees`
- **Seats**: Seat 1 (`S1-F07`) + Lead Cross-Exam
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Causal Chain**:
  1. **Producer**: Backend endpoints and stores attach `reassess` ([`server.py:2922`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py#L2922)), `flight_status_updates` ([`contract.py:1318`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/contract.py#L1318) in `TripPatchRequest`), `decision` (`DecisionResult` from `run_spine_once`), `updated_at` (for optimistic concurrency control), `traveler_asks` ([`followups.py:372`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/followups.py#L372)), `booking_data`, `analytics`, and `fees`.
  2. **Contract**: `GET /trips/{id}`, `PATCH /trips/{id}`, and `POST /trips/{id}/reassess` serialize through [`TripResponse.from_dict()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/contract.py#L1137-L1308).
  3. **Consumer**: `TripResponse` omits those 8 fields:
     - In `POST /trips/{id}/reassess` ([`server.py:2922, 2949`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py#L2922-L2949)), `updated_trip["reassess"] = ...` is set and immediately stripped 27 lines later by `TripResponse.from_dict(updated_trip)`!
     - `PATCH /trips/{id}` accepts `flight_status_updates` on `TripPatchRequest` (`contract.py:1318`), persists it, and strips it from the response.
     - Omitting `updated_at` prevents the frontend from updating its `expected_updated_at` CAS token after a `GET` or `PATCH`, causing subsequent `PATCH` calls with `expected_updated_at` to fail with `409 Conflict`.
- **Fix Direction**: Add `reassess`, `decision`, `updated_at`, `flight_status_updates`, `traveler_asks`, `booking_data`, `pending_booking_data`, `analytics`, and `fees` to `TripResponse` and `TripResponse.from_dict()` in `spine_api/contract.py`, and add a contract parity test asserting every key written by `TripPatchRequest`, `_build_processed_trip`, and trip routers round-trips through `TripResponse.from_dict()`.

#### `AUD-15` [P1] — Operator Override Cache Invalidation Hardcodes `cache_key = None` (`TRV-N03`)
- **Seats**: Seat 1 (`S1-F12`) + Seat 4 (`S4-07`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S2`
- **Causal Chain**:
  1. **Producer**: [`override_trip_decision()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/legacy_ops.py#L666-L674) calls `learn_from_operator_override(trip_id=trip_id, cache_key=cache_key, ...)` with `cache_key = None  # TODO(P1): derive cache key from trip packet`.
  2. **Contract**: When an operator overrides an AI decision, [`learn_from_operator_override()`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/hybrid_engine.py#L261-L266) must invalidate `DecisionCache` (`if cache_key and _decision_cache: _decision_cache.invalidate(cache_key)`).
  3. **Consumer**: Because `cache_key` is hardcoded to `None`, `DecisionCache.invalidate()` is **never called in production**, serving stale pre-override decisions on subsequent runs with identical packet parameters.
- **Fix Direction**: Compute `cache_key = DecisionCache.compute_key(packet_dict, model_id)` in `spine_api/routers/legacy_ops.py:667` before calling `learn_from_operator_override`.

#### `AUD-16` [P1] — Hardcoded Fallback HMAC Key in `GDPRMemoryEngine` & Plaintext PII Logged into Immutable Hash-Chained `audit_logs.changes`
- **Seats**: Seat 3 (`SEC-07`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S0`
- **Causal Chain**:
  1. **Hardcoded GDPR HMAC Key**: [`GDPRMemoryEngine.erase_entity_memories()`](file:///Users/pranay/Projects/travel_agency_agent/src/memory/gdpr_engine.py#L28) defaults `secret_key: str = "waypoint-gdpr-secret-key-2026"` instead of reading `os.environ["GDPR_SIGNING_KEY"]` (unlike [`spine_api/routers/dsr.py:56`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/dsr.py#L56)).
  2. **Plaintext PII in Immutable Audit Chain**: [`customer_memory.py:372`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/customer_memory.py#L372), [`public_proposals.py:1013-1014`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/public_proposals.py#L1013-L1014) (`accepted_by_name`, `accepted_by_email`), and [`followups.py:382`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/followups.py#L382) write plaintext PII into `AuditLog.changes`. Because [`audit_chain_hash.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/audit_chain_hash.py#L39-L50) hashes `changes` into an immutable cryptographic chain (`row_hash`), erasing PII later breaks the audit chain, while keeping the chain intact violates GDPR Art. 17!
- **Fix Direction**: Require `GDPR_SIGNING_KEY` from env in `GDPRMemoryEngine`, and hash/redact PII fields (`sha256` pseudonym or `[REDACTED]`) before passing `changes` to `log_audit_event()`.

---

### 4.3 P2 & P3 Workflow, Evaluation, Schema, and Hygiene Findings

#### `AUD-17` [P2] — Disruption Claims UX Dead-End (`FND-0317`): `PlanningStageGate` Locks Decision Tab on Blocked Disruption Trips, and `ClaimDispositionCard` / `GhostConciergeCard` Have Zero Action Triggers
- **Seats**: Seat 4 (`S4-03`)
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S1`
- **Evidence**:
  1. [`frontend/src/lib/planning-status.ts:12, 145-152`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/planning-status.ts#L145-L152) blocks `strategy` and `decision` tabs whenever `status.missingCount > 0`. [`DecisionPanel.tsx:266-310`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/DecisionPanel.tsx#L266-L310) wraps the entire panel—including `ClaimDispositionCard` (`line 368`) and `GhostConciergeCard` (`line 378`)—inside `<PlanningStageGate stage="decision">`, locking operators out of disruption handling whenever a disruption note lacks budget/party (`FND-0317`).
  2. Even when unlocked, [`ClaimDispositionCard.tsx:166-267`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/ClaimDispositionCard.tsx#L166-L267) and [`GhostConciergeCard.tsx:157-293`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/GhostConciergeCard.tsx#L157-L293) are 100% read-only display components with zero buttons or API calls, and `POST /api/v1/passenger-rights/trips/{trip_id}/generate-claim` + `POST /api/v1/passenger-rights/trips/{trip_id}/claim/disposition` are unmapped in `frontend/src/lib/route-map.ts`.

#### `AUD-18` [P2] — Jev Contract & Spine Evaluation Gaps (`FND-S2-003`, `FND-S2-004`, `FND-S2-005`, `FND-S2-007`)
- **Seats**: Seat 2
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S2`
- **Evidence**:
  1. **Jev `question` vs `instructions` Key Mismatch & Multi-Property Confidence Overwrite (`FND-S2-003`)**: [`failure_triage.py:74`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/failure_triage.py#L74) and [`nl_evaluator.py:90`](file:///Users/pranay/Projects/travel_agency_agent/src/corporate_policy/nl_evaluator.py#L90) pass `"question"` in `decision_schema`, whereas [`TypesafeJevClient.decide()`](file:///Users/pranay/Projects/travel_agency_agent/src/llm/typesafe_client.py#L162) reads `decision_schema.get("instructions")`, dropping the system prompt on live API calls! Also, `decide()` (`lines 215-235`) overwrites `raw_confidence` in each loop iteration, so multi-property schemas (`live_triage.py`, `ambiguity_classifier.py`, `scorer.py`) only check the **last** property's confidence against `confidence_threshold`.
  2. **`FND-0316` Jev Coherence Guard Ordering & Incomplete Check (`FND-S2-004`)**: In [`src/intake/orchestration.py:424-439`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py#L424-L439), the `FND-0316` guard runs **before** Phase 9 (`make_decision`), so `decision.follow_up_questions` has not yet been populated by Phase 9b (`decision.py:490-519`), and the guard only checks `validation.blocking_unknowns()`—missing unresolved material ambiguities, hard suitability stops, and `ESCALATE` criteria.
  3. **Mixed Senior + Family Party Undercount (`FND-S2-005`)**: In [`src/intake/extractors.py:2495-2505`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/extractors.py#L2495-L2505), `_NAMED_AGE_PERSON_RE` returns early as soon as `len(named_age_matches) >= 2`, ignoring explicit adult/child counts in mixed notes like `"We are 2 adults and 1 child, traveling with my parents Ramesh (68) and Sunita (65)"` (returning `party_size=2` instead of `5`).
  4. **Disconnected In-Memory DLQ/Checkpoints (`FND-0161`) & Accuracy-Only Eval Manifest (`FND-0165`) (`FND-S2-007`)**: Three disconnected checkpoint/DLQ systems exist (`spine_api/run_ledger.py`, `src/agents/runtime.py`, `src/orchestration/langgraph_runtime.py`), `server.py:926-945` mounts the in-memory `RunCheckpointStore`/`DeadLetterQueue` instead of `SQLRunCheckpointStore`/`SQLDeadLetterQueue`, and `src/evals/manifest.py:139-203` (`check_Threshold_gates`) enforces accuracy-only thresholds without cost, latency, or escalation bounds.

#### `AUD-19` [P2] — Persistence, Schema Drift, & Multi-Store Split-Brain (`S1-F05`, `S1-F08`, `S1-F09`, `S1-F10`, `S1-F13`)
- **Seats**: Seat 1
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S2`
- **Evidence**:
  1. **Post-Commit `emit_event_best_effort` on Released RLS Connection (`S1-F05`)**: While `refresh_or_reselect` (`spine_api/core/rls.py:114-149`) cleanly fixed `FND-0310`/`FND-0311` across all 20 service call sites, [`document_service.py:139-142, 232-235, 315-318`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/document_service.py#L139-L142) still calls `await emit_event_best_effort(db, ...)` after `await db.commit()` on the released PgBouncer connection.
  2. **Canonical Packet & Frontend Type Drift (`S1-F08`, `S1-F09`)**: [`specs/canonical_packet.schema.json`](file:///Users/pranay/Projects/travel_agency_agent/specs/canonical_packet.schema.json) (`additionalProperties: false`) is missing `date_flexibility` and `trip_stage` emitted by [`CanonicalTripPacket.to_dict()`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py#L186-L202). [`frontend/src/types/spine.ts`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/types/spine.ts) is hand-maintained rather than generated from `scripts/export_openapi.py`, omitting Sim #3 fields (`passenger_claim`, `ghost_concierge`, `traveler_answers`, `branch_options`, `date_flexibility`).
  3. **3-Way Customer Memory Split-Brain (`S1-F10` / `U1`)**: `/api/v1/customers` writes to SQL `CustomerMemoryProfile` ([`customer_memory.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/customer_memory.py)), agent tools write to `src/memory/memory_store.py`, and `/run` reads neither unless the caller manually passes `repeat_customer_profile` in the request payload ([`pipeline_execution_service.py:187`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/pipeline_execution_service.py#L187)).
  4. **`message_store.py` Phone Matching Checks Empty `packet` (`S1-F13`)**: [`match_trip_by_phone()`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/message_store.py#L124-L146) inspects `trip.get("packet")` (`line 130`), which is empty on `SQLTripStore` trips (where extraction lives in `trip.get("extracted")`), breaking inbound WhatsApp/SMS phone-to-trip matching in SQL mode.

#### `AUD-20` [P2/P3] — XML Injection in Tally Export, Cross-Tenant KDD Glob, Workspace Hygiene, Lint Failure, & Stale Findings
- **Seats**: Seat 3 (`SEC-08`, `SEC-09`) + Seat 4 (`S4-08`) + Lead Baseline
- **Truth Label & Evidence Tier**: `Verified` (T1) — Sensitivity `S2`
- **Evidence**:
  1. **Tally XML Injection & Lax PAN Check (`SEC-08`)**: [`export_tally_xml()`](file:///Users/pranay/Projects/travel_agency_agent/src/accounting/export_bridge.py#L69-L95) interpolates `entry.narration` (`line 83`) and `line.account_name` (`line 85`) into XML via raw f-strings without `xml.sax.saxutils.escape()`, and [`tax_compliance.py:136`](file:///Users/pranay/Projects/travel_agency_agent/src/accounting/tax_compliance.py#L136) validates Indian PAN using only `len(customer_pan.strip()) == 10` instead of regex `^[A-Z]{5}[0-9]{4}[A-Z]$`.
  2. **Cross-Tenant Override Glob in KDD Analytics (`KDD-3`)**: [`src/analytics/kdd/jobs.py:126`](file:///Users/pranay/Projects/travel_agency_agent/src/analytics/kdd/jobs.py#L126) globs `overrides_*.jsonl` across all agencies without filtering by `agency_id`.
  3. **Workspace Secret & Artifact Hygiene (`SEC-09` / `TRV-N04`)**: `.env` and `.env.local` have `0644` world-readable permissions; `.gitignore` does not ignore `data/messages/` or `data/trips/t11hook002.json`; and 12 root clutter files (`dogfood_cookies.txt`, `test_*.db`, `*.Basic.json`) remain in the workspace root.
  4. **Lint & Test Fixture Hygiene**: [`tests/test_message_store_and_feed.py:8`](file:///Users/pranay/Projects/travel_agency_agent/tests/test_message_store_and_feed.py#L8) has an unused `import json` breaking `ruff check`, and [`tests/test_privacy_guard_http.py`](file:///Users/pranay/Projects/travel_agency_agent/tests/test_privacy_guard_http.py) uses DB-requiring `session_client` even though it tests a pre-DB 422 guard.
  5. **Stale Findings in `FINDINGS_STORE.jsonl` (`S4-08`)**: Four open P3 findings are already implemented in code and can be closed with verification events (`FND-0061`, `FND-0063`, `FND-0107`, `FND-0167`), and `FND-0215` is an exact duplicate of `FND-0014`.

---

## 5. Lead Synthesis (`PER-0100`) & Sequenced Remediation Plan

### 5.1 Executive Assessment
The Sim #3 and Launch-Readiness wave delivered substantial domain modules (`claim_framework.py`, `claim_disposition.py`, `ghost_concierge.py`, `public_asks.py`, `trip_dsr.py`, `accounting_export.py`, `quotes.py`, `refresh_or_reselect`, and `TypesafeJevClient`). However, **cross-boundary integration and security invariants broke at the seams**:
1. **Security & Privacy Gates (`AUD-01`, `AUD-02`, `AUD-03`, `AUD-05`, `AUD-11`, `AUD-16`)**: A single key-existence bug (`"fixture_id" in raw_input` where `fixture_id` is `None`) silently disabled Privacy Guard on 100% of `/run` requests; `SQLTripStore` leaves `analytics._extra` and `customer_contact` unencrypted; GDPR Art. 17 erasure writes literal `"packet.customer_name"` keys without scrubbing nested dicts or auxiliary stores; and `TypesafeJevClient` sends unredacted traveler notes to an external API from the live serving spine.
2. **Persistence & Async Loop Safety (`AUD-08`, `AUD-09`, `AUD-14`)**: Seven SQL stores still share the main FastAPI `AsyncEngine` inside `_SYNC_ASYNC_BRIDGE` (`FND-0321`), `save_processed_trip` wipes `analytics._extra` and booking columns on every reprocess, and `TripResponse.from_dict()` strips 8 operational fields (`reassess`, `decision`, `updated_at`, `flight_status_updates`, etc.).
3. **End-to-End Workflow Completion (`AUD-06`, `AUD-07`, `AUD-10`, `AUD-12`, `AUD-13`, `AUD-17`)**: `T1` (`/a/[token]`), Live Jev Message Triage (`/api/triage/message`), and Disruption Claim Disposition have backend endpoints and frontend views that are disconnected in `route-map.ts` or lack pipeline readers.

### 5.2 Sequenced Remediation Waves (Recommended Execution Order)

#### Wave 1 — Release Safety, Privacy Guard, Encryption at Rest, & GDPR Erasure (P0 Blockers: `AUD-01`..`AUD-04`, `AUD-05`, `AUD-16`)
1. **Gate `.github/workflows/deploy.yml` (`AUD-04`)**: Disable automatic `master` push deploy until `Docs/LAUNCH_STATUS.md` is `GO`.
2. **Fix Privacy Guard Fixture Bypass & Door Consistency (`AUD-01`)**: Fix `_is_known_fixture()` in `src/security/privacy_guard.py:212-213` (`bool(raw_input.get("fixture_id"))` matching known fixture prefixes), and unify Layer 1/Layer 2 behavior across `/run` and `/inbound/parse`.
3. **Complete `SQLTripStore` Encryption at Rest (`AUD-02`)**: Expand `_PII_FIELDS`, encrypt/decrypt `analytics_with_extra`, and configure `ENCRYPTION_KEY` in local/staging environments.
4. **Fix GDPR Art. 17 Erasure (`AUD-03`) & Audit Redaction (`AUD-16`)**: Mutate nested `packet`, `extracted`, `traveler_bundle`, `internal_bundle`, `booking_data`, `traveler_asks`, `traveler_answers`, `passenger_claim`, `DraftStore`, `CustomerMemoryProfile`, and lock-safe `message_store.py` JSONL tombstoning; require `GDPR_SIGNING_KEY` from env and redact PII before `log_audit_event`.
5. **Enforce `llm_egress` on `TypesafeJevClient` (`AUD-05`)**: Redact PII (`redact_pii` + `add_prompt_delimiters`), remove `.env` `os.environ.setdefault` side effects, and fix `decision_schema` key/confidence bugs (`AUD-18`).

#### Wave 2 — Async Loop Unification, Non-Destructive Reprocess, & Contract Parity (P1 State Blockers: `AUD-08`, `AUD-09`, `AUD-11`, `AUD-14`, `AUD-15`)
1. **Unify Loop-Keyed SQL Sessions (`AUD-08` / `FND-0321`)**: Route `get_rls_session()`, `event_service.py`, and all 7 SQL stores through loop-keyed `tripstore_session_maker()`, and add the missing `await` in `SQLRunCheckpointStore.list_metas()` (`run_ledger_sql.py:300`).
2. **Make `save_processed_trip` / `save_trip` Non-Destructive (`AUD-09`)**: Preserve existing `analytics._extra` keys and booking/assignment columns across reprocessing.
3. **Complete `TripResponse.from_dict()` Parity (`AUD-14`)**: Add `reassess`, `decision`, `updated_at`, `flight_status_updates`, `traveler_asks`, `booking_data`, `analytics`, and `fees` to `TripResponse`.
4. **Fix Public Proposal RLS & Token Scope Separation (`AUD-11`)**: Use `update_trip_for_agency` / `token_agency_id` in `public_proposals.py:829, 990` and add cryptographic `purpose` claims (`"ask"` vs `"proposal"`).
5. **Wire Operator Override Cache Key (`AUD-15` / `TRV-N03`)**: Derive `cache_key` in `legacy_ops.py:667`.

#### Wave 3 — End-to-End Workflow Wiring, Statutory Claim Accuracy, & Gate Alignment (P1/P2 Product Blockers: `AUD-06`, `AUD-07`, `AUD-10`, `AUD-12`, `AUD-13`, `AUD-17`..`AUD-20`)
1. **Wire `T1` Ask-Traveler E2E Loop (`AUD-06`)**: Map `/followups/{trip_id}/send` and `/followups/dashboard` in `route-map.ts`, wire the "Send Ask Link" button in `IntakePanel.tsx`, and consume `traveler_answers` into `reassess_trip`.
2. **Wire Live Message Triage BFF Route & Schema (`AUD-07`)**: Add `/api/triage/message` to `route-map.ts` and align `MessageTriageResponse`.
3. **Fix Destination Override Precedence & Reassess Field Clearing (`AUD-10` / `FND-0309`)**: Honor cleared fields in `trip_lifecycle_service.py` and structured destination overrides in `extractors.py`.
4. **Fix Statutory Claims & Strip Unmasked VCC Generation (`AUD-12`, `AUD-17`)**: Fix `distance_km`, `_currency`, `UK261` Rule 6, and `_country_text_hint`; remove unapproved `issue_supplier_vcc()` from `irops_healer.py`; unlock `PlanningStageGate` for active disruption claims (`FND-0317`); and wire disposition actions in `ClaimDispositionCard.tsx`.
5. **Unify `PlanningStageGate` with Backend `blocking_unknowns()` (`AUD-13` / `U11`)** and clean up `ruff` (`tests/test_message_store_and_feed.py:8`), XML escaping (`export_bridge.py`), `specs/canonical_packet.schema.json`, and stale `FINDINGS_STORE.jsonl` entries (`AUD-19`, `AUD-20`).
