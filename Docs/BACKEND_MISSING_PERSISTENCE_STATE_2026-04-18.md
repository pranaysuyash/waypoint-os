# Backend Gaps: From Stateless Pipeline to SaaS OS
**Date**: 2026-04-18
**Status**: Foundational Gaps — The core deterministic pipeline works, but the surrounding persistence, commercial logic, and multi-tenant isolation are absent.

---

## Executive Summary
The backend currently operates as a highly robust, stateless "Spine" (Intake → Decision → Strategy). You feed it text, and it returns a structured JSON packet with confidence scores and safe outputs. 

However, it is currently a "calculator," not an Operating System. If the server restarts, everything is forgotten. It has no concept of an "Agency," a "Customer," or a "Vendor."

---

## 1. Missing Persistence & State (The "Brain Amnesia")
The current backend uses local JSON file-backing (`spine-api/persistence.py`) for audit logs and run states. There is no relational database.

*   **No Relational DB**: Missing Postgres/Supabase schema for `agencies`, `users`, `customers`, `trips`, and `vendors`.
*   **No Cross-Run Memory**: If a client asks a question on Tuesday and follows up on Thursday, the system treats it as two entirely separate events. It cannot stitch `CanonicalPackets` together over time.
*   **No Multi-Tenant Isolation**: The file-backed persistence does not partition data by `agency_id`. All trips are dumped into the same local directory (`runs/`).

## 2. Missing Commercial & Margin Logic (The "Money Gap")
The system can plan a beautiful trip, but it cannot price it or track the agency's profit.

*   **No Vendor/Supplier Graph**: The system cannot store or retrieve preferred suppliers, contracted rates, or specific commission tiers.
*   **No Margin Calculator**: It cannot ingest a net cost (e.g., Hotel A: $200/night net) and apply the agency's specific margin policy (e.g., 15% markup) to generate the gross quote.
*   **No Financial State Tracking**: It cannot track whether a trip is "Quoted," "Deposit Paid," "Fully Paid," or "Commission Settled." It is entirely blind to the financial lifecycle.

## 3. Missing CRM & Customer Lifecycle
A boutique agency survives on repeat business and knowing their clients deeply.

*   **No Customer Profiles**: The system extracts travelers for *this specific trip*, but it does not save a persistent `CustomerProfile` (e.g., "The Sharma Family always flies Business Class and prefers Marriott").
*   **No Lifecycle Triggers**: It cannot detect when a past client hasn't booked in 18 months (churn risk) or when an anniversary trip is approaching.

## 4. Missing External Integrations (The "Silo")
The current decision engine (`src/intake/decision.py`) relies entirely on hardcoded logic or LLM inference. It does not speak to the outside world.

*   **No Live Pricing/Availability**: It cannot check if flights are actually available or if a hotel is sold out.
*   **No Communication Gateways**: It drafts great WhatsApp messages (`StrategyBundle`), but it cannot actually *send* them via Twilio/WATI or receive replies via webhooks.

## 5. Implementation Priorities

| Feature | Gap Level | Priority | Dependency |
| :--- | :--- | :--- | :--- |
| **Postgres Database Setup** | **Total** | **P0** | Foundation for all state |
| **Multi-Tenant Schema (Agency ID)** | **Total** | **P0** | Database Setup |
| **Customer Profile Entity** | **Total** | **P1** | Database Setup |
| **Financial/Margin Engine** | **Total** | **P2** | Database Setup |
| **WhatsApp/Email Webhooks** | **Total** | **P2** | Auth & Persistence |

---

## Next Steps for Backend Wave C (Post-Wave A & B)
While Wave A formalized the "Run Lifecycle" and Wave B proposed "Agentic Automation", **Wave C must be the Persistence Wave**.
1.  **Stand up a Postgres DB** (e.g., Supabase/Render).
2.  **Migrate `persistence.py`** from local JSON to relational tables.
3.  **Inject `agency_id`** into every core entity (`Trip`, `Customer`, `Run`).
