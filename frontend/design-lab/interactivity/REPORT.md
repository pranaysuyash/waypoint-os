# Interactivity & animation — measured at runtime

**Captured:** 2026-08-31 12:37:55
**Method:** instrumented `requestAnimationFrame`, `addEventListener`, `IntersectionObserver` and `canvas.getContext` **before page scripts ran**, then sampled rAF throughput while idle, while scrolling, and while hovering. Static CSS greps cannot answer "is it animated" — this can.

## Side by side

| Metric | http://127.0.0.1:5183/ | https://fieldcanvas.app |
|---|---:|---:|
| DOM nodes | 1,144 | 43 |
| Page height (px) | 15,381 | 1,066 |
| Screens of scroll | 17.1 | 1.2 |
| Transfer (KB) | 912 | 15 |
| Requests | 21 | 8 |
| Buttons | 57 | 0 |
| Links | 49 | 3 |
| Form inputs | 6 | 0 |
| [aria-expanded] (disclosure) | 0 | 0 |
| Dialogs / tabpanels | 0 | 0 |
| <canvas> elements | 9 | 1 |
| WebGL contexts | 0 | 0 |
| <video> elements | 0 | 0 |
| SVG SMIL animations | 0 | 0 |
| @keyframes blocks | 3 | 0 |
| Infinite CSS rules | 1 | 0 |
| Elements animating (computed) | 2 | 0 |
| Transition rules | 1 | 2 |
| Elements transformed | 16 | 0 |
| will-change elements | 1 | 0 |
| sticky/fixed elements | 3 | 1 |
| Gradient elements | 7 | 1 |
| backdrop-filter elements | 3 | 2 |
| Event listeners registered | 155 | 2 |
| IntersectionObservers | 1 | 0 |
| rAF calls/sec while IDLE | 125.0 | 85.0 |
| rAF calls/sec while SCROLLING | 683.8 | 366.9 |
| rAF calls/sec while HOVERING | 1631.0 | 627.9 |

## http://127.0.0.1:5183/

*Title:* FieldCanvas — paint space, pull structure. The spatial canvas for anyone who works on space.
*h1+h2 count:* 13 · *DOM depth:* 15
*Screenshot:* `/Users/pranay/Projects/travel_agency_agent/frontend/design-lab/interactivity/127.0.0.1_5183.png`

**Top event listeners:** `invalid`×7, `scroll`×5, `pointermove`×4, `pointerdown`×3, `pointerup`×3, `message`×2, `close`×2, `auxclick`×2, `click`×2, `contextmenu`×2

**Animation names:** `fcPulse`

**Canvas contexts:** `2d` 1440×900, `2d` 510×383, `2d` 517×356, `2d` 1440×900, `2d` 1440×900, `2d` 1440×900, `2d` 1440×900, `2d` 1440×900, `2d` 1440×900, `2d` 1440×900

**Honours `prefers-reduced-motion`:** yes

## https://fieldcanvas.app

*Title:* FieldCanvas
*h1+h2 count:* 1 · *DOM depth:* 7
*Screenshot:* `/Users/pranay/Projects/travel_agency_agent/frontend/design-lab/interactivity/fieldcanvas.app.png`

**Top event listeners:** `resize`×1, `DOMContentLoaded`×1

**Canvas contexts:** `2d` 300×150

**Honours `prefers-reduced-motion`:** NO

## How to read this

- **rAF/sec while IDLE** is the headline number. ~0 means the page is static until you touch it. 30–60 means a permanent animation loop (a WebGL scene, a marquee, a breathing glow) burning a frame budget every second the tab is open.
- **rAF/sec while SCROLLING** versus idle tells you whether a scroll engine (GSAP ScrollTrigger, Lenis, Locomotive) is driving the page.
- **WebGL contexts > 0** means real 3D — the heaviest and most expensive kind of "interactive", and the hardest to make accessible.
- High **DOM nodes** + high **transfer** is the cost column; high **buttons / [aria-expanded] / inputs** is the actual-interactivity column.
