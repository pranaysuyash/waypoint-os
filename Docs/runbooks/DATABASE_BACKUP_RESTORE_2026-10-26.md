# Runbook — Database Backup & Restore (FND-0388 / FND-0394)

Verified 2026-10-26 by live drill against `waypoint_os` (50,341 trips / 1,361 users /
1,359 agencies; artifact 36,891,756B, sha256 241992ceb666…, 66 tables). Tools:
`tools/db_backup.py` + `tools/db_restore.py`. This runbook supersedes the earlier
same-day draft (consolidated; the `--i-accept-live-overwrite` flag it referenced no
longer exists — live-DB restore is refused unconditionally). Finding closures carry
this doc as evidence.

## The one rule

**Never touch `waypoint_os` with a destructive command.** All restores and migration
drills happen in a THROWAWAY scratch database (`waypoint_restore_drill_<date>`),
created and dropped within the drill. The data-safety doctrine (AGENTS.md) forbids
TRUNCATE/DELETE/reset against the live DB; this runbook is written so you never need one.
The restore tool enforces this: the live database name is REFUSED as `--target`,
unconditionally.

## Backup

```bash
set -a; source .env; set +a      # provides DATABASE_URL
python3 tools/db_backup.py                # → backups/<db>_<ts>.dump + manifest
python3 tools/db_backup.py --keep-last 14 # + prune artifacts beyond 14
```

- Custom format (-Fc, compressed); verified post-write via `pg_restore --list`;
  manifest.json records sha256, size, and core-table row counts **at backup time**
  (trips/users/agencies/audit_logs/execution_events) — the restore tool diffs against them.
- Cadence: before every deploy, before every migration, daily. (`--keep-last 14` ≈ two
  weeks of dailies ≈ 500MB.)
- **FORCE RLS / backup role:** `pg_dump` as the app role (`waypoint`) FAILS on
  FORCE-RLS tables (`advisor_payouts` et al. — the ADR-008 tenant-isolation hardening
  denies the owner's COPY by design). Run backups as a `BYPASSRLS` role (`pranay` is
  superuser locally). **Never weaken RLS to make backups easier** — grant the backup
  role, not the data.

## Restore drill (the only restore you should ever practice)

```bash
set -a; source .env; set +a
createdb waypoint_restore_drill_<date>                    # scratch — throwaway
pg_restore --no-owner -d waypoint_restore_drill_<date> \
  backups/waypoint_os_<ts>.dump
psql -d waypoint_restore_drill_<date> -tAc "select count(*) from trips"   # vs manifest
python3 tools/db_restore.py --from backups/<artifact>.dump \
  --target waypoint_restore_drill_<date> --drop-existing  # createdb+restore+verify
dropdb waypoint_restore_drill_<date>                      # cleanup
```

Verified drill result (2026-10-26): restore exit 0; trips 50,341 = manifest 50,341;
users 1,361 ✓; agencies 1,359 ✓.

## Migration rollback drill (FND-0394)

```bash
export DATABASE_URL="postgresql+asyncpg://<admin>@localhost/waypoint_restore_drill_<date>"
python3 -m alembic current          # = backup-time revision
python3 -m alembic downgrade -1     # the rollback you are validating
python3 -m alembic upgrade head     # re-apply everything after backup-time
python3 -m alembic current          # = file head
psql -d waypoint_restore_drill_<date> -tAc "select count(*) from trips"  # data intact
dropdb waypoint_restore_drill_<date>
```

Verified drill result (2026-10-26): head `add_email_verification_tokens` → downgrade →
`add_user_consent_verification` → upgrade → `add_revoked_tokens (head)`; trips still
50,341 after the round-trip.

### Three gotchas the drill caught (all recorded, all handled)

1. **Driver:** `alembic/env.py` builds an ASYNC engine — `DATABASE_URL` must keep the
   `postgresql+asyncpg://` scheme for alembic (plain `postgresql://` dies with
   `psycopg2` missing; the app's runtime env already has the right scheme).
2. **Backup-vs-files drift:** the backup pins `alembic_version` at backup time. If
   migrations landed after the backup, a restored DB is BEHIND file head — the drill's
   `alembic upgrade head` step is not optional; it is exactly what a real restore needs.
   (Caught live: `waypoint_os` moved from `add_email_verification_tokens` to
   `add_revoked_tokens` between this backup and drill.)
3. **Ownership:** run the restore/alembic as the role that owns the scratch's objects
   (or `REASSIGN OWNED` after restore). Mixed-owner scratches fail alembic with
   `permission denied for table alembic_version`.

### Restoring INTO production (real incident, not a drill)

Last resort only — it overwrites the live DB. Sequence: stop the API → take a
just-in-case backup of the current (broken) state → drop/recreate `waypoint_os` owned by
`waypoint` → `pg_restore --no-owner --role waypoint -d waypoint_os <artifact>` as the
admin role → `alembic upgrade head` → restart API → verify `/health` + row counts vs
manifest. Every step after the just-in-case backup is documented here so it is never
improvised. Prefer point-in-time granularity? Add WAL archiving (`archive_mode=on`) —
recorded as the follow-on, not built here.

## Store hygiene

`backups/` is generated artifacts only. Manifests are small; keep them with their dump.
