# Post-Council Audit: Comprehensive Findings, First-Principles Review & Implementation Plan (2026-10-21)

- **Audit Date**: `2026-10-21`
- **Orchestrating Council**: Lead `PER-0100 Launch Readiness Director` + Specialists (`PER-0442`, `PER-0443`, `PER-0362`, `PER-1098`, `PER-0468`)
- **Status**: Formulated, Reviewed from First Principles, and Actively Executing
- **Doctrines Applied**:
  - `OPERATING_DOCTRINE.md` (v8.2)
  - `RELEASE_READINESS_DOCTRINE.md` (v1.0)
  - `ARCHITECTURE_DOCTRINE.md` (v1.1)
  - `SECURITY_PRIVACY_SAFETY_DOCTRINE.md` (v1.0)
  - `TESTING_DOCTRINE.md` (v1.0)

---

## 1. Comprehensive Findings Inventory (Explicit, Implicit, Identified & Inferred)

This inventory encompasses all findings identified directly during the Launch Readiness Council, inferred from codebase inspection, derived from runtime test behaviors, and extracted from the historical findings ledger:

### 1.1 Category A: Ledger Integrity, Traceability & State Invariants
- **`FND-AUD-01` [Explicit] Finding Ledger Monotonicity Break (`FINDINGS_STORE.jsonl`)**:
  - *Evidence*: `python3 scripts/findings.py validate` fails on events 623, 624, 625 (`unknown finding_id 'FND-0323'..'FND-0325'`).
  - *Cause*: `audit-council-wave` appended `finding.closed` events for `FND-0323` (TRV-N03 cache key), `FND-0324` (AUD-07 triage route), and `FND-0325` (AUD-06 ask loop) without recording their preceding `finding.opened` events.
  - *Impact*: CI gate exits non-zero; findings store fails validation.
- **`FND-AUD-02` [Explicit] Findings Staleness (>45 Days Threshold)**:
  - *Evidence*: 15 open P3 findings have verification timestamps older than 45 days (`FND-0014`, `FND-0061`, `FND-0063`, `FND-0083`, `FND-0107`, `FND-0161`, `FND-0164`, `FND-0165`, `FND-0167`, `FND-0168`, `FND-0215`, `FND-0234`, `FND-0235`, `FND-0236`, `FND-0237`).
  - *Cause*: Development focused intensely on P0/P1 remediation waves (Sim #3, T1..T15) without running routine re-verification sweeps on legacy P3 backlog items.
  - *Impact*: CI gate enforcement fails closed; backlog hygiene is blocked.
- **`FND-AUD-03` [Identified] In-Code TODO Markers vs Findings Store Linkage (`TRV-N02` / `TRV-N03`)**:
  - *Evidence*: 15 in-code TODO markers across `spine_api/` and `src/`. `legacy_ops.py:667` was resolved, but other tags (`frontier.py:36`, `ivr_gateway.py:266`, `metrics_registry.py:97`) require formal alignment to open findings rows.

### 1.2 Category B: Security, Privacy & Fail-Closed Guard Hardening
- **`FND-AUD-04` [Inferred] Encryption Fallback Dev Key Exposure in Production**:
  - *Evidence*: [`src/security/encryption.py:20-30`](file:///Users/pranay/Projects/travel_agency_agent/src/security/encryption.py#L20-L30) checks `if os.getenv("DATA_PRIVACY_MODE") == "production"` before raising ValueError. If an operator sets `ENVIRONMENT=production` or `NODE_ENV=production` but omits `DATA_PRIVACY_MODE`, it logs a warning and uses a static hard-coded dev key (`v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8=`).
  - *Impact*: High security risk; PII in production PostgreSQL could be encrypted with a known public key if environment variables are inconsistently named.
- **`FND-AUD-05` [Identified] TripStore Backend Validation Allows File Storage in Production**:
  - *Evidence*: [`spine_api/server.py:199-221`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py#L199-L221) raises an error if `TRIPSTORE_BACKEND` is unset in production, but if an operator explicitly sets `TRIPSTORE_BACKEND=file`, it boots into `FileTripStore`.
  - *Impact*: Multiple horizontal container instances running with `FileTripStore` experience split-brain state, lost updates, and zero cross-instance durability.
- **`FND-AUD-06` [Inferred] Token Capability Parity & Fallback TTL**:
  - *Evidence*: Public proposals use signed tokens (`/p/[token]`) with explicit expiration, revocation, and tenant isolation via `proposal_token_store.py`. Ask links (`/a/[token]`) reuse the same signed token machinery, but must have identical TTL, revocation checks, and tamper-resistance.

### 1.3 Category C: Product Workflows, Ask-Traveler & Operator Parity
- **`FND-AUD-07` [Identified] Ask-Traveler Human-Readable Question Fallback**:
  - *Evidence*: In [`spine_api/routers/public_asks.py:54-72`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/public_asks.py#L54-L72), `_open_questions()` extracts questions from `decision.follow_up_questions`. If a question dictionary lacks a populated `"question"` or `"text"` key, it can render empty or fallback to `"general"`.
  - *Impact*: Traveler sees a blank or machine-vocabulary card on `/a/[token]`.
- **`FND-AUD-08` [Inferred] Autonomous Ask Loop Reassessment Race & Error Isolation**:
  - *Evidence*: In `public_asks.py:208-225`, posting traveler answers immediately triggers `queue_trip_reassessment()` inside a `try/except Exception` block. While safe from crashing the HTTP response, the reassessment failure status should be logged to the audit ledger so the operator knows if an automated re-run failed.
- **`FND-AUD-09` [Identified] Attachment & Multimedia Ingestion UI (`T6` / `FND-0305`)**:
  - *Evidence*: WhatsApp and omnichannel webhooks ingest audio notes and image attachments into `message_store.py`. `ChannelMessagesPanel.tsx` renders metadata, timestamp, and text, but lacks inline audio playback and visual image rendering.
- **`FND-AUD-10` [Identified] Decision Dossier Provenance Substrate (`FND-0236`)**:
  - *Evidence*: Decision provenance is mounted in `DecisionPanel.tsx`, but does not yet export an immutable, hashed cryptographic evidence bundle for regulatory or compliance audit replay.

### 1.4 Category D: CI/CD, Build & Test Hermeticity
- **`FND-AUD-11` [Explicit] Uncontrolled CD Auto-Deployment on Master Push (`TRV-N05`)**:
  - *Evidence*: `.github/workflows/deploy.yml` triggers on `workflow_run` (CI completion) on `master` and `main`. While a check for `Docs/LAUNCH_STATUS.md` exists, running CD on every push creates noisy failure logs and risks accidental deployments.
- **`FND-AUD-12` [Explicit] Vitest Test Sandbox TCP Port Binding Failure**:
  - *Evidence*: `api-client.auth.test.ts` and `api-client-auth-refresh.test.ts` fail with `TypeError: fetch failed (connect EPERM 127.0.0.1:57575)` inside Standard Sandbox Mode because they spin up live Node.js `http.createServer()` sockets.
  - *Impact*: Blocks clean zero-warning test execution in sandboxed development environments.
- **`FND-AUD-13` [Identified] PostgreSQL Integration Tests Sandbox Isolation**:
  - *Evidence*: `tests/test_refresh_after_commit.py` attempts to connect to `::1:5432` and fails with `PermissionError: [Errno 1] Operation not permitted` inside the sandbox.

### 1.5 Category E: Operational, Financial & External Provider Readiness
- **`FND-AUD-14` [Identified] Accounting Export Durability (`E08` / `T13`)**:
  - *Evidence*: `spine_api/routers/accounting_export.py` derives TCS/GST and commercial invoices dynamically on read. For enterprise compliance, generated commercial invoices should be snapshot-persisted to prevent retroactive drift if tax rates change.
- **`FND-AUD-15` [Explicit] Zero Live Provider Integrations (`B6/B7` Blocker)**:
  - *Evidence*: Amadeus, Sabre, and Hotelbeds GDS feeds remain simulated or un-credentialed. Live flight pricing and booking cannot be executed in production.
- **`FND-AUD-16` [Identified] Disaster Recovery & Backup Drill Receipt**:
  - *Evidence*: While SQL migrations exist in `alembic/`, there is no documented and tested PostgreSQL snapshot/restore drill receipt in `Docs/`.

---

## 2. First-Principles & Architectural Soundness Review

| Finding | Current/Proposed Approach | First-Principles & Architectural Evaluation | Better / Generalized Long-Term Solution |
| :--- | :--- | :--- | :--- |
| **`FND-AUD-01` (Ledger Monotonicity)** | Insert missing `finding.opened` events for `FND-0323..0325` before their close events. | **Correct & Minimal**: The event store is append-only and monotonic. Mending the event sequence at event 623 restores mathematical consistency without rewriting history. | Execute monotonic event insertion; verify with `scripts/findings.py validate`. |
| **`FND-AUD-02` (Stale P3 Findings)** | Re-verify each finding against current code reality or close if already resolved. | **Doctrine-Aligned**: Doctrine states: "Treat current files and runtime as ground truth." Findings older than 45 days must either be verified as still an open backlog item with fresh evidence, or closed with a closure receipt. | Run a comprehensive verification sweep across all 15 findings; update timestamps with concrete file:line receipts. |
| **`FND-AUD-04` (Encryption Key Guard)** | Check only `DATA_PRIVACY_MODE == "production"`. | **Flawed / Incomplete**: Real-world operations commonly use `ENVIRONMENT=production` or `NODE_ENV=production`. Relying on a custom env var (`DATA_PRIVACY_MODE`) risks silent fallback to the insecure dev key. | **Unify Environment Checking**: Fail-close if *any* of `ENVIRONMENT`, `NODE_ENV`, or `DATA_PRIVACY_MODE` is `"production"` or `"staging"`. Never allow fallback keys in non-local environments. |
| **`FND-AUD-05` (TripStore in Production)** | Fail if `TRIPSTORE_BACKEND` is empty in production. | **Fragile**: Allows an operator to accidentally set `TRIPSTORE_BACKEND=file` in production, which leads to split-brain data corruption across multi-container Fly/Render deployments. | **Enforce SQL in Production**: In production/staging, `TRIPSTORE_BACKEND` *must* be `"sql"` and `DATABASE_URL` *must* be valid. Explicitly forbid `file` backend in production. |
| **`FND-AUD-07` (Ask Loop Questions)** | `_open_questions()` passes whatever raw text is in `follow_up_questions`. | **Suboptimal**: If decision logic emitted a field without generating human prose, the traveler sees `[High] origin_city`. | **Deterministic Human-Question Fallback**: If question text is empty or matches raw field name, resolve through `src/intake/decision.py:generate_question(field_name)` before serving to the traveler. |
| **`FND-AUD-11` (CD Auto-Deploy)** | `workflow_run` on master runs deploy job, which fails on grep. | **Anti-Pattern**: Fails the master CI build pipeline on every commit, generating false-positive incident alarms. | **Explicit Gate**: Limit automatic CD to release tags (e.g. `v*.*.*`) or manual `workflow_dispatch`. Remove `workflow_run` from `master` branch pushes until public launch is authorized. |
| **`FND-AUD-12` (Vitest TCP Sockets)** | Tests use `http.createServer()` on `127.0.0.1`. | **Over-Engineered / Brittle**: Testing whether `ApiClient` sends an HTTP header does not require an actual operating system network socket. In sandboxed CI and secure agent environments, socket binding fails. | **Hermetic Fetch Mocking**: Mock `globalThis.fetch` in `api-client.auth.test.ts` to inspect requested URL, headers, and body options. Eliminates network dependencies while asserting 100% identical client transport behavior. |

---

## 3. Sequenced Implementation Plan

### Phase 1: Ledger Integrity & Hygiene (Immediate)
1. **Fix `FINDINGS_STORE.jsonl`**:
   - Insert `finding.opened` events for `FND-0323` (P1 legacy cache key), `FND-0324` (P1 triage route), and `FND-0325` (P1 ask loop).
   - Ensure strictly monotonic `event_id` progression (`623`..`628`).
2. **Re-verify / Reconcile 15 Stale P3 Findings**:
   - Re-verify each of `FND-0014`, `FND-0061`, `FND-0063`, `FND-0083`, `FND-0107`, `FND-0161`, `FND-0164`, `FND-0165`, `FND-0167`, `FND-0168`, `FND-0215`, `FND-0234`, `FND-0235`, `FND-0236`, `FND-0237`, `FND-0293` with updated evidence.
   - Run `python3 scripts/findings.py validate` to achieve **PASS (0 errors)**.

### Phase 2: Security & Fail-Closed Guard Hardening
1. **Harden `src/security/encryption.py`**:
   - Fail-close if `ENCRYPTION_KEY` is missing and `ENVIRONMENT` or `NODE_ENV` or `DATA_PRIVACY_MODE` is `"production"` or `"staging"`.
2. **Harden `spine_api/server.py`**:
   - Forbid `TRIPSTORE_BACKEND=file` when running in `production` or `staging`. Require `DATABASE_URL`.
   - Add test pins in `tests/test_startup_assertions.py` or `tests/test_privacy_guard.py`.

### Phase 3: Test Hermeticity & Frontend CI Suite
1. **Hermetically Mock `api-client.auth.test.ts` and `api-client-auth-refresh.test.ts`**:
   - Refactor tests to mock `fetch` rather than binding live TCP sockets on `127.0.0.1`.
   - Verify `cd frontend && npm test -- --run` achieves **100% pass across all 189 test files**.

### Phase 4: Ask-Traveler Quality & CI/CD Safety
1. **Harden `public_asks.py`**:
   - Fallback to `generate_question(field_name)` when question text is missing or blank.
   - Add audit logging on background reassessment exceptions.
2. **Harden `.github/workflows/deploy.yml`**:
   - Remove automatic master deployment trigger, making CD strictly manual (`workflow_dispatch`) or tag-based (`v*`).

### Phase 5: Verification & Full Regression Pass
1. Run `ruff check`, `tsc --noEmit`, backend pytest suites, frontend vitest suite, and `findings.py validate`.
2. Document all results and update `Docs/EXPLORATION_TOPICS.md` and `Docs/INDEX.md`.
