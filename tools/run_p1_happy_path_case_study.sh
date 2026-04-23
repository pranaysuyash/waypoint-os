#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/Docs/reports"
DATE_TAG="${1:-$(date +%F)}"

mkdir -p "$REPORT_DIR"

echo "[P1] Running backend contract + scenario checks..."
cd "$ROOT_DIR"
uv run pytest -vv --durations=0 \
  --junitxml "$REPORT_DIR/p1_happy_path_backend_${DATE_TAG}.xml" \
  tests/test_e2e_freeze_pack.py::TestScenario1_MessyFamilyDiscovery \
  tests/test_realworld_scenarios_v02.py::TestVagueLead::test_vague_lead_asks_followup_with_missing_blockers \
  tests/test_realworld_scenarios_v02.py::TestWhatsAppDump::test_whatsapp_dump_reveals_ambiguity_gap \
  tests/test_timeline_e2e.py::test_spine_run_emits_audit_events \
  tests/test_timeline_rest_endpoint.py::test_timeline_endpoint_response_structure

echo "[P1] Running backend mode edge checks..."
uv run pytest -vv --durations=0 \
  --junitxml "$REPORT_DIR/p1_happy_path_modes_${DATE_TAG}.xml" \
  tests/test_nb01_v02.py::TestOperatingModeTopLevel::test_emergency_mode \
  tests/test_nb02_v02.py::TestEmergencyMode::test_emergency_suppresses_soft \
  tests/test_nb02_v02.py::TestOwnerReviewAudit::test_audit_mode_adds_feasibility_contradiction \
  tests/test_nb03_v02.py::TestEmergencyMode::test_emergency_only_crisis_questions \
  tests/test_e2e_freeze_pack.py::TestScenario3_AuditModeSelfBooked::test_audit_mode_routing \
  tests/test_e2e_freeze_pack.py::TestScenario5_EmergencyCancellation::test_cancellation_mode_detected

echo "[P1] Running frontend user-journey + workspace checks..."
cd "$ROOT_DIR/frontend"
npm test -- --run --reporter=verbose --reporter=json \
  --outputFile="../Docs/reports/p1_happy_path_frontend_${DATE_TAG}.json" \
  src/app/__tests__/p1_happy_path_journey.test.tsx \
  src/components/workspace/panels/__tests__/IntakePanel.test.tsx \
  src/components/workspace/panels/__tests__/OutputPanel.test.tsx \
  src/components/workspace/panels/__tests__/TimelinePanel.test.tsx

echo "[P1] Case-study run complete. Artifacts saved under: $REPORT_DIR"
