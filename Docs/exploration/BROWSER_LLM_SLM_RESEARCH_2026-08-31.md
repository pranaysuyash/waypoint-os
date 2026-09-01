# Browser-Based / On-Device LLM & SLM Inference — Research for Waypoint OS

**Date:** 2026-08-31
**Persona:** PER-0882 Model-Routing Optimization Engineer
**Central question:** Which model should handle this particular case, and what evidence makes the routing policy better than one-model-for-everything?
**Scope:** Web research on in-browser LLM/SLM runtimes, structured-output support, practical constraints, and applicability to Waypoint OS (travel-intake pipeline: raw notes → canonical packet → quotes; public `/checker` tool at `frontend/src/app/(traveler)/itinerary-checker/`).

---

## 1) Runtime Landscape

| Runtime | Engine / backend | Representative models | Structured output | Typical model size (browser-usable) | Maturity | Source |
|---|---|---|---|---|---|---|
| **WebLLM (MLC AI)** | WebGPU via MLC/TVM-compiled kernels; OpenAI-compatible API; WebWorker offload | Llama 3.1/3.2/3.3, Qwen 2.5/3, Phi-3.5/4, Gemma 2/3, Mistral, SmolLM2 (full prebuilt registry in `prebuiltAppConfig.model_list`) | **Native constrained decoding via XGrammar**: JSON schema, regex, EBNF; `response_format: {type:"json_object", schema:...}`; function calling via `tools` | 1B q4f16 ≈ 0.6–1 GB; 8B q4f16 ≈ 4–5 GB; weights cached in browser Cache API | Actively maintained; production-usable for 1–8B on desktop Chromium; 70B impractical | [github.com/mlc-ai/web-llm](https://github.com/mlc-ai/web-llm), [MLC LLM docs](https://llm.mlc.ai/docs/), [structured-output blog](https://huggingface.co/blog/mlc-ai/webllm-structured-output-structured-generation) |
| **Transformers.js (HF)** | ONNX Runtime Web; WASM CPU default (q8 default dtype), WebGPU opt-in (fp32/fp16) | Llama 3.x, Qwen2/2.5/3, Phi-3, Gemma 2/3/3n, SmolLM3, Mistral, GPT-OSS (Hub tag `transformers.js`; e.g. `onnx-community/Llama-3.2-1B-Instruct-q4f16`) | **No built-in constrained decoding** — prompt-and-parse; client-side schema validation (e.g. zod) is app-level | q4 ≈ 0.5–1 GB for 1B-class; q8 ≈ 2x that | Mature for encode/classify/NER tasks; LLM generation works but slower and less optimized than WebLLM; browser caching via HF's Cache API | [huggingface.co/docs/transformers.js](https://huggingface.co/docs/transformers.js/en/index) |
| **Chrome built-in AI (Gemini Nano)** — Prompt API | Model shipped/maintained by Chrome itself, downloaded per-origin on first use | Gemini Nano (single fixed model; size varies per release — check `chrome://on-device-internals`) | **Native `responseConstraint`**: JSON schema **or regex** constrained decoding, in `prompt()`/`promptStreaming()` | ~2–3 GB (Chrome-managed, free to the app) | **Web stable in Chrome 148**; **stable for extensions since Chrome 138**; desktop Windows/macOS 13+/Linux/Chromebook-Plus only; **no Android/iOS** | [developer.chrome.com/docs/ai/prompt-api](https://developer.chrome.com/docs/ai/prompt-api) |
| **MediaPipe LLM Inference (web)** | WebGPU + WASM runtime (`@mediapipe/tasks-genai`) | Gemma-3 1B (.task), Gemma 2B/7B, Gemma-2 2B; conversion for Phi-2, Falcon, StableLM | **None documented** — only sampling controls (`topK`, `temperature`, `maxTokens`, `randomSeed`) | Gemma-3 1B class | **Maintenance mode** — Google directs web projects to the newer LiteRT-LM JS API | [developers.google.com/edge/mediapipe/.../llm_inference/web_js](https://developers.google.com/edge/mediapipe/solutions/genai/llm_inference/web_js) |
| **wllama** | llama.cpp compiled to WASM (Web Worker); WebGPU offload since v3.1 | Any GGUF (Llama, Qwen, Phi, Gemma…) | llama.cpp supports GBNF grammars; **wllama README does not document grammar/JSON-schema exposure** — treat as unverified | 2 GB hard cap per file (ArrayBuffer limit); chunked 512 MB downloads recommended; Q4/Q5/Q6 advised | Niche but active (~1.2k stars); **multithreading requires COOP/COEP headers** (SharedArrayBuffer) | [github.com/ngxson/wllama](https://github.com/ngxson/wllama) |
| **Apple / Safari on-device** | WebKit | Apple Intelligence / Foundation Models (~3B) | Native-only today: Swift Foundation Models framework with `@Generable` guided generation (iOS 26/macOS 26) | n/a for web | **No shipped web API** as of research date; WebKit is prototyping Web AI APIs (experimental LanguageModel-style surface) and standardization runs through the W3C Web Machine Learning WG (chartered to 2027-04-30); Safari 26 has only **partial WebGPU** | [webkit.org/blog](https://webkit.org/blog), [W3C WebML WG](https://www.w3.org/groups/wg/webmachinelearning/), [caniuse WebGPU](https://caniuse.com/webgpu) |

**Structured-output takeaway (critical for our pipeline):** exactly two runtimes give us real, in-browser grammar-constrained JSON today — **WebLLM (XGrammar)** and **Chrome's Prompt API (`responseConstraint`)**. Constrained decoding guarantees *schema-valid* output, not *correct* output — see §4 PER-0882 verdicts.

## 2) Chrome Built-in AI Status (as of 2026-08-31)

From the official [Prompt API docs](https://developer.chrome.com/docs/ai/prompt-api):

- **Stable:** Prompt API ships in **Chrome 148 (web)** and shipped for **extensions in Chrome 138**; Summarizer/Writer/Translator family follows the same built-in-AI track. (Earlier training-data assumptions of "138 stable for web" were wrong — web stable is 148.)
- **Platforms:** Windows 10/11, macOS 13+, Linux, ChromeOS (Chromebook Plus only). **Not Android, not iOS.** This caps our addressable share at desktop-Chromium only.
- **Hardware gates:** ≥22 GB free disk on the Chrome-profile volume (model evicted below 10 GB); **4 GB+ VRAM GPU, or 16 GB+ RAM with 4+ cores**. Eligibility is checked via `LanguageModel.availability()` — with the *same options* you will prompt with; `downloading` state exposes `downloadprogress`; `create()` requires user activation.
- **Model:** Gemini Nano, Chrome-managed and free to the app (no download served by us, no CDN cost, no version pinning — also a governance risk: Google updates it underneath you).
- **Structured output:** `responseConstraint` accepts a JSON schema or regex. The constraint consumes context budget — measure with `session.measureContextUsage()`, or set `omitResponseConstraintInput: true` and put instructions in the prompt instead.
- **Context:** `session.contextUsage`/`contextWindow` (no `maxTokens` param); oldest turns evicted on overflow (system prompt preserved); `QuotaExceededError` when nothing can be freed. `initialPrompts` with `prefix: true` can prefill a response format.
- **Languages:** en, ja, es, de, fr (English travel notes are fine).

## 3) Constraints & Browser Support Reality

- **WebGPU coverage: 85.56% globally** ([caniuse](https://caniuse.com/webgpu)) — Chrome/Edge 113+ (bulk of that figure), **Safari partial since 26**, **Firefox still disabled through 157**. Any WebGPU-only runtime (WebLLM, MediaPipe, Transformers.js-GPU) fails outright for ~1 in 7 users; WASM fallbacks (Transformers.js q8, wllama single-thread) are 5–20x slower.
- **First-load UX is the dominant cost.** A 1B q4 model is ~0.6–1 GB; Gemini Nano is Chrome's problem but gated on 22 GB free disk + hardware checks. Public-tool conversion funnels die on multi-hundred-MB downloads. Mitigations: Cache API persistence (WebLLM), Chrome-managed download (Prompt API), explicit user consent screens.
- **In-browser speed (approximate, community/MLC figures — must be benchmarked on our target hardware):** 1B-class q4 on Apple-silicon desktop Chrome ≈ 50–100+ tok/s; 8B q4 ≈ 15–25 tok/s decode. Extraction tasks are output-short, so prefill dominates; still, a ~2k-token messy travel note prefill on a 1B model is noticeably slower than a cloud round-trip on fast networks.
- **Memory ceilings:** browser tab GPU-memory limits are tighter than native; wllama caps single GGUF files at 2 GB; Chrome evicts Gemini Nano below 10 GB free disk.
- **Cloud comparison points (per 1M tokens, standard tier)** — [OpenAI pricing](https://developers.openai.com/api/docs/pricing): gpt-5-nano $0.05/$0.40, gpt-4o-mini $0.15/$0.60, gpt-5-mini $0.25/$2.00, gpt-5.4-nano $0.20/$1.25, gpt-5.4-mini $0.75/$4.50 (input/output). On-device marginal inference cost is **$0**, but the real costs shift to: download bandwidth (once per user), device battery/wall-clock, and **quality risk** (see §4). Our deterministic extractors (`src/intake/extractors.py`, ExtractionPipeline v0.2, pattern-based) are already a $0 tier-0 "model".
- **Structured output ≠ correctness.** XGrammar and `responseConstraint` eliminate malformed JSON, but a weak SLM under constraint happily emits *valid JSON with wrong field values* — the exact silent-quality-loss failure PER-0882 warns about.

## 4) Waypoint Applicability (with PER-0882 verdicts)

### (a) Public checker running extraction fully in-browser

**Verdict: REJECTED for default path; "device-only mode" as opt-in is NOT YET.**

- **Today's reality:** `/checker` (`frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx`) posts notes to the backend (`spine_api/routers/public_checker.py` → `run_public_checker_submission`); extraction runs server-side. So notes already leave the device — the privacy claim of in-browser is a *change*, not a preservation.
- **Against PER-0882 failure modes:**
  - *Cost savings measured without task success* — cloud extraction of a standard messy note costs ~$0.001–0.01 (gpt-5-mini class, ~2k in / 1k out). There is no cost problem to solve. Zero-API-cost is not a win if packet quality drops and the free tool's purpose (demonstrate pipeline quality → convert agencies) is damaged.
  - *Weak classifier causing silent quality loss* — an in-browser 1–3B model will be materially weaker than our cloud tier on exactly the hard cases that matter (colloquial notes; see `Docs/exploration/DEMO02_COLLOQUIAL_EXTRACTION_GAPS_2026-08-31.md`). Constrained decoding hides the failure as plausible-but-wrong JSON.
  - *Routing on prompt length alone* — gating "in-browser vs cloud" on anything except measured extraction coverage would be arbitrary.
- **What would flip it:** coverage ≥85–90% parity vs cloud tier on our golden set + 85%+ WebGPU/Prompt-API coverage + a premium privacy story ("notes never leave your device") as an explicit user choice, not default.

### (b) Client-side pre-extraction/drafting with server verification

**Verdict: JUSTIFIED as a bounded experiment (Chrome Prompt API first); not yet for production trust.**

- This is the correct shape of the idea: local SLM produces a *draft*; the server's canonical pipeline validates and corrects; server output remains authoritative. Escalation/verification is exactly what PER-0882 prescribes for weak local tiers.
- **Best first vehicle is Gemini Nano, not WebLLM**: zero model download served by us, native `responseConstraint` against our packet schema, `availability()` gating gives a clean capability probe. Ship as progressive enhancement: *if* `availability() === "available"`, prefill form fields client-side; *always* submit raw notes for canonical extraction. The only thing this saves is user typing latency — value is UX, not cost.
- **Guardrails (non-negotiable):** server verify is the acceptance authority; log draft-vs-server field disagreement rate as a telemetry signal (this doubles as free labeled data for §d); never let a client draft bypass gates.
- **PER-0882 check:** *no evaluation of router itself* — the disagreement-rate metric must exist before this ships, otherwise we can't tell if the pre-fill helps or harms.

### (c) Routing policy design — deterministic tier is already the cheapest model

**Verdict: JUSTIFIED — this framing is correct and already half-built.**

Waypoint's routing stack, expressed in model-tier terms:

| Tier | What | Cost | Where today |
|---|---|---|---|
| 0 | Deterministic extractors/heuristics (ExtractionPipeline, geography, route analysis) | $0 | `src/intake/extractors.py`, `src/intake/geography.py`, `src/intake/route_analysis.py` |
| (proposed 0.5) | On-device SLM draft (Gemini Nano → WebLLM) | $0 + device time | §b experiment |
| 1 | Cloud small (gpt-5-mini/nano class) for standard messy notes | ~$0.001–0.01/note | current cloud path |
| 2 | Cloud large, escalation-only (validation failure, high ambiguity, high-stakes fields) | ~10–50x tier 1 | escalation path |

- The right router signal is **not prompt length** — it's the pipeline's own evidence: deterministic coverage %, validation gate outcomes, ambiguity/escalation flags, confidence. Classification happens after tier 0 runs, from real coverage data, not text statistics.
- **Privacy as a routing dimension:** travel notes contain passports/phones. A PII-density signal could (a) route *pseudonymized* text to cloud with local reattachment, or (b) justify tier-0.5-local for users who refuse cloud. Both are policy choices requiring explicit consent UI — none exists yet.
- `checker_model` is already an agency-level setting (`frontend/src/lib/api-client.ts` ~line 809) — the routing knob exists; a policy layer formalizes what is currently manual.

### (d) What `routing_health` measures today vs. what a router-level evaluation needs

**Measured today:**
- `build_routing_metrics` in `src/evals/agentic_feedback.py` (line 508) feeds **routing_health** into the D6 gate snapshot; `RoutingHealthAuthority` (`src/evals/audit/public_authority.py`) reads `{status, blocks_ci, thresholds}` with operational thresholds like `fallback_trigger_rate_warning: 0.3` and `latency_p95_ms_critical: 30000` (`tests/evals/test_routing_health_gate.py`); alerting/paging on warning/critical states lives in `src/analytics/logger.py` (`log_routing_health_alert`, dedup signatures, paging escalation).

**What these are:** operational health of an *existing* router (fallback rate, latency). **What PER-0882 says a router needs that we lack:**
1. **Task-success ground truth** — field-level extraction accuracy against human-repaired packets (the repair surface is our label source). Fallback rate tells us the router escalated; it does not tell us the escalation produced a *correct* packet.
2. **Per-tier quality profiles** — measured accuracy of deterministic vs each cloud model vs (future) local SLM on a versioned golden set, so tier assignment is evidence-based.
3. **Escalation outcome tracking** — did tier-2 retries actually fix validation failures, or do we pay 10–50x for the same wrong answer?
4. **Router regression suite** — frozen request bundles replayed against policy versions; policy changes gated like code (same CI philosophy as the existing D6 snapshot gate).
5. **Cost per *accepted* packet** (not per token) — the only cost number that survives the "savings without task success" critique.

## 5) Recommended Routing Policy Sketch

```
request(note) ──► Tier 0: deterministic extraction (always, free)
                     │
                     ├─ coverage high + gates pass ──► DONE (most well-formed notes)
                     │
                     └─ coverage low / ambiguity / gate failure
                          │
                          ├─ [future, opt-in] Tier 0.5: on-device draft
                          │     only if LanguageModel.availability()==available
                          │     server re-extracts; disagreement rate logged
                          │
                          ├─ Tier 1: cloud small (default escalation)
                          │     pseudonymize PII-dense spans first (policy TBD)
                          │
                          └─ Tier 2: cloud large
                                only on Tier-1 validation failure or
                                high-stakes field conflicts; outcome tracked
```

- **Classifier:** post-tier-0 coverage/confidence signals + gate results. No prompt-length heuristics.
- **Escalation:** on structured-validation failure with bounded retries; every escalation recorded with before/after field diff.
- **Router evaluation:** shadow-mode replay of golden set on every policy change; promotion requires ≥ current policy's task-success at ≤ current cost.
- **Local tier admission criteria (when we revisit §a/§b):** golden-set parity ≥85% vs tier 1 AND device-coverage ≥85% AND explicit privacy consent AND disagreement telemetry in place. Until all four hold: **one well-instrumented cloud tier beats a cheaper silent tier.**

## 6) Open Questions

1. **SLM extraction accuracy on our data** — no published benchmark covers "messy colloquial travel notes → nested packet schema". Needs a golden-set eval of Llama-3.2-1B/Qwen3-1.7B/Gemini-Nano before any local tier is credible.
2. **Gemini Nano fleet coverage** — desktop Chrome 148+ with hardware eligibility is a minority of *our* traffic mix (Android/iOS Safari excluded); is there any real population for tier 0.5?
3. **`responseConstraint` context cost** — our packet schema is large; how much of Nano's context window does the constraint itself consume, and does `omitResponseConstraintInput` degrade quality?
4. **Safari/Firefox trajectory** — WebKit's Web AI APIs and WebNN (W3C WebML WG, chartered to 2027-04) could change the coverage math within 12–18 months; re-check before investing in WebLLM-specific integration.
5. **LiteRT-LM JS** (MediaPipe's successor) — maturity and structured-output support unverified; re-evaluate if Google ships grammar support.
6. **wllama GBNF exposure** — unverified whether the WASM binding surfaces llama.cpp grammar constraints; would need a spike.
7. **PII pseudonymization round-trip** — is span-mask → cloud → local reattachment actually safer end-to-end than full-text cloud under our current DPAs, or is it security theater?

---

### Source index
- WebLLM: [github.com/mlc-ai/web-llm](https://github.com/mlc-ai/web-llm) · [llm.mlc.ai/docs](https://llm.mlc.ai/docs/) · [WebLLM structured outputs (XGrammar)](https://huggingface.co/blog/mlc-ai/webllm-structured-output-structured-generation)
- Transformers.js: [docs](https://huggingface.co/docs/transformers.js/en/index)
- Chrome built-in AI: [Prompt API](https://developer.chrome.com/docs/ai/prompt-api)
- MediaPipe web LLM: [docs](https://developers.google.com/edge/mediapipe/solutions/genai/llm_inference/web_js)
- wllama: [github.com/ngxson/wllama](https://github.com/ngxson/wllama)
- Apple/WebKit: [webkit.org/blog](https://webkit.org/blog) · W3C WebML WG: [w3.org/groups/wg/webmachinelearning](https://www.w3.org/groups/wg/webmachinelearning/)
- WebGPU support: [caniuse.com/webgpu](https://caniuse.com/webgpu) (85.56%, checked 2026-08-31)
- Cloud pricing: [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing)
- Repo grounding: `src/intake/extractors.py`, `src/evals/agentic_feedback.py`, `src/evals/audit/public_authority.py`, `src/analytics/logger.py`, `tests/evals/test_routing_health_gate.py`, `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx`, `frontend/src/lib/api-client.ts`, `spine_api/routers/public_checker.py`
