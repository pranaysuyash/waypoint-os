# Mimosa sealed-scan receipt + candidate triage posture (2026-10-25)

**Scan:** `scan-2026-10-25T17-39-34.028Z-269ce8e4797f` · **seal**
`sha256:da07a4d83cd7d10487bd22f12c2a58a009b3d1c6c6f66f4ba521205b161cea4c` ·
depth deep · findings 128 (45 business-logic candidates) · **coverage:
partial / run status: inconclusive** (report: `~/.mimosa/security-scans/
project-1a789e004350b2e32cc42e24/<scanId>/report.md`).

**Why this scan ran:** the managed git hook noted (`scanner_enobufs`) that no
complete scan conclusion existed before the `d2617629` push and advised a
full re-run. This is that re-run. Per the hook's own caveat: this receipt
must NOT be read as a claim that the project is secure.

**Coverage caveat (from the scan's own coverage.json):** the call graph is
partially incomplete — the scanner repeatedly records "未能把入口稳定绑定到
项目证据图中的 handler" (could not bind entry handlers into the evidence
graph) and reports guards/dependencies as absent when it simply cannot see
the FastAPI `Depends(...)` layer. **Second caveat:** the scan ran against a
dirty working tree (a parallel agent had 80+ files mid-flight, including
`src/intake/extractors.py` refactors), so results are provisional for those
files.

## Triage disposition (pattern-level, evidence-backed)

The 45 candidates are two recurring hypothesis shapes, both matching the
2026-09-11 wave's triaged-as-MITIGATED class:

1. **"敏感操作未观察到角色或权限检查" (sensitive op, no observed role check)**
   — spot-verified FALSE for `spine_api/routers/auth.py:253 get_me`
   (`Depends(get_current_user)` + `Depends(get_current_membership)` present,
   lines 254-255) and for `spine_api/routers/auth.py:348
   post_confirm_password_reset` (token-scoped flow). The scanner's handler
   binding gap makes this class structurally unreliable.
2. **"资源标识来自请求，未观察到所有权或租户绑定" (resource id from request,
   no ownership/tenant binding)** — spot-verified FALSE for
   `spine_api/routers/analytics.py:152 get_agent_drill_down`
   (`Depends(get_current_agency)` at :156 + `_all_agency_records(
   TripStore.list_trips, agency.id)` at :159 — tenant-scoped). This class
   deserves a systematic pass because the zero-red sweep (57113daf) proved
   REAL instances existed historically (generic trip views leaking
   booking/pending PII). **Action queued:** full 45-candidate triage with
   per-site file:line evidence (same protocol as the 2026-09-11 annex) as
   its own wave — registered here, not silently dismissed.

**Dependency advisories:** offline advisory matched 8 packages / 37
advisories — apparently contradicting FND-0374's just-committed
"14 vulnerable packages resolved to 1 documented residual". Resolution
pending: the scanner's offline advisory DB likely keys loosely (name-only,
unfiltered severity) where FND-0374 used filtered ranges; reconcile in the
same queued triage wave before treating either number as current truth.

**Standing open item continuity:** FND-0117 (memory-partition scanner caveat)
stays open per the 2026-09-11 wave; nothing in this scan supersedes it.
