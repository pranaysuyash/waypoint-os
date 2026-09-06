# A-02 / R-03 RAG retrieval-honesty review

**Date:** 2026-09-04\
**Scope:** `src/rag/`, its focused tests, and the RAG architecture records\
**Decision:** ACCEPT+MODIFY for local contract/doc honesty; DEFER provider-backed semantic retrieval

## Executive finding

The repository has a useful, deterministic, tenant-filtered offline retrieval
slice. It does **not** currently implement provider-backed semantic embeddings,
standards-compliant BM25, or graph traversal. Several older module and
architecture descriptions used those terms as if they were current behavior.
The safe near-term correction is to preserve the stable API and local fallback,
correct the public `alpha` weighting bug, and label the current mechanisms
precisely. A real semantic provider remains a separately researched and gated
implementation task; no provider dependency is introduced in this lane.

## Evidence matrix

| Claim or surface | Current implementation evidence | Honest classification |
|---|---|---|
| “Dense semantic search” | `src/rag/indexer.py:20-42` hashes normalized words with MD5 into 64 buckets; `src/rag/retriever.py:34-41` calls that function for every query; `src/rag/store.py:141-168` computes local cosine similarity in Python | **Local hash-vector similarity**, deterministic and reproducible; not semantic-model evidence |
| “API and deterministic local fallbacks” | `src/rag/indexer.py:1-5,20-35` contains only the deterministic local function; no provider adapter or API call exists in the indexer | **Overclaim removed**; provider integration is future work |
| “BM25” | `src/rag/store.py:170-212` tokenizes with `\\w+`, counts substring occurrences in content/title, applies a length divisor, and never calculates corpus document frequency or IDF | **BM25-style lexical heuristic**, useful for offline exact-ish matching but not standards-compliant BM25 |
| “Knowledge graph traversal” | `src/rag/retriever.py:79-89` loads nodes, matches `node.label` as a substring of the query, and boosts referenced chunks; `get_edges_for_node` is not called | **Node-label/entity-reference boost**; persisted edges are not traversed |
| “Groundedness prevents hallucinations” | `src/rag/grounding.py:36-70` combines top dense/sparse scores with answer/chunk word overlap and emits `must_confirm` when below threshold; it does not perform claim-level entailment, and `src/rag/service.py` accepts a caller-supplied generator | **Heuristic risk flag and provenance formatting**, not truth proof or a hallucination-prevention guarantee |
| Tenant isolation | `src/rag/store.py:149-158,182-191,256-279` binds `agency_id` in chunk/node/edge queries; existing `tests/test_rag_store.py::test_tenant_isolation` passes | **Real local guarantee under this store path**, still not hosted RLS or multi-replica proof |
| Hybrid weighting | `src/rag/models.py:95` documents `alpha=0` as sparse-only and `alpha=1` as dense-only; prior `src/rag/retriever.py` applied those weights in reverse | **Contract defect fixed**; regression test locks both extremes |

## Changes made in this lane

1. Corrected the RRF weights in `src/rag/retriever.py` so `alpha` matches the
   existing model contract: `alpha` weights local-vector rank and
   `1-alpha` weights lexical rank.
2. Corrected module/function docstrings in `src/rag/models.py`,
   `src/rag/indexer.py`, `src/rag/store.py`, `src/rag/retriever.py`, and
   `src/rag/grounding.py` to identify local hash vectors, lexical substring
   scoring, node-label boosting, and heuristic groundedness semantics.
3. Added `tests/test_rag_retrieval_honesty.py`, which verifies alpha extremes
   against independent dense/sparse rank lists.

No provider, database, route, schema, or Git mutation was introduced.

## Decision and long-term path

### ACCEPT+MODIFY — current local fallback

Keep the SQLite and deterministic representation as an explicit offline/test
mode. It is low-dependency, reproducible, inspectable, and preserves strict
agency filtering. The stable `search_sparse_bm25` method name is retained for
compatibility, but its docstring now says what it does. A future API rename
would need a compatibility and migration decision rather than a silent rename.

### DEFER — provider-backed semantic retrieval

Before claiming semantic retrieval, research and benchmark candidate providers
against a versioned, agency-safe corpus. The next decision package should cover:

- provider/model version, dimensionality, language and travel-domain coverage;
- privacy, retention, DPA/TOS, PII handling, residency, and tenant boundaries;
- latency, rate limits, outage behavior, cost per indexed/query token, and
  deterministic retry/idempotency semantics;
- embedding provenance (`provider`, `model`, `version`, `dimension`, source
  text hash, created-at, and re-index policy);
- lexical fallback and mixed-provider migration behavior;
- an independently labeled retrieval benchmark with exact-code, policy,
  paraphrase, negation, cross-tenant leakage, and no-hit cases;
- calibrated score semantics and claim-level grounding evaluation before any
  threshold is treated as a release gate.

The graph lane likewise needs an explicit traversal contract (direction,
depth, relation allow-list, tenant enforcement, cycle/size bounds, and
provenance) before `graph_distance` or “Graph RAG” is exposed as behavior.

## Verification receipt

Command:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_rag_retriever.py tests/test_rag_store.py \
  tests/test_rag_integration.py tests/test_rag_grounding.py \
  tests/test_rag_grounding_pipeline.py tests/test_rag_retrieval_honesty.py
```

Result: **14 passed in 1.08s** (local unit/integration evidence; not hosted,
provider, browser, or production evidence).

The focused test is `tests/test_rag_retrieval_honesty.py::test_alpha_contract_weights_dense_and_sparse_lanes_in_documented_direction`.

## Open boundaries / follow-up tasks

- `Docs/exploration/RAG_VECTOR_AND_LEXICAL_RETRIEVAL_ARCHITECTURE_2026-09-03.md`
  still describes a proposed pgvector/provider architecture and should be
  updated or explicitly marked as proposal-only by the owning architecture
  lane; this review does not rewrite that historical exploration.
- `Docs/ADR_RAG_GROUNDING_AND_CITATION_PROVENANCE_2026-07-29.md` uses
  “prevents hallucinations” and “BM25/graph-vector” language for the current
  implementation. Its historical decision record should receive a superseding
  addendum or status correction before release claims rely on it.
- The repository has no evidence here for hosted RLS, an external vector
  service, model quality, calibrated confidence, or multi-replica consistency.
- Parent/child chunking is present, but parent expansion, summary vectors,
  entity extraction, telemetry persistence, and claim-level citation lineage
  described in the exploration remain separate implementation tasks.

## Ownership and disposition

This bounded lane is complete locally. The parent task should carry this note,
the focused test, and the source truth corrections into the next review wave.
Git staging, commit, push, broad status-register edits, and provider selection
remain outside this lane.
