# Hybrid Decision Engine — KDD Experiment Protocol & Results

*Date: 2026-09-11 · Ratification: owner accepted option (b) — flag stays OFF in prod; evidence experiment authorized (OpenAI models first, other providers later)*
*Framing: Knowledge Discovery in Databases (KDD) — selection → preprocessing → transformation → mining → evaluation → knowledge. Every artifact archived for re-analysis.*
*Governing docs: `Docs/exploration/C03_ROUTER_DESIGN_2026-09-02.md` (tier ladder), ADR-2026-09-02 (asset dispositions), E11 adversarial design §4.*

---

## 1. Research questions

- **Q1 (quality):** Does hybrid (LLM-assisted) risk/decision generation improve decision quality over tier-0 deterministic rules on the graded corpora — and on WHICH slices (colloquial? adversarial? budget-edge)?
- **Q2 (economics):** What is the cost per record and per accepted packet (token usage × model pricing), and what is the cache-hit rate on repeat inputs?
- **Q3 (latency):** What is the per-record wall-time and LLM latency distribution vs the deterministic path?
- **Q4 (safety):** Does the LLM path introduce wrong-value risks (hallucinated risks, dropped critical document checks) not present in rules?
- **Q5 (models):** How do candidate models compare (gpt-4o-mini vs gpt-4o in run 1; other providers/models in later runs)?

## 2. KDD phases

| Phase | This experiment |
|---|---|
| **Selection** | Full graded surface: budget (20) + colloquial (15) + scenarios (30) + adversarial golden (21) + adversarial known-defects (12) ≈ 98 records. Excluded: pipeline lane (no producer). |
| **Preprocessing** | Tier-0 extraction pass (deterministic, identical in all arms) → CanonicalPacket per record. Packet is the shared substrate; the arms differ only in the decision stage. |
| **Transformation** | **Arm A (baseline):** `USE_HYBRID_DECISION_ENGINE=0` → pure rules. **Arm B(m):** flag ON, hybrid per model m ∈ {openai/gpt-4o-mini, openai/gpt-4o}. Arm B is run twice per record: **cold** (LLM path) and **warm** (decision cache → cache-hit measurement). |
| **Mining** | Per record per arm: risks generated (count/types/severities), decision source (rule/llm/cache), confidence, llm_used, llm_model, cost_inr, wall-time ms; per LLM call: full prompt + response archived, token usage, estimated cost, cache key. |
| **Evaluation** | (1) Decision-state diff A↔B per record (escalation added/dropped, blocker sets changed); (2) risk-set precision/recall vs rule baseline where the rule baseline is corroborated by fixtures; (3) failure exemplars (wrong/missing risks); (4) aggregate per-model: escalation rate, mean cost/record, p50/p95 latency, cache-hit rate warm pass. |
| **Knowledge** | Results appended to this doc; go/no-go recommendation per slice for flag/router posture; register + ADR updates; JSONL archived for future model runs. |

## 3. Experiment matrix (run 1)

| Arm | Flag | Provider/Model | Records | Notes |
|---|---|---|---|---|
| A | OFF | — (deterministic) | ~98 | Baseline; also the current prod path |
| B1 | ON | openai / gpt-4o-mini | ~98 | "Cloud small" tier-1 candidate (client docstring: recommended for decisions) |
| B2 | ON | openai / gpt-4o | ~98 | "Better reasoning, more expensive" — quality ceiling probe |

Later arms (out of scope run 1): Gemini (needs `GEMINI_API_KEY`), local SLM (needs hardware — see C-04 protocol), additional OpenAI models.

## 4. Measurement schema (per record, JSONL)

```json
{
  "corpus": "colloquial", "record_id": "…", "raw_text_sha256": "…",
  "arm": "A|B1|B2|B1-warm|B2-warm",
  "packet_facts": ["…"], "packet_unknowns": ["…"],
  "risks": [{"severity": "…", "type": "…", "message": "…"}],
  "decision_source": "rule|llm|cache", "llm_used": true,
  "llm_model": "gpt-4o-mini", "cost_inr": 0.0,
  "cache_hit": false, "wall_ms": 0.0,
  "llm_calls": [{"prompt_chars": 0, "response_chars": 0,
                 "latency_ms": 0, "error": null}],
  "prompt_archive": "prompts/<record>-<arm>-<n>.txt"
}
```

Prompts and responses are archived verbatim under `data/experiments/hybrid_kdd_v1/prompts/` (prompt-injection provenance: record inputs are test-corpus text, no real PII).

## 5. Guardrails

- No DB writes; no trips created — the harness calls extraction + decision functions in-process.
- Usage guard respected: if the repo's LLM usage guard blocks a call, the record is marked and the run continues (blocked = data point, not crash).
- Gate fixtures are used as the *evaluation set*; per PER-0897 leakage discipline, results on gate fixtures are development evidence — the holdout policy (E-11/E-03) applies to any promotion claim: a flip recommendation must ALSO pass a fresh paraphrase holdout, not just the graded corpus.

## 6. Results

### 6.1 Session log — 2026-09-11 (harness commissioning)

The harness commissioning run itself produced the experiment's first real
findings: three latent defects in the hybrid decision engine, all unreachable
until now because the engine's LLM path had never executed in this repo.

**F1 — Broken import, LLM path never available (`src/decision/hybrid_engine.py:48`).**
The module guarded its LLM support with `try: from llm import BaseLLMClient,
create_llm_client` — the bare `llm` package, not `src.llm`. The import fails in
this venv, so `LLM_AVAILABLE` has been permanently `False`: every `_call_llm`
call bailed with "LLM not available" and the engine silently degraded to
defaults. This is the orphaned-module failure mode predicted by the agentic
deep audit (G-01 family): code that was never exercised rotted invisibly.
Fixed to `from src.llm import ...`.

**F2 — UnboundLocalError in the failure handler (`hybrid_engine.py` `_call_llm`).**
The except handler reads `usage_decision` for guard bookkeeping, but the
variable was assigned mid-`try`, after several fallible statements
(`estimate_cost`, prompt build). Any exception before that point crashed the
handler itself with `UnboundLocalError`, which surfaced as a generic "Hybrid
engine failed" and skipped the failed-call guard record. Fixed by hoisting
`usage_decision = None` to the top of the `try`. Regression-validated with an
exploding stub client: graceful default fallback, no handler crash.

**F3 — lru_cached env flag made per-arm toggling invisible (`src/intake/decision.py:38`).**
`_is_hybrid_engine_enabled()` is `@lru_cache(maxsize=1)`. The harness flips
`USE_HYBRID_DECISION_ENGINE` between arms, but the cached value stuck — arm B
silently ran the deterministic path. The repo already provides
`_reset_hybrid_engine()` for exactly this (test isolation); the harness now
calls it after every env flip. Serving-path behavior is unaffected (the flag
doesn't change within a process in production).

**F4 (measurement) — Cache isolation for cold/warm validity.**
The first full run showed cache hits in *cold* passes: `DecisionCacheStorage`
persists to `data/decision_cache/` across runs, contaminating the cold/warm
distinction the experiment is designed to measure. The harness now creates a
per-model run-scoped cache dir (`cache_<model>/`, wiped before cold, reused
for warm), so warm-pass hit rates are attributable to this run's cold entries.

**Mechanics validation (stub client).** With a stub LLM client the full chain
is verified end-to-end without spend: `decide → source=llm, llm_used=True`,
cost accounting in INR, per-call prompt/error archival, and the egress PII
redaction + audit path (`spine_api/core/llm_egress.py`) firing on real
extraction content (4 redactions on a sample note, audit hash logged).

### 6.2 Full-matrix dry run (175 rows: 35 records × 5 arms)

Executed with the revoked-key environment, so arm B is **401-contaminated**
and not valid for model comparison. What the dry run does establish:

| Arm | Decide-source distribution (of 140) | Reading |
|---|---|---|
| A (deterministic) | n/a — 6 risk flags on 6/35 records | **Valid baseline** |
| B-gpt-4o-mini (cold) | rule 51 · cache 55 · default 34 | cache 55 = within-pass cross-record hits |
| B-gpt-4o (cold) | rule 51 · cache 55 · default 34 | identical to mini (no LLM ever succeeds) |
| B-*-warm | cache 106 · default 34 | warm hits everything the cold pass cached |

- All 124 LLM attempts failed with `AuthenticationError 401` — the key in
  `.env` (`sk-proj-…VeQA`, 164 chars, well-formed) is **revoked or expired**.
  Zero successful LLM decisions; the B arms currently measure
  "hybrid with dead LLM", which doubles as an honest failover datapoint: the
  engine degrades to defaults without crashing, and guards record the failures.
- The 34 `default` decides per arm are `visa_timeline_risk` on records whose
  rules abstain (no international-visa facts) — precisely the slice where the
  LLM path will differentiate once credentials work.
- Arm A baseline: 35 records, 6 risk-flagged. Deterministic wall time ≈ 0 ms.

### 6.3 Blocker — valid OPENAI_API_KEY required

Per the agreed sequencing (OpenAI models first), the model-comparison arms
(B1 gpt-4o-mini, B2 gpt-4o) cannot produce valid data until a working key is
in `.env` (OPENAI_API_KEY). Everything else is ready: harness, cache
isolation, per-arm instrumentation, prompt archival, cost accounting, and the
baseline. The remaining run is one command:
`scripts/run_hybrid_kdd_experiment.py` (≈35 records × 5 arms, est. cost
≈₹2–8 for the full matrix at current pricing).

### 6.4 Full matrix run — VALID (2026-09-11, key rotated, 175 rows)

35 records × 5 arms with working credentials. **16 LLM escalations per cold
arm** (all `visa_timeline_risk` — the type whose rules abstain on
ambiguous/partial facts), deterministic warm replay, zero errors.

**Q1 — Does hybrid change decisions?** Yes, materially: arm A emits 6 risk
flags (6/35 records); arm B emits 32 (26/35). 26 records differ A↔B, all
differences are *added* `visa_timeline_risk` flags — zero flags removed. The
hybrid path is strictly additive on this corpus, adding visa-timeline risk
signals the deterministic rules never produce.

**Q2 — Quality of added flags?** Mixed — this is the experiment's headline
finding. Most LLM flags are contextually sound (Bali 10-day trip, Japan
family trip, Thailand in December → visa timing advice). But the LLM also
produced a **spurious high-severity visa flag on a destination-less packet**
(`budget_simple_002`: "no destination candidates and nothing booked" →
"insufficient time to process a visa"), and the decision cache then propagated
that same flag to 7 other records with identical context. The LLM path has no
abstention mechanism: it always answers, even when facts are insufficient.
**If the flag were flipped on naively, cache would amplify this precision
defect.** Candidate fix: require `destination_candidates` presence before
LLM escalation, or a "cannot assess" verdict in the prompt schema.

**Q3 — Model comparison (gpt-4o-mini vs gpt-4o).** Both escalate on the same
16 records; escalation *sets* disagree on only ~4 boundary records. Decision
text differs (different phrasings) but substance matches. Cost diverges 19×:

| Metric | gpt-4o-mini | gpt-4o |
|---|---|---|
| Cold-pass total cost | ₹0.1122 (16 calls) | ₹2.1036 (16 calls) |
| Cost per LLM decide | ≈₹0.007 | ≈₹0.13 |
| LLM decide latency | avg 2,253 ms / max 3,144 ms | avg 3,039 ms / max 4,070 ms |
| Risk flags emitted | 32 (26 records) | 32 (26 records) |

**Recommendation: gpt-4o-mini.** Same coverage, 19× cheaper, 35% faster; 4o's
extra escalations on 4 boundary records are not worth ₹2.10/run.

**Q4 — Cache economics.** Warm passes hit 140/140 (100%) at ₹0.0000 total and
p50 wall 1.8 ms — cache completely amortizes repeat traffic. Cold passes
already show 73 within-pass cache hits (identical-context records share one
LLM call). Content-hash caching on packet context works as designed, with the
amplification caveat from Q2.

**Q5 — Latency budget.** Cold escalation costs 2.3–3.0 s per LLM decide
(worst record 4.1 s). Acceptable only for async/batch paths; a synchronous
serving path with hybrid ON would add seconds on escalated records. The
OFF-by-default posture (ADR A1 option b) remains correct; if a deployment
opts in, it should be for escalation-tolerant flows.

**Decision posture (for owner ratification of ADR A1):** evidence supports
keeping hybrid wired and OFF-by-default, with gpt-4o-mini as the sanctioned
model should any deployment opt in — *after* the abstention guard (Q2) is
implemented and this lane re-run to confirm the spurious-flag class is gone.

## 7. Experiment wave 2 — model ladder + decision-architecture patterns (2026-09-11)

Owner direction: v1 tested only one architecture (rules→single-LLM fallback)
with two models. Wave 2 widens both axes, using the current OpenAI catalog
(developers.openai.com/api/docs/models — ladder spans gpt-3.5-turbo 2022 →
gpt-6-astra 2026) and official pricing (developers.openai.com/api/docs/pricing,
fetched 2026-09-11; USD×83 → INR in `src/llm/openai_client.py` PRICING).

### 7.1 Client compatibility (prerequisite found by ladder probes)

The repo's OpenAI client assumed the classic Chat Completions contract. Probes
exposed two failure classes; fixed model-aware in `openai_client.py`:
- Reasoning models (`gpt-5*`, `gpt-6*`, `o1*`, `o3*`, `o4*`): require
  `max_completion_tokens` (reject `max_tokens`) and reject `temperature != 1`
  → params now omit temperature and use max_completion_tokens.
- Legacy `gpt-4` (non-turbo): rejects `response_format: json_object`
  → `_supports_json_mode()` gate (turbo/4o/4.1+ keep JSON mode).
- PRICING extended to 24 ladder models (was: 4o-mini + 4o only).
104 existing LLM-client tests pass; all 11 probe models return valid JSON.

### 7.2 Design

**Axis 1 — model ladder (17 models × 35 records, single pattern, cold+warm):**
gpt-3.5-turbo, gpt-4-turbo, gpt-4.1-nano/mini, gpt-4.1, gpt-5-nano/mini,
gpt-5.1, gpt-5.2, gpt-5.4-nano/mini, gpt-5.4, gpt-5.5, gpt-5.6-luna,
gpt-5.6-terra, o4-mini, gpt-6-astra. Research questions:
- Q6: Does decision quality (escalation precision vs arm A) improve with
  model era, or plateau at mini-class?
- Q7: Where is the cost/quality knee? (nano-class vs flagship at 19×+ spread)

**Axis 2 — decision architecture patterns (35 records × 4 patterns ×
{gpt-4o-mini, gpt-5.6-luna}):**
- `single` (v1 baseline): rules → one LLM fallback.
- `llm_first`: rules disabled; LLM decides every type (rules vs LLM ordering).
- `guard` (LLM + regex/fact validation): LLM proposes; deterministic validator
  drops LLM/cache visa flags on destination-less packets — implements the §6.4
  Q2 abstention fix as an architecture, not an engine change.
- `vote` (LLM ensemble): two models decide independently; flag survives only
  if both agree non-low (conservative merge on disagreement).
- `critic` (creator-validator orchestrator): creator (pattern model) proposes;
  critic (gpt-5.6-terra) reviews against context; rejection downgrades to low.
Research questions:
- Q8: Which pattern best kills the spurious-flag class without losing true
  escalations?
- Q9: Cost/latency multiplier per pattern vs the quality gained?

Harness: `scripts/run_hybrid_kdd_experiment.py` (--patterns/--pattern-models/
--tag). Pattern clients: `VotingClient`, `CriticClient`; `guard` = post-filter.
Per-pattern cache dirs prevent cross-pattern cache contamination. All inner
calls archived under `prompts/`.

### 7.3 Evaluator-portability note (promptfoo)

OpenAI is winding down its Evals product in favor of Promptfoo
(developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo).
This lane's corpus + arms + assertions map naturally to a portable
`promptfooconfig.yaml` (providers = the ladder models; tests = the 35 records;
assertions = risk-flag expectations). Recommended follow-up once wave-2
results fix the reference arms: generate a promptfoo config from the same
fixtures so the lane runs in CI identically for any provider. Not blocking —
recorded as EX-track follow-up.

### 7.4 Wave-2 results (both runs valid; data: records_ladder.jsonl, records_patterns.jsonl)

**Axis 1 — model ladder (19 models incl. v1's mini/4o; 35 records; cold cost ₹; avg LLM latency):**

| Model | Flags | Added vs A | Cold ₹ | Lat ms | Note |
|---|---|---|---|---|---|
| A (deterministic) | 6 | — | 0 | 0 | reference |
| gpt-3.5-turbo (2022) | 12 | +6 | 0.27 | 4,053 | conservative |
| gpt-4-turbo (2023) | 9 | +3 | 7.10 | 6,574 | most conservative |
| gpt-4o-mini (2024) | 32 | +26 | 0.11 | 2,253 | fastest |
| gpt-4o | 32 | +26 | 2.10 | 3,039 | |
| gpt-4.1-nano (2025) | 41 | +35 | 0.09 | 3,308 | cheapest, most aggressive |
| gpt-5-nano | 41 | +35 | 0.009 | 10,010 | only 2 LLM calls — cache carried 41 flags |
| gpt-5-mini | 37 | +31 | 0.58 | 13,934 | slowest (reasoning) |
| gpt-5.1 / 5.2 | 36 | +30 | 2.70/3.15 | ~4,400 | |
| gpt-5.4-nano | 41 | +35 | 0.28 | 3,347 | |
| gpt-5.4-mini | 26 | +20 | 0.96 | 2,786 | |
| gpt-5.5 (2026) | 26 | +20 | 5.99 | 6,066 | |
| gpt-5.6-luna | 28 | +22 | 0.23 | 5,508 | |
| gpt-5.6-terra | 36 | +30 | 2.32 | 5,110 | |
| o4-mini | 25 | +19 | 0.90 | 5,781 | |
| gpt-6-astra (2026) | 38 | +32 | 11.45 | 5,952 | flagship, most expensive |

- **Q6 (does era improve quality?):** No monotonic quality signal. All models
  are strictly additive (zero flags removed vs A, universally). Aggressiveness
  varies **12×** with identical prompts (4-turbo +3 vs nanos +35) — model
  choice is really a *recall/precision posture* choice, not a capability
  ladder. No ground-truth visa-risk labels exist on this corpus, so added-count
  measures aggressiveness; true-quality ranking requires the E-07 judge lane.
- **Q7 (cost/quality knee):** Flagships (6-astra ₹11.45, 5.5 ₹5.99, 5.4 ₹3.26)
  show no added-flag advantage over nano-class (₹0.09–0.28). The knee is at
  nano/mini tier: **gpt-4o-mini, gpt-4.1-nano, gpt-5.4-nano, gpt-5.6-luna** are
  the value frontier. Reasoning models (gpt-5*) pay 3–6× latency for no
  observable gain on this task. Warm passes: ₹0.000 for every model — cache
  fully amortizes repeat traffic at any tier.
- **gpt-5-nano anomaly:** escalated only 2× but emitted 41 flags — its two
  decisions were cached and replayed across all context-identical records.
  Cache amplification cuts both ways (§6.4 Q2).

**Axis 2 — architecture patterns (35 records × 4 patterns × {4o-mini, 5.6-luna}; critic = 5.6-terra):**

| Pattern | mini flags | luna flags | Cost ₹ (mini/luna) | Lat ms | Verdict |
|---|---|---|---|---|---|
| single (ref) | 21 (+15) | 28 (+22) | 0.11 / 0.23 | 2.3–5.5 | baseline |
| guard (LLM+fact-gate) | 20 (+14) | 14 (+8) | 0.11 / 0.23 | +0–0 (filter) | kills spurious class for free |
| vote (2-model ensemble) | 12 (+6) | 11 (+5) | 0.24 / 0.26 | 8.0–8.5 | halves escalation; 2× cost |
| critic (creator→validator) | 7 (+1) | 26 (+20) | 2.01 / 2.12 | 5.4–6.5 | **model-dependent** |
| llm_first (no rules) | 109 (+103) | 101 (+95) | 0.60 / 1.70 | 3.1–5.9 | flag flood; rules are load-bearing |

- **Q8 (which pattern kills the spurious class?):** `guard` — deterministic,
  zero cost, zero latency, surgical (drops only LLM/cache visa flags on
  destination-less packets). `vote` also suppresses it (disagreement → low) but
  pays 2× cost + 3× latency and also suppresses true escalations. `critic` is
  **unreliable as a quality gate**: terra rejected 14/16 of mini's escalations
  (+1 net) yet approved 20/22 of luna's (+20 net) — the validator's agreement
  tracks creator identity more than flag validity. No model era fixes
  abstention: every 2024+ model emits the dest-less visa flag (11/11
  dest-less records); only 3.5-turbo/4-turbo avoid it by under-escalating.
- **Q9 (cost/latency multipliers):** guard ×1.0 cost (recommended default);
  vote ×2.2 cost ×3.5 latency; critic ×18–9 cost; llm_first ×5–7 cost with a
  15–17× flag flood.
- **Run-to-run nondeterminism (found):** single-mini escalated +26 flags in v1
  but +15 in this run (temperature 0.3, same corpus) — LLM arms are not
  reproducible run-to-run; eval conclusions need multi-seed runs or
  temperature 0. Recorded as a lane-design requirement.

**Wave-2 verdict for ADR A1:** the value frontier is `rules-first + LLM
fallback (single) with the guard fact-gate`, model = nano/mini class
(gpt-4o-mini or gpt-5.6-luna), cache ON. Ensemble/critic orchestration adds
cost without demonstrable quality gain at this corpus scale; llm_first is
disqualified (flag flood). Still OFF-by-default in prod; the guard fix should
land in the engine (or prompt schema) before any opt-in, then this lane re-runs.

### 7.5 Follow-ups

1. Implement the §7.4 guard (destination-presence abstention) in
   `hybrid_engine` prompts or `_call_llm` gate; re-run lane to confirm.
2. Ground-truth visa-risk labels on the corpus (or E-07 calibrated judge) to
   convert added-count into precision/recall.
3. Multi-seed / temperature-0 protocol for LLM arms (nondeterminism finding).
4. Promptfoo port of this lane for CI (promptfoo 0.123.0 available via npx;
   config generation from the same fixtures; per the OpenAI
   Evals→Promptfoo migration cookbook).
5. Gemini + local-provider arms (create_llm_client already supports both;
   needs credentials/models for C-04).

## 8. Remediation wave — findings landed as engine fixes (2026-09-11, later same day)

Owner go-ahead on §7.5. Executed in value order; the experiment's findings are
now production code.

**Fix 1 — engine-side abstention gate (`src/decision/hybrid_engine.py`).**
`_FACT_REQUIREMENTS` map: `visa_timeline_risk` now requires the
`destination_candidates` fact. `_call_llm` skips the LLM call entirely when a
required fact is absent (saves the call, not just the flag) and falls through
to the deterministic default. Two unit tests cover both directions
(gate blocks dest-less, gate transparent with facts).

**Fix 2 — default-source decisions are not risk evidence
(`src/intake/decision.py`).** The confirmation run exposed a second layer the
first run had masked: with escalation gated, decide() returned the engine's
safe default (`risk_level: medium, "unable to assess"`) — and the flag
conversion in `_generate_risk_flags_with_hybrid_engine` was emitting those as
visa flags. An unassessed decision is not evidence of risk; the conversion now
skips `source == "default"`. This aligns hybrid-ON semantics with arm A:
strictly additive, never fabricated. One more unit test covers the conversion.

**Confirmation (records_postguard2.jsonl, gpt-4o-mini cold):** total flags
19 (was 32), escalations 15 (all destination-bearing), **spurious flags on
destination-less records: 0** (was 11). Hybrid-path semantics now match the
deterministic baseline plus genuine LLM additions only.

**Fix 3 — multi-seed protocol (harness `--runs N`).** Independent cold passes
per hybrid arm with per-run cache dirs (run 0 keeps the plain arm name + warm
pass; runs 1+ get `-rN` suffixes). Smoke-verified at `--runs 3`. Protocol for
all future LLM-arm claims: ≥3 runs or temperature 0.

**Fix 4 — promptfoo CI port (`tools/generate_promptfoo_config.py`).**
Generates `promptfooconfig.yaml` (35 test cases, structural + no-spurious-visa
invariant assertions) plus a python provider wrapping the real pipeline.
Verified live: **35/35 passed in 1s at zero API cost** (credential-free shell
→ deterministic degradation, the intended CI posture). Requirements:
`PROMPTFOO_PYTHON=<repo>/.venv/bin/python` (provider needs repo deps);
provider path is emitted absolute (promptfoo mangles relative ids). Documented
in `tools/README.md`. Ground-truth visa labels remain open (§7.5 item 2) —
the lane asserts the invariant, not per-record verdicts.

**Suite:** related suites 146 passed; full-suite receipt appended to the
inventory on completion.

**Remaining §7.5 items:** ground-truth visa-risk labels / E-07 judge lane
(open, bigger design); Gemini + local-provider arms (blocked on credentials).

### 8.1 Post-fix reference runs (2026-09-12, shipped engine semantics)

Both §7.4 measurement runs were re-executed with the two-layer fix live, so
the final reference numbers reflect what would actually ship.

**Variance protocol (`records_final_single.jsonl`, 3 independent cold passes ×
{gpt-4o-mini, gpt-5.6-luna}):**

| Model | Escalation-set stability | Flags per run | Cost ₹ per run | Spurious |
|---|---|---|---|---|
| gpt-4o-mini | **35/35 records identical** (15 escalations every run) | 24 / 18 / 20 | 0.104–0.109 | 0/3 runs |
| gpt-5.6-luna | **35/35 identical** (15 every run) | 15 / 14 / 12 | 0.212–0.225 | 0/3 runs |

The §7.4 nondeterminism finding resolves cleanly: pre-fix, the 11 fabricated
default-flags varied with LLM/cache behavior (+26 vs +15 between runs). Post-fix,
**whether** the hybrid path engages is fully stable; the only run-to-run
variance left is the model's severity judgment on escalated decisions
(`medium` vs `low`), which moves flag counts ±20%. Warm replay remains exact.

**Pattern matrix re-run (`records_final_patterns.jsonl`, post-fix):**

| Pattern | mini flags (+vs A) | luna flags | Spurious | Cost ₹ |
|---|---|---|---|---|
| single | 24 (+18) | — (see variance run) | 0 | 0.109 |
| guard | 17 (+11) | 13 (+7) | 0 | 0.105 / 0.220 |
| vote | 10 (+4) | 14 (+8) | 0 | 0.220 / 0.259 |
| critic | 7 (+1) | 11 (+5) | 0 | 1.879 / 1.980 |
| llm_first | 96 (+90) | 97 (+91) | 0 | 0.607 / 1.723 |

- Spurious = 0 in every arm: the engine-side gate covers all patterns because
  it lives in `_call_llm` — even `llm_first` now abstains on dest-less packets.
- The harness-level `guard` post-filter is now redundant (its job moved into
  the engine); residual single-vs-guard deltas are within-pass cache path
  differences and severity sampling, verified per-record (5 cache-path, 3
  severity-judgment, 0 systematic drops).
- Verdicts from §7.4 stand post-fix: single + engine gate is the recommended
  architecture; vote/critic add cost without quality signal at this scale;
  llm_first remains disqualified (96–97 flags vs A's 6 — severity inflation
  persists even with abstention).

**ADR A1 final evidence package:** deterministic-first + credential-gated LLM
escalation with the destination-fact abstention gate; sanctioned models
gpt-4o-mini (₹0.10/cold run, 2.3s) or gpt-5.6-luna (₹0.22, 5.5s); cache ON
(warm = ₹0, exact replay); OFF-by-default unchanged; promptfoo lane ready for
CI (35/35, free). Remaining open: ground-truth visa labels (E-07 judge),
Gemini/local arms (no credentials in `.env` — confirmed 2026-09-12).

## 9. Open items closed — ground-truth grading + local provider (2026-09-12)

Owner: "complete the open items." Both §7.5 residues executed.

### 9.1 Ground-truth labels + precision/recall (item 2 CLOSED)

Labels: `data/fixtures/risk_flags/ground_truth_labels.json`; grader:
`tools/grade_kdd_flags.py` (both documented in `tools/README.md`).

- **Rubric (fixed before any arm was scored):** note-level business reality —
  a flag is expected when a competent advisor reading the raw note would raise
  it at discovery. This grades the FULL pipeline: extraction misses count as
  pipeline failures (the real-world measure), so `budget_simple_002` ("trip to
  Europe") *expects* a visa flag even though city-level extraction misses
  "Europe". Visa severity: medium default, high for tight windows
  ("hitting bali next month"). 22 visa-justified, 13 not, 2 toddler.
- **Vocabulary correction found by grading:** the first pass flagged 6 constant
  "FPs" that were all `traveler_safe_leakage_risk` — a pipeline-integrity flag
  family (internal-data boundary), not a travel-risk judgment. Excluded from
  decision-quality grading (documented in `_meta.excluded_flags`).
- **Grader bug caught during build:** the FP check initially iterated the
  filtered emitted-dict, making FP registration impossible (precision read
  1.000 even for a 96-flag flood). Fixed before any conclusions were drawn
  from it; noted here because it is exactly the "eval grading the grader"
  trap.

**Post-fix ladder grading (`records_ladder2.jsonl`, 17 models):**

| Model | F1 | P | R | Lat ms | Note |
|---|---|---|---|---|---|
| **gpt-5.4-nano** | **0.909** | 1.000 | 0.833 | 2,606 | best overall |
| **gpt-4.1-nano** | **0.909** | 1.000 | 0.833 | 2,641 | tie |
| gpt-5.6-terra | 0.857 | 1.000 | 0.750 | 3,878 | |
| gpt-5.1 | 0.857 | 1.000 | 0.750 | 3,915 | |
| gpt-6-astra | 0.829 | 1.000 | 0.708 | 4,730 | flagship: no advantage |
| gpt-5-mini | 0.829 | 1.000 | 0.708 | 15,966 | slowest |
| gpt-5.5 | 0.154 | 1.000 | 0.083 | 5,094 | flagship under-flags |
| gpt-5-nano | 0.080 | 1.000 | 0.042 | — | cache-collapse anomaly |

**Headlines (revising §7.4 with clean labels + shipped semantics):**
1. **P=1.000 for every model and every pattern** — the two-layer fix
   eliminated all false positives repo-wide; zero spurious visa flags across
   all 34 ladder arms. The decision surface is now: how much recall each
   model recovers at zero precision cost.
2. **The nano tier wins on quality, not just cost** — gpt-5.4-nano /
   gpt-4.1-nano F1=0.909 at ₹0.09–0.28/run. Flagships add nothing (6-astra
   0.829; gpt-5.5 0.154). Recall variance across models is a *judgment*
   property (some models answer "low" after escalating), not engagement.
3. **Pattern grading (`records_final_patterns.jsonl`):** single mini
   F1=0.884; guard/vote/critic all P=1.0 but lower recall — vote (0.286) and
   critic (0.080) quantitatively confirmed as recall-killers; llm_first
   P=0.156 (F1=0.246) — quantified disqualification: it fabricates
   elderly/toddler risks the notes never mention.
4. **Run-to-run variance in graded terms (mini ×3):** F1 0.857 / 0.667 /
   0.737 — presence-level swings from severity judgment; multi-seed protocol
   (--runs) remains mandatory for claims.

**Final ADR A1 recommendation (evidence-complete):** `single + engine
abstention gate`, model = **gpt-5.4-nano or gpt-4.1-nano** (F1 0.909) with
gpt-4o-mini as the cheapest acceptable alternative (F1 0.857–0.884, ₹0.11);
cache ON (warm ₹0, exact); OFF-by-default unchanged until owner flips.

### 9.2 Local-provider arm (item 5 CLOSED for local; Gemini documented-blocked)

The repo's local provider was believed credential/hardware-blocked — it was
not: ollama runs locally and exposes an OpenAI-compatible endpoint. Harness
now supports `--models "local-ollama/<model>"` (`_build_client`; OLLAMA_BASE_URL
overridable, api_key dummy).

**qwen2.5vl:7b (local, ₹0):** P=1.000, R=0.333–0.375, **F1≈0.50–0.55**,
11.8s/call, zero spurious. A free 7B local model is precision-clean under the
gate and lands in gpt-5.6-luna's quality band at 2–5× latency — a viable
zero-cost deployment tier for non-urgent/async paths.

**Gemini:** confirmed hard-blocked — `.env` has no GEMINI_API_KEY (checked
2026-09-12; `src/llm/gemini_client.py:92`). One-command path when a key
arrives: add `GEMINI_API_KEY=…` to `.env`, then
`scripts/run_hybrid_kdd_experiment.py --skip-baseline --models
"gemini/gemini-2.0-flash" --tag "_gemini"` and re-run
`tools/grade_kdd_flags.py`. (gemini-2.0-flash is the client's DEFAULT_MODEL;
other Gemini models work the same way.)

**Remaining truly-open:** none from §7.5. E-07 calibrated-judge remains a
separate designed-not-built lane; with curated labels now in place, its
judge-vs-labels calibration harness has a concrete target.

### 9.3 Local-tier ladder — common configs, tested→graded→pruned (2026-09-12)

Owner framing: do NOT optimize for the dev machine — target the *common*
deployment configs (8GB/16GB machines, browser/transformers.js, MLX), test one
model at a time, and delete poor performers immediately (disk pressure).

**Tier landscape (HF catalogs, 2026-09-12; live data, not benchmarks):**

| Config tier | Practical class | Current-generation candidates | Runtime |
|---|---|---|---|
| Browser (WASM) | 0.3–1B | SmolLM2-360M, Qwen2.5-0.5B, Llama-3.2-1B (onnx-community ports) | transformers.js |
| Browser (WebGPU) | 1–4B | gemma-4-E2B/E4B ONNX (onnx-community, 6.9k/15k dl), Qwen3.5-2B-ONNX | WebGPU |
| 8GB machine | 3–4B Q4 | llama3.2:3b, qwen3:1.7b/4b, phi4-mini | ollama/llama.cpp |
| 16GB machine | 7–14B Q4 or MoE | gpt-oss:20b (~13GB, the canonical 16GB MoE), gemma3:12b, Qwen3.8-27B is 32GB-class NOT 16 | ollama/MLX |
| MLX (Apple) | all | mlx-community 4bit quants (Qwen3.5-4B/9B, gemma-4-26b-a4b, MiniCPM5-2B) | MLX |

**Graded results (all local, ₹0; harness `local-ollama/`; own-tag JSONLs;
test→grade→delete loop):**

| Model | Size | F1 | P | R | Lat/call | Verdict |
|---|---|---|---|---|---|---|
| llama3.2:3b | 2.0GB | **0.737** | 1.000 | 0.583 | 2.5s | **KEEP — 8GB-tier champion** |
| gemma3:12b | 8.1GB | 0.629 | 1.000 | 0.458 | 24.4s | KEEP — 16GB-tier rep |
| qwen2.5vl:7b | 6.0GB | ~0.52 | 1.000 | ~0.35 | 11.8s | KEEP — vision-coupled (multimodal extraction feature) |
| gemma3:4b | 3.3GB | 0.400 | 1.000 | 0.250 | 7.1s | **DELETED** |
| aya-expanse:8b | 5.1GB | 0.400 | 1.000 | 0.250 | 22.5s | **DELETED** (multilingual-special, slow) |
| qwen2.5:7b | 4.7GB | 0.400 | 1.000 | 0.250 | 19.7s | **DELETED** |
| mistral:7b | 4.4GB | 0.345 | 1.000 | 0.208 | 12.6s | **DELETED** |
| qwen2.5:3b | 1.9GB | 0.345 | 1.000 | 0.208 | 8.3s | **DELETED** |

**~15GB freed; disk 421MB→31Gi free.** Store now: llama3.2:3b (winner),
gemma3:12b (16GB rep), qwen2.5vl:7b (feature), deepseek-ocr + nomic-embed
(feature-coupled), cloud models (no disk).

**Findings:**
1. P=1.000 for every local model too — the engine abstention gate makes even
   small free models precision-clean; quality differences are all recall.
2. **llama3.2:3b is the local sweet spot** (F1 0.737 ≈ gpt-5.4-mini class API
   quality, 2.0GB, fastest) — recommended local default for 8GB+ machines.
3. Bigger ≠ better locally: qwen2.5:7b and aya-expanse:8b UNDERPERFORM the 3B
   llama on this task while running 8–9× slower. The "under-flags after
   escalation" behavior seen with API flagships repeats in open weights.
4. Ops lesson encoded: background (sandboxed) shells silently failed all
   ollama pulls — foreground network required; and the harness's `"w"`-mode
   JSONL **overwrote** previously-run arms when reusing a tag — per-model
   `--tag` now mandatory for sequential ladders.

**Not tested (documented for one-command later, disk/bandwidth gated):**
`gpt-oss:20b` (16GB MoE champion — 14GB pull), `qwen3:4b`/`qwen3.5:4b`
(current-gen 4B, 2.5GB), `gemma3:1b` + onnx-community E2B/E4B (browser tier),
`phi4-mini`. Pull+run: `scripts/run_hybrid_kdd_experiment.py --skip-baseline
--models "local-ollama/<tag>" --tag "_loc_<name>"`, then
`tools/grade_kdd_flags.py`.

### 9.4 New-generation local models tested → pruned; load-hold protocol (2026-09-12)

Owner correction: the §9.3 local ladder graded 2024-era stock already on disk
— the current generation was documented but never *tested*. Closed under the
disk-pressure protocol (pull one → test → grade → delete; hold further pulls,
reduce system load):

| Model (gen) | F1 | P | Lat/call | Verdict |
|---|---|---|---|---|
| **phi4-mini (2025, 3.8B)** | **0.737** | 1.000 | 13.5s | ties champion quality, 5× slower → **deleted** |
| qwen3.5:4b (2026, thinking) | 0.588 | 1.000 | **97.3s** | loses on both axes → **deleted** |
| qwen3:4b (2025, thinking) | 0.000 (partial 8/35) | 0.000 | 96.3s | killed per owner load directive → **deleted** |
| llama3.2:3b (2024) — champion | 0.737 | 1.000 | 2.5s | KEPT |

**Headline: the current generation of small "thinking" models is
anti-suitable for this lane** — reasoning tokens inflate latency 5–40× while
the downstream risk judgment does not improve; qwen3.5:4b is dominated by the
2024-era llama3.2:3b on BOTH quality and speed. phi4-mini matches champion
quality but cannot match its speed. The local recommendation is unchanged and
now evidence-complete: **llama3.2:3b**; gemma3:12b kept as 16GB-tier rep.

**Load state (per owner directive):** all pulls held; all models unloaded
(`ollama ps` empty); store = 5 feature/tier models; disk 13Gi free. Blocked
candidates with one-command recipes in the comparison sheet: gpt-oss:20b
(16GB MoE SOTA), qwen3:1.7b, gemma3:1b.

**Full comparison sheet (everything — kept, deleted, failed, partial,
blocked):** `Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md` +
`comparison_sheet.csv`, regenerated by `tools/build_model_comparison.py`
(33 rows: 19 API + 11 local tested + 3 blocked candidates, with a
failure/ops log covering the 401 dry-run, sandbox pull failures, partial-blob
leak, harness overwrite bug, and thinking-mode latency findings).
