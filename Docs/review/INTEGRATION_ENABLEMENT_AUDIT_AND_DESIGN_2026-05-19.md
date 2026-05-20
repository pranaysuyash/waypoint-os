# Integration Enablement Audit and Design

Date: 2026-05-19
Repo: `/Users/pranay/Projects/travel_agency_agent`
Mode: audit/design only, no provider implementation

## Verdict

Waypoint currently has provider-specific runtime configuration in several places, but it does not yet have a canonical integration enablement layer.

The important distinction:

- Existing code can call some providers through global environment configuration.
- Existing settings can store agency operational preferences such as preferred channels.
- The repo does not yet model agency-owned integration instances, connection state, credential references, provider capabilities, health checks, or integration audit events as first-class product concepts.

So the next correct move is not WhatsApp, Gmail, Calendar, SMS, Telegram, backup automation, or continuity fallback. The next move is a small integration foundation that makes provider work safe, tenant-scoped, auditable, and visible.

## Scope

This audit checked current integration readiness across:

- backend routers and settings APIs
- tenant/settings models
- environment/provider configuration
- frontend settings and route-map surfaces
- docs and exploration notes
- tests for settings, auth, routes, provider config, and audit
- secret/encryption primitives
- audit trail primitives

Non-goals for this pass:

- no WhatsApp implementation
- no OAuth implementation
- no credential write flow
- no frontend settings UI implementation
- no data migration implementation

## Current Repo Evidence

### Instruction and context sources checked

- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/motto_v2.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`

### Backend settings surface exists, but is not integration enablement

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py:34-74` returns profile, operational, and autonomy settings from `GET /api/settings`.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py:77-159` updates operational settings, including contact fields and preferred channels.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py:162-259` handles autonomy settings.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py:262-283` exposes pipeline and approval settings collections.

Finding:

There is no `/api/settings/integrations` runtime route in this router, and no enable/disable/test/health/rotate flow for integrations.

### Agency settings include channel preferences, not provider instances

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py:160-191` defines `AgencySettings` with profile fields, operational fields, `preferred_channels`, frontier flags, autonomy settings, and LLM guard settings.
- `/Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py:218-230` persists settings in a SQLite `agency_settings` table with `agency_id` and `config_json`.
- `/Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py:250-315` loads and saves the dataclass to the settings store.

Finding:

`preferred_channels` is useful product intent, but it is not connection state. It does not answer whether WhatsApp, Gmail, Calendar, SMS, Telegram, or Drive are enabled, connected, degraded, credentialed, scoped, or healthy for a specific agency.

### Frontend settings UI has no integrations surface

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/settings/page.tsx:22-27` defines current settings tabs as `profile`, `operations`, `autonomy`, and `people`.
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/settings/page.tsx:88-103` saves operational fields and preferred channels.
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/hooks/useAgencySettings.ts:1-18` wraps existing settings APIs.
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/hooks/useAgencySettings.ts:27-88` provides profile/operational/autonomy update hooks.
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/settings/components/OperationalTab.tsx` renders preferred channel controls.

Finding:

The operator can express preferred channels, but cannot see provider connection status, enable/disable an integration, run a health check, rotate credentials, or see safe last-error state.

### Frontend route map has no integrations route

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:23-28` maps settings-related BFF paths.
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:123-129` maps payments and booking-data paths.

Finding:

No `integrations` or `settings/integrations` route-map entry exists. If an integration API is added, BFF/frontend alignment must be explicit.

### Provider calls exist, but are global/env-driven

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/src/llm/__init__.py:68-118` creates LLM clients from provider/model arguments and environment configuration.
- `/Users/pranay/Projects/travel_agency_agent/src/llm/__init__.py:121-159` resolves the default client from `LLM_PROVIDER` and fallback providers.
- `/Users/pranay/Projects/travel_agency_agent/src/llm/__init__.py:162-177` checks whether any LLM provider is available.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/extraction_service.py:77-120` builds extractors from `EXTRACTION_MODEL_CHAIN` or `EXTRACTION_PROVIDER`.
- `/Users/pranay/Projects/travel_agency_agent/src/agents/live_tools.py:236-345` defines HTTP-backed travel tools for flight status, price watch, and safety alerts.
- `/Users/pranay/Projects/travel_agency_agent/src/agents/live_tools.py:405-443` builds live tools from `TRAVEL_AGENT_*` environment variables.

Finding:

These are useful provider-adapter patterns, but they are not tenant-scoped integrations. They do not provide agency-owned connection records, credential refs, or operator-visible health state.

### Environment and secret configuration are scattered and global

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/.env.example:8-10` documents `JWT_SECRET`.
- `/Users/pranay/Projects/travel_agency_agent/.env.example:63-67` documents `LLM_PROVIDER`.
- `/Users/pranay/Projects/travel_agency_agent/.env.example:73-86` documents `GEMINI_API_KEY` and `OPENAI_API_KEY`.
- `/Users/pranay/Projects/travel_agency_agent/.env.example:117-121` also lists `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `HF_HUB_TOKEN`.
- `/Users/pranay/Projects/travel_agency_agent/.env.example:127-138` documents extraction provider/model settings.

Finding:

Global env is appropriate for platform-level services, but not enough for agency-specific provider enablement. The repo needs a first-class boundary between platform secrets, per-agency integration credentials, and safe config visible to operators.

### Encryption primitives exist, but need a credential-specific contract

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/src/security/encryption.py:13-31` creates a Fernet instance from `ENCRYPTION_KEY`, enforcing the key in production privacy mode.
- `/Users/pranay/Projects/travel_agency_agent/src/security/encryption.py:38-52` provides `encrypt_string` and `decrypt_string`.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/private_fields.py:15-21` encrypts a JSON blob into a structured encrypted marker.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/private_fields.py:24-32` decrypts the structured encrypted blob.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/private_fields.py:35-47` encrypts and decrypts single fields inside mappings.

Finding:

The repo has reusable encryption primitives. However, integration credentials should not casually reuse loose JSON config fields. Credential handling should have strict tests proving raw tokens never appear in normal tables, audit logs, list responses, error responses, or frontend payloads.

Risk:

`src/security/encryption.py` has a permissive decrypt fallback that returns the original token on decrypt failure. That behavior may be useful for older field compatibility, but a credential subsystem should prefer a stricter helper so a failed decrypt cannot silently behave like plaintext credential support.

### Audit trail primitives exist, but no integration events exist yet

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/audit.py:42-59` defines `AuditAction` values for create, update, delete, login, logout, run, override, assign, and export.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/audit.py:61-117` defines SQL `AuditLog` with `agency_id`, `user_id`, action, resource type, resource id, changes, IP, user agent, and timestamp.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/audit.py:51-108` exposes scoped audit-log querying.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/core/audit.py:47-105` provides request-aware SQL audit logging.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/core/audit.py:116-167` extracts agency/user context from auth.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/core/audit_bridge.py:39-73` dual-writes legacy audit and SQL audit events.

Finding:

Integration writes should use the existing SQL audit trail instead of inventing a second log. New actions or resource types are still needed for `integration_enabled`, `integration_disabled`, `integration_tested`, `integration_credentials_rotated`, and `integration_health_checked`, or their canonical equivalents.

### Tenant models exist, but integration models do not

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/tenant.py:21-39` defines `Agency`, including a generic `settings` JSON field.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/tenant.py:75-110` defines `Membership`.
- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/tenant.py:653-690` defines execution events with actor fields.

Finding:

There is no `AgencyIntegration`, `IntegrationCredential`, `IntegrationHealth`, or equivalent tenant-scoped integration table/model. Do not bury integration state inside `Agency.settings` or `AgencySettings.config_json`; that would make health, audit, scoping, and credential hygiene worse.

### Tests cover settings and provider config, not integration enablement

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/tests/test_settings_router_contract.py:4-39` checks the current settings response shape.
- `/Users/pranay/Projects/travel_agency_agent/tests/test_settings_router_contract.py:62-69` checks pipeline and approvals collections.
- `/Users/pranay/Projects/travel_agency_agent/tests/test_agency_settings.py:8-17` checks settings defaults.
- `/Users/pranay/Projects/travel_agency_agent/tests/test_agency_settings.py:26-58` checks settings save/load behavior.
- `/Users/pranay/Projects/travel_agency_agent/tests/test_agency_settings.py:131-149` checks profile field persistence.

Finding:

No tests currently prove provider registry behavior, per-agency integration scoping, safe credential storage, health state, audit events for integration operations, frontend route-map parity, or OpenAPI/path parity for integrations.

## Stale or Aspirational Docs

### Settings integrations docs are ahead of implementation

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/Docs/SETTINGS_ROUTE_SUBROUTE_UX_CONTRACT_2026-04-23.md` references `/settings/integrations` and `GET /api/settings/integrations` as a settings subroute/API concept.
- Current runtime settings page has no `integrations` tab or subroute.
- Current backend settings router has no `/api/settings/integrations` handler.

Classification: aspirational/stale relative to current runtime.

### Role matrix includes integrations before runtime support exists

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/Docs/CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md` references integration settings permissions.
- Current code has no integration resource/API to enforce those permissions against.

Classification: aspirational permission design.

### WhatsApp and provider docs mix MVP manual workflow with future automation

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/Docs/INTEGRATIONS_AND_DATA_SOURCES.md:92-100` describes WhatsApp Business API as an optional/future layer and manual WhatsApp workflow as MVP.
- `/Users/pranay/Projects/travel_agency_agent/Docs/INTEGRATIONS_AND_DATA_SOURCES.md:193-196` says provider integrations should happen when demand/scale triggers.
- `/Users/pranay/Projects/travel_agency_agent/Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md:11-13` says the app can start without a registered WhatsApp Business API and recommends manual copy-paste first.
- `/Users/pranay/Projects/travel_agency_agent/Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md:857-870` says manual/WhatsApp Business App comes before full automation.
- `/Users/pranay/Projects/travel_agency_agent/Docs/discussions/integrations_2026-04-29.md:15-23` treats WhatsApp API and Google Calendar as important, while also calling integrations debt.
- `/Users/pranay/Projects/travel_agency_agent/Docs/discussions/integrations_2026-04-29.md:332-333` says WhatsApp API should happen now and calendar sync can be manual.

Classification: mixed historical product discussion. Current safest interpretation is: manual channel workflows may remain valid, but automated provider work should wait behind integration enablement foundation.

### Existing integration architecture note is directionally useful but not implementation evidence

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/Docs/research/INTEGRATION_ARCHITECTURE.md:21-80` introduces integration enablement foundation as the right first step.
- Later parts of that same doc still discuss provider-specific sequencing and WhatsApp/Twilio tradeoffs.

Classification: useful research map, not proof of implemented runtime.

## What Exists

- Authenticated agency/membership model.
- Settings router and settings frontend surface.
- Preferred channel preferences for agency operations.
- Several provider adapter patterns for LLMs, extraction, live travel tools, and document storage.
- Encryption helpers for private fields.
- SQL audit logging with user and agency attribution.
- Route-map discipline for frontend/BFF/backend alignment.
- Tests for settings contracts and provider config behavior.

## What Is Missing

- Canonical provider registry.
- Agency-specific integration instance model/table.
- Explicit integration status lifecycle.
- Integration capability model.
- Credential reference or encrypted credential storage contract.
- Strict no-secret/no-PII list response contract.
- Integration health-check model and endpoint.
- Integration enable/disable/test/rotate APIs.
- Integration-specific audit events/resource types.
- Frontend settings UI for integration status and actions.
- BFF route-map entries for integration APIs.
- OpenAPI/path parity coverage for integration routes.
- Tests for agency scoping, credential redaction, health status, status transitions, audit events, and frontend contract alignment.

## Security and Privacy Risks

1. Raw credentials could leak if integration config is stored in generic JSON settings.
2. Global env-based provider configuration does not support tenant-specific revocation, rotation, visibility, or health.
3. Existing loose decrypt fallback should not be used as the credential-read failure behavior for new integration credentials.
4. Audit events must never include raw access tokens, refresh tokens, webhook secrets, phone numbers unless explicitly safe/masked, payment references, proof URLs, freeform customer notes, passport data, or traveler names.
5. Provider health errors must be normalized into safe codes/messages, not raw provider responses.
6. Channel preferences must not be mistaken for consent or deliverability.
7. A future WhatsApp/Gmail/Calendar adapter without integration state would make policy failures and auth expiry invisible to operators.

## Proposed Minimal Data Model

The smallest correct foundation should be tenant-scoped and provider-agnostic.

### Code-level provider catalog

Start with a code constant, not a database table:

```python
SUPPORTED_INTEGRATION_PROVIDERS = {
    "whatsapp": {"capabilities": ["outbound_messages", "inbound_messages"]},
    "gmail": {"capabilities": ["email_read", "email_send"]},
    "google_calendar": {"capabilities": ["calendar_read", "calendar_write"]},
    "google_drive": {"capabilities": ["file_backup", "file_read"]},
    "sms": {"capabilities": ["outbound_messages", "delivery_status"]},
    "telegram": {"capabilities": ["outbound_messages", "inbound_messages"]},
}
```

This avoids premature provider CRUD while making the frontend and API deterministic.

### Database table: agency_integrations

Recommended fields:

- `id`
- `agency_id`
- `provider`
- `display_name`
- `enabled`
- `status`: `disabled | connected | degraded | auth_expired | misconfigured`
- `capabilities`: safe JSON/list copied from provider registry or selected subset
- `config_json`: safe non-secret config only
- `credential_ref`: reference to encrypted secret material, not the secret itself
- `last_health_check_at`
- `last_success_at`
- `last_error_code`
- `last_error_message_safe`
- `created_by_user_id`
- `updated_by_user_id`
- `created_at`
- `updated_at`

Credential implementation can be a second slice. The first slice can support disabled/misconfigured records with no real credentials.

### Credential boundary

Do not store raw provider tokens in:

- `Agency.settings`
- `AgencySettings.config_json`
- integration list responses
- audit `changes/details`
- frontend local state beyond a write-only credential form
- generic logs

Use either:

- encrypted credential blob behind a dedicated service, or
- a credential reference that later maps to a dedicated encrypted table or external secret manager.

For the first implementation unit, prefer `credential_ref` as a nullable field and do not implement secret writes yet.

## Proposed Minimal API Surface

Canonical resource API should be integration-owned, with the settings UI consuming it:

- `GET /api/integrations`
- `GET /api/integrations/{provider}`
- `POST /api/integrations/{provider}/enable`
- `POST /api/integrations/{provider}/disable`
- `POST /api/integrations/{provider}/test`
- `GET /api/integrations/{provider}/health`
- `POST /api/integrations/{provider}/rotate-credentials`

To keep the first slice small, implement only:

- `GET /api/integrations`
- `GET /api/integrations/{provider}`

Those endpoints should return disabled/default provider records even before credentials exist. They should be agency-scoped and should not expose raw secrets.

Avoid creating both `/api/settings/integrations` and `/api/integrations` unless one is explicitly deprecated or delegated. The canonical resource should be one route family to avoid duplicate API route drift.

## Proposed Minimal UI Surface

First UI slice after backend foundation:

- add an `Integrations` tab or subroute under current agency settings
- show provider cards with:
  - provider name
  - capabilities
  - enabled/disabled status
  - connection status
  - last health check timestamp
  - safe last error code/message
- disable credential actions until credential write flow exists
- do not show raw tokens, webhook secrets, provider responses, or customer PII

The UI can live under settings, but it should call the canonical `/api/integrations` resource route.

## Tests Required

### Backend model/service tests

- provider registry returns expected providers and capabilities
- default integration records are disabled when no agency-specific record exists
- agency-scoped records cannot be read across agencies
- list response never includes `credential_ref` unless explicitly safe, and never includes raw credentials
- status enum rejects invalid status values

### Backend route tests

- `GET /api/integrations` requires auth
- `GET /api/integrations` scopes to current agency
- `GET /api/integrations/{provider}` returns 404 or contract-safe error for unsupported provider
- response shape is stable and documented

### Audit tests for later write endpoints

- enable/disable/test/rotate logs actor user id and agency id
- audit payload contains safe metadata only
- no raw credential, webhook secret, phone number, token, provider raw response, traveler data, payment proof URL, or freeform note appears in audit payload

### Frontend/BFF tests

- route-map includes canonical integration paths
- typed client fetches list and provider detail
- settings UI renders disabled/default states safely
- frontend handles `disabled`, `misconfigured`, and `auth_expired` without crashing

### Parity and contract tests

- OpenAPI/path parity test includes integration routes if the repo's route snapshot tests require it
- BFF path parity test aligns frontend client, route map, backend route, and tests

### Env/module-cache tests if provider env is touched

- do not modify global provider env behavior in the first slice
- if a later slice reads env for provider defaults, test monkeypatch/module-cache behavior explicitly

## Deduped Issue Register

### I1: No canonical integration enablement resource

Current state:

- settings and provider env config exist
- no first-class integration model/API/UI exists

Impact:

- provider work will drift into one-off WhatsApp/Gmail/Calendar implementations
- operators cannot see connection state or degraded status

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py:34-283`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/settings/page.tsx:22-27`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:23-28`

Priority: P0 foundation before provider automation

### I2: Channel preferences are overloaded as if they were integrations

Current state:

- `preferred_channels` exists in agency settings
- no channel capability, consent, delivery, or provider connection model exists

Impact:

- product may incorrectly infer a channel is usable because it is preferred

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py:160-191`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/settings/components/OperationalTab.tsx`

Priority: P1

### I3: Provider config is global, not agency-scoped

Current state:

- LLM, extraction, live tools, and document storage use env-driven provider config
- no agency-specific enablement state

Impact:

- auth expiry, vendor outage, disabled provider, and per-agency credential differences are invisible

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/src/llm/__init__.py:68-177`
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/extraction_service.py:77-139`
- `/Users/pranay/Projects/travel_agency_agent/src/agents/live_tools.py:236-443`

Priority: P1

### I4: No strict credential storage contract for integrations

Current state:

- encryption helpers exist
- integration credential storage does not exist

Impact:

- future provider work may store secrets in generic settings/config/logs

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/src/security/encryption.py:13-52`
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/private_fields.py:15-47`

Priority: P0 before credential write flows

### I5: Integration audit events are missing

Current state:

- SQL audit log exists
- no integration-specific audit actions/resource types exist

Impact:

- enable/disable/test/rotate operations would not be accountable unless added deliberately

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/audit.py:42-117`
- `/Users/pranay/Projects/travel_agency_agent/spine_api/core/audit.py:47-167`
- `/Users/pranay/Projects/travel_agency_agent/spine_api/core/audit_bridge.py:39-156`

Priority: P1 with first write endpoint

### I6: Settings integrations docs are ahead of runtime

Current state:

- docs mention `/settings/integrations` and integration permissions
- runtime lacks backend route and UI surface

Impact:

- future agents may treat aspirational docs as implemented truth

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/Docs/SETTINGS_ROUTE_SUBROUTE_UX_CONTRACT_2026-04-23.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`

Priority: P2 docs reconciliation after foundation choice

### I7: WhatsApp/Google/SMS/Telegram sequencing is not settled in docs

Current state:

- some docs recommend manual WhatsApp first
- some discussion docs push WhatsApp API now
- latest architecture direction says integration enablement first

Impact:

- provider work could start before platform capability is ready

Evidence:

- `/Users/pranay/Projects/travel_agency_agent/Docs/INTEGRATIONS_AND_DATA_SOURCES.md:92-100`
- `/Users/pranay/Projects/travel_agency_agent/Docs/INTEGRATIONS_AND_DATA_SOURCES.md:193-196`
- `/Users/pranay/Projects/travel_agency_agent/Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md:11-13`
- `/Users/pranay/Projects/travel_agency_agent/Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md:857-870`
- `/Users/pranay/Projects/travel_agency_agent/Docs/discussions/integrations_2026-04-29.md:15-23`
- `/Users/pranay/Projects/travel_agency_agent/Docs/discussions/integrations_2026-04-29.md:332-333`

Priority: P2

## Explicit Tasks Extracted

- Establish whether integration enablement exists.
- Inventory existing provider/config/settings/auth/audit surfaces.
- Separate aspirational docs from implemented runtime.
- Design the smallest correct foundation before provider work.
- Add the integration enablement topic to the exploration/research map.

## Implicit Tasks Extracted

- Prevent duplicate `/api/settings/integrations` versus `/api/integrations` route families.
- Prevent raw credential leakage through generic settings JSON, audit logs, frontend payloads, or provider error messages.
- Preserve manual WhatsApp/contact workflows as business continuity options without mistaking them for provider automation.
- Keep provider-specific work behind a stable adapter/resource boundary.
- Reconcile stale docs after a canonical API route family is chosen.

## Priority Queue

1. P0: Integration registry + read-only agency integration status model/API.
2. P0: Credential storage contract design before any credential write API.
3. P1: Integration audit action/resource taxonomy for enable/disable/test/rotate.
4. P1: Settings UI/BFF route-map alignment for integration status visibility.
5. P2: Docs reconciliation for `/settings/integrations`, role matrix, and WhatsApp sequencing.
6. P2: Provider-specific adapter selection: WhatsApp, Gmail, Calendar, Drive, SMS, Telegram.
7. P3: Continuity/fallback model, export/backup/restore, delivery attempt logs.

## Recommended Safe First Implementation Unit

Implement a read-only integration registry and agency-scoped status API.

Scope:

- add backend provider registry constant/service
- add `AgencyIntegration` persistence model/table with safe fields only
- add service method that returns default disabled records for supported providers
- add `GET /api/integrations`
- add `GET /api/integrations/{provider}`
- add tests for auth, agency scoping, response shape, unsupported provider, and no secret fields
- add frontend route-map/client types only if the API is intended to be immediately reachable from the app

Do not include in this first unit:

- real WhatsApp/Gmail/Calendar/SMS/Telegram calls
- OAuth
- credential write forms
- webhook handling
- health-check provider calls
- enable/disable write actions
- continuity backup/export logic

Why this is safe:

- It creates the source of truth without storing credentials.
- It makes future provider work converge on one route family.
- It can be tested without third-party accounts.
- It gives the settings UI a stable contract later.
- It avoids raw PII/payment/credential leakage by construction.

## Exact Files Likely Touched In First Unit

Backend:

- `/Users/pranay/Projects/travel_agency_agent/spine_api/models/tenant.py` or a new dedicated model module if that is the repo convention for new tables
- `/Users/pranay/Projects/travel_agency_agent/spine_api/routers/integrations.py`
- `/Users/pranay/Projects/travel_agency_agent/spine_api/server.py` only to include the router if routers are registered there
- `/Users/pranay/Projects/travel_agency_agent/spine_api/services/integration_registry.py`
- migration file under the repo's migration directory

Tests:

- `/Users/pranay/Projects/travel_agency_agent/tests/test_integrations_api.py`
- OpenAPI/path parity tests if route snapshots require updating
- auth/agency-scoping tests if existing fixtures cover new routers

Frontend if included:

- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts`
- frontend API client/types for integration list/detail
- frontend route-map parity tests

Docs:

- `/Users/pranay/Projects/travel_agency_agent/Docs/research/INTEGRATION_ARCHITECTURE.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/exploration/backlog.md`

## Tests To Run For First Unit

Minimum targeted backend checks:

```bash
uv run pytest tests/test_integrations_api.py -q
uv run pytest tests/test_settings_router_contract.py tests/test_agency_settings.py -q
uv run pytest tests/test_auth_integration.py -q
```

If backend routes/OpenAPI snapshots are touched:

```bash
uv run pytest tests -k "openapi or route or parity or integrations" -q
```

If frontend route-map/client is touched:

```bash
cd frontend && npm run typecheck
cd frontend && npm test -- --runInBand route-map
```

If env/module cache behavior is touched:

```bash
uv run pytest tests -k "env or provider or extraction or runtime_factory" -q
```

## Open Product and Architecture Questions

1. Should the canonical backend route be `/api/integrations` or `/api/settings/integrations`?

Recommendation: use `/api/integrations` as the resource API and let settings UI consume it. Avoid duplicate route families.

2. Should credentials be stored in the app database or external secret manager?

Recommendation: start with `credential_ref` and no credential writes in the first unit. Decide encrypted DB blob versus external manager before `rotate-credentials` is implemented.

3. Which provider should be first after the foundation?

Recommendation: do not choose yet. Foundation should support all provider statuses disabled/misconfigured before any live provider adapter.

4. Are channels and providers separate concepts?

Recommendation: yes. WhatsApp is both a channel and provider in many workflows, but Gmail/Google Calendar/Google Drive are providers with different capabilities. Model capabilities explicitly.

5. How should consent/opt-out relate to integration status?

Recommendation: separate contactability/consent from provider enablement. Integration connected does not mean a customer has consented to a channel.

6. Should manual workflows be represented as integrations?

Recommendation: no. Manual WhatsApp/phone/email can be operational workflows, but provider integrations should represent configured runtime capability.

7. Should integration health run synchronously in request paths?

Recommendation: no for real providers. The read model should show cached health; explicit `test` can trigger a bounded check later.

8. How visible should integration failures be to operators?

Recommendation: visible enough for operational action: status, safe last error, last check, and suggested next step. Hide raw provider responses and secrets.

## Final Recommendation

Treat integration enablement as an unimplemented foundation layer. Build the read-only registry/status API first, then add credential contract and write operations, then UI, then provider adapters. This sequence preserves the first-principles architecture: integrations are tenant-scoped product capabilities, not scattered env variables or one-off provider routes.
