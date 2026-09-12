# Intake Ontology — entities, states, events, actions (first-principles realignment)

**Date:** 2026-09-13 · **Supersedes the layer-framing of**
`EXTRACTION_REALIGNMENT_REGEX_NLP_LLM_2026-09-13.md` (the L0–L4 "layers"
reappear here as *actions*; the ontology is the foundation they act on).
**Trigger:** Sim #2 (FND-0272…0276). Owner directive: think from first
principles in terms of states, events, actions — identify the entities
(flights, destinations, people, …) so that **every failure, singly or in
combination, can be attributed to *what, where, when*.**

---

## 0. The root cause, stated in one line

**The packet is state without events.** Each `Process` is a pure function
`full-thread-text → packet` that replaces fields wholesale. There is no
record of *what was asserted, by whom, when, against what* — so a wrong
value is indistinguishable from a right one, conflicts resolve silently by
order, and "where did this come from?" has no answer. Every Sim #2 failure
is this one deficiency wearing different clothes. (Contrast: the trip side
already has a status machine + `status_history`; the findings store is
append-only. The intake packet is the last mutable-state-without-history
surface.)

## 1. The five planes (every question decomposes into these)

| Plane | Question | Example |
|---|---|---|
| **Who** (attribution) | which speaker/holder does this belong to? | "jain" → Meera, not the group |
| **What** (facts) | which entity, which field, which value? | Budget.scope = total |
| **What happened** (events) | which assertions, contradictions, supersessions? | Arjun's note *contradicted* the season |
| **What we did** (actions) | which pipeline action produced this value? | L1 cue-extract, L3 merge, L4 gated-LLM |
| **What state** (outcomes) | which state is each entity in; which lifecycle transition fired? | lead: new → blocked; destination: proposed |

Failure attribution then has a deterministic grammar — for any wrong value:
**what** (entity.field), **where** (segment + layer/action), **when**
(event/sequence number), **who** (speaker/holder), **why** (which guard was
missing). The design goal is that this grammar is always answerable from the
event log, not from re-derivation.

## 2. Entity catalog (the "stuff") with per-entity states

### 2.1 Delegation / Trip (the collective)
- **Fields:** budget cap {amount, currency, scope, flexibility}, date window
  {earliest, latest, anchors[]}, party size, purpose.
- **States (facts):** `unasserted → asserted → conflicted → resolved(asked|confirmed)`
- **States (lifecycle):** the existing trip/lead machine
  (new → blocked → escalated → planning → …) with `status_history`.

### 2.2 Person (traveler)
- **Fields:** name, role (`organizer` | `member`), pairings (couple-of),
  constraints[] (dietary, mobility, fear, occasion), preferences[].
- **States:** `mentioned → identified(name) → role-assigned` per person;
  constraints per person: `asserted → attributed → active`.
- **Key invariant:** a personal constraint can never silently become a group
  constraint; a group constraint can never override a personal hard
  constraint (FND-0275).

### 2.3 Place (destination | origin | lodging)
- **Destination:** `proposed → acknowledged → confirmed → dropped`;
  conflicting proposals (december-ski vs spring) coexist as `conflicted`
  until resolved. Okinawa-as-side-trip lands here — **never** at origin.
- **Origin:** requires an origin-cue event to even exist; states:
  `unasserted → asserted → confirmed`. No cue → no entity instance
  (FND-0273 okinawa fabrication becomes structurally impossible).
- **Lodging:** type (ryokan/hostel/hotel), room count, room orientation
  (2 doubles); `proposed → confirmed`.

### 2.4 Budget
- **Instances (not a single field):** each amount-assertion is an event
  carrying {amount, currency, scope, flexibility, holder, explicitness}.
- **States:** `asserted → conflicted → resolved`. Precedence rule lives in
  the merge action, not in the scanner (FND-0273).

### 2.5 Time
- **Window** (spring-next-year, flexible ±1 week), **Anchors** (April 14
  must-be-covered), **Seasons** (cherry blossoms, december-skiing).
- Anchors are hard constraints with holder; windows are soft with holder.
  A window that fails to cover an anchor is itself `conflicted` (this is the
  three-way constraint FND-0275/0276 tripped over).

### 2.6 Activity
- scuba, skiing, cooking class, nightlife, kimono photos: `proposed →
  confirmed → dropped`, each optionally destination-coupled (okinawa+scuba)
  and holder-coupled (Arjun proposes ≠ group confirmed).

### 2.7 Constraint (cross-cutting)
- {holder: person|group, kind: dietary|mobility|fear|occasion|budget,
  hardness: hard|soft, source-event}.
- States: `asserted → attributed → active`; `unattributed` is a *degraded,
  visible* state (never silently group-widened — FND-0275).

### 2.8 Question (follow-up)
- {text, targets: facts in conflict/missing, addressee}.
- States: `raised → answered → closed`. The missing-fields banner is a
  rendering of open questions — which is why it was unstable: it rendered
  derived state, not open questions (FND-0276).

### 2.9 Channel artifacts (transcript segments)
- Speaker-labelled lines, forwarded headers: **they are events' carriers,
  never facts.** Their text may not enter any fact field (FND-0274 becomes a
  type error, not a cleanup).

## 3. Event vocabulary (append-only log, per lead)

```text
note.received      {note_id, seq, channel, raw_text}
segment.parsed     {segment_id, note_id, speaker?, kind: prose|transcript|forward, span}
entity.mentioned   {entity_ref, segment_id}
entity.identified  {entity_ref → name/person, segment_id}
fact.asserted      {fact_id, entity_ref, field, value, evidence_span(verbatim),
                    speaker, layer: L1cue|L2attr|L4llm, confidence}
fact.conflicted    {fact_id, with_fact_id, kind: scope|holder|window|…}
fact.superseded    {fact_id, by_fact_id, reason: explicit-overrides-inferred|…}
question.raised    {question_id, targets[], text}
question.answered  {question_id, segment_id}
lifecycle.changed  {entity: lead|destination|activity|…, from, to, because}
lead.persisted     {trip_id, store: sql}          ← FND-0272's missing event
```

Rules: the log is append-only; `Process` **appends events** and *reprojects*
the packet from them (CQRS read-model — the packet becomes a projection,
which is exactly how Lead Inbox already works over trips). Reprocessing an
accumulated thread then cannot lose history: new segments append new events;
old assertions are superseded or conflicted, never erased.

## 4. Action taxonomy (what the pipeline does — the realigned "layers")

| Action | Precondition | Postcondition / failure mode |
|---|---|---|
| **A-segment** (L0) | raw note | segments with speaker/kind/span; transcript segments flagged as carriers-only |
| **A-cue** (L1) | a segment | fact.asserted only when segment carries field-specific cue AND evidence (amount for budget; origin-verb for origin); evidence_span verbatim |
| **A-attribute** (L2) | a segment + speaker | constraint/fact bound to person or group; unresolvable → holder=unattributed (visible degraded state) |
| **A-merge** (L3) | event log | apply precedence (explicit>inferred, amount-bearing>casual, anchor>window); conflicts → fact.conflicted + question.raised; never silent overwrite |
| **A-llm** (L4) | fields where A-cue abstained | gated LLM (abstention gate + JSON recovery, both shipped); output enters log with layer=L4, authority=inferred |
| **A-ask** | fact.conflicted / required-missing | question.raised; banner renders open questions |
| **A-persist / A-block / A-escalate** | run terminal state | lead.persisted event MUST exist (FND-0272) — a blocked run with no `lead.persisted` event is itself a detectable failure |

## 5. Attributability contract (the acceptance test of this design)

Every packet value must be traceable as: **entity.field = value ←
fact.asserted(event_id, speaker, segment, verbatim span, layer) ←
note.received(seq)** — and every missing/misleading value must be traceable
to a named missing guard/action. Verified by replaying Sim #2:

| Sim #2 failure | What | Where (action/layer) | When (event) | Missing guard |
|---|---|---|---|---|
| FND-0273 scope=per_night | Budget.scope | A-cue ran unscoped over whole thread | after note.received#2 | amount-scoped evaluation + total-precedence (Phase 1 **landed**) |
| FND-0273 origin=okinawa | Origin.city | A-cue without origin-cue precondition | note #2 segment | origin-cue precondition (Phase 2) |
| FND-0274 `[arjun]:` in fields | Constraints/Preferences | A-segment absent | note #5 | transcript-kind segmentation (Phase 3/L0) |
| FND-0275 jain unattributed; no-heights/apr-14 dropped | Person(Meera).constraints | A-attribute absent | notes #3/#4 | person slots + anchor constraints (Phase 3) |
| FND-0276 unstable missing list / corrupted raw / D-02 misfire | banner + ambiguities | rendering + A-cue evidence | every pass | open-question rendering + verbatim spans + explicit short-circuit (Phase 4) |
| FND-0272 no lead | lead.persisted | A-persist on UI path | after each blocked run | persist-event invariant + E2E test (Phase 0) |

The ontology is *correct* iff this table stays answerable for every future
failure — i.e., the fix for each finding is a missing named event/guard, not
an ad-hoc patch.

## 6. Migration (additive; no big-bang)

1. **Event log first:** persist `note.received`/`segment.parsed` per draft
   (draft JSON already stores the thread; add `events[]`). Phase 0's
   `lead.persisted` invariant lands here.
2. **Entity refs next:** `Slot.evidence_refs` already carries provenance —
   add `entity_ref` + `status` (asserted/conflicted/superseded) to Slot;
   `travelers[]` added to the packet alongside group facts.
3. **Projection re-write:** packet fields become projections of the log
   (merge action = projection rule). Downstream consumers keep reading the
   same packet shape — nothing breaks.
4. **Then the L1 cue-guards, L2 attribution, L3 precedence, L4 gating**
   from the realignment doc apply *as actions* on the log, each with its own
   regression test pinned to a Sim #2 (or future sim) replay.

## 7. What this buys us

- **Failure grammar is always answerable** (what/where/when/who/why).
- Cross-voice contradictions become first-class `fact.conflicted` +
  questions — the delegation product behavior (IDEA-134) is the ontology
  falling out naturally.
- The LLM stays a *gated contributor of events*, never a state owner.
- Reprocess = append; history is cumulative by construction; the packet is
  reproducible from the log at any point (replay = test).

---

## 8. v2 RECONCILIATION — against the taught systems model (2026-09-13)

Re-look driven by Pranay's Waypoint training sessions (state machines,
events vs conditions vs failures vs risks, idempotency, component states,
queues, permission tiers, gates). Honest grading of §1–§7 against that
model, then the corrections.

### 8.1 Where v1 was right (confirmed by the teachings)

- Event vocabulary + append-only log; "events update facts, state
  transitions depend on the resulting facts and rules" — v1's projection
  stance matches exactly.
- Per-entity state machines ≈ the taught *component-level state* pattern.
- L4-gated LLM ≈ "use AI for ambiguity; deterministic software for truth
  you can calculate or verify."
- Attributability contract ≈ the observability requirement ("who decided
  what: customer / agent / rule engine / operator / supplier?").

### 8.2 Corrections v1 missed — now adopted

**(a) The full trip lifecycle is the aggregate state machine — and it is
richer than the repo's current one.** v1 pointed at "the existing lead/trip
machine" without reconciling. The taught lifecycle:
`INTAKE → NEEDS_INFORMATION → FEASIBILITY_CHECK → PLANNING →
AWAITING_CUSTOMER_APPROVAL → APPROVED(+freshness recheck) →
BOOKING_IN_PROGRESS → BOOKED → CHANGE_REQUESTED → IN_TRIP → COMPLETED`,
with `ESCALATED` as an exception state reachable from many states. Task
opened (T-O1): reconcile the repo's status machine against this set — some
taught states exist in the repo under other names, several do not exist at
all (FEASIBILITY_CHECK, APPROVED-recheck, CHANGE_REQUESTED, IN_TRIP).

**(b) The four-question template per state** (what is true / what can
happen / what cannot happen / what moves us out). Every state in §2 now
gets this block. The key taught insight v1 lacked: **NEEDS_INFORMATION
does not freeze the system — only dependent work freezes** (non-blocked
searches may continue). Sim #2's run froze *everything* on
Travel-Dates+Purpose; under the v2 model the correct behavior is: enter
`NEEDS_INFORMATION`, continue non-blocked work (e.g., destination
confirmation), ask, and block only `fare_quote`/`booking`.

**(c) `required_for` gates instead of global requiredness.** A field is not
"required"; it is `required_for: [fare_quote, booking, entry_validation]`,
and requiredness varies by lifecycle stage (child ages: important in
planning, required at pricing, blocking at booking). This retroactively
explains Sim #2's blocking semantics: blocking on Travel-Dates+Purpose at
*intake* may have been stage-correct, but the banner rendered it as a
global block. Task (T-O2): replace the packet's boolean missing-flags with
`required_for` maps and render blockers per next-intended-step.

**(d) Event vs Condition vs Failure vs Risk are four different things.**
v1's vocabulary had only events. Adopted: *events* (observable, append to
log: `customer_responded`, `fare_changed`, `reminder_timer_expired`),
*conditions* (currently-true, derived: `customer_response_missing`,
`fare > approved_budget`), *failures* (attempted-and-did-not-work:
`ocr_failed`, `provider_call_failed` — also logged), *risks* (might happen
— **not log events**; they materialize as conditions when thresholds/timers
fire). The orchestrator reacts to events and conditions, never to risks
directly.

**(e) Decision layer made explicit: observe state → detect gap/problem →
choose action.** v1 had actions but no decision layer. Adopted, including
the taught distinctions: **dependency** (B needs A) vs **gate** (we make B
wait for A because A decides whether B is worth doing — e.g., entry/visa
feasibility before paid searches) vs **parallelizable**; **short-circuiting**
(don't spend an LLM call on a corrupt input); **request failure vs goal
failure** (this plan infeasible → NEEDS_REVISION with alternatives; goal
infeasible → escalate/human).

**(f) Permission tiers + read/write split + retry policies.** The action
taxonomy (§4) gains three columns: `class` (read | recommend | write),
`autonomy tier` (cost-of-mistake determines it — search is reversible,
₹2L charge is not), and `retry policy` (free / with duplicate protection /
only with idempotency key / very careful).

**(g) Idempotency and `*_RESULT_UNKNOWN`.** v1 mentioned reprocess
idempotency incidentally. Adopted formally: every write action carries an
idempotency key; `BOOKING_RESULT_UNKNOWN` is its own component state
(timeout ≠ failure); partial completion produces aggregate
`BOOKING_EXCEPTION` with component states (`flight: CONFIRMED, hotel:
CONFIRMED, disney: FAILED`) — v1's per-entity machines now extend to
**BookingComponent** (`not_started → in_progress → confirmed | failed |
result_unknown`) alongside the aggregate.

**(h) Freshness as a fact state.** Approval→execution needs a recheck
because prices/availability decay. Facts already carry `maturity` in the
repo; adopted: fact states gain `fresh → stale`, and validation includes
"evidence checked recently enough" as a deterministic check.

**(i) Queues/jobs for side-effectful work.** Long-running or
externally-visible work (booking, payments, reminders) is a **Job**
(`queued → running → done | failed | unknown`), consumed by workers,
emitting events — the web request never performs writes inline. Intake's
LLM calls are read-class and stay inline (cheap, gated); booking is
job-class. State consistency under concurrent mutators (customer WhatsApp +
operator edit + provider event) is the orchestrator's conflict resolution,
same precedence machinery as L3.

**(j) Trip state vs customer memory, explicitly separated.** "Trip state =
what is true now; customer memory = what may help decisions. Do not mix
them." v1's Person entity conflated these (preferences can come from
memory); now: trip-state facts and memory-enrichments are different planes,
memory only *suggests* defaults, never asserts trip facts.

**(k) Two output planes** — operator-facing and traveler-facing renderings
of the same state (v1 had only the operator packet).

### 8.3 Sim #2 re-read under v2

- The run should have transitioned `INTAKE → NEEDS_INFORMATION` (event:
  `lifecycle.changed`, plus `lead.persisted`) — FND-0272 is the missing
  transition, not just a missing save.
- Allowed actions in `NEEDS_INFORMATION` include `run_nonblocked_searches`
  — the total freeze we observed was a v1-model artifact.
- The banner must render `required_for(next-step)` open questions — the
  four blocked items were conflated across stages (T-O2).
- Meera's constraints bind to Person(Meera) with
  `required_for: [itinerary, booking]` — attribution is not cosmetic; it is
  what makes the constraint *enforceable* in later states.

### 8.4 Updated migration

- **Phase 0** (unchanged in code, reframed): `lead.persisted` = the
  `INTAKE → NEEDS_INFORMATION` transition event; FND-0272 fix + A14 E2E.
- **Phase 1** (landed): amount-scoped scope guard = A-merge precedence rule.
- **Phase 2–4** (unchanged): cue-guards, speaker slots, invariants.
- **Phase 2.5 (new, T-O1):** lifecycle reconciliation — map the repo status
  machine to the taught lifecycle; name the deltas; propose additive states.
- **Phase 4.5 (new, T-O2):** `required_for` gates replacing boolean
  missing-flags; banner renders per-next-step blockers.
- **Later:** booking-phase entities (BookingComponent, Job queue,
  idempotency keys) apply the same ontology to the execution half; intake
  realignment does not block on them.

### 8.5 Source

Taught model: Pranay's Waypoint systems-training sessions (state machines,
orchestration, agent loops — "state = where the trip currently is; action =
work performed in the state; event = something that happened; transition =
event moves trip between states"; idempotency; component states; queues;
permission levels). The teachings are design doctrine for this repo's
intake/booking architecture — treated as owner doctrine, above persona
judgment, and now encoded here as the ontology's v2 contract.
