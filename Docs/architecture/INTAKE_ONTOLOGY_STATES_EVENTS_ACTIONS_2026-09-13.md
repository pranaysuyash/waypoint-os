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
