# Extraction Realignment — layered regex → NLP → LLM architecture (2026-09-13)

**Trigger:** Sim #2 "Family Summit" (live, 6-note multi-voice delegation)
produced 1 P0 + 4 P1 failures (`Docs/sims/SIM2_FAMILY_SUMMIT_RESULTS_2026-09-12.md`,
FND-0272…0276). Owner verdict: *"regex or just LLM is a bad choice — we need
proper realignment work with a mix of regex-NLP-LLM."*

**Root-cause statement (verified in code):** the current pipeline runs
single-purpose regexes over the **entire accumulated thread as one string**
(`_extract_budget_scope(text)` at `src/intake/extractors.py:1868` scans every
cue phrase anywhere in the text; origin heuristics likewise). There is no
speaker segmentation, no per-fact provenance, and no authority-ordered merge.
Sim #1 proved pure-regex misses colloquial phrasings; the KDD lane proved
pure-LLM lacks abstention and calibration. Both are true because each is
being asked to do the *whole* job. The realignment splits the job.

## 1. Failure → layer mapping (every Sim #2 finding)

| Finding | Failure | Owning layer of the fix |
|---|---|---|
| FND-0273 scope flip `total→per_night` | global cue scan: any "a day"-class phrase anywhere overrides the explicit "3.5 lakhs total INCLUDING flights, hard cap" | **L1 cue-scope + L3 authority merge** — scope may only be set from a segment containing a currency amount; explicit-total-with-amount outranks everything |
| FND-0273 Origin `okinawa` | "okinawa side trip?" (a proposal) bound to origin | **L1 origin-cue guard** — origin requires an origin-cue (from / flying out of / departing / based in) + validated city; proposals bind to destinations |
| FND-0274 transcript leak | `[arjun]: …` chat lines glommed into Constraints/Soft Preferences | **L0 segmentation** — speaker-labelled lines and forwarded headers are transcript segments; only their intent content may enter fields, never the labels/raw lines |
| FND-0275 no-heights + Apr-14 dropped, Jain unattributed | no per-speaker slots; personal statements ("I can't") generalized or lost | **L2 attribution** — per-segment speaker binding; "I"-statements → that traveler's slot; "we"-statements → group slot |
| FND-0276 unstable missing-list + corrupted Raw quotes + D-02 misfire | derived flags computed from corrupted fields; raw snippets not verbatim | **L3 invariants** — missing-flags clear only on explicit-correct values; Raw quotes must be verbatim spans; explicit-cue short-circuits ambiguity detectors |
| FND-0272 P0 persistence | UI-path skip of ESCALATE persistence | orthogonal (separate fix), but the same doctrine: every layer must degrade persistently, never silently |

## 2. Target architecture

```text
thread (accumulated notes, chat dumps, forwards)
  └─ L0 SEGMENTATION (deterministic)
       speaker-labelled lines / forwarded headers / paragraphs →
       segments{speaker?, kind: prose|transcript|forward, spans}
  └─ L1 CUE EXTRACTION per segment (deterministic regex, cue-gated)
       scope/origin/dates/party/constraints — each extractor may only fire
       inside a segment that carries its cue AND its evidence (amount for
       budget; origin-verb for origin). Raw evidence = verbatim span.
  └─ L2 ATTRIBUTION (NLP-light, deterministic-first)
       speaker slots + group slot; "I/my" → speaker; "we/our" → group;
       unresolved pronouns in transcript segments → that line's speaker.
  └─ L3 AUTHORITY MERGE (deterministic)
       explicit-amount > inferred; organizer/total-markers > casual; group
       slot conflicts with personal slot → ambiguity + follow-up, never
       overwrite. Missing-flags clear only on explicit-correct values.
  └─ L4 LLM (gated, per the KDD verdict)
       only segments/fields where L1–L3 abstain (fuzzy phrasings), with the
       shipped abstention gate + JSON recovery; output enters L3 with
       authority="inferred" and never outranks explicit cues.
```

**Design invariant:** the LLM is the *last* layer, not the first — the exact
posture the KDD ladder and pattern runs converged on (rules-first + gated
fallback; llm_first disqualified with a 15–17× flag flood; guard = free + surgical).

## 3. Phased implementation (codebase-anchored)

- **Phase 1 (this commit) — stop the bleeding on the misquote path:**
  `_extract_budget_scope` becomes amount-scoped: consider only
  amount-bearing sentences; explicit total markers with an amount outrank
  per-unit cues without amounts; document the precedence. Regression test =
  the exact Family Summit thread (fixture `sim2_family_summit_thread`).
- **Phase 2 — origin cue-guard:** origin binding requires an origin-cue verb
  phrase; "X side trip / add X / X nightlife" bind to destination candidates.
  Regression: okinawa case.
- **Phase 3 — L0/L2:** speaker-segment segmentation + per-speaker slots in
  the packet (`travelers[]` alongside group facts); transcript-kind segments
  excluded from prose fields. This is IDEA-134's implementation surface.
- **Phase 4 — L3 invariants:** missing-flag clearing rules, verbatim
  evidence spans, explicit-cue short-circuits for D-02-class detectors.
- **Phase 5 — L4 wiring:** route only abstained fields through the gated LLM
  path (client work already shipped: model-aware params, JSON recovery).

## 4. Evidence & test strategy

- New golden fixture: the full Family Summit 6-note thread (verbatim from the
  personas doc) — every phase must keep the thread's known-good values
  (scope=total, 350000 INR, 4 adults, japan+tokyo+kyoto) while gradually
  fixing the failure set; each phase's regression test pins its slice.
- The existing colloquial/adversarial gates stay green (no re-baselining).
- Sim #2 re-run (live) is the acceptance test for Phases 1–4 together.
