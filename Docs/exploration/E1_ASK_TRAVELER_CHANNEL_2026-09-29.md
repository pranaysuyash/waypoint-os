# E1 — Ask-Traveler Channel Architecture (FND-0301 companion research)

**Date:** 2026-09-29 · **Status:** RESEARCHED-STRUCTURE / RATES-UNVERIFIED (web-search quota exhausted until 2026-10-06)
**Related:** `Docs/review/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md` T1; `spine_api/services/message_dispatch.py` (shipped); `/a/{token}` answer page (shipped)

## What already exists (shipped this session)

The ask loop is **channel-agnostic by design**: `POST /followups/{trip_id}/send` composes
questions + a token-gated `/a/{token}` answer link, then dispatches through
`message_dispatch.py` (WhatsApp Cloud API / SendGrid adapters, honest
`NOT_CONFIGURED` without creds). The **link itself is already a delivery channel** —
an operator can paste it into any conversation they already have open. This
matters: WhatsApp template approvals are the long pole; the link works day one
without them.

## Channel options

| Option | Reach | Cost | Consent/approval burden | Answer capture |
|---|---|---|---|---|
| **A. Link-only (shipped)** | Any channel the advisor already uses | ₹0 | None | Native (`/a/{token}` → `traveler_answers`) |
| **B. WhatsApp Cloud API direct** | Highest in India | Per-message template fees; service replies (user-initiated, 24h window) free-tier | Business verification + template approval per category | Link click-through → native capture |
| **C. Email (SendGrid)** | Good for formal/proposal-stage | ~$0.001–0.02/msg (unverified) | Domain auth (SPF/DKIM) only | Link click-through → native capture |
| **D. In-thread WhatsApp bot** (webhook auto-reply) | Highest UX | Free service conversations | Webhook verify (already built: Meta HMAC in `messaging.py`) | Would need answer parsing — E2 (Jev) |

## Pricing structure (UNVERIFIED — confirm on Meta's pricing page after 2026-10-06)

Per the general model (India moved to per-message template pricing, ~2025):
Marketing ≈ ₹0.78–0.88/msg; Utility within 24h window ≈ ₹0.115; service
conversations (traveler replies first) free-tier. **Do not build send-volume
commitments on these numbers until verified against
[Meta's WhatsApp Business pricing](https://business.facebook.com/wa/manage/pricing/).**

## Recommendation (pending owner DECIDE)

1. **Now:** Option A is live — operators send asks today with zero approvals.
2. **Next (recommended):** Option B as the primary channel for an India-first
   agency (WhatsApp is the de-facto channel for Indian travel planning),
   Option C for proposal-stage formality. The dispatch adapter already
   exists; the remaining work is Meta business verification + 2–3 approved
   templates (ask-questions, proposal-ready, re-engagement).
3. **Later:** Option D (in-thread bot answers, no link click) once E2 proves
   Jev answer-parsing quality — it converts the ask loop from "click a link"
   to "just reply", at the cost of parser-driven write-back risk.

**Falsifier:** if Meta business verification + template approval exceeds ~2
weeks of elapsed time for the pilot agency, link-only remains the primary
channel and B demotes to parallel work.

## Verification TODO (after 2026-10-06 quota reset)

- [ ] Confirm per-message rates on Meta pricing page (record actuals here)
- [ ] BSP vs direct Cloud API decision (direct is code-complete; BSPs like Gupshup/Wati add markup but handle verification)
- [ ] SendGrid India deliverability check (transactional vs marketing route)
