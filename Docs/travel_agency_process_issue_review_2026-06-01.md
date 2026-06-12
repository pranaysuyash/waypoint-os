# Travel Agency Process Issue Review: Seasonal Surface Supersession & Removal Audit

**Audit date:** 2026-06-01  
**Scope:** `spine_api/routers/settings.py`, `spine_api/contract.py`, `frontend/src/app/(agency)/seasons/PageClient.tsx`, `frontend/src/hooks/useSeasonalCampaigns.ts`, `frontend/src/lib/api-client.ts`, `frontend/src/lib/route-map.ts`  
**Context package:** `motto_v2.md`, `/Users/pranay/AGENTS.md`, `/Users/pranay/Projects/AGENTS.md`, `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`, `Docs/context/agent-start/SESSION_CONTEXT.md`, `frontend/src/app/(agency)/settings/components/SeasonalTab.tsx`, `frontend/docs` references.  

## 1) Baseline and instruction-stack re-check

- Instruction stack was re-synced before this pass.
- Canonical routes were re-checked for seasonal campaigns via:
  - [`spine_api/routers/settings.py`](/Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py) endpoints
  - [`frontend/src/lib/route-map.ts`](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts) mappings
- Frontend contract and API client path were confirmed through explicit function signatures and route calls:
  - `CreateSeasonalCampaignRequest`, `UpdateSeasonalCampaignRequest`, and `SeasonalCampaignPlan` in [`spine_api/contract.py`](/Users/pranay/Projects/travel_agency_agent/spine_api/contract.py)
  - matching request builders and mutators in [`frontend/src/app/(agency)/seasons/PageClient.tsx`](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/seasons/PageClient.tsx) and [`frontend/src/hooks/useSeasonalCampaigns.ts`](/Users/pranay/Projects/travel_agency_agent/frontend/src/hooks/useSeasonalCampaigns.ts)

## 2) Supersession check (explicit per request)

### Candidate C1: Local state `activeMutations` in `PageClient.tsx`
- Candidate identified: `activeMutations` array in `frontend/src/app/(agency)/seasons/PageClient.tsx`
- Supersession probe:
  - Was there a better/new canonical equivalent? **No** (local UI-only intermediate state).
  - Did we find duplicate logic serving same role elsewhere? **No** (no call-sites and no consumers).
  - Could it be safely merged elsewhere? **Not applicable** (no behavior surface lost).
- Result: **REMOVE** (dead state, no functional owner, no public contract impact).
- Preservation evidence:
  - No downstream callsite usage remained after removal.
  - Mutation loading states are still taken directly from `useCreateSeasonalCampaign`, `useUpdateSeasonalCampaign`, etc.

### Candidate C2: Contract shape for update clears (null semantics)
- Candidate identified: `UpdateSeasonalCampaignRequest` payload types not allowing explicit clears.
- Supersession probe:
  - Existing canonical behavior: update route already accepts JSON nulls for fields (`SeasonalCampaignPlan` and persistence layer coerce path support).
  - Existing frontend types narrowed values to non-null, which made null-clear intent ambiguous.
  - No duplicate contract implementation exists.
- Result: **EVOLVE, NOT REMOVE** by expanding frontend type to include explicit nulls where user intent requires clears:
  - [`frontend/src/lib/api-client.ts`](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/api-client.ts)
  - no route change.

## 3) Call-site and drift verification (touched surfaces)

- One canonical write path for seasonal campaign operations exists:
  - backend: `spine_api/routers/settings.py`
  - contract: `spine_api/contract.py`
  - client methods: `frontend/src/lib/api-client.ts`
  - hook orchestration: `frontend/src/hooks/useSeasonalCampaigns.ts`
  - UI orchestration: `frontend/src/app/(agency)/seasons/PageClient.tsx`
- Route mapping remains centralized in one location:
  - [`frontend/src/lib/route-map.ts`](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts) includes seasonal campaign route families.
- No duplicate seasonal campaign route path was found in router layer or proxy mappings.
- No alternate canonical implementation was identified for these campaign operations, so replacement was not applicable.

## 4) What changed behavior-wise

- UI: no-op save in edit mode now exits edit mode with no network call when no effective field changed.
- API type safety: update request now permits explicit clears (`null`) for optional string/number campaign fields.
- Backend handling: unchanged at route signatures; update and create logic already treats null values consistently with current canonical schema and persistence coercion.

## 5) Risks, fragility, and long-term follow-up

- **Long-term risk 1:** Null-clearing semantics still rely on runtime/contract drift discipline.
  - Follow-up: add a small client/server contract parity check (generated types or dedicated test) before merge freeze.
- **Long-term risk 2:** Seasonal planner validation still has local parse/normalize helpers duplicated in UI and no shared domain helper.
  - Follow-up: extract a shared seasonal input normalization utility and reuse it in create/edit payload builders.
- **Long-term risk 3:** Backend preflight/simulation numeric parsing now defaults missing budget to 10000; this is resilient but should be made policy-visible in docs.
  - Follow-up: add explicit policy note in `Docs/SEASONAL_PLAN_04_EXECUTION_AND_INTEGRATION.md`.

## 6) Recommendation

- **Keep the canonical seasonal path and continue** with one editable path in:
  - backend route module,
  - contract module,
  - generated API client types,
  - UI hooks.
- **No legacy duplicate seasonal implementation** exists to supersede.
- Do not re-introduce removed local state.

## 7) Next tasks (actionable)

1. [DONE] Add contract parity verification in CI-like checks for seasonal campaign request/response types.  
   - Status: added in `frontend/src/types/__tests__/contract-surfaces.test.ts`.
2. [DONE] Introduce shared seasonal payload normalization helper for create/update parity.  
   - Status: shared helpers now live in `frontend/src/lib/seasonalCampaigns.ts` and are used by `PageClient.tsx`.
3. [DONE] Add a small integration check list for seasonal CRUD simulation/preflight flows.  
   - Status: added in `frontend/docs/SEASONAL_PLAN_04_EXECUTION_AND_INTEGRATION.md`.

Checklist applied: `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`
