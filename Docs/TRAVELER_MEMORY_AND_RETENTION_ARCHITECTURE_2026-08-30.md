# Traveler Memory & Data Retention Architecture

**Date:** 2026-08-30  
**Authors:** Waypoint OS Core Architecture Team  
**Persona Alignment:** `PER-0717: Agent Memory Architect`  
**Status:** Implemented & Verified  

---

## 1. Executive Summary & First-Principles Separation

Agent memory in an autonomous travel agency platform spans two distinct operational contexts:
1. **In-Flight Workflow (Traveler Intake & Proposal Generation)**: Where memory is **consumed and verified**.
2. **Agency Governance & Privacy (Settings & Compliance)**: Where memory policies are **configured and audited**.

Mixing these two contexts into a standalone top-level tab created unnecessary visual clutter and cognitive overhead. Waypoint OS cleanly bifurcates memory capabilities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             WAYPOINT OS WORKSPACE                           │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 1. INTAKE & TRIP LIFECYCLE           │ 2. AGENCY SETTINGS & GOVERNANCE      │
│    (Workbench -> New Inquiry)        │    (Settings -> Memory & Retention)  │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Repeat Traveler Auto-Recall Card   │ • Preference Freshness Decay Policy  │
│ • Real-time Dietary & Safety Cues    │ • GDPR Article 17 Right-to-Erasure   │
│ • One-Click "Apply to Proposal"      │ • 5-Tier Memory Classification Map   │
│ • Inline Persistent Preference Log   │ • Multi-Tenant Isolation Enforcement │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 In-Flight Memory: `RepeatTravelerRecallCard` (`IntakeTab.tsx`)
- **Trigger**: Mounted in the `New Inquiry` (`IntakeTab.tsx`) workflow.
- **Functionality**:
  - Automatically matches incoming customer messages/emails against verified repeat traveler profiles.
  - Displays **Permanent Safety Constraints** (e.g. `Strict Vegan Meals (Permanent Safety Constraint)`).
  - Displays **Seating Choices** with freshness indicators (e.g. `Aisle seat preferred · 88% Fresh`).
  - Displays **Loyalty Identifiers** (e.g. `Delta SkyMiles #928410294 · Diamond Medallion`).
  - Provides a single-click `Apply to Proposal` action that appends structured notes directly into the quote draft.
  - Allows the agent to log new persistent facts directly with `[ Add Note ]`.

### 2.2 Agency Governance: `MemorySettingsTab` (`settings/page.tsx`)
- **Trigger**: Mounted in `Agency Settings` under the `Memory & Retention` tab.
- **Functionality**:
  - **Retention & Decay Lifespans**:
    - Medical/Allergies: `Permanent (No Decay)`
    - Loyalty & Passports: `36 Months (3 Years)`
    - Seating & Cabin: `24 Months (2 Years)`
    - Seasonal Vibes: `6 Months`
  - **5-Tier Architecture Map**:
    - Tier 1: Working Memory (Run scratchpad)
    - Tier 2: Episodic Memory (Historical disruption ledger)
    - Tier 3: Semantic Memory (Profile affinities & safety constraints)
    - Tier 4: Procedural Memory (Agency markup & commercial guardrails)
    - Tier 5: Preference Memory (Autonomy & communication cadence)
  - **GDPR Article 17 Right-to-Erasure Console**:
    - Wipes customer PII and replaces active records with cryptographically signed anonymous tombstone receipts.

---

## 3. Contract & Backend API Alignment

| Surface / Flow | API Endpoint | Description |
| :--- | :--- | :--- |
| **New Inquiry Auto-Recall** | `GET /api/v1/customers/memory` | Retrieves matching customer profile by email/phone/name. |
| **Trip Proposal Hydration** | `POST /api/v1/customers/hydrate-trip/{trip_id}` | Injects verified preferences into trip packet. |
| **Inline Fact Logging** | `POST /api/v1/customers/memory/ingest` | Ingests fact through Write Eligibility Gate with SHA-256 hash. |
| **Settings Policy Updates** | `POST /api/settings/operational` | Persists agency retention and decay parameters. |
| **GDPR Customer Purge** | `POST /api/v1/customers/memory/forget` | Issues verified cryptographic Certificate of Erasure. |

---

## 4. Verification & Testing Proof

- Pytest Test Suite: `tests/test_agent_memory_architecture.py` (10/10 tests passing).
- Parity & Route Inventory: `tests/test_server_route_parity.py` (6/6 tests passing).
- Linter Clean Gate: `uv run ruff check .` (0 errors, 0 warnings).
- Visual E2E: Verified on `http://localhost:3005/workbench` and `http://localhost:3005/settings?tab=memory`.
