# Feature Progression Review — May 11, 2026

**Date:** 2026-05-11  
**Verified at:** 2026-05-11 19:26 IST  
**Scope:** Reconcile `Docs/FEATURE_COMPLETENESS_SCAN_2026-05-03.md` with current code/docs and define what a healthy next feature progression should look like.  
**Status:** Review / decision artifact. No production code changes in this pass.  
**Checklist applied:** `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

---

## 1. Instruction And Drift Checks

Read and applied:

- `/Users/pranay/AGENTS.md`
- `/Users/pranay/Projects/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

Searched for additional repo-local agent files:

```text
find ... -name AGENTS.md -o -name CLAUDE.md -o -name QWEN.md -o -name CODEX.md -o -name GEMINI.md -o -name copilot-instructions.md -o -name .cursorrules
```

Found only:

- `AGENTS.md`
- `CLAUDE.md`
- `frontend/AGENTS.md`
- `frontend/CLAUDE.md`

No repo-local Qwen, Codex, Copilot, Gemini, or `.cursorrules` file was present.

Skill workflows used directly from local `SKILL.md` files:

- `feature-completeness-detection`
- `search-first`
- `verification-before-completion`
- `software-architecture`

Note on instruction conflict / tooling gap: `CLAUDE.md` says to invoke matching skills through a Skill tool as the first action. Codex in this session exposes skill files but no callable Skill tool. The practical application was to read and follow the relevant `SKILL.md` workflows directly.

Parallel-agent drift observed:

- Many uncommitted frontend page/client split changes are present.
- Current route/settings work has changed during/after earlier route inventory docs.
- Existing parallel pytest jobs were already running before this review; they were left alone.
- Long-running pytest jobs started by this review were stopped after they stopped producing output; their result is recorded as interrupted, not passing.

---

## 2. Review Verdict

The May 3 scan is **historically useful but not current enough to drive implementation directly**.

Current reality is better than the scan in several important areas:

- Document/PDF extraction has landed.
- Public itinerary checker has landed.
- Booking collection/tasks/documents are materially beyond "zero".
- Dashboard and route-map inventory are more mature.

Current reality is also riskier than a simple score suggests:

- A transient duplicate `/api/settings*` backend route regression was observed during the review, then superseded by later live-tree changes before this document was finalized.
- The feature scanner still has stale metadata and noisy evidence terms.
- The core thesis gaps remain: D6 eval harness, canonical itinerary/option model, per-person utility, wasted-spend math, and full D5 feedback learning.

Go/no-go:

- **Go for focused implementation after the latest route parity checks.**
- **Go for focused review/planning and documentation cleanup.**
- **No-go for consumer/audit feature expansion that increases public claims before D6 gating exists.**

---

## 3. Fresh Verification Evidence

### Commands that passed

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
```

Result:

```text
2026-05-11 19:26:28 IST
```

```bash
uv run python tools/architecture_route_inventory.py --format json
```

Latest result summary:

```text
backend_route_count=146
server_py_route_count=81
router_module_count=14
router_module_route_count=65
bff_route_map_count=71
bff_backend_path_count=70
bff_unmatched_backend_path_count=0
potential_duplicate_backend_route_count=0
```

```bash
cd frontend && npx tsc --noEmit
```

Result: exit code 0.

```bash
uv run pytest -q tests/test_booking_task_service.py tests/test_override_api.py
```

Result:

```text
49 passed in 41.23s
```

Feature scanner rerun:

```bash
python3 /Users/pranay/.hermes/skills/software-development/comprehensive-audit/scripts/feature_scan.py \
  /Users/pranay/Projects/travel_agency_agent \
  --catalog /Users/pranay/.hermes/skills/software-development/comprehensive-audit/references/feature_catalog.json \
  --delta --json
```

Result summary:

```text
scanned_at 2026-05-03
current_overall 0.63
```

The scanner executed, but its `scanned_at` value is stale and its term evidence remains too broad for authoritative scoring.

### Commands that failed or were inconclusive

```bash
cd frontend && npx vitest run \
  src/app/__tests__/public_marketing_pages.test.tsx \
  src/lib/__tests__/route-map.test.ts \
  src/lib/__tests__/api-client-contract-surface.test.ts
```

Observed:

```text
Test Files 3 passed
Tests 23 passed
Errors 1 error
Error: [vitest-worker]: Timeout calling "onTaskUpdate"
```

Interpretation: assertions passed, but Vitest exited non-zero due to worker/RPC timeout. Do not claim this slice green.

```bash
uv run pytest -q \
  tests/test_architecture_route_inventory.py \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py
```

Latest result:

```text
7 passed in 9.99s
```

During the review, an earlier run of this same slice failed because the live tree briefly had duplicate `/api/settings*` ownership in both `spine_api/server.py` and `spine_api/routers/settings.py`. A later live-tree check showed that `server.py` no longer owns those handlers, and the parity slice now passes. The transient failure is useful process evidence: route extraction work must always finish by removing the old route owner and rerunning parity/OpenAPI checks.

Long-running targeted runs interrupted:

- `uv run pytest -q tests/test_document_extractions.py`
- `uv run pytest -q tests/test_public_checker_path_safety.py tests/test_product_b_events.py`
- One combined broader backend run

These produced some progress output but were stopped after they stopped producing useful output. Record as **not completed**.

---

## 4. Stale / Current Matrix For May 3 Scan

| May 3 claim | Current classification | Evidence / notes |
|---|---|---|
| PDF/document extraction zero or not built | **Stale** | `src/extraction/`, `spine_api/services/extraction_service.py`, `spine_api/services/document_service.py`, and extraction endpoints now exist. |
| Public traveler/itinerary checker not started | **Stale** | `frontend/src/app/(traveler)/itinerary-checker/page.tsx` and `PageClient.tsx`; public checker backend routes exist. |
| Booking coordination zero | **Stale / partially valid** | Booking data, public collection, booking documents, and booking tasks exist. Still lacks a mature quote/payment/confirmation financial state model. |
| Analytics dashboard endpoint missing | **Stale** | `spine_api/routers/system_dashboard.py` owns `/api/dashboard/stats`. |
| D6 eval harness missing | **Still valid** | No `src/evals/` package found. Docs still repeatedly identify D6 as the quality gate. |
| Itinerary model/output absent | **Still valid, with frontend caveat** | UI/output surfaces exist, but no canonical itinerary option model for ranked options, day plans, per-person utility, cost, and trade-offs. |
| Per-person utility/wasted spend absent | **Still valid** | Suitability exists, but not explicit utility percentage and wasted-spend math. |
| Sourcing hierarchy stub | **Partially valid** | `src/intake/sourcing_path.py` now provides a resolver extension point, but supplier/package data and `SourcingPolicy` are not real. |
| Override feedback bus missing | **Partially valid** | Override API/tests exist, but full D5 feedback bus, pattern detection, and learning loop are not complete. |
| Feature scanner automated score inflated | **Still valid** | It still reports stale `scanned_at`, misses live surfaces, and over-counts broad terms. |

---

## 5. What Is Better Now

### Runtime product surface is less theoretical

The public itinerary checker has real UI and backend support. This changes the product state from "planned GTM wedge" to "partially live wedge."

Good:

- Real public route and upload/paste flow.
- Public checker API routes.
- Event/KPI plumbing for Product B.
- Export/delete paths exist.

Bad / risk:

- Consumer surface appears to have shipped ahead of the D6 gating philosophy in the D2/D6 docs.
- This can create trust risk if public findings are not limited to high-precision categories.

Better path:

- Add explicit `presentation_profile` and D6 category gating before broadening consumer-visible findings.
- Treat the current public checker as beta/gated until eval evidence exists.

### Document operations are materially stronger

Good:

- Upload validation exists.
- Storage abstraction exists.
- Extraction service and provider clients exist.
- Extraction attempts/retry/apply/reject endpoints exist.
- Booking document operations integrate with ops workflows.

Bad / risk:

- Document/extraction routes still live in `server.py`.
- Long-running extraction needs a worker/queue boundary soon.
- Tests were too slow/hung in this review, so verification ergonomics need attention.

Better path:

- Consolidate document routes into a router after the settings duplicate regression is fixed.
- Keep extraction attempts append-only.
- Move provider calls behind a same-repo worker boundary before adding more providers/channels.

### BFF route-map maturity improved

Good:

- Current BFF route map has no unmatched backend paths in the latest inventory output.
- Route-map tests exist.
- Route inventory tooling exists.

Bad / risk:

- Current route docs conflict with each other because code changed after the Phase 0 execution note.
- Backend parity/OpenAPI are now broken by settings duplication.

Better path:

- Fix duplicate settings routes.
- Regenerate route inventory and snapshots after the fix.
- Treat route inventory as a required preflight before route extraction.

### Test and quality culture improved

Good:

- Many focused tests now exist around route inventory, product B events, booking, override, extraction, route map, contracts, and frontend surfaces.
- React Doctor/status docs are detailed.

Bad / risk:

- Vitest worker timeout makes "all assertions pass" insufficient.
- Some backend slices can hang or run very long.
- Route parity fixtures lag behind live route changes.

Better path:

- Split slow suites into smaller reliable CI groups.
- Mark live/provider/network tests opt-in.
- Keep parity snapshots as blockers for route changes.

---

## 6. What Is Bad Or Blocking

### P0: D6 is still missing while public audit/checker surfaces exist

This is the biggest product trust risk.

The architecture says consumer-facing audit should expand only when D6 gating categories pass high precision. The current product has a public itinerary checker before the D6 harness exists.

Correct implementation path:

1. Scaffold `src/evals/audit/`.
2. Define category manifest: `planned`, `shadow`, `gating`.
3. Add first fixture pack for budget/pacing/document readiness.
4. Add metrics: precision, recall, severity correctness, false-positive rate.
5. Make consumer-visible findings require `gating` category status.

### P0/P1: No canonical itinerary option model

The product still lacks the central artifact that makes travel output real:

```text
ItineraryOption
  days[]
  activities[]
  travelers/participants
  cost breakdown
  per-person utility
  wasted spend
  risk/suitability flags
  sourcing path
  trade-offs
```

Without this, output remains assembled from scattered pipeline artifacts and UI-specific shapes.

Correct implementation path:

1. Define the domain model in `src/intake` or a dedicated domain package.
2. Add a builder that consumes existing `CanonicalPacket`, suitability results, fees, and strategy.
3. Do not create a parallel output route; feed existing output/workbench/public checker surfaces from the canonical artifact.
4. Add contract tests before UI adoption.

### P1: Route extraction parity remains a mandatory guardrail

The settings route extraction appears fixed in the latest live tree, but the transient failure showed why route extraction must be treated as an atomic unit:

1. Add/move router.
2. Remove old owner only after field-by-field supersession comparison.
3. Regenerate route inventory/snapshots if the route set intentionally changes.
4. Run route inventory, route parity, and OpenAPI parity before claiming the extraction complete.

Current latest evidence:

- Only `spine_api/routers/settings.py` owns `/api/settings*`.
- `potential_duplicate_backend_route_count=0`.
- Route/OpenAPI parity tests pass.

### P1: Feature scanner is not reliable as a progression source

Problems:

- `scanned_at` is hardcoded/stale.
- Broad terms produce inflated scores.
- Current implementation can be missed if terms are old.
- It treats evidence presence as feature completion.

Correct implementation path:

1. Fix scan timestamp to actual runtime date.
2. Replace broad terms with domain-unique evidence.
3. Add negative/false-positive notes to the catalog.
4. Add a generated "raw evidence" artifact separate from the human review.
5. Treat scanner score as a signal, never the verdict.

---

## 7. What A Healthy Feature Progression Should Look Like

Feature progression for Waypoint OS should be measured by user/business outcomes, not just code existence.

### Stage 0: Contract exists

- Domain artifact named.
- Inputs/outputs typed.
- Ownership clear.
- No duplicate route/system path.
- Failure modes stated.

Example: `ItineraryOption` contract before output UI refactor.

### Stage 1: Deterministic baseline works

- No LLM dependency for core correctness.
- Fixtures cover the first travel scenarios.
- Runtime behavior verified through direct tests.
- All maturity labels honest: `stub`, `heuristic`, `verified`, `ml_assisted`.

Example: deterministic utility scoring for a small activity catalog.

### Stage 2: Operator workflow consumes it

- Real agency workbench path shows it.
- Operator can accept/reject/override.
- Audit trail records decisions.
- Existing canonical route/pipeline is extended, not duplicated.

Example: output panel renders canonical itinerary options and operator feedback.

### Stage 3: Quality gate exists

- D6 fixture manifest measures quality.
- False positives are tracked.
- Consumer-visible categories must pass thresholds.
- Regression suite is fast enough to run repeatedly.

Example: public checker only shows `gating` category findings.

### Stage 4: External delivery

- WhatsApp/email/share/PDF output uses the same artifact.
- Delivery events are tracked.
- No copy/paste-only dead end.

Example: generated share link from canonical `ItineraryOption`.

### Stage 5: Learning loop

- Overrides and outcomes feed D5.
- Pattern detection proposes changes.
- Owner approves policy/rule changes.
- No silent self-modification of agency-wide policy.

Example: repeated utility overrides suggest activity catalog tuning.

---

## 8. Recommended Next Work Units

### Task 1 — D6 Eval Harness Scaffold

Objective: create the quality gate needed before expanding consumer-facing audit claims.

Scope:

- `src/evals/audit/` package.
- Manifest schema with category status: `planned`, `shadow`, `gating`.
- First YAML/JSON fixture set for budget/pacing/document readiness.
- Runner that produces metrics summary.

Acceptance:

- Harness runs locally.
- At least one category can be measured.
- Consumer checker can later query category status.

Verification:

```bash
uv run pytest -q tests/test_evals_audit_manifest.py tests/test_evals_audit_runner.py
uv run python -m src.evals.audit.runner --fixtures tests/fixtures/evals/audit
```

Non-goals:

- Do not build a model leaderboard.
- Do not replace existing pytest contract tests.
- Do not expose new public findings before gating.

### Task 2 — Canonical Itinerary Option Model

Objective: create the domain artifact that all output surfaces can share.

Scope:

- Define `ItineraryOption`, `ItineraryDay`, `ActivityPlan`, `ParticipantUtility`, `CostBreakdown`.
- Builder consumes existing packet/suitability/fee/strategy data.
- Add contract tests.

Acceptance:

- One canonical artifact can represent an option with day plan, cost, suitability, utility, and risks.
- Output/workbench/public checker can adopt it incrementally.

Verification:

```bash
uv run pytest -q tests/test_itinerary_option_contract.py
uv run pytest -q tests/test_traveler_proposal_boundary.py tests/test_suitability_wave_12.py
```

Non-goals:

- Do not build final PDF/share/email delivery in this slice.
- Do not create a parallel output API route.

### Task 3 — Feature Scanner Catalog Repair

Objective: make automated progression scans less misleading.

Scope:

- Fix real scan timestamp.
- Tighten search terms for current implementation.
- Add explicit false-positive notes.
- Update scan report generation conventions.

Acceptance:

- Scanner no longer reports `scanned_at 2026-05-03` on May 11.
- Known live routes/surfaces are detectable.
- Broad terms like `email`, `engine`, `network`, and `dashboard` are not treated as completion proof.

Verification:

```bash
python3 /Users/pranay/.hermes/skills/software-development/comprehensive-audit/scripts/feature_scan.py \
  /Users/pranay/Projects/travel_agency_agent \
  --catalog /Users/pranay/.hermes/skills/software-development/comprehensive-audit/references/feature_catalog.json \
  --delta --json
```

Non-goals:

- Do not use scanner output as the sole feature-completeness verdict.

---

## 9. Decision Gate

Recommended immediate sequence:

1. Build D6 scaffold.
2. Build canonical itinerary option model.
3. Then implement per-person utility and wasted-spend calculation into that model.
4. Repair the feature scanner/catalog so future progression reviews are less manual.

Why this order:

- D6 is needed to prevent the public checker from over-claiming.
- Itinerary option model is the foundation for utility, waste, output delivery, and booking/quote progression.
- Utility/waste without a canonical itinerary artifact would become another parallel computation path.

---

## 10. Notes For Future Agents

- Treat May 3 scan as historical input, not current truth.
- Treat "Complete" in docs as ambiguous unless it says research complete, implementation complete, or both.
- Do not add any new API route for a resource/action that already has one.
- Do not create a parallel document/output/public-checker flow; extend canonical routes and artifacts.
- Before any route extraction, run route inventory and parity tests first.
- Before any frontend/backend integration, verify real API contracts, not just TypeScript types.
- Before claiming green, run fresh verification and record exact command/output.
