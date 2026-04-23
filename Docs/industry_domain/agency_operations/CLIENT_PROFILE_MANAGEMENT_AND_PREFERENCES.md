# Domain Knowledge: Client Profile Management & Preferences

**Category**: Communication & Data Intake Architecture  
**Focus**: The "Digital Mirror" of the traveler—maintaining high-fidelity preferences.

---

## 1. The "Golden" Profile
- **Logic**: A single source of truth for the traveler's identity.
- **Fields**:
    - **Identity**: Passport, Visas, Known Traveler Number (KTN).
    - **Loyalty**: 20+ Airline/Hotel/Car loyalty numbers.
    - **Physical**: Seat (Aisle/Window), Bed (King/Twin), Floor (High/Low).
    - **Dietary**: Allergies (Gluten, Nut, Shellfish), Religious (Kosher, Halal).

---

## 2. Preference "Evolution"
- **Logic**: People's preferences change (e.g., "I used to love the window, but now I prefer the aisle for easier access").
- **SOP**: Every 12 months, the agent sends a **"Preference Audit"** summary: "We have you down for Aisle seats and Nut-free meals. Still accurate?"

---

## 3. GDS Profile Sync (STARs / PRO-files)
- **Logic**: The CRM profile must match the GDS "STAR" or "Profile."
- **SOP**: When a profile is updated in the CRM, it must "Push" the update to the GDS via an API (e.g., Amadeus MasterPricer / Sabre Profiles).

---

## 4. The "Vibe" & "Idiosyncrasies"
- **Logic**: The "Soft" data that standard CRM fields miss.
- **Examples**: "Only drinks Evian water," "Hates the color purple," "Needs a room with a desk facing the window."
- **SOP**: Use of **"Free-text Tags"** that are surfaced to the agent (or AI) during the booking process.

---

## 5. Proposed Scenarios
- **The "Stale" Passport**: A client's passport expired last week. The agent didn't catch it because the "Expiry Alert" was ignored. The agent must have an **"Automatic Block"** on ticketing if the passport expiry is < 6 months from the return date.
- **Wrong Seat "Crisis"**: A client is booked in a Window seat but had updated their preference to Aisle in a WhatsApp message. The agent missed the update. The agent must have **"Real-time CRM Sync"** for chat-based preferences.
- **The "Nut" Allergy Scare**: A client has a severe nut allergy. The agent books a flight but forgets to add the **"SPML"** (Special Meal) SSR code. The agent must have a **"Safety Checklist"** that blocks "End Segment" if a known allergy hasn't been coded.
- **Profile Collision**: Two clients have the same name. Their loyalty numbers are mixed up. The agent must use **"Unique Client IDs"** (UUIDs) that are separate from the traveler's name.
