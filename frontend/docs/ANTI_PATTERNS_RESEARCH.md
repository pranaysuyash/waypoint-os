# Anti-Patterns Research - Travel Agency Agent Workspace

> Context: Building "Palantir for travel agencies" — a tool for fast, efficient, correct operations.
> Goal: Avoid generic patterns that signal "AI-generated" or don't serve the use case.

---

## What "AI Slop" Looks Like in 2024-2025

### The Card Grid + Blue Button Pattern
**What it is:** Identical cards in a grid, each with icon + heading + text, blue primary button
**Why it fails:** No information hierarchy, everything looks equally important
**Our alternative:** Data-dense tables, lists with inline actions, asymmetric layouts

### The Gradient Accent Pattern
**What it is:** Cyan/purple/blue gradients on dark backgrounds, glowing borders
**Why it fails:** Distracting from actual data, signals "tech demo" not production tool
**Our alternative:** Monochrome with limited accent colors, focus on data visibility

### The Hero Metric Dashboard
**What it is:** Big numbers at top, small labels, supporting stats, gradient accent
**Why it fails:** Celebrates vanity metrics, wastes prime screen real estate
**Our alternative:** Metrics integrated where relevant, no decorative numbers

### Glassmorphism Everywhere
**What it is:** Blur effects, semi-transparent cards, glow borders used decoratively
**Why it fails:** Reduces readability, feels like a theme not a tool
**Our alternative:** Solid backgrounds, clear borders, high contrast

### Side-Stripe Borders (ABSOLUTE BAN)
**What it is:** `border-left: 4px solid var(--color-warning)` on cards, alerts, list items
**Why it fails:** The single most overused "design touch" in admin/medical UIs
**Our alternative:** Background tints, full borders, icons, or no visual indicator

---

## Travel Industry Anti-Patterns

### Consumer Booking Site Patterns
**What to avoid:**
- Search forms with destination/date/passenger fields
- Carousel hotel/flight cards
- "Book Now" CTAs everywhere
- Beach/palm tree imagery
- Vacation photo backgrounds

**Why:** Agents aren't consumers. They need operations, not inspiration.

**Our direction:** No destination search cards, no booking flows. This is a workspace, not a storefront.

### Stock Travel Imagery
**What to avoid:**
- Beaches, palm trees, mountains as decorative backgrounds
- Airplane icons for "trips"
- Suitcase icons for "itinerary"
- Globe icons for "destinations"

**Why:** Generic, signals "travel template" not "operations tool"

**Our direction:** Use abstract or data-visualization iconography. Flags for countries (precise), not generic globes.

---

## Enterprise/CRM Anti-Patterns

### Dashboard Overwhelm
**What to avoid:**
- 20+ metrics on one screen
- Complex filters buried in drawers
- Notification badges everywhere
- Dense tables without visual breaks

**Our approach:** Progressive disclosure. Show what's needed now, hide complexity behind intentional interaction.

### Notification Spam
**What to avoid:**
- Toast notifications for every minor event
- Badge numbers that never reset
- "Did you know?" tooltips

**Our approach:** Notifications for time-sensitive only. SLA breaches, urgent messages.

### Modal Chains
**What to avoid:**
- Modal opens another modal
- Multi-step wizards in modals
- Modals for simple confirmations

**Our approach:** Inline editing (already implemented). Use modals sparingly.

---

## False Confidence Patterns (Critical for Reassurance)

### Over-Promising Accuracy
**What to avoid:**
- "98% match!" confidence scores without context
- Hidden uncertainty
- Pretending AI is perfect

**Our approach:**
- Show confidence ranges, not point estimates
- Surface uncertainty explicitly
- "This quote needs review" vs "Quote ready"

### Silent Failures
**What to avoid:**
- Actions that fail silently
- Loading states that never resolve
- "Something went wrong" with no details

**Our approach:** Always show what's happening and why. Explicit error states.

---

## Anti-Reference List

Sites/apps to actively avoid patterning after:

| Site | Why to Avoid | What to Do Instead |
|------|--------------|-------------------|
| Typical booking.com clone | Consumer travel patterns | Look at Palantir, Linear, Notion |
| Generic admin dashboards | Card grids, blue buttons | Data-dense, asymmetric |
| AI demo sites | Gradients, glassmorphism | Solid, high-contrast |
| Mobile-first consumer apps | Big touch targets, hidden menus | Desktop-first, visible actions |
| Corporate SaaS landing pages | Stock photos, value props | Focus on the work surface |

---

## Positive References

Patterns that align with our direction:

| Reference | What to Steal | How to Adapt |
|-----------|---------------|--------------|
| **Palantir** | Data density, dark theme, serious | Adapt for travel context |
| **Linear** | Command palette, speed, keyboard-first | Cmd+K for trips, actions |
| **Notion** | Slash commands, inline editing | Already doing inline edit |
| **GitHub** | Audit trail, change history | Already implementing |
| **Superhuman** | Keyboard shortcuts, speed | Cmd+K navigation |
| **Figma** | Properties panel, layer hierarchy | Panel-based workspace |

---

## Design Constraints Summary

1. **NO consumer travel patterns** — no booking cards, search forms, vacation imagery
2. **NO generic card grids** — use tables, lists, asymmetric layouts
3. **NO gradient accents** — solid colors, limited accent usage
4. **NO border-left stripes** — use backgrounds, full borders, icons
5. **NO glassmorphism** — solid surfaces, clear boundaries
6. **NO false confidence** — surface uncertainty explicitly
7. **NO notification spam** — only time-sensitive alerts

---

## Next: Command Palette Deep-Dive

Given the "fast responses" priority and Palantir inspiration, the next feature to design is:

**Command Palette (Cmd+K)**
- Global search across trips
- Quick actions (create trip, change status, etc.)
- Keyboard-first navigation
- Instant access — supports "11 PM WhatsApp panic" scenario

This will be explored in a separate design brief.
