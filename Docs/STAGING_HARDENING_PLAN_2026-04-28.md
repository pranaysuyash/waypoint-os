# Waypoint OS Production Hardening Plan (Stage 2)
**Date:** 2026-04-28
**Status:** PROPOSED

## Overview
This document outlines the architectural and functional hardening required to transition Waypoint OS from its current "dogfood" development state to a production-ready environment.

## Audit Findings Summary (NO-GO for Launch)
- **P0:** `POST /api/trips` returns mock data.
- **P0:** `TripStore` uses local JSON files (plaintext).
- **P1:** Python environment mismatch (3.11 vs 3.13).
- **P1:** 14/496 frontend test failures.

## Proposed Implementation

### 1. Spine Pipeline Integration
- **File:** `frontend/src/app/api/trips/route.ts`
- **Action:** Replace `return NextResponse.json(MOCK_TRIP)` with an internal `fetch` or direct call to `spine_api`.
- **Validation:** Ensure `raw_input` is correctly serialized and passed to the intake stage.

### 2. SQL Persistence (PostgreSQL)
- **Engine:** SQLAlchemy + Alembic.
- **Location:** `spine_api/persistence.py`
- **Logic:**
  - Create `SQLTripStore` implementing the `TripStore` interface.
  - Use `DATA_PRIVACY_MODE` to switch backends.
  - Implement field-level encryption for PII fields (Email, Phone) using `cryptography` Fernet.

### 3. Environment Stabilization
- **Action:** Standardize on Python 3.13.
- **Dependency:** `uv sync` to refresh the venv.

### 4. Quality Gates
- **Frontend:** Fix Vitest regressions.
- **Backend:** Enable `pytest` coverage for SQL paths.

## Next Steps
1. User approval of `implementation_plan.md`.
2. Execute Phase 1: Pipeline Connection.
3. Execute Phase 2: PostgreSQL Migration.
