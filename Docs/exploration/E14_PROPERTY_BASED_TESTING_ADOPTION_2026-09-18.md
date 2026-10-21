# E14 — Property-Based Testing Adoption for Intake Normalization (2026-09-18)

**Status:** Explored — bounded experiment complete; adoption decision pending owner.
**Origin:** `Docs/FIRST_PRINCIPLES_GAP_ASSESSMENT_2026-04-14.md` Stage-B ask
("deterministic transformations should be covered by property-like tests"),
re-verified by the 2026-09-18 random-document audit.
**Depends on:** nothing. **Feeds:** `pyproject.toml` dev-dependency decision.

## Question

Should `hypothesis` be adopted as a dev dependency to property-test the pure
normalizer transformations?

## Evidence gathered (2026-09-18, ephemeral `uv run --with hypothesis`)

- `hypothesis` is absent from `pyproject.toml:37-44` (dev group) and `uv.lock`.
- CI would run such tests automatically: `.github/workflows/ci.yml:171` runs
  `uv run pytest -q tests/` — no lane changes needed.
- Import path works: `from src.intake.normalizer import Normalizer`.
- Return shapes confirmed: `parse_budget("1.5L")` →
  `{'raw','min':150000,'max':150000,'currency':'INR'}`.
- 300-example fuzz runs (5.0s wall total): `parse_budget` — 0 crashes,
  0 invariant violations on generic text; `normalize_city` — total dict
  lookup, not worth fuzzing.
- **Targeted digit-strategy probe found a real defect:** `parse_budget("9"*400)`
  raised a raw `OverflowError` (`float()` → `inf` → `int(inf)`) — a plausible
  Excel/WhatsApp paste artifact. **Fixed in this wave** (graceful degradation
  to `min=None/max=None` + regression tests in
  `tests/test_extraction_fixes.py::TestParseBudgetOverflowHardening`), which is
  itself the strongest evidence that property testing pays for itself here.

## Verdict

Adoption is a small, low-risk, high-signal dev-dependency addition — but it is
still a dependency adoption decision (repo policy), not a casual add. The
property suite itself is ~40 lines: digit-focused `st.text()` strategies over
`parse_budget` (idempotence of re-parsing, min<=max, currency vocabulary,
no-crash), and month-invariants over `parse_date_window`.

**Recommended next step (owner gate):** add `hypothesis` to the dev group +
`tests/test_normalizer_properties.py` as one atomic change. Falsifier: if a
month of property runs surfaces no new defect beyond the overflow (already
fixed), retire the suite or shrink it to the digit-strategy case.
