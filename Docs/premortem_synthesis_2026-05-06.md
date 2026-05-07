# Pre-Mortem Synthesis: Waypoint OS Launch Readiness

**Generated:** 2026-05-06
**Source reports:**
- Docs/premortem_01_decision_engine.md — Decision Engine Integrity (8 findings)
- Docs/premortem_02_agent_llm.md — Agent/LLM Pipeline Reliability (8 findings)
- Docs/premortem_03_data_state.md — Data Persistence & State (8 findings)
- Docs/premortem_04_operator_ux.md — Operator UX & Trust (8 findings)
- Docs/premortem_05_security.md — Security & Privacy (6 findings)
- Docs/premortem_06_scale_ops.md — Scale & Operational Survival (6 findings)

**Total findings reviewed:** 44
**Confirmed real & actionable:** ~38
**Already causing data loss:** 3 (audit corruption, index.json RMW, no file lock on overrides)

---

## 1. Cross-Cutting Themes

### Theme A: Guard Boundaries Are Misplaced

Every layer has a boundary it protects and a boundary it ignores:

| Layer | What it guards | What it ignores |
|-------|---------------|-----------------|
| Privacy Guard | Storage (dogfood mode) | Transmission to LLM providers |
| Encryption | At-rest (with dev key) | Key management, rotation failure |
| Jurisdiction Policy | Policy definitions | Wired to production code path |
| Usage Guard | Budget reservation | Phantom orphan reservations |
| Recovery Agent | Re-queue logic | Persistence of re-queue counts |
| Confidence Score | Arithmetic correctness | Semantic meaning to operators |

The pattern: each control was correctly conceived, correctly implemented within its module, and then left disconnected from the larger system. Modules look safe in isolation. The system is not safe.

### Theme B: Production Bugs Already Exist

Three findings are not predictions of future failure — they are observations of current failure:

1. **Audit trail has lost data 4 times** in 5 days (Apr 28 to May 3). Events are being silently trimmed at 10K cap.
2. **Bulk Assign silently does nothing** — `handleBulkAssign` receives an agentId and never calls `assignTrips`.
3. **Override index.json is already clobbering itself** — timestamps show concurrent writes within 1-5ms.
4. **"System Ready" is a hardcoded green div** — never reflects actual backend health.

These are not theoretical. They are in production code right now, waiting to be discovered by the first beta operator who uses bulk assign or notices their override vanished.

### Theme C: Operator Trust Is Unearned

The entire UX presents verdicts without reasoning chains. The operator sees confidence scores without sub-scores, flags without provenance, blockers without remediation paths, and recovery mode without recovery context. The operator is treated as a consumer of AI conclusions, not a partner in reasoning.

This is the most expensive pattern to fix late. If operators learn to ignore confidence scores or dismiss amber badges during beta, they will never unlearn it.

### Theme D: Solo Founder Surface Area Exceeds One Person

The founder handles code, deploy, support, sales, and customer discovery simultaneously. The pre-mortem surfaced 38+ actionable risks. Each requires investigation, fix, deploy, and validation. The first week of beta will surface enough issues that the founder must choose between fixing bugs, supporting agencies, and building pipeline — and cannot do all three.

---

## 2. Ranked Findings by Urgency

### Tier 0: Fix Before Any Beta Operator Touches the System

These are production bugs or data-loss risks happening right now.

| # | Finding | Source | Effort | Impact |
|---|---------|--------|--------|--------|
| 1 | **Bulk Assign silently does nothing** | UX F1 | <1h | Trips never assigned, SLA breaches |
| 2 | **OverrideStore JSONL writes have no file_lock** | Data F5 | <1h | Concurrent writes corrupt override files |
| 3 | **Override index.json non-atomic RMW** | Data F1 | <1h | Override IDs silently lost |
| 4 | **Audit trail silently trims at 10K cap** | Data F3, Scale F5 | 1h | Compliance data permanently gone |
| 5 | **"System Ready" is hardcoded green div** | UX F5 | 30m | Operators misled about backend status |

**Total time to fix Tier 0:** ~4 hours.

### Tier 1: Fix Before Beta Launch (First 5 Agencies)

These are structural gaps that will cause incidents or trust erosion within the first week.

| # | Finding | Source | Effort | Impact |
|---|---------|--------|--------|--------|
| 6 | **Encryption key hardcoded in source** | Security F1 | 1h | Anyone with repo access can decrypt all PII |
| 7 | **PII flows to LLM providers before guard runs** | Security F3, LLM F4 | 4h | Traveler data sent to OpenAI/Gemini |
| 8 | **Beta/prod mode has zero encryption enforcement** | Security F6 | 1h | Plaintext PII storage with no warning |
| 9 | **LLM returns invalid JSON against schema, no validation** | LLM F1 | 2-4h | Silent decision bypass on schema violations |
| 10 | **No LLM fallback chain** | LLM F3 | 1-2 days | Single provider outage = complete system halt |
| 11 | **Confidence scores shown without reasoning chains** | UX F2 | 4-8h | Operators learn to ignore the number |
| 12 | **Pipeline/tab navigation mismatch (5 stages vs 3 tabs)** | UX F3 | 2-4h | New operators can't find decision output |
| 13 | **Flags without provenance in inbox** | UX F4 | 4-8h | Operators dismiss all amber badges |
| 14 | **Recovery mode banner has no recovery context** | UX F6 | 2-4h | Operators resolve feedback they can't see |
| 15 | **All FileTripStore writes use open("w") without temp-file-rename** | Data F2 | 2h | Crash mid-write = zero-length trip file |
| 16 | **assignments.json is single-file crash risk** | Data F7 | 2h | Crash mid-write = all assignments lost |
| 17 | **decrypt() silently returns plaintext on failure** | Security F2 | 1h | Key rotation causes silent data corruption |
| 18 | **Jurisdiction policy is dead code** | Security F4 | 1-2 days | EU agencies have no compliance enforcement |
| 19 | **No DB migration framework** | Data F4 | 1 day | Schema changes are ad-hoc/manual |
| 20 | **Decorrelation between Paris alias and its budget table** | Decision F2 | 30m (verify), 1h (fix) | Paris/London budget quotes are wrong |

**Total time to fix Tier 1:** ~12-20 days of focused work. Not all must be done before beta — some can be deferred with known mitigations.

### Tier 2: Fix Within First 3 Months of Beta

These are real risks that will compound over time but won't kill the launch.

| # | Finding | Source | Effort | Impact |
|---|---------|--------|--------|--------|
| 21 | **Confidence score is flat average, semantically meaningless** | Decision F1 | 2-4 days | Operators learn to ignore confidence |
| 22 | **Toddler age cutoff contradiction (decision.py <4, integration.py <5)** | Decision F3 | 2 days (structural) | 4-year-olds fall through gap |
| 23 | **Activity catalog has zero destination scoping** | Decision F4 | 2-3 days | Dubai trips get snorkeling warnings |
| 24 | **Hardcoded elderly risk set misses dangerous destinations** | Decision F5 | 1-2 days | Swiss altitude not flagged |
| 25 | **Tag-based warnings overridden by intensity scoring** | Decision F6 | 1 day | "discourage" becomes "neutral" |
| 26 | **Context rule penalties compound without bound** | Decision F7 | 2-3 days | Three correlated risks = exclusion |
| 27 | **Multi-destination budget returns "unknown" with no risk flag** | Decision F8 | 2-3 days | Most expensive trips skip budget check |
| 28 | **Recovery agent requeue counts are in-memory** | LLM F2 | 1 day | Restart causes infinite requeue loop |
| 29 | **Recovery mode banner sends hardcoded resolution string** | UX F6 follow | 1 day | The system lies on operator's behalf |
| 30 | **Blockers shown without remediation actions** | UX F8 | 2-3 days | Operators reprocess without changing inputs |
| 31 | **Auto-save without undo/version browser** | UX F7 | 4-8 hours | Operators compose in external editors |
| 32 | **HTTP live tools store raw provider payloads** | LLM F8 | 2-3 days | Session tokens leaked into trip records |
| 33 | **File-to-SQL migration has no tooling** | Data F6 | 1-2 days | Switching backends loses all data |
| 34 | **Data accumulation with no lifecycle** | Data F8, Scale F1 | 2-3 days | 814 run dirs, grows unbounded |
| 35 | **Geography re-indexes on every start** | Scale F2 | 1 day | ~500ms-2s startup tax per restart |

### Tier 3: Monitor and Defer

These are real but not urgent — or need more evidence before investing.

| # | Finding | Source | Why Deferred |
|---|---------|--------|-------------|
| 36 | **Usage guard budget reservation leak on crash** | LLM F5 | Depends on crash frequency; add TTL sweep when you hit it |
| 37 | **60s lease expiry for InMemoryWorkCoordinator** | LLM F6 | Must verify actual agent execution times; likely <10s in practice |
| 38 | **Local LLM is_available() blocks model load** | LLM F7 | Only relevant if local LLM is active provider |
| 39 | **LLM costs unmonitored/unbounded** | Scale F4 | ₹150/trip is manageable; enforce cap when you see pattern |
| 40 | **No rollback path for override store (now gitignored)** | Scale F6 | Data-loss risk is real but deferred until override volume grows |
| 41 | **Single-file assignments.json at scale** | Data F7 | 4KB now; concern at 500+ trips |

---

## 3. The Seven Most Important Actions

If I had to pick the minimum set of fixes that would prevent the most likely launch failure scenarios:

### 1. Fix Bulk Assign and "System Ready" (Tier 0, ~1.5h combined)
These are the two UX bugs that will be discovered first. Bulk assign silently doing nothing will cause the first SLA breach. The hardcoded green dot will cause the first trust fracture. Fix both immediately.

### 2. Add file_lock to OverrideStore (Tier 0, <1h)
The `file_lock` utility already exists in the codebase. It's used by FileTripStore, AssignmentStore, and AuditStore. OverrideStore just doesn't use it. The index.json is already clobbering itself. This is a one-line wrapper.

### 3. Audit trail: extend cap + add alerting (Tier 0, 1h)
10K events is a 2-week window at current volume. Bump to 100K or 500K. Add a WARNING log when trim fires. Add a cron that counts `.corrupt-*.json` files.

### 4. Move encryption key out of source (Tier 1, 1h)
The hardcoded dev key is in Git history. Set `ENCRYPTION_KEY` in production env, remove the fallback default at `encryption.py:25`. The dev key can stay for dev use cases but should not compile into production.

### 5. Add LLM response schema validation (Tier 1, 2-4h)
Add Pydantic model validation after `json.loads()` in each `decide()` method. If the LLM returns `{decision, confidence}` instead of `{decision_state, risk_flags, blockers}`, the system should reject it, not silently pass malformed data through.

### 6. Add LLM fallback chain (Tier 1, 1-2 days)
Minimum viable: catch `LLMUnavailableError` in orchestration.py and retry once with a different provider. This doesn't need to be elegant — just enough that a Gemini outage doesn't kill the entire pipeline.

### 7. Show confidence reasoning chains (Tier 1, 4-8h)
The `ConfidenceScorecard` type already has `data_quality`, `judgment_confidence`, `commercial_confidence` sub-scores. Surface them in the DecisionTab instead of hiding them behind the JSON debug toggle.

---

## 4. Risk Matrix

| Impact ↓ Likelihood → | Low | Medium | High | Already Happening |
|----------------------|------|--------|------|-------------------|
| **Minor** | Geography startup tax | Local LLM blocking health checks | LLM cost retry amplification | — |
| **Major** | Assignments.json crash risk | Key rotation data corruption | LLM fallback gap | Bulk assign bug, Index.json clobbering, Pipeline/tab mismatch |
| **Critical** | Tag-based warnings overridden | No schema validation on LLM output | Encryption key in source, PII to LLM providers, No encryption in beta | Audit trail data loss, Override file corruption |

---

## 5. Pattern: "It's Not Wrong, It's Selectively Wrong"

The most dangerous property across all reports is not that individual decisions are wrong — it's that they are wrong in a way that feels right:

- Paris costs are underestimated by 40-60% but the numbers look plausible (₹25K flights from India to Paris sounds reasonable until you actually try to book)
- Dubai trips get snorkeling warnings but operators dismiss them because they're obviously irrelevant — and then dismiss real warnings too
- Four-year-olds miss the toddler pacing flag but the suitability system fires partial warnings, creating the illusion of coverage
- Multi-destination budget returns "unknown" which downstream treats as "not infeasible" — the conservative answer becomes the permissive one
- Confidence is a flat average that decorrelates from actual decision quality
- Privacy guard blocks storage but not transmission — the data already left before it was checked
- Recovery agent re-queues but doesn't remember how many times — the system treats its own amnesia as a fresh start

The system never fails with a bang. It fails with a slow accumulation of "probably fine" judgments, each just wrong enough to erode margin, trust, and safety.

---

## 6. Source Reports

All six pre-mortem reports are in `Docs/`:

| File | Focus | Findings | Size |
|------|-------|----------|------|
| premortem_01_decision_engine.md | Suitability scoring, confidence, overrides, budget logic | 8 | 19KB |
| premortem_02_agent_llm.md | LLM clients, agent runtime, recovery, usage guard | 8 | 30KB |
| premortem_03_data_state.md | Persistence layer, file stores, migration, audit | 8 | 23KB |
| premortem_04_operator_ux.md | Frontend inbox, workbench, navigation, trust | 8 | 27KB |
| premortem_05_security.md | Encryption, PII, jurisdiction, privacy guard | 6 | 10KB |
| premortem_06_scale_ops.md | Run dirs, geography, solo founder ops, LLM costs | 6 | 10KB |
