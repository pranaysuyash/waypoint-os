# Feature Coverage + Research Audit

**Date:** 2026-05-12  
**Status:** Evidence review / planning artifact  
**Scope:** Codebase + docs + current external travel-tech signals. No production code changes.

## Executive Verdict

We do **not** have every feature covered.

The product is much better covered than the older May 2/May 3 audits imply, but coverage is uneven:

1. **Implemented and documented:** core intake/decision spine, operator shell, auth/team/workspace, D6 scaffold, itinerary option economics, public checker authority metadata, booking collection/tasks/documents/extraction, Product B KPI backend contract, route inventory/parity tooling.
2. **Implemented but not fully productized/rendered:** canonical itinerary option, per-person utility, wasted-spend math, D6 gate snapshots, documents module, booking/document extraction flows, Product B KPI definitions.
3. **Documented/researched but not fully implemented:** source adapter protocol, PDF/URL/WhatsApp/voice intake unification, proposal/versioning, communication composer/log, Trip Master Record, supplier/commission/rate intelligence, payments, traveler memory, policy/rights engine, visa/document authority integrations, real-time collaboration, full admin control plane.
4. **Under-researched or newly discovered:** travel document precheck provider strategy, IATA agency credential verification, multi-jurisdiction traveler-rights rules, package-travel obligations, consented personalization, agentic booking authorization boundaries, fraud/chargeback risk, supplier reliability scoring, mobile/offline field operations.

Coverage should now be measured as a **four-state matrix**, not a single score:

| State | Meaning | Product handling |
| --- | --- | --- |
| `implemented_documented` | Code exists, docs describe behavior, tests verify it. | Can be used as current ground truth. |
| `implemented_needs_productization` | Code exists, but UX/docs/integration are not complete. | Finish rendering, contracts, runbooks, and public limits. |
| `documented_not_implemented` | Docs/specs/research exist, but code is absent or scaffold-only. | Convert into atomic implementation tasks. |
| `frontier_research_needed` | Important domain capability is not yet researched enough. | Research first; do not build from guesses. |

## Instruction + Drift Baseline

Loaded and applied:

- `/Users/pranay/AGENTS.md`
- `/Users/pranay/Projects/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`

Additional repo-local agent files checked: no Qwen/Codex/Copilot instruction files were found beyond the files above.

Skill workflows used from local skill files:

- `/Users/pranay/.hermes/skills/product-strategy/wide-open-brainstorm/SKILL.md`
- `/Users/pranay/.hermes/skills/product-strategy/product-research-audit/SKILL.md`
- `/Users/pranay/.hermes/skills/product-strategy/opportunity-solution-tree/SKILL.md`
- `/Users/pranay/Projects/skills/search-first/SKILL.md`
- `/Users/pranay/Projects/skills/verification-before-completion/SKILL.md`

Read-only drift check found an active worktree with many modified/untracked files from parallel agents, including route extraction, D6 authority, Product B, documents module gates, frontend lint/typecheck, and new tests. This audit treats those live files as current evidence and avoids destructive or git-write actions.

## Fresh Verification Evidence

Commands run during this audit:

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
# 2026-05-12 09:23:28 IST

python3 tools/feature_scan.py . --json
# scanned_at: 2026-05-12
# current_overall: 1.0 for the scoped D6/itinerary/suitability progression catalog

uv run python tools/architecture_route_inventory.py --format json
# backend_route_count=146
# server_py_route_count=27
# router_module_route_count=119
# router_module_count=24
# bff_unmatched_backend_path_count=0
# potential_duplicate_backend_route_count=0

uv run pytest -q tests/test_itinerary_option_model.py tests/evals/test_d6_audit_scaffold.py tests/evals/test_public_authority.py tests/evals/test_d6_gate_snapshot.py tests/test_public_checker_contract_authority.py tests/test_product_b_events.py
# 36 passed in 3.59s

cd frontend && npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot
# 1 test file passed, 2 tests passed
```

Important interpretation: the repo-local feature scanner is useful only for the **scoped progression catalog** in `tools/feature_catalog.json`. It does not mean the whole product is complete.

## Current Coverage Matrix

| Product area | Code coverage | Doc coverage | Verdict | Evidence |
| --- | --- | --- | --- | --- |
| Core intake + NB decision spine | Strong | Strong | `implemented_documented` | `README.md`, `src/intake/`, `specs/canonical_packet.schema.json`, `specs/decision_policy.md` |
| Operator workbench / agency shell | Moderate/strong | Moderate | `implemented_needs_productization` | `frontend/src/app/(agency)/...`, `frontend/src/components/workspace/...`, `Docs/status/LEFT_SIDEBAR_NAV_CONTEXT_REVIEW_2026-05-12.md` |
| Auth/team/workspace/multi-tenant baseline | Moderate | Moderate | `implemented_documented` with RLS caveat | `spine_api/routers/auth.py`, `team.py`, `workspace.py`, `Docs/RLS_TENANT_ISOLATION_2026-05-04.md` |
| Route ownership / BFF parity | Strong | Strong | `implemented_documented` | `tools/architecture_route_inventory.py`, `Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md` |
| D6 eval scaffold | Partial/real | Strong | `implemented_needs_productization` | `src/evals/audit/`, `Docs/status/D6_ITINERARY_OPTION_PROGRESS_2026-05-11.md` |
| Public checker D6 authority | Partial/real | Strong | `implemented_needs_productization` | `src/evals/audit/public_authority.py`, `Docs/status/D6_PUBLIC_CHECKER_AUTHORITY_PROGRESS_2026-05-12.md` |
| Canonical itinerary option | Real model, limited runtime adoption | Strong | `implemented_needs_productization` | `src/suitability/models.py`, `src/suitability/options.py`, `tests/test_itinerary_option_model.py` |
| Per-person utility + wasted spend | Real deterministic baseline | Strong | `implemented_needs_productization` | `src/suitability/options.py`, `src/evals/audit/rules/activity.py` |
| Rendered itinerary/proposal output | Limited | Strong | `documented_not_implemented` / partial UI | `Docs/NEXT_FEATURE_PRIORITIZATION_2026-05-11.md`, `frontend/src/app/(agency)/trips/[tripId]/output` |
| Product B public checker + KPI backend | Moderate/real | Strong | `implemented_needs_productization` | `spine_api/product_b_events.py`, `spine_api/routers/product_b_analytics.py`, `Docs/status/PRODUCTB_KPI_SELF_DESCRIBING_CONTRACT_2026-05-12.md` |
| Document upload/extraction | Moderate/real | Strong | `implemented_needs_productization` | `spine_api/services/document_service.py`, `extraction_service.py`, document routes still in `server.py` |
| Documents module frontend | Real route shell | Strong | `implemented_needs_productization` | `frontend/src/app/(agency)/documents/`, `frontend/docs/status/*GATE_2026-05-12.md` |
| Booking collection/tasks/confirmations | Moderate/real | Strong | `implemented_needs_productization` | `spine_api/routers/booking_tasks.py`, `confirmations.py`, `public_collection.py`, `Docs/PHASE5A_BOOKING_EXECUTION_DESIGN_2026-05-09.md` |
| Trip Master Record | Fragmented | Strong | `documented_not_implemented` | booking/task/document/confirmation pieces exist, but no single master record surface |
| Source adapter protocol | Not found as canonical layer | Strong | `documented_not_implemented` | `Docs/NEXT_FEATURE_PRIORITIZATION_2026-05-11.md`, `Docs/research/INTEGRATION_SPEC_PROTOCOL_ADAPTER.md` |
| WhatsApp/email communication composer | Limited/manual helpers | Strong | `documented_not_implemented` | `Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md`, `Docs/UNIFIED_COMMUNICATION_AND_CHANNEL_STRATEGY.md`, `src/decision/whatsapp_formatter.py` |
| Traveler portal/live brief | Partial public surfaces | Strong | `documented_not_implemented` | `frontend/src/app/(traveler)/itinerary-checker/`, Product spec two-screen model not complete |
| Supplier/rate/commission intelligence | Light/scaffold | Moderate/strong | `documented_not_implemented` | sourcing docs, `src/intake/sourcing_path.py`, supplier docs under `Docs/industry_domain/` |
| Payments, billing, reconciliation | Mostly absent | Moderate | `documented_not_implemented` | `Docs/exploration/backlog.md`, booking/payment roadmap docs |
| Compliance/privacy/security | Partial | Strong | `implemented_needs_productization` | privacy gates, RLS docs, `src/security/privacy_guard.py`, missing full policy/runbook coverage |
| Admin/global control plane | Partial | Moderate | `documented_not_implemented` | `Docs/exploration/backlog.md`, `spine_api/routers/system_dashboard.py` |
| Agent runtime control plane | Partial/real | Moderate | `implemented_needs_productization` | `src/agents/runtime.py`, `spine_api/routers/agent_runtime.py`, backlog graph/SLO items |
| Analytics/reports | Moderate | Moderate | `implemented_needs_productization` | `spine_api/routers/analytics.py`, `frontend/src/app/(agency)/insights/` |
| Mobile/offline/PWA | Absent | Light/moderate | `frontier_research_needed` | backlog only |
| Internationalization/currency/localization | Limited | Moderate | `frontier_research_needed` | backlog, intake currency/date parsing notes |
| Customer/traveler memory | Limited | Strong | `documented_not_implemented` | lifecycle fields exist; no durable customer preference store |
| In-trip ops/disruption/emergency | Partial agent signals | Strong | `documented_not_implemented` | `src/agents/runtime.py`, disruption/crisis docs |

## First-Principles Gaps Still Worth Exploring

### 1. Trust Infrastructure Before More Autonomy

External 2026 signals support the repo thesis: AI is gaining planning adoption, but purchase trust remains the hard boundary. Deloitte reports accelerated gen-AI trip-planning adoption and increased privacy/consent pressure. Expedia/YouGov reports that 68% of surveyed travelers still prefer trusted travel brands over AI agents/chatbots at booking time, even when AI booking is available.

Implication: Waypoint should prioritize **operator-verifiable action packets, authority labels, provenance, and consented data use** before autonomous booking.

Next docs/tasks:

- Add a Product B public authority UX spec: authoritative vs advisory vs internal-only.
- Add a trust boundary map: read-only planning, operator-assisted execution, and future authorized action.
- Add a public claims policy: no finding category is marketed as authoritative unless D6 status is `gating` and threshold evidence is current.

Sources:

- Deloitte 2026 Travel Industry Outlook: https://www.deloitte.com/us/en/insights/industry/transportation/travel-hospitality-industry-outlook.html
- Expedia Group AI Trust Gap: https://expediagroup.com/investors/news-and-events/news/news-details/2026/Expedia-Group-Reveals-The-AI-Trust-Gap-Travelers-Embrace-AI-for-Planning-but-Rely-on-Trusted-Brands-to-Book/default.aspx
- Phocuswright 2026 technology trends: https://www.phocuswright.com/Travel-Research/Technology-Innovation/Travel-Innovation-and-Technology-Trends-2026

### 2. Travel Document + Visa Authority Layer

The repo has document extraction and document readiness concepts, but not a full authoritative travel-document precheck layer. IATA Timatic AutoCheck explicitly supports automated passenger checks for passport, visa, health, and restrictions and says it can integrate into booking/check-in/operational processes.

Implication: visa/document readiness should become a provider-backed, evidence-attached policy result, not only heuristic text.

Next docs/tasks:

- Create `Docs/research/TRAVEL_DOCUMENT_PRECHECK_PROVIDER_STRATEGY_2026-05-12.md`.
- Define provider strategy: Timatic-class API, fallback/manual mode, evidence retention, per-traveler result schema.
- Map precheck output into `decision.hard_blockers`, `documents` D6 category, booking readiness, and public checker authority.

Sources:

- IATA Timatic AutoCheck: https://www.iata.org/en/services/compliance/timatic/autocheck/
- IATA Travel Documentation / Travel Centre: https://www.iata.org/en/services/compliance/timatic/travel-documentation/

### 3. Agency Credential Trust

Supplier integrations, high-value actions, and marketplace/network effects need verified agency identity. IATA CheckACode WebService validates IATA issued codes against IATA agency data.

Implication: future supplier/API workflows should have an agency credential trust layer before high-risk automation.

Next docs/tasks:

- Add an agency credential model: credential type, source, verified status, expiry, evidence, scope.
- Define which actions require verified credentials vs soft warning.
- Keep normal agency users tenant-scoped; make super-admin credential reads audited.

Source:

- IATA CheckACode WebService: https://www.iata.org/en/services/data/travel-agent/global-data-products/checkacode-webservice/

### 4. Traveler Rights + Refund/Package Policy Engine

The backlog now includes DOT refund rules and EU package-travel obligations. These should not be one-off copy blocks. They need a versioned policy substrate.

Implication: cancellation/refund/disclosure should be policy-as-data with jurisdiction, effective date, trigger, obligation, deadline, and evidence requirements.

Next docs/tasks:

- Create `Docs/research/TRAVELER_RIGHTS_POLICY_ENGINE_2026-05-12.md`.
- Start with US DOT refund trigger rules and EU package-travel organizer obligations.
- Add tests with historical rule snapshots and jurisdiction overlap cases.

Sources:

- US DOT final refund rule PDF: https://www.transportation.gov/sites/dot.gov/files/2024-04/Final%20Rule%20Refunds%20and%20Other%20Consumer%20Protections%20%282105-AF04%29.pdf
- European Commission Package Travel Directive: https://commission.europa.eu/law/law-topic/consumer-protection-law/travel-and-timeshare-law/package-travel-directive_en
- Council of the EU 2026 package travel safeguards: https://www.consilium.europa.eu/en/press/press-releases/2026/03/30/consumer-protection-council-gives-final-sign-off-to-additional-safeguards-for-package-travel-users/

### 5. Competitive Workflow Baseline

Travel agency platforms commonly bundle itinerary, CRM, proposal, payments, supplier/content libraries, collaboration, and client communication. Travefy positions proposals/itineraries/CRM/marketing and supplier integrations as connected workflow; Sembark advertises itinerary builder, payment/collection tracking, and supplier/contracting management.

Implication: Waypoint's differentiation should not be "we have itinerary/CRM." It should be **risk-aware, utility-aware, authority-gated agency operations**.

Next docs/tasks:

- Update competitive matrix with capability parity vs differentiation:
  - itinerary/proposal builder
  - CRM/client profile
  - payments/collections
  - supplier library/contracts
  - documents/visa
  - risk audit + D6 authority
  - per-person utility/wasted spend
  - action packets/re-audit loop

Sources:

- Travefy travel agency software guide: https://travefy.com/blog-post/best-travel-agency-software
- Travefy product site: https://travefy.com/
- Sembark product site: https://sembark.com/

## Recommended Coverage Roadmap

### P0: Close Current Trust + Output Loop

1. Public checker UX consumes D6 authority metadata and visually separates authoritative/advisory/internal-only findings.
2. Render canonical `ItineraryOption` in operator output/workbench surfaces.
3. Convert per-person utility and wasted-spend from backend artifact to operator-visible decision support.
4. Add D6 fixtures/runners for pacing, logistics, documents, weather, and safety; keep categories `shadow` until evidence supports promotion.

### P1: Turn Fragmented Ops Into Durable Workflow

1. Implement Source Adapter protocol across text/PDF/URL/upload paths.
2. Build Trip Master Record from booking data, documents, extractions, confirmations, tasks, and execution events.
3. Add manual WhatsApp/email composer with communication log and follow-up scheduling.
4. Move remaining document/extraction routes from `server.py` into canonical routers after service-boundary review.

### P2: Build Domain Authority Layers

1. Travel document precheck integration strategy.
2. Agency credential verification strategy.
3. Supplier/rate/reliability knowledge model.
4. Versioned traveler-rights policy engine.

### P3: Expand Platform Surface

1. Global admin control plane.
2. Mobile/offline/PWA and field-agent flows.
3. Collaboration/comments/mentions/version history.
4. Internationalization, currency/date localization, multilingual intake.
5. Report builder and exports.

## Decision Notes

- Do not build a parallel public-checker, itinerary, document, or booking path. Extend canonical artifacts and routes.
- Do not treat scaffolded code as launch-ready. Use the code-ready / feature-ready / launch-ready distinction from `AGENTS.md`.
- Do not expand consumer-visible claims faster than D6 evidence.
- Do not treat older baseline docs as wrong; treat them as historical. Several items moved since May 2/May 3, but the gap framing remains useful.
- Treat external research as directional, not direct product requirements. The implementation path must be contract-driven inside this repo.

## Living Update Protocol

Future agents should update this audit by appending a dated addendum, not rewriting history.

For each feature, record:

```text
Feature:
State: implemented_documented | implemented_needs_productization | documented_not_implemented | frontier_research_needed
Code evidence:
Doc evidence:
Tests/verification:
Next atomic task:
Owner/notes:
```

When a feature moves state, cite the exact file paths and verification commands that prove the move.
