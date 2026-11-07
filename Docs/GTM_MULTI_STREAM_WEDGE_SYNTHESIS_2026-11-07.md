# Unified Multi-Stream GTM Strategy: Itinerary Checker & Diagnostic Engine
**Date:** 2026-11-07  
**Status:** Decided & Ratified (Resolves D-01 / EX-01 from `Docs/review/WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md`)  
**Scope:** GTM Wedge Architecture, Monetization, Retention & Acquisition Flywheel

---

## 1. Executive Summary & Resolution of Previous Category Error

In September 2026, an audit (`GTM_ANGLE_ASSESSMENT_2026-09-01.md` and `WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md`) prematurely characterized the GTM wedge as "falsified in practice" because historical telemetry consisted of synthetic and test fixture runs. 

**This was a textbook category error:**
1. **Pre-Launch Telemetry $\neq$ Market Validation:** On a software product that was never publicly promoted, indexed, or shared with live travelers, automated test fixtures and simulation events are the expected engineering baseline. Declaring a consumer wedge "dead" before any distribution channel was opened confused development staging with market failure.
2. **Simulations Are Engineering Proof:** Multi-persona simulations and test fixtures were what hardened the extraction pipeline, exposed colloquial parsing edge cases, and prompted the creation of the multi-gov safety and ERA5 climate engines.
3. **The False Dichotomy:** The audit framed the future as a mutually exclusive three-way choice: Option A (B2C traveler surface), Option B (Invert to agency white-label), or Option C (Kill the consumer surface).

**The Decision (2026-11-07):**
We reject the zero-sum choice. All three paths are complementary distribution and revenue streams powered by the **exact same underlying engine**.

```
                              ┌─────────────────────────────────────────────────────────┐
                              │            WAYPOINT UNIFIED ENGINE                      │
                              │  • Ingestion: Messy text, WhatsApp, OCR, PDFs           │
                              │  • Diagnostics: Layover physics, Pacing curve, Climate  │
                              │  • Value Radar: Virtuoso/FSPP perks, Rate parity        │
                              └────────────────────────────┬────────────────────────────┘
                                                           │
         ┌─────────────────────────────────────────────────┼─────────────────────────────────────────────────┐
         ▼                                                 ▼                                                 ▼
   [STREAM 1: MONETIZATION]                         [STREAM 2: RETENTION]                          [STREAM 3: ACQUISITION]
 Agency White-Label Portal                       Internal Workflow Superpower                     Public Free Diagnostic
   (B2B2C Paid SaaS Tier)                            (Daily Agency Utility)                        (Viral / Inbound Top-of-Funnel)
─────────────────────────────                   ─────────────────────────────                  ─────────────────────────────
• Route: `/check/[agencySlug]`                  • In-app Quick-Ingest Palette                  • Route: `/itinerary-checker`
• Agency logo, colors, advisor card             • Paste WhatsApp, email, voice-note OCR        • Open to DIY travelers & Reddit
• Branded client audit report                   • Instant extraction into quote brief          • Visual "Aha!" gauges & perks radar
• Leads land directly in *their* inbox          • Eliminates 45m of retyping per trip          • Option to route lead to member agencies
  ➔ **Paid Monthly Feature ($49–$99/mo)**          ➔ **Core Platform "Sticky" Value**              ➔ **Inbound Lead-Gen for Agencies**
```

---

## 2. The Three Synergistic Streams

### Stream 1: The Paid Agency White-Label Portal (`/check/[agencySlug]`)
* **Target:** Travel agency owners and independent advisors.
* **Value Proposition:** *"Give your clients a luxury digital experience before they even book. Send them your custom audit link. They see your branding, your advisor bio, and our visual 'Aha!' reports—and the ready-to-quote brief lands straight into your Workbench."*
* **Why Agencies Pay:**
  - Eliminates the adversarial framing: the agency uses the diagnostic as their own high-tech intake tool.
  - Replaces boring Typeforms/intake surveys with interactive, high-value visual reports.
  - Highlights what the advisor can unlock (e.g. +\$650 in Virtuoso/FSPP amenities) while protecting against OTA traps (e.g. 50-minute CDG connections).
* **Monetization:** Premium B2B SaaS tier (\$49–\$99/month/seat).

### Stream 2: In-App "Messy Ingestion" Superpower (Daily Utility)
* **Target:** The travel advisor during their daily operational routine.
* **Value Proposition:** Advisors are inundated with messy inputs (WhatsApp voice notes, rambling email threads, screenshot dumps, flight confirmation PDFs). Instead of manually retyping fields, they drop the raw input into Waypoint's Quick-Ingest palette, which parses flights, hotels, travelers, dates, and budget into a quote-ready brief in seconds.
* **Role in Flywheel:** Daily retention engine. It prevents churn and ensures daily active usage regardless of outbound marketing volume.

### Stream 3: Public Free Diagnostic & Community Wedge (`/itinerary-checker`)
* **Target:** Unrepresented travelers, DIY planners, Reddit (`/r/TravelHacks`, `/r/ItineraryFeedback`, `/r/JapanTravel`), and organic search.
* **Value Proposition:** Free instant sanity check exposing impossible schedules, airport connection friction, and unclaimed luxury amenities.
* **Role in Flywheel:** 
  - Produces viral, shareable screenshot cards (the `LayoverStressGauge` and `PacingExhaustionCurve`).
  - Acts as an acquisition funnel that routes qualified, high-intent travelers to **paying subscriber agencies**, creating the ultimate B2B sales pitch: *"Waypoint doesn't just manage your travel business; we send you pre-qualified luxury travelers."*

---

## 3. The 5 Visual "Aha!" Moment Assets (Shipped Oct 30, 2026)

All streams leverage the 5 visual components created and verified on 2026-10-30:
1. **`LayoverStressGauge`**: Real airport physics (taxi + terminal transfer + border control + gate cutoff) with an interactive delay simulator slider.
2. **`RouteArcRibbon`**: Spatial flight/rail vector ribbon highlighting transport modes and friction.
3. **`PacingExhaustionCurve`**: Circadian and physical fatigue curves exposing impossible schedules vs. human recovery limits.
4. **`BeforeAfterComparison`**: Interactive split view showing raw DIY chaos vs. protected advisor experience.
5. **`HiddenPerksRadar`**: Auto-detects luxury properties and quantifies uncollected VIP consortia amenities (Virtuoso, FSPP, Belmond Bellini: breakfast, room upgrades, \$100 property credit, late checkout).

---

## 4. Implementation & Execution Roadmap

| Milestone | Deliverables | Status |
|---|---|---|
| **M1: Core Engine & Visuals** | Diagnostic pipeline, 5 visual components, destination intelligence (safety consensus, ERA5 climate normals) | **Done & Verified** |
| **M2: Stream 1 Route** | Dynamic tenant route `/check/[agencySlug]`, agency branding fetcher, scoped lead injection into agency Workbench | **In Progress** |
| **M3: Stream 2 Quick-Ingest** | Workbench Quick-Ingest modal/palette for raw WhatsApp/email/PDF paste | **Next** |
| **M4: Stream 3 Distribution** | OpenGraph social preview cards, shareable visual export, community seeding | **Planned** |
| **M5: Discovery Interviews** | 5 structured advisor demos validating willingness-to-pay for Stream 1 & 2 | **Planned** |
