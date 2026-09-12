# Sim #2 Findings & Tasks Inventory — complete enumeration (2026-09-13)

Scope: every finding, task, and capability gap — explicit, implicit, or
inferred — arising from the live Family Summit run
(`SIM2_FAMILY_SUMMIT_RESULTS_2026-09-12.md`, FND-0272…0276) and its
surroundings, classified by disposition. This is the working checklist for
the realignment; the comparison sheets remain the model-venue record.

Legend: **[FND-x]** = already registered in the findings store ·
**[RL-n]** = owned by realignment Phase n
(`EXTRACTION_REALIGNMENT_REGEX_NLP_LLM_2026-09-13.md`) ·
**[IDEA-134]** = idea-pad tracked · status: open / partial / done.

## A. IMPLEMENTATION

| # | Item | Priority | Status / owner layer |
|---|---|---|---|
| A1 | ~~UI-path blocked-lead persistence~~ **RETRACTED** — leads persisted; initial check was an RLS/GUC verification error (FND-0272 closed 2026-09-13). Replacement defect: duplicate-lead reprocess → A1' | ~~P0~~ | [FND-0272 closed; FND-0284 fixed] |
| A2' | **Origin cue-guard** — origin requires origin-cue verb (from/flying out of/departing/based in) + validated city; proposal verbs ("side trip", "add", "nightlife at") bind to destination candidates | P1 | [FND-0273 residual] [RL-2] open (scope half landed) |
| A3 | **Amount-scoped budget scope** — cue phrases evaluated only in amount-bearing segments; explicit-total precedence | P1 | [FND-0273] **done** (Phase 1 landed + 8 tests) |
| A4 | **Transcript-contamination guard** — `[speaker]:` lines and forwarded headers are transcript segments; labels/lines never enter packet fields; only intent content | P1 | [FND-0274] [RL-0] open |
| A5 | **Per-traveler attribution slots** — `travelers[]` with dietary/mobility/occasion attributes; "I/my"→speaker, "we"→group; no-heights becomes a safety constraint flag (never dropped silently) | P1 | [FND-0275] [IDEA-134] [RL-3] open |
| A6 | **Verbatim evidence spans** — ambiguity/constraint "Raw:" quotes must be verbatim substrings of the input (the "5 lakhs" corruption class) | P2 | [FND-0276] [RL-4] open |
| A7 | **D-02 explicit-cue short-circuit** — flights-inclusiveness ambiguity must not fire when inclusiveness is explicitly stated ("INCLUDING flights") | P2 | [FND-0276] [RL-4] open |
| A8 | **Missing-flag invariant** — a missing-field flag clears only when a validated explicit value replaces it; a fabricated/wrong value must not clear it (Origin disappearing) | P2 | [FND-0276] [RL-4] open |
| A9 | **Additive destination merge** — later-voice destination mentions ("maybe osaka", "osaka nightlife is non-negotiable") merge into Destinations or Unresolved-Alternatives ambiguities | P1 | open (new) |
| A10 | **Room primitive** — room_count/room_type ("2 separate double rooms") captured and hooked to quote splitting | P2 | open (new) |
| A11 | **Activity capture** — scuba/skiing/cooking class as structured activities with destination coupling, not prose in Trip Priorities | P2 | open (new) |
| A12 | **Date-anchor constraint** — "trip must COVER April 14" as a hard date anchor distinct from a full date window; three-way constraint (spring ∩ ±1wk ∪ covers-Apr-14) representable | P1 | [FND-0275 adjacent] open |
| A13 | **Conflict surfacing** — cross-voice contradictions (Dec-vs-spring, ryokan-vs-party-hostel) emit follow-up questions + advisor flags; never last-writer-wins | P1 | [FND-0273 adjacent] open |
| A14 | ~~Browser E2E for persistence~~ **RESOLVED BY EVIDENCE** — UI and API are one path (`/run` with draft_id); Phase 0 verified draft-linked reprocess preserves a single lead via API-level test after the FND-0284 fix | P0 | [FND-0272 companion] done |
| A15 | **Promote the Family Summit thread to a golden fixture** in the colloquial/adversarial gates (failure-becomes-fixture doctrine; currently only string constants in a test) | P1 | open |
| A16 | **Speaker-segment parser (L0 core)** — cheap deterministic parse of `[name]:` markers and forwarded headers; prerequisite for A4/A5 | P1 | [RL-0] open |
| A17 | **Budget Flexibility authority merge** — soft→firm on "3.5L MAX" was correct; pin it with a test + define flexibility precedence (same invariant class as A8) | P2 | open (new) |
| A18 | **Trip Priorities field gating** — it absorbed "the 14th covered" prose; needs a structured vocabulary or stricter admission rules | P2 | open (new, part of A4 class) |

## B. EXPLORATION

| # | Item | Priority | Note |
|---|---|---|---|
| B1 | **Confidence recalibration under cue conflict** — scope flip carried 95% confidence on a wrong value; confidence should drop when cues conflict across segments | P2 | design task, pairs with L3 |
| B2 | **Derived per-person budget** — ₹3.5L/4 ≈ ₹87.5k as a validation signal for quotes ("what does each owe" needs exactly this) | P2 | ties to A10/A12 |
| B3 | **Couples/room-orientation pairing** — "2 couples" → 2 rooms inference; group-composition → room topology | P3 | blocks nothing |
| B4 | **Prose self-identification as attribution** — "meera here" (no `[label]`) should bind the segment's speaker; extend A16's parser beyond markers | P2 | L2 design |
| B5 | **Channel-aware intake modes** — the UI promises WhatsApp/email/call-transcript handling; transcript-format parsing should be a first-class mode, not an accident | P2 | productizes A16 |
| B6 | **Season-window reasoning** — spring ∩ december ∩ covers-Apr-14 conflict detection needs lightweight calendar reasoning; where it lives (regex vs L4) is open | P2 | feeds A13 |
| B7 | **Delegation & split-payment workflow** — "what does each person owe" is a product surface beyond intake (quote split by family, approvals) | P3 | big concept, FOR-LATER unless owner pulls |
| B8 | **Urgency/sentiment cues** (😤, "keeps getting lost") → SLA priority | P3 | optional |
| B9 | **Gemini / local-LLM arms for the gated L4 layer** | P2 | blocked: no GEMINI_API_KEY |
| B10 | **Reasoning-model tier-2 re-test on a reasoning-bound corpus** — prior simulation showed +0.029 (within variance); needs a corpus whose hard cases are reasoning-bound, not extraction-lossy | P3 | policy knob stays documented |

## C. DOCUMENTATION

| # | Item | Status |
|---|---|---|
| C1 | Realignment doc per-phase status updates as phases land | ongoing (Phase 1 recorded) |
| C2 | Sim #2 results doc ↔ findings-store cross-map (doc uses F1–F8; store uses FND-0272…0276) | **open — do with next store write** |
| C3 | tools/README entries for new fixtures/tests when A15 lands | pending A15 |
| C4 | Feature List V3 update when attribution primitive (A5) lands | pending A5 |
| C5 | Persona constructs doc + results doc committed ✓; council design committed ✓ | done |

## Positives to lock as regression tests (from the same run)

- Party Size/Composition stable at 4-adults across all six passes.
- Budget Flexibility `soft→firm` on "3.5L MAX" (S5 firm-marker) — correct.
- Reprocess idempotency (no duplicate leads across five reprocesses) — API
  level only; the UI-level companion is A14.
- Jain meal captured from a second voice (worked, but unattributed — A5).

## Phase 0 outcome addendum (2026-09-13)

- A1 retracted (FND-0272 closed — RLS/GUC verification error; all six leads
  persisted). New P1 found & FIXED during Phase 0: FND-0284 duplicate-leads
  (resolver now uses explicit-agency RLS; 3 structural tests; live-verified:
  two draft-linked reprocesses → one lead).
- FND-0285 registered (P2): encrypted raw_input blocks inbox content search.
- Realignment Phase 1 (scope guard) previously landed; Phase 2 (origin
  cue-guard) is next implementation item.

## Current ledger

- Registered: FND-0272 (P0), FND-0273/74/75 (P1), FND-0276 (P2).
- Done: A3 (scope guard, 8 tests, 622 extraction tests green).
- This inventory adds **18 implementation items (A1–A18, 7 new)**,
  **10 exploration items**, **5 documentation items**, and **4 regression
  locks** — i.e., the realignment is ~1 of 18 implementation items deep.
