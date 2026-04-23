# Feature: Semantic Taste Graph Discovery

## POV: User POV (Personalization)

### 1. Objective
To move beyond "Star Ratings" and "Categories" (e.g., 5-star hotel, Beach) toward a "Semantic Map" of traveler taste that allows the system to source "Soul-Matches" for any destination.

### 2. Functional Requirements

#### A. The "Taste Genome" (Deep Personalization)
- **Mood-Based Sourcing**: Sourcing options based on abstract descriptors: "Gothic Noir," "Sun-Drenched Minimalism," "High-Energy Chaos," "Quiet Seclusion."
- **Activity Nuance**: Distinguishing between "Active" (Hiking) and "High-Impact" (Skydiving).
- **Culinary Specificity**: Storing preferences for "Street Food/Local Gems" vs. "Michelin-Starred/White Tablecloth."

#### B. Semantic Recommendation Engine
- **"If You Liked X, You'll Love Y"**: Cross-destination matching. e.g., "Since you loved the Aman Kyoto's forest seclusion, you'll likely appreciate this specific lodge in the Chilean Patagonia."
- **Architecture & Design Filter**: Allowing users to filter hotels by architect (e.g., "Show me everything by Zaha Hadid or Tadao Ando").

#### C. Friction-Tolerance Mapping
- **The "Grumpiness" Score**: Mapping how a traveler reacts to specific frictions (e.g., "Hates Layovers > 3 hours," "Doesn't mind long drives if there's a view").
- **Social Battery Profile**: Identifying if a user wants "High-Interaction Concierge" or "Invisible/Zero-Touch Service."

### 3. Core Engine Logic
- **Knowledge Graph Integration**: Linking the "Customer Genome" to a global "Place Graph" that includes local secrets, design history, and vibe-check data.
- **Dynamic Weighting**: Adjusting the "Taste Graph" based on the *company* (e.g., "When traveling with kids, prioritize safety/space; when solo, prioritize design/vibe").

### 4. Privacy & Governance
- **Taste Portability**: Allowing the user to "Export" their taste graph to other platforms (Interoperability).
- **The "Surprise Me" Toggle**: Intentionally suggesting 1 option that is *outside* their taste graph to prevent "Filter Bubble" stagnation.
