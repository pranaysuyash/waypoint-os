# Waypoint OS Design System

Source: exported from Claude Design (claude.ai/design), 2026-04-28.

## Files

| File | Contents |
|---|---|
| `wp-shared.jsx` | Design tokens (`WP`, `WP_C`) + base components (`WpBtn`, `WpBadge`, `WpPill`, `WpCard`, `WpKicker`, `WpIcon`) |
| `wp-tokens.jsx` | Design system showcase — color palette, typography scale, component states |
| `wp-landing.jsx` | Landing page prototype — `LandingHero` (cockpit mockup, count-up metrics) + `LandingSections` (bento problem grid, how-it-works, persona cards, CTA+waitlist) |
| `wp-app.jsx` | App shell prototype — `WpSidebar` (left-border active state), `WpTripCard` (dashed metric row, priority bar), `AppInbox`, `AppWorkspace` (3-col) |
| `wp-wedge.jsx` | GTM wedge prototype — `WedgeUpload` (tool-first, mode tabs, trust chips) + `WedgeResults` (score ring, email gate, findings, agency conversion) |
| `chat1.md` | Full design session transcript — intent and decisions behind the designs |

## Token reference

| Token | Value |
|---|---|
| canvas | `#07090b` |
| surface | `#0d1117` |
| elevated | `#161b22` |
| blue | `#58a6ff` |
| cyan | `#39d0d8` |
| amber | `#d29922` |
| green | `#3fb950` |
| red | `#f85149` |
| purple | `#a371f7` |
| fDisplay | Outfit 700/900 |
| fBody | Inter |
| fMono | JetBrains Mono |

## What's implemented

- **Tailwind config** — all CSS vars wired as Tailwind utilities ✓
- **globals.css** — `animate-fade-up`, `animate-stagger-container`, `animate-route-pulse`, `fadeUp` keyframe ✓
- **Shell.tsx** — left-border `2px solid #58a6ff` active nav state ✓
- **TripCard** — dashed metric separator row + left priority bar ✓
- **AgencyHeroCockpit** — coded UI mockup in hero (no AI image) ✓
- **CtaBand** — waitlist email input alongside "Book a demo" ✓
- **Landing page** — trust chips, persona cards with top-border accent, problem bento, numbered how-it-works ✓
- **Itinerary checker** — full tool-first rebuild: upload zone as hero, mode tabs, trust chips, results with score ring + email gate + agency conversion ✓
