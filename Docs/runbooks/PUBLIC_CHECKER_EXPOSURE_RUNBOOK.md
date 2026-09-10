# Runbook — Public Checker Exposure (GO punch-list)

**Status:** ready; execution gated on the owner's exposure-scope choice (hold / checker-only GO / GO + spend-test).
**Scope:** checker-only exposure — this runbook does NOT flip the platform `LAUNCH_STATUS.md` NO-GO.
**Owner:** Pranay · **Last validated:** never (validate on first real deploy; see §7).

## 1. Purpose

Open the public itinerary checker to real internet traffic as a standalone, scoped surface: honest Manifest page, sealed funnel metrics, matched-choice marketplace in waitlist mode, 90-day retention, kill switch available at runtime.

## 2. Prerequisites (all built; verify at deploy)

- Honest page + signed-off disclaimer (owner-approved 2026-09-09)
- Kill switch: `PUBLIC_CHECKER_ENABLED` (call-time read; 0 → 503 everywhere + maintenance page)
- Abuse caps: 12/min run, 30/min events+trips-reads, 6/min route-request+re-verify, payload caps
- Sealed funnel: `check_completed` server-emitted only (client POST → 403)
- Erasure: capability tokens issued per run (hashed at rest); token routes under `/api/public-checker/trip/`
- Ghost Hotel entity checks: advisory-only, fail-open (Open-Meteo + OSM Nominatim egress)

## 3. Environment

fly.toml `[env]` carries: `PUBLIC_CHECKER_ENABLED=1`, `PUBLIC_CHECKER_RETENTION_DAYS=90`, `PUBLIC_CHECKER_RETENTION_SWEEP_ENABLED=1`, `PUBLIC_CHECKER_RETENTION_SWEEP_HOURS=24`, `ENTITY_CHECK_ENABLED=1`.

Secrets (never in fly.toml):

```bash
fly secrets set PUBLIC_CHECKER_AGENCY_ID=<dedicated-uuid> \
                DATABASE_URL=... JWT_SECRET=... PROPOSAL_SIGNING_KEY=... \
                SPINE_API_CORS=...
```

Frontend: `NEXT_PUBLIC_SITE_URL=https://<host>` (robots/sitemap), `NEXT_PUBLIC_PUBLIC_CHECKER_DISABLED=0`.

## 4. Deploy steps (ordered)

1. Provision the checker agency on the target DB:
   `TRIPSTORE_BACKEND=sql DATABASE_URL=... python scripts/bootstrap_public_checker_agency.py`
   → seeds the agency row + a placeholder marketplace profile (edit `data/agency_marketplace/profiles.json` fields — places, customer types, services — before traffic; matched-choice only shows scored > 0 matches).
2. `fly secrets set ...` (§3) → `fly deploy`.
3. Verify: `curl -s https://<host>/ready` → 200; `POST /api/public-checker/run` with a sample plan → `trip_id` + `access_token`; `GET /api/public-checker/trip/<trip_id>` with Bearer → 200; without → 403; `POST /api/public-checker/events` with `check_completed` → 403 (sealed-counter check).
4. Deploy the frontend with robots.ts/sitemap.ts live; verify `/<host>/robots.txt` and `/sitemap.xml` include `/itinerary-checker`.

## 5. Agency receiver onboarding (waitlist → routed)

1. Agree scope with the agency (they receive waitlist briefs for covered places/customer types).
2. Create/verify the agency row; run the bootstrap with `PUBLIC_CHECKER_AGENCY_ID=<their-uuid>` if a new checker agency is wanted.
3. Seed their marketplace profile (bootstrap does it automatically; else upsert into `data/agency_marketplace/profiles.json`): places_covered, customer_types, services, languages, response_sla_hours.
4. Agree the Cold Open first-message rule (free partial fix of one flagged day; never a call) — that behavior lives with the agency, not the code.

## 6. Kill switch / rollback

- Runtime kill: `fly env set PUBLIC_CHECKER_ENABLED=0 && fly deploy` → all checker endpoints 503 + frontend maintenance page. No code change.
- Full rollback: `fly deploy --image <previous>`; frontend ships independently.

## 7. Monitoring / validation

- Sealed funnel: `data/product_b_events/` `check_completed` counts (server-emitted only; client-fed events are quarantined from KPI truth per RDA_EX03).
- Retention: sweep thread runs daily (log absence of `product_b_event_log_failed`/sweep exceptions); `route_leads.jsonl` for captured demand.
- Nominatim/Open-Meteo egress: capped by per-run entity cap (3) + 1 req/s limiter + 6h cache.
- **Validate this runbook on first real deploy** and stamp the date here: ____________

## 8. Known boundaries

- SQL-side trip deletion is not implemented (file-store sweep v0; SQL lifecycle = durable-store endgame E-G). On SQL backends the sweep prunes tokens/segments only — trip rows need the E-G migration or manual SQL.
- Re-verification is on-demand only; scheduled per-trip re-checks wait for exposure data.
- `NEXT_PUBLIC_PUBLIC_CHECKER_DISABLED=1` is the frontend half of the kill switch (bakes at build); the backend 503 is the authoritative runtime gate.
