# Design System V2: Liquid Glass & Midnight Garden

**Status**: Active  
**Last Updated**: April 2026  
**Concept**: A fusion of high-end hospitality (Belmond/Aman) with "Invisible Tech" (Ghost Concierge).

---

## 1. Visual Manifesto
- **Atmospheric Depth**: Use layers of translucent glass over high-fidelity destination imagery.
- **Silent Guidance**: Use micro-animations and "Tech-Violet" glows to signal AI activity (Ghost Concierge).
- **Premium Weight**: Interface elements should feel physical, with soft refraction and subtle border glows.

---

## 2. Core Palette

### Primary (Backgrounds)
| Name | Hex | Usage |
|------|-----|-------|
| Midnight Garden | `#0A1F1C` | Main dashboard background. |
| Deep Emerald | `#062C25` | Secondary containers / Sidebar. |
| Obsidian | `#050505` | Deepest shadows. |

### Secondary (Accents)
| Name | Hex | Usage |
|------|-----|-------|
| Frontier Gold | `#D4AF37` | Serif headings, Logo, Luxury highlights. |
| Tech-Violet | `#8B5CF6` | AI Active states, Sentiment "High" indicators. |
| Ghost White | `#F8FAFC` | Main body text (high contrast). |

---

## 3. Typography
- **Headings**: `Playfair Display` or `Cormorant Garamond` (Elegant Serif).
- **Body**: `Inter` or `Plus Jakarta Sans` (High-readability Sans-Serif).
- **UI Metrics**: `Space Mono` (Data-heavy elements, flight numbers).

---

## 4. UI Patterns: "The Bento Grid"
All operational data is housed in modular cards with the following properties:
- `backdrop-filter: blur(20px) saturate(180%);`
- `background: rgba(10, 31, 28, 0.7);`
- `border: 1px solid rgba(212, 175, 55, 0.15);` (Subtle gold border)
- `border-radius: 24px;`

---

## 5. Visual Inspiration
![Frontier OS Dashboard Concept](/Users/pranay/.gemini/antigravity/brain/1aa8f72c-13a5-41e5-b44e-3bc9229e073c/frontier_os_dashboard_concept_1777010344912.png)

---

## 6. CSS Token Map (Draft)
```css
:root {
  --midnight-garden: #0a1f1c;
  --emerald-deep: #062c25;
  --frontier-gold: #d4af37;
  --tech-violet: #8b5cf6;
  --glass-bg: rgba(10, 31, 28, 0.7);
  --glass-border: rgba(212, 175, 55, 0.15);
  --radius-lg: 24px;
}
```
