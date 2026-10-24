# Exploration: RAG / Embeddings / Vectors — Mount Readiness

- **Date:** 2026-10-22
- **Mode:** Exploration (no implementation this pass). Follows the DECIDE item from the determinism audit remediation ("RAG — mount the router … or archive").
- **Question:** What exactly exists in Waypoint OS's RAG stack, is it healthy, what would mounting it actually take, and what is worth stealing from the medpiper insurance app's (CoverWise) production retrieval stack?
- **Evidence tiers:** Tier 1 (code inspection, file:line) unless marked; Tier 2 (test run) for the health baseline. No provider calls were made.

---

## 1. What exists here (runtime truth)

The stack is **not a stub** — it is a complete, coherent, honestly-labeled hybrid retrieval engine, ~1.4k lines plus a router and 7 test modules. Nothing in it is fabricated; every approximation is labeled in its own docstring (the honesty doctrine predates my audit — someone built this right).

| Module | What it does | Notes |
|---|---|---|
| `src/rag/models.py` | Pydantic models: chunks w/ full provenance metadata (agency, source_type, page/line, tags, entity_references), knowledge nodes/edges (`destination`/`supplier`/`policy`/`niche`/`activity` × `SUITABLE_FOR`/`GOVERNED_BY`/`REQUIRES_VISA`/`PREFERRED_SUPPLIER`), hybrid query (alpha, top_k, filters), `GroundedAnswer` w/ citations + `must_confirm` | Domain-aware, not generic |
| `src/rag/store.py` | `SQLiteRAGStore` at `data/rag_store.db` — 3 tables (chunks/nodes/edges), **`agency_id` on every table and every query** (tenant isolation is real, application-enforced); cosine over JSON vectors; substring-count sparse heuristic explicitly labeled "not standards-compliant BM25" | Dimension-mismatched vectors silently score 0.0 (`store.py:26-27`) — see §3.1 |
| `src/rag/embeddings.py` | `HashEmbeddingProvider` (64-dim md5 word-buckets, deterministic, `is_semantic=False`); `SemanticEmbeddingProvider` (OpenAI `text-embedding-3-small`, 1536-dim, graceful fallback); `get_default_embedding_provider()` keyed on `RAG_EMBEDDING_PROVIDER` | OpenAI calls are raw `urllib` — no retry, no usage-guard, no `record_llm_call` forensics, no egress treatment (§3.4) |
| `src/rag/indexer.py` | Parent/child hierarchical chunking (2000/500 chars, paragraph-aware) | Sound |
| `src/rag/retriever.py` | `HybridGraphVectorRetriever`: dense + sparse → alpha-weighted RRF fusion → entity-match graph boost (×1.5 direct, ×1.25 one-hop) | Loads ALL agency nodes per query (`retriever.py:93`) — fine at seed scale |
| `src/rag/grounding.py` | Heuristic groundedness (retrieval score ×0.4 + answer↔chunk token overlap ×0.6), `must_confirm` flags, Markdown citation formatter | Explicitly "not calibrated confidence" |
| `src/rag/service.py` | `RAGService` facade: index / search / `query_and_ground` (pluggable generator with honest extractive fallback) | |
| `spine_api/routers/rag.py` | 5 endpoints (`/rag/query`, `/rag/documents/index`, `/rag/nodes` GET+POST, `/rag/edges` POST), `get_current_agency` auth, node/edge agency_id forced to caller | **Never registered in `server.py`** (mount list `server.py:1575-1689` has no rag). Docstring claims "multi-tenant RLS protection" — it is application-level filtering, not DB RLS (§3.5) |
| `src/intake/specialty_knowledge.py` | The ONE live hook: `identify_niche(text, agency_id, rag_service=None)` — called in the spine (`frontier_orchestrator.py:135`) **without `rag_service`** → keyword fallback always. `seed_rag_knowledge()` has zero callers | Silent `except Exception: pass` on the RAG branch (`specialty_knowledge.py:89-90`) |

**State:** `data/rag_store.db` does not exist — the store has **never been seeded or indexed in this checkout**. Health: all 7 test modules pass (18/18, Tier 2, 2026-10-22).

## 2. Why it was orphaned (supersession context)

The determinism audit classified it T5 "orphaned." The §6.1 abandonment test now has a cleaner answer: this is **wired-at-the-edges, empty-in-the-middle** — the service, auth, models, and tests were built (2026-09-04→14, per file mtimes), the intake hook was written to consume it, but the two last-mile joints (router registration + `rag_service` injection at the hook) and the seeding path were never finished. The module docstrings show active maintenance as late as Sep 14 (`retriever.py`, `embeddings.py`). This is last-mile-missing, not superseded: **finish-the-capability is the §6.1 verdict**, matching the owner's "mount it" directive.

## 3. Defects/gaps found during exploration (must fix as part of mounting, not after)

1. **[P2 — silent retrieval corruption] No embedding provenance or dimension guard.** Chunks store only `embedding_json`; neither model/version nor dimension is recorded. If `RAG_EMBEDDING_PROVIDER=openai` is set *after* documents were indexed with hash vectors (or vice versa), query vectors (1536-d) meet stored vectors (64-d), `cosine_similarity` returns 0.0 on the length mismatch (`store.py:26-27`), and the retriever **silently serves sparse-only results** — no error, no honesty marker. This is precisely the "deterministic code faking probabilism" family inverted: semantic retrieval silently pretending to work.
2. **[P3 — honesty] `identify_niche` swallows all RAG exceptions** (`except Exception: pass`, `specialty_knowledge.py:89-90`). Everywhere else in the codebase the pattern is abstain-with-reason (context_resolver, dispatch). Must log with reason when mounted.
3. **[P2 — latent, mounts with the router] No input caps or cost guard on `/rag/documents/index`** (arbitrary `text` length → unbounded chunking + one embedding call per chunk ≈ unbounded API cost) and `/rag/query` (unbounded query length). The public-checker DoS-cap lesson (`entity_checks.py` rate limiting) and `usage_guard` exist — the router predates/ignores them. Also `HTTPException(500, detail=str(e))` leaks internals.
4. **[P2 — egress boundary] `SemanticEmbeddingProvider` sends agency document text to OpenAI with no egress treatment** (no `prepare_egress_payload`/PII strip, no `record_llm_call` forensics, no usage/cost accounting). Agency policy docs and trip documents are exactly the corpus — this is an X-09-class decision, not a plumbing detail.
5. **[P3] Router docstring claims "RLS"** — it's app-level filtering. Fix the label, or make it actually RLS if/when the store moves to Postgres (see §5).
6. **[P3] No seeding path** — `seed_rag_knowledge` is dead code until something calls it (startup hook, admin endpoint, or on-first-query auto-seed are the options).
7. **[P3] SQLite single-writer posture** — fine for the current single-process serving model; document the constraint and the Postgres endgame link (`Docs/architecture/DURABLE_STORE_ENDGAME_2026-09-08.md`) rather than solving it now.

## 4. What CoverWise (medpiper insurance_app) does — transferable ideas, ranked

CoverWise runs a production retrieval boundary over insurance-policy wordings (`corpus_global/<market>/<lob>/<insurer>__<product>.pdf`). Its architecture directly answers the gaps above — and it **had the same disease**: a duplicate, unmounted RAG service, which they archived with a pointer (`DECISION_LOG.md` Decision 11, 2026-09-07) and replaced with one canonical `src/rag/pipeline.py`. Precedent: canonicalize-or-archive, never leave twins.

Ranked by value to Waypoint:

1. **Embedding contract, fail-closed** (`supabase_vector_store.py:29-42, 94-107`): every chunk row carries `embedding_model` + `embedding_version` + `embedding_dimensions`; upsert **raises** on missing model or wrong dimension; search **filters by model+version** and hard-pins 1536. This is the exact cure for §3.1 — adopt the pattern in `SQLiteRAGStore` (add columns/JSON fields + WHERE filtering; dimension check becomes a loud contract, not a silent 0.0).
2. **Retrieval audit, privacy-safe by construction** (`retrieval_audit_service.py`): one `retrieval_runs` row (query **hash** + length, strategy, top_k, embedding model/version, reranker, latency, cache_hit, failure_class) + bounded `retrieval_candidates` + `rag_answers`/`answer_evidence` rows — "the caller supplies only hashes and identifiers; this function never accepts raw text." Same philosophy as my `record_llm_call` (validated independently in two projects — strong signal it's the right shape). Waypoint's version writes to `llm.calls` log; a `rag_runs` SQLite table would make it queryable.
3. **Real FTS as the lexical leg** (`match_document_chunks_fts` RPC): Postgres full-text with owner filter vs Waypoint's substring-count heuristic. Cheap adaptation for SQLite: FTS5 virtual table — big precision win on the sparse leg with no new dependencies (sqlite3 ships FTS5).
4. **`source_text` vs `retrieval_text` separation** (`supabase_vector_store.py:61-64`): store both the verbatim source (for citations/grounding) and a retrieval-optimized rendering. Waypoint's grounding evaluator scores answer overlap against chunk content — separating these makes citations verbatim-provable while retrieval stays fuzzy.
5. **Adjacent-chunk expansion** (`get_adjacent_chunks`, `chunk_links` with deterministic `chunk_index±1` fallback): after retrieval, pull neighbors so grounded answers see whole sections. Waypoint's parent/child chunking gives the same structure for free (`parent_id` already stored — the expansion query is trivial).
6. **RAGAS-style eval with a gate** (`eval/ragas_eval.py`): fixed QA corpus file (`policy_qa_v1.json`) **including negative questions**, faithfulness/context-precision/relevancy, `--fail-under-faithfulness 0.80` CI gate. This is the KDD-ladder pattern applied to retrieval — the missing piece that would let a semantic provider flip on with an eval gate instead of vibes (mirrors ADR-008 §4.2's preconditions for the suitability scorer).
7. **Optional cross-encoder reranker** (`pipeline.py:211-220`): `ms-marco-MiniLM-L-6-v2` via sentence-transformers, graceful fallback to lexical when the lib is absent. Right for later — it adds a heavy dependency; note it, don't install it now.
8. **Corpus governance** (`corpus_global/NOTICE.md` + `manifest.json` with `license_class`: redistribution-safe vs LOCAL-EVAL-ONLY): matters the moment Waypoint indexes third-party content (supplier contracts, government advisories are already `DocumentSourceType`s).
9. **Private cache scope** (`cache_policy.py`): responses cached only when an owner/document boundary exists — relevant when `/rag/query` gets a frontend consumer.

## 5. Mount options (for DECIDE — not executed this pass)

**Option A — minimal mount (smallest safe step).** Register the router in `server.py`; build `RAGService` once at lifespan; pass it into `identify_niche` with the real agency_id; auto-seed specialty knowledge per agency on first use; kill the silent `except`; log the abstention. Stays on `HashEmbeddingProvider` (zero egress, zero cost, deterministic — consistent with the current prod posture). Limitation: hash vectors + substring sparse over 5 seeded docs ≈ a slightly fancier keyword match — honest but low marginal value over the existing fallback.

**Option B — mount + harden first (recommended).** Do Option A, but fix §3.1/3.3/3.4 as part of the mount: embedding contract fields (model/version/dim per chunk, fail-closed — CoverWise pattern #1), router caps + usage-guard + no `detail=str(e)`, egress-gated semantic provider (opt-in env, PII strip, `record_llm_call`, cost accounting), FTS5 sparse leg, `identify_niche` abstain-with-reason, and a small retrieval-audit record. Then `/rag/query` is real: agency policy docs + trip documents become first-class searchable knowledge with honest provenance. Effort: a focused tranche (store contract + router hardening + provider guard + seed + tests), no new heavy dependencies.

**Option C — archive (Decision-11 precedent).** If the product doesn't want knowledge retrieval now, archive the package with a pointer like CoverWise did, freeing the intake hook to stay keyword-only. Rejected by the owner's "mount it" directive, recorded as the alternative.

**Recommendation: B.** The stack is good, tested, and domain-aware; the missing joints are small; and the semantic leg is exactly where the KDD model-policy experience (small models win, eval-gate everything) applies. The single non-negotiable inside B: **the embedding egress boundary is an owner decision** (which documents may leave the premises, and under which provider) — I will implement the contract/caps/audit scaffolding and keep the semantic leg behind its env gate until you rule, same posture as JEV serving.

## 6. Registered findings

- **FND-0362** — embedding provenance/dimension hazard (silent 0.0 cross-dimension retrieval) — the load-bearing one.
- **FND-0363** — `identify_niche` silent `except: pass` (honesty-pattern violation).

## 7. Open questions for the owner

1. Semantic leg: enable OpenAI embeddings for agency corpora (egress!) now, later, or hash-only at first?
2. Corpus scope at mount: specialty knowledge only (5 curated entries), or also agency policy uploads + trip documents (which pulls in retention/PII questions)?
3. Frontend surface: is `/rag/query` operator-facing (workbench panel) or service-internal (grounding for ask-loop answers) at first?

---

## 8. Executed record — Option B implemented (2026-10-22)

All Option B items shipped the same day, per the doctrine 4-phase workflow. Semantic-embedding egress remains **env-gated off by default** (`RAG_EMBEDDING_PROVIDER` unset → hash provider) — the egress decision stays with the owner.

### What changed

| Layer | Change |
|---|---|
| `src/rag/models.py` | `RAGChunkMetadata.embedding_model` + `embedding_dimension` — the per-chunk provenance contract (FND-0362). |
| `src/rag/store.py` | Fail-closed contract in `insert_chunk` (embedding without provenance refused; dimension mismatch refused); `search_dense` requires `embedding_model` and filters to it — cross-model/legacy rows are excluded by contract, never silently zero-scored; provenance stored in `metadata_json` (SQL-level columns deferred to the Postgres endgame); **FTS5 lexical leg** (`rag_chunks_fts`, parameterized quoted-token MATCH, bm25-ordered, honest fallback to the substring heuristic when FTS5 is unavailable or a MATCH expression fails); `rag_runs` lineage table (hashed queries only) + `record_retrieval_run`; `count_chunks` + `get_embedding_models` for seeding/status; `delete_chunks_by_document`/`clear_agency_data` keep the FTS index in sync. Every SQL statement is static and parameterized — optional `source_types` filters moved to Python over tenant-scoped rows (Mimosa gate drove the zero-dynamic-SQL shape; strictly better). |
| `src/rag/embeddings.py` | Semantic lane now: strips PII via `spine_api.core.llm_egress` **before** anything leaves the process; transports through the OpenAI SDK (`embeddings.create`) instead of raw urllib; emits `record_llm_call` forensics (hashes only) + `last_call_record`. Hash provider kept with an explicit MD5-is-not-a-security-primitive note. |
| `src/rag/indexer.py` | One `embed_batch` per document (N remote calls → 1); provenance stamped from the provider that produced the vectors. Optional `entity_references` threaded into chunk metadata. |
| `src/rag/retriever.py` | Dense leg scoped to the live provider's model; graph node matching extended to keyword properties (so seeded niche nodes actually boost). |
| `src/rag/service.py` | Canonical `get_default_rag_service()` factory (`RAG_STORE_PATH` overridable) — router and pipeline share one instance; `search()` records lineage + warns loudly when the corpus holds vectors from a different model than the live provider; `status()` truth surface. |
| `src/intake/specialty_knowledge.py` | `ensure_seeded` (idempotent, count-guarded): seeds the 5 specialty docs **with** entity references + registers `niche:*` graph nodes carrying keywords; `identify_niche` auto-seeds then searches; the silent `except: pass` is now an abstain-with-reason log (FND-0363). `seed_rag_knowledge` superseded and removed (behavior fully covered; sole caller migrated). |
| `src/intake/frontier_orchestrator.py` | The specialty hook now passes the real agency id and the canonical service — RAG retrieval actually runs in the spine, inheriting the `enable_frontier_orchestration` tier gate. |
| `spine_api/routers/rag.py` | Mounted surface hardened: `prefix=/api/v1/rag`; 200k-char document cap (413), 4k query cap, tag/title/doc-id caps, `top_k∈[1,50]`, `alpha∈[0,1]` (pydantic-bounded); canonical slowapi limits (60/min query, 30/min index); contract violations → 400 with our message, unexpected failures → opaque 500; `GET /rag/status`; docstring corrected (application-level tenant scoping, not DB RLS); delegates to the canonical factory. |
| `spine_api/server.py` | Router registered behind `_auth_or_skip` (per-route `get_current_agency` enforces the tenant). |
| `tests/conftest.py` | `RAG_STORE_PATH` pinned to a session-local temp path — the spine-instantiated default service can never write into the repo's `data/` during tests. |

### Test evidence (Tier 2; S2 by construction — the pre-fix code IS the failing assertion)

- New: `tests/test_rag_mount.py` — 10 tests: auth required, truthful status, index+query roundtrip + hashed lineage row, tenant isolation through the mounted API, 413/422 caps, frontier wiring (canonical service + agency id injected), provider egress strip + forensics, honest degradation on provider failure.
- Updated to the new contract (hostile-coverage correction, same as the FND-0355 pattern): `test_rag_store.py` (+2 new contract tests: fail-closed insert, model-required/model-filtered dense), `test_rag_retriever.py` (provenance fixtures), `test_rag_integration.py` (`ensure_seeded` idempotence + graph nodes + auto-seed + lineage audit).
- One design fallout fixed at the right layer: the grounding evaluator's retrieval-confidence bound itself to the lexical backend's raw score scale; the FTS leg's bounded scores moved `is_grounded` without any relevance change. Retrieval confidence is now presence-based (citations exist ⇒ 1.0) and scale-free — the overlap term remains the hallucination guard.
- Results: RAG suites 21 + mount 10 + feature gates 35 + specialty salvage + determinism regression batch — all green; server app imports with all 6 `/api/v1/rag/*` routes; zero repo pollution.

### Still open (unchanged DECIDE items)

1. **Semantic embedding egress** — flip `RAG_EMBEDDING_PROVIDER=openai` only on owner ruling (agency document text would leave the process, PII-stripped).
2. Retrieval eval corpus + CI gate (RAGAS-style) before the semantic leg is *trusted* (vs merely available).
3. Frontend surface for `/rag/query` (operator panel vs service-internal).
4. Follow-up candidates logged in the exploration backlog: adjacent-chunk expansion, `source_text`/`retrieval_text` split, cross-encoder reranker (optional dep), corpus governance manifest.

---

## 9. "Do all" executed — remaining DECIDEs resolved and built (2026-10-22, same session)

The owner ruled "do all" on the §7 open questions. Each is now implemented; the one judgment call inside it (which frontend surface first) is recorded below.

### 9.1 Semantic egress — RATIFIED + DEFAULT-ON (owner ruling)

`get_default_embedding_provider()` now defaults to the **semantic lane** (`text-embedding-3-small` via the OpenAI SDK) whenever `OPENAI_API_KEY` is present, degrading to the hash lane only when credentials are absent. PII stripping + `record_llm_call` forensics apply on every call. The test suite pins `RAG_EMBEDDING_PROVIDER=local_hash` (conftest hard set) and stays fully offline; provider tests construct the semantic provider explicitly with mocked transport. This resolves DECIDE #1.

### 9.2 Contract-verification catch: failure semantics hardened (real bug, mine)

Verifying the real ASGI response shapes (AGENTS.md API-contract rule) exposed a defect in my own mount: with the semantic lane active, a provider failure (401 observed live) silently fell back to hash vectors **stamped with the semantic model's name** — precisely the mislabeled-vector class FND-0362 forbids. Fixed at the root:

- **Indexing:** an active-provider failure now RAISES — the document is not indexed, nothing mislabeled is written (test: end-to-end refusal + empty corpus).
- **Querying:** the retriever catches the failure and degrades to sparse-only with a logged reason (no hash-query-vs-semantic-store comparison — test: sparse-only retrieval under provider failure).
- The old "graceful fallback" test was flipped (S2): it previously pinned the bug as contract.

### 9.3 RAGAS-style eval corpus + CI gate (resolves DECIDE #2's precondition)

- Corpus: `tests/evals/data/rag_specialty_qa_v1.json` — 6 positives (keyword-rich + paraphrase) and 3 negatives (out-of-domain, gibberish, non-travel), with `expected_niche` ground truth.
- Gate: `tests/evals/test_rag_eval_gate.py` — runs the SERVING seam (`identify_niche`) on the deterministic hash lane; requires **hit-rate 1.0 and negative-rejection 1.0**.
- Runner: `tools/rag_eval.py` — standalone metrics over any corpus, `--semantic` for the live lane (refuses to fake a live lane without a key), `--fail-under` for optional gating.
- **The gate caught a real serving defect on its first run:** the RRF retriever always ranks *something* top-k (fused scores are rank-derived, never zero), and `identify_niche` accepted hits unconditionally — every gibberish query "matched" three niches. Fixed with a relevance floor at the consuming seam: a hit must contain a substantive query token in its content/title. This is exactly the KDD-doctrine pattern working: the gate falsified the pipeline before production could.

### 9.4 First frontend surface — operator workbench "Knowledge" tab (resolves DECIDE #3; workbench chosen over service-internal grounding)

- `KnowledgePanel.tsx`: truthful status strip (SEMANTIC/HASH chip, FTS5/fallback chip, model name), multi-model corpus warning, document inventory with license badges, grounded query box with GROUNDED/LOW-GROUNDING badge, must-confirm flags, citations with verbatim excerpts + license + retrieval method. Zero simulated content.
- Registered as the 7th workbench tab (`workbench-state.ts`), rendered in `PageClient`, BFF-proxied via four `route-map.ts` entries (`v1/rag/*`).
- Types: canonical `spine.ts` RAG section, verified against the real ASGI responses (contract rule); the query response strips embedding vectors at the router (payload hygiene — up to 1536 floats per citation never reach the UI).
- Tests: 3 vitest suites (status chips, grounded roundtrip, low-grounding + must-confirm). FE: 1431+3 pass; the single failure (`public_marketing_pages` itinerary-checker framing) is pre-existing/parallel-tree — page and test unchanged since `5a544ba5`, my import-graph contribution to that page is type-only, `tsc` clean; registered for the owner with evidence.

### 9.5 Later candidates — all implemented

- **Parent-chunk context expansion** (CoverWise adjacent-context, adapted to parent/child chunking): `query_and_ground(expand_parents=True)` appends up to 5 parent sections as `parent_context` citations (score 0.0), so grounded answers see whole sections.
- **`source_text` split**: metadata gains `source_text` (store defaults it to content at insert); the citation formatter emits verbatim excerpts from it — the citable truth stays clean if a retrieval-optimized transform is added later.
- **License governance**: `license_class` on every chunk (`agency_owned` default; `redistribution_safe` / `local_eval_only` validated at the API edge), `GET /api/v1/rag/documents` inventory listing, license shown on citations and in the panel.
- **Cross-encoder reranker** (`src/rag/reranker.py`): `ms-marco-MiniLM-L-6-v2`, active only when `RAG_RERANKER=1` AND `sentence-transformers` is importable — dark by default, zero new dependencies, RRF ordering preserved as the floor on any failure.

### 9.6 Verification summary

- Backend: 113-test regression batch green (RAG suites + eval gate + feature gates + specialty + determinism remediation + failure-triage/recovery). Ruff clean.
- Frontend: `tsc --noEmit` clean; workbench suites 130/130; full FE 1431 pass / 1 pre-existing failure (§9.4 attribution); KnowledgePanel 3/3.
- Mimosa write-gate interactions this tranche: blocked multi-line SQL (drove the zero-dynamic-SQL store shape) and raw `urllib` (drove the SDK transport) — both outcomes strictly better than the first draft.

---

## 10. Zero-red sweep — every suite failure root-caused and fixed (2026-10-22, evening)

The owner directive "fix and do it right" ended the attribution era: the 45 backend + 1 frontend failures previously marked "SIM4-owned / pre-existing" were root-caused and fixed in this pass. **Result: full backend 5368 passed / 0 failed; full frontend 1435 passed / 0 failed — the first zero-red suite since 57113daf.** Seven distinct root causes, none of them what the earlier attribution guessed:

| # | Root cause | Fix |
|---|---|---|
| 1 | **57113daf privacy leak**: `pending_booking_data` AND `booking_data` added to `_to_dict`/`_row_to_dict`/`TripResponse` — customer PII in the generic trip view, breaking six pinned boundary tests across two files | Removed from all three serializers; both blobs ride the existing tenant-scoped accessors; `constraints` router + `booking_task_service` switched from generic-dict reads to the scoped accessors; payment queue already had its own SQL projection (FND-0358 closed) |
| 2 | **Session-wide store poison**: `test_ghost_concierge_monitor.py:12` set `TRIPSTORE_BACKEND=file` at MODULE level (import/collection phase) on the false belief backend selection happens at import time; the facade reads env per call, so the whole session silently hit the file store — every later SQL-backed test failed FK violations | Module-level write removed; the in-module autouse `_hermetic_store` fixture delivers the same data-safety guarantee correctly scoped (FND-0359 closed) |
| 3 | **Dogfood Layer-1 vs persistence tests**: the privacy guard blocks ANY populated freeform field in dogfood over SQL — `api_trips_post` and `social_inbound` wrote `agent_notes` notes/fixtures and regressed when freeform detection landed | Beta-mode autouse fixtures (the established `test_inbound_router` pattern): guard still audits, encryption/RLS is the boundary |
| 4 | **Route parity drift**: mounted `/api/v1/rag/*` + fare-drop routes were absent from the parity snapshots | `scripts/snapshot_server_routes.py --write` — verified the diff is exactly the intentional additions |
| 5 | **FND-0328 test drift**: public_asks test asserted against the pre-fix corrupted facts shape (bare key strings); the canonical shape is a dict of slot dicts | Test asserts the slot dict (`value`/`authority_level`/`epistemic_status`) |
| 6 | **Contract-parity drift**: TripResponseParity pinned `booking_data`/`pending_booking_data` as TripResponse fields; BlobEncryption pinned blob `v: 1` | Parity updated: fields must be ABSENT from TripResponse (boundary pin); blob v2 + `kid` provenance (FND-0327) pinned |
| 7 | **`EpistemicStatus.VERIFIED` runtime crash** (57113daf): structured-destination intake referenced an enum member that never existed — every structured-destination inbound crashed extraction | Fixed to `EpistemicStatus.FACT` (verified customer input, matching IMPORTED_STRUCTURED authority) with rationale comment |
| 8 | **Guard false positive**: `_GENERATED_ID_PATTERN` rejected underscore segments, so `trip_hist_scope_2360617619` (all-digit uuid suffix) matched the phone scan and blocked a minimal SQL save | Pattern widened to `^(?:draft\|trip\|pkt\|run\|ref)(?:_[a-z0-9]+)*$` — anchored whole-string, so freeform text with real phones is still caught; regression tests added (positive + anchored-negative) |
| 9 | **FE a11y contract drift** (FND-0364): 57113daf rebuilt the upload drop zone as labeled `role=region` (correct — it wraps interactive children) while the marketing test still pinned `role=button` | Test updated to the region contract with rationale; frontier tenant-isolation tests rewritten to PIN the ghost-CRUD removal (never-fabricate) instead of the removed schema |
| 10 | **First-wins audit reason** (found via the checker-gate test): a CRITICAL specialty hit clobbered the checker agent's more-specific `audit_reason` — surfaced only because the RAG-backed specialty detection started returning real hits | First-wins in `frontier_orchestrator`: keep the specific verdict, still raise `requires_manual_audit` |

### Verdict

The "pre-existing, parallel session" attribution on FND-0360 was **wrong in mechanism** — the failures were real defects in HEAD and the test tree, most introduced by 57113daf itself (whose "core pytest suite 27/27" claim was a subset run), plus one session-poisoning test and two contract-parity drifts. All fixed at root; every boundary the old tests pinned is preserved (the scoped accessors and dedicated routes were already the serving paths — 57113daf's `_to_dict` exposure was redundant AND leaky). FND-0358/0359/0360/0364 all closed `fixed`.

---

## 11. Lane-status sweep — unconfigured-vs-failed across ALL model lanes (2026-10-22, night)

The owner asked whether the FND-0352 lane fix ("lane not configured" vs "lane failed") was complete. The intake ambiguity lane was; the sibling lanes were not. All model-backed lanes now carry the same vocabulary (`model_lane_unconfigured` / `model_call_failed` / `jev`-or-None when the model served), so no operator surface can conflate posture with degradation:

| Lane | Mechanism | Change |
|---|---|---|
| Intake ambiguity | `AmbiguityReport.fallback_reason` + decision.py policy | Already done (FND-0352 remediation); verified end-to-end incl. the 5-case policy test |
| Live message triage | `LiveTriageResult.lane_status` (new field, in `to_dict`) | `_triage_fallback` takes the reason; empty input records `empty_input` |
| NL corporate-policy audit | `NaturalLanguagePolicyAuditResult.lane_status` (new field) | `_audit_heuristic` takes `lane_status` (`model_lane_unconfigured` default / `model_call_failed` from the JEV exception path); JEV result pins `"jev"` |
| Failure triage | `FailureTriageOpinion.lane_status` (new field) | Both heuristic entry points carry the reason; JEV result pins `"jev"` |
| Context resolver | `{"available": False, "reason": ...}` | Already honest — distinguishes `resolver_disabled_by_env` / `no_llm_provider` / `llm_unavailable` / `llm_call_failed`; no change |
| Ask reply router | `ReplyRoutingProposal.source` | **Real gap closed**: a configured client that THREW crashed the endpoint (no try/except) — now returns a needs_review proposal with `source="model_call_failed"`, distinct from `"unavailable"` (no creds) and `"disabled"` (env off) |
| Question render selector | per-candidate try/except → verbatim fallback with `grades[]` attached | Verified honest as-is: nothing fabricated, the verbatim engine question is the floor, grade evidence rides the result. Default-off lane; left unchanged |
| Suitability LLM scorer | `source="rule"` (FND-0355 fix) | Already honest; deliberately unwired |
| Ghost concierge checker | `checker_status` enum (FND-0356 fix) | Already carries posture vs verdict |

**Verification:** new `tests/test_lane_status_sweep.py` — 11 tests pinning unconfigured/failed/jev on live-triage, NL-policy, failure-triage, and ask-router (with the ask-loop env gate explicitly ON to reach the client path — the gate previously masked the call-failed branch). Lane-adjacent suites 83 passed; **full backend suite 5379 passed / 0 failed**. Ruff clean.

---

## 12. FND-0361 + deferred-item closeout (2026-10-22, night II)

The final open finding from this arc and the proportionate deferred items, all closed:

| Item | Resolution |
|---|---|
| **FND-0361** (tier3/tier4 fabricated confidences) | `assess_activity_suitability` flags now carry `confidence=1.0` with `details.confidence_basis="deterministic_rule_trigger"` — asserting the certain TRIGGER, never a graded judgment. These confidences are operator-rendered ("85% confidence" in SuitabilityPanel/SuitabilitySignal), so the fabricated constants were directly user-visible. Source-level S2 test asserts the constants are gone. |
| **Embedding cost rollup** | `record_llm_call` gains `cost_estimate_inr` (char-derived: ≈4 chars/token × $0.02/1M × ₹83 — repo conventions, honestly named ESTIMATE); the semantic embedding provider computes it per call (both text and batch); the `/documents/index` response surfaces `embedding_cost_estimate_inr` (None on the hash lane — honest absence, never fabricated). Full accounting rollup into the usage-store quota ledger stays available when real traffic justifies it — the per-call estimate is now the source it would aggregate. |
| **Render selector wart** | `RenderSelection.source` now names what produced the SELECTED question: when the JEV lane grades but nothing passes the rubric, `source="verbatim_fallback"` (grades[] still carries the full JEV evidence). Previously `source="jev"` stuck on a verbatim selection. |

**Genuinely left, with reasons (not dodges):**
- **`retrieval_text` transform** — the storage/citation half shipped (`source_text`); the transform half needs someone to *design a retrieval-optimized rendering*, which is content work with no consumer today. Activates when one exists.
- **Reranker activation** — needs `sentence-transformers` (a multi-GB torch dependency) + `RAG_RERANKER=1` + the eval gate run on the semantic lane. Code is done and dark; activation is an environment + trust decision.
- **Usage-store quota integration** — per-call estimates now exist as the aggregation source; wiring them into the agency quota ledger is worth doing only when semantic-lane volume is real.
- **Commit** — the entire arc remains uncommitted pending owner approval + motto attestation + a slicing decision (this tranche vs. the SIM4 wave interleave in adjacent files).

**Verification:** `tests/test_doall_closeout.py` — 7 tests (rule-trigger pinning, source-level constant check, cost estimator math incl. the /1M correction the tests themselves caught, forensics cost recording, hash-lane honest absence, index-endpoint surfacing, render-selector floor provenance). Full suite **5386 passed / 0 failed / 56 skipped**. Ruff clean. FND-0361 closed — findings store now has **zero open findings from this entire arc**.

---

## 13. Final state — venv, transforms, reranker, ledger; commit deferred on a contested tree (2026-10-22, night III)

Owner directive "do, create venv with uv and 3.13+ and do" executed to the edge of what a contested tree allows:

**Done:**
- **Environment:** uv-managed `.venv` on Python 3.13.3; `sentence-transformers` + torch 2.11 installed into the existing `llm` dependency group (`uv add --group llm sentence-transformers`); cross-encoder `ms-marco-MiniLM-L-6-v2` loads and reranks.
- **`retrieval_text` transform (source/retrieval split completed):** the indexer now builds a contextual retrieval rendering per chunk (document title prepended so contextless child chunks match on their document's subject); FTS indexes the retrieval rendering; embeddings embed it; `metadata.source_text` preserves the verbatim span and citations quote THAT. Eval gate: 1.000/1.000 with the transform.
- **Reranker activated + validated:** `RAG_RERANKER=1` in `.env` (deployment posture); eval gate with reranking + contextual transform held **1.000/1.000**; suite pins `RAG_RERANKER=0` (conftest) so the ~15s cross-encoder load never runs per test process and deterministic ordering stays pinned.
- **Usage-store quota integration:** `RAGService.index_document` now reserves against the agency quota ledger (feature `rag_embedding`) when the semantic lane serves, blocks BEFORE any vectors are written when the budget says so, and finalizes with actual cost. Wiring the tests exposed **FND-0365 (P1, pre-existing)**: `UsageGuard.check_before_call` treated the SQLite store's `(allowed, reservation)` tuple as a dict — quota enforcement had NEVER worked over the durable ledger. Guard fixed (normalize tuple/dict); block + finalize paths proven over a real SQLite store; existing guard suites 67/67.

**Also surfaced and fixed en route:** a duplicated `logger` assignment and the `STOPWORDS` constant briefly dropped by an edit in `embeddings.py` (restored + verified); `_strip_pii_for_egress` in the RAG provider unpacked `strip_pii`'s `(cleaned, count)` tuple as a raw string — caught by the quota tests, fixed to match the typesafe client's pattern.

**Commit deferred — contested moving tree:** the final gate captured a different failure set than every prior run (failures moved entirely into parallel-session files: `insurance_quote_evidence`, `confirmation_family_durability`, `quotes_read_model`), 172 changed entries, `uv.lock` modified mid-run — the SIM4 session is live-editing shared-adjacent files while full suites execute. Committing now would snapshot their half-finished intermediate state. My tranche remains green in the churned tree (166 tests across all touched suites). **The commit executes the moment the tree stabilizes** — attestation + slicing plan are ready (SIM4 wave first, then determinism remediation, then RAG mount+do-all, then red-sweep+lanes; shared interleaved files `persistence.py`/`extractors.py`/`privacy_guard.py`/`FINDINGS_STORE.jsonl` ride with the wave that dominantly owns them, noted in the messages).

---

## 14. FND-0326 fixed — privacy boundary at every persistence door (2026-10-23)

The remaining P0: the privacy guard ran at the TripStore door only. Two sibling doors accepted the same customer PII in plaintext in every posture:

1. **Run-ledger mirrors** (`run_ledger_sql.mirror_meta`/`mirror_step`) — checkpoint payloads are pipeline packet state.
2. **DraftStore writes** — `create`/`save`/`patch`/`update_run_state` carry `customer_message`, `agent_notes`, `customer_name_snapshot`, and `run_snapshots` (packet snapshots).

**Fix (door-parity, mode-consistent):**
- `mirror_step`: payload scanned with `check_trip_data`; a dogfood refusal **skips the mirror** (cache-grade — losing a mirror write degrades replay, never lifecycle honesty) with a loud warning. Refused PII never persists.
- `mirror_meta`: `extra_meta` (the wildcard carrier) scanned; on refusal the lifecycle record STILL persists (state-machine honesty) with `extra_meta` redacted to a non-PII marker — the redaction marker itself must not quote the detected text (caught by the parity test).
- `DraftStore` facade: `_run_privacy_guard` at create/save/patch/update_run_state seams (so a future SQL backend inherits it); dogfood raises → the global handler maps to the 422-with-reason shape (server.py:1553), consistent with trips.

**Tests:** `tests/test_fnd0326_privacy_parity.py` — draft refusal (PII draft blocked, nothing persisted) + clean-synthetic still saves (workflow usable in dogfood) + mirror-step skip + meta-redaction with PII-survival assertion. Drafts router suites 22/22; full suite 5507 passed with the failure set confined to the parallel session's live quote/retail lane (their routes, their corpus state).

**Residual:** at-rest ENCRYPTION parity for draft files and ledger rows (TripStore encrypts blobs; drafts/ledger hold only non-refused payloads in dogfood and unencrypted-but-audited in beta/prod) — posture work, separate finding if pursued.

**Residual failure set:** the parallel session's live quote/retail work is failing its own suites mid-edit (insurance_quote_evidence ×6, quotes_read_model ×2, plus singletons) and their new `/quotes/retail` route drives route-parity drift. Their lane, their pass.

---

## 15. Night III additions — draft at-rest encryption + query-side quota ledger + FND-0366 bisection (2026-10-23)

**Draft at-rest encryption (FND-0326 residual, partial):** `FileDraftStore._save_json` wraps every persisted payload (drafts AND the rebuildable index — transparent to both) in the `__encrypted_draft` v2 envelope (kid fingerprint, same shape as TripStore blobs); `_load_json` decrypts via `decrypt_strict` with an explicit key-mismatch branch (named as a key problem, not masked as "corrupt file") and tolerates legacy plaintext files (pre-envelope loads as-is, re-encrypts on next save). Draft files no longer hold `customer_message`/`agent_notes` in plaintext.

**FND-0366 bisection aid:** the three mid-session master commits (390be0cc / 9beeba6f / 3a8288d5 — constraints topic-50 + DP-04 docs) contain ZERO destructive statements. The deleter is not in committed code from that window; the suspect pool is non-commit sources (DSR path, collided-agency test outside pytest, operator). The tripwire bisects any recurrence automatically.

**Query-side quota ledger:** `RAGService.search` reserves the query embedding (feature `rag_query_embedding`, tiny char-derived estimate) when the semantic lane serves; a block serves sparse-only (logged) instead of making the call; `retrieve(skip_dense=)` param added. Allowed calls finalize with actual cost after retrieval.

**Residual failure set (theirs):** the parallel session's live quote/retail work fails its own suites mid-edit (`insurance_quote_evidence` ×6, `quotes_read_model` ×2, `confirmation_*`, plus their new `/quotes/retail` route driving route-parity drift) and their FE TDD artifacts (`EmptyStateOnboarding.outcomes` ×4 — untracked test pinning an unimplemented step ordering). My tranche: 166+ tests green in every targeted run.
