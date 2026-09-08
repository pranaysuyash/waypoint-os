# Persona Audit — PER-0443 Agentic Travel Systems Architect (2026-09-07)

**Status:** complete review artifact (documentation + plan; no product-behavior change in this pass)  
**Date:** 2026-09-07  
**Persona applied:** PER-0443 — Agentic Travel Systems Architect  
**Canonical persona file:** `/Users/pranay/Desktop/Understanding_Personas_sept6/01 Expanded Personas/09 Travel - Waypoint OS/PER-0443 - Agentic Travel Systems Architect.docx` (repository expansion 2026-09-05; 33-line expanded form extracted via OOXML this session)  
**Why this persona (not PER-0700 again):** PER-0700 (Agentic Systems Architect) already audited generic agency/eval/authority on 2026-09-06. PER-0442 (Travel Operating Systems Architect) audited OS structure on 2026-09-03. PER-0443 is the **intersection**: which *travel* tasks may an agent perceive, infer, plan, call, change, remember, schedule, notify, or escalate — with tool contracts, duplicate-action control, and human approval by *consequence*.  
**OrbitCover boundary:** the persona file forbids treating OrbitCover as a Waypoint subsystem. Insurance findings below are honesty/authority findings, not a request to import OrbitCover.

**Doctrine:** Operating Doctrine 8.0 (§2 truth, §11 engineering, §12 AI-output, §13 claim reality) + Review 1.1 + Architecture 1.1 + Documentation 1.1.  
**Checklist applied:** `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

**Companions:**

- Findings/tasks register: [FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07](FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md)
- Implementation plan: [IMPLEMENTATION_PLAN_PER0443_2026-09-07](IMPLEMENTATION_PLAN_PER0443_2026-09-07.md)
- Skills catalog (agent-pointable): [../FULL_SKILLS_CATALOG.md](../FULL_SKILLS_CATALOG.md)
- Session evidence: [SESSION_EVIDENCE_PER0443_2026-09-07](SESSION_EVIDENCE_PER0443_2026-09-07.md)

**Canonical status store remains** `Docs/review/FINDINGS_REGISTER_2026-08-31.md`. This audit does not close or reopen those rows.

---

## 0. Substantial-task gate (this conversation)

| Item | Statement |
|---|---|
| Objective | Persona-audit the live repo; document implicit/explicit findings; judge 1P/LT/doctrine alignment; list explore vs implement; produce an implementation plan; publish a skills catalog other agents can follow. |
| Scope | `Docs/review/*PER0443*`, `Docs/FULL_SKILLS_CATALOG.md`, `Docs/INDEX.md`. No Git mutation. No hosted deploy. No money-path behavior change in this pass. |
| Ownership | Review/docs. Canonical register stays the status authority. |
| Side effects | New durable docs only. |
| Risk | Low. Residual: catalog could go stale if skill stores move; mitigated by pointing at `AGENTS.md` search order. |
| Evidence plan | Persona extraction (Observed) + live file:line (Observed) + register parser-backed counts (Observed, inherited) + focused code reads of P0 claims (Observed). No hosted Tier-3. |
| Stop | Ask only if Git/commit, production, or money-path implementation is requested as a new gate. |

Truth labels used below: **Observed** / **Inferred** / **Proposed** / **Unknown** / **Contested**. Evidence this pass is **Tier 1** (static inspection) unless a test file is cited.

---

## 1. Persona kernel (extracted)

**Mandate:** turn agent capability into safe, useful, inspectable *travel* action while keeping authority, context, tool use, cost, and persistent state under explicit system control.

**Central questions:** Which travel tasks are agent-appropriate? What may execute automatically vs require approval? Which tools and data can each agent access? How do agents share state and avoid duplicate or conflicting action?

**Inspection surface:** agent roles, goals, tool calling, memory/context, plans, delegated tasks, approvals, retries, idempotency, conflict resolution, scheduling, notifications, uncertainty, cost limits, permissions, provenance, audit logs, fallback, cross-agent coordination.

**Named failure modes (persona §10) — used as the hunt list:**

1. Hidden shadow state  
2. Duplicate bookings/actions  
3. Unbounded tool access  
4. Confidence inferred from model tone (or invented scores)  
5. No approval policy  
6. Retries causing side effects  
7. Agent-to-agent consensus without evidence  
8. Notifications replacing durable state  
9. Treating insurance/OrbitCover workflows as internal Waypoint agents  

---

## 2. Executive verdict

**Observed:** Waypoint already has the *right travel primitives* (canonical packet + NB01/NB02, Journey Dependency Graph schema, confirmation state machine, bounded supervised fleet with “do not book” contracts, reality-tier vocabulary, durable proposal acceptance from PER-0700). It does **not** yet *operate* as an agentic travel OS because those primitives are not the source of truth at runtime.

The system is:

- **Under-agentic where travel value lives:** the journey graph is never persisted (`journey_graph_nodes` is read in `spine_api/routers/journey_graph.py` and written only in tests). IROPS, companion, passenger rights, and fulfillment therefore cannot see the traveler’s itinerary.
- **Over-agentic where presentation lives:** IROPS/counterfactual/compiler/loyalty/visa-radar/companion still mint luxury brands, PNRs, scores, and “ON TIME” without provider evidence. Some surfaces are honestly preview-wrapped (IROPS router — keep). Some are not (companion fallbacks, counterfactual router, loyalty balances).
- **Collapsed on commitment:** search → hold → book → ticket is one `fulfill_accepted_proposal` that can run twice (no existing-confirmation guard) and writes a JSON blob instead of the real `BookingConfirmation` machine.
- **Misnamed on “next best action”:** `next_best_action` is CRM (`SEND_FOLLOWUP`, `CLOSE_LOST`). Nineteen fleet agents stamp the same `operator_next_action` field. Last writer wins. There is no next-best-*travel*-action.

**Doctrine in one line:** the *fleet’s authority strings* and the *intake gates* are first-principles-aligned; the *journey is not canonical state*, so long-term travel operations (IROPS, companion, entitlements) cannot compose. Claim-reality still leaks on traveler-facing UI after the PER-0700 honesty wave.

**Launch posture unchanged:** public/paid **NO-GO** (`Docs/LAUNCH_STATUS.md`). This audit does not clear L1–L8.

---

## 3. Method

| Pass | What | Evidence |
|---|---|---|
| P0 | Load instruction stack + PER-0443 + Waypoint persona index | OOXML extract of both docx files |
| P1 | Re-verify remaining PER-0700 OPEN/PARTIAL against live tree | Register Part 4g + file reads (`decision.py:40` hybrid default `"0"`, `failure_taxonomy.py` 8-class enum, `metrics_registry.py` exists) |
| P2 | Travel-domain hunt (journey, IROPS, NBA, duplicate book, companion, visa, loyalty, insurance, group, memory) | Parallel explore agent + lead re-read of P0 claims |
| P3 | Skills inventory | `AGENTS.md` search order + `/Users/pranay/Projects/SKILLS_CATALOG.md` + `~/Projects/skills/` listing + `agentic-eval-loop` |
| P4 | Alignment + plan that does **not** redo PER-0700 Phase 0–2 | Cross-walk to ADR-008, E-B/E-C, launch blockers |

Lead-verified this session (Observed):

- Hybrid default `"0"` in `src/intake/decision.py:40`; compose `:-0`; `fly.toml` unset; **`.env.example:67` and `render.yaml:27-28` still `1`** (Contested with PA-03).
- `journey_graph_nodes` writers: tests only (rg).
- Companion fabricates `'BA 178'`, `'006-2345678901'`, `'HTL-AMAN-88219'`, `'Tokyo & Kyoto'`, `'ON TIME'` (`companion/page.tsx:118-181`) and fetches `/api/public/journey-graph/${tid}` **without token**.
- Fulfillment builds an in-memory JDG node then persists **only** `booking_confirmation` (`booking_fulfillment.py:250-277`); no refuse-if-already-booked.
- IROPS engine synthesizes BA178/DL490/Four Seasons regardless of `trip_id` (`src/orchestration/irops_healer.py:70-80`); router honestly sanitizes (`irops_healer.py:61-129`).
- Counterfactual router mints a dummy Air France node; scores 94.5/88/91 hardcoded (`counterfactual.py:41-52`, `counterfactual_recovery.py:80-114`); **no RealityTier**.
- `decide_commercial_action` is the NBA producer (`decision.py:1653-1682`).
- E-B design (7 classes) **≠** live `FailureClass` (8 classes: model/tool/environment/state/verification/authority/policy_block/unclassified).

---

## 4. Travel-task appropriateness matrix

Ladder used: ADR-008 R0 human-only → R1 approve-per-action → R2 auto+review → R3 auto+audit → R4 full-auto. A rung is real only if a named seam executes it.

| Travel task | Current (enforced?) | Should-be | 1P | LT | DOC | Evidence |
|---|---|---|---|---|---|---|
| Intake extract / NB01–NB02 | R3 yes (gates) | R3 | ✅ | ✅ | ✅ | `src/intake/gates.py` |
| Hybrid LLM enrichment | R3, default off, credential-gated | R3 flagged | ✅ | 🟡 | 🟡 | `decision.py:40`; `.env.example` still 1 |
| Suitability | R3 deterministic; Tier-3 unwired | R3; keep PLANNED | ✅ | ✅ | ✅ | PA-36 / ADR-008 §4.2 |
| Next-best **question** | R3 | R3 + optional memory slot | ✅ | 🟡 | 🟡 | strategy/question gen; PA-18 |
| Next-best **travel action** | none / last-writer stamp | **R2 projection** | ❌ | ❌ | ❌ | AT-07 |
| Proposal compile | R3 over sim inventory | R2 until live offers | 🟡 | 🟡 | 🟡 | PA-25 honesty; still names Belmond/Blacklane |
| Traveler accept | R0 durable | R0 | ✅ | ✅ | ✅ | PA-02 local |
| Fare hold | preview, not persist | R2 propose; R1 persist | 🟡 | ❌ | ✅ | PA-06; AT-16 |
| Book / ticket | auto if mandate off | **R1 always** | ❌ | ❌ | ❌ | AT-03/09/15; flag default `"0"` |
| Ticket void | machine exists, unwired from fulfill | R1 | 🟡 | ❌ | 🟡 | `CONFIRMATION_VALID_TRANSITIONS` |
| IROPS detect | annotator + wrong-itinerary preview | R3 detect | 🟡 | ❌ | 🟡 | AT-06 |
| IROPS rebook | engine says auto; router preview | **R1** | ❌ | ❌ | ✅ router | keep sanitizer; do not auto-rebook |
| EU261 pay | stripped preview | **R0** case | ✅ not paying | ❌ no case | ✅ | AT-17 |
| Visa/docs | static seed, `legal_finality: False` | R2 checklist | 🟡 | ❌ | 🟡 | AT-11; keep legal_finality |
| Insurance bind | formula quote + typed policy # | **R0 bind** | ❌ | ❌ | ❌ | AT-12 |
| Loyalty redeem | fabricated balances | R0 / fail-closed | ❌ | ❌ | ❌ | AT-13 |
| Group consensus | compute-only | R0 per-pax accept | 🟡 | 🟡 | 🟡 | AT-14 |
| Memory → questions | not wired | R3 gated | 🟡 | 🟡 | 🟡 | AT-10 / E-D |
| Memory → inventory | not wired (**good**) | **never** | ✅ | ✅ | ✅ | AT-10 |
| Fleet scans | R3 JSON stamps | R2 review queue | ✅ contracts | 🟡 last-writer | 🟡 | AT-08 — **keep authority strings** |
| Follow-up send | drafts only | R1/R2 | ✅ | ✅ | ✅ | communicator |

---

## 5. Persona failure-mode scorecard

| Persona failure mode | Hit? | Finding |
|---|---|---|
| Hidden shadow state | **Yes** | In-memory JDG at fulfill/IROPS/counterfactual; confirmation blob vs SQL table (AT-01, AT-04) |
| Duplicate bookings | **Yes** | Second fulfill overwrites confirmation (AT-03); PA-40 residual |
| Unbounded tool access | Partial | Fleet mocks by default (good); compiler/IROPS still name real brands |
| Confidence from tone/scores | **Yes** | Hardcoded 94.5/88/91 (AT-13-class / AT-19) |
| No approval policy | Partial | ADR-008 proposed, unratified; mandates default off (AT-15) |
| Retries with side effects | Residual | Fulfillment not on idempotency registry (PA-40) |
| Consensus without evidence | **Yes** | Council theater (PA-35); group solvers unbound (AT-14) |
| Notifications as state | **Yes** | Companion SOS `setTimeout`; ON TIME badge (AT-18) |
| Insurance as internal agent | **Yes** | Formula Allianz-class plans + typed attach (AT-12) |

---

## 6. What is excellent — keep and extend

1. **JDG schema** (`src/schemas/journey_graph.py`) — node types, MCT, `evaluate_disruption`. Right primitive; needs persistence (AT-01).
2. **PA-01 public abstain** — do not regress. Companion has not caught up (AT-05).
3. **Confirmation state machine** — draft/recorded/verified/voided. Make fulfillment use it (AT-04).
4. **Fleet authority strings** — “Do not book, ticket, charge…” (`runtime.py` BookingReadiness / FlightStatus). This *is* the travel agency boundary.
5. **NB01/NB02 + STOP_NEEDS_REVIEW never auto-suppressed.**
6. **Durable acceptance + lease + registry cap + mandate CAS** (PER-0700) — skeleton is right; turn mandate default on only after ADR-008.
7. **IROPS router sanitizer** — strips VCC/claims, `PREVIEW_ONLY`. Keep when the engine is pointed at a *real stored graph*.
8. **Communicator drafts, does not send.**
9. **Document readiness `legal_finality: False`.**
10. **Reality-tier vocabulary + SimulatedBadge CI.**

---

## 7. Relationship to PER-0700 (do not rebuild)

PER-0700 Phase 0–2 is **executed locally, uncommitted**. This audit treats PA-01…PA-10, PA-12 (GC half), PA-14–17, PA-24–28, PA-38 as **fixed-locally** and does not re-file them.

Still OPEN from PER-0700 (explicit carry-forward): PA-11, 18, 19, 22, 29–37, 39, 40 and residual halves of PA-13/15/20/21/23/08/12.

**Contested with PER-0700 docs:**

| Topic | PER-0700 / E-B doc | Live 2026-09-07 |
|---|---|---|
| Hybrid default | default off | code off; `.env.example` + `render.yaml` still 1 |
| Failure taxonomy | E-B 7 classes, “no code changed” | `failure_taxonomy.py` 8 classes **already shipped** |
| E-D/E-E/E-G | planned | **still missing as docs** |
| Companion honesty | F-41 backend fixed locally | traveler UI still fabricates (AT-05) |

---

## 8. New findings (AT-01…AT-19)

Full tables, class, alignment, and “what best adds” live in the companion register. Summary:

| ID | Sev | One line |
|---|---|---|
| AT-01 | P0 | Journey graph is not persisted; travel ops have no itinerary SSOT |
| AT-02 | P0 | Progressive commitment collapsed (no hold vs ticket) |
| AT-03 | P0 | Fulfillment can double-issue PNR/VCC |
| AT-04 | P1 | Two confirmation stores (trip JSON vs SQL machine) |
| AT-05 | P0 | Companion fabricates PNR/status/SOS; ignores PA-01 token |
| AT-06 | P1 | IROPS heals a sample BA178 graph, not the traveler’s; duplicate engines |
| AT-07 | P1 | NBA is CRM; 19 agents fight `operator_next_action` |
| AT-08 | P1 | Fleet is scan-and-stamp cron (keep contracts; stop implying travel agents) |
| AT-09 | P1 | Compile → accept → fulfill → void is not a chain of artifacts |
| AT-10 | P2 | Memory must not become a booking input (E-D constraint) |
| AT-11 | P1 | Visa radar hardcodes dates / TEST_AGENCY_ID |
| AT-12 | P1 | Insurance quote/bind is an internal fake carrier |
| AT-13 | P1 | Loyalty balances invented per customer_id |
| AT-14 | P2 | Group consensus does not bind booking |
| AT-15 | P1 | Money-path R1 unsigned; mandates default off |
| AT-16 | P2 | Fare hold / freshness never feeds the journey |
| AT-17 | P2 | Passenger rights are a preview number, not an operator case |
| AT-18 | P2 | SOS/ON TIME replace durable ops state |
| AT-19 | P2 | Evaluate/compiler still mint synthetic providers as success; TRIP-LIVE-* defaults |

---

## 9. Alignment of *existing* implementations (not just new bugs)

Question asked: are current implementations first-principles, long-term, doctrine-aligned — and what would make them the best?

| Area | 1P | LT | DOC | What “best” adds |
|---|---|---|---|---|
| Intake spine | ✅ | ✅ | ✅ | Keep. Wire memory only at question-gen (E-D). |
| Hybrid engine | ✅ default-off | 🟡 env drift | 🟡 | Align `.env.example`/`render.yaml`; startup rung log (ADR-008). |
| JDG schema | ✅ | ❌ unused | 🟡 | Persist on compile/fulfill; trip derives from graph. |
| Supervised fleet | ✅ authority | 🟡 last-writer | 🟡 | One NBTA projection; ratify as R2 annotators. |
| Fulfillment | 🟡 lease+readback | ❌ no once-booked | 🟡 preview labeled | Idempotent; write confirmation table; persist JDG. |
| IROPS API | ✅ honesty wrapper | ❌ wrong itinerary | ✅ | Point at stored graph; archive `src/logistics/irrops_healer.py`. |
| Counterfactual | ❌ invented scores | ❌ dummy graph | ❌ no tier | Load stored graph; RealityTier; delete hardcoded scores. |
| Companion | ❌ | ❌ | ❌ §13 | Token + abstain; never invent PNR. |
| Memory graph | 🟡 write machinery | ❌ no read | 🟡 | E-D then two slots; never inventory. |
| Evals D6 | ✅ honest lane | 🟡 accuracy-only | 🟡 | E-C dims; PA-11 live or simulated lineage. |
| Failure taxonomy | ✅ classes exist | 🟡 E-B mismatch | 🟡 | Ratify one enum. |
| ADR-008 | ✅ model | ❌ unratified | 🟡 | Owner §6 block. |

---

## 10. Explore vs implement (persona rule)

Do **not** implement a second journey store, a second IROPS healer, a second confirmation machine, or OrbitCover.

**Explore/document first:** E-D (memory slots), E-E (timeline-as-evidence), E-G (durable SQL endgame), E-H activation, E-B vs live enum, ADR-008 ratification, D-01…D-03 product contracts.

**Implement next (travel-domain, extend canonical paths):** AT-01 persist JDG, AT-03 idempotent fulfill, AT-05 companion honesty, AT-06 IROPS-on-stored-graph, AT-07 NBTA projection, Wave-1 hybrid/docs drift (`.env.example`, `render.yaml`, F-43).

Full sequencing: the implementation plan companion.

---

## 11. Skills other agents must be able to find

Published at `Docs/FULL_SKILLS_CATALOG.md`. The sentence to give them:

> Open `Docs/FULL_SKILLS_CATALOG.md`, search for the relevant skill in category X, and follow its `SKILL.md` file.

---

## 12. Limits of this audit

- **Observed** in the working tree on 2026-09-07, including uncommitted PER-0700 remediations.
- Not hosted, not multi-worker, not a browser proof of companion (AT-05 is source-level; UI verification remains L7).
- Skills catalog is high-signal canonical paths, not a crawl of 2,899 community skills.
- No Git commit (not authorized).
