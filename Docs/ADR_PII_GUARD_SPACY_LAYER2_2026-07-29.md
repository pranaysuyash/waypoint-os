# ADR: SpaCy Layer 2 NLP Guard for Server-Side PII Detection

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Server-side PII guardrails in dogfood/beta mode

---

## Context

`src/security/privacy_guard.py` enforces data privacy guardrails to prevent unencrypted plaintext persistence of real user PII in `DATA_PRIVACY_MODE=dogfood`.

Layer 1 relies on regex heuristics (emails, phone numbers, Aadhaar patterns, medical keywords). However, regex cannot reliably detect named entities in natural prose (e.g., `"My name is Priya Sharma"` or `"Contact Rahul at the office"`).

---

## Decision

Integrated SpaCy `en_core_web_sm` as **Layer 2 NLP Guard** in `privacy_guard.py`:

1. **Lazy Loading & Fail-Open**: SpaCy model is loaded lazily on demand. If `spacy` or `en_core_web_sm` is missing, it logs a single warning and gracefully falls back to Layer 1 regex (fail-open architecture).
2. **PERSON Entity Target**: Specifically scans freeform fields for `PERSON` entity labels. `ORG` and `GPE` (locations) are intentionally ignored because travel inquiries naturally contain hotel names and destinations.
3. **Environment Flag**: Controlled by `NLP_PII_GUARD_ENABLED=1|0` (default enabled, set to 0 in light test environments).
4. **Installer Script**: Added `scripts/setup_nlp_models.sh` for one-shot environment bootstrapping (`uv add --group privacy spacy` + `spacy download en_core_web_sm`).

---

## Model Evaluation Matrix

We evaluated multiple local NLP/NER models for PII detection:

| Model / Library | Model Size | Target Layer | Evaluation Result | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **SpaCy `en_core_web_sm`** | ~12 MB | Server Layer 2 | **Selected (Active)** | Ultra-lightweight, CPU fast (~5ms), accurate `PERSON` NER, zero GPU requirement. |
| **Presidio Analyzer** | ~150 MB | Server Layer 2+ | Deferred | Built on top of SpaCy/Transformers; higher overhead without immediate gain over pure SpaCy for names. |
| **Maziyar/mdeberta-v3-base-pii** | ~800 MB | Server Layer 3 | Evaluated / Deferred | High accuracy for multi-domain PII, but 800MB download and torch dependency adds cold-start latency to server. |
| **Gemma2-2B-IT / Local LLM** | ~4.5 GB | Server/Client | Deferred | Too heavy for inline synchronous persistence guard. |
| **Client-Side Worker Regex** | <1 KB | Extension Layer 1 | **Selected (Active)** | Runs inside extension WebWorker for instant pre-submit scanning without network latency. |

---

## Consequences

- High precision name detection in dogfood mode without blocking synthetic test fixtures (`KNOWN_FIXTURE_IDS`).
- Purely optional dependency (`spacy` under `[privacy]` dependency group in `pyproject.toml`).
- Robust test coverage in `tests/test_privacy_guard_nlp.py` verifying fail-open behavior.
