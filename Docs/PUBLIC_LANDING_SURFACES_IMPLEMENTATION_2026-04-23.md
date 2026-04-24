# Public Landing Surfaces Implementation — 2026-04-23

## Scope
Implemented two public-facing landing surfaces in the Next.js frontend:

1. `frontend/src/app/page.tsx`
   - B2B Waypoint OS homepage
   - Positioned as the operating system for boutique travel agencies
2. `frontend/src/app/itinerary-checker/page.tsx`
   - Consumer-facing itinerary stress-test / GTM wedge page
   - Positioned as a trust-first audit surface

## Architectural Change
The existing internal dashboard previously lived at `/`.

To create a clean public/private split without collapsing the authenticated app, the internal dashboard was moved to:
- `frontend/src/app/overview/page.tsx`

Routing/auth updates:
- `/` is now public
- `/itinerary-checker` is now public
- `/overview` is now protected
- `frontend/src/proxy.ts` updated to protect `/overview` instead of `/`
- login/signup now redirect to `redirect` query param when present, else `/overview`
- `frontend/src/components/layouts/Shell.tsx` now bypasses shell chrome for public marketing and auth pages
- shell navigation now points Overview to `/overview`

## Files Added
- `frontend/src/app/overview/page.tsx`
- `frontend/src/app/itinerary-checker/page.tsx`
- `frontend/src/components/marketing/marketing.tsx`
- `frontend/src/components/marketing/marketing.module.css`
- `frontend/src/app/__tests__/public_marketing_pages.test.tsx`

## Files Updated
- `frontend/src/app/page.tsx`
- `frontend/src/proxy.ts`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/signup/page.tsx`

## Design Outcome
### B2B homepage
Built as a real multi-section SaaS/product site, not a hero-only composition.

Included:
- public header/nav
- hero with product framing and CTA
- product surface grid
- workflow compression section
- persona-specific value blocks
- operational trust section
- bottom CTA band
- public footer

### Itinerary checker page
Built as a conversion-oriented acquisition page.

Included:
- upload-first hero
- score/result snapshot module
- issue categories
- three-step flow explanation
- trust/privacy block
- FAQ block
- bottom CTA band
- public footer

## Verification
### Build
- `cd frontend && npm run build`
- Passed

### Focused tests
- `cd frontend && npm test -- --run src/app/__tests__/public_marketing_pages.test.tsx src/app/__tests__/p1_happy_path_journey.test.tsx src/app/__tests__/p2_owner_onboarding_journey.test.tsx`
- Passed (`8` tests)

### Runtime
Verified both routes return `200 OK`:
- `http://127.0.0.1:3000/`
- `http://127.0.0.1:3000/itinerary-checker`

Captured runtime screenshots for visual validation:
- `/tmp/waypoint-root.png`
- `/tmp/waypoint-itinerary-checker.png`

## Notes
- The public surface now has a stable ownership boundary separate from the authenticated product shell.
- The itinerary checker page is framed as an empowerment tool, not anti-agent replacement messaging.
- The B2B page is now visually and structurally closer to a shippable product homepage.

## Pending / Next Natural Work
- wire final CTA actions to actual lead/demo flows if desired
- add mobile-specific polish passes after broader browser QA
- decide whether to keep `/overview` as the permanent internal dashboard route or rename to another internal canonical route later

## 2026-04-24 Hero Fidelity Correction
The B2B homepage first fold was revised after live browser review at `1144x953` showed the prior implementation behaving like a split text/card layout with weak hierarchy and overflow risk. The correction was re-anchored to the generated reference image in `frontend/public/landing/waypoint-b2b-landing-page-full-2026-04-23.png`.

Changed:
- Restored the generated mock's hierarchy: `Waypoint OS` H1 with `The operating system for boutique travel agencies` as the large secondary line.
- Replaced the old generic preview with a constrained dashboard artifact modeled on the saved mock: greeting, unread/action/trip counters, inbox, workspaces, revenue, and AI copilot panels.
- Updated the first-fold proof row to match the saved design: travel-specific, end-to-end workspace, AI copilot, and secure/private proof.
- Hid the legacy floating scene nodes in the agency hero because they visually competed with the saved mock's clean dashboard composition.
- Adjusted the dashboard sizing so the product preview stays inside the reviewed `1144px` viewport instead of clipping.

Verification:
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run src/app/__tests__/public_marketing_pages.test.tsx` passed (`3` tests).
- `curl -I http://127.0.0.1:3000/` returned `200 OK`.
- Runtime screenshot captured at the reviewed viewport: `/tmp/waypoint-home-mock-reference-correction-1144.png`.

## 2026-04-24 Review-Driven B2B Page Simplification
An external visual/content review identified that the B2B page still read like an internal technical manual: repeated card grids, meta copy, too many accents, and a dense hero with competing elements.

Changed:
- Removed the remaining self-referential product/design copy from the page body.
- Removed the below-fold wall of equally weighted `surfaceGrid`, `personaGrid`, and `proofGrid` sections from the homepage route.
- Replaced them with fewer asymmetric buyer-facing sections:
  - agency pain section: messy inbox, hidden risk, owner visibility
  - product story section: capture request, ask before quoting, send safer output
  - role strip: solo advisors, owners, junior agents
  - trust panel: supplier preference, private notes, review controls
  - itinerary checker: public lead-quality surface
- Moved hero proof/stat density below the fold and kept the first fold focused on headline, CTA, and one dashboard artifact.
- Tightened the accent palette in the B2B dashboard preview toward cyan/blue, using other colors only as exceptions.
- Raised hero heading line-height to avoid collision-prone display typography.
- Added responsive collapse rules for the new asymmetric B2B sections.

Additional code cleanup:
- Removed `HeroScene` from the B2B homepage hero so the hero has one product metaphor: the dashboard artifact.
- Removed dead `LogoShowcase`, `HeroStat`, and unused brand/stat/surface-grid CSS from the marketing layer after call-site audit.
- Replaced visible "acquisition wedge" language with customer-facing itinerary-checker language.
- Reduced secondary CTA visual weight so paired actions no longer present as two equally weighted pills.

Verification:
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run src/app/__tests__/public_marketing_pages.test.tsx` passed (`3` tests).
- Runtime screenshots captured:
  - `/tmp/waypoint-home-surgical-cleanup-1440.png`
  - `/tmp/waypoint-home-surgical-cleanup-full-1144.png`
