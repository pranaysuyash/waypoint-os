# Itinerary Checker V2

Date: 2026-05-01

## Goal

Rework the public itinerary checker so it feels fun, travel-forward, and clearly separate from the agency workspace logic.

## Principles

- Keep the agency workflow distinct from the public checker surface.
- Share only the underlying scoring / enrichment engine where needed.
- Make the public page feel like a travel scene, not a SaaS dashboard.
- Use motion, destination imagery, route ribbons, and playful cards to imply travel planning.

## What We Discussed

- The public surface should not look or read like an enterprise SaaS dashboard.
- The visual tone should feel fun and travel-forward, with interactive motion, travel imagery, paper-plane cues, destination tags, and trip-ribbon language.
- The public checker must remain logically distinct from the agency workflow.
- The shared spine-style B2B intake flow is too heavy for the public wedge because it is quote-ready and partial-intake aware.
- The better public architecture is a lighter path: OCR / text extraction, NER or slot-filling, LLM synthesis, and tool calls for live context.
- We should keep agency logic and public checker logic separate, while still allowing the public checker to hand off a cleaned-up brief to an agent.

## Current State

- The public checker page now has a travel-scene hero instead of a generic SaaS panel.
- The hero uses destination tags, route-ribbon imagery, a scenic preview card, and GSAP motion.
- The trust strip was replaced with travel-moment cards so the page feels more like a trip-planning tool.
- The copy now explicitly says `itinerary or travel plan` so pasted text, PDFs, and screenshots are all covered.
- The backend now exposes a dedicated public checker POST route rather than tunneling through the agency `/run` route.
- The public checker uses consented storage and public export/delete controls.
- A dummy Singapore family PDF was generated and repeatedly used to verify the live flow.

## What Changed

- The public checker hero now reads like a travel map instead of a generic dashboard.
- The checker now includes a scenic preview card with route ribbon, plane motion, and destination tags.
- The trust strip was replaced with travel moments cards so the page feels more human and less enterprise.
- The copy now explicitly says `itinerary or travel plan` so pasted text and uploaded files are both covered.
- The backend/public checker flow now has a dedicated public submission route and keeps the agency `/run` path separate.
- The dummy Singapore itinerary PDF was improved so it now includes origin, purpose, budget, party size, and family notes in addition to the activity schedule.

## Verification

- `frontend/src/app/__tests__/public_marketing_pages.test.tsx` passes.
- The live backend accepts `POST /api/public-checker/run`.
- The public checker can process the dummy Singapore PDF and return a live report.
- The sample PDF still trips the intake logic in the B2B spine, which is why the architecture needs a public-only path rather than the full agency spine.

## Notes

- The public checker should keep evolving toward a more playful travel experience without becoming gimmicky.
- The logic split matters: the public checker is a public front door, not a duplicate agency workflow.
- The public checker should use a narrower public pipeline, not the quote-ready B2B spine.

## Conclusion

The right architecture for the public checker is:

- OCR / direct text extraction for uploads
- NER or slot-filling for the few facts that matter
- LLM synthesis for the narrative score / upgrade suggestions
- tool calls for live context such as weather, AQI, hotel pricing, and safety signals

That is a better fit than forcing the public wedge through the full agency intake spine, which is designed for quote-ready completeness and therefore degrades on realistic public uploads.

## Next Steps

1. Replace the public checker submit path with the lighter public pipeline.
2. Keep the agency backend untouched and route agency users through the B2B spine.
3. Expand the public checker live-data tool calls.
4. Keep the v2 travel-scene design evolving without turning it into gimmick UI.
