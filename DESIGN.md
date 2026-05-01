---
name: Waypoint OS Public Wedge
version: alpha
description: Visual system for the public itinerary checker GTM wedge
colors:
  canvas: "#07090b"
  surface: "#0d1117"
  elevated: "#161b22"
  input: "#111318"
  text: "#e6edf3"
  muted: "#8b949e"
  accent-blue: "#58a6ff"
  accent-cyan: "#39d0d8"
  accent-purple: "#a371f7"
  accent-amber: "#d29922"
  accent-green: "#3fb950"
  border: "#30363d"
typography:
  display:
    fontFamily: Outfit
    fontSize: clamp(3rem, 7vw, 5rem)
    fontWeight: 700
  body:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
  mono:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
rounded:
  sm: 8px
  md: 14px
  lg: 20px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
---

## Overview

This design system is for the public itinerary checker wedge. The page should feel like a premium scan instrument: playful motion, luminous depth, and crisp hierarchy. It must not feel like a travel booking engine, a generic AI chatbot, or a replacement for the agency workspace.

## Principles

- Use a dark canvas, high-contrast text, and one primary blue or cyan path for action.
- Reserve amber and green for warnings and confirmations only.
- Use motion to suggest scanning, orbiting, and evaluation; avoid constant decoration.
- Keep layouts breathable and glanceable on mobile and desktop.
- Make the upload, paste, and score actions obvious in the first viewport.

## Do

- Keep the checker traveler-led.
- Keep the agency handoff visible.
- Use editorial spacing and a calm content rhythm.
- Prefer one strong accent per surface rather than many competing colors.
- Let live data and blockers carry the credibility, not ornament.

## Do Not

- Do not build a generic AI app chrome.
- Do not use heavy 3D or WebGPU unless it materially improves comprehension.
- Do not introduce purple-on-white defaults.
- Do not over-animate the experience.
- Do not frame the checker as a cheaper agency replacement.

## Motion

- Use subtle GSAP motion for scanlines, glow drift, and reveal timing.
- Keep motion functional: it should imply review, scoring, and detection.
- Respect reduced motion by ensuring the page remains strong when animations are muted.

## Relationship To Other Design Files

- `frontend/DESIGN.md` remains the broader Waypoint OS design system.
- This file narrows the public itinerary checker wedge.
- When the public checker evolves, update this file first so new UI stays on-brand.
