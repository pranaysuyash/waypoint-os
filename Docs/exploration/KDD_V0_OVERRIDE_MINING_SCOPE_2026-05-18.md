# KDD v0 — Override-Mining Prototype Scope

**Date**: 2026-05-18
**Status**: Scoped, ready for implementation handoff.
**Parent**: [KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md](KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md)
**Implementation owner**: Claude (handoff)
**Estimated effort**: 2-3 days of focused work
**Kill criterion** (carried from parent): if after 4 weeks of operation no mined pattern has driven a concrete prompt/validator/UI change, scrap and revisit.

---

## 1. Goal

Build the smallest end-to-end loop that:
1. Reads operator override events from the existing audit trail.
2. Extracts structured features `(ai_decision, operator_decision, intake_features)`.
3. Clusters overrides per agency on a rolling window.
4. Surfaces clusters of size ≥ N as a weekly digest with support / sample size labels.
5. Provides a single human-facing review surface where an operator or internal reviewer can mark a cluster as "actionable", "noise", or "already fixed".

**Non-goals (explicit)**: no model fine-tuning, no automatic prompt edits, no cross-agency mining, no real-time scoring, no new audit instrumentation, no UI beyond the digest review surface.

## 2. Why v0 (Recap)

- Override corpus already exists in `AuditLog` (`spine_api/models/audit.py`).
- Single-digit-N clusters are still informative (3 identical overrides = systematic miss).
- Directly feeds the AI-override-controls launch blocker called out in AGENTS.md.
- Defers every higher-N application (association rules, suitability mining, anomaly detection) until v0 proves the loop is consumed.

## 3. Data Surface (Already Exists — Do Not Duplicate)

| Element | Location | Notes |
|---|---|---|
| `AuditLog` ORM model | [spine_api/models/audit.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/models/audit.py) | Has `action`, `resource_type`, `resource_id`, `changes` (JSON dict), `agency_id`, `user_id`, `created_at`. Sufficient for v0. |
| `AuditAction` enum | same file, line 42 | Confirm override-related action values are stable; extend only if v0 surfaces a real gap. |
| `AuditStore` | [spine_api/persistence.py:1605](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py#L1605) | Existing reader/writer. v0 reads only. |
| Audit → timeline mapper | [src/analytics/logger.py:164](file:///Users/pranay/Projects/travel_agency_agent/src/analytics/logger.py#L164) | Reference implementation for how to consume audit events. |
| Trip lifecycle override flows | [spine_api/services/trip_lifecycle_service.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/trip_lifecycle_service.py), [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py) | Where overrides originate. Read to understand decision shape; do not modify. |
| Intake features | `Validation`, slot extraction outputs on the trip | Use what's already persisted on the trip; do not add new extraction. |

**Hard rule**: v0 reads from existing tables only. No schema migrations except those listed in §6.

## 4. v0 Pipeline

```diagram
╭─────────────────────╮     ╭──────────────────────╮     ╭────────────────────╮
│ AuditLog            │────▶│ Override feature     │────▶│ Cluster job        │
│ (filtered to        │     │ extractor            │     │ (per agency,       │
│  override actions)  │     │ (pure function)      │     │  rolling 30d)      │
╰─────────────────────╯     ╰──────────────────────╯     ╰─────────┬──────────╯
                                                                   │
                                                                   ▼
                                            ╭──────────────────────────────────╮
                                            │ kdd_override_clusters table      │
                                            │ (versioned, with support, sample │
                                            │  size, mined_at, window)         │
                                            ╰─────────┬────────────────────────╯
                                                      │
                                                      ▼
                                            ╭──────────────────────────────────╮
                                            │ /api/kdd/override-digest         │
                                            │ (read-only, role-gated)          │
                                            ╰─────────┬────────────────────────╯
                                                      │
                                                      ▼
                                            ╭──────────────────────────────────╮
                                            │ Digest review UI                 │
                                            │ (actionable / noise / fixed)     │
                                            ╰──────────────────────────────────╯
```

## 5. File-Level Plan

### Backend (new)
- `src/analytics/kdd/__init__.py`
- `src/analytics/kdd/override_features.py` — pure functions: `extract_features(audit_event, trip_snapshot) -> OverrideFeatureVector`. No I/O, fully unit-testable.
- `src/analytics/kdd/clustering.py` — `cluster_overrides(vectors, min_cluster_size=3) -> list[OverrideCluster]`. Start with `sklearn.cluster.HDBSCAN` if it's already in the dependency tree; otherwise k-means with elbow heuristic. Justify the pick in the docstring; no new heavy dependency.
- `src/analytics/kdd/jobs.py` — `run_override_mining_job(agency_id: UUID, window_days: int = 30, now: datetime)` — composes feature extract + cluster + persist. Pure orchestration; testable with fake stores.
- `spine_api/routers/kdd.py` — `GET /api/kdd/override-digest` (read), `POST /api/kdd/override-digest/{cluster_id}/review` (label as actionable/noise/fixed). Owner/admin only via `require_permission`.

### Backend (existing — read or extend)
- `spine_api/persistence.py` — add `KDDOverrideClusterStore` next to `AuditStore`. Do not modify `AuditStore`.
- `spine_api/models/` — add `kdd.py` with `KDDOverrideCluster` ORM model. No changes to existing models.

### Schema (one migration)
- `alembic/versions/<ts>_add_kdd_override_clusters.py`. Creates one table. No changes to existing tables. RLS policy mirrors `audit_log` (per-agency isolation).

### Frontend (smallest possible)
- `frontend/src/routes/(app)/kdd/digest/+page.svelte` (or the equivalent in the actual framework) — list view, per-cluster card with representative override sample, support, sample size, three review buttons.
- One BFF proxy route at the canonical location; **do not** create a parallel API route.

### Tests
- `tests/analytics/kdd/test_override_features.py` — feature extraction unit tests with fixtures.
- `tests/analytics/kdd/test_clustering.py` — deterministic clustering tests on synthetic vectors.
- `tests/analytics/kdd/test_jobs.py` — end-to-end with in-memory fakes.
- `tests/api/test_kdd_router.py` — auth scoping, agency isolation, schema contract.

## 6. Schema (one table, additive)

```sql
CREATE TABLE kdd_override_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    mined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    algorithm TEXT NOT NULL,           -- e.g. "hdbscan-v1"
    feature_version TEXT NOT NULL,     -- bumped whenever extract_features changes
    cluster_label TEXT,                -- human-meaningful short label, nullable until labeled
    sample_size INT NOT NULL,          -- number of overrides in this cluster
    support FLOAT NOT NULL,            -- sample_size / total_overrides_in_window
    representative_sample JSONB NOT NULL,  -- 3 anonymized example overrides
    feature_centroid JSONB NOT NULL,   -- centroid vector for debugging
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
        -- one of: unreviewed | actionable | noise | already_fixed
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    review_note TEXT
);

CREATE INDEX idx_kdd_override_clusters_agency_mined
    ON kdd_override_clusters (agency_id, mined_at DESC);
```

**Why these columns**:
- `feature_version` so we can re-mine deterministically after schema changes without losing history.
- `representative_sample` so the digest is reviewable without joining back to audit_log.
- `review_status` is the only mutable column post-write; everything else is append-only.
- `support` + `sample_size` are surfaced in the UI so reviewers never trust a pattern blindly.

## 7. Job Trigger

v0 trigger: cron-equivalent on existing scheduler infra (do not add a new scheduler). Frequency: weekly per agency. If no scheduler exists, expose a CLI entrypoint at `scripts/run_kdd_override_mining.py` and document manual invocation; do not stand up new infrastructure for v0.

## 8. Acceptance Criteria

A reviewer can call v0 done when **all** of the following hold:

1. `GET /api/kdd/override-digest` returns at least one cluster on a seeded dataset of ≥10 synthetic overrides exhibiting two distinct failure modes.
2. Tests cover: feature extraction edge cases, clustering determinism on fixed seed, agency isolation in the API, RLS scoping in the DB.
3. The digest UI renders the cluster, its sample, and the three review buttons; clicking each button persists the label.
4. A second mining run on the same window produces stable cluster IDs *or* (more honestly) versioned cluster rows linked by `feature_centroid` proximity — pick one and document.
5. No new dependency heavier than scikit-learn (which may already be present).
6. No modifications to `AuditLog`, `AuditStore`, or any existing router.
7. Migration applies cleanly forward and rolls back cleanly.
8. AGENTS.md "test schema validation" rule satisfied: the digest UI is tested against a real backend response, not a mocked one.

## 9. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Low N → noisy clusters | `min_cluster_size=3` floor; surface sample size next to every cluster; reviewers can mark "noise". |
| Override action taxonomy is inconsistent | v0 just reads what's there; surfaces inconsistencies as a finding rather than silently normalizing. |
| Cluster IDs churn between runs | Documented explicitly; either pinned via centroid similarity or accepted as versioned snapshots. |
| Privacy: representative samples may contain PII | Anonymize at extraction time; redact free-text fields; only structured features go into centroids. |
| Premature commitment to an algorithm | `algorithm` and `feature_version` columns make it cheap to switch in v0.1 without losing history. |
| Becomes a vanity dashboard | Kill criterion in §1 — 4 weeks, zero downstream changes, scrap. Reviewer is on the hook to enforce. |

## 10. Out of Scope for v0 (Will Be Tempting — Resist)

- Cross-agency mining.
- Association rules over gate failures (parent doc §4.2 — separate v0.5).
- Suitability signal mining (parent doc §4.3 — separate workstream tied to the renderer).
- Process mining on timelines (parent doc §4.4).
- Automatic prompt-update PRs.
- Slack/email digest delivery.
- Time-series of cluster evolution.

Add any of these only after v0 has cleared its kill criterion.

## 11. Handoff Notes for Claude

- Follow the canonical pipeline / no-duplicate-routes rule in AGENTS.md. There is one new router (`/api/kdd/override-digest`) — extend with new HTTP methods rather than creating sibling files.
- All new code must run the test schema validation pattern from AGENTS.md (`curl` the real endpoint, then write the frontend against the verified shape).
- Use shared validation stack. No ad-hoc `request.json()`.
- Use `slots=True` dataclasses where applicable per AGENTS.md performance patterns.
- Preserve existing audit code intact. No reformatting drive-bys.
- Verify with: `uv run pytest tests/analytics/kdd tests/api/test_kdd_router.py` and the frontend's targeted vitest run.
- Open question to resolve before coding: confirm the exact `AuditAction` enum value(s) that represent operator overrides. Read `src/intake/decision.py` and `spine_api/services/trip_lifecycle_service.py` to ground this; do not guess.

---

*Scope locked at v0. Any expansion requires returning to the parent exploration doc and updating the ranking, not extending this scope inline.*
