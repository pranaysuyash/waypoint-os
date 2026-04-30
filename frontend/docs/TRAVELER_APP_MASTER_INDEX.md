# Traveler Companion App — Master Index

> Research on the customer-facing traveler companion mobile app, providing itinerary access, real-time maps, budget tracking, emergency contacts, in-trip chat with agent, and on-destination assistance for the Waypoint OS platform.

---

## Series Overview

This series covers the traveler companion app — the customer-facing mobile experience that travelers use before, during, and after their trip. Built as a PWA (no app store download), the companion app provides day-by-day itinerary access, interactive maps, budget tracking, documents wallet, agent chat, and emergency information. The app is designed for Indian outbound travelers who may face roaming data costs, limited connectivity, and unfamiliar destinations.

**Target Audience:** Product managers, mobile engineers, UX designers

**Key Insight:** 80% of traveler anxiety comes from not knowing what happens next — "Where do I go?", "What time is my pickup?", "Do I have my hotel voucher?". The companion app eliminates this by making every detail available at a glance, offline-capable, and one tap away. For the agency, it reduces 60% of "where is my..." support calls and creates a branded touchpoint that travelers share with friends.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [TRAVELER_APP_01_COMPANION.md](TRAVELER_APP_01_COMPANION.md) | PWA architecture, trip dashboard, day-by-day itinerary, interactive map, budget tracker, documents wallet, agent chat, emergency card, offline capabilities, photo journal |

---

## Key Themes

### 1. Offline-First, Not Offline-Optional
Indian travelers on international roaming face ₹50-200/MB. The companion app must work fully offline for essential features (itinerary, documents, emergency info, budget logging) and gracefully degrade for online-only features (live weather, nearby search, flight tracking). Offline is the default; online is the upgrade.

### 2. No App Store, No Friction
PWA architecture means travelers access the app via a WhatsApp link — no download, no app store account, no storage anxiety. "Tap this link → Add to Home Screen → done." This eliminates the #1 adoption barrier for one-time-use travel apps.

### 3. Emergency Access Is Always Visible
Every screen has an emergency button. All emergency numbers, embassy contacts, insurance helpline, and hospital locations are cached offline. This is not a feature — it's a responsibility. Travelers in distress should never need to search for help.

### 4. The Trip Journal Is Marketing
Auto-compiled photo journals with agency branding turn travelers into brand ambassadors. "5 days · 3 cities · 87 photos" shared on social media is authentic marketing that no ad campaign can replicate.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Customer Portal (CUSTOMER_PORTAL_*) | Self-service portal (pre-trip) |
| Support AI (SUPPORT_AI_*) | Chatbot on traveler app |
| Trip Control Room (TRIP_CTRL_*) | Emergency support during active trips |
| Trip Budget (TRIP_BUDGET_*) | Budget tracking integration |
| WhatsApp Business (WHATSAPP_BIZ_*) | PWA link distribution via WhatsApp |
| Concierge (CONCIERGE_*) | Premium in-trip assistance |
| Post-Trip Ecosystem (POST_TRIP_*) | Trip journal → memory products |
| In-Trip Upsell (INTRIP_UPSELL_*) | During-trip upgrade opportunities |

---

**Created:** 2026-04-30
