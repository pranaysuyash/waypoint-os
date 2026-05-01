# Homepage GTM Alignment

Date: 2026-05-01

## Goal

Align the main landing page with the public itinerary-checker wedge without losing the agency-first product story.

## Principles

- Keep Waypoint OS as the agency operating system.
- Present the public itinerary checker as a traveler-led plan audit, not a replacement travel desk.
- Make the CTA split explicit: agencies book a demo, travelers inspect a plan.
- Avoid ambiguous pricing language when the CTA actually points to the public checker.

## What Changed

- Homepage hero copy now says the public itinerary checker gives travelers a cleaner brief before they ask the agency to build.
- Homepage and checker CTAs now explicitly say `itinerary or travel plan` so the wedge is unambiguous for pasted text and uploaded PDFs.
- The hero secondary CTA now points directly to `/itinerary-checker` with the label `See the public checker`.
- The hero proof chips now include `Public checker for traveler-led plan audits`.
- The wedge section now states that the checker is a public plan-audit layer, not a replacement for agency work.
- The final CTA band no longer says `See pricing` when it links to the checker.

## Verification

- Updated homepage copy and CTA expectations in `frontend/src/app/__tests__/public_marketing_pages.test.tsx`.
- Existing public marketing tests should cover the homepage and checker story after the copy update.

## Notes

- The homepage remains agency-first.
- The public checker is positioned as the entry point for travelers who want to self-audit an itinerary before bringing it to an agent.
- This keeps the GTM wedge additive instead of cannibalizing the core agency offer.
