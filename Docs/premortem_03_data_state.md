# PRE-MORTEM: Waypoint OS — DATA PERSISTENCE & STATE

**Date:** 2026-05-05  
**Operator register:** dry alarm — the numbers quietly get worse  
**Scope:** persistence.py (1,695 lines), OverrideStore, AuditStore, FileTripStore, SQLTripStore, TripStore facade, index.json, per-trip JSONL, assignment JSON, migration scripts  

---

## FINDING 1: Override index.json is a non-atomic read-modify-write on every save

1. **WHAT GOES WRONG:**  
   `OverrideStore._update_index` reads the entire `index.json` into memory, mutates it, then writes it back as a full JSON dump. Two concurrent override saves can interleave: Process A reads → Process B reads → Process B writes → Process A writes → Process A's write clobbers B's entry. The index loses B's override_id.  

2. **CHAIN OF EVENTS:**  
   - Agent Priya overrides flag on trip X at 09:20:37.047.  
   - Agent Rahul overrides flag on trip Y at 09:20:37.048.  
   - Both call `_update_index` nearly simultaneously.  
   - One index write overwrites the other.  
   - `get_override(ovr_XXX)` returns None for the clobbered entry.  
   - The override still exists in the JSONL file but is invisible to lookups.  

3. **USER EXPERIENCE:**  
   Agent submits a suppress override. API returns `ovr_abc123`. When they later query `GET /overrides/ovr_abc123`, they get 404. The override is "lost" — the agent believes the flag was suppressed but the system can't find the record.  

4. **EMOTIONAL IMPACT:**  
   A quiet dread — the audit trail says the override exists in the JSONL, but the system can't find it. The agent starts doubting their own actions.  

5. **WHY TEAM MISSES IT:**  
   Tests run sequentially in `tmp_path`. No concurrent save tests. The `_update_index` call looks harmless — it's just "update a JSON file." No one thinks about two FastAPI handlers hitting it at the same millisecond.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: HIGH (already visible in the index.json timestamps — multiple overrides have timestamps within 1-5ms of each other). Impact: HIGH (silent data loss in override index). Score: 9/10.  

7. **TRUST DAMAGE:**  
   An override that the system "lost" is an override that might as well not exist. The agent loses faith that their interventions stick. If a safety flag is supposedly suppressed but the system can't prove it, the founder is exposed to liability.  

8. **RECOVERABILITY:**  
   Poor. The JSONL files still have the data, but there's no index-rebuild utility. The index has 1,146 lines (52KB) — scanning all 144 JSONL files to rebuild is possible but not implemented.  

9. **EARLIEST SIGNAL:**  
   `GET /overrides/{id}` intermittently returning 404 for IDs that appear in per_trip JSONL files. Count of entries in index.json vs count of lines across all JSONL files diverges over time.  

10. **VERIFY BY:**  
    - Count entries in `data/overrides/index.json`.  
    - Count total JSONL lines across `data/overrides/per_trip/*.jsonl`.  
    - If these numbers differ, index corruption has already occurred.  
    - Run two concurrent `save_override` calls in a test harness — verify index contains both.  

---

## FINDING 2: FileTripStore.update_trip has a TOCTOU race between get_trip and write

1. **WHAT GOES WRONG:**  
   `FileTripStore.update_trip` acquires the file lock, then calls `FileTripStore.get_trip` (which does NOT use the file lock — it reads directly), merges updates, and writes. If another thread writes the same trip between `get_trip` and the write, the second write clobbers the first.  

2. **CHAIN OF EVENTS:**  
   - Thread A: acquires lock, reads trip (status: "new").  
   - Thread B: acquires lock, reads trip (status: "new").  
   - Thread A: merges {status: "in_progress"}, writes.  
   - Thread A releases lock.  
   - Thread B acquires lock, reads trip (status: "in_progress" — good, actually the lock prevents this specific sequence).  
   
   Wait — the actual code at line 314: `with FileTripStore._lock: with file_lock(filepath): trip = FileTripStore.get_trip(trip_id)`. But `get_trip` at line 256 does NOT acquire any lock. If another caller invokes `get_trip` directly (e.g., the list API, or a stats endpoint), they see a partially-written file. More critically: `update_trip` reads inside the lock, but if the process crashes between read and write, the write is lost. The `_lock` is a threading lock — it doesn't protect against process crashes mid-write.

3. **USER EXPERIENCE:**  
   Agent updates a trip status. The write fails silently (partial write or crash during json.dump). Next read returns an empty file or a JSON parse error. Trip disappears from the list.  

4. **EMOTIONAL IMPACT:**  
   The trip was there a second ago. Now it's gone. The agent refreshing the dashboard sees it vanish.  

5. **WHY TEAM MISSES IT:**  
   The threading lock + file_lock combo looks robust. No one tests what happens when json.dump is interrupted mid-write (partial JSON on disk). The `open(filepath, "w")` truncates before writing — if crash happens after truncation but before write completes, the file is zero-length.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: MEDIUM (requires crash during a write window). Impact: CRITICAL (total trip data loss for that trip). Score: 7/10.  

7. **TRUST DAMAGE:**  
   A single vanishing trip destroys confidence in the entire store. The founder has no backup.  

8. **RECOVERABILITY:**  
   Zero. No write-ahead log, no temp-file-rename pattern for trip files. Once `open(filepath, "w")` truncates, the old data is gone. No `.bak` file is kept.  

9. **EARLIEST SIGNAL:**  
   `list_trips` returning fewer results over time. Trips that were "new" yesterday are gone today. JSON parse errors in logs from `get_trip`.  

10. **VERIFY BY:**  
    - Check for zero-length `.json` files in `data/trips/`.  
    - grep for `json.JSONDecodeError` in application logs.  
    - Simulate: start `save_trip`, kill process mid-write, check if file is valid JSON.  

---

## FINDING 3: Audit trail events.jsonl hits 10K cap and silently trims — no recovery for compliance

1. **WHAT GOES WRONG:**  
   `AuditStore._trim_if_needed` compacts `events.jsonl` to 10,000 lines every 100 writes. The current file is already at 10,098 lines. This means trim has already kicked in. Old audit events are permanently deleted. The trim uses atomic rename, but the data is gone — there's no archiving, no backup, not even a log message saying "trimmed N events."  

2. **CHAIN OF EVENTS:**  
   - System runs for 2 weeks of dogfood.  
   - Trip modifications generate ~700 events/day.  
   - After ~14 days, events older than ~14 days are silently discarded.  
   - A dispute arises about a trip processed on day 3. The audit trail shows no evidence of it.  
   - The founder cannot prove what happened.  

3. **USER EXPERIENCE:**  
   An agent asks "why was this trip escalated last week?" The audit endpoint returns nothing. The event simply doesn't exist anymore.  

4. **EMOTIONAL IMPACT:**  
   The audit trail is supposed to be the source of truth. When it has holes, it's worse than no audit trail — it gives false confidence. You can't prove what happened, but the system implies it has a record.  

5. **WHY TEAM MISSES IT:**  
   The 10K cap is mentioned in code but not in any config or docs. The trim happens silently. No alert fires when events are trimmed. The `MAX_EVENTS = 10000` constant is buried in a class body.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: CERTAIN (already happening — file is at 10,098 lines). Impact: HIGH for compliance, MEDIUM for operations. Score: 8/10.  

7. **TRUST DAMAGE:**  
   Audit trail gaps make the system legally unreliable. If a traveler disputes a decision and the audit can't show the override history, the founder has no defense.  

8. **RECOVERABILITY:**  
   None. The `.migrated-from` and `.corrupt-*.json` files show that at least 4 corrupt events.json files already existed. The trim is a hard cap with no archiving. Data is permanently gone.  

9. **EARLIEST SIGNAL:**  
   `wc -l data/audit/events.jsonl` hovering around 10,000. Queries for old events returning empty results. The `.migrated-from` and 4 `.corrupt-*.json` files already in the audit directory — corruption has happened 4 times already.  

10. **VERIFY BY:**  
    - `wc -l data/audit/events.jsonl` → should be ~10K (already confirmed at 10,098).  
    - Check earliest timestamp in the file vs. earliest trip creation date. Gap = lost audit history.  
    - Count `.corrupt-*.json` files in `data/audit/` — already 4.  

---

## FINDING 4: No database migration framework — schema changes are ad-hoc scripts run manually

1. **WHAT GOES WRONG:**  
   There is no Alembic (or any migration framework). Schema changes are done via: (a) standalone scripts like `migration_add_assigned_to_id.py`, (b) startup "compatibility checks" in `server.py` that run `ALTER TABLE ADD COLUMN IF NOT EXISTS`, and (c) raw `CREATE TABLE IF NOT EXISTS` in agent_work_coordinator.py. There's no migration version tracking, no rollback path, no way to know which migrations have been applied.  

2. **CHAIN OF EVENTS:**  
   - Founder adds a new column to the Trip model.  
   - They update `_ensure_*_schema_compatibility` in server.py.  
   - They deploy to production without running the migration script first.  
   - SQLTripStore.save_trip tries to set the new column, gets a column-not-found error.  
   - All new trip saves fail. Existing trips can't be updated.  
   - The `_run_async_blocking` bridge throws RuntimeError. The entire TripStore facade is broken.  

3. **USER EXPERIENCE:**  
   New trip submissions silently fail. The API might return 500 or might return the trip ID without actually persisting (depending on error handling). The dashboard shows no new trips.  

4. **EMOTIONAL IMPACT:**  
   The founder deployed what they thought was a minor feature. Instead, the system stopped accepting new data. They don't know why. They can't roll back because there's no migration version — they don't know which ALTERs have and haven't been run.  

5. **WHY TEAM MISSES IT:**  
   The startup compatibility checks create a false sense of safety. They handle the happy path: "column might not exist, add it." They don't handle: "column exists but with wrong type," "index is missing," "constraint was dropped," or "I forgot to add the compatibility check at all." No test verifies that deploying new code to a stale DB actually works.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: HIGH (it's a solo founder deploying manually). Impact: CRITICAL (total save failure). Score: 9/10.  

7. **TRUST DAMAGE:**  
   Data loss during what should have been a routine deploy is a trust-killer. The founder loses confidence in their own ability to ship safely.  

8. **RECOVERABILITY:**  
   If the startup check covers the new column, recovery is automatic on next restart. If it doesn't, recovery requires manual SQL. There's no way to know the current schema version — you have to manually inspect `information_schema.columns`.  

9. **EARLIEST SIGNAL:**  
   `psycopg2.errors.UndefinedColumn` or `asyncpg.exceptions.UndefinedColumnError` in server logs after a deploy. New trip count stalls at zero for more than an hour.  

10. **VERIFY BY:**  
    - Check if there's an `alembic.ini` or `alembic/` directory. (None found.)  
    - List standalone migration scripts in `spine_api/`. Found: `migration_add_assigned_to_id.py`.  
    - Check if `server.py` startup checks cover ALL columns in the current Trip model.  

---

## FINDING 5: OverrideStore.save_override writes JSONL with no file lock — concurrent appends can interleave

1. **WHAT GOES WRONG:**  
   `OverrideStore.save_override` opens the trip's JSONL file in append mode and writes a line. It then calls `_update_index` which also has no file lock. If two processes (e.g., FastAPI workers) append to the same JSONL file simultaneously, the writes can interleave, producing a corrupted line that's not valid JSON.  

   The `file_lock` context manager exists in the codebase and is used by `FileTripStore`, `AssignmentStore`, and `AuditStore._append_event`. But `OverrideStore` and `_add_pattern_override` never use it.  

2. **CHAIN OF EVENTS:**  
   - FastAPI worker 1: `open(trip_X.jsonl, "a")`, starts writing `{"flag": ...`  
   - FastAPI worker 2: `open(trip_X.jsonl, "a")`, starts writing `{"flag": ...`  
   - Both write their JSON lines, but the bytes interleave at the OS level.  
   - Result: `{"flag": "risk_1", ...}{"flag": "risk_2", ...}` becomes one line or partial JSON.  
   - `get_overrides_for_trip` encounters a `json.JSONDecodeError`, silently skips the line.  
   - Override is written but unreadable.  

3. **USER EXPERIENCE:**  
   Agent submits an override. The API returns the override_id. When they query the trip's overrides, theirs is missing — the corrupted line was skipped. They resubmit. Now there are duplicate overrides with no way to know which is canonical.  

4. **EMOTIONAL IMPACT:**  
   The override system feels unreliable. Agents can't trust that their actions are recorded. They start double-submitting "just to be sure."  

5. **WHY TEAM MISSES IT:**  
   The tests use `tmp_path` and run sequentially. Appending to JSONL looks atomic (it's just "append a line"), but multi-process appends to the same file can interleave on Linux without locking. The `file_lock` utility exists in the codebase but wasn't applied here.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: MEDIUM-HIGH (depends on running multiple workers or concurrent requests). Impact: MEDIUM (one corrupted line, one lost override). Score: 6/10.  

7. **TRUST DAMAGE:**  
   Overrides are the human-check on automated decisions. If overrides can silently vanish, the safety net has holes.  

8. **RECOVERABILITY:**  
   Partial. The JSONL file has most lines intact; only the interleaved ones are corrupt. No automated repair exists. Manual inspection is required.  

9. **EARLIEST SIGNAL:**  
   `get_overrides_for_trip` returning fewer overrides than expected. Corrupted JSONL lines visible on manual inspection. Count of overrides in JSONL file != count of parseable lines.  

10. **VERIFY BY:**  
    - Inspect any per_trip JSONL file for malformed lines.  
    - Write a test that appends from two threads/processes simultaneously.  
    - Compare `wc -l` (total lines) with count of JSON-parseable lines.  

---

## FINDING 6: File-to-SQL migration has no tooling — switching TRIPSTORE_BACKEND loses all file-based data

1. **WHAT GOES WRONG:**  
   `TRIPSTORE_BACKEND` env var switches between `FileTripStore` and `SQLTripStore`. There is no migration tool to move existing file-based trips into PostgreSQL. Currently 78 trip JSON files exist in `data/trips/`. If the founder sets `TRIPSTORE_BACKEND=sql` (as `seed_test_user.py` defaults to), those 78 trips vanish from the API. They still exist on disk but are invisible to the SQL-backed store.  

2. **CHAIN OF EVENTS:**  
   - Founder runs dogfood with `TRIPSTORE_BACKEND=file` for weeks. Accumulates 78+ trip files.  
   - Decides to switch to SQL for "production readiness."  
   - Sets env var, restarts server.  
   - Dashboard shows 0 trips. All historical data is gone from the API.  
   - OverrideStore still reads from files, so overrides exist for trips that the API can't find.  
   - AuditStore still reads from JSONL, so audit events reference trips that don't exist in the DB.  

3. **USER EXPERIENCE:**  
   The dashboard goes blank. All trip history is gone. Overrides and audit events reference phantom trips. The system is in an inconsistent state — half file-based, half SQL-based.  

4. **EMOTIONAL IMPACT:**  
   The founder just wanted to "upgrade" to production infrastructure. Instead, they lost access to all historical data. No warning, no migration prompt, no error. Just an empty dashboard.  

5. **WHY TEAM MISSES IT:**  
   The `TripStore._backend()` method is seamless in code — it just returns one class or the other. The disconnect is invisible because each backend only knows its own storage. No startup check says "hey, you have 78 trip files but you're using SQL — want to import them?"  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: HIGH (the default in `seed_test_user.py` is already `sql`). Impact: CRITICAL (total data disappearance). Score: 8/10.  

7. **TRUST DAMAGE:**  
   Losing all historical data during a "simple config change" is catastrophic. The founder might not even realize immediately — they might think the DB is empty and seed new data, creating a split-brain situation.  

8. **RECOVERABILITY:**  
   Technically recoverable — the files still exist on disk. But there's no import tool. The founder would need to write a one-off script to read all JSON files and call `SQLTripStore.save_trip` for each. Data integrity depends on whether the script handles schemas correctly.  

9. **EARLIEST SIGNAL:**  
   Trip count in dashboard drops to 0 after a config change. Override and audit lookups return data for trip IDs that the trip API can't find.  

10. **VERIFY BY:**  
    - Set `TRIPSTORE_BACKEND=sql`, call `TripStore.list_trips()`. Count should be 0 if DB is empty.  
    - Count files in `data/trips/`. If both are non-zero, there's a silent data gap.  
    - Search for any `file_to_sql` or `import_trips` migration utility. (None found.)  

---

## FINDING 7: assignments.json is a single-file bottleneck — full read-modify-write on every assignment change

1. **WHAT GOES WRONG:**  
   `AssignmentStore` stores ALL assignments in a single `assignments.json` file. Every `assign_trip` or `unassign_trip` reads the entire file, modifies it, and writes it back. As trip count grows (currently 78 trips), this file grows linearly. The entire file is rewritten on every single assignment change.  

2. **CHAIN OF EVENTS:**  
   - 500 trips exist. `assignments.json` is ~50KB with 500 entries.  
   - Agent A assigns trip 1: reads all 500 entries, modifies one, writes all 500 back.  
   - Agent B assigns trip 2 at nearly the same time.  
   - The `threading.RLock` prevents thread-level races, but the `file_lock` acquisition on the same file creates contention.  
   - More critically: if the process crashes after `open(filepath, "w")` truncates but before `json.dump` completes, the entire assignments file is wiped. Every assignment is gone.  

3. **USER EXPERIENCE:**  
   All trip assignments vanish. Dashboard shows no agents assigned to any trip. Previous assignment history is gone.  

4. **EMOTIONAL IMPACT:**  
   The assignment system is the operational backbone — who's working on what. Losing it means the team can't coordinate. Everyone thinks someone else is handling trips.  

5. **WHY TEAM MISSES IT:**  
   The file is small now (4KB, ~78 entries). The truncation-before-write risk exists for all JSON stores but is most acute here because the ENTIRE state is in ONE file. The team sees the RLock and thinks it's safe. They don't consider the crash-during-write scenario.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: LOW (requires crash during write), but growing with file size. Impact: HIGH (all assignments lost). Score: 6/10.  

7. **TRUST DAMAGE:**  
   Losing all assignments is operationally devastating. The team has to manually re-assign every trip. Historical "who did what" is gone.  

8. **RECOVERABILITY:**  
   None. No backup, no temp-file-rename pattern for assignments.json. The file_lock protects against concurrent writes but not against crash-mid-write.  

9. **EARLIEST SIGNAL:**  
   `assignments.json` file size growing beyond a few KB. Agent assignment API taking longer due to full-file rewrite. Any zero-length `assignments.json` after a server restart.  

10. **VERIFY BY:**  
    - `du -sh data/assignments/assignments.json` → currently 4KB.  
    - Check if the write pattern uses temp-file-rename. (It doesn't — line 920-921: direct `open(path, "w")` + `json.dump`.)  
    - Simulate: kill process during `assign_trip`, check if file is valid JSON.  

---

## FINDING 8: audit events.json has corrupted 4 times already — the migration path leaves debris

1. **WHAT GOES WRONG:**  
   The `data/audit/` directory contains 4 `.corrupt-*.json` files: `events.corrupt-20260428T102633Z.json`, `events.corrupt-20260502T111955Z.json`, `events.corrupt-20260502T183419Z.json`, `events.corrupt-20260503T083535Z.json`. This means the old `events.json` was corrupted at least 4 times in the first week of use. The migration code renames corrupt files but doesn't alert or log at WARNING level — it just silently renames and moves on.  

2. **CHAIN OF EVENTS:**  
   - Server crashes during a write to `events.json`. File is corrupted.  
   - On next startup, `_migrate_if_needed` tries to `json.load(legacy)`, fails, renames to `events.corrupt-20260503T083535Z.json`.  
   - All audit events from before the corruption are permanently lost.  
   - The new `events.jsonl` starts empty.  
   - No alert is sent. The founder doesn't know audit history was lost.  

3. **USER EXPERIENCE:**  
   The audit dashboard shows events only from the last restart. All prior history is gone and no one noticed.  

4. **EMOTIONAL IMPACT:**  
   Four corruptions in one week means the system is losing audit history repeatedly. The founder believes they have an audit trail. They don't. It's Swiss cheese.  

5. **WHY TEAM MISSES IT:**  
   The migration gracefully handles corruption — it renames the file instead of crashing. This is "good" error handling that hides a "bad" underlying problem. No one looks in the audit directory for `.corrupt-*.json` files. No monitoring checks file integrity.  

6. **LIKELIHOOD x IMPACT:**  
   Likelihood: ALREADY HAPPENING (4 times). Impact: HIGH (each corruption loses all prior audit history). Score: 9/10.  

7. **TRUST DAMAGE:**  
   An audit trail that's been wiped 4 times in one week is not an audit trail. It's a suggestion of one. Any compliance argument based on audit data is indefensible.  

8. **RECOVERABILITY:**  
   The `.corrupt-*.json` files still exist on disk. Partial data recovery might be possible by attempting to parse them manually. But there's no recovery tool.  

9. **EARLIEST SIGNAL:**  
   Count `.corrupt-*.json` files in `data/audit/`. Currently at 4. If this number grows week over week, the write pattern is fundamentally unsafe.  

10. **VERIFY BY:**  
    - `ls data/audit/events.corrupt-*.json | wc -l` → currently 4.  
    - Attempt to `json.load` each corrupt file and see how many events are recoverable.  
    - Check if `_migrate_if_needed` logs at WARNING or ERROR level. (It doesn't — it just renames and returns.)  

---

## The failure nobody wants to talk about:

The system already has 4 corrupted audit files, a 52KB override index being mutated without atomicity, JSONL files being written without locks, 78 trip files one `open("w")` away from vaporization, and no migration path off any of it. The founder is running this solo, pre-launch, with a persistence layer that was fine for a prototype and is quietly becoming a data-loss machine. Every "graceful" error handler — rename the corrupt file, skip the malformed line, reinitialize the index — is a small funeral for data that used to exist. The system doesn't crash. It just forgets. And by the time anyone notices, it's been forgetting for weeks.