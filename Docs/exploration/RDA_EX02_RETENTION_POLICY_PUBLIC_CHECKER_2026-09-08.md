# EX-02 — Retention Policy Research: Public-Checker Data (2026-09-08)

Status: research + proposal. Decision gate: D-03. Implementation: FT-06 (events, shipped) + a future trip-TTL job.

## Current state (verified 2026-09-08)

- Every public-checker run persists a full trip row unconditionally via `save_processed_trip(..., source="public_checker")` (`spine_api/services/public_checker_service.py:281-303`) — consent only gates the *raw text* stored in `meta.submission` (`spine_api/services/live_checker_service.py:76-83`) and the uploaded artifact files (`spine_api/persistence.py:2564-2566`, 10 MiB cap, `data/public_checker/uploads/`).
- Derived payloads (packet facts, validation, decision, scores) persist with no TTL anywhere. Repo-wide `rg "retention|TTL|cleanup|purge"` on persistence paths finds only the artifact consent check.
- Event store was append-only; FT-06 (shipped 2026-09-08) added segment rotation at `PUBLIC_B_EVENTS_MAX_BYTES` (default 10 MiB) — bounded size, not age.
- The only other GC in the repo covers `data/runs` (PA-12). No trip-row GC exists for any source.

## Constraints

1. **Storage limitation principle** (GDPR Art. 5(1)(e)) — data kept in identifiable form no longer than necessary. The checker collects traveler-supplied itineraries from anonymous users; indefinite retention is indefensible if the surface is ever exposed.
2. **Erasure interplay** — `DELETE /api/public-checker/{trip_id}` exists but is unreachable for anonymous users (401, middleware gap — AUD-04/FT-G2). Until capability tokens ship, a TTL is the *only* working deletion path for the target user.
3. **Analytics value** — KPI computations (`compute_kpis`) only read a 30-day window (`list_events(window_days=30)`); older events are dead weight for analytics. Trip rows feed no memory/pricing loop (EX-08: linkage never built), so their analytical value decays fast.
4. **All-TTL-not-partial rule** — a TTL on trips but not events (or vice versa) recreates the split-brain the data-safety rules warn about; policy must cover trips, event segments, and consented upload artifacts.

## Proposal (pending D-03)

| Surface | Retention | Mechanism |
|---|---|---|
| Public-checker trip rows | 90 days | Daily TTL job (extend the PA-12 ledger-GC pattern): delete `trips where source='public_checker' and created_at < now()-90d`, respecting the checker agency id |
| Consented upload artifacts | 90 days, cascade | Delete alongside the owning trip row |
| Event JSONL segments | 2 rotations (current + `.1`) | Already shipped via FT-06; add an age check on `.1` files (delete >180d) in the same TTL job |
| In-process idempotency keys | existing 30-min reclaim | unchanged |

Retention should be disclosed in the consent toggle copy ("stored ~90 days for product improvement"), which strengthens rather than weakens the consent's honesty.

## Open questions for D-03

1. 90/30/180-day defaults acceptable, or different numbers?
2. Does retention apply identically under Option B (agency-branded inversion, `WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md`)? Agency-branded reports may be business records the *agency* wants kept — inversion likely moves checker trips out of TTL scope.
3. Owner for the TTL job cadence: piggyback on the ledger-GC loop or a new scheduler entry?
