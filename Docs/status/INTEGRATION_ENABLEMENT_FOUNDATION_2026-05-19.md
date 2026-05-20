# Integration Enablement Foundation Status

Date: 2026-05-19
Repo: `/Users/pranay/Projects/travel_agency_agent`

## Summary

The integration enablement audit identified that Waypoint had provider-specific env/runtime configuration, but no agency-scoped integration foundation. The first safe implementation slice now exists locally as a read-only integration registry/status API.

This slice intentionally does not implement WhatsApp, Gmail, Google Calendar, SMS, Telegram, OAuth, credential writes, health-check provider calls, webhooks, or continuity/backup flows.

## Implemented Scope

- Added an agency-scoped `agency_integrations` model/table shape.
- Added a provider registry service with deterministic supported providers.
- Added safe read-model output for integration statuses.
- Added `GET /api/integrations`.
- Added `GET /api/integrations/{provider}`.
- Added frontend route-map entries and API-client types/functions for the read-only contract.
- Added a read-only Settings `Integrations` tab that consumes the status list.
- Updated route/OpenAPI snapshots for the two new backend paths.
- Added tests for auth, default disabled providers, detail lookup, unsupported provider 404, agency scoping, safe output shape, secret-field exclusion, malformed status handling, API-client wiring, route-map wiring, and the read-only Settings tab.

## Current Contract

Supported providers in this first catalog:

- `whatsapp`
- `gmail`
- `google_calendar`
- `google_drive`
- `sms`
- `telegram`

Status values:

- `disabled`
- `connected`
- `degraded`
- `auth_expired`
- `misconfigured`

Public response fields:

- `provider`
- `display_name`
- `enabled`
- `status`
- `capabilities`
- `category`
- `last_health_check_at`
- `last_success_at`
- `last_error_code`
- `last_error_message_safe`
- `updated_at`

Explicitly not returned:

- `credential_ref`
- `config_json`
- raw credentials
- raw provider responses
- customer/traveler/payment PII

## Validation Run

Commands run successfully:

```bash
uv run pytest tests/test_integrations_api.py -q
```

Result: `11 passed` before status-constraint hardening, then covered by the broader reruns below.

```bash
uv run pytest tests/test_integrations_api.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py -q
```

Result: `14 passed`.

```bash
uv run pytest tests/test_settings_router_contract.py tests/test_agency_settings.py tests/test_auth_integration.py -q
```

Result: `26 passed`.

```bash
uv run pytest tests -k "integrations or openapi or route" -q
```

Result: `88 passed, 2250 deselected`.

```bash
cd frontend && npm run typecheck
```

Result: passed.

```bash
cd frontend && npm test -- src/lib/__tests__/route-map.test.ts --run
```

Result: `1 passed`, `17 passed` assertions.

```bash
cd frontend && npm test -- src/app/'(agency)'/settings/components/IntegrationsTab.test.tsx src/lib/__tests__/api-client-contract-surface.test.ts src/lib/__tests__/route-map.test.ts --run
```

Result: `2 passed`, `20 passed` assertions.

```bash
cd frontend && npm run build
```

Result: passed. Next.js compiled, completed TypeScript, generated static pages, and finalized page optimization.

```bash
uv run alembic heads
```

Result: single head, `add_agency_integrations (head)`.

```bash
git diff --check -- <integration-slice-files>
```

Result: passed.

## Notes For Next Agent

- Do not add `/api/settings/integrations` as a second resource route unless explicitly deprecating/delegating one route family. The canonical resource API in this slice is `/api/integrations`.
- The UI now lives under Settings and consumes the canonical `/api/integrations` contract.
- Credential writes are intentionally not implemented. Add a strict credential storage contract before `rotate-credentials` or provider OAuth work.
- Integration audit events are intentionally not implemented because this slice is read-only. Add audit taxonomy before enable/disable/test/rotate actions.
- The test suite was refactored to avoid direct writes/deletes against the shared `waypoint_os` database.

## Remaining Work

1. Add a credential storage/rotation design and tests before any secret-bearing write endpoint.
2. Add write endpoints for enable/disable/test/rotate with SQL audit events and safe payloads.
3. Reconcile stale docs that mention `/settings/integrations` as if already implemented.
4. Choose the first real provider adapter only after the credential/audit boundary exists.
