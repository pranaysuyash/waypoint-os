# Design System: Waypoint OS
**Project:** AI-powered travel agency decision support system  
**Frontend Stack:** Next.js 15, React 19, Tailwind CSS, TypeScript  
**Primary Theme:** Cartographic Dark — precise, instrument-grade, spatially aware  
**Secondary Theme:** Minimalist Document — clean, Swiss-inspired, editorial light

---

## Table of Contents

1. [Visual Theme & Atmosphere](#1-visual-theme--atmosphere)
2. [Color Palette & Roles](#2-color-palette--roles)
3. [Typography Rules](#3-typography-rules)
4. [Component Stylings](#4-component-stylings)
5. [Layout Principles](#5-layout-principles)
6. [Animation & Motion](#6-animation--motion-principles)
7. [Accessibility Foundations](#7-accessibility-foundations)
8. [Page Patterns](#8-page-patterns)
9. [Component Usage Examples](#9-component-usage-examples)
10. [Tailwind Plugin Config](#10-tailwind-plugin-configuration)
11. [Theme B: Minimalist Document](#11-theme-b-minimalist-document)
12. [File Reference](#12-file-reference)

---

## 1. Visual Theme & Atmosphere

### Theme A: Cartographic Dark (Current)

Waypoint OS embodies a **"Cartographic Dark"** aesthetic — the visual language of precision navigation instruments merged with modern SaaS density. The interface feels like operating a high-end flight deck or maritime chart plotter: every pixel serves wayfinding, every color encodes state, and every surface layers information with cartographic clarity.

**Mood & Density:**
- **Dense but breathable** — information-rich interfaces (trip cards, workbenches, analytics) use tight packing with clear hierarchical separation
- **Instrumental seriousness** — no playful decoration; credibility and operational urgency dominate
- **Spatial awareness** — geographic metaphors permeate the color system (land, water, route, waypoint, destination)
- **Two modes of expression:**
  - *App Shell:* Utilitarian, compact, high-contrast-for-readability — operators spend hours here
  - *Marketing/Public Pages:* Dramatic, atmospheric, glassmorphic — cinematic depth with animated gradient fields, grid overlays, and floating UI artifacts

**Atmosphere keywords:** Night-mode chart plotter, mission control, precision instrument, cold efficiency, spatial cognition

### Theme B: Minimalist Document (Alternative)

A complete alternative visual system that preserves the same information architecture and component structure but replaces the cartographic instrument metaphor with an **editorial document** aesthetic. Inspired by Swiss design, Kinopio, and Linear's lighter moments — think of working on a clean desk with well-organized folders rather than operating a flight deck.

**Mood & Density:**
- **Airy and deliberate** — 30–50% more whitespace per screen. Information is given room to breathe
- **Editorial warmth** — off-white and warm gray tones replace cold blacks. The feeling is "paper on a clean desk" not "screen in a dark room"
- **Restrained color discipline** — reduced from 7 accent colors to 3 functional accents (blue for action, amber for attention, green for confirmation)
- **No atmospheric effects** — no radial gradients, no glows, no glassmorphism, no animated backgrounds
- **Uniform across app and marketing** — the same calm, document-like aesthetic applies to both the operational shell and public pages

**Atmosphere keywords:** Clean desk, editorial layout, Swiss precision, warm minimalism, document-first

---

## 2. Color Palette & Roles

### Theme A: Cartographic Dark

The palette is organized into semantic layers that mirror cartographic conventions. All colors are chosen for WCAG AA compliance on the dark canvas.

#### Backgrounds — The Cartographic Layers
| Descriptive Name | Hex | Functional Role |
|---|---|---|
| **Deep Space Canvas** | `#080a0c` | Primary page background — the "ocean" of the interface |
| **Chart Surface** | `#0f1115` | Secondary surfaces — cards, panels, input backgrounds |
| **Elevated Terrain** | `#161b22` | Elevated surfaces — hovered rows, active states, dropdown menus |
| **Highlight Ridge** | `#1c2128` | Subtle highlights — selected items, table row hovers |
| **Input Bunker** | `#111318` | Dedicated input field backgrounds |

#### Text — The Signal Hierarchy
| Descriptive Name | Hex | Contrast on Canvas | Role |
|---|---|---|---|
| **Polar Star White** | `#e6edf3` | 15.4:1 | Primary text — headings, body, critical labels |
| **Fog Gray** | `#a8b3c1` | 5.2:1 | Secondary text — descriptions, metadata, timestamps |
| **Mist Gray** | `#9ba3b0` | ~4.5:1 | Tertiary text — captions, helper text |
| **Distant Shore** | `#8b949e` | 3.9:1 | Muted text — for large text only, section labels |

#### Accents — State & Action Encoding
| Descriptive Name | Hex | Role |
|---|---|---|
| **Azimuth Blue** | `#58a6ff` | Primary actions, links, focus rings, active navigation |
| **Signal Green** | `#3fb950` | Success states, on-track SLA, completion badges |
| **Caution Amber** | `#d29922` | Warnings, at-risk states, pending reviews |
| **Alert Red** | `#f85149` | Errors, breached SLA, critical alerts, destructive actions |
| **Waypoint Cyan** | `#39d0d8` | Geographic routes, processing animations, pipeline flows |
| **Intelligence Purple** | `#a371f7` | Derived data badges, manual overrides, agent-generated signals |
| **Sunset Orange** | `#ff9248` | Secondary highlights, warm geographic accents |

#### Geographic Colors
| Descriptive Name | Hex | Role |
|---|---|---|
| **Land Mass** | `#1c2128` | Geographic land representation |
| **Deep Water** | `#0d2137` | Water bodies, inactive regions |
| **Active Route** | `#39d0d8` | Live paths, connections, pipeline flows |
| **Dim Route** | `#1a3a3f` | Inactive or historical route segments |
| **Waypoint Marker** | `#d29922` | Intermediate stops, checkpoints |
| **Destination Beacon** | `#3fb950` | Final goals, completed destinations |

#### Borders — Contour Lines
| Descriptive Name | Hex | Role |
|---|---|---|
| **Default Contour** | `#30363d` | Standard borders — card outlines, dividers |
| **Hover Contour** | `#8b949e` | Elevated borders on hover |
| **Active Contour** | `#58a6ff` | Focused or active borders |
| **Route Glow** | `rgba(57, 208, 216, 0.3)` | Subtle cyan borders for route-related elements |

#### Marketing Gradients (Atmospheric Only)
- **Primary glow:** `radial-gradient(circle at 12% 8%, rgba(88, 166, 255, 0.24), transparent 24%)`
- **Cyan accent glow:** `radial-gradient(circle at 88% 6%, rgba(57, 208, 216, 0.14), transparent 22%)`
- **Brand mark gradient:** `linear-gradient(135deg, #2563eb, #39d0d8)`
- **Primary CTA gradient:** `linear-gradient(135deg, #7ab9ff 0%, #57e0ef 52%, #39d0d8 100%)`

---

### Theme B: Minimalist Document

A reduced, warm palette built on off-white and charcoal. The same semantic roles exist but with far fewer colors and no decorative gradients.

#### Backgrounds — The Paper Layers
| Descriptive Name | Hex | Functional Role |
|---|---|---|
| **Archive White** | `#f7f5f2` | Primary page background — warm off-white, like quality paper |
| **Card Stock** | `#ffffff` | Secondary surfaces — cards, panels, modals |
| **Hovered Sheet** | `#f0eeea` | Elevated surfaces — hovered rows, active dropdowns |
| **Selected Sheet** | `#e8e5e0` | Selected items, table row hovers, focused sections |
| **Input Field** | `#ffffff` | Input backgrounds — pure white for clarity |
| **Sidebar Canvas** | `#f0eeea` | Navigation sidebar background — slightly darker than page |

#### Text — The Type Hierarchy
| Descriptive Name | Hex | Contrast on Archive | Role |
|---|---|---|---|
| **Ink Black** | `#1a1a1a` | 16:1 | Primary text — headings, body, critical labels |
| **Graphite** | `#4a4a4a` | 8:1 | Secondary text — descriptions, metadata |
| **Lead Gray** | `#6b6b6b` | 5:1 | Tertiary text — captions, helper text |
| **Silver Gray** | `#9a9a9a` | 3:1 | Muted text — timestamps, placeholders, disabled |

#### Accents — Reduced to Three
| Descriptive Name | Hex | Role |
|---|---|---|
| **Royal Blue** | `#2563eb` | Primary actions, links, focus rings, active navigation |
| **Warm Amber** | `#d97706` | Warnings, at-risk states, attention required |
| **Forest Green** | `#059669` | Success states, confirmations, on-track indicators |

#### Borders — Hairline Precision
| Descriptive Name | Hex | Role |
|---|---|---|
| **Hairline** | `#e5e2dd` | Standard borders — card outlines, dividers, table borders |
| **Hover Line** | `#c4c0b8` | Elevated borders on hover |
| **Focus Line** | `#2563eb` | Focused or active borders |
| **Error Line** | `#dc2626` | Error states — red used sparingly, only for errors |

#### State Surfaces (Subtle Backgrounds)
- **Green:** `rgba(5, 150, 105, 0.08)` bg + `rgba(5, 150, 105, 0.2)` border
- **Amber:** `rgba(217, 119, 6, 0.08)` bg + `rgba(217, 119, 6, 0.2)` border
- **Red:** `rgba(220, 38, 38, 0.06)` bg + `rgba(220, 38, 38, 0.15)` border
- **Blue:** `rgba(37, 99, 235, 0.06)` bg + `rgba(37, 99, 235, 0.15)` border
- **Neutral:** `rgba(0, 0, 0, 0.04)` bg + `rgba(0, 0, 0, 0.08)` border

#### Marketing Palette (No Gradients)
- **Primary CTA:** Solid Royal Blue (`#2563eb`) with white text
- **Secondary CTA:** White background, Hairline border, Ink Black text
- **Hero background:** Archive White with subtle geometric line art (1px Hairline) instead of gradients
- **Brand mark:** Solid Royal Blue square with white icon — no gradients, no glows

---

## 3. Typography Rules

### Font Families (Shared Across Themes)
- **Display / UI:** IBM Plex Sans (weights: 400, 500, 600, 700) — clean, technical, highly legible at small sizes
- **Monospace / Data:** JetBrains Mono — code, timestamps, trip IDs, metric values
- **Data alternate:** IBM Plex Mono — tabular data, financial figures

### Type Scale (Shared)
| Token | Size | Role |
|---|---|---|
| **xs** | 12px | Minimum readable — captions, badges, micro-labels |
| **sm** | 14px | Secondary text, metadata, card descriptions |
| **base** | 16px | Body text — WCAG recommended minimum |
| **md** | 18px | Emphasized body, subheadings |
| **lg** | 20px | Small headings, section titles |
| **xl** | 22px | Medium headings |
| **2xl** | 24px | Large headings |
| **3xl** | 28px | Extra large headings |
| **4xl** | 32px | Display text, page titles |
| **Hero** | clamp(52px, 6vw, 80px) | Marketing hero titles |

### Typography Character

**Theme A (Cartographic):**
- Tight leading for headings (1.0–1.25) to create density and authority
- Relaxed leading for body (1.5–1.82) for readability
- Negative letter-spacing on large display type (-0.065em)
- Uppercase + wide tracking for section labels (0.1–0.14em)
- Tabular figures for all monetary values and IDs

**Theme B (Minimalist):**
- Generous leading for headings (1.2–1.35) — breathing room is the point
- Comfortable leading for body (1.6–1.75)
- Slight negative letter-spacing on display only (-0.02em)
- Uppercase + moderate tracking for labels (0.05em) — less aggressive
- Tabular figures for monetary values and IDs (unchanged)

---

## 4. Component Stylings

### Buttons

**Theme A (Cartographic):**
| Variant | Background | Text | Border | Hover |
|---|---|---|---|---|
| Primary | Azimuth Blue | Near-black (#0d1117) | None | Lighten to `#6eb5ff` |
| Secondary | Elevated Terrain | Polar Star | Default Contour | Highlight Ridge + Hover Contour |
| Ghost | Transparent | Fog Gray | None | Elevated Terrain bg |
| Destructive | Alert Red | White | None | Lighten to `#ff6b63` |
| Outline | Transparent | Polar Star | Default Contour | Elevated Terrain bg |

**Shape:** `rounded-lg` (8px) for app. Marketing CTAs use `rounded-full` (pill).
**Sizes:** sm (28px), md/default (32px), lg (40px), icon (32px square).

**Theme B (Minimalist):**
| Variant | Background | Text | Border | Hover |
|---|---|---|---|---|
| Primary | Royal Blue | White | None | Darken to `#1d4ed8` |
| Secondary | Card Stock | Ink Black | Hairline | Hovered Sheet bg |
| Ghost | Transparent | Graphite | None | `rgba(0,0,0,0.04)` bg |
| Destructive | Error Red | White | None | Darken to `#b91c1c` |
| Outline | Transparent | Ink Black | Hairline | `rgba(0,0,0,0.04)` bg |

**Shape:** `rounded-md` (6px) universally — no pills, no dramatic rounding.
**Sizes:** Same heights but with slightly more horizontal padding for breathing room.

### Cards / Containers

**Theme A:**
- **Default:** Chart Surface bg, Default Contour border, `rounded-xl` (12px)
- **Elevated:** Elevated Terrain bg, medium shadow, same border
- **Bordered:** Chart Surface bg with stronger border
- **Ghost:** Transparent bg

**Theme B:**
- **Default:** Card Stock bg, Hairline border, `rounded-lg` (8px) — smaller radius, softer
- **Elevated:** Card Stock bg, subtle shadow (`0 2px 8px rgba(0,0,0,0.06)`), Hairline border
- **Bordered:** Card Stock bg with slightly stronger border
- **Ghost:** Transparent bg
- **No glow effects** — glow utilities removed entirely

### Inputs / Forms

**Theme A:**
- Background: Input Bunker or Chart Surface
- Border: Default Contour, `rounded-md` (6px)
- Text: Polar Star White
- Placeholder: Distant Shore (`#484f58`)
- Focus: 2px Azimuth Blue ring with 2px offset
- Error: Alert Red border + focus ring + error text

**Theme B:**
- Background: Input Field (pure white)
- Border: Hairline, `rounded-md` (6px)
- Text: Ink Black
- Placeholder: Silver Gray (`#9a9a9a`)
- Focus: 2px Royal Blue ring with 2px offset (offset color: Archive White)
- Error: Error Red border + focus ring + error text
- **Difference:** Inputs feel like they sit ON the surface rather than recessed INTO it

### Badges / Chips

**Theme A:** State surface system with `rounded-md` (6px) for app, `rounded-full` for marketing.

**Theme B:** Same state surface system but with Theme B colors. All badges use `rounded-md` (6px) — no pills. Typography: 11px medium weight, uppercase with 0.05em tracking (less aggressive than Theme A's 0.1em).

### Tabs

**Theme A:** Bottom border of Default Contour. Active tab gets Azimuth Blue underline (2px). Inactive: Distant Shore text, hover raises to Highlight Ridge.

**Theme B:** Bottom border of Hairline. Active tab gets Royal Blue underline (2px) + Ink Black text. Inactive: Lead Gray text, hover raises to Hovered Sheet. Same keyboard navigation support.

### Loading / Skeleton

**Theme A:** Highlight Ridge skeleton background, pulse animation. Spinner uses accent colors on transparent top.

**Theme B:** `rgba(0,0,0,0.06)` skeleton background, pulse animation. Spinner uses Royal Blue on transparent top. Loading overlay: `rgba(247, 245, 242, 0.8)` with `backdrop-blur-sm`.

---

## 5. Layout Principles

### Spatial System (Shared)
Spacing follows a 4px base grid:

| Token | Value | Usage |
|---|---|---|
| **space-1** | 4px | Tight internal padding, icon gaps |
| **space-2** | 8px | Tight component gaps |
| **space-3** | 12px | Small component padding |
| **space-4** | 16px | Standard padding |
| **space-5** | 20px | Medium section gaps |
| **space-6** | 24px | Large section padding |
| **space-8** | 32px | Section separations |
| **space-10** | 40px | Major section margins |
| **space-12** | 48px | Page-level padding |
| **space-16** | 64px | Hero section padding (Theme B) |
| **space-20** | 80px | Major page breaks (Theme B) |

### Shell Architecture

**Theme A (Cartographic Sidebar):**
- **Sidebar:** 72px collapsed / 220px expanded. Deep Space Canvas bg with Default Contour right border. Brand mark (gradient square), navigation sections (OPERATE, GOVERN, TOOLS), system status footer with pulse dot
- **Command Bar:** 44px height, sticky top. Backdrop blur (`backdrop-blur-xl`). Breadcrumb + user controls
- **Main Content:** Flex-1, scrollable. Max-width 1400px for wide layouts
- **Integrity Banner:** Full-width Alert Red bar for critical warnings

**Theme B (Minimalist Sidebar):**
- **Sidebar:** 72px collapsed / 240px expanded. Sidebar Canvas bg with Hairline right border. Brand mark (solid blue square), navigation sections with more vertical padding (16px between items vs 8px), no system status footer — status shown in command bar only
- **Command Bar:** 48px height, sticky top. No backdrop blur — solid Card Stock bg with Hairline bottom border. Breadcrumb + user controls
- **Main Content:** Flex-1, scrollable. Max-width 1200px — tighter, more focused reading width
- **Integrity Banner:** Full-width warm amber bar with Ink Black text

### Grid & Content Width

**Theme A:**
- App max-width: 1400px
- Marketing shell: 1320px centered
- Marketing hero: Asymmetric two-column (1.04fr / 0.96fr) with 54px gap
- Cards: Responsive 1–3 columns

**Theme B:**
- App max-width: 1200px — tighter focus
- Marketing shell: 1100px centered — editorial column width
- Marketing hero: Single column centered, generous top/bottom padding (120px+), max-width 800px for text
- Cards: Responsive 1–2 columns — never more than 2 side-by-side for focus

### Whitespace Strategy

**Theme A:**
- App pages: Tight, efficient. 16–24px section gaps. High information density
- Marketing pages: Generous, cinematic. 72px+ section padding. Asymmetric layouts
- Trip cards / inbox: Ultra-dense with progressive disclosure

**Theme B:**
- App pages: Generous, calm. 24–40px section gaps. Same information but with more breathing room
- Marketing pages: Very generous. 120px+ section padding. Centered, single-column focus
- Trip cards / inbox: Medium density — same content, 20% more internal padding per card

### Responsive Behavior (Shared)
- Mobile nav: Sidebar collapses to icon-only mode
- Breakpoints: sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px
- Touch targets: Minimum 44x44px

### Scrollbar Design

**Theme A:** Custom thin scrollbar (8px). Track: transparent. Thumb: Default Contour, rounded. Hover: Hover Contour.

**Theme B:** System default scrollbar — no custom styling. The minimal aesthetic respects native OS chrome.

---

## 6. Animation & Motion Principles

### Transition Timing (Shared)
| Name | Duration | Usage |
|---|---|---|
| Fast | 150ms | Hover states, color changes, opacity shifts |
| Base | 200ms | Standard UI feedback |
| Slow | 300ms | Larger state changes, panel reveals |

### Key Animations

**Theme A (Instrumental Motion):**
- **Pulse dot:** 2s infinite opacity pulse — live indicators
- **Node processing:** 1.5s ease-out infinite — cyan box-shadow radiating outward
- **Route pulse:** 2s ease-in-out infinite — opacity breathing for active routes
- **Fade-in:** 0.2s ease-out + 8px upward translate — content appearance
- **Slide-in-left:** 0.2s ease-out + 12px horizontal translate — sidebar content
- **Float:** 3s ease-in-out infinite — gentle vertical oscillation for decorative elements

**Theme B (Subtle Motion):**
- **Fade-in:** 0.2s ease-out + 4px upward translate — gentler, shorter distance
- **Slide-in-left:** 0.2s ease-out + 8px horizontal translate
- **No infinite animations** — no pulse dots, no route pulses, no floating elements
- **No decorative motion** — motion is reserved for actual state changes only
- **Reduced motion respected** — `prefers-reduced-motion` is the default assumption

---

## 7. Accessibility Foundations

Both themes are built on WCAG 2.1 AA compliance:

- **Contrast:** All text-on-background combinations meet 4.5:1 minimum
  - Theme A primary: 15.4:1
  - Theme B primary: 16:1
- **Focus visible:** 2px solid outline (Azimuth Blue for A, Royal Blue for B) with 2px offset
- **Skip links:** Hidden until focused, positioned top-left
- **Screen reader support:** Live regions, proper ARIA labels, sr-only utility
- **Color independence:** State never communicated by color alone — icons, text, and borders reinforce
- **Minimum font size:** 12px for UI text, 16px base body
- **Motion:** Theme A has purposeful motion; Theme B defaults to minimal motion

---

## 8. Page Patterns

### 8.1 Inbox / Trip Queue

**Information Architecture:**
The inbox is the operational command center. It displays a filterable, sortable grid of trip cards. Each card progressively discloses information across three rows: primary context (destination, type, customer), metrics (role-dependent), and status (priority, SLA, assignment).

**Theme A Pattern:**
- Page bg: Deep Space Canvas
- Header: Page title "Inbox" + subtitle + search input + sort dropdown + trip count
- Filter bar: Horizontal pill buttons with counts (All, At Risk, Critical, Unassigned) + role selector
- Bulk actions toolbar: Appears on selection — Elevated Terrain bg, Default Contour border
- Trip grid: 1–3 columns. Cards use Chart Surface bg with left priority accent bar
- Empty state: Centered illustration + helpful copy + CTA

**Theme B Pattern:**
- Page bg: Archive White
- Header: Same structure but with more vertical padding (40px top vs 20px)
- Filter bar: Same pills but with Hairline borders, more horizontal padding per pill
- Bulk actions toolbar: Card Stock bg, Hairline border, Royal Blue primary action
- Trip grid: 1–2 columns max. Cards use Card Stock bg with left priority accent bar (thinner — 3px vs 4px)
- Empty state: Same structure but warmer tone, more generous spacing

**Layout code (Theme A):**
```tsx
<div className="p-5 pb-4 max-w-[1400px] mx-auto space-y-5">
  <header className="flex items-center justify-between pt-1">
    <div>
      <h1 className="text-xl font-semibold text-[#e6edf3]">Inbox</h1>
      <p className="text-sm text-[#8b949e] mt-0.5">Trip queue · sorted by urgency</p>
    </div>
    {/* Search + Sort + Count */}
  </header>

  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
    {trips.map(trip => <TripCard key={trip.id} trip={trip} />)}
  </div>
</div>
```

**Layout code (Theme B):**
```tsx
<div className="p-8 pb-6 max-w-[1200px] mx-auto space-y-8">
  <header className="flex items-center justify-between pt-2">
    <div>
      <h1 className="text-xl font-semibold text-[#1a1a1a]">Inbox</h1>
      <p className="text-sm text-[#6b6b6b] mt-1">Trip queue · sorted by urgency</p>
    </div>
    {/* Search + Sort + Count */}
  </header>

  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {trips.map(trip => <TripCard key={trip.id} trip={trip} />)}
  </div>
</div>
```

### 8.2 Workspace / Trip Detail

**Information Architecture:**
A dedicated workspace for a single trip. Header shows trip metadata + stage navigation tabs. Main content area shows the active stage panel. Optional right rail shows timeline/history.

**Theme A Pattern:**
- Header card: Chart Surface bg, Default Contour border, `rounded-xl`. Contains breadcrumb, destination title, state badge, metadata row, stage tab buttons
- Stage tabs: Pill-shaped buttons with borders. Active: Azimuth Blue border + bg tint
- Main panel: Chart Surface bg, Default Contour border, `rounded-xl`, min-height 440px
- Right rail (optional): Chart Surface bg, timeline scrollable area
- Layout: `grid-cols-[minmax(0,1fr)_320px]` on xl screens

**Theme B Pattern:**
- Header card: Card Stock bg, Hairline border, `rounded-lg`. Same content but with more internal padding
- Stage tabs: Same pill buttons but with Hairline borders. Active: Royal Blue border + bg tint
- Main panel: Card Stock bg, Hairline border, `rounded-lg`, min-height 440px
- Right rail: Card Stock bg, Hairline border
- Layout: `grid-cols-[minmax(0,1fr)_280px]` — slightly narrower rail

**Layout code (Theme A):**
```tsx
<div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-5 space-y-4">
  <header className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 sm:p-5">
    {/* Trip metadata + stage tabs */}
  </header>

  <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4">
    <main className="rounded-xl border border-[#1c2128] bg-[#0f1115] min-h-[440px]">
      {children}
    </main>
    {isRailOpen && (
      <aside className="rounded-xl border border-[#1c2128] bg-[#0f1115]">
        <TimelinePanel tripId={tripId} />
      </aside>
    )}
  </div>
</div>
```

### 8.3 Settings / Configuration

**Information Architecture:**
Tabbed configuration page with three sections: Profile, Operations, Autonomy & AI. Dirty state tracking with save/reset actions.

**Theme A Pattern:**
- Page bg: Deep Space Canvas
- Header: Title + description + save/reset buttons (right-aligned)
- Save status: Inline feedback (green check or red alert)
- Tabs: Underline style, Azimuth Blue active indicator
- Tab content: Chart Surface bg card, Default Contour border, `rounded-xl`, p-6
- Form layout: Two-column grid on large screens, single column on mobile

**Theme B Pattern:**
- Page bg: Archive White
- Header: Same structure but with more vertical padding
- Save status: Same inline feedback
- Tabs: Underline style, Royal Blue active indicator
- Tab content: Card Stock bg card, Hairline border, `rounded-lg`, p-8 (more padding)
- Form layout: Single column max-width 640px — forms should feel focused, not sprawling

### 8.4 Marketing / Landing Page

**Information Architecture:**
Multi-section landing page: Hero with scene visualization, product surfaces grid, workflow story, persona cards, proof points, CTA band, footer.

**Theme A Pattern (Cinematic):**
- Page bg: Complex layered radial gradients + grid overlay + pseudo-element overlays
- Header: Sticky glassmorphic bar (`backdrop-filter: blur(24px)`, gradient bg, heavy shadow)
- Hero: Asymmetric two-column grid. Left: eyebrow badge, massive title, body copy, action buttons, stat cards. Right: floating UI preview with glow effects, animated scene nodes
- Section spacing: 72px–94px vertical padding
- Cards: `rounded-[22px]` to `rounded-[24px]` — very generous rounding for marketing warmth
- Shadows: Heavy, multi-layer (`0 18px 48px rgba(0,0,0,0.3)`)

**Theme B Pattern (Editorial):**
- Page bg: Archive White. No gradients. Optional: subtle 1px geometric line art in corners
- Header: Sticky solid bar (Card Stock bg, Hairline bottom border). No blur, no shadow
- Hero: Single centered column. Eyebrow text, large title, body copy, action buttons, stat cards below. Max-width 800px for text.
- Section spacing: 120px–160px vertical padding — much more generous
- Cards: `rounded-lg` (8px) — consistent with app, no marketing-only rounding
- Shadows: Single subtle layer (`0 2px 8px rgba(0,0,0,0.06)`) or none
- Typography: Larger body text (18px) with more generous line-height (1.75)

### 8.5 Itinerary Checker (Acquisition Wedge)

**Information Architecture:**
Public tool page. Hero with upload area, feature grid, notebook mode showcase, proof section, FAQ, CTA band.

**Theme A Pattern:**
- Uses same cinematic background as marketing landing
- Upload area: Dashed border zone with drag-and-drop affordance, Elevated Terrain bg on hover
- Feature grid: 2–3 column grid of cards with icon, title, description
- Notebook showcase: Side-by-side layout with visual preview

**Theme B Pattern:**
- Uses Archive White background
- Upload area: Dashed border zone, Card Stock bg on hover, Royal Blue dashed border on active
- Feature grid: Single column or 2-column max. Each feature is a horizontal row (icon left, text right) rather than a card
- Notebook showcase: Centered single column with screenshots stacked vertically

### 8.6 Auth Pages (Login / Signup)

**Theme A Pattern:**
- Centered card on Deep Space Canvas
- Card: Chart Surface bg, Default Contour border, `rounded-xl`
- Logo: Brand mark gradient square, centered above form
- Inputs: Full width, Input Bunker bg
- Primary button: Full width, Azimuth Blue bg
- Links: Azimuth Blue text

**Theme B Pattern:**
- Centered card on Archive White
- Card: Card Stock bg, Hairline border, `rounded-lg`
- Logo: Solid Royal Blue square, centered above form
- Inputs: Full width, pure white bg
- Primary button: Full width, Royal Blue bg
- Links: Royal Blue text

---

## 9. Component Usage Examples

### Trip Card

The TripCard is the most information-dense component in the system. It uses a three-row layout with progressive disclosure.

**Theme A implementation:**
```tsx
<Card
  variant="bordered"
  className="group relative overflow-hidden flex transition-all duration-200 ease-out hover:border-[#30363d]"
  style={{
    borderColor: trip.slaStatus === 'breached' ? 'rgba(248,81,73,0.4)' : '#1c2128',
  }}
>
  {/* Priority Accent Bar — 4px wide color-coded strip */}
  <div className="w-1 shrink-0 self-stretch" style={{ background: priorityColor, opacity: 0.7 }} />

  <div className="p-4 flex-1 min-w-0">
    {/* Row 1: Destination + Stage Badge */}
    <div className="flex items-start justify-between gap-3 mb-1 pr-6">
      <div className="flex flex-col min-w-0">
        <span className="text-[14px] font-semibold truncate leading-tight text-[#e6edf3]">
          {trip.destination}
        </span>
        <span className="text-[10px] uppercase tracking-wider font-bold mt-0.5 text-[#8b949e]">
          {trip.tripType}
        </span>
      </div>
      <StageBadge stage={trip.stage} />
    </div>

    {/* Row 2: Metrics — role-dependent, separated by vertical dividers */}
    <div className="flex items-center gap-3 my-3 py-2 border-y border-dashed border-[rgba(48,54,61,0.5)]">
      {metrics.map((field, i) => (
        <div key={field} className="flex items-center gap-2">
          {i > 0 && <div className="w-px h-4 bg-[#30363d]" />}
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase font-medium text-[#8b949e]">{label}</span>
            <span className="text-[11px] font-medium flex items-center gap-1 text-[#e6edf3]">
              {icon}{value}
            </span>
          </div>
        </div>
      ))}
    </div>

    {/* Row 3: Priority + SLA + Assignment */}
    <div className="flex items-center justify-between mt-2">
      <div className="flex items-center gap-2 flex-wrap">
        <PriorityBadge priority={trip.priority} />
        <ContextualSLABadge trip={trip} />
      </div>
      <AssignmentBadge trip={trip} />
    </div>
  </div>
</Card>
```

**Theme B implementation:**
```tsx
<Card
  variant="bordered"
  className="group relative overflow-hidden flex transition-all duration-200 ease-out hover:border-[#c4c0b8]"
  style={{
    borderColor: trip.slaStatus === 'breached' ? 'rgba(220,38,38,0.3)' : '#e5e2dd',
  }}
>
  {/* Priority Accent Bar — 3px wide, thinner than Theme A */}
  <div className="w-[3px] shrink-0 self-stretch" style={{ background: priorityColor, opacity: 0.6 }} />

  <div className="p-5 flex-1 min-w-0">
    {/* Row 1: Destination + Stage Badge */}
    <div className="flex items-start justify-between gap-3 mb-2 pr-6">
      <div className="flex flex-col min-w-0">
        <span className="text-[15px] font-semibold truncate leading-tight text-[#1a1a1a]">
          {trip.destination}
        </span>
        <span className="text-[11px] uppercase tracking-wide font-medium mt-1 text-[#9a9a9a]">
          {trip.tripType}
        </span>
      </div>
      <StageBadge stage={trip.stage} />
    </div>

    {/* Row 2: Metrics */}
    <div className="flex items-center gap-4 my-4 py-3 border-y border-dashed border-[rgba(0,0,0,0.08)]">
      {metrics.map((field, i) => (
        <div key={field} className="flex items-center gap-2">
          {i > 0 && <div className="w-px h-4 bg-[#e5e2dd]" />}
          <div className="flex flex-col gap-1">
            <span className="text-[11px] uppercase font-medium text-[#9a9a9a]">{label}</span>
            <span className="text-[12px] font-medium flex items-center gap-1 text-[#1a1a1a]">
              {icon}{value}
            </span>
          </div>
        </div>
      ))}
    </div>

    {/* Row 3: Priority + SLA + Assignment */}
    <div className="flex items-center justify-between mt-2">
      <div className="flex items-center gap-2 flex-wrap">
        <PriorityBadge priority={trip.priority} />
        <ContextualSLABadge trip={trip} />
      </div>
      <AssignmentBadge trip={trip} />
    </div>
  </div>
</Card>
```

### Workspace Panel

**Theme A pattern:**
```tsx
<div className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-5">
  <h2 className="text-base font-semibold text-[#e6edf3] mb-4">Panel Title</h2>
  <div className="space-y-3">
    {/* Content */}
  </div>
</div>
```

**Theme B pattern:**
```tsx
<div className="rounded-lg border border-[#e5e2dd] bg-white p-6">
  <h2 className="text-base font-semibold text-[#1a1a1a] mb-5">Panel Title</h2>
  <div className="space-y-4">
    {/* Content */}
  </div>
</div>
```

### Form Section

**Theme A pattern:**
```tsx
<div className="space-y-4">
  <div>
    <label className="text-[12px] font-medium text-[#8b949e]">Field Label</label>
    <input
      className="flex w-full rounded-md border border-[#30363d] bg-[#0f1115] text-[#e6edf3]
        placeholder:text-[#484f58] focus:outline-none focus:ring-2 focus:ring-[#58a6ff]
        focus:ring-offset-2 focus:ring-offset-[#080a0c] h-9 px-3 text-[13px]"
      placeholder="Enter value..."
    />
  </div>
</div>
```

**Theme B pattern:**
```tsx
<div className="space-y-5">
  <div>
    <label className="text-[13px] font-medium text-[#4a4a4a] mb-1.5 block">Field Label</label>
    <input
      className="flex w-full rounded-md border border-[#e5e2dd] bg-white text-[#1a1a1a]
        placeholder:text-[#9a9a9a] focus:outline-none focus:ring-2 focus:ring-[#2563eb]
        focus:ring-offset-2 focus:ring-offset-[#f7f5f2] h-10 px-3.5 text-[14px]"
      placeholder="Enter value..."
    />
  </div>
</div>
```

### Data Table

**Theme A pattern:**
```tsx
<div className="rounded-xl border border-[#1c2128] bg-[#0f1115] overflow-hidden">
  <table className="w-full text-sm">
    <thead className="bg-[#161b22] text-[#8b949e]">
      <tr>
        <th className="px-4 py-3 text-left font-medium">Column</th>
      </tr>
    </thead>
    <tbody className="divide-y divide-[#1c2128]">
      <tr className="hover:bg-[#161b22] transition-colors">
        <td className="px-4 py-3 text-[#e6edf3]">Value</td>
      </tr>
    </tbody>
  </table>
</div>
```

**Theme B pattern:**
```tsx
<div className="rounded-lg border border-[#e5e2dd] bg-white overflow-hidden">
  <table className="w-full text-sm">
    <thead className="bg-[#f0eeea] text-[#6b6b6b]">
      <tr>
        <th className="px-5 py-3.5 text-left font-medium">Column</th>
      </tr>
    </thead>
    <tbody className="divide-y divide-[#e5e2dd]">
      <tr className="hover:bg-[#f7f5f2] transition-colors">
        <td className="px-5 py-3.5 text-[#1a1a1a]">Value</td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 10. Tailwind Plugin Configuration

A Tailwind plugin that registers the full design system as utilities and components. This allows consistent usage across the codebase without relying solely on CSS variables.

### Installation

Create `frontend/tailwind.config.js` (or extend the existing minimal config):

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      // === COLORS ===
      colors: {
        // Theme A: Cartographic Dark
        canvas: '#080a0c',
        surface: '#0f1115',
        elevated: '#161b22',
        highlight: '#1c2128',
        'input-bg': '#111318',

        // Theme B: Minimalist Document
        'archive-white': '#f7f5f2',
        'card-stock': '#ffffff',
        'hovered-sheet': '#f0eeea',
        'selected-sheet': '#e8e5e0',
        'sidebar-canvas': '#f0eeea',

        // Text (both themes, used with dark/light modifiers)
        'text-primary': {
          DEFAULT: '#e6edf3',
          light: '#1a1a1a',
        },
        'text-secondary': {
          DEFAULT: '#a8b3c1',
          light: '#4a4a4a',
        },
        'text-tertiary': {
          DEFAULT: '#9ba3b0',
          light: '#6b6b6b',
        },
        'text-muted': {
          DEFAULT: '#8b949e',
          light: '#9a9a9a',
        },

        // Accents (Theme A)
        'accent-blue': '#58a6ff',
        'accent-green': '#3fb950',
        'accent-amber': '#d29922',
        'accent-red': '#f85149',
        'accent-cyan': '#39d0d8',
        'accent-purple': '#a371f7',
        'accent-orange': '#ff9248',

        // Accents (Theme B)
        'accent-royal': '#2563eb',
        'accent-forest': '#059669',
        'accent-warm-amber': '#d97706',
        'accent-error': '#dc2626',

        // Borders
        'border-default': {
          DEFAULT: '#30363d',
          light: '#e5e2dd',
        },
        'border-hover': {
          DEFAULT: '#8b949e',
          light: '#c4c0b8',
        },
        'border-active': {
          DEFAULT: '#58a6ff',
          light: '#2563eb',
        },

        // Geographic (Theme A only)
        'geo-land': '#1c2128',
        'geo-water': '#0d2137',
        'geo-route': '#39d0d8',
        'geo-waypoint': '#d29922',
        'geo-destination': '#3fb950',
      },

      // === FONTS ===
      fontFamily: {
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'SF Mono', 'monospace'],
        data: ['var(--font-data)', 'monospace'],
      },

      // === SPACING ===
      spacing: {
        'space-1': '4px',
        'space-2': '8px',
        'space-3': '12px',
        'space-4': '16px',
        'space-5': '20px',
        'space-6': '24px',
        'space-8': '32px',
        'space-10': '40px',
        'space-12': '48px',
        'space-16': '64px',
        'space-20': '80px',
        'space-24': '96px',
      },

      // === BORDER RADIUS ===
      borderRadius: {
        'sm': '4px',
        'md': '6px',
        'lg': '8px',
        'xl': '12px',
        '2xl': '16px',
        '3xl': '22px',
        '4xl': '24px',
        'full': '9999px',
      },

      // === SHADOWS ===
      boxShadow: {
        // Theme A
        'sm-dark': '0 1px 2px rgba(0, 0, 0, 0.3)',
        'md-dark': '0 4px 6px rgba(0, 0, 0, 0.3)',
        'lg-dark': '0 10px 15px rgba(0, 0, 0, 0.3)',
        'xl-dark': '0 20px 25px rgba(0, 0, 0, 0.3)',
        'glow-blue': '0 0 20px rgba(88, 166, 255, 0.15)',
        'glow-amber': '0 0 20px rgba(210, 153, 34, 0.2)',
        'glow-green': '0 0 20px rgba(63, 185, 80, 0.15)',

        // Theme B
        'sm-light': '0 1px 3px rgba(0, 0, 0, 0.06)',
        'md-light': '0 2px 8px rgba(0, 0, 0, 0.06)',
        'lg-light': '0 4px 16px rgba(0, 0, 0, 0.08)',
        'xl-light': '0 8px 32px rgba(0, 0, 0, 0.08)',
      },

      // === TRANSITIONS ===
      transitionDuration: {
        'fast': '150ms',
        'base': '200ms',
        'slow': '300ms',
      },

      // === LAYOUT ===
      maxWidth: {
        'app': '1400px',
        'app-light': '1200px',
        'marketing': '1320px',
        'marketing-light': '1100px',
      },

      // === Z-INDEX ===
      zIndex: {
        'dropdown': '10',
        'sticky': '20',
        'overlay': '30',
        'modal': '40',
        'tooltip': '50',
      },
    },
  },
  plugins: [
    // State badge plugin
    function({ addComponents }) {
      addComponents({
        '.badge-green': {
          backgroundColor: 'rgba(63, 185, 80, 0.1)',
          color: '#3fb950',
          borderColor: 'rgba(63, 185, 80, 0.3)',
        },
        '.badge-green-light': {
          backgroundColor: 'rgba(5, 150, 105, 0.08)',
          color: '#059669',
          borderColor: 'rgba(5, 150, 105, 0.2)',
        },
        '.badge-amber': {
          backgroundColor: 'rgba(210, 153, 34, 0.1)',
          color: '#d29922',
          borderColor: 'rgba(210, 153, 34, 0.3)',
        },
        '.badge-amber-light': {
          backgroundColor: 'rgba(217, 119, 6, 0.08)',
          color: '#d97706',
          borderColor: 'rgba(217, 119, 6, 0.2)',
        },
        '.badge-red': {
          backgroundColor: 'rgba(248, 81, 73, 0.1)',
          color: '#f85149',
          borderColor: 'rgba(248, 81, 73, 0.3)',
        },
        '.badge-red-light': {
          backgroundColor: 'rgba(220, 38, 38, 0.06)',
          color: '#dc2626',
          borderColor: 'rgba(220, 38, 38, 0.15)',
        },
        '.badge-blue': {
          backgroundColor: 'rgba(88, 166, 255, 0.1)',
          color: '#58a6ff',
          borderColor: 'rgba(88, 166, 255, 0.3)',
        },
        '.badge-blue-light': {
          backgroundColor: 'rgba(37, 99, 235, 0.06)',
          color: '#2563eb',
          borderColor: 'rgba(37, 99, 235, 0.15)',
        },
      });
    },
  ],
};
```

### Recommended CSS Variable Strategy

For runtime theme switching, use CSS custom properties in `globals.css`:

```css
/* Theme A (default) */
:root {
  --bg-canvas: #080a0c;
  --bg-surface: #0f1115;
  --bg-elevated: #161b22;
  --text-primary: #e6edf3;
  --text-secondary: #a8b3c1;
  --accent-primary: #58a6ff;
  --accent-success: #3fb950;
  --accent-warning: #d29922;
  --accent-error: #f85149;
  --border-default: #30363d;
}

/* Theme B (minimalist) */
[data-theme="minimalist"] {
  --bg-canvas: #f7f5f2;
  --bg-surface: #ffffff;
  --bg-elevated: #f0eeea;
  --text-primary: #1a1a1a;
  --text-secondary: #4a4a4a;
  --accent-primary: #2563eb;
  --accent-success: #059669;
  --accent-warning: #d97706;
  --accent-error: #dc2626;
  --border-default: #e5e2dd;
}
```

---

## 11. Theme B: Minimalist Document

### Complete Design Rationale

The Minimalist Document theme exists for contexts where the Cartographic Dark aesthetic is too heavy or too specialized:

1. **Daytime operations** — agents working in bright environments
2. **Client-facing views** — sharing trip details with travelers who are not operators
3. **Mobile-heavy usage** — light themes perform better in bright ambient light
4. **Brand evolution** — a cleaner aesthetic may resonate with agencies that serve luxury or wellness travelers
5. **Reduced cognitive load** — fewer colors and no decorative motion can reduce fatigue over long sessions

### What Changes vs. What Stays

| Element | Theme A (Cartographic) | Theme B (Minimalist) |
|---|---|---|
| **Background** | Near-black `#080a0c` | Warm off-white `#f7f5f2` |
| **Surface cards** | Dark gray `#0f1115` | Pure white `#ffffff` |
| **Accent count** | 7 distinct colors | 3 functional colors |
| **Gradients** | Radial glows, brand gradients | None — flat colors only |
| **Shadows** | Heavy, multi-layer dark | Single subtle layer or none |
| **Glassmorphism** | Backdrop blur on headers | Solid backgrounds |
| **Border radius (app)** | 12px (`rounded-xl`) | 8px (`rounded-lg`) |
| **Border radius (marketing)** | 22–24px | 8px (same as app) |
| **Max content width** | 1400px | 1200px |
| **Card grid max columns** | 3 | 2 |
| **Infinite animations** | Pulse, float, route glow | None |
| **Scrollbar** | Custom styled | System default |
| **Typography scale** | Tight leading, aggressive tracking | Generous leading, moderate tracking |
| **Input metaphor** | Recessed "bunker" | Flat "document field" |
| **Shell density** | Compact (44px bars, 8px gaps) | Relaxed (48px bars, 16px gaps) |

### What Does NOT Change

- **Component structure** — TripCard still has 3 rows, Workspace still has header+tabs+panel
- **Information architecture** — same fields, same progressive disclosure
- **Interaction patterns** — hover reveals, selection mechanics, keyboard navigation
- **Accessibility requirements** — WCAG AA maintained
- **Font families** — IBM Plex Sans + JetBrains Mono
- **Iconography** — Lucide icons remain unchanged
- **Data density** — same metrics shown, same decision surfaces exposed

### Migration Path

To implement Theme B in production:

1. **Add theme toggle** to settings (persisted preference)
2. **Extend `globals.css`** with `[data-theme="minimalist"]` variable overrides
3. **Update `tailwind.config.js`** with light-mode color variants
4. **Audit components** for hardcoded colors — replace with CSS variables or token references
5. **Create marketing variant** — a second set of marketing CSS modules without gradients/glows
6. **Test contrast** — verify all combinations on off-white backgrounds
7. **Remove decorative animations** in minimalist mode via `data-theme` selector

---

## 12. File Reference

| File | Purpose |
|---|---|
| `src/app/globals.css` | CSS custom properties, animations, utility classes, scrollbar styling |
| `src/lib/tokens.ts` | Centralized TypeScript tokens for colors, spacing, typography, elevation |
| `tailwind.config.js` | Tailwind entry point (minimal — should be extended with plugin config above) |
| `src/app/layout.tsx` | Root layout — font loading (IBM Plex Sans, JetBrains Mono), Shell wrapper |
| `src/components/ui/*.tsx` | Core components: Button, Card, Input, Select, Tabs, Badge, Loading |
| `src/components/layouts/Shell.tsx` | App shell — sidebar, command bar, main content area |
| `src/components/marketing/marketing.module.css` | Marketing page styles — gradients, glassmorphism, hero layouts (Theme A) |
| `src/components/marketing/marketing.tsx` | Marketing component primitives — Header, Hero, Section, CTA, Footer |
| `src/components/inbox/TripCard.tsx` | Dense information card — the primary content vessel |
| `src/components/workspace/panels/*.tsx` | Workspace stage panels — Intake, Packet, Decision, Strategy, etc. |
| `src/components/visual/*.tsx` | Data visualization — PipelineFunnel, RevenueChart, TeamPerformance |

---

*This DESIGN.md serves as the source of truth for Waypoint OS visual design. All new screens, components, and marketing materials should align with the tokens, colors, and principles documented here. When in doubt, prefer restraint over decoration, function over flourish, and clarity over cleverness.*
