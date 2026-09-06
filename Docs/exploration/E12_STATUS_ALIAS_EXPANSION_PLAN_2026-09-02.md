# E-12: Status Alias Expansion Plan — Evidence-First Growth + Telemetry

**Series date:** 2026-09-02 · **Written:** 2026-09-04 (environment date verified)
**Status:** Exploration — read-only research, no code changed. This document creates exactly one file.
**Feeds:** E-1 (`Docs/exploration/E1_TYPED_ENUM_STATUS_ENFORCEMENT_EXPLORATION_2026-09-02.md`) — this is E-1's data-collection substrate for the status axis specifically
**Claim marking:** **[V]** = verified (file:line or live read-only query run today); **[V-per-E1]** = verified in the E-1 exploration (2026-09-04 live SQL); **[I]** = inferred from verified evidence

---

## 1. The Question

`spine_api/core/trip_status.py:80` emits `logger.warning("Unclassified trip status %r passed through unnormalized", value)` on every unknown status token. Three questions decide whether that warning can actually grow the alias table:

1. **Is it queryable?** Where do these logs go — stdout? a file? any aggregator?
2. **What statuses ACTUALLY exist in persisted data?** There is no standing table of that; only one-shot explorations.
3. **What is the minimal instrumentation** that turns warned-unknowns and persisted distributions into alias-table growth *with provenance*, instead of whiteboard guesses?

**Headline finding [V]:** the warning is currently *unqueryable and unreachable at the same time* — it goes to bare stderr with no aggregation anywhere in the stack, **and** `normalize_trip_status` has zero callers (re-verified 2026-09-04, rg across `spine_api/` + `src/`, non-test), so no real write path can ever fire it. The telemetry exists as code but not as signal. Fixing reachability is E-1 §7-1; this doc covers what to build *around* it so the signal is collectable, queryable, and actionable.

---

## 2. Seed Alias Table — Every Known Status Literal + Writer Provenance

This is the seed the alias map grows from. Six (really eight) status vocabularies live in the backend; only §2.1 belongs in `_STATUS_ALIASES`. §2.2 exists so growth never absorbs a foreign vocabulary by mistake (the routing-token trap).

### 2.1 Axis 1: `Trip.status` — every literal with a live writer **[V unless noted]**

| Literal | Writer (file:line) | Semantics | Current alias-map entry? |
|---|---|---|---|
| `new` | `spine_api/routers/inbound.py:175` (POST /inbound, no missing fields); `spine_api/services/pipeline_execution_service.py:529` (full packet save, default); `spine_api/routers/inbound.py:350` (sync promotion); insert defaults `spine_api/persistence.py:930` (file store), `spine_api/models/trips.py:39` (ORM column); seed passthrough default `spine_api/server.py:1542,1645` | Intake registered | yes (`"new": "new"`) |
| `active` | `spine_api/routers/inbound.py:175` (POST /inbound, missing fields present) | Intake complete, unassigned | yes (`"active": "active"`) — but see fall-through bug |
| `incomplete` | `spine_api/services/pipeline_execution_service.py:373` (ESCALATE early-exit), `:453` (partial reprocess) | Packet not trustworthy; NB01-blocked | **no — warned as unknown if ever routed through normalize** |
| `needs_followup` | `src/agents/runtime.py:878` (FollowUp overdue agent) | Agent flagged follow-up due | no |
| `needs_clarification` | **no writer**; read-only in `src/agents/runtime.py:647` eligible set **[V-per-E1]** | Intake blocked, awaiting customer | no |
| `awaiting_customer_details` | **no writer**; same eligible set `runtime.py:647` **[V-per-E1]** | Intake blocked | no |
| `escalated` | **no trip-status writer**; `runtime.py:928` writes `review_status: "escalated"` (different field) | Routing/review vocabulary bleeding candidate | no |
| `assigned` | `spine_api/routers/legacy_ops.py:229,754`; `spine_api/routers/inbox.py:227` | Owned by an operator | **no** |
| `in_progress` | Operator PATCH only (no code writer) **[V-per-E1, §2.4: 853 SQL rows]** | Work started | yes (`"in_progress": "in_progress"`; legacy `inprogress` absorbed) |
| `archived` | `spine_api/routers/inbox.py:231` | Bulk archive | **no** |
| `completed` | Operator PATCH via ready-gate (`spine_api/server.py:2144-2163` gate, `:2489` write) **[V-per-E1]** | Done | no |
| `cancelled` | Operator PATCH only **[V-per-E1]** | Dead | no |
| *(any operator string)* | `PATCH /trips/{id}` — `TripPatchRequest.status: Optional[str]`, `spine_api/contract.py:1029-1030`, applied `server.py:2489`; only the transition invariant + completed ready-gate constrain it | **Freeform hole: the writer that can produce arbitrary unknowns** | n/a (this is the growth surface) |
| *(missing key)* | Legacy direct file-store writes | 138 rows in `data/trips/` **[V — rescan today]** | `""→new` covers empty string, not absent key |

**Frontend read-model vocabulary for the same axis** `frontend/src/lib/bff-trip-adapters.ts:10-25` **[V]** — 12 keys: `new, incomplete, needs_followup, awaiting_customer_details, snoozed, assigned, in_progress, ready_to_quote, ready_to_book, blocked, completed, cancelled`. Workspace partition `:59-65` = `{assigned, in_progress, ready_to_quote, ready_to_book, blocked}` (also `frontend/src/lib/trip-domain.ts:1-7` **[V]**); inbox partition `:67-73`. Only frontend writer: `IntakePanel.tsx:853` sends `{status: "completed"}` **[V-per-E1]**. `snoozed` and `blocked` have **no backend writer** — frontend-only inventions; `active` and `archived` fall through `STATUS_TO_STATE` to `undefined` (live bug class, E-1 §2.5-1).

**Observed persisted distribution** (E-1 §2.4, live RLS-scoped SQL 2026-09-04 **[V-per-E1]**; file store re-verified today **[V]**):

| status | SQL n | file n | in alias map? | frontend-mapped? |
|---|---:|---:|---|---|
| assigned | 18,527 | 495 | no | yes |
| new | 1,752 | 304 | yes | yes |
| in_progress | 853 | 0 | yes | yes |
| incomplete | 132 | 21 | no | yes |
| active | 76 | 978 | yes | **no (undefined state)** |
| completed | 13 | 0 | no | yes |
| cancelled | 2 | 0 | no | yes |
| archived | 0 | 0 | no | **no** |
| *(missing key)* | — | 138 | partially | — |

Zero case variants in SQL (`count(DISTINCT lower(status))` = 1 per norm **[V-per-E1]**); case-folding fear is theoretical in the store. Counts drift between sessions (`Docs/KNOWN_TEST_DATA_ACCUMULATION.md` **[V]**) — which is exactly why §4 makes the distribution query a standing tool rather than a one-off exploration.

### 2.2 Axis 2+: adjacent vocabularies that must NOT enter `_STATUS_ALIASES` **[V unless noted]**

These are the false-positive traps for alias growth. The `escalated`/`assigned` collision across axes is why triage (§5) checks *which field* a token came from.

| Vocabulary | Values | Where | Field |
|---|---|---|---|
| Routing state | `unassigned, assigned, escalated, returned` | `spine_api/services/routing_service.py` (create default `"unassigned"` verified at ~:49; full set per E-1 §2.3 **[V-per-E1]**) | `TripRoutingState.status` — separate column |
| Follow-up | `pending, completed, snoozed` (+ runtime sets `due` at `runtime.py:846` **[I]**) | `spine_api/routers/followups.py:46`; `src/agents/runtime.py:846,878` | `follow_up_status` |
| Review status | `unreviewed` (kdd clustering `src/analytics/kdd/clustering.py:118`), `escalated` (`runtime.py:928`) **[I — sampling, full set not enumerated]** | agent/analytics writes | `review_status` metadata |
| Agent terminal sets | `{closed, cancelled, completed, archived, lost, booked}` — 7 divergent copies | `src/agents/runtime.py:769,852,983,1189,1391,2324,2482`; `src/agents/communicator_agent.py:52` **[V-per-E1]** | read-side eligibility |
| Agent draft routing | `quoted`, `proposal` | `runtime.py:832-840` **[V-per-E1]** | draft state, not lifecycle |
| Metrics revenue | `booked, delivered, completed` | `src/analytics/metrics.py:51,191,315` **[V-per-E1]** | read-side; `booked` has no writer (metric structurally zero) |
| Deal Literal (quote domain) | `OPEN, NEGOTIATING, WON, LOST` (UPPERCASE) | `spine_api/contract.py:56` | `Deal.status` |
| Agency/config Literal | `draft, active, paused, archived` | `spine_api/contract.py:818,836,849` | agency/pipeline config |
| Checker verdict | `pass, warn, fail` | `spine_api/contract.py:868` | validation result |
| SLA | `on_track, at_risk, breached` | `spine_api/contract.py:1273` | `slaStatus` |
| Response default | `IN_PROGRESS` (UPPERCASE, matches nothing) | `spine_api/contract.py:1451` **[V-per-E1]** | `ConciergeMonitorResponse.trip_status` — response-model only, candidate alias `→in_progress` |

**Current `_STATUS_ALIASES` coverage** (`trip_status.py:46-52` **[V]**): exactly 5 entries — `""→new`, `in_progress→in_progress`, `inprogress→in_progress`, `new→new`, `active→active`. Of the 13 known literals with a writer (§2.1), **8 are absent** — including three the live data contains (`assigned`, `incomplete`, plus the pass-through cases). The map was seeded from *code-shape intuition*, not from the distribution. That is the gap this plan closes.

---

## 3. Telemetry Today — What Actually Exists (Honest Audit)

### 3.1 The warning itself **[V]**

- Emitter: stdlib `logging`, logger name `spine_api.core.trip_status` (`trip_status.py:32`), level WARNING, plain-text single line, `%r`-formatted raw value.
- **Reachability: zero.** `normalize_trip_status` has no callers (rg re-verified 2026-09-04). Store paths (`persistence.py`) do NOT call it. The warning cannot fire on any current write path; unknowns reach the store raw via the freeform PATCH hole and file-store passthrough.

### 3.2 Where logs go **[V — full inventory below]**

| Layer | What exists | What it means for the warning |
|---|---|---|
| App config | Only `logging.basicConfig(level=INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")` inside `if __name__ == "__main__"` (`spine_api/server.py:3355-3359`). No `dictConfig`, no structured `Formatter`, no `FileHandler`/`RotatingFileHandler` anywhere in `spine_api/` or `src/` (rg verified; hits were migration/tool scripts only) | Root logger → **stderr**. Not structured, not timestamped consistently, not persisted by the app itself |
| Durable local capture | `tools/dev_server_manager.py:43,98-102` redirects backend stdout+stderr to `.runtime/local/backend.log` | **The only queryable surface today**: `rg "Unclassified trip status" .runtime/local/backend.log` — and only when servers were started via the manager; log is ephemeral per worktree, unrotated |
| Log aggregation / Loki / file shipping | None. `rg -l "loki\|tempo\|grafana\|collector"` over `docker-compose.yml` + deploy dirs: zero matches. The compose stack is exactly 4 services (spine_api, frontend, redis, postgres) **[V]** | No aggregation exists in-stack |
| OpenTelemetry | **Traces only.** Backend: `FastAPIInstrumentor` + OTLP-gRPC `BatchSpanProcessor`, gated on `SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT` / `OTEL_EXPORTER_OTLP_ENDPOINT` (`server.py:73-78, 93-105`); pipeline/intake spans (`pipeline_execution_service.py:289`, `src/intake/orchestration.py:253-292`). Frontend: `frontend/instrumentation.ts` (OTLP-HTTP, same gating). **No `LoggingHandler` / `set_logger_provider` anywhere [V]** — logs are not exported to OTel even when traces are | Warning stays on stderr regardless of OTel state |
| Endpoint config reality | Local `.env` sets neither OTEL endpoint var (grep verified) → **OTel export dormant locally**. docker-compose.yml sets no OTEL env either → **dormant in the canonical compose topology** **[V]** | Traces exist as capability, not as running telemetry |
| Metrics | `GET /metrics` (`server.py:2002-2003`) returns static JSON `{"status":"ok",...}` — **a stub, not Prometheus format**; no `prometheus-client` dependency in `pyproject.toml` **[V]** | No counter for unknown statuses can land here today |

**Verdict [I, from verified pieces]:** today the warning is stdout/stderr-only, queryable solely by grepping `.runtime/local/backend.log` after a dev_server_manager session, and unreachable in practice. "Querying unknown-status telemetry" currently means *re-running a SQL exploration by hand* — which is what §4 fixes first, because the store itself is the best telemetry that already exists.

### 3.3 The telemetry that already works: the stores **[V]**

`Docs/KNOWN_TEST_DATA_ACCUMULATION.md` ships an inline read-only diagnostic: `tripstore_session_maker()` + `select(Trip.status, func.count()).group_by(Trip.status)` — parameterized, RLS-scoped, zero writes. The file store is a plain JSON glob scan. A read-only rescan today reproduced E-1's file-store numbers exactly (`active: 978, assigned: 495, new: 304, incomplete: 21, missing-key: 138`). The distribution is already collectable; it just isn't *standing*.

---

## 4. Minimal Collection Design — `tools/status_vocabulary_report.py`

One reusable tool (per repo convention: `tools/` + `tools/README.md` entry; not a throwaway). It closes the "no table of what actually exists" gap with zero new dependencies.

### 4.1 Spec

- **Name:** `tools/status_vocabulary_report.py` (read-only; pure stdout by default)
- **Inputs:**
  - `--backend {sql,file,both}` (default `both`)
  - `--agency-id UUID` (default: `PUBLIC_CHECKER_AGENCY_ID` from env, else the known test agency; validated as UUID — never interpolated into SQL)
  - `--source-dir PATH` (default `data/trips/`)
  - `--format {table,json}` (json for diffing between runs)
  - `--out PATH` (opt-in; writes a timestamped snapshot only when explicitly requested — default writes nothing to the repo)
- **SQL path:** reuse `spine_api.persistence.tripstore_session_maker` + `Trip` model, mirroring the KNOWN_TEST_DATA_ACCUMULATION snippet: `select(Trip.status, func.count()).where(Trip.agency_id == :agency_id).group_by(Trip.status)` — **const/parameterized, read-only session, no commit, no `TRUNCATE`/`DELETE` anywhere** (data-safety rule, AGENTS.md 2026-05-03). Additionally: `count(DISTINCT lower(status))` per norm (case-variant detector) and count of rows with non-empty `status_history`.
- **File path:** `json.load` each `data/trips/*.json`, read top-level `trip.status`; report per-literal counts, missing-key count, case variants. Never writes to `data/trips/`.
- **Output (the value-add):** each observed literal annotated with coverage columns —
  `in _STATUS_ALIASES?` · `has backend writer?` (§2.1 table, embedded as module constants) · `frontend-mapped?` (12-key set) · `verdict ∈ {canonical-covered, known-gap, UNKNOWN → growth queue}`.
  The `UNKNOWN` rows are the alias-growth queue; `known-gap` rows are pre-decided aliases awaiting the enum slice.
- **Exit semantics:** exit 0 always on success; `--format json` prints stable key order for mechanical diffing.

### 4.2 Cadence and consumption

- Run manually after test waves, before any enum/alias decision, and before/after every alias addition (§5 verification step). **[I]**
- Optional later: invoke from `tools/e2e_scenario_runner.py` end-of-run to get a distribution delta per scenario (it already produces per-scenario evidence bundles — same pattern). **[I]**
- Snapshot files, if requested, belong under `Docs/` (e.g. `Docs/reports/`), never `/tmp` (repo rule).

### 4.3 What this tool does NOT do

No normalization writes, no backfill, no DB mutation of any kind, no log scraping (log scraping is explicitly rejected as the primary source: local logs are ephemeral stderr; the store is durable truth — the warning log is the *early* signal, the scan is the *authoritative* signal).

---

## 5. Growth Procedure — Alias vs Fix-the-Writer (Decision Tree)

Each triaged unknown follows exactly one path. Inputs: warning log (once reachable, E-1 §7-1), §4 tool `UNKNOWN` rows, frontend `state: undefined` fall-throughs, `trip_status_changed` audit rows (`server.py:2493-2497`, currently operator-PATCH-only **[V]**).

```text
Unknown token T observed (with value, writer/store, count)
│
├─ Q1. Is T written by OUR code on a live path?
│   ├─ YES → FIX THE WRITER at source (preferred): emit the canonical
│   │        literal / enum member in the writer; add a regression test.
│   │        Do NOT alias away a bug in our own writer.
│   │        (e.g. today: inbound "active" vs frontend unmapped — writer-side
│   │        or map-side fix, not an alias.)
│   │
│   └─ NO (data artifact, seed, import, historical rows, operator habit)
│       ├─ Q2. Does T belong to a DIFFERENT vocabulary (§2.2) that leaked
│       │   into trip.status (e.g. routing "escalated", deal "WON")?
│       │   ├─ YES → REJECT: do not absorb. Fix the leaking writer
│       │   │        (cross-axis write bug); log the rejection in this doc.
│       │   └─ NO → Q3.
│       │
│       └─ Q3. Is T a stable variant (case/spacing/spelling) of a canonical
│           value, or a semantically distinct new state?
│           ├─ VARIANT → ADD ALIAS with provenance comment:
│           │     "<token>": "<canonical>",  # provenance: <writer/source>,
│           │     # <file:line or origin>, <date>, <n rows observed>
│           │   + unit test in trip_status tests + before/after §4 run.
│           └─ NEW STATE → it's not an alias problem: propose it as an enum
│               member in E-1 §4/§8 (decision), add writer + frontend map
│               entry + partition decision together.
```

**Invariants for every alias addition** (per repo doctrine):

1. **Additive-first:** unknowns keep passing through with the warning; an alias only *reduces* warnings, never rejects (E-1 Stage-0/2 boundary owns rejection).
2. **Provenance comment mandatory** — an alias without evidence gets deleted at the next review.
3. **Both stores, one map:** alias lives only in `spine_api/core/trip_status.py` (canonical module; no parallel tables in `persistence.py` or frontend).
4. **Verify:** §4 tool run before/after must show the token leaving the UNKNOWN queue; module tests green.
5. **Feedback to E-1:** when the UNKNOWN queue is empty over a soak window and all remaining tokens are `known-gap`/absorbed aliases, E-1's Stage 2 (strict boundary) is safe to flip (E-1 §3 decision rule).

---

## 6. Relationship to E-1

This document is **E-1's data-collection substrate for the status axis**, not a competing plan:

- E-1 §3 ("Data-Collection Plan") listed the instruments; E-12 specifies the *procedure and tooling* that make those instruments produce alias growth continuously, plus the honest telemetry audit (§3) E-1 assumed.
- E-1's Stage 0 ("Instrument — zero behavior change") is implemented by E-12 §6 tasks 1-3; the enum cut (E-1 §8 Decision 1) stays gated on Stage-0 evidence that this plan's tooling generates.
- E-1 owns the vocabulary *decision*; E-12 owns the *evidence loop* (collect → triage → alias-or-fix → re-collect). The alias table in E-1 §4.2 and the seed table here (§2.1) must stay in sync — this doc is the working copy with per-token provenance; E-1 §4.2 is the decision-level distillation.
- E-12 generalizes: the same collect/triage/absorb loop applies to the other axis vocabularies (§2.2) when they get typed enums later, with the cross-axis rejection rule preventing vocabulary bleed.

---

## 7. Sized Next Tasks

| # | Task | Size | Gate / dependency |
|---|---|---|---|
| 1 | **`tools/status_vocabulary_report.py`** per §4 spec + `tools/README.md` entry | S | none — do now; zero deps, read-only |
| 2 | **Reachability:** wire `normalize_trip_status` into `FileTripStore.save_trip` and `SQLTripStore` save/update paths (E-1 §7-1) so the warning actually fires | S | none — makes all telemetry below meaningful |
| 3 | **Unknown counter:** module-level `Counter` in `trip_status.py` incremented in the unknown branch; expose via internal read endpoint (E-1 §3) | S | with #2 |
| 4 | **Audit coverage:** emit `trip_status_changed` (today operator-only, `server.py:2493`) from inbox/legacy/agent/inbound write helpers — turns writer attribution into SQL-queryable evidence, strictly better than log scraping | M | none |
| 5 | **Warning ergonomics:** keep the exact message string stable (it is the grep key), attach `extra={"trip_status_raw": value, "store": ...}` so a future structured formatter/OTel-log hop is mechanical | S | with #2; format-stability note **[I]** |
| 6 | **OTel log export + local collector** (Loki/OTLP-collector service in compose) so warnings are queryable in an aggregator, not ephemeral stderr | L | only when a deployed topology exists; dormant today, no local payoff |
| 7 | **Prometheus counter** `spine_trip_status_unknown_total{value=…}` when `/metrics` becomes real (it is a JSON stub today, `server.py:2002`) | S | piggyback on metrics work (E-1 §3 last row) |

Sequencing: 1+2 unblock everything; 3-5 are the standing loop; 6-7 are deployment-tier and correctly deferred.

---

## 8. Decision Needed

- **Decision needed:** alias-provenance comment format — the §5 convention (`# provenance: <source>, <date>, <n rows>`) vs. a `Docs/`-side ledger table? Recommendation: inline comment + this doc's §2 as the ledger (no new parallel doc system).
- **Decision needed:** should the §4 tool treat the 138 file-store missing-key rows as `""→new` (aliased) or as their own `MISSING` bucket in reports? Recommendation: own bucket — aliasing absence invisibly repeats the file-store split-brain lesson (2026-05-03).
- **Decision needed:** cadence — manual runs only, or wire the §4 report into `e2e_scenario_runner.py` end-of-run? Recommendation: manual first; wire in when scenario suites start asserting status vocabularies.
- **Decision needed:** accept "store is the authoritative signal, warning-log is the early signal" as the telemetry stance (rejecting log-aggregation-first)? Recommendation: yes — matches the dual-store reality and defers infra (task 6) until a deployed topology exists.
- **Decision needed (owner: E-1):** the pending enum-cut questions in E-1 §8 remain the upstream decisions this evidence loop serves; none can be settled by E-12 alone.

---

*Exploration only — no code, schema, config, or additional files were created or modified. All live queries were read-only (file-store JSON scan + rg inventory); SQL figures cited from E-1's 2026-09-04 RLS-scoped read. `spine_api/core/trip_status.py` is currently untracked in git (`git status` — in-flight hardening wave, HEAD `2f9a638`), so its line numbers are stable only for this wave.*

## 2026-09-05 implementation receipt — read-only distribution report

The first safe E-12 slice is implemented as
`tools/status_vocabulary_report.py`, with focused coverage in
`tests/test_status_vocabulary_report.py`. The tool imports the canonical
`_STATUS_ALIASES`, preserves raw tokens, reports missing/null/malformed file
records separately, marks known Trip-status writers and adjacent vocabulary
candidates, and never mutates the store. It returns a nonzero exit code when a
requested SQL source cannot be read instead of presenting incomplete output as
complete.

Local receipt:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_status_vocabulary_report.py
2 passed in 0.43s
PYTHONPATH=. .venv/bin/python tools/status_vocabulary_report.py --backend file
files_scanned=1936; malformed_files=0; missing_status_key=138;
explicit_null_status=0; tokens=active:978, assigned:495,
incomplete:21, new:304
```

This is file-store Tier-1/2 evidence for the current checkout only. It does
not establish production distribution, SQL multi-agency coverage, or justify
an enum/alias expansion. The next evidence step is an RLS-scoped SQL run and
writer-provenance comparison, followed by the E-1 vocabulary decision.

An additional read-only SQL invocation on 2026-09-05 returned
`groups_returned=0; rows_counted=0` both unscoped and for the configured test
agency. This is an environment/RLS observation, not a claim that the canonical
database is empty; the report now exposes those counts so an empty visibility
window cannot be confused with a zero-production-distribution result.

## 2026-09-05 repair evidence — explicit scope and trustworthy observations

**Current status for the reporting tool:** implementation and focused verification
complete; E-1 vocabulary decisions, writer reachability, consumer migration, and
the remainder of E-12 remain open. This section supersedes the preceding receipt's
writer flags and its attribution of the empty SQL result to the environment. The
original exploration and first implementation receipts are retained as history.
Date was checked with `date -Iseconds`: `2026-09-05T16:53:18+05:30` before edits.

### Objective, authority, ownership, and doctrine

The user requested full doctrine-aligned work; the delegated scope was limited to
`tools/status_vocabulary_report.py`, `tests/test_status_vocabulary_report.py`, and
this evidence section. No Git mutation, provider effect, database data mutation,
or application service start was part of this repair. Parent review owns shared
registers, README alignment, and full-worktree delivery. Unrelated changes and
all prior reports were preserved.

The engineering outcome is an observation tool that cannot quietly equate an
unavailable source with an empty source, or invented writer classification with
provenance. For users this reduces decisions based on false lifecycle counts;
for the team it makes the enum/migration evidence usable; internally it preserves
tenant isolation and failure diagnosability without leaking exception payloads.

Applied doctrine: Operating 8.0, Testing 1.1, Security/Privacy/Safety 1.0, and
Documentation 1.1, from the canonical doctrine family. Operating SHA-256 read in
this wave: `ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a`.
The context pack read was generated at `2026-09-05T10:00:34Z`; retrieval was
explicitly skipped. `systematic-debugging`, `test-driven-development`, and
`verification-before-completion` skills drove reproduction, failing-first tests,
mutation sensitivity, and evidence-bounded handoff. The TDD skill's referenced
`testing-anti-patterns.md` was absent at its stated path; its available main
instructions and Testing Doctrine were applied directly.

### Established cause and decision

**Observed source defect:** the old `scan_sql_store` opened an application DB
session and added an optional `WHERE`, but never called canonical
`spine_api/core/rls.py::apply_rls`. FORCE RLS uses the transaction's
`app.current_agency_id`; a parameterized filter does not supply that context.
The original zero-row invocation therefore did not establish a database or
environment limitation. **Verified improvement:** the corrected CLI read 21,937
rows for the explicitly named test agency, with enforced runtime RLS posture.
This live result supports missing context as the cause of the prior visibility
failure; it does not reconstruct the exact historical database state.

Selected design:

1. Require a valid explicit agency UUID for `sql` and `both`; reject before any
   database access. No fallback to a test tenant and no unscoped SQL mode.
2. Begin one transaction, set `READ ONLY` before data access, set a bounded
   transaction-local statement timeout, apply the canonical transaction-local
   RLS helper, and inspect canonical runtime posture for `trips`.
3. Refuse roles/tables that fail the canonical RLS posture check. Keep the agency
   predicate as defense in depth, then roll back on both success and failure.
   No session-level tenant state or ambient ContextVar mutation is introduced.
4. Bound the async SQL operation with a cancellation deadline, default 30 seconds,
   configurable only above zero and at most 120 seconds. PostgreSQL also gets
   `statement_timeout`. Cancellation/driver cleanup can take additional time;
   this is not an absolute real-time process termination guarantee.
5. Keep file observation independently useful during SQL failure and vice versa;
   expose complete, partial, and unavailable outcomes with fixed error codes.

Rejected alternatives: bypassing RLS to obtain counts would invalidate the tenant
claim; setting a session-level tenant unnecessarily risks pooled-state leakage;
silently defaulting the agency hides observation scope; returning zero on error
destroys the diagnostic distinction. No new dependency was needed: the existing
SQLAlchemy connection/model, canonical RLS helpers, and Python standard library
cover these responsibilities.

Primary references checked on 2026-09-05:
[PostgreSQL SET TRANSACTION](https://www.postgresql.org/docs/current/sql-set-transaction.html)
describes transaction-local access mode and restrictions of `READ ONLY`;
[PostgreSQL client connection defaults](https://www.postgresql.org/docs/current/runtime-config-client.html)
describes statement timeouts and RLS settings. The use of read-only transactions
protects application data; it is not a claim that PostgreSQL performs no internal
disk activity, lock acquisition, statistics work, or connection cleanup.

### Schema 2 and observation semantics

The JSON `schema_version` is now **2**. It intentionally changes the following
contract; consumers must inspect the schema version before comparing old reports.

| Field/behavior | Current meaning |
|---|---|
| `observation_status` | `complete`: all requested source scans returned without excluded invalid/unreadable records; `partial`: a successful source or subset exists but another source/record failed; `unavailable`: no requested source could be observed. Completeness describes observation, not valid business state. |
| `rows_counted` | File: parsed JSON objects, including missing/null/invalid status fields. SQL: all visible grouped rows, including null. File schema 1 counted only string-coerced status values, so its numbers are not directly comparable. |
| `status_values_counted` | Count of actual string statuses represented by the token entries; no list/dict/bool/number coercion. |
| `missing_status_key` / `explicit_null_status` / `blank_status` | Distinct states. Blank strings retain raw representation and show the current alias-map result; missing/null never become an implied `new` record. |
| Invalid input | Separate counts for non-object records, non-string status fields, malformed encoding/JSON, unreadable files, and unsafe files. No raw invalid payload or filename is emitted. |
| `scope` | SQL is `agency_rls_and_predicate`. File is **`directory_unfiltered`**: `--agency-id` applies only to SQL; every eligible JSON file in the explicitly selected directory is observed. A `both` run is not a same-population comparison. |
| `writer_provenance` | Always `not_evaluated`; the distribution scan does not prove a live writer or classify a token as belonging to another field. |
| `canonical` / `alias_covered` | Current canonical alias-map interpretation/coverage only. An uncovered token can still be a valid current writer output. Neither field approves a new alias or enum member. |
| `errors` | Fixed `{source, code}` values; exception text, SQL parameters, DSNs, credentials, and raw command-line text are not emitted. |
| Exit | 0 for complete observation; 2 for partial/unavailable observation or invalid CLI usage. A complete empty directory is distinct from a missing root. |

The handwritten `KNOWN_TRIP_STATUS_WRITERS` and
`FOREIGN_VOCABULARY_CANDIDATES` flags were superseded by explicit unknown
provenance. Call-site search found only this report and its tests using the
constants; their unique purpose (routing writer research) remains represented
by `writer_provenance` and this E-12 research loop. There was no verified writer
inventory to preserve as machine truth. The original section 2 inventory is a
dated research lead, not a complete current writer table: current
`src/analytics/review.py:101` explicitly writes `status = delivered`, and its
recovery update at `:268` writes `recovery`. A fresh caller/reachability audit is
needed before adopting semantic classifications from the historical tables.

File scans pin an open directory descriptor and use `O_NOFOLLOW` for the root
and each JSON file; JSON symlinks are skipped rather than followed. `O_NONBLOCK`
plus regular-file checks prevents FIFO reads hanging the scan. This implementation
targets the repository's macOS/Linux environments; Windows portability is not
claimed. Reads are not an atomic snapshot of concurrently modified JSON files.
File contents remain byte-for-byte unchanged in the preservation regression.

### Verification receipts and sensitivity

All listed tests use synthetic inputs/fakes unless explicitly labeled live. The
SQL fake models context-dependent visibility but leaves real query construction,
canonical `apply_rls`, and posture interpretation in the exercised path. It is
Tier 2 evidence, not a substitute for a real database.

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/pytest -q -p no:cacheprovider tests/test_status_vocabulary_report.py --tb=short
Before implementation: 15 failed in 6.96s (exit 1).
First implementation: 15 passed in 11.77s (exit 0).
Defensive review additions: 27 passed in 9.06s (exit 0).

.venv/bin/ruff check tools/status_vocabulary_report.py tests/test_status_vocabulary_report.py
All checks passed (exit 0).
.venv/bin/ruff format tools/status_vocabulary_report.py tests/test_status_vocabulary_report.py
Formatting applied; no behavioral rewrite.
```

Known-defect regressions reached S2 for missing-root false success, non-string
coercion, raw exception leakage, and missing tenant context (the fake returned
zero rather than five expected rows before the fix). Newly introduced controls
and defensive cases have S1 coverage; an initial missing-function-argument error
is not itself proof of runtime timeout behavior. Final tests additionally cover
timeout cancellation/rollback, query-failure rollback, bypass-role refusal,
invalid tenant/deadline rejection before access, root symlinks/non-directories,
FIFO skipping, source-byte preservation, and both directions of partial-source
failure.

**Harness correction preserved:** the first pre-fix CLI negative test was missing
the fake-session fixture and could invoke the old unscoped application read. No
data-writing statements were in that path, but it was not an appropriately
isolated negative test. The fixture was added, and the quoted 15-failure baseline
was rerun with SQL replaced at the driver boundary. The first run is not used as
tenant-isolation evidence. No database cleanup/reset was performed.

RLS omission mutation (in-memory only, never written to application files):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/python -c 'import pytest
from spine_api.core import rls
async def omitted_tenant_context(session, agency_id):
    pass
rls.apply_rls = omitted_tenant_context
raise SystemExit(pytest.main(["-q", "-p", "no:cacheprovider", "tests/test_status_vocabulary_report.py::test_sql_sets_transaction_local_tenant_before_read_and_rolls_back", "--tb=short"]))'
```

Observed result: **1 failed** in 6.78 seconds (exit 1), `rows_counted: 0 != 5`.
One pytest harness warning noted `anyio` had been imported before assertion
rewriting. This establishes S3 sensitivity for omitting canonical RLS application;
it does not independently prove every PostgreSQL RLS policy is correct.

Live command (only the existing, instruction-named developer test agency):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/python -m tools.status_vocabulary_report \
  --backend both --agency-id d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b \
  --sql-timeout-seconds 20
```

Observed at report time `2026-09-05T11:31:15.613660+00:00`, exit 0:

| Source | Counts |
|---|---|
| File directory, unfiltered | 1,936 JSON objects; 1,798 string status values; 138 missing; 0 null/blank/invalid/malformed/unreadable/unsafe. `active=978`, `assigned=495`, `incomplete=21`, `new=304`. |
| SQL, explicit test agency | 21,937 rows, 7 status groups, 0 null/blank. `active=79`, `assigned=19022`, `cancelled=2`, `completed=13`, `in_progress=880`, `incomplete=135`, `new=1806`. Runtime RLS posture enforced, read-only transaction, no errors. |

This is live local CLI/database integration evidence (Tier 3), not deployed,
all-agency, real-customer, migration-readiness, or production proof. Counts can
change through unrelated authorized developer/test activity. The report never
normalizes persisted rows or changes the alias map.

### Review, residual risk, and next work

Review cycle 1 (parent source/test review): canonical RLS, read-only mode, tenant
predicate, rollback, and error separation accepted; requested explicit schema,
scope, sensitivity, platform, and timeout limitations are recorded above. Cycle 2
(defensive review): added root/FIFO, source-preservation, invalid deadline,
rollback-on-query-error, and partial-source tests; all passed. Correctness,
canonical architecture, and doctrine/scope review are complete for this tool.
Full-repository before/after suites and Git hooks are owned by the parent's
broader delivery gate and were not run by this bounded worker.

| Dimension | Assessment and remaining evidence |
|---|---|
| Code | Focused tests and lint pass; parent independent rerun and full-worktree gates remain separate. |
| Operational | CLI returns distinguishable observation/error states; source provenance and recovery instructions provided. |
| User experience | Developer/operator CLI only; no frontend change or browser claim. |
| Logical consistency | Scope and invalid/unknown distinctions explicit; no guessed status semantics. |
| Commercial | Indirect value: trustworthy migration/analytics decisions; no monetization claim. |
| Data integrity | No persistence mutations; rollback and byte-preservation tests; live scoped read succeeds. |
| Quality/reliability | S2 defect checks and RLS-omission S3; hostile resource scale and driver cleanup failure remain unproven. |
| Compliance/privacy | Errors sanitized, raw status strings deliberately retained for research; treat report output as potentially sensitive and review before committing/sharing. This is not legal compliance proof. |
| Operational readiness | macOS live read demonstrated; Linux nofollow behavior relies on supported POSIX API and still needs CI/runtime coverage. |
| Critical path | E-1 still needs writer/caller provenance, explicit vocabulary decisions, consumer migration and real gate evidence. |
| Final verdict | Tool code is locally verified; reporting feature is usable under the stated local scope. Overall E-12 and product launch remain incomplete. |

Recovery is rerunning the same bounded command after the specific source is
restored or choosing `--backend file` when SQL is unavailable. Do not disable
RLS, broaden the agency, or substitute an empty result to obtain exit 0. There
is no data rollback migration because no data was changed. Revisit this design
when report consumers depend on schema 2, the runtime role/RLS contract changes,
file stores move off POSIX, or file size/cardinality requires streaming/resource
budgets. A future writer-provenance mechanism must be source-linked and
reachability-aware; it must not resurrect the removed handwritten booleans.

Files are left uncommitted for the parent delivery workflow. Earlier exploration,
old snapshots, and unrelated work remain preserved.

Final defensive correction: a `*.json` directory caused `os.fdopen` to raise
before its context manager owned the descriptor. The added
`test_json_named_directory_is_skipped_and_all_descriptors_closed` failed first
(`os.fstat(fd)` unexpectedly succeeded, 1 failed in 1.17 seconds), demonstrating
a leaked descriptor. The scanner now owns and closes every descriptor in
`finally`, independently of stream construction, and classifies non-regular
entries as unsafe. This is a second S2 resource-lifecycle defect fix.

Final receipt after that correction and formatting:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/pytest -q -p no:cacheprovider tests/test_status_vocabulary_report.py --tb=short
28 passed in 1.29s (exit 0).
.venv/bin/ruff check tools/status_vocabulary_report.py tests/test_status_vocabulary_report.py
All checks passed (exit 0).
.venv/bin/ruff format --check tools/status_vocabulary_report.py tests/test_status_vocabulary_report.py
2 files already formatted (exit 0).
```
