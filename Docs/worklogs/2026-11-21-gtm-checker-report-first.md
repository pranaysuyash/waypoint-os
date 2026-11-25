# Itinerary checker report-first implementation

November 21, 2026. Companion to the [GTM wedge UI and UX review](../exploration/GTM_WEDGE_UI_UX_DESIGN_REVIEW_2026-11-21.md).

## Implementation

- Failed or malformed responses keep the input form and its draft mounted. The failure alert receives focus, and each explicit retry sends one request. A blocked backend response with a usable packet opens a partial report.
- The public landing page and metadata use a pre-booking second opinion. Narrow layouts show intake before the sample. The report puts the first finding or clarification at the top and offers an edit path with the previous text. A separate new check starts fresh.
- The report omits the synthetic score and sample-generated route, hotel and perks data. The sample gallery remains on the landing page. Findings combine server blocker order, known copy mappings, and matching source text from the report. Missing weather values display as unavailable rather than fake measurements.
- Advisor handoff asks for a named selection and consent. No-match users retain access to their report and are not enrolled in an anonymous future transfer. Capture receipts distinguish the request from confirmed delivery. Branded URLs show distinct missing and unavailable states. Displayed response times come from the profile.
- Sharing previews the summary and respects cancellation. Export no longer emits the finding-evidence event. The checker forwards a report bearer capability only to the existing read, export and delete endpoints. The traveler UI keeps that capability in memory for the current report.
- Original-input retention is opt-in. The copy states that a derived report may still be stored. Persistent report links remain a separate decision.

## Visual evidence

The screenshots and recordings use fictional input. Desktop is Chromium at **1440 × 900** and mobile is Chromium touch emulation at **390 × 844**. The video shows real browser interactions with synthetic API responses. The recording pauses briefly on key states for reading.

| State | Desktop | Mobile |
|---|---|---|
| Intake before | [PNG](../evidence/gtm-checker-2026-11-21/desktop-before-intake.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-before-intake.png) |
| Intake after | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-intake.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-intake.png) |
| Failure before | [PNG](../evidence/gtm-checker-2026-11-21/desktop-before-failure.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-before-failure.png) |
| Failure after | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-failure.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-failure.png) |
| Report with findings | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-report.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-report.png) |
| Partial report | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-partial.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-partial.png) |
| No flagged findings | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-no-findings.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-no-findings.png) |
| No agency match | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-no-match.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-no-match.png) |
| Share preview | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-share-preview.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-share-preview.png) |
| Named recipient and consent | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-advisor-consent.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-advisor-consent.png) |
| Request receipt | [PNG](../evidence/gtm-checker-2026-11-21/desktop-after-advisor-receipt.png) | [PNG](../evidence/gtm-checker-2026-11-21/mobile-after-advisor-receipt.png) |
| Walkthrough | [MP4](../evidence/gtm-checker-2026-11-21/desktop-walkthrough.mp4) | [MP4](../evidence/gtm-checker-2026-11-21/mobile-walkthrough.mp4) |

## Verification and remaining scope

- Public browser flow, local integration with fixture API responses (Tier 3): run `node e2e/gtm-checker-visual.cjs` from the frontend directory against port 3005. Set `GTM_CHECKER_BROWSER` to a local Chromium executable when the matching Playwright browser is unavailable. Asserts request shape and retry count, focus and preserved draft, report hierarchy, no fabricated result values, report token header, share cancellation, download, no-match behavior, and named consent and receipt.
- Frontend focused tests (Tier 2, S1): `vitest run checker-report agency-branding honesty-sweep blocker-copy stage-declaration` passed 17 tests. `tsc --noEmit` passed. The two standalone showcase suites had seven baseline failures recorded in the audit. They are outside the updated report path.
- Backend focused tests (Tier 2, S1): public checker live-check, entity, contract-authority, branding and access/retention suites passed 35 tests, with one existing Starlette deprecation warning. The isolated tests use test data. No live advisor delivery or production service check was performed.
- Local HTTP: frontend and backend health responded. The metrics endpoint requires authentication. The unknown advisor link showed an explicit missing state. The principal browser captures exercise the public path. A real mobile device, VoiceOver, real provider-backed trip analysis, and a staffed advisor response remain unverified.
- Extraction characterization, optional source-linked travel visuals, full accessibility acceptance, queue fulfillment, funnel analytics and legacy backend authorization remain separate audit work. The checker now uses the scoped capability route. Server-side retirement of older endpoints needs its own caller and authorization review.
