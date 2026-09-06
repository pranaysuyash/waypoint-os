# A-17 WelcomeCard Browser Render Evidence — 2026-09-04

## Scope and boundary

This is the browser-render tranche for A‑17. It verifies that the current
`WelcomeCard` implementation is visible and usable in the live local app at
desktop and 390×844 mobile viewports. It does not claim hosted, production,
screen-reader, contrast-lab, or complete keyboard/focus-order certification.

## Runtime preconditions

The project preview contract was followed before inspection:

- backend `uv run uvicorn spine_api.server:app --port 8000` was running;
- frontend `npm run dev -- -p 3005` was running;
- `GET http://localhost:8000/health` returned HTTP **200**;
- `GET http://localhost:8000/metrics` returned HTTP **200**;
- `GET http://localhost:3005` returned HTTP **200**.

The backend response correctly reported the local boundary: rules/cache were
healthy, while no LLM provider was configured. That warning was not treated as
an onboarding failure.

## Inspected artifacts

- Desktop render: [a17_welcome_card_desktop_2026-09-04.png](assets/a17_welcome_card_desktop_2026-09-04.png)
- Mobile render: [a17_welcome_card_mobile_390x844_2026-09-04.png](assets/a17_welcome_card_mobile_390x844_2026-09-04.png)

Both artifacts were opened and visually inspected before being accepted as
evidence.

## Observations

### Desktop

- The WelcomeCard is rendered as a non-blocking panel at the lower-right of
  the overview surface.
- Heading “Welcome to Waypoint” and explanatory copy are visible.
- The card exposes the expected onboarding actions, including “Get started.”
- The underlying overview remains visible and interactive-looking; there is no
  backdrop or dialog treatment.
- The underlying overview also shows unavailable sample/runtime data states.
  Those states are separate from the onboarding card and are not counted as
  product-success evidence.

### Mobile (390×844)

- The WelcomeCard is rendered as a bottom panel within the viewport.
- Heading, explanatory copy, “Open intake,” and “Get started” remain visible.
- The card remains non-modal: the rest of the navigation/header is visible and
  no blocking backdrop is present.
- Text wraps without clipping in the inspected viewport.

## Contract interpretation

The source-level A‑17 contract remains:

- component identity: `WelcomeCard`;
- compatibility export: `WelcomeModal` remains an alias for existing callers;
- semantic role: labelled `region`, not `dialog`;
- `aria-labelledby="welcome-card-title"`;
- `aria-describedby="welcome-card-description"`;
- no `aria-modal`, focus trap, scroll lock, or Escape-to-close behavior is
  claimed because this is intentionally a non-blocking card.

The visual evidence is consistent with that contract at both tested sizes.

## Verification boundary and next checks

This tranche upgrades A‑17 from source/unit-only evidence to **local browser
render evidence**. It does not close the broader accessibility gate. The next
required checks are:

1. browser accessibility-tree inspection of the card's computed name and
   description;
2. keyboard Tab/Shift+Tab traversal and visible focus-ring observation;
3. screen-reader announcement check;
4. contrast measurement for text, borders, and focus states;
5. authenticated onboarding journey across a clean tenant;
6. hosted/device evidence before pilot promotion.

No provider, customer, legal, or production claim is made by these local
screenshots.
