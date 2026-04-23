# Operational Integrity & Proactive Diagnostics (Phase 2 Add-ons)

**Date**: Wednesday, April 22, 2026
**Status**: Strategic Additions

This document outlines the final phase of "Cockpit" hardening: shifting from reactive monitoring to proactive system health management.

---

## 1. Proactive Integrity Watchdog (Drift-Detection)
**Objective**: Automate data consistency checks to ensure the SSOT pipeline never drifts silently.

- **Implementation**: Implement a background cron job within `spine-api` that runs the `DashboardAggregator` every 5-15 minutes.
- **Alerting**: If `integrity_meta.consistent` returns `False`, trigger an automated alert via `src/analytics/review.py`'s `_emit_notification` function.
- **Goal**: Proactive awareness. System failures should be detected by the system, not the operator.

## 2. "Why" vs "What" Performance Benchmarking
**Objective**: Use the AuditStore to turn analytics into a coaching/diagnosis tool.

- **Implementation**: In `Owner Insights`, introduce a "Regression Analysis" card that compares an agent's current `AuditStore` logs (Why) against their macro `ConversionRate` (What).
- **Goal**: Automatically surface the root cause of performance dips (e.g., "Agent X performance dropped because they started ignoring [Constraint Flag X]").

## 3. Systemic Feedback Loop
**Objective**: Capture the root cause of human overrides to inform AI fine-tuning.

- **Implementation**: Update `ReviewControls.tsx` to include a required "System Error Category" dropdown when `request_changes` is triggered.
- **Data Capture**: These categories (e.g., "Constraint Ignored", "Math Error", "Tone") must be logged in the `AuditStore`.
- **Insight Surfacing**: The `DashboardAggregator` will report a "Top 3 Systemic Errors" metric, providing a clear, evidence-based roadmap for AI re-training.

---

## 4. Operational Implementation Guide
- **Phase A**: Integrate these into the current backend service layers.
- **Phase B**: Frontend UI exposure (Integrity Banner, Regression Card, Feedback Dropdown).
- **Verification**: All background tasks must have their own internal audit log entries to ensure the "Watchdog" itself doesn't become a source of drift.
