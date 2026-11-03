# Re-baseline Evidence — Council Tranche Wave (2026-11-03)

**Purpose:** verified current-state before the build wave ordered by the owner
(2026-11-03: "everything gets built; no waiting on onboarding"). Supersedes the
stale gap claims in `COUNCIL_LAUNCH_READINESS_PRODUCT_2026-09-29.md` and the
ledger claim in `COUNCIL_LAUNCH_READINESS_2026-10-21.md` §S5. Evidence tier:
Tier 1 static inspection by two independent Explore agents + targeted test run;
file:line cites below.

## STALE-CLAIM CORRECTIONS (verified observed)

1. **Commission/payout ledgers are NOT purely in-memory.**
   `spine_api/services/advisor_payout_store.py:94` (`AdvisorPayoutStore`) +
   `commission_reconciliation.py:62-65` (SQL backend when
   `advisor_payout_store.backend() == "sql"`; `_sql_ledger` durable=True,
   agency_id mandatory :137-172). In-memory `ADVISOR_LEDGERS` remains the
   non-SQL default path (:37). → T3 = posture audit/flip, not greenfield.
2. **A tax compliance engine already exists**: `src/fees/tax_compliance.py`
   (`TaxComplianceEngine` :104; TCS §206C(1G) ₹7,00,000/5%-20% tiers :109 —
   STALE per `Docs/research/INDIA_COMPLIANCE_RATES_TCS_GST_2026-11-03.md`;
   GST `TOUR_PACKAGE_5PCT`/`SERVICE_FEE_18PCT` :27-29); router mounted
   `server.py:1682`. `TripQuoteView.tax_percent` producer absent by design
   (`contract.py:1674` "None = no persisted tax producer; never a default").
   → T6 = extend canonical engine (doctrine §5) + wire producer.
3. **FE gap-2 items already resolved** (from 2026-09-29 council): intake routes
   unified via redirect (`workbench/page.tsx:1-26` → `/inquiries/new`),
   DecisionPanel mounted (`workbench/PageClient.tsx:70-72,904`),
   `/quotes` real read model (`quotes/PageClient.tsx:8-11`), reject reason
   capture real (`reviews/PageClient.tsx:182,202,214`), A1/A7 breadcrumbs fixed,
   ChannelMessagesPanel live in inbox (`inbox/PageClient.tsx:25,468`),
   `/a/[token]` traveler ask loop live (`a/[token]/page.tsx:42,73`;
   `public_asks.py:154,178`).

## REMAINING DELTAS (verified absent — the actual build scope)

- **T2 operator-surface:** IntakeTab still paste-only (`IntakeTab.tsx:209-215`);
  no message→intake hand-off; attachments unviewable (inbox PageClient has no
  attachment render); no operator share-link UI for asks (DecisionPanel renders
  questions only, `DecisionPanel.tsx:389-405`); A5 WelcomeModal still mounted
  (`AuthProvider.tsx:20,193`); `RouteMapStudio.tsx` orphaned (0 importers).
- **T3 money:** in-memory ledger default path — SQL posture audit + flip.
- **T4 fact store:** `resolve_field_merge` exists (`field_merge.py:166-179`);
  `_preserve_authoritative_facts` (`persistence.py:4022`, authority set :4018).
  Roadmap inv-2 remaining: merge generalization, memory→intake U13,
  follow-ups-from-merged-view invariant test. "Display columns" verified absent.
- **T5 R2-B:** `commission_reconciliation.py` = per-advisor ledgers + tiers +
  `reconcile_trip_commission` (:253, $0.01 tolerance). Missing: CSV/image/email
  ingest + fuzzy supplier match + manual-link fallback (Travefy bar).
- **T6 R2-C:** engine rate tables stale (see research doc); no tax producer
  wiring into TripQuoteView; FE has no compliance display.
- **T7 gap-4:** public proposal has stated-requirements render (de-attributed
  by design, `p/[token]/page.tsx:266-284`) + demo badge; **why-this-option
  rationale absent from public page**; repair banner w/ field names absent from
  public page; per-traveler attribution deliberately de-attributed (privacy —
  design decision recorded in T7).
- **T8 R2-F:** `/api/v1/inbox/stats` exists (`inbox.py:114`); insights agent
  drill-down exists (`insights/PageClient.tsx:315,342-348`); named
  agent-resolved-share KPI absent.
- **T9:** watcher taxonomy has pre+post-booking fare-drop triggers
  (`src/agents/runtime.py:2918-2934`); IRROPS semantics doc absent.
- **T10 R2-A:** no external API-key auth (verified absent); JWT `_auth_or_skip`
  house dependency is the auth pattern (`core/auth.py:28-40`).

## DRIFT LEDGER (shared-tree in-flight work)

- `spine_api/routers/destination_intelligence.py` (untracked) + mount in
  uncommitted `spine_api/server.py:1708` + 6/6 passing tests
  (`test_destination_intelligence_router.py`): **complete-and-healthy**.
  Preserved; owner commit pending (commit authorization is owner-only).
- `Docs/review/COUNCIL_NEXT_TRANCHE_SEQUENCING_2026-11-03.md` (this wave's
  council record) untracked by design.

## Test baseline

- `uv run pytest tests/test_destination_intelligence_router.py -q` → 6 passed
  (Tier 2/S1).
- FE `npx tsc --noEmit` → PASS.
- Canonical full suite: `uv run pytest -q` (last recorded 4 pre-existing
  rate-limiter failures / 1595 passed per ANALYTICS_PROGRAM_TRACKER.md:147).
