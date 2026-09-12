# Multi-Vendor Serving Experiment — design before experiment (2026-09-12)

Owner question: *would it be a better experiment to also use OpenRouter or
other providers to test even already-tested local models plus new models — so
we know whether serving locally is fine or online models with better
latency/cost are good? Explore OpenRouter (claims a built-in router),
Cerebras, Grok for faster inference, HF, and other marketplaces; explore and
document BEFORE we plan the experiment.*

Status: **DESIGN ONLY — no experiment executed, no keys required yet.**
Upstream: `Docs/exploration/HYBRID_KDD_EXPERIMENT_2026-09-11.md` (model
quality axis COMPLETE: `Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md`);
this document adds the missing axis: **the serving layer**.

---

## 1. What is actually being tested (and what isn't)

The completed ladder answered: *which model weights produce the best risk
flags at what quality?* It did NOT answer:

- **Does the same model, served by different venues, behave the same?**
  (Quantization differs per venue: local Q4_K_M vs hosted FP8/BF16 — this is a
  real quality variable, not just plumbing.)
- **What does the latency/cost/reliability frontier look like across
  venues?** (Local: 0₹ but 2.5–97s/call on the dev machine; hosted: sub-second
  claims at per-token cost.)
- **Do the routers deliver?** (OpenRouter auto-router, HF `:fastest` /
  `:cheapest` — both claim to pick well; neither has been measured against a
  deterministic task lane.)

Crucially, the experiment infrastructure already separates the two axes:
quality is graded against the note-level ground-truth labels (F1/P/R), and
serving metrics (per-call latency, cost) are already captured per decide-call
by the harness. The serving experiment **reuses the same 35-record corpus,
labels, grader, and sheet** — it adds venue as a dimension, not new machinery.

## 2. Vendor / marketplace landscape (researched 2026-09-12; sources inline)

### 2.1 OpenRouter (openrouter.ai) — meta-router marketplace
- Hundreds of models via one OpenAI-compatible endpoint
  (`https://openrouter.ai/api/v1` — drop-in for the OpenAI SDK).
- **Router lineup (docs/llms.txt, fetched 2026-09-12):** Auto Router
  ("automatically select the best model for your prompt"), Pareto Router,
  Fusion Router, Free Models Router, Latest-Model Resolution, Model Fallbacks,
  Auto Exacto; plus **routing metadata header** surfacing what was chosen.
- **Model variants:** `:free`, `:nitro` (high-speed), `:floor` (lowest-cost),
  `:thinking`, `:online`, `:extended`.
- BYOK (bring your own provider keys), Zero-Data-Retention option, in-region
  routing ("Sovereign AI"), workspace budgets, Zero Completion Insurance.
- Pricing: passthrough per-provider + credits; no markup documented on the
  pages fetched (verify at signup).

### 2.2 Groq (groq.com) — LPU ultra-low-latency host
- Models served (console.groq.com/docs/models, fetched 2026-09-12):
  **gpt-oss-20b at ~1,000 t/s ($0.075/$0.30 per 1M in/out)**,
  gpt-oss-120b at ~500 t/s ($0.15/$0.60), llama-3.1-8b-instant ~560 t/s,
  llama-3.3-70b ~280 t/s; preview: Qwen3.6-27B, Qwen3.8-27B, MiniMax M2.7.
- OpenAI-compatible (`api.groq.com/openai/v1`). Developer plan rate limits
  (250K TPM / 1K RPM on GPT-OSS) — effectively a free evaluation tier.
- **Key relevance: gpt-oss-20b is the exact model we could not fit locally**
  (14GB pull killed during the disk crisis) — Groq serves it ~30× faster than
  our local tier could, at trivial cost.

### 2.3 Cerebras (cerebras.ai/inference) — wafer-scale speed host
- Claims 2,000+ t/s (Llama 4 Scout quote), "up to 30× faster than GPU
  systems"; catalog highlights GPT-5.6 Sol Ultrafast, Kimi K2.6, Codex-Spark.
- OpenAI-compatible ("two code changes"); **$5 free credit**; pay-per-token
  Developer tier from $10 top-ups.

### 2.4 Hugging Face Inference Providers — one-token router (docs fetched)
- `https://router.huggingface.co/v1` — **drop-in OpenAI-compatible chat
  endpoint**; model ids take policy suffixes: `:fastest` (default, max t/s),
  `:cheapest` (min $/output-token), `:preferred` (user's priority order), or a
  literal provider (`openai/gpt-oss-120b:groq`).
- **17 partner providers**: Groq, Cerebras, Together, Fireworks, DeepInfra,
  Novita, Baseten, Cohere, Featherless, HF Inference, Nscale, OVHcloud,
  Public AI, Replicate, Scaleway, Z.ai, WaveSpeed.
- Auto-failover between providers; no markup on provider rates; **auth = a
  standard HF fine-grained token** (the HF token this workspace already has).
- `GET /v1/models` returns per-provider pricing/context/latency/throughput —
  the harness can ingest live pricing instead of hardcoding it.

### 2.5 xAI / Grok (docs.x.ai) — TO VERIFY (fetch blocked by quota this session)
- Known: OpenAI-compatible (`api.x.ai/v1`), Grok family + Grok Code Fast;
  whether they host open-weight third-party models is unverified — check at
  experiment time. Include only if Phase-2 warrants.

### 2.6 Ollama Cloud — already in this workspace
- The local ollama store already lists `qwen3.5:cloud`, `gemma4:31b-cloud`,
  `kimi-k2.5:cloud`, `glm-5:cloud`, `minimax-m2.7:cloud`,
  `nemotron-3-super:cloud` — ollama's hosted tier is **already configured in
  the tooling** (`local-ollama/` provider path, zero new integration), making
  it the cheapest first hosted comparison leg.

### 2.7 Others noted (not prioritized)
Together / Fireworks / DeepInfra / Novita — reachable *through* the HF router,
so direct keys add little for this experiment. Cloudflare Workers-AI (edge
tier) — different niche (tiny models), FOR-LATER.

## 3. Experiment design (KDD-framed, reusing the lane)

**Selection/preprocessing/mining are frozen** (35-record corpus, labels,
grader, decide-log instrumentation). New dimension: **venue**.

### Same-weights matrix (the core — isolates the serving layer)

| Weights | local (ollama) | Groq | Cerebras | HF :fastest | HF :cheapest | OpenRouter auto/nitro/floor |
|---|---|---|---|---|---|---|
| gpt-oss-20b | re-pull 14GB | ✅ (~1000 t/s) | ? | ✅ | ✅ | ✅ |
| llama-3.1/3.2-8B class | llama3.2:3b ✅ kept | ✅ 560 t/s | ✅ | ✅ | ✅ | ✅ |
| qwen3.5-4b | tested (deleted; re-pull) | preview | ? | ✅ | ✅ | ✅ |

Research questions:
- **Q10 (same-weights quality drift):** does F1 change across venues for
  identical weights? Hypothesis: ≈equal for same precision; local Q4 vs hosted
  FP8/BF16 may differ measurably — this is the real quality question.
- **Q11 (latency frontier):** end-to-end decide latency + est. t/s per venue;
  local vs hosted crossover point.
- **Q12 (cost per run):** ₹/35-records per venue (API-reported usage where
  available; HF `/v1/models` pricing ingestion).
- **Q13 (router quality):** do OpenRouter auto/:nitro/:floor and HF
  :fastest/:cheapest make the choice we'd make manually? (router-metadata
  header + HF provider pinning let us verify what actually served.)
- **Q14 (privacy posture):** all legs flow through the repo's egress PII
  redaction layer already; local remains the only zero-egress option —
  document as a decision gate for production use, not just a benchmark row.

### Integration (small, additive)
- Extend harness `_build_client` with a generic
  `openai-compatible:<base_url_env>:<model>` provider form (OpenRouter, Groq,
  Cerebras, HF router all drop in; local-ollama already proved the pattern).
- Extend `comparison_sheet.py` MANIFEST tier field: `venue` becomes part of
  the row key (same weights may appear on multiple rows).
- Multi-seed (`--runs`) mandatory per Q-run variance findings.

### Proposed sequencing (phases, each independently useful)
1. **Phase 1 — HF router only** (one token we already hold): all three
   policies (`:fastest/:cheapest/:preferred`) × 3 open-weights models →
   answers Q10–Q13 for the router with zero new keys.
2. **Phase 2 — OpenRouter** (one key): auto vs HF `:fastest` head-to-head;
   `:nitro`/`:floor` vs manual venue choice.
3. **Phase 3 — same-weights deep-dive**: re-pull gpt-oss:20b locally (14GB,
   needs disk window) + direct Groq key → the cleanest local-vs-hosted pair.
4. **Phase 4 — Cerebras direct + xAI verification** (optional).

Estimated total cost if all phases run: **≈₹40–80** (sub-$1) at 35 records ×
~6 venue-arms × 1–3 runs; Groq dev-tier rate limits may make Phase-3's Groq
leg free. Runtime ≈1–2 h wall clock, dominated by local legs.

## 4. Decision needed from owner (before experiment)

1. **Keys:** OpenRouter key (Phase 2) and/or direct Groq/Cerebras keys
   (Phases 2–4). HF token exists.
2. **Budget:** authorize ≈₹40–80 hosted spend (or Phase 1 only ≈₹10–20,
   partially free-tier).
3. **Disk window:** Phase 3's local gpt-oss:20b leg needs ~14GB (delete-after
   test, per the established protocol).

## 5. Position (opinion, per collaboration style)

Yes — this is the right next experiment, with one sharpening: the interesting
question is **not** "hosted vs local" in general (quality is already decided —
the gate makes even free local models precision-clean). It is three narrower
questions: (a) does venue/quantization move F1 at all for the same weights;
(b) where is the latency/cost crossover given llama3.2:3b's shockingly good
local showing; and (c) do the routers actually route well — which, measured
against a deterministic graded lane with router-metadata verification, would
be a genuinely novel datapoint. Phase 1 first (HF token, near-zero cost),
then decide on 2–4 from its results.

---

## 6. Phase 1 EXECUTED (2026-09-12, later same session) — HF router, 6 arms

Owner said "continue" → Phase 1 ran with the workspace's existing HF
credential (found in the macOS keychain after the token-file path proved
empty). Harness gained a generic `hf-router/` provider (`_build_client`;
HF_TOKEN env; router base URL overridable). Models trio (router catalog
reality: no llama-3.2-3b/Qwen3.5-4B hosted): gpt-oss-20b (7 providers),
Qwen/Qwen3-4B-Instruct-2507, meta-llama/Llama-3.1-8B-Instruct — each under
both `:fastest` and `:cheapest` policies. 35 records × 6 arms; PII egress
gate active on every call; actual spend ≈ a few cents.

### Results (P=1.000 on all six; escalations exactly 15 on all six)

| Arm | F1 | P | R | Lat/call |
|---|---|---|---|---|
| **Llama-3.1-8B :fastest** | **0.800** | 1.000 | 0.667 | **1,208 ms** |
| Llama-3.1-8B :cheapest | 0.629 | 1.000 | 0.458 | 5,027 ms |
| Qwen3-4B-2507 :fastest | 0.500 | 1.000 | 0.333 | 2,178 ms |
| Qwen3-4B-2507 :cheapest | 0.345 | 1.000 | 0.208 | 2,473 ms |
| gpt-oss-20b :fastest | 0.286 | 1.000 | 0.167 | **792 ms** |
| gpt-oss-20b :cheapest | 0.286 | 1.000 | 0.167 | 3,056 ms |

Local champion reference: llama3.2:3b F1 0.737 @ 2,485 ms; best API tier:
gpt-5.4-nano / 4.1-nano F1 0.909 @ ~2,600 ms.

### Findings

1. **Q10 (venue/quantization drift on same weights): PRELIMINARY YES.**
   Llama-3.1-8B ΔF1 = 0.171 between policies; Qwen ΔF1 = 0.155. Honest
   caveat: single pass per policy, and the observed same-venue run-variance
   band is ~±0.19 (mini: 0.857/0.667/0.737) — so these deltas are
   *suggestive, not conclusive*; the multi-seed protocol (`--runs 3`) is
   required before a firm claim. The direction was consistent on both models
   tested (fastest ≥ cheapest on F1), and on latency (3/3).
2. **`:fastest` dominated `:cheapest` 3/3 on latency AND 3/3 directionally on
   quality** — for this lane, cheapest is a dominated strategy (likely routes
   to more aggressively quantized providers).
3. **Llama-3.1-8B:fastest beats the local champion on BOTH axes** (0.800 @
   1.2s vs 0.737 @ 2.5s) and lands in the top API tier's neighborhood
   (0.829–0.909) at 2× nano-tier speed. For non-privacy-critical, online
   deployments this is the new default candidate.
4. **Serving cannot fix a model**: hosted gpt-oss-20b at 792 ms still
   under-flags (F1 0.286) — same trait as the API ladder showed. Quality is
   weights+prompt-side; venue moves speed/cost and (maybe) a few points.
5. **Engagement stability across venues**: exactly 15 escalations on every
   arm — the engine's engagement is venue-invariant; only severity varies.
6. **Bug found + fixed in the harness** (this run's commissioning): arm ids
   containing "/" (`openai/gpt-oss-20b:fastest`) made the prompt-archive
   filename a nested path — the finally-block write raised AFTER the
   successful LLM call, masking every result as `default` (P=1.0-but-R≈0
   signature, zero archives). Filename sanitization added; cache-dir names
   sanitized with the same hazard in mind (`_safe_name`). First 6-arm pass
   (pre-fix) is preserved in git-less history only via this note; data was
   rerun post-fix.

### Answer to the owner's original question

Serving **locally is no longer automatically the right call for online
paths**: a hosted 8B open-weights model now beats our best local setup on
both quality and speed at negligible cost. Local keeps three real advantages:
zero data egress (privacy gate), zero marginal cost at scale, and offline
operation. Routers work — but `:fastest` > `:cheapest` here. Phase 2
(OpenRouter head-to-head) and Phase 3 (multi-seed same-weights confirmation)
are ready when wanted.

### 6.1 Phase 1b — large models hosted (2026-09-12, same session)

Owner directive: when serving hosted, don't limit to smaller models —
provider-side caching, throughput, and quantization infra make the big
classes viable. Tested the 20B→235B class under `:fastest`:

| Model (hosted) | F1 | P | R | Lat/call | Note |
|---|---|---|---|---|---|
| **gemma-3-27b-it** | **0.629** | 1.000 | 0.458 | 6,749 ms | best of the large class |
| Qwen3-235B-A22B-2507 | 0.452 | 1.000 | 0.292 | 1,458 ms | sev-agreement 0.14 (worst) |
| GLM-5.3-Flash | 0.286 | 1.000 | 0.167 | 1,859 ms | |
| gpt-oss-120b | 0.286 | 1.000 | 0.167 | **734 ms** | 11 providers; fastest large arm |
| Llama-3.3-70B | 0.222 | 1.000 | 0.125 | 2,205 ms | scale didn't help llama |
| DeepSeek-V4-Flash-0731 | 0.154 | 1.000 | 0.083 | 3,656 ms | 1M ctx; needed JSON-recovery |
| Qwen3.5-9B | (failed-run) | — | — | 23,339 ms | thinking: 7/15 calls empty content even at 4096 tokens |

vs. Phase-1 small class: Llama-3.1-8B:fastest 0.800 @ 1.2s; local champion
0.737 @ 2.5s; API nano tier 0.909 @ 2.6s.

**Finding — scale does NOT rescue this task.** Every model from 20B to 235B
under-flags relative to the 8B and the nano API tier; gpt-oss-120b at 734 ms
scores 0.286, and the 235B MoE scores 0.452 with the worst severity
calibration of any arm. Lane quality is a *calibration* property (does the
model treat missing-visa-facts as flag-worthy), not a capability scale
property. The owner's serving hypothesis is half-confirmed: hosted serving
removes the size constraint and the big models are trivially cheap and fast —
but the best hosted large model (gemma-3-27b, 0.629) still loses to the best
hosted small one (Llama-3.1-8B, 0.800). Model choice remains
calibration-first; venue choice is orthogonal.

**Production hardening landed from this phase** (in the shared client, not
the harness): `_recover_json_object()` in `src/llm/openai_client.py` —
reasoning models on multi-vendor endpoints emit malformed JSON (DeepSeek's
doubled-brace `{\n{...}`); the recovery tries each `{` as a balanced-block
start and parses the first valid candidate. 6 unit tests
(`tests/test_llm_json_recovery.py`, including the exact DeepSeek shape);
105+ llm/hybrid tests green. Also: hf-router client raised to 4096 max_tokens
(env-overridable) because reasoning models exhaust 1024 before emitting
content.

**Failure documentation:** Qwen3.5-9B hosted = failed-run (empty content is
unrecoverable client-side — the model puts everything in `reasoning` and
content stays empty; matches its local 97s/call anti-suitability). First
hf2 pass was invalidated by a shell-quoting bug (`$m:fastest` unbraced — zsh
history-expansion mangled model ids into absolute paths; 400s from the
router), re-run clean; the bad file was deleted, per no-bad-data doctrine.

**Updated recommendation stack:**
1. Online/default: hosted Llama-3.1-8B:fastest (F1 0.800, 1.2s, ~free) —
   pending multi-seed confirmation.
2. Cheapest acceptable online: gpt-4o-mini / nano tier (0.857–0.909, ₹0.1–0.3).
3. Privacy-critical/offline: local llama3.2:3b (0.737, ₹0).
4. Large hosted models: no advantage on this lane; use only if another task
   needs their capability (they're all P=1.000 — safe, just conservative).

### 6.2 Owner follow-up — reasoning models for extreme cases (2026-09-12)

Owner idea: even if reasoning models are bad as the default escalation path,
can the agentic flow use them selectively where reasoning helps?

**Architecture simulated (post-hoc blend of existing single-pass runs):**
tier-1 = Llama-3.1-8B:fastest decides everything; tier-2 = a reasoning model
reviews ONLY the records where tier-1 said "low" (second-opinion-on-negatives
— a runtime router may legitimately read tier-1's output). Extreme-case
trigger = tier-1 negative; 19 of 35 records triggered.

| Tier-2 candidate | Blended F1 | Δ vs tier-1 | Extra TPs |
|---|---|---|---|
| gpt-oss-20b | 0.829 | +0.029 | 1 (budget_easy_002, severity correct) |
| Qwen3-235B-A22B | 0.829 | +0.029 | 1 |
| DeepSeek-V4 / gpt-oss-120b / GLM-5.3 / o4-mini | 0.800 | +0.000 | 0 |

**The structural insight:** gpt-oss-20b was our WORST standalone arm (0.286)
yet the BEST second opinion — conservative reasoning models are ideal tier-2
validators because they almost never override (P stays 1.000 — zero FP risk
added) and only augment when confident. The composition turns an unusable
model into a useful one.

**But the honest verdict is NOT YET:** the 3-seed confirmation of tier-1
(F1 0.829 / 0.769 / 0.737, ±0.05 band, P=1.000 and 15 escalations on every
pass) shows the tier-2 gain (+0.029) is *within seed variance*. On this
corpus the extreme-case tier is not statistically justified. It stays in the
design as a policy knob with a defined trigger (tier-1 negative → tier-2
review) to be re-tested on a corpus with genuinely reasoning-bound cases
(visa-policy nuance, multi-hop temporal windows) — this corpus's hard cases
are mostly extraction-lossy, not reasoning-bound.

**Multi-seed receipt (records_hf1_llama8b_multi.jsonl):** F1 0.829 / 0.769 /
0.737; escalations 15/15/15; latency 1,570 / 1,291 / 1,144 ms; P=1.000 every
pass. Headline for the recommendation stack: hosted Llama-3.1-8B:fastest =
**F1 0.74–0.83, beats-or-matches the local champion on all seeds.**
