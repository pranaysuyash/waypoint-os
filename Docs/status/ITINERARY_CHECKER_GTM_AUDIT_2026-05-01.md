# Itinerary Checker GTM Audit

Date: 2026-05-01

## Source Objective

User-provided goal, captured verbatim in working terms:

- free end-user itinerary checker as a GTM wedge
- traveler-led, not agency-replacement messaging
- upload a plan or paste text
- parse with OCR or direct LLM/text extraction first
- understand entities, nuance, and itinerary structure
- call live tools/data sources
- score on multiple criteria and suggest upgrades
- persist uploaded files, entered data, extracted data, and suggestions
- use consented data to improve algorithms and, later, train models
- keep deployment easy and cost-effective
- explore optional side income without cannibalizing B2B2B customers
- keep imagery, design language, and positioning aligned with the agency business
- document the prompt, the research, the checks, and the implementation state

## Completion Criteria

The objective is only complete when all of the following are true:

1. Public page exists and is traveler-led.
2. Upload or paste flow is real, not just static marketing.
3. Itinerary text can be parsed from direct text and file inputs.
4. Live checks run against real data sources.
5. The report returns multiple criteria, not a single vanity score.
6. Uploaded/entered data, extracted data, and suggestions can be stored with consent.
7. The implementation stays cost-conscious and easy to deploy.
8. Messaging and visuals avoid competing with the agency workspace.
9. The work is documented with evidence, not just intent.

## Prompt-to-Artifact Checklist

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Free public checker | Traveler-facing copy is live in `frontend/src/app/(traveler)/itinerary-checker/page.tsx` and homepage wedge copy is live in `frontend/src/app/page.tsx`. | Verified |
| Traveler-led positioning | Public copy says `Free itinerary ATS`, `Bring your plan. Get it checked.`, and `Share this report with them directly`. | Verified |
| Avoid agency replacement framing | Research docs explicitly say the checker should not be positioned as a replacement for agency work. | Verified |
| Upload or paste plan | Paste path and file upload path are both wired; supported files are read in-browser and turned into scored runs. | Verified |
| OCR/direct parsing | Text files use direct browser reads; PDFs use browser-side text extraction; images use OCR. | Verified |
| Live tool/data calls | `useSpineRun` and `runSpine` call `/api/spine/run` and poll `/api/runs/{run_id}`. | Verified |
| Multi-criteria scoring | Checker page derives a score from live `RunStatusResponse` fields, including the Open-Meteo climate enrichment signal, and displays live blocker counts. | Verified |
| Save uploaded / entered / extracted data | The public checker now persists consented raw uploads plus extracted and entered data through the canonical trip record and public checker artifact store. | Verified |
| Consent-based retention | The public checker UI includes an explicit consent control, and the backend only archives raw upload bytes when consent is present. | Verified |
| Cost-effective deployment | Frontend reuses the existing Spine BFF and accepted-only polling model; no new route family was added. | Verified |
| Design language alignment | Page now uses an expressive dark treatment with GSAP motion and scanned-glass accents; inspiration was checked against Google’s `design.md`, Material 3 Expressive, and Refero Styles. | Verified |
| GTM separation from agency product | Agency CTA remains separate, and the public tool does not advertise itself as a new agency desk. | Verified |
| Durability of documentation | This file captures the goal prompt and state explicitly. | Verified |

## What Is Real Today

### Public surface

- `frontend/src/app/(traveler)/itinerary-checker/page.tsx` is now a live, interactive surface with traveler-led language.
- The hero uses a richer visual language: layered glow, scan ring, orbiting chips, and GSAP motion.
- The checker copy stays aligned with the agency boundary.
- Upload handling now supports text, PDF text extraction, and image OCR before scoring.

### Backend and transport

- `frontend/src/hooks/useSpineRun.ts` submits to `/api/spine/run` and polls `/api/runs/{run_id}`.
- `frontend/src/lib/api-client.ts` contains the same accepted-only spine polling contract.
- `spine_api/server.py` persists accepted/processed spine runs through `save_processed_trip(...)`.
- `spine_api/persistence.py` contains `TripStore` and `save_processed_trip(...)` for durable trip persistence.
- Submission provenance from the public checker is now attached to the persisted run metadata, consented uploads are archived under the public checker artifact store so the file name, MIME type, extraction method, and raw bytes survive storage, and the backend attaches a live climate risk signal from Open-Meteo to the run payload when destination/date context is available.
- `spine_api/server.py` exposes public export/delete routes for consented checker records, and `spine_api/core/middleware.py` marks `/api/public-checker/*` as public.
- `src/public_checker/live_checks.py` isolates the climate/geocoding lookup logic from the main spine path.

### Verification

- `frontend/src/app/__tests__/public_marketing_pages.test.tsx` passes and covers the current public copy and paste-button behavior.
- `frontend` type-check passes with `npx tsc --noEmit`.

## What Is Still Missing

1. The public checker currently uses one live climate source; broader enrichment sources can be added later if desired.
2. More granular retention windows and background cleanup can still be added as a later hardening pass.

## Design References Reviewed

Checked for visual direction before the motion pass:

- Google Material 3 Expressive announcement
- Google `design.md` repository
- Refero Styles

Design takeaway:

- use expressive motion and layered depth
- keep the layout glanceable and premium
- avoid turning the checker into a generic dashboard or a heavy 3D demo
- keep the checker visually distinct from the agency workspace while still sharing the same design family

### Durable Design Artifact

- [`DESIGN.md`](/Users/pranay/Projects/travel_agency_agent/DESIGN.md) now captures the public wedge visual system as a repo-level artifact.
- [`frontend/DESIGN.md`](/Users/pranay/Projects/travel_agency_agent/frontend/DESIGN.md) remains the broader Waypoint OS design system for the app shell.
- The public checker should follow the repo-level file first so future iterations keep the same scan-instrument identity.

## Current Product Judgment

- Code-ready: yes
- Feature-ready: yes
- Launch-ready: partial

Reason:

- the public surface exists and is coherent
- the live text path, file upload extraction, live Spine contract, consented storage, public export/delete controls, and live climate enrichment are wired
- the remaining work is expansion and hardening, not a missing core deliverable

## Next Concrete Build Step

1. Add richer live-data sources if the wedge needs broader destination intelligence.
2. Add retention windows / background cleanup for long-term operational hygiene.
3. Keep the public checker design system updated as the wedge evolves.
