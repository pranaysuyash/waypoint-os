# Incoming Work Classification Map — first-principles taxonomy of everything that arrives (2026-10-24)

**Author:** ZCode (classifier pass) · **Status:** current-state map + separately-mapped should-be register
**Method:** read-only sweep from the app root — `spine_api/server.py` (93 router mounts, counted 2026-10-24), `frontend/src/app` (52 pages, counted), the canonical map ([CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03](CODEBASE_FEATURES_FLOWS_LOOPS_MAP_2026-09-03.md) + addenda through 2026-10-21), the [Long-Term Structural Roadmap](LONG_TERM_STRUCTURAL_ROADMAP_2026-10-23.md), and endpoint greps of the newest routers (`messages`, `public_asks`, `dsr`, `feedback`, `customer_memory`, `inbound`, `messaging`, `message_triage`, `rag`).
**Companion:** this doc classifies *work arriving at the product*; the roadmap classifies *structural defects*. They meet in §5.

---

## 1. First-principles taxonomy: what kinds of work can arrive at a travel agency

A travel agency is a work-processing system. Stripped to first principles, **work = an event that obligates the system or an operator to act**. Every such event decomposes along these axes:

**Origin (who/what produced the obligation)** — five classes, and every door in §2 maps to exactly one:

| Class | Origin | Who is the principal |
|---|---|---|
| **W1 Demand** | Traveler or their proxy (EA, family, corporate booker) | The traveler |
| **W2 Supply** | Fulfillment parties (DMC, hotel, airline, GDS, sub-agent, insurer) | The vendor |
| **W3 Operator** | Agency staff acting inside the app | The agency |
| **W4 System** | Autonomous generation (loops, monitors, deadlines, evals) | The system itself |
| **W5 World** | External events & channels (webhooks, disruption feeds, FX moves, regulatory clocks, GDPR retention) | Nobody — the world |

**Axes the system must classify every item on** (these are the routing inputs, and each one already exists somewhere in the codebase — the gap is that they are scattered):

1. **Authority rank** of the payload's assertions — `explicit_user > operator > profile/memory > inferred > estimated`. (Exists as slot epistemic status; invariant 2 wants it on every writer.)
2. **Intent type** — `new_demand | supply_info | answer | decision/approval | exception/disruption | query | meta` (settings, knowledge, memory, evals).
3. **Entity binding** — agency | customer-profile | lead/draft | trip | proposal | claim | none.
4. **Urgency/SLA** — the urgency signal is *extracted* (S0) but never *ranked into a queue*.
5. **Epistemic status** — explicit fact vs inference vs estimate vs fabricated-risk (invariant 3: "no number without a basis").
6. **Money boundary** — tracking-only vs money-touching (owner constraint: the system NEVER moves money; ADR-008 rungs).
7. **PII class / retention posture** — feeds R-15, DP-03a/b, DSR.
8. **Terminal vs continuous** — one-shot request vs standing monitor (perishable sentinel, disruption radar).

---

## 2. The doors: entry-surface inventory (runtime truth, from the app root)

### 2.1 W1 Demand-side doors (the strongest lane)

| Door | Surface | What arrives | Feeds |
|---|---|---|---|
| Operator-typed note | `POST /run` (inline, `server.py`) → workbench Intake tab | raw_note ≤100k, stage, hints | full 12-phase spine |
| Inbound parse | `POST /api/v1/inbound/parse` (`routers/inbound.py:193`) | channel note → draft | draft → promote → spine |
| Social/anonymous | `POST /api/v1/inbox/parse_social`, `POST /api/public-checker/run` | anonymous lead | spine (checker lane) |
| Fast intake UI | `/intake/fast` page + `/corporate/offsites` | form intake | (offsites = fixed fabrication defect) |
| Channel webhook | `POST /api/v1/messaging/webhook/{provider}` (`routers/messaging.py:134`) | provider reply, idempotent per `message_id` | message store → inbox feed |
| Traveler answers | `POST /api/public-asks/{token}/answers` (`routers/public_asks.py:178`) + `/a/[token]` page | answers to asks | `_apply_answers_to_facts` → reassess (closed loop) |
| Booking data + docs | `booking-collection/[agencyId]/[token]` page → collection tokens | passports, PAN, payment data | pending_booking_data accept/reject |
| Proposal decision | `p/[token]` view/calculate/accept (e-sign) | traveler's pick + consent | proposal acceptance state |
| Group deposit share | `g/[token]` | co-traveler share decision | group ledger |
| Voice | multimodal router + `voice_copilot` | transcript | intake packet |

### 2.2 W2 Supply-side doors (the hollow lane)

`supplier` (contracts store), `gds_sandbox` (Amadeus/Sabre **sandbox**), `negotiation` (engine, no real counterparty), `commission`/`subagent_payouts` (in-memory ledgers), `distribution` (PREVIEW_ONLY). **No real vendor-facing door exists**: no supplier quote inbox, no vendor booking-confirmation ingest, no commission-statement ingestion. Every W2 arrival today is either operator-keyed or simulated.

### 2.3 W3 Operator doors

Workbench CRUD: trips/[tripId] stage tabs (intake repair / packet / strategy / suitability / decision / output / ops / timeline / followups / safety), `drafts` promote, `trip_lifecycle` reassess + PATCH (explicit field clears), `trip_actions`, `trip_history` undo/redo, overrides (`legacy_ops` decision cache), claims PATCH (`claim_disposition` 8-state), settings (30 endpoints), team/assignments, `customer_memory` (`/remember`, `/memory/ingest`, `/hydrate-trip/{trip_id}`), `rag` documents/index + nodes/edges (knowledge corpus), accounting export, DSR export/erasure, stress/eval tools.

### 2.4 W4 System-generated doors (loops — the invisible workforce)

From the map §6 + runtime: requeue worker (5s), recovery agent (300s), agent supervisor ticking FrontDoor/SalesActivation/FollowUp/QualityEscalation/DocumentReadiness/DestinationIntelligence/WeatherPivot agents (300s), zombie reaper (5s), integrity watchdog (600s), stale-run sweep (poll-driven, 300s), perishable sentinel (visa/ticket/deposit deadlines), ghost concierge monitor (`ghost_concierge_monitor.py`, DRAFT_AWAITING_OPERATOR — honest telemetry), pre-departure cadence D-7/D-3/D-1, retention enforcer, DLQ inspector. Each generates operator-facing work through: escalated queue, DLQ, notifications, drafts.

### 2.5 W5 World doors

Channel webhooks (§2.1), disruption feeds (`disruption_radar` — no live provider), FX (`fx_sentinel` — preview), visa registry (`visa_radar` — registry-driven), regulatory clocks (GDPR retention/DSR), market/season data (seasons page). Honest status: **mostly preview/simulated**; the only live world-door is the messaging webhook seam + public-checker's Open-Meteo enrichment.

### 2.6 Frontend surface reality (52 pages)

- Operator: `(agency)` group — 31 pages incl. workbench (canonical), `/inquiries/new` (duplicate route, catalogued A2), `/quotes` (sample-data problem, A3), overview/inbox/trips/payments/audit/insights/knowledge(-base)/seasons/suppliers/settings/reviews/documents/bookings/platform-admin.
- Traveler/public: `/a/[token]` (asks), `/p/[token]` (proposals), `/g/[token]` (group), `booking-collection`, `companion` + `itinerary-checker` (traveler surfaces), auth group, marketing (`/`, `/pricing`, `/terms`, `/privacy`).
- Known debt: `/v2..v5` prototype routes (A6-class), `corporate/offsites`, `intake/fast`.
- BFF deny-by-default route map (`src/lib/route-map.ts`) is the product reachability gate — exactly the 11-door parity gap FND-0340 closed with CI.

---

## 3. The spine: one pipeline, stage by stage — internal behavior + actual user flow

All W1 work converges on `run_spine_once` (`src/intake/orchestration.py:187`; 12 phases, map §2.1). Unified stage map (S-numbers mine, phases in parens):

| Stage | Internal (what happens) | Actual user flow (who sees what) |
|---|---|---|
| **S0 Ingest/Identify** | door adapter → envelope; identity harvest `_resolve_existing_lead`; draft created | Operator pastes note in Intake tab (or webhook/answer lands); draft autosaves 5s |
| **S1 Extract** (phase 1) | regex-only extractors → `CanonicalPacket`; GeoNames gazetteer; epistemic provenance | invisible to user — this is where fabrication defects lived (0329/0333, fixed) |
| **S2 Validate/Gate NB01** (2–3) | INTAKE_MINIMUM/QUOTE_READY; ESCALATE persists incomplete lead (never clobbers); DEGRADE partial + follow-ups | Operator sees run progress panel; blocked → repair banner deep-links `/trips/{id}/intake?repair=<field>` |
| **S3 Decide** (4–6) | ambiguity/budget/MVB → DecisionState; NB02+D1 autonomy rungs; suitability can force STOP | Decision tab renders verdict + reasons; overrides recorded → override learning |
| **S4 Enrich** (7–9) | frontier orchestration (gated), strategy, fees, plan candidates | Strategy/suitability tabs; Yield/panels for the domain work |
| **S5 Output** (10–11) | traveler-safe bundles, leakage scan, readiness tiers (never auto-advances stage) | Output tab; readiness chips; quotes read model derives only from persisted strategy |
| **S6 Traveler loop** | asks dispatched (purpose-scoped tokens) → answers written as explicit_user slots → reassess | Traveler answers on `/a/[token]`; answers now consumed (closed-loop test landed) |
| **S7 Book/collect** | proposal compiler (deterministic_preview) → `p/[token]`; price lock 72h; collection tokens → docs (magic-byte validated); booking_tasks; confirmations extract/verify/void; payments **tracking only** | Traveler accepts + e-signs, submits docs via collection link; operator accepts/rejects pending data; tasks reconcile |
| **S8 In-trip** | disruption radar, IROPS healer (counterfactual 3-tier), ghost concierge (drafts-only), duty-of-care/crisis (preview), claims disposition 8-state | Ops tab; claim letter cites the statutory resolver; VCC issuance gated DRAFT_AWAITING_OPERATOR (AUD-17) |
| **S9 Post-trip** | feedback survey/scorecard, loyalty, memory write-path (5-tier graph), accounting export (E08), DSR Art.15/17 | Reviews/insights pages; customer memory visible via `/memory` endpoints; DSR from trip page |
| **S10 Meta-loops** | eval flywheel (D6 gates), override learning, autoresearch, watchdog, retention | CI gates; system dashboard; findings store (the repo's own flywheel) |

---

## 4. Coverage matrix — work class × lifecycle (LIVE/PARTIAL/GATED/SIM/MISSING)

| Work class | Ingest | Decide | Traveler loop | Book | In-trip | Post-trip |
|---|---|---|---|---|---|---|
| W1 new demand (note/web) | **LIVE** | **LIVE** (deterministic; hybrid GATED) | **LIVE** | **LIVE** (tracking-only) | — | — |
| W1 answers/decisions | **LIVE** | **LIVE** (post-0351) | **LIVE** | LIVE | — | — |
| W1 channel replies (WhatsApp/email) | webhook seam LIVE, **real channels MISSING** | rides spine | LIVE | — | — | — |
| W1 attachments/documents | **LIVE** (MRZ, magic-bytes, extraction provider-gated) | — | — | LIVE | — | — |
| W2 supplier quotes/confirmations | **MISSING** (sandbox/sim only) | — | — | PARTIAL (confirmations operator-keyed) | — | commission ledgers **in-memory** |
| W2/W5 disruption events | door **MISSING** (no live feed) | — | — | — | engines LIVE, input SIM | claims LIVE (statutory resolver) |
| W3 operator edits/overrides | **LIVE** | LIVE | — | LIVE | LIVE | LIVE |
| W3 knowledge/memory admin | **LIVE** (RAG, custmem) | — | — | — | — | LIVE |
| W4 system-generated operator work | loops LIVE | — | — | — | drafts-only monitor LIVE | retention PARTIAL |
| W5 regulatory (GDPR/DSR) | LIVE | — | — | — | — | **LIVE** (Art.15/17) |
| W5 FX/market | — | — | — | FX **preview** | — | — |
| Cross-cutting: known-traveler recognition | identity harvest LIVE, **memory→intake injection MISSING (U13)** | — | — | — | — | — |
| Cross-cutting: dedup across doors | draft 1:1 + idempotency LIVE, **cross-channel same-traveler dedup MISSING** | — | — | — | — | — |
| Cross-cutting: urgency-ranked operator queue | urgency extracted, **queue ranking MISSING** | — | — | — | — | — |

---

## 5. The Should-Be Map (separately mapped — what I'd change, and why)

Ordered by structural leverage; each ties to the roadmap invariants (I1–I5) where applicable.

### A. The classification gap itself (biggest first-principles finding)

**A1 — There is no single work-intake contract; there are ~10 parallel doors each with its own parse path.**
`/run`, `/inbound/parse`, `parse_social`, public-checker, webhook, asks-answers, collection, `message_triage`, `customer_memory/ingest`, `rag/index` all normalize differently before converging. First principles: classification is a *choke point*, not a per-door activity. **Proposal:** one `WorkItem` envelope at the ingest seam — `{origin_class, intent, entity_binding, authority_rank, urgency, money_touch, pii_class, payload}` — with thin door adapters, recorded in the run ledger, consumed by routing (queue, autonomy rung, retention). This is the intake-side mirror of I2's fact-store merge and would have made FND-0326/0328/0340 structurally impossible. Effort M; rides I2's schema pass.

**A2 — Authority rank is a slot concept but not a door concept.** An operator PATCH, a traveler answer, and a webhook reply should enter with different authority the way invariant 2 specifies for facts — generalize to the item level, not just extracted facts.

### B. Missing doors (work classes with no real entry)

**B1 — Channel ingestion (WhatsApp/email).** The single highest-volume real door for the target market (Indian leisure/VFR agencies) does not exist as a live door; the webhook seam + jev E2 probe (1.000/1.000) prove it's buildable. Everything else in W1 is polished behind a door travelers mostly won't use. **This is the biggest product-side gap.**

**B2 — Supply-side ingestion.** No vendor quote inbox, no supplier booking-confirmation ingest, no commission statements. The system is demand-complete, supply-hollow — quotes/booking/money stages all depend on operator keying. First proposal compiler → supplier round-trip would unlock the `preferred_supplier`/`network` sourcing tiers that today stub to `network`/`open_market`.

**B3 — Live event feeds (disruptions, FX).** S8 engines are built and idle on simulated input; the work class "the world changed" has no live door. Each is a producer decision (roadmap "out of scope" list) — but the *classification* should reserve the door now so feeds plug into the same WorkItem seam.

### C. Classification dimensions computed but not consumed

**C1 — Urgency → queue ranking (missing).** Urgency is extracted at S1; nothing ranks operator work by urgency/value. The inbox read-model projects trips, not a prioritized work queue. This is the operator-side payoff of classification.
**C2 — Known-traveler recognition (U13).** Identity is computed; `CustomerMemoryProfile` exists; the run path doesn't inject it (I2 step 3). Returning guests start from zero every door.
**C3 — Cross-channel dedup.** Same traveler, two doors (web form + WhatsApp when B1 lands) = two leads; needs the WorkItem identity key (A1).

### D. Structural items already on the roadmap (endorsed, not restated)

I1 persistence boundary (encryption-as-boundary + token table), I2 fact-store merge + projection (retires display-lag), I3 basis-enforced schemas, I4 closed-loop CI (shipped=reachable+consumed), I5 failure flywheel. **Endorse the sequencing** (Phase 1 = I3 money cluster first). A1/A2 should be folded into Phase 2 (I2) as its intake-side counterpart; C1/C2 are cheap riders on the same pass.

### E. Smaller should-be-betters (from this pass, not yet registered anywhere)

- **E1** `/intake/fast` + `/corporate/offsites` + `/v2..v5` pages still exist as doors with known fabrication history — fold into the route-grammar cleanup the UI council started (A2/A6 classes).
- **E2** `message_triage` is a single endpoint answering one message; it should classify *into the queue* (C1) rather than return an advisory — it's the natural first consumer of the WorkItem contract.
- **E3** W4 system-generated work lands in scattered places (escalated queue, DLQ, notifications, drafts). One operator work queue should consume all of it — the inbox projection is the right home.
- **E4** The claims/disposition lane (S8→S9) is genuinely strong (statutory resolver + 8-state machine) — it's the template for how every exception class should look: single authority, basis-cited, operator-gated.

---

## 6. Discussion

The system's center of gravity is correct: **one deterministic spine, authority-ranked facts, gates that escalate rather than fabricate, money that is tracked but never moved.** The Sim #2–4 arc + council waves fixed the lying; the roadmap fixes the leaking and the lagging. What no pass has yet named is that **intake itself is unclassified**: work arrives through ten doors with ten normalizations, three persistence stores (I1's evidence), and no shared notion of who the item is from, what it wants, how urgent it is, or what it may touch. Every major finding class of the last six weeks (PII in three stores, answers unconsumed, doors unreachable, display lag) is a symptom of a missing classification choke point, which is why A1 is the recommendation I'd put alongside the five invariants — as invariant 2's other half.

Practical order I'd argue for: roadmap Phase 0 (DP-03 owner calls) → Phase 1 (I3) unchanged → **Phase 2 = I2 + A1/A2 + C1/C2 as one "intake & facts" pass** (they share the schema edit sessions and the same tests) → Phase 3 (I1) → Phase 4/5. Product-side, B1 (WhatsApp door) is the only item I'd pull forward independently of the structural work — it has the highest real-world value per unit of effort and lands entirely behind the existing webhook + WorkItem seams.

## 7. Not verified here / open

- Live status of hybrid engine posture and RAG egress toggles is env-dependent (`.env`); read at deploy time, not from this doc.
- The working tree is hot (memory/custmem lane in flight: `spine_api/contract.py`, `persistence.py` modified; `tests/test_probe_mem.py` untracked). This map reflects the tree as of 2026-10-24; the memory lane may add doors — re-sweep §2 before citing after that lands.
- Feature counts (93 mounts / 52 pages) are mine, counted today; the FEATURE_LIST_V3 status counts (93 LIVE/…) are a different enumeration (features, not surfaces).

---

## 8. Implementation record (2026-10-24, same session — A1/A2/C1/C2/C3/E2 SHIPPED)

Owner directive "continue and do all" executed. **FND-0371 registered and closed with this evidence.**

### Shipped

| Item | What | Where |
|---|---|---|
| **A1/A2** | Canonical work classifier + append-only store: origin/intent/authority/urgency/entity/money/PII axes; door registry with reserved seams (`whatsapp_channel`, `vendor_quote_inbox`, `disruption_feed`); door-level authority (`/run`→operator, channel/asks→explicit_user) | `spine_api/services/work_intake.py` (new) |
| **C1** | Urgency-ranked operator queue endpoint with honest counts (`count_basis: work_item_log_total` — invariant-3 style) | `spine_api/routers/work_items.py` (new) → `GET /api/v1/work-items`; mounted in `server.py` |
| **C2** | Returning-guest annotation at intake: contact → canonical `cust_` entity id → durable memory read (`memory_on_file_facts`); surfaced on the queue, **never written into the packet** | inside `classify()`; all wired doors + triage |
| **C3** | Agency-scoped SHA-256 `identity_key` (never raw contact) + 24h `duplicate_of` flagging; public `duplicate_risk()` preview seam | `work_intake.py` |
| **E2** | Triage consumes the canonical classifier (preview-only, no recording): `work_origin/work_authority/urgency_class/identity_known/returning_customer/duplicate_risk` on `MessageTriageResponse` | `spine_api/routers/message_triage.py` |
| Doors wired | `/run` (single call site in `_launch_spine_pipeline_thread`, both idempotency branches), `POST /api/v1/inbound/parse`, `POST /api/v1/messaging/webhook/{provider}` (per inbound record), `POST /api/public-asks/{token}/answers` | `server.py`, `inbound.py`, `messaging.py`, `public_asks.py` |

### Design decisions (recorded)

1. **C2 boundary honored, not overridden.** The roadmap's U13 slot-injection (authority_level "profile" below explicit_user) collides with the **ratified** ADR-008 §7 row 4 / E-D §3 slot 2 display-only contract (`customer_memory.py:400-407` states the packet-mutating path is forbidden). Shipped the contested-state-safe cut: returning-guest is queue/display metadata read through the same entity-id convention the remember path writes (`traveler_entity_for`); slot injection stays roadmap Phase-2 (Invariant 2) work with its own owner gate.
2. **No PII in the store — structurally.** Records carry a one-way `identity_key` and derived flags only; the raw text/contact never lands in `data/work_items/*.jsonl`. Test-proven by content assertion (S3): stored bytes contain neither the seeded email nor the phone.
3. **Classification is best-effort by contract** — every door wraps it in try/except; a classification failure can never fail a door (mirrors the run-meta enrichment pattern).
4. **Router-local response models** (message_triage precedent) — no `contract.py` churn while that file is a live lane; promotion to `contract.py` can ride the I2/I3 schema pass.

### Evidence (doctrine §3 labels)

- Tests: `tests/test_work_intake.py` **14/14** — door contracts, unknown-door rejection, identity normalization/stability/scoping, urgency heuristics, **no-PII-persisted (S3 content check)**, **C3 dedup S2+S3** (same-contact flags; intent mutation un-flags), C2 via memory-seam, **C1 ranking S3** (insertion order ≠ rank order), tenant isolation, **closed-loop Tier-3**: inbound/parse → queue surface changes; webhook → queue; triage carries axes and persists nothing.
- Regression: route/OpenAPI snapshots regenerated via `scripts/snapshot_server_routes.py --write` (398→399 routes, only `/api/v1/work-items` added); parity suites green (`test_server_route_parity`, `test_server_openapi_path_parity`, `test_bff_parity_gate`); `test_inbound_router`, `test_messaging_router`, `test_public_asks`, `test_live_triage`, `test_customer_memory_router` green; `uv run ruff check --fix .` → **All checks passed**.
- `/run` door wiring is **Tier 1** (shared single call site; the same record path is Tier-2/3-proven at three other doors; a full `/run` POST test would drag the pipeline thread into the suite — deferred).
- Residue note: suites that exercise the wired webhook door write benign classified records to `data/work_items/` (same posture as `data/messages/`; no PII possible by design). Cleaned once; expect it to re-appear as test data accumulates.

### Not shipped (still open, owner-gated or producer-gated)

- **B1** WhatsApp live channel (needs provider creds/decision; seam reserved), **B2** vendor quote inbox, **B3** live disruption/FX feeds (producer decisions per roadmap out-of-scope list).
- **E1** route-grammar cleanup (`/intake/fast`, `/v2..v5`, `/quotes` sample data) — deletions need the supersession workflow + owner sign-off; not bundled here.
- **E3** W4 unification (loops → same queue) — store + endpoint are the seam; loop writers not yet wired.
- I2 generalization: `merge_facts` + projection (roadmap Phase 2) — the WorkItem contract is its intake-side counterpart, ready to fold in.

