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
