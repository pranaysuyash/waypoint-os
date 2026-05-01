# Itinerary Checker V2

Date: 2026-05-01

## Goal

Rework the public itinerary checker so it feels fun, travel-forward, and clearly separate from the agency workspace logic.

## Principles

- Keep the agency workflow distinct from the public checker surface.
- Share only the underlying scoring / enrichment engine where needed.
- Make the public page feel like a travel scene, not a SaaS dashboard.
- Use motion, destination imagery, route ribbons, and playful cards to imply travel planning.

## What Changed

- The public checker hero now reads like a travel map instead of a generic dashboard.
- The checker now includes a scenic preview card with route ribbon, plane motion, and destination tags.
- The trust strip was replaced with travel moments cards so the page feels more human and less enterprise.
- The copy now explicitly says `itinerary or travel plan` so pasted text and uploaded files are both covered.
- The backend/public checker flow remains separate from the agency `/run` path.

## Verification

- Update the browser flow after the backend route and route-map mapping land.
- Confirm upload, paste, and screenshot all still reach the public checker submit path.
- Keep the agency workspace untouched by the public checker surface.

## Notes

- The public checker should keep evolving toward a more playful travel experience without becoming gimmicky.
- The logic split matters: the public checker is a public front door, not a duplicate agency workflow.
