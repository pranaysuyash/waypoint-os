# Operations Overview — Incoming Work Queue & Start Here Overhaul (2026-11-11)

**Date:** 2026-11-11
**Status:** Implemented and verified (unit tests, type-check, lint, live browser)

---

## Summary

Executed Part 1 (sync commit `4be08058` of `frontend/docs/context/agent-start/STEP1_ENV.sh`) and Part 2: a first-principles overhaul of the `Start Here` spotlight and `Incoming Work` triage queue (`WorkQueuePanel`) on `/overview`.

### Root Causes Diagnosed

1. **System watchdog drowning live client demand:**
   In the live agency work log (`5,392` total items; `1,254` `demand`, `4,003` `operator`, `133` `system`), every `system` `stale_run_timeout` watchdog row enters at `urgency: "high"`, while `ranked_queue` sorted purely by `(urgency, returning_customer, -received_at)`. With no `origin` filter exposed on the API or UI, all 8 visible rows in `Incoming Work` were identical `HIGH · Run timed out · by the run watchdog` entries, completely burying 1,254 live client inquiries (`public_checker`, `instagram_dm`, `extension`, `whatsapp_web`).
2. **Dead-end rows & UI slop:**
   - Bound work items (`trip_id` present) offered only Claim/Dismiss actions with zero link to open the associated trip workspace.
   - `WorkQueuePanel` carried `CLASSIFIED` pill text, repeated uppercase `NORMAL` / `HIGH` pills, raw `instagram_dm` / `extension` tokens when unmapped, and internal jargon copy (`"totals count the append-only work log"`).
   - `Start Here` in `/overview` stacked 4 redundant lines directly beneath `Action Required`, duplicating card #1 with bare uppercase `ENQUIRY URGENT` chrome and un-sanitized machine tokens (`STOP_NEEDS_REVIEW`, `PENDING`).

---

## Changes Made

### 1. Backend Origin Filtering & Channel Display Normalization
- `spine_api/services/work_intake.py`:
  - Added `"whatsapp_web": "WhatsApp"`, `"instagram_dm": "Instagram DM"`, `"extension": "Chrome extension"` to `CHANNEL_DISPLAY`.
  - Added `origin: Optional[str] = None` parameter to `ranked_queue()` filtering `visible` after ranking while leaving `total`, `actionable`, and `counts` as honest queue-wide aggregates.
- `spine_api/routers/work_items.py`:
  - Exposed `origin: Optional[str] = Query(default=None, ...)` on `GET /api/v1/work-items` and forwarded it to `work_intake.ranked_queue()`.
- `tests/test_work_intake.py`:
  - Extended `test_ranked_queue_filters_honestly` to verify `origin="demand"` and `origin="system"` isolation with honest totals.
  - Extended `test_display_for_channel_aware_headlines` to verify `"whatsapp_web"`, `"instagram_dm"`, and `"extension"`.

### 2. Frontend API, Hook & `WorkQueuePanel` Overhaul
- `frontend/src/lib/work-items-api.ts` & `frontend/src/hooks/useWorkItems.ts`:
  - Added optional `origin?: WorkItemEntry['origin']` parameter to `WorkItemFilterParams`, `getWorkItems`, and `useWorkItems` query key & filter forwarding.
- `frontend/src/components/overview/WorkQueuePanel.tsx`:
  - Defaulted `WorkQueuePanel` to `originTab = 'demand'` with stably mounted Origin tabs (`Client Demand`, `System Alerts`, `Team Activity`, `All Signals`) and per-origin counts (`counts.by_origin`), plus one-click `"View all N active items"` fallback when `demand` has 0 items but `actionable > 0`.
  - Replaced `CLASSIFIED` pill + `HIGH`/`NORMAL`/`LOW` uppercase clutter with semantic source icons (`Globe` for web checker, `MessageSquare` for messaging channels, `FileCheck2` for proposal links, `AlertTriangle` for system exceptions, `Activity` for team actions) and subtle `Urgent` badge only on high-urgency items.
  - Added direct `<Link href={getTripRoute(item.trip_id, 'intake')}>Open trip</Link>` dispatch CTA on bound items.
  - Normalized legacy channel tokens in meta lines and replaced `"totals count the append-only work log"` footer text with `"Showing X of Y logged work items"`.
- `frontend/src/components/overview/__tests__/WorkQueuePanel.test.tsx`:
  - Updated 3 existing filter assertions to expect default `origin: 'demand'`.
  - Added tests for default `demand` query, Origin tab switching (`System Alerts`, `All Signals`), `Open trip` `<Link>` rendering on bound rows, and empty-demand fallback CTA.

### 3. `Start Here` Spotlight Compaction
- `frontend/src/app/(agency)/overview/PageClient.tsx`:
  - Compacted `<section aria-label='Start Here'>` into a single-row priority command strip, preserving `aria-label="Start Here"`, `"Start here"`, `featuredAction.title`, primary/secondary links, while removing bare uppercase `URGENT` slop and sanitizing `STOP_NEEDS_REVIEW` / `PENDING` tokens in copy.

---

## Verification

- **Backend unit tests:** `uv run pytest tests/test_work_intake.py -k "not router and not closed_loop and not session_client and not t_work_item_action_endpoint and not include_done_history_reader and not messaging_webhook and not triage_consumes" tests/test_bff_parity_gate.py -q` → `31 passed, 10 deselected in 0.68s` (note: Postgres-dependent `session_client` tests require unsandboxed DB socket access and were excluded from the sandboxed run).
- **Backend lint:** `uv run ruff check spine_api/services/work_intake.py spine_api/routers/work_items.py tests/test_work_intake.py` → `All checks passed!`.
- **Frontend unit tests:** `npm test --prefix frontend -- src/components/overview/ src/app/\(agency\)/overview/ --run` → `8 test files passed (8), 62 tests passed (62)` (`WorkQueuePanel.test.tsx`: 13/13; `page.test.tsx`: 16/16).
- **Type-check & ESLint:** `cd frontend && npx tsc --noEmit && ./node_modules/.bin/eslint -c eslint.config.mjs src/components/overview/WorkQueuePanel.tsx src/app/\(agency\)/overview/PageClient.tsx src/lib/work-items-api.ts src/hooks/useWorkItems.ts src/components/overview/__tests__/WorkQueuePanel.test.tsx` → exit code `0`.
- **Live Browser Verification (`http://localhost:3005/overview` + restarted `uvicorn` on `:8000`):**
  - Reloaded with live backend and verified `Client Demand (1254)` surfaces real `Public checker`, `Chrome extension`, and `Instagram DM` items with `Open trip` links (`/trips/trip_d9c07cf4/intake`, `/trips/trip_669fcf9a/intake`), `System Alerts (133)` still opens `Run timed out` rows on click, and `Start Here` renders cleanly as a single-row strip.
  - Before/after visual captures: `/Users/pranay/.gemini/antigravity/brain/51dc08fd-8b47-470a-b883-0b05f9971a9c/work_queue_before.png` and `/Users/pranay/.gemini/antigravity/brain/51dc08fd-8b47-470a-b883-0b05f9971a9c/work_queue_after.png`.
