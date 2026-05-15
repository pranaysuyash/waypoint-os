# Workbench → Trip Workspace Migration: Disposition Register
**Date:** 2026-05-14  
**Migration:** Ops execution moves from Workbench to Trip Workspace  
**Status:** In progress — see Implementation Status column

---

## Disposition Key

| Code | Meaning |
|------|---------|
| **MIGRATE** | Capability moves into Trip Workspace as canonical durable location |
| **ALIAS** | Old route/path becomes a **permanent** redirect to the new canonical location — old URLs must keep working indefinitely |
| **REMOVE (UI duplicate)** | The duplicate editable Workbench UI is removed after verified parity in Trip Workspace — the capability itself is not removed, only the Workbench-side copy |
| **RETAIN** | Kept in Workbench; not part of this migration |
| **DEFERRED** | Not handled in this slice; tracked for follow-up |

---

## Route Dispositions

| Item | Current Location | New Canonical | Disposition | Reason | User Impact | Approval Required | Implementation Status |
|------|-----------------|---------------|-------------|--------|-------------|-------------------|-----------------------|
| Ops / booking execution UI | `/workbench?tab=ops` | `/trips/{id}/ops` | MIGRATE + REMOVE (UI duplicate) | Ops is durable trip execution state, not ephemeral processing. All capabilities migrated. Old Workbench editable UI removed; Trip Workspace is now the canonical location. | Operators use Trip Workspace Ops; the capability itself is fully preserved | No — decision already made | ✅ Done (Phase 3 + 9) |
| `/workbench?tab=ops&trip={id}` deep link | Workbench URL pattern | `/trips/{id}/ops` | ALIAS (permanent) | Old links in SOPs, bookmarks, and integrations must continue working indefinitely | Old links redirect silently to Trip Workspace Ops; no operator action needed | No | ✅ Done (Phase 9) |
| `/workbench?tab=ops` (no trip) | Workbench | `/workbench?tab=intake&notice=ops-requires-trip` | ALIAS (with notice) | No trip context means operator is starting new work, not executing booking ops | Redirected to intake; notice explains Ops requires a proposal/booking-stage trip | No | ✅ Done (Phase 9) |
| Post-Spine "View Trip" navigation | → `/trips/{id}/intake` | → `/trips/{id}/ops` for proposal/booking | MIGRATE | Operators land at the actionable tab, not intake | Better handoff after AI processing | No | ✅ Done (Phase 5) |
| `processed <timestamp>` in Trip Workspace header | `useWorkbenchStore().result_run_ts` | Nothing (removed) | REMOVE | No trip-level `last_ai_run_at` field exists; `updated_at` is misleading; transient session state is wrong source | Minor — display was inaccurate from fresh sessions anyway | No | ✅ Done (Phase 7) |

---

## Capability Dispositions

| Capability | Workbench Ops | Trip Workspace Ops | Disposition | Parity Status |
|-----------|--------------|-------------------|-------------|---------------|
| Booking readiness display | ✅ | ✅ | MIGRATE | Verified — `OpsPanel` renders in Trip Workspace with `TripContext` |
| BLOCKED/ESCALATED reasons | ✅ | ✅ | MIGRATE | Verified — `trip?.validation` fallback already exists in OpsPanel lines 182–184 |
| Traveler booking data | ✅ | ✅ | MIGRATE | OpsPanel uses `trip.id` for API calls; works from direct load |
| Document list/upload/review | ✅ | ✅ | MIGRATE | OpsPanel `getDocuments` uses tripId, no workbench store dependency |
| Extraction history/status | ✅ | ✅ | MIGRATE | Pending booking data APIs use tripId |
| Payment tracking | ✅ | ✅ | MIGRATE | Payment state is local to OpsPanel, loaded from tripId |
| Collection link generation | ✅ | ✅ | MIGRATE | Collection link APIs use tripId |
| Booking tasks | ✅ | ✅ | MIGRATE | Booking execution panel uses tripId |
| Error states | ✅ | ✅ | MIGRATE | OpsPanel local error states are component-level, not store-dependent |
| Loading states | ✅ | ✅ | MIGRATE | OpsPanel loading state is component-level |
| Direct URL load without Workbench store | ❌ | ✅ | MIGRATE | `useWorkbenchStore` dependency removed from OpsPanel |

---

## File Dispositions

| File | Disposition | Action | Approval Required | Status |
|------|-------------|--------|-------------------|--------|
| `workbench/OpsPanel.tsx` | RETAIN + DECOUPLE | Remove `useWorkbenchStore` import; use `trip?.validation` fallback only | No | ✅ Done (Phase 6) |
| `workbench/DecisionTab.tsx` | DEFERRED | Import removed from PageClient; file retained; see inventory doc | Yes — before delete | ✅ Import removed |
| `workbench/StrategyTab.tsx` | DEFERRED | Import removed from PageClient; file retained; see inventory doc | Yes — before delete | ✅ Import removed |
| `workbench/PageClient.tsx` | MODIFY | Remove Ops tab, showOps, OpsPanel render, dead imports; add URL redirect | No | ✅ Done (Phase 8+9) |
| `trips/[tripId]/layout.tsx` | MODIFY | Add Ops tab with stage gate; remove workbench store read | No | ✅ Done (Phase 2+7) |
| `trips/[tripId]/ops/page.tsx` | CREATE | New page shell | No | ✅ Done (Phase 3) |
| `trips/[tripId]/ops/PageClient.tsx` | CREATE | New page client with migration banner | No | ✅ Done (Phase 3+4) |
| `lib/routes.ts` | MODIFY | Add 'ops' to WorkspaceStage | No | ✅ Done (Phase 1) |

---

## Store Dependency Dispositions

| Store Field | Component | Disposition | Replacement | Status |
|-------------|-----------|-------------|-------------|--------|
| `result_validation` | `OpsPanel.tsx:180` | REMOVE | `trip?.validation` fallback (already exists at line 183) | ✅ Done (Phase 6) |
| `result_run_ts` | `layout.tsx:103` | REMOVE | No replacement — display removed; no trip-level field | ✅ Done (Phase 7) |

---

## Known Risks and Follow-up

1. **`DecisionTab` and `StrategyTab`**: Files contain non-trivial logic. Not deleted. Product decision needed on whether to migrate to Trip Workspace tabs or archive. See `WORKBENCH_DEFERRED_TABS_INVENTORY_2026-05-14.md`.

2. **Workbench re-run flow (Option C)**: If an operator opens an existing trip in Workbench to re-run Spine, they still land on `/intake` afterwards (unless at proposal/booking stage). Full redirect-on-load for existing trips is deferred until a re-run affordance is built inside Trip Workspace. Tracked as Phase 3 (roadmap) in architecture docs.

3. **`last_ai_run_at` field**: Trip Workspace no longer displays a "last processed" timestamp because no trip-level field exists. To restore this display, add a `spine_updated_at` or `last_ai_run_at` field to the `TripResponse` in `spine_api/contract.py` and populate it whenever a Spine run completes for a trip.

4. **Phase-adaptive tabs**: Not implemented in this slice. Roadmap item for a future sprint.
