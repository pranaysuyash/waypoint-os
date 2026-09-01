# v8 "Disciplined Dark" — rationale

**Status:** parallel build, live page untouched (`git status --short -- frontend/src`
clean at build time).
**Supersedes:** `v7-document/` as the *recommended* direction. v7 is retained, not
deleted — see §5.
**Evidence:** `../PROD_FINDINGS.md`, produced by `../inspect-app-dna.py`.

---

## 1. Why v7 was the wrong call

v7 was built from `DESIGN.md` §11 — Theme B "Minimalist Document", light. It is a
faithful implementation of the spec. It is also, on the evidence of the running
product, the wrong direction.

Measured across 11 authenticated routes:

- **Every route is dark.** `body` background `rgb(13,17,23)` on 11/11. There is no
  light route and no theme switch.
- **Theme B is implemented nowhere.** 0 of 13 Theme B token *values* are present.
  (Token *names* are shared with Theme A, so a presence check is meaningless — this
  was a bug in my own first report and is now corrected in `inspect-app-dna.py`.)
- The product has real volume: `LATEST TRIPS STATUS · SHOWING 5 OF 9140`.

A light landing dumping into a dark console creates a tonal seam, and coherence
would require migrating the entire app to Theme B — unreviewed, unscoped, and
contrary to 100% of shipped surface.

**I built v7 from the document instead of from the product.** That is exactly the
error Pranay called out. v8 is the correction.

---

## 2. What prod actually said

The decisive measurement is *where* the dated aesthetic lives:

| | Landing `/` | 10 app routes | Landing's share |
|---|---:|---:|---:|
| gradients | **17** | 14 | **55%** |
| `backdrop-filter` | **1** | 0 | **100%** |
| glow shadows (blur ≥ 24px) | **11** | 3 | **79%** |
| SMIL animations | **2** | 0 | **100%** |
| infinite CSS animations | **6** | 10 | 38% |

**The app is already disciplined.** Every app route carries 1–3 gradients, zero
blur, zero–two glows, zero SMIL. The early-2020s feel is a decoration layer that
exists on **one route**.

So the problem was never "the design system is dated." It is "the marketing page is
decorated and the product is not."

---

## 3. The synthesis

Apply **Theme B's rules** to **Theme A's palette** — the palette actually shipping.

| Theme B rule (§11) | v8 |
|---|---|
| No gradients | 0 (`verify.mjs` B) |
| No glassmorphism | 0 `backdrop-filter` |
| No glow / single subtle shadow | 1 declaration, blur 8px |
| 8px radius everywhere, no pills | `--r:8px`; max hard-coded radius 5px |
| No infinite animations | 0 CSS, 0 SMIL, 0 `@keyframes` |
| Generous typography | body 18px / 1.75 (live landing runs the app's 14px / 1.6) |
| Marketing shell 1100px | yes |

Result: **one visual language across marketing and product**, none of the
decoration. This satisfies §11's intent without a light/dark seam and without
touching the app.

---

## 4. Content is grounded, not invented

v7's specimen advertised `EpistemicStatus` (FACT / INFERRED / ASSUMED / UNKNOWN).
That enum is real — in `src/intake/packet_models.py` — and has **no UI**. Searching
the frontend for the vocabulary returns 3 files, none a UI surface.

What `/trips/trip_8b15e3f848f9/intake` actually renders:

> H1 **Trip details incomplete** → H3 *Missing customer details* → H3
> *Suggested Follow-up* → H3 *Trip Details* → H3 *Notes*

So v8's specimen uses **those exact strings**, and the copy claims only what ships:

- "it tells you which fields are still missing and the question to ask" — true.
- No FACT/INFERRED/ASSUMED/UNKNOWN anywhere in the body copy (`verify.mjs` D).
- No invented metrics — v5 shipped `'2m 14s'`, `'3'`, `'18%'` with no source. v8 has
  none, and `verify.mjs` fails on any `%` or `Nm Ns` claim.
- Flow steps cite **real routes**: Lead Inbox, Quote Review, Bookings, Documents.

The epistemic surface is logged as a **build item** (§6), not marketed as a feature.

---

## 5. What happens to v7

v7 is not deleted — this repo's rule is archive, never delete. It is retained as the
faithful Theme B implementation for the case where Pranay wants §11 done properly
(app *and* marketing migrating together). It is no longer the recommended
direction.

Nothing is retired until Pranay picks a path. That is a decision, not a default.

---

## 6. Open items for Pranay

1. **Approve "disciplined dark" as the marketing direction?** That is the fork this
   build represents.
2. **`DESIGN.md` §2 is stale** — all five background tokens drifted, two by exactly
   one step up the ramp. Fix the doc to the shipped values, or fix the code to the
   doc. Right now the spec describes a system that was replaced.
3. **Fonts.** §3 specifies IBM Plex Sans; prod loads Sora + Rubik, and
   **Outfit** (3 elements) is undocumented. Measured: Rubik 1,427 · JetBrains Mono
   88 · Sora 10 · Outfit 3 · **IBM Plex 0**. v8 matches prod, so it does not
   compound the drift — but the drift is real and needs a ruling.
4. **Build the epistemic UI, then market it.** `EpistemicStatus` +
   `AssumptionRecord` (`criticality`, `acknowledged_by_operator`) exist in the
   backend and nowhere in the frontend. This is the strongest genuine differentiator
   available and it is currently invisible.
5. **Sidebar IA.** 15 flat items mixing pipeline stages (Lead Inbox, Quote Review,
   Trips in Planning) with sections (Settings, Knowledge Base, Audit). Out of scope
   for the landing, but it is the next real usability problem.

---

## 7. Verification

`node verify.mjs` — four suites: **A** contrast against composited backgrounds,
**B** retirement of the measured 2020s patterns, **C** palette continuity with the
running app, **D** jsdom behaviour + content grounding.

**Not yet executed.** The shell in the session that produced this build failed
(exit 127 on every command, including `echo`), so the gate was hand-checked but not
run. Run one command to certify it:

```
cd frontend/design-lab/v8-disciplined-dark && node verify.mjs
```

Hand-verified during authoring: 4 real defects found and fixed —
(a) footer `h4` after `h2` skipped a heading level (now `h3`);
(b) a `mask-image` gradient in the hero violated the file's own zero-gradient
invariant (replaced with per-path `stroke-opacity` in the SVG);
(c) the progress bar read "5 of 9" but was drawn at 44% (now 55.6%, and
`verify.mjs` now ties the width to the label);
(d) `--ink-none` (3.8:1 — icon tier) was applied via `color:` to a text-bearing
element; it is now scoped to the `aria-hidden` chevron only.

---

## 8. Design references

Named, not vibes — the previous build was rejected partly for having none.

| Reference | What v8 takes |
|---|---|
| **Linear** | Dark, flat surfaces, hairline borders, zero glow, restrained blue accent |
| **Vercel** | Dark canvas, high-contrast display type, no decorative motion |
| **GitHub Primer dark** | The actual token source the app's palette drifted toward |
| **Height / Things** | Calm density; generous line-height on a product surface |
| **Stripe Dashboard** | Document-metaphor cards; one shadow layer, no elevation theatre |

Deliberately not taken: the glassmorphic blurred header, radial gradient fields,
floating glowing previews, and pill CTAs that `DESIGN.md` §8.4 specifies for
Theme A marketing — those are the patterns measured as the problem.
