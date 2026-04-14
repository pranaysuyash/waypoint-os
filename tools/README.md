# Tools

This directory stores reusable helper utilities for this project.

## 1) `context_digest.py`

Purpose:
- Convert large exported conversation/context `.txt` files into structured summaries.
- Keep the full source context intact while generating a quick navigation layer.

Use cases:
- Ingest large chat exports from Downloads into project documentation.
- Produce action candidates and theme clustering for planning.
- Generate JSON + Markdown digest artifacts for traceability.

Usage:
```bash
python tools/context_digest.py \
  --input Archive/context_ingest/travelagency_context_2026-04-14.txt \
  --output-md Docs/context/CONTEXT_DIGEST_2026-04-14.md \
  --output-json Docs/context/context_digest_2026-04-14.json
```

Outputs:
- Markdown digest (`--output-md`) with sections, themes, top terms, and action candidates.
- JSON digest (`--output-json`) for automation or downstream tooling.

Notes:
- Heuristic summarization only; keep archived source as system-of-record.
- Works offline and has no third-party dependencies.

## 2) `e2e_scenario_runner.py`

Purpose:
- Run repeatable end-to-end intake scenarios through `ExtractionPipeline -> run_gap_and_decision`.
- Support phased runs: first 5 scenarios, remaining existing scenarios, and combined existing+new scenarios.
- Export scenario outcomes to JSON and Markdown for owner tracking.

Use cases:
- Demonstrate 5 E2E scenarios quickly.
- Execute full existing scenario sweep after baseline.
- Re-run all existing + new scenarios after additions.
- Generate artifacts for documentation/review in `Docs/reports/`.

Usage:
```bash
# First 5 existing scenarios
PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set first5 \
  --json-out Docs/reports/e2e_first5_YYYY-MM-DD.json \
  --md-out Docs/reports/e2e_first5_YYYY-MM-DD.md

# Remaining existing scenarios
PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set rest \
  --json-out Docs/reports/e2e_rest_existing_YYYY-MM-DD.json \
  --md-out Docs/reports/e2e_rest_existing_YYYY-MM-DD.md

# Existing + new scenarios
PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set existing_plus_new \
  --json-out Docs/reports/e2e_existing_plus_new_YYYY-MM-DD.json \
  --md-out Docs/reports/e2e_existing_plus_new_YYYY-MM-DD.md
```

Supported sets:
- `first5`
- `rest`
- `existing`
- `new`
- `existing_plus_new`

Outputs:
- JSON: one object per scenario including decision state, blockers, contradictions, ambiguities, and confidence.
- Markdown: tabular summary for quick review.

Notes:
- This tool is additive and does not replace legacy notebooks/scenario scripts.
- Uses current runtime models from `src/intake/`.
