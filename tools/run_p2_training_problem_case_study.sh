#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/Docs/reports"
DATE_STR="$(date +%F)"

mkdir -p "$REPORT_DIR"

echo "[P2-S4] backend targeted suite"
(
  cd "$ROOT_DIR"
  /usr/bin/time -p uv run pytest -q \
    --junitxml "$REPORT_DIR/p2_training_problem_backend_${DATE_STR}.xml" \
    tests/test_nb02_v02.py::TestOwnerReviewAudit::test_owner_review_mode \
    tests/test_nb02_v02.py::TestOwnerReviewAudit::test_audit_mode_adds_feasibility_contradiction \
    tests/test_nb02_v02.py::TestDecisionResultStructure::test_decision_result_has_all_fields \
    tests/test_nb03_v02.py::TestInternalDraftAssumptions::test_soft_blockers_listed_as_assumptions \
    tests/test_nb03_v02.py::TestToneScaling::test_low_confidence_cautious_tone \
    tests/test_nb03_v02.py::TestToneScaling::test_high_confidence_direct_tone
) 2>&1 | tee "$REPORT_DIR/p2_training_problem_backend_timing_${DATE_STR}.txt"

echo "[P2-S4] frontend targeted suite"
set +e
(
  cd "$ROOT_DIR/frontend"
  /usr/bin/time -p npm test -- --run --reporter=verbose --reporter=json \
    --outputFile="../Docs/reports/p2_training_problem_frontend_${DATE_STR}.json" \
    src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx \
    src/components/workspace/panels/__tests__/SuitabilitySignal.test.tsx \
    src/components/workspace/panels/__tests__/SuitabilityPanel.test.tsx
) 2>&1 | tee "$REPORT_DIR/p2_training_problem_frontend_timing_${DATE_STR}.txt"
FRONTEND_EXIT=${PIPESTATUS[0]}
set -e

if [[ "$FRONTEND_EXIT" -ne 0 ]]; then
  echo "[P2-S4] frontend suite failed (exit $FRONTEND_EXIT). See JSON/timing artifacts."
  exit "$FRONTEND_EXIT"
fi

echo "[P2-S4] completed successfully"
