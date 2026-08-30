# Research & Exploration: Zero-Trust Capability Delegation across Multi-Agency B2B Travel Consortia

**Personas:** `PER-0933 & PER-0927: Boundary Systems & Human-AI Authority Architects`  
**System:** Waypoint OS (`pranaysuyash/travel_agency_agent`)  
**Date:** August 29, 2026  
**Status:** Canonical Specialist Exploration  

---

## 1. Problem Statement & Threat Model

In modern travel agency operations, host agencies delegate bookings to sub-agents, independent contractors, and corporate bookers. Sharing master API keys or global JWT tokens introduces severe attack vectors:
1. **Privilege Escalation**: An unverified sub-agent modifying payment routing or marking unpaid bookings as "PAID".
2. **Cross-Tenant Data Leakage**: Sub-agents browsing traveler profiles outside their assigned agency roster.
3. **Unbounded Financial Commitments**: Autonomous AI agents issuing non-refundable airline tickets without client payment pre-authorization.

---

## 2. Zero-Trust Scoped Capability Delegation Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            ZERO-TRUST CAPABILITY TOKEN MODEL                                │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│ 1. Immutable Subject Claims   │ 2. Scoped Action Bitmask      │ 3. Cryptographic Signature  │
│    - trip_id, agency_id       │    - VIEW_ONLY (0x01)         │    - HMAC-SHA256 / Ed25519  │
│    - traveler_id, role        │    - PROPOSE_EDIT (0x02)      │    - Replay-protected nonce │
│    - TTL expiration timestamp │    - AUTHORIZE_PAYMENT (0x08) │    - Instant revocation     │
└───────────────────────────────┴───────────────────────────────┴─────────────────────────────┘
```

### 2.1 The 5-Tier Human-AI Authority Evaluation
Every consequential system operation is evaluated against the 5-Tier Human-AI Authority Matrix before execution:
* **Tier 0 (Autonomous)**: AI parses, plans, searches, and validates without human gating.
* **Tier 1 (Recommendation)**: AI synthesizes alternative routes; human operator reviews before dispatch.
* **Tier 2 (Operator Sign-off)**: Rebooking or sending formal quote to traveler requires operator confirmation.
* **Tier 3 (Client Authorization)**: Payment processing or contractual acceptance requires explicit traveler signature.
* **Tier 4 (Dual Control)**: High-value refund (> \$500) or manual rate override requires two distinct human managers.

---

## 3. Production Recommendations
* Enforce capability token verification on all `/api/v1/` routes.
* Log all authority evaluations into immutable audit tables.
