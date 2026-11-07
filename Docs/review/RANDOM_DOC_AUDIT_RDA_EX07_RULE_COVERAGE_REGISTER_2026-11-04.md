# Random Document Audit — `Docs/exploration/RDA_EX07_RULE_COVERAGE_GAP_REGISTER_2026-09-08.md` (2026-11-04)

**Selection:** pool of 3,621 markdown docs (instruction-stack files excluded), time-seeded `awk srand()` draw.
**Governing stack loaded:** `~/.zcode/AGENTS.md` → `/Users/pranay/AGENTS.md` → `/Users/pranay/Projects/AGENTS.md` → repo `AGENTS.md` → `OPERATING_DOCTRINE.md` 8.2 → `REVIEW_DOCTRINE.md` 1.3 → context pack. Council built via `council-orchestrator` (canonical persona repo `/Users/pranay/Downloads/Understanding_Personas_24sep`, resolver-confirmed high confidence, index freshness-gated).

## 1. What the audited document is

A 2026-09-08 research register mapping a 2026-04-14 GTM-wedge doc's 15 rule IDs (CONN/TRF/VISA/INS/CHK/HOT/PACE/MEAL/FEE/BUF/WEATHER + 3 info rows) against the shipped public checker, feeding decision D-04. Its four recommendations:

1. Accept the gap register as the honest scope statement of the public checker.
2. Wire `timed-entry-audit`/`connection-risk` into the public path only after capability-gated structured input exists; gate as `advisory_*`.
3. **"Fix the one cheap asymmetry now (D-04 fast path): stage-awareness — let users declare 'already booked' so `visa_not_applied` can fire."**
4. Retire the doc's rule taxonomy as a tracking unit.

## 2. Evidence (truth status labeled)

| # | Claim verified | Status | Evidence |
|---|---|---|---|
| E1 | Register's `spine_api/decision.py` citations are stale (file moved) | Observed | `src/intate/decision.py` now `src/intake/decision.py:1476-1498`; `src/decision/` package split out |
| E2 | `SpineRunRequest.stage` is free-form `str`, default `"discovery"`, no allowlist | Observed | `spine_api/contract.py:112` |
| E3 | **Backend capability exists**: `stage="booking"` fires `visa_not_applied`(critical); `stage="discovery"` does not | **Verified (Tier 2 runtime probe)** | probe on `generate_risk_flags` with identical visa facts (`requirement=required, status=not_applied`): discovery→`visa_timeline_risk(high)` only; booking→`visa_not_applied(critical)` + `visa_timeline_risk` |
| E4 | Traveler UI hardcodes `stage: 'discovery'` — no declaration surface | Observed | `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx:3129` (live read) |
| E5 | `timed-entry-audit`/`connection-risk` remain agency-internal; no public wiring | Observed | consumers: `RouteLogisticsPanel.tsx:91`, `route-map.ts:271` |
| E6 | `visa_not_applied`/`document_risk` are non-suppressible (`SAFETY_INVARIANT_FLAGS`) | Observed | `src/decision/override_learning.py:33-37` |
| E7 | No canonical findings-store rows existed for these gaps (frozen markdown registers only) | Observed | grep of `Docs/review/FINDINGS_STORE.jsonl` pre-open |
| E8 | Baseline targeted tests: 26/26 pass; no test drives `stage="booking"` through the public path | Verified | `uv run pytest tests/test_decision_rules.py tests/test_public_checker_contract_authority.py tests/test_live_checker_service.py -q` → 26 passed |
| E9 | Unknown stage values silently degrade to discovery-like behavior | Observed | `== "booking"` strict equality + `MVB_BY_STAGE.get(stage, MVB_BY_STAGE["discovery"])` (src/intake/decision.py:2309); canonical vocabulary exists unshared at `spine_api/routers/settings.py:278` |
| E10 | WOBS (2026-09-09) deferred rec-3 to a 6-month horizon; pre-exposure punch-list is now 5/5 closed | Observed | `Docs/exploration/WOBS_AGENCY_BRANDED_CHECKER_2026-09-09.md:78,178,286` |
| E11 | Wedge doc supersession note already pinned; launch NO-GO/hold; exposure-scope choice remains open (owner gate) | Observed | wedge doc header; `Docs/LAUNCH_STATUS.md` |

## 3. Council (condensed; full lenses applied in-session)

- **Lead — PER 99011 Visa Intelligence Architect.** Decision ownership of the register's single P1 asymmetry.
- **PER 1129 Travel Growth Opportunity Analyst** — launch posture: checker NO-GO/hold bounds severity to "pre-exposure readiness"; punch-list otherwise closed, so rec-3 is one of the last semantic pre-flip gaps; rec-2 deferral is correct (prerequisite unmet).
- **PER WPSYS 0010 Source of Truth & Authority Architect** — contract drift (E2/E9): reuse the canonical stage vocabulary in one place; silent fallback is invisible degradation.
- **PER 1082 Travel Product Trust & Safety Designer** — **naive rec-3 fires wrong copy**: "booking blocked" is factually wrong for a user who declared already-booked; copy must be stage-semantics-aware ("required before travel", not "booking blocked").
- **Skeptic PER 0522 Epistemics Red Team** — falsification attempts and outcomes: backend-capability claim survived probe; harm-deferred-bounded survived (P1-in-pre-exposure, not P0); WOBS-vs-register "now vs 6mo" value disagreement reconciled on evidence (deferral rationale weakened; change small/reversible/advisory; reversible design decision under delegated authority with decision record). What would falsify: proof that public-path intake cannot produce `visa_status` facts — rejected: extractors produce them (visa extractor fixes VA-06/07 recorded).

## 4. Material disagreement reconciled

Register ("fix now") vs WOBS ("6mo horizon"). Resolution: WOBS deferred while the pre-exposure punch-list was open; punch-list is 5/5 closed; capability already exists backend-side; cost small and reversible; the audited register itself recommended now. → **Implement now**, divergence recorded here and in the register's disposition addendum.

## 5. Deduplicated register (see chat report for full issue anatomy)

- **FND-0399 (P1)** — ISSUE-001: stage declaration missing; `visa_not_applied` unreachable for declared-booked travelers.
- **FND-0400 (P2)** — ISSUE-002: free-form `stage` contract, silent fallback, unshared vocabulary.
- **FND-0401 (P2)** — ISSUE-003: register never dispositioned; stale citations (`decision.py` move; `src/intake/extractors.py:3336` comment).
- **ISSUE-004** — canonical findings rows now opened (FND-0399..0401) — done by this audit.
- **ISSUE-005 (P3)** — visual-evidence pair requirement for the FE control (doctrine §3); attempted at implementation end.
- **Parked (not a finding):** rec-2 logistics wiring — prerequisite (capability-gated structured itinerary input) unmet; revisit trigger = structured-input capability landing on the public path.
- **Already done (verified):** wedge supersession note; EX-05 disclaimer; Ghost Hotel entity checks; consent redesign.

## 6. Implementation unit (approved via user wrapper: "Implement the audit tasks")

Stage-declaration at the public checker boundary: FE declaration control + payload; canonical `STAGE_VALUES` allowlist applied at the contract (extend canonical, no duplicate constant); stage-semantics-aware visa/passport copy; stale-citation fixes; register disposition addendum; tests with S2 sensitivity where a defect-fix claim is made; targeted backend + FE suites; visual pair if the dev servers allow.

**Explicitly out of scope:** exposure flip (owner gate), rec-2 wiring (prerequisite unmet), rule-ID retrofit (rejected, prior audit).

## 7. Implementation record (executed 2026-11-04, same session)

**Backend**
- `src/intake/constants.py` — canonical `TRIP_STAGE_VALUES` + `assert_valid_trip_stage` (single vocabulary source; follows the file's own decision-state precedent).
- `spine_api/contract.py` — `SpineRunRequest.stage` `field_validator` rejects unknown stages with the canonical vocabulary in the error (was: silent discovery-degrade, FND-0400). Unknown stage → FastAPI 422.
- `spine_api/routers/settings.py` + `spine_api/services/trip_lifecycle_service.py` — local stage-set copies consolidated to the canonical constant; the reassessment builder now clamps stored legacy stages to the canonical set (stored trips may predate validation).
- `src/intake/decision.py` — booking-stage visa/passport copy made stage-semantics-honest: "must be resolved before you book or travel" (the old "booking blocked"/"cannot book" claims are false for declared-booked travelers). Flag names/severities unchanged; `SAFETY_INVARIANT_FLAGS` preserved.
- `src/intake/extractors.py` — stale `decision.py` citation corrected (FND-0401).
- `spine_api/services/public_checker_service.py` — `declared_stage` added to `intake_started` event properties (operator funnel signal).

**Frontend** (`frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx`)
- New `AlreadyBookedPicker` declare-radio ("Have you booked this trip?" — Not booked yet / Already booked), mounted on both paste and file tabs next to `PlanSourcePicker`; threaded through paste payload (`already_booked`) and the `onAnalyzeFile` signature.
- `handleAnalyze` maps the declaration via exported pure helper `stageForSubmittedPlan(alreadyBooked)` → `stage: "booking" | "discovery"` (was hardcoded `'discovery'`).

**Verification (evidence tiers)**
- Tier 2: probe — identical visa facts, `discovery` → `visa_timeline_risk(high)` only; `booking` → `visa_not_applied(critical)`.
- S1/S2 tests: backend 37/37 targeted + 34/34 lifecycle/settings/pipeline + 209/209 blast-radius sweep (`test_public_checker*`, `test_decision*`, `test_intake*`, contract, settings, live-checker). FE: typecheck clean; checker suites 11/11 (incl. honesty-sweep unchanged); new `stage-declaration.test.ts`.
- S2 note: the booking-fires/discovery-doesn't pair is the defect-claim pair; the copy-honesty test guards the trust-and-safety finding.
- Tier 4 (browser): `/itinerary-checker` renders the new control (AFTER pair `Docs/profiling/visual_pairs/rda_ex07/`); click toggles selected state correctly. BEFORE = the same card region without the booking row (pre-edit DOM; a strict before-screenshot would require reverting the shared tree, which git safety forbids).
- Full-loop e2e run not executed (would write to the shared test agency during a contested parallel-lane tree). Named next check: `curl -s -X POST http://localhost:8000/api/public-checker/run -d '{"raw_note":"...","stage":"booking"}'` and confirm `visa_not_applied` in the decision block.

**Baseline classification (regression discipline):** full FE suite shows 49 failures in 13 files — none import the edited file (verified: zero import edges), failures are DOM-structure errors on canonical stages, and the tree carries an active parallel lane (insights, public-proposal token page, departure-board, governance-api all dirty). Classified parallel-lane/in-flight baseline, not this change; zero failures in the edited surface.

**Findings closed:** FND-0399, FND-0400, FND-0401 (via `scripts/findings.py` with this evidence).
