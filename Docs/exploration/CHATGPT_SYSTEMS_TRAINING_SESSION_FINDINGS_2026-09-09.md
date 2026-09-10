# ChatGPT Systems-Training Session — Findings Register & Promotion Record (2026-09-09)

**Source:** `Docs/exploration/CHATGPT_SYSTEMS_TRAINING_TRANSCRIPT_2026-09-09_RAW.md` (verbatim, full fidelity)
**Lineage:** continuation of the TPM training thread — `Docs/exploration/TPM_SYSTEMS_LEARNINGS_PROMOTION_2026-09-01.md` (state/decision/action decomposition, progressive autonomy, dependency/gate/parallelism) → this session (trip-state vs memory, decision layer, action autonomy, validation, idempotency, failure modes, state machines, lifecycle states, orchestration gates).
**Mode:** evidence-backed extraction and bounded promotion (same method as the 2026-09-01 record). Every "already exists" claim below was verified against code on 2026-09-09 with file:line anchors; gaps were probed in-repo before being registered.
**Doctrines applied:** Operating Doctrine 8.0; Exploration Doctrine 1.1; Inquiry & Analysis 1.0; Documentation 1.1.

---

## 1. Headline verdict

The session is **architecture-validating more than architecture-changing**. Of the ~20 concepts the tutor taught, the repo already independently implements or has a ratified design for **14** — in several cases (four-question state contracts, progressive commitment rungs, gates vs dependencies) the repo's implementation is *more specific than the lesson*. The genuinely new delta is **6 register items (TS-01…TS-06)**, of which **TS-01 (hard itinerary-feasibility validators)** is the only one that is pure-deterministic, provider-independent, and implementable now. The session also produces **2 owner-learning items (TS-L1/TS-L2)** with a direct bridge into open product work (E-8 dormant lifecycle states).

Score progression recorded in the transcript: 6/10 (business-flow level) → 8/10 (dependencies, sources of truth, AI-vs-deterministic boundaries). Weakest area per tutor: route-design dependency modeling (register: TS-06).

---

## 2. Validated doctrine — concept → current implementation (no new task; recorded as confirmation evidence)

| # | Transcript concept | Repo status (verified 2026-09-09) |
|---|---|---|
| V-1 | **Trip state ≠ customer memory.** "State = what is true now; memory = what may help decisions." | Packet/state models carry current truth with epistemic status (`src/intake/packet_models.py:150-181`); memory is a separate 5-tier store with provenance/decay/supersession; read-path slot spec constrains memory to *ranking questions, never inventory* (`Docs/architecture/MEMORY_READ_PATH_SLOT_SPEC_2026-09-08.md`). Memory remains write-only pending PA-18 wiring (already registered). |
| V-2 | **Decision layer answers "what happens next", not "the itinerary".** | Implemented same-week as the lesson's sibling: `travel_next_action` projector with priority bands + CAS verify-and-heal (`src/orchestration/travel_next_action.py:12-228`, wired `src/intake/decision.py:2297-2346`, `src/agents/runtime.py:383-386`; doc `TRAVEL_NEXT_ACTION_PROJECTION_2026-09-07.md`). |
| V-3 | **Cost of a mistake determines autonomy level** (search reversible, charging ₹2L not). | NB02 `decision_readiness` gate → `AutonomyOutcome` auto/review/block, `STOP_NEEDS_REVIEW` always blocks (`src/intake/gates.py:47-92,156-253`); ADR-008 §6 autonomy rungs (ratification = open DECIDE C1, already registered). |
| V-4 | **AUTHORITATIVE DATA → DETERMINISTIC FILTERING → AI RANKING → DETERMINISTIC VALIDATION.** "AI must never alter ₹94,000 / 8h 15m." | Deterministic spine + hybrid engine; constraint engine runs hard rules on provider facts (`src/decision/constraint_engine.py`); fabrication gates on public surfaces (journey graph abstains when missing, PA-01/F-41 fixed). |
| V-5 | **Idempotency** (booking timeout → double-charge). | Deeply implemented: SQL idempotency backend, `Idempotency-Key` on fulfillment, provider-key determinism + side-effect markers + in-lease recheck + lease-heartbeat CAS (PER-0443 Parts H/J), once-booked replay via confirmation record (`PROGRESSIVE_COMMITMENT_JDG_2026-09-07.md` §3). |
| V-6 | **State vs actions-inside-a-state** (OCR/parse/normalize are tasks inside INTAKE, not states). | Exactly the shipped design: `TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md` puts extraction/normalize/OCR inside INTAKE; states are derived from six vocabularies with one enforced structural invariant (`spine_api/core/trip_status.py:93-105`). |
| V-7 | **Four questions per state** (true / allowed / forbidden / what moves us out). | The repo doc *is* this pattern, with an enforcement matrix and honest gap ledger — the tutor's closing exercise template already exists as a product artifact. |
| V-8 | **Gate ≠ dependency ≠ parallelizable.** | `GateVerdict` PROCEED/RETRY/ESCALATE/DEGRADE; NB01 DEGRADE = "saved but unquotable" (gate semantics, not data dependency). |
| V-9 | **Hard stop vs recoverable gate; request-failure vs goal-failure.** | ESCALATE (human) vs DEGRADE (continue with less) vs NEEDS_REVISION loop-back in the lifecycle diagram; escalation is a cross-cutting state reachable from any implemented state. |
| V-10 | **Concurrent writers to the same trip** ("which state wins?"). | CAS + idempotency fencing, store-level priority merge design (E-G), `NextActionAwareTripRepo` verify-and-heal so a low-priority write can't clobber the winning action. |
| V-11 | **CHECK ≠ RESERVE ≠ PURCHASE — progressively stronger certainty.** | `PROGRESSIVE_COMMITMENT_JDG_2026-09-07.md`: `quoted → held → booked → ticketed` node rungs; illegal to skip rungs unlabeled; `quoted→ticketed` only as labeled deterministic preview. This is the lesson, already ratified into code. |
| V-12 | **Provenance behind each important fact.** | Packet level: `EvidenceRef` + `Slot.authority_level/extraction_mode/evidence_refs/derived_from` (`src/intake/packet_models.py:126-181`). Trip level: `_field_provenance` per field with actor precedence (`spine_api/services/field_merge.py:20-89`). Residual gap → **TS-04**. |
| V-13 | **Traveler-facing vs operator-facing outputs.** | Separate surfaces with separate copy gates (AT-21 traveler-copy sweep, 5 traveler surfaces). |
| V-14 | **Scale worries: observability / privacy / cost / model drift / provider failure.** | All already registered as open work: PA-19 audit-chain verify + `/api/audit` store, OTEL trace-correlation gap doc, A4 `booking_confirmation` encryption, C-04 SLM benchmark + `COST_PER_OUTCOME_MODEL_2026-09-07.md`, eval lanes + holdout + drift gate, `FAILURE_TAXONOMY_RECONCILIATION_2026-09-08.md` (live 8-class enum). The transcript reinforces priority; it adds no new row. |

**Feedback loop ("no learning from mistakes")** from the transcript's scale section maps to the already-registered memory write-only finding (PA-18) + `MEMORY_READ_PATH_SLOT_SPEC` — reinforcement, not a new item.

---

## 3. New register items (verified absent or partial in code)

Prefix **TS-** (training-session-sourced, 2026-09-09). No collisions with existing register prefixes (checked).

### TS-01 — IMPLEMENT (S per check, M total) · Hard itinerary-feasibility validators: the timing/transfer/capacity family — **DONE 2026-09-09 (same session)**

The tutor's canonical example — *flight lands 10:40, Disney booking 11:00, 70-minute transfer → a validator must reject it* — plus his validation list. Verified current state **before** implementation:

| Check | Status | Evidence |
|---|---|---|
| Flight connection MCT (hard) | ✅ existed | `src/decision/constraint_engine.py:165-232` (+ terminal MCT matrix `:48-83`; `src/logistics/connection_risk.py:334`) |
| Overlapping bookings / teleportation (hard) | ✅ existed | `constraint_engine.py:184-186` `SPATIAL_OVERLAP` |
| Passport validity vs destination (hard) | ✅ existed | `constraint_engine.py:230-252`; `spine_api/services/visa_radar.py` |
| Total cost ≤ approved budget | ✅ existed | budget gate (F-18 green honestly) |
| **Arrival→first-activity transfer buffer (hard)** | ✅ **implemented** | `GROUND_OVERLAP_` (hard, starts-before-arrival) / `GROUND_ACCESS_DEFICIT_` (hard, explicit `required_transfer_minutes`/`recommended_arrival_buffer_minutes` unmet) / `GROUND_BUFFER_TIGHT_` (soft advisory — heuristic FLIGHT 90m / RAIL·FERRY·CRUISE 45m defaults never hard-reject) in `constraint_engine.py` §1b |
| **Hotel check-in vs arrival** | ✅ **implemented** | `UNCOVERED_FIRST_NIGHT_` hard check, §1c — interval coverage (>12h arrival→check-in with no onward leg = uncovered night); plus owner-confirmed soft companion (2026-09-09): `LONG_LAYOVER_NO_HOTEL_` advisory for ≥6h lodging-less layovers with an onward connection (transit-room upsell, never a block) |
| **Hotel occupancy vs party size (hard)** | ✅ **implemented** | `OCCUPANCY_EXCEEDED_` (CAPACITY_ROOMING — first producer of that dormant category); metadata shapes `max_guests`/`capacity`/`rooms[]`/`room_count`×`max_occupancy_per_room`; abstains without declared capacity |
| **Child-age rules vs fare/product** | ✅ **implemented** | `AGE_RULE_` (COMMERCIAL_SUPPLIER_POLICY) on node `min_age`/`max_age`/`infant_max_age` metadata + `PAX_MISMATCH_` (declared ticket pax vs party — the tutor's "traveler count matches tickets") |

Callers extended: `evaluate_itinerary_graph(..., party_size=)` (compiler passes `traveler_count`; router already passes `travelers`). Tests: `tests/test_constraint_engine_feasibility.py` (31 tests, paired fail/pass per family — S1+S3 style); existing constraint suites untouched-green. **Every check abstains without declared data — no fabricated supplier-side facts.** Hardened through 4 review cycles (cycle-1 P0: multi-check-in false-reject → interval coverage; cycle-2 P1: return-leg/transit false-positives → RETURN_LEG_OF + refined final-arrival discriminator + transit exemption; cycle-3 P1s: transit-exemption set and door-drop-off scope narrowed) — full findings and final mergeable sign-off in `Docs/review/TS_REGISTER_EXECUTION_HANDOFF_2026-09-09.md`.

### TS-02 — EXPLORE (S) → IMPLEMENT later · Quote-freshness / recheck-before-execution contract — **DOC DELIVERED 2026-09-09**

Contract design at `Docs/exploration/TS02_QUOTE_FRESHNESS_CONTRACT_2026-09-09.md`: freshness classes (fresh/stale/unknown), staleness gates by commitment rung, materially-changed re-approval rule (delta = owner DECIDE), deterministic-no-LLM recheck, `revalidate_quote_before_payment` token→logic wiring, and the small honest implementable-now slice (schema fields + labeled panel copy). Full recheck engine intentionally deferred to the B6/B7 provider lane — no recheck theater against simulated inventory.

### TS-03 — EXPLORE (M) → IMPLEMENT (M-L) · Multi-modal intake completion — **DOC DELIVERED 2026-09-09**

Plan at `Docs/exploration/TS03_MULTIMODAL_INTAKE_COMPLETION_2026-09-09.md`: modality priority (image/PDF via the **existing operator vision lane** extended to customer inbound — no second extractor; voice gated on WhatsApp-native transcripts DECIDE; URL last, SSRF-allowlist prerequisite), attachment-envelope schema, PII posture, upload-validation gates, prompt-injection fixtures, and S1–S5 sizing. Strategic anchor: D-01 open verifier/marketplace where a competitor-quote screenshot is both demand capture and checker input.

### TS-04 — EXPLORE (S-M) · Provenance actor vocabulary for tool/provider writes — **IMPLEMENTED 2026-09-09 (same session)**

`spine_api/services/field_merge.py` extended: canonical vocabulary `operator | customer | system | tool | provider`; precedence now **commercial: provider > operator > tool/system > customer** (provider facts are authoritative) and **preference: customer > operator > machines** (machines never override wants). Trust boundary preserved: internal roles are not client-submittable — `normalize_actor_role` folds a client-claimed `provider` to operator, and `resolve_field_merge(..., allow_internal_actors=True)` is the server-side-writer-only escape hatch; stored provenance is parsed against the full vocabulary so a stored `provider` actor keeps its rank in later merges. Contract description updated (`spine_api/contract.py`). Tests: `tests/test_field_merge_actor_vocabulary.py` (16 tests incl. the escalation-guard test); legacy operator/customer behavior regression-guarded.

### TS-05 — EXPLORE / design-note (park until real providers) · Pipeline parallel orchestration & speculative execution — **DOC DELIVERED (parked) 2026-09-09**

Design note at `Docs/exploration/TS05_PARALLEL_ORCHESTRATION_DESIGN_NOTE_2026-09-09.md`: records the tutor's decision factors as the unpark checklist, the proposed shape (single bounded `TaskGroup` around provider I/O only; deterministic phases stay sequential), explicit out-of-scope (no actor framework — runtime roadmap Layer 3 owns durability), and the revisit trigger (live provider >2s median latency or WhatsApp-corridor UX pressure).

### TS-06 — EXPLORE (S) · Candidate route-structure planning with incremental refinement — **IMPLEMENTED 2026-09-10 (same session)**

Verification had confirmed the gap (single-snapshot plan-candidate; `BRANCH_OPTIONS` without a producer). Landed: `src/decision/route_structures.py` — deterministic enumerator (night-splits across city permutations honoring hard constraints: every city once, nights sum, min-nights; bounded; >4 cities keeps input order as the documented geography-lane pruning seam) + open-jaw refinement (arrival/departure city scoring: aligned structure wins, no backtrack; partial alignment between; case-insensitive; generation never blocks on soft dependencies) + `candidates_as_branch_options()` rendering. **Producer wired:** `src/intake/decision.py` Phase 12 — multi-city packets with derivable nights (ISO `date_start`/`date_end` via `_derive_trip_nights`, abstains on anything unparseable) gain up to 2 route-structure `branch_options`; **decision_state is never changed by enrichment** (state-transition wiring stays with the E-8/DECIDE-gated work). Frontend: `DecisionTab` now renders both option shapes (fixes the pre-existing `[object Object]` render defect for dict-shaped budget-tier options) + `spine.ts` union type. Tests: `tests/test_ts06_route_structures.py` (14).

### TS-03 — Multi-modal intake — **S1 IMPLEMENTED 2026-09-10; S2/S3 deferred to the marketplace lane (named seams)**

**S1 done:** `InboundAttachment` envelope on `InboundInquiryRequest` (`spine_api/contract.py`) — kind-paired mime allowlist (image/jpeg, image/png, application/pdf), base64 validation, 5 MiB size cap, max 5 per inquiry; `/api/v1/inbound/parse` persists attachments via the canonical document-storage lane (`{agency}/{trip}/att_*.{ext}`, content-addressed manifest with sha256) and records `inbound_attachments` on the trip; attachment digests participate in idempotency identity (same text + different bytes = different request); storage degradation never fails the parse (best-effort post-save, response reports `attachments_accepted`). Extraction stays in the operator lane (stage-gated) — nothing auto-applied to the packet at intake. Tests: `tests/test_ts03_inbound_attachments.py` (8, incl. the broken-storage degradation case). **S2 seam (deferred):** merge extracted attachment facts into the packet as `tool`-actor writes via `resolve_field_merge(allow_internal_actors=True)` when the operator runs extraction — the manifest's `storage_key` is the join. **S3 seam (deferred):** screenshot-of-quote fixtures + OCR-injection cases into the E-H corpus once the S2 path runs, per the failure-becomes-fixture rule.

---

## 4. Owner-learning items (training thread, not agent work)

- **TS-L1 — Pending exercise (from the tutor):** model `NEEDS_INFORMATION` and `BOOKING_IN_PROGRESS` with the five questions (true / allowed / forbidden / events / out-transitions). **Bridge:** `BOOKING_IN_PROGRESS`, `BOOKED`, `IN_TRIP`, `CHANGE_REQUESTED` are *dormant declared states* in `TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md` (no validator). Pranay's exercise answer can be promoted into the dormant-state contracts and becomes spec input for **E-8** (server-side persisted `TripLifecycleState`) — training output becomes product spec. Recommended: do the exercise in the next tutoring session, then promote.
- **TS-L2 — Tutor's promised next module** (events, queues, retries, idempotency): the repo is the worked answer key — `src/agents/idempotency.py`, execution leases + heartbeat CAS (PER-0443 Part H/J), SQL idempotency backend, dead letters (`MULTI_AGENT_RUNTIME_ROADMAP.md` Layer 3). Use these artifacts as the concrete examples during that session.

---

## 5. Sequencing recommendation

1. **TS-01** now (deterministic validators; fits Wave A "canonical paths, sized" profile; extend `constraint_engine.py`).
2. **TS-04** next (small design + bounded code; closes the provenance residual the transcript explicitly names).
3. **TS-02 + TS-05** fold into **B6/B7** provider work when it unblocks (both are only meaningful against live rate/tool sources).
4. **TS-03** explore-doc whenever the demand-capture funnel (D-01 marketplace) moves to implementation — it is the intake side of that decision.
5. **TS-06** small reconcile pass vs Phase 4.6; promote only if the planner doesn't already do candidate structures.
6. **TS-L1/L2** ride the tutoring cadence; promote exercise output into the lifecycle contracts doc.

Rows above are source-registered here; promote into `FINDINGS_REGISTER_2026-08-31.md` / `OPEN_WORK_ROADMAP` when picked up (roadmap pointer added 2026-09-09).

---

## 6. Second session (2026-09-10) — state machines → idempotency → queues

**Source:** `CHATGPT_SYSTEMS_TRAINING_TRANSCRIPT_2026-09-10_RAW.md` (segment 2: tutor's TS-L1 exercise + owner's 8/10 answer + corrections). All claims below code-verified 2026-09-10.

### Validated doctrine (no new task)

| # | Transcript concept | Repo status (verified 2026-09-10) |
|---|---|---|
| V-15 | **Idempotency & BOOKING_RESULT_UNKNOWN safety** (timeout ≠ failed; retry with same key returns the same booking) | The money path already implements the *machinery*: side-effect marker persisted BEFORE provider calls (`booking_fulfillment.py:252-274`), deterministic provider idempotency key `sha256("fulfill:{trip_id}:{proposal_token}")` (`:574-585`), in-lease recheck before retry (`:244-250`), idempotent replay repairing missing confirmations (`:498-571`), TTL stale-PENDING reclaim (`src/agents/idempotency.py:246-284`). **The vocabulary gap is real though** — see TS-08. |
| V-16 | **Stage-dependent field requiredness** ("a field isn't globally required=true") | Two-tier version EXISTS: `validate_packet(packet, stage=...)` — discovery tier = INTAKE_MINIMUM errors + QUOTE_READY-as-warning; shortlist+ tier = full QUOTE_READY errors (`src/intake/validation.py:100-133`); NB01 DEGRADE = "saved but unquotable" (`gates.py:101-153`); booking-stage passport/visa risk checks (`decision.py:1279-1298`). The operation-keyed generalization is the gap → **TS-07**. |
| V-17 | **Retry policies per operation; read vs write** | Per-agent `RetryPolicy(max_attempts, backoff)` + dead letters + zombie-lease sweeper + poisoned states exist (`src/agents/runtime.py:170-185,139-167,489-495`); SQL work coordinator + durable requeue-jobs queue with worker (`spine_api/services/agent_requeue_jobs.py`). No safety-classification vocabulary (auto / idempotent-only / never) anywhere → **TS-09**. |
| V-18 | **Queues/workers/orchestrator** (booking as queued job) | Leases + requeue-jobs queue exist; **booking fulfillment executes in-request** (sole caller `spine_api/routers/fulfillment.py:155,196`); outbox ABSENT (comment-only, `src/analytics/review.py:167`). This is `MULTI_AGENT_RUNTIME_ROADMAP.md` Layer 3 (durable orchestration) — already registered there; the fulfillment-in-request fact sharpens its priority for the live-provider lane. |
| — | **Route finalization before approval** ("if you're still deciding Tokyo-first, don't buy tickets") | Matches ratified progressive-commitment rungs (register §2 V-11): structure is fixed at proposal/quoted; booking rungs only execute the approved graph. |
| — | **Visa as separate workstream with own lifecycle** | ABSENT: visa is a stateless point-in-time check (`visa_radar.py:31-46`) + intake fact + `verify_visa` task — no independent lifecycle. Cross-reference the visa audit's open VD-02/03/04 DECIDEs rather than a new item. |

### New register items

Prefix TS-, second session.

### TS-07 — EXPLORE (S-M) · Operation-keyed field requiredness (`required_for`) — **IMPLEMENTED 2026-09-10 (same session)**

`src/intake/validation.py`: `OPERATIONS` + `FIELD_REQUIRED_FOR` map (requiredness keyed to planning / fare_quote / entry_validation / booking — the tutor's "a field isn't globally required=true" model) + `classify_missing_fields()` (BLOCKING_FOR_*/PREFERENCE tutor-model classifier for NEEDS_INFORMATION; present fields omitted; nothing invented) + `question_priority_order()` (most-blocking first — the E-D ask-priority ranking input). **Real consumer wired:** the hard-blocker follow-up questions in `src/intake/decision.py` are now ordered by operation impact and each carries `required_for` (additive; decision states unchanged). INTAKE_MINIMUM/QUOTE_READY tiers untouched (extend, not fork). Tests: `tests/test_ts07_operation_keyed_requiredness.py` (9).

### TS-08 — EXPLORE (M), feeds E-8 · Component-state aggregation + unknown-outcome vocabulary (`BOOKING_EXCEPTION`) — **IMPLEMENTED 2026-09-10 (same session)**

Two halves, both landed: (1) **UNKNOWN outcome** — `IdempotencyStatus.UNKNOWN` in `src/agents/idempotency.py` (both backends): fenced `mark_unknown()` (PENDING→UNKNOWN), `resolve_unknown()` (fenced UNKNOWN→COMPLETED/FAILED after verification), acquire refuses UNKNOWN (never re-execute), TTL reclaim exempts UNKNOWN in both backends (the in-memory expiry-delete and the SQL guarded reclaim both skip it — the duplicate-side-effect hazard); fulfillment router classifies timeout/connection-class exceptions (`TimeoutError`/`OSError`) → mark UNKNOWN + 504 `outcome_unknown` (never re-run blindly), other failures stay FAILED+500; an UNKNOWN key on retry → 409 with verification guidance. (2) **Aggregation** — `JourneyDependencyGraph.aggregate_commitment()`: `PENDING_BOOKING / BOOKED / BOOKING_EXCEPTION / None` over per-node commitment statuses (void excluded; the tutor's flight✅hotel✅Disney❌ shape → BOOKING_EXCEPTION), surfaced as `commitment_verdict` on the journey-graph GET (stored nodes only, abstains without non-void nodes). Tests: `tests/test_ts08_unknown_outcome_and_aggregation.py` (20, incl. SQL-backend coverage on the documented SQLite/StaticPool pattern). **E-8 note:** the trip-level persisted-state wiring remains E-8's work; this lands the vocabulary + derivation the contracts addendum specifies.

### TS-09 — EXPLORE (S), fold into B6/B7 · Operation retry-safety registry

The tutor's table (search: auto-retry · WhatsApp: duplicate protection · charge/book: idempotency-only · cancel: very careful) has no repo equivalent: `idempotency_contract` is free-text prose per agent (`runtime.py:182`), tool contracts carry freshness but no safety class. Design: a small enum (`SAFE_RETRY / IDEMPOTENT_KEY_REQUIRED / MANUAL_ONLY`) on tool + provider-operation contracts, enforced at the call seam when live providers land (B6/B7). Pure vocabulary now; enforcement later. Also the natural home to record the read-vs-write boundary for the provider lane.

### TS-L1 status — promotion executed (2026-09-10)

The tutor's exercise happened and was answered (8/10). The corrected four-question contracts for `NEEDS_INFORMATION` and `BOOKING_IN_PROGRESS` are promoted as a dated addendum to `Docs/architecture/TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md` (spec input for E-8, with `required_for`/`blocked_operation` and the component-state model). TS-L1 closed. TS-L2 (next tutoring module: deeper queues/orchestrator/HTTP verb semantics) remains open — repo artifacts to use as worked examples: `src/agents/idempotency.py`, `agent_requeue_jobs.py`, lease heartbeat, fulfillment replay.
