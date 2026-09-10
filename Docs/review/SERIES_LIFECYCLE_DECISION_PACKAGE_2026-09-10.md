# Series Lifecycle Decision Package — ADDITIONAL_SCENARIOS (FND-0256 B3b/B4b)

Date: 2026-09-10
Prepared by: Claude Code (combo session), for owner decision
Finding: FND-0256 (P2, open) — series unowned/unindexed/non-ingestible;
B1 (indexing) shipped same day; this package covers the two remaining owner
decisions.

## Corpus ground truth (verified this session)

| Fact | Value | Source |
|---|---|---|
| Single-scenario docs | 302 (`ADDITIONAL_SCENARIOS_26..330`) | `tools/gen_series_subindex.py` count |
| Legacy compendium | 1 (`ADDITIONAL_SCENARIOS_21_25.md`, scenarios 21–30 as sections) | file inspection |
| Sibling series in same dir | 7 docs (`SCENARIOS_331_335_BLACK_SWAN`, `TARGETED_EXPANSION_BATCH_01–05`, `TO_PIPELINE_MAPPING`) | `ls` |
| Total scenario docs in dir | 414 | `ls *.md \| wc -l` |
| Envelope corruption | 0 (all clean post-repair) | `strip_envelope_fragments.py --check` |
| Live consumer (runtime) | `frontend/src/lib/scenario-loader.ts` → `/api/scenarios` dev UI | line 11 |
| Dev generator (docs mode) | `frontend/src/lib/dev-scenario-generator.ts` | lines 118–145 |
| Filename homoglyph defect | 1 (`_97_..._SIМ_` Cyrillic М) | FND-0258 |

## B3b — ingestion path: make the generator ingest the stubs, or not

**Current behavior (verified in source):** `docsTemplates()` requires each
doc to contain a `Customer:`/`Message:`/`Input:` line with ≥60 chars of
quoted content (`candidate.trim().length < 60 → continue`). The stub series
uses `**Scenario**:` + `## Situation` prose instead, so 302/303 docs are
skipped; only the older rich-format docs (case studies) qualify.

**Option B3b-1: relax the generator parser** (accept Situation-prose docs)
- What: extend `docsTemplates()` to also accept the stub shape — e.g. fall
  back to the first 2–3 sentences of `## Situation` as the raw_note seed.
- Cost: ~20 lines in `dev-scenario-generator.ts` + tests. Low risk —
  generator is dev-only (fixtures + docs modes), no prod path.
- Effect: docs mode gains 302 templates; dev fixture corpus grows from
  ~10 rich docs to ~312. Fixtures are persisted per-run under
  `data/fixtures/scenarios/` — corpus grows but stays dev-bounded.
- Risk: raw_note quality from stub prose is lower (generic situations vs.
  crafted customer messages); `inferScenarioConfigFromText` will produce
  weaker stage/mode inference on generic text.

**Option B3b-2: leave generator as-is; the stubs stay docs-only** (status quo)
- Effect: stubs remain unread by the generator; only the scenario-loader
  serves them (title + first 3 Situation lines) in the dev UI.
- Cost: zero. The series stays "reference material," not test material.

**Option B3b-3: reformat the 302 stubs into the generator-compatible shape**
- Cost: a one-time migration tool + regeneration; touching 302 committed
  files (batch-write risk — the exact defect class this repo just repaired,
  though the new write-time gate now guards it).
- Effect: full ingestion; but destroys the stubs' current shape that the
  scenario-loader tests already pin (`scenario-loader.docs.test.ts`).
- Not recommended: highest cost, gates now exist but the value is unclear
  until B4b decides the series' fate.

**My recommendation: B3b-1.** The generator is dev-only, the parser change
is small and additive (keeps the current rich-format path first, adds the
Situation-prose fallback), and it converts a dead corpus into usable dev
test material without touching any committed doc. If B4b later freezes or
retires the series, the parser change remains harmless.

## B4b — series fate: grow, consolidate, or freeze

**Option B4b-1: freeze new stubs, keep existing 302** — recommended
- The series reached 302 near-identical stubs with no admission criteria
  (FND-0256's core observation); siblings (`SCENARIOS_331_335`,
  `BATCH_01–05`) already cover 331+ — the numbering continuity is broken
  (302 stubs vs 331 start), so new numbered stubs no longer extend a
  coherent series.
- Freeze = no new `ADDITIONAL_SCENARIOS_<N>` files without owner signoff;
  recorded in the series README header + enforced socially (a hard CI gate
  on file-count would be over-coupling for a docs directory).
- Existing 302 stay: they're clean, indexed (B1), live-consumed by the
  loader, and cheap to keep.

**Option B4b-2: consolidate** — merge the 303 into fewer thematic files
- High cost (302 file moves/deletes = mass doc churn; deletion requires
  explicit owner authorization per repo rules), low marginal value: the
  loader and SERIES_INDEX handle discovery fine now.
- Reject unless the directory size itself becomes a problem.

**Option B4b-3: keep growing** — not recommended
- No admission criteria exists; the 21–30 compendium + 26–330 singles
  lineage already shows format drift (compendium → singles → sibling
  batches). Uncontrolled growth is the finding's root cause.

**Enforcement notes if B4b-1 is chosen:** add a short "series frozen"
note to `SERIES_INDEX.md` header (one-line tool edit) and a line in
`Docs/INDEX.md` entry; FND-0256 can then close with the disposition
"indexed + frozen; loader-served; generator fallback optional."

## Sequence after your call

1. Your B3b/B4b decisions recorded here (verbatim or amended).
2. If B3b-1: implement generator parser fallback + unit tests; run
   frontend lib tests (`npm test -- --run` from `frontend/`).
3. If B4b-1: freeze note + findings-store closure with this doc as
   evidence; FND-0258 (homoglyph rename) executed as part of closure
   hygiene.
4. Docs/INDEX.md entries updated if framing changes.
