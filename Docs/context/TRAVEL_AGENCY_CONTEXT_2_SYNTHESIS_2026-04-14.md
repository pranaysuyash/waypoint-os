# Travel Agency Context 2 Synthesis (2026-04-14)

Source:
- `/Users/pranay/Downloads/travel_agency_context_2.txt`
- Archived: `Archive/context_ingest/travel_agency_context_2_2026-04-14.txt`
- Supporting digest:
  - `Docs/context/TRAVEL_AGENCY_CONTEXT_2_DIGEST_2026-04-14.md`
  - `Docs/context/travel_agency_context_2_digest_2026-04-14.json`

## Executive Shifts Captured
- Product framing shifts from "chatbot on WhatsApp" to a persistent **decision workspace**.
- The **one-time link** is treated as a core product primitive (channel-agnostic entry: WhatsApp/email/DM).
- Architecture is compressed from many specialist agents into a smaller core:
  - Discovery
  - Constraint Engine
  - Option Builder
  - Synthesizer
  - Guardian
- Canonical packet remains central and is reinforced as system contract:
  - `facts`, `derived`, `hypotheses`, `unknowns`, `contradictions`, `provenance`, plus commercial fields.
- Strong emphasis on **commercial intelligence** (margin floors, preferred suppliers, effort economics), not just itinerary quality.

## High-Value Additions from Context 2
- Move from linear chat flow to shared **Trip Brief object** with side-by-side branches and explicit trade-offs.
- Confidence calibration and escalation behavior should be first-class output (avoid false certainty).
- Delta/change handling is core: repeated itinerary changes should run through a diff path, not full recompute.
- Provenance visibility is a UX feature:
  - Example pattern: "from WhatsApp 2h ago" next to extracted fields.
- Globalization pressure appears repeatedly:
  - separate universal planning logic from market packs/local rules.

## Implementation Consequences (Adopt Now)
1. Keep canonical packet as single source of truth; all execution writes through it.
2. Preserve deterministic-first Constraint Engine behavior and stop-tests.
3. Add/lock commercial policy hooks in packet + decision stage:
   - margin band
   - supplier preference
   - low-margin warning/escalation
4. Promote "link-first workspace" into UX roadmap as primary surface, with channel ingestion as adapters.
5. Keep NB01/NB02/NB03 sequencing discipline:
   - NB01 extraction integrity
   - NB02 feasibility/decision correctness
   - NB03 operational playbooks and issue handling

## Defer/Validate Before Building
- Full multi-market localization packs beyond MVP market assumptions.
- Real-time omnichannel command center.
- Broad customer companion app surface.
- Heavy channel-specific automation until packet/state model is stable.

## Proposed Backlog Mapping (P0/P1)
- P0
  - Canonical packet field extension for commercial controls.
  - Decision-policy coverage for low-margin and supplier-priority warnings.
  - Provenance surfacing contract for UI payloads.
  - Link-first UX skeleton spec (no full frontend rewrite required yet).
- P1
  - Diff/change-impact service for itinerary revisions.
  - Issue model + operational escalation payload format.
  - Market-pack abstraction for country-specific policy/rules.

## Notes
- Context 2 content contains repeated generated snippets and tactical micro-ideas; this synthesis keeps only durable architecture and product constraints.
- Use archived raw source as ground truth for forensic review.
