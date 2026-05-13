# Known: Test Data Accumulation Causes Dashboard Counts to Vary

## What you will see

After every few test runs or server restarts, the Overview dashboard shows different numbers:

```
Trips in Planning: 1037 → 1054 → 1014 → changes each session
Lead Inbox:        1767 → 1784 → changes each session
System Check:      565  → 2 → changes each session
```

These are **not bugs in the counting logic**. The counts are correct for what is in the database. The numbers change because the **test agency accumulates all records created by tests, seed scripts, spine_api runs, and manual testing** — and nothing ever cleans them up.

## Root cause

The test agency (`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`) has **~2,838 SQL trips** from many sources:

| Source | Count | Why |
|--------|-------|-----|
| `intake_panel` | 1,282 | Every "Process New Inquiry" from the frontend |
| `spine_api` | 420 | Pipeline execution runs |
| `pytest` | 245 | Automated test runs that submit trips |
| `test` | 271 | Manual / fixture-based testing |
| `seed_scenario` | 30 | Auto-seeding for test agencies |
| Other test fixtures | ~400 | Extraction, booking, document tests |

These accumulate **permanently** — no test or process ever deletes them from SQL. The dashboard then faithfully reports every record.

### Why the number changes

- Each session may add or remove test records depending on what tests ran
- Different test scenarios create different status distributions
- Integrity issues (`System Check` count) depend on which trips are "orphaned" — this changes as new records are created without corresponding workspace/inbox assignments
- The file store (`data/trips/`) has only 89 trips but is not the active backend

## Active backend is SQL

The `.env` file sets `TRIPSTORE_BACKEND=sql`. The file store at `data/trips/` is not read by the dashboard in normal operation. Do not rely on file-store counts matching SQL counts.

## Dual-store architecture

Trip data can live in two places:

| Store | Location | Active by default? | Contains |
|-------|----------|-------------------|----------|
| **SQL (PostgreSQL)** | `waypoint_os` database | Yes (via `.env`) | All ~2,838 records |
| **File (JSON)** | `data/trips/trip_*.json` | Only if `TRIPSTORE_BACKEND` is unset | 89 records (mostly test/seed fixtures) |

Auth data (Users, Agencies, Memberships) is always in PostgreSQL. Trip data goes to whichever `TRIPSTORE_BACKEND` says.

The `TripStore` facade in `spine_api/persistence.py` dispatches to either backend. Both backends now support:
- Comma-separated multi-status filtering (`status=assigned,in_progress`)
- `offset` and `limit` pagination
- Agency scoping (`agency_id`)
- Accurate `count_trips` independent of pagination limits

## How to diagnose

To see the real distribution for the current agency:

```python
# From repo root with .venv active
python3 -c "
import os
os.environ['TRIPSTORE_BACKEND'] = 'sql'
from dotenv import load_dotenv
load_dotenv('.env')
from spine_api.models.trips import Trip
from spine_api.persistence import tripstore_session_maker
from sqlalchemy import select, func
import asyncio

MAIN = 'd1e3b2b6-5509-4c27-b123-4b1e02b0bf5b'

async def main():
    async with tripstore_session_maker() as session:
        stmt = select(Trip.status, func.count()).where(Trip.agency_id == MAIN).group_by(Trip.status)
        rows = await session.execute(stmt)
        for k, v in sorted(dict(rows.all()).items(), key=lambda x: -x[1]):
            print(f'  {k}: {v}')

asyncio.run(main())
"
```

To see all sources:

```python
stmt = select(Trip.source, func.count()).where(Trip.agency_id == MAIN).group_by(Trip.source)
```

## What NOT to do

- **Never truncate, delete, or reset the test database** — this is a hard rule (`AGENTS.md`). The test data represents months of working state.
- **Never revert `TRIPSTORE_BACKEND=sql`** in `.env` — it would silently switch to the file store, making all SQL trips invisible and causing the "missing trips" bug.
- **Do not treat changing dashboard numbers as evidence of a counting bug** — verify against the SQL diagnostic above first.

## Long-term

The dual-store architecture is a known design point. The long-term solution is to migrate fully to PostgreSQL and retire the file store. Until then, agents should:

1. Verify which backend is active before reading trip counts
2. Use the SQL diagnostic to explain unexpected numbers
3. Never assume file-store counts reflect the active data
