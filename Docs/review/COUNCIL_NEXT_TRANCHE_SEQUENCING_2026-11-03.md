# Council — Next-Product-Tranche Sequencing (2026-11-03)

**Mandate:** owner request — "call a council and see what next prod. features/improvements to work on." With code findings at 0 open and the 2026-10-30 adjudication having already decided *what* to build (R2-A..I), this council decides **sequencing** of the decided-but-unbuilt backlog under the NO-GO-public launch posture.

**Persona source:** resolved via `council-orchestrator/resolve_persona_repo.py` → `/Users/pranay/Downloads/Understanding_Personas_24sep` (canonical_rank 7, confidence high); index freshness gate passed (fingerprint `fc9aef43…8f83b64a`, valid=true).

## Council Manifest

- **Lead:** PER-0100 Launch Readiness Director (decision ownership: release posture governs sequencing; continuity with 2026-10-21 council).
- **Seats:**
  | Seat | Persona | Mission |
  |---|---|---|
  | Sequencer | PER-0443 Agentic Travel Systems Architect | dependency graph, cost/risk, downstream unlock |
  | Operator | PER-1098 Travel Agency TMC UX Designer | day-1 agency-operator value |
  | Commercial | PER-20748 Pricing, Monetization & Unit Economics Strategist | revenue/margin, India-launch-market fit, pre-build legality |
  | Skeptic | PER-0468 Missing Workflow Red Team | falsify the field, trap identification, missing workflows |
- **Contracted:** Security & Compliance seat (R2-C content pre-adjudicated; only trigger facts needed). DI-research seat (in-flight lane is agent-owned).
- **Roster changes:** none after start.

## Evidence base (tier: repo docs + findings CLI + git log, read 2026-11-03)

- `findings.py validate`: 397 findings — 392 closed / 5 deferred / **0 open**. Code-quality bar met.
- `Docs/LAUNCH_STATUS.md`: **NO-GO public**, 8 infra/provider blockers (deployment target, hosted DB/provider proof, ungated Fly CD, legal sign-off…); backup/restore + rollback drills landed 2026-10-26. Pilot browser journey gate: signup → intake → blocked/repair → inbox → proposal.
- `Docs/review/COUNCIL_OPEN_ITEM_ADJUDICATION_2026-10-30.md`: R2-A post-pilot · R2-B next tranche · R2-C first-India-pilot trigger · R2-F rides inbox analytics · R2-H post-IRROPS-doc · R2-I post-pilot · owner-only residual: DP-04a, DP-04b, 51c ADR, Facebook session, disk menu, IDEA-141, R2-G sequencing.
- `Docs/architecture/LONG_TERM_STRUCTURAL_ROADMAP_2026-10-23.md`: five invariants; inv-3 schema honesty partially landed; inv-2 fact store marked START HERE, deps none outstanding; inv-1 encryption boundary = DP-03a→B decided, implementation queued.
- `Docs/review/COUNCIL_LAUNCH_READINESS_PRODUCT_2026-09-29.md`: ranked gaps 1–4; gap 1 answer-flow closed in code (AUD-06, 2026-10-21); outbound ask dispatch still credential-gated.
- In flight: Destination-Intelligence program (ERA5 climate normals, weather suitability gate, safety band engine, World Bank fetchers, multi-gov consensus).
- IRROPS expedition doc: **does not exist** (R2-H gate open).

## Seat verdicts (condensed)

| Seat | TOP-2 | Key argument |
|---|---|---|
| Sequencer (PER-0443) | ① inv-2 fact store (+inv-3 schema pass riding) ② operator surfaces (gaps 2+3) + IRROPS doc in slack | inv-2 is the substrate for gap-4 trust surfaces, memory→intake, FE unification; surfaces tranche unlocks R2-F and the pilot journey |
| Operator (PER-1098) | ① gap-2 operator coherence ② gap-3 message-consumption UI (R2-B third, flips to #1 when pilots have bookings) | gaps 2/3 break the daily loop every session; India-first differentiator dies at a paste-only front door; found `/quotes` nav already resolved and `DecisionTab`→`DecisionPanel` renamed (mount unverified) — evidence decay, re-baseline required |
| Commercial (PER-20748) | ① R2-B commission-recon **including durable commission/payout ledgers** ② R2-C structural pre-build (material dissent vs trigger) | margin recovery + strongest WTP narrative; in-memory ledgers can't back any commercial claim; India agency can't onboard onto a misquoting system |
| Skeptic (PER-0468) | Do-not-rank: R2-C pre-build, R2-A, ⑫ watcher, ⑨ analytics-on-paste-inbox, ③-on-in-memory-ledgers, ①-DI-without-rendering. Conditional endorsement: ⑦+⑥ **folded with gap-1 outbound ask loop** | traps identified with recorded triggers; first-week-of-pilot test winner = message-consumption UI; missing workflows: outbound ask, money durability, legal surfaces |

## Cross-examination resolutions

1. **Substrate vs surfaces:** surfaces lead (pilot journey runs through them); inv-2 proceeds as the parallel backend lane feeding the gap-4 tranche.
2. **R2-B timing:** split — durability half (durable ledgers) now (Skeptic+Commercial independent convergence; launch-blocker-4 class), ingest breadth after surfaces.
3. **R2-C:** recorded trigger stands; Commercial's chicken-and-egg argument preserved as **material dissent**; optional cheap additive schema-seam (effective-dated tax field + PAN-gating flag on quote/booking) proposed for owner consideration — not decided.
4. **Gap-1:** code-complete for answer flow; remaining delta = credentials or a link-first dispatch floor → scoped into tranche 1.

## Council Decision

### Recommendation — next wave (zero owner gates)

**Tranche 1 — Operator-surface tranche (gaps 2+3 + gap-1 link floor).**
Re-baseline first (verify A1–A7 breadcrumbs, DecisionPanel mount, /quotes removal, reject-note capture state). Then: unify intake routes; mount-or-delete DecisionPanel; real reason capture on Reject/Request-Changes; message/attachment consumption UI in the unified intake; **link-first ask dispatch** (shareable ask page, no credential dependence) so gap-1 is no longer blocked on provider keys. PII discipline at the message boundary (DP-03b redact-at-ingest seam; do not pre-empt DP-03a encryption mode).
*Unlocks:* pilot browser journey; R2-F (inbox analytics + agent-resolved-share KPI); makes channels genuinely supported or honestly unmarketed.

**Parallel backend lane — Money-lifecycle durability + fact-store substrate.**
(a) Promote commission/payout ledgers from in-memory to durable shared storage (consensus-critical; closes the money-lifecycle gap; launch-blocker-4 class). (b) inv-2 generalization (`resolve_field_merge` → one `merge_facts(existing, incoming, actor)`) with the remaining inv-3 schema pass riding the same edit session; additive read-time projection first (landed `readPacketFacts` pattern), display columns folded after.
*Feeds:* the next surface tranche (gap-4 traveler trust surfaces) and R2-B ingest breadth.

**Slack task:** draft the IRROPS semantics doc (cheap; opens R2-H watcher generalization).

**Sequenced after (in order):** R2-B ingest breadth (on durable ledgers) → gap-4 traveler-visible trust surfaces (constraint attribution, why-this-option, repair-banner fields — the differentiators) → R2-F KPI with inbox analytics. DI program continues as the in-flight lane but **must terminate in rendered surfaces** (Skeptic falsification: scoring without a consumer is invisible at pilot).

### Do-not-build-now (recorded triggers stand)
R2-C full implementation · R2-A API · ⑫ watcher generalization · ⑨ analytics before a real inbox · X-09 LLM resolver · owner gates unchanged (DP-04a, DP-04b, 51c ADR, Facebook session, disk menu, commit authorization).

### Material dissent
Commercial (PER-20748) ranks R2-B-ingest + R2-C-pre-build first on margin logic and argues the R2-C trigger is backwards. Preserved; the trigger-discipline counterargument (Skeptic, adjudication text) governs until the owner amends it.

### Unknowns / falsifiers
- DecisionPanel mount status, A1–A7 current state, outbound-ask surface completeness, DI consumer surfaces, commission-ledger storage state (in-memory claim dated 2026-10-21) — all resolved by tranche 1's re-baseline pass.
- Falsifier for the ranking: if the first pilot starts with real bookings within 30 days, R2-B ingest breadth jumps to tranche 1 position.

### Next action
Owner picks up: start tranche 1 with the re-baseline pass (or say "go" and the agent executes tranche 1).
