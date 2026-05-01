# Frontier Phase 0 — Removal Diff Plan

**Date:** 2026-04-30
**Status:** IMPLEMENTED. All changes applied, build passes, 4/4 workbench page tests pass, no leaked frontier terms in production UI.

---

## Files Changed

### 1. `frontend/src/app/(agency)/workbench/page.tsx`

| Change | Lines | Detail |
|--------|-------|--------|
| Removed `FrontierDashboard` dynamic import | 56-60 | `const FrontierDashboard = dynamic(...)` block deleted |
| Removed `{ id: 'frontier', label: 'Frontier OS' }` from `workspaceTabs` | 79 | Tab no longer exists in the tab array |
| Updated comment re: workspace sections | 118-119 | Changed "Output, Frontier OS, and Feedback" to "Output and Feedback" + note about park |
| Updated transient run artifacts comment | 229 | Changed "Clear only transient run artifacts (frontier, run_ts, acknowledged flags)" |
| Removed `activeTab === 'frontier' && <FrontierDashboard />` block | 1073-1086 | All 14 lines of render block deleted |

### 2. `frontend/src/app/(agency)/workbench/SettingsPanel.tsx`

| Change | Lines | Detail |
|--------|-------|--------|
| Removed `Ghost, Heart, Network, ShieldCheck` imports | 3 | Cleaned unused lucide-react icons |
| Removed `enable_ghost_concierge`, `enable_sentiment_analysis`, `federated_intelligence_opt_in`, `audit_confidence_threshold`, `enable_auto_negotiation`, `negotiation_margin_threshold` from store destructuring | 17-28 | All frontier config selectors removed |
| Removed entire "Advanced AI Features" section | 99-283 | Ghost Concierge, Sentiment, Federated Intelligence, Auto-Negotiation, Negotiation Margin, Audit Threshold — all UI removed |

### 3. `frontend/src/stores/workbench.ts`

| Change | Lines | Detail |
|--------|-------|--------|
| Added `PARKED (Frontier Phase 0)` comment above config toggles | 58-63 | Documents why they're kept |
| Added `PARKED (Frontier Phase 0)` comment above `result_frontier` | 86 | Documents why field is kept |

### 4. `frontend/src/app/(agency)/workbench/__tests__/page.test.tsx`

| Change | Lines | Detail |
|--------|-------|--------|
| Added PARKED comment to `result_frontier` mock | 69-70 | Documents test mock |
| Added test: "does not render Frontier OS tab" | 134-142 | Verifies "Frontier OS" text is absent |
| Added test: "falls back safely when an invalid tab is requested" | 144-152 | Verifies `?tab=frontier` doesn't crash |

### NOT Changed (Kept)

| File | Why |
|------|-----|
| `FrontierDashboard.tsx` | Parked — component file kept for design reference. Not reachable in UI. |
| `spine_api/models/frontier.py` | Parked — real DB models |
| `spine_api/routers/frontier.py` | Parked — real REST endpoints |
| `src/intake/frontier_orchestrator.py` | Kept — real pipeline logic, runs every pipeline invocation |
| `src/intake/federated_intelligence.py` | Parked — prototype |
| `src/intake/specialty_knowledge.py` | Kept — real niche checklists |
| `spine_api/contract.py` | Kept — canonical contract, `FrontierOrchestrationResult` stays |
| `spine_api/server.py` | Kept — no frontier wiring changed |
| `data/fixtures/sc_frontier_*.json` | Kept — test scenarios |

---

## Expected UI After Change

1. Workbench has **7 tabs** (was 8): Intake, Packet, Decision, Strategy, Safety, Output, Feedback
2. No "Frontier OS" tab visible
3. URL `/workbench?tab=frontier` silently falls back (shows intake/default tab)
4. Settings panel has **only strict leakage** toggle (no Ghost/Sentiment/Federated/Negotiation)
5. No "Frontier OS", "Ghost Concierge", "Federated Intelligence", "No active risks detected" text anywhere in the workbench

---

## Verification Results

| Check | Status |
|-------|--------|
| Build passes | ✅ `npm run build` — clean |
| Workbench page tests | ✅ 4/4 pass (including 2 new Phase 0 tests) |
| Integrity panel tests | ✅ 2/2 pass |
| No "Ghost Concierge" in workbench | ✅ grep returns 0 matches |
| No "Federated Intelligence" in workbench | ✅ grep returns 0 matches |
| No "No active risks" in workbench | ✅ grep returns 0 matches |
| No "GHOST-SEQ" in workbench | ✅ grep returns 0 matches |
| No "412 variables" in workbench | ✅ grep returns 0 matches |
| No "Sentiment Detection" in workbench | ✅ grep returns 0 matches |
| Backend models untouched | ✅ Zero changes to any .py file |
| Store fields preserved | ✅ `result_frontier` + frontier config fields kept with PARKED comments |
