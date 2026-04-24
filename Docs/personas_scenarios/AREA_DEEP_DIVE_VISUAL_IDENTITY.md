# Area Deep Dive: Visual Identity & Sensory Layout

**Domain**: Brand & Experience  
**Focus**: Cinematic imagery, "Liquid Glass" UI, and sensory-driven information architecture.

---

## 1. The "Cinematic" Imagery Strategy
Moving away from stock photos to "Sense of Place" narratives.

### Visual Principles
- **Atmosphere over Detail**: Prefer a blurred sunset through a villa window over a sharp photo of the bed.
- **Triptych Narratives**: UI should group images in threes to tell a story (e.g., *Arrival -> Detail -> View*).
- **Analog Texture**: Subtle film grain and soft light blooms to contrast with the "digital precision" of the AI.

### Layout Implementation: The "Scene" Card
Instead of a simple image gallery, we use "Scene Cards" in the Bento Grid:
- **State A (Resting)**: A single moody image with a glass overlay.
- **State B (Hover)**: The glass slides away, revealing a cinematic video loop or a triptych of details.

---

## 2. "Liquid Glass" UI Components
Based on the **Frontier OS** design system, we define the interactive grammar:

| Component | Visual Logic | Rationale |
|-----------|--------------|-----------|
| **Ghost Feed** | Translucent scroll with refraction. | Shows AI background activity without blocking the "Scene." |
| **Sentiment Orb** | A tech-violet glowing orb that pulses based on traveler happiness. | Ambient signaling of emotional state. |
| **Bento Workspace** | Modular cards that rearrange based on the traveler's context (e.g., Flight focus vs. Dinner focus). | Adaptive density. |

---

## 3. Sensory Color Palette: "Midnight Garden"
| Color | Role | Psychological Impact |
|-------|------|----------------------|
| `#0A1F1C` | Canvas | Calm, exclusive, nocturnal. |
| `#D4AF37` | Highlight | Value, heritage, precision. |
| `#8B5CF6` | Signal | Intelligence, novelty, speed. |

---

## 4. Industry Imagery Archetypes
To be used in the `PromptBundle` for generating traveler-safe communication:
1. **The "Quiet Luxury" Frame**: Minimalist architecture, soft shadows, expensive textures (linen, stone).
2. **The "Autonomic Flow" Frame**: Motion-blurred transport, glowing boarding passes, seamless transitions.
3. **The "Human Connection" Frame**: Blurred candid laughter, hands sharing a meal, eye contact.

---

## 5. Next Steps: Scenario Generation
We will generate scenarios that specifically trigger these "Visual State" changes:
1. `sc_visual_hostile_sentiment_ui_pivot.json`: UI turns from Green/Gold to Warn/Amber as sentiment drops.
2. `sc_visual_ghost_concierge_midnight_mode.json`: UI enters "High-Alert" night mode during a flight emergency.
3. `sc_visual_bento_reconfiguration_group.json`: Bento grid shifts from "Solo Agent" density to "Group Coordinator" summary.
