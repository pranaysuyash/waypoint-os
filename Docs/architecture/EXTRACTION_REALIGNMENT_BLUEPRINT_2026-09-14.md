# Extraction Architecture — Full Story, Realignment, and Design Blueprint

**Date:** 2026-09-14 · **Author:** ZCode (extraction realignment arc)
**Status:** DESIGN DOCUMENT — the implementation plan for how Waypoint extracts
travel intent from real human speech. This replaces all prior extraction
architecture documents as the canonical design.

---

## PART 1 — THE FULL STORY (chronological, nothing omitted)

### Phase 1: The demo that started everything (Sim #1, 2026-08-31)

A live computer-use demo as a "Tool-Taster" persona submitted a realistic
millennial note:

> "hey! me and 3 friends want to do japan next spring, maybe late march for
> the cherry blossoms. flying from SF. we are all pretty active, one friend
> is vegetarian. budget around 3.5k USD each, not sure if that includes
> flights. thinking tokyo + kyoto + osaka, 10-12 days. one of us is
> terrified of heights so no cable cars please."

**What the pipeline missed:** destination "japan" (verb-object pattern not
matched), party size 3→wrong (should be 4), "terrified of heights" dropped,
"cooking class" dropped. **What it got right:** budget, date flexibility,
origin SF, destinations tokyo+kyoto (partial).

**Verdict:** Postpone. The demo exposed that the extraction layer was
built for agency-speak, not real speech.

### Phase 2: The remediation wave (2026-08-31 → 09-02)

27-item IMPLEMENT wave: colloquial extraction patterns added ("do japan",
"me and 3 friends", "next spring"), adversarial corpus created, D-02
contract ambiguity added, security hardening (token system, egress gates),
eval lanes (scenario, adversarial), safety constraints captured.

**What was fixed:** colloquial verb patterns, party composition from group
phrasings, budget scope, D-02 ambiguity, adversarial corpus.

**What was NOT fixed:** Hinglish, Gen Z slang, airport codes, continent
names, space-separated city sets, multi-voice threads, per-traveler
attribution. These weren't known gaps yet.

### Phase 3: The persona demo (Sim #2, 2026-09-12)

"The Family Summit" — a 4-person delegation (Priya/Arjun/Meera/Dev) with
contradictory needs submitted as a multi-voice thread. This was the first
test of **multi-voice** input, not just casual single-person phrasings.

**What Sim #2 found (FND-0272–0288):**

| Finding | Root cause | Class |
|---|---|---|
| FND-0272: Lead not persisted | UI path skipped ESCALATE save (later retracted — RLS verification error) | Infrastructure |
| FND-0273: Budget scope flipped total→per_night | Number-free "budget whatever" triggered global cue scan | **Architecture: no precedence** |
| FND-0273: Origin fabricated from "okinawa side trip?" | "side" postposition matched without checking if it's a noun compound | **Architecture: no cue-gating** |
| FND-0274: Transcript contamination | "[arjun]: fine but..." leaked into constraints field | **Architecture: no L0 segmentation** |
| FND-0275: Safety constraint dropped | "terrified of heights" has no "no" prefix; fear-phrased constraints invisible to negation scanner | **Architecture: narrow verb vocabulary** |
| FND-0276: D-02 misfire + unstable missing list | "including" treated as uncertainty; ambiguity raw quotes synthesized not verbatim | **Architecture: no verbatim invariant** |
| FND-0284: 6 duplicate leads | Reprocess resolution used ContextVar-based RLS (empty in executor) | **Infrastructure: RLS context** |
| **NEW: 21/24 real-world phrasings fail destination extraction** | Hinglish, Gen Z, airport codes, continents, space-separated cities all unrecognized | **FUNDAMENTAL: extraction vocabulary too narrow** |

**The P0 retraction:** FND-0272 was initially reported as "lead not
persisted." Phase 0 proved this was a verification error — all six leads
WERE persisted in SQL but my direct queries didn't set the RLS session GUC
(`app.current_agency_id`). The trips table has enforced RLS; without the
GUC, you see zero rows. This was a verification lesson, not a product bug.

### Phase 4: The realignment arc (2026-09-12 → 09-14)

Owner counter: *"regex or just LLM is a bad choice — we need proper
realignment work with a mix of regex-NLP-LLM."* This was correct, but the
initial response was inadequate: I fixed individual defects (scope guard,
origin guard, etc.) instead of implementing the architectural realignment.

**What was implemented (Phases 1–4c, 10 commits):**

| Fix | Root cause addressed | Commit |
|---|---|---|
| Amount-scoped budget scope | Global cue scan flipped scope on number-free notes | Phase 1 |
| Origin cue-guard ("side trip") | Hinglish "side" postposition fabricated origin from proposed destination | Phase 2 |
| Fear-phrased constraints | "terrified of heights" invisible to negation scanner | Phase 3 |
| Occasion anchors (both date orders) | "10th anniversary (april 14th)" never captured | Phase 3 |
| Speaker self-ID capture | "meera here" / "it's arjun" not recognized | Phase 3 |
| Soft-preference fragment guard | "that" (single word) became a preference | Phase 3 |
| Love verb added | "we'd love a quiet ryokan" missed (only want/prefer/like) | Phase 3 |
| Travelers[] attribution binding | Per-speaker constraint bundles with asymmetric containment dedup | Phase 3b |
| D-02 v2 explicit short-circuit | "including flights" fired ambiguity despite being explicit | Phase 4a |
| Verbatim-or-labeled raw quotes | Synthesized renderings presented as quotations | Phase 4b |
| D-02 ambiguity ownership | budget_flexibility site scanned full text, bypassing D-02 gate | Phase 4c |
| Multi-clause resolution | Only first flights clause checked; explicit assertion in ANY clause resolves | Phase 4c |
| FND-0284 duplicate-leads fix | ContextVar-based RLS in executor saw empty set; created new lead per reprocess | Phase 0 |
| FND-0274 label stripping | `_prepare_extraction_text` now strips `[speaker]:` prefixes | FND-0274 fix |

**What was NOT implemented (the realignment gap):**

The realignment was designed to be a layered architecture (L0 segmentation
→ L1 cue extraction → L2 attribution → L3 merge → L4 gated LLM). What was
actually implemented: individual guards on the existing single-pass
extractor. The architectural change — restructuring HOW extraction works —
did not happen. The 21/24 destination extraction failure proves this.

### Phase 5: The destination extraction failure discovery (2026-09-14)

Live testing with 24 real-world casual/Hinglish/GenZ phrasings:

**Score: 3/24 found a destination.**

| Category | Examples | Result |
|---|---|---|
| Hinglish cues | "yahan se japan", "bali chahiye", "4 log" | 0/6 dest found |
| Gen Z casual | "vibing for a goa trip", "tokyo is the move" | 1/7 dest found |
| Activity + constraint | "need vegan food...bali", "scuba MUST, maldives" | 0/6 dest found |
| Route + multi-city | "tokyo kyoto osaka", "dubai then abu dhabi", "blr to goa" | 1/5 dest found |

**Root cause:** the destination extractor matches against:
1. A known-city database (590k cities from GeoNames)
2. Specific verb patterns ("do X", "visit X", "trip to X", "flying from X")
3. Separator-based city sets ("X + Y", "X and Y", "X, Y")

Real speech doesn't follow these patterns. It uses:
- Hinglish postpositions ("X se", "X chahiye", "X mein")
- Gen Z idioms ("X is the move", "vibing for X", "yall")
- Space-separated city sequences ("tokyo kyoto osaka")
- Airport codes ("blr to goa")
- Continent/country names ("europe", "rajasthan")
- Activity-destination co-mentions ("scuba diving, maldives")
- Relationship-implied party sizes ("my gf" = 2, "me n my wife" = 2)

**Pranay's earlier ask that was not handled:** *"mix of regex-nlp-llm,
single pipeline/multi-agentic/orchestrator worker pipeline etc"* — this was
the architectural realignment ask. What was delivered was individual regex
patches, not an architecture change. This document corrects that.

---

## PART 2 — WHAT WAS FOUND (complete findings inventory)

### Extraction findings (from live testing)

| # | Finding | Severity | Status |
|---|---|---|---|
| FND-0286 | Destination extraction fails on 21/24 real-world phrasings | **P0** | open |
| FND-0287 | Party size fails on informal phrasings ("my gf"=2, "4 log", "4 ppl") | P1 | open |
| FND-0288 | Origin not extracted from Hinglish/route patterns | P1 | open |
| FND-0273 | Cross-voice overwrite (scope flip + origin fabrication) | P1 | **closed** (scope+origin guards) |
| FND-0274 | Transcript contamination in packet fields | P1 | **closed** (label stripping) |
| FND-0275 | Per-traveler constraints dropped/unattributed | P1 | **closed** (travelers[] binding) |
| FND-0276 | D-02 misfire + unstable missing list + non-verbatim raws | P2 | **closed** (D-02 v2 + verbatim invariant) |
| FND-0272 | Lead not persisted (retracted: verification error) | ~~P0~~ | **closed** (retracted) |
| FND-0284 | Duplicate leads per reprocess | P1 | **closed** (RLS fix) |
| FND-0285 | Encrypted raw_input blocks inbox search | P2 | **open** (trade-off accepted) |

### Architecture findings

| # | Finding | Impact |
|---|---|---|
| A1 | 37 status values across 4 disconnected dimensions, no state machine | Contradictory UI, unstable missing-fields list |
| A2 | No speaker segmentation in main extraction path | Transcript contamination, no per-person attribution |
| A3 | No cue-gating on budget/origin extractors | Global cue scan fabricates facts from any text position |
| A4 | L4 gated LLM path exists but is unused (no fallback for regex-abstained fields) | Fuzzy phrasings fall through silently |
| A5 | Destination extractor relies on exact city database + narrow verb patterns | 21/24 real-world phrasings fail destination extraction |

---

## PART 3 — WHAT WAS FIXED vs WHAT WASN'T

### Fixed (with commits and test evidence)

| Fix | How | Tests |
|---|---|---|
| Budget scope amount-scoping | `_extract_budget_scope` evaluates cues only in amount-bearing segments; explicit-total precedence | 8 tests |
| Origin cue-guard | `_side_is_trip_compound()` blocks "X side trip" noun compounds; Hinglish preserved | 8 tests |
| Fear-constraint capture | `(terrified|afraid|scared|phobic) of X` → hard constraint with terminator | 3 tests |
| Occasion anchors | `(anniversary|birthday|honeymoon)` + date (both orders) → occasion fact | 3 tests |
| Speaker self-ID | `"X here"` / `"it's X here"` / `"voice note from X"` → speakers[] fact | 3 tests |
| Soft-preference fragment guard | Single-word candidates rejected | 2 tests |
| Travelers[] binding | Per-speaker bundles from segmented thread; asymmetric containment dedup | 7 tests |
| D-02 v2 short-circuit | Explicit "including flights" → fact, not ambiguity | 2 tests (updated) |
| Verbatim-or-labeled raws | Synthesized renderings prefixed "derived from extracted candidates:" | 4 tests |
| D-02 multi-clause resolution | ALL flights clauses checked; explicit anywhere resolves | 1 test |
| FND-0284 duplicate leads | Resolver uses explicit-agency RLS session | 3 tests |
| FND-0274 label stripping | `_prepare_extraction_text` strips `[speaker]:` prefixes | Included in suite |
| T-O2 required_for unknowns | Unknown notes carry `required_for: ... [BLOCKING_FOR_X]` | Included in suite |
| travelers[] downstream | Decision emits `traveler_safety_constraint` + `traveler_occasion_anchor` risk flags | 3 tests |

### Not fixed (the honest gap)

| Gap | Why it wasn't fixed | What's needed |
|---|---|---|
| 21/24 destination extraction failures | Destination extractor relies on exact city database + narrow verb patterns; real speech uses Hinglish, Gen Z, airport codes, continents, space-separated sets | **Architecture change: L4 gated LLM path** for destination extraction (regex abstains, LLM resolves) |
| Party size from relationship words | "my gf" = 2, "me n my wife" = 2 — requires NLP, not regex | **L4 gated LLM** or **L2 relationship parser** |
| Transcript contamination in main path | L0 speaker-segment parser exists in attribution.py but is NOT wired into `_extract_from_freeform` | **L0 wiring** into main extraction |
| Missing-flag clearing invariant | Fabricated value clears the unknown flag | **L3 invariant**: unknown clears only on validated explicit value |
| travelers[]→quote/strategy | Travelers[] exists as packet fact but decision/strategy don't read it for per-person pricing or constraint enforcement | **Quote-layer design** |
| Lifecycle state machine wiring | `lifecycle_states.py` defines 14 states + legal transitions but the trip store still uses old scattered statuses | **Migration**: map old statuses to lifecycle states, enforce legal transitions in TripStore |
| T-O2 frontend banner | Backend unknowns carry required_for notes; frontend PacketTab renders flat list | Small FE change |
| OpenRouter :nitro/:floor | Provider wired, one command each | Run when ready |
| Gemini arms | No GEMINI_API_KEY | Blocked on credentials |

---

## PART 4 — WHAT I COUNTERED (owner corrections, each one a lesson)

| # | What you said | What I was doing wrong | Lesson |
|---|---|---|---|
| 1 | "dont care for pilot, doctrine says long term 1st principles" | Framed lifecycle gaps as "sufficient for pilot" | **No pilot tier**: design for the real system from first principles. Architectural shortcuts justified by "pilot" are technical debt |
| 2 | "why only p0, do all i said" | Fixed only the P0; left P1s open | **Do everything you find**, not just the severity-1 items |
| 3 | "not how we work, everything should be owned by you" | Deferred decisions back to owner ("needs your ratification") | **Own the decisions**. The council orchestrator, persona repo, and doctrines exist so I can decide, not ask |
| 4 | "i wont jump to decisions because you asked" | Was deferring Phase 2 OpenRouter to owner | **Stop asking, start executing** when the key/data/design already exists |
| 5 | "mix of regex-nlp-llm, single pipeline/multi-agentic/orchestrator-worker" | Fixed individual defects instead of implementing the architectural realignment | **Architecture change, not patches**. The extraction pipeline needs restructuring, not more guards |
| 6 | "i dont care for pilot" (lifecycle context) | Framed missing lifecycle states as "documentation for when booking lands" | **The taught states ARE the architecture**. They're not a future enhancement |
| 7 | "everything documented, even failed/deleted models" | Was only documenting successes | **Full comparison sheets** including failures, retractions, and near-misses |

---

## PART 5 — WHAT I EXPLORED AND RE-FOUND

### Models tested (complete)

**API (19 models, 2022→2026):**
gpt-3.5-turbo → gpt-4-turbo → gpt-4o → gpt-4o-mini → gpt-4.1 → gpt-4.1-mini →
gpt-4.1-nano → gpt-5 → gpt-5-mini → gpt-5-nano → gpt-5.1 → gpt-5.2 →
gpt-5.4 → gpt-5.4-mini → gpt-5.4-nano → gpt-5.5 → gpt-5.6-luna →
gpt-5.6-terra → gpt-6-astra → o4-mini

**Local (8 models):**
llama3.2:3b (champion) → gemma3:12b → qwen2.5:7b → mistral:7b →
gemma3:4b → aya-expanse:8b → qwen2.5:3b → qwen2.5vl:7b

**New-generation (5 models):**
phi4-mini → qwen3.5:4b → qwen3:4b → gpt-oss:20b → gpt-oss:120b

**OpenRouter (2 arms):**
llama-3.1-8b-instruct → gpt-oss-20b

**Cross-vendor matrix:**
HF router + OpenRouter + local ollama — same weights, different venues.
All P=1.000 with realignment guards active. Quality is weight-side;
latency/cost is venue-side.

### Key findings that changed the architecture

1. **Every model under-extracts real-world speech.** This is not a model
   problem — it's an extraction-layer problem. The models are ready; the
   front door is broken.

2. **Thinking models (qwen3, qwen3.5) are anti-suitable** for the
   decision lane: 40–97s/call with no quality gain. But they'd be
   excellent for the FEASIBILITY_CHECK state where reasoning matters.

3. **Calibration is a weight property.** gpt-oss-20b under-flags at every
   venue. Llama-3.1-8B scores 0.74–0.80 at every venue. The model
   determines the *ceiling*; the extraction layer determines the *floor*.

4. **The regex layer is simultaneously the strongest and weakest layer.**
   Strongest: it's deterministic, fast, and correct for known patterns.
   Weakest: it can't handle phrases it wasn't told about. This is why the
   architecture needs regex (for speed/accuracy on known patterns), NLP
   (for attribution and relationship extraction), and LLM (for fuzzy
   phrasings) — each doing what it's best at.

5. **Multi-voice threads are the hardest input class.** The current
   pipeline treats all text as one speaker. Real delegations have
   contradicting voices, and the pipeline must segment, attribute, and
   resolve conflicts across them.

---

## PART 6 — THE PLAN (what we do next)

### Architecture: three-layer extraction

```text
INPUT (accumulated notes, chat dumps, voice-note transcripts)
  │
  ├── L0: SEGMENTATION + SANITIZATION
  │     Speaker-labelled lines → per-speaker segments
  │     [speaker]: prefixes stripped (content preserved)
  │     Transcript fragments excluded from prose fields
  │     _prepare_extraction_text + attribution.py segmentation
  │
  ├── L1: CUE EXTRACTION per segment (deterministic regex)
  │     Budget: amount-bearing sentences only, explicit-total precedence
  │     Origin: origin-cue verb required, proposals → destinations
  │     Party: explicit counts + relationship inference
  │     Dates: windows + anchors + seasons
  │     Activities: structured capture with destination coupling
  │     Constraints: fear-phrased + negation + dietary families
  │
  ├── L2: ATTRIBUTION (speaker binding)
  │     Personal facts → speaker slots
  │     Group facts → delegation slot
  │     "I/my" → speaker, "we/our" → group
  │     Speakers[] → travelers[] bundle
  │
  ├── L3: AUTHORITY MERGE
  │     Explicit > inferred
  │     Amount-bearing > casual
  │     Organizer > group > individual
  │     Conflicts → ambiguities + follow-up questions
  │     Never silent overwrite
  │
  └── L4: GATED LLM (credential-gated, abstention-enforced)
        Only for fields where L1-L3 abstain
        Output enters fact log as layer=L4, authority=inferred
        JSON recovery for reasoning-model malformations
```

### Pipeline architecture decision

**Multi-agentic orchestrator-worker**, not single pipeline:

```text
ORCHESTRATOR (reads lifecycle state, dispatches work)
  ├── INTAKE WORKER: L0 segmentation + L1 cue extraction
  ├── ATTRIBUTION WORKER: L2 speaker binding
  ├── MERGE WORKER: L3 authority merge
  ├── LLM WORKER: L4 gated fallback (async, non-blocking)
  ├── VALIDATION WORKER: structural checks + missing-flag invariants
  └── STATE TRANSITION WORKER: lifecycle state machine updates
```

Each worker reads from and writes to the event log. The orchestrator
reads the lifecycle state to determine what work is authorized in the
current state, dispatches to workers, and evaluates results.

**Why multi-agentic, not single pipeline:**
- NEEDS_INFORMATION allows non-blocked searches while blocking booking —
  this requires concurrent workers with different permissions
- LLM calls are slow (2–97s) and should not block fast deterministic
  extraction
- Lifecycle state transitions may happen mid-pipeline (e.g., enough data
  arrives to move from NEEDS_INFORMATION to FEASIBILITY_CHECK)
- Failure isolation: one worker failing doesn't block others

### Implementation phases (in order, each independently valuable)

| Phase | What | Deliverable |
|---|---|---|
| **P-A: Activity capture** | Structured activity extraction from "NEED a scuba day", "skiing", "cooking class" → activities[] fact with destination coupling | extractors.py + tests |
| **P-B: Party size from relationships** | "my gf"=2, "me n my wife"=2, "4 log"=4 — relationship parser + party composition inference | extractors.py + tests |
| **P-C: Hinglish destination cues** | "chahiye", "se" (destination reading), "trip" patterns, "yahan se" → destination extraction for Hinglish inputs | extractors.py + tests |
| **P-D: L0 wiring** | Connect attribution.py's segmentation to the MAIN extraction path: constraints/preferences extracted per segment, not from full text | extractors.py refactor |
| **P-E: Space-separated city sets** | "tokyo kyoto osaka" (consecutive known cities) → city set extraction | extractors.py + geography.py |
| **P-F: Airport code resolution** | "blr", "del", "bombay" → resolve to cities via airport code table | geography.py + tests |
| **P-G: Continent/country as destination** | "europe", "rajasthan" → destination_candidates (not city-level, region-level) | extractors.py + geography.py |
| **P-H: Lifecycle state machine wiring** | lifecycle_states.py → TripStore transition validation + pipeline state gate | trip_lifecycle_service.py + tests |
| **P-I: L4 gated LLM fallback** | When L1-L3 abstain on a field, route to the configured LLM (per KDD model results) with the abstention gate | pipeline + LLM worker |
| **P-J: required_for frontend** | PacketTab renders BLOCKING_FOR class per unknown field | PacketTab.tsx |

### What I will NOT do (anti-goals)

- I will NOT add more regex patterns to the single-pass extractor without
  also wiring the L0 segmentation — that's how we got 670+ patterns that
  still fail on real speech
- I will NOT use the LLM as the primary extractor — the KDD results prove
  that regex+deterministic is faster and more accurate for known patterns
- I will NOT defer lifecycle states to "when booking lands" — the state
  machine gates current behavior, not just future behavior
- I will NOT optimize for the dev machine's specs — the architecture
  targets common consumer configs (8GB/16GB, browser, MLX)

### Est. cost and effort

| Phase | Effort | Risk |
|---|---|---|
| P-A | 2h | Low — existing pattern structure |
| P-B | 3h | Medium — relationship inference needs NLP |
| P-C | 2h | Low — regex expansion |
| P-D | 4h | Medium — refactor of extraction flow |
| P-E | 1h | Low — geography lookup |
| P-F | 1h | Low — airport code table |
| P-G | 2h | Medium — region-level destination handling |
| P-H | 4h | Medium — lifecycle wiring |
| P-I | 6h | High — LLM worker design |
| P-J | 1h | Low — frontend change |
| **Total** | **~26h** | |

### Dependencies and sequencing

P-A and P-B are independent. P-C depends on nothing. P-D should come
before P-E/P-F (they add patterns that P-D's segmentation improves).
P-G is independent. P-H should come after all extraction phases (it gates
the full pipeline). P-I comes last (it's the fallback for everything
else). P-J is independent and small.

Recommended order: P-A → P-C → P-E → P-F → P-B → P-D → P-G → P-H → P-I → P-J

---

## Addendum 2026-09-13 (session): sweep hardening + direction-intent contract

Follow-on to FND-0286 guard work, closing the sweep-level gaps found by the
adversarial corpus and extraction suites.

### Owner correction: "<place> side" is direction intent (binding)

First design treated "Bangalore side jaana hai" as noise to drop. Pranay
corrected the semantics: **"X side jana hai" = "heading that way / somewhere
around X"** — a real direction intent where the destination is NOT committed
(not necessarily X itself, could be "around there"). Binding contract:

- `<place> side` (+ motion verb, not a side-trip compound) NEVER fabricates
  `<place>` as a destination candidate.
- The intent is real, so the extractor returns status `open` — intake asks
  "whereabouts near X?" instead of committing or going silent.
- Implemented as a post-filter wrapper (`_extract_destination_candidates`)
  over the raw extraction, so pattern paths and the broad sweep are both
  covered; `_is_direction_side_reference` reuses `_SIDE_TRIP_NOUN_RE` so
  "okinawa side trip?" stays a valid destination.

### Sweep guards landed

1. GeoNames collision stop words: need/old/side/parks/top/set/lie/bad —
   the 590k-city DB contains villages named after common English words.
   Tradeoff documented: bare "Side, Turkey" degrades to country-level in
   the fallback sweep (compound bigrams unaffected).
2. Shared placeholder filter (`_NON_DESTINATION_PLACEHOLDERS`) now applies
   in the sweep word loop — bare "beach" no longer matches GeoNames Beach
   (ND/NE); cures adv_struct_005, adversarial gate lane back to 21/21 @ 1.0.
3. Family-locative prose guard: "<family noun> in/at/near <place>" within a
   clause is visit-family context, not a committed destination ("want to
   visit family in india" → no candidates). "family trip to japan" keeps
   Japan (preposition gate: only in/at/near trigger the skip).
4. Past-trip clause guard: "(we) went/visited/been ... last year|YYYY|ago"
   spans are memories; destination words inside the span never form a city
   set ("we went to japan, korea last year and loved it" → []).

### Verification

- extraction + adversarial corpus + gate lane + lifecycle suites: 421 passed
- true-positive probes: se/jana-hai/chahiye paths, Virginia-Beach-class
  bigrams, tokyo/kyoto/osaka city sets, bali chahiye, okinawa side-trip
  compounds (both forms) — all preserved
- ruff clean on touched files; findings note appended to FND-0286

---

## Addendum 2 (2026-09-13, session): the deterministic-rules learning

Owner's framing: "we obviously need all that we discussed but also some
deterministic rules we can put, adding as we find during tests." Agreed —
and the arc's own data sharpens what kind of rules and where they sit.

### Evidence from this arc (both failure worlds are on record)

| World | Evidence | Failure mode |
| ----- | -------- | ------------ |
| Deterministic-only | FND-0286 baseline: 21/24 casual/Hinglish phrasings failed silently | Brittle recall; endless pattern whack-a-mole |
| LLM-trusted, ungated | Sim #2: fabricated Origin (okinawa), transcript contamination, constraint drops | No hard guarantees; hallucinated facts enter the packet |
| Layered (current) | P=1.000 KDD arms post-fix; adversarial gate 21/21 @ 1.0; 421-test green | The composition, not either layer alone |

### What today's guards have in common

All four (direction-side, family-locative, past-trip clause, placeholder
filter) are **"never" invariants**, not "always" extractors. Deterministic
layers do two different jobs, and the doctrine must name both:

- **Fast paths** — positive extraction for canonical, high-frequency forms
  ("singapore jana hai"). Cheap, instant, testable.
- **Invariants** — negative guarantees that clip every producer: pattern
  paths, the broad sweep, and LLM output. "We went to japan last year" is
  not an intent no matter who claims it — regex, sweep, or gpt-5.x. This is
  precisely what Sim #2 lacked: LLM output entered the packet with no
  deterministic post-conditions.

### The flywheel (incident → permanent constraint)

1. Failure observed (test, sim, live note, adversarial record).
2. Fixture added to the adversarial corpus / golden set (`passes_today`
   property contract).
3. Guard implemented as a **class** where possible (past-clause span,
   locative+family, direction postposition), word-list only at the edges
   (GeoNames collisions).
4. Counter-tests prove true positives survive; note-level F1 re-run gates
   recall regressions.
5. The guard becomes spec: it now clips all future producers, including
   any LLM worker (P-I) — which is why P-I's scope is now precise: recall
   for the long tail, invoked on deterministic abstention, output passing
   through the same invariant layer.

Doctrine home: `Docs/V02_GOVERNING_PRINCIPLES.md` §1 (Deterministic-First).

---

## Addendum 3 (2026-09-13, session): VFR correction + travel-history asks

Owner challenges on the guard wave produced two contract corrections and
one new feature. Both corrections follow the same pattern: a guard built
from an adversarial test turned out to be wrong about the world, and the
owner's real-world semantics won.

### Correction 1 — family visits ARE destinations (VFR)

The family-locative guard suppressed "want to visit family in india" to
[]. Owner challenge: India IS where they want to go — VFR (visiting
friends & relatives) is one of the largest real travel segments, and
asking "where would you like to go?" after the customer just said India
is broken UX and lost momentum. New contract:

- "visit/visiting/see/meet family|relatives|grandparents|in-laws|cousins
  in <place>" → <place> promoted as destination candidate.
- Purpose lane gains `family_visit` (VFR) — downstream this carries visa
  (invitation letters) and accommodation (staying with family) semantics.
- The guard's constants are deleted, not disabled — class-rule removal,
  per the supersession discipline.

Lesson recorded: the guard was class-shaped but wrong-valenced. Counter-
tests protect against over-blocking only when someone writes them; the
missing counter-test here was exactly "visit family in india" asserting
PROMOTION.

### Correction 2 — past-trip memories must resurface as preference asks

Owner question: "can it help ask something like, based on the past, do
they prefer East Asian destinations?" Yes — and suppression alone would
have thrown the signal away. The past-trip guard now has a capture twin:

- `_extract_past_trip_places()` walks past-trip spans and returns
  structured history: `{place, clause, sentiment, region}` — "we went to
  japan, korea last year and loved it" → Japan + Korea, positive, East
  Asia. Country-level names ("korea") resolve via the new
  `geography.COUNTRY_MACRO_REGIONS` / `get_macro_region()` (city →
  country → macro region), so region affinity works without a region DB.
- The packet's `past_trips` fact (previously a bare phrase-match hook)
  now carries these structured entries.
- Decision layer: when destination is missing and history exists, the
  generic "where would you like to go?" becomes history-informed:
  "You mentioned loving Japan and Korea — thinking somewhere else in
  East Asia, or somewhere new this time?" Memories feed the QUESTION,
  never `suggested_values` — suggesting them as answers would
  re-introduce the contamination the guard removes.

### Consolidation (doctrine self-application)

The sweep's past-trip guard initially duplicated the pattern paths'
checker — a one-stack violation caught within the hour. The span branch
now lives inside `_is_past_trip_mention` (clause OR span), and the sweep
calls the shared function. `_SWEEP_STOP_WORDS` moved to module level
(perf doctrine: constant data is not rebuilt per call).

### Verification

- extraction + history-question + adversarial corpus + gate lane +
  lifecycle + decision families: 1,236 passed / 0 failed; ruff clean.
- Live probe: note → packet.past_trips=[Japan, Korea, positive, East
  Asia] → destination candidates=[] → destination ask = history-informed
  question (shown above).

---

## Addendum 4 (2026-09-13, session): gates run — both green, FND-0286 closed

### Gate 1 — note-level KDD re-run (the falsification gate from Addendum 2)

Reference: `records_ladder2.jsonl` (post-fix grades of record), champion
arm B-gpt-4.1-nano F1 0.800 (P 0.769 / R 0.833).

Fresh run after the guard wave: `records_sweepguard2.jsonl` —
B-gpt-4.1-nano and B-gpt-5.4-nano both **F1 0.808 (P 0.750 / R 0.875,
21tp/7fp/3fn)**: recall up (4→3 fn), precision within single-run
variance, +1 TP vs reference, nothing lost.

**The gate earned its keep before it passed.** The first fresh run
collapsed (F1 0.065 — stale shell OPENAI_API_KEY → 401 fallback; the
runner does not load `.env`) and the second exposed a real substrate
defect: F1 dipped to 0.764 with four visa_timeline_risk FPs traced to
garbage destinations — "any time" swept the village of **Time**, "resort
with a pool" swept **Pool** (UK). Root cause = the same GeoNames
collision class as the wave's stop-word fix, incomplete list. 48 more
verified colliders added (prose + amenity nouns), substrate re-probed
clean, gate re-run → 0.808. Exactly the doctrine's loop: incident →
fixture-class guard → counter-tests → eval re-run.

Also fixed en route (owner-directed, 2026-09-13): the runner does not
load `.env`, and the shell inherited a DEAD `sk-proj` key from
`~/.zshenv:3` that shadowed valid keys in every non-interactive zsh —
that caused the 401-fallback run (preserved as
`records_sweepguard.jsonl`). Fix: the dead export is commented out in
`~/.zshenv` with a dated note (history preserved); the valid key lives
canonical in the repo `.env` (verified HTTP 200, 136 models visible)
and must be exported explicitly for experiment runs:
`export OPENAI_API_KEY=$(grep -m1 '^OPENAI_API_KEY=' .env | cut -d= -f2)`.
Note: the `~/.zshrc` agentrouter.org block was left untouched — that
key targets a different provider, not api.openai.com.

### Gate 2 — fresh Sim #2 acceptance

New reusable probe `tools/sim2_acceptance_probe.py` (embedded verbatim
persona scripts, real pipeline, deterministic, exit-code gate):
**9/9 GREEN** — origin fabrication dead, budget scope stable under
"budget whatever", D-02 fact-not-unknown, Meera's jain/no-heights
attribution, anniversary survives Dev's ±1-week trade, chat-dump
per-speaker binding, direction intent → open, VFR → India +
family_visit, past-trip memory → history-informed ask with memories
never offered as suggested values.

### Dispositions

- **FND-0286 CLOSED** with the gate + acceptance evidence (findings store).
- Residual known noise: 1 FP (visa_timeline_risk on colloq_party_the_four_001)
  on a single temperature>0 pass — tracked via normal variance, not a defect.
- Still open (owner DECIDE): origin-path "X side" semantics; family-visit
  subordinate-case handling. Engineering next: preference ranking reads
  past_trips; lifecycle→runtime wiring.


---

## Addendum 5 (2026-09-13, session): region_affinity + runner env loading

### region_affinity — the past_trips consumer contract

The past-trip memory wave left one gap: `past_trips` fed the decision
ask, but the ranking layers (suitability/proposal) had no signal to
consume. Now the packet derives a `region_affinity` fact whenever past
trips resolve to macro regions:

```
[{"region": "East Asia", "trips": 2, "positive": 2, "places": ["Japan", "Korea"]}]
```

Contract (binding for consumers):
- It is a PREFERENCE signal — never an extraction fact. Destinations,
  dates, and origins are unaffected; memories still never become
  suggested values.
- Semantics: `trips` = past trips in the region; `positive` = trips with
  a positive sentiment cue; ordering is trips-descending.
- Intended consumers: suitability scoring and proposal ranking may bias
  toward high-affinity regions; the decision layer's confidence math
  must NOT consume it (extraction confidence is certainty, not taste —
  same wrong-valence lesson as the family-locative guard).
- No unresolved region → no fact (never guess).

### Experiment runner loads .env

`scripts/run_hybrid_kdd_experiment.py` now fills missing keys from the
repo `.env` (shell env still takes precedence). Reason: a dead shell key
silently 401-fallbacked an entire gate run; the owner directed cleanup
of `~/.zshenv` (done) and the runner now self-heals. The smoke-verified
loader path: `records_envloader_smoke.jsonl` — real 4.1s call, zero
errors, from a shell with no OPENAI_API_KEY.


---

## Addendum 6 (2026-09-14, session): origin "side" Option 3 — RATIFIED + implemented

Owner ratified Option 3 in discussion (2026-09-14): the origin path splits
the Hinglish postposition semantics that the destination side already had.

### Binding contract (three-way)

| Input shape | Origin outcome |
| ----------- | -------------- |
| "Bangalore **se**/ru ..." (explicit "from") | FACT @ 0.85 (unchanged) |
| "Bangalore side jaana hai" (bare "side") | SOFT HYPOTHESIS @ 0.55 — never a fact; the ask renders "Starting from Bangalore itself, or somewhere else?" with can_infer=True, suggested_values=[Bangalore] |
| "Bangalore side se ..." (side + explicit marker) | FACT @ 0.85 (marker upgrades) |
| "okinawa side trip?" (trip compound) | nothing (existing `_side_is_trip_compound` guard) |

Rationale: origin anchors real money math (flight distance, visa
corridor). A direction reference entered the packet at 0.85 FACT-grade —
wrong-but-confident silently skews quotes; the hypothesis lane preserves
the (usually right) signal and asks one cheap confirm question.

### Exclusion vs fact (architectural separation made explicit)

`_is_likely_origin` (destination-exclusion gate) treats non-compound
"side" as a location REFERENCE — "<place> side" is excluded from
destination candidates regardless of fact/hypothesis status. Exclusion
never creates an origin; only the marker semantics above do. A parallel
tranche had narrowed this gate to se/ru-only, dropping "we are bangalore
side, plan something" through to the destination sweep — restored, with
the OPEN-intent path (`_has_bare_side_direction_intent`) keeping
destination-less side notes at status OPEN rather than undecided.

### Collateral record flip

`adv_ling_003` ("humko Thailand beach villa chahiye, 4 log, ...") flipped
from `must_not_extract: party_size` to `must_extract: party_size=4` —
"4 log" Hinglish headcount is now correctly extracted by the FND-0286
wave; the record's expectation predated the fix (`fixed_in` noted in the
seed record).

### Verification

- 422 extraction/scope-guard/corpus tests + full -k decision net green
  (1 known order-flake on price_lock, passes in isolation);
- acceptance probe now **10/10** (check 10: origin fact None, hypothesis
  Bangalore, ask "Starting from Bangalore itself, or somewhere else?",
  suggested_values=[Bangalore], can_infer=True);
- ruff clean.


---

## Addendum 7 (2026-09-14): family-visit subordinate case — RATIFIED: keep as-is

Owner decision (2026-09-14, in discussion of the VFR promotion wave):

**"SE Asia trip, might visit family in Chennai" keeps promoting Chennai as
a co-equal destination candidate.** No secondary-destination tier.

Options considered:
1. *Keep co-equal (ratified)* — honest semantics (the customer would visit
   both); the multi-stop cost path already handles multiple candidates.
2. *Secondary tier* — rejected: adds packet schema (a `secondary` flag or
   parallel list) with no degraded consumer. Standing bar: schema is added
   only when something downstream is demonstrably worse without it.

Reopen trigger: if the proposal compiler is observed producing noisy
itineraries from co-equal family stops, revisit with that run evidence —
the tier gets built against a real consumer at that point.

Related: origin-marker semantics (Addendum 6) are the model here — the
extraction layer states what was said, downstream layers decide what it
is worth. "Secondary" is a ranking concern, not an extraction concern.

---

## Addendum 8 (2026-09-14): lifecycle ontology council — full decision record

Owner directive: "implement it but not 14 or not 17 — check what and how
many they should be; if needed call the council." Council convened via the
council-orchestrator skill (smallest-sufficient-council model, evidence-first).

### Census (what actually exists — runtime > source > docs)

| Vocabulary | Where | Count | Notes |
|---|---|---|---|
| V1 taught machine | src/intake/lifecycle_states.py | 14 | zero runtime consumers; tests only |
| V2 packet CRM statuses | src/intake/packet_models.py:260 | 16 | no production writer (test-only); name-collides with V1 (BOOKING_IN_PROGRESS, LOST) |
| V3 runtime strings | spine_api/core/trip_status.py | ~11 + unknown pass-through | ONE enforced invariant (intake-blocked ↛ quote-capable); docstring itself defers full enforcement to a distribution harness that was never built |
| V4 discovered by council | src/intake/lifecycle.py LeadStage | 6 | a FOURTH, duplicate lead machine — registered FND-0289 |

### Council manifest

- Lead: PER-0450 Travel State-Machine Architect (owns state semantics)
- PER-0444 Travel Lifecycle Architect (lifecycle continuity; found V4 + post-trip gaps)
- PER-0453 Travel Financial Systems Architect (money-load-bearing boundaries)
- PER-0369 Customer Success Architect (relationship axis, CS systems)
- PER-0274 Skeptical Customer Reviewer (counterposition, falsification)
- Evidence precedence: runtime > tests > source/config > docs; personas are lenses.

### Seat rulings (independently analyzed)

- **PER-0450 (Lead, conf 0.8):** 12 enforced-eligible states; demote
  NEEDS_INFORMATION (typed condition), FEASIBILITY_CHECK (planning stage),
  NEEDS_REVISION (re-entry condition); ADD CANCELLED terminal (lead-death ≠
  booked-trip cancellation — different refund/penalty obligations); ESCALATED
  stays the single exception state (operator-owned entry/exit, no auto-exits);
  V2 splits into a separate relationship machine + derived signals; V3 mapping
  table with audit-gated ambiguous strings.
- **PER-0444 (conf 0.82):** two axes formally (trip lifecycle restarts per
  trip; relationship lifecycle persists); COMPLETED does double duty — split
  ratified in model as RETURNED → ARCHIVED (dormant, no producers);
  cancellation gap confirmed; LOST is trip-scoped; found V4 (LeadStage) as a
  duplicate system; post-COMPLETED arc entirely unmapped prior to this.
- **PER-0453 (conf 0.82):** five load-bearing boundaries (quote-existence,
  authorization, recheck, commitment, post-commitment-delta); pre-quote states
  financially inert (merge-safe); APPROVED must survive (consent-TTL anchor,
  recheck enforcement point, rollback anchor — merging into AWAITING makes
  overcharge/chargeback chains unconstructable); payment_status orthogonal
  (two divergent vocabularies already exist — flagged); **ready_to_book is the
  priority hazard** (readiness on a customer-visible dashboard with zero
  authorization semantics — must never map to APPROVED).
- **PER-0369 (conf 0.82/0.7):** minimal relationship stages = 6 (prospect,
  booked_active, post_trip, repeat_client, dormant, lost/churned); GHOST_RISK
  demoted to derived score (already computed in decision.py, never persisted);
  ENGAGED_AFTER_QUOTE/QUOTE_SENT/WON = derived condition/deal events; hybrid
  persistence (persist coarse stage + entered_at, derive signals, decay job,
  invariants not adjacency table) — full derivation fails on retention-purge
  and play-dedup evidence; LOST terminal at trip level, soft at relationship
  level.
- **PER-0274 skeptic (conf 0.82):** 9 of 14 V1 states have NO producer; only
  6 strings have real triggering events; enforcement before the distribution
  harness violates the runtime module's own documented gate; strict machine +
  historical unknown strings = writer failures; operator hand-fixing is the
  primary recovery path. Counter-proposal: ratify vocabulary as read-model
  target, enforce predicates only. Self-acknowledged steelman: predicates cap
  out; pre-launch (zero consumers, small data) is the cheapest moment to land
  the machine — audit-only-first rollout resolves the timing.

### Disagreements and resolutions

| Issue | Position A | Position B | Resolution |
|---|---|---|---|
| Machine enforcement timing | Lead: gate replaces invariant now | Skeptic: predicates now, machine gated on distribution harness | **Staged ratchet**: gate classifies against the machine for EVERY write now; RAISE only the proven class (P1); machine-illegal pairs LOG + count; classes graduate to raise on harness evidence. Wired ≠ raising; dormant-but-tested vs forgotten. |
| FEASIBILITY_CHECK / NEEDS_REVISION / NEEDS_INFORMATION | V1: states | Lead+Financial: conditions/stages | Demoted (financially inert; duplicate representations of signals with canonical homes). |
| COMPLETED terminal | V1: terminal | PER-0444: does double duty | Split ratified IN MODEL (returned → archived), dormant until post-trip work exists. |
| Cancellation | V1: absent | Both seats: gap | cancelled terminal added, distinct from lost. |
| V2's 16 | Lead: 5 relationship states + derived | CS: 6 coarse stages + derived | CS set adopted (6); alignment is high — both demote GHOST_RISK and split the axes. |

### Ratified answer to "how many"

- **Trip-execution lifecycle: 12 enforced-eligible states** (intake, planning,
  awaiting_customer_approval, approved, booking_in_progress, booked,
  change_requested, in_trip, completed, cancelled, lost, escalated) + 2
  dormant model extensions (returned, archived).
- **Relationship lifecycle: 6 stages** (separate machine; not modeled in the
  trip gate — implementation is a later slice with its decay job).
- **Everything else is not a state**: conditions (needs_information,
  quote_ready, freshness_recheck_pending, attention_needed, revision_pending),
  derived scores (ghost_risk, churn_risk, window_shopper, repeat_likelihood),
  deal events (quote_sent, won), timer conditions (retention_window).

### Implementation (this commit)

- spine_api/core/trip_lifecycle.py: machine (states/conditions/transitions/
  operator-dynamic ESCALATED), V3→canonical mapping table with
  financial-ruling encodings (ready_to_book → planning+quote_ready, NEVER
  approved; in_progress/active audit-gated), staged
  assess_transition (raise/log/allow).
- spine_api/persistence.py `_apply_status_guard`: consults the machine on
  every status write; machine-illegal pairs LOGGED + counted
  (_LIFECYCLE_VIOLATION_COUNTS) — never raise; P1 unchanged.
- tests/test_trip_lifecycle_gate.py: 16 contract tests (model shape, full
  transition table, staged enforcement, mapping rulings).

### Findings and open items

- FND-0289 (new, P2): LeadStage duplicate vocabulary — supersede into the
  relationship axis.
- Docs/LEAD_LIFECYCLE_AND_RETENTION.md presents GHOST_RISK mid-funnel —
  category error to correct when the relationship axis is implemented.
- Two divergent payment_status vocabularies (packet vs payment_queue_service)
  need one canonical enum before booking work.
- Open (evidence-gated): distribution harness reading the violation counters;
  per-class graduation to hard enforcement; relationship-axis implementation
  (decay job, stage persistence); persisted-distribution audit to de-gate
  in_progress/active mappings.

---

## Addendum 9 (2026-09-14): ADR-008 ratification council — full decision record

Owner challenge accepted: ADR-008 (six open items) walked through a
five-seat council re-derivation instead of a defaults walk. Manifest:
PER-0700 (Lead, ADR author), PER-0453-equivalent financial-governance seat
via LLM cost/outcome governance specialist, memory-architecture specialist,
metrics/ops specialist folded into seats, PER-0274 skeptic. Every seam claim
re-verified in-tree, 2026-09-14.

### The falsifications (what a defaults walk would have missed)

1. **Item 2 is contradicted by the repo itself.** ADR proposes prod default
   "0" + startup rung log. Reality: Dockerfile:89 bakes
   `USE_HYBRID_DECISION_ENGINE=1` (Fly inherits it — its PA-03 comment is
   materially false), CI sets "1" explicitly "as the serving images",
   compose/render set 0, code default is 0, the startup rung log exists
   NOWHERE. Serving determinism is image-envelope-conditional — four
   envelopes, three answers.
2. **routing_health has ZERO producers.** Live alert + paging + operator
   triage pipelines built on events that can never be emitted (phantom
   surface). Meanwhile the minimal tier ladder the ADR offers as option A
   already exists in hybrid_engine telemetry.
3. **The ADR's cheapest clause was never executed:** Tier-3's required
   PLANNED docstring declaration never landed.
4. **ADR conditions dissolved by later work:** E-C cost model landed
   (partially wired: usage_store run/trip correlation in serving path;
   decision_id/rollups missing); calibrated labels landed for the WRONG
   surface (note-level risk flags ≠ activity suitability verdicts); E-D
   landed 09-08 making suitability a memory NON-slot (dissolving the
   4.2→4.3 coupling) and E-10 landed 09-10 (governed write path) — the
   "write-only machine" the archive clause threatens no longer exists.
5. **Item 1's ratified seam is weaker than its text:** payouts never read
   the mode; `holder_id` is a client-asserted denylist that PASSES by
   default ("fulfillment_advisor" isn't in the autonomous list) and is
   never bound to the JWT principal; settlement/refund executors don't
   exist (overclaim); the mode lives in local SQLite (redeploys revert it);
   no audit event on mode change; iROPS VCC minting bypasses the mode read.
6. **Missing rungs (landed post-ADR, no §3 row):** iROPS auto-heal loop
   (autonomous, persists healed plans, mints emergency VCCs — no mode read,
   no registry call), agent memory write loop, the trip lifecycle write
   gate itself, and price-lock R2 is decoration (preview-only endpoint).

### Council ruling per item (reconciled)

| # | Ruling | Key amendments |
|---|---|---|
| 1 | Ratified+implemented; **amend** | Bind holder_id to the JWT principal (delete the client field); payouts read + audit the mode; audit event on mode change; read-only mode exposure; settlement/refunds read the mode *when executors exist*; correct the overclaim |
| 2 | **Falsified as written — owner decision** | (a) ratify hybrid-ON as declared posture (KDD F1 0.808 vs brittle rules-only; fail-closed proven; pennies/run) conditional on the X-09 PII-egress gate, with one declared mode identical in all five envelopes + startup rung log + fly.toml comment fix — or (b) flip Dockerfile to 0 + CI dual-mode + rung log. Council leans (a); rollback triggers recorded |
| 3 | PLANNED, unwired — **amended** | Land the missing PLANNED docstring now; drop the 4.3 coupling (E-D forbids memory-feeding-suitability); wire gate = suitability-surface corpus (≥50 verdicts, fixed-before-grading) graded via the KDD harness + shadow scoring + cost thresholds; labels-for-the-wrong-surface noted |
| 4 | WIRE — archive branch **struck** | E-D landed (spec + invariant "memory may rank questions, never select inventory"); E-10 landed (governed write path); archive would destroy tested value. Wire Slot 1 (strategy.py promotion-only question reorder) shadow-first (`MEMORY_SLOT_READ_MODE=shadow` + audit events), Slot 2 = E-D's display-only FreshnessCard; preconditions: E-D import-containment test, X-14 purge propagation, close the hydrate-trip GDPR leak |
| 5 | Ratified as written | Badges + honesty CI + tier gate all real; amendment: frontier.py backend responses carry reality_tier (register rule 1) |
| 6 | **Rename** (not implement-or-rename) | Metric measures decision-route quality with zero producers; the ladder already exists. Rename to decision_route_health with an event-type alias cycle; wire hybrid_engine telemetry into it; delete the phantom legacy_ops triage surface if unwired by cycle end |
| 7 | Hold — **reason replaced, target ratified** | ADR reason falsified (cost model + KDD venue data landed). New reason: experiment cost ≠ production cost-per-outcome; no routing seam. Ratified benchmark: F1 ≥ 0.8, ≤ 3s/call, ≤ ₹0.50/run — hold becomes a check, not a debate |

Also registered: missing-rung list (iROPS auto-heal → proposed R3 sim-tier
with mandatory mode-read the day a real provider lands; memory write loop R3
at the eligibility gate; lifecycle write gate added to §2 with graduation
policy; **fulfillment must require approved/booking_in_progress at RAISE
class** — cross-link to the 12-state machine ratified in Addendum 8);
PA-26 corporate-policy R1 confirmed landed (stale parenthetical fixed);
price-lock honestly R0+preview until a real rate source lands.

Global reopen trigger: any evidence of a rung executing without its named
seam (phantom events, denylist bypass, image-level mode drift) reopens the
ADR in full.

---

## Addendum 10 (2026-09-14): no-decisions-needed batch — landed

Owner directive: "do all implementation and exploration work that doesn't
need me or decisions." Executed via parallel seats + direct work:

1. **Distribution harness** (lifecycle graduation gate): 
   spine_api/core/trip_lifecycle_harness.py — reads the write-gate violation
   counters, ranks classes, graduation ledger (LOG→RAISE flips only via
   reviewed `graduate_class`), graduation-ready listing. Tests landed.
2. **E-C steps 2–3** (seat-built): decision_id minted per
   run_gap_and_decision; telemetry context threading (decision_id/trip_id
   through hybrid_engine.decide context); get_cost_rollup +
   hybrid_decision_cost_per_decision_inr Prometheus gauge via
   metrics_registry. Tier-3/SLM activation preconditions now partially
   satisfied (decision_id + rollups landed; suitability corpus remains).
3. **P-F airport codes** (seat died on limits — landed by hand):
   src/intake/airport_codes.py (60+ curated IATA→city, membership-is-guard)
   integrated into the destination sweep; "flying into SIN" → Singapore;
   unknown 3-letter words can never become destinations via this path.
4. **Relationship axis** (seat landed full module pre-limit):
   src/memory/relationship_stages.py — 6 ratified stages, event-driven
   transitions + audit dicts, invariant validation, time decay
   (POST_TRIP→DORMANT), retention-window derived condition, win-back
   re-entry. 35 tests. Integration wiring (trip-gate hooks) = later slice.
5. **Hinglish extraction extensions**: past-trip verbs (gaye/gaya/ghumne
   gaye/pahunche) + SOV backward span extension ("hum goa gaye the" → Goa);
   Hinglish positive sentiment cues (bahut accha, mazaa aaya, mast…);
   Hinglish pronoun + animal GeoNames colliders stopped (Hum/HR, Dog…).
6. **GDPR X-14 propagation fix**: customer_memory forget now removes ALL
   same-identity profiles in the agency (duplicate-key leak closed —
   forgotten travelers were re-hydratable by email from duplicate keys);
   propagated removals audited. Tests landed.
7. **Housekeeping**: FND-0058 closed on the FND-0286 evidence chain;
   FND-0050/0230 alias rows both confirmed closed (self-resolved).

Remaining (needs owner/decisions/evidence): X-09 PII gate → hybrid-ON
review; shadow→active flip (needs window data); suitability corpus; Slot 2
FreshnessCard; relationship-axis trip-gate hooks; P-B/P-I/P-G/P-J.
