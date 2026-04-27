# Audit Mode Research & Exploration — 2026-04-28

## Purpose

Capture the research and exploration areas surfaced by the audit of `/itinerary-checker`, `Audit Mode`, and the public/internal product boundary.

This document is a working index of what still needs to be explored before the audit wedge can be treated as a real feature.

---

## 1. Audit Mode as a GTM wedge

### Research questions
- Can Audit Mode legitimately be the first acquisition wedge for this product?
- What is the minimum viable value proposition for the traveler-facing audit surface?
- How should the audit wedge be positioned to agencies vs travelers?

### Evidence
- `Docs/UX_AUDIT_MODE_DEEP_DIVE.md`
- `Docs/GTM_AND_DATA_NETWORK_EFFECTS.md`
- `Docs/PUBLIC_LANDING_SURFACES_IMPLEMENTATION_2026-04-23.md`

### Notes
- Audit Mode is explicitly described as the only direct-to-consumer path in a B2B2C product.
- It is also described as a lead-gen tool disguised as a value-add service.
- The audit wedge needs a clear conversion funnel and lead capture model before being considered production-ready.

---

## 2. Itinerary checker scope: real feature vs marketing placeholder

### Research questions
- Should `/itinerary-checker` be a true end-user functional audit tool or remain a public marketing experiment until the core product is stable?
- What is the smallest useful functional scope for the page?
- What are the user expectations for upload/analyze in this wedge?

### Evidence
- `Docs/PUBLIC_LANDING_SURFACES_IMPLEMENTATION_2026-04-23.md`
- `Docs/FRONTEND_COMPREHENSIVE_AUDIT_2026-04-16.md`
- `frontend/src/app/itinerary-checker/page.tsx`
- `frontend/src/components/marketing/MarketingVisuals.tsx`

### Notes
- The page currently simulates notebook behavior in the UI without a real backend analysis hook.
- The product should treat the audit page as a minimal functional experiment until the agent workbench is working.
- If launched prematurely, the wedge risks overpromising and underdelivering.

---

## 3. Backend integration and API contract

### Research questions
- Does a proper backend analysis API exist for the audit wedge?
- If not, what is the smallest API contract needed to support upload/analyze behavior?
- How should the public audit funnel connect to the existing spine/decision pipeline?

### Evidence
- `frontend/src/app/itinerary-checker/page.tsx` (UI-only upload flow)
- `frontend/src/components/marketing/MarketingVisuals.tsx` (simulated notebook run)
- `Docs/UX_AUDIT_MODE_DEEP_DIVE.md`
- `Docs/FRONTEND_COMPREHENSIVE_AUDIT_2026-04-16.md`

### Notes
- The audit wedge appears to lack a real route or backend integration in the current implementation.
- Research should confirm whether the API exists elsewhere, or whether a new `POST /api/v1/analyze` style endpoint is required.

---

## 4. Product flow prioritization and stability

### Research questions
- Given the core agent workbench is not stable, what should be the priority of the audit wedge?
- What are the criteria for moving the wedge from "secondary experiment" to "true product feature"?
- How should the wedge be framed relative to the main agent delivery path?

### Evidence
- `Docs/FRONTEND_COMPREHENSIVE_AUDIT_2026-04-16.md`
- `Docs/UX_AND_USER_EXPERIENCE.md`
- `Docs/PRODUCT_VISION_AND_MODEL.md`

### Notes
- The audit wedge should be positioned as a secondary GTM experiment until the main flow is functional.
- The core B2B workbench remains the primary product; the wedge only works if the underlying product can support leads.

---

## 5. Public lead capture and conversion design

### Research questions
- What information should the audit page collect to convert visitors into agency leads?
- What is the right balance between enough detail and low friction?
- What follow-up path should audit results trigger (agency CRM, direct contact, demo request)?

### Evidence
- `Docs/PUBLIC_LANDING_SURFACES_IMPLEMENTATION_2026-04-23.md`
- `Docs/UX_AUDIT_MODE_DEEP_DIVE.md`
- `Docs/GTM_AND_DATA_NETWORK_EFFECTS.md`

### Notes
- The page currently includes marketing CTAs and a public footer, but the actual lead/demo flow is not wired.
- Research should define the lead capture form, follow-up channel, and what parts of the audit are gated vs free.

---

## 6. Data assumptions for audit analysis

### Research questions
- What data sources are required for a useful audit analysis?
- How should wasted spend and suitability be calculated?
- What public or inferred benchmarks are acceptable for a minimum viable audit score?

### Evidence
- `Docs/UX_AUDIT_MODE_DEEP_DIVE.md`
- `Docs/COVERAGE_MATRIX_2026-04-15.md`

### Notes
- Audit analysis depends on budget efficiency, suitability scoring, and group fit assumptions.
- The product needs research into sources for cost benchmarks, activity suitability, and document/visa gaps.

---

## 7. Messaging and positioning research

### Research questions
- How should the audit page avoid sounding like an agent replacement tool?
- What wording best communicates "audit" without alienating agents or travelers?
- How should the audit wedge be branded relative to the internal workbench?

### Evidence
- `Docs/PUBLIC_LANDING_SURFACES_IMPLEMENTATION_2026-04-23.md`
- `frontend/src/app/itinerary-checker/page.tsx`

### Notes
- The page currently states: "This is not a booking site and it is not an adversarial agent-replacement pitch." 
- Research should validate that the messaging is both trust-building for travelers and agency-safe.

---

## 8. Product boundary and route classification

### Research questions
- Should `/itinerary-checker` remain public forever, or should it be moved to a separate domain/tenant later?
- Should route naming and auth boundaries be refined for a real wedge?
- What are the long-term implications of keeping this route public alongside the protected `/overview` dashboard?

### Evidence
- `Docs/PUBLIC_LANDING_SURFACES_IMPLEMENTATION_2026-04-23.md`
- `Docs/AUTH_IDENTITY_SYSTEM_AUDIT_2026-04-24.md`

### Notes
- The audit route is already whitelisted as public.
- Research should cover long-term architecture for the wedge vs internal product boundary.

---

## Recommended next artifact

Create a short decision memo that answers:
1. Should `/itinerary-checker` be treated as a real functional wedge today, or a staged marketing-led experiment?
2. If real, what is the minimal backend contract required?
3. If staged, what exact behavior should remain in the page and what should be deferred?

Suggested file: `Docs/AUDIT_MODE_WEDGE_DECISION_MEMO_2026-04-28.md`
