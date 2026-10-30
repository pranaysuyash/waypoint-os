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

---

## 9. Independent verification pass + E3 implementation record (2026-10-24, later same day)

Two read-only Explore agents (the ones that failed at session start; relaunched) independently verified §2 and the frontend surface inventory. Verdicts and deltas:

### 9.1 Backend verification (Observed)

- **94 router mounts** confirmed at `server.py:1576-1697` (93 at map time + the new `work_items` mount); 63 carry include-level `_auth_or_skip`, 31 rely on in-file agency auth; three modules mount twice (public + authed variants). The real public gate is the middleware allowlist at `core/middleware.py:31-53`.
- **All four door wirings verified live**: `run` (`server.py` `_launch_spine_pipeline_thread`), `inbound_parse` (`inbound.py`), `channel_webhook` (`messaging.py`, per record), `ask_answers` (`public_asks.py`) + `triage_preview` classify-only. Store no-PII and `count_basis` honesty re-confirmed.
- **Registered-but-unwired doors** (the next wiring tranche, in value order): `collection_submit` (`public_collection.py:146`+documents), `proposal_acceptance` (`public_proposals.py` calculate/accept + trust-scorecard 1-click at `:349`), `group_share` (`group_booking.py:214`), `public_checker` (`run` at `server.py:2144` — persists under the checker agency), `operator_action` (PATCH `/trips` auto-reassess), `knowledge_admin` (`rag` index/nodes/edges). Doors with NO registry entry yet: `inbox/parse_social` (`social_inbound.py:77`), `public_checker/route-request` (consented lead capture), multimodal voice/OCR, IVR status webhook (logs-only today).
- **Corrections to §2.4**: the **perishable sentinel has no live callers** (dormant; `audit_perishables()` uninvoked) — it should not be counted as an active loop; **ghost concierge is event-driven, not a loop** (fires on `PATCH /trips` flight-status changes `server.py:2996-3006` and on webhook traveler messages `messaging_webhooks.py:101`). The IROPS watch loop is operator-started (`POST /irops/watch/start`), not lifespan-scheduled.

### 9.2 Frontend verification (Observed)

- 52 pages confirmed; the workbench tab set, traveler token surfaces (`/a /p /g`), and BFF deny-by-default allowlist (`route-map.ts`) all match §2.6.
- **Finding: `GET /api/v1/work-items` was backend-only** (absent from `route-map.ts`) — the exact shipped-but-unreachable class invariant 4 exists to kill. **Fixed this pass**: `v1/work-items` added to `frontend/src/lib/route-map.ts`; `tests/test_bff_parity_gate.py` green. (No FE UI consumes it yet — reachable, not yet rendered; a queue panel is the natural next FE tranche.)
- Additional structural gaps the pass surfaced for the E1 cleanup tranche: three **BFF bypasses** call the backend origin directly (`/intake/fast` → `inbox/parse_social`, `/corporate/offsites` → hardcoded sample IDs, `booking-collection` via `SPINE_API_URL` in `api-client`) — holes in the F-43 allowlist posture; `/bookings` page is self-described sample-preview; dev-session backdoor in `(agency)/layout.tsx` fabricates an admin session in non-prod.
- **Pre-existing drift recorded, not touched**: HEAD fails `tsc` with 6 TS2322 errors in `overview/__tests__/EmptyStateOnboarding.outcomes.test.tsx` (parallel lane's committed wave `63e95b24`; noted on **FND-0359**). This session's only FE edit (`route-map.ts`) is clean.

### 9.3 E3 shipped (W4 system work joins the queue)

- New doors `ghost_concierge` and `requeue_poison` (origin=system, intent=exception, authority=system) in `DOOR_CONTRACTS`.
- **Ghost concierge → agency queue**: `run_ghost_concierge_for_trip` records a high-urgency system item whenever draft interventions exist (`ghost_concierge_monitor.py`); healthy evaluations record nothing (noise guard, test-proven).
- **Poison → `SYSTEM_WORK_SCOPE`**: `_emit_poisoned_side_effects` records under `__system__` — deliberately NOT on any tenant queue, preserving the agency-less ownership boundary the requeue store documents (`list_poisoned`). Error text never enters the record (context stays in audit + DLQ).
- Tests: `tests/test_work_intake.py` now **17/17** (three new: system-door contracts, ghost-concierge closed loop + healthy-trip S3 guard, poison system-scope + tenant-isolation S3). Regression: requeue/poison/recovery/ghost suites **79 passed**; ruff clean.
- Still unwired W4 sources (next tranche): recovery-agent escalations, supervisor agent events, IROPS watch detections, stale-run sweeps — the store and scope pattern are established.

---

## 10. Second door tranche + HEAD un-red (2026-10-24, third pass)

### 10.1 All six §9.1 unwired doors are now WIRED

`collection_submit` (`public_collection.py` submit), `proposal_acceptance` (`public_proposals.py` accept — `money_touch=True`, the PA-02 authorization artifact), `group_share` (`group_booking.py` pay-share, `money_touch=True`), `public_checker` (`public_checker_service.run_public_checker_submission` — funnel visible on the checker agency's queue), `operator_action` (PATCH `/trips` auto-reassess trigger in `server.py`), `knowledge_admin` (`rag.py` documents/index). All best-effort try/except; no payload/PII crosses into records. Remaining un-registered doors: social inbound, checker route-request, multimodal, IVR webhook (next tranche).

**Door coverage now: 10 wired + triage preview + 3 reserved seams.** Tests: `tests/test_work_intake.py` **19/19** (new: six-door contract matrix; PATCH→operator_action closed loop with run linkage). Regression: collection/token-CAS/group/checker/proposal/rag/parity/route suites **167 passed**; ruff clean.

### 10.2 HEAD tsc failures fixed in-pass (FND-0359 noted)

Two committed drift instances, both fixed rather than deferred:
1. `EmptyStateOnboarding` — the `63e95b24` wave landed the outcomes-test spec without its component. Implemented the facts-driven outcomes mode to the committed test contract (activation facts, "N of 3 outcomes complete", single next-action CTA, recovery deep-link, **zero localStorage** — current agency facts outrank browser history); legacy no-props render preserved (old tests green); overview call site wired to derive activation from live counts.
2. `ConfirmationPanel` test fixture — `component_key: "primary"` added, matching the backend contract (always emitted, default `"primary"`).

**FE `tsc` exit 0**; 24/24 tests across the three affected files. Evidence noted on **FND-0359**.

---

## 11. Third tranche — every real door now classified (2026-10-24, fourth pass)

### 11.1 Wired

- **`social_inbound`** — `POST /api/v1/inbox/parse_social` (`social_inbound.py`): a social DM / fast-intake text is the traveler's own words (envelope `actor="traveler"`); the raw text feeds urgency heuristics only, the scrubbed pipeline path is unchanged.
- **`checker_route_request`** — `POST /api/public-checker/route-request` (`public_checker.py`): the WOBS P2 consent moment. ROUTED leads (matched agency) land on that agency's queue as real operator work; CAPTURED ones land on the checker agency queue. Contact hashes into `identity_key` (C2/C3 ride).
- **`multimodal`** (both legs) — `voice-note` (transcript feeds urgency only, never stored — test-proven) and `image-ocr` (no text passed at all: OCR output can carry document PII, so the urgency heuristic is deliberately skipped).
- **`recovery_escalation`** (W4 writer) — the PA-38 escalation mirror in `agent_runtime_adapters.py` records a high-urgency system item on the trip's agency queue right after the TripRoutingState mirror succeeds.

### 11.2 Deliberately NOT wired (recorded reasoning, not omission)

- **IVR status webhook** (`ivr_gateway.py:254`): logs-and-acknowledges only — no obligation attaches to the event, so per the map's own §1 definition (work = an event that obligates act) recording it would be noise, not classification. Revisit when the advisor push channel exists ("missing-for-upgrade" note in the router).

### 11.3 State after this pass

**Door coverage: 14 wired (run, inbound_parse, channel_webhook, ask_answers, collection_submit, proposal_acceptance, group_share, public_checker, operator_action, knowledge_admin, social_inbound, checker_route_request, multimodal×2) + triage preview + 2 W4 writers (ghost_concierge, requeue_poison, recovery_escalation = 3) + 3 reserved seams.** Every HTTP surface that accepts external input and creates an obligation now records exactly one classified WorkItem. Tests **22/22** (new: four-door contract matrix; multimodal closed loop incl. no-transcript-persistence; social closed loop incl. low-urgency detection); social suites 10 passed; ruff clean. Remaining W4 writers (supervisor agent events, IROPS watch, stale sweeps) and the FE queue panel (with full before/after visual protocol per doctrine §3) are the next tranches.

---

## 12. FE consumption tranche — the queue is now an operator surface (2026-10-24, fifth pass)

Invariant 4 ("shipped = reachable AND consumed") closes for the work-item store: the classified queue is rendered in the product, not just queryable.

### 12.1 Shipped

- **Route parity**: `v1/work-items` added to the BFF `route-map.ts` allowlist (frontend path `/api/v1/work-items` → backend `api/v1/work-items`); parity gate green. Route snapshot 398→399 (only the new route).
- **Client stack**: `frontend/src/lib/work-items-api.ts` (typed `WorkItemEntry`/`WorkItemQueueResponse`, `getWorkItems(limit=8)`) → `frontend/src/hooks/useWorkItems.ts` (TanStack Query, 30s staleTime) → `frontend/src/components/overview/WorkQueuePanel.tsx` mounted on `/overview` in `PageClient.tsx` (after the Start-Here card).
- **Panel contract** (display honors the store's semantics, extends none of them):
  - Ranked rows: urgency chip (HIGH=accent-red) + title; `returning` / `duplicate?` / `money` badges; subtitle `origin · intent · authority · channel · trip_id`.
  - Header: "Incoming Work" + `CLASSIFIED` badge + honest counters (urgent / returning / dup? / total) computed from the response totals, not the visible page.
  - Footer: "Showing N of M · totals count the append-only work log" — the `work_item_log_total` count-basis honesty rule surfaced verbatim in the UI.
  - Empty / loading / error-degraded states (error never blanks the page).
  - C2 boundary respected: `returning_guest` renders as annotation only; no slot/packet mutation anywhere in the FE stack.
- **Tests**: `WorkQueuePanel.test.tsx` 3/3 (rows+badges+counters, empty state, error degradation) — mocked to the REAL backend response shape (contract-first rule). `tsc` exit 0; **ESLint clean** on all four new FE files.

### 12.2 Visual evidence (doctrine §3 — inspected, not assumed)

Files under `Docs/sims/assets/overview/`:

- `work-queue-before-2026-10-24.png` — panel temporarily stubbed; no "Incoming Work" section anywhere on /overview (verified by inspection: nav rail, Action Required, Start Here, stat cards only).
- `work-queue-after-2026-10-24.png` — full page with the panel live (below the fold: header + CLASSIFIED badge + "2 urgent" chip visible).
- `work-queue-after-clean-2026-10-24.png` — element capture of the panel after dismissing the (pre-existing, unrelated) Welcome onboarding modal. Verified contents, top-down:
  1. **Ghost Concierge** — HIGH — `system · exception · system` (+trip) — the seeded urgent system exception ranks first.
  2. **Channel Webhook** — HIGH — `demand · new_demand · traveler · channel:web` — urgency heuristic fired on the message text.
  3. **Proposal Acceptance** — NORMAL — `money` badge, `demand · confirmation · traveler`.
  4. **Inbound Parse** — NORMAL — `duplicate?` badge (C3 dedup window flagged the re-send).
  5–8. Remaining NORMAL rows (inbound parse, knowledge admin, social inbound×2) in recency order.
  - Counts line `2 urgent · 1 dup? · 24 total` matches the seeding command output (`total 24 high 2 dupes 1`) exactly; footer `Showing 8 of 24 · totals count the append-only work log`. No undefined/blank/clipped rows; no error state.

Seeding was additive (`classify_and_record` calls on the live dev backend for agency `d1e3b2b6-…bf5b`; no store resets). Both dev servers left running for live preview (backend :8000, frontend :3005).

### 12.3 Remaining (unchanged gates)

Remaining W4 writers (supervisor agent events, IROPS watch detections, stale-run sweeps); owner-gated E1 (route deletions + BFF bypass holes); provider-gated B1–B3 (WhatsApp / vendor quote inbox / live feeds); I2 `merge_facts` generalization (roadmap Phase 2). A natural follow-on now unblocked: an operator action surface on top of the queue (claim/dismiss per item) — deliberately NOT built here; it needs outcome-state semantics on WorkItem (`record_outcome` exists but there is no claimed/dismissed lifecycle state yet).

---

## 13. Final W4 tranche — every system obligation source is wired (2026-10-24, sixth pass)

The last three W4 writers from the Should-Be register are wired; the W4 class is now fully covered with no unwired sources.

### 13.1 Wired

- **`disruption_feed`** (was a reserved seam; now wired by the in-tree producer) — `irops_watch_service._scan_trip` records one world-origin high-urgency item per detected disruption, right after the healing plan is persisted and audited. The reality tier (`deterministic_preview`) lives on the healing plan; the operator obligation to review the plan is real regardless, so it classifies now. The live flight-status upgrade (B3) rides the same door with zero further wiring.
- **`supervisor_escalation`** — `AgentSupervisor.run_once` records a system/exception item when a work item terminally poisons (`AGENT_ESCALATED`). Unlike the agency-less requeue queue, supervisor items carry a `trip_id`, so the item lands on the trip's agency queue (tenanted); unresolvable trips fall back to `SYSTEM_WORK_SCOPE`. Failure reasons stay in audit/DLQ — never in the classified record.
- **`stale_run_timeout`** — `RunLedger._timeout_scan` records one item per run it sweeps to FAILED, attributed from the run's own `meta.agency_id` (tenanted — the sweep is triggered opportunistically on the run-status GET but can time out ANY agency's run, so attribution must come from the run, not the caller). Agency-less runs fall to `SYSTEM_WORK_SCOPE`. Only fires on the queued/running→FAILED transition, so terminal runs never re-record.

### 13.2 Deliberate boundaries kept

- Supervisor escalation ≠ requeue poison: same exception class, different ownership contract — the requeue queue is agency-less by design (list_poisoned boundary), the supervisor's is trip-tenanted. Two doors, not one overloaded one.
- No text/payload crosses into any of the three records (same metadata-only contract as every W4 writer).

### 13.3 State after this pass

**W4 coverage complete: 6 writers wired (ghost_concierge, requeue_poison, recovery_escalation, disruption_feed, supervisor_escalation, stale_run_timeout) + 14 demand/operator doors + triage preview + 2 reserved seams (whatsapp_channel, vendor_quote_inbox).** Tests **26/26** (new: three-door contract matrix; IROPS closed loop with world-origin assertion; supervisor full run_once loop with a failing agent incl. no-failure-text-persistence; stale-sweep closed loop incl. tenanted + agency-less fallback). Regression: supervisor/runtime/coordinator/requeue/irops/ghost suites **145 passed**; run_status 6; sweep-touching suites (pa_agentic_remediations, partial_intake_lifecycle) **57 passed**; ruff clean. Backend restarted on current code for the live preview.

Remaining after this pass are only the gated items: owner-gated E1, provider-gated B1/B2 (+B3's live-feed upgrade, which now needs zero new wiring), I2 merge_facts (roadmap Phase 2), and the queue action surface (needs WorkItem outcome-state lifecycle first).

---

## 14. Outcome-state lifecycle + operator action surface (2026-10-24, seventh pass)

The queue becomes actionable: operators can claim, release, dismiss, and resolve items — the outcome-state semantics §12.3 identified as the missing prerequisite.

### 14.1 Design — event-sourced on the append-only log

Lifecycle transitions do NOT mutate item records. `record_lifecycle()` appends `{"record_type": "lifecycle_event", "target_item_id", "action", "actor", "note?", "at"}` to the same agency JSONL, and `_derive_lifecycle()` folds events (in append order) into per-item state at read time. The log stays append-only; the event trail IS the audit trail (who claimed, when, with what note — no second audit system needed). Stale/duplicated events are ignored by the fold, so a replayed event can never corrupt state.

State machine: `open →(claim) claimed →(resolve|dismiss) resolved|dismissed`; `claimed →(unclaim) open`; `open →(resolve|dismiss)` direct. **resolved/dismissed are terminal** — done work never re-enters the queue through the same item.

### 14.2 Surfaces

- **API**: `PATCH /api/v1/work-items/{item_id}` on the EXISTING router (no new route file) — body `{action: claim|unclaim|dismiss|resolve, note?≤200}`; 404 unknown/other-tenant item (tenant isolation is inherent — each agency folds only its own log), 409 invalid transition, 422 bad action. Actor = the authenticated user (email), from `get_current_user`.
- **Queue semantics**: `ranked_queue` is lifecycle-aware — resolved/dismissed leave the ranked list; open + claimed stay (claimed carries `claimed_by`). Honesty preserved: `total` and new `counts.by_state` cover the FULL log; class counts (by_origin/by_intent/by_urgency, duplicates, returning) describe ACTIONABLE work only; new `actionable` count; `count_basis` stays `work_item_log_total`.
- **FE**: `v1/work-items/{id}` route-map entry (BFF `{id}` substitution, same pattern as trips); `actOnWorkItem()` client + `useWorkItemAction()` mutation (invalidates all work-items queries); panel rows get Claim/Dismiss (open) or Resolve/Release (claimed) + a `claimed` badge with the claimer in its tooltip; honest action-failure alert line (suggests refresh — a 409 means the item changed under you).

### 14.3 Verification

- **BE**: `tests/test_work_intake.py` **29/29** (new: state-machine unit incl. terminal rejection + append-only proof — the original item line is untouched and events are separate records; lifecycle-aware ranked_queue with honest by_state/total vs actionable class counts; PATCH closed loop incl. cross-tenant 404, terminal 409, bad-action 422). Route snapshot 399→400 (only the PATCH path); parity gate 2/2; ruff clean.
- **FE**: panel tests **6/6** (badge render, both action clusters, claim-mutation→refetch, action-failure alert, empty, unavailable); `tsc` exit 0; ESLint clean on all five touched files.
- **Live E2E (real session, real store, 295-item log)**: claim → badge "Claimed by newuser@test.com" with Resolve/Release swapped in; release → back to open; claim → resolve → **row leaves the ranked list** while the footer stays honest ("Showing 8 of 295" — total still counts the log). Suspected right-edge clip in the first capture disproven by DOM measurement (every row scrollWidth == clientWidth; no overflow; modal absent). Evidence: `Docs/sims/assets/overview/work-queue-lifecycle-claimed-2026-10-24.png` (claimed row + Resolve/Release, modal-free).

### 14.4 History reader + note capture SHIPPED (2026-10-25 addendum)

Both follow-ons from §14 landed:

- **History reader**: `GET /api/v1/work-items?include_done=true` (same route, new query param — no new route file). `ranked_queue(include_done=True)` appends resolved/dismissed items AFTER the actionable list (same sort within each group), so the top of the queue is always actionable even in history mode. Default view unchanged (test-pinned). Done rows render with a `resolved`/`dismissed` state badge, dimmed, with NO action buttons (terminal).
- **Note capture**: Resolve/Dismiss open an inline note editor on the row (optional, ≤200 chars — the API cap); Confirm submits the note with the action, Cancel closes. The note persists on the lifecycle EVENT (not the item), so the trail reads "who dismissed, why, when".
- **FE**: `getWorkItems(limit, includeDone)`, `useWorkItems` query key gains the flag, header toggle `show N done / hide done` (only when done > 0, aria-pressed), per-row editor with confirm/cancel. Tests 8/8 (added: note-editor submit flow incl. note payload assertion; history toggle incl. done-row-no-actions render); tsc 0; eslint 0.
- **Live E2E (browser, real 585-item log)**: toggle `show 1 done` → `hide done` [pressed] with include_done refetch; dismissed a Channel Webhook item WITH a note ("duplicate of an existing whatsapp lead") → row left the ranked list, footer stayed "Showing 8 of 585"; the event log holds `{record_type: lifecycle_event, action: dismiss, target_item_id: wi_f59de45f5f05, actor: newuser@test.com, note: "duplicate of an existing whatsapp lead"}`. Authenticated contract check: `total: 585, actionable: 583, by_state: {open: 583, resolved: 1, dismissed: 1}`. Evidence: `Docs/sims/assets/overview/work-queue-history-notes-2026-10-25.png`.

Operational note: during this pass the Data volume hit 100% (853Mi free), which broke tooling mid-verification. Freed rebuildable `CACHEDIR.TAG`-marked caches only (`~/.cache/waypoint/models`, 8G — the offline SLM lane re-downloads on demand); `uv cache clean` was skipped because another process held the uv lock. ~12Gi free after. No user data touched.

### 14.5 Remaining

The same gated set: E1 (owner), B1/B2 (providers), B3 live-feed upgrade (door already wired), I2 merge_facts (roadmap Phase 2).

---

## 15. Operator display vocabulary — the queue speaks human (2026-10-25, eighth pass)

Owner feedback: "why are all these technical jargon on user facing frontend?" — rows read `Channel Webhook / demand · info · explicit_user · whatsapp`. Root cause: a category error in §12.1's own panel contract, which specified the raw subtitle. The W1–W5 × 9-axis enums are machine routing vocabulary; the queue is a read-model projection and needed its own display layer. This § SUPERSEDES §12.1's subtitle contract.

### 15.1 Shipped (backend by the parallel session, FE + tests this pass — one tranche, split across sessions)

- **Choke-point display composer** (`work_intake.py`): `DOOR_DISPLAY` (per-door headline templates, `{channel}` substitution via `CHANNEL_DISPLAY`) + `display_for()` composing `headline` + `meta` (channel / entity label / actor) **at read time — never persisted**, so label evolution never rewrites history and pre-lifecycle rows are retroactively labeled. Unknown doors degrade to title-case, never raise.
- **Entity labels** (router `_annotate_display`): bound trips resolve to human labels ("Trip — Tokyo · August 10-17, 2026") with per-request memoization (≤1 TripStore read per distinct trip on the page); unresolved trips keep the raw id off the prose (tooltip/tooling only).
- **FE**: row title = `headline` (fallback: humanized door); subtitle = `meta.join(' · ')`; the raw classification axes moved into the subtitle tooltip ("Classification: demand · new_demand · explicit_user …"). No FE vocabulary fork — the backend is the only composer.
- **Exhaustiveness test** (`test_door_display_covers_every_door`): every DOOR_CONTRACTS door must have a DOOR_DISPLAY entry and produce an underscore-free headline — a new door cannot ship jargon. (The composer comment promised this test; it was missing — closed in-pass.) Channel fix in-pass: `public_checker`/`proposal_link`/`group_pay` added to CHANNEL_DISPLAY (was rendering "Public_Checker" title-case fallback).

### 15.2 Verification

BE suite **31/31** (incl. exhaustiveness + channel composition); FE panel tests **8/8** (human headline/meta assertions, raw-enum-absence assertion, tooltip presence); tsc 0; eslint 0; ruff clean. **Live E2E** on the 585-item log: rows now read "Run request submitted / by …", "Public checker request routed in / Public checker", "New trip request / Email", "Traveler submitted details / Collection form · by traveler_collection_link", "Operator updated a trip / Trip — Tokyo · August 10-17, 2026 · by …" — zero raw enums in prose. Evidence: `Docs/sims/assets/overview/work-queue-human-display-final-2026-10-25.png`.

### 15.3 Actor display names + run collapse — SHIPPED same day (owner correction applied)

The two gaps below were initially written up as "deferred by design"; the owner corrected that framing — deferred things are things *in time* (needed by the long-term design), so they were implemented in the same pass:

- **Actor display names**: user-UUID actors resolve to display names via one batched lookup per queue read (`_resolve_actor_names` — primary-key `session.get` per distinct actor, bounded by page size; the first attempt used `IN (...)` and was blocked by the Mimosa pre-commit scanner, so the safer PK-get form ships). System/synthetic actors map through `ACTOR_DISPLAY` ("irops_watch" → "the disruption watch", "traveler_collection_link" → "the collection form", …). Operator emails pass through as-is. Unresolved UUIDs drop the `by` line entirely — an opaque id never reaches prose.
- **Run collapse**: identical OPEN entity-bound items sharing (door, trip_id, channel, urgency) collapse into one row with `group_count=N` (newest is the representative). The entity binding is what proves identity — unbound and claimed items never collapse. Honesty preserved: every count (`total`, `actionable`, `counts.*`) is computed over the UNCOLLAPSED actionable list; `count_basis` stays `work_item_log_total`. FE shows a `×N` chip with the meaning in its tooltip.
- **Live E2E**: the dev log's 30 identical "Operator updated a trip" items on one trip now render as one row with `×30` and "Trip — Tokyo · August 10-17, 2026 · by New User" (the actor UUID resolved through the real users table); "Traveler submitted details / Collection form · by the collection form". Evidence: `Docs/sims/assets/overview/work-queue-actors-collapse-2026-10-25.png`.
- **Tests**: BE **33/33** (actor display classes incl. unresolved-UUID-drops-line; collapse honesty incl. claimed/unbound never collapse and uncollapsed counts); FE **9/9** (×N chip + tooltip). tsc/eslint/ruff clean.

Nothing in §15 remains deferred: the only open display thread is new doors/channels declaring their vocabulary at the seam as they ship (enforced by the exhaustiveness test).


## 16. B1 readiness — the WhatsApp system is key-ready (2026-10-26)

Owner directive: "do all that can be done without the API key — get the systems ready." Ground truth found §5 B1's "MISSING / seam reserved" note **stale**: the parallel waves since 2026-09-29 had already built nearly the whole channel — `POST /api/v1/messaging/webhook/{provider}` (Meta challenge handshake fail-closed on unset `WHATSAPP_VERIFY_TOKEN`; default-deny `X-Hub-Signature-256` HMAC verification), Cloud API `entry[].changes[].value.messages[]` parsing + flat adapter shape, `message_store` persistence with digit-normalized trip matching, work-intake classification (`channel_webhook` door, C3 identity + C2 returning-guest riding), the FND-0126 concierge reply loop, and a REAL env-gated outbound dispatch (`message_dispatch.py`: Cloud API + SendGrid, honest `SENT`/`FAILED`/`NOT_CONFIGURED`, never fabricated). This section records the readiness-closing pass and supersedes the "B1 = provider-gated, not started" framing.

### 16.1 Gaps closed this pass (all key-free)

- **Inbound idempotency (at-least-once safety)**: Meta redelivers webhooks; the orchestrator now checks `message_store.find_by_provider_message_id()` before storing, classifying, or replying — one lookup guards all three consumers. Response carries `duplicates_skipped`. (`spine_api/routers/messaging.py`, `spine_api/services/message_store.py`)
- **Delivery-truth persistence**: Meta `statuses[]` callbacks (sent/delivered/read/failed + error titles) now attach to the matching OUTBOUND stored row via `apply_provider_status` (bounded one-line rewrite under the store lock). Statuses are delivery truth, not obligations — they never create work items (intake doctrine). Unmatched ids are honest non-applies. Response carries `statuses_applied`.
- **FND-0384 (found by the new idempotency test, fixed in-pass)**: outbound dispatch discarded the provider-assigned message id, so delivery statuses could never match stored outbound rows, and outbound reply rows collided with inbound pmids via reply threading. Fix: dispatch captures `messages[0].id` on `SENT`; outbound rows store it as `provider_message_id`; threading moved to a new `reply_to_provider_message_id` field; status application pinned to `direction="outbound"`.
- **Dispatch pre-flight guards**: body > 4096 chars (Meta's limit) and digit-less recipients fail BEFORE the network call with the real reason — the operator sees why, creds or not; `to` is digit-normalized for the Cloud API.
- **Operator flip-check**: `GET /api/v1/messaging/channel-status` (JWT-scoped) reports per-channel `CONFIGURED`/`NOT_CONFIGURED` with the exact missing env names, plus the webhook binding block (`WHATSAPP_VERIFY_TOKEN`/`WHATSAPP_APP_SECRET` set, `MESSAGING_WEBHOOK_AGENCY_ID`) — no secret echo, no network I/O. Verified once here, re-verified after the key lands.

### 16.2 The flip checklist (when credentials arrive)

1. Set `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` (outbound), `WHATSAPP_VERIFY_TOKEN` + `WHATSAPP_APP_SECRET` (webhook auth), `MESSAGING_WEBHOOK_AGENCY_ID` (which agency owns this number — unset records under `webhook-unattributed`).
2. Point the Meta app webhook to `POST /api/v1/messaging/webhook/whatsapp` (GET handshake verifies against the token).
3. `GET /api/v1/messaging/channel-status` must show whatsapp `CONFIGURED` with empty `missing_env`.
4. Send one live traveler message; verify: row in `data/messages/{agency}.jsonl`, one work item on the queue (headline "WhatsApp message received"), concierge reply stored with a provider-assigned id, and the inbound `statuses[]` attaching `delivery_status` to it.

### 16.3 What genuinely remains (provider/owner-gated, none buildable key-free)

- Live E2E against real Meta servers (needs the key; everything up to the network boundary is test-covered with signed fixtures).
- WhatsApp template approval for business-initiated (outside-24h-window) messages — a Meta-side approval, not code; free-form replies inside the window are unblocked.
- Multi-tenant number→agency mapping (today: one number per deployment via `MESSAGING_WEBHOOK_AGENCY_ID`); the phone-id→agency table is the Phase-2 follow-on.
- Inbound media DOWNLOAD (metadata is stored honestly; the bytes need a token-gated GET — natural first slice after the flip).
- **B2 vendor quote inbox** build plan (not built this pass — completion over partial work): mirror this exact shape — IMAP/webhook receiver → `vendor_quote_inbox` door (reserved seam already in `DOOR_CONTRACTS`) → `message_store` row → work item; the only B2-specific logic is the quote-attachment parser, which should reuse the multimodal door's document lane.

Tests this pass: `tests/test_messaging_router.py` **6/6** (idempotent redelivery → 1 row / 1 work item / 1 reply with `reply_to` threading; `statuses[]` → outbound row incl. error detail; unmatched id honest; pre-flight guards; flip-check endpoint). Regression: concierge ×3 + followups + work-intake suites **57/57**; ruff clean. Findings: **FND-0384** opened+closed with evidence.

---

## 17. E1 route-grammar cleanup EXECUTED (2026-10-25, supersession workflow applied)

The E1 tranche from §5/§11 — previously parked pending "owner sign-off" — was
executed under the delegated-authority ruling (reversible, pre-launch, git-revertible;
the supersession workflow IS the authority). Record per the workflow's step 5:

| Candidate | Field comparison vs replacement | Call-site audit | Action |
|---|---|---|---|
| `app/v2..v5/page.tsx` ×4 | Pure `redirect('/')` stubs — replacement `/` is a strict superset (the stubs' only behavior) | Zero nav/sitemap refs; only `proxy.ts` PUBLIC_PAGES + its test listed them | **DELETED** + proxy PUBLIC_PAGES cleaned + proxy test updated |
| `app/intake/fast/page.tsx` | **CORRECTION (owner challenged "should it be gone?"): NO backend `/intake/fast` route ever existed** — zero occurrences in the route snapshot across all history; my "backend already gone" premise was false. The page calls the canonical `parse_social` door, and the parallel lane had just SECURITY-HARDENED it in `2a2bfa7c` (FND-0372: env-pinned base, constant path, "never caller-shaped") — a committed, intentional, keeper surface. My "zero references" audit also missed the FND-0372 ledger, the codebase map's door inventory, and the lane's hardening intent | References found: FND-0372 records, codebase map §doors, lane hardening commit `2a2bfa7c` | **RESTORED** — supersession REJECTED, deletion reverted |
| `app/corporate/offsites/page.tsx` | **CORRECTION: same premise failure.** The lane hardened it in `2a2bfa7c` (pinned `/api/v1/corporate` base, constant paths) as a keeper surface for the real corporate-policy product area; the hardcoded company id is its sandbox parameter | Lane hardening commit `2a2bfa7c` | **RESTORED** — supersession REJECTED, deletion reverted |
| BFF bypass #3 — `api-client` booking-collection ×3 hit `NEXT_PUBLIC_SPINE_API_URL` origin directly | Same endpoints, now through the F-43 allowlist catch-all: 3 route-map keys added (`public/booking-collection/{agency_id}/{token}[/submit\|/documents]`); client switched to same-origin relative paths; unused `SPINE_API_URL` const removed | 3 call sites migrated | **FIXED** (allowlist posture restored) |
| Dev-session backdoor `(agency)/layout.tsx` | Fabricated `usr_dev_1`/`agency_dev_1` admin session for ANY non-prod build → now requires explicit `NEXT_PUBLIC_WAYPOINT_DEV_SESSION=1` (staging that forgets NODE_ENV no longer renders an admin shell) | Single site | **TIGHTENED** |
| `app/(agency)/bookings` (nav-linked!) | NOT deletable — rebuilt honestly: rendered REAL `booking_data` (travelers/passports, payment tracking, notes), pending customer submissions with accept/reject, and collection-link lifecycle (generate/copy/revoke) — all pre-existing backend surfaces (`getBookingData`, `getPendingBookingData`, collection endpoints); deleted the fabricated rows, fake operational checklist, and the client-side keyword "extractor" (a fake parser in the browser) | Nav entry kept; tests rewritten 4/4 (real-render, honest empty, pending accept, link lifecycle) | **REBUILT HONEST** |

**Blast-radius catch:** the parity gate flagged the parallel lane's B1 commit
(`418f42ae`) — `GET /v1/messaging/channel-status` lacked a BFF mapping; route-map key added
(`v1/messaging/channel-status`), gate 2/2.

**Contested-tree note:** the full FE suite shows 14 failing files at this instant; every one
fails inside the parallel lane's UNCOMMITTED edits (IntakePanel "Build trip options"/next-action
copy, insights/overview/quotes/workbench suites) — none import or exercise this tranche's files.
This tranche's own suites: bookings 4/4, proxy ✓, nav-modules ✓, work-intake/parity gates green;
`tsc` exit 0; eslint 0 errors (1 pre-existing bare-fetch warning in layout session hydration).

**E1 status after the owner's challenge: the v2–v5 stub deletions, the booking-collection
bypass fix, the dev-session gate, and the Bookings honest rebuild STAND (each verified against
real references and real replacement surfaces). The intake/fast + corporate/offsites deletions
were REVERTED — the "backend already gone" premise was false (no such backend route ever
existed), and the pages are lane-hardened intentional keepers (FND-0372 commit `2a2bfa7c`).
Their final disposition (improve/integrate vs retire) belongs to a deliberate product pass, not
a route-grammar sweep. Lesson recorded on the memory: an unverified "already gone" premise is
exactly the interrupted-work trap the supersession rule names — verify the REMOVAL's history,
not just the candidate's references.** The standing-broken things E1 targeted remain fixed: no
origin bypasses, no unconditional fabricated session, no fabricated sample surface in the
agency nav.

---

## 18. B2 vendor quote inbox SHIPPED (2026-10-26) — the reserved-door set is now empty

The B2 build plan (§16) executed: vendors (DMCs, hotels, operators) email quotes to the
agency; before this router those lived in operators' inboxes, invisible to the system.
The B1 messaging-webhook pattern is mirrored exactly:

- **`POST /api/v1/vendor-inbox/webhook`** (public_router, JWT-less): default-deny —
  401 unless `VENDOR_INBOX_WEBHOOK_SECRET` is configured AND `X-Webhook-Token` matches
  (constant-time). Accepts SendGrid Inbound Parse (multipart form) AND a plain JSON
  envelope; providers and tests need not care which.
- **Deterministic trip binding only**: explicit `trip_id` field, or a whole-token
  `trip_*` id in subject/body, VALIDATED against the trip store. Destination-text
  matching is deliberately absent (the origin-fabrication class). Nothing verifiable
  → unbound row; the operator binds later.
- **Honest extraction**: amounts/currency signals parsed deterministically into
  message `metadata.extraction` (new optional `metadata` field on
  `message_store.append_message`, additive) — labeled `unverified: True`; bare
  numbers after a currency anchor inherit it with `inherited: True`; sub-1000 bare
  numbers stay out ("Valid 14 days" never becomes an amount). Extraction NEVER
  touches facts, packets, or the quotes read model — the money boundary holds;
  quotes enter the read model exclusively through operator action.
- **Idempotency**: Message-ID lookup guards the store row AND the work item (B1
  contract).
- **`vendor_quote_inbox` door retired from reserved → wired**: classification with
  `text=None` (a quote email is a document, not an urgent message — urgency/PII
  heuristics would misfire; same reasoning as the multimodal OCR leg),
  `contact=vendor_email`, `channel=vendor_email`, origin=supply.
- **Attachment content NOT parsed**: recorded (filename/mime) for the operator; the
  multimodal document lane owns binary parsing — no parallel system.
- **`GET /api/v1/vendor-inbox`** (auth router): operator view, channel-filtered,
  route-map key added (`v1/vendor-inbox`). The channel-messages feed renders
  `vendor_email` rows via the panel's new icon/label.

**Config (key-ready)**: `VENDOR_INBOX_WEBHOOK_SECRET` (unset → webhook 401s, default-
deny), `VENDOR_INBOX_AGENCY_ID` (falls back to `MESSAGING_WEBHOOK_AGENCY_ID`, then
`webhook-unattributed`). SendGrid Inbound Parse setup is pure config once credentials
exist — the same shape as B1's flip checklist.

**Verification**: `tests/test_vendor_inbox.py` 7/7 (default-deny unconfigured +
wrong-token, ingest+classify w/ lakh-grouping parse, Message-ID idempotency,
deterministic binding incl. the no-fabrication case, extraction-stays-out-of-facts
money-boundary pin, empty-payload ack). Regression: messaging 6/6 + work-intake 26/26
+ parity 2/2; FE inbox suites 56/56; tsc 0; eslint 0; route snapshots written.

**DOOR LEDGER FINAL**: 14 wired doors + ALL reserved seams now wired (B1
whatsapp_channel §16, B2 vendor_quote_inbox here) + 6 W4 writers + triage preview.
The classification map's door universe is complete: every surface that accepts
external input and creates an obligation records exactly one classified WorkItem.
