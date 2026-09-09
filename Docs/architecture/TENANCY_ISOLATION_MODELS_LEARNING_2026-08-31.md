# Tenancy Isolation Models — A First-Principles Learning Record (2026-08-31)

**Type:** Learning / design-knowledge doc (question from Pranay during the A-19 resolution, 2026-08-30)
**Trigger:** *"Would it have been first-principles, long-term, to have each client get their own DB? What about scalability, costs, infra?"* — asked right after A-19 found 44 of 50 routers relying on application-level tenant filtering instead of the enforced RLS path.
**TL;DR:** For Waypoint OS, shared schema + RLS was and remains the right architecture. The audit failure was **enforcement debt**, not a wrong isolation model. The first-principles rule the question exposes: *an isolation guarantee must live in the layer that cannot forget.*

---

## 1. First principles: where does the guarantee live?

The requirement is one sentence: **agency A must never read or write agency B's data.** Architecture gives you three layers that can hold that guarantee, in increasing strength and increasing cost:

| Layer | Mechanism | Failure mode |
|---|---|---|
| **Application discipline** | Every query remembers `WHERE agency_id = :current` | A developer forgets one clause. One time in 50. (This exact thing happened — A-19.) |
| **Database enforcement (RLS)** | Postgres row-level security policies keyed on a session variable; wrong-tenant rows are invisible even to a forgotten-WHERE query | Misconfiguration: policies dormant (owner-role bypass), session variable bleeding across pooled connections |
| **Physical isolation (DB-per-tenant)** | Tenant data lives in a separate database; pointing at the wrong tenant yields *zero rows, full stop* | Operational disease: migrations × N tenants, connection explosion, cross-tenant features become federation projects |

The extreme version of layer three's opposite is **Salesforce**: the most successful multi-tenant system ever built runs *one* shared store where raw SQL is made impossible by a governance layer — tenants *cannot* express a cross-tenant query because the query language itself is tenant-bounded. The lesson from both ends is the same and is the core takeaway:

> **Make the safe path the default path, and make the unsafe path impossible — not merely discouraged.**

## 2. The models, compared honestly

| Dimension | Shared + app filtering | Shared + RLS *(this repo)* | Schema-per-tenant | DB-per-tenant |
|---|---|---|---|---|
| Isolation strength | Weakest (discipline) | Strong *when enforced*; dormant if owner-bypass | Strong (namespace) | Strongest (physical) |
| Connection cost | 1 pool | 1 pool | 1 pool | N pools → pgBouncer mandatory; transaction-pooling breaks session state (incl. RLS session vars!) |
| Migrations | 1× | 1× | N schemas, 1 engine | **N databases** — drift is the notorious disease |
| Cross-tenant features | Easy | Easy (policies can be scoped) | Painful | Federation projects |
| GDPR erasure | DELETE + tombstones in audit trail | Same | DROP schema | `DROP DATABASE` — the cleanest story |
| Breach blast radius | All tenants | All tenants (rows) | One tenant | One tenant |
| Ops surface | Small | Small | Medium | Linear in tenants |
| Scale path | Shared | Shared → replicas → Citus (partitions **by tenant_id** — the model already matches) | pg_catalog bloat | Horizontal for free, cross-tenant caps |
| Cost at 20–200 tenants | Lowest | Lowest | Medium | High (ops, not storage) |

> **⚠️ Live correction (2026-08-31, same day):** subtlety 1 below was written from the
> audit's Tier-1 reading and is **wrong for this repo's FORCE-RLS tables**. `pg_class`
> verification shows `trips` and `booking_collection_tokens` carry
> `relforcerowsecurity = true` — the owner does NOT bypass, RLS is enforcing *now*,
> and the policies are fail-closed (no context ⇒ zero rows). The real hazards this
> exposes: (a) unscoped endpoints only "worked" via stale session context bleeding
> through pooled connections (cleaned by `get_rls_db`'s exit-reset — until the next
> request needs it), and (b) commit-then-refresh flows break when the session
> re-checks out a fresh connection (fixed: flush → refresh → commit in
> `collection_service` / `document_service`). Subtlety 1's *general* lesson stands —
> verify enforcement empirically (pg_class, not docs) — but this repo's FORCE tables
> are the counter-example to "RLS here is dormant".

Two subtleties worth internalizing:

1. **"Shared + RLS" only protects if RLS is live.** This repo's tables use ENABLE-without-FORCE RLS and the app connects as the table *owner* — and owners bypass ENABLE RLS. So RLS here is currently *dormant defense-in-depth*: the active guard is application filtering, and RLS becomes real armor only at a **non-owner-role cutover**. A dormant safety system that everyone believes is active is itself a risk (the audit's "13/14 nav modules active" claim was the same disease in a different organ).
2. **Database-per-tenant's connection story eats its own isolation story.** Pooling N tenants' connections forces transaction-pooling mode, which discards session state — the very mechanism (`SET app.current_agency_id`) that shared+RLS relies on. The models are less independent than they look.

## 3. Evidence from this repo (why the question was smart — and why the answer is "no")

- **A-19 (2026-08-29/30):** 44/50 routers used the unscoped session. That is the strongest argument *for* per-tenant DBs — application discipline did, in fact, forget. But the resolution (converting 5 routers, documenting auth.py, adding cross-tenant probes + a CI coverage checker) cost ~a day. Migrating to DB-per-tenant would have cost months and bought isolation the product's threat model doesn't require at the current stage.
- **A-20 (2026-08-30):** with **one** database, four tables silently missed their migrations and their endpoints were runtime-broken. Migration drift is already a live failure mode here — under DB-per-tenant it multiplies by tenant count and becomes per-tenant drift, the hardest operational disease in that model.
- **The product is cross-tenant by ambition:** the federated intelligence pool (anonymized cross-agency risk data — `source_agency_hash`, no raw agency linkage), market-level yield benchmarks, and the intelligence graph are all natural in a shared store and all become federation projects in silos. The ICP (many small-to-mid agencies, not a few giant regulated ones) points the same way.
- **The failure class the question worries about is now CI-enforced closed:** `scripts/check_rls_coverage.py` (every `agency_id` table protected or exempt-with-reason), `get_rls_db` as the default dependency, and HTTP cross-tenant probes (`tests/test_cross_tenant_router_probe.py`). Enforcement debt was paid down once, mechanically, instead of being paid forever via architecture.

## 4. The long-term shape (recommendation)

1. **Now/default:** shared schema + RLS, non-owner-role cutover so defense-in-depth becomes live defense (the flagged re-verification trigger in `review/A19_RLS_COVERAGE_RESOLUTION_2026-08-30.md`).
2. **At scale:** read replicas, then Citus/sharding **partitioned by `agency_id`** — which is per-tenant isolation and horizontal scale arriving *inside* the shared model, with zero data-model change. The escalation path is already aligned.
3. **Enterprise tier (when someone pays for it):** the hybrid — connection-layer routing pins flagged tenants to dedicated databases on the same codebase. "Your data is physically isolated" becomes a pricing tier, not an architecture decision made prematurely on day one. This is the pattern most mature B2B SaaS converge on.

## 5. When DB-per-tenant WOULD be the right answer

A decision guide, so this doc generalizes beyond this repo:

- **Few, large, regulated tenants** (medical, legal, finance) where a customer's security review demands physical isolation and will pay for it.
- **Isolation is the product** (multi-tenant hosting platforms, government clouds).
- **Per-tenant restore/export is a hard requirement** (erasure = drop; point-in-time restore per client).
- **Tenants are huge and independent** (each needs different schema/extensions/versions anyway).
- You accept and staff for: migration tooling across N databases, connection-routing infrastructure, and the loss of easy cross-tenant analytics.

## 6. Generalized lessons (the part worth remembering)

1. **Guarantees live in layers that cannot forget.** Every "remember to do X" security control degrades; count how many call sites must remember, and assume one will fail.
2. **Distinguish enforcement debt from architecture debt.** This was the former. Rewriting architecture to escape an enforcement failure doubles the debt.
3. **A dormant safety system is a belief hazard.** RLS that "exists" but isn't binding is worse than none, because it's cited as protection. Either make it live (role cutover) or label it loudly (the exemption dict now does).
4. **Proof beats posture.** The coverage checker + probes convert "we're isolated" from a claim into a CI result.
5. **Ask the opposite before scaling the current answer.** "Should this have been per-tenant DBs?" was the right question to ask right after finding the gap — asking it is what produced this record; the answer just happens to be no.

**Related:** `review/A19_RLS_COVERAGE_RESOLUTION_2026-08-30.md` (the resolved finding this question came from) · `EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` EX-05 (negative-space map) · `Docs/context/` multi-tenant roadmap (2026-04-23).
