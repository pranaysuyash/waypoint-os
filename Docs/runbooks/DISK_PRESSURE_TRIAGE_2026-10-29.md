# Disk Pressure Triage — 2026-10-29

**Trigger:** the Mimosa scanner advisory stamped on every commit this session
(`scanner_enobufs` — the scanner could not complete for lack of disk). ENOSPC
has caused at least three real project incidents: scanner aborts, test-run
timeouts, and a hung `:8000` backend (FND-0397's root cause class).

**State at triage:** Data volume 926Gi capacity, **899Gi used, 2.8Gi free (100%)**.

## Where the space is (read-only du sweep, 2026-10-29)

| Location | Size | Class |
|---|---|---|
| `~/Projects` | **332G** | user repos — of which `media_experiments` 79G, `qwen-image-21-local` 41G, `fieldcanvas` 13G, `LLM` 12G, `photosearch_experiment` 10G are the top five |
| `/Applications` | 77G | user apps |
| `~/Library` | 50G | mixed (Android SDK+AVDs 5.1G, CoreSimulator 2.1G, Docker VM 1.7G, app caches ~1G, rest = app support data — protected) |
| `/private/var/folders` | 50G | macOS temp incl. active session temp; no `*code_sign_clone*` dirs present |
| `~/Downloads` | 26G | **protected** (AGENTS.md) |
| `/Library` | 27G | system-level, mixed |
| `/opt` (homebrew) | 22G | rebuildable in principle; breaks toolchains if purged |
| `~/Documents` 8.1G / `~/pinokio` 6.2G / `~/Models` 5.8G / `~/Desktop` 3.7G / `~/Audio` 2.9G | ~27G | **protected** (AGENTS.md) |

## What was cleaned (within agent authority — rebuildable caches only)

- `uv cache clean`: removed 144,078 files / **3.1GiB of cache entries** — but free
  space moved only ~0.1Gi: uv cache entries are hardlinked into project
  `.venv`s (same double-count lesson as FND-0397), so blocks stay referenced
  by the venvs themselves. Real recovery requires deleting per-project venvs
  (owner call — they are live environments).
- No `code_sign_clone` temp dirs existed to purge.

## Owner-gated recovery menu (needs explicit naming per AGENTS.md)

Rough yields, most valuable first:

1. **`~/Projects/media_experiments` (79G)** + **`qwen-image-21-local` (41G)** —
   experiment repos; if any are concluded, archiving to external storage
   recovers the most space of any single class.
2. **Per-project `.venv` regeneration** across `~/Projects` (`.venv` dirs are
   recreated by `uv sync`; combined footprint is large but unmeasured here) —
   name the projects whose venvs may be dropped.
3. **`~/Downloads` (26G)** — protected; name files/patterns to remove.
4. **`/private/var/folders` (50G)** — mixed with ACTIVE session temp (including
   this agent's own); a reboot clears stale temp safely. Do not hand-delete
   around live sessions.
5. **Docker images/containers** (`docker system prune`) — 1.7G VM layer +
   whatever images inside; requires Docker decisions.
6. **Android AVD/system-image pruning** (5.1G) — breaks emulator configs that
   get removed; name which AVDs are dead.
7. **`/Applications` (77G)** — user's app choices; name uninstall targets.

## Standing rule while volume is ≥95% full

Do not run: Mimosa deep scans, full Playwright browser installs, model
downloads, Docker pulls, or large fixture generation. The normal-depth
security scan started 2026-10-29 is the exception attempt (smaller artifact
set); if it reports `scanner_enobufs` again, the scan is blocked until the
owner menu above is executed.

---

# Mimosa normal-depth scan — verdict (2026-10-29)

**The standing `scanner_enobufs` advisory is CLEARED at normal depth.** Scan
`scan-2026-10-29T15-47-51.691Z-c914142f4f33` completed and sealed in ~15s
(`sha256:014875d17f5c164c5f1b52ab70e3410358bf14b824efb4a9d290692ec13287d0`;
artifacts under `~/.mimosa/security-scans/project-1a789e004350b2e3…/`). 76
findings (49 HIGH / 4 MEDIUM / 23 LOW), 695 packages scanned. **Zero real
defects** — every class matches the prior FND-0374/FND-0383 adjudications,
re-verified with fresh file:line evidence (all findings below translated from
the scanner's Chinese output per the English-only-output rule):

| Class | Count | Verdict | Fresh evidence |
|---|---|---|---|
| path-traversal (HIGH) | 40 | sanitizer-invisible FP | scripts/tools take operator argv (`generate_scenario.py:64` etc.); `spine_api/persistence.py:3226` has a containment raise *immediately above* the flagged line (`archive_path resolves outside trip_dir` → `ValueError`); `draft_store.py:199` is an atomic envelope write (`.tmp` + `os.replace`) on store-configured paths |
| SSRF (HIGH) | 8 | operator-configured-target FP | `capture_nav_screenshots.py`/`dev_server_manager.py`/`sim4_sims.py` take URL argv from the local operator; `ivr_gateway.py:177/270` + `hotelbeds_adapter.py` are configured-base-URL outbound clients (IVR class split to a finding in the FND-0374 wave) |
| hardcoded-credential (HIGH) | 1 | test-fixture FP | `tools/sim3_runner.py:44` `TEST_PASSWORD` — local sim persona credential, no production surface |
| cross-file taint → SQL (MEDIUM) | 4 | parameterized-ORM FP (FND-0374 class) | route sites `auth.py:337/389/423` + `server.py:3670` flow into `auth_service.py` `.execute(select(...).where(...))` with bound params — verified by direct read of the service; `server.py:3670` is the FND-0382-hardened hash-only collection-token generation |
| insecure-randomness (LOW) | 23 | local-tooling FP | `generate_scenario.py`/`inspect_page.py` — scenario generators and debug tooling; no security boundary |

**Dependency advisories:** the offline advisory DB matched 6 packages /
41 advisories during the scan, but the sealed artifact carries no per-package
detail to adjudicate. Follow-up: re-run the dependency wave's verification
(FND-0292 lineage — advisories were zeroed then) with a networked auditor
(`uv audit`-class tool) and name the 6 packages explicitly. Not blocking:
code-level findings are fully adjudicated above.

**Deep scan remains disk-blocked** until the owner-gated recovery menu above
executes (deep runs the business-logic research pass and is what hit ENOSPC
previously). Standing rule at ≥95% full volume unchanged.

## Deep scan verdict (2026-10-30) — ADVISORY FULLY CLEARED

Deep scan `scan-2026-10-30T13-42-35.404Z-0bc8f0ec942c` **completed and sealed**
(`sha256:028cea40ad2aaf77ebc243a301b2d877190e3b74554b5dcb4877149dc2c7bb56`, ~67s)
at 3.7GiB free — the previous ENOSPC bar no longer applies. 128 findings:
**zero real defects**, every class matches prior adjudications:

- 46 business-logic-risk (the RLS-invisible class) — `tools/mimosa_triage.py`
  posture histogram: 21 AGENCY-DI-guarded, 10 PUBLIC-BY-DESIGN (7 token-verified
  + 3 needs-eye re-verified), 1 capability-token, 2 NON-ROUTE, **5 UNGUARDED-LEAD
  all FALSE on eyes-on** (multiline-signature guards: customer_memory.py:698
  `get_current_agency_id` DI; dsr.py:147 `get_current_agency` +
  `require_permission("trips:write")`; product_b_analytics.py:43
  `require_platform_role("super_admin")`; social_inbound.py:206 agency-DI +
  RLS-scoped store; team.py:62 agency+user+`require_permission("team:manage")`
  + RLS db) — the classifier's documented multiline limitation.
- 40 path-traversal / 8 ssrf / 23 insecure-randomness / 1 hardcoded-credential —
  same script-family + fixture classes adjudicated in FND-0374/0383 and the
  normal-scan verdict above.

Offline advisory DB again over-matched (8 pkgs/37 advisories); the networked
pip-audit truth is 0 (post-fix, see TRV-DP-06 D1 + `tools/check_dependency_
advisories.py` gate). **Standing advisory status: CLEARED at both depths.**
Note: Data volume consumed +24G between 2026-10-29 and 2026-10-30 (899→923G) —
growth source unidentified; the owner menu remains the structural fix.
