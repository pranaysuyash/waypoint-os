# C-04 — SLM Benchmark Protocol: Messy Travel Notes → Nested Canonical Packet

**Date:** 2026-09-02. **Status:** protocol design (not executed) — this doc is the executable spec.
**Persona:** PER-0882 Model-Routing Optimization Engineer.
**Why this benchmark exists:** no published benchmark covers "messy colloquial travel notes → nested structured packet" (browser research §6.1); the deterministic extractors are the incumbent, and any on-device tier (router T0.5) is inadmissible until measured (`BROWSER_LLM_SLM_RESEARCH_2026-08-31.md` §4a/§5; synthesis G-16). The benchmark itself is the contribution.
**Companions:** `C03_ROUTER_DESIGN_2026-09-02.md` (tier ladder, quality profiles), `C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md`.

---

## 1. Research question (one line)

**Does a 1B-class SLM, under constrained decoding, beat the tier-0 deterministic extractors on colloquial/adversarial phrasings — at a quality level that justifies an opt-in on-device draft tier — or does it only add plausible-but-wrong fields?**

The baseline is **not** "zero": it is the existing `ExtractionPipeline` (`src/intake/extractors.py`, 22 pattern passes, ~30 fact fields), already anchored by live lanes (budget F1 0.9524 on 20 fixtures; `data/evals/d6_audit_gate_snapshot.json` → `budget_health`). Every SLM number is reported as a **delta vs tier-0 on the identical corpus**.

---

## 2. Dataset

Built from corpora that already exist in-repo, plus one authored split. Sizes are small today; §2.5 defines the growth path.

| Split | Source | Size today | Notes |
|---|---|---|---|
| **A. Budget** | `data/fixtures/budget/golden_dataset.json` | 20 fixtures | The live budget lane's corpus (`snapshot.py:42,92-148`); anchor F1 0.9524. Includes `raw_input` |
| **B. Colloquial** | `data/fixtures/extraction/colloquial_golden.json` | 15 fixtures | Hard class by design (`difficulty: "hard"`; e.g. `"want to do japan"`, `colloquial_golden.json[0]`); tags per fixture (`verb_object`, `lowercase_text`, …) enable per-pattern slices. **This is the benchmark's center of gravity** |
| **C. General extraction golden** | `data/fixtures/extraction/golden_dataset.json` | 50 fixtures | ⚠ Currently **not runnable**: fixtures carry no `raw_input` (registered gap **N-02**) — author runnable content first, or exclude and say so in the report |
| **D. Scenario-derived notes** | scenario corpus backing the live scenario lane (`tests/evals/test_30_scenario_corpus_gate.py`, `data/fixtures/scenario_*.json`) | ~30 | Renders each scenario's traveler-facing text as a raw note; nested targets (multi-destination, open-jaw) exercise packet nesting |
| **E. Adversarial (to be authored)** | Hinglish, voice-transcript (ASR artifacts), emoji-dense, mixed-language, contradiction-laden | target ≥40 | Registered as explore item E-11; also the holdout-leak antidote (**G-06**): author from *new* phrasings, never paraphrases of A–D |

### 2.1 Holdout discipline (non-negotiable)

- Split each corpus: **70% dev / 30% hidden holdout**, holdout files 0700-style access (evals/audit lane only) per the G-06 policy direction.
- The colloquial leak precedent (fixtures verbatim in `tests/test_extraction_fixes.py`) is why model candidates must **never** see dev fixtures in their tuning prompts, and why holdout results are the only reportable headline.

### 2.2 Target schema

The nested `CanonicalPacket` subset that tier-0 extracts and gates consume:
`destination_candidates, destination_status, origin_city, date_window (+confidence/flexibility), party_size (+party_composition), budget_min/max/currency/scope/flexibility, trip_purpose, ...` — exactly the field map the eval harness already normalizes (`snapshot.py:52-89` `_BUDGET_FIELD_MAP`, `_COLLOQUIAL_FIELD_MAP`) and the gates depend on (`src/intake/validation.py:50-66`). Using the *same* comparison helpers (`normalise`, empty→None collapse, `snapshot.py:68-77`) guarantees apples-to-apples with tier-0 numbers.

### 2.3 What is explicitly NOT scored

Full-packet richness (hypotheses/contradictions/etc.) — SLMs are asked only for the field set tier-0 targets; everything else remains the deterministic pipeline's job (PER-0700: the SLM is a tier, not a pipeline replacement).

---

## 3. Setup

### 3.1 Models (all 1B-class, q4f16 GGUF/MLX as available)

| Family | Variants | Rationale |
|---|---|---|
| Qwen 2.5 | 1.5B-Instruct, 3B-Instruct | Best-in-class small instruct; already WebLLM-served (browser research §1) |
| Llama 3.2 | 1B-Instruct, 3B-Instruct | The browser research's named candidates |
| Gemma 2 | 2B-it | Chrome/Gemini ecosystem proximity |
| Phi-3.5 | mini (3.8B) | Small but strong instruction-following; included as 3B-class ceiling probe |
| (probe) Gemini Nano | Chrome-managed | Device-tier reality check via Prompt API `responseConstraint`; not a headline candidate |

### 3.2 Constrained decoding

- **Server/native harness:** XGrammar (via WebLLM runtime or xgrammar wheel) or Outlines against the **packet field schema** (§2.2). One constrained and one unconstrained run per model — the delta *is* a reported metric (§4).
- **Browser run (phase 2):** WebLLM (`response_format` JSON-schema) for Qwen/Llama; Chrome Prompt API `responseConstraint` for Nano, including `measureContextUsage` of the schema (browser research §2, open question 6.3).
- Fixed decoding params across models (greedy or temp 0.1); seed recorded; 3 samples for the stochastic config to report variance.

### 3.3 Prompting

Two prompt conditions, both *fixed* per model:

1. **Zero-shot schema instruction** (the realistic on-device condition — no corpus-specific tuning allowed on holdout).
2. **Few-shot from dev split only** (3 examples) — reports whether few-shot closes the gap; never uses holdout content.
Prompt templates are versioned artifacts of the benchmark (part of the regression surface, C-03 §5).

---

## 4. Metrics

All computed with the eval harness's existing comparison semantics (`snapshot.py` normalise + `run_extraction_eval`).

| Metric | Definition | Why |
|---|---|---|
| **Field-level P / R / F1** | Per-field and macro, vs golden `expected_extracted_fields`, empty-capture = None (no silent misses) | Comparable to tier-0 anchors (budget 0.9524) |
| **Per-pattern slices** | F1 by fixture `tags` (verb_object, party, dates, lowercase, Hinglish…) | Locates exactly *which* colloquial families the SLM wins/loses |
| **Delta vs tier-0** | Same corpus through `ExtractionPipeline`; report `F1_slm − F1_t0` per split | The research question, quantified |
| **Valid-JSON rate** | Parses + schema-validates, constrained vs unconstrained | Isolates what the grammar buys |
| **Hallucinated-field rate** | Fields emitted with non-null values **not grounded in the input note** (spot-audited sample + deterministic substring/geography checks: value must appear in note or resolve via the 590k city set, `src/intake/geography.py`) | PER-0882's "valid JSON with wrong field values" failure made measurable |
| **Corruption rate** | Golden fields tier-0 got right that the SLM output overwrote wrongly | Net-gain math below |
| **Net field gain** | fields added-correct − fields corrupted − hallucinated | The only quality number that matters for tier admission |
| **Gate survival** | Packet from SLM output → `validate_packet` + NB01: % reaching PROCEED vs DEGRADE/ESCALATE | Ties quality to the actual product boundary |
| **Latency** | p50/p95 end-to-end; prefill vs decode tok/s | Output-short tasks are prefill-dominated (browser research §3) |
| **Device feasibility** | Model download MB, peak RAM/VRAM, WebGPU-vs-WASM mode | T0.5 admission inputs |
| **Cost** | $0 marginal; energy/wall-clock per 100 notes on reference hardware | The honest cost accounting (browser research §4a) |

---

## 5. Baselines & reference rows

1. **Tier-0 deterministic extractors** — the incumbent; every number is a delta against it. Its known failure class (silent wrong data on colloquial phrasings: "me and 3 friends" → party 1, DEMO-02/03) defines the win condition: the SLM must fix that class **without** corrupting the easy class tier-0 already nails (budget lane shows tier-0 is near-ceiling on structured-ish notes — a "beats regex" claim only counts where tier-0 fails).
2. **Tier-1 cloud small** (`checker_model` class) — upper reference: if cloud-small also fails a split, no on-device tier can be expected to pass it; that split gets fixed in data/extractors, not models.
3. **Trivial baseline** — empty packet (fields all None) F1 floor, so small-corpus F1s are interpretable.

---

## 6. Go / no-go criteria for the on-device (T0.5) experiment

Adopted directly from the browser research's admission rule, now made concrete:

| # | Criterion | Bar |
|---|---|---|
| G1 | Colloquial-split F1 ≥ tier-0 colloquial F1 **on tier-0's failing subset** | ≥85% of tier-1 cloud-small's score on that subset |
| G2 | Net field gain on holdout ≥ 0 (no split shows corruption > correction) | hard |
| G3 | Hallucinated-field rate | <2% of emitted fields |
| G4 | Constrained valid-JSON rate | ≥99% (else constraint config is wrong, model is out) |
| G5 | Device feasibility on reference hardware | model ≤ ~1.2 GB download, decode ≥ 30 tok/s, p95 note→draft ≤ 8 s |
| G6 | Fleet coverage | Desktop-Chromium+WebGPU/Prompt-API coverage of *our* traffic ≥ 85% (research §3: WebGPU 85.56% global, minus Android/iOS reality) |
| G7 | Governance | Explicit privacy-consent UI + server-verify always authoritative + disagreement telemetry live *before* opt-in ships |

**No-go / park:** any G1–G4 failure → the SLM cannot be trusted even as a draft; record results, keep tier-0 + cloud escalation (C-03 R5) as the path. Partial pass (quality yes, coverage no, G5/G6) → park until Safari/WebKit Web-AI trajectory changes (research §6.4), revisit in 12–18 months.

---

## 7. Execution mechanics (design only — not run here)

- Harness: a `tools/benchmark_slm_extraction.py`-style runner (reusable tool per repo rules) that reads the corpora, runs tier-0, runs each model via vLLM/llama.cpp/XGrammar or Outlines, emits per-fixture JSONL + summary tables versioned under `data/evals/slm_benchmark/<date>/`.
- Runs are CI-independent (GPU/local, not in `run_backend_tests.sh`); only the **summary tables** enter the D6-adjacent record so the benchmark result is as gateable as the rest of the eval lanes (C-03 §5).
- Reproducibility: model revisions, quantization, grammar build, prompt template versions, hardware IDs, and seed all recorded in the run manifest.

## 8. Contribution framing (the published-benchmark gap)

Deliverable on completion: a reproducible **"ColloquialNotes2Packet"** benchmark — colloquial + adversarial travel-note corpora with field-level goldens, a constrained-decoding harness, deterministic-extractor baselines, and per-pattern slices. No published eval targets messy-note→travel-packet extraction with a deterministic baseline incumbent; publishing the protocol + (sanitized) corpus would position Waypoint as the reference point for exactly the class of small-model intake tasks the browser tier needs.

## 9. Open questions

1. **N-02 dependency:** author `raw_input` for the 50 general fixtures, or exclude split C from v1? (Recommend: author — 50 runnable fixtures is the biggest corpus-quality lever.)
2. Adversarial corpus authorship ownership + hidden-holdout governance (synthesis §6.3: who may add holdout fixtures?).
3. Do SLM *fine-tunes* (LoRA on dev split) belong in v1, or zero/few-shot only? (Recommend: v1 zero/few-shot only; a fine-tuned 1.5B is a strong v2 candidate once the harness exists.)
4. Is Gemini Nano in scope for v1 given Chrome-managed model drift (governance risk, research §2), or probe-only?
5. Reference hardware for G5: pick two anchors (M-series MacBook Chrome; one Windows/Chromebook-Plus class device) before running.
