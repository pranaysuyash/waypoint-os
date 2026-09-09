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

### TS-01 — IMPLEMENT (S per check, M total) · Hard itinerary-feasibility validators: the timing/transfer/capacity family

The tutor's canonical example — *flight lands 10:40, Disney booking 11:00, 70-minute transfer → a validator must reject it* — plus his validation list. Verified current state:

| Check | Status | Evidence |
|---|---|---|
| Flight connection MCT (hard) | ✅ exists | `src/decision/constraint_engine.py:165-232` (+ terminal MCT matrix `:48-83`; `src/logistics/connection_risk.py:334`) |
| Overlapping bookings / teleportation (hard) | ✅ exists | `constraint_engine.py:184-186` `SPATIAL_OVERLAP` |
| Passport validity vs destination (hard) | ✅ exists | `constraint_engine.py:230-252`; `spine_api/services/visa_radar.py` |
| Total cost ≤ approved budget | ✅ exists | budget gate (F-18 green honestly) |
| **Arrival→first-activity transfer buffer (hard)** | ❌ absent | `src/logistics/timed_entry.py:48-101` buffer is **advisory only** and not chained to flight-arrival nodes |
| **Hotel check-in time vs arrival** | ❌ absent | `HOTEL_CHECKIN` is a node type only (`src/schemas/journey_graph.py:23`), no check-in-time validation |
| **Hotel occupancy vs party size (hard)** | ❌ absent | `src/logistics/rooming_list.py` allocates rooms, never validates against max-occupancy |
| **Child-age rules vs fare/product** | ❌ absent vs fares | child-age enforced vs *activities* only (`src/suitability/models.py:37-38`); `src/distribution/fare_rules_engine.py` is markup/ADM risk only |

Canonical home: extend `src/decision/constraint_engine.py` (beside MCT/overlap/passport) so every validator family lives in one engine; chain `timed_entry` buffers to flight-arrival journey nodes. Pure deterministic, provider-independent, fully testable — **the highest-value transcript item and the recommended next unit**. Aligns with the doctrine line the tutor emphasized: *use AI for ambiguity, deterministic software for truth you can calculate.*

### TS-02 — EXPLORE (S) → IMPLEMENT later · Quote-freshness / recheck-before-execution contract

The tutor's `APPROVED → freshness recheck → if materially changed, back to AWAITING_CUSTOMER_APPROVAL` state has a token but no logic: `revalidate_quote_before_payment` exists only as a next-action priority-band entry (`src/orchestration/travel_next_action.py:18`, band 60); fulfillment charges the stored `selected_total_price_usd` with **no staleness gate** (`src/orchestration/booking_fulfillment.py:202,318`); `price_lock_expires_at` is written/read but the endpoints are preview-only (A5 reclassified). Explore-first because "stale" needs defining for simulated inventory (deterministic preview = no real rate to recheck); the real recheck lands with a live rate source. Fold the design into **B6/B7 provider work** and ADR-008 money rungs. Output: a freshness contract doc (what TTL, what delta counts as "materially changed", which rung blocks execution).

### TS-03 — EXPLORE (M) → IMPLEMENT (M-L) · Multi-modal intake completion

The transcript's input model — *raw messages, attachments, voice notes, links* — is the demand-capture funnel for the **D-01-decided open verifier + marketplace**, and it is the weakest intake surface today:

- **Images/PDF:** real vision extraction exists (OpenAI + Gemini, `src/extraction/vision_client.py:238-250`) but only via the **operator** trip-documents flow (`spine_api/routers/trip_documents.py:225,484,649`); the customer-message path (`src/intake/` inbound parse) is text-only. `/api/v1/multimodal/image-ocr` accepts only **pre-OCR'd text** (`spine_api/routers/multimodal.py:211-258`).
- **Voice:** no ASR anywhere; `voice-note` endpoint and `process_voice_memo` both require a pre-supplied transcript (`multimodal.py:161-208`, `src/intake/audio_intake.py:50`). WhatsApp webhook handles delivery statuses only, no inbound media (`spine_api/routers/messaging.py:125-166`).
- **URLs:** no fetching of customer-shared links anywhere in intake (URL fetching exists only in agent live-tools / public checker).

Explore first: modality priority for an Indian proprietor-agency funnel (screenshot of a competitor quote is likely #1), ASR provider DECIDE (Whisper vs Deepgram vs WhatsApp-native transcripts), **SSRF allowlist design for URL fetch** (directly adjacent to the open Mimosa SSRF findings on fetch surfaces), PII posture for voice/images. Then implement by extending the existing vision/trip-documents lane into the customer inbound path rather than building a parallel one.

### TS-04 — EXPLORE (S-M) · Provenance actor vocabulary for tool/provider writes

`_field_provenance` models only operator/customer actors (`spine_api/services/field_merge.py:20-36`); packet-level provenance is rich but tool/provider-sourced writes to trip state don't uniformly carry per-field provenance. The tutor: *"the proposal must retain provenance to the authoritative source behind each important fact."* Design: extend the actor vocabulary (tool/provider/system subclasses) or route provider writes through evidence packets so the two provenance systems converge.

### TS-05 — EXPLORE / design-note (park until real providers) · Pipeline parallel orchestration & speculative execution

`run_spine_once` is strictly sequential (Phase 1 extraction → … → Phase 10 fixture compare, `src/intake/orchestration.py:181-614`); no fan-out, no speculative execution, no downstream cancellation anywhere (asyncio.gather exists only in the stress simulator). The tutor's decision checklist is the design brief: *parallelize independent work when expected latency benefit exceeds expected cost of wasted work* — as a function of latency, API cost, gate-failure probability, wasted-work consequence, downstream reusability, UX. **Honest recommendation: park.** Today's pipeline is local-deterministic + one LLM extraction call; parallelism buys little and adds cancellation complexity. Value arrives when external provider tools land (B6/B7) — e.g. entry-check as a cheap early gate with speculative flight/Disney feasibility in flight, cancel-on-gate-fail. Reconcile with `MULTI_AGENT_RUNTIME_ROADMAP.md` Layer 3 (durable orchestration = queues/retries/outbox, a different axis than intra-pipeline parallelism).

### TS-06 — EXPLORE (S) · Candidate route-structure planning with incremental refinement

Tutor's weakest-score area in the owner's answer: route design has hard deps (cities, duration, party) and **soft deps** (exact flights, hotels) — the system should generate candidate structures (Tokyo 4N/Kyoto 3N vs 3N/4N) *before* exact flights and refine dramatically when flight data arrives (arrival Tokyo 10:00 / return Osaka 23:00 → open-jaw Tokyo→Kyoto→Osaka instead of backtracking). The route-feasibility matrix (`ROUTE_FEASIBILITY_AND_GEOSPATIAL_AVIATION_PIPELINE_2026-09-02.md`) **validates** routes (MCT, zigzag, transit visas) but does not **generate/refine candidate structures** under soft dependencies. Verify what Phase 4.6 plan-candidate (`orchestration.py:528`) does today, then design the incremental-refinement seam.

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
