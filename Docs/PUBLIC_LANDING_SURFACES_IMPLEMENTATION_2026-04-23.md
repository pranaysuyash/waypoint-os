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
