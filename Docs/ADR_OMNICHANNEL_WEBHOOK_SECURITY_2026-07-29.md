# ADR: Omnichannel Webhook Security & Verification

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Messaging Integration Hardening (Priority #4)

---

## Context

Inbound webhooks from messaging providers (WhatsApp Business Cloud API, SendGrid) carry message status callbacks (`SENT`, `DELIVERED`, `READ`, `FAILED`) and incoming traveler replies. Unverified webhook endpoints risk spoofing attacks and fake status injections.

---

## Decision

Implemented production webhook security & verification in `spine_api/routers/messaging.py`:

1. **Meta GET Challenge Handshake (`GET /api/v1/messaging/webhook/{provider}`)**:
   - Implements Meta Developer Protocol hub mode & verify token handshake (`hub.mode=subscribe`, `hub.verify_token`, `hub.challenge`).
   - Returns challenge integer on successful token match.
2. **HMAC SHA-256 Signature Verification (`POST /api/v1/messaging/webhook/{provider}`)**:
   - Validates `X-Hub-Signature-256` header against `WHATSAPP_APP_SECRET` using constant-time `hmac.compare_digest()`.
   - Rejects unverified payloads with HTTP 401.
3. **Audit Ledger & Delivery Tracking**:
   - Records outbound message dispatch and webhook status callbacks in `AuditStore`.

---

## Consequences

- Prevents unauthorized third parties from spoofing delivery events or injecting false incoming messages.
- Full compliance with Meta WhatsApp Cloud API production requirements.
