# ADR: Chrome Extension Auth, Offline Queue, and Client-Side PII Pre-Scrubber

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Chrome Companion Ingestion Production Hardening

---

## Context

The Chrome Extension (`tools/extensions/chrome-inbound-companion`) allows travel agents to capture unstructured client inquiries from WhatsApp Web, Gmail, or web selections directly into Waypoint OS.

Prior to hardening, the extension had three major production limitations:
1. Hardcoded target `http://localhost:8000` with no auth headers or configurable host in `manifest.json`.
2. Failed silently when offline or when backend was unreachable.
3. Transmitted raw client text without any client-side privacy checks or PII scrubbing.

---

## Decision

Implemented a production-grade 3-commit upgrade package for the companion extension:

### 1. Configurable Backend & Bearer Token Authentication
- Added `settings.html` and `settings.js` options page.
- Allowed user to configure custom backend URL (`http://localhost:8000` default) and JWT token.
- Token stored securely in `chrome.storage.sync` and injected into `Authorization: Bearer <token>` HTTP header.
- Handled `401`/`403` gracefully with clear user guidance linking to settings.
- Expanded `host_permissions` in `manifest.json` to include `https://*/*` and `alarms`.

### 2. IndexedDB Offline Queue & Background Sync
- Implemented `DB_NAME = 'waypoint_offline_queue'` using IndexedDB in `popup.js` and `background.js`.
- If an API request fails due to network outage or server unreachability, the inquiry payload is queued in IndexedDB.
- `background.js` sets a 2-minute `chrome.alarms` scheduler and an `onStartup` listener to drain the queue automatically when connection is restored.
- Evicts queued entries after 5 retries to prevent unbounded growth.
- Added visual offline queue badge displaying pending items count in `popup.html`.

### 3. Client-Side PII Pre-Scrubber (WebWorker)
- Created `pii-worker.js` running in an isolated Web Worker.
- Uses regex heuristics for Indian travel inquiry PII:
  - **Red Severity (Hard Block)**: Aadhaar numbers (12-digit), PAN cards, Indian passports, credit cards, mobile numbers (+91), emails.
  - **Amber Severity (Warning)**: Partial numbers, dates of birth.
- Returns redacted preview strings (`****1234`) to `popup.js`.
- Renders an inline amber/red alert banner in `popup.html`. Red severity disables the send button unless the user explicitly clicks "Send anyway".

---

## Alternatives & Model Evaluation

We evaluated client-side ML models vs. regex WebWorker vs. server-side NLP:
- **Transformers.js / ONNX Gemma 2B**: Deferred due to heavy asset downloads (>50MB-4GB) breaking chrome extension performance and startup limits.
- **Client-Side Regex WebWorker**: Selected as the optimal client-side layer (instant execution, zero network, 0MB bundle impact).
- **Server-Side SpaCy NER**: Complements the client-side pre-scrubber as Layer 2 in the Python backend.

---

## References

- `tools/extensions/chrome-inbound-companion/`
- `Docs/ADR_PII_GUARD_SPACY_LAYER2_2026-07-29.md`
