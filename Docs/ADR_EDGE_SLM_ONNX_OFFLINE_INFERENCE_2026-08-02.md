# ADR 15: Edge SLM ONNX Progressive Downloading and Offline Client Inference Engine

**Date**: 2026-08-02  
**Status**: APPROVED  
**Deciders**: Lead Architect, AI Systems Team  
**Governing Rule**: `motto_v4.md` (Rule 0.15: Third-Layer Decoupling & Local Fallback Mandate)

---

## 1. Context & Business Need

Travel agency operations must maintain zero-downtime execution even when internet connectivity degrades (e.g. airport Wi-Fi, remote resort locations, cellular drops). Relying solely on cloud LLM API calls leaves planners vulnerable to outages and latency spikes.

## 2. Technical Architecture & Decision

We implement a progressive background downloading ServiceWorker (`frontend/public/sw-slm-downloader.js`) paired with an offline client inference manager (`frontend/src/lib/offline-slm-engine.ts`):

1. **Progressive Network-Aware Download**:
   - The ServiceWorker monitors `navigator.connection` and downloads Gemma 2B 4-bit ONNX model weights in 4MB chunks only on unmetered connections.
   - Model chunks are validated via SHA-256 integrity hashes and stored in IndexedDB (`ModelCacheDB`).

2. **Client-Side Fallback Execution**:
   - When offline or API requests time out (>3000ms), `offline-slm-engine.ts` activates Web Worker ONNX Runtime (`onnxruntime-web`) execution.
   - Provides local PII scrubbing, basic entity extraction, and offline inquiry draft capture without sending data over the network.

## 3. Verification & Compliance

- **ServiceWorker Storage**: Checked via Chrome DevTools Application -> IndexedDB.
- **Offline Fallback Test**: Verified by simulating offline state (`navigator.onLine = false`) in browser end-to-end tests.
