# Pricing Page Redesign 2026-06-28

## Decision

Align `/pricing` with the main app's dark product-shell language instead of the warmer editorial landing-page palette.

## Context

- The landing page is intentionally warm and editorial.
- The pricing page is a product-access surface, so it should feel like part of the app.
- The old pricing page read like a separate marketing page and reused a softer cream palette that didn't match the current product shell.

## Chosen Path

1. Keep the public pricing route self-serve and honest.
2. Use the dark shell, blue accent, and glass-card treatment that the app uses elsewhere.
3. Keep the access paths explicit:
   - self-serve workspace,
   - guided rollout,
   - separate traveler checker.
4. Avoid fake demo dependency language.
5. Make the shared public header responsive on mobile so the pricing page stays usable on narrow screens.

## Files

- `frontend/src/components/marketing/pricing-page.tsx`
- `frontend/src/components/marketing/pricing-page.module.css`
- `frontend/src/components/marketing/marketing.module.css`
- `frontend/src/app/pricing/__tests__/page.test.tsx`

## Verification

- `npm test -- --run src/app/pricing/__tests__/page.test.tsx src/app/__tests__/public_marketing_pages.test.tsx`
- `npm run build`
- Chrome headless screenshots on desktop and mobile-sized viewports

