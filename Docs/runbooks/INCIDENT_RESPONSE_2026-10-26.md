# Runbook — Incident Response (FND-0389)

**Scope:** the local/self-hosted Waypoint stack (FastAPI `spine_api` on :8000, Next.js
BFF on :3005, Postgres `waypoint_os` on :5432). Written from the system's RECORDED
failure modes — every triage entry below traces to a real incident or finding in the
store, not hypotheticals. Companion: `DATABASE_BACKUP_RESTORE_2026-10-26.md` (restore +
rollback drills, both verified).

## Severity ladder

| Sev | Definition | Examples (real) | First move |
|---|---|---|---|
| S1 | Data loss risk or live data silently wrong | split-brain (backend reading file-store while trips live in SQL); FORCE-RLS bypass | Stop writes. Engage DB runbook. Page owner. |
| S2 | Product down or core flow broken | API 500s on /runs; BFF rejecting all /api; migrations failing on deploy | Triage table below; restore drill if schema involved |
| S3 | Degraded / noisy | lane-status `unconfigured` floods, single renderer crash, count drift on overview | Ticket + fix in normal flow |

## Triage — the five recorded failure classes, in the order to check them

1. **Wrong backend / split-brain (S1).** Symptom: counts "drop to zero", trips
   "missing" (the 2026-05-03 incident: 40 trips invisible). Cause: server started
   without `TRIPSTORE_BACKEND=sql` → file-store activated → SQL trips invisible.
   Check: `grep '^TRIPSTORE_BACKEND' .env` (must be `=sql`; the pin exists for this
   reason — never remove it), then `curl -s localhost:8000/health`. Fix: restart
   **from the repo root** (`uv run uvicorn spine_api.server:app --port 8000` — starting
   from `spine_api/` dies with `ModuleNotFoundError`).
2. **Schema behind file-head (S2).** Symptom: new columns/tables missing, alembic
   errors on deploy. Check: `python3 -m alembic current` vs `python3 -m alembic heads`.
   Fix: `alembic upgrade head` (transactional DDL; the rollback drill validated
   `downgrade -1` as the escape hatch). If the migration itself is the incident, follow
   the DB runbook's restore-into-scratch procedure before touching live.
3. **RLS / tenant bleed (S1).** Symptom: cross-agency rows visible, or `InsufficientPrivilege`
   on owner reads. Context: FORCE RLS is LIVE on payment_mandates/trips class tables
   (ADR-008 hardening — pg_class-verified, fail-closed); the app sets a per-request GUC,
   and pooled connections lose it at commit (`refresh_or_reselect` handles the known case).
   Check backend logs for RLS denial bursts; NEVER "fix" by weakening RLS — escalate to
   owner with the exact query + role.
4. **Auth/credential outage (S2).** Symptom: everything 401/403. Check `.env` auth
   knobs (`SPINE_API_DISABLE_AUTH` is a TEST-only switch — it must never be set in a
   serving env), JWT secret drift between BFF and API. The BFF proxies auth headers;
   a BFF restart mid-session shows as mass 401s — wait/retry before deeper triage.
5. **Resource exhaustion (S2→S1).** Symptom: tooling + writes fail with ENOSPC
   (recorded 2026-10-25: disk at 100% broke Postgres writes and Playwright). Check
   `df -h /System/Volumes/Data`. Free only rebuildable caches (CACHEDIR.TAG-marked);
   never user data. Postgres at 100% disk can corrupt — if the data volume hit 100%,
   take a backup FIRST thing after freeing space (`tools/db_backup.py`).

## Verification surfaces

- `GET :8000/health` — liveness + component states (cache/rules/LLM circuit). 200.
- `GET :8000/metrics` — Prometheus; JWT-gated (fetch with a token or check via the
  BFF). Request rates + lane statuses here.
- `GET :3005` — BFF up (200). BFF→API parity gate: `tests/test_bff_parity_gate.py`.
- Row-count spot checks: `psql -d waypoint_os -tAc "select count(*) from trips"` —
  compare against the latest `backups/*.manifest.json`.
- Findings gate: `python3 scripts/findings.py validate` (must be OK — a red gate here
  is process-health, not an incident).

## Escalation & communication

- Owner (Pranay) is the escalation point for S1, any FORCE-RLS/tenant event, any
  live-DB restore. **Never run a live-DB restore without owner authorization** — the
  runbook documents the sequence so it is executed, not improvised.
- Record what happened in `Docs/review/FINDINGS_STORE.jsonl` via
  `python3 scripts/findings.py open --title "..." --priority P1 --actor <you>` —
  incidents become findings; findings become fixtures (the failure-flywheel invariant).
- Post-incident: backup immediately after service is restored (post-corruption backup
  first, per the DB runbook), then write the timeline into the finding before closing.

## What this runbook deliberately does NOT cover

- Provider outages (WhatsApp/Meta, SendGrid): the dispatch layer reports honest
  `FAILED`/`NOT_CONFIGURED` states — check lane status in /metrics, not this doc.
- Deploy pipeline (Fly/CI): no production deploy pipeline is live yet; when one lands,
  extend this runbook with its failure modes rather than improvising.
