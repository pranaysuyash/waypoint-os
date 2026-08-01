# ADR: Progressive Background Model Pre-Caching & Offline Sync

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Progressive Offline Resilience & Local SLM Pre-Caching

---

## Context

Relying exclusively on cloud endpoints creates latency jitter and prevents offline travel intake when planners travel or experience network degradation. Conversely, downloading heavy multi-gigabyte models on demand creates unbearable cold-start delays.

---

## Decision

Implemented progressive background model pre-caching and draft-first offline state management:

1. **ServiceWorker Pre-Caching (`sw-model-cache.js`)**:
   - Detects active network connection and silently pre-fetches local ONNX model assets (35MB DeBERTa ONNX PII model, 15MB SpaCy NER model) into CacheStorage/IndexedDB.
2. **Draft-First Offline Sync (`draft_pending_sync`)**:
   - Updates Zustand/IndexedDB client store (`frontend/src/stores/workbench.ts`) to mark local drafts with `draft_pending_sync` during network interruptions.
   - Automatically reconciles draft packets with `spine_api` when server connection recovers.

---

## Consequences

- 100% client-side privacy scrubbing and offline intake capability.
- Instant model execution from IndexedDB cache with zero cold-start delay on repeat usage.
