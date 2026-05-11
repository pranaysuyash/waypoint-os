# D6 + Itinerary Option Progress

**Date:** 2026-05-11  
**Scope:** First implementation pass for D6 eval scaffold, canonical itinerary option artifact, per-person utility, wasted-spend calculation, and repo-local feature scanner repair.

## Baseline

The May 11 progression review identified four next implementation items:

1. Build the D6 eval harness scaffold.
2. Build the canonical `ItineraryOption` model.
3. Implement per-person utility and wasted-spend calculation into that model.
4. Repair the feature scanner/catalog so future progression reviews are less manual.

The earlier gap was real: suitability scoring existed at activity/participant level, but there was no canonical travel-product artifact that aggregated an itinerary option into person utility, group utility, cost, and waste.

## Decisions

### D6

Accepted the architecture from `Docs/D6_EVAL_CONTRACT_DESIGN_2026-04-22.md` and `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`: D6 is an offline measurement layer, not runtime routing logic.

Implemented a minimal scaffold under `src/evals/audit/`:

- `manifest.yaml` defines category progression: `planned`, `shadow`, `gating`.
- `manifest.py` loads and validates the manifest with Pydantic.
- `fixtures.py` defines `AuditFixture`, `ExpectedFinding`, `ExpectedAbsentFinding`, and fixture loading.
- `metrics.py` computes category precision, recall, and severity accuracy.
- `runner.py` runs fixtures through an injected rule runner and returns an `EvalReport`.
- `data/fixtures/audit/activity/activity_toddler_low_utility.json` seeds the first activity fixture.

This is intentionally not wired into D1 or public checker gating yet. It creates the contract needed to measure those surfaces first.

### Itinerary Option

Added canonical option contracts in `src/suitability/models.py` and construction logic in `src/suitability/options.py`:

- `ItineraryOption`
- `SuitabilityBundle`
- `PersonUtility`
- `WastedSpendItem`
- `WastedSpendSummary`
- `build_itinerary_option()`
- `build_suitability_bundle()`

The model is additive and uses the existing deterministic suitability scorer. No existing runtime API contract was changed.

### Utility And Waste

Per-person utility is computed as the average activity score percentage for each participant.

Wasted spend is computed per low-utility participant/activity:

```text
wasted amount = activity cost per person * (1 - participant score)
```

Activities with missing cost clamp to zero waste while still preserving utility scoring, so missing commercial data does not erase suitability signal.

Current thresholds:

- Low utility: below 50%.
- High utility: 70% or above.

These are explicit constants in `src/suitability/options.py` and should eventually become agency policy or D6-calibrated thresholds.

### Feature Scanner

Added repo-local scanner and catalog:

- `tools/feature_scan.py`
- `tools/feature_catalog.json`

The scanner fixes the stale-date issue by using the current date by default and supports `--scan-date` for reproducible tests. It also checks all configured file globs and reports `matched_terms` / `missing_terms`, which makes noisy scoring easier to debug.

The new catalog is deliberately scoped to the current progression surface: D6, itinerary option, per-person utility, and wasted-spend evidence. It does not claim to replace the entire May 2 baseline catalog yet.

## Verification

Fresh verification on 2026-05-11:

```bash
uv run pytest -q tests/test_itinerary_option_model.py tests/evals/test_d6_audit_scaffold.py tests/test_feature_scan_tool.py
# 7 passed in 5.55s

uv run pytest -q tests/test_suitability.py tests/test_suitability_wave_12.py tests/test_itinerary_option_model.py tests/evals/test_d6_audit_scaffold.py tests/test_feature_scan_tool.py
# 36 passed in 4.54s

python3 tools/feature_scan.py . --json
# scanned_at: 2026-05-11
# current_overall: 1.0 for the scoped progression catalog
```

## Progression Update — 2026-05-11 21:34 IST

### What Is Better

- D6 now has a real activity-category rule runner instead of only accepting a lambda/stub.
- The activity runner measures the canonical `ItineraryOption` artifact, so D6 and D4 are sharing the same suitability/waste economics instead of duplicating logic.
- The seed corpus now has both a positive fixture and a clean false-positive fixture:
  - `activity_toddler_low_utility`
  - `activity_family_clean_culture`
- Manifest gate evaluation now distinguishes:
  - category status (`planned`, `shadow`, `gating`)
  - threshold pass/fail
  - CI-blocking readiness
  - public-surface authority readiness

### What Is Still Bad / Not Better Enough

- D6 still measures only the activity category. Budget, pacing, logistics, and documents are manifest entries but do not yet have rule runners or fixture coverage.
- `activity` is still `shadow`, so even if its current tiny fixture set passes, it is not authoritative for consumer-facing public checker claims.
- The public checker is not yet consuming D6 gate decisions. The gate contract exists, but runtime public output still needs a deliberate integration pass.
- The fixture corpus is too small for a real precision/recall claim. Current passing metrics prove the scaffold and rule path work; they do not prove product-grade accuracy.

### Fresh Verification For This Update

```bash
uv run pytest -q tests/evals/test_d6_audit_scaffold.py tests/test_itinerary_option_model.py tests/test_feature_scan_tool.py
# 10 passed in 15.34s

uv run pytest -q tests/test_suitability.py tests/test_suitability_wave_12.py
# 29 passed in 13.03s

python3 tools/feature_scan.py . --json
# scanned_at: 2026-05-11
# current_overall: 1.0 for the scoped progression catalog, including M4 activity runner and M5 manifest gates

python3 -m compileall -q src/evals src/suitability tools/feature_scan.py
# exit 0
```

### Feature Progression Criteria From Here

A healthy next progression should look like this:

1. Add at least one clean and one broken fixture per category.
2. Implement rule runners category by category, reusing runtime analyzers/contracts rather than writing eval-only logic.
3. Keep categories in `shadow` until the fixture set is broad enough to justify thresholds.
4. Wire public checker output to show only `gating + thresholds met` findings as authoritative; `planned` and `shadow` findings should be advisory/internal.
5. Promote a category from `shadow` to `gating` only with documented precision/recall evidence.

## Remaining Work

- Add category fixtures beyond the activity fixtures: budget clean/broken, pacing broken, logistics broken, documents broken, and multi-issue cases.
- Implement non-activity D6 rule runners and avoid eval-only reimplementations when runtime analyzers already exist.
- Add a public-checker gate that prevents consumer-visible findings from presenting as authoritative when category status is only `planned` or `shadow`.
- Move utility/waste thresholds into policy once D6 has enough fixtures to calibrate false positives and false negatives.
- Expand `tools/feature_catalog.json` from scoped progression catalog into the full baseline catalog after reviewing each evidence term for signal quality.
