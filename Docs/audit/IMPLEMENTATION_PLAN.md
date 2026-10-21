# Implementation Plan — travel_agency_agent (nightly orchestrator)

- Source: `Docs/audit/OPEN_ITEMS_AUDIT.md` (2026-10-12 01:03 IST run)
- Status: PLANNED, not started. All items wait on the owner confirming who currently owns the dirty tree (see DECISIONS_PENDING TRV-DP-01).

| # | Task | Acceptance criteria | Regression check | Rollback |
|---|---|---|---|---|
| 1 | Refresh the LAUNCH_STATUS evidence snapshot (TRV-N01) | Every snapshot row has a dated receipt newer than 2026-10-05: backend pytest totals, frontend vitest + `tsc --noEmit`, `findings.py validate` counts. The verdict changes only with an owner decision. | Blocker list unchanged unless the evidence says otherwise | Restore the prior doc text (doc-only) |
| 2 | TODO-to-findings cross-check (TRV-N02/N03) | Read-only script or test: every `TODO(<ID>)` in `spine_api/ src/` maps to an open findings row. The `legacy_ops.py:667` P1 is registered. | Full backend suite stays green | Remove the new test/script |
| 3 | Root clutter triage (TRV-N04) | Owner-approved list of exact paths to archive or delete. `dogfood_cookies.txt` is classified (secret or not) without its contents being printed. | None (no code) | n/a, nothing is deleted without approval |
