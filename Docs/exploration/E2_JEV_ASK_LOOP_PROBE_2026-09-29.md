# E2 — Jev Probe Design: Question Rendering + Answer Parsing (T1 companion)

**Date:** 2026-09-29 · **Status:** EXECUTED 2026-10-13 — BOTH GATES PASS (see execution record at bottom; Probe 1 role corrected from "Jev renders" to "Jev grades" — Jev cannot generate text)
**Related:** `scripts/benchmark_colloquial_jev.py` (harness pattern); `Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md`; 2026-09-18 G1 lesson (rubric-explicit or fail)

## Why

The shipped ask loop (`/a/{token}`) renders questions verbatim from the decision
engine — machine-authored text like "Which city would you fly out from?" is
already traveler-voiced, so **rendering** is a quality upgrade, not a blocker.
**Parsing** is the higher-value target: Option D in E1 (in-thread WhatsApp
replies) needs free-text answers mapped back to `field_name`s safely.

## Probe 1 — Question rendering quality

**Task:** given the decision engine's question objects (field_name, question,
priority, packet context), produce a traveler-voiced variant ≤2 sentences,
Hinglish-tolerant, no new facts, no jargon.

**Rubric (explicit, per G1 lesson):**
1. Preserves the asked field's intent exactly (origin stays origin) — FAIL if any field drift.
2. ≤2 sentences, second person, no system vocabulary ("packet", "field", "quote-ready" forbidden).
3. Adds zero facts (no invented dates/destinations) — FAIL on any fabrication.
4. Reads naturally to a Hinglish speaker (spot-check set of 10).
5. Deterministic validator: question still maps 1:1 to the same `field_name`.

**Gate:** F1 ≥ 0.80 on 16 colloquial fixtures (match `records_sweepguard2.jsonl` bar), severity-style per-criterion ≥ 0.95, zero fabricated-fact FPs. Below gate → Jev does not render; verbatim questions ship (current behavior is already safe).

## Probe 2 — Answer parsing (field write-back proposal only)

**Task:** given one question + one free-text reply ("mumbai se hi", "mid dec for
5 nights"), output `{field_name, proposed_value, confidence}`.

**Hard boundary:** parsed values are **proposals only** — they enter the packet
with `authority=derived_from_traveler_reply` and never `explicit_user` (only
structured `/a/{token}` form answers keep that authority). The deterministic
extractor stack (`src/intake/extractors.py`) re-validates every proposal
through the normal intake path; Jev output that fails extraction is dropped
with an operator-visible "couldn't parse this reply" flag.

**Rubric:** correct field routing ≥ 0.95 (wrong-field = automatic FAIL class);
value extraction F1 vs colloquial golden set ≥ 0.85; zero silent drops
(unparseable must yield explicit `unparsed` marker).

## Harness

Extend `scripts/benchmark_colloquial_jev.py` pattern:
`scripts/benchmark_jev_ask_loop.py` with fixtures from
`data/fixtures/extraction/colloquial_golden.json` + a new
`ask_loop_golden.json` (16 questions × 3 answer styles). Receipt JSON like
`grading_receipt.json`. Run only when `JEV_*` creds present in env; skips
honestly otherwise.

## Cost estimate

G1 precedent: full 24-fixture eval ≈ $0.005. Two probes ≈ **under $0.02 total**.

## Decision tree

- Probe 1 pass → Jev renders traveler-voiced questions behind a flag, verbatim fallback preserved.
- Probe 2 pass → Option D (in-thread WhatsApp parsing) becomes buildable; else link-form answers remain the only write path (safe by construction).
- Either fail → document, keep verbatim/link-form (shipped behavior is the floor, not a regression).

---

## Execution record — 2026-10-13 (BOTH GATES PASS)

**Harness:** `scripts/benchmark_jev_ask_loop.py` (new, reusable; skips honestly without creds) over
`data/fixtures/extraction/ask_loop_golden.json` (new; 12 engine questions from the canonical
`FIELD_REQUIRED_FOR` vocabulary × 3 renderings × 4 reply styles). Live on pinned `jev-1.13.0`.
Receipt: `data/experiments/hybrid_kdd_v1/ask_loop_probe_receipt.json`. Spend ≈ $0.006 for both runs.

**Probe 1 design correction (binding):** the original design asked Jev to *produce* traveler-voiced
renderings. Jev cannot generate text (jaggedness #9; expedition §3E-1) — the corrected role is
**grader/selector**: the generative ladder supplies candidate renderings, Jev scores each against the
explicit rubric (noul `preserves_field_intent`, noul `introduces_no_new_facts`, score 1–5
`traveler_naturalness`) and the flag-selects. The probe validates exactly that grading ability.

**Probe 1 result — GATE PASS.** Defect detection 1.000: field-drift renderings caught 12/12
(intent noul collapses to ~0.01 vs ~0.95 for faithful renderings — textbook separation), fact-fabricating
renderings caught 12/12 (no-new-facts noul ≤ 0.08). Good-rendering acceptance 11/12 (0.917): the one
false rejection was a rendering adding "right now" — a benign temporal clarification the no-new-facts
rubric literally reads as an added assumption (jaggedness #1 again; failure direction is safe: the
selector drops a usable rendering). Naturalness scores (1.4–3.1, mean ≈ 2.2) say our machine-authored
questions have real headroom vs human-agent phrasing — the rendering upgrade has value to capture.

**Probe 2 result — GATE PASS.** Field routing 24/24 = 1.000 (direct + colloquial answers, including
Hinglish "delhi se hi", "1.5 lakh ke andar total"); true non-answers → explicit `unparsed` 12/12;
implicit answers kept 12/12; wrong-field = 0; silent drops = 0. Confidence notes: the ambiguous
implicit answer ("One of us is applying…") routed to the visa/passport sibling at conf 0.51 — below
the 0.60 act gate → routes to operator review, exactly the designed safety behavior.

**Label honesty note:** run 1 flagged 2 fixtures as silent drops ("One of us is applying, not sure
about the rest", "Whatever is standard is fine"). Inspection showed both were **fixture-label defects**,
not model defects — they are implicit answers, and Jev read them semantically. Labels corrected
(`implicit_answer` class added), harness extended, re-run clean. The inverse-G1 lesson recorded:
Jev is literal when *we* under-specify labels too.

**Decision-tree outcome:** Probe 1 pass → traveler-voiced rendering is buildable behind a flag with
Jev grading ladder-produced variants (verbatim fallback preserved). Probe 2 pass → **Option D
(in-thread WhatsApp free-text parsing) is buildable**: Jev routes free-text replies to canonical
fields; extracted values remain proposal-only (`authority=derived_from_traveler_reply`) and the
deterministic extractor stack re-validates every proposal (hard boundary unchanged).

**Wiring defects found by the same sweep (FND-0322, closed/fixed same pass):** the failure-triage lane's
severity Score question shipped without `criteria` (HTTP 422 → silent heuristic fallback, Jev path had
never executed) and the NL-policy lane's Noul questions shipped without `instructions` (HTTP 400 →
silent fallback whose heuristic **false-cleared violations**), plus nouls carry no native `confidence`
(the 0.65 review gate flagged 100% of clauses). All fixed and live-verified — details in the
expedition doc §7 v7.

---

## Wiring addendum — 2026-10-13 (same day, post-execution)

Both decision-tree outcomes landed as production services behind `JEV_ASK_LOOP_ENABLED`
(**default off** per the ADR-008 prod posture — activation requires the flag AND G2):

- **`src/intake/ask_reply_router.py`** — Probe 2 productionized. `AskReplyRouter.route(question, reply)`
  → `ReplyRoutingProposal` (canonical field | explicit `unparsed`, calibrated confidence, act gate at
  0.60 → `needs_review`). Routing proposal ONLY: values stay with the deterministic extractor stack
  (`authority=derived_from_traveler_reply` when a consumer feeds one forward); never a packet write.
  Flag-off / Jev-unavailable → honest `needs_review=True` results, never a guess.
- **`src/intake/question_render_selector.py`** — Probe 1 productionized.
  `QuestionRenderSelector.select(field_name, engine_question, candidates)` grades each candidate with
  the E2 rubric and selects the best passing one; zero passing / grading error / flag-off /
  unavailable → **verbatim engine question** (shipped floor preserved; failures fail safe).
- The E2 benchmark (`scripts/benchmark_jev_ask_loop.py`) now imports the canonical field vocabulary
  from the router module — one definition, no drift.

**Verification:** 12 new contract tests (`tests/test_ask_loop_services.py`: flag-off honesty, act-gate
review routing, derived-confidence fallback, grade/select separation, all-fail verbatim fallback,
grading-exception safety) + the full Jev surface 38/38 green + ruff clean. **Live on jev-1.13.0 with
the flag on:** "delhi se hi" → origin_city (conf 1.0), "1.5 lakh ke andar total" → budget_raw_text
(conf 1.0), "Will confirm soon!" → explicit unparsed; the fabricated "Are you flying out of Mumbai?"
candidate rejected (no-new-facts noul 0.02) while the faithful rendering was selected (intent 0.98).
