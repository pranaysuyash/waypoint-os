# Worklog — Council Wave Build (T2–T10), 2026-11-03/04

Owner order (2026-11-03): "no waiting on onboarding — everything gets built."
All ten tranche items from the 2026-11-03 council implemented, tested, and
documented. Commits remain owner-gated (working tree carries the wave).

## Landed

| Tranche | Deliverable | Tests |
|---|---|---|
| T2 operator surface | Inbox→intake hand-off (`pending_intake_prefill` store + "Use for intake"), attachment chips | 14 FE |
| T3 money durability | Audit: payout ledgers already durable-by-default; NEW startup guard `ADVISOR_PAYOUT_BACKEND` (memory override rejected in production/staging) | +5 (58 file) |
| T4 authority-ranked facts | `try_record_fact_override` guarded writer; operator edits = `manual_override`, ask answers = `explicit_user` (conflicts reported honestly via `rejected_facts`); memory-adopt endpoint (`explicit_owner` + `adopted_from_memory`, composes ADR-008 display-only) | +16 (fact guard 12, adopt 4) + 27 consumer suites |
| T5 commission ingest (R2-B) | `commission_ingest.py` (CSV/email/OCR-text parse, booking-ref → amount+fuzzy difflib match, manual-link fallback), 3 router endpoints, route-map, FE `CommissionStatementsTab` | 10 BE + 4 FE + parity gate |
| T6 compliance (R2-C) | Effective-dated TCS regimes (budget2024/25/26 — current law: **flat 2% from first rupee**; research corrected the stale adjudication figure), GST 2.0 service matrix, `TripQuoteView` `tax_basis` conditional vocabulary + statutory preview producer, quotes FE render + 2 in-blast-radius FE defect fixes (null-retail crash; missing-inputs invisible when quote exists) | 15 engine + 8 producer + 8 quotes FE |
| T7 trust surfaces (gap-4) | Public proposal: `why_this_fits` (deterministic, persisted-facts-only) + `open_questions` with field names; FE sections | +6 |
| T8 KPI (R2-F) | `agentResolvedShare` on inbox stats (None when nothing resolved — never fabricated 0%), insights StatCard | +2 BE, FE type+mock |
| T9 IRROPS (R2-H gate) | `Docs/architecture/IRROPS_SEMANTICS_2026-11-04.md` (closed trigger taxonomy, signal sources, decision-desk mapping, watcher generalization plan, JDG gap recorded); `irrops.py` + `POST /disruptions/{trip_id}/report` operator-reported producer | +11 |
| T10 agency API (R2-A) | Hashed API-key auth core (show-once, revoke fail-closed, documented non-RLS posture), provenance-gated trip-summary envelope (license_tier/as_of/sources, PII withheld), key mint/revoke JWT-gated, parity-gate exemption with rationale | +6 |

Also: TCS/GST research record (TinyFish route; WebSearch quota-blocked) at
`Docs/research/INDIA_COMPLIANCE_RATES_TCS_GST_2026-11-03.md`; TRV-DP-07
decision records; FND-0398 opened (/suppliers hardcoded tiers);
RouteMapStudio park-or-mount surfaced to owner (§6.1).

## Residual / exact next checks
1. **Visual BEFORE/AFTER captures** for the FE surfaces (doctrine §3
   sharpening) — needs servers + browser pass; surfaces: commission tab,
   quotes tax line, public-proposal trust sections, inbox intake button.
   Start backend :8000 + frontend :3005, walk the four surfaces.
2. `/suppliers` sample tiers disposition (FND-0398) — ship real read model
   or label, owner call next tranche.
3. Watcher generalization tranche (triggers beyond price) — unblocked by the
   IRROPS doc; sequence after DP-04a or first pilot demand signal.
4. Route snapshot fixtures can be regenerated (`scripts/snapshot_server_routes.py`)
   at next commit gate for documentation freshness.

## Regression closeout (2026-11-05)

- Full backend suite: **5,906–5,908 passed / 0–2 flaky per run** (trim order-pollution and pa_wave2 multi-process probe pass in isolation; neither file is in the wave diff). All 26 initial failures root-caused: 11 = D1 authority-label pins updated to the TRV-DP-07 contract, 10 = stale TCS pins updated to regime-explicit form (budget2024 window pinned via as_of + current-law asserts), 2 rate-limit/message-store drift pins updated, 1 route-map backendPath normalization, 1 RLS registry entry for `agency_api_keys` (excluded per D5, same credential-hash precedent as proposal_access_tokens), 1 characterization mock missing the new store fields.
- FE: all wave-owned suites green (characterization 11/11 after mock fix); residual = FND-0402 prior-wave drift (mode_selector 10 + overview ~17, stale button-copy/planning-panel mocks, verified pre-existing by stash-baseline + git provenance of the copy change).
- Snapshots regenerated (`scripts/snapshot_server_routes.py --write`); parity + inventory gates green.

## FND-0402/0398 closeout (2026-11-06)

**FND-0402 CLOSED — FE suite 199 files / 1,489 tests ALL PASSING, tsc clean.**
Root-cause class: trip fixtures predated the required-brief gate (FND-0379
added trip purpose to the required set), so every "ready" fixture silently
rendered the lead-review state. Fixed: 9 fixture completions + 4 stale
gate-copy pins + 1 regex match + 1 QueryClientProvider wrap.

**Product fixes beyond test repair (tests were the spec — features were
never built):**
1. **AT-20 public proposal** (`p/[token]/page.tsx`): acceptance POST now
   binds `revision_id` (stale-terms protection); 409 revision conflict
   renders a recoverable role=alert with the backend detail + "Review latest
   proposal" re-fetch button; `requires_reacceptance` renders the
   previously-accepted-terms banner; native-currency total via house
   `formatMoney` (replaces the hardcoded `$` that mislabeled INR as
   "$125,000 INR"); ProposalData carries the reacceptance wire fields.
2. **Insights commercial evidence** (`insights/PageClient.tsx`): removed the
   five fabricating money StatCards ("$0 Confirmed revenue" et al.); added
   the evidence-backed Commercial Outcomes section — Pipeline budgets /
   Recorded booking value / Agency earned revenue groups render ONLY from
   `commercial.*` measures with availability, per-currency totals, trip
   counts, and partial-evidence qualifications.

**FND-0398 CLOSED** — suppliers commission tiers suffixed "(illustrative)"
at record level (FND-0182 rigor); real master data awaits DP-04a.

Remaining owner items unchanged: DP-04a/b, X-09, 51c ADR, RouteMapStudio
park-or-mount, commit authorization.

## Verification tranche (2026-11-06) — "do it all"

**D1 — agency_api_keys migration (defect fixed).** The table had only runtime
ensure-table; backup/restore + rollback drills couldn't see it. Added
`alembic/versions/agency_api_keys_r2a.py` (chain: add_revoked_tokens →
agency_api_keys_r2a, head). Live-verified against waypoint_os Postgres:
upgrade → downgrade → upgrade round-trip on the empty table, column/index
shape matches the runtime model exactly (Tier 4). Data-safety: row count
checked (0) before downgrade; no data dropped.

**D2 — ingest→payout flow closure (defect fixed).** The commission flow
stopped at preview candidates with nothing moving money truth. Added
`record_row_payout` (spine_api/services/commission_ingest.py) + POST
`/ingest/{batch_id}/record` (routers/commission.py): matched-only, USD-only
(explicit no-FX-conversion rejection with operator guidance), advisor-
attributed, double-record guard via row.recorded/recorded_payout_id, full
provenance note into the durable payout. FE: record control on matched USD
rows + recorded badge; route-map key + api-client fn. Tests: BE 15/15
(incl. double-count + no-silent-FX), FE 6/6, parity gate green.

**V1 — runtime walk (Tier 3-4), servers live on :8000/:3005, test-user
session.** Flows exercised live: commission ingest → link → record →
re-record guard (all green; `backend: memory` is the correct dev default —
production is startup-asserted to SQL); IRROPS report → radar; agency API
key mint → provenance envelope read → bogus/no-key 401 fail-closed; memory
adopt (honest 404 no-profile); quotes (honest quote_ready=false).
**Runtime defect found + fixed + re-verified live:** the IRROPS report
stored the raw IRROPS payload whose keys (flight_ref/trigger_kind/severity)
don't match the radar's DisruptionAlert contract (flight_number/
disruption_type/urgency_level) — /alerts silently skipped every reported
row. Report endpoint now writes the radar-shaped superset; radar renders the
alert live (CANCELLATION CRITICAL AI-472, ACTIVE). Radar-integration keys
pinned in tests/test_irrops_ingest.py. Also found: the long-running backend
was pre-wave code (missing /record) — restarted on current tree.
**FND-0403 opened:** analytics endpoints 30s+/call at runtime (decryption
spam per encrypted trip row; degrades under parallel load) — pre-existing
perf problem, blocks browser render of Insights (React Query aborts at 30s).

**V2 — visual captures.** Captured (Docs/sims/assets/):
`commission_tab_after_record_flow.png` (full flow through the real UI:
ingest → 2 rows → manual link → record → recorded badge `pay_5f4c7e6851a6`);
`suppliers_illustrative_tiers.png` (5 × "(illustrative)" labels live).
Blocked by FND-0403: Insights page render (commercial-evidence section is
suite-verified at Tier 2; browser capture pending the analytics perf fix).
Public-proposal native-currency capture also pending a priced proposal
token (needs a spine run on a real trip).

**V5 — Mimosa normal scan (sealed `scan-2026-11-06T17-33-21.052Z-a5c851b630c0`).**
77 findings; cross-referenced against the wave's 132 changed files: **zero
findings in wave-changed code.** The 5 HIGH path-traversal hits are on
`src/decision/cache_storage.py` (untouched 2026-09 module, name-collision on
"decision" with `src/intake/decision.py`'s message-copy-only diff); remaining
classes (23 insecure-randomness, 40 path-traversal, 8 ssrf, 2 hardcoded-cred)
match the documented prior-wave triage patterns (test fixtures,
sanitizer-invisible, FND-0374/0383/0394 posture). Advisory snapshot: 6
packages matched / 41 advisories offline — same pip-audit posture as the
TRV-DP-06 D1 wave.

## V3/V4 compact closeout + final regression (2026-11-07)

Background reviewer agents hit the concurrency limit — review executed inline.

**V4 contract review (2-cycle, inline):**
- `/keys` middleware-exemption check: POST /keys without JWT → 401 live
  (route-level get_current_agency enforces JWT despite PUBLIC_PREFIXES
  skip — defense-in-depth holds; /summary without X-API-Key → 401 live).
- record_fact_override ValueError → 500 risk: unreachable — manual_override
  (rank 1) cannot conflict with any stored authority; only rank>1 writers
  could conflict and all such callers use try_* (public_asks, memory adopt).
- trip_lifecycle_service.py authority read-list covers manual_override
  (replay-baseline set) — consistent with the new write levels.
- Cycle 2: 409 error path carries backend detail; success path claims only
  on valid accepted payload (Part-J #8); idempotency marker is stable within
  the report window (hour granularity) — tested.

**V3 sim pass (inline, per persona):** operator flows survive day-1 use
(intake hand-off requires zero new clicks; commission record requires only
advisor ID input). Red-team residuals: (1) ingest batch store is in-process
— a backend restart mid-review loses the batch (FND-0396 class, acceptable
for preview-grade per D4, revisit if operators hold batches open); (2)
advisor_id is free-text — no validation against the agency roster (P3,
 revisit at pilot); (3) reacceptance banner requires backend
requires_reacceptance (verified wired).

**Final regression:** backend **5,879 passed / 56 skipped / 0 failed**
(route snapshots regenerated for /record); FE **199 files / 1,491 tests
passed**; tsc clean; parity + inventory gates green; findings store
validated 0 warnings (FND-0398/0402 closed, FND-0403 opened: analytics
30s+ latency — P1, pre-existing, blocks Insights browser render).

## Sim-pass integration (2026-11-07)

Persona sim (PER-1098 + PER-0468) returned 4 findings across the new surfaces.
**Fixed immediately (all suite-verified):**
1. **Prefill consume-and-drop (P1 data loss):** IntakeTab now appends the
   channel message beneath a labeled separator when a draft exists — draft
   AND message both survive.
2. **Fuzzy-match one-click payout (money safety):** difflib matches are now
   suggestion-only (manual_candidate + `fuzzy_suggestion` method + suggested
   trip in raw_text) — recording requires explicit operator link-confirm.
   Pins updated in tests/test_commission_ingest.py.
3. **Confidence clause removed from public proposal:** internal planning
   confidence is an agent-model metric — never rendered to travelers (test
   file rewritten to the no-confidence contract).

**Filed:** FND-0404 (batch durability + re-open UI), FND-0405 (IRROPS
operator entry point + resolve action; single-slot overwrite), FND-0406
(inbox feed one-shot).

**Final regression after sim fixes:** backend 5,912 passed / 0 failed
(+1 known trim flake passing in isolation); FE 199 files / 1,491 passed;
tsc clean.

## Contract-review fixes (2026-11-07) — final state

2-cycle review delivered 2 P1 + 2 P2 + 4 P3; **all fixed, all suite-verified:**
- **R1 (P1)** budget dual-write through ranked writer (manual_override via
  explicit_fact_override, FND-0368 parsed-numeric propagation preserved) —
  exposed + fixed a latent read-path gap: resolve_trip_field budget branch
  now normalizes currency symbols/commas before parse_budget (operators'
  "$8,500"-style raw text previously zeroed the ranked read).
- **R2 (P1)** durable double-record guard: deterministic payout_id
  `stmt-{batch}-{row}` + pre-check + duplicate-catch via get_payout —
  multi-worker/restart can no longer double-record.
- **R3 (P2)** dependent invalidation skips dependents held above incoming
  authority (no silent downgrade of operator-corrected derived slots).
- **R4 (P2)** `explicit_user_raw` added to AuthorityLevel.RANK (read-compat
  only, NOT in FACT_LEVELS — legacy rows read at rank 2, never re-writable).
- **R5 (P3)** quotes dead conditional removed; producer-disable now warns;
  commission /record maps revalidation ValueErrors → 4xx not 500.

**Final regression:** backend 5,912 passed / 0 real failures (1 order-
pollution flake passes in isolation); FE 199 files / 1,491 tests passed;
tsc clean; findings store validated. Sim-pass follow-ups: FND-0404/0405/0406.

## Sim-followup build (2026-11-07) — FND-0404/0405/0406 done, 0403 narrowed

- **FND-0406 CLOSED:** inbox feed loads via useCallback + manual Refresh
  button + 15s poll (no longer one-shot). FE 6/6 + tsc.
- **FND-0404 CLOSED:** batches persist to `data/commission_batches/*.json`
  on every mutation, lazily reloaded on get miss (restart/reload no longer
  orphans manual links); GET /ingest list endpoint; FE recent-batches
  reopen list. Disk round-trip + tenant-scoping test 16/16. Money-truth
  boundary unchanged.
- **FND-0405 CLOSED:** POST /disruptions/{trip_id}/resolve archives the
  provenance row to disruption_history and clears the radar slot; 13/13
  BE tests. Operator UI: IrropsReportSection on trips/[tripId]/ops —
  report form + active-alert resolve; ops suite 9/9; tsc clean.
- **FND-0403 NARROWED:** decrypt log-storm eliminated (counter + aggregate
  warning in src/security/encryption.py); analytics direct 30s+ → ~12s,
  decrypt-spam 1000s → 9 lines. Browser still aborts: 5 parallel calls
  queue behind the sync worker — residual = per-trip serial aggregation,
  needs caching/pre-aggregation. REMAINS OPEN, narrowed scope.
