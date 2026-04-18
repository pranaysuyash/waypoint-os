# Frontend Gaps: Onboarding, Multi-Tenancy & Auth
**Date**: 2026-04-18
**Status**: Critical Gaps — Designed in wireframes, absent in Next.js implementation.

---

## Executive Summary
While Waypoint OS has a functional "Workbench" for analyzing single trips, it currently operates as a **single-user, single-tenant, auth-less** system. All designs for "Multi-agency" support, user onboarding, and agent permissions are currently "Ghost Features"—they exist as wireframes (`Docs/UX_DETAILED_USER_FLOWS.md`) but have zero code representation in the `frontend/` directory.

---

## 1. Missing Onboarding Flows
The first-use experience is currently a major blocker for scaling to real agencies.

*   **Landing Page (`/`)**: Currently a technical dashboard. Missing the marketing/onboarding hook (Screens 1-2 in wireframes).
*   **Sign-Up / Account Creation (`/signup`)**: No logic to create a new user account or agency profile.
*   **Welcome / Path Selection**: No flow to guide a new user between "Work on a trip," "See example," or "Upload historical data" (Screen 3).
*   **Quick Setup Wizard**: No UI to capture agency-level metadata (Market: Domestic/International, typical budget, specializations) (Screen 4).

## 2. Missing Multi-Tenant Architecture
The frontend is built for a single agency environment, making it impossible to onboard a second agency safely.

*   **No `agency_id` Context**: The Next.js frontend doesn't pull an `agency_id` from a session or config. All data fetching is global.
*   **Missing Agency Settings**: No UI for the owner to configure:
    *   **Margin Policies**: Default markup per country/service.
    *   **Tone of Voice**: Customizing the AI's proposal draft style.
    *   **Supplier White-lists**: Prioritizing specific partner networks.
*   **Multi-Agency Branding**: No ability to upload a logo or set primary brand colors for traveler-safe views.

## 3. Missing Identity & Roles (Auth)
The system lacks a user identity layer, meaning everyone has "Admin" level access to everything.

*   **Clerk Integration**: Planned but not implemented. No login/logout capability.
*   **Role-Based UI Guards**:
    *   **Owner View**: Analytics, team metrics, and margin policy are accessible to everyone (or not built).
    *   **Junior Agent View**: Restricted view with higher "Needs Review" thresholds—not built.
*   **Trip Assignment**: The `Inbox` and `Workspace` lack an `assigned_to` field, making team collaboration impossible.

## 4. Implementation Priorities

| Feature | Gap Level | Priority | Blocked By |
| :--- | :--- | :--- | :--- |
| **Clerk Auth Integration** | **Total** | **P0** | Foundation for Identity |
| **Agency Context Provider** | **Total** | **P0** | Auth Integration |
| **Onboarding Wizard** | **Total** | **P1** | Agency Context |
| **Agency Settings Dashboard** | **Total** | **P1** | Agency Context |
| **Role-Based Routing** | **Total** | **P2** | Auth Integration |

---

## Next Steps for Wave 2 Frontend
1.  **Integrate Clerk**: Drop in the `<ClerkProvider>` and wrap routes.
2.  **Define `agency_id`**: Ensure every API request and frontend hook (`useTrips`) passes an agency context.
3.  **Build Onboarding Screen 4**: At minimum, capture the "Market" and "Budget" signals to replace hardcoded defaults.
