# v9 Living Journey — implementation rationale

## What this is

A complete landing prototype for Waypoint that treats the customer journey as one
spatial narrative rather than four disconnected product stages.

The central interaction is a single, reduced-motion-gated 2D canvas. It renders a
representative Kerala itinerary with four real journey states:

- **Intake** — fragments arrive from WhatsApp, email, and a call note.
- **Decisions** — dates, nights, and transfers resolve into a route.
- **Disagreements** — a budget / room-type tension stays visible instead of being
  buried in a thread.
- **Updates** — a late call note redraws the brief while preserving its source.

The content is grounded in the existing design-lab prototype and product strings:
`Missing customer details`, `Suggested Follow-up`, Kerala, Mumbai, Kumarakom, and
Marari. The prototype does not pretend to be the production route or claim a backend
integration that does not yet exist.

## Why the canvas is the right abstraction

FieldCanvas works because its animation is a live view of a real model. This prototype
applies the same principle to travel operations: the map is not a decorative globe;
it is a visual explanation of how a request becomes a quote-ready brief.

The canvas state is normalized in the script as `nodes`, `events`, and `stageData`.
Changing a state tab updates the same route, markers, arcs, and caption. The replay
control walks the four states in sequence. The stage tabs are the keyboard-accessible
alternative to clicking canvas markers.

## Motion and performance decisions

- One 2D canvas; no WebGL, 3D dependency, video, or remote map SDK.
- Animation runs only while the map is in view and motion is allowed.
- `prefers-reduced-motion: reduce` renders a static frame and changes the control to
  `Play motion`.
- The visible map has an explicit `Pause motion` control because the loop is longer
  than a short transition.
- `IntersectionObserver` stops the loop when the map leaves the viewport.
- Canvas resizing caps device pixel ratio at 2.
- Content is visible by default; the observer scaffolding is progressive-enhancement ready, but no content is hidden if JavaScript or intersection callbacks are unavailable.
- No `transition: all`, gradients, backdrop glass, pill buttons, or glow-heavy styling.

## Interaction model

- Four stage tabs update `aria-selected`, the live status line, map emphasis, and the
  explanatory caption.
- `Replay journey` moves through intake → decisions → disagreement → update.
- Clicking a visible map marker selects its related state; tabs remain the canonical
  accessible control for the same state change.
- The motion button is an explicit pause / play affordance with `aria-pressed`.

## Verification

- `verify.mjs`: **25 passed, 0 failed** — structure, accessibility hooks, reduced-motion
  branch, loop cancellation, contrast, and design-system constraints.
- Browser smoke: desktop, mobile, stage-tab changes, pause / replay, reduced-motion
  context, canvas sizing, and page-error capture all passed.
- Captures: `journey-desktop.png`, `journey-mobile.png`, `journey-method.png`, and
  `journey-agency.png`.

## Deliberate boundary

This is a landing prototype, not a production feature implementation. The normalized
journey model is intentionally local and representative so the interaction can be
judged now. The production follow-up is to feed the same rendering contract from a
real public-safe journey summary endpoint, without changing the landing's visual or
interaction model.
