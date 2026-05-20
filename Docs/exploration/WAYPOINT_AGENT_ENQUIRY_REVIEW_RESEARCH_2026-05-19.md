# Waypoint Agent Enquiry Review Research

**Date:** 2026-05-19  
**Status:** Exploration / design backlog  
**Principle:** Prepared by Waypoint, accepted by the operator.

## Why This Exists

The enquiry review surface should not be framed as an "AI feature" in product language. Boutique agencies sell judgment, taste, relationships, and trust. If the product foregrounds AI, operators may feel undermined and clients may devalue the agency's expertise.

The better product promise is:

> Waypoint prepares the first draft so the team can review faster.

Waypoint can still carry the heavy operational burden behind the scenes, but the visible workflow should keep the operator as the expert and final approver.

## Existing Evidence To Reconcile

- `Docs/CHANDI_PERSONA_REVIEW_2026-04-30.md` frames the system as an augmentation tool for the agent, not a replacement.
- `Docs/SIMULATED_USER_INTERVIEW_OTA_SWITCHER_2026-04-28.md` says the automation should be invisible to clients and preserve the agent's voice.
- `Docs/CALL_NOTES_AYSE_2026-04-30.md` warns that "I build AI tools" is not positioning; the market-facing wedge is business outcome and speed.
- `Docs/research/RESEARCH_OPPORTUNITY_MASTER_LIST_2026-04-25.md` already has broad AI/LLM research items, but lacks this specific assisted-enquiry-review product and infrastructure slice.

## User-Facing Language

Use:

- Waypoint Agent
- Assistant
- Suggested summary
- Suggested reply
- Missing details
- Prepared draft
- Review before saving
- Drafted for review

Avoid:

- AI-generated
- LLM
- Autonomous agent
- AI replaces manual work
- AI knows best
- Auto-send
- Auto-decide

## First Product Slice

Operator opens an enquiry and clicks a support action:

1. Waypoint checks whether a prepared suggestion already exists.
2. If not, Waypoint prepares a structured draft behind the server boundary.
3. UI shows suggested summary, missing details, and suggested reply as editable advisory content.
4. Operator accepts, edits, or ignores the draft.
5. No canonical trip field changes until the operator explicitly saves.
6. No traveler-facing message is sent automatically.

## Research Questions

1. Where should the first surface live: Lead Inbox row, enquiry detail panel, or Workbench intake panel?
2. Which exact enquiry fields should be sent to the provider, and which should be redacted or blocked?
3. What structured response schema should Waypoint return: summary, missing details, suggested reply, confidence notes, and provenance?
4. What persistence model should store prepared suggestions?
5. What cache key should be canonical: normalized raw text, owner note hash, prompt version, model/provider, locale, agency config?
6. What invalidates a prepared suggestion: raw note edit, owner note edit, prompt version change, model change, trip fact edit, or manual regenerate?
7. Should stale suggestions be visible with a clear regenerate action?
8. Which actions are operator-triggered versus system-prepared?
9. How should system-prepared drafts be attributed in history and audit logs?
10. What per-agency usage limits and budget controls are required?
11. What should happen when the provider key is absent or unavailable?
12. How should the privacy guard prevent passport, payment, secret, or unnecessary PII transmission?
13. Which old enquiries should be processed in batch or overnight backfills?
14. Which provider caching or batch APIs reduce cost without becoming the product source of truth?
15. How should operators correct bad suggestions so Waypoint improves without silently changing future behavior?

## Technical Direction

App-level cache is canonical. Provider caching and provider batch APIs are optional cost optimizations, not product state.

Suggested persistence shape:

- `id`
- `agency_id`
- `trip_id` or `lead_id`
- `input_hash`
- `prompt_version`
- `model`
- `provider`
- `status`
- `summary`
- `missing_details`
- `suggested_reply`
- `confidence_notes`
- `created_at`
- `expires_at`
- `invalidated_at`
- `generated_by`: `system` or `operator`
- `generated_by_user_id`, nullable

Background preparation should be server-side job work, not browser idle work first. Conditions:

- agency has Waypoint Agent assistance enabled
- privacy guard passes
- no valid cached suggestion exists
- raw note has changed since last suggestion
- per-agency budget and rate limits allow it
- queue has capacity

Batch/backlog processing is appropriate for old unreviewed enquiries and migration/backfill work. It is not the right path for an operator waiting after clicking "Prepare draft."

## What Not To Build Yet

- No auto-send to traveler.
- No hidden dashboard ranking created solely by model output.
- No autonomous canonical trip updates.
- No provider-cache-only state.
- No direct browser-to-provider calls.
- No sending passport/payment/secrets.
- No new duplicate API route family if an existing enquiry/workbench route can be extended.
- No user-facing "AI generated" positioning unless a legal/compliance requirement explicitly forces disclosure in that context.

## Acceptance Checks For A Future Design/Build Task

- Product copy follows the Waypoint Agent language guide above.
- Operator remains the final approver before any canonical data or customer reply changes.
- Provider calls are behind the server boundary.
- Suggestions are cached with explicit versioning and invalidation rules.
- System-generated and operator-triggered suggestions are separately attributed.
- Provider unavailable/no-key fallback is graceful and visible.
- Privacy guard blocks or redacts sensitive data before provider calls.
- Tests cover cache hit, cache miss, invalidation, no-key fallback, privacy-blocked fallback, and operator accept/edit/save.
