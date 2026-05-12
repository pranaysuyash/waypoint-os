# D6 Public Checker Authority Progress (2026-05-12)

## Scope completed in this slice

- Added D6 authority metadata plumbing to public-checker live-check payloads.
- Added D6 manifest category coverage for public-checker risk lanes (`weather`, `safety`) as `shadow`.
- Enforced authoritative-only blocker merges into `decision.hard_blockers` / `decision.soft_blockers`.
- Added explicit advisory blocker fields for consumer-safe visibility without over-claiming authority.
- Added runtime D6 authority resolver that prefers eval-gate snapshot evidence when available and falls back to manifest status.
- Added endpoint-level public-checker contract tests for advisory vs authoritative blocker behavior.
- Added canonical D6 gate snapshot generator and runtime artifact path for CI/ops.
- Added/updated tests for metadata + merge behavior.

## What is better now

1. Public checker findings now carry explicit authority metadata:
   - `public_surface_authority` per structured risk (`authoritative` vs `advisory`)
   - `d6_category_status` per structured risk (`gating` / `shadow` / `planned` / `untracked`)
   - top-level `d6_public_surface` summary
2. Live-check blocker promotion now respects D6 authority:
   - only authoritative live-check blockers are merged into canonical decision blockers
   - advisory live-check blockers remain visible under `advisory_hard_blockers` / `advisory_soft_blockers`
3. The system no longer treats all live-check findings as implicitly equivalent in trust semantics.
4. This creates a clean migration path to full D6 eval-outcome gating without breaking existing API consumers.
5. Runtime authority now supports measured-outcome governance:
   - If `D6_AUDIT_GATE_SNAPSHOT_PATH` points to a valid snapshot with category decisions, authority is resolved from that snapshot.
   - If snapshot is missing/invalid/category-absent, authority falls back safely to manifest progression status.
6. `/api/public-checker/run` contract now has direct regression coverage for:
   - advisory weather findings remaining out of canonical hard blockers
   - weather findings becoming canonical blockers when snapshot marks category authoritative
7. We now have a repeatable snapshot artifact pipeline:
   - Builder module: `src/evals/audit/snapshot.py`
   - CLI entrypoint: `scripts/generate_d6_gate_snapshot.py`
   - Default runtime artifact: `data/evals/d6_audit_gate_snapshot.json`

## What is still bad / incomplete

1. There is no canonical pipeline yet that automatically writes and rotates the latest validated D6 gate snapshot artifact in CI/CD.
2. `weather` and `safety` are now tracked but still `shadow`, so they remain advisory by design until precision/recall/severity gates are promoted.
3. D6 harness exists as scaffold, but production quality gate enforcement is still partial until snapshot generation and promotion are standardized and enforced.

## Files changed

- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/live_checker_service.py`
- `/Users/pranay/Projects/travel_agency_agent/src/evals/audit/public_authority.py`
- `/Users/pranay/Projects/travel_agency_agent/tests/test_live_checker_service.py`
- `/Users/pranay/Projects/travel_agency_agent/src/evals/audit/manifest.yaml`
- `/Users/pranay/Projects/travel_agency_agent/tests/evals/test_d6_audit_scaffold.py`
- `/Users/pranay/Projects/travel_agency_agent/tests/evals/test_public_authority.py`
- `/Users/pranay/Projects/travel_agency_agent/tests/test_public_checker_contract_authority.py`
- `/Users/pranay/Projects/travel_agency_agent/src/evals/audit/snapshot.py`
- `/Users/pranay/Projects/travel_agency_agent/scripts/generate_d6_gate_snapshot.py`
- `/Users/pranay/Projects/travel_agency_agent/tests/evals/test_d6_gate_snapshot.py`
- `/Users/pranay/Projects/travel_agency_agent/data/evals/d6_audit_gate_snapshot.json`

## Verification

- `uv run pytest -q tests/test_live_checker_service.py tests/test_public_checker_live_checks.py tests/evals/test_d6_audit_scaffold.py`
- `uv run pytest -q tests/evals/test_public_authority.py tests/test_live_checker_service.py tests/test_public_checker_live_checks.py tests/evals/test_d6_audit_scaffold.py`
- `uv run pytest -q tests/test_public_checker_contract_authority.py tests/evals/test_public_authority.py tests/test_live_checker_service.py tests/test_public_checker_live_checks.py tests/evals/test_d6_audit_scaffold.py`
- Result: `21 passed`
- `uv run pytest -q tests/evals/test_d6_gate_snapshot.py tests/evals/test_public_authority.py tests/test_public_checker_contract_authority.py tests/test_live_checker_service.py tests/evals/test_d6_audit_scaffold.py`
- Result: `20 passed`
- `uv run python scripts/generate_d6_gate_snapshot.py`
- Result: wrote `data/evals/d6_audit_gate_snapshot.json`

## Recommended next implementation order (updated)

1. Add CI job wiring to regenerate `data/evals/d6_audit_gate_snapshot.json` and fail on unexpected drift.
2. Update frontend itinerary checker UI to distinguish authoritative vs advisory findings explicitly.
3. Build D6 fixtures/rules for weather+safety and promote categories from `shadow` to `gating` only after thresholds are proven.
