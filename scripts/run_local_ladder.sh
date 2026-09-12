#!/bin/bash
# KDD local-model ladder: pull common-config-tier models via ollama, then run
# the graded hybrid-lane harness per model. Throwaway orchestration for the
# §9.3 experiment run; the reusable tool is scripts/run_hybrid_kdd_experiment.py.
cd /Users/pranay/Projects/travel_agency_agent || exit 1
set -a; source .env 2>/dev/null; set +a
MODELS=("gpt-oss:20b" "qwen3.5:4b" "gemma4:e4b" "qwen3:4b" "phi4-mini" "llama3.2:3b" "qwen3:1.7b" "gemma3:1b")
PULLED=()
for m in "${MODELS[@]}"; do
  if ollama list | rg -q "${m%%:*}"; then PULLED+=("$m"); echo "[pull] already local: $m"; continue; fi
  echo "[pull] pulling $m ..."
  if ollama pull "$m" >/dev/null 2>&1 && ollama list | rg -q "$m"; then
    PULLED+=("$m"); echo "[pull] OK: $m"
  else
    echo "[pull] FAILED/unavailable: $m"
  fi
done
echo "[pull] pulled set: ${PULLED[*]}"
SPECS=""
for m in "${PULLED[@]}"; do SPECS="$SPECS,local-ollama/$m"; done
SPECS="${SPECS#,}"
echo "[kdd] running local ladder: $SPECS"
.venv/bin/python scripts/run_hybrid_kdd_experiment.py --skip-baseline --models "$SPECS" --tag "_local_ladder" 2>&1 | tail -5
echo "[kdd] LOCAL LADDER DONE"
