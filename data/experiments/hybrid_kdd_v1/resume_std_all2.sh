#!/usr/bin/env bash
# Resume launcher for the killed 2026-09-16 std_all2 OpenRouter ladder.
# Context: KDD_MODEL_COMPARISON_2026-09-12.md ops log (app-update SIGKILL at
# 11:31). Detach with setsid so app restarts cannot kill the run. --resume
# skips completed (record, arm) pairs and preserves paid-for cache entries,
# so re-invoking after a top-up continues the same run to completion.
set -euo pipefail
cd "$(dirname "$0")/../../.."
exec .venv/bin/python scripts/run_hybrid_kdd_experiment.py \
  --skip-baseline \
  --resume \
  --tag _or_std_all2 \
  --models "$(cat data/experiments/hybrid_kdd_v1/or_std_all2_models.txt)"
