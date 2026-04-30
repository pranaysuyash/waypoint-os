# Local Transport & Destination Navigation — Master Index

> Research on customer-facing local transport guidance, destination transit profiles, transit card management, route planning, fair price indicators, and getting-around intelligence for the Waypoint OS platform.

---

## Series Overview

This series covers local transport and destination navigation — the customer-facing system that answers "how do I get around?" at any travel destination. From detailed transit profiles for Bangkok, Singapore, Dubai, and 50+ other destinations to fair price indicators that prevent tourist overcharging, and from offline metro maps to real-time route planning, the navigation system is what transforms a traveler from "stranded at hotel" to "confident explorer."

**Target Audience:** Product managers, agents, content managers

**Key Insight:** The #1 traveler anxiety after accommodation is local transport. "How do I get from my Bangkok hotel to the Grand Palace?" "Is ₹500 for a tuk-tuk ride fair?" "Which metro line do I take?" An agency that answers these questions in real-time via the companion app eliminates the biggest source of traveler stress. The traveler who confidently navigates Bangkok's BTS system thanks to the agency's guide becomes a loyal customer.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [LOCAL_NAV_01_TRANSPORT.md](LOCAL_NAV_01_TRANSPORT.md) | Destination transport profiles (Bangkok, Singapore, Dubai, Bali, London), route planner, fair price indicator, transit card tracker, safety alerts, downloadable offline guides |

---

## Key Themes

### 1. Answer "How Do I Get There?" Before They Ask
The companion app should proactively show transport guidance for each day's itinerary. When the day's plan includes the Grand Palace, the app already shows the BTS route + boat connection + estimated cost + walking time.

### 2. Prevent Tourist Overcharging
The fair price indicator ("Siam to Grand Palace: fair price ₹80-120, drivers may ask ₹500") is the single most impactful trust-building feature. Travelers who feel protected from scams trust the agency deeply.

### 3. Offline Is Non-Negotiable
Travelers often land without data. Metro maps, key phrases, and transport guides must be pre-downloaded and work offline. Online-only navigation fails at the moment it's needed most.

### 4. One Destination at a Time
Each destination has unique transport culture. Tuk-tuks in Bangkok, Grab in Singapore, Nol cards in Dubai, Oyster in London — the guide must be destination-specific, not generic.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Ground Transportation (GROUND_TRANSPORTATION_*) | Booking transport (this series = navigating locally) |
| Traveler Companion App (TRAVELER_APP_*) | Transport guide in companion app |
| Maps (MAPS_*) | Map visualization for routes |
| Offline Capabilities (OFFLINE_*) | Offline transport guide downloads |
| Travel Preparation (TRAVEL_PREP_*) | Pre-trip transport guide download |
| Travel News (TRAVEL_NEWS_*) | Transit strike or disruption alerts |
| Weather (WEATHER_*) | Weather-impacted transport advice |
| Accessibility (ACCESSIBLE_*) | Accessible transport route guidance |
| AI Itinerary (AI_ITINERARY_*) | Itinerary includes transport between stops |

---

**Created:** 2026-04-30
