# Discussion: Retention Consent — Agency vs Traveler Boundary

**Date:** 2026-05-04
**Context:** Random document audit of `Docs/ARCHITECTURE_DECISION_SPINE_API_2026-04-15.md`
**Participants:** User (Pranay), Agent

## What Was Found

The `SpineRunRequest` Pydantic model has `retention_consent: bool = False` (default no-consent).
The backend has a filtering path: when `retention_consent=False`, raw text fields (`raw_note`, `owner_note`, `itinerary_text`, `structured_json`) are stripped from the persisted `meta.submission`.

**Problem discovered during audit:** The frontend agency IntakePanel (`IntakePanel.tsx`) and workbench (`workbench/page.tsx`) never send `retention_consent` in their `SpineRunRequest` payload. Only the public itinerary checker page sends it.

This means every agency-submitted trip has `retention_consent=False` on the backend, and the raw submission text is stripped from metadata.

## Initial Proposal

Add a consent checkbox to the agency IntakePanel UI, mirroring the public checker's pattern.

## User Pushback

Pranay asked: "Since the call came from the customer and not the agency, do they still need a consent box? Because it's not the customer entering data but the agency itself."

This reframed the entire approach.

## Analysis

### Data Flow
- **Agency flow (IntakePanel/workbench):** Travel agency employee enters customer data into our system. The traveler is not present.
- **Public checker flow (itinerary-checker):** The traveler directly enters their own trip details.

### Legal/Architectural Boundaries

| Layer | Actor | Role |
|-------|-------|------|
| Traveler ↔ Agency | Traveler | Data subject |
| Agency ↔ Our Product | Agency employee | Data controller |
| Our Product → Database | Our system | Data processor |

The consent boundary is between **traveler and agency**, not between **agency and our product**. The agency is the data controller — they have their own legal basis (contract performance, legitimate interest) for processing traveler data. Our product acts as a processor for the agency.

Adding a consent checkbox in the agency UI would be:
1. **Unnecessary friction** — the agency already has consent from their traveler
2. **Confusing** — the agent didn't consent, the traveler did; asking the agent to toggle consent is misplaced
3. **Wrong architectural layer** — consent lives between traveler and agency, not between agency and our processor

### Public Checker Distinction

The public itinerary checker is different because there is **no agency intermediary**. The traveler directly enters data into our system. Here:
- Our product acts as the direct controller (for this specific flow)
- A consent checkbox is correct and necessary
- GDPR/CCPA right-to-deletion and data-portability endpoints (`/api/public-checker/{trip_id}` and `DELETE`) are correctly implemented

## Reframing: retention_consent Was Never About Consent To Us

Pranay observed: agencies consent to us storing/using their data via **ToS / Privacy Policy at signup** — the same way Google, Salesforce, or any B2B SaaS works. None of them ask per-submission.

This reframes the entire `retention_consent` flag:

| What it was mistaken for | What it actually is |
|--------------------------|---------------------|
| "Should we ask the agency for permission to store this submission?" | "Should the raw input text be preserved in the trip metadata?"
| A consent/legal mechanism | An audit-trail toggle |
| Per-submission opt-in | Always yes for agencies (they entered the data, they own it) |

The consent to **us** (the product) to store and process data is provided at agency signup via ToS and Privacy Policy. The `retention_consent` flag only controls whether the **raw submission text** is kept in the trip record for the agency's own reference — not whether we can store it.

### Why The Public Checker Is Different

The public checker has no agency intermediary — the traveler directly enters data into a system they have no ToS agreement with. Here, per-submission consent is the correct pattern. That's why the consent checkbox lives there and works correctly.

### What This Means For The Code

- `retention_consent=true` for agency flows: preserves raw text so the agency can review what they submitted
- `retention_consent=false` for agency flows: strips raw text from metadata — the agency loses their own audit trail. There's no reason to default to this
- The public checker's consent checkbox is a completely different feature serving a different boundary

The flag name `retention_consent` is misleading (sounds like a legal consent gate when it's really a storage-toggle for raw text), but renaming it is out of scope for this fix.

## Follow-Up: Our Own Analytics / Admin Panel

Pranay raised a second-order concern: what if we (the product builder) build admin analytics — we shouldn't look at names/PII, but non-PII data (destinations, booking trends, budgets) is valuable for product decisions.

This reveals a **conflation in the current design**: `retention_consent` controls whether the raw submission text is stored in `meta.submission`, but the extracted trip data (packet, validation, decision) is always stored regardless. So even with `retention_consent=false`, the TripStore contains structured analytics data (destinations, dates, budgets).

### Tiered Data Model (Implicit)

| Data Tier | Examples | Stored When | Who Uses It |
|-----------|----------|------------|-------------|
| Raw input text | `raw_note`, `owner_note`, `itinerary_text` | Only if `retention_consent=true` | Agency (review past submissions) |
| Structured trip data | packet, validation, decision, strategy | Always | Agency workflow + our analytics |
| File artifacts | uploaded files, base64 content | Only if `retention_consent=true` | Agency reference |

### Open Questions for Future

1. **Our analytics access policy** — Should we build admin dashboards that aggregate trip data? The structured data already exists in the TripStore regardless of `retention_consent`. If we build analytics, the policy question is: do we inform agencies that aggregated non-PII data gets used for product analytics, or is this implicit in the processor-controller relationship?

2. **Separation of concerns** — If needed later, `retention_consent` could be split into two flags:
   - `store_raw_submission` — preserve the agency's raw input for their reference
   - `allow_analytics_use` — opt in to our product analytics
   Currently both are bundled under one flag. Not needed now, but worth keeping in mind.

3. **Admin panel PII boundary** — If we build admin analytics, we must build a PII filter on the admin query layer (aggregated data only, no raw text surfacing in admin UIs). The current `_to_dict` recursive serializer (server.py:679) walks everything by default.

## Decision (2026-05-04)

**`retention_consent` for agency flows should always be `true`.** This is not a consent gate — it's a "store the raw input for the agency's own audit trail" toggle. The agency's consent to us is governed by ToS/Privacy Policy at signup. Per-submission consent checkboxes belong only in the public checker (direct-to-traveler) flow.

**Fix applied:**
- `IntakePanel.tsx` — now sends `retention_consent: true`
- `workbench/page.tsx` — now sends `retention_consent: true`
- Existing code comments updated to reflect the corrected rationale

**Deferred:**
- Analytics/admin-panel question — structured trip data is already in TripStore regardless of `retention_consent`. If an admin panel is built, design a separate data-access policy and admin PII boundary.
- Renaming `retention_consent` — the name is misleading but too widely referenced to change in this fix.

## Files Changed

- `frontend/src/components/workspace/panels/IntakePanel.tsx` — add `retention_consent: true`
- `frontend/src/app/(agency)/workbench/page.tsx` — add `retention_consent: true`
- `frontend/src/app/__tests__/mode_selector_spine_payload.test.tsx` — add test for `retention_consent: true`
- `Docs/discussions/retention_consent_agency_vs_traveler_2026-05-04.md` — this document

## Related

- `Docs/ARCHITECTURE_DECISION_SPINE_API_2026-04-15.md` — the ADR that defines the spine API contract
- `DOC-2026-05-04-retention-consent-audit-fix.md` — the implementation plan
