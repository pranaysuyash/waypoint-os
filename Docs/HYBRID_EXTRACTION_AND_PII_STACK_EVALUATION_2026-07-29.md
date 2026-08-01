# Architectural Evaluation: 4-Layer Hybrid Extraction, Local PII Models & Progressive Pre-Caching

**Date**: 2026-07-29  
**Governing Standard**: `motto_v4.md` (Section 0.15 Third-Layer Rule, Section 0.12 Decision Records)  
**Status**: Canonical Architectural Strategy  

---

## 1. Executive Summary & Core Insight

Relying exclusively on heavy cloud LLMs or multi-gigabyte client models creates an inefficient trade-off between latency, cost, and offline resilience. 

Waypoint OS adopts a **4-Layer Cascading Extraction & PII Stack** coupled with **Progressive Background Model Pre-Caching** and a **Draft-First Offline Sync Architecture**.

---

## 2. The 4-Layer Cascading Extraction Stack

```text
[Raw Inbound Text / WhatsApp / Gmail]
  │
  ├── LAYER 1: Regex & Heuristic Scrubber (0ms, 0MB)
  │   - Instant pattern matching for emails, phone numbers, passport formats, ISO dates, budget currency.
  │
  ├── LAYER 2: Lightweight NLP & Local PII Models (5–50ms, 15–40MB)
  │   - SpaCy / NLTK / MaziyarPanahi HuggingFace ONNX PII NER models running via Transformers.js in WebWorker.
  │   - Extracts named entities (people, cities, hotel names) and redacts sensitive PII locally before network transit.
  │
  ├── LAYER 3: Ultra-Lightweight Mobile SLMs (100–300ms, 150–500MB)
  │   - Gemma 2B/4B (4-bit quantized), Qwen-0.5B/1.5B, or Phi-3-mini.
  │   - Used for quick local draft intent parsing, follow-up prompt suggestions, and offline intake assistance.
  │
  └── LAYER 4: Cloud Core Engine (FastAPI `spine_api`)
      - Gemini 1.5 Pro / GPT-4o reserved strictly for multi-variable constraint math, budget decomposition, yield arbitrage, and contract generation.
```

---

## 3. Progressive Background Pre-Caching & Offline Sync Strategy

```text
[USER IS ONLINE]
  │
  ├── 1. Service Worker detects active network connection (Wi-Fi / TLS).
  ├── 2. Silently pre-fetches small ONNX PII models (MaziyarPanahi ONNX ~35MB) and Gemma 2B 4-bit (~500MB).
  └── 3. Caches weights in browser `IndexedDB` / CacheStorage.

[USER GOES OFFLINE / BACKEND DOWN]
  │
  ├── 1. User captures WhatsApp text in Chrome Extension.
  ├── 2. Layer 2 ONNX / Layer 3 Gemma local model parses intent instantly from IndexedDB cache.
  ├── 3. Saves draft packet locally in Zustand / IndexedDB (`status: "draft_pending_sync"`).
  │
[USER RECONNECTS ONLINE]
  │
  └── 4. Client auto-syncs local draft packet to `POST /api/v1/inbound/parse` in `spine_api`
         for deterministic constraint check, rate table matching, and immutable audit logging.
```

---

## 4. Specialized PII & Extractor Model Evaluation Matrix

| Tool / Model | Architecture | Primary Role | Size / Latency | Integration Surface |
| :--- | :--- | :--- | :--- | :--- |
| **Regex & Pattern Rules** (`src/security/privacy_guard.py`) | Rule Engine | Passports, credit cards, emails, phone numbers, currency symbols | <1 MB / **0ms** | Extension + Backend |
| **MaziyarPanahi / PII NER ONNX** (HuggingFace) | DeBERTa / BERT ONNX via `@transformers.js` | Local client-side PII token scrubbing (names, SSN, addresses) | ~35 MB / **15ms** | Chrome Extension WebWorker |
| **Microsoft Presidio / SpaCy NER** | SpaCy `en_core_web_sm` / Presidio engine | Named entity recognition (cities, airports, traveler names) | ~15 MB / **10ms** | Backend (`spine_api`) + Extension |
| **Gemma 2B / 4B Mobile (4-bit)** | Quantized SLM via WebGPU / WASM | Offline intent draft generator & fast structured JSON extractor | ~500 MB / **200ms** | IndexedDB background cache |
| **MedGemma-style Vision Transformer** | LayoutLMv3 / Donut ONNX | Passport, visa, and hotel voucher PDF/image parsing | ~120 MB / **300ms** | Document Ingestion Pipeline |

---

## 5. Architectural Alignment with `motto_v4.md`

1. **Zero Shadow Pipeline Risk**: Local models act exclusively as **Pre-Scrubbers (Layer 2)** and **Offline Draft Buffers (Layer 3)**. Final constraint verification and state integrity remain strictly governed by the canonical `spine_api` pipeline.
2. **Zero Key Hazard**: All local models run on-device via WebAssembly/WebGPU with zero cloud API keys exposed.
3. **Maximum Performance & Privacy**: Users experience instant 15ms local extraction and complete data privacy, while the backend maintains 100% deterministic safety gates.
