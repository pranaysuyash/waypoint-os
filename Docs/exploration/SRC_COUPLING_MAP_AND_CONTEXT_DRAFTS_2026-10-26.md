# FND-0387 Step 1–2 — src/ Coupling Map & Draft Bounded Contexts

**Date:** 2026-10-26
**Status:** EVIDENCE COMPLETE — steps 1–2 of the recorded sequencing (topic 51c). Step 3 (owner ADR) is the gate; **no code moves until it**.
**Method:** AST import-graph analysis over all 40 real modules (39 + `__init__`), line counts per module, plus spine_api-subdependency profiling for the top modules. Mechanical, no decisions embedded.

---

## 1. The coupling map (evidence)

| module | lines | imports-out | imported-by |
|---|---|---|---|
| intake | 19,594 | 8 | 7 |
| agents | 8,017 | 8 | 1 |
| decision | 7,703 | 5 | 4 |
| evals | 6,236 | 3 | 1 |
| llm | 4,289 | 2 | 6 |
| analytics | 3,379 | 0 | 2 |
| orchestration | 2,807 | 8 | 3 |
| memory | 2,393 | 1 | 1 |
| rag | 2,008 | 1 | 1 |
| logistics | 1,980 | 0 | 1 |
| suitability | 1,912 | 2 | 2 |
| distribution | 1,330 | 0 | 1 |
| security | 1,316 | 0 | **5** |
| extraction | 1,256 | 0 | 0 |
| services | 1,253 | 2 | 0 |
| fees | 984 | 0 | 3 |
| public_checker | 768 | 2 | 0 |
| schemas | 764 | 0 | **5** |
| …19 more modules <700 lines each | | | |

**Structural facts the map establishes:**

1. **`intake` is the gravitational center** (19.6k lines, imports 8 modules, imported by 7). It already depends on `decision`, `fees`, `llm`, `memory`, `rag`, `suitability`, `analytics`, `orchestration`.
2. **`security` and `schemas` are the shared libraries** (imported by 5 each, importing nothing upward) — they are already de-facto foundations, not peers.
3. **`llm` is a low-coupling hub** (imported by 6, imports only `intake`+`security`).
4. **`analytics`, `extraction`, `logistics`, `distribution` are leaf modules** (import-out = 0 for the latter three) — trivially movable.
5. **The core cycle cluster is `intake ↔ decision ↔ orchestration`** (+ `agents` touching all three): these four cannot be split into separate contexts without first defining which interfaces cross.
6. **src→spine_api coupling is real but narrow**: `intake` reaches `persistence` + `core.auth`; `agents` reaches 6 spine surfaces; `decision` reaches `persistence` + `core.llm_egress`. A bounded-context move must either keep these seams or formalize them as ports.
7. **19 modules are under 700 lines** — many are single-concern leaves (`charter`, `briefing`, `crisis`, `telephony`, `concierge`, `yield_arbitrage`…) that are cheap to relocate once boundaries exist.

## 2. Draft bounded contexts (candidates for the ADR — NOT decisions)

**Draft A — "one context per lifecycle stage" (6 contexts):**

| Context | Members | Rationale |
|---|---|---|
| `contexts/foundation` | `security`, `schemas`, `llm`, `utils`, `config` | shared libraries (5-importer evidence); zero upward deps |
| `contexts/understanding` | `intake`, `extraction`, `memory`, `rag` | parse → extract → remember; the 19.6k-line gravity well + its satellites |
| `contexts/judgment` | `decision`, `suitability`, `fees`, `evals` | score/price/evaluate; decision imports exactly these |
| `contexts/planning` | `orchestration`, `proposals`, `compilers`, `distribution`, `negotiation` | assemble and route the offer |
| `contexts/operations` | `agents`, `logistics`, `crisis`, `telephony`, `concierge`, `charter`, `briefing`, `monitoring`, `corporate*`, `documents`, `yield_arbitrage`, `accounting`, `financial`, `governance`, `public_checker`, `benchmarking`, `adapters`, `services`, `state` | the long tail of small leaf modules + the runtime agents |
| `contexts/analytics` | `analytics`, `rag`→(or understanding) | leaf, zero-out-deps |

**Cycle warning for Draft A:** `intake ↔ decision ↔ orchestration` cross the understanding/judgment/planning lines. The ADR must either (a) define the crossing interfaces (ports), (b) accept `understanding+judgment+planning` as one "pipeline" context, or (c) break the cycle at `orchestration` (it becomes a coordinating layer above, not a peer).

**Draft B — "three contexts" (coarser, lower-risk):**
`core` (foundation+llm) · `pipeline` (intake/extraction/decision/suitability/fees/orchestration/agents + satellites) · `platform` (everything else). Fewer moves, respects the existing cycle, but preserves less boundary discipline.

## 3. What the ADR must decide

1. Draft A (6 contexts, cycle resolved via ports) vs Draft B (3 contexts, cycle kept internal) vs a variant.
2. How `src→spine_api` seams are treated (ports/formal interfaces vs accepted as-is).
3. Move mechanics: import-path compatibility shim during transition, or hard cutover (test suite is the safety net; 1435+152 recent greens are the baseline).
4. Naming (`contexts/X` vs top-level rename) and the deprecation protocol for old paths (AGENTS.md's deprecation rule: shim → warn → one release → remove).

## 4. Verification plan for the eventual move (recorded now, executed after the ADR)

- Full backend suite + frontend suite + mypy + build before/after (the standing regression bar).
- Import-graph re-analysis post-move: assert no NEW cross-context imports beyond the ADR-defined ports (a CI checker can enforce this — same pattern as `route-map` parity tests).
- Zero behavior change: the diff is moves + import rewrites only.

## 5. Effort estimate

- Map + draft (this doc): done.
- ADR: owner decision session.
- Draft A mechanics: ~40 module moves + import rewrites; with shims, 1–2 sessions; CI checker adds ~half a session.
- Draft B mechanics: roughly a third of that.
