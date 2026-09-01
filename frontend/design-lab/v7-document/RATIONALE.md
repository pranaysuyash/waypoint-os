# v7 — Landing page, Theme B "Minimalist Document"

**Status:** prototype for validation · **Date:** 2026-08-31
**Location:** `frontend/design-lab/v7-document/`
**Touches nothing live.** `src/app/page.tsx` still renders `landing-v5`.

---

## 0. Why the previous attempt was rejected

My first pass (`_archive/v6-atlas-rejected-20260831/`) built a design system that
does not exist in this repo: warm paper `#F7F4ED`, vermilion `#C8462A`, Fraunces.
It was rejected for three reasons, and the third was the real one:

1. **I read 120 of 1112 lines** of `frontend/DESIGN.md` before designing.
2. I leaned on `frontend-design`'s "avoid generic AI aesthetics" directive and
   let it outrank the product's own spec.
3. **I forked the canonical artifact.** The repo rule is *no duplicate or
   parallel systems — extend canonical routes.* A third theme is the exact
   opposite of that.

The irony worth recording: v6 was ~90% of the way to a theme that **already
exists in your spec** and I substituted my own taste for the last 10%. A
near-duplicate fork is worse than an obviously different direction, because it
looks deliberate.

v6 is archived, not deleted. It is not a candidate.

---

## 1. The actual finding: the cure is already in your spec

`DESIGN.md` defines **two** themes, not one.

| | Theme A "Cartographic Dark" | Theme B "Minimalist Document" |
|---|---|---|
| Spec'd | §2 | §2, §11 |
| Built in code | ✅ everywhere | ❌ **nowhere** |

The live landing page is Theme A. Read what §8.4 asks Theme A marketing to be:

> - Page bg: **Complex layered radial gradients + grid overlay**
> - Header: Sticky **glassmorphic** bar (`backdrop-filter: blur(24px)`, gradient bg, heavy shadow)
> - Hero: …**floating UI preview with glow effects, animated scene nodes**
> - Cards: `rounded-[22px]` to `rounded-[24px]`
> - Shadows: Heavy, multi-layer

**That is a literal description of the 2020–2022 SaaS aesthetic.** "Reads like
early 2020s" is not a bug in the execution — it is the spec being followed
correctly. The page looks dated because Theme A marketing *is* dated.

§8.4 also specifies the alternative, and §11 §Migration lists it as step 5:

> **Create marketing variant — a second set of marketing CSS modules without
> gradients/glows**

That step has never been done. **This prototype is that step.** It is not a new
design system; it is the second half of the one you already wrote.

### Two drifts found while verifying

| Spec | Live code |
|---|---|
| §3 Fonts: **IBM Plex Sans** + JetBrains Mono | `layout.tsx:2` loads **Sora + Rubik**; `grep -r "IBM_Plex" src/` → **0 hits** |
| §12 CSS variables for theme switching | `grep -n "data-theme" globals.css` → **0 hits**; Theme B tokens do not exist |

Neither is a v7 problem, but both need a decision. See §7.

---

## 2. Design references

Named, external, and chosen because they constrain the same problem — not
because they are trendy. (This is the part I skipped last time.)

| Reference | What it governs here | Source |
|---|---|---|
| **IBM Carbon Design System** | IBM Plex is Carbon's typeface. Since §3 specifies Plex, Carbon is the canonical body of guidance for how to *use* it — scale, weight discipline, tabular figures, restrained accent use. | `carbondesignsystem.com/elements/typography/overview/` |
| **Linear** | The reference for restraint as a product position: hairline borders, one accent, no decorative motion, density earned through alignment rather than colour. Closest working precedent for "calm software that still feels expensive." | `linear.app/now/how-we-redesigned-the-linear-ui` |
| **Swiss International Style** (Müller-Brockmann) | The historical root of "Minimalist Document": grid discipline, flush-left/ragged-right, type as the primary hierarchy device, ornament as failure. §11's "generous leading + hairline + flat colour" is Swiss. | — |
| **37signals / Basecamp** | Plain-language marketing: single-column, big type, specific claims, no hero video, no gradient mesh. Directly the model for the copy register used here. | — |
| **Vercel Web Interface Guidelines** | The objective checklist this was audited against (see §5). | `github.com/vercel-labs/web-interface-guidelines` |

**What was deliberately *not* referenced:** the current AI-default marketing
register — serif display + terracotta/vermilion + grain overlay. Using it would
have reproduced the "slop" complaint in a different font.

---

## 3. What changed, and why

### Removed (Theme B forbids all of these — §11)
- 4 radial-gradient glow blobs + 92px grid overlay (`landing-v5.module.css:1–24`)
- Glassmorphic header — `backdrop-filter: blur(24px)` (`:38–46`) → solid `#fff`
- Gradient CTA (`:336`) → solid Royal Blue `#2563eb`
- Uppercase letterspaced kickers at `:217`, `:273`, `:493` → 11px / `0.05em`, per §3
- `rounded-[24px]` marketing-only radius → **8px**, unified with app (§11)
- Multi-layer shadows → single `0 2px 8px rgba(0,0,0,.06)`
- Both infinite animations: `ribbon-dash 12s linear infinite` (`:173`),
  `ribbon-breathe 4.8s ease-in-out infinite` (`:182`)

### Added
- **The specimen** — the page's centrepiece is a working model of the product's
  actual differentiator, not a decorative screenshot. See §4.
- **1px geometric line art** in the hero. §2 explicitly authorises this for
  Theme B: *"Hero background: Archive White with subtle geometric line art (1px
  Hairline) instead of gradients."* Visual interest comes from your spec, not
  from invention. Drawn once on entry, never loops.
- `text-wrap: balance`, `font-variant-numeric: tabular-nums`, `env(safe-area-inset-*)`,
  skip link, `scroll-margin-top`, `color-scheme: light`, `translate="no"` on the brand name.

### Copy
v5 carried invented metrics (`'2m 14s'`, `'3'`, `'18%'`) and defensive framing
("Not a prettier CRM."). Both are credibility costs. v7 asserts **no numbers it
cannot support** and replaces defence with a "not a good fit if" column, which
converts better precisely because it is willing to disqualify.

---

## 4. The specimen is the product, not a mockup

Every chip maps to a real enum in `src/intake/packet_models.py`:

```python
class EpistemicStatus(StrEnum):
    FACT = "FACT"; INFERRED = "INFERRED"; ASSUMED = "ASSUMED"; UNKNOWN = "UNKNOWN"
```

and every expanded panel exposes real `AssumptionRecord` fields:

```python
rationale: str
criticality: Literal["critical", "preference", "advisory"]
acknowledged_by_operator: bool
```

Verified against the file, not assumed. `verify.mjs` asserts the page can only
render those four statuses — so if the enum changes, the prototype fails loudly
rather than drifting.

The UNKNOWN row is the argument: it stays **empty** and offers the question
you'd have asked anyway, with a copy button. A generic LLM summariser fills that
field with a confident guess. The product refusing to guess is the product.

---

## 5. Verification — `node verify.mjs` → **50 passed, 0 failed**

Tokens are parsed out of `index.html`, so the audit cannot drift from the file.

### Contrast (WCAG 2.1 AA)
Checked against **actual composited backgrounds** — each `--wash-*` composited
over its real parent — not against the base surfaces. This matters: two
combinations pass on `#ffffff` and fail on the tint actually beneath them.

| Token | Value | Worst | On |
|---|---|---|---|
| `--ink` | `#1a1a1a` | 15.99 | body |
| `--graphite` | `#4a4a4a` | 8.14 | body copy |
| `--ink-muted` | `#666666` | 4.86 | labels |
| `--royal` | `#2563eb` | 4.75 | links |
| `--royal` | `#2563eb` | 4.77 | inferred chip |
| `--royal-dark` | `#1d4ed8` | 5.67 | step number |
| `--amber-ink` | `#a35a04` | 4.79 | assumed / unknown chip |
| `--forest-ink` | `#047857` | 5.00 | fact chip |
| `--error-ink` | `#b91c1c` | 5.45 | criticality |
| white on `--royal` | — | 5.17 | primary button |

### Four tokens had to be derived. The canonical ones fail.

This is a defect in `DESIGN.md`, not in the prototype. Flagging rather than
silently patching:

| Canonical | As text | Problem | Derived | Now |
|---|---|---|---|---|
| `#6b6b6b` Lead Gray | 4.24:1 on Selected Sheet | fails AA | `--ink-muted` `#666666` | 4.57 |
| `#d97706` Warm Amber | 3.19:1 | fails AA | `--amber-ink` `#a35a04` | 4.80 |
| `#059669` Forest Green | 3.77:1 | fails AA | `--forest-ink` `#047857` | 5.04 |
| `#dc2626` Error Red | 4.07:1 on red wash | fails AA | `--error-ink` `#b91c1c` | 5.45 |

`#9a9a9a` Silver Gray is 2.59:1 — §2 assigns it to "timestamps, placeholders,
disabled," all of which are text. **It cannot be used as specified.** Left in
the file as decorative-only, guarded by an assertion.

`--royal-dark` `#1d4ed8` and `--error-ink` `#b91c1c` are not new colours — both
are already in §4 as Theme B hover states.

**Encoded constraint:** accent-coloured text may sit only on `--archive`,
`--card`, or a `--wash-*` over those. `--hovered`/`--selected` are 4.11–4.46:1
against the accents. If you move accent text onto a hovered surface,
`verify.mjs` fails. That is the point of the test.

### Behaviour (jsdom)
Structure · single `h1`, hierarchical headings, skip link, every button has
accessible text, no inline `onclick`. Accordion · ARIA `expanded`/`controls`,
one-open-at-a-time. Copy · `aria-live="polite"` status. Reveal · hidden before
intersect, revealed on, **unobserved after** (one-shot). Degradation · without
`IntersectionObserver` everything renders visible and the accordion still
works. Reduced motion · all content visible immediately, line art not
dash-hidden, **zero observers constructed**. Cleanup · listeners, observers and
timers released on `pagehide`.

### Audit of the live v5, for contrast
| Check | v5 | v7 |
|---|---|---|
| Infinite CSS animations | 2 | 0 |
| SVG SMIL loops | **2** (`landing-v5.tsx:292,298`) | 0 |
| SMIL covered by `prefers-reduced-motion` | **No** — CSS `animation: none` does not stop SMIL | n/a |
| Gradients | many | 0 |
| `backdrop-filter` | yes | 0 |
| `text-wrap: balance` | ✅ present (`:291`, `:411`) | ✅ |
| `tabular-nums` | absent | ✅ |
| `prefers-reduced-motion` | ✅ present (`:726`) | ✅ |

Credit where due: v5 already handles reduced motion and text balancing. Its
specific gap is the two `animateMotion` elements, which its own media query
cannot reach.

---

## 6. Skills applied

| Skill | Where it is load-bearing |
|---|---|
| `web-design-guidelines` | Guidelines fetched live; drove the antipattern scan, ARIA, typography and touch rules. `verify.mjs` encodes ~20 of them as assertions. |
| `optimize-web-animations` | No infinite motion anywhere; `IntersectionObserver` gates the reveal and the line art; one-shot + `unobserve`; full teardown on `pagehide`; motion gated at source under reduced motion rather than merely shortened. |
| `web-interactive-storytelling` | Narrative arc — thread → gap → mechanism → fit → ask. The specimen is progressive disclosure: collapsed list, per-field drilldown, question on demand. |
| `frontend-design` | Applied as *craft*, not as licence to invent. Its own rule is intentionality, and here the intentional act is executing a specified system precisely. Restraint is the differentiator. |

---

## 7. Open items for you

1. **Theme B for marketing — approve?** This is §11 migration step 5. Nothing
   here changes the app shell; it only adds the marketing variant.
2. **Fonts.** §3 says IBM Plex Sans; `layout.tsx` loads Sora + Rubik; IBM Plex
   appears nowhere in `src/`. Either the spec or the code is wrong. v7 uses Plex
   per spec — say the word and I'll flip it.
3. **Theme switching is unimplemented.** No `data-theme` in `globals.css`, so
   Theme B tokens have nowhere to live. Recommended: add the
   `[data-theme="minimalist"]` block from §10, then port.
4. **The four contrast defects in §2** should be fixed at the source in
   `DESIGN.md`, not absorbed downstream.
5. **No metrics on the page.** If you have real ones, I'll add them; I won't
   invent them.

---

## 8. Port plan + retirement gate

The repo has `src/app/v2/`, `v3/`, `v4/`, `v5/` — four parallel landing
generations, none retired. That is the duplication defect in §1, and the reason
to gate this rather than add a `v6/`.

**Port (on approval):**
1. Add `[data-theme="minimalist"]` tokens to `globals.css` (§10 block).
2. Add the four derived tokens with a comment pointing here.
3. Port as CSS Modules into `src/components/marketing/` — extend the existing
   `marketing.module.css` primitive set; do not fork it.
4. Wire the specimen to real intake output rather than the fixture.
5. Delete the four derived tokens from the prototype once they live in `globals.css`.

**Retirement gate — the control this repo is missing:**
> No new canonical path merges without a deletion date for the one it replaces.

Concretely: this landing page goes live at `src/app/page.tsx` (replacing
`landing-v5`, not sitting beside it), and `v2/`–`v5/` get a dated removal
commit in the same change. Otherwise v7 becomes v8's predecessor.
