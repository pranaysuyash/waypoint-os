# Execution Status and Complete Findings/Tasks Register — 2026-09-04

## Current continuation — 2026-09-08

This section supersedes September 5 checkout/count assertions, not their
historical receipts. Live HEAD is now
`096ceba39e320b527ed60e47f0c54d8d00a11748`; 179 paths were staged at the initial
read-only check and no unstaged paths were reported before this continuation's
edits. The intervening commit contains 585 changed paths. Its existence does
not establish this agent performed it, that remote delivery succeeded, or that
the current candidate passed gates. No Git mutation was performed here.

Current canonical/CI-companion lifecycle check: **207 rows — 151 open,
55 closed, one deferred; zero warnings**. The newer PA/AT work expands the
register; the historical 145-row count is not the current inventory.

The user explicitly requested Luna/high subagents and Astra/light-or-medium
help when needed. Two bounded Luna/high lanes were started: quote-contract
implementation/tests, and read-only attachment authorization/durability review.
Main owns integration, evidence records and full gates. All staged preview
labels and unrelated product changes must be preserved; no writer identity is
inferred from dirty state.

### Instruction/context refresh boundary

The required command
`/Users/pranay/Projects/agent-start/bin/agent-start --project travel_agency_agent --skip-index`
failed before regeneration: canonical Review Doctrine title is `1.2`, but its
internal-version field contains `1.2` plus an explanatory parenthetical, which
the integrity validator treats as a different version. The failure is retained;
no validator bypass or shared-doctrine edit was made. Main read the canonical
Review 1.2 and Architecture 1.1 directly. Existing generated context remains
dated September 7 and records skipped/locked retrieval; it is not fresh complete
retrieval. Operating 8.0 hash remains
`ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a`.

### Current verification handles

- Backend before-change baseline: session `69057`,
  `USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -p no:cacheprovider`.
  The runner detected an existing server on port 8000 and warned of shared
  integration-state interference. It was not stopped. This is explicitly not
  a hermetic baseline. Terminal **exit 0: 4,091 passed, 10 skipped, 9 warnings
  in 385.71s**. Warnings were one unregistered `live_db` marker and eight
  multi-threaded Python `fork()` warnings. Product quote changes began only
  after this before-change run completed.
- Frontend: session `62261`, from `frontend`,
  `npm run typecheck && npm run lint && npm test -- --run && npm run build`.
  Terminal **exit 1**: typecheck passed, lint failed with two companion-page
  hook errors (`set-state-in-effect` and loader use before declaration).
  Tests/build were not reached. A bounded Luna/high worker owns the companion
  lifecycle repair and tests; no lint suppression is accepted as the repair.
- During-run source/config/test checkpoint at `2026-09-08T06:02:42.974Z`:
  1,461 paths, SHA-256
  `4d1e11b8e40d1dd5b1fd01902d57c9050c03489ac319d07af42d5537d1c7af57`.
  This checkpoint was taken after launch, not an immutable pre-run snapshot.

The initial insurance source added preview/carrier-confirmation labels but
retained unsupported affirmative eligibility and the universal deadline
calculation. The quote worker has now replaced those primary results with
nullable, explicitly unevaluated values, preserving the three illustrations.
Its first focused receipt was **33 passed in 23.75s**, plus scoped Ruff and
diff checks. Reported S3 mutations restoring affirmative eligibility and a
fabricated deadline each failed the new assertions, then were restored.
These are local fixture receipts with explicit auth bypass, not production
authorization or carrier proof. Independent source review accepted the main
contract; parent review then found UTC-normalization overflow outside the
exception handler and obsolete 14-day bounds arithmetic. A second failing-first
correction followed; the first receipt does not cover that final change.

Full backend after-run session `92587` uses the same command as the baseline.
The normalization correction arrived while this run was active; no immutable
final-candidate claim is made. Terminal **exit 1: nine failed, 4,057 passed,
12 skipped, eight warnings, 37 setup errors in 867.97s**. Failure/error IDs
are confined to `test_booking_data.py` and `test_booking_documents.py` in the
returned summary. Traceback excerpts explicitly show `OSError: [Errno 28]
No space left on device`, numbered temporary-directory creation failure,
and `asyncpg.exceptions.CannotConnectNowError` with database recovery/startup
messages. These are observed environment failures, not assumed quote regressions
or evidence that every failure is explained by ordinary contention. The tool
truncated the large traceback output; this note preserves the terminal counts,
affected modules and observed error classes, not a claimed complete raw log.

Post-run read-only checks: root volume 927 GB / 917 GB used / about 9.6 GB
available (99% used), inode use 7%; `.runtime` 50 MB, frontend `.next` 412 MB,
test trips 32 MB. These later sizes do not reconstruct peak usage or identify
who caused/recovered the transient exhaustion. `pg_isready` then reported
accepting connections and existing port-8000 `/health` returned HTTP 200.
No service restart, cleanup, database reset or deletion was performed.

Parent serialized retry session `63445` selects insurance quote/F-31/capability
and the two failed booking modules through the canonical runner, after the
worker's backend test processes ended. Terminal **130 passed, 3,989 deselected
in 52.54s**, exit 0. All five changed Python files passed Ruff. It remains shared-environment evidence,
not a hermetic full after-pass. Existing attachment findings are not closed by
the quote work or by preview labels.

Second full after-run `57559` is serialized against other backend test writers
and adds only `--tb=short` to the canonical command. The existing developer
server remains running, so its shared-target warning remains applicable.
Terminal **exit 0: 4,109 passed, 10 skipped, eight warnings in 509.72s**.
All eight warnings are the pre-existing multithreaded `fork()` deprecation in
ledger tests; the unknown `live_db` marker warning is absent. Each of the five
scoped fingerprints below matched after the run, and HEAD remained unchanged.
This is a successful local full gate, not isolated infrastructure, hosted,
provider or end-to-end attachment proof. The earlier failed receipt remains.
Pre-run SHA-256 checkpoints (a scoped fingerprint, not the entire repository):

| File | SHA-256 |
|---|---|
| `spine_api/routers/insurance.py` | `53f34f2f8566f6836daf6664d6a04c87966dff090a86345d2efbd13287925662` |
| `tests/test_insurance_quote_evidence.py` | `8b21dbf513ec4e125c83a87534b22834b51841a7cb96cb42b9c4d555482de528` |
| `tests/test_register_wave_f30_f40.py` | `098107f6ee349f2d3915da6f606538f1bb8d7ac578229cbba1abd69aba226ec6` |
| `tests/test_capability_routers_batch.py` | `c3fd642aed1ac045e3de4839c7a697c476bd2a32d8f0dae0abb3ff8d7f7e54c3` |
| `tests/conftest.py` | `ce472c30cc515578115d687a6d5713d0b288073ab68248d97d2f8b4cbd48eaac` |

### F-19: durable verification isolation requirements

Luna/high's bounded read-only review found no isolated full-suite runner.
The local runner only warns about port 8000, uses the shared default database
and omits the migration step that CI performs. `session_client` stabilizes one
process's event loop but commits a fixed test principal; fixture rollback does
not undo service commits through other sessions. File-backed trips, audit,
assignments and related test paths are also shared between pytest processes.
The collection hook enables HTTP integration from a hardcoded port-8000 login
probe; PostgreSQL availability checks only TCP readiness, not database ownership
or schema version. CI has a fresh PostgreSQL service per job, not proof of local
isolation. These source findings describe risks; they do not identify the actor
or full causal chain behind this run's ENOSPC/database recovery.

Required coherent remediation: per-run real PostgreSQL and file-store namespace,
migrations/bootstrap against that explicit target, coordinated full-suite writer,
capacity/readiness preflight, redacted target identity and source receipts, and
an explicit HTTP integration tier with a separately allocated server/base URL.
All clients/fixtures must honor the selected namespace; changing one environment
variable while fixed paths remain is insufficient. Preserve real PostgreSQL
semantics rather than substituting a SQLite-only green gate.

**Accept with modification:** fail closed on ambiguous/shared verification
targets, not merely because an unrelated developer service exists on port 8000.
A correctly isolated run should coexist with it. Disposable resource creation
must have exact ownership and retained receipts; cleanup is a separate exact-
target operation, never deletion of ambient application/database state.
The design remains unimplemented. F-19 remains open and no commit-ready claim
follows from a focused retry.

### Companion lifecycle and private-data boundary — September 8

The frontend baseline's two hook errors led to a bounded repair of
`frontend/src/app/(traveler)/companion/page.tsx` and its honesty tests.
The React effect discipline skill informed the separation of URL-derived
identity from request lifecycle. Main and Astra/medium review found that a
trip-only guard was insufficient: token changes and A → missing token → A
could reveal old accepted data before revalidation. The final data-owning
child is keyed by exact trip/token identity, with AbortController/cancellation
and `cache: 'no-store'` for each new graph request.

An intermediate token-hashed persistent cache was reviewed and **superseded**,
not accepted as the long-term solution. Backend share verification refreshes
revocations and checks TTL per request; an earlier success does not authorize
offline replay after a later request fails. The optional offline-policy question
has no recorded answer. The stated safe default is online revalidation, not an
assumed approval for offline access.

| Capability / old path | Final implementation / preservation |
|---|---|
| Private journey cache read/write and transport fallback | Removed from this component; no dead write-only cache retained. Existing localStorage entries are untouched, not migrated or deleted. |
| Authorized journey display | Preserved after a fresh successful response for the current identity; denial, missing token, mismatched trip, empty graph and tested malformed shapes abstain. |
| URL-derived state in mount effect | Replaced by `useSearchParams` and keyed child; source identity and request state no longer drift independently. |
| Late response from previous identity | Cancellation plus remount prevents it from overwriting the current view. |
| Offline/verification badge claims | Replaced by neutral “Itinerary loaded”; no booking/provider verification inferred from successful loading. |
| Sample and preview behavior | Existing honesty tests retained; provider-provenance compatibility fallback retained for older response shapes, not for reading persisted caches. |

Worker final receipt: **12/12 focused tests**, targeted ESLint zero errors,
typecheck and diff check passed. The initial URL-race regression failed against
the baseline before the repair. Final tests also cover token removal/replacement,
same-token return before new validation, network failure after prior authorized
load/remount, null/non-array-node responses and preservation of existing storage.
This is local mocked-request behavior evidence (S2 where failing-first demonstrated),
not a browser/real-auth proof or a universal malformed-payload validator claim.

The worker's earlier build passed before the final privacy supersession; it is
not the final build receipt. Parent full frontend gate `62910` runs typecheck,
lint, all tests and build after ownership release. Before-run SHA-256:

- Companion page: `448fb100191df679920f4469f4e3aac4975d0bc2198134f8270f8cb994ddc39b`.
- Companion tests: `ac0f7e76fecb5ab24cc18e479cf951b89a0a07911e724432a088180b8f4a2a23`.

Gate `62910` ended exit 1: typecheck and lint passed; **179 test files / 1,344
tests passed in 351.01s**; build compiled and typechecked but failed during page
data collection with `PageNotFoundError: Cannot find module for page: /_document`
and ENOENT. Test collection preceded the subsequent null-destination regression;
this receipt does not cover the final candidate. A live developer server and
production build shared `.next`. That is an observed unsafe output boundary,
not a demonstrated forensic explanation of every build failure.

Parent found the backend legitimately returns `destination: null`; the new
frontend guard had rejected that otherwise valid itinerary. Regression `39376`
failed first (one failed / 12 skipped), then `31330` passed **13 tests** after
allowing null and retaining the existing destination fallback. Astra/medium
independently reviewed that exact corrected source. Later browser inspection
found unsupported satellite/consular connectivity copy and fixed local times.
Regression `20669` failed first; final focused `53372` passed **14 tests in
3.94s** after the SOS surface consistently said demonstration/no alert sent,
sample location and demo progress. Stored transfer/hotel start times are shown
when available; missing times abstain, while explicitly sample times remain in
sample view. Node count now says itinerary items, not days. This is not a full
calendar/day-projection implementation or durable emergency service.

The Browser Daemon skill was used for visible browser inspection. Existing
backend `/health` returned 200, `/metrics` returned **401**, and frontend root
returned 200. The missing-token companion requested no journey graph and showed
the private-link abstention, but CSS and four inspected asset requests included
404s; the screenshot was unstyled. Preserved and viewed failure artifact:
`Docs/review/companion-no-token-before-copy-2026-09-08.png`. It is not clean
render proof. Metrics' 401 agrees with `core/middleware.py::PUBLIC_PATHS`,
which excludes `/metrics`; `server.py::metrics_endpoint` incorrectly says it
remains public. PA-10 retains the scrape-auth/documentation gap; no public
metrics exposure was added and no authenticated scrape is claimed.

### Frontend output isolation — September 8

Luna/high implemented phase-aware configuration in the existing
`frontend/next.config.mjs`: development `.next-dev`, production build and server
`.next`. Existing standalone packaging, headers, image settings and staged
F-43 wildcard-rewrite removal are preserved. Git, ESLint, Vitest and both Docker
contexts exclude the new generated directory. Parent corrected the generated
type include to `.next-dev/types/**/*.ts`, matching installed Next **14.2.35**
`writeConfigurationDefaults.js` and the observed generated directory; inherited
type includes remain. No build-output deletion or manual server restart was used.

Decision sources: official [Next.js 14 configuration functions and phases](https://nextjs.org/docs/14/app/api-reference/next-config-js)
and [Next.js 14 distDir contract](https://nextjs.org/docs/14/app/api-reference/next-config-js/distDir).
Worker focused test failed twice before implementation and passed **2/2**
afterward; scoped lint/typecheck passed. Parent full gate `48337` runs typecheck,
lint, all frontend tests and build after ownership release. Its result remains
pending until a terminal receipt is appended. A checkpoint just after launch:

| File | SHA-256 |
|---|---|
| Companion page | `6074edd9103d6178cfb106c6a430ea58e60c220c9bbd06844657bce164f1099a` |
| Companion tests | `a11a3390ac49a5a86a7bb424dc9f9dec74f71ff2224cb50d428853d21903f42c` |
| Next config | `87553de1635d91e9e1e18101e211dacbd143fcf373b6145260ddacef9b7d59f2` |
| TypeScript config | `4ce9bf8693fe7b44af4666d6c35273cea4f76db35fdc178835064c68491277a1` |
| Next config tests | `7b15243d643cc1efb6a1943d3cd7bcae6a4db92482f2b61fc08f1ed7ed266ed8` |

Follow-up visible browser check after phase isolation loaded styled companion
content at desktop 1682×1083 and mobile 390×844. Both screenshots were inspected:
`Docs/review/companion-no-token-desktop-2026-09-08.png` and
`Docs/review/companion-no-token-mobile-2026-09-08.png`. The missing-token route
showed the private-link requirement and demo-only SOS; no graph resource request
was observed. Mobile document width equaled viewport width (390 px). Fresh
console inspection showed React DevTools information and two unused font-preload
warnings, with no repeated asset 404s in that captured navigation. These are
Tier 3 browser observations for unauthenticated abstention only; real signed
itinerary/provider behavior and installed-device behavior are not proved.

Independent final review accepted privacy, nullable destination, sample-time
and output-isolation semantics but identified pending fetch and network failure
sharing one unavailable state. A bounded follow-up worker now owns explicit
per-identity request states. Consequently `48337` is an intermediate gate, not
the final immutable candidate. Terminal **exit 0**: typecheck/lint, **180 files /
1,348 tests in 391.60s**, then production build completed all 60 static pages
and route/build-trace output. Existing dynamic-server-usage messages appeared
for cookie/search-param API handlers during static probing; those handlers
were emitted as dynamic routes. This is a successful local build receipt, not
a warning-free log or coverage of subsequently added request-state/manifest tests.

Install metadata also advertised unsupported offline itineraries, live alerts
and crisis SOS. Parent's new `companion-manifest.test.ts` failed first (`50626`)
then passed (`36699`, one test, 5.09s) after the manifest description stated
online private-link itinerary access, sample itinerary and SOS demonstration.
Start URL/icons/install configuration are preserved. Existing installed metadata
may remain stale; service-worker registration/cache ownership is under separate
read-only review. No browser storage purge or unrelated cache deletion occurred.

### Service-worker boundary and live denial follow-up

Read-only source review found the companion registers `/sw.js` at origin-root
scope; the separate SLM downloader has no discovered registration/message
sender. The v1 shell worker precaches only companion/manifest, but globally
looks through CacheStorage on every request and deletes every other named cache
on activation. No current graph-response CacheStorage writer was found; this
is an unsafe interception/ownership boundary, not demonstrated existing private
graph replay. Main's fresh browser observed the root-scope active `sw.js` and
`waypoint-companion-v1` cache. No unrelated profile was controlled.

Accepted narrow remediation, assigned to Luna/high: same-origin GET only,
exact query-free shell/manifest allowlist, explicit private API/no-store bypass,
network-first public shell/manifest with fallback only in its new owned cache.
All existing caches are preserved; remove the previous global deletion behavior
without executing cache cleanup. Legacy retirement requires a separate exact
ownership/retention policy. PWA metadata discovery and SLM activation are not
included. [MDN CacheStorage.match](https://developer.mozilla.org/en-US/docs/Web/API/CacheStorage/match)
documents its cross-cache lookup; the [service-worker lifecycle guide](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers)
informed the update/ownership boundary. Worker tests and final gate are pending.

Parent's live invalid-token companion check returned HTTP 404 through the BFF
(browser console and independent curl). No private itinerary appeared. The
intermediate UI incorrectly treated this as connectivity failure; backend
intentionally uses generic 404 for invalid/mismatched/revoked capabilities.
The request-state worker was instructed to add 404 contract coverage and generic
cannot-open/fresh-link guidance without revealing trip existence. This is
denial-path runtime evidence, not valid-token authorization/acceptance proof.
The browser helper's network-idle wait timed out after 30 seconds during that
navigation; subsequent DOM/console inspection and curl supplied the stated
observations, not a successful helper-navigation receipt.

Request-state repair is released: loading, denied (401/403/404), service
unavailable, transport error, invalid envelope and genuinely empty graph have
separate states. The backend's `exists:false` envelope without nodes remains
valid; invalid/wrong-trip payloads do not become evidence of no bookings.
Worker focused suite: 19 passed, scoped lint/typecheck clean. Parent mutation
`6093` temporarily removed 404 denial handling: the targeted assertion failed
(one failed / 18 skipped, 7.47s). Restoring the mapping then passed all **19
tests in 8.00s** (`10359`). This is Tier 2/S3 sensitivity for that mapping,
not a claim that every added state had a pre-implementation red receipt.

Service-worker implementation released: **14 focused VM-harness tests** passed
(1.93s), targeted ESLint and typecheck passed. The initial source run had 10
failures after fixing a harness-path issue; distinguish that harness repair from
product regression evidence. The actual worker source is executed by the VM
harness, with string and Request-like cache keys normalized. Parent review also
required cache-control handling during warmup, field-qualified private headers,
optional warmup failure and fresh-response preservation on cache-write failure.

| Superseded behavior | Preserved capability / new boundary |
|---|---|
| Global `caches.match` for all origin requests | Public shell fallback only through `waypoint-companion-shell-v2`; API, non-GET, cross-origin, query-bearing and no-store requests are not intercepted. |
| Cache-first manifest and companion | Network-first exact public resources, successful cacheable responses only; no-store/private responses are not stored. |
| Delete every cache except current | No enumeration/deletion on activation. Existing v1 and unrelated caches remain untouched. Future retirement requires exact ownership/retention policy. |
| Install requires precache success | Warmup is optional; unavailable storage/network cannot block installation of the safer worker. |
| Cache-write failure can obscure successful network response | Return fresh response even if optional cache refresh fails. |

Registration call-site audit found one companion mount registration. The SLM
downloader remains separate and unregistered; no model-cache capability is
claimed or removed. Browser update through that registration reached activated
state with both v1 and v2 cache names present. The v2 cache contained only
`/manifest.json` at inspection; the fetched manifest had the corrected online/
demo description. Do not claim a fully cached/offline app from this observation.
No stored cache entries were purged; v1 preservation was observed directly.
After update, a normal browser manifest fetch returned the corrected description;
an explicit no-store invalid-capability API fetch returned **404**. The owned
cache still contained only `/manifest.json`, with v1 still present (`2834`).
The final invalid-link DOM showed generic access denial/fresh-link guidance;
saved and viewed `Docs/review/companion-invalid-link-mobile-2026-09-08.png`.
The navigation helper again timed out; these subsequent DOM/HTTP/screenshot
observations, not an invented network-idle success, support the narrow claim.

### Final coordinated frontend candidate

Parent gate `85080` runs the standard typecheck → lint → all tests → build
chain after both workers released ownership. Its result is pending until a
terminal receipt is recorded. Before-run SHA-256 fingerprints:

| File | SHA-256 |
|---|---|
| Companion page | `124217d9a9422f350ed351c082d6dd4281e1915cdda341be0310daf7d9c2addc` |
| Companion tests | `2457cb7d1e8a5b67d95db9c738e17cb8adacbe29f43d39ebce13921ee840fb1d` |
| Service worker | `2ba2185556a295aef774207219bdd2e8f77f0806c69018f2de5e5e39479545bb` |
| Service-worker tests | `e6404d21e04415183545dd4901636d15713627d8a6650be053f36fd1a70a12aa` |
| Manifest | `ae0c50f8489333d46d96e7b6882bb722752fd83f1392c16d19faa2812a9b039b` |
| Manifest tests | `ba9b4093496778fe015ef3bbc452104e0122fcede1388c1adef8104d8bde3b42` |
| Next config | `87553de1635d91e9e1e18101e211dacbd143fcf373b6145260ddacef9b7d59f2` |
| TypeScript config | `4ce9bf8693fe7b44af4666d6c35273cea4f76db35fdc178835064c68491277a1` |
| Next config tests | `7b15243d643cc1efb6a1943d3cd7bcae6a4db92482f2b61fc08f1ed7ed266ed8` |

Residuals: already displayed data is not continuously revoked while an unchanged
page stays open; no polling/push revocation channel was added. Explicit offline
download, bounded expiry/revocation and recovery need a separate product contract.
The service worker's global cache lookup is superseded by the bounded shell
implementation above; no pre-existing graph CacheStorage writer was found,
so historical private API replay is not claimed. Installed-device rollout,
legacy-cache retirement and PWA metadata discovery remain unproved/open.
Durable SOS, provider fulfillment and whole AT-05/AT-18 readiness are
not established by this lifecycle repair.

Main repaired the newly used `live_db` marker registration in the canonical
`tests/conftest.py::pytest_configure` location. Strict collection failed first
with unknown marker (exit 2), then collected all four probe tests (exit 0,
0.11s); Ruff passed. This is Tier 2/S2 collection evidence, not execution of
those probes or removal of the independent `fork()` warnings. No test was
disabled and no warning filter was added.

Astra/medium was called for the attachment transaction design after Luna's
current-source review. It identified the existing encrypted
`BookingConfirmation` insurance type as the canonical evidence record;
duplicating full policy evidence in trip extras is not the preferred long-term
path. Main verified the model/service and is recording transaction, replay,
ownership and migration requirements in the F-31 package. Architecture advice
is not implementation or insurer-verification evidence.

## Latest continuation: semantic reconciliation — 2026-09-05

### Full-gate terminal receipts and source drift — 2026-09-05

At `2026-09-05T14:54:16.722Z`, a read-only fingerprint covered 1,394 existing
source/test/config/fixture paths selected from Git's tracked and nonignored
untracked inventory (backend, frontend, scripts/tools, fixtures and CI plus root
dependency/build config). SHA-256:
`ad079a34cd80576216ab93810131617bf57d0a943e54f5c5ced7d4f412635e2a`.
Docs and runtime outputs are not part of that source fingerprint. It is drift
detection, not a checkout lock or an immutable snapshot; compare after the run
and do not promote a changed candidate from an older test result.

Full backend session `27931` ran
`USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -p no:cacheprovider`.
Terminal result: **exit 1; 1 failed, 3,817 passed, 44 skipped, 8 warnings in
886.97s**. Failure:
`tests/test_strategic_phases_6_to_9.py::test_strategic_phases_6_to_9_lifecycle_end_to_end`,
`DisruptionAlert.created_at` missing during alert construction. The eight
warnings concern Python 3.13 multi-threaded `fork()` in ledger durability tests.

Full frontend session `40980` ran
`npm run typecheck && npm run lint && npm test -- --run && npm run build`.
Terminal result: **exit 0; typecheck, lint, 174 test files / 1,313 tests and
build passed**. Vitest duration: **185.74s**. A Google Fonts TLS/download retry
recovered; request-dependent routes emitted dynamic-server-use diagnostics,
then the build completed. No hosted or browser-flow proof follows from this.

At `2026-09-05T15:10:35.822Z`, the same 1,394-path fingerprint was
`b36d06e6e8ba4a01f53c34513be3034c44bb563276035a67ddf5acc1a1602395`.
**The candidate changed during verification.** These terminal receipts describe
the runs, not an immutable current candidate. Live source now backfills missing
disruption timestamps and the strategic test now supplies `created_at`; neither
change was made by this delivery lane. Writer identity remains unknown.

Focused current-source retry, session `19827`:
`USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -k 'strategic_phases_6_to_9 or f31 or f38' -p no:cacheprovider`
returned **exit 0; 8 passed, 3,854 deselected in 31.43s**. This establishes the
selected local behavior, not the missing-timestamp fallback, production auth,
insurance eligibility, or a new full-suite pass. The insurance test still
expects invalid deposit input to become a fresh quote-time window.

Testing wrote its normal fixture/cache/runtime state; no application source was
edited by this delivery lane. No service was stopped to force a clean result.
Commit/push remain pending actual candidate gates and EV-11. Independent review
of the new disruption behavior is required before treating the fallback as a
long-term fix; malformed stored rows, false freshness and operator visibility
must be covered rather than merely returning a successful list.

### Completed semantic and research work

The prior turn made progress, not a verified wait: it repaired delivery gates
and found source drift. This continuation rechecked live files rather than
repeating the old blocker. The insurance quote now uses
`Depends(get_current_agency_id)`; the undefined-Header failure below is historical.
The insurance/disruption scoped Ruff check passes. No fresh full-app gate,
commit or push is claimed; new source/tests continued to appear outside this
delivery lane, whose writer identity is still unknown.

Safe work completed while preserving those edits:

- EV-02: reviewed all 15 colliding F/R labels between the master inventory and
  canonical register; documented same-issue/subtask/related/split/unmapped
  relationships in `FINDINGS_LIFECYCLE_2026-08-30.md`. Structural check verified
  15 unique references, existing source rows and existing canonical targets.
  This is not automatic alias-coverage enforcement or a lifecycle closure.
- EV-03: independent source review corrected A-06's obsolete no-CI-gate claim,
  added A-20's dated metadata/37-operation residual, split F-17 local test/lint
  repair from production race/coverage policy, and replaced the instruction
  to recreate four existing lease-router tests with the actual auth/runtime gaps.
- F-31: independent review and primary-source research showed invalid-date
  fallback, unconditional eligibility, time-zone inconsistency, bounds and auth
  evidence gaps. Main independently reproduced 13 versus 14 days for the same
  instant and an extreme-date OverflowError. The universal 14-day premise was
  corrected; plan-specific evidence is required. See the
  [research and implementation package](../research/INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md).

The canonical CLI remains 145 rows: 91 open, 53 closed, one deferred; the status
refinements do not silently close parent findings. Documentation updates in this
continuation are unstaged. No application source was edited by this delivery
lane; no generated types, shared runtime, database, external provider or Git
delivery state was changed by these reconciliation edits.

Continuation verification: 40 pure lifecycle tests passed in 1.07s; the canonical
plus historical-companion CLI returned zero warnings. Nine changed documents
passed Markdown lint. The focused 17-link check is **not fully green**: 15 OK,
one excluded, and the Allianz research article returned HTTP 403 to Lychee.
The research note retains the accessible-tool/content evidence and provenance
limitations; no blanket status-code acceptance or link exclusion was added.
Independent review approved the bounded identity/status corrections after
removing GM-01's stale commit-split veto, and accepted the F-31 research after
adding privacy and recorded-versus-verified attachment requirements.

## Latest retry: delivery gate paused — 2026-09-05 19:37 IST

This receipt supersedes the earlier full-suite results as a statement of the
current checkout, without erasing those historical passes. No commit or push
was created. HEAD remains `2f9a6384b42a90db415fbf012d94b60b5eaaa3bc`.

- 542 paths are staged. The complete staged `git diff --cached --check` passes.
- 146 changed Markdown files pass lint. Lychee reports 413 total links,
  412 OK, zero errors, one excluded.
- All 38 historical classification CSVs match their staged bytes (4,592,468
  bytes total). Both compressed script originals roundtrip to their recorded
  hashes; readable transcripts match after trailing-whitespace normalization.
- Focused backend retry: 76 passed, two setup errors. The app cannot import
  `spine_api/routers/insurance.py`: `generate_insurance_quotes` still references
  `Header` at line 72, but the import now contains `Depends` instead of `Header`.
  A fresh Ruff check confirms F821. This is not a passing application gate.
- The first Ruff retry also caught `now_iso` unused in the disruption router.
  A subsequent direct diff showed that line removed along with the fabricated
  default-disruption branch. The second Ruff check has only the insurance error.
- Changes appeared during verification in `frontend/src/lib/bff-trip-adapters.ts`,
  `spine_api/routers/disruption_radar.py`, and `spine_api/routers/feedback.py`.
  They are unstaged and were not made by this delivery agent or its two bounded
  reviewers. Their author/owning task is unknown; changing file contents are
  observed, but authorship is not inferred from Git status.
- Frontend retry completed: typecheck, lint, 30 focused tests across two files,
  and production build all passed, exit 0. Dynamic-server-use diagnostics were
  emitted for request-dependent API routes. This is local evidence, not a
  frozen-candidate or hosted receipt.
- Final drift check also found new unstaged edits in
  `frontend/src/components/workspace/panels/PacketPanel.tsx` and
  `src/intake/packet_models.py`, again outside this delivery agent's edits.
  The two retry-record documentation updates remain unstaged as well. No
  further broad staging was done after the change-in-flight condition appeared.

Delivery must resume from a coordinated, stable candidate: preserve and review
the new changes, resolve the insurance import/auth contract with its owner,
regenerate affected API types, rerun relevant/full gates, finish truthful
attestation, then use normal commit hooks. No gate was bypassed. The already
authorized Git operation is not the missing approval; the unresolved boundary
is ongoing shared-checkout mutation, plus master/main's automatic Fly deployment
before push (EV-11). Other writers need coordination, not a speculative owner
classification. The full project objective remains open.

## Current evidence-system correction — 2026-09-05

This is an execution summary, not an independent lifecycle register. Current
IDs/status are owned by `FINDINGS_REGISTER_2026-08-31.md`; this file retains
historical receipts and scoped implementation detail. Its older counts and
blanket authorization/concurrency wording are superseded by this correction
and the request trace's 2026-09-05 section.

- The user already authorized A1-1 `.gitignore` hygiene, `git add -A`, commit,
  full hooks/gates, and push. Placeholder custody labels do not establish
  active concurrency or another session's ownership. Actual artifact/privacy
  review and full delivery receipts remain required.
- Read-only workflow inspection found master/main push triggers Fly deployment
  independently of CI. Resolve destination/deployment direction before push
  (EV-11), not another generic Git permission gate.
- The findings parser now reads explicit status columns, includes formatted
  NEW IDs, excludes historical rows from current counts, preserves explicit
  verification dates, and rejects ambiguous canonical state. Forty focused
  checks pass following failing-first and independent-review cycles; the
  always-closed mutation fails.
  Evidence is Tier 2 / S2, with S3 for the lifecycle-state invariant.
- Seven previously skipped NEW rows now have explicit status, and EV-01–EV-11
  capture additional implicit findings. After EV-06/07 local reporter closure,
  the current gate reports 145 canonical rows: 91 open,
  53 closed, 1 deferred. Re-run the canonical CLI rather than copying counts
  from older snapshots. Counts still represent rows, not unique semantic work.
- `agent-start --skip-index` refreshed context but warned of busy retrieval
  and failed hook/guard installation attempts. Effective hook Downloads-path
  strings resolve through a verified canonical symlink with matching hash;
  stale doctrine content is not established. No shared tools were modified.
- The simulation chronicle's three trailing-space lines were changed to
  explicit paragraph breaks; the tax-test extra EOF blank line was removed.
  Historical content and executable assertions are preserved.
- Reporter independent verification: 28 tests pass; live `both` CLI at
  `2026-09-05T11:46:35Z` returned no errors, 21,937 SQL rows under explicit
  agency RLS/read-only transaction, and 1,936 unfiltered file objects including
  138 missing statuses. These are different populations. E12 evidence and
  `tools/README.md` document schema 2, scope, error handling and residual limits.
- Full backend and frontend gates were started after these repairs; until
  their terminal receipts are appended, earlier full-suite results below are
  historical and are not promoted by the focused tests.

Parser contract/evidence: `FINDINGS_LIFECYCLE_2026-08-30.md`. Request and
authorization history: `CHAT_REQUEST_EVIDENCE_TRACE_2026-09-04.md`.
Fresh full-worktree verification (2026-09-05):

| Gate | Command / result | Evidence limit |
|---|---|---|
| Backend | `USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -p no:cacheprovider` — **3,800 passed, 44 skipped, 8 warnings**, 1126.84s, exit 0 | No backend server detected; server-dependent cases skipped. Warnings concern Python 3.13 fork in a multithreaded process. |
| Frontend | `npm run typecheck && npm run lint && npm test -- --run && npm run build` — exit 0; **174 files / 1,311 tests pass** | Build logged dynamic-server-use diagnostics for dynamic auth/proxy routes; production build completed. No hosted or new browser proof. |
| Ruff | `.venv/bin/ruff check .` — exit 0, all checks pass | Whole-repository configured lint, not semantic correctness. |
| Mypy | `.venv/bin/mypy --config-file pyproject.toml` — exit 0, 10 source files | Scoped security/tenancy coverage, not all backend modules. |
| Imports / tenant access | `bash scripts/check_f401.sh`; `bash scripts/check_unscoped_trip_access.sh` — exit 0 | No F401 violations or detected unscoped router trip access; static boundaries only. |
| D6 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_d6_gate_snapshot.py` — `ok: true`, exit 0 | LLM unavailable/default-decision warnings; no new live-provider evaluation proof. |
| Generated types | Canonical `scripts/generate_types.py` — exit 0, working-copy SHA unchanged, 39,316 bytes | SHA `a457a71b4cee25e8f33c1bc4dff26e352059d3658fca905dddcab99870a81917`; exact staged/committed parity still belongs to delivery. |
| Markdown | First seven-document check: 93 issues; formatter repaired 85; remaining eight corrected without deleting historical content | Full changed-document/link gate still must be distinguished from this subset. |
| Git hygiene | Exact runtime draft-index ignore + index-only untracking; local file SHA unchanged | This one removal from tracking is staged. Other-checkout preservation/rebuild caveat in artifact review. No commit/push. |

Documentation gate follow-through: the full changed-Markdown set initially had
474 issues across 76 of 145 files. Mechanical formatting applied 409 repairs
across 72 files; remaining fence-language, inline-table-pipe, source-marker and
duplicate-heading issues were corrected with content preserved. Fresh full
check: **145 files, zero issues**, exit 0. No Markdown rule was weakened.
The newly added archive README is included in the subsequent final check.

Link validation also passed: **408 total, 407 OK, zero errors, one excluded**
using Lychee 0.24.2 with the CI exclusions and no credentials. A broken
`Docs/INDEX.md` pointer was corrected to the existing historical Wave 5 section
in `Docs/Wave_3_Verification/walkthrough.md`; no replacement narrative was invented.
The ARM macOS binary came from the
[official Lychee release](https://github.com/lycheeverse/lychee/releases/tag/lychee-v0.24.2),
with archive SHA-256 verified against release metadata:
`c9d3740ea2d891854d37116c9fba840f37b6e7c89d330e7db84ac333631c4977`.
It and the isolated Markdown cache are ignored tool state under `.runtime/`,
not source artifacts. Four distinct public documentation URLs were inspected
before the online check; no cookie jar, auth token or mail checking was enabled.

Both source-overwrite scripts are now exact-byte `.py.txt` artifacts under
`Docs/archive/historical_tools/`; original hashes match. After archival,
30 UI/route tests passed and the production build passed again (exit 0).
No product capability was removed; maintained TSX files already contained all
useful generated behavior.

Retry checkpoint: all 537 original delivery paths were staged before the final
whitespace check. That check exposed historical CSV CRLF and newly added source/
Markdown whitespace not covered by the earlier tracked-only check. The artifact
review now records the narrow CSV line-ending policy, exact-byte gzip originals
with readable script transcripts, and formatting-only source/Markdown repairs.
Managed refresh briefly regressed the existing configured-mypy-scope hook logic;
the exact reviewed behavior was restored. These are gate repairs, not additional
product-completion claims. Commit and push still require terminal receipts.

Screenshot/source/runtime artifact evidence and exact dispositions:
`A1_1_DELIVERY_ARTIFACT_REVIEW_2026-09-05.md` (40/40 PNGs viewed). Full hook,
commit/push and external readiness are not claimed. Original full project goal
remains open. All older full-suite/count/authorization tables below are historical.

**Purpose:** current status overlay for the full findings corpus, after the
2026-09-03/04 implementation and verification wave. The historical inventory
at `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` remains the
source of discovery and provenance; this document is the current execution
view and does not delete or rewrite that history.

**Checklist applied:** `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

**Persona lens:** **PER-0164 — Assumption Auditor** from
`/Users/pranay/Desktop/Understanding_Personas_29aug26/01 Expanded Personas/05 Feedback, Critique & Review/PER-0164 - Assumption Auditor.docx`.
Its governing question—“What must be true for this reasoning to hold, and
which conditions have actually been demonstrated?”—is applied below by
separating observed facts, inferences, normative decisions, environmental
dependencies, and unsupported release claims.

**Evidence boundary:** local tests, static checks, generated snapshots, and
local configuration are Tier 1/2 evidence. They do not establish hosted,
provider, browser/device, legal/privacy, customer, backup/restore, or
production-release proof.

## Current truth

| Surface | Current evidence | Status |
|---|---|---|
| Backend | Latest complete local runner: **3,733 passed, 44 skipped, 0 failed** in 382.49s with no :8000 server detected; prior server-present run: **3,760 passed, 10 skipped, 0 failed** in 304.49s | No-server run is more isolated but skips server-dependent integration; server-present run is broader but non-hermetic; 8 known Python 3.13 fork warnings |
| Frontend | Typecheck pass; 174 Vitest files / **1,311 tests pass**; production build pass | Local gate green |
| Frontend lint | **0 errors, 0 warnings** | Audit, IntakePanel, Workbench, and generated-type warning surfaces are clean |
| Route contract | 341 routes / 311 OpenAPI paths; parity tests pass | Local contract green |
| Findings lifecycle | Current checker: **194 rows: 118 open, 70 closed, 6 deferred, 0 warnings** (the earlier 183-row receipt is retained as historical evidence) | Register valid; open work remains |
| Worktree custody | Latest A1-1 ledger: final32 covers **533 live paths** (534 porcelain rows including the ledger); earlier final29/final31 counts are retained as historical receipts | Preserved, not semantically classified |
| Git | No staging, commit, push, reset, checkout, stash, cleanup, or deletion in this wave | Separate Git gate required |

## Assumption register (persona output)

| Assumption behind a closure claim | Classification | Evidence status | Falsification / next check |
|---|---|---|---|
| A green local test suite represents production readiness | Inferred, decision-critical | **False as a general premise**; it proves only the exercised local contract | Run hosted/provider/browser/device/restore gates before release |
| The asyncpg pool can safely reuse connections across ASGI test loops | Environmental/dependency | **Falsified** by the original Future-attached-to-different-loop traceback; fixed and covered by 3 tests plus the current local runner receipts | Recheck under dedicated multi-worker deployment |
| A signed proposal token identifies a real persisted tenant resource | Dependency-related | **Locally demonstrated** through agency-bound lookup and fail-closed projection; process-local cache/shared-host revocation are bounded | Prove shared revocation/issuance durability and hosted/browser/provider behavior |
| A fixture mirror measures extraction or pipeline quality | Factual-looking but unsupported | **Rejected** by evaluator provenance gate; lanes remain shadow | Add independent producers and runnable raw inputs |
| A reachable `/health` endpoint proves all required dependencies are ready | Environmental | **False**; `/health` is liveness-only and `/ready` checks DB/migration/Redis | Run dependency fault injection in compose/release environment |
| One worker is a durable topology decision, not just a local default | Normative/environmental | **Partially demonstrated** in manifests; worker ownership and crash recovery are unproven | Execute worker crash/reacquire/duplicate-run drill |
| Synthetic provider adapters can be described as live business capability | Normative | **Rejected**; they are explicitly sandbox/simulation surfaces | Wire real providers only after contract, secrets, webhook, and cost review |
| The dirty worktree can be safely committed as one coherent change | Ownership/environmental | **Not demonstrated**; current paths remain conservatively concurrent/unknown | Semantic owner classification and separate Git authorization |
| Deployment can call `/ready` without credentials | Contract/environmental | **Falsified before this wave**; middleware returned 401 although deployment manifests named `/ready` | Public-path fix is locally covered; run compose/Fly/Render and dependency fault-injection probes |
| A protected static `/metrics` endpoint is automatically a valid monitoring contract | Normative/operational | **Undecided**; current endpoint is static JSON, protected, and version-inconsistent | Ratify format, exposure, auth/network, labels, privacy, and alerting before wiring a public scrape |

## Implemented and locally verified (promotion is still bounded)

| IDs | Finding/task | Current decision | Evidence / remaining boundary |
|---|---|---|---|
| S-01, S-02, S-03, PT-01..04 | Proposal secret, legacy bypass, agency guess-loop, canonical HMAC payload | **ACCEPT — local complete** | 40 proposal tests + Ruff; explicit demo gate and shared-host revocation/issuance durability remain open |
| S-04 / GM-03 | Stripe webhook HMAC verification, timestamp tolerance, multi-signature support, and fail-closed configuration | **ACCEPT — local complete** | Provider-adapter signature suite passes; live Stripe endpoint, replay store, and webhook delivery proof remain external |
| S-05 / G-09 | Agency-scoped draft promotion with indistinguishable 404 denial and metadata-only denial audit | **ACCEPT — local complete** | Two-tenant denial/positive-control suite passes; hosted authorization and audit sink evidence remain external |
| S-06 | Per-call nonce delimiters for untrusted egress and packet facts | **ACCEPT — local complete** | Egress/hybrid malicious-content regressions pass; provider-specific threat corpus and live adapter evidence remain open |
| N-04 | YieldArbitragePanel route/protocol mismatch and fabricated reticket fallback | **ACCEPT — local complete** | Legacy and app-local panels use canonical `/api/v1/yield`/BFF routes; 21 focused and 174-file/1,311-test full frontend suite passes; live provider/reticket evidence remains open |
| N-05 / F-03 | Public proposal token could mint fabricated content without persisted tenant/resource binding | **ACCEPT+MODIFY — local complete** | Both public proposal routes bind to persisted agency-owned resources and fail closed; explicit demo gate is startup-rejected in staging/production; 65 proposal + 49 startup tests pass; shared revocation, hosted issuance, and browser/provider evidence remain open |
| F-01 | Price-lock optimistic version guard and replay idempotency | **ACCEPT+MODIFY — local complete** | Version-conflict and replay tests pass; durable multi-writer CAS/compensating-action proof remains open |
| S-07 | Public-checker payload/depth limits | **ACCEPT — local complete** | Focused limits suite; provider/abuse load proof remains open |
| S-08, S-10 | Memory/tenant middleware hardening slices | **PARTIAL** | Focused tenant tests pass; full multi-replica and route-order proof remains open |
| S-11, PT-05/06 | Revocation persistence, full SHA-256 digest | **PARTIAL** | Atomic locked JSON restart/merge/corrupt-store tests pass; shared DB/volume needed for replicas |
| S-11 / N-07 / LR-B07 | Crash-safe run ledger and event publication | **ACCEPT+MODIFY — local complete** | Atomic fsync/replace plus process-safe locks; dedicated durability/concurrency tests pass; durable-volume/PostgreSQL, backup/restore, and multi-replica convergence remain open |
| S-13, S-14 | Auth kill-switch and committed DATABASE_URL defaults | **ACCEPT — local complete** | Startup matrix and Alembic fail-closed tests; hosted secret-manager proof remains open |
| E-01, E-02, E-03, E-05 | Honest eval provenance, 30-scenario completeness, holdout policy, register roles | **ACCEPT+MODIFY — shadow where required** | 67 focused tests, D6 verifier green; decision corpus is 30/30, extraction/pipeline have no independent producers, holdout empty |
| E-04 | Journey smoke | **PARTIAL** | Included in backend suite; compose/deployed browser smoke absent |
| LR-B01..B06 | Environment parsing, Redis/SQL requirements, secret strength, Alembic ownership | **ACCEPT — local complete** | 56 focused startup/readiness tests; real deployment matrix remains external |
| LR-B08..B15 | Readiness, containers, compose, Fly/Render manifests, worker topology | **PARTIAL** | Static/semantic checks pass; Docker daemon, image inspect, release migration, rollback, and restore proof absent |
| LR-B08 / LR-B09 | Readiness auth boundary and deployment probe target | **ACCEPT+MODIFY — local contract fixed; runtime proof open** | `/ready` is public, dependency-aware, and now requires exactly one current Alembic revision matching the artifact head; 13 focused readiness/auth tests and the latest full backend gate pass. Bounded-timeout, dependency fault-injection, hosted, multi-replica, and metrics-contract evidence remain open. See [readiness dossier](LR_B08_B09_READINESS_AUTH_BOUNDARY_2026-09-04.md) |
| A1-1 / A-14 / A-21 | Worktree custody and current-path coverage | **ACCEPT — custody complete** | Current final29 validator covers 521 live paths; semantic owner classification and Git mutation are separate gates |
| Route/OpenAPI drift | Generated snapshots refreshed to 341/311 | **ACCEPT — local contract complete** | End-to-end route authorization/provider behavior still requires runtime proof |
| Asyncpg loop affinity | Pooled connections crossing short-lived TestClient loops | **ACCEPT — local complete** | Checkout guard + 3 regression tests; full backend suite green; monitor under real worker topology |
| N-06 / X-11 | Durable SQL JSONB race and stale-owner terminal CAS | **ACCEPT — local/live-DB complete** | Local focused regression 25 passed; live Postgres JSONB + 8-session race (1 winner/7 losers); live TTL stale CAS false/new CAS true; hosted/provider and unknown-outcome evidence remain open |
| S-12 | RLS catalog, policy, and cross-tenant write enforcement | **ACCEPT — local/live-DB complete** | Live rollback-only probe proves agency A cannot update/delete agency B rows and cannot insert a mismatched agency_id (`SQLSTATE 42501`); combined live/mock RLS 20 passed; 12 protected tables, 4 documented exemptions; hosted role provisioning and raw-SQL path coverage remain open |
| A-02 / R-03 | Retrieval implementation and documentation honesty | **ACCEPT+MODIFY — local truth corrected; semantic provider remains open** | Code/docs now identify MD5 hash-bucket vectors, substring BM25-style heuristic, label/entity boost (no edge traversal), and heuristic grounding; 14 focused RAG tests and Ruff pass; provider selection, benchmark, calibrated scores, claim-level entailment, and hosted privacy/cost evidence remain open |
| S-09 / C-01 | Disruption radar execute path | **ACCEPT+MODIFY — local fail-closed complete; provider work open** | `DETERMINISTIC_PREVIEW` capability guard now rejects execution with 403 before mutation/audit; strategic lifecycle regression and Ruff pass; real flight/booking provider, external reference, reconciliation, and hosted approval remain open |
| S-09 / C-01 | GDS/distribution sandbox and order routes | **ACCEPT+MODIFY — local preview truth complete; provider work open** | Search, booking preview, EDIFACT, NDC shopping/order, fare-penalty, and Cat35 routes emit reality metadata; synthetic PNR/e-ticket/charge/provider-confirmation fields are cleared; 11 focused tests pass; real provider submission and reconciliation remain open |
| S-09 / C-01 | FX sentinel and IROPS healer routes | **ACCEPT+MODIFY — local preview truth complete; provider/legal work open** | FX rates/exposure and IROPS recovery plans carry deterministic-preview metadata; missing-cost FX abstains; lock path is non-operative; VCC, legal compensation, rebooking, waiver, and supplier effects are cleared; 8 focused tests pass; provider/hosted/legal evidence remains open |
| S-09 / C-01 | Financial settlement and VCC routes | **ACCEPT+MODIFY — local arithmetic preview complete; financial/provider work open** | Currency conversion, FX quote, payment schedule, and commission routes return computed-preview envelopes; VCC route returns `NOT_ISSUED` with no credential-shaped fields; 9 focused tests pass; payment authorization, PCI, treasury, supplier, and durable-ledger evidence remain open |
| S-09 / C-01 | Duty-of-care cockpit route and panel | **ACCEPT+MODIFY — local preview truth complete; provider/operations work open** | Cockpit route returns preview metadata and marks beacon/STEP/dispatch/SOS states unverified/draft/not-sent; panel uses sample wording; 2 focused route/engine tests pass; threat feeds, trusted beacons, consular, dispatch, messaging, and operator evidence remain open |
| inventory-2026-09-02::F-03 / N-11 | Public proposal and Persona Council demo surfaces | **ACCEPT+MODIFY — local copy/state containment complete; persisted/provider work open** | Sample banner, non-persisted acceptance wording, preview pricing, demo IDs, simulation-labeled selectors, and sample-token copy are covered by 13 focused tests; canonical persisted proposal and authenticated provider actions remain open |
| S-09 / N-11 | Supplier directory and MRZ/document workbench surfaces | **ACCEPT+MODIFY — local sample/authenticity boundary complete; provider/document evidence open** | Supplier records and rate intake are explicitly sample/unavailable; MRZ checksum is format-only and failure clears stale output; 4 focused tests pass; canonical supplier contracts, OCR/authenticity, PII, and browser evidence remain open |
| F-06 | Audit-chain predecessor race | **ACCEPT+MODIFY — local continuity and verifier complete; anchoring and operational recovery open** | Read/hash/append now shares one cross-process lock with fsync; 32-writer regression, tamper/fork verifier, and full backend gate pass; external head anchoring, gap/replay handling, shared replicas, and restore remain open |
| R-11 / F-10 / NEW-07 | Agent lease liveness and fencing | **ACCEPT+MODIFY — local state-machine and route contract complete; integration open** | Manager and in-memory router are synchronized/explicit for expiry, release, fencing, validation, contention, and inspection; 11 focused tests and Ruff pass; SQL fencing, supervisor heartbeat wiring, pipeline-version stamps, agency scope, restart, multi-host evidence, auth integration, and fenced trip-write proof remain open |
| F-08 | Locking semantics and distributed mutual exclusion | **OPEN — audit complete; implementation deferred pending ownership** | 62 focused locking/startup tests pass, but they exercise only the process-local fallback; no production mutation invokes the lock, non-PostgreSQL strict boot is accepted, and transaction lifetime is untested. See [F-08 dossier](F08_LOCKING_SEMANTICS_AUDIT_2026-09-04.md); Add explicit strict-mode dialect policy, PostgreSQL two-session contention/transaction tests, canonical mutation wiring, fenced writes, and multi-worker evidence |
| F-07 | Poisoned queue inspection | **ACCEPT+MODIFY — durable service projection complete; API/replay open** | Canonical `RequeueJobStore.list_poisoned()` is deterministic, payload-free, bounded, and filterable; 34 PostgreSQL-backed queue tests pass and the isolated full runner is green (3,733/44). Agency scope, authenticated route, replay execution, purge/retention, audit, and hosted evidence remain open. See [F-07 dossier](F07_POISONED_QUEUE_INSPECTION_2026-09-04.md) |
| X-01..X-03, X-07, X-08 | Extraction prompt-injection, date/party, destination, homonym, and malformed-structured-input defects | **ACCEPT — local complete** | 7 safety tests + 318 extraction/trap regressions + 52 validation/NB01 regressions; adversarial records abstain or warn as designed |
| X-04..X-06, X-13 | Decision escalation, budget OR-group, blank blockers, and scenario-fixture correctness | **ACCEPT — local complete** | 146 focused tests; D6 live decision corpus 30/30 with 1.0 state/blocker/contradiction accuracy |
| X-09 | Production-vs-CI hybrid configuration parity | **ACCEPT+MODIFY — local truth/parity complete; release ratification open** | Serving/CI declare hybrid mode explicitly; D6 preserves caller mode, records effective configuration and deterministic authority axes; 59 focused tests and 30/30 provider-free parity run pass; model-quality/provider/owner gates remain open |
| X-12 / F-05 | Container build-context, digest, privilege, and stateful-service hardening | **PARTIAL — source contract complete; runtime build/scan/deploy open** | Digest pins, non-root layers, nested `.dockerignore`, internal Postgres/Redis ports, and 6 static tests pass; Docker daemon, image scanner, runtime, and hosted deployment evidence unavailable on this host |
| A-06 | Generated frontend API type drift | **ACCEPT+MODIFY — CI gate wired; clean-commit verification pending** | Backend-lint regenerates `frontend/src/types/generated/spine-api.ts` and fails on a diff; the intentionally dirty checkout makes HEAD comparison non-green, while generation is deterministic/idempotent |
| A-20 | Alembic model/migration drift | **ACCEPT+MODIFY — metadata ownership repaired; reconciliation remains open** | Registry now includes `AuditLog`/`TripRoutingState`, routing FK actions and PostgreSQL JSONB parity are explicit, and only raw `agent_requeue_jobs` is excluded; 34 focused tests pass. Read-only `alembic check` still reports 37 visible operations, so no migration or blocking CI gate was added. See [reconciliation dossier](A20_ALEMBIC_MODEL_MIGRATION_DRIFT_RECONCILIATION_2026-09-04.md) |
| D-01..D-03 | Trip duration, flight inclusiveness, and country/city destination contracts | **EXPLORE/DECIDE — current gaps executable; implementation intentionally gated** | 280 probes document current untyped/missing behavior and ratification-ready value-object/migration package; no new canonical fields were guessed |
| N-02 / N-03 | Independent extraction and pipeline evaluation producers | **ACCEPT+MODIFY — shadow probe complete; producer implementation open** | Three executable probes confirm missing raw-artifact provenance, empty live collectors, and disjoint expected/actual stage facts; no fixture mirror is promoted |
| X-14 / F-05 | Retention-enforcer wire-or-archive disposition | **ACCEPT+MODIFY — claims corrected; canonical wire open** | Prototype is explicitly `shadow` and non-erasing; 10 focused tests pass; durable cross-store inventory, legal holds, lifecycle anchors, provider purge, reconciliation, and recovery remain open |
| A-17 | WelcomeCard browser render | **PARTIAL — local visual evidence added; accessibility/hosted gates open** | Prior browser artifact was inspected; fresh unauthenticated recheck returns `/health` 200, `/metrics` 401, and frontend 200, so metrics reachability remains an LR-B09 auth/observability task; computed accessibility tree, keyboard/focus, screen-reader, contrast, and hosted/device evidence remain open |
| D-08 | Sibling panel sample treatment | **ACCEPT+MODIFY — local truth containment complete; browser/provider evidence open** | MemoryArchitectPanel, MemorySettingsTab, and CrisisEvacuationPanel expose sample/preview/not-dispatched states; focused D-08 coverage is included in 21 passing tests |
| D-09 | Repair deep-link and focus/auto-open | **ACCEPT+MODIFY — local route and authenticated browser contract complete; persistence/hosted evidence open** | Canonical `?repair=<field>` resolver handles machine names, async hydration, route updates, scroll anchoring, focus, and query cleanup; 41/41 lifecycle tests plus a 1280×900 authenticated BFF browser run prove one focused budget editor and URL cleanup; save/reload persistence, mobile/accessibility, hosted auth, and provider evidence remain open |
| D-10 | VCC BFF-relative routing | **ACCEPT — closed in-tree** | FinancialSettlementPanel uses the BFF-relative route and route-map proxy; historical PT-07/GF-05 defect retained as lineage |
| D-09 follow-up | Test-agency list auto-seed could 500 on a fixed trip ID hidden by RLS but globally present | **ACCEPT — local remediation complete** | `spine_api/server.py` skips only `trips.id` duplicate-key conflicts per fixture row and preserves unrelated integrity failures; 3 focused / 49 booking-data tests plus Ruff pass. Historical browser 500 remains recorded; post-fix browser response and hosted race evidence are open |
| Sandbox card shape | Variable-width decimal CVC/`last4` output | **ACCEPT — local complete** | CVC and `last4` now use bounded zero-padded decimal contracts; sandbox adapter suite 14/14; live Stripe contract is not claimed. See `Docs/review/SANDBOX_CARD_FIXED_WIDTH_CONTRACT_2026-09-04.md` |
| Cross-tenant ghost probe fixture | Synthetic agencies missing before FK insert | **ACCEPT — test corrected** | Probe now honors production FK and isolation contract; no schema weakening |
| Phase 1.3 landing/offline honesty | Fabricated operator metrics and offline success fallbacks | **ACCEPT — local complete** | Landing now uses capability claims; intake/offsites show explicit unavailable states; browser/copy review remains |

## Remaining implementation tasks (must be researched/implemented and then

verified at the matching evidence tier)

### Security, data, and provider boundaries

- **S-09:** rename or environment-gate Amadeus/Sabre/telephony/aviation,
  GDS/distribution, FX, IROPS, and duty-of-care adapters that are simulations;
  wire only after real OAuth/webhook contracts, trusted source provenance,
  idempotent order semantics, external references, reconciliation, and
  cost/failure semantics are documented.
- **S-11 / N-07 / LR-B07:** promote revocations and the run ledger to a shared
  PostgreSQL/ratified durable volume; prove restart, concurrent writers,
  multi-replica visibility, and recovery.
- **inventory-2026-09-02::F-03 / N-05:** the normal public proposal path now requires persisted,
  agency-bound trip/resource projection; the three demo tokens are gated by
  `PUBLIC_PROPOSAL_DEMO_MODE`, and startup rejects that mode in
  staging/production. Remaining work is shared revocation/issuance durability
  and correction of any remaining “live/issued/accepted” copy.
- **inventory-2026-09-02::F-03 / N-11:** remove remaining simulator identity/payload residue and
  preserve explicit simulated-data labels in all user-facing paths.
- **S-09 / C-01:** complete the remaining preview containment for VCC,
  financial conversion/quote, ghost-concierge, and any residual IROPS/duty-of-
  care client fallback; retain provider/legal/operator gates for real effects.
- **inventory-2026-09-02::F-05 / X-12:** finish image hardening with a version-pinned lock build,
  `.dockerignore` secret/data exclusions, non-root inspection, vulnerability
  scan, and measured startup/healthcheck evidence.
- **inventory-2026-09-02::F-04:** retain the historical split-commit proposal
  as decision history. The user's explicit all-path A1-1 delivery instruction
  controls the current delivery; do not turn the older proposal into another
  authorization veto or equate Git preservation with release readiness.
- **canonical::R-11 / canonical::F-10 / canonical::NEW-07:** extend the four
  existing isolated lease-router tests to actual server auth/agency boundaries,
  trace each route to a supervisor/worker fenced write, then choose
  one canonical SQL-versus-memory lease source and document migration/rollback.
- **LR-B08 / LR-B09:** keep `/ready` as the narrow unauthenticated,
  dependency-aware deployment probe (the pre-fix 401 is recorded in the linked
  dossier); the exact artifact-head comparison is now locally implemented;
  still prove bounded DB/Redis timeouts, dependency
  fault injection, restart/multi-replica behavior, and compose/Fly/Render
  receipts. Separately ratify the `/metrics` format, version source,
  low-cardinality labels, scrape authentication/private-network mechanism,
  privacy exclusions, and alert delivery before exposing it.

### Eval, decision, and extraction correctness

- **N-01 / X-04:** high-priority conflict escalation is fixed and the live
  decision corpus is 30/30; retain the pre-fix failures as regression lineage
  and continue independent-producer work before promotion.
- **N-02:** author runnable raw document inputs for the 50 extraction fixtures
  or explicitly replace that fixture contract; then add an independent
  document-vision collector.
- **N-03:** add deterministic independent producers for the seven pipeline
  fixtures and promote only with actual stage evidence.
- **E-06/E-07/E-08/E-10/E-11:** add trajectory/production shadow evaluation,
  calibrated judging, a red-team regression corpus, warning-capable gate
  format, and adversarial Hinglish/voice/emoji/mixed-language lanes.
- **X-10:** the audit confirms `checker_model` is declared, persisted, exposed
  by the settings API, and editable in the UI, but has no runtime consumer;
  the deterministic checker accepts no model/provider input. **Disposition:
  DEFER WIRE; RETAIN COMPATIBILITY; CORRECT CLAIMS BEFORE ACTIVATION.** The
  reserved round-trip contract is covered by 53 focused settings/gate tests.
  Remaining work is an owner-ratified router/provider registry, advisory
  proposal boundary, human-review/fallback/consent/spend controls, telemetry,
  golden/holdout/adversarial evaluation, and rollback evidence. See
  `Docs/review/X10_CHECKER_MODEL_WIRE_OR_REMOVE_2026-09-04.md`.
- **N-06 / X-11:** live SQL JSONB race and stale-owner fencing are now verified;
  see `Docs/review/IDEMPOTENCY_FENCING_N06_X11_2026-09-04.md`. Hosted/provider
  release evidence remains separate.
- **E-12 / E-1:** status-alias audit confirms `normalize_trip_status()` has no
  production callers and the persisted `Trip.status` axis is still freeform.
  The read-only distribution-report slice is now implemented and tested; the
  file-store receipt is 1,936 files with four explicit tokens, 138 missing-key
  records, and no malformed or explicit-null records in the current checkout.
  Telemetry-only
  normalizer reachability, alias expansion, strict enum/DB checks, and verified
  frontend active/archived semantics remain product-contract work. SQL reporting
  is no longer an unresolved zero-row observation: the repaired RLS/read-only
  reporter returned 21,937 rows for the explicitly selected test agency at
  2026-09-05T11:46:35Z. The old zero-row run remains historical; its cause was
  not independently reconstructed and is not established as an environment
  limitation. File and SQL scans cover different populations. See
  `Docs/exploration/E12_STATUS_ALIAS_EXPANSION_PLAN_2026-09-02.md`.

### Product contracts and frontend hardening

- **canonical::F-17 split:** recorded TimelinePanel test/lint repairs pass
  locally; production stale-response/race safety is not established. Remaining
  asynchronous React `act(...)` warnings, expected error-boundary console
  output, the non-boolean `fill` warning, and absent Vitest coverage thresholds
  remain **F-17/A-16** quality-policy work (`F-17b` was only a subscope label,
  not an independently registered finding). Do not close F-17 wholesale on the
  basis of test count alone.

- **D-01:** decide and implement the `trip_duration` contract across schema,
  extractor, API, and frontend.
- **D-02:** model `flights_inclusiveness` as a tri-state/ambiguous value with
  explicit user-facing resolution.
- **D-03:** define country-vs-city multi-destination semantics and committed
  versus semi-open sets.
- **D-04 / N-09:** the salutation/colon/label interplay probe is locally
  complete (274 focused extraction tests; GF-01/GF-03 reconciled closed).
  Keep country-vs-city semantics and repeated-currency budget ranges as
  separate contract work.
- **D-08/D-09:** local implementation is complete and covered by the focused
  contract suite. The test-agency seed collision observed during D-09 browser
  capture is remediated locally with per-row duplicate-key handling; repeat the
  authenticated browser list/seed check and verify save/reload persistence,
  mobile/accessibility, hosted, and provider evidence separately. **D-10 is already closed**: the VCC panel uses the canonical
  BFF-relative route and the route-map proxy; retain PT-07/GF-05 as historical
  lineage, not an open implementation task.
- **N-08:** harden Vitest timing under machine contention with bounded retries
  and evidence, not unbounded timeouts.
- **A-16/A-17:** establish coverage thresholds, browser E2E, keyboard/focus
  modal semantics, and mutation-sensitive tests.
- **Frontend lint backlog:** no warnings remain after behavior-sensitive fixes
  in audit, Workbench, IntakePanel, and the generated-type generator. Continue
  to avoid blanket-disabling `exhaustive-deps`.
- **Phase 3.1–3.3:** complete the simulated-label sweep, enforce generated-type
  drift, and prove frontend env/SSE/BFF contracts in a browser. The landing
  metrics and offline success fallbacks were removed in this wave; visual copy
  review is still required.

## Explore/research tasks (document before code)

- **A-02 / R-03:** compare semantic retrieval providers, lexical fallback,
  cost/latency, privacy, and benchmark methodology; rewrite the RAG document
  to match actual hash-vector/substring behavior until a provider is chosen.
- **C-02:** produce wire-or-archive ADRs for the hybrid engine, suitability
  scorer, ghost concierge, retention enforcer, yield modules, and every
  zero-caller subsystem.
- **C-03:** design a real runtime router only after independent eval ground
  truth exists; define ownership, fallback, budget, and telemetry contracts.
- **C-04:** execute the SLM/on-device benchmark protocol and analyze
  disagreement-rate, latency, privacy, and battery trade-offs.
- **C-05/C-06/R-05:** document the 19-agent runtime, lease ownership, and
  human-gated LLM wiring candidates as first-class architecture.
- **S-12:** retain FORCE-RLS positive probes in CI and add production-like
  migration/role coverage.
- **Provider research:** Amadeus/Sabre/NDC, Stripe Issuing, telephony/IVR,
  aviation/visa/MRZ, cancellation/empty-leg semantics, and data-quality SLAs.
- **Operational research:** IROPS/duty-of-care, group Pareto fairness,
  financial settlement/VCC, retention/privacy, backup topology, cost model,
  and Redis/Postgres failure modes.

## Decisions, records, and external gates

- **C-01/C-02:** ratify whether Frontier/Persona Council and each orphaned
  module is a labeled simulator to wire or an archived experiment.
- **inventory-2026-09-02::R-09/R-10:** decide signup verification posture and platform-led versus
  white-label business model before rewriting memory/business docs.
- **inventory-2026-09-02::R-01/R-02/R-04/R-06/R-07/R-08:** annotate simulator caveats, reconcile
  memory/RAG/seasonal docs, consolidate ADR/register numbering without
  deleting history, adopt personas into `Docs/personas/`, and refresh INDEX/
  idea-pad statuses through canonical tools.
- **D-07:** perform the manual banner visual check and preserve a screenshot
  with route/viewport evidence.
- **Operational docs:** create/maintain `LAUNCH_STATUS.md`, one known-issues
  ledger, and a detect→diagnose→contain→rollback→escalate runbook.
- **Legal/privacy:** obtain human review for traveler PII, retention, DPA/TOS,
  consent, simulated-data disclosures, and provider data processing.
- **Release/operator:** choose Fly or Render, configure real secrets/providers,
  webhook endpoints, backups, alerts, hosted worker assets, browser/device
  smoke, migration release, rollback, and restore drills.
- **Git:** classify the dirty tree semantically, refresh motto attestation,
  run full hooks/gates, then stage/commit/push only under a separate explicit
  authorization for that exact snapshot.

## Alignment verdict

The completed slices are first-principles aligned where they enforce a real
trust, lifecycle, or failure boundary (env-only secrets, canonical token
binding, truthful eval provenance, dependency-aware readiness, loop-safe pool
ownership, schema-honoring tests, and persisted proposal/resource binding).
They are long-term aligned where they
retain one canonical source and make unsupported capabilities fail closed.
They are intentionally **not launch-complete**: simulated providers, the
explicitly gated demo proposal seam, absent independent eval producers/holdouts, dirty
ownership, missing hosted/operator/legal evidence, and unresolved simulator
surfaces are known constraints, not hidden behind green local aggregates. The proposal demo
seam and local revocation cache are explicitly bounded rather than presented as
hosted production controls.

## Retry refresh — 2026-09-04

- Live ledger was re-scaffolded and revalidated in the final29 refresh after
  this documentation/test wave; path counts are recorded only after all
  current artifacts settle. Zero tracked deletions and no staging, commit,
  push, reset, checkout, stash, or cleanup are permitted in this wave.
- Focused security/price-lock retry:
  `PYTHONPATH=src .venv/bin/pytest -q tests/test_sandbox_provider_adapters.py
  tests/test_p1_findings_hardening.py` → **19 passed**.
- Focused tenant authorization retry:
  `PYTHONPATH=src .venv/bin/pytest -q tests/test_draft_promote_cross_tenant.py`
  → **2 passed**, including the metadata-only denial-audit assertion.
- Focused proposal resource-binding retry:
  `PROPOSAL_SIGNING_KEY=… .venv/bin/pytest -q tests/test_public_proposals.py
  tests/test_p1_findings_hardening.py tests/test_trust_scorecard_honesty.py
  tests/test_trust_scorecard_router.py tests/test_public_proposal_http.py` →
  **65 passed**.
- Startup demo-mode safety retry:
  `.venv/bin/pytest -q tests/test_startup_assertions.py
  tests/test_production_boot.py` → **49 passed**.
- Focused run-ledger durability retry: `pytest -q
  tests/test_run_ledger_durability.py tests/test_run_state_unit.py
  tests/test_journey_smoke.py` → **51 passed** across the durability/lifecycle
  slice.
- Focused yield contract retry: **21 passed** across panel and route-map
  contract tests; invented routes remain explicitly denied.
- UI lifecycle warning slice: stable modal/drawer escape callbacks and the
  quick-preset apply dependency; **10 focused tests passed**, reducing the
  frontend lint backlog from 16 to 13 warnings without suppressing the rule.
- Overview stale-count warning slice: `useOverviewSummary` now depends on the
  SSOT-derived `inboxCount` rather than raw `inbox.total`; the hook regression
  proves grouped enquiry counts refresh when unified state changes. **8 focused
  tests passed**, and the repository lint backlog is now **12 warnings**.
- RLS write-enforcement retry: rollback-only live PostgreSQL probe added for
  cross-tenant UPDATE/DELETE/WITH-CHECK rejection; **1 focused probe passed,
  20 combined live/mock RLS tests passed**, and `scripts/check_rls_coverage.py`
  reported 12 protected / 4 exempted tables. This is local/live-DB evidence,
  not hosted or production-role proof.
- Retrieval-honesty retry: canonical RAG modules and model contract now state
  the actual local hash-vector, substring-lexical, label-boost, and heuristic
  grounding semantics; **14 focused RAG tests passed** with Ruff and diff-check
  green. A real embedding provider, benchmark, and claim-level truth contract
  remain deliberately open.
- Workbench lint retry: explicit stable Zustand action dependencies and
  `draft_name` autosave dependency landed with **35 focused tests passing**;
  frontend typecheck now passes after repairing the `UnifiedState` test
  fixture. Repository lint is now **0 errors / 0 warnings** after the audit,
  IntakePanel, and generated-type surfaces were corrected.
- Simulator/provider truth audit: read-only review identified S0/S1 residuals
  in hardcoded bookings/suppliers/legacy proposal UI and backend disruption,
  crisis, GDS, VCC, IROPS, FX, and ghost-concierge routes. Crisis, GDS,
  disruption, FX, IROPS, and duty-of-care now have local preview/abstention
  boundaries; bookings, suppliers, proposal/persona copy, VCC, and
  ghost-concierge still require containment or provider evidence before launch.
- Crisis preview truth boundary: `crisis_ops.py` now returns explicit
  `PREVIEW_ONLY`/`DRAFT_NOT_TRANSMITTED` metadata, clears fabricated provider
  identities and operational writes, and passes **8 focused tests**.
- Bookings truth containment: bookings UI now presents sample/unverified rows,
  removes fabricated PNR/voucher/hold/live-GDS claims, and passes **2 focused
  tests** plus targeted typecheck/ESLint. Persisted tenant-bound bookings and
  provider reconciliation remain open.
- GDS/distribution truth containment: sandbox search, booking preview, EDIFACT,
  NDC shopping/order, fare-penalty, and Cat35 routes now emit canonical
  `PREVIEW_ONLY`/`COMPUTED_PREVIEW` reality metadata and clear synthetic PNR,
  e-ticket, charge, and provider-confirmation fields; **11 focused tests pass**.
  Provider connectivity, real order submission, and external-reference
  reconciliation remain open.
- FX/IROPS truth containment: deterministic FX rates/exposure and IROPS plans
  now carry preview metadata; missing-cost FX abstains and lock/rebooking/VCC/
  waiver/supplier effects are non-operative. **8 focused tests pass**; provider,
  hosted, legal, and reconciliation evidence remain open.
- IROPS/financial workbench containment: IROPS recovery renders only local
  candidate analysis, with compensation `Not assessed`, payment `Not issued`,
  and rerouting `Review only`; financial settlement performs arithmetic and
  timing previews without issuing cards, charging funds, or calling providers.
  **14 simulated-panel + 3 IROPS focused frontend tests pass**; browser,
  provider, PCI, and operator evidence remain open.
- Duty-of-care truth containment: cockpit and panel now label threat, beacon,
  STEP, dispatch, and SOS state as sample/unverified/draft/not-sent. **2 focused
  tests pass**; trusted feeds, consular, dispatch, messaging, and operator
  evidence remain open.
- Proposal/persona and suppliers/MRZ truth containment: public proposal and
  Persona Council copy is demo/preview-only; supplier records are sample and
  MRZ checksum is format-only with stale-output clearing. **13 + 4 focused
  frontend tests pass**; persisted/provider/OCR/authenticity evidence remains
  open.
- Frontend lint closure: generator header correction, AuditPage dependency
  stabilization, and IntakePanel dependency fixes reduce the repository to
  **0 errors / 0 warnings**; focused Audit tests **9/9** and Intake suites
  **38/38** pass.
- Canonical backend runner after proposal, ledger, startup, crisis, bookings,
  GDS/distribution, FX, IROPS, duty-of-care, financial-route, and fixture-seed
  collision hardening: latest isolated run **3,733 passed, 44 skipped, 0
  failed** in 382.49s with no `:8000` server detected; prior broader
  server-present run was **3,760 passed, 10 skipped, 0 failed** in 304.49s.
  The isolated run skips server-dependent integration paths, while the
  server-present run is broader but non-hermetic; eight known Python 3.13
  multiprocessing fork deprecation warnings remain.
- Audit-chain verifier retry: `PYTHONPATH=. .venv/bin/pytest -q
  tests/test_cryptographic_audit_ledger.py` → **3 passed**; the new
  read-only verifier detects modified details (hash mismatch) and changed
  predecessors (fork/predecessor mismatch). The full backend receipt above
  includes this regression.
- Findings checker invocation (canonical register plus declared historical
  companion): **183 rows — 108 open, 69 closed, 6 deferred; 0 warnings**.
- Full-repository Ruff remains green. `git diff --check` reports only the
  two preserved formatting residues recorded in the handoff (trailing
  Markdown spaces in the simulation chronicle and a blank EOF line in
  `tests/test_tax_compliance_sourcing.py`); these were not rewritten because
  the owning dirty slices remain semantically unclassified.

## Current retry receipt — 2026-09-04

- Latest isolated full backend gate (no server): `scripts/run_backend_tests.sh`
  → **3,733 passed, 44 skipped, 0 failed** in 382.49s; eight known Python 3.13 fork
  warnings. This run was more isolated but skipped server-dependent integration
  paths; the earlier broader server-present receipt remains in the chronology.
- Current retry regression tranche: currency-range, N-09/GF extraction,
  extraction safety/fixes, X-10 settings, feature-gate, and settings-router
  contracts → **331 passed** in 8.18s.
- Converged implementation tranche: container hardening, X-09 parity,
  D-01/D-02/D-03 probes, N-02/N-03 shadow producers, X-14 retention truth,
  sandbox-card formatting, D6 snapshot, and extraction regressions →
  **369 passed** in 8.72s.
- CI drift-gate retry: generated API type regeneration is deterministic and
  the blocking diff step is wired in `.github/workflows/ci.yml`; post-upgrade
  `alembic check` remains intentionally unwired after exposing real A-20
  schema deltas. See `Docs/review/CI_DRIFT_GATES_A06_A20_2026-09-04.md`.
- Fresh running-server probe before the readiness fix recorded `/ready` as
  401; focused post-fix ASGI tests now prove it reaches the readiness handler.
  The same probe recorded `GET http://127.0.0.1:8000/health` → 200,
  `GET http://127.0.0.1:8000/metrics` → 401 without credentials, and
  `GET http://127.0.0.1:3005` → 200. Define and verify the intended scrape
  authentication/internal-network contract before launch.
- Full frontend gate: `npm test -- --run` → **174 files / 1,311 tests passed**;
  `npm run lint` → **0 errors / 0 warnings**; `npm run typecheck` → pass;
  `npm run build` → pass. Build-time dynamic-route diagnostics for cookie,
  URL, and search-parameter access are expected for server routes and did not
  fail the build.
- Findings lifecycle: `python3 scripts/check_findings_register.py
  Docs/review/FINDINGS_REGISTER_2026-08-31.md
  Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` → **183 rows — 108
  open, 69 closed, 6 deferred; 0 warnings**.
- Custody: the latest validator covers the refreshed live-path set; all live
  paths are classified as preserved pending semantic ownership. See the
  final29 ledger entry and current custody section below (**521 live paths,
  522 porcelain rows including the ledger**).
- `git diff --check` retains only the documented owner-controlled residues in
  `MASTER_PRODUCT_DEMO_SIMULATION_CHRONICLE_2026-09-01.md` and
  `tests/test_tax_compliance_sourcing.py`; no unrelated formatting was
  rewritten.

## Task universe and first-principles alignment

The authoritative lifecycle checker covers **183 rows: 108 open, 69 closed,
and 6 deferred**. The complete ID-level source remains
`FINDINGS_REGISTER_2026-08-31.md` (current truth) plus the preserved historical
task companion `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`. The open/partial
families are:

- **Canonical architecture, security, contracts, and operations:** R-09,
  R-10, R-12, R-13, R-14, R-16; A-02 through A-12 (excluding closed rows),
  A-15 through A-17, A-20; F-01 through F-17, F-19, F-21 through F-26; and
  NEW-01 through NEW-07.
- **Agentic/evaluation/product truth:** G-01 through G-06, G-12 through G-17,
  GM-01, GM-02, GM-05, GM-06, GM-08, GM-09, PT-08, GF-04, and
  REC-1. G-16 is explicitly deferred, not silently dropped.
- **Research/design candidates retained in the companion:** EX-01 (JDG/IROPS
  trigger), EX-02 (epistemic UI), EX-03 (retirement primitive), EX-05
  (negative-space capability map), EX-07/EX-08/EX-09/EX-10 (provider, capacity,
  evidence-dossier, and quarantine follow-ons), EX-11/EX-12/EX-13
  (veto-window, intent subscriptions, itinerary branching), and EX-14
  (`TemporalObligation`). NG-01 through NG-04 remain explicit no-go/deferred
  items until their prerequisites exist.
- **Current truth-containment slices implemented in this wave:** crisis,
  bookings, GDS/distribution, FX, IROPS, duty-of-care, proposal/persona,
  suppliers, and MRZ/document surfaces. Their local status is preview,
  sample, abstention, or format-only; their provider-backed, persisted,
  hosted, legal, and operator tasks remain open under S-09/C-01/F-03/N-11.
- **N-09/GF-01/GF-03 probe:** salutation/honorific exclusion, colon-budget
  connective, parenthetical city-set composition, explicit-label precedence,
  and trailing-season handling are locally verified (274 focused tests). GF-01
  and GF-03 are closed at this deterministic tier. Repeated-currency and
  shared-suffix ranges are now covered by a separate four-test regression;
  country-vs-city semantics remain separate contract work.

Alignment rule: a task is **first-principles/long-term/doctrine aligned** only
when the canonical path has a falsifiable contract, honest reality metadata,
an owner, durable state semantics, matching evidence tier, and a retirement or
recovery path. Local green tests promote an implementation slice; they do not
promote an unproven external effect to “complete.”

## 2026-09-05 retry continuation — newly filed F-30…F-40 and current counts

The live findings checker now reports **194 rows — 118 open, 70 closed, 6
deferred; 0 warnings**. The increase from the earlier 183-row receipt is
caused by the concurrent register addendum, not by silently changing prior
statuses. The newly filed open findings are:

- **F-30:** corporate-policy routes accept raw agency headers without JWT
  subject binding.
- **canonical::F-31:** deposit-based timing is now present; invalid/unknown
  evidence, plan-specific rules, unconditional eligibility and date/auth
  regressions remain. The current research package supersedes the older
  no-deposit-reading description and universal 14-day assumption.
- **F-32:** `price_lock_expires_at` is written at trip top-level but read from
  `strategy`, creating a split-brain sentinel.
- **F-33:** `active` and `archived` trips fall out of frontend operator views.
- **F-34:** approval writes `delivered` while the read model recognizes only
  `completed`.
- **F-35:** booked-revenue metrics count a status with no confirmed writer.
- **F-36:** feedback survey URL, ingestion trigger, and supplier scorecard are
  fabricated/unwired demo behavior.
- **F-37:** assumptions are neither populated nor serialized, while the UI
  synthesizes authoritative-looking fallback facts.
- **F-38:** `GET /alerts` fabricates a critical disruption per trip by default.
- **F-39:** webhook deduplication exists only in an uncalled production path.
- **F-40:** the frontend calls `/api/stats`, but no backend route is present;
  verify the source-of-truth contract before wiring or correcting it.

F-30 has a partial local remediation: both corporate-policy trip routes now
derive agency scope from `get_current_agency_id` and no longer read
`X-Agency-ID`/`TEST_AGENCY_ID` in handler code. Two hermetic source-contract
assertions plus Ruff/compile checks pass. The running TestClient gate could not
complete because the repository app lifespan hung in this environment, so
anonymous HTTP denial, cross-tenant runtime proof, authenticated principal
binding, and hosted/RLS evidence remain open. See
`Docs/review/F30_CORPORATE_POLICY_AUTH_BOUNDARY_2026-09-05.md`.

These rows are now part of the authoritative register and must be sequenced
with the existing F-03, E-1/E-12, feedback, disruption, and frontend contract
work. Each is explicitly open; none is promoted by the existence of a test or
simulation-shaped module.

## Source and evidence pointers

- `Docs/review/A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-03.md` — custody,
  final local receipts, and 2026-09-04 execution addendum.
- `Docs/review/PROPOSAL_TOKEN_SECURITY_ADDENDUM_2026-09-03.md` — token and
  revocation contract/boundaries.
- `Docs/review/PROPOSAL_RESOURCE_BINDING_N05_F03_2026-09-04.md` — both public
  proposal issuance/read paths, fail-closed projection, and demo seam.
- `Docs/review/S11_N07_LRB07_LOCAL_DURABILITY_2026-09-04.md` — crash-safe
  run-ledger/event persistence and the durable-volume/PostgreSQL boundary.
- `Docs/review/YIELD_CONTRACT_N04_2026-09-04.md` and
  `Docs/review/N04_YIELD_ARBITRAGE_CONTRACT_REPAIR_2026-09-04.md` — canonical
  yield API/BFF wiring and negative invented-route evidence.
- `Docs/review/PRODUCT_CONTRACT_DECISIONS_D01_D03_2026-09-04.md` — observed
  duration, flight-inclusiveness, and destination-scope ambiguity with a
  ratification-ready canonical contract.
- `Docs/review/EVAL_GATES_E01_E05_2026-09-03.md` — evaluator provenance,
  shadow lanes, 30-scenario and holdout boundaries.
- `Docs/review/S12_RLS_WRITE_PROBE_2026-09-04.md` — live rollback-only RLS
  write-side evidence and remaining role/deployment boundary.
- `Docs/review/RAG_RETRIEVAL_HONESTY_A02_R03_2026-09-04.md` — corrected
  retrieval/grounding claims, focused tests, and provider-research boundary.
- `Docs/review/DEPLOYMENT_LAUNCH_ENVELOPE_2026-09-03.md` — readiness,
  migration, container, topology, and operator gates.
- `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` — complete
  discovery history, IDs, source links, and prior sequencing decisions.
- `Docs/review/FINDINGS_REGISTER_2026-08-31.md` — authoritative lifecycle
  register; A-02/G-04 now record the local retrieval-claim correction while
  leaving provider/benchmark implementation explicitly open.
- `Docs/LAUNCH_STATUS.md` and `Docs/review/KNOWN_ISSUES_LEDGER_2026-09-04.md`
  — canonical launch decision and operator-facing unresolved-risk ledger.
- `Docs/review/SIMULATOR_PROVIDER_TRUTH_AUDIT_2026-09-04.md` — line-level
  S0/S1 evidence for hardcoded public/agency state and backend operational
  statuses without provider evidence.
- `Docs/review/INDEPENDENT_EVAL_PRODUCERS_N02_N03_2026-09-04.md` — fixture
  contract audit explaining why raw documents and deterministic stage
  producers are required before promotion.
- `Docs/review/DISRUPTION_PREVIEW_FAIL_CLOSED_2026-09-04.md` — fail-closed
  disruption execution and provider-evidence boundary.
- `Docs/review/CRISIS_ROUTER_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — crisis,
  STEP, ground-dispatch, and safety-beacon preview-only contract.
- `Docs/review/BOOKINGS_TRUTH_CONTAINMENT_2026-09-04.md` — bookings sample
  containment, unavailable provider state, and local document-preview limits.
- `Docs/review/GDS_DISTRIBUTION_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — GDS,
  EDIFACT, NDC, fare-rule, and markup preview-only response contract;
  synthetic PNR/e-ticket/charge/confirmation fields are cleared locally.
- `Docs/review/FX_IROPS_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — deterministic
  FX and IROPS routes now abstain or return preview-only plans without lock,
  payment, legal, rebooking, waiver, or supplier effects.
- `Docs/review/DUTY_OF_CARE_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — duty-of-
  care cockpit and panel preview contract for threat, beacon, STEP, dispatch,
  and SOS fixtures.
- `Docs/review/PROPOSAL_PERSONA_TRUTH_BOUNDARY_2026-09-04.md` — public proposal
  and Persona Council sample-state and simulation-copy containment.
- `Docs/review/SUPPLIERS_MRZ_FRONTEND_TRUTH_CONTAINMENT_2026-09-04.md` —
  supplier records and MRZ/document format-only boundary.
- `Docs/review/AUDIT_CHAIN_CONCURRENCY_F06_2026-09-04.md` — local audit-chain
  concurrency root cause, fix, regression, and remaining anchoring boundary.

## A-17 Welcome surface semantics — 2026-09-04

**Decision:** `ACCEPT+MODIFY — local semantic correction complete; browser and
full accessibility evidence remain open.`

`WelcomeModal` was named as a modal but its live behavior was intentionally a
non-blocking fixed card: it did not trap focus, lock body scrolling, dismiss on
Escape, or prevent interaction with the underlying route. Adding
`role="dialog"`/`aria-modal="true"` without those modal invariants would have
misrepresented the interaction contract and could have made keyboard and
screen-reader navigation worse.

The implementation therefore keeps the non-blocking onboarding UX and makes
the semantics explicit:

- the implementation is now `WelcomeCard`; the historical `WelcomeModal`
  export remains as a compatibility alias for `AuthProvider`;
- both responsive render branches expose a labelled `role="region"` with
  `aria-labelledby` and `aria-describedby` tied to the visible heading and
  description;
- the card has a stable `data-testid` for contract tests;
- no false dialog semantics, focus trap, scroll lock, or unsupported Escape
  behavior was added;
- the existing dismiss and navigation buttons remain native keyboard-reachable
  controls, with an Enter-key dismissal regression test.

Focused evidence from `frontend/`:

```text
pnpm exec vitest run \
  'src/components/onboarding/__tests__/WelcomeModal.test.tsx'
  Test Files  1 passed (1)
  Tests       6 passed (6)

pnpm exec eslint \
  'src/components/onboarding/WelcomeModal.tsx' \
  'src/components/onboarding/__tests__/WelcomeModal.test.tsx'
  passed with no diagnostics

pnpm exec tsc -p tsconfig.json --noEmit
  passed
```

This is Tier 2 / S1 evidence for the local semantic and keyboard contract. It
does not prove visual contrast, responsive reflow, screen-reader output,
focus order in a real browser, or a complete authenticated onboarding journey.
Those remain part of the broader A-16/A-17 browser and accessibility gate.
