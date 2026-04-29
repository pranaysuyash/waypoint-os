# Waypoint OS — Frontend Design Specification

_Source of truth: `/Docs/design/waypoint-os/wp-*.jsx` + `chat1.md`_
_Date: 2026-04-28_

---

## 0. What Is Wrong Right Now

Three root problems:

**1. B2B landing page and GTM wedge are the same page.**
`/` (the B2B sales page aimed at agency owners) and `/itinerary-checker` (the consumer-facing free tool) are different products with different audiences, different goals, and different conversion mechanics. They must be completely separate. The current `/` page promotes the itinerary checker as a section — that cannibalises the primary B2B conversion goal.

**2. The B2B landing page has ~5 sections that are not in the design.**
The pipeline diagram, workspace detail mockup, AI capabilities grid, trust grid, and wedge teaser are not in the approved design. They dilute the page and reduce its punchy single-message structure.

**3. The cockpit in the hero has static numbers.**
The design explicitly calls for animated count-up metrics (`useCountUp` hook). Without animation the hero reads as a mockup, not a live product.

---

## 1. Design Tokens

All values come from `wp-shared.jsx`. These are already in `globals.css` as CSS vars and the Tailwind config is wired. Use them exactly.

```
canvas:   #07090b   ← page background
surface:  #0d1117   ← card background
elevated: #161b22   ← raised surface, tabs
sidebar:  #0a0d11   ← sidebar background
input:    #111318   ← form inputs

t1: #e6edf3   ← primary text
t2: #8b949e   ← secondary text
t3: #6e7681   ← muted text
t4: #484f58   ← disabled / placeholder

blue:   #58a6ff
cyan:   #39d0d8
amber:  #d29922
green:  #3fb950
red:    #f85149
purple: #a371f7

b0: #21262d   ← default border
b1: #30363d   ← stronger border

fDisplay: Outfit 700/900
fBody:    Inter
fMono:    JetBrains Mono
```

**Color semantic usage:**

| Token | Use |
|-------|-----|
| `blue` | interactive, selected state, CTA secondary, info |
| `cyan` | AI, data, primary gradient endpoint |
| `amber` | warning, high-priority, at-risk |
| `green` | success, on-track, confirmed |
| `red` | critical, blocked, overdue, error |
| `purple` | AI copilot actions specifically |

---

## 2. Base Components (identical across all surfaces)

### WpBtn — 5 variants, 4 sizes

```
primary:   gradient(135deg, #7ab9ff → #57e0ef → #39d0d8), text #071018
           boxShadow: 0 8px 24px rgba(57,208,216,0.3) + inset 0 1px 0 rgba(255,255,255,0.38)
secondary: gradient(180deg, rgba(13,23,33,0.8), rgba(10,18,26,0.8)), text #e6edf3
           border: 1px solid rgba(88,166,255,0.22), borderRadius: 14px
           boxShadow: inset 0 1px 0 rgba(255,255,255,0.05)
ghost:     background rgba(15,17,21,0.72), text #c9d1d9
           border: 1px solid rgba(168,179,193,0.14)
outline:   transparent bg, text #e6edf3, border: 1px solid #30363d
danger:    background rgba(248,81,73,0.1), text #f85149
           border: 1px solid rgba(248,81,73,0.25), borderRadius: 8px

sizes:
  xs: h-28px, px-10px, text-11px, radius-full
  sm: h-34px, px-14px, text-12px, radius-full
  md: h-42px, px-20px, text-13px, radius-full
  lg: h-48px, px-24px, text-14px, radius-full
```

All buttons: `font-semibold`, `inline-flex items-center gap-7px`, `transition 160ms ease`.

### WpBadge

`text-10px font-mono uppercase tracking-wider`, `px-7px py-2px rounded-5px`, color/bg/border from `WP_C[color]`.

### WpKicker

Pill chip: `border border-[rgba(57,208,216,0.22)]`, `bg-[rgba(7,22,26,0.8)]`, `text-[#d8eef0]`,
`text-[10.5px] tracking-[0.13em] uppercase font-semibold`, with `5×5px` cyan dot
(glow: `box-shadow: 0 0 5px #39d0d8`). `mb-14px`.

### WpCard

`bg-surface`, `border border-b0`, `rounded-12px`,
`shadow: 0 2px 8px rgba(0,0,0,0.2) + inset 0 1px 0 rgba(255,255,255,0.04)`.
Optional `accent` prop adds colour glow.

---

## 3. Page: B2B Landing (`/`)

**Goal:** Get agency owners and advisors to book a demo or join the waitlist.
**Audience:** Boutique travel agency owners, solo FIT advisors, agency leads.
**Primary CTA:** Book a demo → `/signup`
**Secondary CTA:** Join waitlist (email capture, no navigation)
**Do not include:** Anything about the itinerary checker, free tools, or traveler-facing content.

### 3.1 Page shell

```
<PublicPage>       ← canvas bg + dot grid + radial gradients (already correct)
  <PublicHeader /> ← floating glass pill (already correct)
  <LandingHero />
  <LandingSections />
  <PublicFooter />
</PublicPage>
```

The `.page::before` dot grid (92×92px, opacity 0.024, masked to top) and radial gradients
are already correct in `marketing.module.css`. Keep them.

### 3.2 PublicHeader (already correct)

Floating pill, `top: 14px sticky`, `backdrop-filter: blur(24px)`, `border-radius: 24px`,
`border: 1px solid rgba(96,111,128,0.16)`.

Logo: `28×28px` rounded-8px with `gradient(135deg, #2563eb, #39d0d8)` + compass/pin SVG in white.

Nav items: Product / Solutions / For Agencies / Resources / Pricing
— `text-13px text-t2`, `px-13px py-9px`, `rounded-full`. No underlines, no active state.

Right side: `<WpBtn variant="ghost" size="sm">Sign in</WpBtn>`
         + `<WpBtn variant="primary" size="sm">Book a demo <ArrowRight /></WpBtn>`

### 3.3 LandingHero

Two-column grid: `grid-cols-[0.94fr_1.06fr]`, `gap-40`, `pt-52`, `items-center`.

**Left column — copy:**

```
<WpKicker>Built for boutique agencies</WpKicker>

<h1>  Waypoint OS
  font: Outfit 900, 68px, line-height 0.96, tracking -0.04em, color #f5fbff

<p class="subtitle">
  The operating system for boutique travel agencies.
  font: 21px/400, line-height 1.28, color t2, max-width 22ch, mb-20

<p class="body">
  From messy WhatsApp notes to client-safe proposals —
  Waypoint structures the intake, surfaces the risks, and protects your margins.
  font: 15.5px/400, line-height 1.78, color t2, max-width 44ch, mb-30

<div class="actions" gap-12 flex-wrap mb-24>
  <WpBtn variant="primary" size="lg">Book a demo <ArrowRight /></WpBtn>
  <WpBtn variant="secondary" size="lg">Explore the product</WpBtn>
  ← href="#how-it-works"

<div class="trust-chips" gap-18 flex-wrap>
  ✓ Built for travel, not generic SaaS
  ✓ End-to-end agency workspace
  ✓ AI that learns your judgment
  — checkmark color: green (#3fb950), text: 12px t3
```

**Right column — HeroCockpit:**

The CSS already has `transform: perspective(1200px) rotateY(-5deg) rotateX(2deg)`. Keep it.

**MISSING: animated count-up on the three metric numbers.**

Implement `useCountUp`:
```ts
function useCountUp(target: number, duration = 1200) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start: number | null = null;
    const step = (ts: number) => {
      if (!start) start = ts;
      const pct = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - pct, 3); // cubic ease-out
      setVal(Math.round(ease * target));
      if (pct < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return val;
}
```

The three counters (replace current static Unread/Action/Trips):
```
Active Trips  useCountUp(24, 1400)  → "24"
Revenue MTD   useCountUp(284, 1600) → "$284k"
Conversion    useCountUp(68, 1300)  → "68%"
```

**Pulsing route line at cockpit bottom:**
```css
position: absolute; bottom: -1px; left: 10%; right: 10%; height: 2px;
background: linear-gradient(90deg, transparent, rgba(57,208,216,0.6),
            rgba(88,166,255,0.4), transparent);
border-radius: 1px;
animation: routePulse 3s ease-in-out infinite;

@keyframes routePulse { 0%,100% { opacity: 1 } 50% { opacity: 0.4 } }
```

**Cockpit layout: two panels side-by-side (NOT the current 2×2 grid)**

Left panel — Inbox (3 trip rows):
```
Portugal, 12 days    | Mehta family · $18.4k  | [review]  ← red left bar
Japan, Group FIT     | Chen party · $42k       | [options] ← amber left bar
Maldives, Overwater  | Williams couple · $67.2k| [booking] ← green left bar

Row: flex items-center gap-8 padding 8px 13px border-bottom rgba(33,38,45,0.45)
Priority bar: 3×26px rounded-2px flex-shrink-0
Destination: text-12px/600/t1
Client · $value: text-10.5px/t2, value in blue/mono
Badge: WpBadge [stage color]
```

Right panel — AI Analysis:
```
Header: sparkles icon (purple) + "AI Analysis" text-10px/800/uppercase/purple

Trip label: "Portugal · Mehta" text-9.5px/700/uppercase/t3, mb-8

3 stacked mini-cards:
  Missing   | "Passport validity, room split"        | amber
  Next move | "Ask 4 Qs, build 2 option bands"      | cyan
  Owner     | "High-value repeat — review first"     | blue

Each: padding 7px 9px, bg rgba(8,10,12,0.5), rounded-7px,
      border-left: 2px solid [color], mb-6
      label: 8.5px/700/uppercase/[color] mb-1
      value: 11px/t1 line-height 1.4
```

### 3.4 Problem Bento (REPLACES current "industry contrast" section)

DELETE the `industryContrast` section entirely. Replace with:

Section: `<WpKicker>Why agencies switch</WpKicker>`
Grid: `grid-cols-[1.08fr_0.92fr]`, `gap-12`, `mt-6`

**Left — large lead card:**
```
padding: 36px 34px
border-radius: 28px
min-height: 240px
bg: gradient(135deg, rgba(16,20,25,0.97), rgba(8,13,17,0.99))
border: 1px solid b0
display: flex flex-col justify-end

<h2>
  Your best clients don't start as clean forms.
  font: Outfit 800, 36px, color #f5fbff, tracking -0.04em, line-height 1.05, mb-16

<p>
  They arrive as messy conversations. Waypoint turns that mess into the
  brief, questions, and client-ready response your team needs to win the trip.
  font: 14.5px, color t2, line-height 1.72, max-width 40ch
```

**Right — 3 stacked pain-point cards:**
```
Each: grid-cols-[auto_1fr] gap-14, padding 18px 20px, rounded-20px,
      bg rgba(13,17,23,0.92), border 1px solid b0,
      border-left: 3px solid [accent]

⇄  cyan  (#39d0d8)
  FIT requests never arrive clean
  WhatsApp notes, voice memos, screenshots — all in different places, never structured.

⚑  amber (#d29922)
  Margin leaks hide until quoting
  Visa gaps, pacing problems, DMC friction surface after advisors have already
  spent hours researching.

↻  red   (#f85149)
  Quality control breaks at scale
  Growing agencies need structured review points, not more status meetings.

Symbol: 18px, color = accent. Title: 14px/600/t1. Body: 12.5px/t2 line-height 1.55.
```

### 3.5 How It Works

Section id: `how-it-works`

```
<WpKicker>How it works</WpKicker>

<h2>  One workspace. First message to safe reply.
  font: Outfit 700, 26px, color #f5fbff, tracking -0.03em, mb-18

3-column grid, gap-12:
```

Each card: `padding 22px 20px`, `rounded-20px`, `bg rgba(13,17,23,0.92)`, `border 1px solid b0`.

Number badge: `34×34px`, `rounded-11px`, `bg #39d0d8`, `color #071014`,
`text-12px font-800`, `mb-14`.

```
[01]  Intake normalization
      Scattered notes, voice memos, and messy emails parsed into a structured
      FIT brief — travelers, constraints, budget signals, what's missing.

[02]  Risk question generation
      Waypoint surfaces the 3–5 questions that actually change the itinerary:
      visa gaps, pacing conflicts, supplier dependencies.

[03]  Owner review escalation
      High-value or high-risk trips flagged before the proposal leaves.
      Internal rationale stays private; client sees only the confident output.

Title: 15px/600/t1, mb-6. Body: 13px/t2, line-height 1.62.
```

### 3.6 Persona Cards

```
<WpKicker>Built for every role</WpKicker>

3-column grid, gap-12.
```

Each card: `padding 22px 20px`, `rounded-20px`, `bg rgba(13,17,23,0.92)`, `border 1px solid b0`,
**`border-top: 2px solid [accentColor]`** ← key detail.

```
[blue  #58a6ff]  Solo advisors
                 Move faster without turning every request into a blank-page
                 research project.
                 • Run your full pipeline in one place
                 • Save hours every week
                 • Win more, with less stress
                 [See how it helps →]

[cyan  #39d0d8]  Agency owners
                 Lead with clarity. Grow with confidence.
                 • Real-time performance and profit
                 • Coach and align your team
                 • Scale without scaling chaos

[amber #d29922]  Junior agents
                 Do your best work. Learn and grow.
                 • Guided workflows and prompts
                 • Fewer mistakes, faster ramp
                 • More confidence, more impact

Title: 15px/700/t1, mb-8.
Body: 13px/t2, line-height 1.62, mb-14.
Bullet: flex gap-5, check icon 13×13 in accent color, text-12px/t2.
CTA: flex items-center gap-4 mt-14, text-12px/600/accentColor.
```

### 3.7 CTA Band with Waitlist

Outer container:
```
padding: 36px 40px, border-radius: 26px
bg: gradient(135deg, rgba(14,22,32,0.99), rgba(8,10,12,0.99))
border: 1px solid rgba(57,208,216,0.2)
box-shadow: 0 0 80px rgba(57,208,216,0.05)
```

Layout: `flex items-start justify-between gap-40 flex-wrap`

**Left (flex 1 1 360px):**
```
<h2>  Run the next high-value inquiry through Waypoint.
  font: Outfit 700, 24px, color #f5fbff, tracking -0.02em, mb-8

<p>   See how the OS handles a real messy request —
      from inbox to client-safe output.
  font: 14px, color t2, line-height 1.65, mb-18

[Book a demo →]       WpBtn variant=primary size=md
[See a walkthrough]   WpBtn variant=secondary size=md
```

**Right — Waitlist form (flex 1 1 280px):**
```
Container: padding 22px 24px, rounded-18px,
           bg rgba(255,255,255,0.03), border 1px solid rgba(255,255,255,0.08)

Heading:  "Not ready for a demo?"           13px/600/t1
Sub:      "Join the waitlist — no pressure, no spam."  12px/t2, mb-14

Email row (flex gap-8):
  [input container flex-1: bg=input border=b1 rounded-9px padding 8px 12px gap-8]
    mail icon (color: t4) + <input placeholder="your@agency.com" text-13px>
  [WpBtn variant="primary" size="sm"]  Join

Privacy note (mt-10):
  shield icon (t4) + "No spam. Unsubscribe anytime."  text-11px/t4

Success state:
  "✓" 28px center, "You're on the list." 14px/600/t1,
  "We'll be in touch before launch." 12px/t2/mt-4
```

### 3.8 Sections to DELETE from `page.tsx`

| Section | CSS class | Why |
|---------|-----------|-----|
| Pipeline diagram | `pipelineSection` | Not in approved design |
| Workspace detail mockup | `workspaceSection` | Not in approved design |
| AI capabilities grid | `aiSection` | Not in approved design |
| Trust / operations | `trustSection` | Not in approved design |
| Wedge / itinerary checker teaser | `wedgeSection` | Wrong audience for this page |

**Final section order on `/`:**
1. PublicHeader
2. LandingHero (copy + cockpit with count-up)
3. Problem Bento (replaces industryContrast)
4. How It Works (numbered cards)
5. Persona Cards (top-border accent)
6. CTA Band with Waitlist
7. PublicFooter

---

## 4. Page: GTM Wedge (`/itinerary-checker`)

**Goal:** Travelers validate their plan for free → email captured at peak intent →
soft-convert to finding a Waypoint-powered agency advisor.
**Audience:** Travelers with a rough plan.
**No login. No agency context on the upload screen. No B2B messaging.**

### 4.1 WedgeHeader (not the same as PublicHeader)

```
padding: 14px 32px
border-bottom: 1px solid b0
bg: rgba(10,13,17,0.9), backdrop-filter: blur(12px)
layout: flex items-center justify-between

Left:
  28×28px logo: gradient(135deg, #2563eb, #39d0d8) + pin icon
  "Waypoint" 13px/700/t1 + "Itinerary Checker" 10px/t3

Right:
  "Free · No account required · Takes 60 seconds"  text-12px/t3
  [For agencies →]  WpBtn variant=ghost size=sm  href="/signup"
```

### 4.2 Upload State (the tool IS the hero — full viewport)

```
Background: radial-gradient(circle at 50% 30%, rgba(88,166,255,0.09), transparent 50%)
Layout: flex flex-col items-center justify-center h-screen padding 0 24px z-1
```

**Headline (text-center mb-36 max-width 580px):**
```
<WpKicker>Free itinerary stress-test</WpKicker>

<h1>  Find what your
      travel plan missed.
  font: Outfit 900, 52px, line-height 1.0, tracking -0.04em, color #f5fbff, mb-14

<p>   Upload your itinerary. Get a structured risk report — timing gaps,
      visa issues, pacing problems, hidden costs — in under 60 seconds.
  font: 16px, line-height 1.72, color t2, max-width 42ch, margin 0 auto
```

**Upload card (max-width 560px, w-full):**

Mode tabs:
```
Container: flex gap-4 mb-12, bg=surface rounded-10px padding=4px border=b0

[Upload file]  [Paste itinerary]  [Screenshot]
Active:   bg=elevated text=t1 font-600 rounded-7px
Inactive: bg=transparent text=t2 font-400
Each: flex-1, padding 7px 0, text-12px
```

Upload tab (default):
```
Outer: rounded-14px, border: 2px dashed b1, bg=surface, padding 36px 24px, text-center
       on drag-over: border → cyan, bg → rgba(57,208,216,0.04)

Icon zone: 48×48px rounded-14px, bg=rgba(88,166,255,0.1), border=rgba(88,166,255,0.2)
           cloud-upload SVG (22×22, stroke=blue strokeWidth=1.5), margin 0 auto mb-14

"Drop your PDF here"              text-15px/600/t1, mb-5
"PDF, JPG, PNG, or .txt up to 25MB"  text-12px/t3, mb-18
[Choose file to upload]           WpBtn variant=primary size=md
```

Paste tab:
```
Outer: rounded-14px, border=b1, bg=surface, overflow-hidden

<textarea>
  min-height: 180px, padding: 16px 18px
  bg: none, font: JetBrains Mono 13px, color t1, line-height 1.65, resize: none
  placeholder: multi-line example (Day 1: Arrive LAX → London…)

Footer bar: padding 10px 16px, border-top b0, flex justify-between items-center
  Left:  "{n} characters" or "Messy inputs work fine"  text-11px/t4
  Right: [Analyze My Itinerary →]  WpBtn variant=primary size=sm
         disabled until textarea.length > 20
```

Trust chips (mt-14, flex gap-18 justify-center):
```
✓ Free to use            green check + text-11px/t4
✓ No sign-up required
✓ Analyzed then deleted
```

Social proof strip (mt-36, flex items-center gap-24):
```
Left:  5 avatar dots (22px circles, stacked -6px, colors: blue/cyan/green/amber/purple,
       each with border: 2px solid canvas)
       + "20,000+ itineraries analyzed"  text-12px/t3

Sep:   1×16px line bg=b0

Right: ★★★★★ (amber 13px) + "4.8 / 5 from travelers"  text-12px/t3 ml-3
```

### 4.3 Results State

Same WedgeHeader. Body: `overflow-y-auto padding 28px 32px`.

**Results header — `grid-cols-[1fr_1.4fr] gap-20 mb-24`:**

Score card (left, `padding 24px 26px, rounded-20px, bg=surface, border=b0`):
```
Label: "Itinerary Health Score"  text-10px/700/uppercase/t3, mb-14

SVG ring (88×88, rotate -90deg):
  Track: r=36, stroke=b0, strokeWidth=8
  Score: r=36, stroke=amber, strokeWidth=8, strokeLinecap=round
         strokeDasharray: [2π×36×(score/100)]  [2π×36]
  Center: score number (Outfit 900, 26px, t1) + "/100" (9px/t3 mt-1)

Score label:    "Needs attention"   text-15px/600/t1, mb-5
Score summary:  short text          text-12px/t2, line-height 1.55

Count pills (flex gap-10 mt-16):
  Critical / Warnings / Heads up
  Each: flex-1, padding 8px 10px, bg=elevated, rounded-8px, text-center
        value: Outfit 800, 20px, [red/amber/blue]
        label: text-10px/t3, mt-1
```

Right column (flex flex-col gap-12):

Trip summary card (`padding 18px 20px, rounded-16px, bg=surface, border=b0, flex-1`):
```
Label: "Trip Summary (Extracted)"  text-10px/700/uppercase/t3, mb-12
2-column grid of 6 fields:
  Dates / Duration / Destinations / Travelers / Hotels / Flights
  field label: text-9.5px/600/uppercase/t4
  field value: text-12.5px/t1/mono
```

Email gate (`padding 16px 18px, rounded-14px, bg=rgba(57,208,216,0.05), border=rgba(57,208,216,0.18)`):
```
"Get your full report"                                  text-13px/600/t1, mb-3
"Detailed findings + advisor-ready brief sent to inbox."  text-11px/t2, mb-10

Input row (flex gap-8):
  [input: flex-1, bg=input, border=b1, rounded-8px, padding 8px 11px]
    mail icon (t4) + <input placeholder="your@email.com" text-12px>
  [WpBtn variant=primary size=sm]  Send →

Privacy note (mt-7): "Analyzed then deleted. Not shared. No spam."  text-10px/t4

Success state: ✓ green + "Report sent!" 13px/600/t1 + "Check your inbox…" 11px/t2
```

**Findings list (mb-24):**

Label: "Findings"  text-11px/700/uppercase/t2, mb-12

Each finding:
```
grid-cols-[auto_1fr_auto] gap-14, padding 14px 16px, rounded-12px, align-items-start

Critical  bg=rgba(248,81,73,0.06)  border=rgba(248,81,73,0.2)
Warning   bg=rgba(210,153,34,0.06) border=rgba(210,153,34,0.2)
Heads up  bg=rgba(88,166,255,0.05) border=rgba(88,166,255,0.15)

Left:   WpBadge [severity color]
Middle: title text-13.5px/600/t1 mb-3 + body text-12px/t2 line-height 1.55
Right:  "Fix it →"  text-11px/600/[accent], bg=none, border=none, cursor=pointer
```

**Agency conversion strip:**
```
padding 20px 24px, rounded-16px, bg=rgba(13,17,23,0.9), border=b0
layout: flex items-center justify-between gap-24

Left:
  "Working with a travel advisor?"    text-14px/600/t1, mb-4
  "Share this report with them directly — or find an advisor who uses
   Waypoint OS to fix these issues professionally."  text-12px/t2 line-height 1.55

Right (flex gap-8 flex-shrink-0):
  [Share report]      WpBtn variant=secondary size=sm
  [Find an advisor →] WpBtn variant=primary size=sm
```

---

## 5. App Shell

### 5.1 Sidebar (`src/components/Shell.tsx`)

```
width: 228px, bg: #0a0d11
border-right: 1px solid rgba(96,111,128,0.13)
background-image:
  radial-gradient(circle at 50% 0%, rgba(88,166,255,0.07), transparent 55%),
  radial-gradient(circle at 80% 100%, rgba(57,208,216,0.05), transparent 46%)

Brand row (h-56px, border-bottom b0, padding 0 14px):
  28×28px logo: gradient(135deg, #2563eb, #39d0d8) + pin SVG, white
                box-shadow: 0 6px 18px rgba(37,99,235,0.28), 0 0 0 1px rgba(255,255,255,0.1)
  "Waypoint"       text-13px/700/t1, tracking -0.01em
  "v2.4 · spine-v2" text-10px/t4/mono

Nav sections (padding 10px 8px):
  Section header: text-9.5px/800/uppercase/tracking-wider/t4, padding 0 8px 5px, mb-20
```

**Nav item active state — THE KEY DETAIL:**
```css
background: rgba(88,166,255,0.09);
border-left: 2px solid #58a6ff;  ← this is what makes it feel premium
color: #e6edf3;
icon color: #58a6ff;
badge: bg=rgba(88,166,255,0.18) color=blue
```

```css
/* inactive */
background: transparent;
border-left: 2px solid transparent;
color: #8b949e;
icon color: #6e7681;
badge: bg=rgba(139,148,158,0.09) color=t3
```

```
Nav sections and items:
WORK
  /inbox      Inbox           badge: unread count
  /workspace  Workspaces
  /overview   Overview

MANAGE
  /reviews    Pending Reviews  badge: count
  /analytics  Analytics
  /settings   Settings

DEV
  /workbench  Workbench

Status footer (padding 11px 14px, border-top b0):
  ● green glow + "Operations live"    text-11px/t3/mono
  ⚡ amber zap + "147ms avg · spine-v2"  text-10px/t4/mono
```

### 5.2 Command Bar

```
height: 44px, flex items-center justify-between, padding 0 18px
bg: rgba(10,13,17,0.82), border-bottom: b0, backdrop-filter: blur(12px)

Left breadcrumb:
  "Waypoint" text-12px/t4  +  "/" text-12px/b1  +  [page] text-12px/t1/500

Right:
  ⚡ amber + "ready"  text-11px/t3/mono
  [+ New trip]  WpBtn variant=primary size=xs
  Avatar: 28×28px circle, bg=elevated, border=b0, user icon t2
```

### 5.3 TripCard (`src/components/workspace/cards/TripCard.tsx`)

```
Layout: flex cursor-pointer
border-bottom: 1px solid b0
border-left: 3px solid [priority color]  ← left priority bar

Priority colors:
  critical: #f85149
  high:     #d29922
  medium:   #58a6ff
  low:      #6e7681

Row backgrounds:
  selected:      rgba(88,166,255,0.04)
  SLA breached:  rgba(248,81,73,0.025)
  default:       transparent
```

**Row 1 — destination + stage badge:**
```
Left:
  Destination: text-14px/600/t1, overflow-ellipsis
  Flag badges: WpBadge color=red text-8.5px  (e.g. "VISA GAP")
  Trip type:   text-10px/700/uppercase/tracking/t4
  • dot (2×2px t4)
  Client name: text-11px/t2

Right: WpBadge stage
  review  → red
  booking → green
  options → blue
  intake  → cyan
```

**Row 2 — metrics (THE DASHED SEPARATOR ROW):**
```
padding: 6px 0
border-top:    1px dashed rgba(33,38,45,0.6)
border-bottom: 1px dashed rgba(33,38,45,0.6)
margin: 4px 0
flex items-center gap-16

PAX   | value              | t1, sans
DATES | "Sep 14–26"        | t1, sans
VALUE | "$18.4k"           | #58a6ff, mono

Between each: 1px × 14px line bg=b0

Label: text-9px/700/uppercase/tracking/t4
Value: text-12px/500
```

**Row 3 — SLA + assignment:**
```
Left:
  WpPill dot: on_track=green/At Risk=amber/breached=red
  "[Priority] priority" text-11px/600 in priority color

Right:
  Assigned:   pill bg=elevated border=b0 text-11px/t2
  Unassigned: "Unassigned" text-10.5px/700/uppercase/amber/italic
  Trip ID:    text-9px/mono/t4
```

### 5.4 Inbox View

```
Layout: flex h-full overflow-hidden

Left: WpSidebar active="/inbox"

Right (flex-1 flex flex-col):
  WpCommandBar page="Inbox"
  Filter bar (padding 9px 18px, border-bottom b0):
    Search: flex-0-0-240px, bg=input, border=b0, rounded-8px, padding 7px 12px
            magnifier icon (#484f58) + "Search trips…" text-12px/t4
    Stage pills: All / Intake / Options / Review / Booking
                 active: bg=rgba(88,166,255,0.12) color=blue font-600, rounded-full
                 inactive: transparent t2
    Sort (ml-auto): WpPill "Priority ↓"
  Trip list (flex-1 overflow-y-auto):
    {MOCK_TRIPS.map(trip => <WpTripCard trip={trip} />)}
```

### 5.5 Workspace Detail View (3-column)

```
grid-cols-[230px_1fr_252px] h-full overflow-hidden

Col 1 — Trip list sidebar (bg=sidebar, border-right=b0, overflow-y-auto):
  Header: "Active Trips" text-9.5px/800/uppercase/t4, padding 10px 12px 8px, border-bottom b0
  Each row: flex gap-8 padding 10px 12px border-bottom b0
    3×32px priority bar (rounded-2px, flex-shrink-0, mt-2)
    Destination: text-12px/600/t1-or-t2
    Client: text-10px/t3 mt-1
    Stage badge: mt-5
  Active row: bg=rgba(88,166,255,0.08), border-left: 2px solid blue

Col 2 — Main content (overflow-y-auto, padding 20px 24px):
  Header:
    h2: Outfit 700, 22px, t1, tracking -0.02em, mb-6
    Badges: [Under review red] [Critical amber] + trip ID text-11px/mono/t4
    Actions: [Send to client outline sm] [Approve primary sm]

  Flags bar (if flags exist):
    bg=rgba(248,81,73,0.06) border=rgba(248,81,73,0.2) rounded-10px padding 10px 14px mb-18
    flex gap-16: alert icon (red) + flag text text-12px/red/500

  Tabs (border-bottom b0, mb-18):
    Analysis / Details / Timeline
    Active: 13px/600/t1 + border-bottom: 2px solid blue
    Inactive: 13px/400/t2 + border-bottom: 2px solid transparent

  Analysis tab:
    "AI Analysis" header: sparkles icon (purple) + text-11px/700/uppercase/purple, mb-14

    3-column AI cards (gap-10 mb-18):
      Missing before quote  | amber  | border-top: 2px solid amber
      Suggested next move   | cyan   | border-top: 2px solid cyan
      Owner check required  | blue   | border-top: 2px solid blue
      Each: padding 12px 14px, bg=surface, rounded-10px, border=b0
            label: text-9.5px/700/uppercase/[color] mb-5
            value: text-13px/t1 line-height 1.5

    Trip details card (WpCard):
      Header: text-10px/700/uppercase/t3, padding 10px 16px, border-bottom b0
      4-column grid (right border on cols 0-2):
        Client / Travelers / Dates / Budget
        label: text-9.5px/700/uppercase/t4 mb-4
        value: text-14px/t1 (Budget: mono + blue)

Col 3 — Activity panel (bg=sidebar, border-left=b0, padding 16px 14px, overflow-y-auto):
  "Activity" header: text-10px/700/uppercase/t4, mb-14

  Events (flex gap-10 mb-14 per event):
    Left: connector column
      7×7px dot (color = actor: purple=AI, blue=human, t3=system)
      1px line to next event
    Right:
      [Actor] (font-600 in dot color) + action text-12px/t1 line-height 1.45
      Time: text-10px/mono/t4 mt-2

  Comments section (mt-20 pt-16 border-top b0):
    "Comments" text-10px/700/uppercase/t4, mb-10
    Input field: flex gap-8 padding 9px 10px bg=input border=b0 rounded-9px
      msg icon (t4) + "Add a note…" text-12px/t4
```

---

## 6. File Change Map

```
src/app/page.tsx
  - Delete: pipelineSection, workspaceSection, aiSection, trustSection, wedgeSection
  - Replace: industryContrast → problem bento
  - Rewrite: CTA band → add waitlist form

src/app/itinerary-checker/page.tsx
  - Full rewrite: tool-first hero (WedgeUpload), results view (WedgeResults)
  - Replace PublicHeader with WedgeHeader (new stripped component)

src/components/marketing/MarketingVisuals.tsx
  - AgencyHeroCockpit:
      Add useCountUp hook
      Fix metrics: Active Trips / Revenue MTD / Conversion (not Unread/Action/Trips)
      Fix layout: 2 panels (inbox + AI analysis), not 2×2 grid
      Add pulsing route line at bottom

src/components/marketing/marketing.module.css
  - Remove CSS for deleted sections

src/components/Shell.tsx
  - Nav active state: border-left 2px solid #58a6ff + bg-[rgba(88,166,255,0.09)]

src/components/workspace/cards/TripCard.tsx
  - Add dashed metric separator row (border-top/bottom: 1px dashed)
  - Left priority bar (border-left: 3px solid [priority color])
```

---

## 7. Do Not Touch

- `globals.css` — radial gradients and dot grid are correct
- `tailwind.config.js` — token mapping is correct
- `PublicFooter` — no changes
- `SuitabilitySignal`, `DecisionPanel`, `IntakePanel`, `TimelinePanel` — workspace panels, not marketing

---

## 8. Implementation Order (highest impact first)

| # | Change | File | Effort |
|---|--------|------|--------|
| 1 | AgencyHeroCockpit: count-up + 2-panel layout + route pulse | MarketingVisuals.tsx | 15 min |
| 2 | `/` page: delete 5 sections + problem bento + waitlist CTA | page.tsx | 30 min |
| 3 | Shell nav active state (border-left) | Shell.tsx | 5 min |
| 4 | TripCard: dashed row + priority bar | TripCard.tsx | 20 min |
| 5 | `/itinerary-checker`: full tool-first rewrite | itinerary-checker/page.tsx | 1–2 hrs |
