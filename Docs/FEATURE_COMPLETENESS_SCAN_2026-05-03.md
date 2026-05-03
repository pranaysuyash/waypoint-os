# Feature Completeness Scan — May 3 Delta from Baseline

**Date**: 2026-05-03
**Tool**: `comprehensive-audit/scripts/feature_scan.py` v2
**Catalog**: `comprehensive-audit/references/feature_catalog.json`
**Scope**: `travel_agency_agent` — full codebase scan (src/, spine_api/, frontend/, tests/)
**Status**: Complete

## Quick Numbers

- **Baseline (May 2)**: 49/200 (24.5%)
- **Automated score**: 0.64 (inflated — see caveats)
- **Honest estimate**: ~32% (0.32)
- **Direction**: +7.5 points from May 2
- **20 feature areas, 101 sub-features scanned**

---

## Automated Results (Sorted by Score)

| # | Area | Automated | Honest | Delta | Real Change? |
|---|------|-----------|--------|-------|--------------|
| J | Autonomy & Governance (D1) | 1.00 | 0.85 | +0.20 | No — baseline was already 8/10 |
| P | Analytics & Reporting | 1.00 | 0.40 | +0.80 | No — "engine/metrics/dashboard" matched broadly |
| T | Agency Marketplace | 1.00 | 0.00 | +1.00 | No — "network/partner" matched sourcing code |
| C | Revision Loop | 0.93 | 0.45 | +0.83 | Partial — snapshots landed, no diff engine |
| D | Visa & Documentation | 0.80 | 0.30 | +0.60 | No — "document/upload/passport" matched form fields |
| F | In-Trip Operations | 0.80 | 0.35 | +0.60 | No — "disruption/sentiment" matched frontier models |
| H | Sourcing Hierarchy | 0.80 | 0.40 | +0.70 | YES — SourcingPathResolver built since baseline |
| N | Output Delivery & Channels | 0.80 | 0.25 | +0.60 | No — "email" matched 237 lines of notifications |
| Q | Multi-Tenant Infrastructure | 0.80 | 0.70 | +0.20 | No — baseline was 6/10, nothing new |
| R | Production & Deployment | 0.80 | 0.55 | +0.40 | Partial — instrumentation.ts shipped |
| I | Per-Person Suitability | 0.64 | 0.55 | +0.14 | No — utility/wasted spend still zero |
| G | Post-Trip Memory | 0.60 | 0.25 | +0.30 | No — no new post-trip features |
| B | Draft Itinerary Creation | 0.57 | 0.20 | +0.47 | No — still no itinerary data model |
| A | Client Discovery & Intent Capture | 0.56 | 0.25 | +0.26 | No — PDF/voice/WhatsApp still zero |
| M | Evaluation & Quality (D6) | 0.35 | 0.25 | +0.15 | No — src/evals/ still doesn't exist |
| K | Free Engine / Trip Audit (D2) | 0.28 | 0.18 | +0.08 | No — no document extraction built |
| L | Override & Feedback (D5) | 0.27 | 0.27 | -0.03 | No change |
| E | Booking Coordination | 0.25 | 0.00 | +0.25 | No — "booking_readiness" matched field name only |
| S | Traveler-Facing Surfaces | 0.25 | 0.10 | +0.15 | No — no new traveler surfaces |
| O | Financial & Pricing | 0.20 | 0.15 | -0.10 | No — "margin" matched comments, no real code |

---

## What Actually Changed Since May 2

### Newly Shipped (6 items)

1. **H1: SourcingPathResolver** — `src/intake/sourcing_path.py` with SourcingTier enum, resolver class, single extension point. Signal still stub maturity but architecture is real.

2. **R3: Frontend telemetry** — `frontend/instrumentation.ts` rewritten with OTel SDK (BasicTracerProvider, OTLP HTTP exporter, auto-instrumentation).

3. **Q: Audit nav page enabled** — `nav-modules.ts` audit flag flipped to true. Real page at `frontend/src/app/(agency)/audit/page.tsx` fetches audit events from backend.

4. **Pipeline snapshots** — `_emit_audit_event` now takes `pre_state` and `post_state` params with `_snapshot_packet_state()`. No more hardcoded placeholder.

5. **LLM health ping** — `src/decision/health.py` calls real `create_llm_client().ping()` with circuit breaker gating and 60s cache.

6. **Secure member invites** — `membership_service.py` generates `secrets.token_urlsafe(32)` passwords + PasswordResetToken with 72h expiry.

### Real Score Impact

| Baseline | Honest Current | Delta |
|----------|---------------|-------|
| 24.5% | 32% | +7.5 |

The 6 shipped items span 4 feature areas (H, R, Q, C) and 2 infrastructure items. No P0 thesis gaps closed — per-person utility, wasted spend, itinerary rendering, eval harness, and PDF extraction remain at zero.

---

## Inflation Analysis — Why Automated = 0.64 but Honest = 0.32

### Broad Search Terms That Inflated Scores

| Term | Matches | What went wrong |
|------|---------|-----------------|
| `email` | 237 lines | Matched password reset, notifications, form field names — not email delivery |
| `engine` | 101 lines | Matched hybrid_engine, decision engine — not analytics engine |
| `dashboard` | 23 lines | Matched CSS classes and component names — not KPI dashboards |
| `network` | 5 lines | Matched sourcing_path tier enum — not agency marketplace |
| `partner` | 5 lines | Matched sourcing comments — not partner network |
| `portal` | 7 lines | Matched settings/onboarding code — not traveler portal |
| `document` | 46 lines | Matched PII comments, form field names — not document management |
| `upload` | 0 lines | False positive — none of these matched in context |

### What the Scanner Can't Do

- Distinguish "code exists" from "feature works"
- Detect whether code is wired end-to-end
- Know if a module is scaffolded vs operational
- Understand intent (is this a TODO or a real implementation?)

The catalog needs more precise, domain-unique terms. "pdfplumber" — good. "email" — bad. The scanner is correct; the terms need tuning.

---

## Feature Areas Still at Zero (Honest)

These areas have zero real implementation:

- **T**: Agency marketplace / network effects (Phase Z — intentional)
- **E**: Booking coordination (blocked on itinerary model)
- **B4**: Option generation (no option space construction)
- **B6**: Per-person suitability in output
- **I5**: Per-person utility percentage (thesis differentiator)
- **I6**: Wasted spend calculation (thesis differentiator)
- **A3-A5**: WhatsApp, PDF, voice intake
- **K3**: Document extraction for audit mode
- **K4**: Fit Score framework
- **K5**: Consumer presentation_profile
- **M2-M4**: src/evals/, golden paths, manifest runner
- **L2-L5**: OverrideEvent, feedback bus, storage, pattern detection
- **S2-S4**: Traveler portal, live brief, share links
- **O3-O5**: Payment state, quote machine, margin optimization

15 of 20 areas have at least one core sub-feature at zero.

---

## What Blocks the Next 20 Points

| Gap | Why |
|-----|-----|
| No itinerary data model | Blocks B (draft creation), E (booking), and visual output |
| No src/evals/ | Blocks quality claims on D2, D4, D6 |
| No PDF extraction | Blocks D2 audit mode (the GTM wedge) |
| No per-person utility | Blocks I5, I6 (thesis differentiators) |
| No output channels | Blocks N2-N5 (external delivery) |

These 5 gaps block approximately 20 points of honest score. The dependency order from the May 2 baseline audit is still correct: D6 eval harness first (unlocks quality measurement), then itinerary model + per-person utility (unlocks output rendering and thesis features), then PDF extraction (unlocks D2 audit mode wedge).

---

## Source Files

- Catalog: `/Users/pranay/.hermes/skills/software-development/comprehensive-audit/references/feature_catalog.json`
- Scanner: `/Users/pranay/.hermes/skills/software-development/comprehensive-audit/scripts/feature_scan.py`
- Skill: `/Users/pranay/.hermes/skills/software-development/feature-completeness-detection/SKILL.md`
- Prior baseline: `Docs/BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md`
- Master action plan: `Docs/BASELINE_MASTER_ACTION_PLAN_2026-05-02.md`

---

*This document — FEATURE_COMPLETENESS_SCAN_2026-05-03.md — is the authoritative delta from the May 2 baseline. Update the feature catalog when features ship and re-run the scanner to track progress.*
