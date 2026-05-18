# External Review Brief: Coming-Soon Readiness Contracts

Date: 2026-05-17
Owner: Pranay + Hermes
Scope: Non-coding planning quality check before module-contract drafting

## Decision
External help is optional, not required.

Reason:
- We already have enough internal evidence (code + docs + tests + exploration-map audit) to start drafting Bookings-first readiness contract.
- External review is still useful as a challenge function for architecture, sequencing, and hidden assumptions.

## What to ask external reviewer (ChatGPT)
Use this prompt exactly:

"""
You are reviewing a pre-implementation planning package for a travel-agency platform.
This is NOT a coding task. Do not suggest code patches first.

Goal:
Critique and strengthen the readiness-contract approach for 5 planned modules:
1) Bookings
2) Payments
3) Quotes
4) Suppliers
5) Knowledge Base

Context summary:
- These modules are present in navigation as planned/disabled.
- Runtime capability is partial and currently embedded in other surfaces.
- We need canonical module contracts before feature build.

Your tasks:
1) Validate or challenge the proposed order (Bookings -> Payments -> Quotes -> Suppliers -> Knowledge Base).
2) Identify hidden coupling/ownership risks if Bookings is elevated first.
3) Define minimum contract gates that must be met before enabling each module in nav.
4) Provide a risk matrix (severity x likelihood x detectability) for each module.
5) Propose a phased rollout strategy with rollback triggers.
6) Highlight missing observability/operational gates.
7) Call out any anti-patterns (surface-first rollout, duplicate ownership, schema drift).

Output format:
A) Verdict (keep order / change order) with reasons
B) Top 10 risks (ranked)
C) Contract gate checklist per module
D) Rollout + rollback plan
E) What to defer intentionally (non-goals)
F) 5 critical questions we must answer before implementation

Constraints:
- Prefer first-principles architecture over patchwork.
- Avoid speculative abstraction unless justified by 2+ modules.
- Optimize for long-term maintainability and operational clarity.
"""

## Files to provide as context
Primary audit artifacts:
- /Users/pranay/Projects/travel_agency_agent/Docs/review/COMING_SOON_FEATURES_STATUS_ARCHITECTURE_REVIEW_2026-05-17.md
- /Users/pranay/Projects/travel_agency_agent/Docs/review/EXPLORATION_MAP_CODEBASE_AUDIT_2026-05-17.json

Planning/status references:
- /Users/pranay/Projects/travel_agency_agent/Docs/status/LEFT_SIDEBAR_NAV_CONTEXT_REVIEW_2026-05-12.md
- /Users/pranay/Projects/travel_agency_agent/Docs/status/FEATURE_LIST_V2_2026-05-12.md
- /Users/pranay/Projects/travel_agency_agent/Docs/exploration/backlog.md

Implementation evidence anchors:
- /Users/pranay/Projects/travel_agency_agent/frontend/src/lib/nav-modules.ts
- /Users/pranay/Projects/travel_agency_agent/frontend/src/components/layouts/Shell.tsx
- /Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx
- /Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/BookingExecutionPanel.tsx
- /Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/ConfirmationPanel.tsx
- /Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/PaymentTrackingCard.tsx
- /Users/pranay/Projects/travel_agency_agent/spine_api/routers/booking_tasks.py
- /Users/pranay/Projects/travel_agency_agent/spine_api/routers/confirmations.py
- /Users/pranay/Projects/travel_agency_agent/spine_api/services/booking_task_service.py
- /Users/pranay/Projects/travel_agency_agent/spine_api/services/confirmation_service.py

## How to use external feedback
- Treat it as critique input, not authority.
- Accept only points that are evidence-backed and compatible with current runtime reality.
- Capture accepted/rejected points with reason in next local planning doc.

## Expected internal next step after feedback
- Draft: /Users/pranay/Projects/travel_agency_agent/Docs/review/COMING_SOON_READINESS_CONTRACT_01_BOOKINGS_2026-05-17.md
- Then replicate template for Payments, Quotes, Suppliers, Knowledge Base.
