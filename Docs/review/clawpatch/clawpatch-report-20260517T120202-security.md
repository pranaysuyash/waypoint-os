# clawpatch report

findings: 19

## medium: Hardcoded test agency ID as default for PUBLIC_CHECKER_AGENCY_ID

id: fnd_sig-feat-backend-spine-api-0ff40_8d65c4c30a
category: security
confidence: medium
triage: risk
status: open
feature: Backend API service (feat_backend_spine_api)

evidence:
- spine_api/server.py:189-193 (DEFAULT_PUBLIC_CHECKER_AGENCY_ID)

If PUBLIC_CHECKER_AGENCY_ID is unset in production, all public-checker submissions are attributed to the test/development agency. This silently contaminates production data with test-bound records, and the test agency's trip quota/metrics are polluted by public traffic. The _get_public_checker_agency_id function strips whitespace but doesn't validate the format or check that the agency actually exists in the database.

recommendation:
In production/staging, require PUBLIC_CHECKER_AGENCY_ID to be set explicitly (similar to TRIPSTORE_BACKEND enforcement). Log a warning at startup when the default is used. Consider validating that the resolved agency ID exists in the database during lifespan startup.

test analysis:
Tests use the default test agency, so the default works correctly in test environments. No test runs the public checker with PUBLIC_CHECKER_AGENCY_ID unset in a production-like environment.

suggested regression test:
Start the server without PUBLIC_CHECKER_AGENCY_ID set in a staging-like environment (ENVIRONMENT=staging) and verify it either refuses to start or logs a prominent warning.

minimum fix scope:
spine_api/server.py: add startup validation that rejects the default test agency ID in production/staging environments, matching the TRIPSTORE_BACKEND validation pattern

## medium: Mixed sync/async endpoint patterns for TripStore calls create inconsistent concurrency behavior

id: fnd_sig-feat-backend-spine-api-23ec2_04f428034f
category: maintainability
confidence: high
triage: risk
status: open
feature: Backend API service (feat_backend_spine_api)

evidence:
- spine_api/server.py:1541-1566 (list_trips)
- spine_api/server.py:1570-1576 (get_trip)
- spine_api/server.py:1637-1644 (patch_trip)
- spine_api/server.py:2019-2040 (update_booking_data)

The codebase mixes two patterns for calling TripStore from endpoints: (1) async endpoints using await _ts(TripStore.method, ...) which offloads to asyncio.to_thread, and (2) sync endpoints calling TripStore.method() directly, which goes through _run_async_blocking and the serialized bridge. Pattern 1 adds an unnecessary thread hop (async -> threadpool -> bridge loop) but at least doesn't block the event loop. Pattern 2 blocks a threadpool thread AND serializes through the bridge lock. Both patterns are inferior to directly calling SQLTripStore async methods from async endpoints. The inconsistency also makes it harder to reason about performance characteristics: two similar endpoints (list_trips vs get_trip) have very different concurrency profiles.

recommendation:
Standardize on async endpoints with direct SQLTripStore calls. For file-backend compatibility, keep _ts as a thin wrapper for FileTripStore calls but use SQLTripStore directly when the backend is SQL. This eliminates the bridge for the hot path and provides true concurrent SQL access via asyncpg's connection pool.

test analysis:
Tests don't measure concurrency. Both patterns produce correct results for sequential test requests.

suggested regression test:
Concurrent load test comparing throughput of async-only endpoints vs sync endpoints under SQL backend. The sync endpoints should show significantly lower throughput.

minimum fix scope:
Progressive: convert high-traffic sync endpoints (get_trip, patch_trip, get_booking_data, update_booking_data) to async with direct SQLTripStore calls, maintaining FileTripStore compatibility via _ts fallback

## medium: FileTripStore.update_trip_for_agency has TOCTOU race on agency_id check

id: fnd_sig-feat-backend-spine-api-35531_d69e59fc57
category: data-loss
confidence: medium
triage: risk
status: open
feature: Backend API service (feat_backend_spine_api)

evidence:
- spine_api/persistence.py:478-485 (FileTripStore.update_trip_for_agency)

The method reads the trip outside any lock (get_trip does not acquire FileTripStore._lock), checks agency_id, then calls update_trip which acquires the lock. Between the read and the write, another concurrent request could modify the trip — including changing its agency_id — allowing a cross-tenant update to slip through. In contrast, update_trip_if_version_for_agency correctly holds the lock across both read and write (lines 438-475). This is a time-of-check-to-time-of-use vulnerability in the file backend. The SQL backend is not affected because SQLTripStore.update_trip_for_agency uses a WHERE agency_id clause.

recommendation:
Wrap the read-check-write sequence in FileTripStore.update_trip_for_agency inside FileTripStore._lock + file_lock, matching the pattern used by update_trip_if_version_for_agency.

test analysis:
No concurrent request tests exist for the file backend. Single-threaded tests would not surface the race.

suggested regression test:
Test: two threads call update_trip_for_agency concurrently on the same trip with different agency_ids. Verify that only the agency that owns the trip can update it, and that the other gets None.

minimum fix scope:
spine_api/persistence.py: FileTripStore.update_trip_for_agency method — wrap read+check+write in FileTripStore._lock

## low: PORT and WORKERS env vars parsed with bare int() — crashes on invalid input

id: fnd_sig-feat-backend-spine-api-59ad1_f8b87544b7
category: build-release
confidence: high
triage: risk
status: open
feature: Backend API service (feat_backend_spine_api)

evidence:
- spine_api/server.py:535-537
- spine_api/server.py:76-82 (_int_env)

The _int_env helper (lines 76-82) safely handles empty strings, non-numeric values, and negative numbers with fallback defaults. However, PORT and WORKERS use bare int() which raises ValueError on invalid input like SPINE_API_PORT=abc, crashing at import time with an unhelpful traceback. This is inconsistent with the validated pattern used for OTel configuration.

recommendation:
Replace bare int() calls with the existing _int_env helper: PORT = _int_env('SPINE_API_PORT', 8000) and WORKERS = _int_env('SPINE_API_WORKERS', 1).

test analysis:
Tests run with default env vars. No test sets invalid PORT/WORKERS values.

suggested regression test:
Test startup with SPINE_API_PORT=abc and SPINE_API_WORKERS=-1, verifying the server starts with defaults instead of crashing.

minimum fix scope:
spine_api/server.py lines 536-537: replace int(os.environ.get(...)) with _int_env(...)

repro:
Set SPINE_API_PORT=abc and start the server. It crashes with ValueError.

## high: patch_trip endpoint accepts unvalidated Dict[str, Any] allowing arbitrary field writes

id: fnd_sig-feat-backend-spine-api-a1754_5969d868dc
category: security
confidence: high
triage: confirmed-bug
status: open
feature: Backend API service (feat_backend_spine_api)

evidence:
- spine_api/server.py:1637-1644 (patch_trip)
- spine_api/server.py:1651-1663

The endpoint accepts an unbounded Dict[str, Any] and only blocks 'stage' and 'booking_data'. All other fields pass through to TripStore.update_trip_for_agency, which sets any attribute on the trip record that has a matching column (SQL) or key (file). An authenticated user could set internal fields like 'agency_id' (tenant reassignment), 'run_id', 'safety', 'internal_bundle', 'traveler_bundle', or 'validation' directly — bypassing business logic guards. The _sync_manual_trip_fields helper enriches certain fields but does not filter unknown keys. SQLTripStore.update_trip_for_agency uses hasattr(trip_obj, key) to decide what to set, meaning any ORM column can be written.

recommendation:
Replace Dict[str, Any] with a Pydantic model that explicitly lists allowed fields. At minimum, add an allowlist check that rejects keys not in a known safe set (status, follow_up_due_date, origin, destination, budget, party, etc.) before calling update_trip_for_agency.

test analysis:
Tests likely send known-good field sets. No test attempts to write internal fields like agency_id or internal_bundle through this endpoint.

suggested regression test:
Send PATCH /trips/{id} with {"agency_id": "different-agency"} and verify the request is rejected with 400/422. Also test with internal_bundle, safety, and validation fields.

minimum fix scope:
spine_api/server.py: replace Dict[str, Any] with a Pydantic PatchTripRequest model or add an explicit field allowlist before the update call

## high: Sync-async bridge _run_lock serializes all SQL TripStore operations

id: fnd_sig-feat-backend-spine-api-f30e1_a7b61e7391
category: concurrency
confidence: high
triage: confirmed-bug
status: open
feature: Backend API service (feat_backend_spine_api)

evidence:
- spine_api/persistence.py:1203-1217 (_SyncAsyncBridge.run)
- spine_api/persistence.py:1218-1227 (_get_sync_async_bridge)

_SyncAsyncBridge.run() holds self._run_lock for the entire duration of each database operation (submit + wait). This serializes all synchronous TripStore calls through a single global lock: only one SQL operation can be in-flight at a time, regardless of how many concurrent requests arrive. Under concurrent load, every sync endpoint (get_trip, patch_trip, get_booking_data, etc.) queues behind this single lock, creating a throughput ceiling. Additionally, _get_sync_async_bridge() is not thread-safe: two threads can both see _SYNC_ASYNC_BRIDGE is None and create two bridges, leaking a daemon thread and potentially creating two event loops processing SQL operations independently.

recommendation:
Remove _run_lock from _SyncAsyncBridge.run() — asyncio.run_coroutine_threadsafe already serializes coroutines on the single-threaded bridge loop. For the _get_sync_async_bridge race, add a threading.Lock around initialization. Longer-term, migrate sync endpoints to async with direct SQLTripStore calls, eliminating the bridge entirely.

test analysis:
Tests typically run with a single request or sequential requests, so the serialized bridge doesn't surface as a bottleneck. Concurrency tests would be needed to expose the throughput limitation.

suggested regression test:
Concurrent load test: fire 10+ simultaneous GET /trips requests and verify they complete in < sum-of-serial-latencies, not sequentially. Also test _get_sync_async_bridge under concurrent thread creation.

minimum fix scope:
spine_api/persistence.py: remove _run_lock from _SyncAsyncBridge.run(), add threading.Lock guard to _get_sync_async_bridge(). Optional: migrate sync endpoints to async.

## low: Root package.json missing required metadata fields (name, version, private)

id: fnd_sig-feat-config-7528cb5b98-3740d_714c296eb0
category: maintainability
confidence: high
triage: risk
status: open
feature: Project config package.json (feat_config_7528cb5b98)

evidence:
- package.json:1-3

The root package.json contains only the `packageManager` field. npm considers `name` and `version` required fields for a valid package.json, and `private: true` is necessary to prevent accidental `npm publish` of a repository root. While this may be intentional for a Python-primary project with a JS frontend subdirectory, the absence of `private: true` means `npm publish` from the root could succeed if a name were ever added, and tooling that parses package.json for project metadata (e.g., dependabot, renovate, security scanners) may skip or misidentify this project.

recommendation:
Add at minimum: `{ "name": "waypoint-os", "private": true, "packageManager": "pnpm@11.1.0+..." }`. The `private: true` field prevents accidental publish. Adding `name` helps tooling identify the project.

test analysis:
Metadata completeness in package.json is not covered by runtime tests.

suggested regression test:
CI lint step that validates package.json has `name` and `private` fields: `node -e "const p=require('./package.json'); process.exit(p.name && p.private ? 0 : 1)"

minimum fix scope:
Add `name` and `private` fields to the root package.json.

repro:
1. Run `npm publish --dry-run` from root — npm will warn about missing name/version but not error on dry-run
2. Security/dependency scanning tools may not identify this as a valid package

## medium: Empty root package.json provides no build, quality, or release configuration

id: fnd_sig-feat-config-7528cb5b98-4ffc5_7533d016d4
category: build-release
confidence: medium
triage: risk
status: open
feature: Project config package.json (feat_config_7528cb5b98)

evidence:
- package.json:1
- package-lock.json:1-5

The root package.json is an empty object with no name, version, scripts, dependencies, devDependencies, or workspaces field. The lockfile confirms zero packages are resolved at the root level. Meanwhile, the actual frontend configuration lives entirely in frontend/package.json with proper scripts (build, lint, test, typecheck). The feature title claims 'Build, release, or quality configuration in package.json' but this file contains none of those. The project detection also found no typecheck/lint/format/test commands at root level, which is consistent. This creates two concrete risks: (1) anyone running npm commands at the repo root will get no-op or error behavior with no guidance, and (2) CI or tooling that expects root-level scripts (e.g., npm test, npm run lint) will silently succeed with no work done. If this is intentional as a monorepo root, it should declare workspaces pointing to frontend/ — currently it does not, so npm install at root does nothing useful.

recommendation:
Either (a) add a workspaces field pointing to frontend/ and root-level scripts that delegate to the frontend (e.g., "test": "npm run test --workspace=frontend"), or (b) if the root package.json is truly vestigial, document that all npm commands must be run from frontend/ and add a postinstall or prepublishOnly script that prints a redirect notice.

test analysis:
No tests exist for this feature. The feature has no test files listed and the empty package.json itself contains no test script to verify.

suggested regression test:
Add a CI check that runs `npm run test --workspaces --if-present` from the repo root to verify that workspace scripts are wired correctly. Alternatively, a minimal smoke test that asserts package.json contains a 'scripts' key with expected command names.

minimum fix scope:
package.json only — add name, version, workspaces (or scripts), and optionally a root-level redirect script. Update package-lock.json to reflect workspace resolution.

repro:
Run `npm test` or `npm run build` at the repo root. Both will error or no-op because package.json has no scripts field.

## medium: Missing pnpm-lock.yaml — declared package manager has no lockfile

id: fnd_sig-feat-config-7528cb5b98-6bca2_608e3034a4
category: build-release
confidence: high
triage: risk
status: open
feature: Project config package.json (feat_config_7528cb5b98)

evidence:
- package.json:2

The packageManager field tells Corepack to use pnpm, but no pnpm-lock.yaml exists in the repository. Without a lockfile, `pnpm install` will resolve dependencies fresh each time, potentially pulling different versions than what developers tested against. This defeats the reproducibility guarantee that lockfiles provide. The current frontend dependencies are locked via package-lock.json (npm), not pnpm-lock.yaml, so pnpm install would produce a different resolution tree.

recommendation:
After resolving the package manager choice (pnpm or npm), run the chosen tool's install command to generate the correct lockfile, then commit it.

test analysis:
Lockfile absence is a repository configuration issue, not a runtime behavior covered by tests.

suggested regression test:
CI step that checks for the presence of a lockfile matching the declared package manager: `test -f pnpm-lock.yaml`

minimum fix scope:
Run `pnpm install` to generate pnpm-lock.yaml and commit it (assuming pnpm is the chosen manager).

repro:
1. Run `ls pnpm-lock.yaml frontend/pnpm-lock.yaml` — both return 'No such file or directory'
2. Run `pnpm install` — resolves dependencies fresh rather than from a lockfile

## medium: Empty root package.json is a zombie config with orphaned lockfile and node_modules

id: fnd_sig-feat-config-7528cb5b98-bde70_ee4fe5d962
category: build-release
confidence: high
triage: risk
status: open
feature: Project config package.json (feat_config_7528cb5b98)

evidence:
- package.json:1
- package-lock.json:1-6

The root package.json is an empty JSON object {}. It has no name, version, scripts, dependencies, or devDependencies. Yet a package-lock.json exists with lockfileVersion 3 referencing name 'travel_agency_agent' but with packages: {} (zero locked packages). An empty node_modules/ directory also exists at root. This is a zombie configuration: the lockfile and node_modules imply npm was once used at root, but the package.json is now vacuous. Running npm install or npm ci at root would succeed but install nothing, giving a false sense of readiness. The detected project metadata shows all commands (typecheck, lint, format, test) as null, which is a direct consequence of the empty package.json having no scripts field.

recommendation:
Either (a) remove the root package.json, package-lock.json, and node_modules/ if the frontend/ package.json is the sole source of truth, or (b) convert to a proper npm workspace by adding workspaces: ["frontend"] to root package.json with a name/version and shared scripts that delegate to the frontend workspace (e.g., 'build': 'npm run build -w frontend'). Option (b) is recommended for monorepo-style coordination and gives the detected project meaningful commands.

test analysis:
Build/config issues at the package.json level are not typically covered by unit tests; they surface as CI failures or developer confusion when running commands at the project root.

suggested regression test:
Assert that npm ls --depth=0 at project root exits 0 and lists expected top-level deps, or that npm run build exits 0 from root.

minimum fix scope:
Add name, version, and workspaces field to root package.json, or remove it along with root package-lock.json and node_modules/.

repro:
cd /Users/pranay/Projects/travel_agency_agent && npm install && npm run build # fails: no scripts defined

## high: Package manager declaration conflicts with actual lockfile — root declares pnpm but frontend uses npm lockfile

id: fnd_sig-feat-config-7528cb5b98-cd9bd_4da25c0f36
category: build-release
confidence: high
triage: risk
status: open
feature: Project config package.json (feat_config_7528cb5b98)

evidence:
- package.json:2
- frontend/package-lock.json:1-4

The root package.json declares pnpm 11.1.0 via the Corepack `packageManager` field, which tells Node.js tooling to enforce pnpm as the project's package manager. However, the frontend subproject uses an npm v3 lockfile (package-lock.json) with no corresponding pnpm-lock.yaml anywhere in the repository. This means: (1) `pnpm install` at the root would create its own resolution tree that doesn't match what's in package-lock.json; (2) developers using `npm install` in frontend/ will update package-lock.json while pnpm users will create pnpm-lock.yaml — diverging dependency trees; (3) CI or onboarding scripts that respect the packageManager field will run pnpm, producing a different node_modules than what was tested locally with npm. The node_modules directory under frontend/ was installed via npm (package-lock.json lockfileVersion 3), confirming the mismatch is active in the current checkout.

recommendation:
Choose one package manager and fully commit. Recommended: since root already declares pnpm via Corepack, remove frontend/package-lock.json, run `pnpm install` to generate a proper pnpm-lock.yaml, and add a pnpm-workspace.yaml at the root if monorepo support is needed. Alternatively, if npm is preferred, remove the `packageManager` field from root package.json and ensure only package-lock.json is used. Either way, ensure .gitignore excludes the opposite lockfile format and the team aligns on one tool.

test analysis:
There are no tests for the root package.json configuration. Build/reproducibility issues from lockfile mismatch typically surface only in CI or fresh installs, not in an already-populated node_modules directory.

suggested regression test:
Add a CI check that verifies only one lockfile format exists in the repo and that it matches the declared packageManager field. A simple script: `if grep -q pnpm package.json && ! ls pnpm-lock.yaml 2>/dev/null; then echo 'FAIL: pnpm declared but no pnpm-lock.yaml'; exit 1; fi`

minimum fix scope:
Remove frontend/package-lock.json, generate pnpm-lock.yaml via `pnpm install`, optionally add pnpm-workspace.yaml. Or remove the packageManager field and standardize on npm.

repro:
1. Note root package.json declares packageManager pnpm@11.1.0
2. Note frontend/package-lock.json is an npm lockfile (lockfileVersion 3)
3. Run `ls pnpm-lock.yaml frontend/pnpm-lock.yaml` — both absent
4. Run `pnpm install` — creates a new pnpm-lock.yaml with potentially different resolution than package-lock.json
5. Run `npm install` in frontend/ — updates package-lock.json, diverging from pnpm's resolution

## low: Root lockfile is inconsistent: lockfileVersion 3 with requires true and zero packages

id: fnd_sig-feat-config-7528cb5b98-d19e6_58cd2d5d74
category: maintainability
confidence: high
triage: risk
status: open
feature: Project config package.json (feat_config_7528cb5b98)

evidence:
- package-lock.json:1-6

lockfileVersion 3 does not use the 'requires' field (that was v1/v2 semantics). The combination of lockfileVersion 3, requires: true, and packages: {} is internally inconsistent. While npm tolerates this today (it simply installs nothing), it indicates the lockfile was generated or edited incorrectly and could cause unexpected behavior with npm ci or npm install under future npm versions.

recommendation:
If keeping the root package.json, regenerate the lockfile with npm install after adding proper content. If removing the root package.json, delete the lockfile as well.

test analysis:
Lockfile format consistency is not covered by application tests; it is a build infrastructure concern.

minimum fix scope:
Regenerate or delete root package-lock.json when root package.json is populated or removed.

repro:
cat package-lock.json # observe lockfileVersion 3 + requires: true + packages: {}

## medium: Dockerfile ENTRYPOINT hardcodes --workers 4, making SPINE_API_WORKERS env var ineffective

id: fnd_sig-feat-deployment-infrastructu_0567ee92c7
category: bug
confidence: high
triage: confirmed-bug
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- Dockerfile:65
- Dockerfile:72

The ENV sets `SPINE_API_WORKERS=4` but the ENTRYPOINT hardcodes `--workers 4` as a uvicorn CLI argument. The env var is never read by uvicorn (it doesn't recognize `SPINE_API_WORKERS` natively). Changing the env var at runtime has zero effect — the worker count is always 4. This creates a misleading configuration surface where operators believe they can tune worker count via env but actually cannot.

recommendation:
Either remove `SPINE_API_WORKERS` from ENV (if hardcoding is intentional) or replace the hardcoded `--workers 4` with a shell ENTRYPOINT that reads the env var: `ENTRYPOINT ["sh", "-c", "uvicorn spine_api.server:app --host 0.0.0.0 --port ${SPINE_API_PORT:-8000} --workers ${SPINE_API_WORKERS:-4}"]`. Note: this requires switching from JSON to shell form, which changes signal handling. Alternatively, use a startup script.

test analysis:
No test validates container behavior under different env var values.

suggested regression test:
Build and run the image with `SPINE_API_WORKERS=1` overridden, then check `ps aux | grep uvicorn` to confirm single worker.

minimum fix scope:
Dockerfile line 72 — make worker count configurable via env var

repro:
docker run -e SPINE_API_WORKERS=1 spine-api — observe uvicorn still starts with 4 workers

## medium: Placeholder image reference ghcr.io/your-org/spine-api:latest in fly.toml — deploy will fail

id: fnd_sig-feat-deployment-infrastructu_082d2d19b1
category: build-release
confidence: high
triage: risk
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- fly.toml:11

The image reference `ghcr.io/your-org/spine-api:latest` contains the literal placeholder `your-org`. A `fly deploy` using this config will attempt to pull a non-existent image and fail. This is a pre-launch artifact that was never updated with the actual organization/registry path.

recommendation:
Replace `your-org` with the actual GitHub org or remove the `[build]` section and add a Dockerfile-based build instead: `[build] dockerfile = "Dockerfile"`. This is more maintainable and avoids the separate registry push step.

test analysis:
No test validates fly.toml image references resolve.

suggested regression test:
CI check: if fly.toml contains `your-org`, fail the build.

minimum fix scope:
fly.toml line 11 — replace placeholder with real image or switch to Dockerfile build

repro:
fly deploy — observe image pull failure

## critical: Dockerfile ENTRYPOINT uses spine-api (hyphen) but Python package is spine_api (underscore) — container crashes on startup

id: fnd_sig-feat-deployment-infrastructu_1c3f0480f1
category: bug
confidence: high
triage: confirmed-bug
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- Dockerfile:60
- Dockerfile:72

The actual Python package directory is `spine_api/` (underscore, confirmed on disk). Python import paths cannot contain hyphens. The COPY directive on line 60 copies a non-existent `spine-api/` directory (the copy will silently fail or copy nothing if Docker doesn't error on missing source in build context). The ENTRYPOINT on line 72 passes `spine-api.server:app` to uvicorn, which will raise `ModuleNotFoundError: No module named 'spine-api'` on every container start. This is exactly the naming-class mismatch the project's AGENTS.md naming conventions section was written to prevent.

recommendation:
Change COPY and ENTRYPOINT to use `spine_api` (underscore). Update all three owned files consistently: Dockerfile line 60 → `COPY spine_api/ ./spine_api/`, line 72 → `"spine_api.server:app"`. Also fix fly.toml render.yaml service names if they reference the hyphenated form for Python import paths.

test analysis:
No integration test runs the Docker container end-to-end. The feature has zero tests listed. The bug only manifests at container startup, which is outside the scope of unit/integration tests.

suggested regression test:
Add a CI step that builds the Docker image and runs `docker run --rm spine-api python -c "import spine_api.server"` to verify the import path resolves.

minimum fix scope:
Dockerfile lines 60 and 72 — rename `spine-api` to `spine_api` in COPY and ENTRYPOINT

repro:
docker build -t spine-api . && docker run spine-api — observe ModuleNotFoundError crash

## medium: build-essential persists in production runtime image — expands attack surface

id: fnd_sig-feat-deployment-infrastructu_3244cdcedd
category: security
confidence: high
triage: confirmed-bug
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- Dockerfile:18-21

`build-essential` (gcc, make, etc.) is installed in the `base` stage and inherited by `runtime`. Build tools are only needed in the `deps` stage for compiling C extensions. Having gcc and a full toolchain in the production image makes it easier for an attacker who gains RCE to compile and run exploits. The `curl` binary is needed for the healthcheck, so it should stay in runtime, but `build-essential` should not.

recommendation:
Move `build-essential` installation to the `deps` stage only. Keep `curl` in base (needed for healthcheck). Restructure: base installs only `curl`; deps inherits base and adds `build-essential`; runtime inherits base (without build tools).

test analysis:
No image scanning or CIS benchmark test exists in the pipeline.

suggested regression test:
Add `docker run --rm spine-api dpkg -l build-essential` to CI — should return non-zero (package not installed).

minimum fix scope:
Dockerfile lines 18-21 — move build-essential to deps stage, keep curl in base

## low: PUBLIC_CHECKER_AGENCY_ID hardcoded in fly.toml and render.yaml — test UUID in production config

id: fnd_sig-feat-deployment-infrastructu_79e38b8690
category: security
confidence: high
triage: confirmed-bug
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- fly.toml:23
- render.yaml:18-19

The UUID `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b` is the default test agency ID (per AGENTS.md data safety section). Deploying it as a production env var means the public checker is bound to a test agency. If a different agency should be the public checker in production, this is a silent misconfiguration. At minimum, this value should be a secret or deploy-time variable, not committed plaintext.

recommendation:
Move `PUBLIC_CHECKER_AGENCY_ID` to Fly secrets (`fly secrets set`) and Render's secret env vars (`sync: false` with no default value). Document the required value in deployment runbooks.

test analysis:
No test validates deployment env var sourcing for production vs test.

suggested regression test:
CI lint: flag `PUBLIC_CHECKER_AGENCY_ID` in non-secret config sections of fly.toml and render.yaml.

minimum fix scope:
fly.toml line 23 and render.yaml lines 18-19 — move to secrets with no committed default

## high: Hardcoded database password in docker-compose.yml committed to version control

id: fnd_sig-feat-deployment-infrastructu_d7ac224c22
category: security
confidence: high
triage: confirmed-bug
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- docker-compose.yml:7

The Postgres password `waypoint_dev_password` is committed as plaintext in a tracked file. If this compose file is ever used in a non-local context (or if the repo is shared), the credential is exposed. Even for local-only use, committed secrets create drift risk and accidental deployment to other environments.

recommendation:
Replace the hardcoded password with a Docker Compose variable substitution: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-waypoint_dev_password}`. Document the default in a `.env.example` (not `.env`) and add `.env` to `.gitignore` if not already present.

test analysis:
No tests validate docker-compose configuration. Secret scanning is not part of the test suite.

suggested regression test:
Add a pre-commit hook or CI check that greps for plaintext passwords in docker-compose.yml and other infra files.

minimum fix scope:
docker-compose.yml line 7 — use variable substitution with safe default

## high: TRAVELER_SAFE_STRICT=0 baked into production Docker image and fly.toml — safety mode permanently disabled

id: fnd_sig-feat-deployment-infrastructu_fbe177056b
category: security
confidence: high
triage: confirmed-bug
status: open
feature: Deployment and infrastructure config (feat_deployment_infrastructure)

evidence:
- Dockerfile:67
- fly.toml:20

The project's safety model (documented in README) enforces traveler-safe output separation validated by 38+ tests. Baking `TRAVELER_SAFE_STRICT=0` into the Docker image ENV and fly.toml [env] means production containers always run with safety strict mode disabled. This cannot be overridden without rebuilding the image (Dockerfile ENV takes precedence over runtime docker run -e for the same key unless explicitly re-passed). In fly.toml, the non-secret env section means the value is visible in the Fly dashboard and cannot be overridden by `fly secrets set` without removing it from [env] first.

recommendation:
Remove `TRAVELER_SAFE_STRICT` from both the Dockerfile ENV block and fly.toml [env]. Instead, set it as a Fly secret (`fly secrets set TRAVELER_SAFE_STRICT=0`) and as a docker-compose env_file or runtime `-e` flag. This allows per-environment control and prevents the default from being 'unsafe'.

test analysis:
Tests verify safety behavior with strict mode enabled. No test validates the deployment configuration's env defaults.

suggested regression test:
Assert in CI that Dockerfile and fly.toml do not contain `TRAVELER_SAFE_STRICT=0` in non-secret sections.

minimum fix scope:
Dockerfile line 67 and fly.toml line 20 — remove TRAVELER_SAFE_STRICT from baked-in config; move to secrets/runtime env

