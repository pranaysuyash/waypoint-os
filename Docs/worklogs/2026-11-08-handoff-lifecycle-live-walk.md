# Worklog 2026-11-08 — Departure-Board Handoff: Live E2E Walk + Fresh-Agency Overview 500 Fix

## Summary

The departure-board → auth → workbench handoff lifecycle (canonical module
`frontend/src/lib/departure-board-handoff.ts`, built 2026-11-07) is now
verified **live in a real browser, end to end, 9/9 test points** via the new
reusable walk tool `tools/verify_departure_board_handoff.mjs`. The walk also
caught and fixed a real P1 on the acquisition path: **every fresh agency
created by signup got 500s on its Operations Overview** (`/trips` +
`/pipeline`).

## What ran

- **T1–T8 (handoff lifecycle)**: board CTA writes sessionStorage handoff →
  `/signup` Case Queue banner (Italy / ✈ ITA) → real signup against
  `:8000` → redirect `/workbench?source=departure-board&case=italy&iata=ITA&prefill=…`
  → intake consumes prefill (live triage extracted destination Italy, 10
  days, stage DISCOVERY) → handoff key cleared post-auth → no stale banner on
  `/signup` or `/login` revisit.
- **T9 (fresh-agency overview)**: `/overview` loads with zero 4xx/5xx.

Evidence: `Docs/sims/assets/handoff_walk/*.png` (viewed: banner, intake
prefill, no-stale-banner, resolved overview), `walk_results.json`.

## Defect found and fixed in-pass (FND-0408, P1)

`GET /trips` lazily seeds a scenario fixture for empty agencies
(`server.py:_seed_scenario_for_agency`). The guard for the expected global
`trips_pkey` collision (`_is_trip_id_integrity_conflict`) never fired because
the asyncio dialect surfaces the **adapted DBAPI**
`AsyncAdapt_asyncpg_dbapi.IntegrityError` — *not* an
`sqlalchemy.exc.IntegrityError` subclass, and without `.orig`. Every fresh
agency's overview therefore 500'd on `/trips` and `/pipeline`.

Fix (`spine_api/server.py`):
1. Seed loop catches `(IntegrityError, AsyncAdapt_asyncpg_dbapi.IntegrityError)`.
2. `_is_trip_id_integrity_conflict` walks `exc` / `.orig` / `__cause__` /
   `__context__` (guarding non-exception `.orig` doubles) for the asyncpg
   23505 signal + constraint name, and adds the Postgres duplicate-key
   message form as fallback (SQLite form kept).

Verification: `tests/test_booking_data.py` 49/49 (collision-skip + unrelated
FK re-raise fixtures both covered), ruff clean, live walk 9/9, overview
screenshot fully resolved.

## Environment incidents during the session (documented for operators)

- **Disk hit 100% mid-walk** (926G used, 1.3G free): shell session spawn
  failed, `/tmp` purged, freshly installed Playwright browser vanished.
  Freed per the rebuildable-cache protocol: uv cache (570M), npm cache,
  chrome-devtools-mcp (127M), and **7.3 GB orphaned HuggingFace hub blobs**
  (shared `hub/blobs` store retains blobs of deleted model dirs; sweep kept
  the 8 blobs referenced by surviving models — ms-marco reranker, whisper,
  pyannote, surya). 9.2G free at close. **The disk is still near-full at
  918/927G — a proper space audit is owed.**
- **Backend died during the 100%-disk window** (BFF 502 "fetch failed");
  restarted from repo root with `TRIPSTORE_BACKEND=sql` pinned.
- Two `next dev` servers share `frontend/.next` (`:3005` user session +
  `:3006` board-flag server) — a known corruption risk; `:3006` exists only
  because the departure-board landing is flag-gated
  (`NEXT_PUBLIC_LANDING_VARIANT=departure-board`, FND-0386).

## Also landed earlier this session (2026-11-07 evening)

- Signup page: restored `sourceParam`/`caseParam`/`iataParam` consts deleted
  by the unslop edit (dangling refs would ReferenceError the handoff flow).
- Handoff lifecycle consolidated into `frontend/src/lib/departure-board-handoff.ts`
  (read/write/clear; 4 call sites migrated; clear-on-auth-success + terminal
  clear in IntakeTab).
- `public_marketing_pages.test.tsx` aligned to the committed checker UI
  contract (FND-0407): tab labels from the unslop rewrite + paste-default
  tab flow. FE suite 202 files / 1,502 tests green.

## State / next

- FE: 202 files / 1,502 tests green; tsc clean.
- BE: targeted 49/49; full suite run kicked off (see
  `Docs/worklogs/` addendum or the suite log for the final count).
- Uncommitted working tree now carries: handoff module + 4 call-site
  migrations, signup/login fixes, checker test alignment, server.py seed
  guard fix, new walk tool + docs. **Commit remains owner-gated.**
- `:3006` (board-flag dev server) left running for manual clicking;
  `:3005` untouched throughout.
