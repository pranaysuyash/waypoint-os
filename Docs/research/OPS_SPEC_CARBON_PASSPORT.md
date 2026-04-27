# Ops Spec: Agentic 'Carbon-Passport' Lifecycle Manager (OPS-REAL-029)

**Status**: Research/Draft
**Area**: Traveler Sustainability Accountability & Carbon Lifecycle Reporting

---

## 1. The Problem: "The Invisible-Carbon-Ledger"
Most travel agencies offer a checkbox carbon offset at checkout — a $5 token gesture that doesn't reflect the actual footprint of a complex, multi-segment trip. Travelers who genuinely care about their environmental impact have no way to understand their true travel carbon burden across their lifetime of trips, and agencies have no mechanism to help them reduce it meaningfully over time. Without a "Carbon-Passport," sustainability is theater.

## 2. The Solution: 'Sustainability-Ledger-Protocol' (SLP)

The SLP acts as the "Carbon-Accountant."

### Lifecycle Actions:

1.  **Full-Trip-Carbon-Calculation**:
    *   **Action**: Calculating the precise carbon footprint of every booking component: flights (cabin class, routing, aircraft type), hotels (energy certification, food sourcing), ground transport, activities, and meals.
2.  **Traveler-Carbon-Passport-Aggregation**:
    *   **Action**: Maintaining a cumulative "Carbon-Passport" for each traveler — a running ledger of their total travel carbon burden across all trips booked with the agency.
3.  **Intelligent-Offset-Routing**:
    *   **Action**: Moving beyond generic checkbox offsets to "Verified-High-Impact-Projects" matched to the traveler's values (e.g., a safari traveler is offered wildlife corridor reforestation; a coastal traveler is offered ocean plastic recovery).
4.  **Footprint-Reduction-Coaching**:
    *   **Action**: Proactively identifying "Low-Hanging-Fruit" reductions in future trip planning (e.g., "Switching your LAX-LHR leg to a direct Heathrow routing would reduce this trip's footprint by 23%") without sacrificing the core experience.

## 3. Data Schema: `Carbon_Passport_Record`

```json
{
  "passport_id": "SLP-99221",
  "traveler_id": "TRAVELER_ALPHA",
  "lifetime_carbon_kg": 45200,
  "current_year_carbon_kg": 8400,
  "offset_percentage": 0.72,
  "active_offset_project": "WILDLIFE_CORRIDOR_KENYA",
  "next_reduction_opportunity": "LAX_TO_LHR_DIRECT_ROUTING_SAVES_23_PERCENT",
  "passport_status": "ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Science-Based' Calculation Standard**: Carbon calculations MUST use verified methodologies (e.g., ICAO carbon calculator for flights, Green Key certifications for hotels). No proprietary estimates that can't be audited.
- **Rule 2: No-Greenwash-Gate**: The agent MUST NOT recommend any offset project that lacks third-party verification (e.g., Gold Standard, Verra VCS). Checkbox-style offsets with no verification chain are prohibited.
- **Rule 3: Opt-In-Depth**: Traveler carbon passport data MUST be fully opt-in. The agent can calculate footprints internally for routing optimization without requiring traveler-facing publication.

## 5. Success Metrics (Carbon)

- **Passport-Adoption-Rate**: % of travelers who opt in to maintain an active Carbon-Passport.
- **Offset-Quality-Score**: Average third-party verification score of offset projects facilitated through the platform.
- **Per-Trip-Footprint-Trend**: Year-over-year reduction in average carbon footprint per trip for Carbon-Passport holders vs. non-holders.
