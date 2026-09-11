# Mimosa HIGH-Residual Triage — 2026-09-11

**Closes the triage gap in FND-0266** (the 2026-09-10 scan record asserted "noise floor" wholesale;
this annex disposes each HIGH cluster with repository evidence, per the Elena-council audit).
Complements `Docs/review/MIMOSA_FULL_SCAN_RECORD_2026-09-10.md` and replaces its blanket
"noise" framing with per-finding dispositions.

**Source scan:** `~/.mimosa/security-scans/project-1a789e004350b2e32cc42e24/scan-2026-09-10T18-54-35.095Z-8b0238d645fd/findings.json`
(sealed wave-2 verification scan referenced by commit `798dddd`): 113 findings — **59 HIGH**
(48 static path-traversal hypotheses + 9 business-logic ownership hypotheses + 2 cross-file
hypotheses), 3 MEDIUM, 51 LOW. Scanner titles were emitted in Chinese; English glosses below
are translated source labels.

## Dispositions

### A. Business-logic "resource id from request, no ownership/tenant binding observed" — 9 findings — MITIGATED (scanner verdict: inconclusive)

| Location | Evidence |
|---|---|
| `spine_api/routers/drafts.py:133,145,189,206,223,223,242,264` (8) | Every flagged line sits on the draft promote/action path whose cross-tenant guard was verified live: caller-supplied `trip_id` resolves via `TripStore.get_trip_for_agency(trip_id, agency.id)` (`drafts.py:287`); foreign trips return an indistinguishable 404 with a metadata-only `draft_promote_denied` audit record (`drafts.py:288-307`); promoted drafts are single-shot (`drafts.py:280-281` 409). The scanner flagged "no ownership observed" because the binding happens *downstream* of the flagged lines — its own verdict is `inconclusive`, not `vulnerable`. |
| `spine_api/routers/trip_observability.py:55` (1) | False positive on inspection today: the handler calls `TripStore.get_trip_for_agency(trip_id, agency.id)` and 404s on miss before reading events (`trip_observability.py:47-50`). |

### B. Cross-file hypotheses — 2 findings — MITIGATED (verified today)

| Location | Hypothesis | Evidence |
|---|---|---|
| `spine_api/routers/auth.py:303` → `refresh_access_token` | SQL-injection entry via refresh token | The service uses SQLAlchemy ORM `select(User).where(User.id == user_id)` — server-side parameterized (`spine_api/services/auth_service.py:287-306`); the token value never interpolates into SQL text. |
| `spine_api/server.py:1644` → `_seed_scenario_for_agency` | Path-traversal entry via seed name | `seed_name` derives from the `SEED_SCENARIO` **environment variable** (operator config), never from request input (`server.py:1655-1657`); it selects a repo-local fixture, and the helper is a startup/dev seeding path, not a serving route. |

### C. Static path-traversal hypotheses — 48 findings

**C1. `spine_api/persistence.py` (14) — MITIGATED WITH ONE RESIDUAL NOTE.**
The only flagged line where a file name meets an archive write carries an explicit
resolve/containment guard: `persistence.py:2830-2832` resolves the joined path and rejects
escape from the trip directory. The remaining flagged lines build paths from
server-generated identifiers (UUID attachment ids, store-resolved agency/trip ids), not
raw client strings — the scanner cannot observe provenance across the store boundary
(hence `static` kind, no verdict). **Residual:** future code adding client-supplied file
names on these seams must reuse the `:2830` guard pattern; recommend extending the
tenant-isolation CI gate with a persistence-module path-join check (follow-up, not a defect).

**C2. `src/decision/cache_storage.py` (4) + `src/intake/geography.py` (4) — MITIGATED BY CONSTRUCTION.**
All flagged joins resolve inside repo-local `data/`/cache directories from module
constants and hashed/normalized keys; no client-controlled component reaches the join.
(Geography loads its 590k-city dataset from the packaged data dir.)

**C3. Dev tooling (12) — OUT OF PRODUCTION SCOPE.**
`tmp/fix_test_ids.py` (2), `tmp/parse_stash0.py` (1), `frontend/design-lab/inspect-app-dna.py` (2),
`generate_scenario.py` (1), `inspect_page.py` (1), `scripts/generate_niche_scenario.py` (1),
`scripts/generate_types.py` (1), `scripts/migrate_agentnotes_to_columns.py` (1),
`tools/apply_async_pipeline.py` (1), `spine_api/draft_store.py`/`src/decision/override_learning.py`/
`src/memory/store.py` dev-seeding joins. None are serving-path code. Recommendation (already
implied by the 2026-09-09 gate table): exclude `tmp/`, `design-lab/`, and one-off scripts from
production scan scope so real residual signal is not diluted.

## Relation to open findings

- The 2026-09-09 gate table's two real SSRF rows were **closed** by the 2026-09-10 wave
  (canonical `spineUrl()`); this annex does not reopen them.
- **FND-0117 / F-30 (corporate_policy no-JWT auth, P1, open)** is *not* part of this HIGH
  residual and must not be read as triaged away by it — it remains an open P1 with runtime
  authorization proof outstanding (`Docs/review/F30_CORPORATE_POLICY_AUTH_BOUNDARY_2026-09-05.md`).
- Net new defects from this triage: **zero**. Net follow-ups: (1) persistence path-join CI
  extension, (2) dev-tooling scan-scope exclusion, both logged here as recommendations.
