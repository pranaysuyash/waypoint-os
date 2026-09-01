# Landing page v6 — "Waypoint Atlas"

**Status:** Prototype for review. Nothing in the live app was modified.
**Prototype:** `frontend/design-lab/v6-atlas/index.html` (single self-contained file, no build step)
**Live page today:** `frontend/src/app/page.tsx` → `components/marketing/landing-v5.tsx`

---

## 1. Why v5 reads as early-2020s

Not a matter of taste — these are specific, dated conventions that peaked around 2020–2021
and are now read as "old SaaS". Each is cited against the live file.

| # | Tell | Evidence | Why it dates |
|---|---|---|---|
| 1 | Four stacked radial "glow blobs" + fixed 92px grid overlay | `landing-v5.module.css:1-24` | The signature 2021 dark-SaaS background. Reads as decoration, not design. |
| 2 | Glassmorphic floating pill header — `backdrop-filter: blur(24px)`, `border-radius: 24px`, inset white highlight | `landing-v5.module.css:38-46` | Peak 2021 glassmorphism. Also expensive to composite on scroll. |
| 3 | Eyebrow "kickers" — `text-transform: uppercase` + `letter-spacing: 0.08–0.12em` | `landing-v5.module.css:217-218, 273-274, 493-494` | The 2020 eyebrow-label convention. Three separate instances. |
| 4 | Gradient primary CTA `linear-gradient(135deg, #7ab9ff, #57e0ef, #39d0d8)` | `landing-v5.module.css:336` | The 2021 gradient button. Universally read as dated now. |
| 5 | **Infinite animations** — `ribbon-dash 12s linear infinite`, `ribbon-breathe 4.8s infinite`, plus two SVG `animateMotion repeatCount='indefinite'` | `landing-v5.module.css:173,182`; `landing-v5.tsx:292,298` | Loops forever, including offscreen. Burns CPU/GPU on every visit. |
| 6 | Full-bleed hero photo under a heavy dark scrim, with floating translucent panels | `landing-v5.tsx:54-60, 102-135` | The 2020 "hero image + overlay" pattern. |
| 7 | Fake-precision metrics — `2m 14s`, `3`, `18%` | `landing-v5.tsx:22-26` | Unattributable numbers undermine the credibility the page is asking for. |
| 8 | Defensive copy — "Not a prettier CRM.", "The value is not 'AI' for its own sake." | `landing-v5.tsx:95, 176` | Arguing with an objection the visitor has not raised. |
| 9 | Generic icon bullets — `Sparkles`, `CheckCircle2` | `landing-v5.tsx:155, 162` | Stock AI-startup iconography. |

Items 1–5 are the reason it *looks* old. Items 7–8 are the reason it reads as
low-confidence. Both needed fixing; the visual ones alone would not have saved it.

---

## 2. The direction: "Waypoint Atlas"

**Concept.** A survey document — part field notebook, part printed atlas, part editorial
broadsheet. Warm paper stock, deep ink, one sharp accent. Cartographic precision without neon.

The reasoning: the product turns chaos into a legible record. The page should already look
like the output — an annotated document — rather than like a control room. It also happens
to be the one aesthetic nobody else in travel-SaaS is using, which is the point.

**Deliberately rejected:** dark + neon + glass (where v5 already is, and where the whole
category is), and beige minimalism (which has itself become the new default).

### Type

| Role | Family | Why |
|---|---|---|
| Display | **Fraunces** (`SOFT` 24–40, `WONK` 1) | Variable serif with genuine character; carries an editorial voice without becoming decorative. Replaces Sora. |
| Body / UI | **Schibsted Grotesk** | Warm-neutral grotesque; more character than Inter, better UI legibility than a serif. Replaces Rubik. |
| Labels, coordinates, chips | **IBM Plex Mono** | Carries the instrument/survey flavour; makes the small text feel deliberate. |

Three families, each with a distinct job. No Inter, no Space Grotesk, no system stack.

### Colour

Warm paper rather than white, and **vermilion rather than blue** — the single most
important decision here. Every competitor uses blue or purple.

| Token | Value | Contrast on paper | Use |
|---|---|---|---|
| `--paper` | `#F7F4ED` | — | Page stock |
| `--paper-card` | `#FFFDF8` | — | Raised cards |
| `--paper-sunk` | `#F0EBE0` | — | Recessed panels |
| `--ink` | `#16191C` | 16.07:1 | Primary text |
| `--ink-2` | `#41494F` | 8.35:1 | Body copy |
| `--ink-3` | `#5A636A` | 5.58:1 | Labels, meta |
| `--vermilion` | `#BE4225` | 4.78:1 | Accent — **fills, borders, strokes only** |
| `--vermilion-ink` | `#9E3419` | 6.46:1 | Accent **text** |
| `--teal` | `#1F5C58` | 7.00:1 | Resolved / confirmed |
| `--amber` | `#8A5A0B` | 5.39:1 | Attention / inferred |
| `--rule-3` | `#8A8778` | 3.29:1 | Interactive borders (non-text, 3:1 floor) |

Two-token accent (`--vermilion` for graphics, `--vermilion-ink` for text) exists because
`#BE4225` clears 4.5:1 on paper but not on the tinted chip backgrounds. Every text
application uses the ink variant.

---

## 3. What actually changed

**Removed entirely:** glow blobs, grid overlay, glassmorphism, gradient buttons, uppercase
kickers, hero photo + scrim, floating dashboard mockups, all infinite animation,
invented metrics, defensive copy, `backdrop-filter`.

**Added:**

- **The specimen — an interactive intake demo.** The hero shows a real messy enquiry
  (switchable across WhatsApp / email / call notes) and extracts a structured brief in
  front of you. It demonstrates extraction, gap detection, and suggested questions in
  about ten seconds, with no signup. This replaces the static screenshot.
- **Epistemic chips.** Every extracted field is tagged Fact / Inferred / Assumed / Unknown.
  These mirror `EpistemicStatus` in `src/intake/packet_models.py:91-96` — so the page
  advertises a capability the product genuinely has, instead of a generic "AI" claim.
  This is the one thing worth remembering about the page.
- **Gaps ranked by consequence** — blocks the trip / changes the quote / shapes the plan.
  Recasts "we find missing info" as a judgement the buyer cares about.
- **An honest "not a good fit if" column.** Cheap credibility; also pre-qualifies.

### Copy principles applied

Active voice, second person, specific button labels, no first person, curly quotes,
`…` over `...`, numerals for counts. Defensive framing cut; the product is described by
what it does rather than by what it is not.

---

## 4. Verification

| Check | Result |
|---|---|
| JS syntax (`node --check`) | pass |
| HTML tag balance | pass, no unclosed tags |
| jsdom smoke suite | **32/32 pass** |
| — structure (one h1, heading order, skip link, nav label) | 7/7 |
| — specimen initial state + chip distribution | 8/8 |
| — tab switching, reset, re-extract, content swap | 8/8 |
| — motion gating, route normalisation, no infinite anims | 4/4 |
| — runtime errors | 0 |
| — **graceful degradation without IntersectionObserver** | 4/4 |
| Contrast, computed from file tokens | all AA; accent text 5.78–6.98:1 |
| `transition: all` | 0 |
| Infinite animations in CSS | 0 |
| `user-scalable=no` / `maximum-scale` | 0 |
| `outline: none` without replacement | 0 |
| `backdrop-filter` | 0 |

**Motion budget.** No animation on this page loops. Every reveal is one-shot and
`IntersectionObserver`-gated; the route line is drawn once on entry via
`stroke-dashoffset` with `pathLength="1000"` normalisation (v5 used two
`repeatCount='indefinite'` `animateMotion` pulses plus two infinite CSS keyframes).
Observers `unobserve` after firing. `prefers-reduced-motion` disables all transforms and
the CSS-only scroll-progress bar. The scroll bar uses `animation-timeline: scroll()`
and is hidden via `@supports` where unsupported — zero JS listeners.

Accessibility: skip link, `:focus-visible` rings, `aria-live` on extraction results,
full `tablist` semantics with arrow-key support, 44px minimum touch targets,
`env(safe-area-inset-*)` on the container, `theme-color`, `text-wrap: balance` on
headings, `tabular-nums` on numeric readouts.

---

## 5. If you approve — port plan

1. Promote tokens into `frontend/src/app/globals.css` (or the Tailwind theme in
   `tailwind.config.js`) so app shell and marketing share one source.
2. Register the three families in `src/app/layout.tsx` via `next/font/google`, replacing
   the current `Sora` + `Rubik` (line 2). Self-hosting removes the render-blocking
   request; the prototype uses a `<link>` for portability.
3. Split the specimen into `components/marketing/specimen/` — `SpecimenCard.tsx`,
   `BriefTable.tsx`, `EpistemicChip.tsx`, `useSpecimen.ts`. Keep the source fixtures in
   one data module so real intake can replace them.
4. Replace the hardcoded source fixtures with a call to the real intake endpoint, or
   keep them as a canned demo if the endpoint needs auth. **This is a product decision,
   not a design one.**
5. Retire `landing-v5.tsx` + `landing-v5.module.css` and the `v2`–`v5` route
   directories on merge.

### Retirement gate

The repo already carries four parallel landing generations (`src/app/v2` … `v5`) and none
were ever removed. That is the duplication problem noted in prior audits. Concrete
condition for this one:

> Merge v6 to `/` **only** in a commit that also deletes `src/app/v2`, `v3`, `v4`, `v5`
> and `components/marketing/landing-v5.*`. If v6 is rejected, delete
> `design-lab/v6-atlas/` instead. Either way the count of landing implementations goes
> **down**, not up.

---

## 6. Open — needs your call

1. **Metrics.** I removed v5's invented numbers rather than inventing better ones. If you
   have real figures (median time-to-brief, gap detection rate), they belong in the hero.
2. **The specimen's honesty.** It currently uses three hand-written fixtures. If you would
   rather it never show data the live model did not produce, it should call the real
   endpoint — otherwise the copy should say "illustrative".
3. **Photography.** v5 led with a hero image. This build leads with the interactive
   specimen and uses no photography at all. If brand photography matters, the natural
   slot is the closing CTA, not the hero.
4. **Dark mode.** The direction is light-first and the app shell stays dark. If marketing
   needs a dark variant, say so and I will define the token set — but the paper texture
   is most of what makes this work, and it does not survive a naive inversion.
