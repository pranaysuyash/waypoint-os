# Random Document Audit V4 — Product-B KPI Slice-F Completion

## Audit provenance

- Audit date: 2026-09-03
- Audit timestamp: 2026-09-03T21:30:32+05:30
- Project: `/Users/pranay/Projects/travel_agency_agent`
- Selected document: `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEF_PRODUCTB_KPI_COMPLETION_2026-05-08.md`
- Selected document SHA-256: `08ffdbbb43ff36ec39c841277e451233efa3b1f67cc8c45fe47367b8d7be6f0e`
- Selection method: deterministic SHA-derived selection from a current, implementation-relevant Markdown candidate pool
- Selection seed: `2026-09-03-random-document-audit-v4`
- Candidate pool: 217 documents after excluding prior random audits, generated context, archives, and other audit/meta artifacts
- Selected sorted index: 122
- Current repository HEAD observed: `2f9a6384b42a90db415fbf012d94b60b5eaaa3bc`
- Repository state: dirty before this audit; unrelated concurrent changes were preserved and not staged, committed, reset, checked out, or overwritten
- Primary review workflows:
  - `/Users/pranay/Projects/skills/exploration-doc-review/SKILL.md`
  - `/Users/pranay/.codex/skills/product-discoverability-audit/SKILL.md`
  - `/Users/pranay/.codex/skills/product-discoverability-audit/references/discoverability-rubric.md`
- Review doctrine: canonical `REVIEW_DOCTRINE.md`, internal version 1.1
- Documentation doctrine: canonical `DOCUMENTATION_DOCTRINE.md`, internal version 1.1
- Generated mechanical inventory: `Docs/review/assets/random_document_audit_v4_productb_kpi_exploration.json`
- Provenance: current checkout inspection, source/test inspection, OpenAPI and route introspection, current local data-shape inspection, controlled temporary-store falsification, and fresh focused tests; no hosted, production, real-user, or provider proof was performed

## Executive verdict

The selected document is a credible historical implementation checkpoint for the Server.py refactor: the extracted router still exists, the route is still wired, the focused behavior tests pass, and the handler’s documented query/dependency shape remains substantially intact.

It is not safe to treat the document as a current product-completion or release-readiness statement without qualification. Three current gaps change the meaning of the slice:

1. The KPI endpoint accepts an authenticated agency dependency and then discards it. The underlying file-backed event store aggregates by inquiry across the entire normalized event file and has no workspace/agency filter. A controlled two-workspace experiment produced one combined KPI sample, demonstrating that the endpoint’s authority boundary is not expressed by its implementation.
2. The frontend route map contains a BFF mapping, but the current agency Insights page has no Product-B KPI hook, API client, card, panel, page, definition display, loading state, empty state, error recovery, or next action. The capability exists behind a routing entry rather than as a discoverable operator journey.
3. The document’s verification instructions are now stale. The documented historical snapshot was `131` routes / `115` OpenAPI paths; the current snapshot reports `340` routes / `310` OpenAPI paths. The documented snapshot command also fails in the current ambient environment unless `PROPOSAL_SIGNING_KEY` is supplied, because the script does not bootstrap that required non-production setting.

### Decision

- Router extraction: **GO with conditions**. The narrow refactor remains present and the current focused regression lane is green.
- Product-B KPI capability: **NO-GO as a product-complete operator feature** until scope ownership, tenant semantics, typed contract, visible reporting surface, and end-to-end proof are resolved.
- Immediate disposition: **redesign/implement a bounded hardening slice**, beginning with an explicit global-versus-agency contract decision. Do not add a dashboard against an unresolved metric authority boundary.

This is a review-only audit. No implementation changes were made to the selected document, source code, tests, or existing documentation.

## 1. Review charter and scope

### Objective

Determine whether the selected status document still describes current code and current product behavior, and audit the documented capability across implementation truth, contract truth, discoverability, user value, verification quality, and remaining risk.

### In scope

- The selected Slice-F status document and every claim made in it.
- The extracted Product-B analytics router and Server.py wiring.
- Product-B event storage, grouping, filtering, KPI computation, and data authority.
- Focused backend tests and route/OpenAPI behavior.
- Frontend BFF mapping and the agency Insights surface.
- Current local event-data shape, with no raw payloads copied into this report.
- Historical/current documentation contradictions that affect safe use of the selected document.

### Out of scope

- Changing implementation, tests, product UI, schemas, permissions, or documentation.
- Git staging, commits, pushes, branch/worktree operations, or cleanup.
- Hosted deployment, production data, real-user behavior, external providers, browser/device visual proof, billing, and release approval.
- Re-reviewing every unrelated Server.py refactor slice.

### Stop conditions

The audit stops at evidence-backed findings and an atomic task package. It does not silently turn a review into implementation work or infer production readiness from local tests and local files.

## 2. Evidence register

Evidence labels use the project review taxonomy: `Observed`, `Verified`, `Inferred`, `Proposed`, `Unknown`, or `Contested`. Tier numbers describe evidence strength for this audit, not product readiness. The focused test lane is sensitivity `S1` (bounded integration/regression); tenant isolation, UI discoverability, and release claims are `S2`/`S3` concerns and are not established by that lane.

| ID | Evidence | Truth status | Tier / sensitivity | Result |
|---|---|---|---|---|
| E-01 | Selected status document, lines 1-87 | Observed | Tier 1 / S1 | Historical Slice-F extraction, acceptance, non-goals, counts, and stop condition are explicitly recorded. |
| E-02 | `spine_api/routers/product_b_analytics.py` | Verified | Tier 1 / S2 | Router, path, query bounds, agency dependency, and delegation are present. |
| E-03 | `spine_api/server.py` | Verified | Tier 1 / S2 | Current canonical import and `include_router` wiring are present; no in-file handler remains. |
| E-04 | `tests/test_product_b_analytics_router_behavior.py` | Verified | Tier 2 / S1 | Signature/dependency shape and query delegation are tested using a mocked store response. |
| E-05 | `tests/test_product_b_events.py` | Verified | Tier 2 / S1 | Event validation, deduplication, qualified filtering, KPI buckets, definitions, auth, and endpoint payload behavior have focused coverage. |
| E-06 | Fresh route/OpenAPI snapshot | Verified | Tier 2 / S1 | Current runtime reports 340 routes and 310 OpenAPI paths; Product-B route is present. |
| E-07 | Fresh documented test matrix | Verified | Tier 2 / S1 | `38 passed in 4.50s` across the five documented test files. |
| E-08 | Fresh ambient snapshot attempt | Verified | Tier 2 / S1 | The documented snapshot command fails without `PROPOSAL_SIGNING_KEY`; rerun succeeds only with an explicitly ephemeral audit key. |
| E-09 | Controlled temporary-store experiment | Verified | Tier 2 / S2 | Events from `agency-A` and `agency-B` are combined by `compute_kpis`; no workspace filter exists in `list_events` or `compute_kpis`. |
| E-10 | Frontend route map, catch-all proxy, agency Insights page, hooks/types | Verified | Tier 1 / S2 | A BFF mapping exists, but no current Product-B KPI consumer or visible reporting surface was found. |
| E-11 | Later Product-B contract status note, lines 71-75 | Observed | Tier 1 / S2 | It explicitly leaves frontend reporting, public response typing, and richer exclusion signals as follow-up work. |
| E-12 | Current local normalized event file | Observed | Tier 1 / S3 | 887 local rows span multiple workspace identifiers; this is local file evidence only, not production or real-user evidence. |

### Automated inventory caveat

The required `exploration-doc-review` script was run in `auto` mode. It indexed 715 files and mechanically emitted 12 feature items: 10 `FIX`, 0 `GO`, 0 `MAYBE`, and 2 `NO-GO`, with 11 apparent status-drift indicators. Manual inspection showed that its parser promoted document section headings such as “Scope implemented,” “Files changed,” “Verification executed,” and “Acceptance update” into pseudo-features and matched unrelated files. Its JSON output is therefore retained as a reproducible inventory artifact, not accepted as the audit verdict. The findings below come from manual claim-to-source verification and controlled tests.

## 3. What the selected document claims

The document says that, on 2026-05-08:

- only `GET /analytics/product-b/kpis` moved out of `server.py`;
- `spine_api/routers/product_b_analytics.py` and its behavior test were added;
- the path, function name, `window_days` bounds, `qualified_only` flag, and `get_current_agency` dependency were preserved;
- the handler intentionally discards the agency object and delegates to `ProductBEventStore.compute_kpis`;
- there is no response model, permission dependency, rate-limit decorator, or persistence write in the handler;
- a five-file test matrix passed 22 tests in 4.82 seconds;
- the snapshot contained 131 routes and 115 OpenAPI paths;
- no public checker, agent runtime, settings, `/run(s)`, startup/lifespan/app-factory/middleware, or cleanup/hardening work was mixed into Slice F;
- Slice F was accepted as an isolated refactor, while Phase 3 remained in progress.

As a historical extraction record, these claims are internally coherent. The audit question is whether they can still be read as present-tense product truth. They cannot, without separating “the extraction remains” from “the capability is safe, visible, scoped, and release-ready.”

## 4. Current claim-to-code reconciliation

| Document claim | Current truth | Status and consequence |
|---|---|---|
| Extracted router exists at the documented path | `spine_api/routers/product_b_analytics.py` exists and defines `get_product_b_kpis` | **Verified.** The narrow refactor survived. |
| Endpoint is wired into the app | `server.py` imports the router from `spine_api.routers`, retains a fallback loader, and includes `product_b_analytics_router.router` | **Verified with drift.** Wiring exists, but the documented normal import `from routers ...` is no longer the current spelling. |
| Query contract is preserved | OpenAPI exposes `window_days` default 30, min 1, max 365 and `qualified_only` default false | **Verified.** |
| Agency dependency is part of the route contract | Route depends on `get_current_agency` and invalid/missing auth returns 401 in the focused lane | **Verified.** The dependency’s business effect is not verified because the handler discards the resolved agency. |
| `ProductBEventStore.compute_kpis` is the source of the response | Router delegates directly to it | **Verified.** This exposes the store’s global aggregation behavior through an agency-authenticated route. |
| No response model is present | OpenAPI has no typed response schema for this operation; responses are only 200/422 plus security metadata | **Verified.** This is acceptable for a historical extraction boundary but weak for a BFF-consumed product contract. |
| No permission dependency or route rate limit is present | The route has only `get_current_agency`; no route-local permission or rate-limit decorator | **Verified.** Whether that is correct depends on the unresolved global-versus-agency audience decision. |
| The handler performs no persistence writes | Handler delegates to a read computation only | **Verified.** The underlying store reads the normalized JSONL file. |
| Five-file matrix passed 22 tests | Same command currently passes 38 tests in 4.50 seconds | **Verified, historical count superseded.** The current receipt is stronger for this bounded lane; it does not establish tenant, UI, browser, hosted, or release proof. |
| Snapshot is 131 routes / 115 OpenAPI paths | Current rerun reports 340 routes / 310 OpenAPI paths | **Historical baseline only.** The document needs freshness labeling and a maintained snapshot procedure. |
| Documented snapshot command is executable as written | Current ambient invocation fails because `PROPOSAL_SIGNING_KEY` is missing; an ephemeral non-production key makes it run | **Verified drift.** The verification recipe is not self-contained in the current environment. |
| Non-goals and isolation condition still describe all current state | The current repository has substantial unrelated dirty Server.py and infrastructure/frontend work | **Not re-verified as a present-tense claim.** The Slice-F historical patch may remain isolated, but the current checkout is not a clean isolated release candidate. |

## 5. Current system reconstruction

The current path is:

```text
public checker
  -> ProductBEventStore.log_event(workspace_id)
  -> data/product_b_events/events_normalized.jsonl
  -> ProductBEventStore.list_events(window_days)
  -> group globally by inquiry_id
  -> ProductBEventStore.compute_kpis(window_days, qualified_only)
  -> authenticated GET /analytics/product-b/kpis
  -> frontend BFF mapping /api/insights/product-b/kpis
  -> no current agency Insights consumer
```

The store’s envelope requires and preserves `workspace_id`, but `list_events` filters by time, event name, inquiry, and trip only. It does not accept an agency/workspace filter. `_group_by_inquiry` groups only on `inquiry_id`. The route receives `agency: Agency` and immediately assigns it to `_`, so authentication establishes a request context without establishing metric scope.

The local normalized file currently contains 887 rows, 667 unique inquiries, and multiple workspace identifiers, including `public-checker` and two UUID-like identifiers. Those values prove that the local store contains more than one scope; they do not prove the rows are production or real-user data.

## 6. Product discoverability audit

### Product charter used for this slice

Product-B instrumentation exists to measure whether an evidence-backed traveler artifact becomes an agency-revisable action and whether that wedge creates Product-A demand. The useful product outcome is not merely “the endpoint returns JSON”; it is that the accountable operator can inspect trustworthy signals, understand what they mean, and take the next product or operational action.

### Capability and affordance map

| Capability | Exists | Recognition cue | Placement | Invocation | Result semantics | Feedback / recovery | Assessment |
|---|---:|---|---|---|---|---|---|
| Fetch Product-B KPIs | Yes | Weak; no visible Product-B label in current agency UI | BFF route map only; absent from rendered Insights page | Technically available through a mapped API path | JSON includes values, sample, counts, and definitions, but no response model | No visible loading, empty, error, retry, or “what next” state found | Hidden and fragmented; `D1`/`D4` |
| Understand KPI formulas | Partly | Definitions exist in backend response and store tests | Not placed in a user-facing surface | No frontend consumer currently invokes it | Definitions are useful but not schema-typed | No visible explanation of unknown/dark-funnel or data freshness | Contract exists; product explanation does not |
| Trust metric scope | No | Agency authentication suggests an agency-scoped reading | Route sits beside agency Insights mappings | Any authenticated agency request can invoke it | Current implementation combines multiple workspaces | No scope label, permission explanation, or warning | Ambiguous authority boundary; `D2`/`D7` |
| Act on KPI result | No | No result surface or CTA | No Product-B panel/page | No discoverable operator invocation | No next action or linked inquiry sample | No recovery or drill-through | Continuity gap; `D5`/`D6` |

### Discoverability chain

The chain required by the product review skill is:

`need → recognition → cue → label → placement → invocation → result → explanation → next action/recovery`

For an agency operator or product analyst, the current chain breaks after technical invocation. The BFF mapping supports invocation by a caller who already knows the path, but there is no visible recognition, placement, explanation, or next action. A route-map entry is infrastructure discoverability, not product discoverability.

### Persona lens

| Persona | Need | Current experience | Finding |
|---|---|---|---|
| Agency operator / owner | Know whether Product-B exposure is producing useful agency-side outcomes | Current Insights page shows generic pipeline, revenue, team, and bottleneck views; no Product-B KPI surface | Product-B value is invisible in the operator workflow (`D1`, `D4`, P1). |
| Product / operations analyst | Compare forwardability, observed revision, dark funnel, and Product-A pull-through with formula context | Can call a hidden endpoint, but cannot rely on an explicit scope or typed response contract | Analysis is possible only through technical knowledge and manual API access (`D2`, `D5`, P1). |
| Security / workspace administrator | Ensure an authenticated workspace sees only the metrics it is authorized to see | Route resolves an agency but store aggregates globally; no explicit permission/audience contract | Metric authority is ambiguous and potentially misleading or cross-tenant (`D7`, P1). |
| Traveler / first-time Product-B user | Receive a credible action artifact and have the agency response measured accurately | This document does not claim to ship the traveler flow; the audit found instrumentation storage but did not perform browser proof | Traveler outcome and event provenance remain outside this slice’s verified scope (`Unknown`, S3). |

## 7. Findings

### FINDING P1 — Authenticated agency context is dead, while KPI aggregation is global

- Category: contract, tenancy, trust, security/privacy boundary
- Discoverability class: `D2` ambiguous; `D7` system drift
- Truth: `Verified` for implementation; `Contested` for intended product scope
- Evidence: E-02, E-05, E-09, E-12
- Current behavior: `get_product_b_kpis` depends on `get_current_agency`, then discards `agency`. `compute_kpis` calls unscoped `list_events`, groups by inquiry globally, and computes over the shared normalized JSONL file.
- Falsification: A controlled temporary store with qualifying events from `agency-A` and `agency-B` returned a combined sample of two inquiries from both workspaces. The store signature also confirms that `list_events` has no workspace parameter.
- Why it matters: An agency-facing consumer can reasonably interpret the route as “my agency’s KPIs” while receiving cross-workspace totals. If the intended audience is a global Product-B operator, the current agency dependency and agency Insights/BFF placement communicate the wrong authority boundary instead.
- User/business consequence: operators may make decisions from numbers that do not describe their workspace; analysts may compare incomparable populations; a future UI could expose cross-tenant information without an explicit product/security decision.
- Immediate mitigation: Declare the route audience and scope in the canonical API/product contract before adding consumers. Label the current route as internal/global or agency-scoped only according to that decision.
- Proper fix direction: Either add an explicit workspace/agency filter and enforce the corresponding permission, or move the capability to a deliberately global/admin surface with a global authorization dependency and explicit scope in the response. Do not leave the agency argument as dead context.
- Acceptance evidence required: per-workspace isolation tests using two workspaces, an authorization matrix, a response scope field, and an integration request that proves the caller cannot read another workspace’s KPI sample.
- Priority: `P1` because this is a trust and potentially cross-tenant correctness issue.

### FINDING P1 — Product-B KPI capability is hidden behind infrastructure and absent from the operator journey

- Category: product discoverability, continuity, reporting UX
- Discoverability class: `D1` hidden; `D4` fragmented; `D5` feedback gap; `D6` recovery gap
- Truth: `Verified`
- Evidence: E-10, E-11
- Current behavior: `frontend/src/lib/route-map.ts` maps `insights/product-b/kpis` to `analytics/product-b/kpis`, and the catch-all proxy will forward mapped paths. The agency Insights page currently fetches and renders generic insights only; no Product-B KPI hook, API client, type, panel, page, definition view, empty state, error state, retry, or drill-through was found.
- Why it matters: The backend capability cannot create operator value if the intended operator has no cue, placement, or safe interpretation path. A technically reachable endpoint is not a discovered product capability.
- User/business consequence: Product-B learning remains invisible to the agency team, the Product-A pull-through loop cannot be operationally inspected, and users must know an undocumented API path to access the feature.
- Immediate mitigation: Keep the BFF mapping from being treated as completion evidence. Add the missing consumer only after the scope/authority finding is resolved.
- Proper fix direction: Add a visible Product-B section or route in the canonical Insights experience with human labels, formula definitions, scope/freshness context, explicit no-data/unknown states, permission-aware errors, and a next action such as opening the relevant inquiry sample or review queue.
- Acceptance evidence required: frontend API contract test, component tests for loading/empty/unknown/error states, browser evidence at the actual agency route, and a user-facing check that the displayed scope matches the backend authorization.
- Priority: `P1` for the intended learning loop; `P2` if Product-B reporting is intentionally deferred and the status/docs explicitly say so.

### FINDING P2 — Response contract is self-describing in code but not typed at the API boundary

- Category: API contract, integration durability, documentation drift
- Discoverability class: `D2` ambiguous semantics; `D5` feedback gap
- Truth: `Verified`
- Evidence: E-02, E-04, E-05, E-11
- Current behavior: The store returns values, sample data, counts, confidence tiers, and definitions. The route has no `response_model`; OpenAPI therefore exposes no structured response schema. Focused router tests monkeypatch `compute_kpis` and verify selected fields rather than the actual full response contract.
- Why it matters: The later self-describing contract work improves human interpretation, but a BFF/frontend consumer still has no generated or runtime-checked boundary for null KPI values, unknown outcomes, scope, freshness, or future additive changes.
- User/business consequence: consumers can silently drift from backend semantics, and the UI may display a mathematically valid value without the context needed to trust it.
- Proper fix direction: Define a typed response model that includes explicit scope, data freshness/source, sample semantics, nullable/no-data KPI fields, definitions, and confidence/unknown states. Generate or manually align the frontend type against the verified response.
- Acceptance evidence required: OpenAPI schema inspection, contract test against the real store response, frontend type check, and a no-data/unknown sample test.
- Priority: `P2`; raise to `P1` when the endpoint becomes a supported public-facing or customer-visible contract.

### FINDING P2 — Verification recipe and counts are historical, and the documented command is not self-contained

- Category: verification drift, documentation freshness, release evidence
- Discoverability class: `D7` system drift
- Truth: `Verified`
- Evidence: E-01, E-06, E-07, E-08
- Current behavior: The selected document records 22 tests and a 131/115 route snapshot from 2026-05-08. The same five-file command currently passes 38 tests in 4.50 seconds. The snapshot command fails in the current environment before inspection because `PROPOSAL_SIGNING_KEY` is required during app import; supplying an ephemeral audit-only key produces 340 routes and 310 OpenAPI paths.
- Why it matters: A future reviewer may mistake the historical counts for current inventory or conclude the verification procedure is broken for an unrelated reason. The document also says “implemented and verified” without an explicit historical-baseline qualifier.
- User/business consequence: stale evidence can create false confidence in refactor completeness and makes route drift harder to detect.
- Proper fix direction: Preserve the historical checkpoint, label its counts as point-in-time, update the canonical runbook/snapshot script to perform a safe non-production configuration preflight, and record current counts in a new status/review entry rather than overwriting history.
- Acceptance evidence required: fresh command succeeds in a clean documented environment, required variables are explicit and non-production-safe, output labels its timestamp/commit, and current route inventory is reconciled against the intended baseline.
- Priority: `P2`; raise to `P1` for a release gate that depends on route parity.

### FINDING P2 — Focused tests prove extraction parity but do not prove the complete product contract

- Category: test oracle, integration coverage, product evidence
- Discoverability class: `D5` feedback gap; `D7` evidence drift
- Truth: `Verified` for the gap
- Evidence: E-04, E-05, E-07, E-09, E-10
- Current coverage: Tests cover route signature/dependency shape, query delegation, auth failures, event validation, deduplication, qualified filtering, outcome buckets, definitions, and mocked endpoint payloads.
- Missing or not independently proven in this lane: cross-workspace isolation, authorization matrix, actual unmocked endpoint-to-store contract, typed OpenAPI response, empty/no-data response semantics, stale-data/freshness behavior, frontend rendering, browser route reachability, and user-facing recovery.
- Why it matters: The selected document’s acceptance is valid for a narrow refactor slice, but the same green lane cannot support a product-complete KPI claim.
- Proper fix direction: Keep extraction tests separate from product contract tests. Add one bounded matrix for scope/permission and one for real response/UI behavior.
- Acceptance evidence required: explicit test-to-claim mapping with sensitivity tier; no single aggregate “pass” count used as release proof.
- Priority: `P2`.

## 8. Contradictions and status drift

| Source | Statement | Current interpretation |
|---|---|---|
| Selected Slice-F document | “Implemented and verified,” 22 tests, 131/115 snapshot | Accurate as a historical 2026-05-08 checkpoint; stale as present-tense inventory. |
| `Docs/status/PRODUCTB_KPI_SELF_DESCRIBING_CONTRACT_2026-05-12.md` | Backend contract is complete; frontend reporting and response model remain follow-up | Consistent with this audit and useful corroborating evidence. |
| Current frontend route map | Product-B KPI BFF mapping exists | Infrastructure path exists, but it does not prove a rendered product surface. |
| Current agency Insights page | Generic metrics only | Confirms the visible Product-B reporting gap. |
| Current store implementation | `workspace_id` is stored, but KPI computation is unscoped | Confirms authority ambiguity; the intended scope must be decided rather than inferred. |
| Current repository state | Large unrelated dirty changes are present | The selected document’s “Slice-F-isolated patch” condition cannot be used as a current release-candidate claim without classifying those changes. |

No existing historical document was overwritten or “corrected” during this audit. The selected status note should remain as historical evidence; a follow-up status note should carry current truth once the contract and UI decisions are made.

## 9. Priority task package

The tasks below are deliberately ordered by dependency. They are recommendations from this review, not changes authorized or performed in this turn.

### Task 1 — Decide the canonical KPI audience and authority boundary

- Owner: product + architecture + security/privacy
- Scope: Decide whether `/analytics/product-b/kpis` is agency-scoped or global/internal.
- Must settle: workspace key (`agency_id`, `workspace_id`, or another canonical owner), permitted roles, whether public-checker events are shared or partitioned, whether the BFF mapping belongs under agency Insights, and what “qualified sample” means per scope.
- Exit evidence: an ADR/status decision with one canonical route ownership and explicit rejected alternative.

### Task 2 — Implement and prove the chosen scope/permission model

- Owner: backend
- Scope: Add filtering and authorization, or move the endpoint to an explicitly global/admin route.
- Exit evidence: two-workspace isolation test, positive/negative authorization tests, response scope metadata, and real endpoint integration against isolated data.
- Dependency: Task 1.

### Task 3 — Stabilize the typed response contract

- Owner: backend/API contract
- Scope: Add a response model/schema for KPI values, definitions, sample, unknown/no-data state, scope, and freshness/source.
- Exit evidence: OpenAPI schema, contract regression, and frontend type alignment.
- Dependency: Task 1; should follow or accompany Task 2’s scope decision.

### Task 4 — Build the visible Product-B reporting journey

- Owner: frontend/product design
- Scope: Add the canonical hook/client, visible placement in Insights, human labels, formula definitions, scope/freshness cues, loading/empty/error/retry states, and a useful next action.
- Exit evidence: component tests plus browser proof at the actual agency route with authenticated state and a controlled known dataset.
- Dependency: Tasks 2 and 3.

### Task 5 — Expand the product evidence lane

- Owner: QA/review
- Scope: Add negative query bounds, empty/stale data, duplicate/retry, unknown outcome, cross-workspace, frontend contract, and browser reachability coverage. Keep extraction parity tests separately named.
- Exit evidence: claim-to-test matrix with S1/S2/S3 sensitivity and explicit unproven gates.
- Dependency: Tasks 2-4.

### Task 6 — Refresh the historical status/runbook boundary

- Owner: documentation/release
- Scope: Leave the 2026-05-08 checkpoint intact, add a current follow-up status, label historical route counts, and make the snapshot command’s safe environment preflight explicit.
- Exit evidence: reproducible command succeeds from the documented setup and records timestamp/commit/config provenance.
- Dependency: Task 5, or immediately after Task 1 if the runbook is blocking other reviewers.

## 10. Explore versus build decision

This should move to **bounded implementation after one explicit contract decision**, not directly to UI construction.

The extraction itself is already implemented and does not need another exploratory rewrite. The unresolved question is product ownership: whether the metric is a global Product-B learning instrument or an agency-scoped operational insight. That is a short architecture/product decision with high downstream leverage. Once settled, the work is a bounded build sequence: scope/permission, typed contract, visible reporting, and evidence.

Do not treat the existing BFF mapping as a reason to skip the decision. Doing so would cement an ambiguous authority model into a user-facing surface.

## 11. Completeness and uncertainty statement

### Reviewed

- Selected document claims and historical metadata.
- Current router and Server.py wiring.
- Route/OpenAPI shape and auth dependency.
- Product-B event store filtering/grouping/KPI computation.
- Focused tests and fresh five-file regression run.
- Frontend route mapping, catch-all proxy, agency Insights page, and available hooks/types.
- Current local event-store shape at aggregate level.
- Product-B follow-up status documentation.

### Not reviewed

- Browser/device rendering or accessibility of a Product-B UI, because no current UI consumer was found and no servers were started for this review.
- Hosted deployment, production configuration, real-user telemetry, provider behavior, or release approval.
- Every concurrent dirty change in the repository.
- Legal/privacy approval for analytics collection.
- Whether the local event rows are synthetic, replayed, or production-derived beyond their file location and shape.

### Remaining uncertainties

- The intended canonical scope of Product-B KPIs is not explicit enough to resolve whether global aggregation is a defect or an intentionally internal metric.
- The product owner for the future reporting surface is not identified in the selected document.
- The current route count has drifted substantially, but this audit did not classify every route change.
- The browser-visible user flow from public checker through event emission was not independently executed in this turn.

### Evidence needed to close the audit findings

- Written scope/permission decision.
- Cross-workspace backend proof.
- Typed API contract and frontend type proof.
- Visible authenticated UI with no-data/error/recovery states.
- Browser evidence and current runbook/snapshot receipt.
- Fresh status note that distinguishes historical Slice-F extraction from product capability completion.

### Overall evidence floor

The audit reaches Tier 2 for the bounded backend extraction and test claims, Tier 1 for direct source/document observations, and does not reach Tier 3 product/release proof. The strongest current claim is: “Slice-F router extraction remains present and its focused regression lane passes.” The unsupported claim is: “Product-B KPI reporting is a trustworthy, discoverable, agency-safe, product-complete feature.”

## 12. Review handoff

Review verdict: **historically valid extraction; current product capability requires contract hardening and visible productization before GO.**

Verified implemented: extracted route, current wiring, query bounds, auth dependency presence, event/KPI calculation coverage, and focused regression lane.

Partially implemented: self-describing KPI payload and frontend BFF mapping.

Claimed but not current/proven: historical route counts as current inventory, self-contained snapshot verification, tenant-scoped KPI semantics, visible Product-B reporting, browser behavior, and release readiness.

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## 13. Dated resolution update — 2026-09-04

The product/architecture decision requested after this audit is now recorded
in `Docs/architecture/adr/ADR-007-PRODUCT-B-SCOPED-ANALYTICS_2026-09-03.md`.
The decision keeps both views, with different authorities:

- The existing `/analytics/product-b/kpis` route is agency-scoped to the
  authenticated workspace.
- `/platform/admin/analytics/product-b/kpis` is a separate global read route,
  restricted initially to the persisted `super_admin` platform role.
- Agency `owner`/`admin` membership does not imply platform-global access.
- Both routes use the same KPI engine and expose an explicit scope/provenance
  response contract.

The implementation work addressed the P1/P2 findings in the following way:

| Prior finding | Resolution | Evidence boundary |
|---|---|---|
| Dead agency context and global aggregation | `workspace_id` is passed into the agency KPI computation; global aggregation moved to a distinct platform route | Local focused tests prove two-workspace separation and explicit global aggregation; no hosted or production proof |
| Hidden reporting capability | Added a scoped Product-B panel to agency Insights and a separate platform-admin page with loading, empty, error, retry, and scope labels | Frontend typecheck/tests/lint; browser proof remains a release gate |
| Untyped API boundary | Added `ProductBKpiResponse` to the FastAPI route and aligned the frontend contract | OpenAPI and focused route checks remain required in the final receipt |
| Historical verification drift | Preserved this audit and added a dated implementation status artifact | Snapshot counts remain checkout-specific and are not release proof |
| Incomplete sensitive-read accountability | Added a durable `read` audit event for global KPI reads, including scope/count/window metadata | Audit persistence is locally exercised through the route; operational retention/alerting remains outside this change |

The first `super_admin` was deliberately not seeded. The migration defaults all
existing identities to `none`; granting the role to the intended platform
owner is a separate identity-verification and operational activation step.
This prevents a broad or guessed user mutation from being mistaken for a
product implementation detail.

This amendment supersedes the prior “decide scope before implementation” task
package, but it does not promote the feature to production or release-ready
status. The local route/OpenAPI receipt and rate-limit header are now verified;
the remaining gates are browser proof with authenticated state, deployment /
shared-store rate-limit verification, privacy/retention review, and explicit
platform-owner role activation.
