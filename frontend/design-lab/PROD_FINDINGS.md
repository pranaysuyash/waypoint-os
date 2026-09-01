# Prod findings — measured from the signed-in app

**Date:** 2026-08-31
**Method:** logged in as `newuser@test.com` (owner, agency `Test`) and read **computed
styles + DOM** across 11 authenticated routes. Not screenshots — this model cannot
reliably read PNGs, so the inspection was rebuilt to emit data.
**Reproduce:** `python3 inspect-app-dna.py` → `app-dna/*.json` + `app-dna/REPORT.md`

---

## 0. Correction to the record

Earlier in this session I reported visual findings from screenshot files — a light
`#FFFFFF` inbox, an `ARIVUS` wordmark, a categorised sidebar, 4 stat cards. **Those
claims were not grounded and the measurements contradict them.** Measured truth:

| Earlier claim | Measured |
|---|---|
| `/inbox` is light `#FFFFFF` | `body` bg = `rgb(13,17,23)` — dark, like every other route |
| Wordmark `ARIVUS` | `Waypoint OS` |
| Categorised sidebar (Trips / Finances / Settings) | One **flat 15-item** list |
| 4 stat cards (8 / 12 / 3 / 0) | `LATEST TRIPS STATUS · SHOWING 5 OF 9140` |

I should have said "I can't read these" instead of describing them. Fixing the method
was the right call, and the correction stands.

---

## 1. The product is uniformly dark — and internally disciplined

All **11** routes: `body` background `rgb(13,17,23)` = `#0d1117`, text `#e6edf3`,
`color-scheme: dark`. There is no light route. There is no theme switch.

| Route | Gradients | `backdrop-filter` | Glow shadows (blur ≥ 24px) | SMIL |
|---|---:|---:|---:|---:|
| **`/` (landing)** | **17** | **1** | **11** | **2** |
| `/overview` | 2 | 0 | 1 | 0 |
| `/trips` | 3 | 0 | 2 | 0 |
| `/inbox` | 1 | 0 | 0 | 0 |
| `/quotes` | 1 | 0 | 0 | 0 |
| `/settings` | 2 | 0 | 0 | 0 |
| `/insights` | 1 | 0 | 0 | 0 |
| `/suppliers` | 1 | 0 | 0 | 0 |
| `/trips/trip_8b15e3f848f9` | 1 | 0 | 0 | 0 |
| `…/intake` | 1 | 0 | 0 | 0 |
| `…/packet` | 1 | 0 | 0 | 0 |
| **Total** | **31** | **1** | **14** | **2** |

**The landing page is carrying the entire 2020s aesthetic, alone:**

- **55%** of all gradients (17 / 31)
- **79%** of all glow shadows (11 / 14)
- **100%** of `backdrop-filter` (1 / 1)
- **100%** of SMIL animation (2 / 2)
- **6** infinite CSS animations (`ribbon-dash 12s`, `ribbon-breathe 4.8s` × 5)

This is the answer to "the landing page reads like very poor, early 2020's style."
It is not the dark theme. It is **a decoration layer that exists on exactly one
route.** Every app route is already restrained: 1–3 gradients, zero blur, zero–two
glows, zero SMIL.

---

## 2. Consequence: v7 (light editorial) was the wrong direction

`v7-document/` was built from `DESIGN.md` §11 — Theme B "Minimalist Document", light.
Prod says the product ships dark on 100% of its surface, with real data
(9,140 trips). A light landing dumping into a dark console creates a tonal seam, and
coherence would require migrating the whole app — unreviewed and unscoped.

**The synthesis:** apply Theme B's *rules* to Theme A's *palette*.

| Theme B rule (§11) | Applied to the dark palette the product actually ships |
|---|---|
| No gradients | Strip 17 |
| No glassmorphism | Strip the 1 `backdrop-filter` |
| No glows / single subtle shadow | Strip 11; cap blur at 8px |
| 8px radius everywhere, no pills | Replace `999px`/`30px`/`24px` |
| No infinite animations | Strip 6 CSS + 2 SMIL |
| Generous typography (body 18px / 1.75) | Landing currently runs the **app** scale: 14px / 1.6 |

That fixes the dated feel **without** introducing a light/dark seam, and without
touching the app. That is `v8-disciplined-dark/`.

---

## 3. Design-system drift: every background token is off-spec

`DESIGN.md` §2 vs live `:root` values (measured):

| Token | §2 spec | Live | |
|---|---|---|---|
| `--bg-canvas` | `#080a0c` | `#0d1117` | off-spec (GitHub Primer value) |
| `--bg-surface` | `#0f1115` | `#161b22` | **= spec's `--bg-elevated`** |
| `--bg-elevated` | `#161b22` | `#1c2128` | **= spec's `--bg-highlight`** |
| `--bg-highlight` | `#1c2128` | `#222833` | off-spec, new value |
| `--bg-input` | `#111318` | `#0e1116` | off-spec |

Two of the five slid exactly one step up the ramp; three are foreign values. The
ramp was redefined and the docs never followed. **§2 is not a description of the
shipped system — it is a description of a system that was replaced.**

Also measured: `--text-rationale` (`#c9d1d9`), an **app-UI token, is painted on the
marketing page** (3 elements). And a landing text colour `rgb(122,185,255)` =
`#7ab9ff` matches no token (`--accent-blue` is `#58a6ff`, hover is `#79b8ff`).

---

## 4. Typography: the spec's font is never loaded

Measured element counts across all routes:

| Font | Elements |
|---|---:|
| Rubik | 1,427 |
| JetBrains Mono | 88 |
| Sora | 10 |
| Outfit | 3 |
| **IBM Plex Sans** (§3 spec) | **0** |

`DESIGN.md` §3 specifies IBM Plex Sans + JetBrains Mono. `layout.tsx` loads Sora +
Rubik. **Outfit** (3 elements) is a third family nobody documented. Body copy renders
at **14px / 22.4px** — the app's dense scale — on the marketing page too.

---

## 5. Radius: five competing scales

Across all routes: `6px` ×228, `9999px` ×184, `8px` ×125, `12px` ×102, `4px` ×79,
`999px` ×21, `2px` ×10, `30px` ×8, `16px` ×6, `20px` ×2.

On the landing **alone**: `999px` ×21, `30px` ×8, `20px` ×2, `24px` ×1 — **zero**
6px or 8px. Every landing CTA is a `999px` pill whose `background-color` is
`rgba(0,0,0,0)`; the fill comes from a gradient in `background-image`. `DESIGN.md`
§4 says *"rounded-md 6px universally — no pills."*

---

## 6. Information architecture (measured, all app routes)

One flat sidebar, 15 items, no grouping:

> New Inquiry · Overview · Lead Inbox · Quote Review · Trips in Planning · Quotes ·
> Bookings · Documents · Payments · Suppliers · Insights · Audit · Knowledge Base ·
> Settings · Seasonal Campaigns

Plus a second bottom nav (Inbox, Trips, New, Docs, Settings) and a header strip
(`Expand`, `Quote Review 0 quotes to review`, `System Check 31 items to check`).

**Pipeline stages** (Lead Inbox, Quote Review, Trips in Planning) are interleaved with
**sections** (Settings, Knowledge Base, Audit) at one level. 15 flat items is past the
point where a flat list aids recall. Noted, not in scope for the landing.

---

## 7. The epistemic capability is real in the backend and absent from the UI

`/trips/trip_8b15e3f848f9/intake` renders:

> H1 **Trip details incomplete** → H3 *Missing customer details* → H3
> *Suggested Follow-up* → H3 *Trip Details* → H3 *Notes*

`src/intake/packet_models.py` defines `EpistemicStatus` (FACT / INFERRED / ASSUMED /
UNKNOWN) and `AssumptionRecord` (with `criticality` and
`acknowledged_by_operator`). Searching the frontend for that vocabulary returns
**3 files, none of them a UI surface** (`traveler-prompts.ts`,
`DistributionPanel.tsx`, an overview test).

**So the product's intake tells you a field is *missing* — it does not tell you
whether a filled field is *fact, inferred, or assumed*.** The differentiator my v7
specimen advertised is a genuine backend capability with **no UI**.

Two honest options, not one:

1. **Landing claims only what ships:** "it tells you what's missing and what to ask"
   (true — *Missing customer details* + *Suggested Follow-up* are real).
2. **Build the epistemic surface, then claim it** — the stronger product, but the
   landing must not get ahead of it.

`v8` takes option 1. The epistemic UI is logged as a build item, not a claim.

---

## 8. Verdict

| Question | Answer (measured) |
|---|---|
| Is the app light or dark? | **Dark, 11/11 routes, no switch** |
| Where does the 2020s feel live? | **The landing page alone** (55% of gradients, 79% of glows, 100% of blur + SMIL) |
| Is the app's design system healthy? | Palette is coherent; **docs are stale** (5/5 bg tokens drifted, spec font never loaded) |
| Should the landing go light? | **No** — it would seam against 100% of shipped surface |
| What should change? | Strip the decoration layer; adopt Theme B's *rules* on Theme A's *palette* |

**Next:** `v8-disciplined-dark/` is that build.
