# Implementation Plan — PER-0443 Agentic Travel Systems (2026-09-07)

**Status:** plan for remaining work. PER-0700 Phase 0–2 is **executed locally, uncommitted** — do not redo it.  
**Derived from:** [PERSONA_AUDIT_PER0443](PERSONA_AUDIT_PER0443_AGENTIC_TRAVEL_SYSTEMS_ARCHITECT_2026-09-07.md) + [FINDINGS REGISTER PER0443](FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md) + remaining PER-0700 Phase 3/4 + `Docs/LAUNCH_STATUS.md`.  
**Does not replace:** [IMPLEMENTATION_PLAN_PER0700_2026-09-06](IMPLEMENTATION_PLAN_PER0700_2026-09-06.md) or [LAUNCH_IMPLEMENTATION_PLAN_2026-09-02](LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md). This plan **slots after** PER-0700 0–2 and **beside** launch L1–L8.

**Standing rules:** findings lifecycle (one status store) · no duplicate routes · supersession before deletion · no test-DB truncate · no commit without explicit owner approval · S2 minimum on touched behavior; S3 on money/traveler-facing.

**Sizing:** S ≤ ½ day · M ≤ 2 days · L ≤ 1 week (one agent).

---

## September 8 execution refinement

This dated refinement governs the affected tasks below; September 7 sizing and
phrasing are historical planning assumptions, not current completion evidence.
Lifecycle authority remains `FINDINGS_REGISTER_2026-08-31.md` (207 rows, 151 open,
55 closed, one deferred). Execution receipts and scoped fingerprints are in
`EXECUTION_STATUS_2026-09-04.md`; chat decisions are in
`CHAT_REQUEST_EVIDENCE_TRACE_2026-09-04.md`.

| Unit / risk | Current disposition and next atomic acceptance boundary |
|---|---|
| 2.5b / F-31, AT-12 — high | Quote's unsupported affirmative eligibility and universal deadline have been replaced by nullable not-evaluated results with evidence provenance; full backend 4,109 passed. A typed confirmation ID is not verification. Next implement canonical insurance BookingConfirmation ownership/action authorization, path/body agreement and actual actor attribution; then shared transaction/audit/idempotent replay and legacy projection migration. Use the insurance research package's exact acceptance matrix; no provider binding or purchase is authorized by this plan. |
| 2.2 / F-17, AT-05, AT-18 — high | Keyed private-link lifecycle, no persistent private graph replay, nullable destination and explicit SOS/sample-time honesty are implemented with failing-first tests. Final request-state correction and full frontend receipts remain tracked in execution status. No continuous revocation, durable SOS delivery, offline access contract or full date-grouped itinerary projection is claimed. |
| F-19 — high | Development/build output isolation is implemented; full backend infrastructure isolation is not. Next implement a per-run PostgreSQL/file target contract, migrations/readiness/capacity preflight and explicit HTTP tier before relying on a hermetic verification claim. Preserve unrelated running services and storage. |
| F-38 — high | Fresh review retains incomplete enumeration, unreadable-record handling, stable pagination/snapshot, unknown-time and action-capability gaps. Implement the four atomic seams in `F38_DISRUPTION_DATA_INTEGRITY_REVIEW_2026-09-05.md`; do not call a page with more pages outstanding a complete scan. E9 date policy remains a decision, not a fabricated filter. |
| PA-10 — medium | Registry/exposition work is retained. Verify intended authenticated scraping and fix source/documentation disagreement: live anonymous metrics is 401. Do not add metrics to the public allowlist merely to make a readiness command green. |
| EV-11 / delivery — high | Preserve staged work and retain actual full-gate/attestation receipts. Shared doctrine version-validation failure and push-triggered Fly deployment boundary remain separate unresolved delivery gates. No Git or deployment completion follows from local tests. |

For each implementation unit: recheck current source, constrain one writer per
shared file, demonstrate failing-before/passing-after behavior, retain failure
receipts, run the affected full gate against the final candidate, and update
the canonical row without blanket closure of adjacent requirements. Source,
mocked tests, browser, provider and hosted evidence remain distinct.

## Non-goals (explicit)

- Re-implement PA-01…PA-10, PA-12 GC half, PA-14–17, PA-24–28, PA-38.
- New routers for existing resources.
- Importing OrbitCover.
- Public/paid launch, provider money movement, Git push (separate gates).
- Treating local test greens as L1–L8 proof.

---

## Wave 0 — Owner gates (no product code)

Blocks Phase 4 of PER-0700 and AT-15.

| # | Task | Findings | Size | Output |
|---|---|---|---|---|
| 0.1 | Ratify ADR-008 §6 (or written deltas) | AT-15, PA-03, C-01…C-04 | S (owner) | Ratified ADR or rejection note |
| 0.2 | Reconcile E-B 7-class design vs live 8-class `FailureClass` | E-B contested | S | One enum in code+doc |
| 0.3 | Commission **missing** exploration docs only: E-D, E-E, E-G, E-NBA, E-commit | AT-10, PA-18/19, L4, AT-07, AT-02 | M | Four design docs |
| 0.4 | Git classification of the uncommitted PER-0700 tree | inventory F-04 / EV-11 | S (owner) | Authorized commit **when asked** — not this session |

**Default if 0.1 unanswered:** keep hybrid `"0"`, fulfillment R1, mandates flag off.

---

## Wave 1 — Honesty drift created by Phase 0–2 (small IMPLEMENT)

Independent of Wave 2. Do first.

| # | Task | Findings | Size | Verification |
|---|---|---|---|---|
| 1.1 | Align `.env.example` and `render.yaml` hybrid to `"0"` (or document Render as explicit opt-in) | PA-03 residual | S | rg shows no serving default `=1` without a comment that names the exception |
| 1.2 | F-43: narrow Next rewrites / restore BFF allowlist for `/api/v1/*` | F-43 | M | Route-map test; unauthenticated `/api/v1` money path 401 |
| 1.3 | Rename remaining `TRIP-LIVE-*` defaults; add RealityTier to counterfactual router | AT-19 | S | No `TRIP-LIVE` in request defaults; counterfactual response has `reality_tier` |
| 1.4 | E-F leftovers: TierMetadata on negotiation/charter/yield/stress/logistics/export | E-F | M | Each listed router returns tier field |
| 1.5 | RECORD: stale comments (`metrics_registry` TODO, C02 “default-ON”, E-F PA-26 “not started”, INDEX PER-0700 P0 sentence now historical) | — | S | Docs match live |

**Do not redo:** journey-graph de-fabrication, fulfillment persist/read-back, metrics exporter, failure_class persist, SSE cap, collection CAS, IVR simulated, compiler share-token block, PA-26 auth, PA-38 mirror.

---

## Wave 2 — Travel-domain contracts (this persona’s new work)

Highest real-world consequence. Extend canonical paths only.

### 2.0 Persist the journey (P0) — unblocks 2.1–2.4

| # | Task | Findings | Size | Verification (S2/S3) |
|---|---|---|---|---|
| 2.0a | On compile **and** fulfill, persist `journey_graph_nodes` + edges on the trip (or a dedicated table keyed by trip). Public GET already reads this field. | AT-01 | M | S2: fulfill a seeded trip → GET graph `exists:true` with persisted node ids; no stored graph → still 404/abstain |
| 2.0b | Fulfillment writes `BookingConfirmation` (SQL machine) with `reality_tier`; trip JSON becomes a projection | AT-04, AT-09 | M | S2: confirmation row present; void path can see it |
| 2.0c | Node commitment states `quoted \| held \| booked \| ticketed \| void` (design in E-commit if Wave 0.3 not done — minimal enum in schema is enough to start) | AT-02 | M | S2: ticketed node cannot be silently overwritten |

### 2.1 Once-booked + idempotent fulfill (P0)

| # | Task | Findings | Size | Verification |
|---|---|---|---|---|
| 2.1 | If `booking_confirmation` or verified confirmation exists → 409 replay. Wire `Idempotency-Key` to the durable CAS registry on fulfill (and price-lock persist-when-real). | AT-03, PA-40 | M | S2: second POST same key returns original PNR; second POST no key with existing confirmation → 409; no second VCC |

### 2.2 Companion honesty (P0 traveler-facing)

| # | Task | Findings | Size | Verification |
|---|---|---|---|---|
| 2.2a | Fetch with signed token; on 401/404 show abstain, never `'BA 178'` / e-ticket / Aman / Tokyo fallbacks | AT-05 | S | S2: unit test no fallback PNR; empty graph UI is sample-labeled |
| 2.2b | Remove hardcoded ON TIME; SOS writes a durable event (or is labeled demo and does not claim transmission) | AT-18 | S | S2: no SOS success without an API; flight status from snapshot or unknown |

Browser S3 remains L7 (launch). Do 2.2 anyway — source-level fabrication is a §13 defect.

### 2.3 IROPS on the stored graph (P1)

| # | Task | Findings | Size | Verification |
|---|---|---|---|---|
| 2.3a | `execute_healing_protocol` loads persisted JDG for `trip_id`; if missing → abstain. Keep router sanitizer. | AT-06 | M | S2: sample BA178 graph gone when trip has stored nodes; no graph → PREVIEW abstain not fake Four Seasons |
| 2.3b | FlightStatusAgent high-risk → `evaluate_disruption` on stored graph → escalated queue item (R2). **No auto-rebook.** | AT-06, R-12 | M | S2: recovery-escalated trip appears with `failure_class`/disruption reason |
| 2.3c | Supersede `src/logistics/irrops_healer.py` (comparison table + migrate unique EU261 bits into `passenger_rights.py` if any) | AT-06, AT-17 | S | Supersession workflow in commit message |

### 2.4 Next-best-travel-action projection (P1)

| # | Task | Findings | Size | Verification |
|---|---|---|---|---|
| 2.4 | Single server projection `travel_next_action` owned by lifecycle+JDG+readiness+disruption. Fleet may **propose**; they must not overwrite a higher-priority action. Rename CRM field to `commercial_next_action`. | AT-07 | M | S2: flight disruption cannot be clobbered by weather stamp; decision payload still has commercial action under the new name |

### 2.5 Honesty on adjacent travel surfaces (P1)

| # | Task | Findings | Size | Verification |
|---|---|---|---|---|
| 2.5a | Visa radar: real trip dates/nationality or abstain; drop TEST_AGENCY_ID fallback in prod | AT-11 | S | S2 |
| 2.5b | Insurance quote evidence and canonical recorded-vs-verified attachment contract; September 8 refinement above supersedes the earlier typed-confirmation-ID-only prescription | AT-12, F-31 | Re-size transaction unit after seam review | S2/S3 plus local/full, authorization and replay receipts; no provider proof inferred |
| 2.5c | Loyalty GET: sample badge or empty; never invent balances | AT-13 | S | S2 |
| 2.5d | Counterfactual `/replan-disruption` loads stored graph; strip hardcoded 94.5 scores or mark `heuristic` | AT-19 | S | S2 |

### 2.6 Product contracts (after or in parallel with owner D-01…D-03)

| # | Task | Findings | Size |
|---|---|---|---|
| 2.6 | Duration, flights-inclusiveness, country/city — extractor + API + UI together | D-01…D-03, F-21, F-22 | L |

Do not implement 2.6 until the DECIDE rows are answered (probes already exist).

---

## Wave 3 — Remaining PER-0700 observability / eval (true Phase 3 leftovers)

| # | Task | Findings | Deps |
|---|---|---|---|
| 3.1 | Audit-chain verify + re-anchor + one `/api/audit` store | PA-19, F-06 | E-E |
| 3.2 | `usage_events` schema columns + rollup | PA-20 residual | E-C + A-20 alembic custody |
| 3.3 | Autoresearch: live D6 **or** `simulated:true` lineage (label exists; `accepted=True` still written) | PA-11 | — |
| 3.4 | Closed-loop real fixture re-execution | PA-21 residual | D6 |
| 3.5 | Eval cost/latency/human dims | PA-34 | E-C |
| 3.6 | Per-trip in-flight lease on `/run` | PA-13 residual | — |
| 3.7 | Terminal lease/requeue TTL; honest checkpoint/DLQ | PA-29, PA-30 | — |
| 3.8 | Activate adversarial corpus as a lane | E-H | corpus already seeded |

Memory read-path (PA-18) **only after E-D**. Hard rule from AT-10: never a hold/ticket input.

---

## Wave 4 — Launch envelope (owns L1–L8)

Do not mix with Wave 2. Sequence: E-G → SQL projection (L4) → platform choice (L1) → backup/restore (L2) → remaining sim/provider (L3) → legal (L6) → browser smoke including companion (L7) → authorized snapshot (L8).

PER-0443 code does not substitute for these.

---

## Critical path

```text
Wave 0 owner (ADR-008)     ── parallel ──► Wave 1 honesty drift
         │
         ▼
Wave 2.0 persist JDG  ──► 2.1 once-booked fulfill
         │
         ├──► 2.2 companion honesty (can start after 2.0a contract known; even before persist using abstain)
         ├──► 2.3 IROPS on stored graph
         └──► 2.4 NBTA projection
                └──► 2.5 visa/insurance/loyalty/counterfactual
Wave 3 observability      (parallel after Wave 1)
Wave 4 launch             (after E-G + owner L1)
```

Companion 2.2 can ship **before** JDG persist: abstain is already the public contract. That is the fastest traveler-facing §13 win.

---

## First implementation unit (recommended)

If the owner says “start coding” without changing this plan:

1. **2.2 companion honesty** (S, S2 tests, no money path)  
2. **1.1 hybrid env drift** (S)  
3. **2.0a persist JDG on fulfill** (M, unblocks IROPS)

Stop and ask if they want money-path 2.1 (fulfillment idempotency) in the same slice — that is a higher risk class even though adapters are simulated.

---

## Wave 2 execution evidence (2026-09-07, uncommitted)

Owner authorized the four OS-layer breaks in this conversation. Local unit executed:

| Plan # | Status | Proof |
|---|---|---|
| 0.3 E-NBA + E-commit | done (docs + code) | `Docs/architecture/TRAVEL_NEXT_ACTION_PROJECTION_2026-09-07.md`, `PROGRESSIVE_COMMITMENT_JDG_2026-09-07.md` |
| 1.1 hybrid env | done earlier same day | `.env.example` / `render.yaml` = `0` |
| 1.3 TRIP-LIVE defaults + counterfactual tier | done | no `TRIP-LIVE` request defaults; counterfactual `reality_tier` |
| 2.0a persist JDG | done | fulfill + compiler persist; GET hydrates; evaluate abstain |
| 2.0b SQL confirmation | **not done** (AT-04; AsyncSession vs file-store tests) | — |
| 2.0c commitment states | done (enum + lock) | ticketed nodes not overwritten by compile |
| 2.1 once-booked | done as replay (not 409 + CAS) | second fulfill `idempotent_replay`; PA-40 CAS still open |
| 2.2a/b companion honesty | done except durable SOS | token + abstain; SOS still labeled demo |
| 2.3a IROPS stored graph | done | missing graph abstains; sample BA178 gone |
| 2.3b FlightStatusAgent → evaluate | **not done** | fleet still snapshot-only |
| 2.3c logistics healer supersession | **not done** | — |
| 2.4 NBTA | done | commercial vs travel fields; priority merge |
| 2.5a–d visa/insurance/loyalty/counterfactual | done at honesty layer | balances empty; visa abstain; heuristic scores labeled |
| F-43 / 2.6 / Wave 3–4 / ADR-008 | **not this unit** | — |

Verification: 43 focused backend + 66 agent/decision + 5 FE honesty; ruff clean on OS-layer files. Not Git. Not hosted. Not L1–L8.

---

## Ratification checklist for owner

1. Approve Wave 0.1 ADR-008 (or deltas).  
2. Approve Wave 2.0 as the itinerary SSOT (trip-as-document ends).  
3. Confirm no auto-rebook (2.3 stays R1).  
4. Confirm AT-10: memory never selects inventory.  
5. Confirm this plan does **not** authorize Git commit or hosted deploy.  
6. Approve promotion of AT-01…AT-19 into the canonical register (additive).  

---

## Skills for the implementing agent

Open `Docs/FULL_SKILLS_CATALOG.md`, search category **Travel operating system** (persona) plus:

- persist/idempotency: category **Backend, contracts, state** → `backend-patterns`, `python-testing`, `tdd-workflow`
- companion UI: category **Frontend & operator UX** + **Testing & verification** (`webapp-testing`, `browse`)
- eval leftovers: category **Agentic systems & evals** → `agentic-eval-loop` + `AGENTIC_EVAL_RULES.md`
- before claiming done: `verification-before-completion`
