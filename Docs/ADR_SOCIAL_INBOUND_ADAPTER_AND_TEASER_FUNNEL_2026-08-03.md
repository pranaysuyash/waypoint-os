# ADR 18: Social Inbound Adapter, Zero-External-API Direct Lead Surface & 2-Stage Teaser Funnel

**Date**: 2026-08-03  
**Status**: APPROVED / PROPOSED  
**Deciders**: Engineering & Product Lead, Creator Operations Lead  
**Governing Motto**: `motto_v4.md` (Rule 0: Zero Shadow Pipelines, Rule 0.15: Third-Layer Decoupling, ADR-First)

---

## 1. Context & Problem Statement

Travel creators and boutique agencies lose ~90% of social media DMs (Instagram, TikTok, WhatsApp) due to slow manual quoting (3–5 days). However, building automated platform-specific webhooks (Meta Graph API) introduces severe third-party fragility, expired OAuth tokens, and rate limits. Furthermore, generating full free itineraries for every casual DM produces low-intent noise (95% tire-kickers) and risks itinerary IP theft.

---

## 2. Decision Outcomes & Architecture

### A. Zero-External-API Direct Fast-Lead Intake (`POST /api/v1/inbox/parse_social`)

- **Direct Intake Surface**: A lightweight, standalone web interface (`/intake/fast` or `/c/[creatorId]/plan`) that operates without external platform APIs.
- **Dual Operating Modes**:
  1. *Creator Fast-Paste Mode*: Creator copies raw DM text $\rightarrow$ pastes into `/intake/fast` widget/extension $\rightarrow$ AI generates proposal short-link in <15s.
  2. *Follower Self-Serve Direct Link Mode*: Creator places `waypoint.os/c/[creatorId]/plan` in link-in-bio or sends in DMs $\rightarrow$ Follower inputs raw text $\rightarrow$ AI generates proposal short-link.
- **Canonical Pipeline Integration (`motto_v4` Rule 0)**:

  ```text
  [ Raw DM / Quick Input ] 
            │
            ▼
  [ POST /api/v1/inbox/parse_social ]
            │
            ▼
  [ privacy_guard.py (SpaCy PII Scrubbing) ]
            │
            ▼
  [ src/intake/lifecycle.py (Slot & Budget Extraction) ]
            │
            ▼
  [ Spine API Persistence (TripStore) ]
  ```

---

### B. 2-Stage Teaser-to-Deposit Conversion Funnel

- **Stage 1 (Free Instant Teaser Surface)**:
  - Generates unauthenticated short URL: `/proposals/[proposalId]?token=tok_teaser_xyz`.
  - Displays glassmorphic UI, high-res photos, 96% Suitability Match score, 72-hour price lock countdown, and Visual Trust Badges (`[VERIFIED_PARTNER]`, `[PRICE_LOCK_72H]`).
  - **Property Masking (IP Protection)**: Supplier names and flight details are masked (e.g. *"5★ Luxury Riad in Medina"* instead of *"Royal Mansour"*).
- **Stage 2 (Deposit Unmask Gate)**:
  - Traveler places a $25–$50 refundable deposit (or 1-click Apple Pay hold).
  - Unmasks exact hotel/flight details, locks the 72-hour price guarantee, and unlocks 1-click booking confirmation. 100% of deposit applies toward the trip cost.

---

### C. Universal Autonomic Ghost Concierge Integration

- Concierge operations use a single canonical engine (`spine_api/routers/concierge.py`) serving all 4 Customer Personas (B2B Luxury Agencies, Corporate EAs, Creator Hosts, Direct B2C Travelers).
- **Autonomic Cascade Engine**: Flight delay detection $\rightarrow$ calculate downstream group transfer & dinner impact $\rightarrow$ push live SSE updates to `/group/[tripId]` portal.
- **3-Tier Autonomy Classification Matrix**:
  - *Tier 1 (Read-Only Informational)*: 100% automated flight tracking and group ETA recalculation.
  - *Tier 2 (Guarded Operational)*: Rescheduling shared shuttles, $0 fare-difference rebookings; executed per Host Switch.
  - *Tier 3 (Financial & Relationship)*: Out-of-pocket rebookings (>$100 delta), non-refundable cancellations; 100% mandatory human signoff.
- **Human Takeover Switch**: Operator cockpit (`/group/[tripId]/host-cockpit`) features a `[ ⚡ TAKEOVER / OVERRIDE ]` switch that pauses AI solvers and allows manual injection of custom offline solutions.

---

## 3. Consequences & Compliance

---

## 4. Autonomic Agentic Workflows & Inter-Engine Orchestration

The 2-stage teaser funnel and social lead fast-pass are fully integrated into Waypoint OS's multi-agent workforce ecosystem. The architecture supports 4 interconnected agentic flows:

```text
+--------------------------+     +--------------------------+
|  SocialInboundAdapter    | --> | Autonomic Ghost          |
|  (PII Scrub + Teasers)   |     | Concierge Watcher        |
+--------------------------+     +--------------------------+
             |                                |
             v                                v
+--------------------------+     +--------------------------+
| Yield Arbitrage Engine   | <-- | Karpathy AutoResearch    |
| (Wholesale Net Rates)    |     | Eval & Tuning Loop       |
+--------------------------+     +--------------------------+
```

1. **SocialInboundAdapter Agent**: Ingests DMs via extension fast-paste or direct links, scrubs PII via `src/security/privacy_guard.py`, extracts parameters (`src/intake/lifecycle.py`), and constructs 72h price-locked Stage 1 teasers.
2. **Autonomic Ghost Concierge Disruption Watcher (`spine_api/routers/concierge.py`)**: Continuously monitors executive flight status and group itineraries. Automatically detects delays (e.g. BA710 90m delay) and auto-reschedules ground shuttles or notifies affected travelers. Includes a 1-click **Manual Takeover Switch** in `/corporate/offsites` and `/group/[tripId]/host-cockpit` for operator manual control.
3. **Yield & Commission Arbitrage Engine (`spine_api/routers/yield_arbitrage.py`)**: Triggers upon Stage 2 deposit payment (`POST /api/v1/inbox/unmask_teaser`). Compares preferred DMC wholesale net rates against GDS rates to lock target margins ($250–$500 per booking).
4. **Karpathy AutoResearch Evaluation Loop (`src/evals/autoresearch_loop.py`)**: Evaluates proposal suitability score matches (e.g. 96% match score), deposit conversion rates, and per-diem policy audit compliance to continuously optimize prompt templates and extraction accuracy.

---

## 5. Standing Review: "Anything else?" (§0.11.1)

- **Q: Are all agentic workflows backwards-compatible with existing human operator dashboards?**
  - **Yes.** Every autonomic action emits a structured event to `AuditStore` and updates `TripStore`. Human operators can view, override, or revert any agent-initiated change at any time via the Host Cockpit.
- **Q: Does this implementation comply with `motto_v4` Rule 0 (Zero Shadow Pipelines)?**
  - **Yes.** All 4 agentic flows consume the same canonical API routes, Pydantic schemas, and persistence models without shadow databases or parallel LLM pipelines.

---

## 6. Update Log (Append-Only)

- **2026-08-03**: Initial ADR 18 approved & implemented. Added explicit specifications for Autonomic Agentic Workflows, Manual Takeover Switches, and Yield Arbitrage Integration (`motto_v4` §0.3.1).
