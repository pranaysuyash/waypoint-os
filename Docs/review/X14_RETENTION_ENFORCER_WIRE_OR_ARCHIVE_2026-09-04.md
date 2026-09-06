# X-14 Retention Enforcer — Wire-or-Archive Decision

**Date:** 2026-09-04\
**Scope:** `src/security/retention_enforcer.py`, retention/erasure callers,
trip/document/artifact deletion paths, and the privacy/memory contracts\
**Owner:** security/privacy review lane\
**Status:** **RETAIN AS DESIGN PROTOTYPE; DEMOTE CLAIMS; DEFER CANONICAL WIRE**\
**Sensitivity:** S1/P1 privacy and compliance boundary

## Executive decision

`src/security/retention_enforcer.py` is a compliance-shaped, in-process
prototype. It has no non-test production caller and does not erase data from
any product store. It must not be described as GDPR/DPDP enforcement or as a
cryptographic erasure control.

The correct disposition is not to wire it into one deletion route. A partial
wire would create a certificate for only one resource while leaving trip
records, uploaded documents, blobs, memory, manifests, analytics, and other
derived artifacts untouched. That is worse than an explicit shadow boundary.

For this slice:

1. retain the module and its historical tests as a clearly labelled design
   probe; no historical code is deleted;
2. make its shadow status machine-readable and correct its module/class
   claims;
3. keep the current direct deletion and memory-erasure paths unchanged;
4. defer a production wire until a durable, tenant-scoped, cross-store
   erasure workflow and legal retention policy have been ratified; and
5. keep F-05/X-14 open for the production capability even though the
   wire-or-archive audit is now closed with this disposition.

## Source-of-truth evidence

### The enforcer is registry-only

The module now states its runtime boundary at
`src/security/retention_enforcer.py:1-17`: it is a shadow, in-process
registry; `execute_erasure` only marks a registry object and creates an
in-memory certificate-shaped record; no TripStore, document storage,
MemoryStore, audit persistence, or provider is touched.

The machine-readable boundary is
`src/security/retention_enforcer.py:58-79`:

- `RetentionEnforcer.RUNTIME_STATUS == "shadow"`;
- `RetentionEnforcer.EXTERNAL_ERASURE_ENABLED is False`;
- `_ASSET_REGISTRY` and `_CERTIFICATE_STORE` are class-level Python
  dictionaries, not durable tables or an external queue.

The behavior is visible in the implementation:

- `sweep_and_enforce_erasure` scans only `_ASSET_REGISTRY`
  (`retention_enforcer.py:104-128`);
- `execute_erasure` constructs a SHA-256 hash from in-process values,
  toggles `asset.is_erased`, and writes `_CERTIFICATE_STORE`
  (`retention_enforcer.py:130-160`); and
- there is no import or call to TripStore, SQLAlchemy, blob storage,
  MemoryStore, AuditStore, a scheduler, or a provider client.

The SHA-256 value is therefore an integrity-shaped identifier for the
prototype's certificate inputs. It is not proof of physical deletion,
cryptographic key destruction, provider erasure, or an auditable legal event.

### Exact caller inventory

An exact repository search on 2026-09-04 found only these references:

```text
src/security/retention_enforcer.py
tests/test_extraction_and_mandates_suite.py:18-20,134-183
```

There are no imports or calls from `src/`, `spine_api/`, `frontend/`, a
worker, a scheduler, or a request handler. The two existing tests exercise
the prototype directly and therefore prove only its local behavior.

The new boundary tests are in
`tests/test_x14_retention_enforcer_truth.py:1-64`. They verify the explicit
shadow status, registry-only sweep behavior, and no duplicate sweep for an
already-marked registry asset.

### Existing memory erasure is a separate path

The customer-memory endpoint is real local application behavior, but it does
not use this enforcer:

- `spine_api/routers/customer_memory.py:492-515` calls
  `MemoryStore.forget_entity_gdpr` and removes one legacy memory-store key;
- `src/memory/store.py:187-200` delegates to
  `GDPRMemoryEngine.erase_entity_memories` and persists the memory cache; and
- `src/memory/gdpr_engine.py:24-70` tombstones matching memory items in the
  provided list and returns a `GDPRForgetCertificate`.

This covers the memory store's own records only. It does not prove deletion
of trips, uploaded files, public-checker manifests, documents, analytics,
provider copies, backups, or all audit representations.

### Product deletion paths bypass the enforcer

The canonical trip stores delete directly:

- file store: `spine_api/persistence.py:578-594` unlinks the trip JSON;
- SQL store: `spine_api/persistence.py:1405-1413` deletes the SQL row;
- agency-scoped file facade: `spine_api/persistence.py:647-652`; and
- agency-scoped SQL facade: `spine_api/persistence.py:1545-1558`.

None registers a retention asset, creates an erasure request, waits for a
legal hold decision, or emits an erasure certificate.

Public-checker deletion likewise acts directly:

- `spine_api/routers/public_checker.py:112-127` removes public-checker
  artifacts and then deletes the trip for the configured public-checker
  agency;
- `spine_api/persistence.py:2646-2666` removes the manifest and local upload
  directory; and
- `spine_api/services/document_service.py:339-380` soft-deletes a booking
  document in SQL but explicitly leaves the storage object retained.

The `BookingDocument` model has `deleted_at`, `deleted_by`, and
`storage_delete_status` (`spine_api/models/tenant.py:235-286`), but there is
no retention-enforcer registration or purge worker for those rows/objects.

The Trip model has `created_at` and `updated_at` but no retention category,
legal-hold, erasure-request, purge state, or deletion certificate reference
(`spine_api/models/trips.py:15-96`).

## Findings against the current implementation

| Finding | Evidence | Consequence |
|---|---|---|
| No production caller | exact search inventory above | The advertised SLA never runs in the product |
| In-memory state | class-level dictionaries at `retention_enforcer.py:78-79` | restart, worker, and replica loss; no durable audit |
| Wrong deletion unit | asset marker only at `:157-159` | source data remains in backing stores |
| Wrong expiry anchor | `created_at_iso + sla_days` at `:117-120` | passport/payment/log schedules require trip-completion, settlement, or inquiry anchors, not generic creation time |
| No tenant authorization | `execute_erasure(asset_id, ...)` at `:131-140` has no agency/actor/permission | guessed IDs could be erased if this API were exposed |
| No legal hold | no model or branch for litigation/tax/chargeback holds | automatic sweep could violate a valid preservation obligation |
| No idempotency/reconciliation | new UUID certificate on each manual call at `:142-159` | retries can create multiple certificates with no request identity or per-store outcome |
| No failure state | sweep returns a list only; no pending/failed/retry record | partial deletion cannot be detected or resumed safely |
| Schedule claims are unratified | category comments at `:29-33` and `DEFAULT_SLA_DAYS` at `:71-76` | legal SLA assertions must be approved per jurisdiction, contract, and data class |
| Existing document deletion retains blob | `storage_delete_status="retained"` at `document_service.py:355-359` | a row-level delete is not data erasure |

## Why immediate wiring is rejected

The following alternatives were evaluated:

| Option | Decision | Reason |
|---|---|---|
| Call `RetentionEnforcer.execute_erasure` from `DELETE /trips/{id}` | **Reject** | would issue a certificate while deleting only one trip row/file and leaving related stores/objects; also changes a destructive route without a legal-hold contract |
| Call it from customer-memory `/memory/forget` | **Reject** | memory erasure is a separate resource scope; the enforcer has no memory-store adapter and would misstate coverage |
| Add registrations at current write points only | **Defer** | registrations without durable inventory, lifecycle anchors, and a complete deletion map create false completeness and data drift |
| Delete/archive the module now | **Defer** | historical tests and design intent are useful; removal would erase traceability and does not solve F-05 |
| Retain as explicit shadow prototype and design the canonical workflow first | **Accept** | honest current capability, preserves history, and creates a measurable path to real compliance behavior |

## Required canonical production design

Before any wire is attempted, the implementation plan must establish the
following contracts.

### 1. Durable asset inventory

Create a tenant-scoped SQL inventory keyed by `asset_id`, with:

- resource type and immutable resource reference;
- agency/tenant and data-subject reference;
- classification and jurisdiction;
- lifecycle anchor event (trip completion, settlement, inquiry close,
  upload deletion, or legal basis expiry);
- retention policy/version and legal basis;
- current state (`ACTIVE`, `DUE`, `HELD`, `PURGING`, `PARTIAL`, `ERASED`,
  `FAILED`); and
- provider/object references without storing unnecessary PII.

The policy must use explicit lifecycle anchors, not only `created_at`.

### 2. Erasure request state machine

Add an idempotent, actor-bound `ErasureRequest` with request ID, subject,
tenant, reason/legal basis, requested/approved/completed timestamps, and
operator or system actor. A request must be replayable and must not issue a
success certificate until every required adapter reports success or an
approved exception.

### 3. Per-store adapters and reconciliation

Adapters must cover, at minimum:

- SQL/file trip records;
- booking documents and binary storage;
- public-checker manifests/uploads;
- `MemoryStore` and legacy customer memory;
- extraction artifacts and derived PII;
- analytics/search indexes and caches;
- provider-side copies and webhook state; and
- backups/replicas subject to the documented retention policy.

Each adapter needs idempotency, tenant authorization, a dry-run preview,
bounded retry, failure state, and a reconciliation reader. The final receipt
must list per-resource outcomes and any legally retained minimal tombstone.

### 4. Legal holds and jurisdiction policy

The existing `jurisdiction_policy.py` declares broad behavior but returns
`None` for jurisdiction-level retention days. That is a signal to obtain
legal/product-owner decisions, not permission to apply the prototype's hard-
coded numbers. Define tax, chargeback, fraud, litigation, safety, and
contract holds before automated purge. Retention schedules require a legal
owner and versioned policy record.

### 5. Audit, security, and recovery

Persist minimal non-PII audit events with chain continuity, actor identity,
request id, policy version, adapter outcomes, and timestamps. Protect the
workflow with RLS/tenant checks, authorization, rate limits, and secrets
management. Prove crash recovery, retry behavior, multi-worker concurrency,
backup/restore, and a stop/rollback procedure before enabling a sweeper.

## Implementation sequence

1. **Decide:** obtain legal/owner ratification for data classes, lifecycle
   anchors, jurisdiction schedules, legal holds, and whether hard delete,
   cryptographic key destruction, or provider deletion is required.
2. **Map:** inventory every persisted/derived copy and identify the canonical
   resource owner and adapter.
3. **Model:** add durable asset/request/policy state and idempotency before
   adding a scheduler.
4. **Implement:** add one end-to-end tenant-scoped adapter slice with dry-run,
   failure/retry, reconciliation, and audit proof; keep it behind an explicit
   feature gate.
5. **Evaluate:** run independent deletion fixtures, legal-hold cases,
   cross-tenant denial, crash/retry, concurrent worker, and restore tests.
6. **Promote:** only after owner/legal sign-off and hosted evidence should the
   scheduler issue a compliance certificate. Until then keep the prototype
   shadow and all UI/docs explicit.

## Verification receipt

Commands run against the live shared worktree on 2026-09-04:

```text
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_x14_retention_enforcer_truth.py \
  tests/test_extraction_and_mandates_suite.py
10 passed in 1.31s

rg -n "RetentionEnforcer|RetainedDataAsset|ErasureCertificate|RetentionCategory|retention_enforcer" ...
```

The focused tests verify the module's explicit shadow contract and preserve
the original two prototype tests. The search is static call-site evidence;
it does not prove absence from a future runtime, so the inventory must be
repeated before any implementation promotion.

## Final disposition

**X-14 audit question:** closed with high confidence — the module is a
compliance-shaped shadow with zero production callers.\
**Production retention/erasure capability:** open; F-05 remains open.\
**Current action:** retain prototype, demote claims, build the durable
cross-store contract before wiring.\
**No-go:** do not add a scheduler or call this class from one deletion route.\
**Evidence tier:** local static/source + focused unit tests (Tier 1/2 only);
not legal, hosted, provider, backup, or customer proof.
